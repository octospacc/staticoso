#!/usr/bin/env python3
""" ================================= |
| This file is part of                |
|   staticoso                         |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
|   Copyright (C) 2022, OctoSpacc     |
| ================================= """

import argparse
import os
import shutil
import time
from ast import literal_eval
from datetime import datetime
from pathlib import Path

from Modules.Config import *
from Modules.Gemini import *
from Modules.Logging import *
from Modules.Markdown import *
from Modules.Site import *
from Modules.Sitemap import *
from Modules.Utils import *

try:
	from Modules.ActivityPub import *
	ActivityPub = True
except:
	logging.warning("⚠ Can't load the ActivityPub module. Its use is disabled. Make sure the 'requests' library is installed.")
	ActivityPub = False

def ResetOutDir(OutDir):
	for e in (OutDir, f"{OutDir}.gmi"):
		try:
			shutil.rmtree(e)
		except FileNotFoundError:
			pass

def DelTmp(OutDir):
	for Ext in FileExtensions['Tmp']:
		for File in Path(OutDir).rglob(f"*.{Ext}"):
			os.remove(File)
	for Dir in (OutDir, f"{OutDir}.gmi"):
		for File in Path(Dir).rglob('*.tmp'):
			os.remove(File)

def SetSorting(Sorting):
	Default = {
		'Pages':'Standard',
		'Posts':'Inverse'}
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

def CheckSafeOutDir(OutDir):
	InDir = os.path.realpath(os.getcwd())
	OutDir = os.path.realpath(OutDir)
	OutFolder = OutDir.split('/')[-1]
	if InDir == OutDir:
		logging.error(f"⛔ Output and Input directories ({OutDir}) can't be the same. Exiting.")
		exit(1)
	elif OutFolder in ReservedPaths and f"{InDir}/{OutFolder}" == OutDir:
		logging.error(f"⛔ Output directory {OutDir} can't be a reserved subdirectory of the Input. Exiting.")
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

def Main(Args, FeedEntries):
	Flags, Snippets, FinalPaths = {}, {}, []
	HavePages, HavePosts = False, False
	SiteConf = LoadConfFile('Site.ini')

	ConfigLogging(DefConfOptChoose('Logging', Args.Logging, ReadConf(SiteConf, 'Main', 'Logging')))

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

	Threads = Args.Threads if Args.Threads else 0
	DiffBuild = Args.DiffBuild if Args.DiffBuild else False

	BlogName = Flags['BlogName'] = OptChoose('', Args.BlogName, ReadConf(SiteConf, 'Site', 'BlogName'))
	SiteTagline = Flags['SiteTagline'] = OptChoose('', Args.SiteTagline, ReadConf(SiteConf, 'Site', 'Tagline'))
	SiteTemplate = Flags['SiteTemplate'] = DefConfOptChoose('SiteTemplate', Args.SiteTemplate, ReadConf(SiteConf, 'Site', 'Template'))
	SiteDomain = Flags['SiteDomain'] = OptChoose('', Args.SiteDomain, ReadConf(SiteConf, 'Site', 'Domain'))
	SiteRoot = Flags['SiteRoot'] = OptChoose('/', Args.SiteRoot, ReadConf(SiteConf, 'Site', 'Root'))
	SiteLang = Flags['SiteLang'] = DefConfOptChoose('SiteLang', Args.SiteLang, ReadConf(SiteConf, 'Site', 'Lang'))

	Sorting = Flags['Sorting'] = literal_eval(OptChoose('{}', Args.Sorting, ReadConf(SiteConf, 'Site', 'Sorting')))
	Sorting = Flags['Sorting'] = SetSorting(Sorting)

	NoScripts = Flags['NoScripts'] = StrBoolChoose(False, Args.NoScripts, ReadConf(SiteConf, 'Site', 'NoScripts'))
	FolderRoots = Flags['FolderRoots'] = literal_eval(Args.FolderRoots) if Args.FolderRoots else {}

	ActivityPubTypeFilter = Flags['ActivityPubTypeFilter'] = DefConfOptChoose('ActivityPubTypeFilter', Args.ActivityPubTypeFilter, ReadConf(SiteConf, 'ActivityPub', 'TypeFilter'))
	ActivityPubHoursLimit = Flags['ActivityPubHoursLimit'] = DefConfOptChoose('ActivityPubHoursLimit', Args.ActivityPubHoursLimit, ReadConf(SiteConf, 'ActivityPub', 'HoursLimit'))

	MastodonURL = Flags['MastodonURL'] = OptChoose('', Args.MastodonURL, ReadConf(SiteConf, 'Mastodon', 'URL'))
	MastodonToken = Flags['MastodonToken'] = OptChoose('', Args.MastodonToken, ReadConf(SiteConf, 'Mastodon', 'Token'))

	MarkdownExts = Flags['MarkdownExts'] = literal_eval(OptionChoose(str(MarkdownExtsDefault), Args.MarkdownExts, ReadConf(SiteConf, 'Markdown', 'Exts')))
	SitemapOutput = Flags['SitemapOutput'] = StrBoolChoose(True, Args.SitemapOutput, ReadConf(SiteConf, 'Sitemap', 'Output'))

	Minify = Flags['Minify'] = StrBoolChoose(False, Args.Minify, ReadConf(SiteConf, 'Minify', 'Minify'))
	MinifyKeepComments = Flags['MinifyKeepComments'] = StrBoolChoose(False, Args.MinifyKeepComments, ReadConf(SiteConf, 'Minify', 'KeepComments'))

	ImgAltToTitle = Flags['ImgAltToTitle'] = StrBoolChoose(True, Args.ImgAltToTitle, ReadConf(SiteConf, 'Site', 'ImgAltToTitle'))
	ImgTitleToAlt = Flags['ImgTitleToAlt'] = StrBoolChoose(False, Args.ImgTitleToAlt, ReadConf(SiteConf, 'Site', 'ImgTitleToAlt'))
	HTMLFixPre = Flags['HTMLFixPre'] = StrBoolChoose(False, Args.HTMLFixPre, ReadConf(SiteConf, 'Site', 'HTMLFixPre'))

	CategoriesAutomatic = Flags['CategoriesAutomatic'] = StrBoolChoose(False, Args.CategoriesAutomatic, ReadConf(SiteConf, 'Categories', 'Automatic'))
	CategoriesUncategorized = Flags['CategoriesUncategorized'] = DefConfOptChoose('CategoriesUncategorized', Args.CategoriesUncategorized, ReadConf(SiteConf, 'Categories', 'Uncategorized'))

	GemtextOutput = Flags['GemtextOutput'] = StrBoolChoose(False, Args.GemtextOutput, ReadConf(SiteConf, 'Gemtext', 'Output'))
	GemtextHeader = Flags['GemtextHeader'] = Args.GemtextHeader if Args.GemtextHeader else ReadConf(SiteConf, 'Gemtext', 'Header') if ReadConf(SiteConf, 'Gemtext', 'Header') else f"# {SiteName}\n\n" if SiteName else ''

	FeedCategoryFilter = Flags['FeedCategoryFilter'] = DefConfOptChoose('FeedCategoryFilter', Args.FeedCategoryFilter, ReadConf(SiteConf, 'Feed', 'CategoryFilter'))
	FeedEntries = Flags['FeedEntries'] = int(FeedEntries) if (FeedEntries or FeedEntries == 0) and FeedEntries != 'Default' else int(ReadConf(SiteConf, 'Feed', 'Entries')) if ReadConf(SiteConf, 'Feed', 'Entries') else DefConf['FeedEntries']

	DynamicParts = Flags['DynamicParts'] = literal_eval(OptionChoose('{}', Args.DynamicParts, ReadConf(SiteConf, 'Site', 'DynamicParts')))
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

	if os.path.isdir('Pages'):
		HavePages = True
		shutil.copytree('Pages', OutDir, dirs_exist_ok=True)
		if Flags['GemtextOutput']:
			shutil.copytree('Pages', f"{OutDir}.gmi", ignore=IgnoreFiles, dirs_exist_ok=True)
	if os.path.isdir('Posts'):
		HavePosts = True
		shutil.copytree('Posts', f"{OutDir}/Posts", dirs_exist_ok=True)
		if Flags['GemtextOutput']:
			shutil.copytree('Posts', f"{OutDir}.gmi/Posts", ignore=IgnoreFiles, dirs_exist_ok=True)

	if not (HavePages or HavePosts):
		logging.error("⛔ No Pages or posts found. Nothing to do, exiting!")
		exit(1)

	logging.info("Generating HTML")
	Pages = MakeSite(
		Flags=Flags,
		LimitFiles=LimitFiles,
		Snippets=Snippets,
		ConfMenu=ConfMenu,
		GlobalMacros=ReadConf(SiteConf, 'Macros'),
		Locale=Locale,
		Threads=Threads)

	if FeedEntries != 0:
		logging.info("Generating Feeds")
		for FeedType in (True, False):
			MakeFeed(Flags, Pages, FeedType)

	if ActivityPub and MastodonURL and MastodonToken and SiteDomain:
		logging.info("Mastodon Stuff")
		MastodonPosts = MastodonShare(Flags, Pages, Locale)
	else:
		MastodonPosts = []

	for File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image in Pages:
		if IsLightRun(File, LimitFiles):
			continue
		File = f"{OutDir}/{StripExt(File)}.html"
		Content = ReadFile(File)
		Post = ''
		for p in MastodonPosts:
			if p['Link'] == SiteDomain + '/' + File[len(f"{OutDir}/"):]:
				Post = HTMLCommentsBlock.format(
					StrComments=Locale['Comments'],
					StrOpen=Locale['OpenInNewTab'],
					URL=p['Post'])
				break
		Content = ReplWithEsc(Content, '[staticoso:Comments]', Post)
		Content = ReplWithEsc(Content, '<staticoso:Comments>', Post)
		WriteFile(File, Content)
		FinalPaths += [File]

	logging.info("Creating Redirects")
	for File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image in Pages:
		for URL in Meta['URLs']:
			DestFile = f"{OutDir}/{URL}"
			if DestFile not in FinalPaths:
				DestURL = f"{GetPathLevels(URL)}{StripExt(File)}.html"
				mkdirps(os.path.dirname(DestFile))
				WriteFile(
					DestFile,
					RedirectPageTemplate.format(
						DestURL=DestURL,
						TitlePrefix=f"{SiteName} - " if SiteName else '',
						StrClick=Locale['ClickHere'],
						StrRedirect=Locale['IfNotRedirected']))

	if Flags['GemtextOutput']:
		logging.info("Generating Gemtext")
		GemtextCompileList(Flags, Pages, LimitFiles)

	logging.info("Cleaning Temporary Files")
	DelTmp(OutDir)

	if Flags['SitemapOutput']:
		logging.info("Generating Sitemap")
		MakeSitemap(Flags, Pages)

	logging.info("Copying Assets")
	os.system(f"cp -R Assets/* {OutDir}/")

if __name__ == '__main__':
	StartTime = time.time()

	Parser = argparse.ArgumentParser()
	Parser.add_argument('--Logging', type=str) # Levels: Debug, Info, Warning, Error.
	Parser.add_argument('--Threads', type=str)
	Parser.add_argument('--DiffBuild', type=str)
	Parser.add_argument('--OutputDir', type=str)
	#Parser.add_argument('--InputDir', type=str)
	Parser.add_argument('--Sorting', type=str)
	Parser.add_argument('--SiteLang', type=str)
	Parser.add_argument('--SiteRoot', type=str)
	Parser.add_argument('--SiteName', type=str)
	Parser.add_argument('--BlogName', type=str)
	Parser.add_argument('--SiteTemplate', type=str)
	Parser.add_argument('--SiteDomain', type=str)
	Parser.add_argument('--Minify', type=str)
	Parser.add_argument('--MinifyKeepComments', type=str)
	Parser.add_argument('--NoScripts', type=str)
	Parser.add_argument('--ImgAltToTitle', type=str)
	Parser.add_argument('--ImgTitleToAlt', type=str)
	Parser.add_argument('--HTMLFixPre', type=str)
	Parser.add_argument('--GemtextOutput', type=str)
	Parser.add_argument('--GemtextHeader', type=str)
	Parser.add_argument('--SiteTagline', type=str)
	Parser.add_argument('--SitemapOutput', type=str)
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

	Main(
		Args=Args,
		FeedEntries=FeedEntries)
	logging.info(f"✅ Done! ({round(time.time()-StartTime, 3)}s)")
