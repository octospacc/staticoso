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

def MakeSitemap(Flags, Pages):
	Map = ''
	Domain = Flags['SiteDomain'] + '/' if Flags['SiteDomain'] else ''
	for File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image in Pages:
		File = f"{StripExt(File)}.html"
		Map += Domain + URLEncode(File) + '\n'
	WriteFile(f"{Flags['OutDir']}/sitemap.txt", Map)
