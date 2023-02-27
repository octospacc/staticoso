# staticoso

**staticoso** (_from Italian statico [static] + coso [thingy]_) is an unpretentious **static site generator**.

I'm making this because I need a simple and kind-of-minimal program to serve me as a static site generator with (limited) mixed-CMS+Wiki features. Just the ones I need, of which some are unique, however.

This won't replace any of the big projects out there that do the same thing but, as all of my projects, I'm releasing it as free libre software, in the hope that someone would find it useful.  
Also, this software is needed for someone to edit and compile my personal website [sitoctt](https://gitlab.com/octtspacc/sitoctt) from its source. Being that site too released under a libre license that allows modifications, I have to also release the tools I use to build it, or really people will never be able to make the most out of it.

**Everything is still kind of a WIP**, and some bugs might appear across commits, but feel free to experiment with all of this stuff! If you really want to use this tool for your website, I suggest you don't do like I do in my build process, running always with the latest code commit; instead, either download a snapshot of the code and keep that, or always clone from a specific commit, until you have time when I do an update to check if your site actually builds correctly with the new version.

## Usage

### Documentation

Documentation can be found at [octtspacc.gitlab.io/staticoso-docs](https://octtspacc.gitlab.io/staticoso-docs).  
Obviously, it's built with staticoso itself 😁️. Its source repo can be found at [gitlab.com/octtspacc/staticoso-docs](https://gitlab.com/octtspacc/staticoso-docs).

Keep in mind that, currently, it's still very incomplete. **Any help**, from writing the documentation to creating a decent HTML+CSS template for its site, **is more than welcome**.

### Dependencies

- [Python >= 3.10](https://python.org)
- (Included) [Python Markdown == 3.3.7](https://pypi.org/project/Markdown)
- (Included) [Beautiful Soup == 4.11.1](https://pypi.org/project/beautifulsoup4)
- (Included) [feedgen == 0.9.0](https://pypi.org/project/feedgen)
  - (Not included) [lxml == 4.9.1](https://pypi.org/project/lxml)
- (Included) [htmlmin == 0.1.12](https://pypi.org/project/htmlmin)
- (Included) [rcssmin == 1.1.1](https://pypi.org/project/rcssmin)

#### Optional dependencies

Needed for Pug input support:

- [node == 12.22.5](https://nodejs.org) - [npm == 7.5.2](https://www.npmjs.com)
- (Included, but must be manually installed in system $PATH) [pug-cli == 1.0.0-alpha6](https://npmjs.com/package/pug-cli)

Needed for Gemtext output support:

- [Go](https://go.dev)
- [html2gmi](https://github.com/LukeEmmet/html2gmi)

### Getting a version

The recommended way to get staticoso is to choose a commit, (preferably the most recent as of you're reading this) and stick to that for workflows and automatic deployments. You can either fork the repository at a certain point and always clone from yours, clone from a specific commit of this repo, or download an archive of the commit in question (click the GitLab download icon after navigating to a commit, or try `https://gitlab.com/octtspacc/staticoso/-/archive/<FullCommitHash>/staticoso-<FullCommitHash>.tar.bz2`).

Once that's set-up, it will also be possible to download the latest version from the CI/CD, based on if that commit has or has not passed runtime tests.

All of this is because some crucial things might be changed from one commit to another, possibly causing your site build to fail. Always make sure you have some spare minutes at hand for checking that your site actually still builds, whenever you want to update your workflows to the bleeding edge.

## Roadmap

### Features

- [x] Generation of simplified pages compliant with the [HTML Journal standard](https://journal.miso.town)
- [x] HTML feeds (pages with list of N most recent posts)
- [x] Lists of all pages in a site directory
- [x] Page redirects / Alt URLs (+ ActivityPub URL overrides) 
- [x] Progress bars for the build process!
- [x] Multithreading
- [x] Differential building
- [ ] Overriding internal HTML snippets for template-specific ones
- [ ] Static syntax highlighing for code blocks in any page
- [x] File name used as a title for pages without one
- [ ] Custom category names in header links
- [ ] Choosing custom name for Blog and Uncategorized categories
- [ ] Choosing to use a template for all pages in a folder/category
- [x] Configuration with both INI files and CLI arguments
- [ ] Category-based feeds
- [ ] Support for multi-language sites
- [x] The `title` attribute is added to images which only have `alt` (for desktop accessibility), or viceversa
- [x] Local (per-page) and global (per-site) macros
- [x] ActivityPub (Mastodon) support (Feed + embedded comments)
- [ ] Polished Gemtext generation
- [x] Autodetection of pages and posts
- [x] Info for posts shown on their page
- [x] HTML and CSS minification for Pages and Assets
- [x] Full Open Graph support
- [x] Custom categories for posts
- [x] Custom static and dynamic page parts
- [x] Showing creation and modified date for posts
- [x] Generation of category pages (ex. page with list of blog posts)
- [x] Custom and automatic page sorting
- [ ] SCSS compilation support for CSS templates
- [ ] Pug support for base templates and page side parts
- [ ] Hot-recompile (for website development)
- [x] TXT sitemap generation
- [x] Atom + RSS feed generation
- [x] Generation of global website menu as a tree or as a line
- [x] Generation of page (titles) menu as a tree
- [x] Auto-detection of titles in a page
- [x] **HTML**, **TXT**, **Extended Markdown**, and **Pug** supported as input page files

### Meta

- [ ] Preparing more themes, both original and ported
    - [ ] First the theme build system should be even more streamlined
- [ ] Actually making the documentation useful
- [ ] Presentation website for the project
    - [ ] With a devlog maybe?
- [ ] Constructing something to make testing of staticoso work in a web browser (doable with WASM Python?)

## Known issues (might need further investigation)

- Bad HTML included in Markdown files can cause a build to fail entirely.
- Despite differential building and multithreading, the program still needs some more optimizations.
- Ordering pages in the global menu with external configuration flags (outside the pages' source) yields broken and unpredictable results.
- If site is small, the graphic of percentage completion is bugged (appears shorter).
- Markdown markup in headings (e.g. `## Title **text**`) is not processed and will render literally (e.g. `<h2>Title **text**</h2>`)
