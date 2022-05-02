#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Randal Eike, Phuong Tran, Joseph Tarango
# *****************************************************************************/
import re, os, sys, array, ctypes, time, glob, getopt, math
from optparse import OptionParser, OptionGroup
from operator import itemgetter

##### .exe extension patch for the compiled version of this script
if not re.search('\.PY$|\.PYC$|\.EXE$', os.path.split(sys.argv[0])[1].upper()):
    sys.argv[0] = os.path.join(os.path.split(sys.argv[0])[0], os.path.split(sys.argv[0])[1] + '.exe')

#### extend the Python search path to include TWIDL_tools directory
#### import necessary paths
importPath = os.path.abspath(os.getcwd())
importPathNext = os.path.abspath(os.path.join(importPath, "bin"))
print("Importing Paths: ", str(importPath), str(importPathNext))
sys.path.insert(1, importPath)
sys.path.insert(1, importPathNext)

# import test utilities
from src.software.parse.output_log import OutputLog
from src.software.parse.internal.drive_utility import testDrive
from src.software.parse.internal.drive_utility import SetUlink
from src.software.parse.internal.drive_utility import ScanDrives
from src.software.parse.internal.drive_utility import driveList

# import telemetry modules
from src.software.parse.telemetry_drive import logDevice
from src.software.parse.telemetry_util import TelemetryLogBlockSize
from src.software.parse.telemetry_util import openReadFile
from src.software.parse.telemetry_util import openWriteFile
from src.software.parse.telemetry_util import cleanDir

from src.software.parse.headerTelemetry import *
from src.software.parse.intelVUTelemetry import *

TelemetryV1Last = 5
TelemetryV2Last = 300
version1BlockSize = 4096
BYTES_PER_DWORD = 4

tocDataAreaList = []
aplDataAreaList = []

# dnvme setup data
TOOL_VERSION = 2.1
DEBUG_VERSION = 0


def validateVUTOC(bufferObj, bufferSize):
    """
    Validate the TOC

    @param bufferObj    Buffer object containing the data
    @param bufferSize   Size of the buffer object in bytes

    @return True if the TOC is valid else False
    """
    # Validate the data
    OutputLog.Information("Apply structure to data area TOC data and validate data")
    telemetryVUHeader = intelTelemetryTOC_union(bufferObj, bufferSize).getStruct()
    OutputLog.DebugPrint(2, telemetryVUHeader.tostr())
    if (False == telemetryVUHeader.validate()):
        OutputLog.Error("VU header validation failed.")
        return False
    else:
        return True


def readVUTOCBlock(tstDrive, telemetryData, startOffset, readBlockSize=4096, doubleRead=False):
    """
    Read the VU toc, Request the entire Data Area Block at a time

    @param tstDrive         logDevice object to pull the log from
    @param telemetryData    File object to output the log data to.
    @param startOffset      Offset of the VU TOC in the log page
    @param readBlockSize    Byte count to read
    @param doubleRead       True = Read the TOC twice and make sure the two reads return the same data,
                            False = Single read and validate to the TOC

    @return status = True if there was no error, False if an error occured
    """
    status = True

    # Read the data
    strMeta = f"Read Telemetry data area VUHeader, offset 0x{startOffset:x}:"
    OutputLog.DebugPrint(1, strMeta)
    if (True == tstDrive.getLogPage(readBlockSize, startOffset, 0, 1)):
        tstDrive.writeBlock(telemetryData, readBlockSize)
        if (OutputLog.debugOutputLevel >= 2):
            status = validateVUTOC(tstDrive.getReadBuffer(), readBlockSize)
    else:
        status = False

    if (doubleRead and status):
        OutputLog.DebugPrint(1, "Read Telemetry data area VUHeader (2nd time):")
        if (True == tstDrive.getLogPage(readBlockSize, startOffset, 0, 1)):
            status = validateVUTOC(tstDrive.getReadBuffer(), readBlockSize)
        else:
            status = False
    return status


def readTelemetryLogInterfaceHeader(tstDrive, telemetryData, interfaceLogSize, createLog=True):
    """
    Read the interface header data

    @param tstDrive         logDevice object to pull the log from
    @param telemetryData    File object to output the log data to.
    @param interfaceLogSize Byte count to read
    @param createLog        True = send create log to drive, False read interface log without creation

    @return lastBlock = Last block number of the log,
            dataAreaLastBlockList = List of the last blocks for each data area,
            ciAvailable = True if a controller initiated log is available else False,
            ciGeneration = Generation number of the controller initiated log,
            block0Size = Size of the interface header block in bytes, either 512 or 4096
    """
    # Set the block 0 create flag
    if (createLog):
        create = 1
    else:
        create = 0

    # Read block 0, NVMe telemetry data header
    OutputLog.DebugPrint(1, "Read Telemetry Header:")
    numDwords = (interfaceLogSize / BYTES_PER_DWORD) - 1
    if (True == tstDrive.getLogPage(int(interfaceLogSize), 0, create, 1)):
        tstDrive.writeBlock(telemetryData, interfaceLogSize)

        # Parse the header data to see how many more blocks to read
        telemetryHeader = tstDrive.getInterfaceHeader()
        if (telemetryHeader is None):
            return None, None, None, None, interfaceLogSize

        OutputLog.DebugPrint(1, telemetryHeader.tostr())
        if (False == telemetryHeader.validate()):
            OutputLog.Error("Invalid Header data")
            return None, None, None, None, interfaceLogSize

        lastBlock, dataAreaLastBlockList = telemetryHeader.getLastBlock()
        ciAvailable, ciGeneration = telemetryHeader.getCIdata()
        if (telemetryHeader.IsVersion1()):
            block0Size = version1BlockSize
        else:
            block0Size = TelemetryLogBlockSize
        return lastBlock, dataAreaLastBlockList, ciAvailable, ciGeneration, block0Size
    else:
        OutputLog.Error("Interface header read failed")
        return None, None, None, None, interfaceLogSize


def readTelemetryDataArea(tstDrive, telemetryData, startOffset, lastBlock, readBlockSize=4096, TOCAlignedBlock=False, doubleTOCRead=False):
    """
    Read the telemetry data area

    @param tstDrive         logDevice object to pull the log from
    @param telemetryData    File object to output the log data to.
    @param startOffset      Offset of the VU TOC in the log page
    @param lastBlock        Last block number of the data area
    @param readBlockSize    Byte count to read (default = 4K)
    @param TOCAlignedBlock  True = starting offset is aligned with the start of the data area, False = starting offset is not aligned (default = False)
    @param doubleTOCRead    True = Read the TOC twice and make sure the two reads return the same data,
                            False = Single read and validate to the TOC, this is the default value

    @return status = True if there was no error, False if an error occured
    """
    if (0 != (readBlockSize % TelemetryLogBlockSize)):
        OutputLog.Error("Read block size must be a multiple of 512!!")
        return False

    if (tstDrive is None):
        OutputLog.Error("Invalid input drive object!!")
        return False

    # Initialize the offset data
    currentOffset = startOffset
    endOffset = lastBlock * TelemetryLogBlockSize
    remainingByteCount = endOffset - currentOffset
    applyTOC = TOCAlignedBlock

    # Read the rest of the data
    while (currentOffset < endOffset):
        # Set the read count
        byteCount = readBlockSize
        if (remainingByteCount < byteCount):
            byteCount = remainingByteCount

        # Read the data
        OutputLog.DebugPrint(2, "Reading block " + str(currentOffset / TelemetryLogBlockSize) + " bytes: " + str(byteCount) + " offset: " + str(currentOffset) + " remaining: " + str(remainingByteCount))

        if (applyTOC):
            applyTOC = False
            if (False == readVUTOCBlock(tstDrive, telemetryData, currentOffset, byteCount, doubleTOCRead)):
                OutputLog.Error("Telemetry VU TOC validation failed")
                return False
        else:
            if (True == tstDrive.getLogPage(byteCount, currentOffset, 0, 1)):
                tstDrive.writeBlock(telemetryData, byteCount)
            else:
                OutputLog.Error("Get Telemetry Log page failed: offset = " + str(currentOffset))
                return False

        # adjust the pointers
        currentOffset += byteCount
        remainingByteCount -= byteCount

    return True


# @ TODO
def readTelemetryLogByUid(tstDrive, telemetryData, blockSize=4096, block0Size=TelemetryLogBlockSize, createLog=True, doubleTOCRead=False):
    """
    Read the telemetry log, split into uids

    @param tstDrive         logDevice object to pull the log from
    @param telemetryData    File object to output the log data to.
    @param blockSize        Byte count of blocks to read (default 4K)
    @param block0Size       Byte count of interface header block to read (default = 512)
    @param createLog        True = Issue create with first log page request, False = issue all log page requests with no create flag (default = True)
    @param doubleTOCRead       True = Read the TOC twice and make sure the two reads return the same data,
                            False = Single read and validate to the TOC this is the default value

    @return status = True if there was no error, False if an error occured,
            ciGeneration = Current controller initiated generation from the interface header page
    """
    readStatus = None
    # Check the input block size
    if (((blockSize % TelemetryLogBlockSize) != 0) or ((block0Size % TelemetryLogBlockSize) != 0)):
        strMeta = f"Block size must be a multiple of the telemetry sector size ({TelemetryLogBlockSize} bytes)"
        OutputLog.Error(strMeta)
        return False, 0

    # Read block 1, NVMe telemetry data header
    lastBlock, dataAreaLastBlockList, ciAvailable, ciGeneration, block0Alignment = readTelemetryLogInterfaceHeader(tstDrive, telemetryData, block0Size, createLog)
    if ((lastBlock is None) and (dataAreaLastBlockList is None)):
        OutputLog.Error("Interface header data area last blocks invalid")
        return False, ciGeneration

    # Parse telemetry data header to get uid Locations

    # Initialize data read offset
    dataAreaStartOffset = block0Size
    dataArea = 1

    # Test if this is a data area aligned read or not
    if ((block0Size == block0Alignment) and (dataAreaLastBlockList is not None)):
        # read each data Area
        for dataAreaLastBlock in dataAreaLastBlockList:
            # Read the data area and check the status
            OutputLog.DebugPrint(2, "Read Telemetry Data Area " + str(dataArea) + ", offset: " + str(dataAreaStartOffset) + ", last block: " + str(dataAreaLastBlock) + ", blocksize: " + str(blockSize))
            readStatus = readTelemetryDataArea(tstDrive, telemetryData, dataAreaStartOffset, dataAreaLastBlock, blockSize, True, doubleTOCRead)
            if (False == readStatus):
                OutputLog.Error("Read data area failed")
                return False, ciGeneration

            # Move on to next data Area
            dataAreaStartOffset = dataAreaLastBlock * TelemetryLogBlockSize
            dataArea += 1
    else:
        # Read the data area and check the status
        OutputLog.DebugPrint(2, "Read Telemetry Data offset: " + str(dataAreaStartOffset) + ", last block: " + str(lastBlock) + ", blocksize: " + str(blockSize))
        readStatus = readTelemetryDataArea(tstDrive, telemetryData, dataAreaStartOffset, lastBlock, blockSize, False, False)

    return readStatus, ciGeneration


def readTelemetryLog(tstDrive, telemetryData, blockSize=4096, block0Size=TelemetryLogBlockSize, createLog=True, doubleTOCRead=False):
    """
    Read the telemetry log

    @param tstDrive         logDevice object to pull the log from
    @param telemetryData    File object to output the log data to.
    @param blockSize        Byte count of blocks to read (default 4K)
    @param block0Size       Byte count of interface header block to read (default = 512)
    @param createLog        True = Issue create with first log page request, False = issue all log page requests with no create flag (default = True)
    @param doubleTOCRead    True = Read the TOC twice and make sure the two reads return the same data,
                            False = Single read and validate to the TOC this is the default value

    @return status = True if there was no error, False if an error occured,
            ciGeneration = Current controller initiated generation from the interface header page
    """
    readStatus = None
    # Check the input block size
    if (((blockSize % TelemetryLogBlockSize) != 0) or ((block0Size % TelemetryLogBlockSize) != 0)):
        OutputLog.Error(f"Block size must be a multiple of the telemetry sector size ({TelemetryLogBlockSize}")
        return False, 0

    # Read block 1, NVMe telemetry data header
    lastBlock, dataAreaLastBlockList, ciAvailable, ciGeneration, block0Alignment = readTelemetryLogInterfaceHeader(tstDrive, telemetryData, block0Size, createLog)
    if ((lastBlock is None) and (dataAreaLastBlockList is None)):
        OutputLog.Error("Interface header data area last blocks invalid")
        return False, ciGeneration

    # Initialize data read offset
    dataAreaStartOffset = block0Size
    dataArea = 1

    # Test if this is a data area aligned read or not
    if ((block0Size == block0Alignment) and (dataAreaLastBlockList is not None)):
        # read each data Area
        for dataAreaLastBlock in dataAreaLastBlockList:
            # Read the data area and check the status
            OutputLog.DebugPrint(2, "Read Telemetry Data Area " + str(dataArea) + ", offset: " + str(dataAreaStartOffset) + ", last block: " + str(dataAreaLastBlock) + ", blocksize: " + str(blockSize))
            readStatus = readTelemetryDataArea(tstDrive, telemetryData, dataAreaStartOffset, dataAreaLastBlock, blockSize, True, doubleTOCRead)
            if (False == readStatus):
                OutputLog.Error("Read data area failed")
                return False, ciGeneration

            # Move on to next data Area
            dataAreaStartOffset = dataAreaLastBlock * TelemetryLogBlockSize
            dataArea += 1
    else:
        # Read the data area and check the status
        OutputLog.DebugPrint(2, "Read Telemetry Data offset: " + str(dataAreaStartOffset) + ", last block: " + str(lastBlock) + ", blocksize: " + str(blockSize))
        readStatus = readTelemetryDataArea(tstDrive, telemetryData, dataAreaStartOffset, lastBlock, blockSize, False, False)

    return readStatus, ciGeneration


def getTelemetryAPI(outFile="telemetry.bin", outDir=None, drvnum=None, hilog=True, sata=False, version1=False, readBlockSize=None, readBlock0Size=None, ulink='', createLog=True, doubleTOCRead=False, debug=0, prepend=True):
    """
    Args:
        outFile:      Location where to save Telemetry Binary
        outDir:       Output directory
        drvnum:       Drive number to analyze
        hilog:        Pull Host Initiated log (this is the default case), if False, Pull Controller Initiated log
        sata:         If False NVME drive (default), if True, specify SATA drive
        version1:     If True Telemetry Version 1, else, Version 2 (default)
        readBlockSize:    Specify Block size in bytes(default = 4096)
        readBlock0Size:   Block size in bytes(default = 4096)
        ulink:            ULINK Control: ON, OFF, or Power Cycle (OFF+ON)
        createLog:        Default True, if False, don't create Log output file
        doubleTOCRead:    Do a double read and validate on the VU TOC (default = False)
        debug:            Print debug info
        prepend:
    """
    # Set the debug level
    OutputLog.setDebugLevel(debug)

    # Get the log pull object
    if (sata):
        block0Size = TelemetryLogBlockSize
        secondaryBlockSize = TelemetryLogBlockSize
    else:
        # Nvme
        block0Size = TelemetryLogBlockSize
        secondaryBlockSize = 4096

    # Check the log type
    if (hilog):
        filePrepend = "v2hi_"
        readAsOne = False
    else:
        filePrepend = "v2ci_"
        readAsOne = True

    if prepend:
        outFile = filePrepend + outFile

    # Check for an output directory
    if (outDir is not None):
        outFile = os.path.join(outDir, outFile)

    # Check for v1 4K pull
    if (version1):
        block0Size = version1BlockSize
    else:
        block0Size = TelemetryLogBlockSize

    # Check for block 0 override
    if (readBlock0Size is not None):
        block0Size = readBlock0Size

    # Check for default block size override
    if (readBlockSize is not None):
        secondaryBlockSize = readBlockSize

    # check for ulink power cycle
    if (ulink):
        if (False == SetUlink(ulink)):
            OutputLog.Error("INVALID --ulink argument")
            sys.exit(1)

    # if no options specified use drive
    driveNumber = driveList.checkDriveIndex(drvnum)
    if (driveNumber is None):
        sys.exit(1)

    ### Select drive to analyze
    drive = testDrive(driveNumber)
    if (drive is None):
        sys.exit(1)
    logDrive = logDevice(drive.getTestDrive(), hilog)

    ### Determine what to do
    drive.globalDriveSpecificParams()
    OutputLog.Information("Get Id information")
    OutputLog.Information(drive.toStr())

    ### Verify drive is not asserted
    if (drive.isDriveAsserted()):
        AssertedDrive = True

    else:
        AssertedDrive = False
    OutputLog.Information("Assert Status: %s" % (AssertedDrive))

    ### Perform Test ###
    OutputLog.Information("Get log data... ")
    telemetryData = openWriteFile(outFile)
    if (telemetryData is not None):
        if (debug == 1):
            print("logDrive:%s,telemetryData=%s,secondaryBlockSize=%s,block0Size=%s,createLog=%s,doubleTOCRead=%s\n" % (logDrive, telemetryData, secondaryBlockSize, block0Size, createLog, doubleTOCRead))
        status, ciGeneration = readTelemetryLog(logDrive, telemetryData, secondaryBlockSize, block0Size, createLog, doubleTOCRead)
    else:
        status = False

    if (True == status):
        OutputLog.Information("passed.")
    else:
        OutputLog.Information("failed.")
    telemetryData.close()
    return status, outFile


def main():
    #### Command-line arguments ####
    parser = OptionParser(usage="usage: %prog [options] outputFile", version="%prog Version: " + str(TOOL_VERSION))
    parser.add_option('--debug', type="int", dest='debug', action="store", default=0, help='Enable debug level')
    parser.add_option('-d', type='int', dest='drvnum', metavar='<DRVNUM>', default=None, help='Drive number to analyze')
    parser.add_option('-q', action='callback', callback=ScanDrives, help='Query system for the drive list')
    parser.add_option('-o', action='store', dest="outDir", default=None, help='Output directory')
    parser.add_option('--ulink', metavar='on|off|pc', default='', help='ULINK Control: ON, OFF, or Power Cycle (OFF+ON)')
    parser.add_option('--nocreate', action='store_false', dest="createLog", default=True, help='Issue command with create bit = 0')
    parser.add_option('--hi', action='store_true', dest="hilog", default=True, help='Pull Host Initiated log (this is the default case)')
    parser.add_option('--ci', action='store_false', dest="hilog", help='Pull Controller Initiated log')
    parser.add_option('--v1', action='store_true', dest="version1", default=False, help='Version 1 pull (default = false)')
    parser.add_option('-b', '--blockSize', type='int', action='store', dest="readBlockSize", default=None, help='Read Block size in bytes(default = 4096)')
    parser.add_option('--block0Size', type='int', action='store', dest="readBlock0Size", default=None, help='Read Block 0 size in bytes(default = None)')
    parser.add_option('--tocreread', action='store_true', dest="doubleTOCRead", default=False, help='Do a double read and validate on the VU TOC (default = False)')
    parser.add_option('--sata', action='store_true', dest="sata", default=False, help='Perform SATA log page pull')
    parser.add_option('--nvme', action='store_false', dest="sata", help='Perform NVMe log page pull')
    (options, args) = parser.parse_args()

    # Set the output file
    if (len(args) >= 1):
        outFile = args[0]
    else:
        outFile = "telemetry.bin"

    getTelemetryAPI(outFile, outDir=options.outDir, drvnum=options.drvnum, hilog=options.hilog, sata=options.sata, version1=options.version1, readBlockSize=options.readBlockSize, readBlock0Size=options.readBlock0Size, ulink=options.ulink, createLog=options.createLog, doubleTOCRead=options.doubleTOCRead, debug=options.debug)


######## Test it #######
if __name__ == '__main__':
    from datetime import datetime

    p = datetime.now()
    main()
    q = datetime.now()
    OutputLog.Information("\nExecution time: " + str(q - p))
