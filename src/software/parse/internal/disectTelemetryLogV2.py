#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Lukasz Tur
# *****************************************************************************/
"""
Brief:
    disectTelemetryLogV2.py - Generic definitions for parsing telemetry data object blobs

Description:
    This file contains the telemetry data objects decomposition.

Classes:
    Enter ("") to display Class listings.

Function(s):
    None

Related:
    -
"""

import __init__
import os, sys

################################################################################################################
################################################################################################################

try:
    from util.cmd_line_parameter import Param # @todo TWIDL dependancy
except:
    pass

p = Param("[file=None]")

alignment = 512

logFile = p['file']

if not os.path.exists(logFile):
    print('\nTELEMETRY LOG DOES NOT EXIST:' + logFile + '\n')
    exit()

inFile = open(logFile, 'rb') #Open the telemetry log

path, fileWithExt = os.path.split(logFile)
fileName, fileExt = os.path.splitext(fileWithExt)

outPath = os.path.join(path, fileName)

#if os.path.exists(outPath):
#    os.rmdir(outPath)

#os.mkdir(outPath)

#************** NVMe Header Processing **************
nvmeHeader = bytearray(inFile.read(512)) #Read NVMe Header
print('\n**************************')
print('NVME HEADER')
print('Log Identifier: {}'.format(hex(nvmeHeader[0])))
print('IEEE OUI Identifier: {}'.format(hex(nvmeHeader[7] << 16 | nvmeHeader[6] << 8 | nvmeHeader[5])))
print('DA1LB: {}'.format(hex(nvmeHeader[9] << 8 | nvmeHeader[8])))
print('DA2LB: {}'.format(hex(nvmeHeader[11] << 8 | nvmeHeader[10])))
print('DA3LB: {}'.format(hex(nvmeHeader[13] << 8 | nvmeHeader[12])))
print('Controller Initiated Data Available: {}'.format(hex(nvmeHeader[382])))
print('Controller Initiated Data Generation Number: {}'.format(hex(nvmeHeader[383])))
asciiIdentifier = []
for i in range(384,512):
    asciiIdentifier.append(nvmeHeader[i])
asciiIdentifierString = ''.join(chr(i) for i in asciiIdentifier)
print('Reason Identifier: {}'.format(asciiIdentifierString))

#************** DA1 VU Header Processing **************
inFile.seek(alignment) #Seek to DA1 header

for dataArea in range(0, 3):
    startPosition = inFile.tell()
    daHdr = bytearray(inFile.read(8)) #Read TLog header into memory
    print('\n**************************')
    print('Data Area ' + str(dataArea) + ' HEADER')
    print('Version Major: {}'.format(daHdr[0]))
    print('Version Minor: {}'.format(daHdr[1]))
    tocDimension = daHdr[3] << 8 | daHdr[2]
    print('TOC dimension: {}'.format(tocDimension))
    dataAreaSize = daHdr[7] << 24 | daHdr[6] << 16 | daHdr[5] << 8 | daHdr[4]
    print('Size: {}'.format(dataAreaSize))

    for object in range(0, tocDimension) : #Find each object entry in the TOC
        inFile.seek(startPosition + 8 + (object * 8))
        tocObj =  bytearray(inFile.read(8))
        objOffset = tocObj[3] << 24 | tocObj[2] << 16 | tocObj[1] << 8 | tocObj[0]
        objSize = tocObj[7] << 24 | tocObj[6] << 16 | tocObj[5] << 8 | tocObj[4]
        print('Object_' + str(object) + ': offset {}'.format(hex(objOffset)) + ' size:{}'.format(objSize))

        inFile.seek(startPosition + objOffset)
        objHdr = bytearray(inFile.read(12))
        objVerMajor = objHdr[1] << 8 | objHdr[0]
        objVerMinor = objHdr[3] << 8 | objHdr[2]
        objUid = objHdr[7] << 24 | objHdr[6] << 16 | objHdr[5] << 8 | objHdr[4]
        objMedia = objHdr[8]

        print('UID:{}'.format(objUid))

        objData = bytearray(inFile.read(objSize - 12)) # Read log into memory

        outFileName = 'Object_' + str(objUid) + '_ver' + str(objVerMajor) + '_' + str(objVerMinor) + '_m' + str(objMedia) + '.bin' #Construct log file name
        print('Writing to {}'.format(os.path.join(outPath, outFileName)))

#        outFile = open(os.path.join(outPath, outFileName), 'wb')
#        outFile.write(objData)
#        outFile.close()

    inFile.seek(startPosition + dataAreaSize)
