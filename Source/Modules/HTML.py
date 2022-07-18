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

def StripTags(HTML, ToStrip):
	Soup = BeautifulSoup(HTML, 'html.parser')
	Tags = Soup.find_all()
	for t in Tags:
		if t.name in ToStrip:
			t.replace_with('')
	return str(Soup)
