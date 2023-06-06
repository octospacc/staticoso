""" ================================== |
| This file is part of                 |
|   staticoso                          |
| Just a simple Static Site Generator  |
|                                      |
| Licensed under the AGPLv3 license    |
|   Copyright (C) 2022-2023, OctoSpacc |
| ================================== """

import configparser
from ast import literal_eval

DefConf = {
	"Logging": 20,
	"Threads": 0,
	"DiffBuild": False,
	"OutDir": "public",
	"SiteName": "Untitled Site",
	"SiteLang": "en",
	"SiteTemplate": "Default.html",
	"ActivityPubTypeFilter": "Post",
	"ActivityPubHoursLimit": 168,
	"CategoriesUncategorized": "Uncategorized",
	"FeedCategoryFilter": "Blog",
	"FeedEntries": 10,
	"JournalRedirect": False,
}

def LoadConfFile(File):
	Conf = configparser.ConfigParser()
	Conf.optionxform = str
	Conf.read(File)
	return Conf

def LoadConfStr(Str):
	Conf = configparser.ConfigParser()
	Conf.optionxform = str
	Conf.read_string(Str)
	return Conf

def ReadConf(Conf, Sect, Opt=None):
	if Opt:
		if Conf.has_option(Sect, Opt):
			return Conf[Sect][Opt]
	else:
		if Conf.has_section(Sect):
			return Conf[Sect]
	return None

def EvalOpt(Opt):
	if Opt:
		return literal_eval(Opt)
	else:
		return None

# TODO: Cleaning

def OptionChoose(Default, Primary, Secondary, Tertiary=None):
	return Primary if Primary != None else Secondary if Secondary != None else Tertiary if Tertiary != None else Default
def OptChoose(Default, Primary, Secondary, Tertiary=None):
	return OptionChoose(Default, Primary, Secondary, Tertiary=None)

def DefConfOptChoose(Key, Primary, Secondary):
	return OptChoose(DefConf[Key], Primary, Secondary)

def StringBoolChoose(Default, Primary, Secondary):
	Var = Default
	Check = Primary if Primary != None else Secondary
	if type(Check) == bool:
		Var = Check
	elif type(Check) == str:
		if Check in ('True', 'All', '*'):
			Var = True
		elif Check in ('False', 'None'):
			Var = False
	return Var
def StrBoolChoose(Default, Primary, Secondary):
	return StringBoolChoose(Default, Primary, Secondary)
