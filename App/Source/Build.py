#!/usr/bin/env python3
""" ================================== |
| This file is part of                 |
|   staticoso                          |
| Just a simple Static Site Generator  |
|                                      |
| Licensed under the AGPLv3 license    |
|   Copyright (C) 2022-2023, OctoSpacc |
| ================================== """

import argparse
import os
import shutil
import time
from ast import literal_eval
from datetime import datetime
from pathlib import Path
from Modules.Assets import *
from Modules.Config import *
from Modules.Gemini import *
from Modules.Globals import *
from Modules.Logging import *
from Modules.Markdown import *
from Modules.Site import *
from Modules.Sitemap import *
from Modules.Social import *
from Modules.Utils import *

def ResetOutDir(OutDir:str):
	for e in (OutDir, f'{OutDir}.Content', f'{OutDir}.gmi'):
		try:
			shutil.rmtree(e)
		except FileNotFoundError:
			pass

def DelTmp(OutDir:str):
	for Ext in FileExtensions['Tmp']:
		for File in Path(OutDir).rglob(AnyCaseGlob(f'*.{Ext}')):
			os.remove(File)
	for Dir in (OutDir, f'{OutDir}.gmi'):
		for File in Path(Dir).rglob(AnyCaseGlob('*.tmp')):
			os.remove(File)

def SetSorting(Sorting:dict):
	Default = {"Pages": "Standard", "Posts": "Inverse"}
	for i in Default:
		if i not in Sorting:
			Sorting.update({i:Default[i]})
	return Sorting

def GetConfMenu(Entries, MarkdownExts):
	if Entries:
		Menu, Max = [], 0
		for i in Entries:
			if int(i) > Max:
				Max = int(i)
		Menu = [None] * (Max+1)
		for i in Entries:
			e = Entries[i]
			if not ((e.startswith('<') or e.startswith('[') or e.startswith('- ')) and (e.endswith('>') or e.endswith(')') or e.endswith('}'))):
				if not e.lower().endswith(FileExtensions['HTML']):
					e += '.html'
			Menu[int(i)] = e
	return Menu

def CheckSafeOutDir(OutDir:str):
	InDir = os.path.realpath(os.getcwd())
	OutDir = os.path.realpath(OutDir)
	OutFolder = OutDir.split('/')[-1]
	if InDir.lower() == OutDir.lower():
		logging.error(f"⛔ Output and Input directories ({OutDir}) can't be the same. Exiting.")
		exit(1)
	elif OutFolder.lower() in ReservedPaths and f"{InDir.lower()}/{OutFolder.lower()}" == OutDir.lower():
		logging.error(f"⛔ Output directory ({OutDir}) can't be a reserved subdirectory of the Input. Exiting.")
		exit(1)

def GetModifiedFiles(OutDir):
	All, Mod = [], []
	for Path in ('Pages', 'Posts'):
		for Root, Dirs, Files in os.walk(Path):
			for File in Files:
				Src = os.path.join(Root,File)
				SrcTime = int(os.path.getmtime(Src))
				if Path == 'Pages':
					Tmp = '/'.join(Src.split('/')[1:])
				elif Path == 'Posts':
					Tmp = Src
				Obj = f"{OutDir}/{StripExt(Tmp)}.html"
				try:
					ObjTime = int(os.path.getmtime(Obj))
				except FileNotFoundError:
					ObjTime = 0
				All += [{'Tmp':Tmp, 'SrcTime':SrcTime, 'ObjTime':ObjTime}]
	for File in All:
		if File['SrcTime'] > File['ObjTime']:
			Mod += [File['Tmp']]
	return Mod

def WriteRedirects(Flags:dict, Pages:list, FinalPaths, Locale:dict):
	SiteName = Flags['SiteName']
	for Page in Pages:
		for URL in Page['Meta']['URLs']:
			for DestOpts in ((f'{Flags["OutDir"]}/{URL}', ''), (f'{Flags["OutDir"]}/{StripExt(URL)}/index.html', '../')):
				DestFile, DestPrefix = DestOpts
				if DestFile not in FinalPaths:
					DestURL = f'{DestPrefix}{GetPathLevels(URL)}{StripExt(Page["File"])}.html'
					mkdirps(os.path.dirname(DestFile))
					WriteFile(DestFile, RedirectPageTemplate.format(
						SiteDomain=Flags['SiteDomain'],
						DestURL=DestURL,
						TitlePrefix=f'{SiteName} - ' if SiteName else '',
						StrClick=Locale['ClickHere'],
						StrRedirect=Locale['IfNotRedirected']))
		if StripExt(Page["File"]).split('/')[-1].lower() != 'index':
			DestFile = f'{Flags["OutDir"]}/{StripExt(Page["File"])}/index.html'
			DestURL = f'../{StripExt(Page["File"]).split("/")[-1]}.html'
			mkdirps(os.path.dirname(DestFile))
			WriteFile(DestFile, RedirectPageTemplate.format(
				SiteDomain=Flags['SiteDomain'],
				DestURL=DestURL,
				TitlePrefix=f'{SiteName} - ' if SiteName else '',
				StrClick=Locale['ClickHere'],
				StrRedirect=Locale['IfNotRedirected']))

def CopyBaseFiles(Flags:dict):
	f = NameSpace(Flags)
	Have = {"Pages": False, "Posts": False}
	for Type in ('Pages', 'Posts'):
		if os.path.isdir(Type):
			Have[Type] = True
			shutil.copytree(Type, f'{f.OutDir}{PageTypeOutPrefix[Type]}', dirs_exist_ok=True)
			shutil.copytree(Type, f'{f.OutDir}.Content{PageTypeOutPrefix[Type]}', dirs_exist_ok=True)
			if f.GemtextOutput:
				shutil.copytree(Type, f'{f.OutDir}.gmi{PageTypeOutPrefix[Type]}', ignore=IgnoreFiles, dirs_exist_ok=True)
	return Have['Pages'] or Have['Posts']

def DedupeBaseFiles(Flags:dict):
	f = NameSpace(Flags)
	Msg = "⚠ Input files with the same name but different {0} are not allowed. Unpredictable issues will arise. You should rename your files to fix this issue."
	SaidDupes = {"Ext": False, "Name": False}
	Files = {}
	Remove = []
	for Dir in (f.OutDir, f'{f.OutDir}.Content'):
		for File in Path(Dir).rglob('*'):
			if os.path.isfile(File):
				File = str(File)
				Name = '.'.join(File.split('.')[:-1])
				Lower = Name.lower()
				Ext = File.split('.')[-1]
				# If file with same name exists
				if Lower in Files:
					# If extension and name are the same
					if Files[Lower][-1].lower() == Ext.lower():
						if not SaidDupes['Name']:
							logging.warning(Msg.format('capitalization'))
							SaidDupes['Name'] = True
					# If extension differs
					else:
						if not SaidDupes['Ext']:
							logging.warning(Msg.format('extension'))
							SaidDupes['Ext'] = True
					Remove += [File]
				else:
					Files.update({Name.lower(): (Name, Ext)})
	for File in Remove:
		# Avoid duplicate prints executed for multiple folders
		if File.startswith(f'{f.OutDir}/'):
			Name = '.'.join(File[len(f'{f.OutDir}/'):].split('.')[:-1]) + '.*'
			print(Name if Name.startswith('Posts/') else f'Pages/{Name}')
		os.remove(File)

def BuildMain(Args, FeedEntries):
	Flags, Snippets = {}, {}
	SiteConf = LoadConfFile('Site.ini')

	#ConfigLogging(DefConfOptChoose('Logging', Args.Logging, ReadConf(SiteConf, 'staticoso', 'Logging')))

	#if Args.InputDir:
	#	os.chdir(Args.InputDir)
	#	print(f"[I] Current directory: {Args.InputDir}")

	SiteName = Flags['SiteName'] = OptChoose('', Args.SiteName, ReadConf(SiteConf, 'Site', 'Name'))
	if SiteName:
		logging.info(f"Compiling: {SiteName}")

	OutDir = Flags['OutDir'] = DefConfOptChoose('OutDir', Args.OutputDir, ReadConf(SiteConf, 'Site', 'OutputDir'))
	OutDir = Flags['OutDir'] = OutDir.removesuffix('/')
	CheckSafeOutDir(OutDir)
	logging.info(f"Outputting to: {OutDir}/")

	Threads = Args.Threads if Args.Threads else DefConf['Threads']
	DiffBuild = Args.DiffBuild if Args.DiffBuild else DefConf['DiffBuild']

	Flags['BlogName'] = OptChoose('', Args.BlogName, ReadConf(SiteConf, 'Site', 'BlogName'))
	Flags['SiteTagline'] = OptChoose('', Args.SiteTagline, ReadConf(SiteConf, 'Site', 'Tagline'))
	Flags['SiteTemplate'] = DefConfOptChoose('SiteTemplate', Args.SiteTemplate, ReadConf(SiteConf, 'Site', 'Template'))
	SiteDomain = Flags['SiteDomain'] = OptChoose('', Args.SiteDomain, ReadConf(SiteConf, 'Site', 'Domain'))
	Flags['SiteRoot'] = OptChoose('/', Args.SiteRoot, ReadConf(SiteConf, 'Site', 'Root'))
	SiteLang = Flags['SiteLang'] = DefConfOptChoose('SiteLang', Args.SiteLanguage, ReadConf(SiteConf, 'Site', 'Language'))

	Sorting = Flags['Sorting'] = literal_eval(OptChoose('{}', Args.Sorting, ReadConf(SiteConf, 'Site', 'Sorting')))
	Sorting = Flags['Sorting'] = SetSorting(Sorting)

	Flags['NoScripts'] = StrBoolChoose(False, Args.NoScripts, ReadConf(SiteConf, 'Site', 'NoScripts'))
	Flags['FolderRoots'] = literal_eval(Args.FolderRoots) if Args.FolderRoots else {}

	Flags['ActivityPubTypeFilter'] = DefConfOptChoose('ActivityPubTypeFilter', Args.ActivityPubTypeFilter, ReadConf(SiteConf, 'ActivityPub', 'TypeFilter'))
	Flags['ActivityPubHoursLimit'] = DefConfOptChoose('ActivityPubHoursLimit', Args.ActivityPubHoursLimit, ReadConf(SiteConf, 'ActivityPub', 'HoursLimit'))

	Flags['MastodonURL'] = OptChoose('', Args.MastodonURL, ReadConf(SiteConf, 'Mastodon', 'URL'))
	Flags['MastodonToken'] = OptChoose('', Args.MastodonToken, ReadConf(SiteConf, 'Mastodon', 'Token'))

	MarkdownExts = Flags['MarkdownExts'] = literal_eval(OptionChoose(str(MarkdownExtsDefault), Args.MarkdownExts, ReadConf(SiteConf, 'Markdown', 'Exts')))
	Flags['SitemapOutput'] = StrBoolChoose(True, Args.SitemapOutput, ReadConf(SiteConf, 'Sitemap', 'Output'))

	Flags['MinifyOutput'] = StrBoolChoose(False, Args.MinifyOutput, ReadConf(SiteConf, 'Minify', 'Output'))
	Flags['MinifyAssets'] = StrBoolChoose(False, Args.MinifyAssets, ReadConf(SiteConf, 'Minify', 'Assets'))
	Flags['MinifyKeepComments'] = StrBoolChoose(False, Args.MinifyKeepComments, ReadConf(SiteConf, 'Minify', 'KeepComments'))

	Flags['ImgAltToTitle'] = StrBoolChoose(True, Args.ImgAltToTitle, ReadConf(SiteConf, 'Site', 'ImgAltToTitle'))
	Flags['ImgTitleToAlt'] = StrBoolChoose(False, Args.ImgTitleToAlt, ReadConf(SiteConf, 'Site', 'ImgTitleToAlt'))
	Flags['HTMLFixPre'] = StrBoolChoose(False, Args.HTMLFixPre, ReadConf(SiteConf, 'Site', 'HTMLFixPre'))

	Flags['CategoriesAutomatic'] = StrBoolChoose(False, Args.CategoriesAutomatic, ReadConf(SiteConf, 'Categories', 'Automatic'))
	Flags['CategoriesUncategorized'] = DefConfOptChoose('CategoriesUncategorized', Args.CategoriesUncategorized, ReadConf(SiteConf, 'Categories', 'Uncategorized'))

	Flags['GemtextOutput'] = StrBoolChoose(False, Args.GemtextOutput, ReadConf(SiteConf, 'Gemtext', 'Output'))
	Flags['GemtextHeader'] = Args.GemtextHeader if Args.GemtextHeader else ReadConf(SiteConf, 'Gemtext', 'Header') if ReadConf(SiteConf, 'Gemtext', 'Header') else f"# {SiteName}\n\n" if SiteName else ''

	Flags['FeedCategoryFilter'] = DefConfOptChoose('FeedCategoryFilter', Args.FeedCategoryFilter, ReadConf(SiteConf, 'Feed', 'CategoryFilter'))
	FeedEntries = Flags['FeedEntries'] = int(FeedEntries) if (FeedEntries or FeedEntries == 0) and FeedEntries != 'Default' else int(ReadConf(SiteConf, 'Feed', 'Entries')) if ReadConf(SiteConf, 'Feed', 'Entries') else DefConf['FeedEntries']

	Flags["JournalRedirect"] = StrBoolChoose(DefConf["JournalRedirect"], Args.JournalRedirect, ReadConf(SiteConf, 'Journal', 'Redirect'))

	Flags['DynamicParts'] = literal_eval(OptionChoose('{}', Args.DynamicParts, ReadConf(SiteConf, 'Site', 'DynamicParts')))
	DynamicPartsText = Snippets['DynamicParts'] = LoadFromDir('DynamicParts', ['*.htm', '*.html'])
	StaticPartsText = Snippets['StaticParts'] = LoadFromDir('StaticParts', ['*.htm', '*.html'])
	TemplatesText = Snippets['Templates'] = LoadFromDir('Templates', ['*.htm', '*.html'])

	MenuEntries = ReadConf(SiteConf, 'Menu')
	if MenuEntries:
		ConfMenu = GetConfMenu(MenuEntries, MarkdownExts)
	else:
		ConfMenu = []

	SiteDomain = Flags['SiteDomain'] = SiteDomain.removesuffix('/')
	Locale = LoadLocale(SiteLang)

	if DiffBuild:
		logging.info("Build mode: Differential")
		LimitFiles = GetModifiedFiles(OutDir)
	else:
		logging.info("Build mode: Clean")
		ResetOutDir(OutDir)
		LimitFiles = False

	logging.info("Reading Base Files")
	if not CopyBaseFiles(Flags):
		logging.error("⛔ No Pages or Posts found. Nothing to do, exiting!")
		exit(1)
	DedupeBaseFiles(Flags)

	logging.info("Generating HTML")
	DictPages = MakeSite(
		Flags=Flags,
		LimitFiles=LimitFiles,
		Snippets=Snippets,
		ConfMenu=ConfMenu,
		GlobalMacros=ReadConf(SiteConf, 'Macros'),
		Locale=Locale,
		Threads=Threads)

	# REFACTOR: Some functions below are still not changed to accept a Page as Dict, so let's reconvert to Lists
	ListPages = DictPages.copy()
	for i, e in enumerate(ListPages):
		ListPages[i] = list(e.values())

	if FeedEntries != 0:
		logging.info("Generating Feeds")
		for FeedType in (True, False):
			MakeFeed(Flags, ListPages, FeedType)

	logging.info("Applying Social Integrations")
	FinalPaths = ApplySocialIntegrations(Flags, ListPages, LimitFiles, Locale)

	logging.info("Creating Redirects")
	WriteRedirects(Flags, DictPages, FinalPaths, Locale)

	logging.info("Building HTML Search Page")
	WriteFile(f'{OutDir}/Search.html', BuildPagesSearch(Flags, DictPages, TemplatesText[Flags['SiteTemplate']], Snippets, Locale))

	if Flags['GemtextOutput']:
		logging.info("Generating Gemtext")
		GemtextCompileList(Flags, ListPages, LimitFiles)

	logging.info("Cleaning Temporary Files")
	DelTmp(OutDir)

	if Flags['SitemapOutput']:
		logging.info("Generating Sitemap")
		MakeSitemap(Flags, DictPages)

	logging.info("Preparing Assets")
	PrepareAssets(Flags)

if __name__ == '__main__':
	StartTime = time.time()

	Parser = argparse.ArgumentParser()
	Parser.add_argument('--Logging', type=str) # Levels: Debug, Info, Warning, Error.
	Parser.add_argument('--Threads', type=str) # Set 0 to use all CPU cores
	Parser.add_argument('--DiffBuild', type=str)
	Parser.add_argument('--OutputDir', type=str)
	#Parser.add_argument('--InputDir', type=str)
	Parser.add_argument('--Sorting', type=str)
	#Parser.add_argument('--SiteLang', type=str) # DEPRECATED
	Parser.add_argument('--SiteLanguage', type=str)
	Parser.add_argument('--SiteRoot', type=str)
	Parser.add_argument('--SiteName', type=str)
	Parser.add_argument('--BlogName', type=str)
	Parser.add_argument('--SiteTemplate', type=str)
	Parser.add_argument('--SiteDomain', type=str)
	Parser.add_argument('--MinifyOutput', type=str)
	Parser.add_argument('--MinifyAssets', type=str)
	Parser.add_argument('--MinifyKeepComments', type=str)
	Parser.add_argument('--NoScripts', type=str)
	Parser.add_argument('--ImgAltToTitle', type=str)
	Parser.add_argument('--ImgTitleToAlt', type=str)
	Parser.add_argument('--HTMLFixPre', type=str)
	Parser.add_argument('--GemtextOutput', type=str)
	Parser.add_argument('--GemtextHeader', type=str)
	Parser.add_argument('--SiteTagline', type=str)
	Parser.add_argument('--SitemapOutput', type=str)
	Parser.add_argument('--JournalRedirect', type=str)
	Parser.add_argument('--FeedEntries', type=str)
	Parser.add_argument('--FolderRoots', type=str)
	Parser.add_argument('--DynamicParts', type=str)
	Parser.add_argument('--MarkdownExts', type=str)
	Parser.add_argument('--MastodonURL', type=str)
	Parser.add_argument('--MastodonToken', type=str)
	Parser.add_argument('--FeedCategoryFilter', type=str)
	Parser.add_argument('--ActivityPubTypeFilter', type=str, help=argparse.SUPPRESS)
	Parser.add_argument('--ActivityPubHoursLimit', type=int)
	Parser.add_argument('--CategoriesAutomatic', type=str)
	Parser.add_argument('--CategoriesUncategorized', type=str)
	Args = Parser.parse_args()

	ConfigLogging(Args.Logging)

	try:
		import lxml
		from Modules.Feed import *
		FeedEntries = Args.FeedEntries if Args.FeedEntries else 'Default'
	except:
		logging.warning("⚠ Can't load the XML libraries. XML Feeds Generation is Disabled. Make sure the 'lxml' library is installed.")
		FeedEntries = 0

	BuildMain(Args=Args, FeedEntries=FeedEntries)
	logging.info(f"✅ Done! ({round(time.time()-StartTime, 3)}s)")
