#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors:Joseph Tarango, Randal Eike, Daniel Garces
# *****************************************************************************/
"""
Brief:
    output_log.py - Output / display functions
Description:
    -

Classes:
    test_util.output_log

Function(s):
    getWindowSize(handle) - Get the selected window size
    pressReturnToContinue(spacing = '') - Prompt user to press return, indent prompt by spacing string
"""

import sys, platform, ctypes

#### some "constants" for color printing
STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE = -11
STD_ERROR_HANDLE = -12
FOREGROUND_BLUE = 0x01  # text color contains blue.
FOREGROUND_GREEN = 0x02  # text color contains green.
FOREGROUND_MAGENTA = 0x03  # text color contains magenta/light blue.
FOREGROUND_RED = 0x04  # text color contains red.
FOREGROUND_PURPLE = 0x05  # text color contains purple/pinkish.
FOREGROUND_YELLOW = 0x06  # text color contains yellow.
FOREGROUND_WHITE = 0x07  # text color contains yellow.
FOREGROUND_INTENSITY = 0x08  # text color is intensified.

if sys.version_info >= (3, 0):
    raw_input = input


def getWindowSize(handle):
    # stdin handle is -10
    # stdout handle is -11
    # stderr handle is -12
    if (handle < -12) or (handle > -10):
        return -1, -1
    csbi = ctypes.create_string_buffer(22)
    cPlatform = platform.system()
    aPBit = platform.architecture()[0]
    if cPlatform == "Windows" and aPBit == '64bit':
        # name = "win.dll"
        h = ctypes.windll.kernel64.GetStdHandle(handle)
        res = ctypes.windll.kernel64.GetConsoleScreenBufferInfo(h, csbi)
    elif cPlatform == "Windows" and aPBit == '32bit':
        # name = "win.dll"
        h = ctypes.windll.kernel32.GetStdHandle(handle)
        res = ctypes.windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
    elif (cPlatform == "Linux" or cPlatform == "Darwin") and aPBit == '64bit':
        # name = "linux.so"
        h = ctypes.cdll.kernel64.GetStdHandle(handle)
        res = ctypes.cdll.kernel64.GetConsoleScreenBufferInfo(h, csbi)
    elif (cPlatform == "Linux" or cPlatform == "Darwin") and aPBit == '32bit':
        # name = "linux.so"
        h = ctypes.cdll.kernel32.GetStdHandle(handle)
        res = ctypes.cdll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
    else:
        res = None

    if res:
        import struct
        (bufx, bufy, curx, cury, wattr, left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
        sizex = right - left + 1
        sizey = bottom - top + 1
    else:
        sizex, sizey = 80, 25  # can't determine actual size - return default values
    return sizex, sizey


def promptUser(prompt):
    usersInput = raw_input('\n' + prompt + ' or Q to exit: ')
    if (usersInput.upper() == 'Q'):
        sys.exit(0)
    return usersInput


def pressReturnToContinue(spacing=''):
    usersInput = promptUser(spacing + 'Press RETURN to continue')


class OutputLog(object):
    """
    Brief:
        test_util.output_log() - Output utility class

    Description:
        Output utility log functions.

    Class(es):
        test_util.output_log

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
    silent = False

    def __init__(self):
        pass

    @staticmethod
    def setDebugLevel(debugLevel=0):
        OutputLog.debugOutputLevel = debugLevel

    @staticmethod
    def setWarnIsError(treatWarningsAsError=False):
        OutputLog.warningIsError = treatWarningsAsError

    @staticmethod
    def enableSilentMode():
        oldDebugLevel = (OutputLog.debugOutputLevel, OutputLog.quiet, OutputLog.silent)
        OutputLog.silent = True
        OutputLog.quiet = True
        OutputLog.debugOutputLevel = 0
        return oldDebugLevel

    @staticmethod
    def restoreMode(oldDebugLevel):
        OutputLog.debugOutputLevel, OutputLog.quiet, OutputLog.silent = oldDebugLevel

    @staticmethod
    def enableQuiet():
        OutputLog.quiet = True
        OutputLog.debugOutputLevel = 0

    @staticmethod
    def disableQuiet():
        OutputLog.quiet = False

    @staticmethod
    def Error(errorString):
        if (False == OutputLog.silent):
            sys.stderr.write("ERROR: " + errorString + "\n")

    @staticmethod
    def Warning(warningString):
        if (OutputLog.warningIsError):
            OutputLog.Error(warningString)
        elif (False == OutputLog.silent):
            sys.stdout.write("WARNING: " + warningString + "\n")

    @staticmethod
    def DebugPrint(debugLevel, informationString):
        if (OutputLog.debugOutputLevel >= debugLevel):
            sys.stdout.write(informationString + "\n")

    @staticmethod
    def Information(informationString):
        if (False == OutputLog.quiet): sys.stdout.write(informationString + "\n")

    @staticmethod
    def Print(informationString):
        sys.stdout.write(informationString + "\n")

    @staticmethod
    def nlogFormatError(errorType, formatStr, params):
        """
        Output nlog format error message to the error stream

        @param errorType - Error type string
        @param formatStr - format string in error
        @param params - parameter tuple
        """
        # s = (errorType, formatStr, str(type(params)), str(params))
        # OutputLog.Error(format("%s format:%s, param types:%s, param values: %s" % s))

        OutputLog.Error(f"{errorType} format:{formatStr}, param types:{str(type(params))}, param values: {str(params)}")
        return