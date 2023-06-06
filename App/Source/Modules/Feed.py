""" ================================== |
| This file is part of                 |
|   staticoso                          |
| Just a simple Static Site Generator  |
|                                      |
| Licensed under the AGPLv3 license    |
|   Copyright (C) 2022-2023, OctoSpacc |
| ================================== """

from datetime import datetime
from Modules.Utils import *

FeedGenerator = None
try:
	import lxml
	from Libs.feedgen.feed import FeedGenerator
except:
	logging.warning("⚠ Can't load the native XML libraries. XML Feeds Generation will use the interpreted module.")

def MakeFeed(Flags:dict, Pages:list, FullSite:bool=False):
	f = NameSpace(Flags)
	CategoryFilter = Flags['FeedCategoryFilter']
	MaxEntries = Flags['FeedEntries']

	if FeedGenerator:
		Feed = FeedGenerator()
		Link = Flags['SiteDomain'] if Flags['SiteDomain'] else ' '
		Feed.id(Link)
		Feed.link(href=Link, rel='alternate')
		Feed.title(Flags['SiteName'])
		Feed.description(Flags['SiteTagline'] if Flags['SiteTagline'] else ' ')
		if Flags['SiteDomain']:
			Feed.logo(f'{Flags["SiteDomain"]}/favicon.png')
		Feed.language(Flags['SiteLang'])
	else:
		FeedData = {
			'Link': Flags['SiteDomain'],
			'Title': Flags['SiteName'],
			'Description': Flags['SiteTagline'],
			'Language': Flags['SiteLang'],
			'Entries': [],
		}

	DoPages = []
	for e in Pages:
		# No entry limit if site feed
		if FullSite or (not FullSite and MaxEntries != 0 and e[3]['Type'] == 'Post' and e[3]['Feed'] == 'True'):
			DoPages += [e]
			MaxEntries -= 1
	DoPages.reverse()

	for File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image in DoPages:
		if FullSite or (not FullSite and Meta['Type'] == 'Post' and (not CategoryFilter or (CategoryFilter and (CategoryFilter in Meta['Categories'] or CategoryFilter == '*')))):
			File = f'{StripExt(File)}.html'
			Link = Flags['SiteDomain'] + '/' + File if Flags['SiteDomain'] else File
			Title = Meta['Title'] if Meta['Title'] else Titles[0].lstrip('#') if Titles else File.split('/')[-1]
			Title = Title.lstrip().rstrip()
			CreatedOn = GetFullDate(Meta['CreatedOn'])
			EditedOn = GetFullDate(Meta['EditedOn'])
			if FullSite: # Avoid making an enormous site feed file...
				ContentHTML = ''
			if FeedGenerator:
				Entry = Feed.add_entry()
				Entry.id(Link)
				Entry.link(href=Link, rel='alternate')
				Entry.title(Title)
				Entry.description(Description)
				if ContentHTML: 
					Entry.content(ContentHTML, type='html')
				if CreatedOn:
					Entry.pubDate(CreatedOn)
				EditedOn = EditedOn if EditedOn else CreatedOn if CreatedOn and not EditedOn else '1970-01-01T00:00+00:00'
				Entry.updated(EditedOn)
			else:
				FeedData['Entries'] += [{
					'Link': Link,
					'Title': Title,
					'Description': Description,
					'Content': ContentHTML,
					'PublishedOn': CreatedOn,
					'UpdatedOn': EditedOn,
				}]

	if not os.path.exists(f"{Flags['OutDir']}/feed"):
		os.mkdir(f"{Flags['OutDir']}/feed")
	FeedType = 'site.' if FullSite else ''
	if FeedGenerator:
		Feed.atom_file(f"{Flags['OutDir']}/feed/{FeedType}atom.xml", pretty=(not Flags['MinifyOutput']))
		Feed.rss_file(f"{Flags['OutDir']}/feed/{FeedType}rss.xml", pretty=(not Flags['MinifyOutput']))
	else:
		Feeds = PyFeedGenerator(FeedData)
		for Format in ('atom', 'rss'):
			WriteFile(f"{Flags['OutDir']}/feed/{FeedType}{Format}.xml", Feeds[Format])

def PyFeedGenerator(Data:dict, Format:bool=None):
	XmlEntries = {'atom': '', 'rss': ''}
	XmlExtra, AtomExtra, RssExtra = '', '', ''
	XmlHeader = '<?xml version="1.0" encoding="UTF-8"?>'
	XmlLang = f'xml:lang="{Data["Language"]}"'
	XmlTitle = f'<title>{Data["Title"]}</title>'
	XmlExtra += XmlTitle
	if Data['Description']:
		AtomExtra += f'<subtitle>{Data["Description"]}</subtitle>'
		RssExtra += f'<description>{Data["Description"]}</description>'
	if Data['Link']:
		IconUrl = f'{Data["Link"]}/favicon.png'
		AtomExtra += f'<id>{Data["Link"]}</id><link href="{Data["Link"]}"/><logo>{IconUrl}</logo>'
		RssExtra += f'<link>{Data["Link"]}</link><image>{XmlTitle}<url>{IconUrl}</url><link>{Data["Link"]}</link></image>'
	Entries = Data['Entries'] if Data['Entries'] else ()
	for Entry in Data['Entries']:
		XmlEntryExtra, AtomEntryExtra, RssEntryExtra = '', '', ''
		XmlEntryExtra += f'<title>{Entry["Title"]}</title>'
		if Entry['Description']:
			RssEntryExtra += f'<description>{Entry["Description"]}</description>'
		if Entry['Content']:
			AtomEntryExtra += f'<content type="html">{Entry["Content"]}</content>'
			RssEntryExtra += f'<content:encoded>{Entry["Content"]}</content:encoded>'
		if Entry['PublishedOn']:
			AtomEntryExtra += f'<published>{Entry["PublishedOn"]}</published>'
			RssEntryExtra += f'<pubDate>{Entry["PublishedOn"]}</pubDate>'
		if Entry['UpdatedOn']:
			AtomEntryExtra += f'<updated>{Entry["UpdatedOn"]}</updated>'
		XmlEntries['atom'] += f'''
<entry>
	<id>{Entry['Link']}</id>
	<link href="{Entry['Link']}"/>
	{XmlEntryExtra}
	{AtomEntryExtra}
</entry>
		'''
		XmlEntries['rss'] += f'''
<item>
	<guid>{Entry['Link']}</guid>
	<link>{Entry['Link']}</link>
	{XmlEntryExtra}
	{RssEntryExtra}
</item>
		'''
	Feeds = {'atom': f'''{XmlHeader}
<feed xmlns="http://www.w3.org/2005/Atom" {XmlLang}>
	{XmlExtra}
	{AtomExtra}
	<updated>{datetime.now()}</updated>
	<generator uri="https://gitlab.com/octtspacc/staticoso" version="{staticosoNameVersion().split(" ")[1]}">staticoso</generator>
	{XmlEntries['atom']}
</feed>''', 'rss': f'''{XmlHeader}
<rss xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/" version="2.0" {XmlLang}>
	<channel>
		{XmlExtra}
		{RssExtra}
		<language>{Data["Language"]}</language>
		<lastBuildDate>{datetime.now()}</lastBuildDate>
		<generator>{staticosoNameVersion()}</generator>
		{XmlEntries['rss']}
	</channel>
</rss>'''}
	if Format:
		Feeds = Feeds[Format.lower()]
	return Feeds
