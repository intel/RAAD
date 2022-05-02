#!/usr/bin/python
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Jordan Howes, Joseph Tarango
# *****************************************************************************/
# IOMeterLauncher.py
# IOMeter Gen3 Launcher and Parser
# Supporting IOMeter w/ QoS and Randomization

import sys
import os
import csv
import zipfile

#import win32com.client


from IometerTestSchedule import IometerTestSchedule
from IometerResultParser import IometerResultParser

print("Parsing Schedule File - %s"%(sys.argv[1]))
testing = IometerTestSchedule(sys.argv[1], 'result.csv')
print("Parsing Complete")

if((testing.prepDrive >= 1) and (testing.physDrive == 0)):
	print("Preping drive(s) with 64KB sequential write.")
	testing.createPrepFile("driveprep.icf")
	os.system("iometer.exe driveprep.icf driveprep.csv")
	print("Drive prep complete.")

if(	testing.physDrive == 1 ):
	print("Testing drive in physical mode.  No drive prep will be performed, be sure the drive is in the proper " +
		  "state for testing.")

count = 0
while (testing.nextTestFile("testfile.icf")):
	testname = testing.currTestName
	print("Running test %d - %s"%(count, testname))
	os.system("iometer.exe testfile.icf %s.csv"% testname)
	testing.insertResult("inst%s.csv"% testname)
	count += 1

print("All testing complete, parsing results. Saving Results - %s" % (sys.argv[2]))

##  Archive schedule and result file
## 6/14/10 - Result archiving moved to csvZipper.py
#resArchive = zipfile.ZipFile("resultArchive.zip", 'w')
#resArchive.write(sys.argv[1])
#resArchive.write("result.csv")
#resArchive.write("*.csv")
#resArchive.close()

parse = IometerResultParser("result.csv", sys.argv[2])

print("Result parse complete, exiting.")

exit(0)


