// % Title = staticoso docs

# <a href="https://gitlab.com/octtspacc/staticoso">staticoso</a> docs

_View the source for this site: [gitlab.com/octtspacc/staticoso-docs](https://gitlab.com/octtspacc/staticoso-docs)_

Don't yet mind the fact that there is no CSS at all, and only one single page. **Still a heavy WIP** :)


## Input Files

_Note: Non-lowercase file suffixes are currently broken. This will be fixed._

_Note: Files with `.htm` extension are currently broken too._

### Templates and Parts

For templates and parts files, formats supported as input are:

- HTML (Suffixes: `.htm`, `.html`)

### Pages and Posts

For pages and posts files, many formats are supported as input:

- HTML (Suffixes: `.htm`, `.html`)
- Markdown (Suffixes: `.md`, `.markdown`)
- Pug (through [pug-cli](https://npmjs.com/package/pug-cli)) (Suffixes: `.pug`)
- Plain text (Suffixes: `.txt`) (Rendered as plain text enclosed in `<pre>` tags in the HTML)

### Site folder Structure

A **full** staticoso site folder looks like this:

- `Assets/`: Contains files that will be just copied as they are in the root of the output folder (images, CSS files, ...).
- `Pages/`: Contains website pages.
- `Posts/`: Contains website posts, which differ for some things from pages.
- `Templates/`: Contains base HTML pages to be used as templates for compiling all the pages.
- `StaticParts/`: Contains HTML snippets that can be included statically in HTML templates.
- `DynamicParts/`: Contains HTML snippets that can be included dynamically, via configuration flags, in HTML templates. 
- `Site.ini`: Specifies some configuration flags. CLI arguments can often be used as an alternative to this file.

Keep in mind that the only required files (and, consequently, appropriate folders) for a minimum successful build are at least: one HTML base template, and one page or post. Other elements are optional.  
A reasonably **minimal** staticoso site folder tree can look like this:

<pre><code>
.
├── Assets
│   ├── Default.css
│   └── favicon.ico
├── Templates
│   └── Default.html
├── Pages
│   └── index.md
└── Posts
    └── 2022-05-16-That-Day.md
</code></pre>


## Preprocessor Flags

Preprocessor flags can be included in single-line comments.  
They must be prepended by a `%` (percent sign) character, and values are assigned with the [standard Python INI syntax](https://docs.python.org/3/library/configparser.html#supported-ini-file-structure).

_Note: **Markdown** doesn't officially support comments. staticoso thus uses its own syntax: a line starting with `//` (2 slashes) indicates a comment._

For example:
`// % Flag = Value`

Supported values:

- `Template`
- `Style`
- `Type`
- `Index`
- `Feed`
- `Title`
- `HTMLTitle`
- `Description`
- `Image`
- `Macros`
- `Categories`
- `CreatedOn`
- `EditedOn`
- `Order`

TODO: Finish writing this


## Configuration Flags

Many configuration flags are available.

They can be specified from the `Site.ini` file, under the relative sections, or as command-line arguments.  
CLI arguments, if specified, always take priority over the INI values; this is to easily allow for many different build workflows on the same site.

In the INI file, flags are specified as they are, separated by new lines.  
As CLI arguments, they are prepended by double dashes (`--`) and section name, and values are assigned to them with your standard shell syntax (usually, it will be `--SectionFlag="Value"`, with a space for separation between arguments).

_Note: Some flags are currently CLI-only, while others are file-only. This will be soon fixed._

### Site

- `Name` (`--SiteName`): The name of your site.
- `BlogName` (`--BlogName`): The name of the blog section of your site. Can be omitted, and the site name will be used instead.
- `Tagline` (`--SiteTagline`): The tagline or motto of your site.

### Minify

- `Minify` (`--Minify`): Whether or not to minify the output HTML. Defaults to `False`.
- `KeepComments` (`--MinifyKeepComments`): Optionally keeping comments in minified HTML, instead of removing them. Defaults to `False`.

### Categories

- `Automatic` (`--CategoriesAutomatic`): Whether or not to automatically create pages in the `Categories/` directory of your site. Defaults to `False`.
- `Uncategorized` (`--CategoriesUncategorized`): Enabling a custom name for the automatically managed "Uncategorized" category. Defaults to `Uncategorized`.

---

TODO: Correctly categorize all the below flags

- `SiteRoot`: The root path of your site on your server. Useful if you keep many sites on the same domain/address. Defaults to `/`.
- `SiteDomain`: Domain of your website, for use for feeds and sitemaps.
- `SiteLang`: The language of your site. Will be used for choosing certain strings. Defaults to `en`.
- `SiteTemplate`: Name of the template file to use for the site. Defaults to `Default.html`.
- `NoScripts`: Whether or not to strip out `<script>` tags from the output HTML. Defaults to `False`.
- `Sorting`: Set sorting styles for pages and posts lists.
- `GemtextOutput`: Whether or not to output a Gemtext conversion of the site. Requires [html2gmi](https://github.com/LukeEmmet/html2gmi) to be present in system `$PATH`. Defaults to `False`.
- `GemtextHeader`: A string to optionally include at the top of every Gemtext file.
- `SitemapOutput`: Whether or not to create sitemap files. Defaults to `True`.
- `FeedEntries`: Max number of pages to include in feed files. A value of `0` disables feed generation, while `-1` equals no limit. Defaults to `10`.
- `DynamicParts`: Assign any desired HTML files (from the ones stored in the `DynamicParts/` directory) to the relative section in your base HTML.
- `MarkdownExts`: Specify a custom list of extensions to use when parsing Markdown.
- `MastodonURL`: URL of a Mastodon instance to use for notifying of new posts and creating comment links. Leave blank to disable Mastodon.
- `MastodonToken`: Application token of a Mastodon account to use for notifying of new posts and creating comment links. Leave blank to disable Mastodon.
- `FeedCategoryFilter`: List of post categories to include in the site main feed. Defaults to only `['Blog']`.
- `ActivityPubHoursLimit`: Maximum time limit (in hours) for sharing any newly-created post via ActivityPub; posts older than that amount won't get shared. Defaults to `168` (1 week).
- `OutputDir`: Specifies a custom output path for the compiled website's files. Defaults to `./public/`.


## Internal Markup Tags

_Note: You only really need to care about this section if you're developing themes. If you are building your site with an already prepared theme, then you can do without this information._

staticoso uses a simple internal markup language that's the essence of its template system.

Tags are enclosed in square brackets (with colons as token separators), and declared with the form `[staticoso:Name:Values]`.  
For some tags, there are no values to be specified, so the last part can be omitted. Starting the declaration with `staticoso` is always required.

You can use the following tags in your templates or pages, to let everything work as you want. Some are obviously needed for compiling minimum viable pages, like the one for displaying content.

TODO: Finish writing this
