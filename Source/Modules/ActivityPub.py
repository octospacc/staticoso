""" ================================= |
| This file is part of                |
|   staticoso                         |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
|   Copyright (C) 2022, OctoSpacc     |
| ================================= """

from Libs.bs4 import BeautifulSoup
#from Libs.mastodon import Mastodon
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
		Session.status_post(
			Text,
			language=Lang,
			visibility=Visibility)

# TODO: Set a limit/cooldown on how many new posts at a time can be posted, or ignore posts older than date X.. otherwise if someone starts using this after having written 100 blog posts, bad things will happen
def MastodonShare(MastodonURL, MastodonToken, Pages, SiteDomain, SiteLang, Locale):
	#return None
	Session = MastodonGetSession(MastodonURL, MastodonToken)
	Posts = MastodonGetPostsFromUserID(
		Session,
		MastodonGetMyID(Session))
	for i,e in enumerate(Posts):
		Parse = BeautifulSoup(e['content'], 'html.parser')
		Posts[i] = {
			'URL': e['uri'],
			#e['content'],
			'LastLink': Parse.find_all('a')[-1]['href'] if Parse.a else None}
		#print(i['uri'], i['content'])
	#print(Posts)
	Pages.sort()
	for File, Content, Titles, Meta, HTMLContent, Description, Image in Pages:
		if Meta['Type'] == 'Post':
			Desc = ''
			Parse = BeautifulSoup(HTMLContent, 'html.parser')
			Paragraphs = Parse.p.get_text().split('\n')
			Read = '...' + Locale['ReadFullPost'] + ':\n'
			URL = '{}/{}.html'.format(SiteDomain, StripExt(File))
			#Desc = '...' + Read + ':\n' + URL
			#DescLen = len(Read) + 30
			#if not Paragraphs[0]:
			#	Paragraphs.pop(0)
			for p in Paragraphs:
				#while len(Description) <= 450:
				#if p and len(Description+p)+2 <= 450:
				if p and len(Read+Desc+p)+25 < 500:
					Desc += p + '\n\n'
				else:
					if Desc:
						break
					else:
						Desc = p[:500-25-5-len(Read)] + '...'
			#if len(Description) > 450:
			#	Description = Description[:450] + '...'
			DoPost = True
			for p in Posts:
				if p['LastLink'] == URL:
					DoPost = False
					break
			if DoPost:
				MastodonDoPost(
					Session,
					Desc + Read + URL,
					SiteLang)
		#BodyDescription = Parse.p.get_text()[:150].replace('\n', ' ').replace('"', "'") + '...'