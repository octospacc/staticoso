""" ================================= |
| This file is part of                |
|   staticoso                         |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
|   Copyright (C) 2022, OctoSpacc     |
| ================================= """

from Libs.feedgen.feed import FeedGenerator
from Modules.Utils import *

def MakeFeed(Pages, SiteName, SiteTagline, SiteDomain, MaxEntries, Lang, Minify=False):
	Feed = FeedGenerator()
	Link = SiteDomain if SiteDomain else ' '
	Feed.id(Link)
	Feed.title(SiteName if SiteName else ' ')
	Feed.link(href=Link, rel='alternate')
	Feed.description(SiteTagline if SiteTagline else ' ')
	if SiteDomain:
		Feed.logo(SiteDomain.rstrip('/') + '/favicon.png')
	Feed.language(Lang)

	DoPages = []
	for e in Pages:
		if MaxEntries != 0 and e[3]['Type'] == 'Post':
			DoPages += [e]
			MaxEntries -= 1
	DoPages.reverse()

	for File, Content, Titles, Meta, HTMLContent, Description, Image in DoPages:
		if Meta['Type'] == 'Post':
			Entry = Feed.add_entry()
			File = '{}.html'.format(StripExt(File))
			Content = ReadFile('public/'+File)
			Link = SiteDomain+'/'+File if SiteDomain else ' '
			CreatedOn = GetFullDate(Meta['CreatedOn'])
			EditedOn = GetFullDate(Meta['EditedOn'])

			Entry.id(Link)
			Entry.title(Meta['Title'] if Meta['Title'] else ' ')
			Entry.description(Description)
			Entry.link(href=Link, rel='alternate')
			Entry.content(HTMLContent, type='html')
			if CreatedOn:
				Entry.pubDate(CreatedOn)
			EditedOn = EditedOn if EditedOn else CreatedOn if CreatedOn and not EditedOn else '1970-01-01T00:00+00:00'
			Entry.updated(EditedOn)

	os.mkdir('public/feed')
	Feed.atom_file('public/feed/atom.xml', pretty=(not Minify))
	Feed.rss_file('public/feed/rss.xml', pretty=(not Minify))
