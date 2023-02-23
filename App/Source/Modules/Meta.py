""" ================================== |
| This file is part of                 |
|   staticoso                          |
| Just a simple Static Site Generator  |
|                                      |
| Licensed under the AGPLv3 license    |
|   Copyright (C) 2022-2023, OctoSpacc |
| ================================== """

from Modules.Config import *
from Modules.Elements import *
from Modules.HTML import *
from Modules.Markdown import *
from Modules.Utils import *

# Menu styles:
# - Simple: Default, Flat, Line
# - Others: Excerpt, Image, Preview (Excerpt + Image), Full
def GetHTMLPagesList(Flags:dict, Pages:list, PathPrefix:str, CallbackFile=None, Unite=[], Type=None, Limit=None, PathFilter='', Category=None, For='Menu', MenuStyle='Default', ShowPaths=True):
	f = NameSpace(Flags)

	Flatten, SingleLine, DoneCount, PrevDepth = False, False, 0, 0
	if MenuStyle == 'Flat':
		Flatten = True
	elif MenuStyle == 'Line':
		ShowPaths, SingleLine = False, True
	List, ToPop, LastParent = '', [], []
	IndexPages = Pages.copy()
	for e in IndexPages:
		if e[3]['Index'].lower() in PageIndexStrNeg:
			IndexPages.remove(e)
	for i,e in enumerate(IndexPages):
		if Type and e[3]['Type'] != Type:
			ToPop += [i]
	ToPop = RevSort(ToPop)
	for i in ToPop:
		IndexPages.pop(i)
	if Type == 'Page':
		IndexPages = OrderPages(IndexPages)
	for i,e in enumerate(Unite):
		if e:
			IndexPages.insert(i, [e, None, None, {'Type':Type, 'Index':'True', 'Order':'Unite'}])
	for File, Content, Titles, Meta in IndexPages:
		# Allow for the virtual "Pages/" prefix to be used in path filtering
		TmpPathFilter = PathFilter
		if TmpPathFilter.startswith('Pages/'):
			TmpPathFilter = TmpPathFilter[len('Pages/'):]
			if File.startswith('Posts/'):
				continue

		if (not Type or (Meta['Type'] == Type and CanIndex(Meta['Index'], For))) and (not Category or Category in Meta['Categories']) and File.startswith(TmpPathFilter) and File != CallbackFile and (not Limit or Limit > DoneCount):
			Depth = (File.count('/') + 1) if Meta['Order'] != 'Unite' else 1
			# Folder names are handled here
			if Depth > 1 and Meta['Order'] != 'Unite':
				CurParent = File.split('/')[:-1]
				for i,s in enumerate(CurParent):
					if LastParent != CurParent and ShowPaths:
						LastParent = CurParent
						Levels = '.' * ((Depth-2+i) if not Flatten else 0) + ':'
						# If search node endswith index, it's a page; else, it's a folder
						if StripExt(File).endswith('index'):
							Title = MakeListTitle(File, Meta, Titles, 'HTMLTitle', f.BlogName, PathPrefix)
							DoneCount += 1
						else:
							Title = CurParent[Depth-2+i]
						if SingleLine:
							List += f' <span>{Title}</span> '
						else:
							List += f'{Levels}<span>{Title}</span>\n'

			# Pages with any other path
			if not (Depth > 1 and StripExt(File).split('/')[-1] == 'index'):
				Levels = '.' * ((Depth-1) if not Flatten else 0) + ':'
				DoneCount += 1
				if Meta['Order'] == 'Unite':
					Title = markdown(MarkdownHTMLEscape(File, f.MarkdownExts), extensions=f.MarkdownExts).removeprefix('<p>').removesuffix('<p>')
				else:
					Title = MakeListTitle(File, Meta, Titles, 'HTMLTitle', f.BlogName, PathPrefix)
				if SingleLine:
					List += ' <span>' + Title + '</span> '
				else:
					List += Levels + Title + '\n'

	if MenuStyle in ('Default', 'Flat'):
		return GenHTMLTreeList(List, Class="staticoso-PagesList")
	elif MenuStyle in ('Line', 'Excerpt', 'Image', 'Preview', 'Full'):
		return List

def CheckHTMLCommentLine(Line:str):
	if Line.startswith('<!--'):
		Line = Line[4:].lstrip()
		if Line.endswith('-->'):
			return Line
	return None

def TemplatePreprocessor(Text:str):
	Meta, MetaDefault = '', {
		'MenuStyle': 'Default'}
	for l in Text.splitlines():
		ll = l.lstrip().rstrip()
		lll = CheckHTMLCommentLine(ll)
		if lll:
			if lll.startswith('%'):
				Meta += lll[1:-3].lstrip().rstrip() + '\n'
	Meta = dict(ReadConf(LoadConfStr('[Meta]\n' + Meta), 'Meta'))
	for i in MetaDefault:
		if not i in Meta:
			Meta.update({i:MetaDefault[i]})
	return Meta

def FindPreprocLine(Line:str, Meta, Macros):
	Changed = False
	Line = Line.lstrip().rstrip()
	lll = CheckHTMLCommentLine(Line)
	if Line.startswith('//') or lll: # Find preprocessor lines
		lll = Line[2:].lstrip()
		if lll.startswith('%'):
			Meta += lll[1:].lstrip() + '\n'
			Changed = True
		elif lll.startswith('$'):
			Macros += lll[1:].lstrip() + '\n'
			Changed = True
	#if ll.startswith('<!--') and not ll.endswith('-->'): # Find comment and code blocks
	#	IgnoreBlocksStart += [l]
	return (Meta, Macros, Changed)

def PagePreprocessor(Flags:dict, Page:list, SiteTemplate, GlobalMacros, LightRun:bool=False):
	CategoryUncategorized = Flags['CategoriesUncategorized']
	Path, TempPath, Type, Content = Page

	File = ReadFile(Path) if not Content else Content
	Path = Path.lower()
	Content, Titles, DashyTitles, HTMLTitlesFound, Macros, Meta, MetaDefault = '', [], [], False, '', '', {
		'Template': SiteTemplate,
		'Head': '',
		'Style': '',
		'Type': Type,
		'Index': 'Unspecified',
		'Feed': 'True',
		'Title': '',
		'HTMLTitle': '',
		'Description': '',
		'Image': '',
		'Macros': {},
		'Categories': [],
		'URLs': [],
		'CreatedOn': '',
		'UpdatedOn': '',
		'EditedOn': '',
		'Order': None,
		'Language': None,
		'Downsync': None}
	# Find all positions of '<!--', '-->', add them in a list=[[pos0,pos1,line0,line1],...]
	for l in File.splitlines():
		ll = l.lstrip().rstrip()
		Meta, Macros, Changed = FindPreprocLine(ll, Meta, Macros)
		if not Changed: # Find headings
			#if line in ignore block:
			#	continue
			Headings = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
			#if Path.endswith(FileExtensions['HTML']):
			#	if ll[1:].startswith(Headings):
			#		if ll[3:].startswith((" class='NoTitle", ' class="NoTitle')):
			#			Content += l + '\n'
			#		elif ll.replace('	', ' ').startswith('// %'):
			#			pass
			#		else:
			#			Title = '#'*int(ll[2]) + ' ' + ll[4:]
			#			DashTitle = DashifyTitle(Title.lstrip('#'), DashyTitles)
			#			DashyTitles += [DashTitle]
			#			Titles += [Title]
			#			Content += MakeLinkableTitle(l, Title, DashTitle, 'pug') + '\n'
			#	else:
			#		Content += l + '\n'
			if Path.endswith(FileExtensions['HTML']) and not HTMLTitlesFound:
				Soup = MkSoup(File)
				Tags = Soup.find_all()
				for t in Tags:
					if t.name in Headings:
						Title = '#'*int(t.name[1]) + ' ' + str(t.text)
						DashTitle = DashifyTitle(Title.lstrip('#'), DashyTitles)
						DashyTitles += [DashTitle]
						Titles += [Title]
						t.replace_with(MakeLinkableTitle(None, Title, DashTitle, 'md'))
				HTMLTitlesFound = True
				Content = ''
				TmpContent = str(Soup.prettify(formatter=None))
				for cl in TmpContent.splitlines():
					_, _, IsMetaLine = FindPreprocLine(cl, Meta, Macros)
					if not IsMetaLine:
						#print(cl)
						Content += cl + '\n'
				break
			elif Path.endswith(FileExtensions['Markdown']):
				lsuffix = ''
				if ll.startswith(('-', '+', '*')):
					lsuffix += ll[0]
					ll = ll[1:].lstrip()	
				if ll.startswith('#') or (ll.startswith('<') and ll[1:].startswith(Headings)):
					if ll.startswith('#'):
						Title = ll
					elif ll.startswith('<'):
						if ll[3:].startswith((" class='NoTitle", ' class="NoTitle')):
							Content += l + '\n'
							continue
						else:
							Title = '#'*int(ll[2]) + ' ' + ll[4:]
					DashTitle = DashifyTitle(MkSoup(Title.lstrip('#')).get_text(), DashyTitles)
					DashyTitles += [DashTitle]
					Titles += [Title]
					Title = MakeLinkableTitle(None, Title, DashTitle, 'md')
					# I can't remember why I put this but it was needed
					Title = Title.replace('> </', '>  </').replace(' </', '</')
					Content += lsuffix + Title + '\n'
				else:
					Content += l + '\n'
			elif Path.endswith('.pug'):
				if ll.startswith(Headings):
					if ll[2:].startswith(("(class='NoTitle", '(class="NoTitle')):
						Content += l + '\n'
					else:
						Title = '#'*int(ll[1]) + ll[3:]
						DashTitle = DashifyTitle(Title.lstrip('#'), DashyTitles)
						DashyTitles += [DashTitle]
						Titles += [Title]
						# TODO: We should handle headers that for any reason already have parenthesis
						if ll[2:] == '(':
							Content += l + '\n'
						else:
							Content += MakeLinkableTitle(l, Title, DashTitle, 'pug') + '\n'
				else:
					Content += l + '\n'
			elif Path.endswith('.txt'):
				Content += l + '\n'
	Meta = dict(ReadConf(LoadConfStr('[Meta]\n' + Meta), 'Meta'))
	for i in MetaDefault:
		if i in Meta:
			# TODO: Handle strings with spaces but wrapped in quotes
			if i == 'Categories':
				Categories = Meta['Categories'].split(' ')
				Meta['Categories'] = []
				for j in Categories:
					Meta['Categories'] += [j]
			elif i == 'URLs':
				URLs = Meta['URLs'].split(' ')
				Meta['URLs'] = []
				for j in URLs:
					Meta['URLs'] += [j]
		else:
			Meta.update({i:MetaDefault[i]})
	if Meta['UpdatedOn']:
		Meta['EditedOn'] = Meta['UpdatedOn']
	if Meta['Index'].lower() in ('default', 'unspecified', 'categories'):
		if not Meta['Categories']:
			Meta['Categories'] = [CategoryUncategorized]
		if Meta['Type'].lower() == 'page':
			Meta['Index'] = 'Categories'
		elif Meta['Type'].lower() == 'post':
			Meta['Index'] = 'True'
	if GlobalMacros:
		Meta['Macros'].update(GlobalMacros)
	Meta['Macros'].update(ReadConf(LoadConfStr('[Macros]\n' + Macros), 'Macros'))
	return [TempPath, Content, Titles, Meta]

def PagePostprocessor(FileType, Text:str, Meta:dict):
	for e in Meta['Macros']:
		Text = ReplWithEsc(Text, f"[: {e} :]", f"[:{e}:]")
	return Text

def OrderPages(Old:list):
	New, NoOrder, Max = [], [], 0
	for i,e in enumerate(Old):
		Curr = e[3]['Order']
		if Curr:
			if int(Curr) > Max:
				Max = int(Curr)
		else:
			NoOrder += [e]
	New = [None] * (Max+1)
	for i,e in enumerate(Old):
		Curr = e[3]['Order']
		if Curr:
			New[int(Curr)] = e
	while None in New:
		New.remove(None)
	return New + NoOrder

def CanIndex(Index:str, For:str):
	if Index.lower() in PageIndexStrNeg:
		return False
	elif Index.lower() in PageIndexStrPos:
		return True
	else:
		return True if Index == For else False
