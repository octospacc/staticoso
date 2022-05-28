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

def GetTitleIdLine(Line, Title):
	Title = DashifyStr(Title.lstrip('#'))
	Index = Line.find('h')
	NewLine = ''
	NewLine += Line[:Index]
	NewLine += "{}(id='{}')".format(Line[Index:Index+2], Title)
	NewLine += Line[Index+2:]
	return NewLine

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
		'Index': 'True',
		'Title': '',
		'Order': None}
	for l in File.splitlines():
		ls = l.lstrip()
		if ls.startswith('//'):
			if ls.startswith('// Template: '):
				Meta['Template'] = ls[len('// Template: '):]
			elif ls.startswith('// Background: '):
				Meta['Style'] += "#MainBox{Background:" + ls[len('// Background: '):] + ";} "
			elif ls.startswith('// Style: '):
				Meta['Style'] += ls[len('// Style: '):] + ' '
			elif ls.startswith('// Index: '):
				Meta['Index'] = ls[len('// Index: '):]
			elif ls.startswith('// Title: '):
				Meta['Title'] = ls[len('// Title: '):]
			elif ls.startswith('// Order: '):
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
	Paths = ''
	for File, Content, Titles, Meta in Pages:
		FilePath = 'public/{}'.format(File)
		WriteFile(FilePath, Content)
		Paths += '"{}" '.format(FilePath)
	# Pug-cli seems to shit itself with folder paths as input, so we pass ALL the files as arguments
	os.system('pug {} > /dev/null'.format(Paths))

def PatchHTML(Template, Parts, HTMLPagesList, Content, Titles, Meta, SiteRoot):
	HTMLTitles = FormatTitles(Titles)

	Template = Template.replace('[HTML:Page:Title]', 'Untitled' if not Titles else Titles[0].lstrip('#'))
	Template = Template.replace('[HTML:Page:Style]', Meta['Style'])
	Template = Template.replace('[HTML:Page:LeftBox]', HTMLPagesList)
	Template = Template.replace('[HTML:Page:RightBox]', HTMLTitles)
	Template = Template.replace('[HTML:Page:MainBox]', Content)

	for p in Parts:
		Template = Template.replace('[HTML:Site:AbsoluteRoot]', SiteRoot)
		Template = Template.replace('[HTML:Part:{}]'.format(p), Parts[p])
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

def GetHTMLPagesList(Pages, SiteRoot):
	List = ''
	LastParent = []
	Pages = OrderPages(Pages)
	for File, Content, Titles, Meta in Pages:
		if Meta['Index'] == 'True' and Titles:
			n = File.count('/') + 1
			if n > 1:
				CurParent = File.split('/')[:-1]
				for i,s in enumerate(CurParent):
					if LastParent != CurParent:
						LastParent = CurParent
						Levels = '- ' * (n-1+i)
						Title = CurParent[n-2+i]
						List += Levels + Title + '\n'
			Levels = '- ' * n
			Title = Meta['Title'] if Meta['Title'] else 'Untitled' if not Titles else Titles[0].lstrip('#')
			Title = '[{}]({})'.format(
				Title,
				'{}{}html'.format(SiteRoot, File[:-3]))
			List += Levels + Title + '\n'
	return Markdown().convert(List)

def DelTmp():
	for File in Path('public').rglob('*.pug'):
		os.remove(File)
	for File in Path('public').rglob('*.md'):
		os.remove(File)

def MakeSite(Templates, Parts, SiteRoot):
	Pages = []
	for File in Path('Pages').rglob('*.pug'):
		File = FileToStr(File, 'Pages/')
		Content, Titles, Meta = PreProcessor('Pages/{}'.format(File), SiteRoot)
		Pages += [[File, Content, Titles, Meta]]
	PugCompileList(Pages)
	HTMLPagesList = GetHTMLPagesList(Pages, SiteRoot)
	for File, Content, Titles, Meta in Pages:
		Template = Templates[Meta['Template']]
		Template = Template.replace(
			'[HTML:Site:AbsoluteRoot]',
			SiteRoot)
		Template = Template.replace(
			'[HTML:Site:RelativeRoot]',
			'../'*File.count('/'))
		WriteFile(
			'public/{}html'.format(File[:-3]),
			PatchHTML(
				Template, Parts, HTMLPagesList,
				ReadFile('public/{}html'.format(File[:-3])),
				Titles, Meta, SiteRoot))
	for File in Path('Pages').rglob('*.md'):
		File = FileToStr(File, 'Pages/')
		Content, Titles, Meta = PreProcessor('Pages/{}'.format(File), SiteRoot)
		Template = Templates[Meta['Template']]
		Template = Template.replace(
			'[HTML:Site:AbsoluteRoot]',
			SiteRoot)
		Template = Template.replace(
			'[HTML:Site:RelativeRoot]',
			'../'*File.count('/'))
		WriteFile(
			'public/{}html'.format(File[:-2]),
			PatchHTML(
				Template, Parts, HTMLPagesList,
				Markdown().convert(Content),
				Titles, Meta, SiteRoot))
	DelTmp()

def Main(Args):
	ResetPublic()
	SiteRoot = Args.SiteRoot if Args.SiteRoot else '/'

	Templates = LoadFromDir('Templates', '*.html')
	Parts = LoadFromDir('Parts', '*.html')
	shutil.copytree('Pages', 'public')
	MakeSite(Templates, Parts, SiteRoot)
	os.system("cp -R Assets/* public/")

if __name__ == '__main__':
	Parser = argparse.ArgumentParser()
	Parser.add_argument('--SiteRoot', type=str)
	Args = Parser.parse_args()

	Main(Args)
