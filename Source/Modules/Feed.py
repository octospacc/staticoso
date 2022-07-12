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

def MakeFeed(Pages, SiteName, SiteTagline, SiteDomain, MaxEntries, Lang, FullMap=False, Minify=False):
	Feed = FeedGenerator()
	Link = SiteDomain if SiteDomain else ' '
	Feed.id(Link)
	Feed.title(SiteName if SiteName else ' ')
	Feed.link(href=Link, rel='alternate')
	Feed.description(SiteTagline if SiteTagline else ' ')
	if SiteDomain:
		Feed.logo(SiteDomain + '/favicon.png')
	Feed.language(Lang)

	DoPages = []
	if FullMap:
		MaxEntries = 50000 # Sitemap standard limit
	for e in Pages:
		if MaxEntries != 0 and (FullMap or (not FullMap and e[3]['Type'] == 'Post')):
			DoPages += [e]
			MaxEntries -= 1
	DoPages.reverse()

	for File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image in DoPages:
		if FullMap or (not FullMap and Meta['Type'] == 'Post'):
			Entry = Feed.add_entry()
			File = '{}.html'.format(StripExt(File))
			Content = ReadFile('public/'+File)
			Link = SiteDomain + '/' + File if SiteDomain else ' '
			CreatedOn = GetFullDate(Meta['CreatedOn'])
			EditedOn = GetFullDate(Meta['EditedOn'])
			Entry.id(Link)
			Entry.title(Meta['Title'] if Meta['Title'] else ' ')
			Entry.description(Description)
			Entry.link(href=Link, rel='alternate')
			Entry.content(ContentHTML, type='html')
			if CreatedOn:
				Entry.pubDate(CreatedOn)
			EditedOn = EditedOn if EditedOn else CreatedOn if CreatedOn and not EditedOn else '1970-01-01T00:00+00:00'
			Entry.updated(EditedOn)

	if FullMap:
		Feed.atom_file('public/sitemap.xml', pretty=(not Minify))
	else:
		os.mkdir('public/feed')
		Feed.atom_file('public/feed/atom.xml', pretty=(not Minify))
		Feed.rss_file('public/feed/rss.xml', pretty=(not Minify))
