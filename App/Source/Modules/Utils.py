""" ================================== |
| This file is part of                 |
|   staticoso                          |
| Just a simple Static Site Generator  |
|                                      |
| Licensed under the AGPLv3 license    |
|   Copyright (C) 2022-2023, OctoSpacc |
| ================================== """

import json
import os
from datetime import datetime
from multiprocessing import Pool, cpu_count
from pathlib import Path
from types import SimpleNamespace
from Modules.Globals import *

def SureList(e):
	return e if type(e) == list else [e]

# Get base directory path of the staticoso program
def staticosoBaseDir():
	return f"{os.path.dirname(os.path.abspath(__file__))}/../../"

def ReadFile(p:str, m:str='r'):
	try:
		with open(p, m) as f:
			return f.read()
	except Exception:
		logging.error(f"Error reading file {p}")
		return None

def WriteFile(p, c, m='w'):
	try:
		with open(p, m) as f:
			return f.write(c)
	except Exception:
		logging.error(f"[E] Error writing file {p}")
		return False

def FileToStr(File:str, Truncate:str=''):
	return str(File)[len(Truncate):]

# With shutil.copytree copy only folder struct, no files; https://stackoverflow.com/a/15664273
def IgnoreFiles(Dir:str, Files:list):
    return [f for f in Files if os.path.isfile(os.path.join(Dir, f))]

def LoadFromDir(Dir:str, Matchs:list):
	Contents = {}
	Matchs = SureList(Matchs)
	for Match in Matchs:
		for File in Path(Dir).rglob(Match):
			File = str(File)[len(Dir)+1:]
			Contents.update({File: ReadFile(f"{Dir}/{File}")})
	return Contents

def mkdirps(Dir:str):
	return Path(Dir).mkdir(parents=True, exist_ok=True)

def StripExt(Path:str):
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

def DashifyStr(s:str, Limit:int=32):
	Str = ''
	for c in s[:Limit].replace('\n','-').replace('\t','-').replace(' ','-'):
		if c.lower() in '0123456789qwfpbjluyarstgmneiozxcdvkh-':
			Str += c
	return '-' + Str

def GetPathLevels(Path:str, AsNum:bool=False, Add:int=0, Sub:int=0):
	n = Path.count('/') + Add - Sub
	return n if AsNum else '../' * n

# https://stackoverflow.com/a/34445090
def FindAllIndex(Str:str, Sub:str):
	i = Str.find(Sub)
	while i != -1:
		yield i
		i = Str.find(Sub, i+1)

# Replace substrings in a string, except when an escape char is prepended
def ReplWithEsc(Str:str, Find:str, Repl:str, Esc:str='\\'):
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
				New = New[:-1]
				New += Find + e
			else:
				New += Repl + e
	return New

def DictReplWithEsc(Str:str, Dict:dict, Esc:str='\\'):
	for Item in Dict:
		Str = ReplWithEsc(Str, Item, Dict[Item], Esc='\\')
	return Str

def WrapDictReplWithEsc(Str:str, Dict:dict, Wraps:list=[], Esc:str='\\'):
	NewDict = {}
	for Item in Dict:
		for Wrap in Wraps:
			NewDict.update({f'{Wrap[0]}{Item}{Wrap[1]}': Dict[Item]})
	return DictReplWithEsc(Str, NewDict, Esc)

def NumsFromFileName(Path:str):
	Name = Path.split('/')[-1]
	Split = len(Name)
	for i,e in enumerate(Name):
		if e.lower() in 'qwfpbjluyarstgmneiozxcdvkh':
			return Name[:i]
	return Path

def RevSort(List:list):
	List.sort()
	List.reverse()
	return List

def FileNameDateSort(Old): # TODO: Test this for files not starting with date, and dated folders
	New = []
	if Old:
		Old.sort()
		New.insert(0, Old[0])
		for i,e in enumerate(Old):
			if i == 0:
				continue
			Done = False
			for j,f in enumerate(New):
				if NumsFromFileName(e) != e and NumsFromFileName(f) != f and NumsFromFileName(e) < NumsFromFileName(f):
					New.insert(j, e)
					Done = True
					break
			if not Done:
				New += [e]
	return New

def FirstRealItem(List):
	return next(e for e in List if e)

def GetFullDate(Date):
	if not Date:
		return None
	return datetime.strftime(datetime.strptime(Date, '%Y-%m-%d'), '%Y-%m-%dT%H:%M+00:00')

def LoadLocale(Lang:str):
	Lang = Lang + '.json'
	Folder = f'{staticosoBaseDir()}Locale/'
	File = ReadFile(Folder + Lang)
	if File:
		return json.loads(File)
	else:
		return json.loads(ReadFile(Folder + 'en.json'))

def IsLightRun(File, LimitFiles):
	return False if LimitFiles == False or File in LimitFiles else True

def NameSpace(From):
    return SimpleNamespace(**From)

def PrintProcPercentDots(Proc:dict, DivMult=1):
	Div = 5 * DivMult # 100/5 = 20 chars
	Num, Count = Proc['Num'], Proc['Count']
	if int(((Num/Count)*100)/Div) != int((((Num+1)/Count)*100)/Div):
		os.system('printf "="') # Using sys shell since for some reason print() without newline breaks here (doesn't print everytime)
		return True
	return False

def MultiProcFunctWrap(Args:dict):
	PrintProcPercentDots(Args['Process'])
	return Args['Process']['Funct'](Args)

def DoMultiProc(Funct, ArgsCollection:list, Threads:int=cpu_count(), Progress:bool=False):
	FinalArgsCollection = []
	for Index, Args in enumerate(ArgsCollection):
		FinalArgsCollection.append(Args)
		FinalArgsCollection[Index].update({"Process": {"Funct": Funct, "Num": Index, "Count": len(ArgsCollection)}})
	Results = []
	if Progress:
		os.system('printf "["') # Using system print because (see PrintProcPercentDots())
	with Pool(Threads) as MultiprocPool:
		Results = MultiprocPool.map(MultiProcFunctWrap if Progress else Funct, FinalArgsCollection)
	if Progress:
		os.system('printf "]\n"') # Newline after percentage dots
	return Results
