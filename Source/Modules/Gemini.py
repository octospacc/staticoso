""" ================================= |
| This file is part of                |
|   staticoso                         |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
|   Copyright (C) 2022, OctoSpacc     |
| ================================= """

# TODO: Write the Python HTML2Gemtext converter

from Libs.bs4 import BeautifulSoup
from Modules.Utils import *

ClosedTags = (
	'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
	'p', 'span', 'pre', 'code',
	'a', 'b', 'i', 'del', 'strong',
	'div', 'details', 'summary',
	'ol', 'ul', 'li', 'dl', 'dt', 'dd')
OpenTags = (
	'img')

def GemtextCompileList(Pages):
	Cmd = ''
	for File, Content, Titles, Meta, HTMLContent, Description, Image in Pages:
		Src = 'public.gmi/{}.html.tmp'.format(StripExt(File))
		WriteFile(Src, HTMLContent.replace('.html', '.gmi')) # TODO: Adjust links properly..
		Dst = 'public.gmi/{}.gmi'.format(StripExt(File))
		Cmd += 'cat "{}" | html2gmi > "{}"; '.format(Src, Dst)
	os.system(Cmd)

def FindEarliest(Str, Items):
	Pos, Item = 0, ''
	for Item in Items:
		Str.find(Item)
	return Pos, Item

def ParseTag(Content):
	print(Content)
	Parse = BeautifulSoup(str(Content), 'html.parser')
	Tag = Parse.find()

def HTML2Gemtext(Pages, SiteName, SiteTagline):
	#os.mkdir('public.gmi')
	for File, Content, Titles, Meta, HTMLContent, Description, Image in Pages:
		Gemtext = ''
		Content = HTMLContent
		print(File)
		while len(Content) != 0:
			BlockStart = Content.find('<')
			TagEnd = Content.find('>')
			Parse = BeautifulSoup(Content, 'html.parser')
			Tag = Parse.find()
			#if Tag.name in ('a'):
			#	if 'href' in Tag.attrs:
			#		pass
			for i in Tag.contents:
				ParseTag(i)
			if Tag.name in ('h1', 'h2', 'h3'):
				Gemtext += '#' * int(Tag.name[1]) + ' '
			elif Tag.name in ('h4', 'h5', 'h6'):
				Gemtext += '### '
			elif Tag.name in ('li'):
				Gemtext += '* '
			Gemtext += str(Tag.get_text()) + '\n\n'
			#print(File, Tag.name, len(Tag.contents))
			if Tag.name in ClosedTags:
				Str = '</{}>'.format(Tag.name)
			elif Tag.name in OpenTags:
				Str = '>'
			BlockEnd = Content.find(Str) + len(Str)
			Content = Content.replace(Content[BlockStart:TagEnd], '').replace(Content[BlockEnd-len(Str):BlockEnd], '')
			#print(BlockStart, TagEnd, BlockEnd, Tag.contents)
			#print(Content[BlockStart:BlockEnd])
			#Gemtext += Content[BlockStart:BlockEnd]
			Content = Content[BlockEnd:]
		PagePath = 'public.gmi/{}.gmi'.format(StripExt(File))
		WriteFile(PagePath, Gemtext)
		#exit()

""" Gemtext:
# h1
## h2
### h3

* li
* li

=> [protocol://]URL Link Description

> Quote

```
Preformatted
```
"""
