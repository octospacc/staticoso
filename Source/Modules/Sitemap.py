""" ================================= |
| This file is part of                |
|   staticoso                         |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
|   Copyright (C) 2022, OctoSpacc     |
| ================================= """ 

from urllib.parse import quote as URLEncode
from Modules.Utils import *

def MakeSitemap(OutputDir, Pages, SiteDomain=''):
	Map = ''
	Domain = SiteDomain + '/' if SiteDomain else ''
	for File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image in Pages:
		File = f"{StripExt(File)}.html"
		Map += Domain + URLEncode(File) + '\n'
	WriteFile(f"{OutputDir}/sitemap.txt", Map)
