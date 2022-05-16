#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
from Libs.markdown import Markdown

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

def FormatTitles(Titles):
	HTMLTitles = ''
	for t in Titles:
		Heading = '- ' * (t.split(' ')[0].count('#')-1)
		t = t.lstrip('#')
		HTMLTitles += Heading + t + '  \n'
	return Markdown().convert(HTMLTitles)

def LoadFromDir(Dir):
	Contents = {}
	for File in Path(Dir).rglob('*.html'):
		File = str(File)[len(Dir)+1:]
		Contents.update({File: ReadFile('{}/{}'.format(Dir, File))})
	return Contents

def PreProcessor(File):
	File = ReadFile(File)
	Content, Titles, Meta = '', [], {
		'Template': 'Standard.html',
		'Style': ''}
	for l in File.splitlines():
		ls = l.lstrip()
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

def PatchHTML(Template, Parts, Content, Titles, Meta):
	HTMLTitles = FormatTitles(Titles)

	Template = Template.replace('[HTML:Page:Title]', 'Untitled' if not Titles else Titles[0].lstrip('#'))
	Template = Template.replace('[HTML:Page:Style]', Meta['Style'])
	Template = Template.replace('[HTML:Page:RightBox]', HTMLTitles)
	Template = Template.replace('[HTML:Page:MainBox]', Content)

	for p in Parts:
		Template = Template.replace('[HTML:Part:{}]'.format(p), Parts[p])
	print(Template)
	return Template

def MakeSite(Templates, Parts):
	Pages = []
	for File in Path('Pages').rglob('*.md'):
		File = str(File)[len('Pages/'):]
		Content, Titles, Meta = PreProcessor('Pages/{}'.format(File))

		Template = Templates[Meta['Template']]
		Template = Template.replace(
			'[HTML:Page:CSS]',
			'{}{}.css'.format('../'*File.count('/'), Meta['Template'][:-5]))

		print(Content, Titles, Meta)
		WriteFile(
			'public/{}.html'.format(File.rstrip('.md')), 
			PatchHTML(
				Template,
				Parts,
				Markdown().convert(Content),
				Titles,
				Meta))

def IgnoreFiles(dir, files):
    return [f for f in files if os.path.isfile(os.path.join(dir, f))]
def CopyAssets():
	shutil.copytree('Pages', 'public', ignore=IgnoreFiles)
	os.system("cp -R Assets/* public/")

def Main():
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	ResetPublic()
	Templates = LoadFromDir('Templates')
	Parts = LoadFromDir('Parts')
	print(Templates, Parts)
	CopyAssets()
	MakeSite(Templates, Parts)

if __name__ == '__main__':
	Main()
