""" ================================= |
| This file is part of                |
|   staticoso                         |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
|   Copyright (C) 2022, OctoSpacc     |
| ================================= """

# TODO: Write a native Pug parser; There is one already available for Python but seems broken / out-of-date

import os
from Modules.Utils import *

def PugCompileList(Pages):
	# Pug-cli seems to shit itself with folder paths as input, so we pass ALL the files as arguments
	Paths = ''
	for File, Content, Titles, Meta in Pages:
		if File.lower().endswith('.pug'):
			Path = 'public/{}'.format(File)
			WriteFile(Path, Content)
			Paths += '"{}" '.format(Path)
	if Paths:
		os.system('pug -P {} > /dev/null'.format(Paths))
