""" ================================== |
| This file is part of                 |
|   staticoso                          |
| Just a simple Static Site Generator  |
|                                      |
| Licensed under the AGPLv3 license    |
|   Copyright (C) 2022-2023, OctoSpacc |
| ================================== """

import shutil
from datetime import datetime
from multiprocessing import Pool, cpu_count
from Modules.Config import *
from Modules.Elements import *
from Modules.Globals import *
from Modules.HTML import *
from Modules.Logging import *
from Modules.Markdown import *
from Modules.Meta import *
from Modules.Pug import *
from Modules.Utils import *

def PatchHTML(File, HTML, StaticPartsText, DynamicParts, DynamicPartsText, HTMLPagesList, PagePath, Content, Titles, Meta, SiteDomain, SiteRoot, SiteName, BlogName, FolderRoots, Categories, SiteLang, Locale, LightRun):
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

	Title = GetTitle(File.split('/')[-1], Meta, Titles, 'MetaTitle', BlogName)
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
				if Section in DynamicParts:
					Part = DynamicParts[Section]
					Text = ''
					if type(Part) == list:
						for e in Part:
							Text += DynamicPartsText[f"{Path}/{e}"] + '\n'
					elif type(Part) == str:
						Text = DynamicPartsText[f"{Path}/{Part}"]
				else:
					Text = ''
				HTML = ReplWithEsc(HTML, f"[staticoso:DynamicPart:{Path}]", Text)
				HTML = ReplWithEsc(HTML, f"<staticoso:DynamicPart:{Path}>", Text)

	for i in range(2):
		for e in StaticPartsText:
			HTML = ReplWithEsc(HTML, f"[staticoso:StaticPart:{e}]", StaticPartsText[e])
			HTML = ReplWithEsc(HTML, f"<staticoso:StaticPart:{e}>", StaticPartsText[e])

	if LightRun:
		HTML = None
	else:
		HTML = WrapDictReplWithEsc(HTML, {
			#'[staticoso:PageHead]': Meta['Head'],
			#'<staticoso:PageHead>': Meta['Head'],
			# #DEPRECATION #
			'staticoso:Site:Menu': HTMLPagesList,
			'staticoso:Page:Lang': Meta['Language'] if Meta['Language'] else SiteLang,
			'staticoso:Page:Chapters': HTMLTitles,
			'staticoso:Page:Title': Title,
			'staticoso:Page:Description': Description,
			'staticoso:Page:Image': Image,
			'staticoso:Page:Path': PagePath,
			'staticoso:Page:Style': Meta['Style'],
			################
			'staticoso:SiteMenu': HTMLPagesList,
			'staticoso:PageLang': Meta['Language'] if Meta['Language'] else SiteLang,
			'staticoso:PageLanguage': Meta['Language'] if Meta['Language'] else SiteLang,
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
			'staticoso:Site:Name': SiteName,
			'staticoso:Site:AbsoluteRoot': SiteRoot,
			'staticoso:Site:RelativeRoot': RelativeRoot,
			################
			'staticoso:PageContent': Content,
			'staticoso:PageContentInfo': ContentHeader,
			'staticoso:BuildTime': TimeNow,
			'staticoso:SiteDomain': SiteDomain,
			'staticoso:SiteName': SiteName,
			'staticoso:SiteAbsoluteRoot': SiteRoot,
			'staticoso:SiteRelativeRoot': RelativeRoot,
		}, InternalMacrosWraps)
		for e in Meta['Macros']:
			HTML = ReplWithEsc(HTML, f"[:{e}:]", Meta['Macros'][e])
		for e in FolderRoots:
			HTML = WrapDictReplWithEsc(HTML, {
				f'staticoso:CustomPath:{e}': FolderRoots[e],
				f'staticoso:Folder:{e}:AbsoluteRoot': FolderRoots[e], #DEPRECATED
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
		'[staticoso:Site:Name]': SiteName,
		'[staticoso:Site:AbsoluteRoot]': SiteRoot,
		'[staticoso:Site:RelativeRoot]': RelativeRoot,
		################
		'<staticoso:PageTitle>': Title,
		'<staticoso:PageDescription>': Description,
		'<staticoso:SiteDomain>': SiteDomain,
		'<staticoso:SiteName>': SiteName,
		'<staticoso:SiteAbsoluteRoot>': SiteRoot,
		'<staticoso:SiteRelativeRoot>': RelativeRoot,
	}, InternalMacrosWraps)
	for e in Meta['Macros']:
		ContentHTML = ReplWithEsc(ContentHTML, f"[:{e}:]", Meta['Macros'][e])
	for e in FolderRoots:
		ContentHTML = WrapDictReplWithEsc(ContentHTML, {
			f'staticoso:CustomPath:{e}': FolderRoots[e],
			f'staticoso:Folder:{e}:AbsoluteRoot': FolderRoots[e], #DEPRECATED
		}, InternalMacrosWraps)
	for e in Categories:
		ContentHTML = WrapDictReplWithEsc(ContentHTML, {
			f'staticoso:Category:{e}': Categories[e],
			f'staticoso:CategoryList:{e}': Categories[e],
		}, InternalMacrosWraps)
		ContentHTML = ReplWithEsc(ContentHTML, f'<span>[staticoso:Category:{e}]</span>', Categories[e]) #DEPRECATED

	return HTML, ContentHTML, Description, Image

def HandlePage(Flags, Page, Pages, Categories, LimitFiles, Snippets, ConfMenu, Locale):
	File, Content, Titles, Meta = Page
	OutDir, MarkdownExts, Sorting, MinifyKeepComments = Flags['OutDir'], Flags['MarkdownExts'], Flags['Sorting'], Flags['MinifyKeepComments']
	SiteName, BlogName, SiteTagline = Flags['SiteName'], Flags['BlogName'], Flags['SiteTagline']
	SiteTemplate, SiteLang = Flags['SiteTemplate'], Flags['SiteLang']
	SiteDomain, SiteRoot, FolderRoots = Flags['SiteDomain'], Flags['SiteRoot'], Flags['FolderRoots']
	AutoCategories, CategoryUncategorized = Flags['CategoriesAutomatic'], Flags['CategoriesUncategorized']
	ImgAltToTitle, ImgTitleToAlt = Flags['ImgAltToTitle'], Flags['ImgTitleToAlt']
	DynamicParts, DynamicPartsText, StaticPartsText, TemplatesText = Flags['DynamicParts'], Snippets['DynamicParts'], Snippets['StaticParts'], Snippets['Templates']

	FileLower = File.lower()
	PagePath = f'{OutDir}/{StripExt(File)}.html'
	ContentPagePath = f'{OutDir}.Content/{StripExt(File)}.html'
	LightRun = False if LimitFiles == False or File in LimitFiles else True

	if FileLower.endswith(FileExtensions['Markdown']):
		Content = markdown(PagePostprocessor('md', Content, Meta), extensions=MarkdownExts)
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
			Pages=Pages,
			BlogName=BlogName,
			SiteRoot=SiteRoot,
			PathPrefix=GetPathLevels(File),
			Unite=ConfMenu,
			Type='Page',
			For='Menu',
			MarkdownExts=MarkdownExts,
			MenuStyle=TemplateMeta['MenuStyle'])

	HTML, ContentHTML, Description, Image = PatchHTML(
		File=File,
		HTML=TemplatesText[Meta['Template']],
		StaticPartsText=StaticPartsText,
		DynamicParts=DynamicParts,
		DynamicPartsText=DynamicPartsText,
		HTMLPagesList=HTMLPagesList,
		PagePath=PagePath[len(f"{OutDir}/"):],
		Content=Content,
		Titles=Titles,
		Meta=Meta,
		SiteDomain=SiteDomain,
		SiteRoot=SiteRoot,
		SiteName=SiteName,
		BlogName=BlogName,
		FolderRoots=FolderRoots,
		Categories=Categories,
		SiteLang=SiteLang,
		Locale=Locale,
		LightRun=LightRun)

	HTML = ReplWithEsc(HTML, f"<staticoso:Feed>", GetHTMLPagesList(
		Limit=Flags['FeedEntries'],
		Type='Post',
		Category=None if Flags['FeedCategoryFilter'] == '*' else Flags['FeedCategoryFilter'],
		Pages=Pages,
		BlogName=BlogName,
		SiteRoot=SiteRoot,
		PathPrefix=GetPathLevels(File),
		For='Categories',
		MarkdownExts=MarkdownExts,
		MenuStyle='Flat',
		ShowPaths=False))
	if 'staticoso:DirectoryList:' in HTML: # Reduce risk of unnecessary cycles
		for Line in HTML.splitlines():
			Line = Line.lstrip().rstrip()
			if Line.startswith('<staticoso:DirectoryList:') and Line.endswith('>'):
				Path = Line[len('<staticoso:DirectoryList:'):-1]
				DirectoryList = GetHTMLPagesList(
					CallbackFile=File,
					Pages=Pages,
					BlogName=BlogName,
					SiteRoot=SiteRoot,
					PathPrefix=GetPathLevels(File),
					PathFilter=Path,
					For='Categories',
					MarkdownExts=MarkdownExts,
					MenuStyle='Flat')
				HTML = ReplWithEsc(HTML, f"<staticoso:DirectoryList:{Path}>", DirectoryList)

	if Flags['MinifyOutput']:
		if not LightRun:
			HTML = DoMinifyHTML(HTML, MinifyKeepComments)
		ContentHTML = DoMinifyHTML(ContentHTML, MinifyKeepComments)
	if Flags['NoScripts'] and ('<script' in ContentHTML.lower() or '<script' in HTML.lower()):
		if not LightRun:
			HTML = StripTags(HTML, ['script'])
		ContentHTML = StripTags(ContentHTML, ['script'])
	if ImgAltToTitle or ImgTitleToAlt:
		if not LightRun:
			HTML = WriteImgAltAndTitle(HTML, ImgAltToTitle, ImgTitleToAlt)
		ContentHTML = WriteImgAltAndTitle(ContentHTML, ImgAltToTitle, ImgTitleToAlt)
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
			File=File,
			HTML=TemplatesText[Meta['Template']],
			StaticPartsText=StaticPartsText,
			DynamicParts=DynamicParts,
			DynamicPartsText=DynamicPartsText,
			HTMLPagesList=HTMLPagesList,
			PagePath=f'{StripExt(File)}.Journal.html',
			Content=MakeHTMLJournal(Flags, Locale, f'{StripExt(File)}.html', ContentHTML),
			Titles='',
			Meta=Meta,
			SiteDomain=SiteDomain,
			SiteRoot=SiteRoot,
			SiteName=SiteName,
			BlogName=BlogName,
			FolderRoots=FolderRoots,
			Categories=Categories,
			SiteLang=SiteLang,
			Locale=Locale,
			LightRun=LightRun)
		if Flags["JournalRedirect"]:
			HTML = HTML.replace('</head>', f"""<meta http-equiv="refresh" content="0; url='./{PagePath.split('''/''')[-1]}'"></head>""")
		WriteFile(StripExt(PagePath)+'.Journal.html', HTML)

	return [File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image]

def MultiprocPagePreprocessor(d):
	PrintProcPercentDots(d['Process'], 2)
	return PagePreprocessor(d['Path'], d['TempPath'], d['Type'], d['Template'], d['SiteRoot'], d['GlobalMacros'], d['CategoryUncategorized'], d['LightRun'])

def MultiprocHandlePage(d):
	PrintProcPercentDots(d['Process'])
	return HandlePage(d['Flags'], d['Page'], d['Pages'], d['Categories'], d['LimitFiles'], d['Snippets'], d['ConfMenu'], d['Locale'])

def MakeSite(Flags, LimitFiles, Snippets, ConfMenu, GlobalMacros, Locale, Threads):
	PagesPaths, PostsPaths, Pages, MadePages, Categories = [], [], [], [], {}
	PoolSize = cpu_count() if Threads <= 0 else Threads
	OutDir, MarkdownExts, Sorting = Flags['OutDir'], Flags['MarkdownExts'], Flags['Sorting']
	SiteName, BlogName, SiteTagline = Flags['SiteName'], Flags['BlogName'], Flags['SiteTagline']
	SiteTemplate, SiteLang = Flags['SiteTemplate'], Flags['SiteLang']
	SiteDomain, SiteRoot, FolderRoots = Flags['SiteDomain'], Flags['SiteRoot'], Flags['FolderRoots']
	AutoCategories, CategoryUncategorized = Flags['CategoriesAutomatic'], Flags['CategoriesUncategorized']
	ImgAltToTitle, ImgTitleToAlt = Flags['ImgAltToTitle'], Flags['ImgTitleToAlt']
	DynamicParts, DynamicPartsText, StaticPartsText, TemplatesText = Flags['DynamicParts'], Snippets['DynamicParts'], Snippets['StaticParts'], Snippets['Templates']

	for Ext in FileExtensions['Pages']:
		for File in Path('Pages').rglob(f"*.{Ext}"):
			PagesPaths += [FileToStr(File, 'Pages/')]
		for File in Path('Posts').rglob(f"*.{Ext}"):
			PostsPaths += [FileToStr(File, 'Posts/')]
	logging.info(f"Pages Found: {len(PagesPaths+PostsPaths)}")

	PagesPaths = FileNameDateSort(PagesPaths)
	if Sorting['Pages'] == 'Inverse':
		PagesPaths.reverse()
	PostsPaths = FileNameDateSort(PostsPaths)
	if Sorting['Posts'] == 'Inverse':
		PostsPaths.reverse()

	logging.info("Preprocessing Source Pages")
	MultiprocPages = []
	for Type in ['Page', 'Post']:
		if Type == 'Page':
			Files = PagesPaths
			PathPrefix = ''
		elif Type == 'Post':
			Files = PostsPaths
			PathPrefix = 'Posts/'
		for i,File in enumerate(Files):
			TempPath = f"{PathPrefix}{File}"
			LightRun = False if LimitFiles == False or TempPath in LimitFiles else True
			MultiprocPages += [{'Process':{'Num':i, 'Count':len(Files)}, 'Path':f"{Type}s/{File}", 'TempPath':TempPath, 'Type':Type, 'Template':SiteTemplate, 'SiteRoot':SiteRoot, 'GlobalMacros':GlobalMacros, 'CategoryUncategorized':CategoryUncategorized, 'LightRun':LightRun}]
	os.system('printf "["')
	with Pool(PoolSize) as MultiprocPool:
		Pages = MultiprocPool.map(MultiprocPagePreprocessor, MultiprocPages)
	os.system('printf "]\n"') # Make newline after percentage dots

	for File, Content, Titles, Meta in Pages:
		for Cat in Meta['Categories']:
			Categories.update({Cat:''})
	PugCompileList(OutDir, Pages, LimitFiles)

	if Categories:
		logging.info("Generating Category Lists")
		for Cat in Categories:
			for Type in ('Page', 'Post'):
				Categories[Cat] += GetHTMLPagesList(
					Pages=Pages,
					BlogName=BlogName,
					SiteRoot=SiteRoot,
					PathPrefix=GetPathLevels('Categories/'),
					Type=Type,
					Category=Cat,
					For='Categories',
					MarkdownExts=MarkdownExts,
					MenuStyle='Flat')

	if AutoCategories:
		Dir = f"{OutDir}/Categories"
		for Cat in Categories:
			Exists = False
			for File in Path(Dir).rglob(str(Cat)+'.*'):
				Exists = True
				break
			if not Exists:
				File = f"Categories/{Cat}.md"
				FilePath = f"{OutDir}/{File}"
				WriteFile(FilePath, CategoryPageTemplate.format(Name=Cat))
				_, Content, Titles, Meta = PagePreprocessor(FilePath, FilePath, Type, SiteTemplate, SiteRoot, GlobalMacros, CategoryUncategorized, LightRun=LightRun)
				Pages += [[File, Content, Titles, Meta]]

	#logging.info("Building the HTML Search Page")
	#Pages += [PagePreprocessor(Path='Search.html', TempPath='Search.html', Type='Page', SiteTemplate=SiteTemplate, SiteRoot=SiteRoot, GlobalMacros=GlobalMacros, CategoryUncategorized=CategoryUncategorized, LightRun=LightRun, Content=BuildPagesSearch(Flags, Pages))]

	for i,e in enumerate(ConfMenu):
		for File, Content, Titles, Meta in Pages:
			File = StripExt(File)+'.html'
			if e == File:
				ConfMenu[i] = None

	logging.info("Writing Pages")
	MultiprocPages = []
	for i,Page in enumerate(Pages):
		MultiprocPages += [{'Process':{'Num':i, 'Count':len(Pages)}, 'Flags':Flags, 'Page':Page, 'Pages':Pages, 'Categories':Categories, 'LimitFiles':LimitFiles, 'Snippets':Snippets, 'ConfMenu':ConfMenu, 'Locale':Locale}]
	os.system('printf "["')
	with Pool(PoolSize) as MultiprocPool:
		MadePages = MultiprocPool.map(MultiprocHandlePage, MultiprocPages)
	os.system('printf "]\n"') # Make newline after percentage dots

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
