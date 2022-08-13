""" ================================= |
| This file is part of                |
|   staticoso                         |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
|   Copyright (C) 2022, OctoSpacc     |
| ================================= """

from Libs import htmlmin
from Libs.bs4 import BeautifulSoup
from Modules.Config import *
from Modules.HTML import *
from Modules.Markdown import *
from Modules.Pug import *
from Modules.Utils import *

def DashifyTitle(Title, Done=[]):
	return UndupeStr(DashifyStr(Title), Done, '-')

def MakeLinkableTitle(Line, Title, DashTitle, Type):
	if Type == 'md':
		Index = Title.split(' ')[0].count('#')
		return '<h{} id="{}">{}</h{}>'.format(Index, DashTitle, Title[Index+1:], Index)
	elif Type == 'pug':
		NewLine = ''
		Index = Line.find('h')
		NewLine += Line[:Index]
		NewLine += "{}(id='{}')".format(Line[Index:Index+2], DashTitle)
		NewLine += Line[Index+2:]
		return NewLine

def GetTitle(Meta, Titles, Prefer='MetaTitle', BlogName=None):
	if Prefer == 'BodyTitle':
		Title = Titles[0].lstrip('#') if Titles else Meta['Title'] if Meta['Title'] else 'Untitled'
	elif Prefer == 'MetaTitle':
		Title = Meta['Title'] if Meta['Title'] else Titles[0].lstrip('#') if Titles else 'Untitled'
	elif Prefer == 'HTMLTitle':
		Title = Meta['HTMLTitle'] if Meta['HTMLTitle'] else Meta['Title'] if Meta['Title'] else Titles[0].lstrip('#') if Titles else 'Untitled'
	if BlogName and 'Blog' in Meta['Categories']:
		Title += ' - ' + BlogName
	return Title

def GetDescription(Meta, BodyDescription, Prefer='MetaDescription'):
	if Prefer == 'BodyDescription':
		Description = BodyDescription if BodyDescription else Meta['Description'] if Meta['Description'] else ''
	elif Prefer == 'MetaDescription':
		Description = Meta['Description'] if Meta['Description'] else BodyDescription if BodyDescription else ''
	return Description

def GetImage(Meta, BodyImage, Prefer='MetaImage'):
	if Prefer == 'BodyImage':
		Image = BodyImage if BodyImage else Meta['Image'] if Meta['Image'] else ''
	elif Prefer == 'MetaImage':
		Image = Meta['Image'] if Meta['Image'] else BodyImage if BodyImage else ''
	return Image

def MakeContentHeader(Meta, Locale, Categories=''):
	Header = ''
	for i in ['CreatedOn', 'EditedOn']:
		if Meta[i]:
			Header += '{} {}  \n'.format(Locale[i], Meta[i])
	if Categories:
		Header += '{}: {}  \n'.format(Locale['Categories'], Categories)
	return markdown(Header.rstrip())

def MakeCategoryLine(File, Meta):
	Categories = ''
	if Meta['Categories']:
		for i in Meta['Categories']:
			Categories += '[{}]({}{}.html)  '.format(i, GetPathLevels(File) + 'Categories/', i)
	return Categories

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
			lll = ll[4:].lstrip()
			if lll.startswith('%'):
				Meta += lll[1:-3].lstrip().rstrip() + '\n'
	Meta = dict(ReadConf(LoadConfStr('[Meta]\n' + Meta), 'Meta'))
	for i in MetaDefault:
		if not i in Meta:
			Meta.update({i:MetaDefault[i]})
	return Meta

def PagePreprocessor(Path, Type, SiteTemplate, SiteRoot, GlobalMacros):
	File = ReadFile(Path)
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
			if Path.endswith('.html') and not HTMLTitlesFound:
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
			elif Path.endswith('.md'):
				if ll.startswith('#'):
					DashTitle = DashifyTitle(l.lstrip('#'), DashyTitles)
					DashyTitles += [DashTitle]
					Titles += [l]
					Content += MakeLinkableTitle(None, ll, DashTitle, 'md') + '\n'
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
			Meta['Categories'] = ['Uncategorized']
		if Meta['Type'] == 'Page':
			Meta['Index'] = 'False'
		elif Meta['Type'] == 'Post':
			Meta['Index'] = 'True'
	if GlobalMacros:
		Meta['Macros'].update(GlobalMacros)
	Meta['Macros'].update(ReadConf(LoadConfStr('[Macros]\n' + Macros), 'Macros'))
	return Content, Titles, Meta

def PagePostprocessor(FileType, Text, Meta):
	for e in Meta['Macros']:
		Text = ReplWithEsc(Text, f"[: {e} :]", f"[:{e}:]")
	return Text

def MakeListTitle(File, Meta, Titles, Prefer, SiteRoot, BlogName, PathPrefix=''):
	Title = GetTitle(Meta, Titles, Prefer, BlogName)
	Link = False if Meta['Index'] == 'Unlinked' else True
	if Link:
		Title = '[{}]({})'.format(
			Title,
			'{}{}.html'.format(PathPrefix, StripExt(File)))
	if Meta['Type'] == 'Post':
		CreatedOn = Meta['CreatedOn'] if Meta['CreatedOn'] else '?'
		Title = '[{}] {}'.format(CreatedOn, Title)
	return Title

def FormatTitles(Titles, Flatten=False):
	# TODO: Somehow titles written in Pug can end up here and don't work, they should be handled
	MDTitles, DashyTitles = '', []
	for t in Titles:
		n = t.split(' ')[0].count('#')
		Heading = '- ' * (n if not Flatten else 1)
		Title = t.lstrip('#')
		DashyTitle = DashifyTitle(Title, DashyTitles)
		DashyTitles += [DashyTitle]
		Title = '[{}](#{})'.format(Title, DashyTitle)
		MDTitles += Heading + Title + '\n'
	return markdown(MDTitles)

def OrderPages(Old):
	New, NoOrder, Max = [], [], 0
	for i,e in enumerate(Old):
		Curr = e[3]['Order']
		if Curr:
			if int(Curr) > Max:
				Max = int(Curr)
		else:
			NoOrder += [e]
	for i in range(Max+1):
		New += [[]]
	for i,e in enumerate(Old):
		Curr = e[3]['Order']
		if Curr:
			New[int(Curr)] = e
	while [] in New:
		New.remove([])
	return New + NoOrder

def CanIndex(Index, For):
	if Index in ('False', 'None'):
		return False
	elif Index in ('True', 'All', 'Unlinked'):
		return True
	else:
		return True if Index == For else False

def PatchHTML(File, HTML, PartsText, ContextParts, ContextPartsText, HTMLPagesList, PagePath, Content, Titles, Meta, SiteRoot, SiteName, BlogName, FolderRoots, Categories, SiteLang, Locale):
	HTMLTitles = FormatTitles(Titles)
	BodyDescription, BodyImage = '', ''
	Soup = BeautifulSoup(Content, 'html.parser')
	
	if not BodyDescription and Soup.p:
		BodyDescription = Soup.p.get_text()[:150].replace('\n', ' ').replace('"', "'") + '...'
	if not BodyImage and Soup.img and Soup.img['src']:
		BodyImage = Soup.img['src']

	#Content = SquareFnrefs(Content)
	Content = AddToTagStartEnd(Content, '<a class="footnote-ref"', '</a>', '[', ']')

	Title = GetTitle(Meta, Titles, 'MetaTitle', BlogName)
	Description = GetDescription(Meta, BodyDescription, 'MetaDescription')
	Image = GetImage(Meta, BodyImage, 'MetaImage')

	for Line in HTML.splitlines():
		Line = Line.lstrip().rstrip()
		if Line.startswith('[staticoso:ContextPart:') and Line.endswith(']'):
			Path =  Line[len('[staticoso:ContextPart:'):-1]
			Section = Path.split('/')[-1]
			if Section in ContextParts:
				Part = ContextParts[Section]
				Text = ''
				if type(Part) == list:
					for e in Part:
						Text += ContextPartsText[f"{Path}/{e}"] + '\n'
				elif type(Part) == str:
					Text = ContextPartsText[f"{Path}/{Part}"]
			else:
				Text = ''
			HTML = ReplWithEsc(HTML, f"[staticoso:ContextPart:{Path}]", Text)

	for e in PartsText:
		HTML = ReplWithEsc(HTML, f"[staticoso:Part:{e}]", PartsText[e])
	HTML = ReplWithEsc(HTML, '[staticoso:Site:Menu]', HTMLPagesList)
	HTML = ReplWithEsc(HTML, '[staticoso:Page:Lang]', SiteLang)
	HTML = ReplWithEsc(HTML, '[staticoso:Page:Chapters]', HTMLTitles)
	HTML = ReplWithEsc(HTML, '[staticoso:Page:Title]', Title)
	HTML = ReplWithEsc(HTML, '[staticoso:Page:Description]', Description)
	HTML = ReplWithEsc(HTML, '[staticoso:Page:Image]', Image)
	HTML = ReplWithEsc(HTML, '[staticoso:Page:Path]', PagePath)
	HTML = ReplWithEsc(HTML, '[staticoso:Page:Style]', Meta['Style'])
	HTML = ReplWithEsc(HTML, '[staticoso:Page:Content]', Content)
	HTML = ReplWithEsc(HTML, '[staticoso:Page:ContentInfo]', MakeContentHeader(Meta, Locale, MakeCategoryLine(File, Meta)))
	HTML = ReplWithEsc(HTML, '[staticoso:Site:Name]', SiteName)
	HTML = ReplWithEsc(HTML, '[staticoso:Site:AbsoluteRoot]', SiteRoot)
	HTML = ReplWithEsc(HTML, '[staticoso:Site:RelativeRoot]', GetPathLevels(PagePath))
	for e in Meta['Macros']:
		HTML = ReplWithEsc(HTML, f"[:{e}:]", Meta['Macros'][e])
	for e in FolderRoots:
		HTML = ReplWithEsc(HTML, f"[staticoso:Folder:{e}:AbsoluteRoot]", FolderRoots[e])
	for e in Categories:
		HTML = ReplWithEsc(HTML, f"<span>[staticoso:Category:{e}]</span>", Categories[e])

	# TODO: Clean this doubling?
	ContentHTML = Content
	ContentHTML = ReplWithEsc(ContentHTML, '[staticoso:Site:AbsoluteRoot]', SiteRoot)
	ContentHTML = ReplWithEsc(ContentHTML, '[staticoso:Site:RelativeRoot]', GetPathLevels(PagePath))
	for e in Meta['Macros']:
		ContentHTML = ReplWithEsc(ContentHTML, f"[:{e}:]", Meta['Macros'][e])
	for e in FolderRoots:
		ContentHTML = ReplWithEsc(ContentHTML, f"[staticoso:Folder:{e}:AbsoluteRoot]", FolderRoots[e])
	for e in Categories:
		ContentHTML = ReplWithEsc(ContentHTML, f"<span>[staticoso:Category:{e}]</span>", Categories[e])
	SlimHTML = HTMLPagesList + ContentHTML

	return HTML, ContentHTML, SlimHTML, Description, Image

def DoMinifyHTML(HTML):
	return htmlmin.minify(
		input=HTML,
		remove_comments=True,
		remove_empty_space=True,
		remove_all_empty_space=False,
		reduce_empty_attributes=True,
		reduce_boolean_attributes=True,
		remove_optional_attribute_quotes=True,
		convert_charrefs=True,
		keep_pre=True)

def MakeSite(TemplatesText, PartsText, ContextParts, ContextPartsText, ConfMenu, GlobalMacros, SiteName, BlogName, SiteTagline, SiteTemplate, SiteDomain, SiteRoot, FolderRoots, SiteLang, Locale, Minify, NoScripts, Sorting, MarkdownExts, AutoCategories):
	PagesPaths, PostsPaths, Pages, MadePages, Categories = [], [], [], [], {}
	for Ext in FileExtensions['Pages']:
		for File in Path('Pages').rglob(f"*.{Ext}"):
			PagesPaths += [FileToStr(File, 'Pages/')]
		for File in Path('Posts').rglob(f"*.{Ext}"):
			PostsPaths += [FileToStr(File, 'Posts/')]

	if Sorting['Pages'] == 'Standard':
		PagesPaths.sort()
	elif Sorting['Pages'] == 'Inverse':
		PagesPaths = RevSort(PagesPaths)
	if Sorting['Posts'] == 'Standard':
		PostsPaths.sort()
	elif Sorting['Posts'] == 'Inverse':
		PostsPaths = RevSort(PostsPaths)

	print("[I] Preprocessing Source Pages")
	for Type in ['Page', 'Post']:
		if Type == 'Page':
			Files = PagesPaths
		elif Type == 'Post':
			Files = PostsPaths
		for File in Files:
			Content, Titles, Meta = PagePreprocessor(f"{Type}s/{File}", Type, SiteTemplate, SiteRoot, GlobalMacros)
			if Type != 'Page':
				File = f"{Type}s/{File}"
			Pages += [[File, Content, Titles, Meta]]
			for Cat in Meta['Categories']:
				Categories.update({Cat:''})
	PugCompileList(Pages)

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
		Dir = 'public/Categories'
		for Cat in Categories:
			Exists = False
			for File in Path(Dir).rglob(str(Cat)+'.*'):
				Exists = True
				break
			if not Exists:
				File = f"Categories/{Cat}.md"
				FilePath = f"public/{File}"
				WriteFile(FilePath, f"""\
// Title: {Cat}
// Type: Page
// Index: True

# {Cat}

<div><span>[staticoso:Category:{Cat}]</span></div>
""")
				Content, Titles, Meta = PagePreprocessor(FilePath, SiteRoot)
				Pages += [[File, Content, Titles, Meta]]

	for i,e in enumerate(ConfMenu):
		for File, Content, Titles, Meta in Pages:
			File = StripExt(File)+'.html'
			if e == File:
				ConfMenu[i] = None

	print("[I] Writing Pages")
	for File, Content, Titles, Meta in Pages:
		PagePath = 'public/{}.html'.format(StripExt(File))
		if File.endswith('.md'):
			Content = markdown(PagePostprocessor('md', Content, Meta), extensions=MarkdownExts)
		elif File.endswith(('.pug')):
			Content = PagePostprocessor('pug', ReadFile(PagePath), Meta)

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

		HTML, ContentHTML, SlimHTML, Description, Image = PatchHTML(
			File=File,
			HTML=TemplatesText[Meta['Template']],
			PartsText=PartsText,
			ContextParts=ContextParts,
			ContextPartsText=ContextPartsText,
			HTMLPagesList=HTMLPagesList,
			PagePath=PagePath[len('public/'):],
			Content=Content,
			Titles=Titles,
			Meta=Meta,
			SiteRoot=SiteRoot,
			SiteName=SiteName,
			BlogName=BlogName,
			FolderRoots=FolderRoots,
			Categories=Categories,
			SiteLang=SiteLang,
			Locale=Locale)
		if NoScripts:
			HTML = StripTags(HTML, ['script'])
		if Minify:
			HTML = DoMinifyHTML(HTML)
		WriteFile(PagePath, HTML)
		MadePages += [[File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image]]

	return MadePages
