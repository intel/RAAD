#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Randal Eike, Phuong Tran, Joseph Tarango
# *****************************************************************************/
"""
a script that splits the telemetry data extracted into individual bin files by data structure name. For example, bis, initState, etc. have their own bin file.
Stores in a single directory.
"""
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
#### Import system libraries
import re, os, sys, array, ctypes, time, glob, getopt, math
from optparse import OptionParser

##### .exe extension patch for the compiled version of this script
if not re.search('\.PY$|\.PYC$|\.EXE$', os.path.split(sys.argv[0])[1].upper()):
    sys.argv[0] = os.path.join(os.path.split(sys.argv[0])[0], os.path.split(sys.argv[0])[1] + '.exe')

#### extend the Python search path to include TWIDL_tools directory
importPath = os.path.abspath(os.getcwd())
importPathNext = os.path.abspath(os.path.join(importPath, "bin"))
importPathAuto = os.path.abspath(os.path.join(importPath, "ctypeautogen"))
print("Importing Paths: ", str(importPath), str(importPathNext), str(importPathAuto))
sys.path.insert(1, importPath)
sys.path.insert(1, importPathNext)
sys.path.insert(1, importPathAuto)

#### import TWIDL modules
import src.software.parse.headerTelemetry
from src.software.parse.headerTelemetry import *
from src.software.parse.intelVUTelemetry import *
from src.software.parse.intelTelemetryDataObject import *
from src.software.parse.intelObjectIdList import ParserObjectMap
from src.software.parse.telemetry_util import TelemetryLogBlockSize
from src.software.parse.telemetry_util import openReadFile
from src.software.parse.telemetry_util import openWriteFile
from src.software.parse.telemetry_util import cleanDir
from src.software.parse.output_log import OutputLog

### Global variables
debug = 0
TOOL_VERSION = 2.0
DEBUG_VERSION = 4
fileDelimiter = "."  # global delimiter for the parser
smallName = 1  # Will include prefixes when creating the file name

# Global Lists to construct GHS RC file
telemetryObjectFileList = []
telemetryObjectRCMemLoadList = []
telemetryObjectRCViewList = []

productADPList = [5, 6, 8, 10, 20, 44, 45, 46, 47, 48, 49, 50, 51, 52, 54, 57, 58, 86, 88, 89, 109, 225, 247, 248]


class ObjectListEntry(object):
    """
    Telemetry object Data and Metadata
    """

    def __init__(self, binFileOffset, size, objectId, objectMajorVer=1, objectMinorVer=0, mediaBankId=-1, eventNumber=-1, humanName=None, dataArea=-1):
        self.objectId = objectId
        self.objectMajorVer = objectMajorVer
        self.objectMinorVer = objectMinorVer
        self.mediaBankId = mediaBankId
        self.eventNumber = eventNumber
        self.dataOffset = binFileOffset
        self.dataSize = size
        self.humanName = humanName
        self.dataArea = dataArea
        self.binData = None

    def __repr__(self):
        reprString = "\n===objectId= %s, maj= %s, min= %s===\n" % (self.objectId, self.objectMajorVer, self.objectMinorVer)
        reprString += "offset= %s\nsize= %s\n" % (self.dataOffset, self.dataSize)
        reprString += "name= %s\ndataArea= %s\n" % (self.humanName, self.dataArea)
        return reprString

    # @staticmethod
    def getObjectId(self):
        return self.objectId

    # @staticmethod
    def getObjectIdData(self):
        return self.objectId, self.objectMajorVer, self.objectMinorVer

    # @staticmethod
    def getBinLocation(self):
        return self.dataOffset, self.dataSize

    # @staticmethod
    def getMediaBank(self):
        return self.mediaBankId

    # @staticmethod
    def getEventNumber(self):
        return self.eventNumber

    # @staticmethod
    def getDataArea(self):
        return self.dataArea

    # @staticmethod
    def getSize(self):
        return self.dataSize

    # @staticmethod
    def getMajor(self):
        return self.objectMajorVer

    # @staticmethod
    def getMinor(self):
        return self.objectMinorVer

    # @staticmethod
    def setBinData(self, binData):
        self.binData = binData

    # @staticmethod
    def getBinData(self):
        return self.binData

    # @staticmethod
    def setHumanName(self, humanName):
        self.humanName = humanName

    # @staticmethod
    def getHumanName(self):
        if (self.humanName is None):
            return "UNKNOWN"
        else:
            return self.humanName


class ParseTelemetryPhase2(object):
    """
    Brief:
        parseTelemetryPhase2() - Phase2 bin file parser.

    Description:
        Parse the output bin files from phase 1 parser

    Class(es):
        None

    Method(s):
        __init__(self): Constructor
        parseTelemetryPhase2(self)

    Related:

    Author(s):
        Randal Eike
    """

    def __init__(self, nvmeHeaderSize=512, objHeaderSize=None):
        self.nvmeHeaderSize = nvmeHeaderSize
        self.objectHeaderSize = objHeaderSize
        self.objectIdList = ParserObjectMap()

    def parseFiles(self, parseFileList, outFileBaseName):
        # Initialize the nlog lists
        nlogParseList = []
        for fileEntry in parseFileList:
            objectData, inputParseName = fileEntry
            objectId, objectMajorVer, objectMinorVer = objectData.getObjectIdData()

            # Check if this is an nlog ID
            if (self.objectIdList.isNlogObject(objectId)):
                nlogParseList.append(inputParseName)
            else:
                self.objectIdList.ParseObjectData(objectId, objectMajorVer, objectMinorVer, inputParseName, objectData.getMediaBank(), objectData.getEventNumber, outFileBaseName)

        # Output combined NLog text file
        self.objectIdList.ParseNlogData(nlogParseList, outFileBaseName)


class splitTelemetryFile(object):
    """
    Brief:
        splitTelemetryFile() - Telemetry bin master file parser.

    Description:
        Split the input telemetry master bin file into it's component parts for later parsing

    Class(es):
        None

    Method(s):
        __init__(self, blockSize=512, headerSize = None): Constructor
        splitTelemetryFile(self, inputFile, outFilePath = ".", fileNamePrefix = "")

    Related:

    Author(s):
        Randal Eike
    """

    def __init__(self, nvmeHeaderSize=512, tocSize=None, objHeaderSize=None):
        """
        Class constructor

        Input: nvmeHeaderSize - Size of the NVMe header structure block in bytes
               tocSize - Size of the Telemetry table of contents structure block in bytes
               objHeaderSize - Size of the Telemetry object header structure block in bytes
        """
        self.splitFileList = []
        self.splitObjectList = []
        self.dataAreaList = []
        self.nvmeHeaderSize = nvmeHeaderSize
        self.logBlockSize = TelemetryLogBlockSize  # Defined by NVMe version 1.3 specification
        self.stripObjectHeader = True
        self.objectIdList = ParserObjectMap()
        self.outFileBaseName = "telemetry" + fileDelimiter
        self.currentTocMajor = 0
        self.currentTocMinor = 0
        self.currentDataAreaNumber = 0
        OutputLog.DebugPrint(4, "Object Map Data")
        OutputLog.DebugPrint(4, self.objectIdList.tostr())

        # If there is input, use that number else default to the NVMe header size alignment
        if (tocSize is not None):
            self.tocSize = tocSize
        else:
            self.tocSize = nvmeHeaderSize

        # If there is input, use that number else default to the NVMe header size alignment
        if (objHeaderSize is not None):
            self.objHeaderSize = objHeaderSize
        else:
            self.objHeaderSize = nvmeHeaderSize

    def writeOutputData(self, inputFile, dataOffset, dataSize, outputFileName):
        """
        Write the data block to the output file as binary (as-is)

        Input: inputFile - Binary input file object
               objectDesc - Object descriptor containint the location and size of the object in the input binary
               outputFileName - Name and path of the output file to generate
        """
        inputFile.seek(dataOffset)
        OutputLog.DebugPrint(2, format("Creating file: %s, size %d" % (outputFileName, dataSize)))
        outBin = openWriteFile(outputFileName)
        if (outBin is not None):
            outputData = inputFile.read(dataSize)
            outBin.write(outputData)
            outBin.close()
            return outputData
        return None

    def writeOutputText(self, inputFile, dataOffset, dataSize, outputFileName):
        """
        Write the data block to the output file as text (with text line ending and padding)

        Input: inputFile - Binary input file object
               objectDesc - Object descriptor containint the location and size of the object in the input binary
               outputFileName - Name and path of the output file to generate
        """
        inputFile.seek(dataOffset)
        OutputLog.DebugPrint(2, format("Creating file: %s, size %d" % (outputFileName, dataSize)))
        outBin = openWriteFile(outputFileName, True)
        if (outBin is not None):
            putString = inputFile.read(dataSize)
            outBin.write(str(putString))
            outBin.close()
            return putString
        return None

    def writeAllOutputRC(self, outputFileName):
        """
        Write the data block to the output file

        Input: inputFile - Binary input file object
               objectDesc - Object descriptor containint the location and size of the object in the input binary
               outputFileName - Name and path of the output file to generate
        """
        fileNameRC = outputFileName + ".rc"
        OutputLog.DebugPrint(2, format("Creating file: %s" % (fileNameRC)))
        outRCFile = open(fileNameRC, "w+")

        for item in telemetryObjectRCMemLoadList:
            outRCFile.write("%s\n" % item)

        for item in telemetryObjectRCViewList:
            outRCFile.write("%s\n" % item)

        OutputLog.DebugPrint(2, format("Expected: Loads= %s Views= %s" % (len(telemetryObjectRCMemLoadList), len(telemetryObjectRCViewList))))
        outRCFile.close()

    def checkValidationObject(self, telemetryData, objectOffset, tocObjectNumber):
        """
        Check that the validation object is correct

        Input: telemetryData - Binary file object
               objectOffset - Offset from the start of the input binary file where the validation data is stored
               tocObjectNumber - TOC entry number for debug output

        Output: True = Check passed
                False = Validity object does not match expected data
        """
        telemetryData.seek(objectOffset)
        validation = intelTelemetryDataAreaValidation_union(telemetryData)
        if (validation.validate() == False):
            OutputLog.Warning(format("Data Area %d TOC Entry %d validation value error, expected 0x%x, read 0x%x\n" % (self.currentDataAreaNumber, tocObjectNumber, validation.getExpectedValue(), validation.getValidationValue())))
            return False
        else:
            OutputLog.DebugPrint(2, format("Validation object for data area %d TOC entry %d, validation value matched" % (self.currentDataAreaNumber, tocObjectNumber)))
            return True

    def checkObjectBin(self, objectOffset, objectSize, tocObjectNumber, telemetryData):
        """
        Read telemetry header, check validity and check version and size match expected info, return telemetry object data

        Input: objectOffset - Offset from the start of the input binary file where object header is located
               objectSize - Size in bytes of the object data and header structure from the TOC
               tocObjectNumber - TOC entry number for debug output
               telemetryData - Binary file object

        Output: returnStatus - True = Object header was read and parsed
                               False = Unable to read or parse the object headers
                validationStatus - True = All validity checks passed on the object header and header data matched expected,
                                   False = At least one non-fatal validity check failed
                objectData - ObjectListEntry object containing the relevent object data
        """
        returnStatus = True
        validationStatus = True
        telemetryData.seek(objectOffset)
        objectHeader = intelTelemetryObjectHeader_union(telemetryData, self.objHeaderSize).getStruct(self.currentTocMajor, self.currentTocMinor)

        # Parse the object
        objectByteSize = objectHeader.getObjectByteSize(objectSize)
        objectID = objectHeader.getObjectIdentifier()
        objectCpuNumber = objectHeader.getCpuNumber()
        objMajorVersion = objectHeader.getMajorVersion()
        objMinorVersion = objectHeader.getMinorVersion()

        if (self.stripObjectHeader):
            dataOffset, dataSize = objectHeader.getDataOffsetAndSize(objectOffset, objectByteSize)
        else:
            dataOffset = objectOffset
            dataSize = objectByteSize

        # Get the object data from the header
        if (False == objectHeader.validate()):
            OutputLog.Error(format("Object header invalid, DataArea %d TOC index %d\n%s" % (self.currentDataAreaNumber, tocObjectNumber, objectHeader.tostr())))
            returnStatus = False
            validationStatus = False
            objectData = ObjectListEntry(objectOffset, objectByteSize, objectID, objMajorVersion, objMinorVersion, objectCpuNumber, -1, "INVALID", self.currentDataAreaNumber)
        else:
            # Validate the data is as expected
            if (self.currentTocMajor >= 2):
                # Check the header data vs expected
                validationStatus = self.objectIdList.CheckObjectHeader(objectID, objMajorVersion, objMinorVersion, dataSize, self.currentDataAreaNumber, objectOffset)

                # Check the validation if this is a validation ID
                if ((self.objectIdList.isValidationObject(objectID)) and (True == validationStatus)):
                    validationStatus = self.checkValidationObject(telemetryData, dataOffset, tocObjectNumber)

                humanName = self.objectIdList.GetEUIDHumanName(objectID, objMajorVersion, objMinorVersion)
            else:
                # Human name from the object
                humanName = objectHeader.getHumanName()

            # Get event number
            eventNumber = self.objectIdList.GetEventNumber(objectID, objectCpuNumber)

            # debug display
            OutputLog.DebugPrint(3, format("Object header, DataArea %d TOC index %d\n" % (self.currentDataAreaNumber, tocObjectNumber)))
            OutputLog.DebugPrint(3, objectHeader.tostr())
            OutputLog.DebugPrint(3, format("Object Name: %s" % (humanName)))
            OutputLog.DebugPrint(3, format("Object EventNumber: %d\n" % (eventNumber)))

            # New object data entry
            objectData = ObjectListEntry(dataOffset, dataSize, objectID, objMajorVersion, objMinorVersion, objectCpuNumber, eventNumber, humanName, self.currentDataAreaNumber)

        # Return status and data
        return returnStatus, validationStatus, objectData

    @staticmethod
    def constructFileName(outFileBaseName, objectData):
        """
        Constructs the telemetry object bin file based on the identification
        """
        outputFileName = outFileBaseName + fileDelimiter

        if (smallName == 0):
            outputFileName = outputFileName + "eUID" + fileDelimiter
        outputFileName = outputFileName + str(objectData.getObjectId()) + fileDelimiter

        if (smallName == 0):
            outputFileName = outputFileName + "Major" + fileDelimiter
        outputFileName = outputFileName + str(objectData.getMajor()) + fileDelimiter

        if (smallName == 0):
            outputFileName = outputFileName + "Minor" + fileDelimiter
        outputFileName = outputFileName + str(objectData.getMinor()) + fileDelimiter

        if (smallName == 0):
            outputFileName = outputFileName + "FirmwareName" + fileDelimiter
        outputFileName = outputFileName + objectData.getHumanName() + fileDelimiter

        if (smallName == 0):
            outputFileName = outputFileName + "ByteSize" + fileDelimiter
        outputFileName = outputFileName + str(objectData.getSize()) + fileDelimiter

        if (smallName == 0):
            outputFileName = outputFileName + "DataArea" + fileDelimiter
        outputFileName = outputFileName + str(objectData.getDataArea()) + fileDelimiter

        if (objectData.getMediaBank() == -1):
            if (smallName == 0):
                outputFileName = outputFileName + "Core" + fileDelimiter
        outputFileName = outputFileName + str(objectData.getMediaBank()) + fileDelimiter

        outputFileName = outputFileName + "bin"

        return outputFileName

    def createElementForRC(self, outputFileName, objectData):
        # Usage
        # ObjectRCMemLoad, ObjectRCView = createRCFiles(objectData, RCFileName)
        # telemetryObjectRCMemLoadList.append(ObjectRCMemLoad)
        # telemetryObjectRCViewList.append(ObjectRCView)
        #
        # Access Functions for objectData
        # getMediaBank(), getEventNumber(), getDataArea(), getSize(), getMajor(), getMinor(), getHumanName()
        #
        # Example GHS Usage
        # memload raw -noprogress C:\sample\PHAB8506001G3P8AGN.44.13.3.DefragInfoSlow.152.bin &DefragInfoSlow
        strMemLoadRC = "memload raw -noprogress "  # Memory load for telemetry requires raw binary and we do not want to see progress
        strMemLoadRC = strMemLoadRC + outputFileName + " "  # Location to file with filename
        strMemLoadRC = strMemLoadRC + "&" + str(objectData.getHumanName())  # load the GHS with the firmware name by address

        # view DefragInfoSlow
        strViewRC = "view " + str(objectData.getHumanName())  # Create a list to view all data structures loaded
        return strMemLoadRC, strViewRC

    def saveObjectElementInList(self, outputFileName, objectRCMemLoad, objectRCView):
        """
        Saves the object properties for GHS RC file creation.
        """
        updatedOFN = 0
        updatedRML = 0
        updatedRV = 0

        # Add the strings to the corresponding list
        if outputFileName not in telemetryObjectFileList:
            telemetryObjectFileList.append(outputFileName)
            updatedOFN = 1

        if objectRCMemLoad not in telemetryObjectRCMemLoadList:
            telemetryObjectRCMemLoadList.append(objectRCMemLoad)
            updatedRML = 1

        if objectRCView not in telemetryObjectRCViewList:
            telemetryObjectRCViewList.append(objectRCView)
            updatedRV = 1

        return (updatedOFN, updatedRML, updatedRV)

    def outputObjectBin(self, objectData, telemetryData, outFileBaseName):
        """
        Read the object block from the telemetry bin and output the object bin file
        """
        # Get the data location
        print("objectData: ", objectData)
        dataOffset, dataSize = objectData.getBinLocation()

        # Check the validation if this is a validation ID
        if ((self.currentTocMajor >= 2) and (self.objectIdList.isValidationObject(objectData.getObjectId()))):
            validationTextFileName = outFileBaseName + fileDelimiter + "validationtxt" + fileDelimiter + "DA" + str(objectData.getDataArea()) + ".txt"
            self.writeOutputText(telemetryData, dataOffset, dataSize, validationTextFileName)

        outputFileName = self.constructFileName(outFileBaseName, objectData)
        objectRCMemLoad, objectRCView = self.createElementForRC(outputFileName, objectData)

        if (objectData.getObjectId() in productADPList):
            self.saveObjectElementInList(outputFileName, objectRCMemLoad, objectRCView)

        # Copy the data to the output file
        self.splitFileList.append((objectData, outputFileName))
        self.writeOutputData(telemetryData, dataOffset, dataSize, outputFileName)

    def getTelemetryDataAreaTOC(self, dataAreaStartOffset, dataAreaSize, telemetryData):
        """
        Read the data area table of contents and return the parameter
        """
        # Read the TOC data
        telemetryData.seek(dataAreaStartOffset)
        tocRead = min(self.tocSize, dataAreaSize)
        intelTelemetryTOC = intelTelemetryTOC_union(telemetryData, tocRead).getStruct()
        OutputLog.DebugPrint(3, "Table of contents:")
        OutputLog.DebugPrint(3, intelTelemetryTOC.tostr())
        return intelTelemetryTOC

    def checkTelemetryFileDataArea(self, dataAreaStartOffset, dataAreaSize, telemetryData):
        """
        Parse the data area file into it's object parts and check the object validity

        Input: dataAreaStartOffset - Data area starting offset from the main telemetry file
               dataAreaSize - Size of the data area in bytes
               telemetryData - Binary data area input file object

        Output: returnStatus - True = Data area TOC was parsed and object data list was generated, False = unable to read and parse TOC or one of the object headers pointer to by the TOC
                validationStatus - True = All validity checks passed, False = one or more object headers pointer to by the TOC failed the validity checks

        Updated:
                self.splitObjectList - Fills it with ObjectData objects from the Data Area
        """
        # Assume good status until proven otherwise
        daValidationStatus = True
        daReturnStatus = True

        # Read the TOC data
        intelTelemetryTOC = self.getTelemetryDataAreaTOC(dataAreaStartOffset, dataAreaSize, telemetryData)
        objStartList, aplStart = intelTelemetryTOC.buildList(dataAreaSize)
        if (False == intelTelemetryTOC.validate()):
            OutputLog.Error(format("TOC invalid for data area %d, contents:\n%s" % (self.currentDataAreaNumber, intelTelemetryTOC.tostr())))
            return False, False

        # Initialize data object pull
        OutputLog.DebugPrint(1, format("Data area %d TOC list size: %d" % (self.currentDataAreaNumber, len(objStartList))))
        tocObjectNumber = 0
        self.currentTocMajor = intelTelemetryTOC.getMajorVersion()
        self.currentTocMinor = intelTelemetryTOC.getMinorVersion()

        if (self.currentTocMajor >= 2):
            objBaseOffset = dataAreaStartOffset
        elif (1 == self.currentTocMajor):
            objBaseOffset = 0
        else:
            OutputLog.Error(format("Invalid TOC major revision %d" % (self.currentTocMajor)))

        # Pull out the data objects
        for startLocation in objStartList:
            # Check if the TOC entry is ok
            if ((startLocation['startOffset'] >= intelTelemetryTOC.getTOCSize()) and (startLocation['size'] > self.objHeaderSize)):
                # Read the object header
                objStartOffset = startLocation['startOffset'] + objBaseOffset
                OutputLog.DebugPrint(3, format("Object list start offset=0x%x, adjusted offset=0x%x, size=%d" % (startLocation['startOffset'], objStartOffset, startLocation['size'])))

                returnStatus, validationStatus, objectData = self.checkObjectBin(objStartOffset, startLocation['size'], tocObjectNumber, telemetryData)
                self.splitObjectList.append(objectData)
                if (False == returnStatus):
                    OutputLog.Error(format("ObjectID: %d, Data area: %d, TOC entry: %d, Bin offset=0x%x, TOC Offset= 0x%x, TOC size=%u" % (objectData.getObjectId(), self.currentDataAreaNumber, tocObjectNumber, objStartOffset, startLocation['startOffset'], startLocation['size'])))
                    daReturnStatus = False
                if (False == validationStatus):
                    daValidationStatus = False
            else:
                OutputLog.Warning(format("Invalid entry found TOC offset: 0x%x, TOC size: %u, TOC entry: %d, Data area: %d" % (startLocation['startOffset'], startLocation['size'], tocObjectNumber, self.currentDataAreaNumber)))
                daValidationStatus = False

            # Next Object index
            tocObjectNumber += 1

        # Complete the APL data dump
        if (aplStart is not None):
            OutputLog.DebugPrint(3, format("APL list start offset=0x%x,  size=%u" % (aplStart['startOffset'], aplStart['size'])))
            aplObjectID, aplFileName = self.objectIdList.GetAPLReservedFileName(self.currentDataAreaNumber)
            objectData = ObjectListEntry(aplStart['startOffset'], aplStart['size'], aplObjectID, 1, 0, -1, -1, aplFileName)
            self.splitObjectList.append(objectData)

        # Return the data area status
        return daReturnStatus, daValidationStatus

    def checkTelemetryFile(self, telemetryData, hilog=True, outFileBaseName=None):
        """
        Parse telemetry File into its data areas and telemetry objects

        Input: telemetryData - Binary input file object, should be filled at this point

        Output: returnStatus - True = File header, all data area TOCs, and object headers were read and were at least parcially parsed
                               False = Unable to read and parse NVMe header or one or more data area TOC or object headers pointer to by the TOC
                validationStatus - True = All validity checks passed on all structures and matched expected,
                                   False = One or more structure failed the validity checks
        Mutatated:
                self.splitObjectList - Fills it with ObjectData objects from the Data Are
                self.dataAreaList - Fills with logBlock numbers which mark the start of data area
        """

        # Read the nvme Header
        del self.dataAreaList[:]
        fileReturnStatus = True
        fileValidationStatus = True

        telemetryData.seek(0)
        telemetryHeader = TelemetryLogPageHeader_union(telemetryData, self.logBlockSize).getInterfaceTelemetryHeaderStruct()
        if (False == telemetryHeader.validate()):
            OutputLog.Error("Invalid interface header. Aborting parse.")
            return False, False

        if ((True == telemetryHeader.IsHostInitiated()) and (True == hilog)):
            OutputLog.DebugPrint(1, "Host Initiated Log Detected")
        elif ((False == telemetryHeader.IsHostInitiated()) and (False == hilog)):
            OutputLog.DebugPrint(1, "Controller Initiated Log Detected")
        else:
            if (hilog):
                OutputLog.Warning("Controller Initiated Log Detected, expected host initiated log data!")
            else:
                OutputLog.Warning("Host Initiated Log Detected, expected controller initiated log data!")
            return False, False

        OutputLog.DebugPrint(2, telemetryHeader.tostr())

        outputFileName = outFileBaseName + fileDelimiter + "TelemetryHeader.txt"
        outTxt = openWriteFile(outputFileName, text=True)
        if outTxt is not None:
            outTxt.write(telemetryHeader.tostr())
            outTxt.close()
        else:
            print("Writing TelemetryHeader failed...")

        # Get the last block of the data
        lastBlock, dataAreaList = telemetryHeader.getLastBlock()
        dataAreaOffset = self.nvmeHeaderSize
        self.currentDataAreaNumber = 1

        for dataAreaLastBlock in dataAreaList:
            # Mark the ending offset
            endOffset = dataAreaLastBlock * self.logBlockSize
            dataAreaSize = endOffset - dataAreaOffset

            # Read the table of contents and get the starting object offsets of the data objects
            OutputLog.DebugPrint(3, format("Append data area %d, offset: 0x%x, size: 0x%x to list" % (self.currentDataAreaNumber, dataAreaOffset, dataAreaSize)))
            self.dataAreaList.append((dataAreaOffset, dataAreaSize, self.currentDataAreaNumber))

            OutputLog.DebugPrint(1, format("Parse data area %d, offset: 0x%x, size: 0x%x" % (self.currentDataAreaNumber, dataAreaOffset, dataAreaSize)))
            daReturnStatus, daValidationStatus = self.checkTelemetryFileDataArea(dataAreaOffset, dataAreaSize, telemetryData)
            if (False == daReturnStatus):
                fileReturnStatus = False
                OutputLog.Error(format("Data area %d failed to parse" % (self.currentDataAreaNumber)))

            if (False == daValidationStatus):
                fileValidationStatus = False
                OutputLog.Warning(format("Data area %d validity check failed" % (self.currentDataAreaNumber)))

            self.currentDataAreaNumber += 1
            dataAreaOffset = endOffset

        return fileReturnStatus, fileValidationStatus

    def splitTelemetryFile(self, telemetryData, outFileBaseName, hilog=True):
        """
        A wrapper for checkTelemetryFile(), and print data areas to files
        """

        # clean any old list
        del self.splitFileList[:]

        # Check file for validity
        returnStatus, validationStatus = self.checkTelemetryFile(telemetryData, hilog, outFileBaseName)
        if (True == returnStatus):
            # Output data area bin files
            for dataArea in self.dataAreaList:
                dataAreaOffset, dataAreaSize, dataAreaNumber = dataArea
                outputFileName = outFileBaseName + fileDelimiter + "DataArea" + str(dataAreaNumber) + ".bin"
                self.writeOutputData(telemetryData, dataAreaOffset, dataAreaSize, outputFileName)

            # Output object bin files
            for objectData in self.splitObjectList:
                self.outputObjectBin(objectData, telemetryData, outFileBaseName)

            self.writeAllOutputRC(outFileBaseName)  # Output RC GHS scripts

        return self.splitFileList, returnStatus, validationStatus

    def buildNlogList(self, parseFileList, outFileBaseName):
        # Initialize the nlog lists
        nlogParseList = []
        for fileEntry in parseFileList:
            objectID, majorVersion, minorVersion, inputParseName, coreNumber, eventDumpNumber = fileEntry

            # Check if this is an nlog ID
            if (self.objectIdList.isNlogObject(objectID)):
                nlogParseList.append(inputParseName)

        # Output combined NLog text file
        nlogTextFileName = outFileBaseName + "_NLOG_FILE_LIST.txt"
        nlogListFile = openWriteFile(nlogTextFileName, True)
        if (nlogListFile is not None):
            for nlogFile in nlogParseList:
                nlogListFile.write(str("\"" + nlogFile + "\",\n"))
            nlogListFile.close()
        else:
            nlogTextFileName = None

        return nlogTextFileName


class splitTelemetryFile_v1(splitTelemetryFile):
    """
    Brief:
        splitTelemetryFile_v1() - Telemetry version 1 bin master file parser.

    Description:
        Split the input telemetry master bin file into it's component parts for later parsing

    Class(es):
        None

    Method(s):
        None

    Related: - splitTelemetryFile

    Author(s):
        Randal Eike
    """

    def __init__(self):
        super(splitTelemetryFile_v1, self).__init__(4096, 4096, intelTelemetryObjectHeader_V1_struct.objectHeaderSize)


class splitTelemetryFile_v2(splitTelemetryFile):
    """
    Brief:
        splitTelemetryFile_v2() - Telemetry version 2 bin master file parser.

    Description:
        Split the input telemetry master bin file into it's component parts for later parsing

    Class(es):
        None

    Method(s):
        None

    Related: - splitTelemetryFile

    Author(s):
        Randal Eike
    """

    def __init__(self):
        super(splitTelemetryFile_v2, self).__init__(TelemetryLogBlockSize, 4096, intelTelemetryObjectHeader_V2_struct.objectHeaderSize)


class telemetryFileParse(object):
    """
    Brief:
        telemetryFileParsePhase1() - Telemetry parser factory.

    Description:
        Read the input file header to determine the correct parser version

    Class(es):
        None

    Method(s):
        None

    Related: - splitTelemetryFile, splitTelemetryFile_v1, splitTelemetryFile_v2

    Author(s):
        Randal Eike
    """
    telemetrySplit = None
    serialNumber = None
    telemetryBinFile = None
    telemetryPhase2Parse = None
    telemetryHeader = None
    telemetryMajor = None
    telemetryMinor = None

    def __init__(self, telemetryBinFile):
        # Binary file location
        self.telemetryBinFile = telemetryBinFile

        # Create parse object
        self.telemetryPhase2Parse = ParseTelemetryPhase2()

        # Read the nvme Header
        self.telemetryBinFile.seek(0)
        interfaceTelemetryHeader = TelemetryLogPageHeader_union(self.telemetryBinFile, TelemetryLogBlockSize)
        telemetryHeader = interfaceTelemetryHeader.getInterfaceTelemetryHeaderStruct()
        self.telemetryHeader = telemetryHeader

        # Validate the header
        if (True == telemetryHeader.validate()):
            # Read the serial number or default
            self.serialNumber = telemetryHeader.getSerialNumber()

            # Display the data if debug enabled
            OutputLog.DebugPrint(2, "Interface Header Data:")
            headerString = self.telemetryHeader.tostr()
            OutputLog.DebugPrint(2, f"{headerString}")

            # Validate the data
            (self.telemetryMajor, self.telemetryMinor) = telemetryHeader.getVersionInfo()
            if (telemetryHeader.IsVersion1()):
                self.telemetrySplit = splitTelemetryFile_v1()
            else:
                self.telemetrySplit = splitTelemetryFile_v2()
        else:
            OutputLog.Error("Telemetry header block validity check failed!")
        return

    def getVersionInfo(self):
        return self.telemetryMajor, self.telemetryMinor

    def getTelemetyHeader(self):
        return self.telemetryHeader

    def getSerialNumber(self):
        return self.serialNumber

    def buildNlogList(self, parseFileList, outFileBaseName):
        return self.telemetrySplit.buildNlogList(parseFileList, outFileBaseName)

    def parseTelemetryDataPhase1(self, outputBaseName, hiLog=True):
        """ parseTelemetryDataPhase1 is a wrapper function for checkTeletryDataPhase1"""
        return self.telemetrySplit.splitTelemetryFile(self.telemetryBinFile, outputBaseName, hiLog)

    def parseTelemetryDataPhase2(self, parseFileList, outputBaseName):
        return self.telemetryPhase2Parse.parseFiles(parseFileList, outputBaseName)

    def buildGreenHillsScript(self, parseFileList, outFileBaseName):
        return self.telemetrySplit.buildNlogList(parseFileList, outFileBaseName)

    def checkTelemetryDataPhase1(self, hiLog=True):
        fileReturnStatus, fileValidationStatus = self.telemetrySplit.checkTelemetryFile(self.telemetryBinFile, hiLog)
        if ((True == fileReturnStatus) and (True == fileValidationStatus)):
            return True
        else:
            return False

        # print struct

    def get_value(self, value):
        if (type(value) not in [int, float, bool]) and not bool(value):
            # it's a null pointer
            value = None
        elif hasattr(value, "_length_") and hasattr(value, "_type_"):
            # Probably an array
            # print value
            value = self.get_array(value)
        elif hasattr(value, "_fields_"):
            # Probably another struct
            value = self.getdict(value)
        return value

    def get_array(self, array):
        ar = []
        for value in array:
            value = self.get_value(value)
            ar.append(value)
        return ar

    def getdict(self, struct):
        result = {}
        for f in struct._fields_:
            field = f[0]
            value = getattr(struct, field)
            # if the type is not a primitive and it evaluates to False ...
            value = self.get_value(value)


def checkLogValidity(logfileName, hiLog=True):
    validityStatus = True
    telemetryBinFile = openReadFile(logfileName)

    if (telemetryBinFile is not None):
        # check the basic validity of the file
        OutputLog.DebugPrint(1, format("File \"%s\" log validity check\n" % (logfileName)))
        telemetryParser = telemetryFileParse(telemetryBinFile)
        if (False == telemetryParser.checkTelemetryDataPhase1(hiLog)):
            OutputLog.Error(format("File \"%s\" failed log validity check\n" % (logfileName)))
            validityStatus = False

        telemetryBinFile.close()

    return validityStatus


def checkLogListValidity(logFileList, hiLog=True):
    validityStatus = True
    for filename in logFileList:
        if (False == checkLogValidity(filename, hiLog)):
            validityStatus = False

    return validityStatus


def parseInputBin(telemetryInputBin, hilog, outPath, prefix=None, checkOnly=False):
    """
    The main interface, creates and runs telemetryFileParse Factory functionality

    """
    parseStatus = True
    parseValidity = True

    # Validate the header and get the file parser
    telemetryParser = telemetryFileParse(telemetryInputBin)

    # Execute the test
    if (checkOnly):
        # Check the file for valid contents
        OutputLog.setWarnIsError(True)
        parseStatus = telemetryParser.checkTelemetryDataPhase1(hilog)
    else:
        # Determine the output file base name
        if (prefix is None):
            outFilePrefix = telemetryParser.getSerialNumber()
        else:
            outFilePrefix = prefix

        # Construct the output file base name
        outFileBaseName = os.path.join(outPath, outFilePrefix)

        # Read and split the telemetry data file into it's component data files
        OutputLog.setWarnIsError(False)
        parseFileList, parseStatus, parseValidity = telemetryParser.parseTelemetryDataPhase1(outFileBaseName, hilog)
        if (parseFileList is not None):
            # Phase 2 parse (currently does nothing)
            OutputLog.Information("Phase 2 Parse (does nothing yet)")
            telemetryParser.parseTelemetryDataPhase2(parseFileList, outFileBaseName)

    return parseStatus, parseValidity, telemetryParser


def parseTelemetryBinAPI(inputFile, outpath=None, prefix=None, hilog=True, checkOnly=False, debug=False):
    """
    API to replace standard Command Line Call

    inputTelemetryFile = binary file to parse, input required
    outpath = Directory to store output telemetry bin subfiles
    prefix = Output file prefix
    hiLog = Host Initiated Telemetry Data Log
    checkOnly = When set the parsed data is not output only checked for validity (default = false)
    """

    # Assign the argument values
    OutputLog.setDebugLevel(debug)

    # input
    OutputLog.Information("infile:  " + inputFile)

    # Check output path
    if (outpath is not None):
        cleanDir(outpath)
        absOutPath = os.path.abspath(outpath)
        OutputLog.Information("outpath: " + outpath)
    else:
        absOutPath = os.path.abspath(".")

    if (os.path.exists(absOutPath) is False):
        OutputLog.Error(format("Output path %s does not exist\n" % (outpath)))
        return False

    # Try to open the input file
    OutputLog.Information(format("\nAttempting to parsing file \"%s\"..." % (inputFile)))
    telemetryInputBin = openReadFile(inputFile)
    if (telemetryInputBin is not None):
        parseStatus, validityCheck, telemetryParser = parseInputBin(telemetryInputBin, hilog, absOutPath, prefix, checkOnly)
        telemetryInputBin.close()
        if (False is parseStatus):
            OutputLog.Information("Failed!!!!")
            returnStatus = False
        else:
            OutputLog.Information("Passed!!!!")
            returnStatus = True

        OutputLog.Information("File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>")
        return returnStatus, telemetryParser
    else:
        OutputLog.Information("Telemetry Input Binary not found")
        # File open failed
        return False, None


def main():
    #### Command-line arguments ####
    parser = OptionParser(usage="usage: %prog [options] inputTelemetryFile", version="%prog Version: " + str(TOOL_VERSION))
    parser.add_option('--debug', type="int", dest='debug', action="store", default=0, help='Enable debug level')
    parser.add_option('-p', '--prefix', dest='prefix', type="string", default=None, help='Output File Prefix')
    parser.add_option('-o', '--outpath', dest='outpath', type="string", default=None, help='Output File Path')
    parser.add_option('--hi', action='store_true', dest="hilog", default=True, help='Input log is Host Initiated log (this is the default case)')
    parser.add_option('--ci', action='store_false', dest="hilog", help='Input log is Controller Initiated log')
    parser.add_option('--check', action='store_true', dest="checkOnly", default=False, help='Set the check only flag.  When set the parsed data is not output only checked for validity (default = false)')
    (options, args) = parser.parse_args()

    # Assign the argument values
    baseArgIndex = 0
    OutputLog.setDebugLevel(options.debug)
    if (len(args) >= 0):
        inputFile = args[baseArgIndex]
    else:
        inputFile = "telemetry.bin"

    parseTelemetryBinAPI(inputFile, options.outpath, options.prefix, options.hilog, options.checkOnly, options.debug)


######## Test it #######
if __name__ == '__main__':
    from datetime import datetime

    p = datetime.now()
    main()
    q = datetime.now()
    OutputLog.Information("\nExecution time: " + str(q - p))
