""" ================================== |
| This file is part of                 |
|   staticoso                          |
| Just a simple Static Site Generator  |
|                                      |
| Licensed under the AGPLv3 license    |
|   Copyright (C) 2022-2023, OctoSpacc |
| ================================== """

import shutil
from Modules.HTML import DoMinifyHTML
from Modules.Utils import *

from Libs import rcssmin
cssmin = rcssmin._make_cssmin(python_only=True)

def PrepareAssets(Flags):
	f = NameSpace(Flags)
	if f.MinifyAssets:
		shutil.copytree('Assets', f.OutDir, ignore=IgnoreFiles, dirs_exist_ok=True)
		for File in Path('Assets').rglob('*'):
			if os.path.isfile(File):
				Dest = f"{f.OutDir}/{str(File)[len('Assets')+1:]}"
				if str(File).lower().endswith(FileExtensions['HTML']):
					WriteFile(Dest, DoMinifyHTML(ReadFile(File), f.MinifyKeepComments))
				elif str(File).lower().endswith('.css'):
					WriteFile(Dest, cssmin(ReadFile(File), f.MinifyKeepComments))
				else:
					shutil.copy2(File, Dest)
	else:
		shutil.copytree('Assets', f.OutDir, dirs_exist_ok=True)
