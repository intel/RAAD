#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
# Purpose       : Automates dataControl unit tests
import sys, os, re, copy, argparse, shutil, platform, csv, datetime, socket

from subprocess import Popen, PIPE

UIDCOUNTEXPECTED = 366

ENABLE_SHELL = False
myenv = os.environ.copy()

dataControlMainDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print("importing from %s" % dataControlMainDir)
sys.path.append(dataControlMainDir)

PY_FILE = os.path.join(dataControlMainDir, "dataControlGenMain.py")
UID_STRUCTURES_FILE = os.path.join(dataControlMainDir, "structures.csv")
LOG_FILE = os.path.join(dataControlMainDir, "test\\testAll_dataControlMain_log.txt")
PY_FILE_READ_TEST = os.path.join(dataControlMainDir, "test\\testRead_dataControlMain.py")
from testRead_dataControlMain import test_ReadCorrectCount


# calling subprocesses
def test_subproc(command, arg=None, pyFile=PY_FILE):
    if pyFile != PY_FILE:
        p = Popen([sys.executable, pyFile, command], stdin=PIPE, stdout=PIPE)
    else:
        if not arg:
            p = Popen([sys.executable, pyFile, command, "--file", UID_STRUCTURES_FILE, "--debug"], stdin=PIPE,
                      stdout=PIPE, shell=ENABLE_SHELL, env=myenv)
        else:
            p = Popen([sys.executable, pyFile, command, arg, "--file", UID_STRUCTURES_FILE, "--debug"], stdin=PIPE,
                      stdout=PIPE, shell=ENABLE_SHELL, env=myenv)
    pCout, pErr = p.communicate()

    if p.returncode == 0:  # call passed
        with open(LOG_FILE, "w+") as wFile:
            wFile.write(str(pCout))
            wFile.write(str(pErr))
            wFile.write("\ndone!\n")
    else:
        print("======================\n")
        print("ERROR, EXITED. SEE LOG FILE FOR ERRORS\n")
        print("======================\n")
        print("CHECK LOG AND CSV FILE TO MAKE SURE EXPECTED OUTPUT MATCHES\n")
        quit(1)


def main():
    print("==Testing...\n")
    print("PyFile = %s\n" % PY_FILE)
    print("CSV File = %s\n" % UID_STRUCTURES_FILE)
    print("OutFile = %s\n" % LOG_FILE)

    with open(LOG_FILE, "w+") as wFile:
        wFile.write("==TESTING META FILE READ...")
        wFile.write("Creating brand new structures_test.csv Test File. Vital for successful run.\n")
        wFile.write("Testing that reads expected number of Uids Given: %s\n" % UIDCOUNTEXPECTED)
    # test_ReadCorrectCount(UIDCOUNTEXPECTED)
    test_subproc(str(UIDCOUNTEXPECTED), pyFile=PY_FILE_READ_TEST)

    print("Running...\n")

    with open(LOG_FILE, "w+") as wFile:
        wFile.write("==TESTING CREATE metaUID: AUTO\n")
    test_subproc('--create', "[AUTO,testStructName1,6,Transport_PART,ADP,()]")

    with open(LOG_FILE, "w+") as wFile:
        wFile.write("==TESTING CREATE metaUID: SINGLE COMMAND LINE GIVEN UID\n")
    test_subproc('--create', "[temp_it2,testStructName2,6,Transport_PART,ADP,()]")

    with open(LOG_FILE, "w+") as wFile:
        wFile.write("==TESTING CREATE metaUID: MULTPLE COMMAND LINE GIVEN UIDs")
    test_subproc("--create",
                 "[AUTO,testStructName3,6,Transport_PART,ADP,();temp_4,testStructName4,6,Transport_PART,CDR,();temp_5,testStructName5,6,Transport_PART,CDR,();temp_6,testStructName6,6,Transport_PART,CDR,();temp_7,testStructName7,6,Transport_PART,CDR,();temp_8,testStructName8,6,Transport_PART,CDR,()]")

    with open(LOG_FILE, "w+") as wFile:
        wFile.write("==TESTING CREATE metaUID: ALREADY USED UID")
    test_subproc("--create", "[0,testStructName0,6,Transport_PART,ADP,()]")

    with open(LOG_FILE, "w+") as wFile:
        wFile.write("==TESTING DEPRECATE metaUID: SINGLE TEMP UID")
    test_subproc("--deprecate", "[temp_it2,TWO]")

    with open(LOG_FILE, "w+") as wFile:
        wFile.write("==TESTING DEPRECATE metaUID: MULTIPLE TEMP UIDs")
    test_subproc("--deprecate", "[temp_0,TWO;temp_4,TWO]")

    with open(LOG_FILE, "w+") as wFile:
        wFile.write("==TESTING DEPRECATE metaUID: SINGLE PERMANENT UID")
    test_subproc("--deprecate", "[1,TWO]")

    with open(LOG_FILE, "w+") as wFile:
        wFile.write("==TESTING DEPRECATE metaUID: MULTIPLE PERMANENT UIDs")
    test_subproc("--deprecate", "[2,TWO;3,TWO]")

    with open(LOG_FILE, "w+") as wFile:
        wFile.write("==TESTING DEPRECATE metaUID: MEDLEY UIDs")
    test_subproc("--deprecate", "[temp_8,TWO;1,ONE]")

    with open(LOG_FILE, "w+") as wFile:
        wFile.write("==TESTING EDIT metaUID: SINGLE TEMP UID")
    test_subproc("--edit", "[temp_1,TWO,(owner='single_temp_edit',size='0x30')]")

    with open(LOG_FILE, "w+") as wFile:
        wFile.write("==TESTING EDIT metaUID: MULTIPLE TEMP UIDs")
    test_subproc("--edit",
                 "[temp_4,TWO,(owner='multiple_temp_edit',size='0x30');temp_6,TWO,(owner='multiple_temp_edit',autoparsability='WHOO')]")

    with open(LOG_FILE, "w+") as wFile:
        wFile.write("==TESTING EDIT metaUID: MULTIPLE PERMANENT UIDs")
    test_subproc("--edit",
                 "[4,TWO,(owner='multiple_perm_edit',size='0x30');5,TWO,(owner='multiple_perm_edit',size='0x30')]")

    with open(LOG_FILE, "w+") as wFile:
        wFile.write("==TESTING EDIT metaUID: MEDLEY UIDs")
    test_subproc("--edit",
                 "[temp_7,TWO,(owner='Andrea_test',size='0x30');0,ONE,(owner='Andrea_test',autoparsability='WHOO')]")

    with open(LOG_FILE, "w+") as wFile:
        wFile.write("==TESTING H metaUID: SINGLE CALL")
    test_subproc("--h")

    with open(LOG_FILE, "w+") as wFile:
        wFile.write("==TESTING IMPLEMENT metaUID: CHANGES, TEST H FILE UPDATED AS WELL")
    test_subproc("--implement")

    print("Done. See %s for output\n" % LOG_FILE)


if __name__ == '__main__':
    main()
