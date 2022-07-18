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
from ast import literal_eval
from datetime import datetime
from pathlib import Path

try:
	from Modules.ActivityPub import *
	ActivityPub = True
except:
	print("[E] Can't load the ActivityPub module. Its use is disabled. Make sure the 'requests' library is installed.")
	ActivityPub = False

from Modules.Config import *
from Modules.Gemini import *
from Modules.Markdown import *
from Modules.Site import *
from Modules.Sitemap import *
from Modules.Utils import *

def ResetPublic():
	for i in ('public', 'public.gmi'):
		try:
			shutil.rmtree(i)
		except FileNotFoundError:
			pass

def DelTmp():
	for Ext in FileExtensions['Pages']:
		for File in Path('public').rglob('*.{}'.format(Ext)):
			os.remove(File)
	for Dir in ('public', 'public.gmi'):
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
		for i in range(Max+1):
			Menu += [[]]
		for i in Entries:
			e = Entries[i]
			if not ((e.startswith('<') or e.startswith('[') or e.startswith('- ')) and (e.endswith('>') or e.endswith(')') or e.endswith(' }'))):
				if not e.lower().endswith('.html'):
					e += '.html'
			Menu[int(i)] = e
	return Menu

def Main(Args, FeedEntries):
	HavePages, HavePosts = False, False
	SiteConf = LoadConf('Site.ini')

	SiteName = Args.SiteName if Args.SiteName else ReadConf(SiteConf, 'Site', 'Name') if ReadConf(SiteConf, 'Site', 'Name') else ''
	BlogName = Args.BlogName if Args.BlogName else ReadConf(SiteConf, 'Site', 'BlogName') if ReadConf(SiteConf, 'Site', 'BlogName') else ''
	SiteTagline = Args.SiteTagline if Args.SiteTagline else ReadConf(SiteConf, 'Site', 'Tagline') if ReadConf(SiteConf, 'Site', 'Tagline') else ''
	SiteDomain = Args.SiteDomain.rstrip('/') if Args.SiteDomain else ReadConf(SiteConf, 'Site', 'Domain') if ReadConf(SiteConf, 'Site', 'Domain') else ''
	SiteLang = Args.SiteLang if Args.SiteLang else ReadConf(SiteConf, 'Site', 'Lang') if ReadConf(SiteConf, 'Site', 'Lang') else 'en'
	Locale = LoadLocale(SiteLang)
	MastodonURL = Args.MastodonURL if Args.MastodonURL else ''
	MastodonToken = Args.MastodonToken if Args.MastodonToken else ''
	MarkdownExts = literal_eval(Args.MarkdownExts) if Args.MarkdownExts else EvalOpt(ReadConf(SiteConf, 'Site', 'MarkdownExts')) if ReadConf(SiteConf, 'Site', 'MarkdownExts') else ('attr_list', 'def_list', 'markdown_del_ins', 'mdx_subscript', 'mdx_superscript')

	Minify = False
	if Args.Minify != None:
		if Args.Minify not in ('False', 'None'):
			Minify = True
	else:
		if ReadConf(SiteConf, 'Site', 'Minify') != None:
			if ReadConf(SiteConf, 'Site', 'Minify') not in ('False', 'None'):
				Minify = True

	AutoCategories = False
	if Args.AutoCategories != None:
		if literal_eval(Args.AutoCategories) == True:
			AutoCategories = True
	else:
		if ReadConf(SiteConf, 'Site', 'AutoCategories') != None:
			if EvalOpt(ReadConf(SiteConf, 'Site', 'AutoCategories')) == True:
				AutoCategories = True

	Entries = ReadConf(SiteConf, 'Menu')
	if Entries:
		ConfMenu = GetConfMenu(Entries, MarkdownExts)
	else:
		ConfMenu = []

	ResetPublic()

	if os.path.isdir('Pages'):
		HavePages = True
		shutil.copytree('Pages', 'public')
		if Args.GemtextOut:
			shutil.copytree('Pages', 'public.gmi', ignore=IgnoreFiles)
	if os.path.isdir('Posts'):
		HavePosts = True
		shutil.copytree('Posts', 'public/Posts')
		if Args.GemtextOut:
			shutil.copytree('Posts', 'public.gmi/Posts', ignore=IgnoreFiles)

	if not HavePages and not HavePosts:
		print("[E] No Pages or posts found. Nothing to do, exiting!")
		exit()

	print("[I] Generating HTML")
	Pages = MakeSite(
		TemplatesText=LoadFromDir('Templates', '*.html'),
		PartsText=LoadFromDir('Parts', '*.html'),
		ContextParts=literal_eval(Args.ContextParts) if Args.ContextParts else {},
		ContextPartsText=LoadFromDir('ContextParts', '*.html'),
		ConfMenu=ConfMenu,
		SiteName=SiteName,
		BlogName=BlogName,
		SiteTagline=SiteTagline,
		SiteDomain=SiteDomain,
		SiteRoot=Args.SiteRoot if Args.SiteRoot else '/',
		FolderRoots=literal_eval(Args.FolderRoots) if Args.FolderRoots else {},
		SiteLang=SiteLang,
		Locale=Locale,
		Minify=Minify,
		NoScripts=True if Args.NoScripts else False,
		Sorting=SetSorting(literal_eval(Args.ContextParts) if Args.ContextParts else {}),
		MarkdownExts=MarkdownExts,
		AutoCategories=AutoCategories)

	if FeedEntries != 0:
		print("[I] Generating Feeds")
		for FeedType in (True, False):
			MakeFeed(
				Pages=Pages,
				SiteName=SiteName,
				SiteTagline=SiteTagline,
				SiteDomain=SiteDomain,
				MaxEntries=FeedEntries,
				Lang=SiteLang,
				FullSite=FeedType,
				Minify=Minify)

	if Args.SitemapOut:
		print("[I] Generating Sitemap")
		MakeSitemap(Pages, SiteDomain)

	if ActivityPub and MastodonURL and MastodonToken and SiteDomain:
		print("[I] Mastodon Stuff")
		MastodonPosts = MastodonShare(
			MastodonURL,
			MastodonToken,
			Pages,
			SiteDomain,
			SiteLang,
			Locale,
			TypeFilter=Args.ActivityPubTypeFilter if Args.ActivityPubTypeFilter else 'Post',
			CategoryFilter=Args.ActivityPubCategoryFilter if Args.ActivityPubCategoryFilter else 'Blog',
			HoursLimit=Args.ActivityPubHoursLimit if Args.ActivityPubHoursLimit else 168)
	else:
		MastodonPosts = []

	for File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image in Pages:
		File = 'public/{}.html'.format(StripExt(File))
		Content = ReadFile(File)
		Post = ''
		for p in MastodonPosts:
			if p['Link'] == SiteDomain + '/' + File[len('public/'):]:
				Post = '<br><h3>{StrComments}</h3><a href="{URL}" rel="noopener" target="_blank">{StrOpen} ↗️</a>'.format(
					StrComments=Locale['Comments'],
					StrOpen=Locale['OpenInNewTab'],
					URL=p['Post'])
				break
		Content = Content.replace('[HTML:Comments]', Post)
		WriteFile(File, Content)

	if Args.GemtextOut:
		print("[I] Generating Gemtext")
		GemtextCompileList(
			Pages,
			Header=Args.GemtextHeader if Args.GemtextHeader else '# {}\n\n'.format(SiteName) if SiteName else '')

	print("[I] Last Steps")
	DelTmp()
	os.system("cp -R Assets/* public/")

	print("[I] Done!")

if __name__ == '__main__':
	Parser = argparse.ArgumentParser()
	Parser.add_argument('--Minify', type=str)
	Parser.add_argument('--Sorting', type=str)
	Parser.add_argument('--SiteLang', type=str)
	Parser.add_argument('--SiteRoot', type=str)
	Parser.add_argument('--SiteName', type=str)
	Parser.add_argument('--BlogName', type=str)
	Parser.add_argument('--SiteDomain', type=str)
	Parser.add_argument('--NoScripts', type=bool)
	Parser.add_argument('--GemtextOut', type=bool)
	Parser.add_argument('--GemtextHeader', type=str)
	Parser.add_argument('--SiteTagline', type=str)
	Parser.add_argument('--SitemapOut', type=bool)
	Parser.add_argument('--FeedEntries', type=int)
	Parser.add_argument('--FolderRoots', type=str)
	Parser.add_argument('--ContextParts', type=str)
	Parser.add_argument('--MarkdownExts', type=str)
	Parser.add_argument('--MastodonURL', type=str)
	Parser.add_argument('--MastodonToken', type=str)
	Parser.add_argument('--ActivityPubTypeFilter', type=str)
	Parser.add_argument('--ActivityPubCategoryFilter', type=str)
	Parser.add_argument('--ActivityPubHoursLimit', type=int)
	Parser.add_argument('--AutoCategories', type=str)
	Args = Parser.parse_args()

	try:
		import lxml
		from Modules.Feed import *
		FeedEntries = Args.FeedEntries if Args.FeedEntries or Args.FeedEntries == 0 else 10
	except:
		print("[E] Can't load the XML libraries. XML Feeds Generation is Disabled. Make sure the 'lxml' library is installed.")
		FeedEntries = 0

	Main(
		Args=Args,
		FeedEntries=FeedEntries)
