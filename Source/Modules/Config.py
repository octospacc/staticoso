""" ================================= |
| This file is part of                |
|   staticoso                         |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
|   Copyright (C) 2022, OctoSpacc     |
| ================================= """

import configparser
from ast import literal_eval

def LoadConfFile(File):
	Conf = configparser.ConfigParser()
	Conf.optionxform = lambda option: option
	Conf.read(File)
	return Conf

def LoadConfStr(Str):
	Conf = configparser.ConfigParser()
	Conf.optionxform = lambda option: option
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

def OptionChoose(Default, Primary, Secondary, Tertiary=None):
	return Primary if Primary != None else Secondary if Secondary != None else Tertiary if Tertiary != None else Default

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
