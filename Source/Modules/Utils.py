""" ================================= |
| This file is part of                |
|   staticoso                         |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
|   Copyright (C) 2022, OctoSpacc     |
| ================================= """

import json
import os
from datetime import datetime

def ReadFile(p):
	try:
		with open(p, 'r') as f:
			return f.read()
	except Exception:
		print("Error reading file {}".format(p))
		return None

def WriteFile(p, c):
	try:
		with open(p, 'w') as f:
			f.write(c)
		return True
	except Exception:
		print("Error writing file {}".format(p))
		return False

def FileToStr(File, Truncate=''):
	return str(File)[len(Truncate):]

def StripExt(Path):
	return ".".join(Path.split('.')[:-1])

def UndupeStr(Str, Known, Split):
	while Str in Known:
		Sections = Title.split(Split)
		try:
			Sections[-1] = str(int(Sections[-1]) + 1)
		except ValueError:
			Sections[-1] = Sections[-1] + str(Split) + '2'
		Str = Split.join(Sections)
	return Str

def DashifyStr(s, Limit=32):
	Str, lc = '', Limit
	for c in s[:Limit].replace(' ','-').replace('	','-'):
		if c.lower() in '0123456789qwfpbjluyarstgmneiozxcdvkh-':
			Str += c
	return '-' + Str

def GetFullDate(Date):
	if not Date:
		return None
	return datetime.strftime(datetime.strptime(Date, '%Y-%m-%d'), '%Y-%m-%dT%H:%M+00:00')

def LoadLocale(Lang):
	Lang = Lang + '.json'
	Folder = os.path.dirname(os.path.abspath(__file__)) + '/../../Locale/'
	File = ReadFile(Folder + Lang)
	if File:
		return json.loads(File)
	else:
		return json.loads(ReadFile(Folder + 'en.json'))