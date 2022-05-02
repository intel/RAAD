#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Randal Eike, Joseph Tarango
# *****************************************************************************/
"""
Brief:
    intelTelemetryParser.py - Generic parser definitions for parsing telemetry data object blobs

Description:
    This file contains the base class and function definitions needed to build a parser
    for a telemetry data object

Classes:
    Enter GetHeaders("parsers\\intelTelemetryDataObject.py") to display Class listings.
"""
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import os
import sys
import importlib
from ctypes import *
from array import array

################################################################################################################
################################################################################################################

OBJECT_HEADER_V2_SIZE = 12

class telemetryStruct_union(Union):
    """
    Brief:
        telemetryStruct_union() - Union to load structure from file data or array.

    Description:
        Fill union with data from a binary file or other array object.

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Randal Eike
    """
    _pack_      = 1
    _fields_    = [
                    # parser developers should create the Bytes and Fields entries
                  ]

    def __init__(self, imageObject=None, maxBytes=None, ignoreSizeMismatch=False, imageBuffer=None, file=None, returnBlockSize=None):
        """
        Brief:
            Populates union via Bytes field from content stored in imageObject.
        """
        Union.__init__(self)

        # Test if we have a byte definition
        if (hasattr(self, "Bytes") and (imageBuffer is not None)):
            if (maxBytes is None):
                dataSize = len(self.Bytes)
            else:
                dataSize = min(maxBytes,len(self.Bytes))
                if ((maxBytes > len(self.Bytes)) and (ignoreSizeMismatch == False)):
                    print("WARNING: Input structure size is less than input data buffer size.  Buffer truncated.\n")
                if ((maxBytes < len(self.Bytes)) and (ignoreSizeMismatch == False)):
                    print("WARNING: Input data buffer size is less than input structure size.  Structure not completely filled.\n")

            # Test if the input is a file
            if isinstance(imageObject, file):
                # Create a byte array from the file data at the current file pointer
                dataBuffer = array('B')
                dataBuffer.fromfile(imageObject, returnBlockSize)
            else:
                # Assume that the object already has an array definition
                dataBuffer = imageObject

            # Fill the structure
            for i in range (0, dataSize):
                self.Bytes[i] = dataBuffer[i]



class intelTelemetryDataObjectHeaderV2_0_struct(Structure):
    """
    Brief:
        intelTelemetryDataObjectHeaderV2_0_struct() - Intel Telemetry object header structure definition.

    Description:
        Intel data object header structure definition.

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
                ("idNumber",     c_uint32),    # Identification number of the object
                ("majorVersion", c_uint16),    # Major version number of the object
                ("minorVersion", c_uint16),    # Minor version number of the object
                ("cpuId",        c_uint8),     # CPU ID number associated with the object
                ("reserved",     c_uint8 * 3), # Reserved for future expansion and data alignment
                # End More Intel
               ]

    def getIdNumber(self):
        return (self.idNumber)

    def getMajorVersion(self):
        return (self.majorVersion)

    def getMinorVersion(self):
        return (self.minorVersion)

    def getVersionName(self, includeMinor=True):
        if (includeMinor):
            return ('V'+str(self.majorVersion)+'_'+str(self.minorVersion))
        else:
            return ('V'+str(self.majorVersion))

    def getCpuId(self):
        return (self.cpuId)

    def tostr(self):
        retstr  = "Object ID: "+str(self.idNumber)+"\n"
        retstr += "Version  : "+str(self.majorVersion)+"."+str(self.minorVersion)+"\n"
        retstr += "CPU ID   : "+str(self.cpuId)+"\n"



class intelTelemetryDataObjectHeaderV2_0_union(telemetryStruct_union):
    """
    Brief:
        intelTelemetryDataObjectHeaderV2_0_union() - Intel Telemetry object header union fill structure.

    Description:
        This class extends telemetryStruct_union to fill a data object header stucture.

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
                ("header", intelTelemetryDataObjectHeaderV2_0_struct), # Version 2.0 data object header structure
                ("Bytes",  c_ubyte * OBJECT_HEADER_V2_SIZE),                              # fill
                # End More Intel
               ]

    def __init__(self, imageBuffer=None):
        self.telemetryStruct_union(imageBuffer, len(self.Bytes))

    def getStruct(self):
        return self.header

    def getSize(self):
        return (len(self.Bytes))



class DataParserV2_0(object):
    """
    Brief:
        ExampleDataParser() - Data parsing example code.

    Description:
        Example code for parsing a data object.

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Randal Eike
    """

    def _createParseStructure(self, moduleName, versionedStructName, file, objectSize, ignoreSizeMismatch):
        """
        Create a parsing structure based on the telemetryStruct_union and load the data into it

        Input:
            moduleName - Name of module containing the versionedStructName class
            versionedStructName - Name of the class to create
            file - Open binary file to load into the class
            objectSize - Number of bytes to load
            ignoreSizeMismatch - True = ignore objectSize and versionedStructName.Bytes size mismatch,
                                 False = Issue warning message on objectSize and versionedStructName.Bytes size mismatch

        Output:
            versionedStructName object or None if error
        """
        try:
            parseModule = importlib.import_module(moduleName)

            # Check if this is a correct class
            if (issubclass(versionedStructName, telemetryStruct_union)):
                try:
                    return getattr(parseModule, versionedStructName)(file, objectSize, ignoreSizeMismatch)
                except AttributeError:
                    print ("Versioned class %s does not exist in module %s\n" %(versionedStructName, moduleName))
                    return None
            else:
                print ("Class %s must be a subclass of telemetryStruct_union\n" %versionedStructName)
                return None

        except ImportError:
            print ("Unable to find module %s\n" % moduleName)
            return None


    def _openFile(self, filename):
        """
        Open the file and get the file size

        Input:
            filename - Name and path of the binary file to parse

        Output:
            file object, file size in bytes
        """
        # Try to open the file
        try:
            file = open(filename,"rb")
            fileSize = os.stat(filename).st_size
            return file, fileSize

        except IOError:
            print ("Error: Unable to open \"%s\"." % filename)
            return None, 0


    def __init__(self, expectedId, filename, moduleName=None, baseStructName=None, ignoreSizeMismatch=False):
        """
        Open, read and parse the file

        input:
            expectedId - Object identification number expected in the file
            filename - Name and path of the binary file to parse
            moduleName - Name of module containing the baseStructName class or None
            baseStructName - Base unversioned name of the parsing class to create and load the version number from the header
                             in the form "Vx_y" where x is the major version number and y is the minor version number will be
                             appended to this base name
            ignoreSizeMismatch - True = ignore objectSize and versionedStructName.Bytes size mismatch,
                                 False = Issue warning message on objectSize and versionedStructName.Bytes size mismatch
        """
        # default values
        self.parseStruct = None
        self.fileSize = 0
        self.union = None
        self.header = None
        self.objectSize = 0

        # Try to open the file
        self.file, self.fileSize = self._openFile(filename)
        if (self.fileSize > 0):
            # Read the header and make sure it matches
            self.union = intelTelemetryDataObjectHeaderV2_0_union(self.file)
            self.header = self.union.getStruct()
            self.objectSize = self.fileSize - self.union.getSize()

            # Verify the header
            if (self.header.getIdNumber() != expectedId):
                print ("Error: Object identifier mismatch. Expected %d, Read %d." % (expectedId, self.header.getIdNumber()))
            else:
                if ((moduleName is not None) and (baseStructName is not None)):
                    self.parseStruct = self._createParseStructure(moduleName, baseStructName+self.header.getVersionName(), self.file, self.objectSize, ignoreSizeMismatch)

    def FillDataStructure(self, moduleName, baseStructName, includeMinor=True, ignoreSizeMismatch=False):
        self.parseStruct = self._createParseStructure(moduleName, baseStructName+self.header.getVersionName(includeMinor), self.file, self.objectSize, ignoreSizeMismatch)
        return self.parseStruct

    def getFile(self):
        return self.file

    def getVersionName(self, includeMinor=True):
        return self.header.getVersionName(includeMinor)

    def getObjectSize(self):
        return self.objectSize


