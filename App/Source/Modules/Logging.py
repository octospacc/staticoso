""" ================================== |
| This file is part of                 |
|   staticoso                          |
| Just a simple Static Site Generator  |
|                                      |
| Licensed under the AGPLv3 license    |
|   Copyright (C) 2022-2023, OctoSpacc |
| ================================== """

import logging
import sys
from Modules.Config import *

LoggingFormat = '[%(levelname)s] %(message)s'
LoggingLevels = {
	"Debug": {"Name":"D", "Num":15},
	"Info": {"Name":"I", "Num":20},
	"Warning": {"Name":"W", "Num":30},
	"Error": {"Name":"E", "Num":40}}

def SetupLogging(Level):
	logging.basicConfig(format=LoggingFormat, stream=sys.stdout, level=Level)
	logging.addLevelName(15, 'D') # Standard (10) Debug level makes third-party modules spam
	logging.addLevelName(20, 'I')
	logging.addLevelName(30, 'W')
	logging.addLevelName(40, 'E')

def ConfigLogging(Level):
	Num = DefConf['Logging']
	if type(Level) == str:
	    if Level.isdecimal():
		    Num = int(Level)
	    else:
		    if Level.lower() in LoggingLevels:
			    Num = LoggingLevels['Level']['Num']
	SetupLogging(Num)
