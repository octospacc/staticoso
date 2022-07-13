""" ================================= |
| This file is part of                |
|   staticoso                         |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
|   Copyright (C) 2022, OctoSpacc     |
| ================================= """ 

import urllib
from Modules.Utils import *

def MakeSitemap(Pages, SiteDomain=''):
	Map = ''
	for File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image in Pages:
		File = '{}.html'.format(StripExt(File))
		Domain = SiteDomain + '/' if SiteDomain else ' '
		Map += Domain + urllib.parse.quote(File) + '\n'
	WriteFile('public/sitemap.txt', Map)
