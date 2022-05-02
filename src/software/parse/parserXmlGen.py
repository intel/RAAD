#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Randal Eike, Joseph Tarango
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
# General Python module imports
import os, json, uuid, random
from datetime import datetime

# Token objects
from src.software.parse.autoObjects import dataElement
from src.software.parse.autoObjects import structDef
from src.software.parse.autoObjects import objectDefine
from src.software.parse.autoObjects import ctypedef
from src.software.parse.autoObjects import outputGenerationHelper
from src.software.parse.parserTwidlGen import parserTwidlGenerator


class xmlFileGenerator(object):
    def __init__(self, abspath, name = "telemetry_csdp"):
        self.absPath = abspath
        self.filename = name
        self.importList = []
        self.classList = []
        self.currentOutputFile = None
        tagCreate = str(os.getpid()) + "-" + str(datetime.now()) + "-" + str(random.randint(1,1024))
        self.uPIDName = str(uuid.uuid5(uuid.NAMESPACE_DNS, tagCreate))

    def __openfile(self, structName):
        absPath = os.path.join(self.absPath, structName)
        if (not os.path.exists(absPath)): os.makedirs(absPath)

        self.currentFileName = os.path.join(absPath, self.uPIDName+".xml")
        self.currentOutputFile = open(self.currentFileName, "wt")

    def __closeFile(self):
        self.currentOutputFile.close()
        self.currentOutputFile = None

    def __write(self, outStr):
        if (self.currentOutputFile is not None): self.currentOutputFile.write(outStr)
        else: print(outStr)

    def addClassDef(self, structName, structType, fieldList, token = 0, majorVersion = 0, minorVersion = 0):
        # Don't add it if it's already in the system
        duplicate = False
        for existingName, existingType, existingList, existingToken, existingMajorVer, existingMinorVer in self.classList:
            if ((existingName == structName) and (existingToken == token) and (existingMajorVer == majorVersion) and (existingMinorVer == minorVersion)):
                duplicate = True
                break

        if (False == duplicate): self.classList.append((structName, structType, fieldList, token, majorVersion, minorVersion))

    def __outputStructureData(self, fieldList, token = 0, majorVersion = 0, minorVersion = 0):
        self.__write(format("    <telemetry_struct token=\"%d\" versionMajor=\"%d\" versionMinor=\"%d\">\n" % (token, majorVersion, minorVersion)))

        for fieldName, fieldType, fieldOffset, fieldSize, docstr in fieldList:
            self.__write(format("        <field offsetByte=\"%d\" sizeByte=\"%d\" type=\"%s\" uid=\"%s\" name=\"%s\"></field>\n" % (fieldOffset, fieldSize, fieldType, fieldName, docstr)))

        self.__write("    </telemetry_struct>\n")

    def generateFile(self, telemetryVersionMajor, telemetryVersionMinor):

        self.masterListFile = os.path.join(self.absPath, "masterList.txt") #assign name of master list for filename

        try:
            with open(self.masterListFile) as json_file: #open file directory list to get names of files
                self.fileList = json.load(json_file)
        except (IOError, ValueError):
            self.fileList = {} #if there is not file directory list, create one

        for structName, structType, fieldList, token, majorVersion, minorVersion in self.classList:

            currentEntry = {"structName":structName, "structType":structType, "fieldList":fieldList, "token":token}

            try:
                self.fileList[structName][self.uPIDName] = currentEntry #add new entry for new hash
                self.fileList[structName]["Latest"] = currentEntry #update latest
            except KeyError:
                self.fileList[structName] = {self.uPIDName:currentEntry, "Latest":currentEntry} #if not there, make new sub-dictionary and give it the parameters

            self.__openfile(structName)

            # Output default header
            self.__write("<?xml version=\"1.0\"?>\n")
            self.__write(format("<telemetry versionMinor=\"%d\" versionMajor=\"%d\">\n" % (telemetryVersionMinor, telemetryVersionMajor)))

            # Output class data
            self.__outputStructureData(fieldList, token, majorVersion, minorVersion)

            self.__write("</telemetry>\n")
            self.__closeFile()

        with open(self.masterListFile, "wt") as json_file:
            json.dump(self.fileList, json_file)




class parserXmlGenerator(outputGenerationHelper):
    subdirName = "xmldata"
    nameSeparator = "_"

    def __init__(self):
        self.absPath = None
        return super(parserXmlGenerator, self).__init__()

    def __isFilteredType(self, xmlType):
        if ((xmlType[:9] == "bitfield:") or (-1 != xmlType.find("array")) or (xmlType[:6] == "struct")): return True
        else: return False

    def __addMemberDecription(self, member, workingDefList, basename = None, fileGenerator = None):
        substruct = member.getSubstruct()

        if (substruct is not None):
            subStructName = substruct.getName()
            memberName = member.getName()
            structBaseOffset = member.getOffset()

            # process the structure inline
            substructMembers = self.__generateClassDescription(substruct, basename, fileGenerator)

            # No file generator or special name (_name) or only one member in the structure
            for memberName, xmlType, offset, size, docStr in substructMembers:
                qualName = subStructName + parserXmlGenerator.nameSeparator + memberName
                qualOffset = offset + structBaseOffset
                if ((False == self.__isFilteredType(xmlType)) and (False == self.isSpecialName(memberName))):
                    workingDefList.append((qualName, xmlType, qualOffset, size, docStr))
        else:
            # Non-structure definition
            name, docStr, offset, size, xmlType = member.getXmlData()
            if ((False == self.__isFilteredType(xmlType)) and (False == self.isSpecialName(name))):
                workingDefList.append((name, xmlType, offset, size, docStr))

    def __generateStructMemberDescription(self, workingDescList, inputStruct, basename = None, fileGenerator = None):
        # Go through the members
        for member in inputStruct.getMemberList():
            self.__addMemberDecription(member, workingDescList, basename, fileGenerator)

    def __generateClassDescription(self, inputStruct, basename = None, fileGenerator = None):
        workingDescList = []
        self.__generateStructMemberDescription(workingDescList, inputStruct, basename, fileGenerator)
        return workingDescList

    def __generateFileDesc(self, fileGenerator, structEntry, baseName = None, token = 0, majorVersion= 0, minorVersion = 0):
        structName = structEntry.getName()
        memberList = self.__generateClassDescription(structEntry, baseName, fileGenerator)
        fileGenerator.addClassDef(structName, structEntry.getTwidlType(), memberList, token, majorVersion, minorVersion)

    def CreateFiles(self, objList, outputDir = None):
        # Create the path
        if (outputDir is not None): absPath = os.path.abspath(outputDir)
        else: absPath = os.path.abspath(os.path.join(".", parserTwidlGenerator.subdirName))

        # Check if it exists
        if (not os.path.exists(absPath)): os.makedirs(absPath)
        self.absPath = absPath

        fileGenerator = xmlFileGenerator(self.absPath)

        for objEntry in objList:
            # Generate an ordered list
            objStruct = objEntry.getObjStruct()
            self.__generateFileDesc(fileGenerator, objStruct, objEntry.getName(), objEntry.getUid(), objEntry.getMajorVersion(), objEntry.getMinorVersion())

        fileGenerator.generateFile(2, 0)





