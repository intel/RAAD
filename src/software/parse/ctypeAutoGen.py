#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Jean Mary Madassery, Joe Tarango,  Phoung Tran, Randy Eike, Subhashini Sekaran, Andrea Chamorro
# *****************************************************************************/
'''
Brief:
    ctypeAutoGen.py - Method and Apparatus to extract compiled code into interpreted code.

Description:
    Software application to decode firmware C data structures to python c-types.

Requirement(s):
    All data structure types must be named, meaning no Anonymous subtypes.

    I.E. Invalid coding standard!
    typedef struct
    {
         union
         {
                 struct
                 {
                     uint32_t bottom: 16;
                     uint32_t top: 16;
                 };
                 uint32_t height;
         };
    } person;

    I.E. Valid coding standard!
    typedef struct
    {
         uint32_t bottom: 16;
         uint32_t top: 16;
    } personParts_t;

    typedef union
    {
         uint32_t height; // Note: the all or struct must be before the bitfields.
         personParts_t part;
    } personAll_t;

    typedef struct
    {
         personAll_t allMeta;
    } personHeight_t;

Usage:
    To decode within a wrapper or a python script
    from telemetry.commands.telemetryCmd import *
    myObj = TelemetryObjectCommands()
    myObj.parseTelemetry(5,inFile=r"C:\Development\3DXP-G2\Sandboxes\telemetry\3dxp\gen2\testball\testTelemHostInitObjBis\Object_5_ver1.0_bank0.bin") #todo: update usage
'''

################################################################################################################
################################################################################################################
## General Python module imports
################################################################################################################
################################################################################################################
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
from builtins import (bytes, str, open, super, range, zip, round, input, int, pow, object)

import shutil, errno, logging, platform, uuid, random, traceback

################################################################################################################
################################################################################################################
## Explicit importing of headers
################################################################################################################
################################################################################################################
from datetime import datetime
from pprint import pprint
from subprocess import Popen, PIPE
from src.software.parse.parseUnitTest import *
from src.software.parse.output_log import *

################################################################################################################
################################################################################################################
## Debug methods.
################################################################################################################
################################################################################################################
ENABLE_CLANG = 0  # Adding LLVM clang parser
ENABLE_DEBUG_ENTER = 0  # debug switch

################################################################################################################
################################################################################################################
## LLVM CLang Compiler Keywords
################################################################################################################
################################################################################################################
if ENABLE_CLANG:
    print("Using Clang and it is not supported yet...")
    # Diagram of API https://coggle.it/diagram/VSk7_32dyC9M7Wtk/t/python-clang
    # import clang # @todo
    # from clang.cindex import Index # @todo
    # from clang.cindex import CursorKind, TypeKind # @todo
    # from clang.cindex import Index, TranslationUnit # @todo
    # from clang.cindex import TypeKind # @todo

    # import ctypeslib # @todo
    # from ctypeslib.codegen import cursorhandler # @todo
    # from ctypeslib.codegen import typedesc # @todo
    # from ctypeslib.codegen import typehandler # @todo
    # from ctypeslib.codegen import util # @todo
    # from ctypeslib.codegen.util import log_entity # @todo
    # from ctypeslib.codegen.handler import ClangHandler # @todo
    # from ctypeslib.codegen.handler import CursorKindException # @todo
    # from ctypeslib.codegen.handler import InvalidDefinitionError # @todo
    # from ctypeslib.codegen.handler import DuplicateDefinitionException # @todo

################################################################################################################
################################################################################################################
## Operation Mode
################################################################################################################
################################################################################################################
TRUNK = None


def redefineMedia(shellMode=False):
    '''
    Allows for assignment of the shell status for subprocess execution.
    '''
    global TRUNK
    if (shellMode == True):
        TRUNK = "NAND"
    else:
        TRUNK = "SXP"
    return


################################################################################################################
################################################################################################################
## Filenaming Globals and Updates for Threading
################################################################################################################
################################################################################################################
extTXT = ".txt"
fname_structDefFile = str("ctypeAutoGen_structDefs" + extTXT)
fname_subStructDefFile = str("ctypeAutoGen_subStructDefs" + extTXT)
fname_structSizeFile = str("ctypeAutoGen_structSizes" + extTXT)
fname_srcFileFile = str("ctypeAutoGen_srcFiles" + extTXT)
fname_typedefFile = str("ctypeAutoGen_typedefs" + extTXT)
fname_tempSubStructDefs = str("ctypeAutoGen_tempSubStructDefs" + extTXT)
fname_logFileName = str("ctypeAutoGen_log" + extTXT)

extRC = ".rc"
fname_multiCmdFile = str("ctypeAutoGen_multiCmdFile" + extRC)
fname_subStructMultiCmdFile = str("ctypeAutoGen_subStructMultiCmdFile" + extRC)
fname_structSizeMultiCmdFile = str("ctypeAutoGen_structSizeMultiCmdFile" + extRC)
fname_srcFileMultiCmdFile = str("ctypeAutoGen_srcFileMultiCmdFile" + extRC)
fname_typedefMultiCmdFile = str("ctypeAutoGen_typedefMultiCmdFile" + extRC)

uPIDName = "standard"


def redefineFileNames():
    '''
    Allows for unique id of files.
    '''
    global TRUNK
    global fname_structDefFile
    global fname_subStructDefFile
    global fname_structSizeFile
    global fname_srcFileFile
    global fname_typedefFile
    global fname_tempSubStructDefs
    global fname_logFileName

    global fname_multiCmdFile
    global fname_subStructMultiCmdFile
    global fname_structSizeMultiCmdFile
    global fname_srcFileMultiCmdFile
    global fname_typedefMultiCmdFile

    global uPIDName

    tagCreate = str(os.getpid()) + "-" + str(datetime.now()) + "-" + str(random.randint(1, 1024))
    uPIDName = str(uuid.uuid5(uuid.NAMESPACE_DNS, tagCreate))

    fname_structDefFile = str("ctypeAutoGen_structDefs_" + uPIDName + extTXT)
    fname_subStructDefFile = str("ctypeAutoGen_subStructDefs_" + uPIDName + extTXT)
    fname_structSizeFile = str("ctypeAutoGen_structSizes_" + uPIDName + extTXT)
    fname_srcFileFile = str("ctypeAutoGen_srcFiles_" + uPIDName + extTXT)
    fname_typedefFile = str("ctypeAutoGen_typedefs_" + uPIDName + extTXT)
    fname_tempSubStructDefs = str("ctypeAutoGen_tempSubStructDefs_" + uPIDName + extTXT)
    fname_logFileName = str("ctypeAutoGen_log_" + uPIDName + extTXT)

    fname_multiCmdFile = str("ctypeAutoGen_multiCmdFile_" + uPIDName + extRC)
    fname_subStructMultiCmdFile = str("ctypeAutoGen_subStructMultiCmdFile_" + uPIDName + extRC)
    fname_structSizeMultiCmdFile = str("ctypeAutoGen_structSizeMultiCmdFile_" + uPIDName + extRC)
    fname_srcFileMultiCmdFile = str("ctypeAutoGen_srcFileMultiCmdFile_" + uPIDName + extRC)
    fname_typedefMultiCmdFile = str("ctypeAutoGen_typedefMultiCmdFile_" + uPIDName + extRC)


################################################################################################################
################################################################################################################
## Regular Expression Detection
################################################################################################################
################################################################################################################

if not ENABLE_CLANG:
    TRUNK = "NAND"
    #########################################################################
    # Graphical Flow Draw: https://www.debuggex.com/?flavor=python#cheatsheet
    #########################################################################
    # Legend: Skip means ? outside of statement and Loop means (?) within.  #
    # ....................Skip............Skip...............................#
    # ...................._____..........._____..............................#
    # ....................|...|...........|...|..............................#
    # ====Start====(})====(\s)====(\w)====(\s)====[;]====($)====End====......#
    # ....................|...|...|...|...|...|..............................#
    # ....................|___|...........|___|..............................#
    # ....................Loop............Loop...............................#
    #########################################################################
    detectedStructureMainName = re.compile(r"(})(\s?)+(\w)+?(\s?)+?[;:]$")

    #########################################################################
    # ....................Skip............Skip...............................#
    # ...................._____..........._____..............................#
    # ....................|...|...........|...|..............................#
    # ====Start====(})====(\s)====(\w)====(\s)====[;]====($)====End====......#
    # ....................|...|...|...|...|...|..............................#
    # ....................|___|...........|___|..............................#
    # ....................Loop............Loop...............................#
    #########################################################################
    detectedStructureSubName = re.compile(r"(})(\s?)+(\w)+?(\s?)+?[;]$")

    #########################################################################
    # ....................Skip...............................................#
    # ...................._____..............................................#
    # ....................|...|..............................................#
    # ====Start====(})====(\s)====[;]====($)====End====......................#
    # ....................|...|..............................................#
    # ....................|___|..............................................#
    # ....................Loop...............................................#
    #########################################################################
    detectedAnonymousName = re.compile(r"(})(\s?)+?[;]$")

    ############################################################################
    # Detection of Struct or Union Pointer in a line so we can assign MMU type #
    ############################################################################
    # I.E.myvalue = struct transDmaDwordDesc_t*dmaAdmin;                       #
    ############################################################################
    detectComplexStructOrUnionPointer = re.compile(r"(((\s+(\w)+(\s)+)|(\s+(\w)+=\s+))|(\s+)?)(struct|union)(\s)+?((\w)+)?(\s+)?[*](\s+)?(\w)+(\s+)?[;](\s+)?")

    ############################################################################
    # Detection of Struct or Union Pointer in a line so we can assign MMU type #
    ############################################################################
    # I.E.struct transDmaDwordDesc_t*dmaAdmin;                                 #
    # I.E.union transDmaDwordDesc_t*dmaAdmin;                                  #
    ############################################################################
    detectSimpleStructOrUnionPointer = re.compile(r"((\s+)?)(struct|union)(\s)+?((\w)+)?(\s+)?[*](\s+)?(\w)+(\s+)?[;](\s+)?")

    ############################################################################
    # Detection of basic type Pointer in a line so we can assign MMU type      #
    ############################################################################
    # I.E.char*dmaAdmin;                                                       #
    ############################################################################
    detectBasicPointer = re.compile(r"((\s+)?)(\w+)(\s+)?[*](\s+)?(\w)+(\s+)?[;](\s+)?")

    # Sequences used in matching. Use precompiled version to accelerate code.
    matchSequence = [None] * 27  # Assign size  to the array
    matchSequence[1] = re.compile(r"\d+: (.+)$")
    matchSequence[2] = re.compile(r"^//")
    matchSequence[3] = re.compile(r"^ObjectBegin==>(.+)")
    matchSequence[4] = re.compile(r"^\_+")
    matchSequence[5] = re.compile(r"^0x[a-fA-F0-9]+$")
    matchSequence[6] = re.compile(r"^union \{$")
    matchSequence[7] = re.compile(r"^(\w+) \{$")
    matchSequence[8] = re.compile(r"^(\w+) (\w+) \{$")
    matchSequence[9] = re.compile(r"^(\w+) union (\w+) \{$")
    matchSequence[10] = re.compile(r"^(\w+) (\w+) (\w+) \{$")
    matchSequence[11] = re.compile(r"^(\w+) = (\w+) \{$")
    matchSequence[12] = re.compile(r"^(\w+) = union (\w+) \{$")
    matchSequence[13] = re.compile(r"^(\w+) = (\w+) (\w+) \{$")
    matchSequence[14] = re.compile(r"^([\w ]+) ([*\w]+);$")
    matchSequence[15] = re.compile(r"^(\w+) = union (\w+?::.+) \{")
    matchSequence[16] = re.compile(r"^(\w+) = (\w+?::.+) \{")
    matchSequence[17] = re.compile(r"^(\w+) (\w+?::.+) \{")
    matchSequence[18] = re.compile(r"^\d+$")
    matchSequence[19] = re.compile(r"^(versionMajor) = (.+)")
    matchSequence[20] = re.compile(r"^(versionMinor) = (.+)")
    matchSequence[21] = re.compile(r"(\w+_[et])[ ;:]?")  # NAND type enumeration, and type regex detection. name_size_t causes a slice of name_s detected so removed from NAND.
    matchSequence[22] = re.compile(r"(\w+_[ets])[ ;:]?")  # SXP type enumeration, type, and struct regex detection.
    matchSequence[23] = re.compile(r"(\w+_[et])[ ;]")  # NAND type enumeration, and type regex detection. name_size_t causes a slice of name_s detected so removed from NAND.
    matchSequence[24] = re.compile(r"(\w+_[ets])[ ;]")  # SXP type enumeration, type, and struct regex detection.
    matchSequence[25] = re.compile(r"(versionMajor) = (.+)")
    matchSequence[26] = re.compile(r"(versionMinor) = (.+)")

################################################################################################################
################################################################################################################
## Execute the binaries if there are no changes. I.E. Intel just in time compiler make the binary faster as it
##  is used within our system.
################################################################################################################
################################################################################################################
try:
    if platform.system() == 'Linux':
        ghsPath = '/usr/ghs'
        exeSuffix = ''
    elif platform.system() == 'Windows':
        ghsPath = 'c:/ghs'
        exeSuffix = '.exe'
        import win32com.shell.shell as shell
    elif 'CYGWIN_NT' in platform.system():
        ghsPath = 'c:/ghs'
        exeSuffix = '.exe'
except:
    print(f"{__file__} @{sys._getframe().f_lineno} Failed binary exe. ")

cmdPath, cmdFile = os.path.split(sys.argv[0])

usage = "%s --projectname PROJ_NAME --defineobjs [ALL|DEFAULT|<ENUMERATE_OBJS>] --fwbuilddir FW_BUILD_DIR --tools TELEMETRY_TOOLS_DIR --multiexeversion MULTI_VER --parse" % (sys.argv[0])


# === GUIDE TO --defineobjs ===
# ALL = all uids defined in datacontrol.h
# DEFAULT = all uids marked "Yes" on datacontrol.h
# <ENUMERATE_OBJS> = please insert a comma-separated list of the uids you'd like to define.
# ==============================

################################################################################################################
## Helper function to pause for user input (for debug use only)
################################################################################################################
################################################################################################################
def errorFrameExit():
    # Additional fault analysis information for understanding the fault signature.
    import inspect
    # Notes
    #  inspect.stack()[0] represents this line
    #  inspect.stack()[1] is the caller line caller
    callFrameRecord = inspect.stack()[1]
    frameRecord = callFrameRecord[0]
    suspectInfo = inspect.getframeinfo(frameRecord)
    print("Caller fault file: %s" % (str(suspectInfo.filename)))
    print("Caller fault function: %s" % (str(suspectInfo.function)))
    print("Caller fault file line: %s" % (str(suspectInfo.lineno)))
    quit(suspectInfo.lineno)  # saved fault line


def pressReturnToContinue(aString=None):
    traceback.print_stack()
    if (ENABLE_DEBUG_ENTER == 1):
        if (sys.version_info[0] < 3):
            if aString is None:
                usersInput = input("PRESS RETURN TO CONINTUE or 'q' to quit: ")
            else:
                usersInput = input("(%s) PRESS RETURN TO CONINTUE or 'q' to quit: " % (aString))
        else:
            usersInput = input("PRESS RETURN TO CONINTUE or 'q' to quit")
        if (usersInput == 'q'):
            sys.exit(0)
    else:
        print("Debug enter disabled.")


def formatDataControlObjects(enumGenFile):
    # Process through specified input data object file to get list for scanning
    iFile = open(enumGenFile, 'r')
    if iFile.mode == 'r':
        lines = iFile.readlines()
    else:
        if ENABLE_DEBUG_ENTER: quit(1)
    iFile.close()

    objectList = []
    for l in lines:
        line = l.strip()
        line = re.sub('\/\/\/<', ' ', line)
        line = re.sub('=', ',', line)
        line = re.sub('^ +', '', line)
        line = re.sub(' +', ' ', line)
        line = re.sub(' +,', ',', line)
        line = re.sub(', +', ',', line)
        if re.search('^\/\/', line): continue
        if (line == ''): continue
        objectList.append(line.split(','))

    for i in range(len(objectList)):
        print("    %-40s = %20s, ///< %10s, %18s, %12s" % (str(objectList[i][0]), str(objectList[i][1]), str(objectList[i][2]), str(objectList[i][3]), 'No'))


################################################################################################################
################################################################################################################
# Base class to store intermediate data object info
################################################################################################################
################################################################################################################
class cTypeOptions(object):
    def __init__(self):
        self.fwBuildOutputDir = None
        self.projectName = None
        self.fwToolsDir = None
        self.uidEnumFile = None
        self.multiExeVersion = "mult_716"
        self.extraDebug = False
        self.dataObjToProcess = ""
        self.debug = False
        self.verbose = False
        self.tObjToDefine = ""
        self.parse = True
        self.store = False
        self.media = "NAND"

    def get_fwBuildOutputDir(self):
        return self.fwBuildOutputDir

    def get_projectName(self):
        return self.projectName

    def get_fwToolsDir(self):
        return self.fwToolsDir

    def get_uidEnumFile(self):
        return self.uidEnumFile

    def get_multiExeVersion(self):
        return self.multiExeVersion

    def get_extraDebug(self):
        return self.extraDebug

    def get_dataObjToProcess(self):
        return self.dataObjToProcess

    def get_debug(self):
        return self.debug

    def get_verbose(self):
        return self.verbose

    def get_tObjToDefine(self):
        return self.tObjToDefine

    def get_parse(self):
        return self.parse

    def get_store(self):
        return self.store

    def get_media(self):
        return self.media

    def set_fwBuildOutputDir(self, sVal):
        self.fwBuildOutputDir = sVal

    def set_projectName(self, sVal):
        self.projectName = sVal

    def set_fwToolsDir(self, sVal):
        self.fwToolsDir = sVal

    def set_uidEnumFile(self, sVal):
        self.uidEnumFile = sVal

    def set_multiExeVersion(self, sVal):
        self.multiExeVersion = sVal

    def set_extraDebug(self, sVal):
        self.extraDebug = sVal

    def set_dataObjToProcess(self, sVal):
        self.dataObjToProcess = sVal

    def set_debug(self, sVal):
        self.debug = sVal

    def set_verbose(self, sVal):
        self.verbose = sVal

    def set_tObjToDefine(self, sVal):
        self.tObjToDefine = sVal

    def set_parse(self, sVal):
        self.parse = sVal

    def set_store(self, sVal):
        self.store = sVal

    def set_media(self, sVal):
        self.media = sVal

    def setAll(self, options):
        self.fwBuildOutputDir = options.get_fwBuildOutputDir()
        self.projectName = options.get_projectName()
        self.fwToolsDir = options.get_fwToolsDir()
        self.uidEnumFile = options.get_uidEnumFile()
        self.multiExeVersion = options.get_multiExeVersion()
        self.extraDebug = options.get_extraDebug()
        self.dataObjToProcess = options.get_dataObjToProcess()
        self.debug = options.get_debug()
        self.verbose = options.get_verbose()
        self.tObjToDefine = options.get_tObjToDefine()
        self.parse = options.get_parse()
        self.store = options.get_store()
        self.self_validate()

    def printAll(self):
        print("Firmware Directory " + str(self.fwBuildOutputDir))
        print("Project Name " + str(self.projectName))
        print("Tools Directory " + str(self.fwToolsDir))
        print("UID Enumeration File Location " + str(self.uidEnumFile))
        print("Multi Version " + str(self.multiExeVersion))
        print("Extra Debug Flag " + str(self.extraDebug))
        print("Objects to Process " + str(self.dataObjToProcess))
        print("Debug Flag " + str(self.debug))
        print("Verbose Flag " + str(self.verbose))
        print("Object to Define " + str(self.tObjToDefine))
        print("Objects to Parse " + str(self.parse))
        print("Store Flag " + str(self.store))
        print("Media Type " + str(self.media))

    def self_validate(self):
        faultCase = 0
        errorName = ""
        if self.fwBuildOutputDir is None and not os.path.exists(self.fwBuildOutputDir):
            faultCase = 1
            errorName = "--fwbuilddir"
        if self.uidEnumFile is not None and not os.path.exists(self.uidEnumFile):
            faultCase = 2
            errorName = "--uidenumfile"
        if ((self.multiExeVersion).find("multi_716") == -1):
            faultCase = 3
            errorName = "--multiexeversion"
        if (self.extraDebug is not True and self.extraDebug is not False):
            faultCase = 4
            errorName = "--extradb"
        if (self.dataObjToProcess == ""):
            faultCase = 5
            errorName = "--dataobj"
        if (self.debug is not True and self.debug is not False):
            faultCase = 6
            errorName = "--debug"
        if (self.verbose is not True and self.verbose is not False):
            faultCase = 7
            errorName = "--verbose"
        if (self.tObjToDefine is None or self.tObjToDefine == ""):
            faultCase = 8
            errorName = "--defineobjs"
        if (self.parse is not True and self.parse is not False):
            faultCase = 9
            errorName = "--parse"
        if (self.store is not True and self.store is not False):
            faultCase = 10
            errorName = "--store"
        if ((self.media).find("SXP") == -1 and (self.media).find("NAND") == -1):
            faultCase = 11
            errorName = "--media"
        if faultCase > 0:
            traceback.print_stack()
            print("Error in options, ERROR %s IN INPUT: %s" % (faultCase, errorName))
            print("Run for options: python ctypeAutoGen.py --help ")
            quit(1)


class GenericObject(object):
    """Generic object node used to traverse Abstract Syntax Tree (AST)

    Attributes:
        Tracking node for information to construct a c-type from context free grammar (CFG)

    """

    def __init__(self, debug=False):
        """ Init class with nil content."""
        self.subStructSizeGood = 0
        self.arrayDimList = [1]
        self.debug = debug
        self.depth = 0
        self.endLineNum = 0
        self.fwObject = ''
        self.fwStruct = ''
        self.parent = None
        self.ancestryNames = []
        self.ancestryTypes = []
        self.altMemberList = []
        self.memberList = []
        self.sizeInBits = 0
        self.startLineNum = 0
        self.structType = ''
        self.isPointer = None
        self.uid = 0xBADDC0DE
        self.versionMajor = 0xBADD  ### Default
        self.versionMajorStr = 'versionMajor'  ### Default
        self.versionMinor = 0xC0DE  ### Default
        self.versionMinorStr = 'versionMinor'  ### Default


################################################################################################################
################################################################################################################
# Class for FW C-Struct extraction Python C-Type generation
################################################################################################################
################################################################################################################
class CtypeAutoGen(object):
    """Class to extract FW C-Structs for Telemetry Data Objects

    Attributes:
        Traverses properties of the firmware code to construct the destination type
        in multible stages.
    """

    def __init__(self, options):
        """ Init class with nil and static content."""
        ######################################################################
        ######################################################################
        #  Data members needed for FW C-Struct extraction
        ######################################################################
        ######################################################################

        self.outDir = os.path.abspath(os.path.join(options.fwBuildOutputDir, 'telemetry'))
        if not os.path.exists(self.outDir):
            try:
                os.makedirs(self.outDir)
            except OSError:
                print("Failed to create the telemetry output folder")
                if ENABLE_DEBUG_ENTER: quit(2)

        self.buildDir = os.path.abspath(os.path.join(self.outDir, os.pardir))
        self.objsDir = os.path.abspath(os.path.join(self.buildDir, os.pardir))
        self.projectsDir = os.path.abspath(os.path.join(self.objsDir, os.pardir))

        print
        print("self.outDir     ", self.outDir)
        print("self.buildDir    ", self.buildDir)
        print("self.objsDir    ", self.objsDir)
        print("self.projectsDir", self.projectsDir)

        self.logFileName = os.path.join(self.outDir, fname_logFileName)
        logging.basicConfig(filename=self.logFileName, filemode='w', format='%(asctime)s %(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
        logging.debug('ctypeAutoGen.py Log')
        # logging.debug('Message to file')
        # logging.info('Message to file')
        # logging.warning('Message to file')
        self.log = logging

        self.options = cTypeOptions()
        self.options.setAll(options)
        self.options = options
        self.verbose = options.verbose

        self.telemetryDataControlFile = None
        self.telemetryObjectList = []
        self.telemetryObjectListAll = []

        self.fileList = []
        self.versionList = []
        self.structNameList = []

        self.structDefFile = os.path.join(self.outDir, fname_structDefFile)
        self.subStructDefFile = os.path.join(self.outDir, fname_subStructDefFile)
        self.structSizeFile = os.path.join(self.outDir, fname_structSizeFile)
        self.srcFileFile = os.path.join(self.outDir, fname_srcFileFile)
        self.typedefFile = os.path.join(self.outDir, fname_typedefFile)
        self.multiCmdFile = os.path.join(self.outDir, fname_multiCmdFile)
        self.subStructMultiCmdFile = os.path.join(self.outDir, fname_subStructMultiCmdFile)
        self.structSizeMultiCmdFile = os.path.join(self.outDir, fname_structSizeMultiCmdFile)

        self.srcFileMultiCmdFile = os.path.join(self.outDir, fname_srcFileMultiCmdFile)
        self.typedefMultiCmdFile = os.path.join(self.outDir, fname_typedefMultiCmdFile)

        self.ghsPath = ghsPath
        self.exeSuffix = exeSuffix

        if (self.options.multiExeVersion is not None):
            self.multiExe = os.path.join(self.ghsPath, self.options.multiExeVersion, "multi%s" % (self.exeSuffix))

            if not os.path.exists(self.multiExe):
                print("\n-E- Could not locate multi.exe")
                pressReturnToContinue('self.multiExe %s does not exist' % self.multiExe)
                if ENABLE_DEBUG_ENTER: quit(3)
        else:
            self.multiExe = self.locateMultiExe()
            if self.multiExe is None:
                print("\n-E- Could not locate multi.exe")
                if ENABLE_DEBUG_ENTER: quit(4)
            print("Found the following multi debugger: %s" % (self.multiExe))

        self.elfFile = os.path.abspath(os.path.join(self.options.fwBuildOutputDir, '%s.elf' % (self.options.projectName)))
        if not os.path.exists(self.elfFile):
            print("-E- Could not locate elf file (%s)" % (self.elfFile))
            if ENABLE_DEBUG_ENTER: quit(5)

        if ENABLE_CLANG:
            print("Media Agnostic")
        elif (self.options.media is not None or self.options.media == "NAND"):
            self.TRUNK = "NAND"
        elif (self.options.media == "NAND"):
            self.TRUNK = "SXP"
        else:
            self.TRUNK = "NAND"

        self.recursive = False
        self.subStructList = set()
        self.masterObjectList = {}

        self.numValidStructsFound = 0

        ######################################################################
        ######################################################################
        # Data members needed for Python C-Type generation
        ######################################################################
        ######################################################################

        self.masterObjectListUidValue = {}
        self.objectsInStructDefFile = []
        self.telemetryFolder = self.outDir
        if not os.path.exists(self.telemetryFolder):
            try:
                os.makedirs(self.telemetryFolder)
            except OSError:
                print("Failed to create the telemetry output folder")
                if ENABLE_DEBUG_ENTER: quit(6)

        self.fwToolsDir = self.options.fwToolsDir

        self.parsersFolder = os.path.join(self.outDir, 'parsers')
        if not os.path.exists(self.parsersFolder):
            try:
                os.makedirs(self.parsersFolder)
            except OSError:
                print("Failed to create the parsers folder")
                if ENABLE_DEBUG_ENTER: quit(7)

        self.commandsFolder = os.path.join(self.outDir, 'commands')
        if not os.path.exists(self.commandsFolder):
            try:
                os.makedirs(self.commandsFolder)
            except OSError:
                print("Failed to create the parsers folder")
                if ENABLE_DEBUG_ENTER: quit(8)

        self.maxStructDepth = 0

        # C-Types supported within the automatic generation.
        self.cToPythonCtypeMap = {
            "signed char"       : "ctypes.c_int8",
            "unsigned char"     : "ctypes.c_uint8",
            "char"              : "ctypes.c_uint8",  ### Need to verify
            "bool"              : "ctypes.c_uint8",  ### Need to verify
            "signed short"      : "ctypes.c_int16",
            "short"             : "ctypes.c_int16",
            "unsigned short"    : "ctypes.c_uint16",
            "signed int"        : "ctypes.c_int32",
            "signed long"       : "ctypes.c_int32",
            "int"               : "ctypes.c_int32",
            "unsigned int"      : "ctypes.c_uint32",
            "unsigned long"     : "ctypes.c_uint32",
            "void"              : "ctypes.c_uint32",  ### Need to verify
            "signed long long"  : "ctypes.c_int64",
            "unsigned long long": "ctypes.c_uint64",
        }

    def locateMultiExe(self):
        """Performs the green hills (GHS) compiler executable used in extracting definitions."""
        multiExe = None
        multiExeCtime = None
        for path, dirs, files in os.walk(os.path.abspath(ghsPath)):
            for filename in files:
                if 'multi.exe' == filename.lower():
                    if (multiExe is None):
                        multiExe = os.path.join(path, filename)
                        multiExeCtime = os.path.getctime(multiExe)

                    elif (os.path.getctime(os.path.join(path, filename)) > multiExeCtime):
                        multiExe = os.path.join(path, filename)
                        multiExeCtime = os.path.getctime(multiExe)

        print("\nMulti Debugger: %s" % (multiExe))
        return multiExe

    def runCmd(self, multicmd):
        """Performs an execution of GHS program."""
        proc = Popen(multicmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False)
        # Wait until process terminates
        processSTDOut, processSTDErr = proc.communicate()
        # could do proc.poll() here, but communicate waits for subprocess exit
        if proc.returncode != 0:
            # handle error case here
            print("command {} failed to execute. Exited with {}".format(multicmd, proc.returncode))
            sys.exit(proc.returncode)
        else:
            print("command {} passed execute. Exited with {}".format(multicmd, proc.returncode))
        # all good here
        return (processSTDOut, processSTDErr)

    def autoSrcDirScan(self):
        """Performs an export of all files within the build and writes to a file."""
        multiCmdFile = open(self.srcFileMultiCmdFile, 'w+')
        multiCmdFile.write('_LINES = 10000\n')
        multiCmdFile.write('l f\n')  ### List all source code files
        multiCmdFile.write('quitall\n')  ### Exit multi gracefully
        multiCmdFile.close()

        command = [self.multiExe, self.elfFile, '-nodisplay', '-p', self.srcFileMultiCmdFile, '-RO', self.srcFileFile]
        self.executeMultiScript(command)

        if os.path.isfile(self.srcFileFile) is not True:
            print("srcFileFile does not exist")
            quit(1)

        iFile = open(self.srcFileFile, 'r')
        lines = iFile.readlines()
        iFile.close()

        for i in range(len(lines)):
            line = lines[i].strip()  # debug data.

            if matchSequence[1].match(lines[i].strip()):
                m = matchSequence[1].match(lines[i].strip())
                l = m.group(1).strip()
                f = os.path.abspath(os.path.join(self.projectsDir, l.strip()))
                if f not in self.fileList:
                    self.fileList.append(f)

        # for i in self.fileList: print i
        print('\nScanned %i .h/.c/.cpp files\n' % (len(self.fileList)))

    def locateTelemetryDataControlFile(self):
        """Obtain the datacontrol.h file location"""
        for filename in self.fileList:
            # print ("Filename"  + filename)
            if (self.options.uidEnumFile is not None):
                if self.options.uidEnumFile.strip() in filename:
                    self.telemetryDataControlFile = os.path.join(filename)
                    return True
            elif 'datacontrol.h' in filename:
                self.telemetryDataControlFile = os.path.join(filename)
                return True

        return False

    def getTelemetryObjectList(self, objList=None):
        """
        Find the location of datacontrol.h file in the FW source code, parse, and define which objects to auto gen

        Sample usage:

        getTelemetryObjectList(['1','2','3']) =>     self.telemetryObjectList is all defined in input, needs to be string list
        getTelemetryObjectList(list("all")) =>     self.telemetryObjectList is all defined in datacontrol.h
        getTelemetryObjectList(["range","1","10"]]) =>     self.telemetryObjectList is all defined in datacontrol.h within range
        getTelemetryObjectList() =>     use datacontrol.h "yes"/"no" comments to define self.telemetryObjectList
        """
        ######################################################################
        ######################################################################
        # Extracts telemetry objects from datacontrol.h
        ######################################################################
        ######################################################################

        # Find the location of datacontrol.h file in the FW source code
        if not self.locateTelemetryDataControlFile():
            print("\n-E- Could not locate datacontrol.h to extract the master telemetry object list")
            if ENABLE_DEBUG_ENTER: quit(9)
        print("\n datacontrol.h path:", self.telemetryDataControlFile)

        # Process through datacontrol.h to get the Telemetry Master Object List
        iFile = open(self.telemetryDataControlFile, 'r')
        lines = iFile.readlines()
        iFile.close()

        for i in range(len(lines)):
            if ('typedef enum' in lines[i]):
                self.eUidEnumStart = i + 1
            if ('} eUniqueIdentifier' in lines[i]):
                self.eUidEnumEnd = i + 1
                break

        print("\neUniqueIdentifier Start: %i" % self.eUidEnumStart)
        print("eUniqueIdentifier End:   %i" % self.eUidEnumEnd)

        foundTelemetryV2ListStart = False
        for i in range(self.eUidEnumStart + 1, self.eUidEnumEnd):
            if ('version 2' in lines[i].lower()):
                foundTelemetryV2ListStart = True
                continue

            if ("{" in lines[i]) or ("}" in lines[i]): continue
            line = lines[i].strip()
            line = re.sub(' +', '', line)
            line = re.sub('=', ',', line)
            if re.search('^\/\/', line): continue
            if (line == ''): continue
            line = re.sub('\/\/\/<', '', line)
            if (not foundTelemetryV2ListStart): continue
            myList = line.split(',')
            myList[0] = re.sub('^uid_', '', myList[0])
            myList[0] = re.sub('^eUID_', '', myList[0])
            myList[0] = re.sub('_e', '', myList[0])

            self.telemetryObjectListAll.append(myList)
            if objList is None:
                if ('yes' in myList[-1].lower()):
                    self.telemetryObjectList.append(myList)
            else:
                if "all" in objList[0] and type(objList) is list:
                    self.telemetryObjectList.append(myList)
                elif objList[0] == "range":
                    try:
                        if int(myList[1]) in range(int(objList[1]), int(objList[2])):
                            self.telemetryObjectList.append(myList)
                    except:
                        print("failed to getTelemetryObjectList from: %s" % (",".join(objList)))
                        quit(1)
                else:
                    uid = myList[1]
                    if uid in objList:
                        self.telemetryObjectList.append(myList)

        print("\n====================================================================")
        print("XXXXXXXXX Telemetry Object List obtained from datacontrol.h XXXXXXXX")
        print("====================================================================")
        for i in range(len(self.telemetryObjectList)):
            print("%2i" % (i), )

            for j in range(len(self.telemetryObjectList[i])):
                try:
                    if matchSequence[18].search(self.telemetryObjectList[i][j]):
                        print("%8s" % (self.telemetryObjectList[i][j]))
                    elif ('yes' in self.telemetryObjectList[i][j].lower()):
                        print("%5s" % (self.telemetryObjectList[i][j]))
                    elif ('no' in self.telemetryObjectList[i][j].lower()):
                        print("%5s" % (self.telemetryObjectList[i][j]))
                    else:
                        print("%-20s" % (self.telemetryObjectList[i][j]))
                except:
                    pass
            print
        print("====================================================================")

    def dumpAllTypedefs(self):
        """Performs an extraction of all definitions from GHS."""
        multiCmdFile = open(self.typedefMultiCmdFile, 'w+')
        multiCmdFile.write('_LINES = 50000\n')
        multiCmdFile.write('l t\n')  ### List all source code files
        multiCmdFile.write('quitall\n')  ### Exit multi gracefully
        multiCmdFile.close()

        command = [self.multiExe, self.elfFile, '-nodisplay', '-p', self.typedefMultiCmdFile, '-RO', self.typedefFile]
        self.executeMultiScript(command)
        return

    def getTypeDefName(self, dataObjectName):  # potential to be use Amdahl's law aka parallel.
        """Performs an extraction of the definitions from GHS."""
        typeDefName = None

        objectDeclarationString = re.compile('([a-zA-Z0-9_]+_t) +%s;' % dataObjectName)
        objectDeclarationStringStruct = re.compile('([a-zA-Z0-9_]+_t) +%s([[])' % dataObjectName)

        objectDeclarationMajorVer = re.compile('_MAJOR')
        objectDeclarationMinorVer = re.compile('_MINOR')

        # expansion of uid verification.
        # uidString = 'uid_'+dataObjectName+'_e'
        # uidString = re.compile('///<.+?uniqueIdentifier.+?=.+?([a-zA-Z0-9_]+);')

        for filepath in self.fileList:
            iFile = open(filepath, 'r')
            lines = iFile.readlines()
            iFile.close()

            for txtLine in lines:
                if (dataObjectName not in txtLine): continue
                if dataObjectName + ';' in txtLine or dataObjectName + '[' in txtLine:
                    txtLine = txtLine.strip()
                    txtLine = re.sub('^ +', '', txtLine)
                    txtLine = re.sub(' +', ' ', txtLine)
                    if objectDeclarationString.search(txtLine):
                        m = objectDeclarationString.search(txtLine)
                        typeDefName = m.group(1)
                        return typeDefName
                    elif objectDeclarationStringStruct.search(txtLine):
                        m = objectDeclarationStringStruct.search(txtLine)
                        typeDefName = m.group(1)
                        return typeDefName

        return typeDefName

    def getAllFwVersionMacros(self):
        """Performs an extraction of the macro definitions from GHS."""
        objectDeclarationMajorVer = re.compile('#define +([a-zA-Z0-9_]+_MAJOR) +(\d+)')
        objectDeclarationMinorVer = re.compile('#define +([a-zA-Z0-9_]+_MINOR) +(\d+)')
        for filepath in self.fileList:
            for txtLine in open(filepath, 'r'):
                if matchSequence[2].match(txtLine): continue
                if objectDeclarationMajorVer.search(txtLine):
                    m = objectDeclarationMajorVer.search(txtLine)
                    self.versionList.append([m.group(1), m.group(2)])

                elif objectDeclarationMinorVer.search(txtLine):
                    m = objectDeclarationMinorVer.search(txtLine)
                    self.versionList.append([m.group(1), m.group(2)])
        return

    def getFwMacroValue(self, macroName):
        """Performs an extraction of the definition from GHS."""
        macroSearchPatternDecimal = re.compile('#define +%s +(\d+)' % macroName)
        macroSearchPatternHex = re.compile('#define +%s +(0x[0-9a-fA-F]+)' % macroName)

        for filepath in self.fileList:
            for txtLine in open(filepath, 'r'):
                if matchSequence[2].match(txtLine): continue
                if macroSearchPatternDecimal.search(txtLine):
                    m = macroSearchPatternDecimal.search(txtLine)
                    return int(m.group(1))
                elif macroSearchPatternHex.search(txtLine):
                    m = macroSearchPatternHex.search(txtLine)
                    return int(m.group(1), 16)

        return None

    def getTypeDefStruct(self, typeDefName):
        """Performs an extraction struct of the definitions from GHS."""
        objectDeclarationString = re.compile('\} %s;' % typeDefName)
        objectDeclarationStringWithTypedef = re.compile('typedef +([a-zA-Z0-9_]+_t) +%s;' % typeDefName)
        objectDeclarationStringAlterStruct = re.compile('([a-zA-Z0-9_]+_t) +%s([[])' % typeDefName)

        for filepath in self.fileList:
            iFile = open(filepath, 'r')
            lines = iFile.readlines()
            iFile.close()

            for i in range(len(lines)):
                if typeDefName not in lines[i]: continue
                txtLine = lines[i].strip()
                txtLine = re.sub('^ +', '', txtLine)
                txtLine = re.sub(' +', ' ', txtLine)
                if matchSequence[2].match(txtLine): continue

                if objectDeclarationString.search(txtLine) or \
                        objectDeclarationStringWithTypedef.search(txtLine) or \
                        objectDeclarationStringAlterStruct.search(txtLine):
                    return filepath, typeDefName, i  ### Last param is 0-based lineNum where the typeDefName is found

        return None, None, None

    def isUserAdmin(self):
        """Performs an admin check for execution."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def runShellCmd(self, multicmd):
        """Performs a run command for GHS."""
        shell.ShellExecuteEx(lpVerb='runas', lpFile=sys.executable, lpParameters=multicmd)

    def executeMultiScript(self, command):
        """Performs an execution for the GHS script."""
        try:
            if os.path.isfile(self.elfFile):
                # Ensure the dla, dnm, etc. and elf have the same timestamp (since multi will complain otherwise)
                elfModificationTime = os.path.getmtime(self.elfFile)
                elfAccessTime = os.path.getatime(self.elfFile)

                theDirectory = os.path.dirname(self.elfFile)
                for file in os.listdir(theDirectory):
                    if os.path.splitext(os.path.basename(self.elfFile))[0] in file:
                        fullPath = os.path.join(theDirectory, file)
                        os.utime(fullPath, (elfAccessTime, elfModificationTime))
            else:
                print("Error: %s did not exist!" % self.elfFile)
            # print("Platform: ", str(platform.system()))
            if platform.system() == 'Linux':
                ### Just in case we need to do something different for Linux
                self.runCmd(command)
            elif platform.system() == 'Windows':
                ### Just in case we need to do something different for Windows
                self.runCmd(command)
            print("\nCommand: %s" % command)
        except Exception as e:
            print("Failed Multi execution: \n{}\n{}".format(command, e))
            if ENABLE_DEBUG_ENTER: quit(10)

    def appendNewSubStructs(self, tempSubStructDefFile):
        """Performs sub struct extraction."""
        try:
            tmpFileExists = os.path.isfile(tempSubStructDefFile)
            if tmpFileExists:
                iFile = open(tempSubStructDefFile, 'r')
                lines = iFile.readlines()
                iFile.close()
                subFileExists = os.path.isfile(self.subStructDefFile)
                if subFileExists:
                    oFile = open(self.subStructDefFile, 'a+')
                    for line in lines[6:]:  ### Skip over the first 7 MULTI Debugger startup text lines
                        oFile.write(line)
                    oFile.close()
                else:
                    oFile = open(self.subStructDefFile, 'w+')
                    for line in lines:
                        oFile.write(line)
                    oFile.close()
                    if ENABLE_DEBUG_ENTER: quit(11)
            else:
                if ENABLE_DEBUG_ENTER: quit(12)
        except:
            print("Failed appendNewSubStructs execution")
            if ENABLE_DEBUG_ENTER: quit(13)

    def extractArraySubStructs(self):
        """Performs array type extraction within a struct type."""
        tempSubStructList = set()

        if self.recursive:
            if (self.verbose): print("\n recursive extractArraySubStructs call")
            subFileExists = os.path.isfile(self.subStructDefFile)
            if subFileExists:
                fp = open(self.subStructDefFile, 'r')
            else:

                self.recursive = False
                if ENABLE_DEBUG_ENTER: quit(14)
                return
        else:
            if (self.verbose): print("\n Initial extractArraySubStructs call")
            subFileExists = os.path.isfile(self.structDefFile)
            if subFileExists:
                fp = open(self.structDefFile, 'r')
            else:
                self.recursive = False
                if ENABLE_DEBUG_ENTER: quit(15)
                return

        lines = fp.readlines()
        # print("\n Closing " + str(fp))
        fp.close()

        objectInStructArray = re.compile('struct ([a-zA-Z0-9_]+_t) (([a-zA-Z0-9_]+)([[]))')
        objectInUnionArray = re.compile('union ([a-zA-Z0-9_]+_t) (([a-zA-Z0-9_]+)([[]))')

        for line in lines:
            if objectInStructArray.search(line):
                m = objectInStructArray.search(line)
                if (m.group(1) not in self.subStructList):
                    tempSubStructList.add(m.group(1))
                    self.subStructList.add(m.group(1))

            elif objectInUnionArray.search(line):
                m = objectInUnionArray.search(line)
                if (m.group(1) not in self.subStructList):
                    tempSubStructList.add(m.group(1))
                    self.subStructList.add(m.group(1))

        if self.options.verbose:
            print("subStructList:    ", self.subStructList)
            print("tempSubStructList:", tempSubStructList)

        # print("\n Opening " + str(self.subStructMultiCmdFile))
        multiCmdFile = open(self.subStructMultiCmdFile, 'w+')
        multiCmdFile.write('_LINES = 1000\n')
        for i in range(len(tempSubStructList)):
            if list(tempSubStructList)[i] is not None:
                multiCmdFile.write('mprintf(\"SubstructBegin==>%s\\n\")\n' % (list(tempSubStructList)[i]))
                multiCmdFile.write(list(tempSubStructList)[i] + '\n')
                multiCmdFile.write("sizeof(%s)\n" % (list(tempSubStructList)[i]))
                multiCmdFile.write('mprintf(\"SubstructEnd==>%s\\n\")\n' % (list(tempSubStructList)[i]))
            else:
                multiCmdFile.write('mprintf(\"SubstructBegin==>%s\\n\")\n' % (list(tempSubStructList)[i]))
                multiCmdFile.write('struct {\n')
                multiCmdFile.write('{ ' + list(tempSubStructList)[i] + '\n')
                multiCmdFile.write("0")
                multiCmdFile.write('mprintf(\"SubstructEnd==>%s\\n\")\n' % (list(tempSubStructList)[i]))
                if ENABLE_DEBUG_ENTER: quit(16)
        multiCmdFile.write('quitall\n')  ### Exit multi gracefully
        # print("\n Closing " + str(multiCmdFile))
        multiCmdFile.close()

        tempSubStructDefFile = os.path.join(self.outDir, fname_tempSubStructDefs)
        if (len(tempSubStructList) > 0):
            if self.recursive:
                command = [self.multiExe, self.elfFile, '-nodisplay', '-p', self.subStructMultiCmdFile, '-RO', tempSubStructDefFile]
            else:
                command = [self.multiExe, self.elfFile, '-nodisplay', '-p', self.subStructMultiCmdFile, '-RO', self.subStructDefFile]

            if platform.system() == 'Linux':
                ### Just in case we need to do something different for Linux
                self.runCmd(command)
            elif platform.system() == 'Windows':
                ### Just in case we need to do something different for Windows
                self.runCmd(command)

            if self.recursive:
                if os.path.exists(tempSubStructDefFile):
                    print(" Appending new sub structures 1.")
                    self.appendNewSubStructs(tempSubStructDefFile)

                if os.path.exists(tempSubStructDefFile):
                    print(" Deleting temp structures 2.")
                    os.remove(tempSubStructDefFile)

            self.recursive = True
            print(" Extracting new sub structures 3.")
            self.extractArraySubStructs()

    def searchVersionDataControlComments(self, fileName, typeDefStructName, lineNum, line, tag, delimiter):
        print("trying to match: " + line)
        if tag in line:
            stopAll = False
            startPos = re.search(tag, line).start()
            chunkString = line[startPos:]
            endPos = re.search(delimiter, chunkString).start()
            if (self.options.debug):
                print('Found!')
                print("Start: " + str(startPos))
                print("Chunk: " + chunkString)
                print("End: " + str(endPos))
                print("String: " + str(line[startPos:endPos]))
            for pos in range(startPos, len(line)):
                if (line[pos] == delimiter and stopAll == False):
                    for dataStart in range(startPos, pos):
                        if (line[dataStart] == '=' and stopAll == False):
                            resultStr = line[dataStart + 1:pos]
                            resultStr = resultStr.strip()
                            stopAll = True
                            if (self.options.debug):
                                print("Value " + str(pos))
                                print("SubString " + str(line[startPos:pos]))
                                print("Pizza Slice: " + str(resultStr))
                                return resultStr
        return None

    def searchVersionMajorMinor(self, fileName, typeDefStructName, lineNum):
        """Performs version lookup for a structure."""
        verMajorMacro = None
        verMinorMacro = None
        versionMajor = 0xBADD
        versionMinor = 0xC0DE
        majorFound = False
        minorFound = False
        iFile = open(fileName, 'r')
        lines = iFile.readlines()
        iFile.close()

        print("FileName " + fileName)
        print("Typedef " + typeDefStructName)
        print("LineNumber " + str(lineNum))

        if typeDefStructName not in lines[lineNum]:
            print("Incorrect/inconsistent parameters being passed into searchVersionMajorMinor")
            return None, None

        structStartLine = 0
        for i in range(lineNum, 0, -1):
            if re.search('typedef [union|struct]', lines[i]):
                structStartLine = i
                break

        if (structStartLine == 0): return None, None

        for i in range(structStartLine, lineNum):
            line = lines[i].strip()
            if not re.search('\/\/\/<', line): continue
            if (line == ''): continue
            # print line

            # SXP version extraction
            if ('testCmdVersion_t' in line) and ('_MAJOR' in line) and ('_MINOR' in line):
                if re.search('[\/<, ]([A-Z0-9_]+_MAJOR)', line):
                    m = re.search('[\/< ]([A-Z0-9_]+_MAJOR)', line)
                    verMajorMacro = m.group(1)

                if re.search('[\/<, ]([A-Z0-9_]+_MINOR)', line):
                    m = re.search('[\/< ]([A-Z0-9_]+_MINOR)', line)
                    verMinorMacro = m.group(1)

            # Data Control version extraction
            lineUpper = line.upper()
            if ('MAJOR' in lineUpper):
                majorSearch = re.search('///<.*major = ([^;]*)', line)
                # Major string detection
                if majorSearch and not majorFound:
                    verMajorMacro = majorSearch.group(1)
                    majorFound = True

                if majorFound == False:
                    verMajorMacro = self.searchVersionDataControlComments(fileName, typeDefStructName, lineNum, line, 'major', ';')
                    if (self.options.debug): print(verMajorMacro)
                    if verMajorMacro != None:
                        majorFound = True

            lineUpper = line.upper()
            if ('MINOR' in lineUpper):
                minorSearch = re.search('///<.*minor = ([^;]*)', line)
                # Minor string detection
                if minorSearch and not minorFound:
                    verMinorMacro = minorSearch.group(1)
                    minorFound = True

                if minorFound == False:
                    verMinorMacro = self.searchVersionDataControlComments(fileName, typeDefStructName, lineNum, line, 'minor', ';')
                    if verMinorMacro != None:
                        minorFound = True

                if (self.options.debug):
                    print("Version String: " + verMajorMacro)

                if (self.options.debug and minorFound):
                    print("Version String: " + verMinorMacro)

            if majorFound and minorFound:
                break

        for v in self.versionList:
            if (verMajorMacro is not None) and (verMajorMacro in v[0]): versionMajor = int(v[1])
            if (verMinorMacro is not None) and (verMinorMacro in v[0]): versionMinor = int(v[1])
            if (versionMajor != 0xBADD) and (versionMinor != 0xC0DE): break

        if (self.options.debug): print(verMajorMacro, versionMajor, verMinorMacro, versionMinor)

        return verMajorMacro, versionMajor, verMinorMacro, versionMinor

    def searchUidDADupPersDep(self, fileName, typeDefStructName, lineNum):
        """Performs metaData lookup for a structure."""
        verMajorMacro = None
        verMinorMacro = None
        versionMajor = 0xBADD
        versionMinor = 0xC0DE
        majorFound = False
        minorFound = False
        iFile = open(fileName, 'r')
        lines = iFile.readlines()
        iFile.close()

        print("FileName " + fileName)
        print("Typedef " + typeDefStructName)
        print("LineNumber " + str(lineNum))

        if typeDefStructName not in lines[lineNum]:
            print("Incorrect/inconsistent parameters being passed into searchVersionMajorMinor")
            return None, None

        structStartLine = 0
        for i in range(lineNum, 0, -1):
            if re.search('typedef [union|struct]', lines[i]):
                structStartLine = i
                break

        if (structStartLine == 0): return None, None

        for i in range(structStartLine, lineNum):
            line = lines[i].strip()
            if not re.search('\/\/\/<', line): continue
            if (line == ''): continue

    def getAllStructNames(self):
        """Extract the struct names from definition file."""
        try:
            structDefFileExists = os.path.isfile(self.structDefFile)
            if structDefFileExists:
                iFile = open(self.structDefFile, 'r')
                lines = iFile.readlines()
                iFile.close()
                isDetected = None
                # isPointerDetected = None
                for l in lines:
                    if TRUNK == "SXP" and not ENABLE_CLANG:
                        isDetected = matchSequence[22].search(l)
                        # print ("   Attempt detect SXP name: " + str(l))
                    elif TRUNK == "NAND" and not ENABLE_CLANG:
                        isDetected = matchSequence[21].search(l)
                        # print ("   Attempt detect member NAND name: " + str(l))
                    elif ENABLE_CLANG:
                        isDetected = detectedStructureMainName.search(l)
                        # print ("   Attempt detect CLang name: " + str(l))

                    if isDetected:
                        m = isDetected
                        if (m.group(1) not in self.structNameList):
                            # print ("   [Found] member name: " + str(m.group(1)))
                            # isPointerDetected = detectSimpleStructOrUnionPointer.search(l) # isPointerDetected = detectBasicPointer.search(l)
                            # if (isPointerDetected):
                            #    print ("   [Found] pointer: " + str(m.group(1)))
                            #    # Mark the struct as not needed and use basic type. Mark self.isPointer = 1 later
                            self.structNameList.append(m.group(1))
                        # else:
                        #    print ("   <Duplicate> member name: " + str(m.group(1)))
                    # else:
                    #    print ("   Nothing member: " + str(l))
            else:
                iFile = open(self.structDefFile, 'w+')
                iFile.close()

            try:
                subStructDefFileExists = os.path.isfile(self.subStructDefFile)
                if subStructDefFileExists:
                    iFile = open(self.subStructDefFile, 'r')
                    lines = iFile.readlines()
                    iFile.close()
                    for l in lines:
                        # isAnonymousName = detectedAnonymousName.search(l)
                        # if isAnonymousName:
                        #    print ("   Attempt detect isAnonymousName: " + str(l))
                        if TRUNK == "NAND" and not ENABLE_CLANG:
                            isDetected = matchSequence[23].search(l)
                            # print ("   Attempt detect sub-member NAND name: " + str(l))
                        elif TRUNK == "SXP" and not ENABLE_CLANG:
                            isDetected = matchSequence[24].search(l)
                            # print ("   Attempt detect sub-member SXP name: " + str(l))
                        elif ENABLE_CLANG:
                            isDetected = detectedStructureSubName.search(l)
                            # print ("   Attempt detect sub-member CLang name: " + str(l))

                        if isDetected:
                            m = isDetected
                            if (m.group(1) not in self.structNameList):
                                # print ("   [Found] sub-member name: " + str(m.group(1)))
                                self.structNameList.append(m.group(1))
                            # else:
                            #    print ("   <Duplicate> sub-member: " + str(l))
                        # else:
                        #   print ("   Nothing sub-member: " + str(l))
                else:
                    iFile = open(self.subStructDefFile, 'w+')
                    iFile.close()
                    if ENABLE_DEBUG_ENTER: quit(17)
            except BaseException as error:
                print('An exception occurred: {}'.format(error))
                if ENABLE_DEBUG_ENTER: quit(17)
            except:
                print('An exception occurred: {}'.format("def getAllStructNames - substruct"))
                if ENABLE_DEBUG_ENTER: quit(17)
        except BaseException as error:
            print('An exception occurred: {}'.format(error))
            if ENABLE_DEBUG_ENTER: quit(18)
        except:
            print('An exception occurred: {}'.format("def getAllStructNames"))
            if ENABLE_DEBUG_ENTER: quit(19)

    def getAllStructSizes(self):
        """Performs an extraction of the definitions from GHS."""
        self.getAllStructNames()

        multiCmdFile = open(self.structSizeMultiCmdFile, 'w+')
        multiCmdFile.write('_LINES = 10000\n')
        for s in self.structNameList:
            multiCmdFile.write('mprintf(\"sizeof(%s)=%%i\\n\",sizeof(%s))\n' % (s, s))
        multiCmdFile.write('quitall\n')  ### Exit multi gracefully
        multiCmdFile.close()

        command = [self.multiExe, self.elfFile, '-nodisplay', '-p', self.structSizeMultiCmdFile, '-RO', self.structSizeFile]
        self.executeMultiScript(command)

    def extractCstructs(self):
        """Performs an extraction of the definitions from GHS."""
        self.getAllFwVersionMacros()
        self.numValidStructsFound = 0
        multiCmdFile = open(self.multiCmdFile, 'w+')
        multiCmdFile.write('_LINES = 10000\n')

        print("\nTelemetry Object List")
        for i in range(len(self.telemetryObjectList)):
            dataObjectName = self.telemetryObjectList[i][0]
            typeDefName = self.getTypeDefName(dataObjectName)
            try:
                print("%3i/%i: %-45s" % (i + 1, len(self.telemetryObjectList), "%s ==> %s" % (dataObjectName, str(typeDefName))))

            except:
                pass
            ### Add command to extRC to be executed in Multi Debugger
            if typeDefName is not None:
                fileName, typeDefStructName, lineNum = self.getTypeDefStruct(typeDefName)
                if (typeDefStructName is not None):
                    self.numValidStructsFound += 1

                    #### Extracting version field
                    if (self.options.verbose): print(str(fileName), str(typeDefStructName), str(lineNum))
                    verMajorMacro, versionMajor, verMinorMacro, versionMinor = self.searchVersionMajorMinor(fileName, typeDefStructName, lineNum)
                    try:
                        print(', %30s=0x%04X, %30s=0x%04X,' % (verMajorMacro, versionMajor, verMinorMacro, versionMinor), )
                    except:
                        pass

                    multiCmdFile.write('mprintf(\"ObjectBegin==>%s\\n\")\n' % (dataObjectName))
                    multiCmdFile.write(typeDefStructName + '\n')
                    multiCmdFile.write("sizeof(" + typeDefStructName + ")\n")
                    multiCmdFile.write('mprintf(\"%s = 0x%%04X\\n\",%i)\n' % ('versionMajor', versionMajor))
                    multiCmdFile.write('mprintf(\"%s = 0x%%04X\\n\",%i)\n' % ('versionMinor', versionMinor))
                    multiCmdFile.write('mprintf(\"%s = %d\\n\")\n' % ('uid', int(self.telemetryObjectList[i][1])))
                    multiCmdFile.write('mprintf(\"ObjectEnd==>%s\\n\")\n' % (dataObjectName))

                    if (self.telemetryObjectList[i][1] not in self.masterObjectList.keys()):
                        if ('0X' in self.telemetryObjectList[i][1].upper()):
                            self.masterObjectList[int(self.telemetryObjectList[i][1], 16)] = [self.telemetryObjectList[i][0], typeDefStructName, self.telemetryObjectList[i][2]]

                        elif re.search('^[a-zA-Z_]+', self.telemetryObjectList[i][1]):
                            ### Got a macro for UID.  Let scan the FW to get the value.
                            macroUid = self.getFwMacroValue(self.telemetryObjectList[i][1])

                        else:
                            self.masterObjectList[int(self.telemetryObjectList[i][1])] = [self.telemetryObjectList[i][0], typeDefStructName, self.telemetryObjectList[i][2]]
                    else:
                        print("\n-E- UID (%i for %s) as specified by FW datacontrol.h is not unique!" % (self.telemetryObjectList[i][1], self.telemetryObjectList[i][0]))
                        if ENABLE_DEBUG_ENTER: quit(20)
                    print('+')

                else:
                    self.log.debug("Not able to extract %s" % (dataObjectName))
                    print('-')


            else:
                self.log.debug("Not able to extract %s" % (dataObjectName))
                print('-')

        multiCmdFile.write('quitall\n')  ### Exit multi gracefully
        multiCmdFile.close()

        if (self.options.debug):
            print("\nMaster Object List:")
            print("%8s: %-30s, %-30s, %2s" % ('Key', 'Object', 'Struct', 'DA'))
            for key in sorted(self.masterObjectList.keys()):
                print("%8i: %-30s, %-30s, %2s" % (key, self.masterObjectList[key][0], self.masterObjectList[key][1], self.masterObjectList[key][2]))

        command = [self.multiExe, self.elfFile, '-nodisplay', '-p', self.multiCmdFile, '-RO', self.structDefFile]

        self.executeMultiScript(command)
        self.recursive = False  ### Set recursive flag to False to start a new recursive call
        self.extractArraySubStructs()
        self.getAllStructSizes()
        # self.deleteTempFiles()
        print("\nTotal valid structures found:  %i/%i" % (self.numValidStructsFound, len(self.telemetryObjectList)))

    def deleteTempFiles(self):
        """Performs delete of temp files used in parsing."""
        if os.path.exists(self.multiCmdFile): os.remove(self.multiCmdFile)
        if os.path.exists(self.subStructMultiCmdFile): os.remove(self.subStructMultiCmdFile)

    ####################################################################################
    ####################################################################################
    ####################################################################################
    ####################################################################################

    def createMasterObjectListUidValue(self):
        """Performs a key list creation for unique identifiers."""
        for key in sorted(self.masterObjectList.keys()):
            self.masterObjectListUidValue[self.masterObjectList[key][0]] = key
            self.masterObjectListUidValue[self.masterObjectList[key][1]] = key

        if (self.options.verbose):
            print("\nMaster Object List w/ Data Object and Struct as keys:")
            print("%-30s: %-3s" % ('Key', 'UID'))
            for key in sorted(self.masterObjectListUidValue.keys()):
                print("%-30s: %3s" % (key, self.masterObjectListUidValue[key]))

    def getObjectsFromStructDefFile(self):
        """Performs an extraction of the definitions from GHS produced file."""
        # Process through specified data object file to get list for scanning
        iFile = open(self.structDefFile, 'r')
        lines = iFile.readlines()
        iFile.close()

        myKeys = self.masterObjectListUidValue.keys()

        self.objectsInStructDefFile = []
        for l in lines:
            if ('==>' not in l): continue
            line = l.strip()
            line = re.sub('^ +', '', line)
            line = re.sub(' +', '', line)
            line = re.sub('{', '', line)
            if matchSequence[3].match(line):
                m = matchSequence[3].match(line)
                fwObject = m.group(1)
                if fwObject in myKeys:
                    uid = int(self.masterObjectListUidValue[fwObject])
                    fwStruct = self.masterObjectList[uid][1]
                    self.objectsInStructDefFile.append([fwObject, fwStruct, uid])

        if (self.options.verbose):
            print("\nActual structs found in the stuct definition file:")
            for i in range(len(self.objectsInStructDefFile)):
                print(i, self.objectsInStructDefFile[i][0], self.objectsInStructDefFile[i][1], self.objectsInStructDefFile[i][2])

    def getStructSizeInBits(self, fwStruct):
        """Performs an extraction of the definitions from GHS produced file."""
        iFile = open(self.structSizeFile, 'r')
        lines = iFile.readlines()
        iFile.close()

        sizeInBits = 0
        for l in lines:
            if re.search('^sizeof\(%s\)=(\d+)' % fwStruct, l.strip()):
                m = re.search('^sizeof\(%s\)=(\d+)' % fwStruct, l.strip())
                sizeInBits = eval(m.group(1)) * 8
                break

        return sizeInBits

    def onlyHasSimpleSubstructures(self, obj):
        """Performs check to determine if fundamental type."""
        if (len(obj.memberList) > 0):
            for o in obj.memberList:
                if (len(o.memberList) > 0):
                    return False
        return True

    def determineObjectSizes(self, obj):
        """Performs an extraction of the definitions size from GHS."""
        sizeInBits = 0

        arrayDimString = str(obj.arrayDimList[0])
        for i in range(1, len(obj.arrayDimList)):
            arrayDimString += "*" + str(obj.arrayDimList[i])

        if (obj.fwStruct in self.cToPythonCtypeMap.keys()):
            obj.sizeInBits = ctypes.sizeof(eval(self.cToPythonCtypeMap[obj.fwStruct])) * 8 * eval(arrayDimString)
            obj.subStructSizeGood = 1

        elif self.getStructSizeInBits(obj.fwStruct):
            sizeInBits = self.getStructSizeInBits(obj.fwStruct) * eval(arrayDimString)
            obj.sizeInBits = sizeInBits
            obj.subStructSizeGood = 1

        elif re.search('^struct (.+)$', obj.fwStruct):
            m = re.search('^struct (.+)$', obj.fwStruct)
            sizeInBits = self.getStructSizeInBits(m.group(1)) * eval(arrayDimString)
            if (sizeInBits):
                obj.subStructSizeGood = 1
            else:
                sizeInBits = obj.sizeInBits
            obj.sizeInBits = sizeInBits

        elif re.search('^union (.+)$', obj.fwStruct):
            m = re.search('^union (.+)$', obj.fwStruct)
            sizeInBits = self.getStructSizeInBits(m.group(1)) * eval(arrayDimString)
            if (sizeInBits):
                obj.subStructSizeGood = 1
            else:
                sizeInBits = obj.sizeInBits
            obj.sizeInBits = sizeInBits

        elif re.search('^enum (.+)$', obj.fwStruct):
            m = re.search('^enum (.+)$', obj.fwStruct)
            sizeInBits = self.getStructSizeInBits(m.group(1)) * eval(arrayDimString)
            if (sizeInBits):
                obj.subStructSizeGood = 1
            else:
                sizeInBits = obj.sizeInBits
            obj.sizeInBits = sizeInBits
        else:
            if (self.options.debug):
                # Address corner case Clang syntax of forward declaration @jdtarang
                print("\nObject size mismatch due to obscure syntax expansion!")
                print("subStructSizeGood " + str(obj.subStructSizeGood))
                print("arrayDimList " + str(obj.arrayDimList))
                print("debug " + str(obj.debug))
                print("depth " + str(obj.depth))
                print("endLineNum " + str(obj.endLineNum))
                print("fwObject " + str(obj.fwObject))
                print("fwStruct " + str(obj.fwStruct))
                print("parent " + str(obj.parent))
                print("ancestryNames " + str(obj.ancestryNames))
                print("ancestryTypes " + str(obj.ancestryTypes))
                print("altMemberList " + str(obj.altMemberList))
                print("memberList " + str(obj.memberList))
                print("sizeInBits " + str(obj.sizeInBits))
                print("startLineNum " + str(obj.startLineNum))
                print("structType " + str(obj.structType))
                print("isPointer " + str(obj.isPointer))
                print("uid " + str(obj.uid))
                print("versionMajor " + str(obj.versionMajor))
                print("versionMajorStr " + str(obj.versionMajorStr))
                print("versionMinor " + str(obj.versionMinor))
                print("versionMinorStr " + str(obj.versionMinorStr))
                pressReturnToContinue('Object size exception!')
            else:
                sizeInBits = self.getStructSizeInBits(obj.fwStruct)
                if (sizeInBits):
                    obj.subStructSizeGood = 1
                else:
                    sizeInBits = obj.sizeInBits
                obj.sizeInBits = sizeInBits

        if obj.memberList == []:
            return
        else:
            for i in range(len(obj.memberList)):
                self.determineObjectSizes(obj.memberList[i])

    def auditStructSizes(self, obj):
        """Performs an verification of definitions from GHS."""
        if (len(obj.memberList) <= 0):
            return  ### We do nothing here because I cannot be certain if the simple data object size is valid or not.

        if (obj.sizeInBits == 0):
            ### Dealing with unions of size 0
            if (obj.structType in ['union']):

                ### Setting the size for a 0-size union
                for o in obj.memberList:
                    if (o.structType not in ['union']) and (o.sizeInBits != 0):
                        obj.sizeInBits = o.sizeInBits
                        obj.subStructSizeGood = 1
                        break

                #### Set subStructSizeGood status for the union object's subStructs
                for o in obj.memberList:
                    if (o.sizeInBits == obj.sizeInBits):
                        o.subStructSizeGood = 1
                    else:
                        o.subStructSizeGood = 0
                        o.sizeInBits = obj.sizeInBits

            ### Setting the size for a 0-size struct
            elif (obj.structType in ['struct']):
                for o in obj.memberList:
                    obj.sizeInBits += o.sizeInBits
                obj.subStructSizeGood = 1

            ### Setting the size for a 0-size struct
            elif (obj.structType in ['bitfield']) and self.onlyHasSimpleSubstructures(obj):
                for o in obj.memberList:
                    if (o.structType not in ['union']) and (o.sizeInBits != 0):
                        obj.sizeInBits = o.sizeInBits
                        obj.subStructSizeGood = 1
                        o.subStructSizeGood = 0
                        break

            ### Setting the size for a 0-size struct
            elif (obj.structType in ['bitfield']):
                for o in obj.memberList:
                    obj.sizeInBits += o.sizeInBits
                obj.subStructSizeGood = 1

            ### Catching other 0-size data construct as error for further evaluation later.
            else:
                if (self.options.debug):
                    print(vars(obj))
                    pressReturnToContinue('1 getting obj.sizeInBits')

        ### Obtain size for unions and structs
        gotCalculatedUnionSize = False
        calculatedSubstructSizeTotal = 0
        for o in obj.memberList:
            self.auditStructSizes(o)

            if (obj.structType in ['union']):
                if (not gotCalculatedUnionSize):
                    calculatedSubstructSizeTotal = o.sizeInBits
                if obj.sizeInBits == o.sizeInBits:
                    gotCalculatedUnionSize = True
            else:
                calculatedSubstructSizeTotal += o.sizeInBits

        ### Check the goodness of an object's size relative to its substructures
        if (obj.sizeInBits == calculatedSubstructSizeTotal):
            obj.subStructSizeGood = 1

        ### Otherwise, something is not right about the size of the substructures
        ### Let's set the subStructSizeGood of all substructures to False
        elif ('bitfield' not in obj.structType) and \
                ('unnamed type' not in obj.fwStruct) and \
                (obj.depth > 1):
            for o in obj.memberList:
                o.subStructSizeGood = 0

                # if ('transport' in o.fwObject):
                #    print
                #    pprint(vars(o))
                #    print
                #    pprint(vars(obj))
                #    print
                #    print "obj.sizeInBits", obj.sizeInBits
                #    print "calculatedSubstructSizeTotal", calculatedSubstructSizeTotal
                #    pressReturnToContinue('3.6')

        #### Set subStructSizeGood status for the any object's subStructs
        if (obj.structType and obj.fwStruct):
            if ('bitfield' not in obj.structType) and ('unnamed type' not in obj.fwStruct):
                for o in obj.memberList:
                    if (not obj.subStructSizeGood):
                        o.subStructSizeGood = 0

    def printObjectInfo(self, obj, oFile, structNum=None):
        """Performs console print of the object information to a file."""
        arrayDimString = ''

        arrayDimString = str(obj.arrayDimList[0])
        for i in range(len(obj.arrayDimList)):
            if i > 0: arrayDimString += "*" + str(obj.arrayDimList[i])

        if obj.memberList == []:
            oFile.write('%s,%s,%s,%s,%s,%s,0x%04X,0x%04X,%s,\"%s\",%s\n' % \
                        (obj.fwStruct, str(obj.fwObject), obj.structType, str(obj.sizeInBits),
                         arrayDimString, str(obj.uid), int(obj.versionMajor), int(obj.versionMinor),
                         str(obj.subStructSizeGood), str(obj.ancestryNames), ''))
            return
        else:
            if (obj.depth == 1):
                oFile.write('%s,%s,%s,%s,%s,%s,0x%04X,0x%04X,%s,\"%s\",%s\n' % \
                            (obj.fwStruct, str(obj.fwObject), obj.structType, str(obj.sizeInBits),
                             arrayDimString, str(obj.uid), int(obj.versionMajor), int(obj.versionMinor),
                             str(obj.subStructSizeGood), str(obj.ancestryNames), 'ObjectStart'))

            elif (obj.structType == 'union'):
                oFile.write('%s,%s,%s,%s,%s,%s,0x%04X,0x%04X,%s,\"%s\",%s\n' % \
                            (obj.fwStruct, str(obj.fwObject), obj.structType, str(obj.sizeInBits),
                             arrayDimString, str(obj.uid), int(obj.versionMajor), int(obj.versionMinor),
                             str(obj.subStructSizeGood), str(obj.ancestryNames), 'Union%i%iStart' % (obj.depth, structNum)))
            else:
                oFile.write('%s,%s,%s,%s,%s,%s,0x%04X,0x%04X,%s,\"%s\",%s\n' % \
                            (obj.fwStruct, str(obj.fwObject), obj.structType, str(obj.sizeInBits),
                             arrayDimString, str(obj.uid), int(obj.versionMajor), int(obj.versionMinor),
                             str(obj.subStructSizeGood), str(obj.ancestryNames), 'Struct%i%iStart' % (obj.depth, structNum)))

            for i in range(len(obj.memberList)):
                self.printObjectInfo(obj.memberList[i], oFile, i + 1)

            if (obj.depth == 1):
                oFile.write('%s,%s,%s,%s,%s,%s,0x%04X,0x%04X,%s,\"%s\",%s\n' % \
                            (obj.fwStruct, str(obj.fwObject), obj.structType, str(obj.sizeInBits),
                             arrayDimString, str(obj.uid), int(obj.versionMajor), int(obj.versionMinor),
                             str(obj.subStructSizeGood), str(obj.ancestryNames), 'ObjectEnd'))

            elif (obj.structType == 'union'):
                oFile.write('%s,%s,%s,%s,%s,%s,0x%04X,0x%04X,%s,\"%s\",%s\n' % \
                            (obj.fwStruct, str(obj.fwObject), obj.structType, str(obj.sizeInBits),
                             arrayDimString, str(obj.uid), int(obj.versionMajor), int(obj.versionMinor),
                             str(obj.subStructSizeGood), str(obj.ancestryNames), 'Union%i%iEnd' % (obj.depth, structNum)))
            else:
                oFile.write('%s,%s,%s,%s,%s,%s,0x%04X,0x%04X,%s,\"%s\",%s\n' % \
                            (obj.fwStruct, str(obj.fwObject), obj.structType, str(obj.sizeInBits),
                             arrayDimString, str(obj.uid), int(obj.versionMajor), int(obj.versionMinor),
                             str(obj.subStructSizeGood), str(obj.ancestryNames), 'Struct%i%iEnd' % (obj.depth, structNum)))

    def outputObjectCsv(self, obj):
        """Performs an collection of information to output CSV formated file."""
        outFile = os.path.join(self.parsersFolder, obj.fwObject + '.csv')

        cannotOpenFileForWrite = False
        while (not cannotOpenFileForWrite):
            try:
                with open(outFile, "wb") as oFile:
                    oFile.write('TypeDef,FieldName,Type,SizeInBits,ArrayDim,UID,versionMajor,versionMinor,sizeGood,ancestryNames,Start/End\n')
                    self.printObjectInfo(obj, oFile)
                cannotOpenFileForWrite = True
            except IOError as e:
                if e.errno == errno.EACCES:
                    usersInput = input("File access error.  Close %s before proceeding (q=quit): " % (outFile))
                    if (usersInput.lower() in ['q', 'quit']): quit(21)
                    cannotOpenFileForWrite = False
                else:
                    raise (IOError, e)

    def hasSimpleMemberWithGoodSize(self, obj):
        """Performs a definition check for name and size."""
        simpleMemberWithGoodSize = False
        if (len(obj.memberList) > 0):
            for o in obj.memberList:
                if (len(o.memberList) <= 0):
                    hasSimpleMember = True
                    if obj.subStructSizeGood:
                        simpleMemberWithGoodSize = True

        return simpleMemberWithGoodSize

    def hasSimpleMemberWithGoodSizeMaxSize(self, obj):
        """Performs a definition check for name and approporate size."""
        simpleMemberWithGoodSize = False
        memberObject = None

        if (len(obj.memberList) > 0):
            for o in obj.memberList:
                if (len(o.memberList) <= 0) and obj.subStructSizeGood:
                    if (not simpleMemberWithGoodSize):
                        simpleMemberWithGoodSize = True
                        memberObject = o
                    elif (memberObject.sizeInBits > o.sizeInBits):
                        memberObject = o

        return memberObject

    def writeObjectParserPy(self, obj, pyParserFile, prependStr=''):
        """Performs an extraction of the C definition to python c-type."""
        if len(obj.memberList) > 0:
            pyParserFile.write('# %s%s %s\n' % ((obj.depth * 2) * ' ', obj.fwObject, obj.structType))

        elif not obj.subStructSizeGood:
            # pyParserFile.write('# %s%s %s\n' % ((obj.depth*2)*' ',obj.fwObject,obj.structType))

            if (len(obj.ancestryTypes) > 1) and (obj.ancestryTypes[1] in ['union']):
                pyParserFile.write('# %s%s %s\n' % ((obj.depth * 2) * ' ', obj.fwObject, obj.structType))

            elif (obj.parent is not None) and (obj.parent.subStructSizeGood):
                self.log.debug("Good parent >>>%-40s, %50s, %50s" % (obj.fwObject, str(obj.ancestryTypes), str(obj.ancestryNames)))
            else:
                self.log.debug("Bad parent  >>>%-40s, %50s, %50s" % (obj.fwObject, str(obj.ancestryTypes), str(obj.ancestryNames)))

        elif (len(obj.altMemberList) <= 0):  # integrate array checking into altmemberlist flow
            if (obj.fwObject == 'autoParserToken'):
                pyParserFile.write('%-4s%-35s, %6s, %6s, %7s, %6s, %6s, %-35s,\n' % \
                                   (prependStr + '', '\'' + obj.fwObject + '\'', str(obj.sizeInBits), '0', '0', 'bdSTR', 'None', '\'' + obj.fwObject + '\''))
            else:
                pyParserFile.write('%-4s%-35s, %6s, %6s, %7s, %6s, %6s, %-35s,\n' % \
                                   (prependStr + '', '\'' + obj.fwObject + '\'', str(obj.sizeInBits), '0', '0', 'bdDEC', 'None', '\'' + obj.fwObject + '\''))

        if (len(obj.altMemberList) > 0) and (obj.depth > 1):
            for o in obj.altMemberList:
                self.writeObjectParserPy(o, pyParserFile, '')

        else:
            if (obj.structType in ['union']):
                simpleMemberWithGoodSizeObj = self.hasSimpleMemberWithGoodSize(obj)
                simpleMemberWithGoodSizeMaxSizeObj = self.hasSimpleMemberWithGoodSizeMaxSize(obj)
                for o in obj.memberList:

                    if (simpleMemberWithGoodSizeMaxSizeObj is not None):
                        if (o.fwObject != simpleMemberWithGoodSizeMaxSizeObj.fwObject):
                            continue

                    self.writeObjectParserPy(o, pyParserFile, '')

                    if len(o.memberList) > 0:
                        pyParserFile.write('# %s%s %s\n' % ((o.depth * 2) * ' ', o.fwObject, o.structType))

                    if (obj.structType in ['union']): break

            else:
                for o in obj.memberList:
                    self.writeObjectParserPy(o, pyParserFile, '')
                    if len(o.memberList) > 0:
                        pyParserFile.write('# %s%s %s\n' % ((o.depth * 2) * ' ', o.fwObject, o.structType))

        if obj.depth == 1:
            pyParserFile.write('# %s%s %s\n' % ((obj.depth * 2) * ' ', obj.fwObject, obj.structType))

    def generateObjectParserPy(self, obj):
        """Performs an object generation from C to python c-type."""
        ### Creating [fwObject].py file in the telemetry parsers folder, one per object.
        outParserFile = os.path.join(self.parsersFolder, obj.fwObject + '.py')
        with open(outParserFile, "wb") as pyParserFile:
            telemetryParserTxt = "\"\"\""
            telemetryParserTxt += "This file is automatically generated per Telemetry object.  Please do not modify."
            telemetryParserTxt += "\"\"\""
            telemetryParserTxt += "\nfrom bufdict import *\n\n"
            telemetryParserTxt += "%s_Description_%i_%i = \\\n" % (obj.fwObject[0].upper() + obj.fwObject[1:], obj.versionMajor, obj.versionMinor)
            telemetryParserTxt += "[\n"
            telemetryParserTxt += "%-4s%-35s, %6s, %6s, %7s, %6s, %6s, %-35s\n" % ("#", "name", "size", "signed", "default", "style", "token", "desc")
            pyParserFile.write(telemetryParserTxt)

            self.writeObjectParserPy(obj, pyParserFile)

            telemetryParserTxt = "]\n\n"
            telemetryParserTxt += "%s_dict = {\n" % (obj.fwObject)
            telemetryParserTxt += "%s(%i,%i): %s_Description_%i_%i,\n" % ((len(obj.fwObject) + 9) * ' ', obj.versionMajor, obj.versionMinor, obj.fwObject[0].upper() + obj.fwObject[1:], obj.versionMajor, obj.versionMinor)
            telemetryParserTxt += "%s}\n\n" % ((len(obj.fwObject) + 8) * ' ')
            telemetryParserTxt += "class %s(bufdict):\n" % (obj.fwObject[0].upper() + obj.fwObject[1:])
            telemetryParserTxt += "    \"%s\"\n" % (obj.fwObject[0].upper() + obj.fwObject[1:])
            telemetryParserTxt += "    def __init__(self, buf=None, offset=None, filename=None, other=None, namesize=30, valuesize=10, majorVersion=%i, minorVersion=%i):\n\n" % (obj.versionMajor, obj.versionMinor)
            telemetryParserTxt += "        description = getDescription(desc_dict=%s_dict, key=(majorVersion, minorVersion))\n" % (obj.fwObject)
            telemetryParserTxt += "        bufdict.__init__(self, description=description, version=majorVersion,name=\"%s\",\\\n" % (obj.fwObject)
            telemetryParserTxt += "                         namesize=namesize, valuesize=valuesize, filename=filename, buf=buf, other=other)\n\n"
            telemetryParserTxt += "        pass\n"
            pyParserFile.write(telemetryParserTxt)

        ### Creating telemetryCmd.py file in the telemetry commands folder
        # telemetryCmdTxt  = "import __init__\n" # fix __init__ in gen3/tools/telemetry importing getRoot incorrectly before uncommenting
        telemetryCmdTxt = "import sys\n"
        telemetryCmdTxt += "import importlib\n"
        telemetryCmdTxt += "import os\n\n"
        telemetryCmdTxt += "mapping     = {\n"

        for i in range(len(self.telemetryObjectListAll)):
            fwObject = self.telemetryObjectListAll[i][0]
            uid = self.telemetryObjectListAll[i][1]
            if re.search('^[0-9a-fx]+$', uid.lower()):
                telemetryCmdTxt += "               %s: \'%s\',\n" % (uid, fwObject)

        telemetryCmdTxt += "              }\n\n"
        telemetryCmdTxt += "class TelemetryObjectCommands(object):\n\n"
        telemetryCmdTxt += "    def __init__(self, devObj=None):\n"
        telemetryCmdTxt += "        self._devObj = devObj\n\n"
        telemetryCmdTxt += "    def parseTelemetry(self, objectId, inFile=None, projObjFile=None):\n"
        telemetryCmdTxt += "        '''\n"
        telemetryCmdTxt += "        read the Telemetry object\n"
        telemetryCmdTxt += "        '''\n"
        telemetryCmdTxt += "        os.sys.path.insert(1, r'%s'%(projObjFile))\n"
        telemetryCmdTxt += "        exec(\"from telemetry.parsers.%s import %s\" % (mapping[objectId],mapping[objectId][0].upper()+mapping[objectId][1:]))\n"
        telemetryCmdTxt += "        myObj = eval(\"%s()\" % (mapping[objectId][0].upper()+mapping[objectId][1:]))\n"
        telemetryCmdTxt += "        if inFile is not None:\n"
        telemetryCmdTxt += "            myObj.from_file(filename=inFile)\n"
        telemetryCmdTxt += "        else:\n"
        telemetryCmdTxt += "           myObj.from_buf(self._devObj.getReadBuffer())\n"
        telemetryCmdTxt += "        return myObj\n"

        outCmdFile = os.path.join(self.commandsFolder, 'telemetryCmd.py')
        with open(outCmdFile, "wb") as pyCmdFile:
            pyCmdFile.write(telemetryCmdTxt)

        initFileText = "\"\"\""
        initFileText += "    __init__.py - This file makes this folder a Python package."
        initFileText += "\"\"\"\n"
        initFileText += "import os\n"
        initFileText += "os.sys.path.insert(1,'..')\n"

        ### Creating __init__.py file in the telemetry folder
        outParserInitFile = os.path.join(self.telemetryFolder, '__init__.py')
        with open(outParserInitFile, "wb") as pyParserInitFile:
            pyParserInitFile.write(initFileText)

        ### Creating __init__.py file in the telemetry commands folder
        outCmdInitFile = os.path.join(self.commandsFolder, '__init__.py')
        with open(outCmdInitFile, "wb") as pyCmdInitFile:
            pyCmdInitFile.write(initFileText)

        ### Creating __init__.py file in the telemetry parsers folder
        outParserInitFile = os.path.join(self.parsersFolder, '__init__.py')
        with open(outParserInitFile, "wb") as pyParserInitFile:
            pyParserInitFile.write(initFileText)

        ### Copying bufdict.py and bufdata.py into the telemetry parsers folder
        shutil.copy(os.path.join(self.fwToolsDir, 'bufdict.py'), self.parsersFolder)
        shutil.copy(os.path.join(self.fwToolsDir, 'bufdata.py'), self.parsersFolder)

    def setAncestryType(self, obj):
        """Performs an mutation on the ancestory of the object."""
        if (len(obj.memberList) > 0):
            for o in obj.memberList:
                o.ancestryTypes = [obj.structType] + obj.ancestryTypes
                self.setAncestryType(o)

    def getVarNameListToDedup(self, obj):
        """Performs a reduction of duplicated definitions."""
        if len(obj.memberList) > 0:
            for o in obj.memberList:
                self.getVarNameListToDedup(o)

        elif obj.subStructSizeGood:
            if obj.fwObject in self.varNameList:
                if obj.fwObject not in self.varNameListToDedup:
                    self.varNameListToDedup.append(obj.fwObject)
            else:
                self.varNameList.append(obj.fwObject)

    def dedupVarNames(self, obj, ancestryLevel=0):
        """Performs an reduction of the variable definitions."""
        if len(obj.memberList) > 0:
            for o in obj.memberList:
                self.dedupVarNames(o, ancestryLevel=ancestryLevel)

        elif (obj.subStructSizeGood and (obj.fwObject in self.varNameListToDedup)):
            # print obj.ancestryNames,obj.fwObject,ancestryLevel,"\tAbout to modify fwObject"
            if (obj.ancestryNames[ancestryLevel] != '0') and \
                    (not matchSequence[4].match(obj.ancestryNames[ancestryLevel])) and \
                    (not matchSequence[5].match(obj.ancestryNames[ancestryLevel])):

                tmpAncestryName = ''
                if ('_' in obj.ancestryNames[ancestryLevel]):
                    tmpAncestryNameWordList = re.sub('_s$', '', obj.ancestryNames[ancestryLevel]).split('_')
                    for t in tmpAncestryNameWordList:
                        tmpAncestryName += t[0].upper() + t[1:].lower()
                    tmpAncestryName = tmpAncestryName[0].lower() + tmpAncestryName[1:]
                else:
                    tmpAncestryName = obj.ancestryNames[ancestryLevel][0].lower() + obj.ancestryNames[ancestryLevel][1:]

                obj.fwObject = tmpAncestryName + obj.fwObject[0].upper() + obj.fwObject[1:]

    def checkSubstructSizeGood(self, obj):
        """Performs a child definition check."""
        if len(obj.memberList) <= 0:
            return (obj.subStructSizeGood == 1)

        for o in obj.memberList:
            if (o.subStructSizeGood != 1):
                return False

        return True

    def paddSubstructSizeIfNeeded(self, obj):
        """Performs a child definition construction."""
        myObj = None
        myObj2 = None

        if len(obj.memberList) <= 0: return
        if (obj.structType != 'union'): return

        maxSizeInBits = obj.sizeInBits

        for o in obj.memberList:
            if (o.sizeInBits < maxSizeInBits):
                exec("myObj = GenericObject()")
                myObj.subStructSizeGood = 1
                myObj.arrayDimList = [1]
                myObj.depth = o.depth + 1
                myObj.endLineNum = o.endLineNum
                myObj.fwObject = o.fwObject
                myObj.fwStruct = 'altobj'
                myObj.parent = o
                myObj.ancestryNames = [o.fwObject] + o.ancestryNames
                myObj.memberList = []
                myObj.altMemberList = []
                myObj.sizeInBits = o.sizeInBits
                myObj.startLineNum = o.startLineNum
                myObj.structType = 'var'
                myObj.isPointer = 0
                myObj.uid = o.uid
                myObj.versionMajor = 0xBADD  ### Default
                myObj.versionMajorStr = 'versionMajor'  ### Default
                myObj.versionMinor = 0xC0DE  ### Default
                myObj.versionMinorStr = 'versionMinor'  ### Default

                exec("myObj2 = GenericObject()")
                myObj2.subStructSizeGood = 1
                myObj2.arrayDimList = [1]
                myObj2.depth = o.depth + 1
                myObj2.endLineNum = o.endLineNum
                myObj2.fwObject = o.fwObject + 'pad'
                myObj2.fwStruct = 'altobj'
                myObj2.parent = o
                myObj2.ancestryNames = [o.fwObject] + o.ancestryNames
                myObj2.memberList = []
                myObj2.altMemberList = []
                myObj2.sizeInBits = maxSizeInBits - o.sizeInBits
                myObj2.startLineNum = o.startLineNum
                myObj2.structType = 'var'
                myObj2.isPointer = 0
                myObj2.uid = o.uid
                myObj2.versionMajor = 0xBADD  ### Default
                myObj2.versionMajorStr = 'versionMajor'  ### Default
                myObj2.versionMinor = 0xC0DE  ### Default
                myObj2.versionMinorStr = 'versionMinor'  ### Default
                o.altMemberList = [myObj, myObj2]

    def generateAltMemberList(self, obj):
        """
        When a struct has good size state, but its substructs do not, we need
        to fill in its altMemberList with a single new objects of correct size.
        """
        myObj = None
        if (len(obj.memberList) <= 0):
            return

        if (not matchSequence[5].match(obj.fwObject)) and (obj.fwObject != '0'):
            if (not self.checkSubstructSizeGood(obj)):
                exec("myObj = GenericObject()")
                myObj.subStructSizeGood = 1
                myObj.arrayDimList = [1]
                myObj.depth = obj.depth + 1
                myObj.endLineNum = obj.endLineNum
                myObj.fwObject = obj.fwObject + 'AltObject'
                myObj.fwStruct = 'altobj'
                myObj.parent = obj
                myObj.ancestryNames = [obj.fwObject] + obj.ancestryNames
                myObj.memberList = []
                myObj.altMemberList = []
                myObj.sizeInBits = obj.sizeInBits
                myObj.startLineNum = obj.startLineNum
                myObj.structType = 'var'
                myObj.isPointer = 0
                myObj.uid = obj.uid
                myObj.versionMajor = 0xBADD  ### Default
                myObj.versionMajorStr = 'versionMajor'  ### Default
                myObj.versionMinor = 0xC0DE  ### Default
                myObj.versionMinorStr = 'versionMinor'  ### Default
                obj.altMemberList = [myObj]
                # self.log.debug('%s fwObject has been created for %s' % (myObj.fwObject,obj.fwObject))

            if (obj.structType == 'union'):
                self.paddSubstructSizeIfNeeded(obj)

        for o in obj.memberList:
            self.generateAltMemberList(o)

    def generatePythonCtypes(self):
        """Performs the transformation of the fundamental type to Python c-type."""
        self.createMasterObjectListUidValue()
        self.getObjectsFromStructDefFile()

        if (self.options.dataObjToProcess is not None):
            specifiedObjectFound = False

        for i in range(len(self.objectsInStructDefFile)):
            fwObject = self.objectsInStructDefFile[i][0]
            fwStruct = self.objectsInStructDefFile[i][1]
            uid = self.objectsInStructDefFile[i][2]

            if (self.options.dataObjToProcess is not None):
                if fwObject != self.options.dataObjToProcess:
                    continue
                else:
                    specifiedObjectFound = True

            obj = self.buildStruct(uid, fwObject, fwStruct)

            self.determineObjectSizes(obj)

            self.auditStructSizes(obj)

            ### if struct has good size, but substructs do not.  Need to generate altMemberList
            self.generateAltMemberList(obj)

            if (self.options.extraDebug):
                self.outputObjectCsv(obj)

            self.setAncestryType(obj)

            dedupIteration = 0
            self.varNameList = []
            self.varNameListToDedup = []
            self.getVarNameListToDedup(obj)

            while len(self.varNameListToDedup) > 0:
                if (self.options.verbose):
                    print("+++++++++++++++++++++++++++++++++++++++")
                    print("Variable name dedup iteration: #%i" % (dedupIteration))
                    print("Dedup %s" % (obj.fwObject))
                    print("---------------------------------------")
                    for v in self.varNameListToDedup: print(v)
                    print("---------------------------------------")

                self.dedupVarNames(obj, dedupIteration)

                dedupIteration += 1
                self.varNameList = []
                self.varNameListToDedup = []
                self.getVarNameListToDedup(obj)

            self.generateObjectParserPy(obj)

        if (self.options.dataObjToProcess is not None):
            if (not specifiedObjectFound): print("\n>>> Specified ojbect (%s) is not found")

    def __skipNamedUnionSubstruct(self, lines, index):
        """Performs a child definition skip."""
        depth = 0
        bLine = None
        eLine = None

        ### Find the start and end line numbers for the specified object
        for i in range(index, len(lines)):
            if ('{' in lines[i]):
                depth += 1
                if depth == 1: bLine = i
            elif ('}' in lines[i]):
                depth -= 1
                if depth == 0:
                    eLine = i
                    break

        if (self.options.debug):
            print("depth: %i, bLine: %i, eLine: %i" % (depth, bLine, eLine))
            pressReturnToContinue('skipNamedUnionStruct')

        subStructLevel = 0
        for i in range(bLine, eLine + 1):
            myLine = lines[i].strip()
            myLine = re.sub('^ +', '', myLine)  # take out spaces before actual text
            myLine = re.sub(' +', ' ', myLine)  # take out extra spaces after '=' sign
            myLine = re.sub(' +$', '', myLine)  # take out extra spaces at the end of the line
            myLine = re.sub('\] \[', '][', myLine)  # take out extra spaces between array dim []
            # print i+1,subStructLevel,myLine
            # pressReturnToContinue()
            if ('{' in myLine):
                subStructLevel += 1
            elif ('}' in myLine):
                subStructLevel -= 1
            elif subStructLevel == 1:
                # print "Going back"
                return bLine, eLine, i

        # print "Going back"
        return bLine, eLine, 0

    def __buildStruct(self, lines, obj, startIndex=None, endIndex=None):
        """Performs a definition construction."""
        myObj = None
        o = None
        if (self.options.verbose):
            print("\n***********************************")
            print("Object at __buildStruct Entry point")
            pprint(vars(obj))
            print("***********************************")
            curStructDepth = obj.depth

        if (startIndex is None):
            startIndex = obj.startLineNum
        if (endIndex is None):
            endIndex = obj.endLineNum

        # print "startIndex:   ",startIndex
        # print "endIndex:     ",endIndex
        # print "obj.fwStruct: ",obj.fwStruct
        # print "obj.depth:    ",obj.depth
        # pressReturnToContinue()

        # print "startIndex:   ",startIndex
        # print "endIndex:     ",endIndex
        # print "obj.fwStruct: ",obj.fwStruct
        # print "obj.depth:    ",obj.depth
        # pressReturnToContinue()

        index = startIndex
        while (index < endIndex):

            ### pre-process the text line
            myLine = lines[index].strip()
            # myLine = re.sub('volatile ',' ',myLine)        # take out spaces before actual text
            # myLine = re.sub('static ',' ',myLine)        # take out spaces before actual text
            # myLine = re.sub('const ',' ',myLine)        # take out spaces before actual text
            myLine = re.sub('^ +', '', myLine)  # take out spaces before actual text
            myLine = re.sub(' +', ' ', myLine)  # take out extra spaces after '=' sign
            myLine = re.sub(' +$', '', myLine)  # take out extra spaces at the end of the line
            myLine = re.sub('\] \[', '][', myLine)  # take out extra spaces between array dim []

            if (self.options.debug):
                print("\n>>>>%s" % lines[index].strip())
                print(">>>>%s\n" % myLine)

            ###############################################################################
            # '^union {'
            if matchSequence[6].match(myLine):
                m = matchSequence[6].match(myLine)
                # self.log.debug('(0) %3i ' % (index+1) + lines[index])
                if (self.options.extraDebug): self.outputObjectStructText(lines[index], append=True)
                obj.structType = 'union'
                obj.depth = 1

                if (self.options.debug):
                    pprint(vars(obj))
                    pressReturnToContinue('0')

                index += 1
                continue


            ###############################################################################
            # '^struct/structName_t {'
            elif matchSequence[7].match(myLine):
                m = matchSequence[7].match(myLine)
                # self.log.debug('(1) %3i ' % (index+1) + lines[index])
                if (self.options.extraDebug): self.outputObjectStructText(lines[index], append=True)
                obj.depth = 1
                obj.structType = 'struct'

                if (self.options.debug):
                    pprint(vars(obj))
                    pressReturnToContinue('1')

                index += 1
                continue


            ###############################################################################
            # 'hexnum struct/union {'
            elif matchSequence[8].match(myLine):
                m = matchSequence[8].match(myLine)
                # self.log.debug('(2) %3i' % (index+1) + lines[index])
                if (self.options.extraDebug): self.outputObjectStructText(lines[index], append=True)
                exec("myObj = GenericObject()")
                myObj.arrayDimList = [1]
                myObj.depth = obj.depth + 1
                myObj.endLineNum = obj.endLineNum
                myObj.fwObject = m.group(1)
                myObj.fwStruct = m.group(2)
                # self.log.debug('fwStruct = %s' % myObj.fwStruct)
                myObj.parent = obj
                myObj.ancestryNames = [obj.fwObject] + obj.ancestryNames
                myObj.memberList = []
                myObj.altMemberList = []
                myObj.sizeInBits = 0
                myObj.startLineNum = index + 1
                myObj.structType = m.group(2)
                myObj.isPointer = 0
                myObj.uid = obj.uid
                myObj.versionMajor = 0xBADD  ### Default
                myObj.versionMajorStr = 'versionMajor'  ### Default
                myObj.versionMinor = 0xC0DE  ### Default
                myObj.versionMinorStr = 'versionMinor'  ### Default

                if (self.options.debug):
                    print("Before -- Index:", index)
                    pprint(vars(obj))
                    pressReturnToContinue('2')

                obj.memberList.append(self.__buildStruct(lines, obj=myObj))
                index = obj.memberList[-1].endLineNum + 1

                if (self.options.debug):
                    pprint(vars(obj))
                    pressReturnToContinue('2.1')

                continue


            ###############################################################################
            # hexNum union thing1 {
            elif matchSequence[9].match(myLine):
                m = matchSequence[9].match(myLine)
                # self.log.debug('(3) %3i ' % (index+1) + lines[index])
                if (self.options.extraDebug): self.outputObjectStructText(lines[index], append=True)
                exec("myObj = GenericObject()")
                myObj.arrayDimList = [1]
                myObj.depth = obj.depth + 1
                myObj.endLineNum = obj.endLineNum
                myObj.fwObject = m.group(2)
                myObj.fwStruct = 'union'
                # self.log.debug('fwStruct = %s' % myObj.fwStruct)
                myObj.parent = obj
                myObj.ancestryNames = [obj.fwObject] + obj.ancestryNames
                myObj.memberList = []
                myObj.sizeInBits = 0
                myObj.startLineNum = index + 1
                myObj.structType = 'union'
                myObj.isPointer = 0
                myObj.uid = obj.uid
                myObj.versionMajor = 0xBADD  ### Default
                myObj.versionMajorStr = 'versionMajor'  ### Default
                myObj.versionMinor = 0xC0DE  ### Default
                myObj.versionMinorStr = 'versionMinor'  ### Default

                if (self.options.debug):
                    print("Before -- Index:", index)
                    pprint(vars(obj))
                    pressReturnToContinue('3')

                bLine, eLine, lineNum = self.__skipNamedUnionSubstruct(lines, index)

                if (self.options.debug):
                    print(bLine, eLine, lineNum)
                    print(lines[lineNum])

                obj.memberList.append(self.__buildStruct(lines, obj=myObj, startIndex=lineNum, endIndex=lineNum + 1))
                if (self.options.extraDebug): self.outputObjectStructText(lines[eLine], append=True)
                index = eLine + 1

                if (self.options.debug):
                    print("After -- Index:", index)
                    print("\n>>>>>%s" % lines[index])

                    print
                    pprint(vars(obj.memberList[-1]))
                    print
                    pprint(vars(obj))
                    pressReturnToContinue('3.1')

                continue

            ###############################################################################
            # hexNum struct thing1 {
            elif matchSequence[10].match(myLine):
                m = matchSequence[10].match(myLine)
                # self.log.debug('(4) %3i ' % (index+1) + lines[index])
                if (self.options.extraDebug): self.outputObjectStructText(lines[index], append=True)
                exec("myObj = GenericObject()")
                myObj.arrayDimList = [1]
                myObj.depth = obj.depth + 1
                myObj.endLineNum = obj.endLineNum
                myObj.fwObject = m.group(3)
                myObj.fwStruct = m.group(2)
                # self.log.debug('fwStruct = %s' % myObj.fwStruct)
                myObj.parent = obj
                myObj.ancestryNames = [obj.fwObject] + obj.ancestryNames
                myObj.memberList = []
                myObj.sizeInBits = 0
                myObj.startLineNum = index + 1
                myObj.structType = 'struct'
                myObj.isPointer = 0
                myObj.uid = obj.uid
                myObj.versionMajor = 0xBADD  ### Default
                myObj.versionMajorStr = 'versionMajor'  ### Default
                myObj.versionMinor = 0xC0DE  ### Default
                myObj.versionMinorStr = 'versionMinor'  ### Default

                if (self.options.debug):
                    print("Before -- Index:", index)
                    pprint(vars(obj))
                    pressReturnToContinue('4.1')

                obj.memberList.append(self.__buildStruct(lines, obj=myObj))
                index = obj.memberList[-1].endLineNum + 1

                if (self.options.debug):
                    print("After -- Index:", index)
                    pprint(vars(obj))
                    pressReturnToContinue('4.2')

                continue


            ###############################################################################
            # objName = name_t {
            # @todo:  Question -- Do we need a separate handler for 'something = union {'??
            elif matchSequence[11].match(myLine):
                m = matchSequence[11].match(myLine)
                # self.log.debug('(5) %3i ' % (index+1) + lines[index])
                if (self.options.extraDebug): self.outputObjectStructText(lines[index], append=True)
                exec("myObj = GenericObject()")
                myObj.arrayDimList = [1]
                myObj.depth = obj.depth + 1
                myObj.endLineNum = obj.endLineNum
                myObj.fwObject = m.group(1)
                myObj.fwStruct = m.group(2)
                # self.log.debug('fwStruct = %s' % myObj.fwStruct)
                myObj.parent = obj
                myObj.ancestryNames = [obj.fwObject] + obj.ancestryNames
                myObj.memberList = []
                myObj.sizeInBits = 0
                myObj.startLineNum = index + 1
                myObj.structType = 'struct'
                myObj.isPointer = 0
                myObj.uid = obj.uid
                myObj.versionMajor = 0xBADD  ### Default
                myObj.versionMajorStr = 'versionMajor'  ### Default
                myObj.versionMinor = 0xC0DE  ### Default
                myObj.versionMinorStr = 'versionMinor'  ### Default

                if (self.options.debug):
                    print(">>>>> Before -- Index:", index)
                    pprint(vars(obj))
                    print;
                    print(">>>>>>>" + lines[index])
                    pressReturnToContinue('5')

                obj.memberList.append(self.__buildStruct(lines, obj=myObj))
                index = obj.memberList[-1].endLineNum + 1

                if (self.options.debug):
                    print(">>>>> After -- Index:", index)
                    pprint(vars(obj))
                    print;
                    print(">>>>>>>" + lines[index])
                    pressReturnToContinue('5.1')

                continue  ### Continue since the index is already point to the next line to be processed

            ###############################################################################
            # 'objName = union name_t {' as in 'xyz = struct/union xyz_t {'
            elif matchSequence[12].match(myLine):
                m = matchSequence[12].match(myLine)
                # self.log.debug('(6) %3i ' % (index+1) + lines[index])
                if (self.options.extraDebug): self.outputObjectStructText(lines[index], append=True)
                exec("myObj = GenericObject()")
                myObj.arrayDimList = [1]
                myObj.depth = obj.depth + 1
                myObj.endLineNum = obj.endLineNum
                myObj.fwObject = m.group(1)
                myObj.fwStruct = m.group(2)
                # self.log.debug('fwStruct = %s' % myObj.fwStruct)
                myObj.parent = obj
                myObj.ancestryNames = [obj.fwObject] + obj.ancestryNames
                myObj.memberList = []
                myObj.sizeInBits = 0
                myObj.startLineNum = index + 1
                myObj.structType = 'union'
                myObj.isPointer = 0
                myObj.uid = obj.uid
                myObj.versionMajor = 0xBADD  ### Default
                myObj.versionMajorStr = 'versionMajor'  ### Default
                myObj.versionMinor = 0xC0DE  ### Default
                myObj.versionMinorStr = 'versionMinor'  ### Default

                if (self.options.debug):
                    print("Before -- Index:", index)
                    pprint(vars(obj))
                    pressReturnToContinue('6')

                obj.memberList.append(self.__buildStruct(lines, obj=myObj))
                index = obj.memberList[-1].endLineNum + 1

                if (self.options.debug):
                    print("After -- Index:", index)
                    print("\n>>>>>%s" % lines[index])

                    print
                    pprint(vars(obj.memberList[-1]))
                    print
                    pprint(vars(obj))

                    pressReturnToContinue('6.1')

                continue

            ###############################################################################
            # 'objName = union name_t {'
            # Filtering Union then Struct detection...
            # @todo Duplication possibly remove. Walk through the code to ensure the case is detected.
            elif matchSequence[12].match(myLine):
                m = matchSequence[13].match(myLine)
                # self.log.debug('(7) %3i ' % (index+1) + lines[index])
                if (self.options.extraDebug): self.outputObjectStructText(lines[index], append=True)
                exec("myObj = GenericObject()")
                myObj.arrayDimList = [1]
                myObj.depth = obj.depth + 1
                myObj.endLineNum = obj.endLineNum
                myObj.fwObject = m.group(1)
                myObj.fwStruct = m.group(3)
                # self.log.debug('fwStruct = %s' % myObj.fwStruct)
                myObj.parent = obj
                myObj.ancestryNames = [obj.fwObject] + obj.ancestryNames
                myObj.memberList = []
                myObj.sizeInBits = 0
                myObj.startLineNum = index + 1
                myObj.structType = 'union'
                myObj.isPointer = 0
                myObj.uid = obj.uid
                myObj.versionMajor = 0xBADD  ### Default
                myObj.versionMajorStr = 'versionMajor'  ### Default
                myObj.versionMinor = 0xC0DE  ### Default
                myObj.versionMinorStr = 'versionMinor'  ### Default

                if (self.options.debug):
                    print("Before -- Index:", index)
                    pprint(vars(obj))
                    pressReturnToContinue('7.1')

                obj.memberList.append(self.__buildStruct(lines, obj=myObj))
                index = obj.memberList[-1].endLineNum + 1

                if (self.options.debug):
                    print("After -- Index:", index)
                    pprint(vars(obj))
                    pressReturnToContinue('7.2')

                index += 1
                continue

            ###############################################################################
            # 'objName = struct name_t {' as in 'xyz = struct/union xyz_t {'
            elif matchSequence[13].match(myLine):
                m = matchSequence[13].match(myLine)
                # self.log.debug('(8) %3i ' % (index+1) + lines[index])
                if (self.options.extraDebug): self.outputObjectStructText(lines[index], append=True)
                exec("myObj = GenericObject()")
                myObj.arrayDimList = [1]
                myObj.depth = obj.depth + 1
                myObj.endLineNum = obj.endLineNum
                myObj.fwObject = m.group(1)
                myObj.fwStruct = m.group(3)
                # self.log.debug('fwStruct = %s' % myObj.fwStruct)
                myObj.parent = obj
                myObj.ancestryNames = [obj.fwObject] + obj.ancestryNames
                myObj.memberList = []
                myObj.sizeInBits = 0
                myObj.startLineNum = index + 1
                myObj.structType = 'struct'
                myObj.isPointer = 0
                myObj.uid = obj.uid
                myObj.versionMajor = 0xBADD  ### Default
                myObj.versionMajorStr = 'versionMajor'  ### Default
                myObj.versionMinor = 0xC0DE  ### Default
                myObj.versionMinorStr = 'versionMinor'  ### Default

                if (self.options.debug):
                    print("Before -- Index:", index)
                    pprint(vars(obj))
                    pressReturnToContinue('8.1')

                obj.memberList.append(self.__buildStruct(lines, obj=myObj))
                index = obj.memberList[-1].endLineNum

                if (self.options.debug):
                    print("After -- Index:", index)
                    pprint(vars(obj))
                    pressReturnToContinue('8.2')

                index = index + 1
                continue

            ###############################################################################
            # [typeSpecifier ... ] type name;
            # default types and any pointer is uint32_t
            # @todo special handling of void *cmdHandle;
            # @todo special handling of const struct smartSelectiveSelfTestSpan_t *pTestSpan;
            elif matchSequence[14].match(myLine):
                m = matchSequence[14].match(myLine)
                # self.log.debug('(9) %3i ' % (index+1) + lines[index])
                if (self.options.extraDebug): self.outputObjectStructText(lines[index], append=True)
                exec("myObj = GenericObject()")
                myObj.arrayDimList = [1]
                myObj.depth = obj.depth + 1
                myObj.endLineNum = index
                myObj.fwObject = m.group(2)
                myObj.fwStruct = m.group(1)
                # self.log.debug('fwStruct = %s' % myObj.fwStruct)
                myObj.parent = obj
                myObj.ancestryNames = [obj.fwObject] + obj.ancestryNames
                myObj.memberList = []
                myObj.sizeInBits = 0
                myObj.startLineNum = index
                # print("PCheck: " + str(myLine))
                isPointerDetected = detectBasicPointer.search(myLine)
                if (isPointerDetected):
                    myObj.fwStruct = 'void'
                    myObj.isPointer = 1
                    myObj.sizeInBits = ctypes.sizeof(eval(self.cToPythonCtypeMap["void"]))
                    myObj.structType = 'void'
                    # print ("   [Pointer]: " + str(myLine))
                else:
                    myObj.isPointer = 0
                    myObj.sizeInBits = 0
                    myObj.structType = m.group(1)
                myObj.uid = obj.uid
                myObj.versionMajor = 0xBADD  ### Default
                myObj.versionMajorStr = 'versionMajor'  ### Default
                myObj.versionMinor = 0xC0DE  ### Default
                myObj.versionMinorStr = 'versionMinor'  ### Default
                obj.memberList.append(myObj)

                # print "\n==================================="
                # pprint(vars(obj))
                # print "==================================="
                # pprint(vars(myObj))
                # print "==================================="
                # print lines[index].strip()
                # print "myLine",myLine
                # print "m.group(1)",m.group(1)
                # print "m.group(1)",m.group(1)
                # print "===================================\n"
                # pressReturnToContinue('simple line')

                index += 1
                continue

                # obj.sizeInBits = sizeof(eval(self.cToPythonCtypeMap[obj.fwStruct])) * 8 * eval(arrayDimString)

            ###############################################################################
            # typeSpecifier [typeSpecifier typeSpecifier ...] type arrayName[dim][dim]...;
            elif re.search('^([\w ]+) ([\[\w\]]+);$', myLine):
                m = re.search('^([\w ]+) ([\[\w\]]+);$', myLine)
                # self.log.debug('(10) %3i ' % (index+1) + lines[index])
                if (self.options.extraDebug): self.outputObjectStructText(lines[index], append=True)
                arrayString = re.sub('\]\[', ',', m.group(2))
                if (self.options.debug):
                    print(arrayString);
                    pressReturnToContinue('10.1')

                if re.search('^(\w+)\[([0-9,]+)\]', arrayString):
                    s = re.search('^(\w+)\[([0-9,]+)\]', arrayString)
                    dList = map(int, s.group(2).split(','))
                    if (self.options.debug):
                        print(dList);
                        pressReturnToContinue('10.2')
                else:
                    self.log.debug('(*10.3) %3i' % (index + 1) + lines[index])
                    if (self.options.extraDebug): self.outputObjectStructText('ARRAY_DIM_ERROR: ' + lines[index], append=True)
                    if (self.options.debug):
                        dList = None;
                        pressReturnToContinue('10.3')

                if (self.options.debug):
                    if len(dList) > 1:
                        print(lines[index])
                        print(arrayString)
                        print(dList)
                        if (self.options.debug):
                            pressReturnToContinue('10.4')

                if re.search('^struct (\w+)', m.group(1)):
                    n = re.search('^struct (\w+)', m.group(1))
                    #### @todo Special handling of struct nlogPrimaryBfrState_t primaryBfrState[5];
                    #### @todo Special handling of struct temperatureMonitoredDieAttribute_t temperatureMonitoredDieInfo[2] [4];
                    exec("myObj = GenericObject()")
                    myObj.arrayDimList = dList
                    myObj.depth = obj.depth + 1
                    myObj.endLineNum = index
                    myObj.fwObject = s.group(1)
                    myObj.fwStruct = n.group(1)
                    # self.log.debug('fwStruct = %s' % myObj.fwStruct)
                    myObj.parent = obj
                    myObj.ancestryNames = [obj.fwObject] + obj.ancestryNames
                    myObj.memberList = []  ### @todo parse array of substructs
                    myObj.sizeInBits = 0
                    myObj.startLineNum = index
                    myObj.structType = 'array'
                    myObj.isPointer = 0
                    myObj.uid = obj.uid
                    myObj.versionMajor = 0xBADD  ### Default
                    myObj.versionMajorStr = 'versionMajor'  ### Default
                    myObj.versionMinor = 0xC0DE  ### Default
                    myObj.versionMinorStr = 'versionMinor'  ### Default
                    obj.memberList.append(myObj)

                    # print lines[index].strip()
                    # print "myLine",myLine
                    # print "m.group(1)",m.group(1)
                    # print "n.group(1)",n.group(1)
                    # print "s.group(1)",s.group(1)
                    # pressReturnToContinue('if')

                elif re.search('^union (\w+)', m.group(1)):
                    n = re.search('^union (\w+)', m.group(1))
                    #### @todo Special handling of struct nlogPrimaryBfrState_t primaryBfrState[5];
                    exec("myObj = GenericObject()")
                    myObj.arrayDimList = dList
                    myObj.depth = obj.depth + 1
                    myObj.endLineNum = index
                    myObj.fwObject = s.group(1)
                    myObj.fwStruct = n.group(1)
                    # self.log.debug('fwStruct = %s' % myObj.fwStruct)
                    myObj.parent = obj
                    myObj.ancestryNames = [obj.fwObject] + obj.ancestryNames
                    myObj.memberList = []  ### @todo parse array of substructs
                    myObj.sizeInBits = 0
                    myObj.startLineNum = index
                    myObj.structType = 'array'
                    myObj.isPointer = 0
                    myObj.uid = obj.uid
                    myObj.versionMajor = 0xBADD  ### Default
                    myObj.versionMajorStr = 'versionMajor'  ### Default
                    myObj.versionMinor = 0xC0DE  ### Default
                    myObj.versionMinorStr = 'versionMinor'  ### Default
                    obj.memberList.append(myObj)

                    # print lines[index].strip()
                    # print "myLine",myLine
                    # print "m.group(1)",m.group(1)
                    # print "n.group(1)",n.group(1)
                    # print "s.group(1)",s.group(1)
                    # pressReturnToContinue('if')

                elif re.search('^enum (\w+)', m.group(1)):
                    n = re.search('^enum (\w+)', m.group(1))
                    #### @todo Special handling of struct nlogPrimaryBfrState_t primaryBfrState[5];
                    exec("myObj = GenericObject()")
                    myObj.arrayDimList = dList
                    myObj.depth = obj.depth + 1
                    myObj.endLineNum = index
                    myObj.fwObject = s.group(1)
                    myObj.fwStruct = n.group(1)
                    # self.log.debug('fwStruct = %s' % myObj.fwStruct)
                    myObj.parent = obj
                    myObj.ancestryNames = [obj.fwObject] + obj.ancestryNames
                    myObj.memberList = []  ### @todo parse array of substructs
                    myObj.sizeInBits = 0
                    myObj.startLineNum = index
                    myObj.structType = 'array'
                    myObj.isPointer = 0
                    myObj.uid = obj.uid
                    myObj.versionMajor = 0xBADD  ### Default
                    myObj.versionMajorStr = 'versionMajor'  ### Default
                    myObj.versionMinor = 0xC0DE  ### Default
                    myObj.versionMinorStr = 'versionMinor'  ### Default
                    obj.memberList.append(myObj)

                    # print lines[index].strip()
                    # print "myLine",myLine
                    # print "m.group(1)",m.group(1)
                    # print "n.group(1)",n.group(1)
                    # print "s.group(1)",s.group(1)
                    # pressReturnToContinue('if')

                else:
                    exec("myObj = GenericObject()")
                    myObj.arrayDimList = dList
                    myObj.depth = obj.depth + 1
                    myObj.endLineNum = index
                    myObj.fwObject = s.group(1)
                    myObj.fwStruct = m.group(1)
                    # self.log.debug('fwStruct = %s' % myObj.fwStruct)
                    myObj.parent = obj
                    myObj.ancestryNames = [obj.fwObject] + obj.ancestryNames
                    myObj.memberList = []
                    myObj.sizeInBits = 0
                    myObj.startLineNum = index
                    myObj.structType = 'array'
                    myObj.isPointer = 0
                    myObj.uid = obj.uid
                    myObj.versionMajor = 0xBADD  ### Default
                    myObj.versionMajorStr = 'versionMajor'  ### Default
                    myObj.versionMinor = 0xC0DE  ### Default
                    myObj.versionMinorStr = 'versionMinor'  ### Default
                    obj.memberList.append(myObj)

                    #### For now, just flatten the 1D array of limited elements
                    if (len(dList) == 1) and (dList[0] > 1) and (dList[0] <= 64):
                        for i in range(dList[0]):
                            exec("o = GenericObject()")
                            o.arrayDimList = [1]
                            o.depth = myObj.depth + 1
                            o.endLineNum = index
                            o.fwObject = myObj.fwObject + "_%i" % (i)
                            o.fwStruct = myObj.fwStruct
                            o.parent = myObj
                            o.ancestryNames = [myObj.fwObject] + myObj.ancestryNames
                            o.memberList = []
                            o.sizeInBits = myObj.sizeInBits / int(dList[0])
                            o.startLineNum = index
                            o.structType = 'array'
                            o.isPointer = 0
                            o.uid = myObj.uid
                            o.versionMajor = 0xBADD  ### Default
                            o.versionMajorStr = 'versionMajor'  ### Default
                            o.versionMinor = 0xC0DE  ### Default
                            o.versionMinorStr = 'versionMinor'  ### Default
                            myObj.memberList.append(o)

                    # print lines[index].strip()
                    # print "myLine",myLine
                    # print "m.group(1)",m.group(1)
                    # print "s.group(1)",s.group(1)
                    # print "dList",dList
                    # pprint(vars(myObj))
                    # pressReturnToContinue('else')

                if (self.options.debug):
                    print
                    pprint(vars(obj))
                    print
                    pprint(vars(obj.memberList[-1]))
                    pressReturnToContinue('10.5 InArray')

                index += 1
                continue

            ### End of a structure when '}' is encountered ################################
            elif re.search('\}', myLine):
                # self.log.debug('(11) %3i ' % (index+1) + lines[index])
                if (self.options.extraDebug): self.outputObjectStructText(lines[index], append=True)
                if (self.options.debug):
                    print("\'}\' indicates the end of current struct.  Returning the object.")
                    pprint(vars(obj))

                ### obj.depth of 1 is the base object.  When we reach the end of the base object
                ### we cannot simply return since we still need to get size, versionMajor/Minor
                if (obj.depth > 1):
                    obj.endLineNum = index
                    if (self.options.debug): pressReturnToContinue('11')
                    return obj

                if (self.options.debug): pressReturnToContinue('11.1')

                index += 1
                continue

            ###############################################################################
            ###############################################################################
            ###############################################################################

            ###############################################################################
            # Special handling for 'unnamed type (instance ....'
            elif 'unnamed type (instance ' in myLine:
                if matchSequence[15].match(myLine):
                    m = matchSequence[15].match(myLine)
                    # self.log.debug('(12.0) %3i' % (index+1) + lines[index])
                    if (self.options.extraDebug): self.outputObjectStructText(lines[index], append=True)
                    exec("myObj = GenericObject()")
                    myObj.arrayDimList = [1]
                    myObj.depth = obj.depth + 1
                    myObj.endLineNum = obj.endLineNum
                    myObj.startLineNum = index + 1
                    myObj.fwObject = m.group(1)
                    myObj.fwStruct = m.group(2)
                    # self.log.debug('fwStruct = %s' % myObj.fwStruct)
                    myObj.parent = obj
                    myObj.ancestryNames = [obj.fwObject] + obj.ancestryNames
                    myObj.memberList = []  ### @todo parse array of substructs
                    myObj.sizeInBits = 0
                    myObj.structType = 'union'
                    myObj.isPointer = 0
                    myObj.uid = obj.uid
                    myObj.versionMajor = 0xBADD  ### Default
                    myObj.versionMajorStr = 'versionMajor'  ### Default
                    myObj.versionMinor = 0xC0DE  ### Default
                    myObj.versionMinorStr = 'versionMinor'  ### Default

                    if (self.options.debug):
                        print("\nObject ... before calling buildStruct")
                        pprint(vars(obj))
                        pressReturnToContinue('12.0')

                    obj.memberList.append(self.__buildStruct(lines, obj=myObj))
                    index = obj.memberList[-1].endLineNum + 1

                    if (self.options.debug):
                        print(index, lines[index])

                        print("\nObject ... after calling buildStruct")
                        pprint(vars(obj))
                        pressReturnToContinue('12.1')

                        print("\nSubObject ... after calling buildStruct")
                        pprint(vars(obj.memberList[-1]))
                        pressReturnToContinue('12.1.1')

                    continue


                elif matchSequence[16].match(myLine):
                    # C++ :: Class variable detection
                    m = matchSequence[16].match(myLine)
                    # self.log.debug('(12.2) %3i' % (index+1) + lines[index])
                    if (self.options.extraDebug): self.outputObjectStructText(lines[index], append=True)
                    exec("myObj = GenericObject()")
                    myObj.arrayDimList = [1]
                    myObj.depth = obj.depth + 1
                    myObj.endLineNum = obj.endLineNum
                    myObj.startLineNum = index + 1
                    myObj.fwObject = m.group(1)
                    myObj.fwStruct = m.group(2)
                    # self.log.debug('fwStruct = %s' % myObj.fwStruct)
                    myObj.parent = obj
                    myObj.ancestryNames = [obj.fwObject] + obj.ancestryNames
                    myObj.memberList = []  ### @todo parse array of substructs
                    myObj.sizeInBits = 0
                    myObj.structType = 'bitfield'
                    myObj.isPointer = 0
                    myObj.uid = obj.uid
                    myObj.versionMajor = 0xBADD  ### Default
                    myObj.versionMajorStr = 'versionMajor'  ### Default
                    myObj.versionMinor = 0xC0DE  ### Default
                    myObj.versionMinorStr = 'versionMinor'  ### Default

                    obj.memberList.append(self.__buildStruct(lines, obj=myObj))
                    index = obj.memberList[-1].endLineNum + 1

                    if (self.options.debug):
                        print(index, lines[index])

                        print("")
                        pprint(vars(obj))
                        print("")
                        pprint(vars(obj.memberList[-1]))
                        pressReturnToContinue('12.2')

                    continue

                elif matchSequence[17].match(myLine):
                    # C++ :: Class variable detection
                    m = matchSequence[17].match(myLine)
                    # self.log.debug('(12.3) %3i' % (index+1) + lines[index])
                    if (self.options.extraDebug): self.outputObjectStructText(lines[index], append=True)
                    exec("myObj = GenericObject()")
                    myObj.arrayDimList = [1]
                    myObj.depth = obj.depth + 1
                    myObj.endLineNum = obj.endLineNum
                    myObj.startLineNum = index + 1
                    myObj.fwObject = m.group(1)
                    myObj.fwStruct = m.group(2)
                    # self.log.debug('fwStruct = %s' % myObj.fwStruct)
                    myObj.parent = obj
                    myObj.ancestryNames = [obj.fwObject] + obj.ancestryNames
                    myObj.memberList = []  ### @todo parse array of substructs
                    myObj.sizeInBits = 0
                    myObj.structType = 'bitfield'
                    myObj.isPointer = 0
                    myObj.uid = obj.uid
                    myObj.versionMajor = 0xBADD  ### Default
                    myObj.versionMajorStr = 'versionMajor'  ### Default
                    myObj.versionMinor = 0xC0DE  ### Default
                    myObj.versionMinorStr = 'versionMinor'  ### Default

                    if (self.options.debug):
                        print("\nObject ... before calling buildStruct")
                        pprint(vars(obj))
                        pressReturnToContinue('12.3')

                    obj.memberList.append(self.__buildStruct(lines, obj=myObj))
                    index = obj.memberList[-1].endLineNum + 1

                    if (self.options.debug):
                        print(index, lines[index])

                        print("\nObject ... after calling buildStruct")
                        pprint(vars(obj))
                        pressReturnToContinue('12.3.1')

                        print("\nSubObject ... after calling buildStruct")
                        pprint(vars(obj.memberList[-1]))
                        pressReturnToContinue('12.3.2')

                    continue

                else:
                    self.log.debug('(*12.4) %3i' % (index + 1) + lines[index])
                    if (self.options.extraDebug): self.outputObjectStructText('UNPROCESSED: ' + lines[index], append=True)
                    if (self.options.debug): pressReturnToContinue('*12.4')

                index += 1
                continue

            ###############################################################################
            # ([false..true]) objectName ; 1;
            elif re.search('^(.+) (\w+) : (\d+);$', myLine):
                m = re.search('^(.+) (\w+) : (\d+);$', myLine)
                # self.log.debug('(13) %3i ' % (index+1) + lines[index])
                if (self.options.extraDebug): self.outputObjectStructText(lines[index], append=True)
                exec("myObj = GenericObject()")
                myObj.arrayDimList = [1]
                myObj.depth = obj.depth + 1
                myObj.endLineNum = obj.endLineNum
                myObj.startLineNum = index + 1
                myObj.fwObject = m.group(2)
                myObj.fwStruct = 'bool32_t'
                # self.log.debug('fwStruct = %s' % myObj.fwStruct)
                myObj.parent = obj
                myObj.ancestryNames = [obj.fwObject] + obj.ancestryNames
                myObj.memberList = []  ### @todo parse array of substructs
                myObj.sizeInBits = int(m.group(3)) * 8
                myObj.structType = 'bitfield'
                myObj.isPointer = 0
                myObj.uid = obj.uid
                myObj.versionMajor = 0xBADD  ### Default
                myObj.versionMajorStr = 'versionMajor'  ### Default
                myObj.versionMinor = 0xC0DE  ### Default
                myObj.versionMinorStr = 'versionMinor'  ### Default
                obj.memberList.append(myObj)

                if (self.options.debug):
                    pprint(vars(obj))
                    pressReturnToContinue('13')

                index += 1
                continue


            ###############################################################################
            ###############################################################################
            ###############################################################################

            ### Get struct size ###########################################################
            elif matchSequence[18].match(myLine):
                # self.log.debug('(15) %3i ' % (index+1) + lines[index])
                if (self.options.extraDebug): self.outputObjectStructText(lines[index], append=True)
                obj.sizeInBits = int(myLine) * 8
                if (self.options.debug):
                    pprint(vars(obj))
                    pressReturnToContinue('15')

                index += 1
                continue

            ### Get struct version major ##################################################
            elif matchSequence[19].match(myLine):
                m = matchSequence[25].match(myLine)
                # self.log.debug('(16) %3i ' % (index+1) + lines[index])
                if (self.options.extraDebug): self.outputObjectStructText(lines[index], append=True)
                obj.versionMajorStr = m.group(1)
                obj.versionMajor = int(m.group(2), 16)

                if (self.options.debug):
                    pprint(vars(obj))
                    pressReturnToContinue('16')

                index += 1
                continue

            ### Get struct version minor ##################################################
            elif matchSequence[20].match(myLine):
                m = matchSequence[26].match(myLine)
                # self.log.debug('(17) %3i ' % (index+1) + lines[index])
                if (self.options.extraDebug): self.outputObjectStructText(lines[index], append=True)
                obj.versionMinorStr = m.group(1)
                obj.versionMinor = int(m.group(2), 16)

                if (self.options.debug):
                    pprint(vars(obj))
                    pressReturnToContinue('17')

                index += 1
                continue

            ### Catching unprocessed struct text ##########################################
            else:
                self.log.debug('(*18) %3i ' % (index + 1) + lines[index])
                if (self.options.extraDebug): self.outputObjectStructText('UNPROCESSED: ' + lines[index], append=True)
                index += 1

        return obj

    def outputObjectStructText(self, textLine, append=True):
        """Performs a file definition output."""
        if append:
            txtFile = open(self.objectTextFile, 'a+')
        else:
            txtFile = open(self.objectTextFile, 'w+')
        txtFile.write("%s" % (textLine))
        txtFile.close()

    def buildStruct(self, uid, fwObject, fwStruct):
        """Performs a definition construction from output file."""
        obj = None
        print("fwStruct: %-25s fwObject: %-25s UID: %i" % (fwStruct, fwObject, uid))
        self.objectTextFile = os.path.join(self.parsersFolder, fwObject + extTXT)
        if (self.options.extraDebug): self.outputObjectStructText('# Struct text for Telemetry data object %s (%s)\n' % (fwObject, fwStruct), append=False)
        iFile = open(self.structDefFile, "r")
        lines = iFile.readlines()
        iFile.close()

        startLineNum = 0
        endLineNum = 0
        structDepth = 0  ### current structure depth
        maxStructDepth = 0

        ### Find the start and end line numbers for the specified object
        for i in range(len(lines)):
            if ('ObjectBegin==>%s' % (fwObject) in lines[i]):
                startLineNum = i  ### 0-based line count of lines[]
            elif ('ObjectEnd==>%s' % (fwObject) in lines[i]):
                endLineNum = i  ### 0-based line count of lines[]
                break
            elif ('{' in lines[i]):
                structDepth += 1
                if (structDepth > maxStructDepth): maxStructDepth = structDepth
            elif ('}' in lines[i]):
                structDepth -= 1

        if (maxStructDepth > self.maxStructDepth): self.maxStructDepth = maxStructDepth
        structDepth = maxStructDepth

        # print "Start line number: %i" % (startLineNum)
        # print "End line number:   %i" % (endLineNum)
        # print "Struct depth:      %i" % (structDepth)
        # print "Max Struct depth:  %i" % (self.maxStructDepth)

        exec("obj = GenericObject()")
        obj.arrayDimList = [1]
        obj.depth = 0
        obj.endLineNum = endLineNum
        obj.fwObject = fwObject
        obj.fwStruct = fwStruct
        obj.parent = None
        obj.ancestryNames = []
        obj.ancestryTypes = []
        obj.memberList = []
        obj.sizeInBits = 0
        obj.startLineNum = startLineNum + 1
        obj.structType = None
        obj.isPointer = 0
        obj.uid = uid
        obj.versionMajor = 0xBADD
        obj.versionMajorStr = 'versionMajor'
        obj.versionMinor = 0xC0DE
        obj.versionMinorStr = 'versionMinor'
        return self.__buildStruct(lines, obj)

    def getCleanStructDefFile(self):
        # List of Files to Combine in order of main then sub.
        combineFileList = list()
        cleanedFileName = None
        combineFileList.append(self.subStructDefFile)  # @todo: enable once parser can handle substructs
        combineFileList.append(self.structDefFile)
        srcFile = self.structDefFile  # Cleaned file.

        if os.path.exists(srcFile):
            # Create a new file.
            if (len(srcFile) - len(srcFile) > 1):
                fileLenSize = len(srcFile) - len(srcFile)
            else:
                fileLenSize = len(srcFile)
            fileNameOnly, extension = os.path.splitext(os.path.basename(self.structDefFile))
            cleanFileNameChomp = os.path.join(os.path.dirname(self.structDefFile), fileNameOnly)
            cleanedFileName = cleanFileNameChomp + "_clean" + extension
            print("Clean File name")
            print(cleanedFileName)
            # don't redo if this has been created before
            if os.path.exists(cleanedFileName):
                return cleanedFileName

            cleanFile = open(cleanedFileName, "w+")

            # find header in files and write at top

            headerFound = False
            for iterationFile in combineFileList:
                if ("_structDefs_" in iterationFile):
                    sourceFileContent = open(iterationFile, "r")
                    headerFound = True
                    for i in range(6):
                        line = next(sourceFileContent)
                        cleanFile.write(line)
                    sourceFileContent.close()
            if (not headerFound):
                cleanFile.write("{\n_LINES = 1000\n")

            for iterationFile in combineFileList:
                sourceFileContent = open(iterationFile, "r")
                count = 1
                # for all files, get rid of MULTI header, since we already found it
                try:
                    for i in range(6):  # skip header 6 lines
                        next(sourceFileContent)
                except StopIteration:  # in case reaches end of file
                    pass

                for line in sourceFileContent:

                    # Remove qualifiers
                    line = line.replace('const ', '')
                    line = line.replace('static ', '')
                    line = line.replace('volatile ', '')
                    line = line.replace('SubstructBegin==>', 'ObjectBegin==>')
                    line = line.replace('SubstructEnd==>', 'ObjectEnd==>')

                    # When line has a GHS warning do not push it to the new file.
                    if 'warning: "' not in line:  # remove a specific string
                        if (self.options.debug):
                            print("Line Save   {}: {}".format(count, line.strip()))
                        cleanFile.write(line)
                    else:
                        if (self.options.debug):
                            print("Line Delete {}: {}".format(count, line.strip()))
                    count += 1
                sourceFileContent.close()

            cleanFile.close()
        # @ todo: traceback fail id self.structDef not defined
        return cleanedFileName

    def parseUT(self):
        OutputLog.setDebugLevel(10)
        destDir = os.path.abspath(os.path.join('..', '..', 'projects', 'objs', self.options.projectName, 'telemetry', 'tokenParsers'))
        destDir1 = os.path.abspath(os.path.join('..', '..', 'projects', 'objs', self.options.projectName, 'telemetry', 'twidlParsers'))
        destDir2 = os.path.abspath(os.path.join('..', '..', 'projects', 'objs', self.options.projectName, 'telemetry', 'xmlParsers'))

        cleanedFileName = self.getCleanStructDefFile()

        if cleanedFileName is not None:

            #           ### Perform Test ###
            OutputLog.Information("Start unit test... ")
            errors = parserUnitTest(cleanedFileName, destDir, destDir1, destDir2)
            #
            if (errors == 0):
                OutputLog.Information("passed.")
            else:
                OutputLog.Information("failed.")

    def storeForVersioning(self):
        print("\n==Storing Run Outputs in Unique Version File==\n")
        print("This is run: %s\n" % uPIDName)
        versionDir = os.path.join(os.path.dirname(__file__), "version")
        uPIDLogFile = os.path.join(versionDir, "uPIDLogFile.txt")
        thisRunDir = os.path.abspath(os.path.join(versionDir, uPIDName))

        cleanStructDefFile = self.getCleanStructDefFile()

        if not os.path.exists(versionDir):
            os.mkdir(versionDir)

        if os.path.exists(uPIDLogFile):
            append_write = 'a'  # append if already exists
        else:
            append_write = 'w'  # make a new file if not

        if not os.path.exists(thisRunDir):
            os.mkdir(thisRunDir)
            with open(uPIDLogFile, append_write) as file:
                file.write("%s\n" % (uPIDName))
            storeLocationStructDefFile = os.path.join(versionDir, os.path.basename(cleanStructDefFile))
            # todo: check that copy file is copied correctly. Necessary.
            shutil.copyfile(cleanStructDefFile, storeLocationStructDefFile)
        else:
            print("Folder for this unique Run id: %s has alredy been created\n" % uPIDName)
            # @todo: fail function if run id is not unique? Or just override old folder?


###############################################################################################################
def ctypeAutoGenerationAPI(fwBuildOutputDir, projectName, fwToolsDir, uidEnumFile, multiExeVersion, extraDebug, dataObjToProcess, debug, verbose, tObjToDefine, parse, store, media):
    ctypeOptionsToUse = cTypeOptions()
    ctypeOptionsToUse.set_fwBuildOutputDir(fwBuildOutputDir)
    ctypeOptionsToUse.set_projectName(projectName)
    ctypeOptionsToUse.set_fwToolsDir(fwToolsDir)
    ctypeOptionsToUse.set_uidEnumFile(uidEnumFile)
    ctypeOptionsToUse.set_multiExeVersion(multiExeVersion)
    ctypeOptionsToUse.set_extraDebug(extraDebug)
    ctypeOptionsToUse.set_dataObjToProcess(dataObjToProcess)
    ctypeOptionsToUse.set_debug(debug)
    ctypeOptionsToUse.set_verbose(verbose)
    ctypeOptionsToUse.set_tObjToDefine(tObjToDefine)
    ctypeOptionsToUse.set_parse(parse)
    ctypeOptionsToUse.set_store(store)
    ctypeOptionsToUse.set_media(media)
    ctypeOptionsToUse.self_validate()

    if (fwBuildOutputDir is None) or (projectName is None) or (fwToolsDir is None):
        print('\nPlease specify options...')
        print(ctypeOptionsToUse)
        return (22)

    fwBuildOutputDirCheck = os.path.abspath(fwBuildOutputDir)
    if not os.path.exists(fwBuildOutputDirCheck):
        print('\nPlease specify "fwbuilddir" option to specify the folder with elf file')
        return (23)

    fwToolsDirCheck = os.path.abspath(fwToolsDir)
    if not os.path.exists(fwToolsDirCheck):
        print('\nInvalid output directory path "%s".' % fwToolsDirCheck)
        return (24)

    buffDictionaryCheck = os.path.abspath(os.path.join(fwToolsDirCheck, 'bufdict.py'))
    if not os.path.exists(buffDictionaryCheck):
        print('\nFailed to locate bufdict.py in the specified FW tools folder (%s).' % fwToolsDir)
        return (25)

    if projectName is None:
        print('\nPlease specify "projname" option (ex: alderstream_02)')
        return (1)

    if (fwBuildOutputDir is None) or \
            not os.path.exists(fwBuildOutputDir):
        print('\nPlease specify "fwbuilddir" option to specify the folder with elf file')
        return (1)

    if not ENABLE_CLANG:
        print("MEDIA is " + str(media))
        if media is None:
            redefineMedia(True)
        elif media == "SXP":
            redefineMedia(False)
        elif media == "NAND":
            redefineMedia(True)
        else:
            redefineMedia(True)
        print("Choosing media:                 %s" % str(TRUNK))

    redefineFileNames()  # Set unique names

    print("Build project name:                 %s" % (projectName))
    print("Project build output dir:           %s" % (fwBuildOutputDir))

    ### Extract FW C-structs #####################
    cag = CtypeAutoGen(ctypeOptionsToUse)
    cag.autoSrcDirScan()

    if tObjToDefine == None:
        tObjToDefine = "all"

    # get objects to define
    objs = tObjToDefine.replace('[', '').replace(']', '').lower()
    objList = objs.split(',')
    print("Defining Telemetry Objs: %s ..." % (objList))
    cag.getTelemetryObjectList(objList)

    # different ways of parsing ctypes
    cag.extractCstructs()
    cag.generatePythonCtypes()

    if store:
        cag.storeForVersioning()
    if parse:
        cag.parseUT()

    print("Normal End Process")
    return (0)


################################################################################################################
################################################################################################################

def main():
    """Performs the auto parsing of data control to generate telemetry definitions within a python c-type."""
    parser = OptionParser(usage)
    parser.add_option("--fwbuilddir", dest='fwBuildOutputDir', metavar='<DIR>', help='FW build directory (ex: projects/objs/alderstream_02)')
    parser.add_option("--projectname", dest='projectName', metavar='<PROJ>', help='Project name (ex: alderstream_02)')
    parser.add_option("--tools", dest='fwToolsDir', metavar='<TOOLSDIR>', default=None, help='FW telemetry tools dir where bufdict.py is (ex: tools/telemetry)')
    parser.add_option("--defineobjs", dest='tObjToDefine', metavar='<tObjToDefine>', default=None, help='Required. Manual imput for uids of telemetry Objects that should be defined,(ex: [0,8,9,115]). NO SPACES, COMMA-SEPARATED. Required')
    parser.add_option("--uidenumfile", dest='uidEnumFile', metavar='<UIDFILE>', default=None, help='FW file where eUniqueIdentifier enum is defined (default=datacontrol.h)')
    parser.add_option("--multiexeversion", dest='multiExeVersion', metavar='<MULTIEXEVER>', default=None, help='multi.exe version (Ex: multi_716, default=auto)')
    parser.add_option("--extradb", action='store_true', dest='extraDebug', default=False, help='Output additional debug info.')
    parser.add_option("--dataobj", dest='dataObjToProcess', metavar='<OBJECT>', default=None, help='Process specified data object.')
    parser.add_option("--debug", action='store_true', dest='debug', default=False, help='Debug mode.')
    parser.add_option("--verbose", action='store_true', dest='verbose', default=False, help='Verbose printing for debug use.')
    parser.add_option("--parse", action='store_true', dest='parse', default=False, help='Parsing after ctype generation')
    parser.add_option("--store", action='store_true', dest='store', default=False, help='For creating centralized directory to store all runs resulting in new structDef File')
    parser.add_option("--media", dest='media', metavar='<MEDIA>', default=None, help='Select media destination I.E. NAND, SXP.')

    (options, args) = parser.parse_args()
    print(options)
    print(args)

    exitCode = ctypeAutoGenerationAPI( \
        options.fwBuildOutputDir, \
        options.projectName, \
        options.fwToolsDir, \
        options.uidEnumFile, \
        options.multiExeVersion, \
        options.extraDebug, \
        options.dataObjToProcess, \
        options.debug, \
        options.verbose, \
        options.tObjToDefine, \
        options.parse, \
        options.store, \
        options.media)

    quit(exitCode)


if __name__ == '__main__':
    """Performs execution delta of the process."""
    p = datetime.now()
    try:
        main()
    except Exception as e:
        print("Fail End Process: ", e)
        traceback.print_exc()
    q = datetime.now()
    print("\nExecution time: " + str(q - p))

## @}
