#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors:Joseph Tarango
# *****************************************************************************/
"""
Brief:
    Level2Parser.py - Level 2 parser utility

Description:
    Execute the level 2 parser

Classes:
    telemetryHostTime.
"""

import os, sys, ctypes, array

from src.software.parse.nlogParser.telemetryutil.telemetry_util import openReadFile
from src.software.parse.nlogParser.telemetryutil.telemetry_util import ConvertBinNameToTextName
from src.software.parse.nlogParser.telemetryutil.telemetry_util import GetTruncatedDataBuffer
from src.software.parse.nlogParser.test_util.output_log import OutputLog

class Level2Parser(object):
    def __init__(self, objectParserName, structSize = 0):
        """
        Copy the contents of the input bin file name into a buffer

        @param binFileName - Name of the bin file to read
        @param structSize - Size of the structure or 0 to use the bin file size
        @param outputTextName - Name of the output text file or None
        """
        self.structSize = structSize
        self.objectParserName = objectParserName
        self.objectParserFileName = os.path.join(os.getcwd(), "telemetry_parsers", objectParserName+".py")
        self.outputTextName = None
        self.dataBuffer = None
        self.objectParserFile = None
        self.binFileName = None

    def __readBinFile(self, binFileName):
        """
        Open and read the bin file data into the data buffer

        @param binFileName - Path/Name of the bin file containing the data to parse

        @retval Bool - True if able to open and load bin file and parser script, False if one failed
        """
        # Try and load the bin file into a buffer
        self.binFileName = binFileName
        binDataFile = openReadFile(binFileName)
        if (binDataFile is not None):
            fileSize = os.path.getsize(binFileName)
            if (0 == self.structSize): 
                self.structSize = fileSize
            elif (self.structSize != fileSize):
                OutputLog.Warning(format("Bin file size %d does not match structure size %d" % (fileSize, self.structSize)))
                self.structSize = min(fileSize, self.structSize)

            self.structSize, self.dataBuffer = GetTruncatedDataBuffer(binDataFile, self.structSize, fileSize)
            binDataFile.close()
            return True
        else:
            return False

    def __readParserObjectFile(self):
        """
        Open the parser object file

        @retval Bool - True if able to open and load bin file and parser script, False if one failed
        """
        self.objectParserFileName = os.path.join(os.getcwd(), "telemetry_parsers", self.objectParserName+".py")
        try:
            # Try and open the parser file
            self.objectParserFile = open(self.objectParserFileName, 'rt')
            return True

        except IOError:
            # Add the parser call once it's setup
            OutputLog.DebugPrint(3, format("No Parser yet for %s" % (self.objectParserName)))
            self.objectParserFile = None
            return False

    def __execParser(self):
        """
        Use the parser to parse the input data

        @retval - Bool True = parsed without error, False = parse failed
        """
        returnStatus = False
        if (self.objectParserFile is not None):
            try:
                parserGlobals = {}

                # Load the buffer into the parser object
                if ((self.dataBuffer is not None) and (self.binFileName is not None)):
                    # read was good, load the structure
                    parserGlobals['databuffer'] = self.dataBuffer
                    parserGlobals['offset'] = 0
                    if (self.outputTextName is None): self.outputTextName = ConvertBinNameToTextName(self.binFileName)
                    parserGlobals['outputFileName'] = self.outputTextName
                else:
                    # Bad bin file
                    if (self.binFileName is None): OutputLog.Error(format("Must load bin file before you can parse the data"))
                    else: OutputLog.DebugPrint(1, format("Bin file \'%s\', for ParserName: %s, failed to read" % (self.binFileName, self.objectParserName)))
                    raise IOError

                # Try to execute the parser
                # Use exec rather than import here.
                # Python maintains cached version of the imported files
                # that don't always get updated when the underlying file changes,
                # even if re-imported.
                execString = format("%s\nobjectParser = %s()\nobjectParser.loadData(databuffer, offset)\nobjectParser.tofile(outputFileName)" % (self.objectParserFile.read(), self.objectParserName))
                exec(execString, parserGlobals)

                # Get the structure parser 
                OutputLog.DebugPrint(2, format("Found Parser for ParserName: %s" % (self.objectParserName)))

            except Exception as e:
                exec_type, exec_obj, exec_tb = sys.exc_info()
                OutputLog.Error(format("Parser exec failed for %s error on parser file \'%s\'" % (exec_type, self.objectParserFileName)))

            return returnStatus

    def parseData(self, binFileName, outputTextName = None):
        """
        Parse the data object and output the text

        @param binFileName - Path/Name of the binary file with the data to parse
        @param outputTextName - Path/Name of the output text file or None to use binfileName.txt

        @retval - Bool True = parsed without error, False = parse failed
        """
        # Default if no name given is to use binfile path/basename.txt
        if (outputTextName is None): self.outputTextName = ConvertBinNameToTextName(binFileName)
        else: self.outputTextName = outputTextName

        # Load the bin file into the buffer
        if (self.__readBinFile(binFileName)):
            if (self.__readParserObjectFile()):
                # Execute
                returnStatus = self.__execParser()
                self.objectParserFile.close()
                return returnStatus
            else:
                return False
        else:
            return False

