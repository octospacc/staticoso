""" ================================= |
| This file is part of                |
|   staticoso                         |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
|   Copyright (C) 2022, OctoSpacc     |
| ================================= """

from Libs.bs4 import BeautifulSoup
from Libs.mastodon import Mastodon
from Modules.Utils import *

def MastodonGetSession(MastodonURL, MastodonToken):
	return Mastodon(
		api_base_url=MastodonURL,
		access_token=MastodonToken)

def MastodonGetMyID(Session):
	return Session.me()['id']

def MastodonGetPostsFromUserID(Session, UserID):
	return Session.account_statuses(
		UserID,
		exclude_replies=True)

def MastodonDoPost(Session, Text, Lang=None, Visibility='public'):
	if Text:
		return Session.status_post(
			Text,
			language=Lang,
			visibility=Visibility)

def MastodonGetLinkFromPost(Post, Domain=None):
	Parse = BeautifulSoup(Post['content'], 'html.parser')
	if Parse.a:
		Link = Parse.find_all('a')[-1]['href']
		if not Domain or (Domain and Link.startswith(Domain)):
			return {
				'Post': Post['uri'],
				'Link': Link}
	return None

def MastodonGetAllLinkPosts(Session, Domain=None):
	Posts = []
	for p in MastodonGetPostsFromUserID(Session, MastodonGetMyID(Session)):
		Post = MastodonGetLinkFromPost(p, Domain)
		if Post:
			Posts += [Post]
	return Posts

# TODO: Set a limit/cooldown on how many new posts at a time can be posted, or ignore posts older than date X.. otherwise if someone starts using this after having written 100 blog posts, bad things will happen
def MastodonShare(MastodonURL, MastodonToken, Pages, SiteDomain, SiteLang, Locale):
	Session = MastodonGetSession(MastodonURL, MastodonToken)
	Posts = MastodonGetAllLinkPosts(Session, SiteDomain)
	Pages.sort()
	for File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image in Pages:
		if Meta['Type'] == 'Post':
			Desc = ''
			Parse = BeautifulSoup(ContentHTML, 'html.parser')
			Paragraphs = Parse.p.get_text().split('\n')
			Read = '...' + Locale['ReadFullPost'] + ':\n'
			URL = '{}/{}.html'.format(SiteDomain, StripExt(File))
			for p in Paragraphs:
				if p and len(Read+Desc+p)+25 < 500:
					Desc += p + '\n\n'
				else:
					if Desc:
						break
					else:
						Desc = p[:500-25-5-len(Read)] + '...'
			DoPost = True
			for p in Posts:
				if p['Link'] == URL:
					DoPost = False
					break
			if DoPost:
				sleep(3)
				Post = MastodonGetLinkFromPost(
					Post=MastodonDoPost(
						Session,
						Text=Desc+Read+URL,
						Lang=SiteLang),
					Domain=SiteDomain)
				if Post:
					Posts += [Post]
	return Posts
