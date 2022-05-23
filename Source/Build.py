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

def LoadFromDir(Dir):
	Contents = {}
	for File in Path(Dir).rglob('*.html'):
		File = str(File)[len(Dir)+1:]
		Contents.update({File: ReadFile('{}/{}'.format(Dir, File))})
	return Contents

def PreProcessor(p):
	File = ReadFile(p)
	Content, Titles, Meta = '', [], {
		'Template': 'Standard.html',
		'Style': '',
		'Index': 'True',
		'Title': ''}
	for l in File.splitlines():
		ls = l.lstrip()
		if p.endswith('.pug'):
			if ls.startswith('//'):
				if ls.startswith('// Template: '):
					Meta['Template'] = ls[len('// Template: '):]
				elif ls.startswith('// Background: '):
					Meta['Style'] += "#MainBox{Background:" + ls[len('// Background: '):] + ";} "
				elif ls.startswith('// Style: '):
					Meta['Style'] += ls[len('// Style: '):] + ' '
				elif ls.startswith('// Index: '):
					Meta['Index'] += ls[len('// Index: '):] + ' '
				elif ls.startswith('// Title: '):
					Meta['Title'] += ls[len('// Title: '):] + ' '
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
		elif p.endswith('.md'):
			if ls.startswith('\%'):
				Content += ls[1:] + '\n'
			elif ls.startswith('% - '):
				Content += '<!-- {} -->'.format(ls[4:]) + '\n'
			elif ls.startswith('% Template: '):
				Meta['Template'] = ls[len('% Template: '):]
			elif ls.startswith('% Background: '):
				Meta['Style'] += "#MainBox{Background:" + ls[len('% Background: '):] + ";} "
			elif ls.startswith('% Style: '):
				Meta['Style'] += ls[len('% Style: '):] + ' '
			elif ls.startswith('% Index: '):
					Meta['Index'] += ls[len('% Index: '):] + ' '
			elif ls.startswith('% Title: '):
					Meta['Title'] += ls[len('% Title: '):] + ' '
			else:
				Content += l + '\n'
				Heading = ls.split(' ')[0].count('#')
				if Heading > 0:
					Titles += [ls]
	return Content, Titles, Meta

def PugCompileList(Pages):
	Paths = ''
	for File, Content, Titles, Meta in Pages:
		FilePath = 'public/{}'.format(File)
		WriteFile(FilePath, Content)
		Paths += '"{}" '.format(FilePath)
	# Pug-cli seems to shit itself with folder paths as input, so we pass ALL the files as arguments
	os.system('pug {} > /dev/null'.format(Paths))

def PatchHTML(Template, Parts, HTMLPagesList, Content, Titles, Meta):
	HTMLTitles = FormatTitles(Titles)

	Template = Template.replace('[HTML:Page:Title]', 'Untitled' if not Titles else Titles[0].lstrip('#'))
	Template = Template.replace('[HTML:Page:Style]', Meta['Style'])
	Template = Template.replace('[HTML:Page:LeftBox]', HTMLPagesList)
	Template = Template.replace('[HTML:Page:RightBox]', HTMLTitles)
	Template = Template.replace('[HTML:Page:MainBox]', Content)

	for p in Parts:
		Template = Template.replace('[HTML:Part:{}]'.format(p), Parts[p])
	return Template

def FileToStr(File, Truncate=''):
	return str(File)[len(Truncate):]

def GetHTMLPagesList(Pages, Root):
	List = ''
	LastParent = []
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
				'{}{}.html'.format(Root, File.rstrip('.pug')))
			List += Levels + Title + '\n'
	return Markdown().convert(List)

def DelTmp():
	for File in Path('public').rglob('*.pug'):
		os.remove(File)
	for File in Path('public').rglob('*.md'):
		os.remove(File)

def MakeSite(Templates, Parts, Root):
	Pages = []
	for File in Path('Pages').rglob('*.pug'):
		File = FileToStr(File, 'Pages/')
		Content, Titles, Meta = PreProcessor('Pages/{}'.format(File))
		Pages += [[File, Content, Titles, Meta]]
	PugCompileList(Pages)
	HTMLPagesList = GetHTMLPagesList(Pages, Root)
	for File, Content, Titles, Meta in Pages:
		Template = Templates[Meta['Template']]
		Template = Template.replace(
			'[HTML:Page:CSS]',
			'{}{}.css'.format('../'*File.count('/'), Meta['Template'][:-5]))
		WriteFile(
			'public/{}.html'.format(File.rstrip('.pug')),
			PatchHTML(
				Template, Parts, HTMLPagesList,
				ReadFile('public/{}.html'.format(File.rstrip('.pug'))),
				Titles, Meta))
	for File in Path('Pages').rglob('*.md'):
		File = FileToStr(File, 'Pages/')
		Content, Titles, Meta = PreProcessor('Pages/{}'.format(File))
		Template = Templates[Meta['Template']]
		Template = Template.replace(
			'[HTML:Page:CSS]',
			'{}{}.css'.format('../'*File.count('/'), Meta['Template'][:-5]))
		WriteFile(
			'public/{}.html'.format(File.rstrip('.md')), 
			PatchHTML(
				Template, Parts, HTMLPagesList,
				Markdown().convert(Content),
				Titles, Meta))
	DelTmp()

def Main(Args):
	ResetPublic()
	Root = Args.Root if Args.Root else '/'

	Templates = LoadFromDir('Templates')
	Parts = LoadFromDir('Parts')
	#HTMLPages = SearchIndexedPages()
	shutil.copytree('Pages', 'public')
	MakeSite(Templates, Parts, Root)
	os.system("cp -R Assets/* public/")

if __name__ == '__main__':
	Parser = argparse.ArgumentParser()
	Parser.add_argument('--Root', type=str)
	Args = Parser.parse_args()

	Main(Args)
