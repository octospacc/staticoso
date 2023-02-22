""" ================================= |
| This file is part of                |
|   staticoso                         |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
|   Copyright (C) 2022, OctoSpacc     |
| ================================= """

# TODO: Either switch feed generation lib, or rewrite the 'lxml' module, so that no modules have to be compiled and the program is 100% portable

from Libs.feedgen.feed import FeedGenerator
from Modules.Utils import *

def MakeFeed(Flags, Pages, FullSite=False):
	CategoryFilter = Flags['FeedCategoryFilter']
	MaxEntries = Flags['FeedEntries']

	Feed = FeedGenerator()
	Link = Flags['SiteDomain'] if Flags['SiteDomain'] else ' '
	Feed.id(Link)
	Feed.title(Flags['SiteName'] if Flags['SiteName'] else 'Untitled Site')
	Feed.link(href=Link, rel='alternate')
	Feed.description(Flags['SiteTagline'] if Flags['SiteTagline'] else ' ')
	if Flags['SiteDomain']:
		Feed.logo(Flags['SiteDomain'] + '/favicon.png')
	Feed.language(Flags['SiteLang'])

	DoPages = []
	for e in Pages:
		if FullSite or (not FullSite and MaxEntries != 0 and e[3]['Type'] == 'Post' and e[3]['Feed'] == 'True'): # No entry limit if site feed
			DoPages += [e]
			MaxEntries -= 1
	DoPages.reverse()

	for File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image in DoPages:
		if FullSite or (not FullSite and Meta['Type'] == 'Post' and (not CategoryFilter or (CategoryFilter and (CategoryFilter in Meta['Categories'] or CategoryFilter == '*')))):
			Entry = Feed.add_entry()
			FileName = File.split('/')[-1]
			File = f"{StripExt(File)}.html"
			Content = ReadFile(f"{Flags['OutDir']}/{File}")
			Link = Flags['SiteDomain'] + '/' + File if Flags['SiteDomain'] else ' '
			CreatedOn = GetFullDate(Meta['CreatedOn'])
			EditedOn = GetFullDate(Meta['EditedOn'])
			Entry.id(Link)
			Title = Meta['Title'] if Meta['Title'] else Titles[0].lstrip('#') if Titles else FileName
			Entry.title(Title.lstrip().rstrip())
			Entry.description(Description)
			Entry.link(href=Link, rel='alternate')
			if not FullSite: # Avoid making an enormous site feed file...
				Entry.content(ContentHTML, type='html')
			if CreatedOn:
				Entry.pubDate(CreatedOn)
			EditedOn = EditedOn if EditedOn else CreatedOn if CreatedOn and not EditedOn else '1970-01-01T00:00+00:00'
			Entry.updated(EditedOn)

	if not os.path.exists(f"{Flags['OutDir']}/feed"):
		os.mkdir(f"{Flags['OutDir']}/feed")
	FeedType = 'site.' if FullSite else ''
	Feed.atom_file(f"{Flags['OutDir']}/feed/{FeedType}atom.xml", pretty=(not Flags['MinifyOutput']))
	Feed.rss_file(f"{Flags['OutDir']}/feed/{FeedType}rss.xml", pretty=(not Flags['MinifyOutput']))
