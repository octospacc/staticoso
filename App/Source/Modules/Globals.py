""" ================================== |
| This file is part of                 |
|   staticoso                          |
| Just a simple Static Site Generator  |
|                                      |
| Licensed under the AGPLv3 license    |
|   Copyright (C) 2022-2023, OctoSpacc |
| ================================== """

ReservedPaths = ('Site.ini', 'Assets', 'Pages', 'Posts', 'Templates', 'StaticParts', 'DynamicParts')
FileExtensions = {
	'Pages': ('htm', 'html', 'markdown', 'md', 'pug', 'txt'),
	'HTML': ('.htm', '.html'),
	'Markdown': ('.markdown', '.md'),
	'Tmp': ('htm', 'markdown', 'md', 'pug', 'txt')}

PosStrBools = ('true', 'yes', 'on', '1', 'enabled')
NegStrBools = ('false', 'no', 'off', '0', 'disabled')

PageIndexStrPos = tuple(list(PosStrBools) + ['all', 'listed', 'indexed', 'unlinked'])
PageIndexStrNeg = tuple(list(NegStrBools) + ['none', 'unlisted', 'unindexed', 'hidden'])

InternalMacrosWraps = [['[', ']'], ['<', '>']]
