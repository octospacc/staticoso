#!/usr/bin/env python3
""" ================================= |
| staticoso                           |
| Just a simple Static Site Generator |
| Licensed under AGPLv3 by OctoSpacc  |
| ================================= """

import os
#import pypugjs
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
	return Str

def FormatTitles(Titles):
	HTMLTitles = ''
	for t in Titles:
		n = t.split(' ')[0].count('#')
		Heading = '\-'*n + ' '
		t = t.lstrip('#')
		HTMLTitles += Heading + t + '  \n'
	return Markdown().convert(HTMLTitles)

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
		'Style': ''}
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
			else:
				Content += l + '\n'
				if ls.startswith(('h1', 'h2', 'h3', 'h4', 'h5', 'h6')):
					if not ls.startswith(("h1(class='NoTitle", 'h1(class="NoTitle')):
						Titles += ['#'*int(ls[1]) + str(ls[3:])]
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
			else:
				Content += l + '\n'
				Heading = ls.split(' ')[0].count('#')
				if Heading > 0:
					Titles += [ls]
	return Content, Titles, Meta

def PugCompileList(Pages):
	Paths = ''
	for File, Content, Titles, Meta in Pages:
		Paths += '"public/' + File + '" '
	os.system('pug {} > /dev/null'.format(Paths))
"""
	WriteFile('tmp.pug', c)
	os.system('pug tmp.pug > /dev/null')
	return ReadFile('tmp.html')
"""

def PatchHTML(Template, Parts, Content, Titles, Meta):
	HTMLTitles = FormatTitles(Titles)

	Template = Template.replace('[HTML:Page:Title]', 'Untitled' if not Titles else Titles[0].lstrip('#'))
	Template = Template.replace('[HTML:Page:Style]', Meta['Style'])
	Template = Template.replace('[HTML:Page:RightBox]', HTMLTitles)
	Template = Template.replace('[HTML:Page:MainBox]', Content)

	for p in Parts:
		Template = Template.replace('[HTML:Part:{}]'.format(p), Parts[p])
	return Template

def DelTmp():
	for File in Path('public').rglob('*.pug'):
		os.remove(File)
	for File in Path('public').rglob('*.md'):
		os.remove(File)

def MakeSite(Templates, Parts):
	Pages = []
	for File in Path('Pages').rglob('*.pug'):
		File = str(File)[len('Pages/'):]
		Content, Titles, Meta = PreProcessor('Pages/{}'.format(File))
		Pages += [[File, Content, Titles, Meta]]
	PugCompileList(Pages)
	for File, Content, Titles, Meta in Pages:
		Template = Templates[Meta['Template']]
		Template = Template.replace(
			'[HTML:Page:CSS]',
			'{}{}.css'.format('../'*File.count('/'), Meta['Template'][:-5]))
		WriteFile(
			'public/{}.html'.format(File.rstrip('.pug')),
			PatchHTML(
				Template, Parts,
				ReadFile('public/{}.html'.format(File.rstrip('.pug'))),
				#pypugjs.Compiler(pypugjs.Parser(Content).parse()).compile(),
				Titles, Meta))
	for File in Path('Pages').rglob('*.md'):
		File = str(File)[len('Pages/'):]
		Content, Titles, Meta = PreProcessor('Pages/{}'.format(File))
		Template = Templates[Meta['Template']]
		Template = Template.replace(
			'[HTML:Page:CSS]',
			'{}{}.css'.format('../'*File.count('/'), Meta['Template'][:-5]))
		WriteFile(
			'public/{}.html'.format(File.rstrip('.md')), 
			PatchHTML(
				Template, Parts,
				Markdown().convert(Content),
				Titles, Meta))
	DelTmp()

def Main():
	ResetPublic()
	Templates = LoadFromDir('Templates')
	Parts = LoadFromDir('Parts')
	shutil.copytree('Pages', 'public')
	MakeSite(Templates, Parts)
	os.system("cp -R Assets/* public/")

if __name__ == '__main__':
	Main()
