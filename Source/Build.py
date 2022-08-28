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
	
def ResetOutputDir(OutDir):
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

def CheckSafeOutputDir(OutDir):
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
	HavePages, HavePosts = False, False
	SiteConf = LoadConfFile('Site.ini')

	#if Args.InputDir:
	#	os.chdir(Args.InputDir)
	#	print(f"[I] Current directory: {Args.InputDir}")

	SiteName = OptionChoose('', Args.SiteName, ReadConf(SiteConf, 'Site', 'Name'))
	if SiteName:
		print(f"[I] Compiling: {SiteName}")

	OutputDir = OptionChoose('public', Args.OutputDir, ReadConf(SiteConf, 'Site', 'OutputDir'))
	OutputDir = OutputDir.removesuffix('/')
	CheckSafeOutputDir(OutputDir)
	print(f"[I] Outputting to {OutputDir}/")

	DiffBuild = Args.DiffBuild
	BlogName = OptionChoose('', Args.BlogName, ReadConf(SiteConf, 'Site', 'BlogName'))
	SiteTagline = OptionChoose('', Args.SiteTagline, ReadConf(SiteConf, 'Site', 'Tagline'))
	SiteTemplate = OptionChoose('Default.html', Args.SiteTemplate, ReadConf(SiteConf, 'Site', 'Template'))
	SiteDomain = OptionChoose('', Args.SiteDomain, ReadConf(SiteConf, 'Site', 'Domain'))
	SiteDomain = SiteDomain.removesuffix('/')
	SiteRoot = OptionChoose('/', Args.SiteRoot, ReadConf(SiteConf, 'Site', 'Root'))
	SiteLang = OptionChoose('en', Args.SiteLang, ReadConf(SiteConf, 'Site', 'Lang'))
	Locale = LoadLocale(SiteLang)
	MastodonURL = OptionChoose('', Args.MastodonURL, ReadConf(SiteConf, 'Mastodon', 'URL'))
	MastodonToken = OptionChoose('', Args.MastodonToken, ReadConf(SiteConf, 'Mastodon', 'Token'))
	DynamicParts = literal_eval(OptionChoose('{}', Args.DynamicParts, ReadConf(SiteConf, 'Site', 'DynamicParts'))) 
	MarkdownExts = literal_eval(OptionChoose(str(MarkdownExtsDefault), Args.MarkdownExts, ReadConf(SiteConf, 'Markdown', 'Exts')))
	ActivityPubTypeFilter = OptionChoose('Post', Args.ActivityPubTypeFilter, ReadConf(SiteConf, 'ActivityPub', 'TypeFilter'))
	ActivityPubHoursLimit = OptionChoose(168, Args.ActivityPubHoursLimit, ReadConf(SiteConf, 'ActivityPub', 'HoursLimit'))
	FeedCategoryFilter = OptionChoose('Blog', Args.FeedCategoryFilter, ReadConf(SiteConf, 'Feed', 'CategoryFilter'))
	Minify = StringBoolChoose(False, Args.Minify, ReadConf(SiteConf, 'Site', 'Minify'))
	NoScripts = StringBoolChoose(False, Args.NoScripts, ReadConf(SiteConf, 'Site', 'NoScripts'))
	ImgAltToTitle = StringBoolChoose(True, Args.ImgAltToTitle, ReadConf(SiteConf, 'Site', 'ImgAltToTitle'))
	ImgTitleToAlt = StringBoolChoose(False, Args.ImgTitleToAlt, ReadConf(SiteConf, 'Site', 'ImgTitleToAlt'))
	AutoCategories = StringBoolChoose(False, Args.AutoCategories, ReadConf(SiteConf, 'Site', 'AutoCategories'))
	GemtextOut = StringBoolChoose(False, Args.GemtextOut, ReadConf(SiteConf, 'Site', 'GemtextOut'))
	GemtextHeader = Args.GemtextHeader if Args.GemtextHeader else ReadConf(SiteConf, 'Gemtext', 'Header') if ReadConf(SiteConf, 'Gemtext', 'Header') else f"# {SiteName}\n\n" if SiteName else ''
	SitemapOut = StringBoolChoose(True, Args.SitemapOut, ReadConf(SiteConf, 'Site', 'SitemapOut'))
	FeedEntries = int(FeedEntries) if (FeedEntries or FeedEntries == 0) and FeedEntries != 'Default' else int(ReadConf(SiteConf, 'Site', 'FeedEntries')) if ReadConf(SiteConf, 'Site', 'FeedEntries') else 10
	Sorting = literal_eval(OptionChoose('{}', Args.Sorting, ReadConf(SiteConf, 'Site', 'Sorting')))

	MenuEntries = ReadConf(SiteConf, 'Menu')
	if MenuEntries:
		ConfMenu = GetConfMenu(MenuEntries, MarkdownExts)
	else:
		ConfMenu = []

	if DiffBuild:
		print("[I] Build mode: Differential")
		LimitFiles = GetModifiedFiles(OutputDir)
	else:
		print("[I] Build mode: Clean")
		ResetOutputDir(OutputDir)
		LimitFiles = False

	if os.path.isdir('Pages'):
		HavePages = True
		shutil.copytree('Pages', OutputDir, dirs_exist_ok=True)
		if GemtextOut:
			shutil.copytree('Pages', f"{OutputDir}.gmi", ignore=IgnoreFiles, dirs_exist_ok=True)
	if os.path.isdir('Posts'):
		HavePosts = True
		shutil.copytree('Posts', f"{OutputDir}/Posts", dirs_exist_ok=True)
		if GemtextOut:
			shutil.copytree('Posts', f"{OutputDir}.gmi/Posts", ignore=IgnoreFiles, dirs_exist_ok=True)

	if not (HavePages or HavePosts):
		print("[E] No Pages or posts found. Nothing to do, exiting!")
		exit(1)

	print("[I] Generating HTML")
	Pages = MakeSite(
		OutputDir=OutputDir,
		LimitFiles=LimitFiles,
		TemplatesText=LoadFromDir('Templates', ['*.htm', '*.html']),
		StaticPartsText=LoadFromDir('StaticParts', ['*.htm', '*.html']),
		DynamicParts=DynamicParts,
		DynamicPartsText=LoadFromDir('DynamicParts', ['*.htm', '*.html']),
		ConfMenu=ConfMenu,
		GlobalMacros=ReadConf(SiteConf, 'Macros'),
		SiteName=SiteName,
		BlogName=BlogName,
		SiteTagline=SiteTagline,
		SiteTemplate=SiteTemplate,
		SiteDomain=SiteDomain,
		SiteRoot=SiteRoot,
		FolderRoots=literal_eval(Args.FolderRoots) if Args.FolderRoots else {},
		SiteLang=SiteLang,
		Locale=Locale,
		Minify=Minify,
		NoScripts=NoScripts,
		ImgAltToTitle=ImgAltToTitle, ImgTitleToAlt=ImgTitleToAlt,
		Sorting=SetSorting(Sorting),
		MarkdownExts=MarkdownExts,
		AutoCategories=AutoCategories)

	if FeedEntries != 0:
		print("[I] Generating Feeds")
		for FeedType in (True, False):
			MakeFeed(
				OutputDir=OutputDir,
				CategoryFilter=FeedCategoryFilter,
				Pages=Pages,
				SiteName=SiteName,
				SiteTagline=SiteTagline,
				SiteDomain=SiteDomain,
				MaxEntries=FeedEntries,
				Lang=SiteLang,
				FullSite=FeedType,
				Minify=Minify)

	if ActivityPub and MastodonURL and MastodonToken and SiteDomain:
		print("[I] Mastodon Stuff")
		MastodonPosts = MastodonShare(
			InstanceURL=MastodonURL,
			Token=MastodonToken,
			Pages=Pages,
			SiteDomain=SiteDomain,
			SiteLang=SiteLang,
			Locale=Locale,
			TypeFilter=ActivityPubTypeFilter,
			CategoryFilter=FeedCategoryFilter,
			HoursLimit=ActivityPubHoursLimit)
	else:
		MastodonPosts = []

	for File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image in Pages:
		File = f"{OutputDir}/{StripExt(File)}.html"
		Content = ReadFile(File)
		Post = ''
		for p in MastodonPosts:
			if p['Link'] == SiteDomain + '/' + File[len(f"{OutputDir}/"):]:
				Post = '<br><h3>{StrComments}</h3><a href="{URL}" rel="noopener" target="_blank">{StrOpen} ↗️</a>'.format(
					StrComments=Locale['Comments'],
					StrOpen=Locale['OpenInNewTab'],
					URL=p['Post'])
				break
		Content = ReplWithEsc(Content, '[staticoso:Comments]', Post)
		WriteFile(File, Content)

	if GemtextOut:
		print("[I] Generating Gemtext")
		GemtextCompileList(OutputDir, Pages, GemtextHeader)

	print("[I] Cleaning Temporary Files")
	DelTmp(OutputDir)

	if SitemapOut:
		print("[I] Generating Sitemap")
		MakeSitemap(OutputDir, Pages, SiteDomain)

	print("[I] Copying Assets")
	os.system(f"cp -R Assets/* {OutputDir}/")

if __name__ == '__main__':
	Parser = argparse.ArgumentParser()
	Parser.add_argument('--DiffBuild', action='store_true')
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
	Parser.add_argument('--NoScripts', type=str)
	Parser.add_argument('--ImgAltToTitle', type=str)
	Parser.add_argument('--ImgTitleToAlt', type=str)
	Parser.add_argument('--GemtextOut', type=str)
	Parser.add_argument('--GemtextHeader', type=str)
	Parser.add_argument('--SiteTagline', type=str)
	Parser.add_argument('--SitemapOut', type=str)
	Parser.add_argument('--FeedEntries', type=str)
	Parser.add_argument('--FolderRoots', type=str)
	Parser.add_argument('--DynamicParts', type=str)
	Parser.add_argument('--MarkdownExts', type=str)
	Parser.add_argument('--MastodonURL', type=str)
	Parser.add_argument('--MastodonToken', type=str)
	Parser.add_argument('--FeedCategoryFilter', type=str)
	Parser.add_argument('--ActivityPubTypeFilter', type=str, help=argparse.SUPPRESS)
	Parser.add_argument('--ActivityPubHoursLimit', type=int)
	Parser.add_argument('--AutoCategories', type=str)
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
	print(f"[I] ✅ Done! ({round(time.process_time(),3)}s)")
