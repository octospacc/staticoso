""" ================================= |
| This file is part of                |
|   staticoso                         |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
|   Copyright (C) 2022, OctoSpacc     |
| ================================= """

# Our local Markdown patches conflict if the module is installed on the system, so first try to import from system
try:
	from markdown import markdown
except ModuleNotFoundError:
	from Libs.markdown import markdown

MarkdownExtsDefault = ('attr_list', 'def_list', 'footnotes', 'md_in_html', 'tables')

def MarkdownHTMLEscape(Str, Extensions=()): # WIP
	Text = ''
	for i,e in enumerate(Str):
		if ('mdx_subscript' or 'markdown_del_ins') in Extensions and e == '~':
			e = '&#x7E;'
		Text += e
	return Text
