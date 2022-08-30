""" ================================= |
| This file is part of                |
|   staticoso                         |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
|   Copyright (C) 2022, OctoSpacc     |
| ================================= """

from datetime import datetime
from multiprocessing import Pool, cpu_count
from Libs.bs4 import BeautifulSoup
from Modules.Config import *
from Modules.Elements import *
from Modules.HTML import *
from Modules.Markdown import *
from Modules.Pug import *
from Modules.Utils import *

def GetHTMLPagesList(Pages, BlogName, SiteRoot, PathPrefix, Unite=[], Type='Page', Category=None, For='Menu', MarkdownExts=(), MenuStyle='Default'):
	ShowPaths, Flatten, SingleLine = True, False, False
	if MenuStyle == 'Flat':
		Flatten = True
	elif MenuStyle == 'Line':
		ShowPaths, SingleLine = False, True
	List, ToPop, LastParent = '', [], []
	IndexPages = Pages.copy()
	for e in IndexPages:
		if e[3]['Index'] == 'False' or e[3]['Index'] == 'None':
			IndexPages.remove(e)
	for i,e in enumerate(IndexPages):
		if e[3]['Type'] != Type:
			ToPop += [i]
	ToPop = RevSort(ToPop)
	for i in ToPop:
		IndexPages.pop(i)
	if Type == 'Page':
		IndexPages = OrderPages(IndexPages)
	for i,e in enumerate(Unite):
		if e:
			IndexPages.insert(i,[e,None,None,{'Type':Type,'Index':'True','Order':'Unite'}])
	for File, Content, Titles, Meta in IndexPages:
		if Meta['Type'] == Type and CanIndex(Meta['Index'], For) and (not Category or Category in Meta['Categories']):
			Depth = (File.count('/') + 1) if Meta['Order'] != 'Unite' else 1
			if Depth > 1 and Meta['Order'] != 'Unite': # Folder names are handled here
				CurParent = File.split('/')[:-1]
				for i,s in enumerate(CurParent):
					if LastParent != CurParent and ShowPaths:
						LastParent = CurParent
						Levels = '- ' * ((Depth-1+i) if not Flatten else 1)
						 # Folders with else without an index file
						if StripExt(File).endswith('index'):
							Title = MakeListTitle(File, Meta, Titles, 'HTMLTitle', SiteRoot, BlogName, PathPrefix)
						else:
							Title = CurParent[Depth-2+i]
						if SingleLine:
							List += ' <span>' + Title + '</span> '
						else:
							List += Levels + Title + '\n'
			if not (Depth > 1 and StripExt(File).split('/')[-1] == 'index'):
				Levels = '- ' * (Depth if not Flatten else 1)
				if Meta['Order'] == 'Unite':
					Title = File
				else:
					Title = MakeListTitle(File, Meta, Titles, 'HTMLTitle', SiteRoot, BlogName, PathPrefix)
				if SingleLine:
					List += ' <span>' + Title + '</span> '
				else:
					List += Levels + Title + '\n'
	return markdown(MarkdownHTMLEscape(List, MarkdownExts), extensions=MarkdownExts)

def TemplatePreprocessor(Text):
	Meta, MetaDefault = '', {
		'MenuStyle': 'Default'}
	for l in Text.splitlines():
		ll = l.lstrip()
		if ll.startswith('<!--'):
			lll = ll[4:].lstrip().rstrip()
			if lll.startswith('%') and lll.endswith('-->'):
				Meta += lll[1:-3].lstrip().rstrip() + '\n'
	Meta = dict(ReadConf(LoadConfStr('[Meta]\n' + Meta), 'Meta'))
	for i in MetaDefault:
		if not i in Meta:
			Meta.update({i:MetaDefault[i]})
	return Meta

def PagePreprocessor(Path, TempPath, Type, SiteTemplate, SiteRoot, GlobalMacros, CategoryUncategorized, LightRun=False):
	File = ReadFile(Path)
	Path = Path.lower()
	Content, Titles, DashyTitles, HTMLTitlesFound, Macros, Meta, MetaDefault = '', [], [], False, '', '', {
		'Template': SiteTemplate,
		'Style': '',
		'Type': Type,
		'Index': 'Unspecified',
		'Feed': 'True',
		'Title': '',
		'HTMLTitle': '',
		'Description': '',
		'Image': '',
		'Macros': {},
		'Categories': [],
		'CreatedOn': '',
		'EditedOn': '',
		'Order': None}
	for l in File.splitlines():
		ll = l.lstrip()
		if ll.startswith('//'):
			lll = ll[2:].lstrip()
			if lll.startswith('%'):
				Meta += lll[1:].lstrip() + '\n'
			elif lll.startswith('$'):
				Macros += lll[1:].lstrip() + '\n'
		else:
			Headings = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
			if Path.endswith(FileExtensions['HTML']) and not HTMLTitlesFound:
				Soup = BeautifulSoup(File, 'html.parser')
				Tags = Soup.find_all()
				for t in Tags:
					if t.name in Headings:
						Title = '#'*int(t.name[1]) + ' ' + str(t.text)
						DashTitle = DashifyTitle(Title.lstrip('#'), DashyTitles)
						DashyTitles += [DashTitle]
						Titles += [Title]
						t.replace_with(MakeLinkableTitle(None, Title, DashTitle, 'md'))
				Content = str(Soup.prettify(formatter=None))
				HTMLTitlesFound = True
			elif Path.endswith(FileExtensions['Markdown']):
				if ll.startswith('#') or (ll.startswith('<') and ll[1:].startswith(Headings)):
					if ll.startswith('#'):
						Title = ll
						#Index = Title.split(' ')[0].count('#')
					elif ll.startswith('<'):
						#Index = int(ll[2])
						Title = '#'*h + str(ll[3:])
					DashTitle = DashifyTitle(MkSoup(Title.lstrip('#')).get_text(), DashyTitles)
					DashyTitles += [DashTitle]
					Titles += [Title]
					Title = MakeLinkableTitle(None, Title, DashTitle, 'md')
					Title = Title.replace('> </', '>  </')
					Title = Title.replace(' </', '</')
					Content += Title + '\n'
				else:
					Content += l + '\n'
			elif Path.endswith('.pug'):
				if ll.startswith(Headings):
					if ll[2:].startswith(("(class='NoTitle", '(class="NoTitle')):
						Content += l + '\n'
					else:
						Title = '#'*int(ll[1]) + str(ll[3:])
						DashTitle = DashifyTitle(Title.lstrip('#'), DashyTitles)
						DashyTitles += [DashTitle]
						Titles += [Title]
						# TODO: We should handle headers that for any reason already have parenthesis
						if ll[2:] == '(':
							Content += l + '\n'
						else:
							Content += MakeLinkableTitle(l, Title, DashTitle, 'pug') + '\n'
				else:
					Content += l + '\n'
			elif Path.endswith('.txt'):
				Content += l + '\n'
	Meta = dict(ReadConf(LoadConfStr('[Meta]\n' + Meta), 'Meta'))
	for i in MetaDefault:
		if i in Meta:
			if i == 'Categories':
				Categories = Meta['Categories'].split(' ')
				Meta['Categories'] = []
				for j in Categories:
					Meta['Categories'] += [j]
		else:
			Meta.update({i:MetaDefault[i]})
	if Meta['Index'] in ('Default', 'Unspecified'):
		if not Meta['Categories']:
			Meta['Categories'] = [CategoryUncategorized]
		if Meta['Type'] == 'Page':
			Meta['Index'] = 'False'
		elif Meta['Type'] == 'Post':
			Meta['Index'] = 'True'
	if GlobalMacros:
		Meta['Macros'].update(GlobalMacros)
	Meta['Macros'].update(ReadConf(LoadConfStr('[Macros]\n' + Macros), 'Macros'))
	#PrintPercentDots(ProcPercent)
	return [TempPath, Content, Titles, Meta]

def PagePostprocessor(FileType, Text, Meta):
	for e in Meta['Macros']:
		Text = ReplWithEsc(Text, f"[: {e} :]", f"[:{e}:]")
	return Text

def OrderPages(Old):
	New, NoOrder, Max = [], [], 0
	for i,e in enumerate(Old):
		Curr = e[3]['Order']
		if Curr:
			if int(Curr) > Max:
				Max = int(Curr)
		else:
			NoOrder += [e]
	New = [None] * (Max+1)
	for i,e in enumerate(Old):
		Curr = e[3]['Order']
		if Curr:
			New[int(Curr)] = e
	while None in New:
		New.remove(None)
	return New + NoOrder

def CanIndex(Index, For):
	if Index in ('False', 'None'):
		return False
	elif Index in ('True', 'All', 'Unlinked'):
		return True
	else:
		return True if Index == For else False

def PatchHTML(File, HTML, StaticPartsText, DynamicParts, DynamicPartsText, HTMLPagesList, PagePath, Content, Titles, Meta, SiteRoot, SiteName, BlogName, FolderRoots, Categories, SiteLang, Locale, LightRun):
	HTMLTitles = FormatTitles(Titles)
	BodyDescription, BodyImage = '', ''
	if not File.lower().endswith('.txt'):
		Soup = BeautifulSoup(Content, 'html.parser')
	
		if not BodyDescription and Soup.p:
			BodyDescription = Soup.p.get_text()[:150].replace('\n', ' ').replace('"', "'") + '...'
		if not BodyImage and Soup.img and Soup.img['src']:
			BodyImage = Soup.img['src']

		#Content = SquareFnrefs(Content)
		if '<a class="footnote-ref"' in Content:
			Content = AddToTagStartEnd(Content, '<a class="footnote-ref"', '</a>', '[', ']')

	Title = GetTitle(File.split('/')[-1], Meta, Titles, 'MetaTitle', BlogName)
	Description = GetDescription(Meta, BodyDescription, 'MetaDescription')
	Image = GetImage(Meta, BodyImage, 'MetaImage')

	for Line in HTML.splitlines():
		Line = Line.lstrip().rstrip()
		if Line.startswith('[staticoso:DynamicPart:') and Line.endswith(']'):
			Path =  Line[len('[staticoso:DynamicPart:'):-1]
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

	for e in StaticPartsText:
		HTML = ReplWithEsc(HTML, f"[staticoso:StaticPart:{e}]", StaticPartsText[e])

	if LightRun:
		HTML = None
	else:
		HTML = DictReplWithEsc(
			HTML, {
				'[staticoso:Site:Menu]': HTMLPagesList,
				'[staticoso:Page:Lang]': SiteLang,
				'[staticoso:Page:Chapters]': HTMLTitles,
				'[staticoso:Page:Title]': Title,
				'[staticoso:Page:Description]': Description,
				'[staticoso:Page:Image]': Image,
				'[staticoso:Page:Path]': PagePath,
				'[staticoso:Page:Style]': Meta['Style'],
				'[staticoso:Page:Content]': Content,
				'[staticoso:Page:ContentInfo]': MakeContentHeader(Meta, Locale, MakeCategoryLine(File, Meta)),
				'[staticoso:BuildTime]': datetime.now().strftime('%Y-%m-%d %H:%M'),
				'[staticoso:Site:Name]': SiteName,
				'[staticoso:Site:AbsoluteRoot]': SiteRoot,
				'[staticoso:Site:RelativeRoot]': GetPathLevels(PagePath)
			})
		for e in Meta['Macros']:
			HTML = ReplWithEsc(HTML, f"[:{e}:]", Meta['Macros'][e])
		for e in FolderRoots:
			HTML = ReplWithEsc(HTML, f"[staticoso:Folder:{e}:AbsoluteRoot]", FolderRoots[e])
		for e in Categories:
			HTML = ReplWithEsc(HTML, f"<span>[staticoso:Category:{e}]</span>", Categories[e])
			HTML = ReplWithEsc(HTML, f"[staticoso:Category:{e}]", Categories[e])

	# TODO: Clean this doubling?
	ContentHTML = Content
	ContentHTML = DictReplWithEsc(
		ContentHTML, {
			'[staticoso:Page:Title]': Title,
			'[staticoso:Page:Description]': Description,
			'[staticoso:Site:Name]': SiteName,
			'[staticoso:Site:AbsoluteRoot]': SiteRoot,
			'[staticoso:Site:RelativeRoot]': GetPathLevels(PagePath)
		})
	for e in Meta['Macros']:
		ContentHTML = ReplWithEsc(ContentHTML, f"[:{e}:]", Meta['Macros'][e])
	for e in FolderRoots:
		ContentHTML = ReplWithEsc(ContentHTML, f"[staticoso:Folder:{e}:AbsoluteRoot]", FolderRoots[e])
	for e in Categories:
		ContentHTML = ReplWithEsc(ContentHTML, f"<span>[staticoso:Category:{e}]</span>", Categories[e])
		ContentHTML = ReplWithEsc(ContentHTML, f"[staticoso:Category:{e}]", Categories[e])

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
	PagePath = f"{OutDir}/{StripExt(File)}.html"
	LightRun = False if LimitFiles == False or File in LimitFiles else True

	if FileLower.endswith(FileExtensions['Markdown']):
		Content = markdown(PagePostprocessor('md', Content, Meta), extensions=MarkdownExts)
	elif FileLower.endswith(('.pug')):
		Content = PagePostprocessor('pug', ReadFile(PagePath), Meta)
	elif FileLower.endswith(('.txt')):
		Content = '<pre>' + html.escape(Content) + '</pre>'
	elif FileLower.endswith(FileExtensions['HTML']):
		Content = ReadFile(PagePath)

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
		SiteRoot=SiteRoot,
		SiteName=SiteName,
		BlogName=BlogName,
		FolderRoots=FolderRoots,
		Categories=Categories,
		SiteLang=SiteLang,
		Locale=Locale,
		LightRun=LightRun)

	if Flags['Minify']:
		if not LightRun:
			HTML = DoMinifyHTML(HTML, MinifyKeepComments)
		ContentHTML = DoMinifyHTML(ContentHTML, MinifyKeepComments)
	if Flags['NoScripts']:
		if not LightRun:
			HTML = StripTags(HTML, ['script'])
		ContentHTML = StripTags(ContentHTML, ['script'])
	if ImgAltToTitle or ImgTitleToAlt:
		if not LightRun:
			HTML = WriteImgAltAndTitle(HTML, ImgAltToTitle, ImgTitleToAlt)
		ContentHTML = WriteImgAltAndTitle(ContentHTML, ImgAltToTitle, ImgTitleToAlt)

	if LightRun:
		SlimHTML = None
	else:
		SlimHTML = HTMLPagesList + ContentHTML
	if not LightRun:
		WriteFile(PagePath, HTML)

	#PrintPercentDots(ProcPercent)
	return [File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image]

def MultiprocHandlePage(d):
	return HandlePage(d['Flags'], d['Page'], d['Pages'], d['Categories'], d['LimitFiles'], d['Snippets'], d['ConfMenu'], d['Locale'])

def MultiprocPagePreprocessor(d):
	return PagePreprocessor(d['Path'], d['TempPath'], d['Type'], d['Template'], d['SiteRoot'], d['GlobalMacros'], d['CategoryUncategorized'], d['LightRun'])

def MakeSite(Flags, LimitFiles, Snippets, ConfMenu, GlobalMacros, Locale):
	PagesPaths, PostsPaths, Pages, MadePages, Categories = [], [], [], [], {}
	PoolSize = cpu_count()
	OutDir, MarkdownExts, Sorting, MinifyKeepComments = Flags['OutDir'], Flags['MarkdownExts'], Flags['Sorting'], Flags['MinifyKeepComments']
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

	PagesPaths = FileNameDateSort(PagesPaths)
	if Sorting['Pages'] == 'Inverse':
		PagesPaths.reverse()
	PostsPaths = FileNameDateSort(PostsPaths)
	if Sorting['Posts'] == 'Inverse':
		PostsPaths.reverse()

	print("[I] Preprocessing Source Pages")
	MultiprocPages = []
	for Type in ['Page', 'Post']:
		if Type == 'Page':
			Files = PagesPaths
			PathPrefix = ''
		elif Type == 'Post':
			Files = PostsPaths
			PathPrefix = 'Posts/'
		for File in Files:
			TempPath = f"{PathPrefix}{File}"
			LightRun = False if LimitFiles == False or TempPath in LimitFiles else True
			MultiprocPages += [{'Path':f"{Type}s/{File}", 'TempPath':TempPath, 'Type':Type, 'Template':SiteTemplate, 'SiteRoot':SiteRoot, 'GlobalMacros':GlobalMacros, 'CategoryUncategorized':CategoryUncategorized, 'LightRun':LightRun}]
	with Pool(PoolSize) as MultiprocPool:
		Pages = MultiprocPool.map(MultiprocPagePreprocessor, MultiprocPages)
	#print() # Make newline after percentage dots
	for File, Content, Titles, Meta in Pages:
		for Cat in Meta['Categories']:
			Categories.update({Cat:''})
	PugCompileList(OutDir, Pages, LimitFiles)

	if Categories:
		print("[I] Generating Category Lists")
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
				WriteFile(FilePath, CategoryPageTemplate.format(Title=Cat))
				Content, Titles, Meta = PagePreprocessor(FilePath, 'Page', SiteTemplate, SiteRoot, GlobalMacros, CategoryUncategorized, LightRun=LightRun)
				Pages += [[File, Content, Titles, Meta]]

	for i,e in enumerate(ConfMenu):
		for File, Content, Titles, Meta in Pages:
			File = StripExt(File)+'.html'
			if e == File:
				ConfMenu[i] = None

	print("[I] Writing Pages")
	MultiprocPages = []
	for Page in Pages:
		MultiprocPages += [{'Flags':Flags, 'Page':Page, 'Pages':Pages, 'Categories':Categories, 'LimitFiles':LimitFiles, 'Snippets':Snippets, 'ConfMenu':ConfMenu, 'Locale':Locale}]
	with Pool(PoolSize) as MultiprocPool:
		MadePages = MultiprocPool.map(MultiprocHandlePage, MultiprocPages)
	#print() # Make newline after percentage dots

	return MadePages
