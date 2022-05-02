#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Randal Eike, Joseph Tarango
# *****************************************************************************/

"""
Brief:
    OutputLog.py - Output / display functions
Description:
    -

Classes:
    output_log

Function(s):
    getWindowSize(handle) - Get the selected window size
    pressReturnToContinue(spacing = '') - Prompt user to press return, indent prompt by spacing string
"""
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import sys, ctypes

#### some "constants" for color printing
from ctypes import create_string_buffer

STD_INPUT_HANDLE       = -10
STD_OUTPUT_HANDLE      = -11
STD_ERROR_HANDLE       = -12
FOREGROUND_BLUE        = 0x01 # text color contains blue.
FOREGROUND_GREEN       = 0x02 # text color contains green.
FOREGROUND_MAGENTA     = 0x03 # text color contains magenta/light blue.
FOREGROUND_RED         = 0x04 # text color contains red.
FOREGROUND_PURPLE      = 0x05 # text color contains purple/pinkish.
FOREGROUND_YELLOW      = 0x06 # text color contains yellow.
FOREGROUND_WHITE       = 0x07 # text color contains yellow.
FOREGROUND_INTENSITY   = 0x08 # text color is intensified.

def getWindowSize(handle):
    # stdin handle is -10
    # stdout handle is -11
    # stderr handle is -12
    if (handle<-12) or (handle>-10): return -1,-1
    h = ctypes.windll.kernel32.GetStdHandle(handle)
    csbi = create_string_buffer(22)
    res = ctypes.windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)

    if res:
        import struct
        (bufx, bufy, curx, cury, wattr,left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
        sizex = right - left + 1
        sizey = bottom - top + 1
    else:
        sizex, sizey = 80, 25 # can't determine actual size - return default values
    return sizex,sizey

def promptUser(prompt):
    usersInput = input('\n'+prompt+' or Q to exit: ')
    if (usersInput.upper() == 'Q'): sys.exit(0)
    return usersInput

def pressReturnToContinue(spacing=''):
    usersInput = promptUser(spacing+'Press RETURN to continue')


class OutputLog(object):
    """
    Brief:
        output_log() - Output utility class

    Description:
        Output utility log functions.

    Class(es):
        output_log

    Method(s):
        setDebugLevel(debugLevel = 0) - Set the debug message output level.  All messages with a debug level less than or equal to this level will be displayed.
                                        All messages with s debug level greater than this level will be ignored.

        setWarnIsError(treatWarningsAsError = False) - If the input is true then all warning messages are sent to the error output stream.  If the input is
                                                       false then all warning messages are sent to the standard output stream

        Error(errorString) - Output the input string to the error stream with the ERROR: string prefix

        Warning(warningString) - Output the input string to the proper stream with the proper WARNING: or ERROR: string prefix.  The proper stream is determined
                                 by the state of OutputLog.warningIsError

        DebugPrint(debugLevel, informationString) - If the current value of OutputLog.debugOutputLevel is >= the input debugLevel then output the input informationString
                                                    to the standard output stream.  Else do nothing.

        Print(informationString) - Output the input informationString to the standard output stream.

    Related:

    Author(s):
        Randal Eike
    """
    debugOutputLevel = 0
    warningIsError = False
    quiet = False

    def __init__(self):
        pass

    @staticmethod
    def setDebugLevel(debugLevel = 0):
        OutputLog.debugOutputLevel = debugLevel

    @staticmethod
    def setWarnIsError(treatWarningsAsError = False):
        OutputLog.warningIsError = treatWarningsAsError

    @staticmethod
    def enableQuiet():
        OutputLog.quiet = True
        OutputLog.debugOutputLevel = 0

    @staticmethod
    def disableQuiet():
        OutputLog.quiet = False

    @staticmethod
    def Error(errorString):
        sys.stderr.write("ERROR: "+ errorString+"\n")

    @staticmethod
    def Warning(warningString):
        if (OutputLog.warningIsError): OutputLog.Error(warningString)
        else: sys.stdout.write("WARNING: "+ warningString+"\n")

    @staticmethod
    def DebugPrint(debugLevel, informationString):
        if (OutputLog.debugOutputLevel >= debugLevel): sys.stdout.write(informationString+"\n")

    @staticmethod
    def Information(informationString):
        if(False == OutputLog.quiet): sys.stdout.write(informationString+"\n")

    @staticmethod
    def Print(informationString):
        sys.stdout.write(informationString+"\n")




