# staticoso

**staticoso** (_from Italian statico [static] + coso [thingy]_) is an unpretentious **static site generator**.

I'm making this because I need a simple and kind-of-minimal program to serve me as a static site generator with (limited) CMS features. Just the features I need.

This won't replace any of the big projects out there that do the same thing but, as all of my projects, I'm releasing it as free libre software, in the hope that someone would find it useful.  
Also, this software is needed for someone to edit and compile my personal sub-website [sitoctt](https://gitlab.com/octtspacc/sitoctt) from its source. Being that site too released under a libre license that allows modifications, I have to also release the tools I use to build it.

**Everything is still an heavy WIP**, and features might break across commits, but feel free to experiment with all of this stuff!

## Documentation

Documentation can be found at [octtspacc.gitlab.io/staticoso-docs](https://octtspacc.gitlab.io/staticoso-docs).  
Obviously, it's built with staticoso itself 😁️. Its source repo can be found at [gitlab.com/octtspacc/staticoso-docs](https://gitlab.com/octtspacc/staticoso-docs).

Keep in mind that, currently, it's still very incomplete. **Any help**, from writing the documentation to creating a decent HTML+CSS template for its site, **is more than welcome**.

## Dependencies

- [Python >= 3.10](https://python.org)
- (Included) [Python Markdown == 3.3.7](https://pypi.org/project/Markdown)
  - (Included) Third-Party Extensions for Python Markdown: [markdown_del_ins](https://github.com/honzajavorek/markdown-del-ins), [mdx_subscript](https://github.com/jambonrose/markdown_subscript_extension), [mdx_superscript](https://github.com/jambonrose/markdown_superscript_extension)
- (Included) [Beautiful Soup == 4.11.1](https://pypi.org/project/beautifulsoup4)
- (Included) [feedgen == 0.9.0](https://pypi.org/project/feedgen)
  - [lxml == 4.9.1](https://pypi.org/project/lxml)
- (Included) [htmlmin == 0.1.12](https://pypi.org/project/htmlmin)

### Optional dependencies

Needed for Pug input support:

- [node == 12.22.5](https://nodejs.org) - [npm == 7.5.2](https://www.npmjs.com)
- (Included, must be manually installed in system $PATH) [pug-cli == 1.0.0-alpha6](https://npmjs.com/package/pug-cli)

Needed for Gemtext output support:

- [Go](https://go.dev)
- [html2gmi](https://github.com/LukeEmmet/html2gmi)

## Features roadmap

- [ ] Multithreading
- [ ] Overriding internal HTML snippets for template-specific ones
- [ ] Static syntax highlighing for code blocks in any page
- [x] File name used as a title for pages without one
- [ ] Custom category names in header links
- [ ] Choosing custom name for Blog and Uncategorized categories
- [ ] Choosing to use a template for all pages in a folder
- [x] Configuration with both INI files and CLI arguments
- [ ] Category-based feeds
- [ ] Support for multi-language sites
- [x] The `title` attribute is added to images which only have `alt` (for desktop accessibility), or viceversa
- [x] Local (per-page) and global (per-site) macros
- [x] ActivityPub (Mastodon) support (Feed + embedded comments)
- [ ] Polished Gemtext generation
- [x] Autodetection of pages and posts
- [x] Info for posts shown on their page
- [x] HTML minification
- [x] Full Open Graph support
- [x] Custom categories for posts
- [x] Custom static and dynamic page parts
- [x] Showing creation and modified date for posts
- [x] Generation of category pages (ex. page with list of blog posts)
- [x] Custom and automatic page sorting
- [ ] SCSS compilation support for CSS templates
- [ ] Pug support for base templates and page side parts
- [ ] Differential recompile (to optimize resource waste on non-ephemeral servers)
- [ ] Hot-recompile (for website development)
- [x] TXT sitemap generation
- [x] Atom + RSS feed generation
- [x] Generation of global website menu as a tree or as a line
- [x] Generation of page (titles) menu as a tree
- [x] Auto-detection of titles in a page
- [x] **HTML**, **TXT**, **Extended Markdown**, and **Pug** supported as input page files
- [ ] Out of heavy-WIP state

## Known issues (might need further investigation)

- Bad HTML included in Markdown files can cause a build to fail entirely.
- The program currently takes about 2 seconds to build a smallish site. While by itself that's not a long time, problems could arise for bigger sites.
- Ordering pages in the global menu with external configuration flags (outside the pages' source) yields broken and unpredictable results.
