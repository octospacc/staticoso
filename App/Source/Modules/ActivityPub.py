""" ================================== |
| This file is part of                 |
|   staticoso                          |
| Just a simple Static Site Generator  |
|                                      |
| Licensed under the AGPLv3 license    |
|   Copyright (C) 2022-2023, OctoSpacc |
| ================================== """

import time
from Libs.dateutil.parser import parse as date_parse
from Libs.mastodon import Mastodon
from Modules.HTML import *
from Modules.Logging import *
from Modules.Utils import *

def MastodonGetSession(InstanceURL, Token):
	return Mastodon(
		api_base_url=InstanceURL,
		access_token=Token)

def MastodonGetPostsFromUserID(Session, UserID):
	return Session.account_statuses(
		UserID,
		exclude_replies=True)

def MastodonDoPost(Session, Text:str, Lang:str=None, Visibility:str='public'):
	if Text:
		return Session.status_post(
			Text,
			language=Lang,
			visibility=Visibility)

def MastodonGetLinkFromPost(Post, Domain:str=None):
	Parse = MkSoup(Post['content'])
	if Parse.a:
		Link = Parse.find_all('a')[-1]['href']
		if not Domain or (Domain and Link.startswith(Domain)):
			return {
				'Post': Post['uri'],
				'Link': Link}
	return None

def MastodonGetAllLinkPosts(Session, Domain:str=None):
	Posts = []
	for p in MastodonGetPostsFromUserID(Session, Session.me()['id']):
		Post = MastodonGetLinkFromPost(p, Domain)
		if Post:
			Posts += [Post]
	return Posts

# TODO:
# - Get post lang from page lang instead of site
# - Fix message including some messed up paragraphs with the new methods
def MastodonShare(Flags:dict, Pages:list, Locale:dict):
	f = NameSpace(Flags)
	SaidPosting = False
	NoteLimit, UrlLen = 500, 24
	Token = f.MastodonToken
	Check = ';Debug=True'
	if Token.endswith(Check):
		Debug = True
		Token = Token[:-len(Check)]
	else:
		Debug = False
	TypeFilter, HoursLimit, CategoryFilter = f.ActivityPubTypeFilter, f.ActivityPubHoursLimit, f.FeedCategoryFilter
	Session = MastodonGetSession(f.MastodonURL, Token)
	Posts = MastodonGetAllLinkPosts(Session, f.SiteDomain)
	Pages.sort() # Ensure new posts are sent in order from oldest to newest
	for File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image in Pages:
		if (not TypeFilter or (TypeFilter and (Meta['Type'] == TypeFilter or TypeFilter == '*'))) and (not CategoryFilter or (CategoryFilter and (CategoryFilter in Meta['Categories'] or CategoryFilter == '*'))):
			URL = f"{f.SiteDomain}/{StripExt(File)}.html"
			DoPost = True
			for p in Posts:
				# If already a post linking to this page exists on the net, don't repost
				if p['Link'] in [URL]+Meta['URLs'] and not Debug:
					DoPost = False
					break

			if DoPost and Meta['Feed'] == 'True' and (not HoursLimit or (Meta['CreatedOn'] and time.time() - time.mktime(date_parse(Meta['CreatedOn']).timetuple()) < 60*60*HoursLimit)):
				Read = f'\n\n...{Locale["ReadFullPost"]}:\n'
				Hashtags = ''
				for Cat in Meta['Categories']:
					Hashtags += f' #{Cat.replace("-", "")}'
				Hashtags = '\n\n' + Hashtags.strip()
				Desc = LimitText(HtmlParagraphsToText(ContentHTML, '\n'), NoteLimit - len(Read) - UrlLen - len(Hashtags))

				if not SaidPosting:
					logging.info("Posting to Mastodon")
					SaidPosting = True

				if Debug:
					Text = Desc + Read + URL + Hashtags
					print(f'{len(Desc+Read+Hashtags)+UrlLen}:\n{Text}\n\n\n\n')
				else:
					time.sleep(5) # Prevent flooding
					Post = MastodonGetLinkFromPost(
						Post=MastodonDoPost(
							Session,
							Text=Desc+Read+URL+Hashtags,
							Lang=f.SiteLang),
						Domain=f.SiteDomain)
					if Post:
						Posts += [Post]

	return Posts
