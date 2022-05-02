#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Phuong Tran, Andrea Chamorro, Joseph Tarango
# *****************************************************************************/
# General Python module imports
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import os

# Token objects
from src.software.parse.autoObjects import dataElement
from src.software.parse.autoObjects import structDef
from src.software.parse.autoObjects import objectDefine
from src.software.parse.autoObjects import ctypedef
from src.software.parse.autoObjects import outputGenerationHelper


class parserDictionaryGenerator(outputGenerationHelper):
    nameSeparator = "__"
    subdirName = "tokenparser"

    def __init__(self):
        self.outFile = None
        return super(parserDictionaryGenerator, self).__init__()

    def __write(self, outStr):
        if (self.outFile is not None): self.outFile.write(outStr)
        else: print(outStr)

    def __outputMemberLine(self, name, size, signed, default, docStr, indexList = None, baseName = None):
        bitSize = size*8
        indexStr = ""
        if (indexList is not None):
            for index in indexList:
                indexStr += format("_%d" % (index))

        if (baseName is None): nameOutStr = format("\'%s%s\'" % (name, indexStr))
        else: nameOutStr = format("\'%s_%s%s\'" % (baseName, name, indexStr))

        if (docStr is not None): docOutStr = format("\'%s index%s\'" % (docStr, indexStr))
        else: docOutStr = nameOutStr

        memberStr = format ("      %-40s, %6d, %6d, %7d, %7s, %6s, %-35s,\n" % (nameOutStr, bitSize, signed, default, "bdDEC", "None", docOutStr))
        self.__write(memberStr)

    def __buildIndexModList(self, dimList):
        count = 1
        indexModList = []
        revDimList = dimList
        revDimList.reverse()
        for dim in revDimList:
            indexModList.append((dim, count))
            count *= dim

        indexModList.reverse()
        return count, indexModList

    def __buildEntryIndexList(self, index, indexModList):
        dimIndexList = []
        for indexMod, indexDivisor in indexModList:
            dimIndex = (index / indexDivisor) % indexMod
            dimIndexList.append(dimIndex)

        return dimIndexList

    def __outputStructDefHeader(self):
        # Output struct header
        self.__write("[\n")
        header = format ("#     %-40s, %6s, %6s, %7s, %7s, %6s, %-35s\n" % ("name", "size", "signed", "default", "style", "token", "desc"))
        self.__write(header)

    def __outputStructDefTail(self):
        # Output end comment
        self.__write("]\n\n")

    def __outputMemberData(self, member, basename = None):
        substruct = member.getSubstruct()
        if (substruct is not None):
            subStructName = substruct.getName()
            if (-1 != subStructName.find("__")):
                self.__outputMemberDecription(substruct, basename)
            else:
                memberName = member.getName()
                if (basename is not None): substructBaseName = basename + parserDictionaryGenerator.nameSeparator + memberName
                else: substructBaseName = memberName
                self.__outputMemberDecription(substruct, substructBaseName)
        else:
            name, size, signed, default, docStr, dimList = member.getDescData()

            if (dimList is not None):
                self.__write(format("#   %s array\n" % (name)))
                if (self.isSpecialName(name) or (len(dimList) == 1)):
                    # Special name, don't expand
                    self.__outputMemberLine(name, member.getSize(), signed, default, docStr, None, basename)
                else:
                    # Construct mod list
                    count, indexModList = self.__buildIndexModList(dimList)

                    # Go through the flat array
                    index = 0
                    while (index < count):
                        # New list for this index
                        dimIndexList = self.__buildEntryIndexList(index, indexModList)

                        # Add this one to the list
                        self.__outputMemberLine(name, size, signed, default, docStr, dimIndexList, basename)
                        index += 1

                self.__write(format("#   %s array end\n" % (name)))
            else:
                # Output the data member desc
                self.__outputMemberLine(name, size, signed, default, docStr, None, basename)


    def __outputStructMemberDecription(self, inputStruct, basename = None):
        # Output header comment
        self.__write(format("#   %s %s\n" % (inputStruct.getName(), inputStruct.getType())))

        # Go through the members
        for member in inputStruct.getMemberList():
            self.__outputMemberData(member, basename)

        self.__write(format("#   %s %s end of definition\n" % (inputStruct.getName(), inputStruct.getType())))

    def __outputUnionMemberDecription(self, inputStruct, basename = None):
        # Go through the members
        maxSize = 0
        maxMember = None
        for member in inputStruct.getMemberList():
            if (member.getSize() > maxSize):
                # Maximum size object
                maxMember = member
                maxSize = member.getSize()
            elif ((member.getSize() >= maxSize) and (member.getSubstruct() is not None) and (member.getSubstruct().getStructType() == structDef.STRUCT_TYPE)):
                # Structure overrides
                maxMember = member
                maxSize = member.getSize()

        if (maxMember != None):
            self.__write(format("#   %s %s\n" % (inputStruct.getName(), inputStruct.getType())))
            self.__outputMemberData(maxMember, basename)
            self.__write(format("#   %s %s end of definition\n" % (inputStruct.getName(), inputStruct.getType())))

    def __outputMemberDecription(self, inputStruct, basename = None):
        structType = inputStruct.getStructType()
        if (structType == structDef.STRUCT_TYPE):
            self.__outputStructMemberDecription(inputStruct, basename)
        elif (structType == structDef.UNION_TYPE):
            self.__outputUnionMemberDecription(inputStruct, basename)
        elif (structType == structDef.OBJECT_TYPE):
            self.__outputStructMemberDecription(inputStruct, basename)

    def __writeDictionaryFile(self, objEntry):
        # Output default header
        self.__write("\"\"\"This file is automatically generated per Telemetry object.  Please do not modify.\"\"\"\n")
        self.__write("from bufdict import *\n\n")

        # Output description start
        objName = objEntry.getName()
        capName = self.capFirstLetter(objName)
        majorVersion = objEntry.getMajorVersion()
        minorVersion = objEntry.getMinorVersion()
        descName = format("%s_Description_%d_%d" % (capName, majorVersion, minorVersion))

        self.__write(format("%s = \\\n" % (descName)))
        objStruct = objEntry.getObjStruct()

        # Output struct header, data and tail
        self.__outputStructDefHeader()
        self.__outputMemberDecription(objStruct)
        self.__outputStructDefTail()

        # Output object dictionary
        dictName = format("%s_dict" % (objName))
        padStr = "     "
        for x in range(0, len(objName)):
            padStr += ' '

        self.__write(format("%s = {\n" % (dictName)))
        self.__write(format("%s    (%d,%d): %s,\n" % (padStr, majorVersion, minorVersion, descName)))
        self.__write(format("%s   }\n\n" % (padStr)))

        # Output class
        self.__write(format("class %s(bufdict):\n" % (capName)))
        self.__write(format("    \"%s\"\n" % (capName)))
        self.__write(format("    def __init__(self, buf=None, offset=None, filename=None, other=None, namesize=%d, valuesize=%d, majorVersion=%d, minorVersion=%d):\n" % (30, 10, majorVersion, minorVersion)))
        self.__write(format("        description = getDescription(desc_dict=%s, key=(majorVersion, minorVersion))\n" % (dictName)))
        self.__write(format("        bufdict.__init__(self, description=description, version=majorVersion,name=\"%s\",namesize=namesize, valuesize=valuesize, filename=filename, buf=buf, other=other)\n" % (objName)))
        self.__write(format("        pass\n\n"))

    def CreateFiles(self, objList, outputDir = None):
        # Create the path
        if (outputDir is not None): absPath = os.path.abspath(outputDir)
        else: absPath = os.path.abspath(os.path.join(".", parserDictionaryGenerator.subdirName))

        # Check if it exists
        if (not os.path.exists(absPath)): os.makedirs(absPath)

        # Start generating files
        for objEntry in objList:
            outputFileName = os.path.join(absPath, objEntry.getName()+".py")
            self.outFile = open(outputFileName, "wt")
            if (self.outFile is not None):
                self.__writeDictionaryFile(objEntry)
                self.outFile.close()
                self.outFile = None



