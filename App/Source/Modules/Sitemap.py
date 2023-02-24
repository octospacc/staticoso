""" ================================== |
| This file is part of                 |
|   staticoso                          |
| Just a simple Static Site Generator  |
|                                      |
| Licensed under the AGPLv3 license    |
|   Copyright (C) 2022-2023, OctoSpacc |
| ================================== """

from urllib.parse import quote as URLEncode
from Modules.Utils import *

def MakeSitemap(Flags:dict, Pages:list):
	Map = ''
	Domain = Flags['SiteDomain'] + '/' if Flags['SiteDomain'] else ''
	for Page in Pages:
		Map += Domain + URLEncode(f'{StripExt(Page["File"])}.html') + '\n'
	WriteFile(f"{Flags['OutDir']}/sitemap.txt", Map)
