""" ================================== |
| This file is part of                 |
|   staticoso                          |
| Just a simple Static Site Generator  |
|                                      |
| Licensed under the AGPLv3 license    |
|   Copyright (C) 2022-2023, OctoSpacc |
| ================================== """

from urllib.parse import quote as URLEncode
from Modules.HTML import *
from Modules.Utils import *

def MakeSitemap(Flags:dict, Pages:list):
	Map = ''
	Domain = Flags['SiteDomain'] + '/' if Flags['SiteDomain'] else ''
	for File, Content, Titles, Meta, ContentHtml, SlimHtml, Description, Image in Pages:
		File = f"{StripExt(File)}.html"
		Map += Domain + URLEncode(File) + '\n'
	WriteFile(f"{Flags['OutDir']}/sitemap.txt", Map)

def BuildPagesSearch(Flags:dict, Pages:list):
	SearchContent = ''
	with open(f'{staticosoBaseDir()}Assets/PagesSearch.html', 'r') as File:
		Base = File.read().split('{{PagesInject}}')
	for File, Content, Titles, Meta, ContentHtml, SlimHtml, Description, Image in Pages:
	#for File, Content, Titles, Meta in Pages:
		SearchContent += f'''
			<div
				class="staticoso-HtmlSearch-Page"
				data-staticoso-htmlsearch-name="{html.escape(html.unescape(Titles[0]), quote=True)}"
				data-staticoso-htmlsearch-href="{StripExt(File)}.html"
			>
				{ContentHtml}
			</div>
		'''
	return Base[0] + SearchContent + Base[1]
