#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import operator
from src.software.parse.varType import ghsCvarType

def stripCommentBlocking(docStr):
    # Strip leading comment and whitespace
    index = 0
    stripEnd = False

    while (docStr[index] == '/'): index += 1
    if (docStr[index] == '*'): stripEnd = True
    while ((docStr[index] == '*') or (docStr[index] == '\n') or (docStr[index] == ' ')): index += 1

    if (stripEnd):
        # multiline comment, only use the first line
        endindex = index
        while (docStr[endindex] != '\n'): endindex += 1
        return docStr[index:endindex]
    else:
        # single line comment
        return docStr[index:]


class dataElement(object):
    """
    Data object definition
    """

    vartypeData = ghsCvarType()

    def __init__(self, name, varTypeStr, docStr = None, dimList = None, bitField = False, structReference = None, offset = 0):
        self.name = name
        self.varTypeStr = varTypeStr
        self.docStr = docStr
        self.dimList = dimList
        self.bitField = bitField
        self.structReference = structReference

        self.elementSize = 0
        self.totalSize = 0
        self.offset = offset
        self.__setSizes()

    def __calcTotalSize(self):
        # Set the total size
        self.totalSize = self.elementSize
        if (self.dimList is not None):
            for dim in self.dimList: self.totalSize *= dim

    def __setSizes(self):
        if (self.bitField):
            # set the size data for the bit field
            self.elementSize = 0
            self.structReference = None
            if (self.dimList is None): self.dimList = [1]   # assume single bit if no specified
            self.totalSize = dataElement.vartypeData.getSize(self.varTypeStr)
        else:
            # Set the element size
            if (self.structReference is not None):
                # Defined structure reference, get the size from the structure data
                self.elementSize = self.structReference.getSize()
            elif ((self.varTypeStr[:6] == "struct") or (self.varTypeStr[:5] == "union")):
                # Undefined structure, assume base integer size for now
                self.elementSize = dataElement.vartypeData.getBaseSize()
            else:
                # Standard type definition
                self.elementSize = dataElement.vartypeData.getSize(self.varTypeStr)
            self.__calcTotalSize()

    # ============================
    # Modification routines
    # ============================
    def addDocStr(self, docStr):
        # Strip leading comment and whitespace
        newDocStr = stripCommentBlocking(docStr)

        if (self.docStr is None): self.docStr = newDocStr
        else: self.docStr += format(" %s" % (newDocStr))

    def updateToBitField(self):
        self.bitField = True
        self.structReference = None
        self.offset = 0
        self.__setSizes()

    def resetStructSize(self, size):
        self.elementSize = size
        self.__calcTotalSize()

    def updateOffset(self, offset):
        self.offset = offset

    # ============================
    # Status methods
    # ============================
    def isBitField(self):
        return self.bitField

    def isEnum(self):
        return dataElement.vartypeData.isEnum(self.varTypeStr)

    def isBool(self):
        return dataElement.vartypeData.isBool(self.varTypeStr)

    def isStructOrUnion(self):
        if ((self.varTypeStr[:6] == "struct") or (self.varTypeStr[:5] == "union") or (self.structReference is not None)): return True
        else: return False

    def isQualifier(self):
        if ((self.varTypeStr[:8] == "volatile") or (self.varTypeStr[:6] == "static") or (self.varTypeStr[:5] == "const")): return True
        else: return False

    def isPointer(self):
        return dataElement.vartypeData.isPointer(self.varTypeStr)

    def isArray(self):
        if ((False == self.bitField) and (self.dimList is not None)): return True
        else: return False

    def isChar(self):
        return dataElement.vartypeData.isChar(self.varTypeStr)

    def isIntegerType(self):
        if ((self.structReference is not None) or (self.bitField) or (self.dimList is not None)):
            return False
        else:
            return dataElement.vartypeData.isIntegerType(self.varTypeStr)

    def isFloat(self):
        if ((self.structReference is not None) or (self.bitField) or (self.dimList is not None)):
            return False
        else:
            return dataElement.vartypeData.isFloatType(self.varTypeStr)

    def isSigned(self):
        if ((self.isStructOrUnion()) or \
            (self.bitField) or \
            (self.isEnum()) or \
            (self.isBool()) or \
            (self.isPointer()) or \
            (self.isQualifier()) ):
            return False
        else:
            return dataElement.vartypeData.isSigned(self.varTypeStr)

    def getDoc(self):
        return self.docStr

    # ============================
    # Get attribute methods
    # ============================
    def getSubstruct(self):
        return self.structReference

    def getName(self):
        return self.name

    def getSize(self):
        return self.totalSize

    def getOffset(self):
        return self.offset

    def getAlignmentSize(self):
        if (self.bitField): return self.totalSize
        else: return self.elementSize

    def getBitCount(self):
        return self.dimList[0]

    # ========================================================
    # ========================================================
    # Python Dictionary define generation utilities
    # ========================================================
    # ========================================================
    def getDescData(self):
        if (self.isSigned()): signed = 1
        else: signed = 0
        return self.name, self.elementSize, signed, 0, self.docStr, self.dimList

    # ========================================================
    # ========================================================
    # Pyton CType generation utilities
    # ========================================================
    # ========================================================
    def __getIntCtype(self, size):
        # c_intsize is the way TWIDL does it, which is why I didn't use c_int(size) initialization.
        # handle when size = 0, c_uint0 is not a ctype
        sizeSuffix = str(size*8)

        if (self.isSigned()):
            if (self.isChar()):
                if (self.elementSize == 1): ctypeName = "c_char"
                elif (self.elementSize == 2): ctypeName = "c_wchar"
                else: ctypeName = "c_int"+ sizeSuffix
            else: ctypeName = "c_int"+sizeSuffix
        else: ctypeName = "c_uint"+sizeSuffix
        return ctypeName

    def __getFloatCtype(self):
        if (dataElement.vartypeData.isDoubleDouble(self.varTypeStr)): ctypeName = "c_longdouble"
        elif (dataElement.vartypeData.isDouble(self.varTypeStr)): ctypeName = "c_double"
        else: ctypeName = "c_float"
        return ctypeName

    def __getBitfieldType(self):
        # handle when size = 0, c_uint0 is not a ctype
        sizeSuffix = str(self.totalSize*8)

        ctypeName = "c_uint"+ sizeSuffix
        ctypeName += ","
        ctypeName += str(self.dimList[0])
        return ctypeName

    def __getStructCType(self):
        if (self.structReference is not None):
            ctypeName = self.varTypeStr
            return ctypeName.replace(' ', '_')
        else:
            # handle when size = 0, c_uint0 is not a ctype
            sizeSuffix = str(self.elementSize*8)

            return "c_uint"+sizeSuffix

    def __getArrayCType(self):
        if (self.bitField):
            return self.__getBitfieldType()
        else:
            # handle when size = 0, c_uint0 is not a ctype and c_unint(0) is not accepted by twidl
            sizeSuffix = str(self.elementSize*8)

            if (self.isStructOrUnion()): ctypeName = self.__getStructCType()
            elif (self.isPointer() or self.isEnum()): ctypeName = "c_uint"+ sizeSuffix
            elif (self.isBool()): ctypeName = "c_uint"+ sizeSuffix
            elif (dataElement.vartypeData.isIntegerType(self.varTypeStr)): ctypeName = self.__getIntCtype(self.elementSize)
            elif (dataElement.vartypeData.isFloatType(self.varTypeStr)): ctypeName = self.__getFloatCtype()
            else: ctypeName = None

            # add the dimensions
            if ((len(self.dimList) >= 1) and (self.dimList[0] > 1)):
                for dim in self.dimList: ctypeName = format("(%s*%d)" % (ctypeName, dim))

            return ctypeName

    def getCtypeType(self):
        # @todo: handle when size = 0, c_uint0  is not a ctype and c_uint(0) is not twidl accepted
        sizeSuffix = str(self.totalSize*8)

        if (self.dimList is not None): ctypeName = self.__getArrayCType()
        elif (self.isStructOrUnion()): ctypeName = self.__getStructCType()
        elif (self.isIntegerType()):ctypeName = self.__getIntCtype(self.totalSize)
        elif (self.isFloat()): ctypeName = self.__getFloatCtype()
        elif (self.isPointer() or self.isEnum() or self.isBool()): ctypeName = "c_uint"+ sizeSuffix
        else: ctypeName = None

        return self.name, self.docStr, ctypeName

    # ========================================================
    # ========================================================
    # XML define generation utilities
    # ========================================================
    # ========================================================
    def __getXmlArrayType(self):
        if (self.isStructOrUnion()): xmlType = "struct"
        elif (self.isIntegerType()): xmlType = "eUint"
        elif (self.isFloat()): xmlType = "eFloat"
        elif (self.isPointer() or self.isEnum() or self.isBool()): xmlType = "eUint"
        else: xmlType = "eUint"  # defualt if nothing else
        return xmlType

    def __getXmlType(self):
        if (self.dimList is not None):
           if (self.bitField):
               xmlType = "bitfield:"+str(self.dimList[0])
               size = self.totalSize
           else:
               xmlType = self.__getXmlArrayType()+"_array"
               for dim in self.dimList:
                   xmlType+="["
                   xmlType+=str(dim)
                   xmlType+="]"
                   size = self.elementSize
        elif (self.isStructOrUnion()):
            xmlType = "struct"
            size = self.elementSize
        elif (self.isIntegerType()):
            xmlType = "eUint"
            size = self.elementSize
        elif (self.isFloat()):
            xmlType = "eFloat"
            size = self.elementSize
        elif (self.isPointer() or self.isEnum() or self.isBool()):
            xmlType = "eUint"
            size = self.elementSize
        else:
            xmlType = None
            size = 0
        return xmlType, size

    def getXmlData(self):
        xmlType, size = self.__getXmlType()
        return self.name, self.docStr, self.offset, size, xmlType



class structDef(object):
    """
    Container class for all cType Structure definition and some metadata
    """
    UNKNOWN_TYPE   = 0
    STRUCT_TYPE    = 1
    UNION_TYPE     = 2
    OBJECT_TYPE    = 3
    BITSTRUCT_TYPE = 4


    nameSeparator = "__"
    vartypeData = ghsCvarType()

    def __init__(self, name, typeName, majorVersion = 0, minorVersion = 0, docString = None, inline = True, uid = None):
        self.name = name
        self.structType = structDef.UNKNOWN_TYPE

        self.align = 4
        self.offset = 0
        self.alignCount = 0
        self.inline = inline

        if (typeName[:5] == "union"): self.structType = structDef.UNION_TYPE
        elif (typeName[:6] == "struct"): self.structType = structDef.STRUCT_TYPE
        elif (typeName == "object"): self.structType = structDef.OBJECT_TYPE
        else: print (format("Invalid structure type %s.  Expected struct or union.\n" % (typeName)))

        self.uid = uid
        self.majorVersion = majorVersion
        self.minorVersion = minorVersion
        self.description = docString
        self.members = [] # will be hold majority of ctype content
        self.structIndex = 0
        self.calcSize = 0
        return super(structDef, self).__init__()

    def __eq__(self, otherStruct):
        if ((otherStruct.name == self.name) and (otherStruct.structType == self.structType) and (otherStruct.calcSize == self.calcSize)): return True
        else: return False

    def __cmp__(self, otherStruct):
        if ((otherStruct.name == self.name) and (otherStruct.structType == self.structType) and (otherStruct.calcSize == self.calcSize)): return 0
        elif (otherStruct.name != self.name): return ( operator.eq(otherStruct.name, self.name) ) # @todo jdtarang cmp to -> operator.eq
        elif (otherStruct.structType < self.structType): return -1
        elif (otherStruct.structType > self.structType): return 1
        elif (otherStruct.calcSize < self.calcSize): return -1
        elif (otherStruct.calcSize > self.calcSize): return 1

    def __calcTotalSize(self, entrySize, dimList = None):
        byteCount = entrySize
        totalSize = entrySize
        if (dimList is not None):
            for dim in dimList: totalSize *= dim

        return byteCount, totalSize

    def __checkAlignment(self, memberSize):
        if(memberSize != 0):
            alignCheck = min(self.align, memberSize)
            adjustSize = self.offset % alignCheck
            if (adjustSize != 0): return alignCheck - adjustSize
            else: return 0
        else: return 0

    def __calcStructSize(self):
        byteCount = 0
        bitCount = 0
        offset = 0

        for member in self.members:
            # Make sure the sub struct is updated
            substruct = member.getSubstruct()
            if (substruct is not None):
                 substruct.__calcStructSize()
                 member.resetStructSize(substruct.getSize())

            # Set the member offset
            member.updateOffset(offset)

            # Now add member value
            if (self.structType == structDef.BITSTRUCT_TYPE):
                bitCount += member.getBitCount()
                byteCount = structDef.vartypeData.roundupBitCount(bitCount)
            elif (self.structType == structDef.UNION_TYPE):
                if (member.getSize() > byteCount): byteCount = member.getSize()
            elif ((self.structType == structDef.STRUCT_TYPE) or (self.structType == structDef.OBJECT_TYPE)):
                byteCount += member.getSize()
                offset += member.getSize()

        self.calcSize = byteCount

    def updateToBitField(self):
        if (self.structType == structDef.STRUCT_TYPE):
            # convert the members to bit type
            self.structType = structDef.BITSTRUCT_TYPE
            for memberEntry in self.members: memberEntry.updateToBitField()

            # recalculate the size
            self.__calcStructSize()

    def isPossibleBitStruct(self, unionIntSize):
        if ((self.structType == structDef.STRUCT_TYPE) and (len(self.members) > 1)):
            # One more check, verify that the union type matches the struct bitfield types
            membersMatchCount = 0
            structSize = 0
            memberSize = 0
            enumSize = structDef.vartypeData.getEnumSize()

            for memberEntry in self.members:
                if (((memberEntry.isEnum()) and (enumSize == unionIntSize)) or (memberEntry.isBool()) or (unionIntSize == memberEntry.getSize())):
                    membersMatchCount += 1

                memberSize += memberEntry.getSize()

            if (memberSize > unionIntSize): return True  # Ok, must be bit field struct
            elif (membersMatchCount == len(self.members)): return True  # Ok, must be bit field struct
            else: return False
        else: return False

    def __checkForPossibleBitUnion(self):
        if ((self.structType == structDef.UNION_TYPE) and (len(self.members) == 2)):
            # possible missed bitfield, test if the first is a structure and second is not a structure
            possibleBitStruct = self.members[0].getSubstruct()
            if ((possibleBitStruct is not None) and (self.members[1].isIntegerType())):
                    # Possible bit struct/union
                    unionIntSize = self.members[1].getSize()
                    if (possibleBitStruct.isPossibleBitStruct(unionIntSize)):
                        possibleBitStruct.updateToBitField()
                        self.members[0].resetStructSize(possibleBitStruct.getSize())

    def __createMemberEntry(self, name, varTypeStr, docString = None, dimList = None, bitField = False, subStruct = None):
        if (subStruct is not None):
            return dataElement(name, varTypeStr, docString, dimList, False, subStruct, self.offset)
        elif ((bitField == True) or (self.structType == structDef.BITSTRUCT_TYPE)):
        #elif (bitField == True):
            #was turning all children of bitfieldstruct type to automatic bitfield, even though this is not always the case
            #self.updateToBitField()
            return dataElement(name, varTypeStr, docString, dimList, True, subStruct, 0)
        else:
            return dataElement(name, varTypeStr, docString, dimList, False, None, self.offset)

    def __createAlignmentMember(self, alignmentAdjust):
        self.alignCount += 1
        alignmentMember = self.__createMemberEntry("alignment__N"+str(self.alignCount), structDef.vartypeData.getByteStr(), "Structure alignment", [alignmentAdjust], False, None)
        self.members.append(alignmentMember)
        self.offset += alignmentAdjust

    def addMember(self, name, varTypeStr, docString = None, dimList = None, bitField = False, subStruct = None):
        newMember = self.__createMemberEntry(name, varTypeStr, docString, dimList, bitField, subStruct)
        alignmentAdjust = self.__checkAlignment(newMember.getAlignmentSize())

        if (alignmentAdjust != 0):
            self.__createAlignmentMember(alignmentAdjust)
            newMember.updateOffset(self.offset)

        self.members.append(newMember)
        self.offset += newMember.getSize()

    def finalizeStruct(self):
        self.__checkForPossibleBitUnion()
        self.__calcStructSize()

        # Add structure pad
        endPad = self.__checkAlignment(self.calcSize)
        if ((0 != endPad) and (self.structType != structDef.BITSTRUCT_TYPE)):
            self.__createAlignmentMember(endPad)
            self.calcSize += endPad

    def addDoc(self, docstring):
        self.members[-1].addDocStr(docstring)

    def setName(self, name):
        self.name = name

    def setUid(self, uid):
        self.uid = None

    def setDescription(self, description):
        self.description = stripCommentBlocking(description)

    def setMajorVersion(self, majorVersion):
        self.majorVersion = majorVersion

    def setMinorVersion(self, minorVersion):
        self.minorVersion = minorVersion

    def setNoInline(self):
        self.inline = False

    def getName(self):
        return self.name

    def getMajorVersion(self):
        return self.majorVersion

    def getMinorVersion(self):
        return self.minorVersion

    def getStructType(self):
        return self.structType

    def getUid(self):
        return self.uid

    def getMemberList(self):
        return self.members

    def isBitFieldType(self):
        if (self.structType == structDef.BITSTRUCT_TYPE): return True
        else: return False

    def isInline(self):
        return self.inline

    def getTwidlType(self):
        if (self.structType == structDef.STRUCT_TYPE): return "struct"
        elif (self.structType == structDef.UNION_TYPE): return "union"
        elif (self.structType == structDef.OBJECT_TYPE): return "struct"
        elif (self.structType == structDef.BITSTRUCT_TYPE): return "struct"
        else: return "unknown"

    def getType(self):
        if (self.structType == structDef.STRUCT_TYPE): return "struct"
        elif (self.structType == structDef.UNION_TYPE): return "union"
        elif (self.structType == structDef.OBJECT_TYPE): return "object"
        elif (self.structType == structDef.BITSTRUCT_TYPE): return "bitfieldstruct"
        else: return "unknown"

    def getSize(self):
        if(self.structType == structDef.BITSTRUCT_TYPE): return 0  #return 0 and let the other half of the union carry the day
        return self.calcSize

    def getDisplaySize(self):
        return self.calcSize

    def getDefaultSubstructName(self, structType):
        self.structIndex += 1
        return self.name+"_"+structType+structDef.nameSeparator+"X"+str(self.structIndex)

    def getDefaultMemberName(self):
        return "_"+self.name

class structDefList(object):
    """
    list of structures objects
    """
    def __init__(self):
        self.structList = []

    def cleanList(self):
        del self.structList[0:]

    def createStruct(self, name, typeName, majorVersion = 0, minorVersion = 0, docString = None, inline = True):
        newobj = structDef(name, typeName, majorVersion, minorVersion, docString, inline)
        self.structList.append(newobj)
        return newobj

    def debugPrint(self):
        for structDataDef in self.structList:
            print (format("Definition: %s %s, size: %d" % (structDataDef.getType(), structDataDef.getName(), structDataDef.getDisplaySize())))

    def findStruct(self, structName):
        foundStruct = None
        if (structName is not None):
            for possibleMatch in self.structList:
                if (possibleMatch.getName() == structName):
                    foundStruct =  possibleMatch
                    break

        return foundStruct

    def removeDuplicateStructures(self):
        current = 0
        listLen = len(self.structList)

        while (current < listLen):
            dupCheck = current + 1

            # go through the rest of the list
            while (dupCheck < listLen):
                if (self.structList[current] == self.structList[dupCheck]):
                    self.structList[current].setNoInline()
                    self.structList.pop(dupCheck)
                    listLen = len(self.structList)
                dupCheck += 1

            current += 1

    def updateStuctData(self):
        for updateStruct in self.structList:
            updateStruct.finalizeStruct()

class ctypedefList(object):
    """
    Typedef list
    """
    def __init__(self):
        self.typedefList = []

    def cleanList(self):
        del self.typedefList[0:]

    def addTypedef(self, identifier, value):
        newEntry = {'id': identifier, 'type': value}
        self.typedefList.append(newEntry)

    def isTypedef(self, token):
        typeValue = None
        for entry in self.typedefList:
            if (token == entry('id')):
                typeValue = entry('type')
                break
        return typeValue

class defineList(object):
    """
    #define object list
    """
    def __init__(self):
        self.defines = []

    def cleanList(self):
        del self.defines[0:]

    def addDefine(self, identifier, valueStr):
        newEntry = {'id': identifier, 'defineStr': valueStr}
        self.defines.append(newEntry)

    def isDefine(self, token):
        returnVal = None
        for entry in self.defines:
            if (token == entry('id')):
                returnVal = entry['defineStr']

        return returnVal

class enumValueList(object):
    def __init__(self):
        self.enumValues = []
        self.currentValue = 0

    def cleanList(self):
        del self.enumValues[0:]

    def addEnumEntry(self, identifier, value = None):
        if(value != None): self.currentValue = value
        newEntry = {'id': identifier, 'enumValue': self.currentValue}
        self.enumValues.append(newEntry)
        self.currentValue += 1

    def getEnumEntry(self, identifier):
        enumValue = None
        for entry in self.enumValues:
            if(entry['id'] == identifier):
                enumValue = entry['enumValue']
                break
        return enumValue

class enumList(object):
    """
    enum object list
    """
    def __init__(self):
        self.enumList = []

    def cleanList(self):
        del self.enumList[0:]

    def addEnumName(self, name):
        self.enumList.append(name)

    def isEnum(self, token):
        returnVal = False
        for name in self.enumList:
            if (token == name):
                returnVal = True

        return returnVal


class objectDefine(object):
    """
    ctypeAutoGen_Object definition
    """
    def __init__(self, objName, majorVersion = 0, minorVersion = 0, uid = 0):
        self.objectStartName = objName
        self.structIndex = 0
        self.majorVersion = majorVersion
        self.minorVersion = minorVersion
        self.objStruct = None
        self.size = 0
        self.uid = uid

    def getDefaultSubstructName(self, structType):
        self.structIndex += 1
        # got rid of :: because causing Namespace Error in ctype twidl generation (ex, uid 16)
        #return self.objectStartName+"_"+structType+"::R"+str(self.structIndex)
        return self.objectStartName

    def setSize(self, size):
        self.size = size

    def setMajorVersion(self, version):
        self.majorVersion = version

    def setMinorVersion(self, version):
        self.minorVersion = version

    def setUid(self, uid):
        self.uid = uid

    def getName(self):
        return self.objectStartName

    def getCapName(self):
        retStr = self.objectStartName
        retStr[0].capitalize
        return retStr

    def getSize(self):
        return self.size

    def getMajorVersion(self):
        return self.majorVersion

    def getMinorVersion(self):
        return self.minorVersion

    def getUid(self):
        return self.uid

    def setObjStruct(self, structObject):
        self.objStruct = structObject
        self.objStruct.setNoInline()

    def getObjStruct(self):
        return self.objStruct

class ctypedef(object):
    def __init__(self, name):
        self.name = name

    def getName(self):
        return self.name

class outputGenerationHelper(object):
    def __init__(self):
        return super(outputGenerationHelper, self).__init__()

    def capFirstLetter(self, name):
        capName = name[0:1].capitalize() + name[1:]
        return capName

    def convertToCamelCase(self, name1, name2):
        camelName = name1 + self.capFirstLetter(name2)
        return camelName

    def isSpecialName(self, name):
        if ((name == "reserved") or (name == "rsvd") or (name[:12]== "alignment__N")): return True
        else: return False



