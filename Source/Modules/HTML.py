""" ================================= |
| This file is part of                |
|   staticoso                         |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
|   Copyright (C) 2022, OctoSpacc     |
| ================================= """

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

def MkSoup(HTML):
	return BeautifulSoup(HTML, 'html.parser')

def StripAttrs(HTML):
	Soup = MkSoup(HTML)
	Tags = Soup.find_all()
	for t in Tags:
		if 'href' not in t.attrs and 'src' not in t.attrs:
			t.attrs = {}
	return str(Soup)

def StripTags(HTML, ToStrip):
	Soup = MkSoup(HTML)
	Tags = Soup.find_all()
	for t in Tags:
		if t.name in ToStrip:
			t.replace_with('')
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
			# TagName = FirstRealItem(FirstRealItem(FilterStart.split('<')).split(' '))
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
