""" ================================= |
| This file is part of                |
|   staticoso                         |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
|   Copyright (C) 2022, OctoSpacc     |
| ================================= """

from Modules.HTML import *
from Modules.Utils import *

HTMLSectionTitleLine = '<h{Index} class="SectionHeading"><span class="SectionLink"><a href="#{DashTitle}"><span>»</span></a> </span><span class="SectionTitle" id="{DashTitle}">{Title}</span></h{Index}>'
#PugSectionTitleLine = "{Line[:Index]}{Line[Index:Index+2]}.SectionHeading #[span.SectionLink #[a(href='#{DashTitle}') #[span »]] ]#[span#{DashTitle}.SectionTitle {Line[Index+2:]}]"
CategoryPageTemplate = """\
// Title: {Name}
// Type: Page
// Index: True

# {Name}

<div>[staticoso:Category:{Name}]</div>
"""

def DashifyTitle(Title, Done=[]):
	return UndupeStr(DashifyStr(Title.lstrip(' ').rstrip(' ')), Done, '-')

def MakeLinkableTitle(Line, Title, DashTitle, Type):
	if Type == 'md':
		Index = Title.split(' ')[0].count('#')
		return HTMLSectionTitleLine.format(
			Index=Index,
			DashTitle=DashTitle,
			Title=Title[Index+1:])
	elif Type == 'pug':
		Index = Line.find('h')
		return f"{Line[:Index]}{Line[Index:Index+2]}.SectionHeading #[span.SectionLink #[a(href='#{DashTitle}') #[span »]] ]#[span#{DashTitle}.SectionTitle {Line[Index+2:]}]"

def GetTitle(FileName, Meta, Titles, Prefer='MetaTitle', BlogName=None):
	if Prefer == 'BodyTitle':
		Title = Titles[0].lstrip('#') if Titles else Meta['Title'] if Meta['Title'] else FileName
	elif Prefer == 'MetaTitle':
		Title = Meta['Title'] if Meta['Title'] else Titles[0].lstrip('#') if Titles else FileName
	elif Prefer == 'HTMLTitle':
		Title = Meta['HTMLTitle'] if Meta['HTMLTitle'] else Meta['Title'] if Meta['Title'] else Titles[0].lstrip('#') if Titles else FileName
	if BlogName and 'Blog' in Meta['Categories']:
		Title += ' - ' + BlogName
	return Title

def GetDescription(Meta, BodyDescription, Prefer='MetaDescription'):
	if Prefer == 'BodyDescription':
		Description = BodyDescription if BodyDescription else Meta['Description'] if Meta['Description'] else ''
	elif Prefer == 'MetaDescription':
		Description = Meta['Description'] if Meta['Description'] else BodyDescription if BodyDescription else ''
	return Description

def GetImage(Meta, BodyImage, Prefer='MetaImage'):
	if Prefer == 'BodyImage':
		Image = BodyImage if BodyImage else Meta['Image'] if Meta['Image'] else ''
	elif Prefer == 'MetaImage':
		Image = Meta['Image'] if Meta['Image'] else BodyImage if BodyImage else ''
	return Image

def MakeContentHeader(Meta, Locale, Categories=''):
	Header = ''
	for i in ['CreatedOn', 'EditedOn']:
		if Meta[i]:
			Header += f'{Locale[i]}: {Meta[i]}<br>'
	if Categories:
		Header += f"{Locale['Categories']}:{Categories.removesuffix(' ')}<br>"
	return f'<p>{Header}</p>'

def MakeCategoryLine(File, Meta):
	Categories = ''
	if Meta['Categories']:
		for Cat in Meta['Categories']:
			Categories += f' <a href="{GetPathLevels(File)}Categories/{Cat}.html">{html.escape(Cat)}</a> '
	return Categories

def MakeListTitle(File, Meta, Titles, Prefer, SiteRoot, BlogName, PathPrefix=''):
	Title = GetTitle(File.split('/')[-1], Meta, Titles, Prefer, BlogName)
	Link = False if Meta['Index'] == 'Unlinked' else True
	if Link:
		Title = '[{}]({})'.format(
			Title,
			'{}{}.html'.format(PathPrefix, StripExt(File)))
	if Meta['Type'] == 'Post':
		CreatedOn = Meta['CreatedOn'] if Meta['CreatedOn'] else '?'
		Title = f"[{CreatedOn}] {Title}"
	return Title

def FormatTitles(Titles, Flatten=False):
	# TODO: Somehow titles written in Pug can end up here and don't work, they should be handled
	HTMLTitles, DashyTitles = '', []
	for t in Titles:
		n = 0 if Flatten else t.split(' ')[0].count('#')
		Title = MkSoup(t.lstrip('#')).get_text()
		DashyTitle = DashifyTitle(Title, DashyTitles)
		DashyTitles += [DashyTitle]
		Start = '<ul><li>' * (n - 1)
		End = '</li></ul>' * (n - 1)
		HTMLTitles += f'<li>{Start}<a href="#{DashyTitle}">{html.escape(Title)}</a>{End}</li>'
	return f'<ul>{HTMLTitles}</ul>'
