#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors:Joseph Tarango
# *****************************************************************************/
"""
Brief: 
    __init__.py - This file makes this folder a Python package and resolves any imports from TWIDL tree. 

Description:
    Any module in this folder that imports from TWIDL tree should include a first line import 
    "import __init__", and use explicit import statement. For example, "import Intel.vendspec".
"""

import os
os.sys.path.insert(1,'..')

# we want to include the following folders in the system path
root_folder = os.path.abspath(os.curdir)
os_folder = os.path.join(root_folder,("win" if 'nt' == os.name else 'linux'))

if len(os.sys.path)>2 and os.sys.path[2] == root_folder:
    del os.sys.path[1]
else:
    os.sys.path[1] = root_folder

# add TWIDL os specific folder
if 2 >= len(os.sys.path) or os.sys.path[2] != os_folder:
    os.sys.path.insert(2,os_folder)

del (root_folder,os_folder)
