#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Randal Eike
# *****************************************************************************/
import re, os, sys
from optparse import OptionParser

##### .exe extension patch for the compiled version of this script
if not re.search('\.PY$|\.PYC$|\.EXE$', os.path.split(sys.argv[0])[1].upper()):
    sys.argv[0] = os.path.join( os.path.split(sys.argv[0])[0] , os.path.split(sys.argv[0])[1]+'.exe' )

#### extend the Python search path to include TWIDL_tools directory
if __name__ == '__main__':
    twidlcore = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    sys.path.insert(0,twidlcore)

#### import TWIDL modules
try:
    from device import *
    from device_api import *
    from devices.protocol_bases.nvme_base import logPull
except:
    print("ERROR: cannot find TWIDL")
    pass

#### import test utilities
from src.software.parse.output_log import OutputLog
from src.software.parse.internal.drive_utility import testDrive
from src.software.parse.internal.drive_utility import SetUlink
from src.software.parse.internal.drive_utility import ScanDrives
from src.software.parse.internal.drive_utility import driveList

#### import telemetry modules
from src.software.parse.telemetry_util import openReadFile
from src.software.parse.telemetry_util import openWriteFile
from src.software.parse.telemetry_util import cleanDir

from src.software.parse.internal.getTelemetry import readTelemetryLog
from src.software.parse.parseTelemetryBin import parseInputBin
from src.software.parse.testTelemetryPull import pullTest
from src.software.parse.internal.testCIAER import clearOldLogs

TOOL_VERSION           = 1.0

def makeDirName(dirName):
    folder = os.path.join(os.getcwd(), dirName)
    return folder

def makeFileName(fileName, dirName):
    folder = makeDirName(dirName)
    outName = os.path.join(folder, fileName)
    return outName


def main():
    drvIndex = None
    core = None

    #### Command-line arguments ####
    parser = OptionParser(usage="usage: %prog [options] outputFile", version="%prog Version: "+str(TOOL_VERSION))
    parser.add_option('--debug',type="int", dest='debug', action="store", default=0, help='Enable debug level')
    parser.add_option('-d',type='int', dest='drvnum', metavar='<DRVNUM>', default=None, help='Drive number to analyze')
    parser.add_option('-q',action='callback', callback=ScanDrives, help='Query system for the drive list')
    parser.add_option('--ulink',metavar='on|off|pc', default='', help='ULINK Control: ON, OFF, or Power Cycle (OFF+ON)')
    (options, args) = parser.parse_args()

    if (len(args) >= 1):
        outFile = args[0]
    else:
        outFile = "testAll.txt"

    # Initialize setup
    if (options.debug > 0):
        OutputLog.setDebugLevel(options.debug)
    else:
        OutputLog.enableQuiet()
    OutputLog.setWarnIsError(True)

    # check for ulink power cycle
    if (options.ulink):
        if(False == SetUlink(options.ulink)):
            OutputLog.Error("INVALID --ulink argument")
            sys.exit(1)

    #if no options specified use drive
    driveNumber = driveList.checkDriveIndex(options.drvnum)
    if(driveNumber is None): sys.exit(1)

    ### Select drive to analyze
    drive = testDrive(driveNumber)
    if (drive is None): sys.exit(1)

    ### Determine what to do
    drive.globalDriveSpecificParams()
    OutputLog.Information("Get Id information")
    OutputLog.Information(drive.toStr())
    if(False == drive.unlockDrive()): sys.exit(1)

    ### Verify drive is not asserted
    if (drive.isDriveAsserted()):
        OutputLog.Information( "\nDrive is asserted!!!" )
        AssertedDrive = True
    else:
        OutputLog.Information( "\nDrive is NOT asserted!!!" )
        AssertedDrive = False

    ### Perform Test ###
    testNumber = 0
    runTest = True
    exitStatus = True
    sataMaxBlockSize = 128    # 64K SATA max
    dut = logPull(drive.getTestDrive(), True, True)

    simplePullDir = "simple_pull"
    simpleHiLogName = makeFileName("v2hi_sataLog.bin", makeDirName(simplePullDir))
    simpleCiLogName = makeFileName("v2ci_sataLog.bin", makeDirName(simplePullDir))
    simplehiParse = "hi_parse"
    simpleciParse = "ci_parse"

    hiPullDir = "host_log_pull"
    ciPullDir = "ctrl_log_pull"
    ciEmptyPullDir = "ctrl_log_empty_pull"
    ciaerPullDir = "ciaer_pull"

    while ((True == exitStatus) and (True == runTest)):
        if (0 == testNumber):
            # Clean the output directories
            cleanDir(simplePullDir)
            cleanDir(simplehiParse)
            cleanDir(simpleciParse)
            cleanDir(hiPullDir)
            cleanDir(ciPullDir)
            cleanDir(ciEmptyPullDir)
            dut.setCiLog()
            clearOldLogs(dut)

        elif (1 == testNumber):
            # Perform basic HI pull test
            OutputLog.Print("Basic HI Log Pull...")
            telemetryData = openWriteFile(simpleHiLogName)
            dut.setHiLog()
            if(telemetryData is not None):
                exitStatus, ciGeneration = readTelemetryLog(dut, telemetryData, blockSize = 4096, block0Size = 512, createLog = True, doubleTOCRead = False)
                telemetryData.close()
            else:
                exitStatus = False

        elif (2 == testNumber):
            # Perform basic parse test on the HI file generated during the basic pull
            OutputLog.Print("Basic HI Log Check...")
            telemetryInputBin = openReadFile(simpleHiLogName)
            if(telemetryInputBin is not None):
                parseStatus, fileValidity = parseInputBin(telemetryInputBin, True, simplehiParse, None, False)
                if((False == parseStatus) or (False == fileValidity)):
                    OutputLog.Error(format("File \"%s\" failed validity check\n" % (simpleHiLogName)))
                    exitStatus = False
                telemetryInputBin.close()
            else:
                exitStatus = False


        elif (3 == testNumber):
            # Perform basic CI pull test
            OutputLog.Print("Basic CI Log Pull...")
            telemetryData = openWriteFile(simpleCiLogName)
            dut.setCiLog()
            if(telemetryData is not None):
                exitStatus, ciGeneration = readTelemetryLog(dut, telemetryData, blockSize = 4096, block0Size = 512, createLog = True, doubleTOCRead = False)
                telemetryData.close()
            else:
                exitStatus = False

        elif (4 == testNumber):
            # Perform basic parse test on the CI file generated during the basic pull
            OutputLog.Print("Basic CI Log Check...")
            telemetryInputBin = openReadFile(simpleCiLogName)
            if(telemetryInputBin is not None):
                parseStatus, fileValidity = parseInputBin(telemetryInputBin, False, simpleciParse, None, False)
                if((False == parseStatus) or (False == fileValidity)):
                    OutputLog.Error(format("File \"%s\" failed validity check\n" % (simpleCiLogName)))
                    exitStatus = False
                telemetryInputBin.close()
            else:
                exitStatus = False

        elif (5 == testNumber):
            # Test the log pull function
            OutputLog.Print("Multiple Block Size HI Log Pull...")
            dut.setHiLog()
            exitStatus = pullTest(dut, AssertedDrive,  makeDirName(hiPullDir), sataMaxBlockSize)

        elif (6 == testNumber):
            # Test the log pull function
            OutputLog.Print("Multiple Block Size CI Log Pull (no eventdump)...")
            dut.setCiLog()
            exitStatus = pullTest(dut, AssertedDrive,  makeDirName(ciEmptyPullDir), sataMaxBlockSize)

        elif (7 == testNumber):
            # Test the CI pull with event dump
            OutputLog.Print("Multiple Block Size CI Log Pull (eventdump)...")
            dut.setCiLog()
            dut.generateEvent()
            exitStatus = pullTest(dut, AssertedDrive,  makeDirName(ciPullDir), sataMaxBlockSize)
            clearOldLogs(dut)

        else:
            runTest = False

        testNumber += 1

    if(True == exitStatus): OutputLog.Print ("All bench tests passed!!!!")
    else: OutputLog.Print ("Bench test suite FAILED!!!")

    return exitStatus

######## Test it #######
if __name__ == '__main__':
    from datetime import datetime
    p = datetime.now()
    exitStatus = main()
    q = datetime.now()
    OutputLog.Print("\nExecution time: "+str(q-p))
    sys.exit(exitStatus)
