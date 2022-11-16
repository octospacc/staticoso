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

JournalHeadings = ('h2','h3','h4','h5')
JournalTitleDecorators = {'(':')', '[':']', '{':'}'}
JournalStyles = {
	"Default": {},
	"details": {}
}
HTMLSectionTitleLine = '<h{Index} class="SectionHeading staticoso-SectionHeading"><span class="SectionLink staticoso-SectionLink"><a href="#{DashTitle}"><span>»</span></a> </span><span class="SectionTitle staticoso-SectionTitle" id="{DashTitle}">{Title}</span></h{Index}>'
PugSectionTitleLine = "{Start}{Heading}.SectionHeading.staticoso-SectionHeading #[span.SectionLink.staticoso-SectionLink #[a(href='#{DashTitle}') #[span »]] ]#[span#{DashTitle}.SectionTitle.staticoso-SectionTitle {Rest}]"
CategoryPageTemplate = """\
// Title: {Name}
// Type: Page
// Index: True

# {Name}

<div><staticoso:Category:{Name}></div>
"""
RedirectPageTemplate = """\
<!DOCTYPE html>
<html>
<head>
	<title>{TitlePrefix}Redirect</title>
	<link rel="canonical" href="{SiteDomain}/{DestURL}">
	<meta http-equiv="refresh" content="0; url='{DestURL}'">
</head>
<body>
	<p><a href="{DestURL}">{StrClick}</a> {StrRedirect}.</p>
</body>
</html>
"""
HTMLCommentsBlock = '<br><h3>{StrComments}</h3><a href="{URL}" rel="noopener" target="_blank">{StrOpen} ↗️</a>'

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
		return PugSectionTitleLine.format(
			Start=Line[:Index],
			Heading=Line[Index:Index+2],
			Rest=Line[Index+2:],
			DashTitle=DashTitle)

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
	for e in ['CreatedOn', 'EditedOn']:
		if Meta[e]:
			Header += f'<span class="staticoso-ContentHeader-{e}"><span class="staticoso-Label">{Locale[e]}</span>: <span class="staticoso-Value">{Meta[e]}</span></span><br>'
	if Categories:
		Header += f'<span class="staticoso-ContentHeader-Categories"><span class="staticoso-Label">{Locale["Categories"]}</span>:<span class="staticoso-Value">{Categories.removesuffix(" ")}</span></span><br>'
	return f'<p>{Header}</p>'

def MakeCategoryLine(File, Meta):
	Categories = ''
	for Cat in Meta['Categories']:
		Categories += f' <a href="{GetPathLevels(File)}Categories/{Cat}.html">{html.escape(Cat)}</a> '
	return Categories

def MakeListTitle(File, Meta, Titles, Prefer, SiteRoot, BlogName, PathPrefix=''):
	Title = GetTitle(File.split('/')[-1], Meta, Titles, Prefer, BlogName).lstrip().rstrip()
	Link = False if Meta['Index'] == 'Unlinked' else True
	if Link:
		Href = f'{PathPrefix}{StripExt(File)}.html'
		Title = f'<a href="{Href}">{Title}</a>'
	if Meta['Type'] == 'Post':
		CreatedOn = Meta['CreatedOn'] if Meta['CreatedOn'] else '?'
		Title = f"[<time>{CreatedOn}</time>] {Title}"
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

# Clean up a generic HTML tree such that it's compliant with the HTML Journal standard
# (https://m15o.ichi.city/site/subscribing-to-a-journal-page.html);
# basis is: find an element with the JournalBody attr., and group its direct children as <article>s
def MakeHTMLJournal(HTML):
	Soup, Journal, Entries = MkSoup(HTML), '', []
	#for t in Soup.find_all(attrs={"journalbody":True}):
	for t in Soup.find_all(attrs={"htmljournal":True}):
		JournalStyle = JournalStyles[t.attrs["journalstyle"]] if 'journalstyle' in t.attrs and t.attrs["journalstyle"] in JournalStyles else JournalStyles['Default']
		#if 'journalbody' in t.attrs: # Journal container
		for c in t.children: # Entries, some might be entirely grouped in their own element but others could not, use headings as separators
			#print(123,str(c).strip('\n'))
			for ct in MkSoup(str(c)).find_all():
				# Transform (almost, for now I reserve some) any heading into h2 and remove any attributes
				if ct.name in JournalHeadings:
					Title = ct.text.strip().removeprefix('»').strip()
					Chr0 = Title[0]
					# Remove leading symbols b
					if Chr0 in JournalTitleDecorators.keys():
						Idx = Title.find(JournalTitleDecorators[Chr0])
						Title = Title[1:Idx] + ' - ' + Title[Idx+2:]
					#print(Title)
					if Journal:
						Journal += '\n</article>\n'
					Journal += f'\n<article>\n<h2>{Title}</h2>\n'
				elif ct.name == 'p': # We should handle any type to preserve <details> and things
					#print(ct.name)
					Journal += str(ct)
		#Journal += '\n</article>\n'
		#t.replace_with(Journal)
		#HTML = HTML.replace(str(t), Journal) # Have to do this crap, bs4's replace_with doesn't wanna work
		#print(t)
		#print(Journal)
		t.attrs["journalheader"] if "journalheader" in t.attrs else ""
		Title = t.attrs["journaltitle"] if "journaltitle" in t.attrs else f"Untitled HTML Journal"
		# <a href=""><img width="88" height="31" src="https://journal.miso.town/static/banner-htmlj.png"></a>
		Journal = f'''\
<h1>{t.attrs["journaltitle"] if "journaltitle" in t.attrs else f"Untitled HTML Journal"}</h1>
{t.attrs["journalheader"] if "journalheader" in t.attrs else ""}
{Journal}
</article>
{t.attrs["journalfooter"] if "journalfooter" in t.attrs else ""}
'''
	# Instead of copying stuff from the full page, we use dedicated title, header, and footer
	return Journal
