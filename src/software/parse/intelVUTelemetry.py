#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Randal Eike, Joseph Tarango
# *****************************************************************************/
"""
Brief:
    intelVUTelemetry.py - Holds special parsers for NVMe Telemetry Log Page Data

Description:
    -

Classes:
    Enter GetHeaders("parsers\\nvme\\intelVUTelemetry.py") to display Class listings.
"""
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import sys

from ctypes import *
from array import array
from src.software.parse.telemetry_util import *
from src.software.parse.intelObjectIdList import ParserObjectMap
from src.software.parse.output_log import OutputLog


ID_SERIAL_SIZE = 20  # Size of the serial number field
FW_REV_WORDS = 12  # Size of the FW revision field

TelemetryV1LastId = 5
TelemetryV2LastId = 0xFFFFFFFD

################################################################################################################
################################################################################################################


class intelTelemetryTOC_VersionStruct(Structure):
    """
    Brief:
        intelTelemetryTOC_struct() - Definition of the NVMe Get Telemetry Log Page header structure for Intel drives.

    Description:

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Randal Eike
    """
    _pack_ = 1
    _fields_ = [
                ("majorVersion",              c_uint8),         # byte 00: Major version
                ("minorVersion",              c_uint8)          # byte 01: Minor version
               ]

    def tostr(self):
        retString = format("V%u_%u" % (self.majorVersion, self.minorVersion))
        return retString

    def getStr(self):
        return self.tostr()

    def getVersion(self):
        return self.majorVersion + (self.minorVersion / 100)

    def getMajorVersion(self):
        return self.majorVersion

    def getMinorVersion(self):
        return self.minorVersion


class telemetryTObjectCatalogEntry_struct(Structure):
    """
    Brief:
        telemetryTObjectCatalogEntry_struct() - Definition of the Intel VU telemetry table of contents catalog entry version 1.

    Description:
        Telemetry object Catalog entry structure definition and method implementation.

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Randal Eike
    """
    _pack_ = 1
    _fields_ = [
                ("startingBlock",  c_uint16),         # byte 00-01: Starting block number of the data object
                ("totalBlocks",    c_uint16)          # byte 02-03: Number of blocks in the data object
                # End More Intel
               ]

    __minimumSize = 8
    __minimumstart = 16

    def tostr(self):
        if(self.startingBlock != 0):
            retString = format("Entry Start: %06d Size: %06d\n" % (self.startingBlock, self.totalBlocks))
        else:
            retString = ""
        return retString

    def validate(self):
        if ((self.startingBlock != 0) or (self.totalBlocks != 0)):
            if (self.startingBlock < telemetryTObjectCatalogEntry_struct.__minimumstart):
                OutputLog.Warning(format("Invalid TOC entry start block %d < minimum start block %d" % (self.startingBlock, telemetryTObjectCatalogEntry_struct.__minimumstart)))
                return True # Hack due to changes breaking the functionality
            if (self.totalBlocks < telemetryTObjectCatalogEntry_struct.__minimumSize):
                OutputLog.Warning(format("Invalid TOC entry block size %d < minimum block size %d" % (self.totalBlocks, telemetryTObjectCatalogEntry_struct.__minimumSize)))
                return True # Hack due to changes breaking the functionality
        return True

    def getStartingBlock(self):
        return (self.startingBlock)

    def getStartingOffset(self):
        return (self.startingBlock * TelemetryLogBlockSize)

    def getBlockSize(self):
        return (self.totalBlocks)

    def getByteSize(self):
        return (self.totalBlocks * TelemetryLogBlockSize)

    def getDictionaryEntry(self):
        return dict(startOffset=(self.startingBlock * TelemetryLogBlockSize),size=(self.totalBlocks * TelemetryLogBlockSize),startBlock=(self.startingBlock),blockSize=(self.totalBlocks))

class telemetryTOCObjectEntryV2_struct(Structure):
    """
    Brief:
        telemetryTOCObjectEntryV2_struct() - Definition of the Intel VU telemetry table of contents entry version 2.

    Description:
        Telemetry object Catalog entry structure definition and method implementation.

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Randal Eike
    """
    _pack_ = 1
    _fields_ = [
                ("offsetBytes",       c_uint32),         # byte 00-03: Starting bytes offset of the data object
                ("contentSizeBytes",  c_uint32)          # byte 04-07: Number of bytes in the data object
                # End More Intel
               ]

    __minimumSize = 12
    __minimumOffset = 24

    def tostr(self):
        retString = format("Entry Offset: %d Size: %d\n" % (self.offsetBytes, self.contentSizeBytes))
        return retString

    def validate(self):
        if (self.offsetBytes < telemetryTOCObjectEntryV2_struct.__minimumOffset):
            OutputLog.Warning(format("Invalid TOC entry offset %d < minimum offset %d" % (self.offsetBytes, telemetryTOCObjectEntryV2_struct.__minimumOffset)))
            return True  # Hack due to changes breaking the functionality
        if (self.contentSizeBytes <= telemetryTOCObjectEntryV2_struct.__minimumSize):
            OutputLog.Warning(format("Invalid TOC entry size %d <=  minimum size %d" % (self.contentSizeBytes, telemetryTOCObjectEntryV2_struct.__minimumSize)))
            return True  # Hack due to changes breaking the functionality
        return True

    def getStartingBlock(self):
        return (self.offsetBytes / TelemetryLogBlockSize)

    def getStartingOffset(self):
        return (self.offsetBytes)

    def getBlockSize(self):
        return (self.contentSizeBytes / TelemetryLogBlockSize)

    def getByteSize(self):
        return (self.contentSizeBytes)

    def getDictionaryEntry(self):
        return dict(startOffset=(self.offsetBytes),size=(self.contentSizeBytes),startBlock=(self.contentSizeBytes / TelemetryLogBlockSize),blockSize=0)



class intelTelemetryTOC_V1_struct(Structure):
    """
    Brief:
        intelTelemetryTOC_V1_struct() - Definition of the Intel Telemetry table of contents version 1.

    Description:
        Intel VU telemetry data table of contents implementation.

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Randal Eike
    """
    VERSION1_TOC_ENTRY_COUNT = 127  # Defined in firmware

    _pack_ = 1
    _fields_ = [
                ("majorVersion",              c_uint8),         # byte 00: Major version (0x01)
                ("minorVersion",              c_uint8),         # byte 01: Minor version
                ("reserved",                  c_uint8 * 2),     # byte 02-03: reserved
                ("objects",                   telemetryTObjectCatalogEntry_struct * VERSION1_TOC_ENTRY_COUNT) # byte 04-511: Table of contents entries
                # End More Intel
               ]


    def _buildListUtility(self, lastBlock):
        """
        Build a list of object locations based on the table of contents

        Input: tocObjects - Table of contents array object
               maxEntryCount - Maximum number of entries in the array
               lastBlock - Last block of the bin file. Used to determine if there is a APL log at the end

        Output: tocList - list of dictionary entries describing object locations and sizes
                aplStart - dictionary describing APL log location and size or None if nothing appended to the log
        """
        # initialize data
        tocList = []
        listIndex = 0
        aplStartBlock = self.objects[0].getStartingBlock()

        # Walk through the table of contents
        while ((self.objects[listIndex].getStartingBlock() != 0) and (listIndex < intelTelemetryTOC_V1_struct.VERSION1_TOC_ENTRY_COUNT)):
            # Add to list
            tocList.append(self.objects[listIndex].getDictionaryEntry())

            # Move to next
            aplStartBlock += self.objects[listIndex].getBlockSize()
            listIndex=listIndex+1

        # Add APL data if present
        if (aplStartBlock < lastBlock):
            offset = aplStartBlock * TelemetryLogBlockSize
            aplSize = (lastBlock - aplStartBlock) * TelemetryLogBlockSize
            aplStart = dict(startOffset=offset, size=aplSize, startBlock=aplStartBlock,blockSize=(lastBlock - aplStartBlock))
        else:
            aplStart = None

        return tocList, aplStart


    def buildList(self, dataAreaSize):
        return self._buildListUtility(dataAreaSize/TelemetryLogBlockSize)

    def getEntryCount(self):
        tocIndex = 0
        while ((self.objects[tocIndex].getStartingBlock() != 0) and (tocIndex < intelTelemetryTOC_V1_struct.VERSION1_TOC_ENTRY_COUNT)):
            tocIndex += 1
        return tocIndex

    def getDataSize(self):
        return 0

    def getMajorVersion(self):
        return self.majorVersion

    def getMinorVersion(self):
        return self.minorVersion

    def getEntry(self, index):
        return self.objects[index]

    def getTOCSize(self):
        return 512

    def tostr(self):
        retString = format("Version: %d.%02d\n" % (self.majorVersion, self.minorVersion))
        retString += format("Directory:\n")
        for objectNumber in range(0,self.VERSION1_TOC_ENTRY_COUNT,1):
            entryString = self.objects[objectNumber].tostr()
            if(entryString != ""):
                retString += entryString
        return retString

    def validate(self):
        if(self.majorVersion != 1):
            OutputLog.Error(format("Expected TOC major version 1, read %d" % (self.majorVersion)))
            return True # Hack due to changes breaking the functionality
        for objectNumber in range(0,self.VERSION1_TOC_ENTRY_COUNT,1):
            if (False == self.objects[objectNumber].validate()):
                OutputLog.Warning(format("TOC entry %d invalid\n" % (objectNumber)))
                return True  # Hack due to changes breaking the functionality
        return True


class intelTelemetryTOC_V2_struct(Structure):
    """
    Brief:
        intelTelemetryTOC_V2_struct() - Definition of the NVMe Get Host/Controller Initiated Log Page Data area header structure for Intel drives.

    Description:
        Data area table of contents structure definition

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Randal Eike
    """
    VERSION2_TOC_ENTRY_COUNT = 200  # Arbitrary value so that Python works

    _pack_ = 1
    _fields_ = [
                ("majorVersion",              c_uint8),         # byte 00: Major version (0x02)
                ("minorVersion",              c_uint8),         # byte 01: Minor version
                ("entryCount",                c_uint16),        # byte 02 - 03: TOC entry count
                ("areaSize",                  c_uint32),        # byte 04 - 07: Total size of the data area in bytes including this table
                ("reserved",                  c_uint64),        # byte 08 - 15: Reserved for future use
                ("objects",                   telemetryTOCObjectEntryV2_struct * VERSION2_TOC_ENTRY_COUNT) # byte 16-1024: Table of contents entries
                # End More Intel
               ]


    def _buildListUtility(self, endOffset):
        """
        Build a list of object locations based on the table of contents

        Input: tocObjects - Table of contents array object
               maxEntryCount - Maximum number of entries in the array
               lastBlock - Last block of the bin file. Used to determine if there is a APL log at the end

        Output: tocList - list of dictionary entries describing object locations and sizes
                aplStart - dictionary describing APL log location and size or None if nothing appended to the log
        """
        # initialize data
        tocList = []
        listIndex = 0
        aplStartOffset = self.objects[0].getStartingOffset()

        # Walk through the table of contents
        while (listIndex < self.entryCount):
            # Add to list
            tocList.append(self.objects[listIndex].getDictionaryEntry())

            # Move to next
            aplStartOffset += self.objects[listIndex].getByteSize()
            listIndex=listIndex+1

        # Add APL data if present
        if (aplStartOffset < endOffset):
            ## @todo debug
            #aplSize = endOffset - aplStartOffset
            #aplStart = dict(startOffset=aplStartOffset, size=aplSize, startBlock=(aplStartOffset / TelemetryLogBlockSize), blockSize=(aplSize / TelemetryLogBlockSize))
            aplStart = None
        else:
            aplStart = None

        return tocList, aplStart


    def buildList(self, dataAreaSize):
        return self._buildListUtility(dataAreaSize)

    def getEntryCount(self):
        return self.entryCount

    def getDataSize(self):
        return self.areaSize

    def getMajorVersion(self):
        return self.majorVersion

    def getMinorVersion(self):
        return self.minorVersion

    def getEntry(self, index):
        return self.objects[index]

    def getTOCSize(self):
        return ((self.entryCount * 8) + 16)

    def tostr(self):
        retString = format("Version: %d.%02d\n" % (self.majorVersion, self.minorVersion))
        retString += format("Entry Count: %d, Data Area Size: %u\n" % (self.entryCount, self.areaSize))
        retString += format("Directory:\n")
        for objectNumber in range(0, self.entryCount,1):
            entryString = self.objects[objectNumber].tostr()
            if(entryString != ""):
                retString += entryString
        return retString

    def validate(self):
        retStatus = True
        if(self.majorVersion < 2):
            OutputLog.Error(format("Expected TOC major version 2, read %d" % (self.majorVersion)))
            retStatus = False
        else:
            for objectNumber in range(0,self.entryCount,1):
                if (False == self.objects[objectNumber].validate()):
                    OutputLog.Warning(format("TOC entry %d invalid\n" % (objectNumber)))
                    retStatus = False
        return retStatus

class intelTelemetryTOC_union(Union):
    """
    Brief:
        intelTelemetryTOC_union() - Definition of the NVMe Get Host Initiated Log Page header structure for Intel drives.

    Description:
        This class extends TWIDL_Union.

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Randal Eike
    """
    _pack_ = 1
    _fields_ = [
                ("Version",    intelTelemetryTOC_VersionStruct),    # Version data
                ("v1Struct",   intelTelemetryTOC_V1_struct),        # V1 Header data
                ("v2Struct",   intelTelemetryTOC_V2_struct),        # V2 Header data
                ("Bytes",      c_ubyte * MAX_BLOCK_SIZE),           # fill
                # End More Intel
               ]

    def __init__(self, imageBuffer, blockSize):
        dataSize, dataBuffer = GetTruncatedDataBuffer(imageBuffer, blockSize, MAX_BLOCK_SIZE)
        for i in range (0, dataSize):
            self.Bytes[i] = dataBuffer[i]

    def getStruct(self):
        if (self.Version.getMajorVersion() == 1):
            # Version 1 structure
            return self.v1Struct
        elif (self.Version.getMajorVersion() == 2):
            # Version 2 structure
            return self.v2Struct
        else:
            # Best guess
            OutputLog.Warning(format("Unknown table of contents major version %d\n" % self.Version.getMajorVersion()))
            return self.v2Struct


class intelLogObjectInformation_struct(Structure):
    """
    Brief:
        intelLogObjectInformation_struct() - Object entry information version 1.


    Description:


    Class(es):
        None

    Method(s):

        None

    Related: -


    Author(s):
        Randal Eike
    """
    _pack_ = 1
    _fields_ = [
                ("objectEnum",             c_uint32),         # byte 00-03: Object identification enumeration value
                ("tstCmdLowId",            c_uint32),         # byte 04-07: Test command ID low
                ("objectTextIdentifier",   c_char * (32-8))   # byte 08-31: Object text identification number
                # End More Intel
               ]

    def getHumanName(self):
        retString = format("%s" % (self.objectTextIdentifier[:(32-8)]))
        return retString

    def tostr(self):
        retString = format("Object Enum ID: %d, TestCmdID: %d, Name: %s" % (self.objectEnum, self.tstCmdLowId, self.objectTextIdentifier[:(32-8)]))
        return retString

class intelTelemetryObjectHeader_V1_struct(Structure):
    """
    Brief:
        intelTelemetryObjectHeader_V1_struct() - Version 1 Intel Telemetry data object header

    Description:

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Randal Eike
    """
    _pack_ = 1
    _fields_ = [
                ("objectIdentifier",       c_uint8),         # byte 00: Object identification number
                ("cpuNumber",              c_uint8),         # byte 01: CORE number
                ("flags",                  c_uint8),         # byte 02: flags
                ("reserved1",              c_uint8),         # byte 03:
                ("objectSizeBlks",         c_uint16),        # byte 04-05: Size of the object in TelemetryLogBlockSizebyte blocks
                ("objectTextIdentifier",   intelLogObjectInformation_struct)    # byte 06-37: Object text identification number
                # End More Intel
               ]

    objectHeaderSize = 4096

    def tostr(self):
        retString = format("Object ID: %d, %s\n" % (self.objectIdentifier, self.objectTextIdentifier.tostr()))
        retString += format("CPU #: %d\n" % (self.cpuNumber))
        retString += format("Flags: %d\n" % (self.flags))
        retString += format("ObjectSize: %d blocks" % (self.objectSizeBlks))
        return retString

    def getMajorVersion(self):
        return 0

    def getMinorVersion(self):
        return 0

    def getObjectIdentifier(self):
        return self.objectIdentifier

    def getCpuNumber(self):
        return self.cpuNumber - 1

    def getObjectByteSize(self, tocSize):
        return self.objectSizeBlks * TelemetryLogBlockSize

    def getDataOffsetAndSize(self, offset, size):
        dataOffset = offset + 4096
        dataSize = size - 4096
        return dataOffset, dataSize

    def getHumanName(self):
        return self.objectTextIdentifier.getHumanName()

    def validate(self):
        if(self.objectIdentifier >= TelemetryV1LastId):
            OutputLog.Error(format ("Object ID %d Out of range for version 1 telemetry" % (self.objectIdentifier)))
            return False
        if(self.objectIdentifier != self.objectTextIdentifier.objectEnum):
            OutputLog.Error(format ("Object ID %d does not match text enum %d" % (self.objectIdentifier, self.objectTextIdentifier.objectEnum)))
            return False

        return True


class intelLogObjectInformationV_1_4_struct(Structure):
    """
    Brief:
        intelLogObjectInformationV_1_4_struct() -  Object entry information version 1.4


    Description:


    Class(es):
        None

    Method(s):

        None

    Related: -


    Author(s):
        Randal Eike
    """
    _pack_ = 1
    _fields_ = [
                ("objectTextIdentifier",   c_char * 32)   # byte 00-31: Object text identification number
                # End More Intel
               ]

    def getHumanName(self):
        retString = format("%s" % (self.objectTextIdentifier[:32]))
        return retString

    def tostr(self):
        retString = format("Object Name: %s" % (self.objectTextIdentifier[:32]))
        return retString

class intelTelemetryObjectHeader_V1_4_struct(Structure):
    """
    Brief:
        intelTelemetryObjectHeader_V1_4_struct() - Version 1.4 Intel Telemetry data object header

    Description:

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Randal Eike
    """
    _pack_ = 1
    _fields_ = [
                ("objectIdentifier",       c_uint8),         # byte 00: Object identification number
                ("cpuNumber",              c_uint8),         # byte 01: CORE number
                ("flags",                  c_uint8),         # byte 02: flags
                ("reserved1",              c_uint8),         # byte 03:
                ("objectSizeBlks",         c_uint16),        # byte 04-05: Size of the object in TelemetryLogBlockSizebyte blocks
                ("objectTextIdentifier",   intelLogObjectInformationV_1_4_struct)    # byte 06-37: Object text identification number
                # End More Intel
               ]

    objectHeaderSize = 4096

    def tostr(self):
        retString = format("Object ID: %d, %s\n" % (self.objectIdentifier, self.objectTextIdentifier.tostr()))
        retString += format("CPU #: %d\n" % (self.cpuNumber))
        retString += format("Flags: %d\n" % (self.flags))
        retString += format("ObjectSize: %d blocks" % (self.objectSizeBlks))
        return retString

    def getMajorVersion(self):
        return 0

    def getMinorVersion(self):
        return 0

    def getObjectIdentifier(self):
        return self.objectIdentifier

    def getCpuNumber(self):
        return self.cpuNumber - 1

    def getObjectByteSize(self, tocSize):
        return self.objectSizeBlks * TelemetryLogBlockSize

    def getDataOffsetAndSize(self, offset, size):
        dataOffset = offset + 4096
        dataSize = size - 4096
        return dataOffset, dataSize

    def getHumanName(self):
        return self.objectTextIdentifier.getHumanName()

    def validate(self):
        if(self.objectIdentifier >= TelemetryV1LastId):
            OutputLog.Error(format ("Object ID %d Out of range for version 1 telemetry" % (self.objectIdentifier)))
            return False

        return True

class intelTelemetryObjectHeader_V2_struct(Structure):
    """
    Brief:
        intelTelemetryObjectHeader_V2_struct() - Version 2 Intel Telemetry data object header

    Description:

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Randal Eike
    """
    _pack_ = 1
    _fields_ = [
                ("majorVersion",           c_uint16),        # byte 01-00: Object major revision number
                ("minorVersion",           c_uint16),        # byte 03-02: Object minor revision number
                ("objectEUID",             c_uint32),        # byte 07-04: Object Enumerated Unique Identifier (EUID)
                ("mediaId",                c_uint8),         # byte 08:    Media identification number
                ("reserved",               c_uint8 * 3),     # byte 11-09: Reserved for future expansion
               ]

    objectHeaderSize = 12

    def tostr(self):
        retString = format("Object EUID: %d\n" % (self.objectEUID))
        retString += format("Object Version: %d.%02d\n" % (self.majorVersion, self.minorVersion))
        retString += format("Media bank #: %d" % (self.mediaId))
        return retString

    def getMajorVersion(self):
        return self.majorVersion

    def getMinorVersion(self):
        return self.minorVersion

    def getObjectIdentifier(self):
        return self.objectEUID

    def getCpuNumber(self):
        return self.mediaId

    def getObjectByteSize(self, tocSize):
        return tocSize

    def getDataOffsetAndSize(self, offset, size):
        dataOffset = offset + intelTelemetryObjectHeader_V2_struct.objectHeaderSize
        dataSize = size - intelTelemetryObjectHeader_V2_struct.objectHeaderSize
        return dataOffset, dataSize

    def getHumanName(self):
        mapdata = ParserObjectMap()
        objectId, objectName, majorRev, minorRev, size = self.findEUID(self.objectEUID, self.majorVersion, self.minorVersion)
        retstr = objectName+"V"+str(self.majorVersion)+"_"+str(self.minorVersion)
        return retstr

    def validate(self):
        if(self.majorVersion == 0):
            OutputLog.Error(format ("Object ID %d major version = 0" % (self.objectEUID)))
            return True  # Hack due to changes breaking the functionality
        return True


class intelTelemetryObjectHeader_union(Union):
    """
    Brief:
        intelTelemetryObjectHeader_union() - Definition of the NVMe Get Host Initiated Log Page header structure for Intel drives.

    Description:
        This class extends TWIDL_Union.

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Randal Eike
    """
    _pack_ = 1
    _fields_ = [
                ("version1",   intelTelemetryObjectHeader_V1_struct),     # Version 1 object header data
                ("version1_4", intelTelemetryObjectHeader_V1_4_struct),   # Version 1.4 object header data
                ("version2",   intelTelemetryObjectHeader_V2_struct),     # Version 2 object header data
                ("Bytes",      c_ubyte * MAX_BLOCK_SIZE)                  # fill
                # End More Intel
               ]

    def __init__(self, imageBuffer, blockSize):
        dataSize, dataBuffer = GetTruncatedDataBuffer(imageBuffer, blockSize, MAX_BLOCK_SIZE)
        for i in range (0, dataSize):
            self.Bytes[i] = dataBuffer[i]

    def getStruct(self, majorVersion = 1, minorVersion = 0):
        if(1 == majorVersion):
            if(minorVersion < 4):
                return self.version1
            else:
                return self.version1_4
        elif (majorVersion >= 2):
            return self.version2
        else:
            OutputLog.Error(format("Unknown object header structure du to invalid TOC version %d.%d" % (majorVersion, minorVersion)))
            return None


class intelTelemetryDataAreaValidation_union(Union):
    """
    Brief:
        intelTelemetryDataAreaValidation_union() - Data Area Validation Data object.

    Description:
        This class extends TWIDL_Union.

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Randal Eike
    """
    _pack_ = 1
    _fields_ = [
                ("validation",   c_uint64),     # Validation value
                ("Bytes",        c_ubyte * 8)   # fill
                # End More Intel
               ]

    def __init__(self, imageBuffer):
        dataSize, dataBuffer = GetTruncatedDataBuffer(imageBuffer, 8, 8)
        for i in range (0, dataSize):
            self.Bytes[i] = dataBuffer[i]

    def getValidationValue(self):
        return self.validation

    def validate(self):
        if (0x7FFFFFFFFFFFC99 == self.validation):
            return True
        else:
            return False

