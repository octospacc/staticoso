#!/usr/bin/env python3
""" ================================= |
| staticoso                           |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
| Copyright (C) 2022, OctoSpacc       |
| ================================= """

import argparse
import os
import shutil
from ast import literal_eval
from markdown import Markdown
from pathlib import Path

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

def ResetPublic():
	try:
		shutil.rmtree('public')
	except FileNotFoundError:
		pass

def DashifyStr(s, Limit=32):
	Str, lc = '', Limit
	for c in s[:Limit].replace(' ','-').replace('	','-'):
		if c.lower() in '0123456789qwfpbjluyarstgmneiozxcdvkh-':
			Str += c
	return '-' + Str

def GetTitle(Meta, Titles, Prefer='MetaTitle'):
	if Prefer == 'Title':
		return Titles[0].lstrip('#') if Titles else Meta['Title'] if Meta['Title'] else 'Untitled'
	elif Prefer == 'MetaTitle':
		return Meta['Title'] if Meta['Title'] else Titles[0].lstrip('#') if Titles else 'Untitled'
	elif Prefer == 'HTMLTitle':
		return Meta['HTMLTitle'] if Meta['HTMLTitle'] else Meta['Title'] if Meta['Title'] else Titles[0].lstrip('#') if Titles else 'Untitled'

def GetTitleIdLine(Line, Title):
	Title = DashifyStr(Title.lstrip('#'))
	Index = Line.find('h')
	NewLine = ''
	NewLine += Line[:Index]
	NewLine += "{}(id='{}')".format(Line[Index:Index+2], Title)
	NewLine += Line[Index+2:]
	return NewLine

def MakeListTitle(File, Meta, Titles, Prefer, SiteRoot):
	Title = GetTitle(Meta, Titles, Prefer)
	if Meta['Type'] == 'Post':
		Title = '[{}] [{}]({})'.format(
			Meta['CreatedOn'],
			Title,
			'{}{}html'.format(SiteRoot, File[:-3]))
	else:
		Title = '[{}]({})'.format(
			Title,
			'{}{}html'.format(SiteRoot, File[:-3]))
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

def PreProcessor(p, SiteRoot):
	File = ReadFile(p)
	Content, Titles, Meta = '', [], {
		'Template': 'Standard.html',
		'Style': '',
		'Type': 'Page',
		'Index': 'True',
		'Title': '',
		'HTMLTitle': '',
		'CreatedOn': '',
		'EditedOn': '',
		'Order': None}
	for l in File.splitlines():
		ls = l.lstrip()
		if ls.startswith('// '):
			lss = ls[3:]
			for Item in ['Template', 'Type', 'Index', 'Title', 'HTMLTitle', 'CreatedOn', 'EditedOn']:
				ItemText = '{}: '.format(Item)
				if lss.startswith(ItemText):
					Meta[Item] = lss[len(ItemText):]
			if lss.startswith('Background: '):
				Meta['Style'] += "#MainBox{Background:" + ls[len('// Background: '):] + ";} "
			elif lss.startswith('Style: '):
				Meta['Style'] += ls[len('// Style: '):] + ' '
			elif lss.startswith('Order: '):
				Meta['Order'] = int(ls[len('// Order: '):])
		elif ls.startswith(('h1', 'h2', 'h3', 'h4', 'h5', 'h6')):
			if ls[2:].startswith(("(class='NoTitle", '(class="NoTitle')):
				Content += l + '\n'
			else:
				Title = '#'*int(ls[1]) + str(ls[3:])
				Titles += [Title]
				# We should handle headers that for any reason already have parenthesis
				if ls[2:] == '(':
					Content += l + '\n'
				else:
					Content += GetTitleIdLine(l, Title) + '\n'
		else:
			Content += l + '\n'
	return Content, Titles, Meta

def PugCompileList(Pages):
	# Pug-cli seems to shit itself with folder paths as input, so we pass ALL the files as arguments
	Paths = ''
	for File, Content, Titles, Meta in Pages:
		FilePath = 'public/{}'.format(File)
		WriteFile(FilePath, Content)
		Paths += '"{}" '.format(FilePath)
	os.system('pug {} > /dev/null'.format(Paths))

def PatchHTML(Template, PartsText, ContextParts, ContextPartsText, HTMLPagesList, Content, Titles, Meta, SiteRoot, Macros):
	HTMLTitles = FormatTitles(Titles)
	for Line in Template.splitlines():
		Line = Line.lstrip().rstrip()
		print(ContextPartsText)
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
	Template = Template.replace('[HTML:Page:Style]', Meta['Style'])
	Template = Template.replace('[HTML:Page:MainBox]', Content)
	Template = Template.replace('[HTML:Site:AbsoluteRoot]', SiteRoot)
	for i in Macros:
		Template = Template.replace('<span>[HTML:Macro:{}]</span>'.format(i), Macros[i])
	return Template

def FileToStr(File, Truncate=''):
	return str(File)[len(Truncate):]

def OrderPages(Old):
	New = []
	Max = 0
	#Off = 0
	for i,e in enumerate(Old):
		Curr = e[3]['Order'] #if e[3]['Order'] else 0
		if Curr > Max:
			Max = Curr
	for i in range(Max+1):
		New += [[]]
	for i,e in enumerate(Old):
		#if e[3]['Order']:
		New[e[3]['Order']] = e
		#else:
			#Off += 1
			#New += [[e]]
	while [] in New:
		New.remove([])
	#for i in New:
		#print(i)
	return New

def GetHTMLPagesList(Pages, SiteRoot, Type='Page'):
	List = ''
	LastParent = []
	IndexPages = Pages.copy()
	for e in IndexPages:
		#print(e[3]['Index'])
		if e[3]['Index'] == 'False':
			IndexPages = IndexPages.remove(e)
	#print(IndexPages)
	for i,e in enumerate(IndexPages):
		#print(e[3]['Type'])
		if e[3]['Type'] != Type:
				#print('rem')
				IndexPages.pop(i)
	#print(IndexPages)
	if Type == 'Page':
		IndexPages = OrderPages(IndexPages)
	for File, Content, Titles, Meta in IndexPages:
		if Meta['Type'] == Type and Meta['Index'] == 'True' and GetTitle(Meta, Titles, Prefer='HTMLTitle') != 'Untitled':
			n = File.count('/') + 1
			if n > 1:
				CurParent = File.split('/')[:-1]
				for i,s in enumerate(CurParent):
					if LastParent != CurParent:
						LastParent = CurParent
						Levels = '- ' * (n-1+i)
						if File[:-3].endswith('index.'):
							Title = MakeListTitle(File, Meta, Titles, 'HTMLTitle', SiteRoot)
						else:
							Title = CurParent[n-2+i]
						List += Levels + Title + '\n'
			if not (n > 1 and File[:-3].endswith('index.')):
				Levels = '- ' * n
				Title = MakeListTitle(File, Meta, Titles, 'HTMLTitle', SiteRoot)
				List += Levels + Title + '\n'
	return Markdown().convert(List)

def DelTmp():
	for File in Path('public').rglob('*.pug'):
		os.remove(File)
	for File in Path('public').rglob('*.md'):
		os.remove(File)

def MakeSite(TemplatesText, PartsText, ContextParts, ContextPartsText, SiteRoot):
	Pages = []
	Macros = {
		'BlogPosts': ''}
	for File in Path('Pages').rglob('*.pug'):
		File = FileToStr(File, 'Pages/')
		Content, Titles, Meta = PreProcessor('Pages/{}'.format(File), SiteRoot)
		Pages += [[File, Content, Titles, Meta]]
	PugCompileList(Pages)
	HTMLPagesList = GetHTMLPagesList(Pages, SiteRoot, 'Page')
	#print(GetHTMLPagesList(Pages, SiteRoot, 'Post'))
	Macros['BlogPosts'] = GetHTMLPagesList(Pages, SiteRoot, 'Post')
	for File, Content, Titles, Meta in Pages:
		Template = TemplatesText[Meta['Template']]
		Template = Template.replace(
			'[HTML:Site:AbsoluteRoot]',
			SiteRoot)
		Template = Template.replace(
			'[HTML:Site:RelativeRoot]',
			'../'*File.count('/'))
		WriteFile(
			'public/{}html'.format(File[:-3]),
			PatchHTML(
				Template, PartsText, ContextParts, ContextPartsText, HTMLPagesList,
				ReadFile('public/{}html'.format(File[:-3])),
				Titles, Meta, SiteRoot, Macros))
	for File in Path('Pages').rglob('*.md'):
		File = FileToStr(File, 'Pages/')
		Content, Titles, Meta = PreProcessor('Pages/{}'.format(File), SiteRoot)
		Template = TemplatesText[Meta['Template']]
		Template = Template.replace(
			'[HTML:Site:AbsoluteRoot]',
			SiteRoot)
		Template = Template.replace(
			'[HTML:Site:RelativeRoot]',
			'../'*File.count('/'))
		WriteFile(
			'public/{}html'.format(File[:-2]),
			PatchHTML(
				Template, PartsText, ContextParts, ContextPartsText, HTMLPagesList,
				Markdown().convert(Content),
				Titles, Meta, SiteRoot, Macros))
	DelTmp()

"""
def GetContextPartsText(ContextParts):
	List = {}
	Contents = LoadFromDir('ContextParts', '*.html')
	for i in ContextParts:
		if type(ContextParts[i]) == str:
			if
		elif type(ContextParts[i]) == list:
			
"""

def Main(Args):
	ResetPublic()
	shutil.copytree('Pages', 'public')
	MakeSite(
		LoadFromDir('Templates', '*.html'),
		LoadFromDir('Parts', '*.html'),
		literal_eval(Args.ContextParts) if Args.ContextParts else {},
		LoadFromDir('ContextParts', '*.html'),
		Args.SiteRoot if Args.SiteRoot else '/')
	os.system("cp -R Assets/* public/")

if __name__ == '__main__':
	Parser = argparse.ArgumentParser()
	Parser.add_argument('--SiteRoot', type=str)
	Parser.add_argument('--ContextParts', type=str)
	Args = Parser.parse_args()

	Main(Args)
