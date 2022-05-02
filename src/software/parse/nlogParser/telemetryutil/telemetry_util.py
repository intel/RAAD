#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors:Joseph Tarango, Randal Eike, Daniel Garces
# *****************************************************************************/
"""
Brief:
    telemetryutil.telemetry_util.py - Utility routines for Telemetry data processing

Description:
    -

Classes:
    Enter GetHeaders("telemetryutil.telemetry_util.py") to display Class listings.
"""

import os, sys
import mmap
from array import array

#### import Utility functions
from src.software.parse.nlogParser.test_util.output_log import OutputLog

TelemetryLogBlockSize = 512     # defined by NVMe version 1.3 specification
MAX_BLOCK_SIZE = 4096
BYTES_PER_DWORD = 4

if sys.version_info[0] == 3:
    from io import IOBase
    file = IOBase

def GetTruncatedDataBuffer(imageObject, blockSize, maxBlockSize = 131072):
    """
    From the input image object, pull and return a byte buffer truncated to maxBlockSize bytes

    Input: imageObject - Input binary data object
           blockSize - Size in bytes of the input data object
           maxBlockSize - Maximum data buffer size to return
    """
    if (blockSize > maxBlockSize):
        OutputLog.DebugPrint(2, format("Buffer truncated to %d bytes" % (maxBlockSize)))
        returnBlockSize = int(maxBlockSize)
    else:
        returnBlockSize = int(blockSize)

    if isinstance(imageObject, file):
        data = array('B')
        data.fromfile(imageObject,returnBlockSize)
        return returnBlockSize, data
    else:
        return returnBlockSize, imageObject

def cleanDir(dirName):
    folder = os.path.abspath(dirName)
    if(os.path.exists(folder)):
        for fileName in os.listdir(folder):
            deleteFile = os.path.join(folder, fileName)
            try:
                if (os.path.isfile(deleteFile)): os.remove(deleteFile)
            except:
                OutputLog.DebugPrint(2, format("Unable to clear file \"%s\"" % (deleteFile)))
    else:
        os.mkdir(folder)

def openWriteFile(fileName, text = False):
    ### open output file ###
    if (text == True): mode = "wt"
    else: mode = "wb"
    try:
        outputFile = open(fileName, mode)
    except IOError:
        OutputLog.Error(format("Unable to open file \"%s\" for output\n" % (fileName)))
        outputFile = None
    except:
        OutputLog.Error(format("File error %s Unable to open file \"%s\" for output\n" % (sys.exc_info()[0], fileName)))
        outputFile = None
    return outputFile

def openReadFile(fileName):
    ### open input file ###
    try:
        inputFile = open(fileName,"rb")
    except IOError:
        OutputLog.Error(format("Unable to open file \"%s\" for reading\n" % (fileName)))
        inputFile = None
    return inputFile


def compareTelemetryBinFiles(baseFileName, compareFileName):
    """
    Compare the input binary files
    """
    returnStatus = True

    # Open the two files for reading
    baseFile = openReadFile(baseFileName)
    compareFile = openReadFile(compareFileName)

    mmBase = mmap.mmap(baseFile.fileno(), 0, access=mmap.ACCESS_READ)
    mmCmp = mmap.mmap(compareFile.fileno(), 0, access=mmap.ACCESS_READ)

    # Make sure the size matches
    if(mmBase.size() != mmCmp.size()):
        OutputLog.Error(format("%s file size %d does not match %s file size %d" % (baseFileName, mmBase.size(), compareFileName, mmCmp.size())))
        returnStatus = False
    else:
        # Compare the file
        index = 0;
        mmBase.seek(0)
        mmCmp.seek(0)
        baseSize = mmBase.size()
        while (index < baseSize):
            if (mmBase[index] != mmCmp[index]):
                # Compare Error
                returnStatus = False

                # Find the end of the miscompare
                endLocation = index + 1
                while ((endLocation < baseSize) and (mmBase[endLocation] != mmCmp[endLocation])):
                    endLocation += 1

                # Output error message
                OutputLog.Error(format("Miscompare from offset %d to %d, size %d" % (index, endLocation, endLocation - index)))
                index = endLocation + 1
            else:
                index += 1

    # Cleanup
    mmBase.close()
    mmCmp.close()
    baseFile.close()
    baseFile.close()

    return returnStatus

def GetDefaultFileName(hilog, asserted):
    if(hilog): filePrepend = "v2hi_"
    else: filePrepend = "v2ci_"
    if (asserted): filePrepend += "asserted_"
    defaultName = filePrepend+"telemetry.bin"
    return defaultName

def BuildFileName(filename, defaultPath = None):
    if (defaultPath is None): filePath = os.getcwd()
    else: filePath = os.path.abspath(defaultPath)

    osFileName = os.path.join(filePath, filename)
    return osFileName

def ConvertBinNameToTextName(binFileName):
    path, filename = os.path.split(binFileName)
    baseName, ext = os.path.splitext(filename)
    outputTextName = os.path.join(path, baseName+".txt")
    return outputTextName




