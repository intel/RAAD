#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
# General Python module imports
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import re

# Token objects
from src.software.parse.autoObjects import structDef
from src.software.parse.autoObjects import structDefList
from src.software.parse.autoObjects import objectDefine
from src.software.parse.autoObjects import ctypedef

from src.software.parse.parserSrcUtil import fileTokenizer
from src.software.parse.parserSrcUtil import parserHelper

from src.software.parse.varType import ghsCvarType
import math


class structdefTokenizer(fileTokenizer):
    """
    Tokenize structure definition file
    """

    def __init__(self):
        operatorList = ["=", "<", ">", "+", "-", "/", "%", "*", "^", "&", "|", "~", "!", ",", ".", ":", "::"]
        delimiterList = [';', '[', ']', '(', ')', '{', '}']
        stringOperatorList = ["\"", "\'"]
        slCommentStartList = ["//"]
        mlCommentStartList = ["/*"]
        mlCommentEnd = "*/"
        continuationCharacter = '\\'
        return super(structdefTokenizer, self).__init__(operatorList, delimiterList, stringOperatorList, slCommentStartList, mlCommentStartList, mlCommentEnd, continuationCharacter, True)


class structdefParser(parserHelper):
    """
    Parse structure definition file
    """

    KeyWordList = ["struct", "union", "ObjectBegin", "ObjectEnd", "_LINES", "const", "static", "volatile"]
    OperatorList = ["=", "<", ">", "+", "-", "/", "%", "*", "^", "&", "|", "~", "!", ",", ".", "::"]
    objectList = []
    structList = structDefList()
    structLevel = 0
    defaultNameCounter = 0

    def __init__(self):
        self.lines = None
        self.currentObject = None
        self.globalObject = objectDefine("global", 1, 0)

        self.varTypeParser = ghsCvarType()

        keywordList = structdefParser.KeyWordList
        keywordList.extend(self.varTypeParser.getVarTypeList())
        tokenizer = structdefTokenizer()
        return super(structdefParser, self).__init__(tokenizer, keywordList, structdefParser.OperatorList)

    def __processValue(self, varName, endToken=None):
        startToken = self.currentToken

        # next token should be the value
        self.getNextToken()
        value = self.getValue(self.currentToken)

        if (endToken is not None):
            # Next token should be the end
            self.getNextToken()
            if (self.currentToken != endToken): self.parseError("Invalid input for %s expected numeric value after %s", (varName, startToken))

        return value

    def __isTypedef(self):
        # No typedef in structdef
        return False

    def __isDefine(self):
        # No define in structdef
        return False

    # =====================================================================
    # =====================================================================
    # Variable/Structure member processing functions
    # =====================================================================
    # =====================================================================
    def __isVarTypeKeyWord(self):
        if (self.varTypeParser.isVarTypeToken(self.currentToken)):
            return True
        else:
            return False

    def __processEnumSpecifier(self):
        varTypeStr = self.currentToken
        self.getNextToken()
        if (self.tokenType == parserHelper.IDENTIFIER_TOKEN):
            varTypeStr += ' '
            varTypeStr += self.currentToken
        else:
            self.parseError("Invalid variable type specification enum %s, expected enum followed by name", (self.currentToken))

        return varTypeStr

    def __processArrayIndex(self, varName):
        # get the dimension value
        dim = self.__processValue(varName, "]")
        if (dim is None): self.parseError("Invalid syntax expected numeric value after [")
        return dim

    def findStruct(self, structName):
        foundStruct = structdefParser.structList.findStruct(structName)
        return foundStruct

    # =====================================================================
    # =====================================================================
    # Structure processing functions
    # =====================================================================
    # =====================================================================
    def __getDefaultStructName(self, inputType, parentStruct):
        # when parentStruct is topmost struct, getDefaultsubstruct name causes error
        if (parentStruct is not None):
            structName = parentStruct.getDefaultSubstructName(inputType)
        elif (self.currentObject is not None):
            structName = self.currentObject.getDefaultSubstructName(inputType)
        else:
            structName = self.globalObject.getDefaultSubstructName(inputType)
        return structName

    def __isBitField(self, token):

        if (token == "([false..true])"):
            return True
        elif (token is not None) and re.search('(\s+)?\((\d+)(..)(\d+)\)', token):
            # If format is I.E. (0...123456) then we have a bitfield.
            return True
        elif ((token is not None) and (token == "('\\0'..'\\a')")):
            # If format is I.E ('\0'..'\a')
            return True
        else:
            return False

    def __calculateBits(self, intNum):
        return (math.log(intNum + 1, 2))

    def __calculateBitsPower(self, intNum):
        try:
            return (2 ** (int)(intNum))
        except TypeError:
            self.parseError("Did not identify intNum err.")

    def __isStruct(self):
        if (self.currentToken == "struct"):
            return True
        else:
            return False

    def __isUnion(self):
        if (self.currentToken == "union"):
            return True
        else:
            return False

    def __processBitField(self, parrentStruct=None):
        boolField = False
        errField = False
        bitDimention = None
        workingToken = self.currentToken

        # possible bit field
        if ((self.tokenType == parserHelper.DELIMITER_TOKEN) and (self.currentToken == "(")):
            self.getNextToken()
            workingToken += self.currentToken

            # handle if its a [
            if ((self.tokenType == parserHelper.DELIMITER_TOKEN) and (self.currentToken == "[")):
                boolField = True
                # Get to the end
                while ((self.currentToken != ']') and (self.continueParse())):
                    self.getNextToken()
                    workingToken += self.currentToken

            # if should end regardless
            while ((self.currentToken != ')') and (self.continueParse())):
                self.getNextToken()
                workingToken += self.currentToken

            # @todo: temporary fix for   ('\0'..'\a'), should report to GHS
            if (workingToken == "('\\0'..'\\a')"):
                # make sure entry and exit tokens are different
                errField = True

            # Now we have the whole string, check if it is correct
            if (self.__isBitField(workingToken)):
                numToken = workingToken[4:-1]
                # @todo: why is parent of bitfield also a bitfield
                # if (parrentStruct is not None): parrentStruct.updateToBitField()
                if (boolField):
                    workingToken = "unsigned int"
                    bitDimention = 1
                elif (errField):
                    workingToken = "unsigned int"
                    bitDimention = -1  # Flag to set bitDimention later when known
                else:
                    bitDimention = self.__calculateBits(int(numToken))
                    # @todo: signed or unsigned???, for now, unsigned default
                    workingToken = "unsigned int"

            else:
                self.parseError("Invalid boolean bit field specifier \"%s\", expected bitField format", (workingToken))
                workingToken = None

        return workingToken, bitDimention

    def __processIdentifier(self):
        identifierStr = None
        while (self.tokenType == parserHelper.IDENTIFIER_TOKEN):
            if (identifierStr is None):
                identifierStr = self.currentToken
            else:
                identifierStr += self.currentToken
            self.getNextToken()

            # C++ namespace identifier.
            if ((self.tokenType == parserHelper.OPERATOR_TOKEN) and (self.currentToken == "::")):
                # Add the decoration and get the next part of the name
                identifierStr += "_"
                self.getNextToken()
            elif ((self.tokenType == parserHelper.DELIMITER_TOKEN) and (self.currentToken == "::")):
                # Add the decoration and get the next part of the name
                identifierStr += "_"
                self.getNextToken()
            elif (self.currentToken == "::"):
                # Add the decoration and get the next part of the name
                identifierStr += "_"
                self.getNextToken()
            else:
                break
        return identifierStr

    def __getVarName(self, baseName=None):
        name = self.__processIdentifier()
        if (name is None):
            structdefParser.defaultNameCounter += 1
            name = "defaultName_N" + str(structdefParser.defaultNameCounter)

        if (baseName is not None):
            name = baseName + "_" + name
        return name

    def __getStructName(self, structType, parentStruct):
        structName = None
        if (self.currentToken == '{'):
            structName = self.__getDefaultStructName(structType, parentStruct)
        else:
            structName = self.__processIdentifier()
        return structName

    def __processInlineStruct(self, parentStruct=None, baseName=None):
        """
        Process "[struct | union] structname [{subStructMembers;}] [membername];"
        """
        # get the structure type
        self.getNextToken()
        if (self.__isStruct() or self.__isUnion()):
            # get the type from the token
            structType = self.currentToken
            self.getNextToken()
        else:
            # default to struct type
            structType = "struct"

        # get the structure name
        structName = self.__getStructName(structType, parentStruct)
        varTypeStr = structType + " " + structName

        # process the structure
        if (baseName is None): baseName = parentStruct.getDefaultMemberName()
        activeStruct = self.__processStruct(structType, structName, parentStruct, baseName)

        # get the end name and dimension
        varName, dimension, bitField = self.__processVarName(None, None)

        # return member data
        return varName, varTypeStr, dimension, activeStruct, structName

    def __processVarType(self, parentStruct=None, baseName=None):
        """
        Process <type | struct name | union name | enum name | [(false..true)]>[*] | (0..#) | ('\0'..'\a')
        """
        varTypeStr = None
        bitDimention = None
        pointerType = False
        subStruct = None

        # Test the type specification
        if ((self.tokenType == parserHelper.DELIMITER_TOKEN) and (self.currentToken == "(")):
            varTypeStr, bitDimention = self.__processBitField(parentStruct)
            self.getNextToken()  # move token to the var name

        elif (self.currentToken == "enum"):
            # enum, get the enum name
            varTypeStr = self.__processEnumSpecifier()
            self.getNextToken()  # move token to the var name

        elif (self.__isStruct() or self.__isUnion()):
            # Process struct or union definition
            structType = self.currentToken
            self.getNextToken()  # move to the struct name

            structName = self.__getStructName(structType, parentStruct)
            varTypeStr = structType + " " + structName

            # determine if we need to add a new struct node
            if (self.currentToken == '{'):
                # Process inline structure definition
                subStruct = self.__processStruct(structType, structName, parentStruct, baseName)
            else:
                # Process previous structure definition
                substruct = self.findStruct(structName)

        elif (self.__isVarTypeKeyWord()):
            # generic type specifier
            varTypeStr = self.currentToken
            self.getNextToken()

            # keep pulling until it's not a vartype keyword
            while ((self.tokenType == parserHelper.KEYWORD_TOKEN) and (self.continueParse())):
                varTypeStr += ' '
                varTypeStr += self.currentToken
                self.getNextToken()

            # Case for Function Pointers: bool (*pMoreProcRetState)();
            if (self.currentToken == '('):
                # Keep pulling until it's not a vartype keyword
                flaskTypeStr = ''
                varStrName = ''
                while (self.currentToken == '(' or self.currentToken == '*' or self.currentToken == ')'):
                    flaskTypeStr += self.currentToken
                    if (self.currentToken == '*'):
                        varTypeStr = "void *"  # all pointers are treated as void*
                        pointerType = True
                    self.getNextToken()
                # Get the name
                varStrName = self.currentToken
                # Remove next invalid term.
                oracleTokenType, oracleCurrentToken = self.getIgnoreToken()  # Move the current item and ignore moving current to previous
                # Magic Prediction
                oracleTokenType, oracleCurrentToken = self.getPreviewToken()  # See what is next to be evaluated.
                if (oracleCurrentToken == '(' or oracleCurrentToken == ')'):
                    self.getIgnoreToken()  # Move the current item and ignore moving current to previous
                    oracleTokenType, oracleCurrentToken = self.getPreviewToken()  # See what is next to be evaluated.
                if (oracleCurrentToken == ')'):
                    self.getIgnoreToken()  # Move the current item and ignore moving current to previous
                    oracleTokenType, oracleCurrentToken = self.getPreviewToken()  # See what is next to be evaluated.
            elif (self.currentToken == ':'):
                oracleTokenType, oracleCurrentToken = self.getPreviewToken()  # See what is next to be evaluated.
                if (oracleCurrentToken == ':'):
                    self.getIgnoreToken()  # Move the current item and ignore moving current to previous
                    self.getIgnoreToken()  # Move the current item and ignore moving current to previous
        else:
            # Invalid type
            self.parseError("Invalid variable type specification %s", (varTypeStr))

        # check for pointer modifier
        if ((self.tokenType == parserHelper.OPERATOR_TOKEN) and (self.continueParse())):
            if (self.currentToken == '*'):
                # it is, get the next token which should be the var name
                if (bitDimention is not None):
                    self.parseError("Invalid variable type specification %s%s * operator not allowed", (varTypeStr, self.currentToken))
                else:
                    varTypeStr = "void *"  # all pointers are treated as void*
                    pointerType = True
                    self.getNextToken()
            else:
                self.parseError("Invalid variable type specification %s%s only * operator allowed", (varTypeStr, self.currentToken))

        # this token should be an identifier
        if (self.tokenType == parserHelper.IDENTIFIER_TOKEN):
            # If ('\0'..'\a'), redefine bitDimention
            if (bitDimention == -1):  # -1 is flag value for ('\0'..'\a') type
                print(self.previousToken, self.currentToken)  # @andrea
                while ((self.previousToken != ":") and (self.continueParse())):
                    self.getNextToken()
                    bitDimention = self.__calculateBitsPower(self.currentToken)
                    print("FOUND BITDIMENTION", bitDimention)  # @andrea

            # Good data
            return varTypeStr, bitDimention, pointerType, subStruct
        elif (self.tokenType == parserHelper.DELIMITER_TOKEN):
            if ((self.previousToken == '}') and (self.currentToken == ';')):
                # Good data, unnamed inline struct
                return varTypeStr, bitDimention, pointerType, subStruct
            else:
                self.parseError("Invalid variable type syntax %s %s expected variable name", (varTypeStr, self.currentToken))
                return None, None, False, None
        else:
            self.parseError("Invalid variable type syntax %s %s expected variable name", (varTypeStr, self.currentToken))
            return None, None, False, None

    def __processVarDimension(self, varName, bitDimention):
        # holds bitfield size or type array size
        if (bitDimention is not None):
            bitVar = True
            dimensionList = []
            dimensionList.append(bitDimention)
        else:
            bitVar = False
            dimensionList = None

        # determine if the name is followed by array or bit field
        if (self.currentToken == ":"):
            # bit field, read the next token.  It should be the dimension
            dim = self.__processValue(varName, ';')
            bitVar = True
            if (dim is not None):
                if (dimensionList is None):
                    dimensionList = []
                else:
                    del dimensionList[0:]
                dimensionList.append(dim)
            else:
                self.parseError("Invalid bit dimension %s expected number after %s:", (self.currentToken, varName))

        elif (self.currentToken == "["):
            # array field, read the next token.  It should be the dimension
            if (dimensionList is None): dimensionList = []

            while ((self.currentToken != ';') and (self.currentToken == "[") and (self.continueParse())):
                dim = self.__processArrayIndex(varName)
                self.getNextToken()
                if (dim is not None): dimensionList.append(dim)

        elif (self.currentToken != ";"):
            self.parseError("Invalid declaration %s%s expected %s<: | [ | ;>", (varName, self.currentToken, varName))

        return dimensionList, bitVar

    def __processVarName(self, bitDimention=None, baseName=None):
        # @todo: change logic to keep regular names
        # #determines if default names needed, or name bases
        varName = self.__getVarName(baseName)
        if (varName is not None):
            if (structdefParser.structLevel > 0):
                dimensionList, bitVar = self.__processVarDimension(varName, bitDimention)
            else:
                # objects don't have a ;
                dimensionList = None
                bitVar = False
        else:
            dimensionList = None
            varName = None
            if bitDimention is not None:
                bitVar = True
            else:
                bitVar = False

        return varName, dimensionList, bitVar

    def __processStructMember(self, activeStruct, baseName):
        """
        Process vartype varname [<[] | :n>];
        """
        varName = None
        dimension = None
        bitFlag = False
        subStruct = None

        if (self.tokenType == parserHelper.KEYWORD_TOKEN):
            varTypeStr, bitDimention, pointerType, subStruct = self.__processVarType(activeStruct, baseName)
            varName, dimension, bitField = self.__processVarName(None, baseName)
            if (bitField or bitDimention): bitFlag = True

        elif (self.tokenType == parserHelper.DELIMITER_TOKEN):
            if (self.currentToken == "("):
                # Test for valid data
                isBitField, bitDimention = self.__processBitField()
                if (isBitField):
                    # Syntax good
                    varTypeStr = "unsigned int"
                    self.getNextToken()
                    varName, dimension, bitField = self.__processVarName(bitDimention, baseName)
                    bitFlag = True

            else:
                varName = None
                self.parseError("Invalid syntax in struct %s expected member declaration, got %s", (activeStruct.getName(), self.currentToken))

        elif (self.tokenType == parserHelper.IDENTIFIER_TOKEN):
            # process starting name
            startMemberName = self.currentToken
            self.getNextToken()

            if (self.currentToken == "="):
                # get the structure type
                varName, varTypeStr, dimension, subStruct, substructName = self.__processInlineStruct(activeStruct, startMemberName)
                if (varName is None): varName = startMemberName
                if (varName != startMemberName): self.parseError("Invalid syntax in struct %s member start name %s not equal end name %s", (activeStruct.getName(), startMemberName, varName))

            elif (self.currentToken == "::"):
                self.putToken()  # put the :: back
                self.putToken()  # put the start of the struct type name back
                # deal with inline struct type with no name
                varName, varTypeStr, dimension, subStruct, substructName = self.__processInlineStruct(activeStruct, baseName)
                varName = "struct_" + substructName  # create member name


        elif (self.tokenType == parserHelper.NUMERIC_TOKEN):
            # ignore the numbers at the start of the struct/union definitions
            varName = None
            self.parseWarning("Ignore numeric value %s at start of line", (self.currentToken))

        elif (self.tokenType == parserHelper.COMMENT_TOKEN):
            varName = None
            activeStruct.addDoc(self.currentToken)

        else:
            # Unexpected data
            self.parseError("Unexpected in struct %s, token = %s", (activeStruct.getName(), self.currentToken))

        # Add the new member
        if (varName is not None): activeStruct.addMember(varName, varTypeStr, None, dimension, bitFlag, subStruct)

    def __processStruct(self, inputType, inputName, parentStruct=None, baseName=None):
        """
        Process [{struct members;}] [name];
        """
        activeStructType = inputType
        activeStructName = inputName
        activeStruct = None

        # current token should be an open brace at this point
        if ((self.tokenType == parserHelper.DELIMITER_TOKEN) and (self.currentToken == '{')):
            if (parentStruct is None):
                inline = False
            else:
                inline = True
            activeStruct = structdefParser.structList.createStruct(activeStructName, activeStructType, 0, 0, None, inline)
            structdefParser.structLevel += 1
            self.getNextToken()

            # Parse the structure members until we hit the end of the struct
            while ((self.currentToken != "}") and (self.continueParse()) and (activeStruct is not None)):
                self.__processStructMember(activeStruct, baseName)
                self.getNextToken()

            # get the token after the closing brace
            if (self.currentToken == '}'):
                if (structdefParser.structLevel > 0): structdefParser.structLevel -= 1
                self.getNextToken()

        # else, not an open brace.  Must be just s struct declaration

        # found the end of the struct definition, clean up
        if (activeStruct is not None): activeStruct.finalizeStruct()
        return activeStruct

    # =====================================================================
    # =====================================================================
    # Object processing functions
    # =====================================================================
    # =====================================================================
    def __isObjectBegin(self):
        if (self.currentToken == "ObjectBegin"):
            return True
        else:
            return False

    def __isObjectEnd(self):
        if (self.currentToken == "ObjectEnd"):
            return True
        else:
            return False

    def __isObjectEquate(self):
        if (self.currentToken == "==>"):
            return True
        else:
            return False

    def __processVersionData(self):
        versionNumber = 0
        self.getNextToken()

        # Next token should be =
        if ((self.tokenType == parserHelper.OPERATOR_TOKEN) and (self.currentToken == '=')):
            # next token is the version data
            self.getNextToken()
            if (self.isNumber(self.currentToken)):
                versionNumber = self.tokenNumericValue
            else:
                self.parseError("Invalid syntax %s expected object version value", (self.currentToken))
        return versionNumber

    def __processUidData(self):
        uid = 0
        self.getNextToken()

        # Next token should be =
        if ((self.tokenType == parserHelper.OPERATOR_TOKEN) and (self.currentToken == '=')):
            # next token is the uid data
            self.getNextToken()
            if (self.isNumber(self.currentToken)):
                uid = self.tokenNumericValue
            else:
                self.parseError("Invalid syntax %s expected object uid value", (self.currentToken))

        return uid

    def __processObjectBegin(self):
        self.getNextToken()
        if (self.__isObjectEquate()):
            self.getNextToken()
            if (self.tokenType == parserHelper.IDENTIFIER_TOKEN):
                # good syntax
                newObject = objectDefine(self.currentToken)
                return newObject, self.currentToken
            else:
                self.parseError("Invalid object identifier name ObjectBegin==>%s", (self.currentToken))
                return None, None
        else:
            self.parseError("Invalid syntax ObjectBegin%s, expected ObjectBegin==>", (self.currentToken))
            return None, None

    def __processObjectEnd(self, workingObject):
        returnStatus = False
        self.getNextToken()

        if (self.__isObjectEquate()):
            self.getNextToken()
            if (self.tokenType == parserHelper.IDENTIFIER_TOKEN):
                if (workingObject.getName() != self.currentToken):
                    self.parseError("Object identifier ObjectBegin==>%s not equal ObjectEnd==>%s", (workingObject.getName(), self.currentToken))
                else:
                    # good syntax
                    returnStatus = True
            else:
                self.parseError("Invalid object identifier name ObjectEnd==>%s", (self.currentToken))
        else:
            self.parseError("Invalid syntax ObjectEnd%s, expected ObjectEnd==>", (self.currentToken))

        return returnStatus

    def __processObjectSizeAndVersion(self, workingObject):
        while ((False == self.__isObjectEnd()) and (self.continueParse()) and (self.currentToken is not None)):
            if (self.tokenType == parserHelper.NUMERIC_TOKEN):
                # process size data
                if (self.isNumber(self.currentToken)):
                    workingObject.setSize(self.tokenNumericValue)
                else:
                    self.parseError("Invalid syntax %s expected object size value", (self.currentToken))
            elif (self.tokenType == parserHelper.IDENTIFIER_TOKEN):
                # process version data
                if (self.currentToken == "versionMajor"):
                    structVersion = self.__processVersionData()
                    workingObject.setMajorVersion(structVersion)
                elif (self.currentToken == "versionMinor"):
                    structVersion = self.__processVersionData()
                    workingObject.setMinorVersion(structVersion)
                elif (self.currentToken == "uid"):
                    uidVersion = self.__processUidData()
                    workingObject.setUid(uidVersion)
                elif (self.currentToken == "const" or self.currentToken == "static" or self.currentToken == "volatile"):
                    print("Debug: CONST-STATIC-VOLATILE TOKEN not supported.", self.currentToken)
                else:
                    self.parseError("Invalid syntax %s expected versionMajor or versionMinor", (self.currentToken))
            else:
                self.parseError("Invalid syntax %s expected versionMajor, versionMinor or object size", (self.currentToken))

            self.getNextToken()

    def __processObject(self):
        # Process the object start
        self.currentObject, objectName = self.__processObjectBegin()
        if (self.currentObject is not None):
            self.parseInformation("Parsing Object %s", (self.currentObject.getName()))

            # Process the struct data
            self.getNextToken()
            if ((self.tokenType == parserHelper.KEYWORD_TOKEN) and (self.__isStruct())):
                structType = self.currentToken
                self.getNextToken()
            else:
                structType = "struct"

            # Parse the object structure
            structName = self.__getStructName(structType, None)
            objStruct = self.__processStruct(structType, structName, None)
            endStructName = self.__getVarName(None)

            if (objStruct is not None):
                # Following the struct we should have the name again
                if (endStructName is not None): objStruct.setName(endStructName)
                self.currentObject.setObjStruct(objStruct)

            # Process the size and version data
            self.__processObjectSizeAndVersion(self.currentObject)

            # Next should be the object end
            if (self.__processObjectEnd(self.currentObject)):
                self.objectList.append(self.currentObject)

            self.parseInformation("Parsing Object %s complete Size: %d Version %d.%d", (self.currentObject.getName(), self.currentObject.getSize(), self.currentObject.getMajorVersion(), self.currentObject.getMinorVersion()))

        # Done with this object
        self.currentObject = None

    # =====================================================================
    # =====================================================================
    # _LINES processing function
    # =====================================================================
    # =====================================================================
    def __isLineCount(self):
        if (self.currentToken == "_LINES"):
            return True
        else:
            return False

    def __processLines(self):
        self.getNextToken()
        if (self.currentToken == '='):
            return self.__processValue("_LINES", None)
        else:
            self.parseError("Invalid _LINES syntax %s, expected _LINES=", (self.currentToken))
            return None

    # =====================================================================
    # =====================================================================
    # File processing function
    # =====================================================================
    # =====================================================================
    def parseDefFile(self, inputStream):
        # Reset the parser state
        del structdefParser.objectList[0:]
        structdefParser.structList.cleanList()
        self.currentObject = None
        self.resetParser()

        # Tokenize the input file
        inputStream.seek(0)
        self.tokenizer.parseStream(inputStream)

        # find the start of the data and ignore all the stuff at the top
        self.getNextToken()
        headerBlock = ""
        while ((self.currentToken is not None) and (self.currentToken != "{")):
            headerBlock += self.currentToken
            if (self.tokenType == parserHelper.IDENTIFIER_TOKEN): headerBlock += " "
            self.getNextToken()

        # Iterrate through the file
        while (self.currentToken is not None):
            # get the next token
            self.getNextToken()

            # Check the return type
            if (self.tokenType == parserHelper.KEYWORD_TOKEN):
                # process keywords
                if (self.__isObjectBegin()):
                    if (self.currentObject == None):
                        self.currentObject = self.__processObject()
                    else:
                        self.parseError("Cannot nest ObjectBegin within object %s", (self.currentObject.getName()))
                elif (self.__isLineCount()):
                    self.lines = self.__processLines()
                    self.parseInformation("Lines = %d", (self.lines))
                else:
                    self.parseError("Unexpected keyword %s, only ObjectBegin and _LINES expected", (self.currentToken))

            elif (self.tokenType == parserHelper.COMMENT_TOKEN):
                # Error, We don't do comments right now
                self.parseError("Detected comment %s outside structure", (self.currentToken))

            elif (self.tokenType == parserHelper.IDENTIFIER_TOKEN):
                # Error, We don't do comments right now
                self.parseError("Identifier %s outside of expected location", (self.currentToken))

            elif (self.tokenType == fileTokenizer.OPERATOR_TOKEN):
                # Error, this shouldn't happen
                self.parseError("Operator token %s outside expected range", (self.currentToken))

            elif (self.tokenType == parserHelper.END_OF_LIST):
                break

            else:
                # Error, this shouldn't happen
                self.parseError("Unknown syntax %s", (self.currentToken))

        return self.errorCount

    def CleanList(self):
        structdefParser.structList.removeDuplicateStructures()

    def GetObjectList(self):
        return structdefParser.objectList

    def GetStructList(self):
        return structdefParser.structList
