#!/usr/bin/env python3
""" ================================= |
| staticoso                           |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
| Copyright (C) 2022, OctoSpacc       |
| ================================= """

import argparse
import json
from Libs import htmlmin
import os
import shutil
from ast import literal_eval
from markdown import Markdown
from pathlib import Path

Extensions = {
	'Pages': ('md', 'pug')}

def ReadFile(p):
	try:
		with open(p, 'r') as f:
			return f.read()
	except Exception:
		print("Error reading file {}".format(p))
		return None

def WriteFile(p, c):
	try:
		with open(p, 'w') as f:
			f.write(c)
		return True
	except Exception:
		print("Error writing file {}".format(p))
		return False

def LoadLocale(Lang):
	Lang = Lang + '.json'
	Folder = os.path.dirname(os.path.abspath(__file__)) + '/../Locale/'
	File = ReadFile(Folder + Lang)
	if File:
		return json.loads(File)
	else:
		return json.loads(ReadFile(Folder + 'en.json'))

def StripExt(Path):
	return ".".join(Path.split('.')[:-1])

def ResetPublic():
	try:
		shutil.rmtree('public')
	except FileNotFoundError:
		pass

def GetLevels(Path, Sub=0, AsNum=False):
	n = Path.count('/')
	return n if AsNum else '../' * n

def DashifyStr(s, Limit=32):
	Str, lc = '', Limit
	for c in s[:Limit].replace(' ','-').replace('	','-'):
		if c.lower() in '0123456789qwfpbjluyarstgmneiozxcdvkh-':
			Str += c
	return '-' + Str

def GetTitle(Meta, Titles, Prefer='MetaTitle'):
	if Prefer == 'Title':
		Title = Titles[0].lstrip('#') if Titles else Meta['Title'] if Meta['Title'] else 'Untitled'
	elif Prefer == 'MetaTitle':
		Title = Meta['Title'] if Meta['Title'] else Titles[0].lstrip('#') if Titles else 'Untitled'
	elif Prefer == 'HTMLTitle':
		Title = Meta['HTMLTitle'] if Meta['HTMLTitle'] else Meta['Title'] if Meta['Title'] else Titles[0].lstrip('#') if Titles else 'Untitled'
	if Meta['Type'] == 'Post':
		# TODO: This hardcodes my blog name, bad, will fix asap
		Title += ' - blogoctt'
	return Title

def GetDescription(Meta, Prefer='MetaDescription'):
	if Prefer == 'Description':
		Description = Meta['Description']
	elif Prefer == 'MetaDescription':
		Description = Meta['Description']
	return Description

def GetTitleIdLine(Line, Title, Type):
	DashTitle = DashifyStr(Title.lstrip('#'))
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
	MDTitles = ''
	for t in Titles:
		n = t.split(' ')[0].count('#')
		Heading = '- ' * n
		Title = t.lstrip('#')
		Title = '[{}](#{})'.format(Title, DashifyStr(Title))
		MDTitles += Heading + Title + '\n'
	return Markdown().convert(MDTitles)

def LoadFromDir(Dir, Rglob):
	Contents = {}
	for File in Path(Dir).rglob(Rglob):
		File = str(File)[len(Dir)+1:]
		Contents.update({File: ReadFile('{}/{}'.format(Dir, File))})
	return Contents

def PreProcessor(Path, SiteRoot):
	File = ReadFile(Path)
	Content, Titles, Meta = '', [], {
		'Template': 'Standard.html',
		'Style': '',
		'Type': 'Page',
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
					Titles += [l]
					Content += GetTitleIdLine(l, ls, 'md') + '\n'
				else:
					Content += l + '\n'
			elif Path.endswith('.pug'):
				if ls.startswith(('h1', 'h2', 'h3', 'h4', 'h5', 'h6')):
					if ls[2:].startswith(("(class='NoTitle", '(class="NoTitle')):
						Content += l + '\n'
					else:
						Title = '#'*int(ls[1]) + str(ls[3:])
						Titles += [Title]
						# We should handle headers that for any reason already have parenthesis
						if ls[2:] == '(':
							Content += l + '\n'
						else:
							Content += GetTitleIdLine(l, Title, 'pug') + '\n'
				else:
					Content += l + '\n'
	return Content, Titles, Meta

def PugCompileList(Pages):
	# Pug-cli seems to shit itself with folder paths as input, so we pass ALL the files as arguments
	Paths = ''
	for File, Content, Titles, Meta in Pages:
		if File.endswith('.pug'):
			Path = 'public/{}'.format(File)
			WriteFile(Path, Content)
			Paths += '"{}" '.format(Path)
	os.system('pug -P {} > /dev/null'.format(Paths))

def MakeContentHeader(Meta, Locale):
	Header = ''
	if Meta['Type'] == 'Post':
		if Meta['CreatedOn']:
			Header += "{} {}  \n".format(Locale['CreatedOn'], Meta['CreatedOn'])
		if Meta['EditedOn']:
			Header += "{} {}  \n".format(Locale['EditedOn'], Meta['EditedOn'])
	return Markdown().convert(Header)

def PatchHTML(Template, PartsText, ContextParts, ContextPartsText, HTMLPagesList, PagePath, Content, Titles, Meta, SiteRoot, FolderRoots, Categories, Locale):
	HTMLTitles = FormatTitles(Titles)
	for Line in Template.splitlines():
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
			Template = Template.replace('[HTML:ContextPart:{}]'.format(Path), Text)
	for i in PartsText:
		Template = Template.replace('[HTML:Part:{}]'.format(i), PartsText[i])
	Template = Template.replace('[HTML:Page:LeftBox]', HTMLPagesList)
	Template = Template.replace('[HTML:Page:RightBox]', HTMLTitles)
	Template = Template.replace('[HTML:Page:Title]', GetTitle(Meta, Titles, 'MetaTitle'))
	Template = Template.replace('[HTML:Page:Description]', GetDescription(Meta, 'MetaDescription'))
	Template = Template.replace('[HTML:Page:Path]', PagePath)
	Template = Template.replace('[HTML:Page:Style]', Meta['Style'])
	Template = Template.replace('[HTML:Page:Content]', Content)
	Template = Template.replace('[HTML:Page:ContentHeader]', MakeContentHeader(Meta, Locale))
	Template = Template.replace('[HTML:Site:AbsoluteRoot]', SiteRoot)
	Template = Template.replace('[HTML:Site:RelativeRoot]', GetLevels(PagePath))
	for i in FolderRoots:
		Template = Template.replace('[HTML:Folder:{}:AbsoluteRoot]'.format(i), FolderRoots[i])
	for i in Categories:
		Template = Template.replace('<span>[HTML:Category:{}]</span>'.format(i), Categories[i])
	return Template

def FileToStr(File, Truncate=''):
	return str(File)[len(Truncate):]

def OrderPages(Old):
	New = []
	Max = 0
	for i,e in enumerate(Old):
		Curr = e[3]['Order']
		if Curr > Max:
			Max = Curr
	for i in range(Max+1):
		New += [[]]
	for i,e in enumerate(Old):
		New[e[3]['Order']] = e
	while [] in New:
		New.remove([])
	return New

def GetHTMLPagesList(Pages, SiteRoot, PathPrefix, Type='Page', Category=None):
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
		if Meta['Type'] == Type and (Meta['Index'] != 'False' or Meta['Index'] != 'None') and GetTitle(Meta, Titles, Prefer='HTMLTitle') != 'Untitled' and (not Category or Category in Meta['Categories']):
			n = File.count('/') + 1
			if n > 1:
				CurParent = File.split('/')[:-1]
				for i,s in enumerate(CurParent):
					if LastParent != CurParent:
						LastParent = CurParent
						Levels = '- ' * (n-1+i)
						if File[:-3].endswith('index.'):
							Title = MakeListTitle(File, Meta, Titles, 'HTMLTitle', SiteRoot, PathPrefix)
						else:
							Title = CurParent[n-2+i]
						List += Levels + Title + '\n'
			if not (n > 1 and File[:-3].endswith('index.')):
				Levels = '- ' * n
				Title = MakeListTitle(File, Meta, Titles, 'HTMLTitle', SiteRoot, PathPrefix)
				List += Levels + Title + '\n'
	return Markdown().convert(List)

def DelTmp():
	for Ext in Extensions['Pages']:
		for File in Path('public').rglob('*.{}'.format(Ext)):
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

def MakeSite(TemplatesText, PartsText, ContextParts, ContextPartsText, SiteRoot, FolderRoots, Locale, Minify):
	Files, Pages, Categories = [], [], {}
	for Ext in Extensions['Pages']:
		for File in Path('Pages').rglob('*.{}'.format(Ext)):
			Files += [FileToStr(File, 'Pages/')]
	Files = RevSort(Files)
	for File in Files:
		Content, Titles, Meta = PreProcessor('Pages/{}'.format(File), SiteRoot)
		Pages += [[File, Content, Titles, Meta]]
		for Category in Meta['Categories']:
			Categories.update({Category:''})
	PugCompileList(Pages)
	for Category in Categories:
		Categories[Category] = GetHTMLPagesList(
			Pages=Pages,
			SiteRoot=SiteRoot,
			PathPrefix='../../', # This hardcodes paths, TODO make it somehow guess the path for every page containing the [HTML:Category] macro
			Type='Post',
			Category=Category)
	for File, Content, Titles, Meta in Pages:
		HTMLPagesList = GetHTMLPagesList(
			Pages=Pages,
			SiteRoot=SiteRoot,
			PathPrefix=GetLevels(File),
			Type='Page')
		PagePath = 'public/{}.html'.format(StripExt(File))
		if File.endswith('.md'):
			Content = Markdown().convert(Content)
		elif File.endswith('.pug'):
			Content = ReadFile(PagePath)
		HTML = PatchHTML(
			Template=TemplatesText[Meta['Template']],
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
		if Minify != 'False' and Minify != 'None':
			HTML = DoMinify(HTML)
		WriteFile(PagePath, HTML)
	DelTmp()

def Main(Args):
	ResetPublic()
	shutil.copytree('Pages', 'public')
	MakeSite(
		TemplatesText=LoadFromDir('Templates', '*.html'),
		PartsText=LoadFromDir('Parts', '*.html'),
		ContextParts=literal_eval(Args.ContextParts) if Args.ContextParts else {},
		ContextPartsText=LoadFromDir('ContextParts', '*.html'),
		SiteRoot=Args.SiteRoot if Args.SiteRoot else '/',
		FolderRoots=literal_eval(Args.FolderRoots) if Args.FolderRoots else {},
		Locale=LoadLocale(Args.SiteLang if Args.SiteLang else 'en'),
		Minify=Args.Minify if Args.Minify else 'None')
	os.system("cp -R Assets/* public/")

if __name__ == '__main__':
	Parser = argparse.ArgumentParser()
	Parser.add_argument('--SiteLang', type=str)
	Parser.add_argument('--SiteRoot', type=str)
	Parser.add_argument('--FolderRoots', type=str)
	Parser.add_argument('--ContextParts', type=str)
	Parser.add_argument('--Minify', type=str)
	Main(
		Args=Parser.parse_args())
