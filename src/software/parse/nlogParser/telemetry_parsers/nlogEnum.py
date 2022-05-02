#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors:Joseph Tarango, Randal Eike, Daniel Garces
# *****************************************************************************/

#### library includes
import sys, struct, re, os, time

#### import test utilities
from src.software.parse.nlogParser.test_util.output_log import OutputLog
from src.software.parse.nlogParser.telemetryutil.telemetry_util import BuildFileName


class nlogEnumTranslate(object):
    """
    Brief:
        nlogEnumTranslate() - Translate the format and parameters into enum name strings

    Description:
        Using the specified nlogEnumParser.py translate the format string into enum names as appropriate.

    Class(es):
        OutputLog

    Method(s):
        __init__(enumParserFile = None, inlineTriage = False)
        newFormatString, newParamsTuple enumParser(format, params)

    Related:

    Author(s):
        Matt Zweig - Methods taken from nlogpost2.py
        Randal Eike - Modified to use telemetry tools structures and added enum format id processing

    """
    enumFormatIdMarker = "%("
    enumFormatIdMarkerLen = len(enumFormatIdMarker)
    enumFormatIdEndMarker = ")"
    enumFormatIdEndMarkerLen = len(enumFormatIdEndMarker)

    def __getEnumParser(self, enumParserFile):
        """
        Import (read and execute) the NLog enums parser file into this script.  
        Stolen from nlogpost2.py enum detection and modified to deal with file loaction structure

        @param enumParserFile - Path and name of the nlogenumparser.py file

        @return enumParser - Nlog enum parser object
        """
        if (enumParserFile is None):
            # Try the default file name and location (current working directory)
            enumParserFile = BuildFileName('nlogEnumParser.py')

        # Get Format Strings
        try:
            # Use exec rather than import here.
            # Python maintains cached version of the imported files
            # that don't always get updated when the underlying file changes,
            # even if re-imported.
            myLocals = {}
            myGlobals = {}
            fileObj = open(enumParserFile)
            exec(fileObj.read(), myGlobals, myLocals)
            enumDictionary = myLocals
            fileObj.close()
            return enumDictionary

        except Exception as e:
            exec_type, exec_obj, exec_tb = sys.exc_info()
            OutputLog.DebugPrint(0, format("Couldn't load the enum parser file (%s): %s" % (enumParserFile, exec_type)))
            return None

    def __init__(self, enumParserFile = None):
        """
        Constructor

        @param enumParserFile - Path and name of the nlogenumparser.py file
        """
        self.enumDictionary = self.__getEnumParser(enumParserFile)

    def __enumMarkerReplace(self, format, params):
        """
        Add your nlog format to be parsed below. Make sure that when you add the
        enum-dict translation above, you create a the key as a decimal integer, and the value as a string.
        If you don't you'll get type errors

        @param format - Format string for the nlog message
        @param params - Message parameter value tuple

        @return string - String with enum values inserted
        """
        # Convert the params tuple to a list so we can do something with it
        paramList = []
        for paramdata in params:
            paramList.append(paramdata)

        # Initialize the search
        paramNumber = 0
        nextIndex = format.find("%")
        formatIndex = nextIndex
        newFormat = format[:nextIndex]

        # while more params to check
        while (nextIndex != -1):
            # Check if it's an enum marker
            if (format[formatIndex:formatIndex+nlogEnumTranslate.enumFormatIdMarkerLen] == nlogEnumTranslate.enumFormatIdMarker):
                # Found, get the enum id name
                enumEndIndex = format[formatIndex:].find(nlogEnumTranslate.enumFormatIdEndMarker)
                enumTableName = format[formatIndex+nlogEnumTranslate.enumFormatIdMarkerLen:formatIndex+enumEndIndex]

                # Update Param to the enum name string
                try:
                    enumName = self.enumDictionary[enumTableName][params[paramNumber]]
                    del paramList[paramNumber]

                    # Update the format and move to the next location
                    newFormat += enumName
                    formatIndex += (enumEndIndex + nlogEnumTranslate.enumFormatIdEndMarkerLen)
                except:
                    # Treat is as an integer
                    newFormat += "%d"

            elif (format[formatIndex+1] == "%"):
                # Double %, move on in the string
                while (format[formatIndex] == "%"):
                    newFormat += format[formatIndex]
                    formatIndex += 1
            else:
                # move on to the next parameter
                paramNumber += 1
                newFormat += format[formatIndex]
                formatIndex += 1

            # Find the next parameter
            nextIndex = format[formatIndex:].find("%")
            if (nextIndex != -1):
                newFormat += format[formatIndex:nextIndex+formatIndex]
                formatIndex += nextIndex
            else:
                newFormat += format[formatIndex:]
       
        # final step
        newFormat = newFormat.replace('"', '') #removes the quotes

        try:
            s = newFormat % tuple(paramList[0:])
        except TypeError:
            # Evaluation type error errorType, formatStr, params
            OutputLog.nlogFormatError(errorType="Eval TypeError", formatStr=format, params=params)
            s = None

        return s

    def __bruteForceReplace(self, format, params):
        '''
        Add your nlog format to be parsed below. Make sure that when you add the
        enum-dict translation above, you create a the key as a decimal integer, and the value as a string.
        If you don't you'll get type errors

        @param format - Format string for the nlog message
        @param params - Message parameter value tuple

        @return string - String with enum values inserted
        '''
        try:
            if (("PssDebugTrace" in format) and (len(params) == 1)):
                x = self.enumDictionary['pcie'][params[0]]
                s = format.replace('"', '') #removes the quotes
                s = s.replace('(%d)', x) #removes params
                s = s.replace('"', '')
            elif (("Npl_AdminCmdHandler: Received" in format) and ("AC_IDENTIFY" not in format) and (len(params) != 0)):
                x = self.enumDictionary['nvmeAdminCommands'][params[0]]
                s = format.replace('"', '') #removes the quotes
                s = s.replace('0x%x', x) #removes params 
                #s =  % params #put the params in
            elif (("init state is: (%d)" in format) and (len(params) == 1)):
                x = self.enumDictionary['transInitState_e'][params[0]] 
                s = format.replace('"', '')
                s = s.replace('(%d)', x)
                s = s.replace('"', '')
            elif (("Bis_SetTransportSubSystemState(): Changing PSS State" in format)  and (len(params) == 2)):
                x = self.enumDictionary['pssState_e'][params[0]]
                y = self.enumDictionary['pssState_e'][params[1]]
                s = format.replace('"', '')
                s = s.replace('(%d)', x)
                s = s.replace('%d', y)
                s = s.replace('"', '')
            else:
                s = format % params #put the params in

        except TypeError:
            # Enum type lookup error
            OutputLog.nlogFormatError("TypeError", format, params)
            s = format % params
        except KeyError:
            # Enum key lookup error
            try:
                s = format % params
            except TypeError:
                # Evaluation type error
                OutputLog.nlogFormatError("Eval TypeError", format, params)
                s = None
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            OutputLog.nlogFormatError(str(exc_type), format, params)
            s = None

        return s


    def enumParser(self, format, params): 
        '''
        Add your nlog format to be parsed below. Make sure that when you add the
        enum-dict translation above, you create a the key as a decimal integer, and the value as a string.
        If you don't you'll get type errors

        @param format - Format string for the nlog message
        @param params - Message parameter value tuple

        @return string - String with enum values inserted
        '''
        if (self.enumDictionary is not None):
            if (nlogEnumTranslate.enumFormatIdMarker in format):
                s = self.__enumMarkerReplace(format, params)
            else:
                try:
                    s = self.__bruteForceReplace(format, params)
                except TypeError:
                    # Enum type lookup error
                    OutputLog.nlogFormatError("TypeError", format, params)
                    s = format % params
                except KeyError:
                    # Enum key lookup error
                    try:
                        s = format % params
                    except TypeError:
                        # Evaluation type error
                        OutputLog.nlogFormatError("Eval TypeError", format, params)
                        s = None
        else:
            # No enum dictionary
            try:
                s = format % params #put the params in
            except TypeError:
                # Evaluation type error
                OutputLog.nlogFormatError("Eval TypeError", format, params)
                s = None

        return s


