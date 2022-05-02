#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Randal Eike, Joseph Tarango
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
# General Python module imports


class varType(object):
    def __init__(self, compileBaseSize = 32, pointerModifier = "*", typeDict = None, boolSize = None, enumSize = None, charSize = None):
        self.ptrModifier = pointerModifier

        # Initialize the lists
        self.varTypeList = []
        self.intTypeList = []
        self.modifierList = []

        # Initialize the comparison data
        if (typeDict is not None):
            # Load the lists
            for type, entryData in typeDict.items():
                if (type == 'modifierList'):
                    for modifier in entryData:
                        self.varTypeList.append(modifier)
                        self.modifierList.append(modifier)
                elif (type == 'integerAlias'):
                    for alias in entryData:
                        self.varTypeList.append(alias)
                        self.intTypeList.append(alias)
                else:
                    self.varTypeList.append(entryData)
                    if ((type != 'floatType') and (type != 'doubleType')): self.intTypeList.append(entryData)

            self.longMod      = typeDict['longMod']
            self.shortMod     = typeDict['shortMod']
            self.charName     = typeDict['charType']
            self.intName      = typeDict['integerType']
            self.integerAlias = typeDict['integerAlias']
            self.signedType   = typeDict['signedType']
            self.unsignedType = typeDict['unsignedType']
            self.floatType    = typeDict['floatType']
            self.doubleType   = typeDict['doubleType']
            self.boolType     = typeDict['boolType']
            self.enumType     = typeDict['enumType']
        else:
            self.longMod      = "long"
            self.shortMod     = "short"
            self.charName     = "char"
            self.intName      = "integer"
            self.integerAlias = None
            self.signedType   = "signed"
            self.unsignedType = "unsigned"
            self.floatType    = "float"
            self.doubleType   = "double"
            self.boolType     = "bool"
            self.enumType     = None

        if(self.enumType is not None): self.enumStrLen = len(self.enumType)
        else: self.enumStrLen = 0

        if (compileBaseSize >= 32):
            self.baseIntegerSize = compileBaseSize/8
            self.longIntegerSize = self.baseIntegerSize
            self.longLongIntegerSize = self.longIntegerSize * 2
            self.shortIntegerSize = self.baseIntegerSize / 2
            self.pointerSize = self.baseIntegerSize
            self.floatSize = self.baseIntegerSize
            self.doubleSize = self.floatSize * 2
            self.doubleDoubleSize = self.doubleSize * 2
        else:
            self.baseIntegerSize = 2
            self.longIntegerSize = self.baseIntegerSize * 2
            self.longLongIntegerSize = self.longIntegerSize * 2
            self.shortIntegerSize = self.baseIntegerSize
            self.pointerSize = self.baseIntegerSize
            self.floatSize = self.baseIntegerSize
            self.doubleSize = self.floatSize * 2
            self.doubleDoubleSize = self.doubleSize

        if (enumSize is None): self.enumSize = self.baseIntegerSize
        else: self.enumSize = enumSize

        if (boolSize is None): self.boolSize = self.baseIntegerSize
        else: self.boolSize = boolSize

        if (charSize is None): self.charSize = 1
        else: self.charSize = charSize

        self.longCharSize = self.charSize * 2
        if (charSize > 1):
            self.shortCharSize = self.charSize / 2
            self.byteType = self.unsignedType+" "+self.shortMod+" "+self.charName
        else:
            self.shortCharSize = 1
            self.byteType = self.unsignedType+" "+self.charName

    def __countModifiers(self, searchMod, varTypeStr):
        searchIndex = 0
        foundCount = 0
        foundIndex = 0
        while (foundIndex != -1):
            foundIndex = varTypeStr[searchIndex:].find(searchMod)
            if (foundIndex != -1):
                foundCount += 1
                searchIndex += (foundIndex + len(searchMod))
        return foundCount

    def roundupBitCount(self, bitCount):
        baseBitSize = self.baseIntegerSize * 8
        factor = (bitCount + (baseBitSize - 1)) / baseBitSize
        return self.baseIntegerSize * factor

    def getVarTypeList(self):
        return self.varTypeList

    def isVarTypeToken(self, testToken):
        if (testToken in self.varTypeList): return True
        else: return False

    def isIntegerKeyWord(self, keyWord):
        if (keyWord in self.intTypeList): return True
        else: return False

    def isPointer(self, varTypeStr):
        if (-1 != varTypeStr.find(self.ptrModifier)): return True
        else: return False

    def isBool(self, varTypeStr):
        if (self.boolType is not None):
            if (varTypeStr == self.boolType): return True
            else: return False
        else: return False

    def isEnum(self, varTypeStr):
        if (self.enumType is not None):
            if (varTypeStr[:self.enumStrLen] == self.enumType): return True
            else: return False
        else: return False

    def isSigned(self, varTypeStr):
        if (self.unsignedType is not None):
            if (-1 != varTypeStr.find(self.unsignedType)): return False
            else: return True
        else: return True

    def isChar(self, varTypeStr):
        if (varTypeStr == self.charName): return True
        else: return False

    def isSignedChar(self, varTypeStr):
        if ((-1 != varTypeStr.find(self.charName)) and \
            (-1 == varTypeStr.find(self.longMod)) and \
            (-1 == varTypeStr.find(self.shortMod)) and \
            ((-1 != varTypeStr.find(self.unsignedType)) or (-1 != varTypeStr.find(self.signedType)))):
            return True
        else:
            return False

    def isLongChar(self, varTypeStr):
        if ((-1 != varTypeStr.find(self.charName)) and (-1 != varTypeStr.find(self.longMod))): return True
        else: return False

    def isShortChar(self, varTypeStr):
        if ((-1 != varTypeStr.find(self.charName)) and (-1 != varTypeStr.find(self.shortMod))): return True
        else: return False

    def isInteger(self, varTypeStr):
        aliasIndex = -1
        if (self.integerAlias is not None):
            for intAlias in self.integerAlias:
                aliasIndex = varTypeStr.find(intAlias)
                if(-1 != aliasIndex): break

        if ((-1 != aliasIndex) or (-1 != varTypeStr.find(self.intName)) or ((varTypeStr == self.unsignedType))): return True
        else: return False

    def isShort(self, varTypeStr):
        shortCount = self.__countModifiers(self.shortMod, varTypeStr)
        if (1 == shortCount): return True
        else: return False

    def isShortShort(self, varTypeStr):
        shortCount = self.__countModifiers(self.shortMod, varTypeStr)
        if (2 == shortCount): return True
        else: return False

    def isLong(self, varTypeStr):
        longCount = self.__countModifiers(self.longMod, varTypeStr)
        if (1 == longCount): return True
        else: return False

    def isLongLong(self, varTypeStr):
        longCount = self.__countModifiers(self.longMod, varTypeStr)
        if (2 == longCount): return True
        else: return False

    def isFloat(self, varTypeStr):
        floatIndex = varTypeStr.find(self.floatType)
        doubleIndex = varTypeStr.find(self.doubleType)
        if ((-1 != floatIndex) and (-1 == doubleIndex)): return True
        else: return False

    def isDouble(self, varTypeStr):
        longCount = self.__countModifiers(self.longMod, varTypeStr)
        floatIndex = varTypeStr.find(self.floatType)
        doubleIndex = varTypeStr.find(self.doubleType)
        if (((-1 != doubleIndex) and (0 == longCount)) or ((-1 != floatIndex) and (1 == longCount))): return True
        else: return False

    def isDoubleDouble(self, varTypeStr):
        longCount = self.__countModifiers(self.longMod, varTypeStr)
        doubleIndex = varTypeStr.find(self.doubleType)
        if ((-1 != doubleIndex) and (1 == longCount)): return True
        else: return False

    def isFloatType(self, varTypeStr):
        floatIndex = varTypeStr.find(self.floatType)
        doubleIndex = varTypeStr.find(self.doubleType)
        if ((-1 != floatIndex) or (-1 != doubleIndex)): return True
        else: return False

    def isIntegerOrModifierKeyWord(self, keyWord):
        if (self.isIntegerKeyWord(keyWord) or (keyWord in self.modifierList)): return True
        else: return False

    def isIntegerOrModifierVarType(self, varTypeStr):
        retVal = True
        varTypeList = varTypeStr.split(" ")

        for keyWord in varTypeList:
            if (False == self.isIntegerOrModifierKeyWord(keyWord)):
                retVal = False
                break
        return retVal

    def isIntegerType(self, varTypeStr):
        if (self.isPointer(varTypeStr)): return False
        elif (self.isBool(varTypeStr)): return False
        elif (self.isEnum(varTypeStr)): return False
        elif (self.isFloatType(varTypeStr)): return False
        elif (self.isIntegerOrModifierVarType(varTypeStr)): return True
        else: return False

    def isStruct(self, varTypeStr):
        if (varTypeStr[:6] == "struct"):
            return True
        return False

    def isUnion(self, varTypeStr):
        if (varTypeStr[:5] == "union"):
            return True
        return False

    def getSize(self, varTypeStr):
        if   (self.isPointer(varTypeStr)):      byteCount = self.pointerSize
        elif (self.isBool(varTypeStr)):         byteCount = self.boolSize
        elif (self.isEnum(varTypeStr)):         byteCount = self.enumSize
        elif (self.isLongLong(varTypeStr)):     byteCount = self.longLongIntegerSize
        elif (self.isShortShort(varTypeStr)):   byteCount = self.shortIntegerSize
        elif (self.isShort(varTypeStr)):        byteCount = self.shortIntegerSize
        elif (self.isLong(varTypeStr)):         byteCount = self.longIntegerSize
        elif (self.isLongChar(varTypeStr)):     byteCount = self.longCharSize
        elif (self.isShortChar(varTypeStr)):    byteCount = self.ShortCharSize
        elif (self.isChar(varTypeStr)):         byteCount = self.charSize
        elif (self.isSignedChar(varTypeStr)):   byteCount = self.charSize
        elif (self.isInteger(varTypeStr)):      byteCount = self.baseIntegerSize
        elif (self.isDouble(varTypeStr)):       byteCount = self.doubleSize
        elif (self.isDoubleDouble(varTypeStr)): byteCount = self.doubleDoubleSize
        elif (self.isFloat(varTypeStr)):        byteCount = self.floatSize
        elif (self.isStruct(varTypeStr) or self.isUnion(varTypeStr)): byteCount = self.getBaseSize()         #base size, allows for multiplication based on substructure, bitfield sizes
        else:
            print("warning: unknown Type: %s" %varTypeStr)
            byteCount = 0

        return byteCount

    def getByteStr(self):
        return self.byteType

    def getEnumSize(self):
        return self.enumSize

    def getBaseSize(self):
        return self.baseIntegerSize


cvarTypeDictionary = {'signedType': "signed",
                      'unsignedType': "unsigned",
                      'charType': "char",
                      'integerType': "int",
                      'shortMod': "short",
                      'longMod': "long",
                      'floatType': "float",
                      'doubleType': "double",
                      'boolType': "bool",
                      'voidType': "void",
                      'enumType': "enum",
                      'integerAlias': ["integer"],
                      'modifierList' : ["const", "volatile", "static"]
                     }

class ghsCvarType(varType):
    def __init__(self):
        return super(ghsCvarType, self).__init__(compileBaseSize = 32, pointerModifier = "*", typeDict = cvarTypeDictionary, boolSize = 1, enumSize = 4, charSize = 1)
