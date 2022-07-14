""" ================================= |
| This file is part of                |
|   staticoso                         |
| Just a simple Static Site Generator |
|                                     |
| Licensed under the AGPLv3 license   |
|   Copyright (C) 2022, OctoSpacc     |
| ================================= """

# Our local Markdown patches conflict if the module is installed on the system, so first try to import from system
try:
	from markdown import markdown
except ModuleNotFoundError:
	from Libs.markdown import markdown
