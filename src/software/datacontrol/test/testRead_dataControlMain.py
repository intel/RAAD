#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
# Purpose       : Tests data structure construction of dataControlGenMain
import sys, os, re, copy, argparse, shutil, platform, csv, datetime, socket

dataControlMainDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print("importing from %s" % dataControlMainDir)
sys.path.append(dataControlMainDir)
from src.software.datacontrol.dataControlGenMain import DatacontrolGenCSV


def test_ReadCorrectCount(uidExpectedCount):
    '''Assumes telemetryStructs.csv exists in same directory'''
    # TEST: READ UID DICTIONARY
    print("===============================================")
    print("==Testing CSV API READABILITY==")
    # 359 uids in testing
    structuresFile = os.path.join(dataControlMainDir, 'structures.csv')
    filename, file_extension = os.path.splitext(structuresFile)
    # copy file, rename
    structuresFile_copy = filename + "_test" + file_extension
    print("Running Test on Test File: %s\n" % structuresFile_copy)
    shutil.copyfile(structuresFile, structuresFile_copy)  # vital

    dgcTest = DatacontrolGenCSV(structuresFile_copy)

    uidCount = len(dgcTest.uidMasterDictV1.keys()) + len(dgcTest.uidMasterDictV2.keys())
    if uidCount != uidExpectedCount:
        print("\nFAILED: %s uids created, %s expected\n" % (uidCount, uidExpectedCount))
        print(dgcTest)
        # raise Exception(" READ TEST FAILED: %s uids created, %s expected\n" %(uidCount, UIDSTARTCOUNT))
    else:
        print("SUCCESS!")
    print("===============================================")


if __name__ == '__main__':
    test_ReadCorrectCount(sys.argv[1])
