#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Randal Eike
# *****************************************************************************/
# @file: testTelemetryPull.py
# This file is based on testSetup.py from Phuong Tran.  This file will pull
# the telemetry logs using different block sizes in sequencial and random order
# to test NVMe specification complience
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import re, os, sys, array, ctypes, time, glob, getopt, math
import random
from optparse import OptionParser, OptionGroup
from operator import itemgetter

##### .exe extension patch for the compiled version of this script
if not re.search('\.PY$|\.PYC$|\.EXE$', os.path.split(sys.argv[0])[1].upper()):
    sys.argv[0] = os.path.join( os.path.split(sys.argv[0])[0] , os.path.split(sys.argv[0])[1]+'.exe' )

#### extend the Python search path to include TWIDL_tools directory
if __name__ == '__main__':
    twidlcore = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    sys.path.insert(0,twidlcore)

#### import test utilities
from src.software.parse.output_log import OutputLog
from src.software.parse.internal.drive_utility import testDrive
from src.software.parse.internal.drive_utility import SetUlink
from src.software.parse.internal.drive_utility import ScanDrives
from src.software.parse.internal.drive_utility import driveList

#### import telemetry modules
from src.software.parse.telemetry_drive import logDevice
from src.software.parse.telemetry_util import TelemetryLogBlockSize
from src.software.parse.telemetry_util import openReadFile
from src.software.parse.telemetry_util import openWriteFile
from src.software.parse.telemetry_util import cleanDir

from src.software.parse.headerTelemetry import *
from src.software.parse.intelVUTelemetry import *
from src.software.parse.parseTelemetryBin import checkLogListValidity

AbortOnAssertedDrive = False
TelemetryV1Last = 5
TelemetryV2Last = 300

TOOL_VERSION           = 2.1
DEBUG_VERSION          = 0

def compareTelemetryBinFiles(baseFileName, compareFileName):
    """
    Compare the input binary files
    """
    returnStatus = True
    """
    if (baseFileName != compareFileName):
        fcCmd = format("fc /b %s %s > %s" % (baseFileName, compareFileName, baseFileName+"_err"))
        retValue = os.system(fcCmd)
        if(0 != retValue):
            returnStatus = False
            OutputLog.Error(format("File comparison failed \'%s\' != \'%s\'" % (baseFileName, compareFileName)))
    """
    return returnStatus

def getFileName(outdir, basename, blocksize, sequencialOrder, randomSize, asserted, create):
    ### generate outputfile ###
    if (True == asserted): basename += "_asserted"

    if (True == sequencialOrder): orderstr = "_SeqOrder"
    else: orderstr = "_RndOrder"

    if (False == randomSize): sizestr = "_size_"+str(blocksize)
    else: sizestr = "_rndSize_max_"+str(blocksize)

    if(outdir is not None):
        outFile = os.path.join(outdir, basename+orderstr+sizestr+"_log.bin")
    else:
        outFile = basename+orderstr+sizestr+"_log.bin"

    if (False == create): outFile += "1"
    return outFile

def prepTestDrive(tstDrive, readVUHeaderFirst, minBytes, telemetryData, createList):
    """
    Prepare the test drive for the test
    """
    # Set the create bit
    if(createList): createBit = 1
    else: createBit = 0

    # Read block 0, NVMe telemetry data header
    OutputLog.DebugPrint(1, "Read Telemetry Header:")
    if(False == tstDrive.getLogPage(minBytes, 0, createBit, 1)):
        OutputLog.Error("Telemetry header read failed")
        return  None, None
    tstDrive.writeBlock(telemetryData, minBytes)

    # Parse the header data to see how many more blocks to read
    telemetryHeader = tstDrive.getInterfaceHeader()
    if (telemetryHeader is None):
        OutputLog.Error("Invalid log interface header")
        return  None, None

    # Validate the header
    OutputLog.DebugPrint (1, telemetryHeader.tostr())
    if(False == telemetryHeader.validate()):
        OutputLog.Error("Invalid Header data")
        return  None, None

    # Get the Data area block offsets
    lastBlock, dataAreaLastBlockList = telemetryHeader.getLastBlock()

    # Read all the Data area headers first if requested
    if (readVUHeaderFirst):
        dataAreaStartOffset = TelemetryLogBlockSize
        dataArea = 1
        # read each data Area
        for dataAreaLastBlock in dataAreaLastBlockList:
            # Determine the number of dwords to read, make sure we don't overflow runt logs
            maxBytes = (lastBlock * TelemetryLogBlockSize)
            readBytes = min(minBytes, maxBytes)

            if(False == tstDrive.getLogPage(readBytes, dataAreaStartOffset, 0, RAE=1)):
                OutputLog.Error(format("Read of data area %d Table of contents failed" %(dataArea)))
                return  None, None

            TOCReadSize = readBytes
            tocHeader = intelTelemetryTOC_union(tstDrive.getReadBuffer(), TOCReadSize).getStruct()
            OutputLog.DebugPrint(1, tocHeader.tostr())
            if (False == tocHeader.validate()):
                OutputLog.Error(format("Invalid VU Data Area %d header data\n" % (dataArea)))
                return  None, None

            # Move on to next data Area
            dataAreaStartOffset = dataAreaLastBlock * TelemetryLogBlockSize
            dataArea += 1

    return lastBlock, dataAreaLastBlockList

def randomBlockReadTelemetryLogs(tstDrive, outfileName, readVUHeaderFirst = False, minBlockRead = 1, maxBlockRead = 256, sequencial = True, createList = True, asserted = False):
    """
    Read random blocks of minimumBlockSize
    """
    # set minimum read sizes
    minBytes = minBlockRead * TelemetryLogBlockSize
    maxBytes = maxBlockRead * TelemetryLogBlockSize

    # open the log file
    if(minBlockRead == maxBlockRead): randomSize = False
    else: randomSize = True
    telemetryData = openWriteFile(outfileName)

    # Get the Data area block offsets
    lastBlock, dataAreaLastBlockList = prepTestDrive(tstDrive, readVUHeaderFirst, minBytes, telemetryData, createList)
    if ((lastBlock is None) or (dataAreaLastBlockList is None)):
        return False

    # Create a list of blocks to read
    blockReadList = []
    offset = TelemetryLogBlockSize
    logEndOffset = lastBlock * TelemetryLogBlockSize

    OutputLog.DebugPrint(1, format("Last block from header %d" %(lastBlock)))

    while (offset < logEndOffset):
        if (minBlockRead != maxBlockRead):
            readBlocks = random.randrange(minBlockRead, maxBlockRead, minBlockRead) # Random number between min and max by step of min
            readBytes = readBlocks * TelemetryLogBlockSize
        else:
            readBytes = minBlockRead * TelemetryLogBlockSize

        if ((readBytes + offset) > logEndOffset):
            readBytes = logEndOffset - offset   # truncate to end of log

        location = (offset, readBytes)
        blockReadList.append(location)
        offset += readBytes

    # randomize the list if not sequencial
    if (sequencial is False):
        random.shuffle(blockReadList)

    # Read the data
    for readLocation in blockReadList:
        readLocOffset, readLocBytes = readLocation
        if(False == tstDrive.getLogPage(readLocBytes, readLocOffset, 0, 1)):
            return False
        else:
            telemetryData.seek(readLocOffset)
            tstDrive.writeBlock(telemetryData, readLocBytes)

    telemetryData.close()
    return True

def pullTest(drive, AssertedDrive, outputDir, maxBlockCount = 256, sequencialOnly = False):
    readTestPass = True
    runTest = True
    testNumber = 1
    fileCompareList = []
    outputFileList = []
    lastCreatedFile = None
    absMaxBlockCount = min (256, maxBlockCount)
    defaultBlockCount = min (8, maxBlockCount)

    # Clean the output directory
    if (outputDir is not None):
        cleanDir(outputDir)

    # Run the test sequence
    while ((True == readTestPass) and (True == runTest)):
        skipTest = False

        # Set the parameters
        if (testNumber == 1):
            if (defaultBlockCount > 1):
                OutputLog.Information(format("%dK block size, sequencial order ... " % (defaultBlockCount/2)))
                minBlocks = defaultBlockCount
                maxBlocks = defaultBlockCount
                seqOrder = True
                createFlag = True
            else:
                skipTest = True
        elif (testNumber == 2):
            OutputLog.Information("Single block size, sequencial order ... ")
            minBlocks = 1
            maxBlocks = 1
            seqOrder = True
            createFlag = True
        elif (testNumber == 3):
            if (absMaxBlockCount > defaultBlockCount):
                OutputLog.Information(format("%dK block size, sequencial order ... " % (absMaxBlockCount/2)))
                minBlocks = absMaxBlockCount
                maxBlocks = absMaxBlockCount
                seqOrder = True
                createFlag = True
            else:
                skipTest = True
        elif (testNumber == 4):
            if(absMaxBlockCount > 1):
                OutputLog.Information(format("Random .5 to %dK block size, sequencial order ... " % (absMaxBlockCount/2)))
                minBlocks = 1
                maxBlocks = absMaxBlockCount
                seqOrder = True
                createFlag = True
            else:
                skipTest = True
        elif (testNumber == 5):
            if(False == sequencialOnly):
                OutputLog.Information(format("%dK block size, random order ... " % (defaultBlockCount/2)))
                minBlocks = defaultBlockCount
                maxBlocks = defaultBlockCount
                seqOrder = False
                createFlag = True
            else:
                skipTest = True
        elif (testNumber == 6):
            if((False == sequencialOnly) and (defaultBlockCount > 1)):
                OutputLog.Information("Single block size, random order ... ")
                minBlocks = 1
                maxBlocks = 1
                seqOrder = False
                createFlag = True
            else:
                skipTest = True
        elif (testNumber == 7):
            if((False == sequencialOnly) and (defaultBlockCount > 1)):
                OutputLog.Information(format("Random .5 to %dK block size, random order ... " % (defaultBlockCount/2)))
                minBlocks = 1
                maxBlocks = defaultBlockCount
                seqOrder = False
                createFlag = True
            else:
                skipTest = True
        elif (testNumber == 8):
            if((False == sequencialOnly) and (absMaxBlockCount > defaultBlockCount)):
                OutputLog.Information(format("Random .5 to %dK block size, random order ... " % (absMaxBlockCount/2)))
                minBlocks = 1
                maxBlocks = absMaxBlockCount
                seqOrder = False
                createFlag = True
            else:
                skipTest = True
        elif (testNumber == 9):
            OutputLog.Information(format("%dK block size, sequencial order, create=False ... " % (defaultBlockCount/2)))
            minBlocks = defaultBlockCount
            maxBlocks = defaultBlockCount
            seqOrder = True
            createFlag = False
        elif (testNumber == 10):
            if(absMaxBlockCount > defaultBlockCount):
                OutputLog.Information(format("%dK block size, sequencial order, create=False ... " % (absMaxBlockCount/2)))
                minBlocks = absMaxBlockCount
                maxBlocks = absMaxBlockCount
                seqOrder = True
                createFlag = False
            else:
                skipTest = True
        else:
            runTest = False

        if ((True == runTest) and (False == skipTest)):
            # Generate the file name
            if (minBlocks == maxBlocks): rndSize = False
            else: rndSize = True
            outFileName = getFileName(outdir = outputDir, basename = drive.getLogNameBase(), blocksize = maxBlocks, sequencialOrder = seqOrder, randomSize = rndSize, asserted = AssertedDrive, create = createFlag)

            # Run the read test
            if (False == randomBlockReadTelemetryLogs(drive, outFileName, readVUHeaderFirst = False, minBlockRead = minBlocks, maxBlockRead = maxBlocks, sequencial = seqOrder, createList = createFlag, asserted = AssertedDrive)):
                OutputLog.Information("failed")
                readTestPass = False
            else:
                # Good read, add it to the output list
                outputFileList.append(outFileName)

                # Track the compare list
                if(True == createFlag):
                    lastCreatedFile = outFileName
                else:
                    fileCompareList.append((lastCreatedFile, outFileName))
                OutputLog.Information("passed")

        # Next test
        testNumber += 1

    # Check the output data files for basic validity
    validityCheckPassed = True
    OutputLog.Information("Check output file basic validity...")
    validityCheckPassed = checkLogListValidity(outputFileList, drive.isHiLogTest())
    if(validityCheckPassed): OutputLog.Information("passed\n")
    else: OutputLog.Information ("failed\n")

    # Compare the output data
    compareTestPassed = True
    OutputLog.Information("Check create = 0 files match...")
    if(False == AssertedDrive):
        # Only works if drive is not asserted, else data is live and subject to change without notice
        if(False == drive.isHiLogTest()):
            # This test does not generate or clear CI logs so all logs should match
            baseFile = outputFileList[0]
            for fileName in outputFileList:
                if(False == compareTelemetryBinFiles(baseFile, fileName)):
                    compareTestPassed = False
                OutputLog.DebugPrint(1, format("File compare CI logs \'%s\' and \'%s\' passed" % (baseFile, fileName)))
        else:
            # Compare created file with dup file
            for files in fileCompareList:
                if(False == compareTelemetryBinFiles(files[0], files[1])):
                    compareTestPassed = False
                OutputLog.DebugPrint(1, format("File compare HI logs \'%s\' and \'%s\' passed" % (files[0], files[1])))

    if(compareTestPassed): OutputLog.Information ("passed\n")
    else: OutputLog.Information ("failed\n")

    # Final message and exit
    if((True == readTestPass) and (True == validityCheckPassed) and (True == compareTestPassed)):
        OutputLog.Information ("Test Complete, no errors\n")
        exitStatus = True
    else:
        OutputLog.Information ("Test Complete, test FAILED!\n")
        exitStatus = False
    return exitStatus


def main():
    #### Command-line arguments ####
    parser = OptionParser(usage="usage: %prog [options]", version="%prog Version: "+str(TOOL_VERSION))
    parser.add_option('--debug',type="int", dest='debug', action="store", default=0, help='Enable debug level')
    parser.add_option('-d',type='int',dest='drvnum',metavar='<DRVNUM>',default=None,help='Drive number to analyze')
    parser.add_option('-q',action='callback',callback=ScanDrives,help='Query system for the drive list')
    parser.add_option('-o',action='store',dest="outDir", default=None, help='Output directory')
    parser.add_option('--hi',action='store_true', dest="hilog", default=True, help='Pull Host Initiated log (this is the default case)')
    parser.add_option('--ci',action='store_false', dest="hilog", help='Pull Controller Initiated log')
    parser.add_option('--maxblock', action='store', dest="maxBlocks", default = 256, help='Maximum block count for pulls (default = 256, 128K)')
    parser.add_option('--ulink',metavar='on|off|pc',default='',help='ULINK Control: ON, OFF, or Power Cycle (OFF+ON)')
    (options, args) = parser.parse_args()

    # Initialize setup
    baseArgIndex = 0
    OutputLog.setDebugLevel(options.debug)

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

    ### Verify drive is not asserted
    if (drive.isDriveAsserted()):
        OutputLog.Information( "\nDrive is asserted!!!" )
        AssertedDrive = True
    else:
        OutputLog.Information( "\nDrive is NOT asserted!!!" )
        AssertedDrive = False

    ### Perform Test ###
    logDrive = logDevice(drive.getTestDrive(), options.hilog)
    if(True == pullTest(logDrive, AssertedDrive, options.outDir, int(options.maxBlocks))): return 0
    else: return 1

######## Test it #######
if __name__ == '__main__':
    from datetime import datetime
    p = datetime.now()
    exitStatus = main()
    q = datetime.now()
    OutputLog.Information("\nExecution time: "+str(q-p))
    sys.exit(exitStatus)
