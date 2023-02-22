""" ================================== |
| This file is part of                 |
|   staticoso                          |
| Just a simple Static Site Generator  |
|                                      |
| Licensed under the AGPLv3 license    |
|   Copyright (C) 2022-2023, OctoSpacc |
| ================================== """

from base64 import b64encode
from Modules.Globals import *
from Modules.HTML import *
from Modules.Utils import *

JournalHeadings = ('h2','h3','h4','h5')
JournalTitleDecorators = {'(':')', '[':']', '{':'}'}
#JournalStyles = {
#	"Default": {},
#	"details": {}
#}
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
	<meta charset="UTF-8"/>
	<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
	<title>{TitlePrefix}Redirect</title>
	<link rel="canonical" href="{SiteDomain}/{DestURL}"/>
	<meta http-equiv="refresh" content="0; url='{DestURL}'"/>
</head>
<body>
	<p><a href="{DestURL}">{StrClick}</a> {StrRedirect}.</p>
</body>
</html>
"""
HTMLCommentsBlock = '<br><h3>{StrComments}</h3><a href="{URL}" rel="noopener" target="_blank">{StrOpen} <span class="twa twa-↗️"><span>↗️</span></span></a>'

def DashifyTitle(Title:str, Done:list=[]):
	return UndupeStr(DashifyStr(Title.lstrip(' ').rstrip(' ')), Done, '-')

# Generate HTML tree list (nested list) from our internal metaformat, such as:
# :Item 1               \\  <li>Item 1<ul>
# .:Item 2   ============\\     <li>Item 2<ul>
# ..:Item 3  ============//         <li>Item 3</li></ul></li></ul></li>
# :Item 4               //  <li>Item 4</li>
def GenHTMLTreeList(MetaList:str, Type:str='ul', Class:str=""):
	HTML = ''
	Lines = MetaList.splitlines()
	CurDepth, NextDepth, PrevDepth = 0, 0, 0
	for i,e in enumerate(Lines):
		CurDepth = e.find(':')
		NextDepth = Lines[i+1].find(':') if i+1 < len(Lines) else 0
		HTML += '\n<li>' + e[CurDepth+1:]
		if NextDepth == CurDepth:
			HTML += '</li>'
		elif NextDepth > CurDepth:
			HTML += f'\n<{Type}>' * (NextDepth - CurDepth)
		elif NextDepth < CurDepth:
			HTML += f'</li>\n</{Type}>' * (CurDepth - NextDepth) + '</li>'
		PrevDepth = CurDepth
	return f'<{Type} class="staticoso-TreeList {Class}">{HTML}\n</{Type}>'

def MakeLinkableTitle(Line:str, Title:str, DashTitle:str, Type:str):
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

def GetTitle(FileName:str, Meta:dict, Titles:list, Prefer:str='MetaTitle', BlogName:str=None):
	if Prefer == 'BodyTitle':
		Title = Titles[0].lstrip('#') if Titles else Meta['Title'] if Meta['Title'] else FileName
	elif Prefer == 'MetaTitle':
		Title = Meta['Title'] if Meta['Title'] else Titles[0].lstrip('#') if Titles else FileName
	elif Prefer == 'HTMLTitle':
		Title = Meta['HTMLTitle'] if Meta['HTMLTitle'] else Meta['Title'] if Meta['Title'] else Titles[0].lstrip('#') if Titles else FileName
	if Meta['Type'] == 'Post' and BlogName and 'Blog' in Meta['Categories']:
		Title += ' - ' + BlogName
	return Title

def GetDescription(Meta:dict, BodyDescription:str, Prefer:str='MetaDescription'):
	if Prefer == 'BodyDescription':
		Description = BodyDescription if BodyDescription else Meta['Description'] if Meta['Description'] else ''
	elif Prefer == 'MetaDescription':
		Description = Meta['Description'] if Meta['Description'] else BodyDescription if BodyDescription else ''
	return Description

def GetImage(Meta:dict, BodyImage:str, Prefer:str='MetaImage'):
	if Prefer == 'BodyImage':
		Image = BodyImage if BodyImage else Meta['Image'] if Meta['Image'] else ''
	elif Prefer == 'MetaImage':
		Image = Meta['Image'] if Meta['Image'] else BodyImage if BodyImage else ''
	return Image

def MakeContentHeader(Meta:dict, Locale:dict, Categories:str=''):
	Header = ''
	for e in ['CreatedOn', 'EditedOn']:
		if Meta[e]:
			Header += f'<span class="staticoso-ContentHeader-{e}" id="staticoso-ContentHeader-{e}"><span class="staticoso-Label">{Locale[e]}</span>: <span class="staticoso-Value">{Meta[e]}</span></span><br>'
	if Categories:
		Header += f'<span class="staticoso-ContentHeader-Categories" id="staticoso-ContentHeader-Categories"><span class="staticoso-Label">{Locale["Categories"]}</span>:<span class="staticoso-Value">{Categories.removesuffix(" ")}</span></span><br>'
	if Meta['Index'].lower() in PageIndexStrNeg:
		Header += f'<span class="staticoso-ContentHeader-Index" id="staticoso-ContentHeader-Index"><span class="staticoso-Value">{Locale["Unlisted"]}</span></span><br>'
	return f'<p>{Header}</p>'

def MakeCategoryLine(File:str, Meta:dict):
	Categories = ''
	for Cat in Meta['Categories']:
		Categories += f' <a href="{GetPathLevels(File)}Categories/{Cat}.html">{html.escape(Cat)}</a> '
	return Categories

def MakeListTitle(File:str, Meta:dict, Titles:list, Prefer:str, BlogName:str, PathPrefix:str=''):
	Title = GetTitle(File.split('/')[-1], Meta, Titles, Prefer, BlogName).lstrip().rstrip()
	Link = False if Meta['Index'] == 'Unlinked' else True
	if Link:
		Href = f'{PathPrefix}{StripExt(File)}.html'
		Title = f'<a href="{Href}">{Title}</a>'
	#else:
	#	Title = f'<span class="staticoso-ListItem-Plain">{Title}</span>'
	if Meta['Type'] == 'Post':
		CreatedOn = Meta['CreatedOn'] if Meta['CreatedOn'] else '?'
		Title = f"<span>[<time>{CreatedOn}</time>]</span> {Title}"
	return Title

def FormatTitles(Titles:list, Flatten=False):
	# TODO: Somehow titles written in Pug can end up here and don't work, they should be handled
	List, DashyTitles = '', []
	for t in Titles:
		n = 0 if Flatten else t.split(' ')[0].count('#')
		Level = '.' * (n-1) + ':'
		Title = MkSoup(t.lstrip('#')).get_text()
		DashyTitle = DashifyTitle(Title, DashyTitles)
		DashyTitles += [DashyTitle]
		List += f'{Level}<a href="#{DashyTitle}">{html.escape(Title)}</a>\n'
	return GenHTMLTreeList(List)

# Clean up a generic HTML tree such that it's compliant with the HTML Journal standard
# (https://m15o.ichi.city/site/subscribing-to-a-journal-page.html);
# basis is: find an element with the JournalBody attr., and group its direct children as <article>s
def MakeHTMLJournal(Flags, Locale, FilePath, HTML):
	Soup, Journal, Entries = MkSoup(HTML), '', []
	for t in Soup.find_all(attrs={"htmljournal":True}):
		#JournalStyle = JournalStyles[t.attrs["journalstyle"]] if 'journalstyle' in t.attrs and t.attrs["journalstyle"] in JournalStyles else JournalStyles['Default']
		for c in t.children: # Entries, some might be entirely grouped in their own element but others could not, use headings as separators
			for ct in MkSoup(str(c)).find_all():
				# Transform (almost, for now I reserve some) any heading into h2 and remove any attributes
				if ct.name in JournalHeadings:
					Title = ct.text.strip().removeprefix('»').strip()
					Chr0 = Title[0]
					# Remove leading symbols before date
					if Chr0 in JournalTitleDecorators.keys():
						Idx = Title.find(JournalTitleDecorators[Chr0])
						Title = Title[1:Idx] + ' - ' + Title[Idx+2:]
					if Journal:
						Journal += '\n</article><br>\n'
					Journal += f'\n<article>\n<h2>{Title}</h2>\n'
				elif ct.name == 'p': # We should handle any type to preserve <details> and things
					Journal += str(ct)
		FileName = FilePath.split('/')[-1]
		URL = f'{Flags["SiteDomain"]}/{StripExt(FilePath)}.Journal.html'
		Redirect = f"""<meta http-equiv="refresh" content="0; url='./{FileName}'">""" if Flags["JournalRedirect"] else ''

		# Instead of copying stuff from the full page, for now we use dedicated title, header, footer, and pagination
		Title = t.attrs['journaltitle'] if 'journaltitle' in t.attrs else f'"{StripExt(FileName)}" Journal - {Flags["SiteName"]}' if Flags["SiteName"] else f'"{StripExt(FileName)}" Journal'
		FeedLink = f"""<a title="Journal Atom Feed" href="https://journal.miso.town/atom?url={URL}" target="_blank" rel="noopener"><img width="88" height="31" alt="Journal Atom Feed" title="Journal Atom Feed" src="data:image/png;base64,{b64encode(ReadFile(staticosoBaseDir()+'Assets/ThirdParty/Feed-88x31.png', 'rb')).decode()}"></a>""" if Flags['SiteDomain'] else ''
		Header = t.attrs['journalheader'] if 'journalheader' in t.attrs else f"""\
<p>
<i>{Locale["StrippedDownNotice"].format(Link="./"+FileName)}</i>
<a title="Valid HTML Journal" href="https://journal.miso.town" target="_blank" rel="noopener"><img alt="Valid HTML Journal" title="Valid HTML Journal" width="88" height="31" src="data:image/png;base64,{b64encode(ReadFile(staticosoBaseDir()+'Assets/ThirdParty/Valid-HTML-Journal-88x31.png', 'rb')).decode()}"></a>
{FeedLink}
</p>
"""
		Journal = f"""\
<!--
<!DOCTYPE html>
<html>
<head>
	<meta charset="UTF-8"/>
	<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
	<title>{Title}</title>
	<link rel="canonical" href="{URL}"/>
	{Redirect}
</head>
<body>
--->
	<h1>{Title}</h1>
	<header id="Header">
		{Header}
		<div id="staticoso-LinkToFooter"><b>[<big><a href="#Footer"><span class="twa twa-⬇️"><span>⬇️</span></span> Footer</a></big>]</b></div>
	</header><br>
	{Journal}
	</article><br>
	<footer id="Footer">
		<div id="staticoso-LinkToHeader"><b>[<big><a href="#Header"><span class="twa twa-⬆️"><span>⬆️</span></span> Header</a></big>]</b></div>
		{t.attrs["journalfooter"] if "journalfooter" in t.attrs else ""}
	</footer>
<!--
</body>
</html>
--->
"""
	return Journal
