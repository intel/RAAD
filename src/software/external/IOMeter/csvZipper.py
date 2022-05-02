#!/usr/bin/python
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Jordan Howes, Joseph Tarango
# *****************************************************************************/
## csvZipper.py
## IOMeter Gen3 Launcher and Parser
## Supporting IOMeter w/ QoS and Randomization

import sys
import os
import csv
import zipfile

print("Zipping all CSV files into resultArchive.zip")

##  Archive schedule and result file
resArchive = zipfile.ZipFile("resultArchive.zip", 'w')

## Find every CSV inside the root directory it is called from.
for root, dir, files in os.walk('./'):
	if(root == './'):	
		for name in files:
			if( name.find('.csv') != -1 ):
				resArchive.write(name)

resArchive.close()

exit(0)


