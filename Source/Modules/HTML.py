""" ================================= |
| This file is part of                |
|   staticoso                         |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
|   Copyright (C) 2022, OctoSpacc     |
| ================================= """

import html
import warnings
from Libs import htmlmin
from Libs.bs4 import BeautifulSoup
from Modules.Utils import *

# Suppress useless bs4 warnings
warnings.filterwarnings('ignore', message='The input looks more like a filename than markup.')

def MkSoup(HTML):
	return BeautifulSoup(HTML, 'html.parser')

def StripAttrs(HTML):
	Soup = MkSoup(HTML)
	Tags = Soup.find_all()
	for t in Tags:
		if 'href' not in t.attrs and 'src' not in t.attrs:
			t.attrs = {}
	return str(Soup)

def StripTags(HTML, ToStrip): # Remove desired tags from the HTML
	Soup = MkSoup(HTML)
	Tags = Soup.find_all()
	for t in Tags:
		if t.name in ToStrip:
			t.replace_with('')
	return str(Soup)

def DoHTMLFixPre(HTML):
	if not ("<pre>" in HTML or "<pre " in HTML):
		return HTML
	Soup = MkSoup(HTML)
	Tags = Soup.find_all('pre')
	for t in Tags:
		FirstLine = str(t).splitlines()[0].lstrip().rstrip()
		if FirstLine.endswith('>'):
			New = MkSoup(str(t).replace('\n', '', 1))
			t.replace_with(New.pre)
	return str(Soup)

def WriteImgAltAndTitle(HTML, AltToTitle, TitleToAlt): # Adds alt or title attr. to <img> which only have one of them
	Soup = MkSoup(HTML)
	Tags = Soup.find_all('img')
	for t in Tags:
		if AltToTitle and 'alt' in t.attrs and 'title' not in t.attrs:
			t.attrs.update({'title': t.attrs['alt']})
		elif TitleToAlt and 'title' in t.attrs and 'alt' not in t.attrs:
		    t.attrs.update({'alt': t.attrs['title']})
	return str(Soup)

def AddToTagStartEnd(HTML, MatchStart, MatchEnd, AddStart, AddEnd): # This doesn't handle nested tags
	StartPos = None
	for i,e in enumerate(HTML):
		FilterStart = HTML[i:i+len(MatchStart)]
		FilterEnd = HTML[i:i+len(MatchEnd)]
		if not AddStart and not AddEnd:
			break
		if FilterStart == MatchStart:
			StartPos = i
			if AddStart:
				HTML = HTML[:i] + AddStart + HTML[i:]
				AddStart = None
		if FilterEnd == MatchEnd and StartPos and i > StartPos:
			if AddEnd:
				HTML = HTML[:i+len(MatchEnd)] + AddEnd + HTML[i+len(MatchEnd):]
				AddEnd = None
	return HTML

def SquareFnrefs(HTML): # Different combinations of formatting for Soup .prettify, .encode, .decode break different page elements, don't use this for now
	Soup = MkSoup(HTML)
	Tags = Soup.find_all('sup')
	for t in Tags:
		if 'id' in t.attrs and t.attrs['id'].startswith('fnref:'):
			s = t.find('a')
			s.replace_with(f'[{t}]')
	return str(Soup.prettify(formatter=None))

def DoMinifyHTML(HTML, KeepComments):
	return htmlmin.minify(
		input=HTML,
		remove_comments=not KeepComments,
		remove_empty_space=True,
		remove_all_empty_space=False,
		reduce_empty_attributes=True,
		reduce_boolean_attributes=True,
		remove_optional_attribute_quotes=True,
		convert_charrefs=True,
		keep_pre=True)
