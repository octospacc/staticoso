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

try:
	from Modules.ActivityPub import *
	ActivityPub = True
except:
	print("[W] ⚠ Can't load the ActivityPub module. Its use is disabled. Make sure the 'requests' library is installed.")
	ActivityPub = False

from Modules.Config import *
from Modules.Gemini import *
from Modules.Markdown import *
from Modules.Site import *
from Modules.Sitemap import *
from Modules.Utils import *
	
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
		print(f"[E] ⛔ Output and Input directories ({OutDir}) can't be the same. Exiting.")
		exit(1)
	elif OutFolder in ReservedPaths and f"{InDir}/{OutFolder}" == OutDir:
		print(f"[E] ⛔ Output directory {OutDir} can't be a reserved subdirectory of the Input. Exiting.")
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
	Flags, Snippets = {}, {}
	HavePages, HavePosts = False, False
	SiteConf = LoadConfFile('Site.ini')

	#if Args.InputDir:
	#	os.chdir(Args.InputDir)
	#	print(f"[I] Current directory: {Args.InputDir}")

	SiteName = Flags['SiteName'] = OptionChoose('', Args.SiteName, ReadConf(SiteConf, 'Site', 'Name'))
	if SiteName:
		print(f"[I] Compiling: {SiteName}")

	OutDir = Flags['OutDir'] = OptionChoose('public', Args.OutputDir, ReadConf(SiteConf, 'Site', 'OutputDir'))
	OutDir = Flags['OutDir'] = OutDir.removesuffix('/')
	CheckSafeOutDir(OutDir)
	print(f"[I] Outputting to: {OutDir}/")

	Logging = Args.Logging
	Threads = Args.Threads
	DiffBuild = Args.DiffBuild

	BlogName = Flags['BlogName'] = OptionChoose('', Args.BlogName, ReadConf(SiteConf, 'Site', 'BlogName'))
	SiteTagline = Flags['SiteTagline'] = OptionChoose('', Args.SiteTagline, ReadConf(SiteConf, 'Site', 'Tagline'))
	SiteTemplate = Flags['SiteTemplate'] = OptionChoose('Default.html', Args.SiteTemplate, ReadConf(SiteConf, 'Site', 'Template'))
	SiteDomain = Flags['SiteDomain'] = OptionChoose('', Args.SiteDomain, ReadConf(SiteConf, 'Site', 'Domain'))
	SiteRoot = Flags['SiteRoot'] = OptionChoose('/', Args.SiteRoot, ReadConf(SiteConf, 'Site', 'Root'))
	SiteLang = Flags['SiteLang'] = OptionChoose('en', Args.SiteLang, ReadConf(SiteConf, 'Site', 'Lang'))

	Sorting = Flags['Sorting'] = literal_eval(OptionChoose('{}', Args.Sorting, ReadConf(SiteConf, 'Site', 'Sorting')))
	Sorting = Flags['Sorting'] = SetSorting(Sorting)

	NoScripts = Flags['NoScripts'] = StringBoolChoose(False, Args.NoScripts, ReadConf(SiteConf, 'Site', 'NoScripts'))
	FolderRoots = Flags['FolderRoots'] = literal_eval(Args.FolderRoots) if Args.FolderRoots else {}

	ActivityPubTypeFilter = Flags['ActivityPubTypeFilter'] = OptionChoose('Post', Args.ActivityPubTypeFilter, ReadConf(SiteConf, 'ActivityPub', 'TypeFilter'))
	ActivityPubHoursLimit = Flags['ActivityPubHoursLimit'] = OptionChoose(168, Args.ActivityPubHoursLimit, ReadConf(SiteConf, 'ActivityPub', 'HoursLimit'))

	MastodonURL = Flags['MastodonURL'] = OptionChoose('', Args.MastodonURL, ReadConf(SiteConf, 'Mastodon', 'URL'))
	MastodonToken = Flags['MastodonToken'] = OptionChoose('', Args.MastodonToken, ReadConf(SiteConf, 'Mastodon', 'Token'))

	MarkdownExts = Flags['MarkdownExts'] = literal_eval(OptionChoose(str(MarkdownExtsDefault), Args.MarkdownExts, ReadConf(SiteConf, 'Markdown', 'Exts')))
	SitemapOutput = Flags['SitemapOutput'] = StringBoolChoose(True, Args.SitemapOutput, ReadConf(SiteConf, 'Sitemap', 'Output'))

	Minify = Flags['Minify'] = StringBoolChoose(False, Args.Minify, ReadConf(SiteConf, 'Minify', 'Minify'))
	MinifyKeepComments = Flags['MinifyKeepComments'] = StringBoolChoose(False, Args.MinifyKeepComments, ReadConf(SiteConf, 'Minify', 'KeepComments'))

	ImgAltToTitle = Flags['ImgAltToTitle'] = StringBoolChoose(True, Args.ImgAltToTitle, ReadConf(SiteConf, 'Site', 'ImgAltToTitle'))
	ImgTitleToAlt = Flags['ImgTitleToAlt'] = StringBoolChoose(False, Args.ImgTitleToAlt, ReadConf(SiteConf, 'Site', 'ImgTitleToAlt'))

	CategoriesAutomatic = Flags['CategoriesAutomatic'] = StringBoolChoose(False, Args.CategoriesAutomatic, ReadConf(SiteConf, 'Categories', 'Automatic'))
	CategoriesUncategorized = Flags['CategoriesUncategorized'] = OptionChoose('Uncategorized', Args.CategoriesUncategorized, ReadConf(SiteConf, 'Categories', 'Uncategorized'))

	GemtextOutput = Flags['GemtextOutput'] = StringBoolChoose(False, Args.GemtextOutput, ReadConf(SiteConf, 'Gemtext', 'Output'))
	GemtextHeader = Flags['GemtextHeader'] = Args.GemtextHeader if Args.GemtextHeader else ReadConf(SiteConf, 'Gemtext', 'Header') if ReadConf(SiteConf, 'Gemtext', 'Header') else f"# {SiteName}\n\n" if SiteName else ''

	FeedCategoryFilter = Flags['FeedCategoryFilter'] = OptionChoose('Blog', Args.FeedCategoryFilter, ReadConf(SiteConf, 'Feed', 'CategoryFilter'))
	FeedEntries = Flags['FeedEntries'] = int(FeedEntries) if (FeedEntries or FeedEntries == 0) and FeedEntries != 'Default' else int(ReadConf(SiteConf, 'Feed', 'Entries')) if ReadConf(SiteConf, 'Feed', 'Entries') else 10

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
		print("[I] Build mode: Differential")
		LimitFiles = GetModifiedFiles(OutDir)
	else:
		print("[I] Build mode: Clean")
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
		print("[E] No Pages or posts found. Nothing to do, exiting!")
		exit(1)

	print("[I] Generating HTML")
	Pages = MakeSite(
		Flags=Flags,
		LimitFiles=LimitFiles,
		Snippets=Snippets,
		ConfMenu=ConfMenu,
		GlobalMacros=ReadConf(SiteConf, 'Macros'),
		Locale=Locale)

	if FeedEntries != 0:
		print("[I] Generating Feeds")
		for FeedType in (True, False):
			MakeFeed(Flags, Pages, FeedType)

	if ActivityPub and MastodonURL and MastodonToken and SiteDomain:
		print("[I] Mastodon Stuff")
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
				Post = '<br><h3>{StrComments}</h3><a href="{URL}" rel="noopener" target="_blank">{StrOpen} ↗️</a>'.format(
					StrComments=Locale['Comments'],
					StrOpen=Locale['OpenInNewTab'],
					URL=p['Post'])
				break
		Content = ReplWithEsc(Content, '[staticoso:Comments]', Post)
		WriteFile(File, Content)

	if Flags['GemtextOutput']:
		print("[I] Generating Gemtext")
		GemtextCompileList(Flags, Pages, LimitFiles)

	print("[I] Cleaning Temporary Files")
	DelTmp(OutDir)

	if Flags['SitemapOutput']:
		print("[I] Generating Sitemap")
		MakeSitemap(Flags, Pages)

	print("[I] Copying Assets")
	os.system(f"cp -R Assets/* {OutDir}/")

if __name__ == '__main__':
	StartTime = time.time()

	Parser = argparse.ArgumentParser()
	Parser.add_argument('--Logging', type=str) # Levels: Debug, Verbose, Info, Warning, Error.
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

	try:
		import lxml
		from Modules.Feed import *
		FeedEntries = Args.FeedEntries if Args.FeedEntries else 'Default'
	except:
		print("[W] ⚠ Can't load the XML libraries. XML Feeds Generation is Disabled. Make sure the 'lxml' library is installed.")
		FeedEntries = 0

	Main(
		Args=Args,
		FeedEntries=FeedEntries)
	print(f"[I] ✅ Done! ({round(time.time()-StartTime,3)}s)")
