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

"""
ClosedTags = (
	'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
	'p', 'span', 'pre', 'code',
	'a', 'b', 'i', 'del', 'strong',
	'div', 'details', 'summary',
	'ol', 'ul', 'li', 'dl', 'dt', 'dd')
OpenTags = (
	'img')
"""

def StripAttrs(HTML):
	Soup = BeautifulSoup(HTML, 'html.parser')
	Tags = Soup.find_all()
	for t in Tags:
		if 'href' not in t.attrs and 'src' not in t.attrs:
			t.attrs = {}
	return str(Soup)

def GemtextCompileList(Pages, Header):
	Cmd = ''
	for File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image in Pages:
		if Header:
			SlimHTML = Header + SlimHTML
		Src = 'public.gmi/{}.html.tmp'.format(StripExt(File))
		SlimHTML = StripAttrs(SlimHTML)
		for i in ('ol', 'ul', 'li'):
			for j in ('<'+i+'>', '</'+i+'>'):
				SlimHTML = SlimHTML.replace(j, '')
		WriteFile(Src, SlimHTML.replace('</a>', '</a><br>').replace('.html', '.gmi')) # TODO: Adjust links properly..
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

"""
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
"""
