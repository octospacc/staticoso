#!/usr/bin/env python3
""" ================================= |
| This file is part of                |
|   staticoso                         |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
|   Copyright (C) 2022, OctoSpacc     |
| ================================= """

import argparse
import os
import shutil
from ast import literal_eval
from datetime import datetime
from pathlib import Path

# Our local Markdown patches conflict if the module is installed on the system, so first try to import from system
try:
	from markdown import markdown
except ModuleNotFoundError:
	from Libs.markdown import markdown

from Libs import htmlmin
from Libs.bs4 import BeautifulSoup

try:
	from Modules.ActivityPub import *
	ActivityPub = True
except:
	ActivityPub = False

from Modules.Gemini import *
from Modules.Pug import *
from Modules.Utils import *

Extensions = {
	'Pages': ('md', 'pug')}

def ResetPublic():
	for i in ('public', 'public.gmi'):
		try:
			shutil.rmtree(i)
		except FileNotFoundError:
			pass

def GetLevels(Path, AsNum=False, Add=0, Sub=0):
	n = Path.count('/') + Add - Sub
	return n if AsNum else '../' * n

def DashifyTitle(Title, Done=[]):
	return UndupeStr(DashifyStr(Title), Done, '-')

def GetTitle(Meta, Titles, Prefer='MetaTitle'):
	if Prefer == 'BodyTitle':
		Title = Titles[0].lstrip('#') if Titles else Meta['Title'] if Meta['Title'] else 'Untitled'
	elif Prefer == 'MetaTitle':
		Title = Meta['Title'] if Meta['Title'] else Titles[0].lstrip('#') if Titles else 'Untitled'
	elif Prefer == 'HTMLTitle':
		Title = Meta['HTMLTitle'] if Meta['HTMLTitle'] else Meta['Title'] if Meta['Title'] else Titles[0].lstrip('#') if Titles else 'Untitled'
	if Meta['Type'] == 'Post':
		# TODO: This hardcodes my blog name, bad, will fix asap
		Title += ' - blogoctt'
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

def MakeListTitle(File, Meta, Titles, Prefer, SiteRoot, PathPrefix=''):
	Title = GetTitle(Meta, Titles, Prefer)
	Link = False if Meta['Index'] == 'Unlinked' else True
	if Link:
		Title = '[{}]({})'.format(
			Title,
			'{}{}.html'.format(PathPrefix, StripExt(File)))
	if Meta['Type'] == 'Post' and Meta['CreatedOn']:
		Title = '[{}] {}'.format(
			Meta['CreatedOn'],
			Title)
	return Title

def FormatTitles(Titles):
	# TODO: Somehow titles written in Pug can end up here and don't work, they should be handled
	MDTitles, DashyTitles = '', []
	for t in Titles:
		n = t.split(' ')[0].count('#')
		Heading = '- ' * n
		Title = t.lstrip('#')
		DashyTitle = DashifyTitle(Title, DashyTitles)
		DashyTitles += [DashyTitle]
		Title = '[{}](#{})'.format(Title, DashyTitle)
		MDTitles += Heading + Title + '\n'
	return markdown(MDTitles)

def LoadFromDir(Dir, Rglob):
	Contents = {}
	for File in Path(Dir).rglob(Rglob):
		File = str(File)[len(Dir)+1:]
		Contents.update({File: ReadFile('{}/{}'.format(Dir, File))})
	return Contents

def Preprocessor(Path, SiteRoot):
	File = ReadFile(Path)
	Content, Titles, DashyTitles, Meta = '', [], [], {
		'Template': 'Standard.html',
		'Style': '',
		'Type': '',
		'Index': 'True',
		'Title': '',
		'HTMLTitle': '',
		'Description': '',
		'Image': '',
		'Categories': [],
		'CreatedOn': '',
		'EditedOn': '',
		'Order': None}
	for l in File.splitlines():
		ls = l.lstrip()
		if ls.startswith('// '):
			lss = ls[3:]
			for Item in ('Template', 'Type', 'Index', 'Title', 'HTMLTitle', 'Description', 'Image', 'CreatedOn', 'EditedOn'):
				ItemText = '{}: '.format(Item)
				if lss.startswith(ItemText):
					Meta[Item] = lss[len(ItemText):]
			if lss.startswith('Categories: '):
				for i in lss[len('Categories: '):].split(' '):
					Meta['Categories'] += [i]
			elif lss.startswith('Background: '):
				Meta['Style'] += "#MainBox{Background:" + lss[len('Background: '):] + ";} "
			elif lss.startswith('Style: '):
				Meta['Style'] += lss[len('Style: '):] + ' '
			elif lss.startswith('Order: '):
				Meta['Order'] = int(lss[len('Order: '):])
		else:
			if Path.endswith('.md'):
				if ls.startswith('#'):
					DashTitle = DashifyTitle(l.lstrip('#'), DashyTitles)
					DashyTitles += [DashTitle]
					Titles += [l]
					Content += MakeLinkableTitle(l, ls, DashTitle, 'md') + '\n'
				else:
					Content += l + '\n'
			elif Path.endswith('.pug'):
				if ls.startswith(('h1', 'h2', 'h3', 'h4', 'h5', 'h6')):
					if ls[2:].startswith(("(class='NoTitle", '(class="NoTitle')):
						Content += l + '\n'
					else:
						Title = '#'*int(ls[1]) + str(ls[3:])
						DashTitle = DashifyTitle(Title.lstrip('#'), DashyTitles)
						DashyTitles += [DashTitle]
						Titles += [Title]
						# TODO: We should handle headers that for any reason already have parenthesis
						if ls[2:] == '(':
							Content += l + '\n'
						else:
							Content += MakeLinkableTitle(l, Title, DashTitle, 'pug') + '\n'
				else:
					Content += l + '\n'
	return Content, Titles, Meta

def MakeContentHeader(Meta, Locale, Categories=''):
	Header = ''
	for i in ['CreatedOn', 'EditedOn']:
		if Meta[i]:
			Header += '{} {}  \n'.format(Locale[i], Meta[i])
	if Categories:
		Header += '{}: {}  \n'.format(Locale['Categories'], Categories)
	return markdown(Header)

def MakeCategoryLine(File, Meta):
	Categories = ''
	if Meta['Categories']:
		for i in Meta['Categories']:
			Categories += '[{}]({}{}.html)  '.format(i, GetLevels(File) + 'Categories/', i)
	return Categories

def PatchHTML(File, HTML, PartsText, ContextParts, ContextPartsText, HTMLPagesList, PagePath, Content, Titles, Meta, SiteRoot, FolderRoots, Categories, Locale):
	HTMLTitles = FormatTitles(Titles)
	BodyDescription, BodyImage = '', ''
	Parse = BeautifulSoup(Content, 'html.parser')
	if not BodyDescription and Parse.p:
		BodyDescription = Parse.p.get_text()[:150].replace('\n', ' ').replace('"', "'") + '...'
	if not BodyImage and Parse.img and Parse.img['src']:
		BodyImage = Parse.img['src']

	Title = GetTitle(Meta, Titles, 'MetaTitle')
	Description = GetDescription(Meta, BodyDescription, 'MetaDescription')
	Image = GetImage(Meta, BodyImage, 'MetaImage')

	for Line in HTML.splitlines():
		Line = Line.lstrip().rstrip()
		if Line.startswith('[HTML:ContextPart:') and Line.endswith(']'):
			Path =  Line[len('[HTML:ContextPart:'):-1]
			Section = Path.split('/')[-1]
			if Section in ContextParts:
				Part = ContextParts[Section]
				Text = ''
				if type(Part) == list:
					for i in Part:
						Text += ContextPartsText['{}/{}'.format(Path, i)] + '\n'
				elif type(Part) == str:
					Text = ContextPartsText['{}/{}'.format(Path, Part)]
			else:
				Text = ''
			HTML = HTML.replace('[HTML:ContextPart:{}]'.format(Path), Text)
	for i in PartsText:
		HTML = HTML.replace('[HTML:Part:{}]'.format(i), PartsText[i])
	HTML = HTML.replace('[HTML:Page:LeftBox]', HTMLPagesList)
	HTML = HTML.replace('[HTML:Page:RightBox]', HTMLTitles)
	HTML = HTML.replace('[HTML:Page:Title]', Title)
	HTML = HTML.replace('[HTML:Page:Description]', Description)
	HTML = HTML.replace('[HTML:Page:Image]', Image)
	HTML = HTML.replace('[HTML:Page:Path]', PagePath)
	HTML = HTML.replace('[HTML:Page:Style]', Meta['Style'])
	HTML = HTML.replace('[HTML:Page:Content]', Content)
	HTML = HTML.replace('[HTML:Page:ContentHeader]', MakeContentHeader(Meta, Locale, MakeCategoryLine(File, Meta)))
	HTML = HTML.replace('[HTML:Site:AbsoluteRoot]', SiteRoot)
	HTML = HTML.replace('[HTML:Site:RelativeRoot]', GetLevels(PagePath))
	for i in FolderRoots:
		HTML = HTML.replace('[HTML:Folder:{}:AbsoluteRoot]'.format(i), FolderRoots[i])
	for i in Categories:
		HTML = HTML.replace('<span>[HTML:Category:{}]</span>'.format(i), Categories[i])

	# TODO: Clean this doubling?
	ContentHTML = Content
	ContentHTML = ContentHTML.replace('[HTML:Site:AbsoluteRoot]', SiteRoot)
	ContentHTML = ContentHTML.replace('[HTML:Site:RelativeRoot]', GetLevels(PagePath))
	for i in FolderRoots:
		ContentHTML = ContentHTML.replace('[HTML:Folder:{}:AbsoluteRoot]'.format(i), FolderRoots[i])
	for i in Categories:
		ContentHTML = ContentHTML.replace('<span>[HTML:Category:{}]</span>'.format(i), Categories[i])
	SlimHTML = HTMLPagesList + ContentHTML

	return HTML, ContentHTML, SlimHTML, Description, Image

def OrderPages(Old):
	New = []
	NoOrder = []
	Max = 0
	for i,e in enumerate(Old):
		Curr = e[3]['Order']
		if Curr:
			if Curr > Max:
				Max = Curr
		else:
			NoOrder += [e]
	for i in range(Max+1):
		New += [[]]
	for i,e in enumerate(Old):
		Curr = e[3]['Order']
		if Curr:
			New[Curr] = e
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

def GetHTMLPagesList(Pages, SiteRoot, PathPrefix, Type='Page', Category=None, For='Menu'):
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
	for File, Content, Titles, Meta in IndexPages:
		if Meta['Type'] == Type and CanIndex(Meta['Index'], For) and GetTitle(Meta, Titles, Prefer='HTMLTitle') != 'Untitled' and (not Category or Category in Meta['Categories']):
			n = File.count('/') + 1
			if n > 1:
				CurParent = File.split('/')[:-1]
				for i,s in enumerate(CurParent):
					if LastParent != CurParent:
						LastParent = CurParent
						Levels = '- ' * (n-1+i)
						if StripExt(File).endswith('index'):
							Title = MakeListTitle(File, Meta, Titles, 'HTMLTitle', SiteRoot, PathPrefix)
						else:
							Title = CurParent[n-2+i]
						List += Levels + Title + '\n'
			if not (n > 1 and StripExt(File).endswith('index')):
				Levels = '- ' * n
				Title = MakeListTitle(File, Meta, Titles, 'HTMLTitle', SiteRoot, PathPrefix)
				List += Levels + Title + '\n'
	return markdown(List)

def DelTmp():
	for Ext in Extensions['Pages']:
		for File in Path('public').rglob('*.{}'.format(Ext)):
			os.remove(File)
	for Dir in ('public', 'public.gmi'):
		for File in Path(Dir).rglob('*.tmp'):
			os.remove(File)

def RevSort(List):
	List.sort()
	List.reverse()
	return List

def DoMinify(HTML):
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

def MakeSite(TemplatesText, PartsText, ContextParts, ContextPartsText, SiteName, SiteTagline, SiteDomain, SiteRoot, FolderRoots, Locale, Minify, Sorting, MarkdownExts):
	PagesPaths, PostsPaths, Pages, MadePages, Categories = [], [], [], [], {}
	for Ext in Extensions['Pages']:
		for File in Path('Pages').rglob('*.{}'.format(Ext)):
			PagesPaths += [FileToStr(File, 'Pages/')]
		for File in Path('Posts').rglob('*.{}'.format(Ext)):
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
			Content, Titles, Meta = Preprocessor('{}s/{}'.format(Type, File), SiteRoot)
			if Type != 'Page':
				File = Type + 's/' + File
			if not Meta['Type']:
				Meta['Type'] = Type
			Pages += [[File, Content, Titles, Meta]]
			for Category in Meta['Categories']:
				Categories.update({Category:''})
	PugCompileList(Pages)

	if Categories:
		print("[I] Generating Category Lists")
		for Category in Categories:
			Categories[Category] = GetHTMLPagesList(
				Pages=Pages,
				SiteRoot=SiteRoot,
				PathPrefix=GetLevels('Categories/'),
				Type='Page',
				Category=Category,
				For='Categories')
			Categories[Category] += GetHTMLPagesList(
				Pages=Pages,
				SiteRoot=SiteRoot,
				PathPrefix=GetLevels('Categories/'),
				Type='Post',
				Category=Category,
				For='Categories')

	print("[I] Writing Pages")
	for File, Content, Titles, Meta in Pages:
		HTMLPagesList = GetHTMLPagesList(
			Pages=Pages,
			SiteRoot=SiteRoot,
			PathPrefix=GetLevels(File),
			Type='Page',
			For='Menu')
		PagePath = 'public/{}.html'.format(StripExt(File))
		if File.endswith('.md'):
			Content = markdown(Content, extensions=MarkdownExts)
		elif File.endswith('.pug'):
			Content = ReadFile(PagePath)
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
			FolderRoots=FolderRoots,
			Categories=Categories,
			Locale=Locale)
		if Minify not in ('False', 'None'):
			HTML = DoMinify(HTML)
		WriteFile(PagePath, HTML)
		MadePages += [[File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image]]

	return MadePages

def SetSorting(Sorting):
	Default = {
		'Pages':'Standard',
		'Posts':'Inverse'}
	for i in Default:
		if i not in Sorting:
			Sorting.update({i:Default[i]})
	return Sorting

def Main(Args, FeedEntries):
	SiteName = Args.SiteName if Args.SiteName else ''
	SiteTagline = Args.SiteTagline if Args.SiteTagline else ''
	SiteDomain = Args.SiteDomain.rstrip('/') if Args.SiteDomain else ''
	SiteLang = Args.SiteLang if Args.SiteLang else 'en'
	Locale = LoadLocale(SiteLang)
	MastodonURL = Args.MastodonURL if Args.MastodonURL else ''
	MastodonToken = Args.MastodonToken if Args.MastodonToken else ''

	ResetPublic()
	if os.path.isdir('Pages'):
		shutil.copytree('Pages', 'public')
		if Args.GemtextOut:
			shutil.copytree('Pages', 'public.gmi', ignore=IgnoreFiles)
	if os.path.isdir('Posts'):
		shutil.copytree('Posts', 'public/Posts')
		if Args.GemtextOut:
			shutil.copytree('Posts', 'public.gmi/Posts', ignore=IgnoreFiles)

	print("[I] Generating HTML")
	Pages = MakeSite(
		TemplatesText=LoadFromDir('Templates', '*.html'),
		PartsText=LoadFromDir('Parts', '*.html'),
		ContextParts=literal_eval(Args.ContextParts) if Args.ContextParts else {},
		ContextPartsText=LoadFromDir('ContextParts', '*.html'),
		SiteName=SiteName,
		SiteTagline=SiteTagline,
		SiteDomain=SiteDomain,
		SiteRoot=Args.SiteRoot if Args.SiteRoot else '/',
		FolderRoots=literal_eval(Args.FolderRoots) if Args.FolderRoots else {},
		Locale=Locale,
		Minify=Args.Minify if Args.Minify else 'None',
		Sorting=SetSorting(literal_eval(Args.ContextParts) if Args.ContextParts else {}),
		MarkdownExts=literal_eval(Args.MarkdownExts) if Args.MarkdownExts else ['attr_list', 'def_list', 'markdown_del_ins', 'mdx_subscript', 'mdx_superscript'])

	if FeedEntries != 0:
		print("[I] Generating Feeds")
		MakeFeed(
			Pages=Pages,
			SiteName=SiteName,
			SiteTagline=SiteTagline,
			SiteDomain=SiteDomain,
			MaxEntries=FeedEntries,
			Lang=SiteLang,
			Minify=True if Args.Minify and Args.Minify not in ('False', 'None') else False)

	if ActivityPub and MastodonURL and MastodonToken and SiteDomain:
		print("[I] Mastodon Stuff")
		MastodonPosts = MastodonShare(
			MastodonURL,
			MastodonToken,
			Pages,
			SiteDomain,
			SiteLang,
			Locale)
	else:
		MastodonPosts = []

	for File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image in Pages:
		File = 'public/{}.html'.format(StripExt(File))
		Content = ReadFile(File)
		Post = ''
		for p in MastodonPosts:
			if p['Link'] == SiteDomain + '/' + File[len('public/'):]:
				Post = '<br><h3>{StrComments}</h3><a href="{URL}" rel="noopener" target="_blank">{StrOpen} ↗️</a>'.format(
					StrComments=Locale['Comments'],
					StrOpen=Locale['OpenInNewTab'],
					URL=p['Post'])
				break
		Content = Content.replace('[HTML:Comments]', Post)
		WriteFile(File, Content)

	if Args.GemtextOut:
		print("[I] Generating Gemtext")
		GemtextCompileList(
			Pages,
			Header=Args.GemtextHeader if Args.GemtextHeader else '# {}\n\n'.format(SiteName) if SiteName else '')

	DelTmp()
	os.system("cp -R Assets/* public/")
	print("[I] Done!")

if __name__ == '__main__':
	Parser = argparse.ArgumentParser()
	Parser.add_argument('--Minify', type=str)
	Parser.add_argument('--Sorting', type=str)
	Parser.add_argument('--SiteLang', type=str)
	Parser.add_argument('--SiteRoot', type=str)
	Parser.add_argument('--SiteName', type=str)
	Parser.add_argument('--SiteDomain', type=str)
	Parser.add_argument('--GemtextOut', type=bool)
	Parser.add_argument('--GemtextHeader', type=str)
	Parser.add_argument('--SiteTagline', type=str)
	Parser.add_argument('--FeedEntries', type=int)
	Parser.add_argument('--FolderRoots', type=str)
	Parser.add_argument('--ContextParts', type=str)
	Parser.add_argument('--MarkdownExts', type=str)
	Parser.add_argument('--MastodonURL', type=str)
	Parser.add_argument('--MastodonToken', type=str)
	Args = Parser.parse_args()

	try:
		import lxml
		from Modules.Feed import *
		FeedEntries = Args.FeedEntries if Args.FeedEntries or Args.FeedEntries == 0 else 10
	except:
		print("[E] Can't load the Atom/RSS feed libraries. Their generation is disabled.")
		FeedEntries = 0

	Main(
		Args=Args,
		FeedEntries=FeedEntries)
