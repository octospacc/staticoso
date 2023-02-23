""" ================================== |
| This file is part of                 |
|   staticoso                          |
| Just a simple Static Site Generator  |
|                                      |
| Licensed under the AGPLv3 license    |
|   Copyright (C) 2022-2023, OctoSpacc |
| ================================== """

from Modules.Logging import *
from Modules.Utils import *

try:
	from Modules.ActivityPub import *
	ActivityPub = True
except:
	logging.warning("⚠ Can't load the ActivityPub module. Its use is disabled. Make sure the 'requests' library is installed.")
	ActivityPub = False

def ApplySocialIntegrations(Flags, Pages, LimitFiles, Locale):
	f = NameSpace(Flags)
	FinalPaths = []

	if ActivityPub and f.MastodonURL and f.MastodonToken and f.SiteDomain:
		logging.info("Mastodon Operations")
		MastodonPosts = MastodonShare(Flags, Pages, Locale)
	else:
		MastodonPosts = []

	for File, Content, Titles, Meta, ContentHTML, SlimHTML, Description, Image in Pages:
		if IsLightRun(File, LimitFiles):
			continue
		File = f'{f.OutDir}/{StripExt(File)}.html'
		Content = ReadFile(File)
		Post = ''
		for p in MastodonPosts:
			if p['Link'] == SiteDomain + '/' + File[len(f'{f.OutDir}/'):]:
				Post = HTMLCommentsBlock.format(
					StrComments=Locale['Comments'],
					StrOpen=Locale['OpenInNewTab'],
					URL=p['Post'])
				break
		#Content = ReplWithEsc(Content, '[staticoso:Comments]', Post)
		Content = ReplWithEsc(Content, '<staticoso:Comments>', Post)
		WriteFile(File, Content)
		FinalPaths += [File]

	return FinalPaths
