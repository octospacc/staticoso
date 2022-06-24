# staticoso

**staticoso** (_from Italian statico [static] + coso [thingy]_) is an unpretentious static site generator.

I'm making this because I need a simple and kind-of-minimal program to serve me as a static site generator with (limited) CMS features. Just the features I need.

This won't replace any of the big projects out there that do the same thing but, as all of my projects, I'm releasing it as free libre software, in the hope that someone would find it useful.  
Also, this software is needed for someone to edit and compile my personal sub-website [sitoctt](https://gitlab.com/octtspacc/sitoctt) from its source. Being that site too released under a libre license that allows modifications, I have to also release the tools I use to build it.

Feel free to experiment with all of this stuff!

## Dependencies
- [Python == 3.10.4](https://python.org)
- (Included) [Python Markdown == 3.3.7](https://pypi.org/project/Markdown)
- (Included) [Beautiful Soup == 4.11.1](https://pypi.org/project/beautifulsoup4)
- (Included) [feedgen == 0.9.0](https://pypi.org/project/feedgen)
- (Included) [htmlmin == 0.1.12](https://pypi.org/project/htmlmin)
- [node == 12.22.5](https://nodejs.org) - [npm == 7.5.2](https://www.npmjs.com)
- (Included) [pug-cli == 1.0.0-alpha6](https://npmjs.com/package/pug-cli)

## Features roadmap
- [x] Autodetection of pages and posts
- [x] Info for posts shown on their page
- [x] HTML minification
- [x] Full Open Graph support
- [x] Custom categories for posts
- [x] Custom static page parts programmable by context
- [x] Showing creation and modified date for posts
- [x] Generation of category pages (ex. page with list of blog posts)
- [x] Custom and automatic page sorting
- [ ] SCSS compilation support for CSS templates
- [ ] Pug support for base templates and page side parts
- [ ] Differential recompile (to optimize resource waste on non-ephemeral servers)
- [ ] Hot-recompile (for website development)
- [ ] XML sitemap generation
- [x] Atom + RSS feed generation for posts
- [x] Generation of website page tree in left sidebar
- [x] Generation of titles in right sidebar with clickable links
- [x] Detections of titles in a page
- [x] Custom static page parts by template
- [x] Extended Markdown + Pug support for pages
- [x] Ready for use
