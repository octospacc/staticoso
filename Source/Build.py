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
		'HTMLTitle': '',
		'Order': None}
	for l in File.splitlines():
		ls = l.lstrip()
		if ls.startswith('// '):
			lss = ls[3:]
			for Item in ['Template', 'Index', 'Title', 'HTMLTitle']:
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

def PatchHTML(Template, Parts, HTMLPagesList, Content, Titles, Meta, SiteRoot):
	HTMLTitles = FormatTitles(Titles)
	for p in Parts:
		Template = Template.replace('[HTML:Part:{}]'.format(p), Parts[p])
	Template = Template.replace('[HTML:Site:AbsoluteRoot]', SiteRoot)
	Template = Template.replace('[HTML:Page:LeftBox]', HTMLPagesList)
	Template = Template.replace('[HTML:Page:RightBox]', HTMLTitles)
	Template = Template.replace('[HTML:Page:Title]', GetTitle(Meta, Titles, 'MetaTitle'))
	Template = Template.replace('[HTML:Page:Style]', Meta['Style'])
	Template = Template.replace('[HTML:Page:MainBox]', Content)
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

def GetHTMLPagesList(Pages, SiteRoot):
	List = ''
	LastParent = []
	IndexPages = Pages.copy()
	for e in IndexPages:
		if e[3]['Index'] == 'False':
			IndexPages.remove(e)
	IndexPages = OrderPages(IndexPages)
	for File, Content, Titles, Meta in IndexPages:
		if Meta['Index'] == 'True' and GetTitle(Meta, Titles, Prefer='HTMLTitle') != 'Untitled':
			n = File.count('/') + 1
			if n > 1:
				CurParent = File.split('/')[:-1]
				for i,s in enumerate(CurParent):
					if LastParent != CurParent:
						LastParent = CurParent
						Levels = '- ' * (n-1+i)
						if File[:-3].endswith('index.'):
							Title = GetTitle(Meta, Titles, 'HTMLTitle')
							Title = '[{}]({})'.format(
								Title,
								'{}{}html'.format(SiteRoot, File[:-3]))
						else:
							Title = CurParent[n-2+i]
						List += Levels + Title + '\n'
			if not (n > 1 and File[:-3].endswith('index.')):
				Levels = '- ' * n
				Title = GetTitle(Meta, Titles, 'HTMLTitle')
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
	
