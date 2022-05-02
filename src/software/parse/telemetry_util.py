#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Randal Eike, Joseph Tarango
# *****************************************************************************/
"""
Brief:
    telemetry_util.py - Utility routines for Telemetry data processing
Classes:
    Enter GetHeaders("telemetry_util.py") to display Class listings.
"""
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import os
from array import array

#### import Utility functions
from src.software.parse.output_log import OutputLog

TelemetryLogBlockSize = 512  # defined by NVMe version 1.3 specification
MAX_BLOCK_SIZE = 4096
BYTES_PER_DWORD = 4


def GetTruncatedDataBuffer(imageObject, blockSize, maxBlockSize=131072):
    """
    From the input image object, pull and return a byte buffer truncated to maxBlockSize bytes

    Input: imageObject - Input binary data object
           blockSize - Size in bytes of the input data object
           maxBlockSize - Maximum data buffer size to return
    """
    if (blockSize > maxBlockSize):
        OutputLog.DebugPrint(2, format("Buffer truncated to %d bytes" % (maxBlockSize)))
        returnBlockSize = maxBlockSize
    else:
        returnBlockSize = blockSize

    if hasattr(imageObject, 'read'):
        data = array('B', imageObject.read(returnBlockSize))
        if len(data) < returnBlockSize:
            OutputLog.DebugPrint(2, format("read EOF - returning zero data"))
            return returnBlockSize, array('B', [0] * returnBlockSize)
        else:
            return returnBlockSize, data
    else:
        return returnBlockSize, imageObject


def cleanDir(dirName):
    if (os.path.exists(dirName) is False):
        folder = os.path.join(os.getcwd(), dirName)
    else:
        folder = dirName
    if (os.path.exists(folder)):
        for fileName in os.listdir(folder):
            try:
                deleteFile = os.path.join(folder, fileName)
                if (os.path.isfile(deleteFile)):
                    os.remove(deleteFile)
            except:
                OutputLog.DebugPrint(2, format("Unable to clear file \"%s\"" % (deleteFile)))
    else:
        os.mkdir(folder)
    return


def openWriteFile(fileName, text=False):
    ### open output file ###
    if (text is True):
        mode = "wt"
    else:
        mode = "wb"
    try:
        outputFile = open(fileName, mode)
    except IOError:
        OutputLog.Error(format("Unable to open file \"%s\" for output\n" % (fileName)))
        outputFile = None
    return outputFile


def openReadFile(fileName):
    ### open input file ###
    try:
        inputFile = open(fileName, "rb")
    except IOError:
        OutputLog.Error(format("Unable to open file \"%s\" for reading\n" % (fileName)))
        inputFile = None
    return inputFile
