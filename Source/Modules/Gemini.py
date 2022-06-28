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

def HTML2Gemtext(Pages, SiteName, SiteTagline):
	os.mkdir('public.gmi')
	for File, Content, Titles, Meta, HTMLContent, Description, Image in Pages:
		Parse = BeautifulSoup(HTMLContent, 'html.parser')
		# We should first get the most basic HTML elements, convert them to Gemtext, then replace the Gemtext in the original full HTML, and then removing <p> tags?
		#print(File, Parse.find_all('p'), Parse.find_all('li'))

""" Gemtext:
# h1
## h2
### h3

* li
* li

=> [protocol://]URL Link Description

> Quote

```
Preformatted
```
"""
