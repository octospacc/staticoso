""" ================================== |
| This file is part of                 |
|   staticoso                          |
| Just a simple Static Site Generator  |
|                                      |
| Licensed under the AGPLv3 license    |
|   Copyright (C) 2022-2023, OctoSpacc |
| ================================== """

import html
import warnings
from Libs import htmlmin
from Libs.bs4 import BeautifulSoup
from Modules.Utils import *

# Suppress useless bs4 warnings
warnings.filterwarnings('ignore', message='The input looks more like a filename than markup.')
warnings.filterwarnings('ignore', message='The soupsieve package is not installed.')

def MkSoup(Html):
	if type(Html) == str:
		return BeautifulSoup(Html, 'html.parser')
	elif type(Html) == BeautifulSoup:
		return Html

def StripAttrs(Html:str):
	Soup = MkSoup(Html)
	Tags = Soup.find_all()
	for t in Tags:
		if 'href' not in t.attrs and 'src' not in t.attrs:
			t.attrs = {}
	return str(Soup)

def StripTags(Html:str, ToStrip:list): # Remove desired tags from the HTML
	Soup = MkSoup(Html)
	Tags = Soup.find_all()
	for t in Tags:
		if t.name in ToStrip:
			t.replace_with('')
	return str(Soup)

def DoHTMLFixPre(Html:str):
	if not ("<pre>" in Html or "<pre " in Html):
		return Html
	Soup = MkSoup(Html)
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
	StartPos, DidStart, DidEnd = None, 0, 0
	for i,e in enumerate(HTML):
		FilterStart = HTML[i:i+len(MatchStart)]
		FilterEnd = HTML[i:i+len(MatchEnd)]
		if DidStart == 0 and FilterStart == MatchStart:
			StartPos = i
			if AddStart:
				HTML = HTML[:i] + AddStart + HTML[i:]
				DidStart = 2
		if DidEnd == 0 and FilterEnd == MatchEnd and StartPos and i > StartPos:
			StartPos = None
			if AddEnd:
				HTML = HTML[:i+len(MatchEnd)] + AddEnd + HTML[i+len(MatchEnd):]
				DidEnd = 2
		if DidStart > 0:
			DidStart -= 1
		if DidEnd > 0:
			DidEnd -= 1
	return HTML

def SquareFnrefs(Html:str): # Different combinations of formatting for Soup .prettify, .encode, .decode break different page elements, don't use this for now
	Soup = MkSoup(Html)
	Tags = Soup.find_all('sup')
	for t in Tags:
		if 'id' in t.attrs and t.attrs['id'].startswith('fnref:'):
			s = t.find('a')
			s.replace_with(f'[{t}]')
	return str(Soup.prettify(formatter=None))

def HtmlParagraphsToText(Html:str, Sep:str='\n\n'):
	Soup, Text = MkSoup(Html), ''
	for Par in Soup.find_all('p'):
		Par = Par.get_text().strip()
		if Par:
			Text += Par + Sep
	return Text

def DoMinifyHTML(Html:str, KeepComments:bool):
	return htmlmin.minify(
		input=Html,
		remove_comments=not KeepComments,
		remove_empty_space=True,
		remove_all_empty_space=False,
		reduce_empty_attributes=True,
		reduce_boolean_attributes=True,
		remove_optional_attribute_quotes=True,
		convert_charrefs=True,
		keep_pre=True)