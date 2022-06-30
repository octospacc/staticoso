""" ================================= |
| This file is part of                |
|   staticoso                         |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
|   Copyright (C) 2022, OctoSpacc     |
| ================================= """

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

def MastodonDoPost(Session):
	pass # mastodon.toot('Tooting from python using #mastodonpy !')
