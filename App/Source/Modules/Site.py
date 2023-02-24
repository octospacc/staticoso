""" ================================== |
| This file is part of                 |
|   staticoso                          |
| Just a simple Static Site Generator  |
|                                      |
| Licensed under the AGPLv3 license    |
|   Copyright (C) 2022-2023, OctoSpacc |
| ================================== """

from datetime import datetime
from multiprocessing import cpu_count
from Modules.Config import *
from Modules.Elements import *
from Modules.Globals import *
from Modules.HTML import *
from Modules.Logging import *
from Modules.Markdown import *
from Modules.Meta import *
from Modules.Pug import *
from Modules.Utils import *

def PatchHTML(Flags:dict, File, HTML:str, Snippets:dict, HTMLPagesList:str, PagePath:str, Content:str, Titles:list, Meta:dict, Categories, Locale:dict, LightRun):
	f = NameSpace(Flags)

	HTMLTitles = FormatTitles(Titles)
	BodyDescription, BodyImage = '', ''
	if not File.lower().endswith('.txt'):
		Soup = MkSoup(Content)
		if not BodyDescription:# and Soup.p:
			#BodyDescription = Soup.p.get_text()[:150].replace('\n', ' ').replace('"', "'") + '...'
			for t in Soup.find_all('p'):
				if t.get_text():
					BodyDescription = t.get_text()[:150].replace('\n', ' ').replace('"', "'") + '...'
					break
		if not BodyImage and Soup.img and Soup.img['src']:
			BodyImage = Soup.img['src']

		#Content = SquareFnrefs(Content)
		if '<a class="footnote-ref" ' in Content:
			Content = AddToTagStartEnd(Content, '<a class="footnote-ref" ', '</a>', '[', ']')

		if any(_ in Content for _ in ('<!-- noprocess />', '<!--noprocess/>', '</ noprocess -->', '</ noprocess --->', '</noprocess-->', '</noprocess--->')):
			Content = DictReplWithEsc(
				Content, {
					'<!--<%noprocess>': '',
					'<noprocess%>-->': '',
					'<noprocess%>--->': '',
					'<!-- noprocess />': '',
					'<!--noprocess/>': '',
					'</ noprocess -->': '',
					'</ noprocess --->': '',
					'</noprocess-->': '',
					'</noprocess--->': ''})

	Title = GetTitle(File.split('/')[-1], Meta, Titles, 'MetaTitle', f.BlogName)
	Description = GetDescription(Meta, BodyDescription, 'MetaDescription')
	Image = GetImage(Meta, BodyImage, 'MetaImage')
	ContentHeader = MakeContentHeader(Meta, Locale, MakeCategoryLine(File, Meta))
	TimeNow = datetime.now().strftime('%Y-%m-%d %H:%M')
	RelativeRoot = GetPathLevels(PagePath)

	if 'staticoso:DynamicPart:' in HTML: # Reduce risk of unnecessary cycles
		for Line in HTML.splitlines():
			Line = Line.lstrip().rstrip()
			if (Line.startswith('[staticoso:DynamicPart:') and Line.endswith(']')) or (Line.startswith('<staticoso:DynamicPart:') and Line.endswith('>')):
				Path =  Line[len('<staticoso:DynamicPart:'):-1]
				Section = Path.split('/')[-1]
				if Section in f.DynamicParts:
					Part = f.DynamicParts[Section]
					Text = ''
					if type(Part) == list:
						for e in Part:
							Text += Snippets['DynamicParts'][f"{Path}/{e}"] + '\n'
					elif type(Part) == str:
						Text = Snippets['DynamicParts'][f"{Path}/{Part}"]
				else:
					Text = ''
				HTML = ReplWithEsc(HTML, f"[staticoso:DynamicPart:{Path}]", Text)
				HTML = ReplWithEsc(HTML, f"<staticoso:DynamicPart:{Path}>", Text)

	for i in range(2):
		for e in Snippets['StaticParts']:
			HTML = ReplWithEsc(HTML, f"[staticoso:StaticPart:{e}]", Snippets['StaticParts'][e])
			HTML = ReplWithEsc(HTML, f"<staticoso:StaticPart:{e}>", Snippets['StaticParts'][e])

	if LightRun:
		HTML = None
	else:
		HTML = WrapDictReplWithEsc(HTML, {
			#'[staticoso:PageHead]': Meta['Head'],
			#'<staticoso:PageHead>': Meta['Head'],
			# #DEPRECATION #
			'staticoso:Site:Menu': HTMLPagesList,
			'staticoso:Page:Lang': Meta['Language'] if Meta['Language'] else f.SiteLang,
			'staticoso:Page:Chapters': HTMLTitles,
			'staticoso:Page:Title': Title,
			'staticoso:Page:Description': Description,
			'staticoso:Page:Image': Image,
			'staticoso:Page:Path': PagePath,
			'staticoso:Page:Style': Meta['Style'],
			################
			'staticoso:SiteMenu': HTMLPagesList,
			'staticoso:PageLang': Meta['Language'] if Meta['Language'] else f.SiteLang,
			'staticoso:PageLanguage': Meta['Language'] if Meta['Language'] else f.SiteLang,
			'staticoso:PageSections': HTMLTitles,
			'staticoso:PageTitle': Title,
			'staticoso:PageDescription': Description,
			'staticoso:PageImage': Image,
			'staticoso:PagePath': PagePath,
			'staticoso:PageHead': Meta['Head'],
			'staticoso:PageStyle': Meta['Style'],
			# NOTE: Content is injected in page only at this point! Keep in mind for other substitutions
			# #DEPRECATION #
			'staticoso:Page:Content': Content,
			'staticoso:Page:ContentInfo': ContentHeader,
			'staticoso:Site:Name': f.SiteName,
			'staticoso:Site:AbsoluteRoot': f.SiteRoot,
			'staticoso:Site:RelativeRoot': RelativeRoot,
			################
			'staticoso:PageContent': Content,
			'staticoso:PageContentInfo': ContentHeader,
			'staticoso:BuildTime': TimeNow,
			'staticoso:SiteDomain': f.SiteDomain,
			'staticoso:SiteName': f.SiteName,
			'staticoso:BlogName': f.BlogName,
			'staticoso:SiteAbsoluteRoot': f.SiteRoot,
			'staticoso:SiteRelativeRoot': RelativeRoot,
		}, InternalMacrosWraps)
		for e in Meta['Macros']:
			HTML = ReplWithEsc(HTML, f"[:{e}:]", Meta['Macros'][e])
		for e in f.FolderRoots:
			HTML = WrapDictReplWithEsc(HTML, {
				f'staticoso:CustomPath:{e}': f.FolderRoots[e],
				f'staticoso:Folder:{e}:AbsoluteRoot': f.FolderRoots[e], #DEPRECATED
			}, InternalMacrosWraps)
		for e in Categories:
			HTML = WrapDictReplWithEsc(HTML, {
				f'staticoso:Category:{e}': Categories[e],
				f'staticoso:CategoryList:{e}': Categories[e],
			}, InternalMacrosWraps)
			HTML = ReplWithEsc(HTML, f'<span>[staticoso:Category:{e}]</span>', Categories[e]) #DEPRECATED

	# TODO: Clean this doubling?
	ContentHTML = Content
	ContentHTML = WrapDictReplWithEsc(ContentHTML, {
		# #DEPRECATION #
		'[staticoso:Page:Title]': Title,
		'[staticoso:Page:Description]': Description,
		'[staticoso:Site:Name]': f.SiteName,
		'[staticoso:Site:AbsoluteRoot]': f.SiteRoot,
		'[staticoso:Site:RelativeRoot]': RelativeRoot,
		################
		'<staticoso:PageTitle>': Title,
		'<staticoso:PageDescription>': Description,
		'<staticoso:SiteDomain>': f.SiteDomain,
		'<staticoso:SiteName>': f.SiteName,
		'<staticoso:SiteAbsoluteRoot>': f.SiteRoot,
		'<staticoso:SiteRelativeRoot>': RelativeRoot,
	}, InternalMacrosWraps)
	for e in Meta['Macros']:
		ContentHTML = ReplWithEsc(ContentHTML, f"[:{e}:]", Meta['Macros'][e])
	for e in f.FolderRoots:
		ContentHTML = WrapDictReplWithEsc(ContentHTML, {
			f'staticoso:CustomPath:{e}': f.FolderRoots[e],
			f'staticoso:Folder:{e}:AbsoluteRoot': f.FolderRoots[e], #DEPRECATED
		}, InternalMacrosWraps)
	for e in Categories:
		ContentHTML = WrapDictReplWithEsc(ContentHTML, {
			f'staticoso:Category:{e}': Categories[e],
			f'staticoso:CategoryList:{e}': Categories[e],
		}, InternalMacrosWraps)
		ContentHTML = ReplWithEsc(ContentHTML, f'<span>[staticoso:Category:{e}]</span>', Categories[e]) #DEPRECATED

	return HTML, ContentHTML, Description, Image

def BuildPagesSearch(Flags:dict, Pages:list, Template:str, Snippets:dict, Locale:dict):
	SearchContent = ''
	with open(f'{staticosoBaseDir()}Assets/PagesSearch.html', 'r') as File:
		Base = File.read().split('{{PagesInject}}')
	for Page in Pages:
		SearchContent += f'''
			<div
				class="staticoso-HtmlSearch-Page"
				data-staticoso-htmlsearch-name="{html.escape(html.unescape(Page["Titles"][0]), quote=True)}"
				data-staticoso-htmlsearch-href="{StripExt(Page["File"])}.html"
			>
				{Page["ContentHtml"]}
			</div>
		'''
	return PatchHTML(
		Flags=Flags,
		File='Search.html',
		HTML=Template,
		Snippets=Snippets,
		HTMLPagesList='',
		PagePath='Search.html',
		Content=Base[0] + SearchContent + Base[1],
		Titles=[],
		Meta=PageMetaDefault,
		Categories=[],
		Locale=Locale,
		LightRun=False)[0]

def HandlePage(Flags:dict, Page:list, Pages, Categories, LimitFiles, Snippets:dict, ConfMenu, Locale:dict):
	File, Content, Titles, Meta = Page
	f = NameSpace(Flags)
	TemplatesText = Snippets['Templates']

	FileLower = File.lower()
	PagePath = f'{f.OutDir}/{StripExt(File)}.html'
	ContentPagePath = f'{f.OutDir}.Content/{StripExt(File)}.html'
	LightRun = False if LimitFiles == False or File in LimitFiles else True

	if FileLower.endswith(FileExtensions['Markdown']):
		Content = markdown(PagePostprocessor('md', Content, Meta), extensions=f.MarkdownExts)
	elif FileLower.endswith(('.pug')):
		Content = PagePostprocessor('pug', ReadFile(PagePath), Meta)
	elif FileLower.endswith(('.txt')):
		Content = '<pre>' + html.escape(Content) + '</pre>'
	#elif FileLower.endswith(FileExtensions['HTML']):
	#	Content = ReadFile(PagePath)

	if LightRun:
		HTMLPagesList = None
	else:
		TemplateMeta = TemplatePreprocessor(TemplatesText[Meta['Template']])
		HTMLPagesList = GetHTMLPagesList(
			Flags,
			Pages=Pages,
			PathPrefix=GetPathLevels(File),
			Unite=ConfMenu,
			Type='Page',
			For='Menu',
			MenuStyle=TemplateMeta['MenuStyle'])

	HTML, ContentHTML, Description, Image = PatchHTML(
		Flags,
		File=File,
		HTML=TemplatesText[Meta['Template']],
		Snippets=Snippets,
		HTMLPagesList=HTMLPagesList,
		PagePath=PagePath[len(f"{f.OutDir}/"):],
		Content=Content,
		Titles=Titles,
		Meta=Meta,
		Categories=Categories,
		Locale=Locale,
		LightRun=LightRun)

	HTML = ReplWithEsc(HTML, f"<staticoso:Feed>", GetHTMLPagesList(
		Flags,
		Limit=Flags['FeedEntries'],
		Type='Post',
		Category=None if Flags['FeedCategoryFilter'] == '*' else Flags['FeedCategoryFilter'],
		Pages=Pages,
		PathPrefix=GetPathLevels(File),
		For='Categories',
		MenuStyle='Flat',
		ShowPaths=False))
	if 'staticoso:DirectoryList:' in HTML: # Reduce risk of unnecessary cycles
		for Line in HTML.splitlines():
			Line = Line.lstrip().rstrip()
			if Line.startswith('<staticoso:DirectoryList:') and Line.endswith('>'):
				Path = Line[len('<staticoso:DirectoryList:'):-1]
				DirectoryList = GetHTMLPagesList(
					Flags,
					CallbackFile=File,
					Pages=Pages,
					PathPrefix=GetPathLevels(File),
					PathFilter=Path,
					For='Categories',
					MenuStyle='Flat')
				HTML = ReplWithEsc(HTML, f"<staticoso:DirectoryList:{Path}>", DirectoryList)

	if Flags['MinifyOutput']:
		if not LightRun:
			HTML = DoMinifyHTML(HTML, f.MinifyKeepComments)
		ContentHTML = DoMinifyHTML(ContentHTML, f.MinifyKeepComments)
	if Flags['NoScripts'] and ('<script' in ContentHTML.lower() or '<script' in HTML.lower()):
		if not LightRun:
			HTML = StripTags(HTML, ['script'])
		ContentHTML = StripTags(ContentHTML, ['script'])
	if f.ImgAltToTitle or f.ImgTitleToAlt:
		if not LightRun:
			HTML = WriteImgAltAndTitle(HTML, f.ImgAltToTitle, f.ImgTitleToAlt)
		ContentHTML = WriteImgAltAndTitle(ContentHTML, f.ImgAltToTitle, f.ImgTitleToAlt)
	if Flags['HTMLFixPre']:
		if not LightRun:
			HTML = DoHTMLFixPre(HTML)
		ContentHTML = DoHTMLFixPre(ContentHTML)

	if LightRun:
		SlimHTML = None
	else:
		SlimHTML = HTMLPagesList + ContentHTML
	if not LightRun:
		WriteFile(PagePath, HTML)
		WriteFile(ContentPagePath, ContentHTML)

	if not LightRun and 'htmljournal' in ContentHTML.lower(): # Avoid extra cycles
		HTML, _, _, _ = PatchHTML(
			Flags,
			File=File,
			HTML=TemplatesText[Meta['Template']],
			Snippets=Snippets,
			HTMLPagesList=HTMLPagesList,
			PagePath=f'{StripExt(File)}.Journal.html',
			Content=MakeHTMLJournal(Flags, Locale, f'{StripExt(File)}.html', ContentHTML),
			Titles='',
			Meta=Meta,
			Categories=Categories,
			Locale=Locale,
			LightRun=LightRun)
		if Flags["JournalRedirect"]:
			HTML = HTML.replace('</head>', f"""<meta http-equiv="refresh" content="0; url='./{PagePath.split('''/''')[-1]}'"></head>""")
		WriteFile(StripExt(PagePath)+'.Journal.html', HTML)

	return {"File": File, "Content": Content, "Titles": Titles, "Meta": Meta, "ContentHtml": ContentHTML, "SlimHtml": SlimHTML, "Description": Description, "Image": Image}

def MultiprocPagePreprocessor(d:dict):
	return PagePreprocessor(d['Flags'], d['Page'], d['GlobalMacros'], d['LightRun'])

def MultiprocHandlePage(d:dict):
	return HandlePage(d['Flags'], d['Page'], d['Pages'], d['Categories'], d['LimitFiles'], d['Snippets'], d['ConfMenu'], d['Locale'])

def FindPagesPaths():
	Paths = {"Pages":[], "Posts":[]}
	for Ext in FileExtensions['Pages']:
		for Type in ('Pages', 'Posts'):
			for File in Path(Type).rglob(f'*.{Ext}'):
				Paths[Type] += [FileToStr(File, f'{Type}/')]
	return Paths

def ReorderPagesPaths(Paths:dict, Sorting:dict):
	for Type in ('Pages', 'Posts'):
		Paths[Type] = FileNameDateSort(Paths[Type])
		if Sorting[Type] in ('Inverse', 'Reverse'):
			Paths[Type].reverse()
	return Paths

def PopulateCategoryLists(Flags:dict, Pages:list, Categories):
	for Cat in Categories:
		for Type in ('Page', 'Post'):
			Categories[Cat] += GetHTMLPagesList(
				Flags,
				Pages=Pages,
				PathPrefix=GetPathLevels('Categories/'),
				Type=Type,
				Category=Cat,
				For='Categories',
				MenuStyle='Flat')
	return Categories

def MakeAutoCategories(Flags:dict, Categories):
	Pages = []
	if Flags['CategoriesAutomatic']:
		OutDir = Flags['OutDir']
		Dir = f'{OutDir}/Categories'
		for Cat in Categories:
			Exists = False
			for File in Path(Dir).rglob(str(Cat)+'.*'):
				Exists = True
				break
			if not Exists:
				File = f'Categories/{Cat}.md'
				FilePath = f'{OutDir}/{File}'
				WriteFile(FilePath, CategoryPageTemplate.format(Name=Cat))
				_, Content, Titles, Meta = PagePreprocessor(Flags, [FilePath, FilePath, Type, None], GlobalMacros, LightRun=LightRun)
				Pages += [File, Content, Titles, Meta]
	return Pages

def PreprocessSourcePages(Flags:dict, PagesPaths:dict, LimitFiles, GlobalMacros:dict, PoolSize:int):
	MultiprocPages = []
	for Type in ('Page', 'Post'):
		Files, PathPrefix = {"Page": [PagesPaths['Pages'], ''], "Post": [PagesPaths['Posts'], 'Posts/']}[Type]
		for i, File in enumerate(Files):
			TempPath = f"{PathPrefix}{File}"
			LightRun = False if LimitFiles == False or TempPath in LimitFiles else True
			MultiprocPages += [{'Flags': Flags, 'Page': [f"{Type}s/{File}", TempPath, Type, None], 'GlobalMacros': GlobalMacros, 'LightRun': LightRun}]
	return DoMultiProc(MultiprocPagePreprocessor, MultiprocPages, PoolSize, True)

def WriteProcessedPages(Flags:dict, Pages:list, Categories, ConfMenu, Snippets, LimitFiles, PoolSize:int, Locale:dict):
	MultiprocPages = []
	for i, Page in enumerate(Pages):
		MultiprocPages += [{'Flags': Flags, 'Page': Page, 'Pages': Pages, 'Categories': Categories, 'LimitFiles': LimitFiles, 'Snippets': Snippets, 'ConfMenu': ConfMenu, 'Locale': Locale}]
	return DoMultiProc(MultiprocHandlePage, MultiprocPages, PoolSize, True)

def MakeSite(Flags:dict, LimitFiles, Snippets, ConfMenu, GlobalMacros:dict, Locale:dict, Threads:int):
	Pages, MadePages, Categories = [], [], {}
	PoolSize = cpu_count() if Threads <= 0 else Threads
	f = NameSpace(Flags)

	logging.info("Finding Pages")
	PagesPaths = FindPagesPaths()
	logging.info(f"Pages Found: {len(PagesPaths['Pages']+PagesPaths['Posts'])}")

	logging.info("Reordering Pages")
	PagesPaths = ReorderPagesPaths(PagesPaths, f.Sorting)

	logging.info("Preprocessing Source Pages")
	Pages = PreprocessSourcePages(Flags, PagesPaths, LimitFiles, GlobalMacros, PoolSize)

	PugCompileList(f.OutDir, Pages, LimitFiles)

	logging.info("Parsing Categories")
	for File, Content, Titles, Meta in Pages:
		for Cat in Meta['Categories']:
			Categories.update({Cat:''})

	if Categories or f.CategoriesAutomatic:
		logging.info("Generating Category Lists")
	Categories = PopulateCategoryLists(Flags, Pages, Categories)
	Pages += MakeAutoCategories(Flags, Categories)

	#logging.info("Building the HTML Search Page")
	#Pages += [PagePreprocessor(Flags, Path='Search.html', TempPath='Search.html', Type='Page', SiteTemplate=SiteTemplate, GlobalMacros=GlobalMacros, LightRun=LightRun, Content=BuildPagesSearch(Flags, Pages))]

	for i,e in enumerate(ConfMenu):
		for File, Content, Titles, Meta in Pages:
			File = StripExt(File)+'.html'
			if e == File:
				ConfMenu[i] = None

	logging.info("Writing Pages")
	MadePages = WriteProcessedPages(Flags, Pages, Categories, ConfMenu, Snippets, LimitFiles, PoolSize, Locale)

	# Do page transclusions here (?)
	#while True:
	#	Operated = False
	#	for di,Dest in enumerate(MadePages):
	#		#print(Dest[0])
	#		#TempPath = f'{PathPrefix}{Dest["File"]}'
	#		#LightRun = False if LimitFiles == False or TempPath in LimitFiles else True
	#		#if not LightRun:
	#		if '[staticoso:Transclude:' in Dest[4] and (LimitFiles == False or f'{PathPrefix}{Dest[0]}' in LimitFiles):
	#			for Item in MadePages:
	#				SrcPrefix = '' if Item[0].startswith('Posts/') else 'Pages/'
	#				print(SrcPrefix, Item[0])
	#				if Item[0] != Dest[0] and f'[staticoso:Transclude:{SrcPrefix}{Item[0]}]' in Dest[4]:
	#					MadePages[di][4] = ReplWithEsc(Dest[4], f'<staticoso:Transclude:{Item[0]}>', Item[4])
	#					print(f'[staticoso:Transclude:{SrcPrefix}{Item[0]}]', Item[4])
	#					Operated = True
	#	if not Operated:
	#		break

	return MadePages
