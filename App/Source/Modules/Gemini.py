""" ================================== |
| This file is part of                 |
|   staticoso                          |
| Just a simple Static Site Generator  |
|                                      |
| Licensed under the AGPLv3 license    |
|   Copyright (C) 2022-2023, OctoSpacc |
| ================================== """

# TODO: Write the Python HTML2Gemtext converter

from Libs.bs4 import BeautifulSoup
from Modules.HTML import *
from Modules.Utils import *

def FixGemlogDateLine(Line):
	if len(Line) >= 2 and Line[0] == '[' and Line[1].isdigit():
		Line = Line[1:]
	else:
		Words = Line.split(' ')
		if len(Words) >= 2 and len(Words[1]) >= 2 and Words[1][0] == '[' and Words[1][1].isdigit():
			Line = Words[0] + '\n' + Words[1][1:] + ' ' + ' '.join(Words[2:])
	return Line

def GemtextCompileList(Flags, Pages, LimitFiles):
	Cmd = ''
	for File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image in Pages:
		if IsLightRun(File, LimitFiles):
			continue
		Src = f"{Flags['OutDir']}.gmi/{StripExt(File)}.html.tmp"
		Dst = f"{Flags['OutDir']}.gmi/{StripExt(File)}.gmi"
		SlimHTML = StripAttrs(SlimHTML)
		for i in ('ol', 'ul', 'li'):
			for j in ('<'+i+'>', '</'+i+'>'):
				SlimHTML = SlimHTML.replace(j, '')
		WriteFile(Src, SlimHTML.replace('</a>', '</a><br>').replace('.html', '.gmi')) # TODO: Adjust links properly..
		Cmd += f'cat "{Src}" | html2gmi > "{Dst}"; '
	if Cmd:
		os.system(Cmd)
	for File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image in Pages:
		if IsLightRun(File, LimitFiles):
			continue
		Dst = f"{Flags['OutDir']}.gmi/{StripExt(File)}.gmi"
		Gemtext = ''
		for Line in ReadFile(Dst).splitlines():
			Line = FixGemlogDateLine(Line)
			Gemtext += Line + '\n'
		WriteFile(Dst, Flags['GemtextHeader'] + Gemtext)

def FindEarliest(Str, Items):
	Pos, Item = 0, ''
	for Item in Items:
		Str.find(Item)
	return Pos, Item

def ParseTag(Content):
	print(Content)
	Parse = BeautifulSoup(str(Content), 'html.parser')
	Tag = Parse.find()
