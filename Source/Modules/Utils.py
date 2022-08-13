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
from pathlib import Path

FileExtensions = {
	'Pages': ('htm', 'html', 'md', 'pug', 'txt'),
	'Tmp': ('md', 'pug', 'txt')}

def ReadFile(p):
	try:
		with open(p, 'r') as f:
			return f.read()
	except Exception:
		print("[E] Error reading file {}".format(p))
		return None

def WriteFile(p, c):
	try:
		with open(p, 'w') as f:
			f.write(c)
		return True
	except Exception:
		print("[E] Error writing file {}".format(p))
		return False

def FileToStr(File, Truncate=''):
	return str(File)[len(Truncate):]

# https://stackoverflow.com/a/15664273
def IgnoreFiles(Dir, Files):
    return [f for f in Files if os.path.isfile(os.path.join(Dir, f))]

def LoadFromDir(Dir, Rglob):
	Contents = {}
	for File in Path(Dir).rglob(Rglob):
		File = str(File)[len(Dir)+1:]
		Contents.update({File: ReadFile('{}/{}'.format(Dir, File))})
	return Contents

def StripExt(Path):
	return ".".join(Path.split('.')[:-1])

def UndupeStr(Str, Known, Split):
	while Str in Known:
		Sections = Str.split(Split)
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

def GetPathLevels(Path, AsNum=False, Add=0, Sub=0):
	n = Path.count('/') + Add - Sub
	return n if AsNum else '../' * n

# https://stackoverflow.com/a/34445090
def FindAllIndex(Str, Sub):
	i = Str.find(Sub)
	while i != -1:
		yield i
		i = Str.find(Sub, i+1)

def ReplWithEsc(Str, Find, Repl, Esc='\\'):
	New = ''
	Sects = Str.split(Find)
	for i,e in enumerate(Sects):
		if i == 0:
			New += e
		elif i > 0:
			if Sects[i-1].endswith(Esc*2):
				New = New[:-1]
				New += Repl + e
			elif Sects[i-1].endswith(Esc):
				New += Find + e
			else:
				New += Repl + e
	return New

def NumsFromFileName(Path):
	Name = Path.split('/')[-1]
	Split = len(Name)
	for i,e in enumerate(Name):
		if e.lower() in 'qwfpbjluyarstgmneiozxcdvkh':
			return Name[:i]
			#Split = i
			#break
	#return Name[:Split]
	return Path

def RevSort(List):
	List.sort()
	List.reverse()
	return List

def FileNameDateSort(Old):
	New = []
	Old.sort()
	New.insert(0, Old[0])
	#print(Old)
	for i,e in enumerate(Old):
		if i == 0:
			continue
		#print(e)
		Done = False
		for j,f in enumerate(New):
			#print(f)
			#if NumsFromFileName(e) > NumsFromFileName(f):
			#print(j, e, f)
			#print(j, NumsFromFileName(e), NumsFromFileName(f))
			
			#if NumsFromFileName(e) != e and NumsFromFileName(f) != f and NumsFromFileName(e) > NumsFromFileName(f):
			if NumsFromFileName(e) != e and NumsFromFileName(f) != f and NumsFromFileName(e) < NumsFromFileName(f):
			#if e.split('/')[-1] > f.split('/')[-1]:
				#New.insert(j+1, e)
				New.insert(j, e)
				Done = True
				break
		if not Done:
			#New.insert(0, e)
			New += [e]
	#New.reverse()
	print(New)
	return New

def FirstRealItem(List):
	return next(e for e in List if e)

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
