#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Phuong Tran, Andrew Sainz
# *****************************************************************************/
"""
Brief:
    autoParser.py - Method and Apparatus to extract compiled code into interpreted code

Author(s):


Requirement(s):
    FW project must be built prior to running the tool.

Documentation:
	https://llvm.org/docs/CommandGuide/llvm-dwarfdump.html
	https://en.wikipedia.org/wiki/DWARF 
	https://nil-wiki/Telemetry+Parsing+Guide

	Green Hills Compiler
	Compiling hello.c executable file called a.out is generated, together with the
	following additional files:hello.o, a.map, a.dnm & a.dla
	The a.map file is a map file produced by the linker. The a.dnm & a.dla files 
	contain basic debugging information.
	
	Source		Assembly Files (.s)		Object Files (.o)		Libraries (.a)
	   ||              ||                     ||                    ||
	   \/              \/                     |===================> \/
	Compiler =====> Assembler ====================================> Linker =========> Executable
    
	 The following table describes data type alignments for C and C++.C/C++
	  data type		Size		Alignment
	  char			8			8
	  short			16			16
	  int			32			32
	  long			32			32
	  long long		64			32
	  float			32			32
	  double		64			32
	  long double	64			32
	  *(pointer)	32			32
	  enum(default)	32			32
Date: 2/26/2020
"""

################################################################################################################
# General Python module imports
################################################################################################################
import binascii
import copy
import ctypes
import datetime
import errno
import filecmp
import json
import logging
import os
import pickle
import platform
import re
import shutil
import struct
import sys
import time
import multiprocessing

try:
    import enum  # @todo cleanup unused
    from enum import *  # pip install enum34 # backport from 3.x to 2.7 https://pypi.org/project/enum34/ # @todo cleanup explicit usage
except: 
    pass

################################################################################################################
# Explicit importing of headers
################################################################################################################
from threading import Timer
from subprocess import Popen, PIPE
from optparse import OptionParser

from software.decode.configs import dataStructure

from ctypes import *  # @todo cleanup explicit usage
from ctypes.util import find_library  # @todo cleanup explicit usage
from optparse import OptionGroup  # @todo cleanup explicit usage
from sys import version_info  # @todo cleanup explicit usage

GHS_COMPILER_VERSION = "comp_201754" # "comp_201914"  # "comp_201754"
ENABLE_DEBUG_ENTER = 1  # @todo debug switch
NULL = 'NULL'

if sys.version[:3] > "2.3":
    import hashlib  # @todo cleanup explicit usage

try:
    if platform.system() == 'Linux':
        ghsPath = '/usr/ghs'
    elif platform.system() == 'Windows':
        ghsPath = 'c:/ghs'
        import win32com.shell.shell as shell
    elif 'CYGWIN_NT' in platform.system():
        ghsPath = 'c:/ghs'
except:
    print ("Failed binary exe")

cmdPath, cmdFile = os.path.split(sys.argv[0])

usage = "%s --projectname PROJ_NAME --fwbuilddir FW_BUILD_DIR" % (sys.argv[0])

ARRAY_SUBSTRINGS_TO_SKIP = ['reserved', 'rsvd', 'ctypeAddedPad']

BASE_CDATATYPE_SIZE_MAP = {
    "int8_t": 1,
    "int16_t": 2,
    "int32_t": 4,
    "int64_t": 8,

    "SChar": 1,
    "Short": 2,
    "Int": 4,
    "LongLong": 8,

    "uint8_t": 1,
    "uint16_t": 2,
    "uint32_t": 4,
    "uint64_t": 8,

    "Char": 1,
    "UChar": 1,
    "UShort": 2,
    "UInt": 4,
    "ULongLong": 8,

    "Logical*1": 1,
    "Logical*2": 2,
    "Logical*4": 4,
    "Logical*8": 8,
    "enum": 4,
}

BASE_CTYPE_MAP = {
    "__int8_t": "c_int8",
    "__int16_t": "c_int16",
    "__int32_t": "c_int32",
    "__int64_t": "c_int64",
    "__uint8_t": "c_uint8",
    "__uint16_t": "c_uint16",
    "__uint32_t": "c_uint32",
    "__uint64_t": "c_uint64",
    "int8_t": "c_int8",
    "int16_t": "c_int16",
    "int32_t": "c_int32",
    "int64_t": "c_int64",

    "SChar": "c_int8",
    "Short": "c_int16",
    "Int": "c_int32",
    "LongLong": "c_int64",

    "uint8_t": "c_uint8",
    "uint16_t": "c_uint16",
    "uint32_t": "c_uint32",
    "uint64_t": "c_uint64",

    "Char": "c_uint8",
    "char": "c_uint8",
    "UChar": "c_uint8",
    "UShort": "c_uint16",
    "UInt": "c_uint32",
    "ULongLong": "c_uint64",

    "Logical*1": "c_uint8",
    "Logical*2": "c_uint16",        # Logical*2, Logical*3, and Logical*4 are virtual construct of this autoparser.
    "Logical*3": "c_uint16",        # This indicates a padding alignment issue.  Structure may need to be padded in FW.
    "Logical*4": "c_uint32",
    "Logical*8": "c_uint64",
    "enum": "c_uint32",

    "pointer": "c_uint32",

    # DWARF format for BHB
    "unsigned int": "c_uint32",
    "long unsigned int": "c_uint64",
    "_Bool8": "c_uint8",
    "_Bool16": "c_uint16",
    "_Bool32": "c_uint32",
    "_Bool64": "c_uint64",
    "char": "c_uint8",
    "__uintptr_t": "c_uint64",
}

BASE_CTYPE_SIZE_BYTES = {
    "c_int8":       1,
    "c_int16":      2,
    "c_int32":      4,
    "c_int64":      8,
    "c_uint8":      1,
    "c_uint16":     2,
    "c_uint32":     4,
    "c_uint64":     8,
}

# Renaming to avoid using Python keywords as variable names
VARIABLE_KEYWORD_REMAP = {
    "global": "Global"
}

BUILT_IN_DATA_OBJECT_LIST = [
    # Instance Name             # Typedef                       # VERSION MaJOR macro               # VERSION MINOR macro               # Pack  #versionMajorName   #versionMinorName   RNLBA   WNLBA
    ['asicRegisterAccess',      'asicRegisterAccess_t',         'ASIC_REGISTER_ACCESS_VERSION_MAJOR', 'ASIC_REGISTER_ACCESS_VERSION_MINOR', 4,  'version.major',    'version.minor',    None,   None],  # MFG
    ['assertDumpHeader',        'assertDumpHeader_t',           'ASSERT_DUMP_VERSION_MAJOR',        'ASSERT_DUMP_VERSION_MINOR',        4,      'version.major',    'version.minor',    None,   None],
    ['assertDumpMap',           'assertDumpMap_t',              'ASSERT_DUMP_MAP_VERSION_MAJOR',    'ASSERT_DUMP_MAP_VERSION_MINOR',    4,      'version.major',    'version.minor',    None,   None],
    ['bis',                     'Bis_t',                        'BIS_VERSION_MAJOR',                'BIS_VERSION_MINOR',                4,      'version.major',    'version.minor',     -16,   None],  # MFG
    ['bitErrors',               'bitErrors_t',                  'BITERRORS_VER_MAJOR',              'BITERRORS_VER_MINOR',              4,      'version.major',    'version.minor',    None,   None],  # MFG
    ['bridgeInfo',              'bridgeInfo_t',                 None,                               None,                               4,      None,               None           ,    None,   None],
    ['burnin',                  'burnin_t',                     'BURNIN_CONFIG_VERSION_MAJOR',      'BURNIN_CONFIG_VERSION_MINOR',      4,      'version.major',    'version.minor',    None,   None],  # MFG
    ['burninStats',             'burninSxpStats_t',             'BURNIN_STATS_VERSION_MAJOR',       'BURNIN_STATS_VERSION_MINOR',       4,      'version.major',    'version.minor',    None,   None],  # MFG
    ['channelMap',              'channelMap_t',                 None,                               None,                               4,      None,               None           ,    None,   None],
    ['chronoTrigger',           'TC_CHRONOTRIGGER_t',           'CHRONOTRIGGER_VERSION_MAJOR',      'CHRONOTRIGGER_VERSION_MINOR',      4,      'version.major',    'version.minor',    -700,   None],  # MFG
    ['dataLayout',              'dataLayout_t',                 None,                               None,                               4,      None,               None           ,    None,   None],
    ['dieDataLog',              'dieDataLog_t',                 'DIELOG_VER_MAJOR',                 'DIELOG_VER_MINOR',                 4,      'version.major',    'version.minor',    None,   None],
    ['dieMap',                  'dieMap_v1_t',                  'DIE_MAP_VERSION_MAJOR',            'DIE_MAP_VERSION_MINOR',            4,      'version.major',    'version.minor',    None,   None],  # MFG
    ['dieOfflineMeasurements',  'DieOfflineMeasurements_t',     'DIEOFFLINE_MEAS_VER_MAJOR',        'DIEOFFLINE_MEAS_VER_MINOR',        4,      'version.major',    'version.minor',    None,   None],
    ['driveInformation',        'driveInformation_t',           'DRIVE_INFORMATION_VERSION_MAJOR',  'DRIVE_INFORMATION_VERSION_MINOR',  4,      'version.major',    'version.minor',    None,   None],  # MFG
    ['eccErrorsLog',            'eccErrLog_t',                  None,                               None,                               4,      None,               None           ,    None,   None],
    ['elThrottle',              'elThrottle_t',                 'EL_CONFIG_VER_MAJOR',              'EL_CONFIG_VER_MINOR',              4,      'version.major',    'version.minor',    -337,   None],
    ['errorRecoveryStats',      'errorRecoveryStats_t',         'ERROR_RECOVERY_VER_MAJOR',         'ERROR_RECOVERY_VER_MINOR',         4,      'version.major',    'version.minor',    None,   None],  # MFG
    ['extDieInfo',              'extDieInfoLog_t',              'EXT_DIE_INFO_VERSION_MAJOR',       'EXT_DIE_INFO_VERSION_MINOR',       4,      'version.major',    'version.minor',    None,   None],  # MFG
    ['factoryConfig',           'factoryConfig_t',              None,                               None,                               4,      None,               None           ,    None,   None],
    ['FastCtxFAT',              'SliceFat_t',                   'FAT_MAJOR_REV',                    'FAT_MINOR_REV',                    4,      'version.major',    'version.minor',    None,   None],
    ['geom',                    'geom_t',                       'DRIVE_GEOM_VERSION_MAJOR',         'DRIVE_GEOM_VERSION_MINOR',         4,      'version.major',    'version.minor',    -523,   None],
    ['i2cPeekPoke',             'i2cPeekPoke_t',                'I2C_TC_VERSION_MAJOR',             'I2C_TC_VERSION_MINOR',             4,      'version.major',    'version.minor',    None,   None],  # MFG
    ['initState',               'initState_t',                  'INITSTATE_VER_MAJOR',              'INITSTATE_VER_MINOR',              4,      'version.major',    'version.minor',    -329,   None],
    ['LLFState',                'LLF_State_t',                  None,                               None,                               4,      None,               None           ,    None,   None],
    ['mediaMgr',                'mediaMgr_t',                   'MEDIA_MGR_VER_MAJOR',              'MEDIA_MGR_VER_MINOR',              4,      'version.major',    'version.minor',    None,   None],  # MFG
    ['mediaReg',                'PkPk_MediaReg_t',              'MEDIA_REG_VERSION_MAJOR',          'MEDIA_REG_VERSION_MINOR',          4,      'version.major',    'version.minor',    None,   None],  # MFG
    ['mediaTimeTable',          'mediaTimeTable_t',             'MEDIA_TIMINGS_MAJOR_VER',          'MEDIA_TIMINGS_MINOR_VER',          4,      'header.version.major', 'header.version.minor', None, None], # MFG
    ['metaBitErrors',           'metaBitErrors_t',              'META_BITERRORS_VER_MAJOR',         'META_BITERRORS_VER_MINOR',         4,      'version.major',    'version.minor',    None,   None],  # MFG
    ['nlogSelect',              'nlogSelect_t',                 'NLOG_VERSION_MAJOR',               'NLOG_VERSION_MINOR',               4,      'version.major',    'version.minor',     -51,    -51],
    ['NplCmdStateInfo',         'nplCmdStateInfo_t',            None,                               None,                               4,      None,               None           ,    None,   None],
    ['nplInfo',                 'nplInfo_t',                    None,                               None,                               4,      None,               None           ,    None,   None],
    ['nvmeFeatures',            'nvmeFeatures_t',               None,                               None,                               4,      None,               None           ,    None,   None],
    ['otpEfuseProgramRead',     'otpEfuseProgramRead_t',        'OTP_PROGRAM_EFUSE_DEBUG_VERSION_MAJOR', 'OTP_PROGRAM_EFUSE_DEBUG_VERSION_MINOR', 4, 'versionMajor','versionMinor' ,    None,   None],  # MFG
    ['otpEfuseProgramWrite',    'otpEfuseProgramWrite_t',       'OTP_PROGRAM_EFUSE_DEBUG_VERSION_MAJOR', 'OTP_PROGRAM_EFUSE_DEBUG_VERSION_MINOR', 4, 'versionMajor','versionMinor' ,    None,   None],  # MFG
    ['PersistentData',          'persistentData_t',             None,                               None,                               4,      None,               None           ,    None,   None],
    ['pkpkHeader',              'PkPk_Header_t',                'PEEKPOKE_VERSION_MAJOR',           'PEEKPOKE_VERSION_MINOR',           4,      'version.major',    'version.minor',    None,   None],
    ['Pli',                     'pli_t',                        None,                               None,                               4,      None,               None           ,    None,   None],
    ['pliCapTest',              'pliCapTest_t',                 'PLI_CAP_TEST_REVISION_MAJOR',      'PLI_CAP_TEST_REVISION_MINOR',      4,      'version.major',    'version.minor',    None,   None],  # MFG
    ['PliSlice',                'pliSlice_t',                   'PLI_DUMP_HEADER_REVISION_MAJOR',   'PLI_DUMP_HEADER_REVISION_MINOR',   4,      'PliHeader.version.major', 'PliHeader.version.minor', None, None],
    ['powerThrottleTc',         'powerThrottleTestCommand_t',   'POWER_THROTTLE_TC_VER_MAJOR',      'POWER_THROTTLE_TC_VER_MINOR',      4,      'version.major',    'version.minor',    -296,   None],
    ['sim',                     'sliceIndMap_t',                'SIM_REVISION',                     None,                               4,      'header.rev',       None           ,    None,   None],
    ['SlowCtxRebuild',          'slowCtxRebuild_t',             None,                               None,                               4,      None,               None           ,    None,   None],
    ['smart',                   'smartStruct_t',                None,                               None,                               1,      None,               None           ,    None,   None],
    ['spiRegionData',           'spiRegionData_t',              'SPIREGION_VER_MAJOR',              'SPIREGION_VER_MINOR',              4,      'version.major',    'version.minor',    None,   None],
    ['stats',                   'stats_t',                      'STATS_VER_MAJOR',                  'STATS_VER_MINOR',                  4,      'version.major',    'version.minor',     -82,   None],  # MFG
    ['tcSelfTestRead',          'tcSelfTestRead_t',             'SELF_TEST_TC_VERSION_MAJOR',       'SELF_TEST_TC_VERSION_MINOR',       4,      'tCmdVersion.major','tCmdVersion.minor',None,   None],
    ['telemetryTLogHeader',     'telemetryTLogHeader_t',        'TELEMETRY_VERSION_MAJOR',          'TELEMETRY_VERSION_MINOR',          4,      'majorVersion',     'minorVersion' ,    None,   None],
    ['testCmdIdBlock',          'testCmdIdBlock_t',             None,                               None,                               1,      None,               None           ,     -64,   None],
    ['thermalStats',            'ThermalStats_t',               'THERMAL_STATS_VER_MAJOR',          'THERMAL_STATS_VER_MINOR',          4,      'version.major',    'version.minor',    None,   None],  # MFG
    ['thermalThrottleTc',       'thermalThrottleTestCommand_t', 'THERMAL_THROTTLE_TC_VER_MAJOR',    'THERMAL_THROTTLE_TC_VER_MINOR',    4,      'version.major',    'version.minor',    -295,   None],
    ['throttle',                'throttle_t',                   'THROTTLE_VER_MAJOR',               'THROTTLE_VER_MINOR',               4,      'version.major',    'version.minor',    -113,   None],
    ['transportStateInfo',      'transportStateInfo_t',         None,                               None,                               4,      None,               None           ,    None,   None],
    ['transportStats',          'transportStats_t',             None,                               None,                               4,      None,               None           ,    None,   None],
    ['trainingLogTc',           'trainingLogTc_t',              'TRAINING_LOG_TC_VERSION_MAJOR',    'TRAINING_LOG_TC_VERSION_MINOR',    4,      'version.major',    'version.minor',    -496,   None],  # MFG
    ['tcMediaTopology',         'tcMediaTopology_t',            'MEDIA_TOPOLOGY_VERSION_MAJOR',     'MEDIA_TOPOLOGY_VERSION_MINOR',     4,      'version.major',    'version.minor',    None,   None],  # MFG
    ['vdmRecoveryHistogramSlices', 'vdmRecoveryHistogramSlices_t', 'VDMHISTOGRAM_SLICES_VER_MAJOR', 'VDMHISTOGRAM_SLICES_VER_MINOR',    4,      'version.major',    'version.minor',    None,   None],  # MFG
]


SequenceNumber = 1
PadSequenceNumber = 1
alreadyGeneratedCstructs = []


################################################################################################################
# Helper function to pause for user input (for debug use only)
################################################################################################################
################################################################################################################
def pressReturnToContinue(aString=None, indent=0, enable=ENABLE_DEBUG_ENTER):
    if enable:
        if sys.version_info[0] < 3:
            if aString is None:
                usersInput = input("%sPRESS RETURN TO CONTINUE or 'q' to quit: " % (indent * ' '))
            else:
                usersInput = input("%sPRESS RETURN TO CONTINUE or 'q' to quit (%s): " % (indent * ' ', aString))
        else:
            if aString is None:
                usersInput = input("%sPRESS RETURN TO CONTINUE or 'q' to quit: " % indent * ' ')
            else:
                usersInput = input("%sPRESS RETURN TO CONTINUE or 'q' to quit (%s): " % (indent * ' ', aString))
        if usersInput == 'q':
            sys.exit(0)


def dprint(string, indent=0, enable=ENABLE_DEBUG_ENTER):
    if enable: print("%s%s" % (indent*' ', string))


def writeListToFile(dataList, outFile):
    with open(outFile, 'wb') as oFile:
        for i in dataList: oFile.write(i+'\n')


def writeLineToFile(line, outFile, append=True):
    if append:
        with open(outFile, 'ab') as oFile: oFile.write(line+'\n')
    else:
        with open(outFile, 'wb') as oFile: oFile.write(line+'\n')


def outPutLine(line, outFile=None, append=True):
    if outFile is None:
        print(line)
    elif not append or not os.path.exists(outFile):
        with open(outFile, 'wb') as oFile:
            oFile.write(line + '\n')
    else:
        with open(outFile, 'ab') as oFile:
            oFile.write(line + '\n')


def getDataIdx(dbgData, symRow):
    fileIdx = 0
    for idx in range(len(dbgData)):
        if re.match('^(\d+):.+', dbgData[idx]):
            m = re.match('^(\d+):.+', dbgData[idx])
            if int(m.group(1)) == symRow:
                fileIdx = idx
                break
    return fileIdx


def generateInlinedEnumTypedefName(obj):
    global SequenceNumber
    if obj.dataType == 'enum' and (obj.typedef is None or obj.typedef == ""):
        obj.typedef = "__anEnum%i%i" % (obj.depth, SequenceNumber)
        SequenceNumber = SequenceNumber + 1
    return obj


def generateAnonymousUnionStructNames(obj):
    global SequenceNumber
    if (obj.instance is None or obj.instance == "") and obj.anon:
        if obj.dataType == 'union':
            obj.instance = "__anUnion%i%i" % (obj.depth, SequenceNumber)
            if obj.typedef is None or obj.typedef == "": obj.typedef = "__anUnionTypedef%i%i" % (obj.depth, SequenceNumber)
        else:
            obj.instance = "__anStruct%i%i" % (obj.depth, SequenceNumber)
            if obj.typedef is None or obj.typedef == "": obj.typedef = "__anStructTypedef%i%i" % (obj.depth, SequenceNumber)
        SequenceNumber = SequenceNumber + 1
    return obj


def generateUnamedUnionStructNames(obj):
    global SequenceNumber
    if obj.typedef is None or obj.typedef == "":
        obj.unnamed = True
        if obj.dataType == 'union':
            obj.typedef = "__%s_unUnion%i%i" % (obj.instance, obj.depth, SequenceNumber)
        else: obj.typedef = "__%s_unStruct%i%i" % (obj.instance, obj.depth, SequenceNumber)
    SequenceNumber = SequenceNumber + 1
    return obj


def getTypedefNames(anonNameString):
    typedefName = ""
    inputString = anonNameString
    while inputString is not None and inputString != "":
        if re.match('^(\D)(.+)$', inputString) and re.match('^(_+)(.+)$', inputString):
            m = re.match('^(_+)(.+)$', inputString)
            inputString = m.group(2)
        elif re.match('^(\D)(.+)$', inputString) and re.match('^([a-zA-Z0-9]+)(_.+)$', inputString):
            m = re.match('^([a-zA-Z0-9]+)(_.+)$', inputString)
            inputString = m.group(2)
        elif re.match('^(\d+)(.+)$', inputString):
            m = re.match('^(\d+)(.+)$', inputString)
            letterCount = int(m.group(1))
            nameSubstring = m.group(2)[:letterCount]
            inputString = m.group(2)[letterCount:]
            typedefName = typedefName + nameSubstring
    return typedefName


def sanityChecks(outParserFile, versionMajorMemberName, versionMinorMemberName):
    importCheckStatus = True
    sizeCheckStatus = True

    pyPath, pyFile = os.path.split(outParserFile)
    module = re.sub('\.py', '', pyFile)
    if pyPath not in sys.path: sys.path.append(pyPath)
    try:
        exec ('import %s' % module)
    except Exception as e:
        importCheckStatus = False
    else:
        try:
            u = None
            exec ('u = %s.getUnion()' % module)
            if u.fwSize() != u.ctypeSize():
                print("\n<<<ERROR>>> FW Size = %s, CType Size = %s; delta = %s bits (%s bytes)" % (str(u.fwSize()), str(u.ctypeSize()), str(u.fwSize()-u.ctypeSize()), str((u.fwSize()-u.ctypeSize())/8)))
                sizeCheckStatus = False
        except Exception as e:
            sizeCheckStatus = False

    return importCheckStatus, sizeCheckStatus


################################################################################################################
################################################################################################################
# Base class to store intermediate data object info
################################################################################################################
################################################################################################################
def getUnionInfo(obj):
    totalBitCount = 0
    bitfieldBitCount = 0
    nonBitfieldBitCount = 0
    maxSizeBitfieldCtypeClass = None
    maxSizeBitfieldCtypeClassList = []
    allEnumMembers = True

    for idx in range(len(obj.memberList)):
        m = obj.memberList[idx]
        if not m.enum: allEnumMembers = False
        if m.size > totalBitCount:
            totalBitCount = m.size
            nonBitfieldBitCount = m.size

    return totalBitCount, bitfieldBitCount, nonBitfieldBitCount, maxSizeBitfieldCtypeClassList, allEnumMembers


def roundUpToNextCtypeClass(maxSizeBitfieldCtypeClass, bitCount, pack):
    if re.match('^(.+\D)(\d+)$', maxSizeBitfieldCtypeClass):
        m = re.match('^(.+\D)(\d+)$', maxSizeBitfieldCtypeClass)

        # For 64-bit addressing processor, will have to include the "bitCount > 32" clause
        if pack >= 8 and bitCount > 32: return "%s%d" % (m.group(1), 64)
        if bitCount > 16: return "%s%d" % (m.group(1), 32)
        if bitCount > 8: return "%s%d" % (m.group(1), 16)
        return "%s%d" % (m.group(1), 8)


def roundDownToNextCtypeClass(ctypeClass, bitCount):
    if re.match('^(.+\D)(\d+)$', ctypeClass):
        m = re.match('^(.+\D)(\d+)$', ctypeClass)
        if bitCount >= 64: return "%s%d" % (m.group(1), 64)
        elif bitCount >= 32: return "%s%d" % (m.group(1), 32)
        elif bitCount >= 16: return "%s%d" % (m.group(1), 16)
        else: return "%s%d" % (m.group(1), 8)


def setAlternateBitfieldCtypeClass(obj, startIdx, endIdx, maxSizeBitfieldCtypeClass, bitCount, bitfieldOnlyObject):
    if bitfieldOnlyObject:
        maxSizeBitfieldCtypeClass = roundUpToNextCtypeClass(maxSizeBitfieldCtypeClass, obj.size, obj.pack)
    else: maxSizeBitfieldCtypeClass = roundUpToNextCtypeClass(maxSizeBitfieldCtypeClass, bitCount, obj.pack)

#    firstMemberInstance = 'preTrimActive'
#    if obj.memberList[startIdx].instance == firstMemberInstance:
#        obj.pprint(enable=1, children=True)
#        print bitCount
#        print "maxSizeBitfieldCtypeClass:", maxSizeBitfieldCtypeClass
#        pressReturnToContinue("setAlternateBitfieldCtypeClass Entry", enable=1)

    curCtypeClass = maxSizeBitfieldCtypeClass
    while re.match('^(.+\D)(\d+)$', curCtypeClass):
        m = re.match('^(.+\D)(\d+)$', curCtypeClass)
        nextCtypeClass = "%s%d" % (m.group(1), int(m.group(2)) / 2)
        if bitfieldOnlyObject:
            if (obj.size > int(m.group(2)) / 2) or (nextCtypeClass not in BASE_CTYPE_SIZE_BYTES.keys()): break
        elif (bitCount > int(m.group(2)) / 2) or (nextCtypeClass not in BASE_CTYPE_SIZE_BYTES.keys()): break
        curCtypeClass = nextCtypeClass

    # if BASE_CTYPE_SIZE_BYTES[curCtypeClass] * 8 >= bitCount:
    #     for idx in range(startIdx, endIdx + 1):
    #         obj.memberList[idx].ctypeClass = curCtypeClass
    for idx in range(startIdx, endIdx + 1):
        obj.memberList[idx].ctypeClass = curCtypeClass

#    if obj.memberList[startIdx].instance == firstMemberInstance:
#        obj.pprint(enable=1, children=True)
#        print "maxSizeBitfieldCtypeClass:", maxSizeBitfieldCtypeClass
#        print curCtypeClass
#        print bitCount
#        print BASE_CTYPE_SIZE_BYTES[curCtypeClass]*8
#        pressReturnToContinue("setAlternateBitfieldCtypeClass Exit", enable=1)


def getStructInfo(obj):
    startIdx = 0
    endIdx = 0
    bitCount = 0
    totalBitCount = 0
    bitfieldBitCount = 0
    nonBitfieldBitCount = 0
    maxSizeBitfieldCtypeClass = None
    maxSizeBitfieldCtypeClassList = []
    allEnumMembers = True

    for idx in range(len(obj.memberList)):
#        if obj.memberList[idx].instance == 'pliActiveBandNum':
#            obj.pprint(enable=1, children=True)
#            pressReturnToContinue('pliActiveBandNum',enable=1)

        m = obj.memberList[idx]
        if not m.enum: allEnumMembers = False
        if not m.bitfield:
            totalBitCount += m.size
            nonBitfieldBitCount += m.size
            continue

        # Only bitfields are expected beyond this point
        totalBitCount += m.size
        bitfieldBitCount += m.size

        if (idx == 0) or (not obj.memberList[idx-1].bitfield):
            # Start of new bitfield sequence
            bitCount = 0
            startIdx = idx
            maxSize = 0
            maxSizeBitfieldCtypeClass = None

        if m.dataType in ['enum'] and BASE_CTYPE_SIZE_BYTES[BASE_CTYPE_MAP[m.dataType]] >= maxSize:
            maxSize = BASE_CTYPE_SIZE_BYTES[BASE_CTYPE_MAP[m.dataType]]
            maxSizeBitfieldCtypeClass = BASE_CTYPE_MAP[m.dataType]

        elif m.typedef in BASE_CTYPE_MAP.keys() and BASE_CTYPE_SIZE_BYTES[BASE_CTYPE_MAP[m.typedef]] >= maxSize:
            maxSize = BASE_CTYPE_SIZE_BYTES[BASE_CTYPE_MAP[m.typedef]]
            maxSizeBitfieldCtypeClass = BASE_CTYPE_MAP[m.typedef]

        bitCount += m.size

        if (idx+1) == len(obj.memberList) or not obj.memberList[idx+1].bitfield:
            # End of current bitfield sequence
            endIdx = idx
            maxSizeBitfieldCtypeClassList.append([startIdx, endIdx, maxSizeBitfieldCtypeClass, bitCount])

    return totalBitCount, bitfieldBitCount, nonBitfieldBitCount, maxSizeBitfieldCtypeClassList, allEnumMembers


def addPaddingToNonBitfieldStruct(obj):
    global PadSequenceNumber
    totalBitCount = 0
    for m in obj.memberList:
        arrayElements = 1
        for i in m.arrayLen: arrayElements = arrayElements * i
        totalBitCount += m.size * arrayElements

    # Handling large mismatches in PAD_TO_SECTORSIZE structs in NAND FW.
    # Typically, these PAD_TO_SECTORSIZE structs have only a few non-bitfield members; will use those characteristics to identify them.
    # This is more of a hack for now as it is hard to differentitate PAD_TO_SECTORSIZE structs from those loosely packed structs.
    if len(obj.memberList) < 4 and obj.size > (totalBitCount+8*8):  # + 8*8 since mismatches =< 64 bits can be handled through natural ctypes packing
        arrayLen = [(obj.size-totalBitCount)/8]
        myObj = DataTypeObject(uid=obj.uid, instance='ctypeAddedPad%d' % PadSequenceNumber, dataType='uint8_t', typedef='uint8_t', depth=obj.depth+1,
                               startIdx=obj.startIdx, endIdx=obj.endIdx, anon=None, arrayLen=arrayLen, enum=None, pack=obj.pack,
                               size = obj.size-totalBitCount, width = obj.size - totalBitCount)
        obj.memberList.append(myObj)
        PadSequenceNumber += 1

        # print "object size:  ", obj.size
        # print "totalBitCount:", totalBitCount
        # obj.pprint(enable=1, children=True)
        # pressReturnToContinue(enable=1, children=True)
        # pressReturnToContinue(obj.pprint(enable=1, children=True))


def normalizeBitfieldMemberCtypeClass(obj):
    if obj.dataType == 'union':
        totalBitCount, bitfieldBitCount, nonBitfieldBitCount, maxSizeBitfieldCtypeClassList, allEnumMembers = getUnionInfo(obj)
    else:
        totalBitCount, bitfieldBitCount, nonBitfieldBitCount, maxSizeBitfieldCtypeClassList, allEnumMembers = getStructInfo(obj)

    for startIdx, endIdx, maxSizeBitfieldCtypeClass, bitCount in maxSizeBitfieldCtypeClassList:
        setAlternateBitfieldCtypeClass(obj, startIdx, endIdx, maxSizeBitfieldCtypeClass, bitCount, bitfieldBitCount==totalBitCount)

    # Since autoParser works off of post-compiled debug information, it only sees the result of a
    # directive such as PAD_TO_SECTORSIZE and not the directive itself.  We need a work-around for it.
    if not bitfieldBitCount: addPaddingToNonBitfieldStruct(obj)

    # Correct enum size as needed
    if allEnumMembers and not bitfieldBitCount:
        for m in obj.memberList:
            m.ctypeClass = roundDownToNextCtypeClass(BASE_CTYPE_MAP[m.dataType], m.size)

    # obj.pprint(enable=1, children=True)
    # print("Struct Size:                   %s" % str(obj.size))
    # print("totalBitCount:                 %s" % str(totalBitCount))
    # print("bitfieldBitCount:              %s" % str(bitfieldBitCount))
    # print("nonBitfieldBitCount:           %s" %str(nonBitfieldBitCount))
    # print("maxSizeBitfieldCtypeClassList: %s" % str(maxSizeBitfieldCtypeClassList))
    # pressReturnToContinue(enable=1)


def savePickleObject(obj, outFile):
    oFile = open(outFile, "wb")
    pickle.dump(obj, oFile)
    oFile.close()


def loadPickleObject(inFile):
    try:
        with open(inFile, 'rb') as f: obj = pickle.load(f)
        return obj
    except UnicodeDecodeError as e:
        with open(inFile, 'rb') as f: obj = pickle.load(f, encoding='latin1')
        return obj
    except Exception as e:
        print('    Unable to load data ', inFile, ':', e)
        return None


class DataTypeObject(object):
    """
    Generic data struct object used to traverse the debug symbol table (DST)
    Attributes:
        Tracking node for information to construct a c-type from context free grammar (CFG)
            myObj = DataTypeObject(dataObject=dataObject, typedef=typedef, uid=uid,
    """

    def __init__(self, uid=None, instance=None, typedef=None, dataType=None, info=None, size=None, offset=None, depth=None, startIdx=None, endIdx=None,
                 width=None, anon=False, unnamed=False, arrayLen=[1], enum=False, bitfield=False, versionMajor=0xBADD, versionMinor=0xC0DE, pack=4,
                 versionMajorMemberName=None, versionMinorMemberName=None, inlined=False, readNlba=None, writeNlba=None):
        """ Init class with nil content."""
        self.uid = uid                  # UID
        self.instance = instance        # Example: bis
        self.typedef = typedef          # Example: Bist_t
        self.dataType = dataType        # struct, union, enum, etc
        self.info = info                #
        self.size = size                # Size in bits
        self.offset = offset
        self.depth = depth
        self.startIdx = startIdx
        self.endIdx = endIdx
        self.width = width

        self.location = []              # Use by DataCheck to detect structural changes
        self.dataCheckUid = ''          # Use by DataCheck to detect structural changes
        self.ctypeClass = None          # Used to dynamically adjust ctypeClass based on struct size
        self.status = {}                # Hash to track any and all parsing related issues; used by DataCheck and other autoParser-based tools

        self.anon = anon
        self.unnamed = unnamed
        self.inlined = inlined
        self.arrayLen = arrayLen        # Default is array of length 1
        self.enum = enum
        self.bitfield = bitfield
        self.versionMajor = versionMajor
        self.versionMinor = versionMinor
        self.pack = pack

        self.readNlba = readNlba
        self.writeNlba = writeNlba
        self.versionMajorMemberName = versionMajorMemberName
        self.versionMinorMemberName = versionMinorMemberName

        self.memberList = []

    def pprint(self, indent=None, enable=ENABLE_DEBUG_ENTER, all=False, children=False):
        if indent is None: indent = self.depth * 20
        if enable: print("")
        dprint("uid:            %s" % (str(self.uid)), indent, enable)
        dprint("instance:       %s" % (str(self.instance)), indent, enable)
        dprint("typedef:        %s" % (str(self.typedef)), indent, enable)
        dprint("ctypeClass:     %s" % (str(self.ctypeClass)), indent, enable)
        dprint("dataType:       %s" % (str(self.dataType)), indent, enable)
        dprint("pack:           %s" % (str(self.pack)), indent, enable)
        dprint("info:           %s" % (str(self.info)), indent, enable)
        dprint("size:           %s" % (str(self.size)), indent, enable)
        dprint("offset:         %s" % (str(self.offset)), indent, enable)
        dprint("depth:          %s" % (str(self.depth)), indent, enable)
        dprint("startIdx:       %s" % (str(self.startIdx)), indent, enable)
        dprint("endIdx:         %s" % (str(self.endIdx)), indent, enable)
        dprint("width:          %s" % (str(self.width)), indent, enable)
        dprint("location:       %s" % (str(self.location)), indent, enable)
        dprint("dataCheckUid:   %s" % (str(self.dataCheckUid)), indent, enable)
        dprint("anon:           %s" % (str(self.anon)), indent, enable)
        dprint("unnamed:        %s" % (str(self.unnamed)), indent, enable)
        dprint("arrayLen:       %s" % (str(self.arrayLen)), indent, enable)
        dprint("enum:           %s" % (str(self.enum)), indent, enable)
        dprint("bitfield:       %s" % (str(self.bitfield)), indent, enable)
        dprint("versionMajor:   %s" % (str(self.versionMajor)), indent, enable)
        dprint("versionMinor:   %s" % (str(self.versionMinor)), indent, enable)
        if len(self.memberList) <= 0:
            dprint("memberList:     %s" % (str(self.memberList)), indent, enable)
        else:
            for i in range(len(self.memberList)):
                if not i:
                    dprint("memberList:     %i) %s" % (i+1, str(self.memberList[i])), indent, enable)
                    if all: self.memberList[i].pprint(indent=indent+20, enable=enable, all=all)
                    elif children: self.memberList[i].pprint(indent=indent + 20, enable=enable)
                else:
                    dprint("                %i) %s" % (i+1, str(self.memberList[i])), indent, enable)
                    if all: self.memberList[i].pprint(indent=indent+20, enable=enable, all=all)
                    elif children: self.memberList[i].pprint(indent=indent + 20, enable=enable)
        if enable: print("")

    def visualInspection(self, enable=ENABLE_DEBUG_ENTER):
        if self.depth == 0: dprint("", enable=enable)
        dprint("%s:%s:%s:ctypeClass=%s:size=%s:offset=%s:inlined=%s:anon=%s:arraylen=%s:enum=%s:bitfield=%s:width=%s" %\
               (str(self.instance), str(self.typedef), str(self.dataType), self.ctypeClass, str(self.size), str(self.offset), str(self.inlined),
                str(self.anon), str(self.arrayLen), str(self.enum), str(self.bitfield), str(self.width)), indent=self.depth*4, enable=enable)
        for m in (self).memberList: m.visualInspection(enable=enable)

    def generateCtypeJson(self, outFile):
        with open(outFile, 'wb') as jsonFile:
            json.dump((self), jsonFile, default=lambda o: o.__dict__, indent=4, sort_keys=True)

        # To load JSON data back into an object ...
        # class AutoParserObject(object):
        #     def __init__(self, data):
        #         self.__dict__ = json.loads(data)
        #
        # json_data = open(xFile, 'rb').read()
        # obj = AutoParserObject(json_data)

    def generateCtypeParserLib(self, outFile=None, generatedCtypeClasses=[]):
        preClassString = ""
        classString = ""
        postClassString = ""

        # Generate class object for the root data struct
        if (self.dataType is not None) and (self.dataType.lower() == 'enum'):     # Generate hash for enumeration type
            if self.typedef is None or self.typedef == "":
                self = generateInlinedEnumTypedefName(self)
            if self.typedef not in generatedCtypeClasses:
                outPutLine("\n%s = {" % self.typedef, outFile=outFile)
                for m in self.memberList:
                    outPutLine("    %s: \'%s\'," % (m.typedef, m.instance), outFile=outFile)
                outPutLine('}', outFile=outFile)
                generatedCtypeClasses.append(self.typedef)
        else:
            if self.anon:
                self = generateAnonymousUnionStructNames(self)

            if self.typedef is None or self.typedef == "":
                self = generateUnamedUnionStructNames(self)

            if self.typedef not in generatedCtypeClasses:
                if self.dataType == 'union':
                    classString += "\nclass %s(Union):\n" % self.typedef
                else:
                    classString += "\nclass %s(Structure):\n" % self.typedef
                generatedCtypeClasses.append(self.typedef)

                # Printing anonymous structs/unions first
                maxLen = 0
                for m in self.memberList:
                    if m.anon:
                        m = generateAnonymousUnionStructNames(m)

                    if m.typedef is None or m.typedef == "":
                        m = generateUnamedUnionStructNames(m)

                    if m.dataType in ['union', 'struct'] and m.anon:
                        classString += "    _anonymous_ = (\"%s__\",)\n" % m.typedef
                        preClassString += "\n_%s%s = %s\n" % (re.sub('^_+', '', self.typedef), m.typedef, m.typedef)
                    if m.unnamed:
                        preClassString += "\n_%s%s = %s\n" % (re.sub('^_+', '', self.typedef), m.typedef, m.typedef)
                    if len(str(m.instance)) > maxLen: maxLen = len(str(m.instance))
                    if len(str(m.typedef)) > maxLen: maxLen = len(str(m.typedef))

                classString += "    _pack_   = %s\n" % str(self.pack)
                classString += "    _fields_ = [\n"

                # Get this maxSizeTypeClass in order to make bit field typedef of same size (see below)
                normalizeBitfieldMemberCtypeClass(self)

                for m in self.memberList:
                    ctypeComment = ""
                    if m.dataType in ['enum'] or m.enum:
                        ctypeClass = BASE_CTYPE_MAP[m.dataType]
                        ctypeComment = "# %s" % m.typedef
                    elif m.typedef in BASE_CTYPE_MAP.keys():
                        ctypeClass = BASE_CTYPE_MAP[m.typedef]
                    elif m.dataType in BASE_CTYPE_MAP.keys():
                        ctypeClass = BASE_CTYPE_MAP[m.dataType]
                    else: ctypeClass = m.typedef

                    # Renaming to avoid using Python keywords as variable names
                    if m.instance in VARIABLE_KEYWORD_REMAP.keys():
                        m.instance = VARIABLE_KEYWORD_REMAP[m.instance]

                    # Attempt to make bitfield typedef of same size
                    if m.ctypeClass is not None: ctypeClass = m.ctypeClass

                    if m.bitfield and (m.enum or m.dataType in ['enum']):
                        if m.width is not None:
                            classString += "                (%-*s, %s, %s), %s\n" % (maxLen + 4, "\"%s\"" % m.instance, ctypeClass, m.width, ctypeComment)
                        else: classString += "                (%-*s, %s, %s), %s\n" % (maxLen + 4, "\"%s\"" % m.instance, ctypeClass, m.size, ctypeComment)
                        if ctypeComment == "":
                            if (m.typedef in BASE_CTYPE_MAP.keys()) or m.enum:
                                postClassString += "        retString += \"%s%-*s: %%s\\n\" %% str(self.%s)\n" % ((m.depth - 1) * 4 * " ", maxLen + 2, m.instance, m.instance)
                            else: postClassString += "        retString += \"%s%-*s: %%s\" %% (\"\\n\" + str(self.%s.getStr()))\n" % ((m.depth - 1) * 4 * " ", maxLen + 2, m.instance, m.instance)
                        else: postClassString += "        retString += \"%s%-*s: %%s\\n\" %% str(%s[self.%s] if %s.has_key(self.%s) else %s[-1])\n" % ( (m.depth - 1) * 4 * " ", maxLen + 2, m.instance, m.typedef, m.instance, m.typedef, m.instance, m.typedef)
                    elif m.bitfield:
                        if m.width is not None:
                            classString += "                (%-*s, %s, %s),\n" % (maxLen+4, "\"%s\"" % m.instance, ctypeClass, m.width)
                        else: classString += "                (%-*s, %s, %s),\n" % (maxLen + 4, "\"%s\"" % m.instance, ctypeClass, m.size)
                        postClassString += "        retString += \"%s%-*s: %%s\\n\" %% str(self.%s)\n" % ((m.depth-1)*4*" ", maxLen+2, m.instance, m.instance)
                    else:
                        arrayElements = 1
                        for i in m.arrayLen: arrayElements = arrayElements * i

                        if arrayElements > 1 and len(m.arrayLen) == 1:
                            if m.dataType in ['union', 'struct', 'enum'] and m.anon:
                                classString += "                (%-*s, %s * %i), %s\n" % (maxLen+4, "\"%s__\"" % m.typedef, ctypeClass, arrayElements, ctypeComment)
                            else: classString += "                (%-*s, %s * %i), %s\n" % (maxLen+4, "\"%s\"" % m.instance, ctypeClass, arrayElements, ctypeComment)

                            if not any(s in str(m.instance).lower() for s in ARRAY_SUBSTRINGS_TO_SKIP):
                                postClassString += "\n        for i in range(%s):\n" % arrayElements
                                postClassString += "\n              try:\n"
                                if (m.typedef in BASE_CTYPE_MAP.keys()) or m.enum:
                                    postClassString += "                  retString += \"%s%-*s: %%s\\n\" %% (i, str(self.%s[i]))\n" % ((m.depth-1)*4*" ", maxLen+2, "%s[%%i]" % m.instance, m.instance)
                                else:
                                    postClassString += "                  retString += \"%s%-*s: %%s\" %% (i, \"\\n\"+str(self.%s[i].getStr()))\n" % ((m.depth-1)*4*" ", maxLen + 2, "%s[%%i]" % m.instance, m.instance)
                                postClassString += "\n              except Exception as ErrorFound:\n"
                                postClassString += "\n                    errorString = (\"ERROR in {__file__} @{framePrintNo} with {ErrorFound}\".format(__file__=str(__file__), framePrintNo=str(sys._getframe().f_lineno)))\n"
                                postClassString += "\n                    retString += \"    objectId             : %s\\n\" % str(self.objectId)\n"
                                postClassString += "\n                    print(\"{errorString}\\n\".format(errorString=str(errorString)))\n"
                                postClassString += "\n"

                        elif arrayElements > 1 and len(m.arrayLen) > 1:
                            ctypeArrayString = None
                            for i in m.arrayLen:
                                if ctypeArrayString is None:
                                    ctypeArrayString = "(%s * %s)" % (ctypeClass, str(i))
                                else: ctypeArrayString = "(%s * %s)" % (ctypeArrayString, str(i))

                            if m.dataType in ['union', 'struct', 'enum'] and m.anon:
                                classString += "                (%-*s, %s), %s\n" % (maxLen+4, "\"%s__\"" % m.typedef, ctypeArrayString, ctypeComment)
                            else: classString += "                (%-*s, %s), %s\n" % (maxLen+4, "\"%s\"" % m.instance, ctypeArrayString, ctypeComment)

                            if not any(s in str(m.instance).lower() for s in ARRAY_SUBSTRINGS_TO_SKIP):
                                indent = ""
                                postClassString += "\n"
                                indexOrd = ord('i')
                                indexingString = ""
                                arrayIndexing = ""
                                myArrayLen = copy.deepcopy(m.arrayLen)
                                myArrayLen.reverse()
                                for i in myArrayLen:
                                    postClassString += "        %sfor %s in range(%s):\n" % (indent, chr(indexOrd), str(i))
                                    arrayIndexing = arrayIndexing + "[%s]" % chr(indexOrd)
                                    indexingString = indexingString + "%s, " % chr(indexOrd)
                                    indent = indent + "    "
                                    indexOrd += 1

                                if (m.typedef in BASE_CTYPE_MAP.keys()) or m.enum:
                                    postClassString += "        %sretString += \"%s%-*s: %%s\\n\" %% (%sstr(self.%s%s))\n" % \
                                                       (indent, (m.depth-1)*4*" ", maxLen+2, "%s%s" % (m.instance, "[%i]"*len(m.arrayLen)), indexingString, m.instance, arrayIndexing)
                                else:
                                    postClassString += "        %sretString += \"%s%-*s: %%s\" %% (%s\"\\n\"+str(self.%s%s.getStr()))\n" % \
                                                       (indent, (m.depth-1)*4*" ", maxLen + 2, "%s%s" % (m.instance, "[%i]"*len(m.arrayLen)), indexingString, m.instance, arrayIndexing)
                                postClassString += "\n"

                        else:
                            if m.dataType in ['union', 'struct'] and m.anon:
                                classString += "                (%-*s, %s), %s\n" % (maxLen+4, "\"%s__\"" % m.typedef, ctypeClass, ctypeComment)
                                postClassString += "        retString += \"%s%-*s: %%s\" %% (\"\\n\"+str(self.%s))\n" % ((m.depth-1)*4*" ", maxLen+2, "%s__" % m.typedef, "%s__.getStr()" % m.typedef)
                            else:
                                classString += "                (%-*s, %s), %s\n" % (maxLen+4, "\"%s\"" % m.instance, ctypeClass, ctypeComment)
                                if ctypeComment == "":
                                    if (m.typedef in BASE_CTYPE_MAP.keys()) or m.enum:
                                        postClassString += "        retString += \"%s%-*s: %%s\\n\" %% str(self.%s)\n" % ((m.depth-1)*4*" ", maxLen+2, m.instance, m.instance)
                                    else: postClassString += "        retString += \"%s%-*s: %%s\" %% (\"\\n\" + str(self.%s.getStr()))\n" % ((m.depth - 1) * 4 * " ", maxLen + 2, m.instance, m.instance)
                                else: 
                                    postClassString += "        retString += \"%s%-*s: %%s\\n\" %% str(%s[self.%s] if %s.has_key(self.%s) else %s[-1])\n" % ((m.depth-1)*4*" ", maxLen+2, m.instance, m.typedef, m.instance, m.typedef, m.instance, m.typedef)

                classString += "               ]\n"

                postClassString = "    def getStr(self):\n" + "        retString = \"\"\n" + postClassString + "        return retString\n"

                if self.depth == 0:
                    postClassString += "\n"
                    postClassString += "    def parse(self, outFile=None):\n"
                    postClassString += "        if outFile is not None:\n"
                    postClassString += "            with open(outFile, 'wb') as oFile: \n"
                    postClassString += "                oFile.write('%s\\n' % self.getStr())\n"
                    postClassString += "        else:\n"
                    postClassString += "            print(self.getStr())\n"

                outPutLine(preClassString, outFile=outFile)
                outPutLine(classString, outFile=outFile)
                outPutLine(postClassString, outFile=outFile)

        # Generate the overall union, getStruct() method and getUnion() method
        if self.depth == 0:
            unionClassString = "\n"
            unionClassString += "\n# Main class to import if not using getUnion() and getStruct methods."
            unionClassString += "\nclass %s_union(Union):\n" % self.typedef
            unionClassString += "    _pack_   = %s\n" % str(self.pack)
            unionClassString += "    _fields_ = [\n"
            unionClassString += "                (\"Struct\", %s),\n" % self.typedef
            unionClassString += "                (\"Data\", c_ubyte * sizeof(%s)),\n" % self.typedef
            unionClassString += "               ]\n"
            unionClassString += "\n"
            unionClassString += "    def __init__(self, inFile=None, inBuffer=None):\n"
#           unionClassString += "        self.libc = cdll.msvcrt\n"
#           unionClassString += "        self.bufferSize = sizeof(self)\n"
#           unionClassString += "        self.buffer = cast(self.libc.calloc(1, self.bufferSize), POINTER(c_ubyte))\n"
            unionClassString += "        self.initialized = False\n"
            unionClassString += "\n"
            unionClassString += "        if (inFile is not None) and os.path.exists(inFile):\n"
            unionClassString += "            readFile(inFile, buffer=self.Data, numBytes=int(self.ctypeSize()/8))\n"
            unionClassString += "            self.initialized = True\n"
            unionClassString += "        elif inBuffer is not None:\n"
            unionClassString += "            for i in range(sizeof(self)): self.Data[i] = copy.deepcopy(inBuffer[i])\n"
            unionClassString += "            self.initialized = True\n"
            unionClassString += "\n"
            unionClassString += "    def initialize(self, inFile):\n"
            unionClassString += "        if os.path.exists(inFile):\n"
            unionClassString += "            readFile(inFile, buffer=self.Data, numBytes=int(self.ctypeSize()/8))\n"
            unionClassString += "        else: print(\"The inFile %s does not exist.  Use union.initialize(inFile) as needed.\" % inFile)\n"
            unionClassString += "\n"
            unionClassString += "    def fwSize(self): return %s\n" % str(self.size)
            unionClassString += "\n"
            unionClassString += "    def ctypeSize(self): return sizeof(self)*8\n"
            unionClassString += "\n"
            unionClassString += "    def sizeCheck(self): return sizeof(self)*8 == %s\n" % str(self.size)
            unionClassString += "\n"
            unionClassString += "    def expectedMajor(self): return %s\n" % str(self.versionMajor)
            unionClassString += "\n"

            if self.versionMajorMemberName is not None:
                unionClassString += "    def getVersionMajor(self):\n"
                unionClassString += "        if self.initialized:\n"
                unionClassString += "            try: return self.Struct.%s\n" % str(self.versionMajorMemberName)
                unionClassString += "            except: return None\n"
                unionClassString += "        else: return None\n"
            else:
                unionClassString += "    def getVersionMajor(self): return %s\n" % str(self.versionMajor)

            unionClassString += "\n"
            unionClassString += "    def expectedMinor(self): return %s\n" % str(self.versionMinor)
            unionClassString += "\n"

            if self.versionMinorMemberName is not None:
                unionClassString += "    def getVersionMinor(self):\n"
                unionClassString += "        if self.initialized:\n"
                unionClassString += "            try: return self.Struct.%s\n" % str(self.versionMinorMemberName)
                unionClassString += "            except: return None\n"
                unionClassString += "        else: return None\n"
            else:
                unionClassString += "    def getVersionMinor(self): return %s\n" % str(self.versionMinor)

            unionClassString += "\n"
            unionClassString += "    def getStruct(self): return self.Struct\n"
            unionClassString += "\n"
            unionClassString += "    def parse(self, outFile=None, outBinFile=None):\n"
            unionClassString += "        if outFile is not None:\n"
            unionClassString += "            with open(outFile, 'wb') as oFile: oFile.write('%s\\n' % self.Struct.getStr())\n"
            unionClassString += "        else: print(self.Struct.getStr())\n"
            unionClassString += "        if outBinFile is not None:\n"
            unionClassString += "            with open(outBinFile, 'wb') as obFile: obFile.write(self.Data)\n"
            outPutLine(unionClassString, outFile=outFile)

            utilityMethodsString = "\n"
            utilityMethodsString += "def getUnion(inFile=None, inBuffer=None):\n"
            utilityMethodsString += "    return %s_union(inFile=inFile, inBuffer=inBuffer)\n" % self.typedef
            utilityMethodsString += "\n\n"
            utilityMethodsString += "def readFile(fileName, buffer, numBytes=0, offsetBytes=0):\n"
            utilityMethodsString += "    if not os.path.exists(fileName):\n"
            utilityMethodsString += "        raise IOError(\"File %s does not exist!!!\" % (fileName))\n"
            utilityMethodsString += "    fileSizeInBytes = os.stat(fileName).st_size\n"
            utilityMethodsString += "    if offsetBytes < 0:\n"
            utilityMethodsString += "        raise IOError(\"Offset lower than zero. Offset = %d\" % (offsetBytes))\n"
            utilityMethodsString += "    if offsetBytes > fileSizeInBytes:\n"
            utilityMethodsString += "        raise IOError(\"Offset bigger than file size. Offset = %d, File size = %d\" % (offsetBytes, fileSizeInBytes))\n"
            utilityMethodsString += "    if int(numBytes) <= 0:\n"
            utilityMethodsString += "        raise IOError(\"Number Bytes to read must be bigger than 0, NumBytes = %d\" % (numBytes))\n"
            utilityMethodsString += "    with open(fileName, \"rb\") as fp:\n"
            utilityMethodsString += "        if offsetBytes > 0: fp.seek(offsetBytes, 0)\n"
            utilityMethodsString += "        if fileSizeInBytes <= offsetBytes + int(numBytes):\n"
            utilityMethodsString += "            # read the whole file\n"
            utilityMethodsString += "            dataFromFile = fp.read()\n"
            utilityMethodsString += "            if len(dataFromFile) != (fileSizeInBytes - offsetBytes):\n"
            utilityMethodsString += "                raise IOError(\"Bytes read does not match size of the data file. Data file size = %d , Bytes read = %d\" % (fileSizeInBytes - offsetBytes, len(dataFromFile)))\n"
            utilityMethodsString += "            offsetBytes = 0  # no more data to be read\n"
            utilityMethodsString += "        else:\n"
            utilityMethodsString += "            # read only the request chunk\n"
            utilityMethodsString += "            dataFromFile = fp.read(int(numBytes))\n"
            utilityMethodsString += "            if len(dataFromFile) != int(numBytes):\n"
            utilityMethodsString += "                raise IOError(\"Bytes read does not match size of the file. Data file size = %d , Bytes read = %d\" % (int(numBytes), len(dataFromFile)))\n"
            utilityMethodsString += "            offsetBytes = offsetBytes + int(numBytes)\n"
            utilityMethodsString += "            realOffset = fp.tell()\n"
            utilityMethodsString += "            if realOffset != offsetBytes:\n"
            utilityMethodsString += "                raise IOError(\"Internal error, wrong offset in the file. Real offset = %d , Calculated offset = %d\" % (realOffset, offsetBytes))\n"
            utilityMethodsString += "    index = 0\n"
            utilityMethodsString += "    for b in dataFromFile:\n"
            utilityMethodsString += "        try:\n"
            utilityMethodsString += "            buffer[index] = ord(chr(b))\n"
            utilityMethodsString += "        except TypeError as seenError:\n"
            utilityMethodsString += "            try:\n"
            utilityMethodsString += "                print(\"Error in {__file__} by {seenError} from {b}\".format(__file__=str(__file__), seenError=str(seenError), b=str(b)))\n"
            utilityMethodsString += "                buffer[index] = ord(chr(b))\n"
            utilityMethodsString += "            except TypeError as seenErrorDoubleRambow:\n"
            utilityMethodsString += "                print(\"Nested Error in {__file__} by {seenErrorDoubleRambow} from {b}\".format(__file__=str(__file__), seenErrorDoubleRambow=str(seenErrorDoubleRambow), b=str(b)))\n"
            utilityMethodsString += "                buffer[index] = ord(chr(b))\n"
            utilityMethodsString += "        index = index + 1\n"
            utilityMethodsString += "    return offsetBytes    # return the current offset in the file or zero if all data was already read\n"
            outPutLine(utilityMethodsString, outFile=outFile)

    def cFormatter(self, storageString="", indentBase=None):
        # Generate class object for the root data struct

        global alreadyGeneratedCstructs

        if indentBase is None: indentBase=self.depth

        # Translating enums into Python hashes
        if (self.dataType is not None) and (self.dataType.lower() == 'enum'):     # Generate hash for enumeration type
            if self.typedef in alreadyGeneratedCstructs: return ""
            storageString = "typedef enum\n{\n"
            maxNameLen = 0
            maxValueLen = 0
            for m in self.memberList:
                if maxNameLen < len(str(m.instance)): maxNameLen = len(str(m.instance))
                if maxValueLen < len(str(m.typedef)): maxValueLen = len(str(m.typedef))
            for m in self.memberList:
                storageString += "    %-*s = %*s,\n" % (maxNameLen, m.instance, maxValueLen, m.typedef)
            storageString += '} %s;\n' % self.typedef
            alreadyGeneratedCstructs.append(self.typedef)
            return storageString

        # Translating non-inlined unions and structs
        elif (self.dataType is not None) and (self.dataType.lower() in ['union', 'struct']) and (not self.inlined):
            if self.typedef in alreadyGeneratedCstructs: return storageString
            storageString += "typedef %s\n{\n" % self.dataType
            maxTypedefLen = 0
            maxInstanceLen = 0
            for m in self.memberList:
                if (m.instance is not None) and (len(m.instance) > maxInstanceLen): maxInstanceLen = len(m.instance)
                if (m.typedef is not None) and (not re.match('^__', str(m.typedef))) and (len(str(m.typedef)) > maxTypedefLen): maxTypedefLen = len(str(m.typedef))

            for m in self.memberList:
                if (m.typedef is not None) and ('logical' in m.typedef.lower()):
                    typedefSub = 'bool'
                else: typedefSub = m.typedef

                if m.bitfield:
                    storageString += "%s%-*s %-*s: %s;\n" % ("    "*(m.depth-self.depth), maxTypedefLen, typedefSub, maxInstanceLen, m.instance, str(m.width))
                    continue

                if (m.dataType is not None) and (m.dataType.lower() in ['union', 'struct']) and m.inlined:
                    storageString += m.cFormatter(indentBase=self.depth)
                    continue

                if (m.dataType is not None) and (m.dataType.lower() in ['union', 'struct']) and not m.inlined:
                    storageString += m.cFormatter(indentBase=indentBase)
                    # Note:  Not doing "continue" here so that the next if-else clause will print the inlined struct-instance pair

                if m.arrayLen[0]>1 or len(m.arrayLen)>1:
                    tmpArrayLen = copy.deepcopy(m.arrayLen)
                    tmpArrayLen.reverse()
                    tmpArrayString = re.sub(', ', '][', str(tmpArrayLen))
                    storageString += "%s%-*s %s%s;\n" % ("    "*(m.depth-self.depth), maxTypedefLen, typedefSub, m.instance, tmpArrayString)

                else: storageString += "%s%-*s %s;\n" % ("    "*(m.depth-self.depth), maxTypedefLen, typedefSub, m.instance)

            storageString += "} %s;\n" % self.typedef
            alreadyGeneratedCstructs.append(self.typedef)
            return storageString

        # Translating inlined unions and structs
        elif (self.dataType is not None) and (self.dataType.lower() in ['union', 'struct']) and self.inlined:
            storageString += "%s%s\n%s{\n" % ("    " * (self.depth-indentBase), self.dataType, "    " * (self.depth-indentBase))
            maxTypedefLen = 0
            maxInstanceLen = 0
            for m in self.memberList:
                if (m.instance is not None) and (len(m.instance) > maxInstanceLen): maxInstanceLen = len(m.instance)
                if (m.typedef is not None) and (not re.match('^__', str(m.typedef))) and (len(str(m.typedef)) > maxTypedefLen): maxTypedefLen = len(str(m.typedef))

            for m in self.memberList:
                if (m.typedef is not None) and ('logical' in m.typedef.lower()):
                    typedefSub = 'bool'
                else: typedefSub = m.typedef

                if m.bitfield:
                    storageString += "%s%-*s %-*s: %s;\n" % ("    "*(m.depth-indentBase), maxTypedefLen, typedefSub, maxInstanceLen, m.instance, str(m.width))
                    continue

                if (m.dataType is not None) and (m.dataType.lower() in ['union', 'struct']) and m.inlined:
                    storageString += m.cFormatter(indentBase=indentBase)
                    continue

                if (m.dataType is not None) and (m.dataType.lower() in ['union', 'struct']) and not m.inlined:
                    storageString += m.cFormatter(indentBase=indentBase)
                    # Note:  Not doing "continue" here so that the next if-else clause will print the inlined struct-instance pair

                if m.arrayLen[0] > 1 or len(m.arrayLen) > 1:
                    tmpArrayLen = copy.deepcopy(m.arrayLen)
                    tmpArrayLen.reverse()
                    tmpArrayString = re.sub(', ', '][', str(tmpArrayLen))
                    storageString += "%s%-*s %s%s;\n" % ("    "*(m.depth-indentBase), maxTypedefLen, typedefSub, m.instance, tmpArrayString)

                else: storageString += "%s%-*s %s;\n" % ("    "*(m.depth-indentBase), maxTypedefLen, typedefSub, m.instance)

            if re.search("__Ut\d+$", str(self.instance)):
                storageString += "%s};\n" % ("    " * (self.depth-indentBase))
            else: storageString += "%s} %s;\n" % ("    " * (self.depth-indentBase), self.instance)

            return storageString


################################################################################################################
################################################################################################################
# Class for FW C-Struct extraction Python C-Type generation
################################################################################################################
################################################################################################################
class AutoParser(object):
    """Class to extract FW C-Structs for each data Objects

    Attributes:
        Traverses properties of the firmware code to construct the destination type
        in multiple stages.
    """

    def __init__(self, options):
        """ Init class with nil and static content."""
        ######################################################################
        ######################################################################
        #  Data members needed for FW C-Struct extraction
        ######################################################################
        ######################################################################

        self.outDir = os.path.abspath(os.path.join(options.fwBuildOutputDir, 'autoParsers'))
        if not os.path.exists(self.outDir):
            try:
                os.makedirs(self.outDir)
            except OSError:
                print("Failed to create the output folder")
                if ENABLE_DEBUG_ENTER: quit(2)
        print("self.outDir:                 %s" % self.outDir)

        self.logFileName = os.path.join(self.outDir, 'autoParser_log.txt')
        logging.basicConfig(filename=self.logFileName, filemode='w', format='%(asctime)s %(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
        logging.info('autoParser.py Log')
        # logging.debug('Log debug message to file')
        # logging.info('Log info message to file')
        # logging.warning('Log warning message to file')
        self.log = logging

        self.options = options
        self.verbose = options.verbose
        self.dbgDumpFile = os.path.join(self.outDir, 'autoParser_dbgDump.txt')
        self.ghsPath = ghsPath
        self.AUTOPARSER_DATA_OBJECT_LIST = []

        ######################################################################
        ######################################################################
        # Data members needed for Python C-Type generation
        ######################################################################
        ######################################################################
        self.versionedParserFolder = os.path.join(self.outDir, 'versioned')
        if not os.path.exists(self.versionedParserFolder):
            try:
                os.makedirs(self.versionedParserFolder)
            except OSError:
                print("Failed to create the versioned parser folder")
                if ENABLE_DEBUG_ENTER: quit(7)

        self.unversionedParserFolder = os.path.join(self.outDir, 'unversioned')
        if not os.path.exists(self.unversionedParserFolder):
            try:
                os.makedirs(self.unversionedParserFolder)
            except OSError:
                print("Failed to create the unversioned parser folder")
                if ENABLE_DEBUG_ENTER: quit(7)

        self.pickleParserFolder = os.path.join(self.outDir, 'pickle')
        if not os.path.exists(self.pickleParserFolder):
            try:
                os.makedirs(self.pickleParserFolder)
            except OSError:
                print("Failed to create the json parser folder")
                if ENABLE_DEBUG_ENTER: quit(7)

        self.jsonParserFolder = os.path.join(self.outDir, 'json')
        if not os.path.exists(self.jsonParserFolder):
            try:
                os.makedirs(self.jsonParserFolder)
            except OSError:
                print("Failed to create the json parser folder")
                if ENABLE_DEBUG_ENTER: quit(7)

        self.cFormatHeaderFolder = os.path.join(self.outDir, 'include')
        if not os.path.exists(self.cFormatHeaderFolder):
            try:
                os.makedirs(self.cFormatHeaderFolder)
            except OSError:
                print("Failed to create the C-format header folder")
                if ENABLE_DEBUG_ENTER: quit(7)

        self.maxStructDepth = 0

    #########################################################################################
    #########################################################################################
    # The following member methods are related to the generation of Python C-type Version 2 #
    #########################################################################################
    #########################################################################################

    def __runCmd(self, multicmd, timeout=100):
        """Performs an execution of GHS program."""
        proc = Popen(multicmd, stdout=PIPE, stderr=PIPE, shell=True)
        timer = Timer(timeout, proc.kill)
        try:
            timer.start()
            stdout, stderr = proc.communicate()
        finally:
            timer.cancel()

    def __executeSystemCommand(self, command):
        """Performs an execution for the GHS script."""
        try:
            if platform.system() == 'Linux':
                # Just in case we need to do something different for Linux
                self.__runCmd(command)
            elif platform.system() == 'Windows':
                # Just in case we need to do something different for Windows
                self.__runCmd(command)
        except:
            print("Failed Multi execution")
            return False
        return True

    def __deleteTempFiles(self):
        """Performs delete of temp files used in parsing."""
        if os.path.exists(self.dbgDumpFile): os.remove(self.dbgDumpFile)

    def __doDebugDataDump(self):
        """Dump debug information from GHS .dla file."""
        gdumpExe = None
        if self.options.ghsCompilerVersion is not None:
            gdumpExe = os.path.abspath(os.path.join(self.ghsPath, self.options.ghsCompilerVersion, "gdump.exe"))
            if not os.path.exists(gdumpExe):
                print("\n-E- Could not locate gdump.exe")
                return False
        else:
            print("\n-E- No ghs compiler specified to locate gdump.exe")
            return False

        dbgFile = os.path.abspath(os.path.join(self.options.fwBuildOutputDir, '%s.dla' % (self.options.projectName)))
        if not os.path.exists(dbgFile):
            print("-E- Could not locate elf file (%s)" % (dbgFile))
            return False

        command = '%s %s > %s' % (gdumpExe, dbgFile, self.dbgDumpFile)
        return self.__executeSystemCommand(command)

    def __doDebugDataDumpOlder(self):
        """Dump debug information"""
        autoParserAnalyzerExe = None
        for p in sys.path:
            autoParserAnalyzerExe = os.path.join(p, "autoParserAnalyzer.exe")
            if os.path.exists(autoParserAnalyzerExe): 
                break
            
        if autoParserAnalyzerExe is None or not os.path.exists(autoParserAnalyzerExe):
            print("autoParserAnalyzer.exe is not in sys.path!")
            return False

        command = '%s -ghsdir %s -compiler %s -projectname %s -fwbuilddir %s' %\
                  (autoParserAnalyzerExe, self.ghsPath, self.options.ghsCompilerVersion, self.options.projectName, os.path.abspath(self.options.fwBuildOutputDir))
        return self.__executeSystemCommand(command)

    def __getBuildDbgData(self, typedef):
        idx = -1        # So the first line in the dbg dump file is idx = 0
        dbgDataLines = []
        foundSymbolSubsection = True
        symTypedefRow = None
        symTypedefRefRow = None
        symTypedefStartIdx = None
        symTypedefEndIdx = None

        foundTypedef = False
        continueToIdx = 0
        with open(self.dbgDumpFile, 'r') as iFile:
            for l in iFile:
                line = l.strip()
                idx += 1

                # Recording each line in the Symbol subsection of the dbg dump
                if "Symbols" == line:
                    # Found a new Symbols subsection.  Reset dbgDataLines.
                    dbgDataLines = [line]
                    foundSymbolSubsection = True
                    continue
                elif foundSymbolSubsection:
                    dbgDataLines.append(line)
                else: continue

                # 1351:"bootProfileStructure_DRAM_t" -> "bootProfileStructure_DRAM_VER_1_t"
                if re.match('^(\d+):\"%s\" -> \"(.+)\"' % typedef, line):
                    m = re.match('^(\d+):\"%s\" -> \"(.+)\"' % typedef, line)
                    typedef = m.group(2)
                    continue

                if (not foundTypedef) and ("\"" + typedef + "\"" in line) and ("-Begin" in line):
                    # 4044:    "_coreStats_t" val:2552 ind:(4284,-1) Struct-Begin  Info
                    if re.match('^(\d+): +\"(.*)\" +val:(-?\d+) +ind:\((.+),(.+)\) +(\w+)-Begin +Info', line):
                        m = re.match('^(\d+): +\"(.*)\" +val:(-?\d+) +ind:\((.+),(.+)\) +(\w+)-Begin +Info', line)

                        foundTypedef = True
                        symTypedefRow = int(m.group(1))                                             # Row number where Struct-Begin in ORIGINAL DEBUG DATA FILE
                        symTypedefRefRow = int(m.group(4))                                          # Row number one line beyond Struct-End in ORIGINAL DEBUG DATA FILE
                        symTypedefStartIdx = len(dbgDataLines) - 1                                  # 0-based line number where Struct-Begin in TYPEDEF DEBUG DATA FILE
                        symTypedefEndIdx = symTypedefStartIdx + (int(m.group(4))-int(m.group(1)))   # 0-based line number one line beyond where Struct-End is in TYPEDEF DEBUG DATA FILE
                        continueToIdx = idx + (symTypedefEndIdx - symTypedefStartIdx)

                # 222:     "NandWork_t" Typedef  Info C Struct ref = 1607
                elif (not foundTypedef) and ("\"" + typedef+ "\"" in line) and ("ref " in line):
                    if re.search('^(\d+): +\"(.+)\".+Info (.+) ref = (\d+)', line):
                        m = re.search('^(\d+): +\"(.+)\".+Info (.+) ref = (\d+)', line)

                        foundTypedef = True
                        if int(m.group(4)) <= int(m.group(1)):
                            symTypedefRow = int(m.group(1))                                             # Row number in the ORIGINAL DEBUG DATA FILE referencing to Struct-Begin
                            symTypedefRefRow = int(m.group(4))                                          # Row number where Struct-Begin in the ORIGINAL DEBUG DATA FILE
                            symTypedefStartIdx = (len(dbgDataLines) - 1) - (symTypedefRow - symTypedefRefRow)   # 0-base start line index in TYPEDEF DEBUG DATA FILE referencing to Struct-Begin
                            symTypedefEndIdx = len(dbgDataLines) - 1                                    # 0-base end line index in TYPEDEF DEBUG DATA FILE referencing to one line beyond Struct-End
                            continueToIdx = idx

                        # 222:     "NandWork_t" Typedef  Info C Struct ref = 1607
                        else:
                            symTypedefRow = int(m.group(4))  # Row number where Struct-Begin in ORIGINAL DEBUG DATA FILE
                            symTypedefStartIdx = idx + int(m.group(4)) - int(m.group(1))    # 0-based line number where Struct-Begin in TYPEDEF DEBUG DATA FILE
                            continueToIdx = idx + (int(m.group(4)) - int(m.group(1))) + 1   # Specify to Struct-Begin line for now.

                if idx == symTypedefStartIdx:
                    if re.match('^(\d+): +\"(.*)\" +val:(-?\d+) +ind:\((.+),(.+)\) +(\w+)-Begin +Info', line):
                        m = re.match('^(\d+): +\"(.*)\" +val:(-?\d+) +ind:\((.+),(.+)\) +(\w+)-Begin +Info', line)

                        symTypedefRefRow = int(m.group(4))                                      # Row number one line beyond Struct-End in ORIGINAL DEBUG DATA FILE
                        symTypedefStartIdx = len(dbgDataLines) - 1                              # 0-based line number where Struct-Begin in TYPEDEF DEBUG DATA FILE
                        symTypedefEndIdx = len(dbgDataLines) - 1 + (int(m.group(4)) - int(m.group(1)))  # 0-based line number one line beyond where Struct-End is in TYPEDEF DEBUG DATA FILE
                        continueToIdx = continueToIdx + (int(m.group(4)) - int(m.group(1))) + 1000     # Tagging on more lines to Struct-End line + 1

                # Continue to get the rest of data lines if needed
                if foundTypedef and idx >= continueToIdx: break

        return dbgDataLines, symTypedefRow, symTypedefRefRow, symTypedefStartIdx, symTypedefEndIdx

    def getPackValue(self, typedef):
        for t in self.AUTOPARSER_DATA_OBJECT_LIST:
            if typedef == t[1]: return t[4]
        return None

    def __buildCtypeParser(self, obj, dbgData):

        # debugPrintEnabled = True # Debug print enabled
        debugPrintEnabled = False # Debug print enabled

        dprint("", enable=debugPrintEnabled)
        dprint("uid=%s, instance=%s, typedef=%s" % (str(obj.uid), str(obj.instance), str(obj.typedef)), indent=obj.depth*20, enable=debugPrintEnabled)
        dprint("startIdx=%s, endIdx=%s" % (str(obj.startIdx), str(obj.endIdx)), indent=obj.depth*20, enable=debugPrintEnabled)

        idx = obj.startIdx
        while idx < len(dbgData):
            line = dbgData[idx]

            # if 'Pointer' in line: debugPrintEnabled = True
            # if 'bisDieInfo_t' in line: debugPrintEnabled = True
            dprint('\n'+line, 0, enable=debugPrintEnabled)

            # Matching Case 0.0: >>>983:     "Bis_t" Typedef  Info C++ Struct ref = 958
            if re.match('^(\d+):.+', line):
                m = re.match('^(\d+):.+', line)
                fileIdx = getDataIdx(dbgData, int(m.group(1)))
                if obj.endIdx is not None and fileIdx is not None and fileIdx == obj.endIdx:
                    pressReturnToContinue('POST-Matching Case 0.0: Struct ending', obj.depth*4, enable=debugPrintEnabled)
                    return obj

            # Matching Case 1.0:
            # 2:       "__C2"           val:4   ind:(5,-1)      Struct-Begin    Info
            # 34:      "_iobuf"         val:16  ind:(50,-1)     Struct-Begin    Info
            # 958:     "Bis_t"          val:2048 ind:(983,-1)   Struct-Begin    Info
            # 61:      "pmicIdRegs_t"   val:4   ind:(83,-1)     Struct-Begin    Info
            # 34:      ""               val:4   ind:(38,-1)     Struct-Begin    Info
            #
            # 53:      "pmicDevice_e"   val:4   ind:(60,-1)     Enum-Begin      Info
            # 2003:    "UECType"        val:4   ind:(2495,-1)   Enum-Begin      Info
            # 103:     "sxpErrorType_e" val:4   ind:(112,-1)    Enum-Begin      Info
            # 11:      ""               val:4   ind:(20,-1)     Enum-Begin      Info
            #
            # 131:     "__C4"           val:2   ind:(141,-1)    Union-Begin     Info
            # 1707:    ""               val:8   ind:(1711,-1)   Union-Begin     Info
            if idx == obj.startIdx and re.match('^(\d+): +\"(.*)\" +val:(-?\d+) +ind:\((.+),(.+)\) +(\w+)-Begin', line):
                m = re.match('^(\d+): +\"(.*)\" +val:(-?\d+) +ind:\((.+),(.+)\) +(\w+)-Begin', line)

                if obj.typedef is None: obj.typedef = m.group(2)
                if obj.dataType is None: obj.dataType = m.group(6).lower()

                if (obj.size is None or obj.size == 0) and (obj.width is None) and (int(m.group(3)) > 0):
                    obj.size = int(m.group(3))*8
                    # obj.width = obj.size

                obj.endIdx = getDataIdx(dbgData, int(m.group(4)))

                # Attempt to find object.typedef if it has not been determined yet.
                if obj.typedef is None or obj.typedef == "":
                    if re.match('^(\d+): +\"(.*)\" +Typedef +Info +(.+) +(Struct|Union|Enum|Typedef) +ref += +(\d+)$', dbgData[obj.endIdx]):
                        mm = re.match('^(\d+): +\"(.*)\" +Typedef +Info +(.+) +(Struct|Union|Enum|Typedef) +ref += +(\d+)$', dbgData[obj.endIdx])
                        if int(mm.group(5)) == int(m.group(1)) and int(mm.group(1)) == int(m.group(4)):
                            obj.typedef = mm.group(2)

                obj.pprint(enable=debugPrintEnabled, all=True)
                pressReturnToContinue('POST-Matching Case 1.0: %s-Begin' % m.group(6), obj.depth*4, enable=debugPrintEnabled)

            # Matching Case 1.1:
            # 66:  ("pmicIdRegs_t::[unnamed type (instance 1)]",                              "__Q2_12pmicIdRegs_t5__Ut1")            val:1 ind:(74,-1)   Union-Begin     Info
            # 69:  ("pmicIdRegs_t::[unnamed type (instance 1)]::[unnamed type (instance 1)]", "__Q3_12pmicIdRegs_t5__Ut15__Ut1")      val:1 ind:(73,-1)   Struct-Begin    Info
            # 74:  ("pmicIdRegs_t::[unnamed type (instance 2)]",                              "__Q2_12pmicIdRegs_t5__Ut2")            val:1 ind:(82,-1)   Union-Begin     Info
            # 77:  ("pmicIdRegs_t::[unnamed type (instance 2)]::[unnamed type (instance 1)]", "__Q3_12pmicIdRegs_t5__Ut25__Ut1")      val:1 ind:(81,-1)   Struct-Begin    Info
            # 134: ("vdmInfo_t::__C4::[unnamed type (instance 1)]",                           "__Q3_9vdmInfo_t4__C45__Ut1")           val:2 ind:(140,-1)  Struct-Begin    Info
            # 144: ("vdmInfo_t::__C5::[unnamed type (instance 1)]",                           "__Q3_9vdmInfo_t4__C55__Ut1")           val:2 ind:(150,-1)  Struct-Begin    Info
            # 168: ("shortStrokeEntry_t::__C6::[unnamed type (instance 1)]",                  "__Q3_18shortStrokeEntry_t4__C65__Ut1") val:4 ind:(181,-1)  Struct-Begin    Info
            # 871: ("platformInfo_t::__C8::[unnamed type (instance 1)]",                      "__Q3_14platformInfo_t4__C85__Ut1")     val:4 ind:(883,-1)  Struct-Begin    Info
            # 913: ("mediaInfo_t::__C9::[unnamed type (instance 1)]",                         "__Q3_11mediaInfo_t4__C95__Ut1")        val:2 ind:(922,-1)  Struct-Begin    Info
            # 944: ("transportInfo_t::__C10::[unnamed type (instance 1)]",                    "__Q3_15transportInfo_t5__C105__Ut1")   val:2 ind:(955,-1)  Struct-Begin    Info
            # 973: ("Bis_t::__C11::[unnamed type (instance 1)]",                              "__Q3_5Bis_t5__C115__Ut1")              val:4 ind:(981,-1)  Struct-Begin    Info
            elif re.match('^(\d+): +\(\"(.*)\",\"(.+)\"\) +val:(-?\d+) +ind:\((.+),(.+)\) +(\w+)-Begin', line):
                m = re.match('^(\d+): +\(\"(.*)\",\"(.+)\"\) +val:(-?\d+) +ind:\((.+),(.+)\) +(\w+)-Begin', line)

                startIdx = getDataIdx(dbgData, int(m.group(1)))
                instance = getTypedefNames(m.group(3))
                typedef = "__" + getTypedefNames(m.group(3))

                size = int(m.group(4)) * 8
                endIdx = getDataIdx(dbgData, int(m.group(5)))
                dataType = m.group(7).lower()

                if obj.instance is None or obj.instance == "":  obj.instance = instance
                if obj.typedef is None: obj.typedef = typedef
                if (obj.size is None or obj.size == 0) and (obj.width is None) and (size > 0):
                    obj.size = size
                    # obj.width = obj.size
                obj.dataType = dataType
                obj.endIdx = endIdx
                obj.anon = True
                obj.pprint(enable=debugPrintEnabled, all=True)
                pressReturnToContinue('POST-Matching Case 1.1: Anonymous %s' % m.group(7), obj.depth*4, enable=debugPrintEnabled)

            # Matching Case 2.0:
            # 1235:        "vdmRecoveryLevelSlivers" offset 128,  Member  Info Array of Array of Array of C Typedef ref = 6 [0..3] [0..9] [0..12]
            # 1243:        "vdmRecoveryLevelMeta" offset 128,     Member  Info Array of Array of Array of C Typedef ref = 6 [0..3] [0..9] [0..12]
            elif re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +Info +(Array of Array of Array of.+) +Typedef +ref += +(\d+) +\[(\d+)\.\.(\d+)\] +\[(\d+)\.\.(\d+)\] \[(\d+)\.\.(\d+)\]', line):
                m = re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +Info +(Array of Array of Array of.+) +Typedef +ref += +(\d+) +\[(\d+)\.\.(\d+)\] +\[(\d+)\.\.(\d+)\] \[(\d+)\.\.(\d+)\]', line)
                uid = obj.uid
                instance = m.group(2)
                dataType = 'typedef'
                info = m.group(4)
                offset = int(m.group(3))
                depth = obj.depth + 1
                startIdx = getDataIdx(dbgData, int(m.group(5)))
                endIdx = getDataIdx(dbgData, int(m.group(1)))
                if m.group(2) == "":
                    anon = True
                else: anon = False
                arrayLen = [int(m.group(7))+1, int(m.group(9))+1, int(m.group(11))+1]
                enum = False
                dprint('PRE-Matching Case 2.0: Array of Array of Array of Member Typedef with offset and reference', enable=debugPrintEnabled)

                myObj = DataTypeObject(uid=uid, instance=instance, dataType=dataType, info=info, offset=offset, depth=depth,
                                       startIdx=startIdx, endIdx=endIdx, anon=anon, arrayLen=arrayLen, enum=enum, pack=obj.pack)
                obj.memberList.append(self.__buildCtypeParser(myObj, dbgData))
                obj.pprint(enable=debugPrintEnabled, all=True)
                pressReturnToContinue('POST-Matching Case 2.0: Array of Array of Array of Member Typedef with offset and reference', obj.depth*4, enable=debugPrintEnabled)

            # Matching Case 2.1:
            # 893:         "dieInfo" offset 96,                   Member  Info Array of Array of C++ Typedef ref = 854 [0..9] [0..12]
            # 3163:        "dieInfo" offset 96,                   Member  Info Array of Array of C Typedef ref = 3111 [0..9] [0..12]
            elif re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +Info +(Array of Array of.+) +Typedef +ref += +(\d+) +\[(\d+)\.\.(\d+)\] +\[(\d+)\.\.(\d+)\]', line):
                m = re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +Info +(Array of Array of.+) +Typedef +ref += +(\d+) +\[(\d+)\.\.(\d+)\] +\[(\d+)\.\.(\d+)\]', line)
                uid = obj.uid
                instance = m.group(2)
                dataType = 'typedef'
                info = m.group(4)
                offset = int(m.group(3))
                depth = obj.depth + 1
                startIdx = getDataIdx(dbgData, int(m.group(5)))
                endIdx = getDataIdx(dbgData, int(m.group(1)))
                if m.group(2) == "":
                    anon = True
                else: anon = False
                arrayLen = [int(m.group(7))+1, int(m.group(9))+1]
                enum = False
                dprint('PRE-Matching Case 2.1: Array of Array of Member Typedef with offset and reference', enable=debugPrintEnabled)

                myObj = DataTypeObject(uid=uid, instance=instance, dataType=dataType, info=info, offset=offset, depth=depth,
                                       startIdx=startIdx, endIdx=endIdx, anon=anon, arrayLen=arrayLen, enum=enum, pack=obj.pack)
                dprint('PRE-Matching Case 2.1: Array of Array of Member Typedef with offset and reference', enable=debugPrintEnabled)
                obj.memberList.append(self.__buildCtypeParser(myObj, dbgData))
                obj.pprint(enable=debugPrintEnabled, all=True)
                pressReturnToContinue('POST-Matching Case 2.1: Array of Array of Member Typedef with offset and reference', obj.depth*4, enable=debugPrintEnabled)

            # Matching Case 2.2:
            # 962:         "blRev" offset 96,                     Member  Info Array of C++ Typedef ref = 8 [0..3]
            # 1917:        "Fat" offset 32,                       Member  Info Array of C Typedef ref = 1912 [0..99]
            elif re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +Info +(Array of.+) +Typedef +ref += +(\d+) +\[(\d+)\.\.(\d+)\]', line):
                m = re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +Info +(Array of.+) +Typedef +ref += +(\d+) +\[(\d+)\.\.(\d+)\]', line)
                uid = obj.uid
                uid = obj.uid
                instance = m.group(2)
                dataType = 'typedef'
                info = m.group(4)
                offset = int(m.group(3))
                depth = obj.depth + 1
                startIdx = getDataIdx(dbgData, int(m.group(5)))
                endIdx = getDataIdx(dbgData, int(m.group(1)))
                if m.group(2) == "":
                    anon = True
                else: anon = False
                arrayLen = [int(m.group(7))+1]
                enum = False

                myObj = DataTypeObject(uid=uid, instance=instance, dataType=dataType, info=info, offset=offset, depth=depth,
                                       startIdx=startIdx, endIdx=endIdx, anon=anon, arrayLen=arrayLen, enum=enum, pack=obj.pack)
                dprint('PRE-Matching Case 2.2: Array of Member Typedef with offset and reference', enable=debugPrintEnabled)

                obj.memberList.append(self.__buildCtypeParser(myObj, dbgData))
                obj.pprint(enable=debugPrintEnabled, all=True)
                pressReturnToContinue('POST-Matching Case 2.2: Array of Member Typedef with offset and reference', obj.depth*4, enable=debugPrintEnabled)

            # Matching Case 3.0:
            # 1519: "data" offset 0, Member  Info Pointer to C Typedef ref = 1
            # 5112: "pSupCmd" offset 96, Member  Info Pointer to const C Typedef ref = 2
            # 5408: "GetInternalReadQDepth" offset 0, Member  Info Pointer to Prototype returning C Typedef ref = 5
            # 5416: "GetDmaDesc" offset 256, Member  Info Pointer to Prototype returning Pointer to C Typedef ref = 3101
            # 124:  "getCurrentFormat" offset 256, Member  Info Pointer to Prototype returning C Typedef ref = 114
            # 125:  "getBand" offset 288, Member  Info Pointer to Prototype returning C Typedef ref = 4
            elif re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +Info +(Pointer.+) +ref += +(\d+)', line):
                m = re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +Info +(Pointer.+) +ref += +(\d+)', line)
                dprint(line, 0, enable=debugPrintEnabled)
                uid = obj.uid
                instance = m.group(2)
                typedef = 'uint32_t'
                dataType = 'pointer'
                offset = int(m.group(3))
                info = m.group(4)
                depth = obj.depth + 1
                startIdx = getDataIdx(dbgData, int(m.group(1)))
                endIdx = getDataIdx(dbgData, int(m.group(1)))
                if m.group(2) == "": anon = True
                else: anon = False
                arrayLen = [1]
                enum = False
                dprint('PRE-Matching Case 3.0: Pointer to Typedef with offset and reference', obj.depth*4, enable=debugPrintEnabled)

                myObj = DataTypeObject(uid=uid, instance=instance, typedef=typedef, dataType=dataType, info=info, offset=offset, depth=depth,
                                       startIdx=startIdx, endIdx=endIdx, anon=anon, arrayLen=arrayLen, enum=enum, pack=obj.pack)
                obj.memberList.append(myObj)
                obj.pprint(enable=debugPrintEnabled, all=True)
                pressReturnToContinue('POST-Matching Case 3.0: Pointer to Typedef with offset and reference', obj.depth*4, enable=debugPrintEnabled)

            # Matching Case 3.1:
            # 2315:        "chain" offset 448, Member  Info Array of C Struct ref = 2293 [0..1]
            elif re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +Info +(Array of.+) +(Typedef|Union|Struct) +ref += +(\d+) +\[(\d+)\.\.(\d+)\]', line):
                m = re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +Info +(Array of.+) +(Typedef|Union|Struct) +ref += +(\d+) +\[(\d+)\.\.(\d+)\]', line)
                uid = obj.uid
                instance = m.group(2)
                dataType = m.group(5).lower()
                info = m.group(4)
                offset = int(m.group(3))
                depth = obj.depth + 1
                startIdx = getDataIdx(dbgData, int(m.group(6)))
                endIdx = getDataIdx(dbgData, int(m.group(1)))
                if m.group(2) == "": anon = True
                else: anon = False
                arrayLen = [int(m.group(8))+1]
                enum = False
                dprint('PRE-Matching Case 3.1: Array member of Typedef/Struct/Union with offset and reference', obj.depth*4, enable=debugPrintEnabled)

                myObj = DataTypeObject(uid=uid, instance=instance, dataType=dataType, info=info, offset=offset, depth=depth,
                                       startIdx=startIdx, endIdx=endIdx, anon=anon, arrayLen=arrayLen, enum=enum, pack=obj.pack)

                obj.memberList.append(self.__buildCtypeParser(myObj, dbgData))
                obj.pprint(enable=debugPrintEnabled, all=True)
                pressReturnToContinue('POST-Matching Case 3.1: Array member of Typedef/Struct/Union with offset and reference', obj.depth*4, enable=debugPrintEnabled)

            # Matching Case 3.2: ----------------------------------------------------------
            # 35:          "major" offset 0, Member  Info C Typedef ref = 4
            # -----------------------------------------------------------------------------
            # 959:     "idToken" offset 0, Member  Info C++ Typedef ref = 10
            # 5400:        "adminCmd" offset 0, Member  Info const C Typedef ref = 3519
            # 1909:        "flags" offset 0, Member  Info C Struct ref = 1900
            # 67:              "" offset 0, Member  Info C++ Struct ref = 69
            # -----------------------------------------------------------------------------
            # 64:          "revisionNumber" offset 16, Member  Info C++ Union ref = 66
            # 2095:        "" offset 4800, Member  Info C Union ref = 2022
            # 2956:        "sku" offset 1376, Member  Info C Union ref = 2903
            # 964:         "" offset 192, Member  Info C++ Union ref = 970
            # -----------------------------------------------------------------------------
            # 1409:    "pPolicies" offset 32, Member  Info Pointer to C Typedef ref = 1406
            # 1998:    "pTestSpan" offset 416, Member  Info Pointer to const C Typedef ref = 1963
            # 5371:        "vuAsyncRequest" offset 32, Member  Info Pointer to C Struct ref = 5591
            # 3402:        "pContext" offset 64, Member  Info Pointer to C Union ref = 2724
            # -----------------------------------------------------------------------------
            elif re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +Info +(.+) +(Typedef|Union|Struct) +ref += +(\d+)', line):
                m = re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +Info +(.+) +(Typedef|Union|Struct) +ref += +(\d+)', line)
                uid = obj.uid
                instance = m.group(2)
                dataType = m.group(5).lower()
                info = m.group(4)
                offset = int(m.group(3))
                depth = obj.depth + 1
                startIdx = getDataIdx(dbgData, int(m.group(6)))
                endIdx = getDataIdx(dbgData, int(m.group(1)))
                if m.group(2) == "": anon = True
                else: anon = False
                arrayLen = [1]
                enum = False
                dprint('PRE-Matching Case 3.2: Member Typedef/Struct/Union with offset and reference', obj.depth*4, enable=debugPrintEnabled)

                myObj = DataTypeObject(uid=uid, instance=instance, dataType=dataType, info=info, offset=offset, depth=depth,
                                       startIdx=startIdx, endIdx=endIdx, anon=anon, arrayLen=arrayLen, enum=enum, pack=obj.pack)
                obj.memberList.append(self.__buildCtypeParser(myObj, dbgData))
                obj.pprint(enable=debugPrintEnabled, all=True)
                pressReturnToContinue('POST-Matching Case 3.2: Member Typedef/Struct/Union with offset and reference', obj.depth*4, enable=debugPrintEnabled)

            # Matching Case 3.3:
            # 116:  "setLma" offset 0, Member  Info Pointer to Prototype returning C Void
            # 117:  "trimLma" offset 32, Member  Info Pointer to Prototype returning C Void
            # 118:  "getLma" offset 64, Member  Info Pointer to Prototype returning C Void
            # 119:  "isExceptionBitSet" offset 96, Member  Info Pointer to Prototype returning C Logical*1
            # 120:  "isExceptionBitSetUser" offset 128, Member  Info Pointer to Prototype returning C Logical*1
            # 121:  "setExceptionBit" offset 160, Member  Info Pointer to Prototype returning C Void
            # 122:  "setExceptionBitUser" offset 192, Member  Info Pointer to Prototype returning C Void
            # 123:  "resetExceptionBit" offset 224, Member  Info Pointer to Prototype returning C Void
            # 126:  "preloadIntoCacheLine" offset 320, Member  Info Pointer to Prototype returning C Void
            elif re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +Info +(Pointer to Prototype +returning.+)(Void|Logical\*\d)$', line):
                m = re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +Info +(Pointer to Prototype +returning.+)(Void|Logical\*\d)$', line)
                dprint(line, 0, enable=debugPrintEnabled)
                uid = obj.uid
                instance = m.group(2)
                typedef = 'uint32_t'
                dataType = 'pointer'
                offset = int(m.group(3))
                info = m.group(4)
                depth = obj.depth + 1
                startIdx = getDataIdx(dbgData, int(m.group(1)))
                endIdx = getDataIdx(dbgData, int(m.group(1)))
                if m.group(2) == "": anon = True
                else: anon = False
                arrayLen = [1]
                enum = False
                dprint('PRE-Matching Case 3.3: Pointer to Prototype with offset and no reference', obj.depth*4, enable=debugPrintEnabled)

                myObj = DataTypeObject(uid=uid, instance=instance, typedef=typedef, dataType=dataType, info=info, offset=offset, depth=depth,
                                       startIdx=startIdx, endIdx=endIdx, anon=anon, arrayLen=arrayLen, enum=enum, pack=obj.pack)

                obj.memberList.append(myObj)
                obj.pprint(enable=debugPrintEnabled, all=True)
                pressReturnToContinue('POST-Matching Case 3.3: Pointer to Prototype with offset and no reference', obj.depth*4, enable=debugPrintEnabled)

            # Matching Case 4.0:
            # 54:          "PMIC_DEVICE_INVALID" enumval 0, EnumVal  Info
            # 89:          "BL_ERR_NO_ERROR" enumval 0, EnumVal  Info
            elif re.match('^(\d+): +\"(.*)\" +enumval +([\-\d]+), +EnumVal  Info', line):
                m = re.match('^(\d+): +\"(.*)\" +enumval +([\-\d]+), +EnumVal  Info', line)
                uid = obj.uid
                instance = m.group(2)
                typedef = int(m.group(3))
                pack = self.getPackValue(typedef)
                if pack is None: pack = obj.pack
                dataType = 'enumval'
                info = 'EnumVal'
                depth = obj.depth + 1
                startIdx = getDataIdx(dbgData, int(m.group(1)))
                endIdx = getDataIdx(dbgData, int(m.group(1)))
                if m.group(2) == "":
                    anon = True
                else: anon = False
                arrayLen = [1]
                enum = True
                dprint('Matching Case  4.0: Enumval endpoint', obj.depth*4, enable=debugPrintEnabled)

                myObj = DataTypeObject(uid=uid, instance=instance, typedef=typedef, dataType=dataType, info=info, depth=depth,
                                   startIdx=startIdx, endIdx=endIdx, anon=anon, arrayLen=arrayLen, enum=enum, pack=pack)
                obj.memberList.append(myObj)
                obj.enum = True
                obj.pprint(enable=debugPrintEnabled, all=True)
                pressReturnToContinue('Matching Case  4.0: Enumval endpoint', obj.depth*4, enable=debugPrintEnabled)

            # Matching Case 5.0:
            # 1428:        "valid"              offset 64,  Member  BitField C Subrange UShort:[0..1] width = 1
            # 974:         "prohibitAes"        offset 0,   Member  BitField C++ Subrange UInt:[0..1] width = 1
            # 1726:        "cycleCount"         offset 32,  Member  BitField C Subrange UInt:[0..16777215] width = 24
            # 2176:        "currentCaseTemp"    offset 0,   Member  BitField C Subrange LongLong:[-128..127] width = 8
            # 3024:        "mfgDataNotLoaded"   offset 5,   Member  BitField C Subrange Logical*1:[0..1] width = 1
            # 2835:        "discoveryNotDone"   offset 0,   Member  BitField C Subrange Logical*1:[0..1] width = 1
            elif re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +BitField +(.+) +Subrange ([\w\*]+):\[([\-\d]+)\.\.([\-\d]+)\] +width = (\d+)', line):
                m = re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +BitField +(.+) +Subrange ([\w\*]+):\[([\-\d]+)\.\.([\-\d]+)\] +width = (\d+)', line)
                uid = obj.uid
                instance = m.group(2)
                typedef = m.group(5)
                pack = self.getPackValue(typedef)
                if pack is None: pack = obj.pack
                dataType = 'bitfield'
                offset = int(m.group(3))
                info = 'Member Bitfield %s' % m.group(4)
                depth = obj.depth + 1
                startIdx = getDataIdx(dbgData, int(m.group(1)))
                endIdx = getDataIdx(dbgData, int(m.group(1)))
                if m.group(2) == "":
                    anon = True
                else: anon = False
                arrayLen = [1]
                enum = False
                bitfield = True
                width = int(m.group(8))
                dprint('Matching Case 5.0: BitField Subrange with offset and width\n', enable=debugPrintEnabled)

                myObj = DataTypeObject(uid=uid, instance=instance, typedef=typedef, dataType=dataType, info=info, offset=offset, depth=depth,
                                       startIdx=startIdx, endIdx=endIdx, anon=anon, arrayLen=arrayLen, enum=enum, bitfield=bitfield, width=width, pack=pack)
                obj.memberList.append(myObj)
                obj.pprint(enable=debugPrintEnabled, all=True)
                pressReturnToContinue('Matching Case 5.0: BitField Subrange with offset and width', obj.depth*4, enable=debugPrintEnabled)

            # Matching Case 5.1:
            # 965:         "prohibitAes" offset 0, Member  BitField C++ Typedef ref = 10 width = 1
            # 908:         "staggeredSpinupEnable" offset 4, Member  BitField C++ Subrange Typedef ref = 8:[0..1] width = 1
            # 849:         "sxpError" offset 8, Member  BitField C++ Enum ref = 103 width = 4
            # 3106:        "sxpError" offset 8, Member  BitField C Enum ref = 2988 width = 4
            # 840:         "mediaTrainError" offset 0, Member  BitField C++ Typedef ref = 565 width = 7
            # 867:         "reserved" offset 42, Member  BitField C Typedef ref = 9 width = 22
            elif re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +BitField +(.+) +(Enum|Typedef) +ref = +(\d+).+width += +(\d+)', line):
                m = re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +BitField +(.+) +(Enum|Typedef) +ref = +(\d+).+width += +(\d+)', line)
                uid = obj.uid
                instance = m.group(2)
                if 'Enum' in m.group(5):
                    dataType = 'enum'
                    enum = True
                else:
                    dataType = 'bitfield'
                    enum = False
                offset = int(m.group(3))
                info = 'Member Bitfield %s' % m.group(4)
                depth = obj.depth + 1
                startIdx = getDataIdx(dbgData, int(m.group(6)))
                endIdx = getDataIdx(dbgData, int(m.group(1)))
                if m.group(2) == "":
                    anon = True
                else: anon = False
                arrayLen = [1]
                bitfield = True
                width = int(m.group(7))
                dprint('PRE-Matching Case 5.1: BitField Enum|Typedef with offset, reference, and width', enable=debugPrintEnabled)

                myObj = DataTypeObject(uid=uid, instance=instance, dataType=dataType, info=info, offset=offset, depth=depth,
                                       startIdx=startIdx, endIdx=endIdx, anon=anon, arrayLen=arrayLen, enum=enum, bitfield=bitfield, width=width, pack=obj.pack)
                obj.memberList.append(self.__buildCtypeParser(myObj, dbgData))
                obj.pprint(enable=debugPrintEnabled, all=True)
                pressReturnToContinue('POST-Matching Case 5.1: BitField Enum|Typedef with offset, reference, and width', 8, enable=debugPrintEnabled)

            # Matching Case #6.0:
            # 635:     "testCmdVersion_t" Typedef  Info C++ Struct ref = 631
            # 38:      "testCmdVersion_t" Typedef  Info C Struct ref = 34
            # 1711:    "slowCtxChunkAddr_t" Typedef  Info C Union ref = 1707
            # 565:     "mediaTrainError_e" Typedef  Info C++ Enum ref = 529
            # 60:      "pmicDevice_e" Typedef  Info C++ Enum ref = 53
            # 9427:    "NWB_State_e" Typedef  Info C Enum ref = 9420
            # 10:      "bool32_t" Typedef  Info C Typedef ref = 6
            # 932:     "internalReadFunc" Typedef  Info Pointer to Prototype returning C Typedef ref = 6
            # 9:       "bool32_t" Typedef  Info C Typedef ref = 5
            # 8615:    "dieProgramSuspendPolicyState_e" Typedef  Info C Enum1 ref = 8600
            elif re.match('^(\d+): +\"(.*)\" +Typedef +Info +(.+) +(Struct|Union|Enum|Typedef)(\d+)? +ref += +(\d+)$', line):
                m = re.match('^(\d+): +\"(.*)\" +Typedef +Info +(.+) +(Struct|Union|Enum|Typedef)(\d+)? +ref += +(\d+)$', line)
                typedef = m.group(2)
                pack = self.getPackValue(typedef)
                if pack is None: pack = obj.pack
                dataType = m.group(4).lower()
                offset = obj.offset
                info = m.group(3)
                startIdx = getDataIdx(dbgData, int(m.group(6)))
                endIdx = getDataIdx(dbgData, int(m.group(1)))
                if m.group(2) == "": anon = True
                else: anon = False
                arrayLen = obj.arrayLen
                enum = obj.enum
                bitfield = obj.bitfield
                width = obj.width
                dprint('PRE-Matching Case  6.0: Intermediate Struct ref\n', enable=debugPrintEnabled)

                myObj = DataTypeObject(uid=obj.uid, instance=obj.instance, typedef=typedef, dataType=dataType, offset=offset, info=info, width=width,
                                       depth=obj.depth, startIdx=startIdx, endIdx=endIdx, anon=anon, arrayLen=arrayLen, enum=enum, bitfield=bitfield, pack=pack)
                obj = self.__buildCtypeParser(myObj, dbgData)
                obj.pprint(enable=debugPrintEnabled, all=True)
                pressReturnToContinue('Matching Case  6.0: Intermediate Struct ref', obj.depth*4, enable=debugPrintEnabled)
                return obj

            # Matching Case 6.1:
            # 556:     "interruptHandler_t" Typedef  Info Pointer to Prototype returning C Void
            # 3485:    "pBoolFctUintUint" Typedef  Info Pointer to Prototype returning C Logical*1
            elif re.match('^(\d+): +\"(.*)\" +Typedef +Info +(Pointer to Prototype) +returning.+(Void|Logical\*\d)$', line):
                m = re.match('^(\d+): +\"(.*)\" +Typedef +Info +(Pointer to Prototype) +returning.+(Void|Logical\*\d)$', line)
                typedef = 'uint32_t'
                dataType = 'pointer'
                offset = obj.offset
                info = m.group(3)
                startIdx = getDataIdx(dbgData, int(m.group(1)))
                endIdx = getDataIdx(dbgData, int(m.group(1)))
                if m.group(2) == "": anon = True
                else: anon = False
                arrayLen = obj.arrayLen
                enum = obj.enum
                bitfield = obj.bitfield
                width = obj.width
                dprint('PRE-Matching Case  6.1: Intermediate Struct of Pointer to Prototype\n', enable=debugPrintEnabled)
                obj.typedef = typedef
                obj.dataType = dataType
                obj.pprint(enable=debugPrintEnabled, all=True)
                pressReturnToContinue('Matching Case  6.1: Intermediate Struct of Pointer to Prototype', obj.depth*4, enable=debugPrintEnabled)
                return obj

            # Matching Case 8.0:
            # 2545:        "flushInProgress" offset 128, Member  Info C Logical*1
            # 185:         "quot" offset 0, Member  Info C++ Int
            # 2363:        "sliceCount" offset 0, Member  Info C Int
            # 2794:        "commandFetcherEnabled" offset 0, Member  Info C Logical*1
            # 7153:        "pmicInterruptTriggered" offset 0, Member  Info volatile C Logical*1
            elif re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +Info( volatile)? +(C\+*) +([\w\*\d]+)$', line):
                m = re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +Info( volatile)? +(C\+*) +([\w\*\d]+)$', line)
                uid = obj.uid
                instance = m.group(2)
                typedef = m.group(6)
                pack = self.getPackValue(typedef)
                if pack is None: pack = obj.pack
                dataType = m.group(6)
                offset = int(m.group(3))
                info = m.group(5)
                depth = obj.depth+1
                startIdx = getDataIdx(dbgData, int(m.group(1)))
                endIdx = getDataIdx(dbgData, int(m.group(1)))
                if m.group(2) == "": anon = True
                else: anon = False
                arrayLen = [1]
                enum = False
                dprint('PRE-Matching Case 8.0: End-point member with offset', enable=debugPrintEnabled)

                myObj = DataTypeObject(uid=uid, instance=instance, typedef=typedef, dataType=dataType, info=info, offset = offset,
                                       depth=depth, startIdx=startIdx, endIdx=endIdx, anon=anon, arrayLen=arrayLen, enum=enum, pack=pack)
                obj.memberList.append(myObj)
                obj.pprint(enable=debugPrintEnabled, all=True)
                pressReturnToContinue('POST-Matching Case 8.0: End-point member with offset', obj.depth*4, enable=debugPrintEnabled)

            # Matching Case 8.1:
            # 3747:        "cmdHandle" offset 32, Member  Info Pointer to C Void
            # 35:          "_io_next" offset 0, Member  Info Pointer to C++ UChar
            # 5936:        "allowCmd" offset 0, Member  Info Pointer to C Logical*1
            elif re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +Info Pointer to +(C\+*) +([\w\*\d]+)', line):
                m = re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +Info Pointer to +(C\+*) +([\w\*\d]+)', line)
                uid = obj.uid
                instance = m.group(2)
                typedef = 'uint32_t'
                dataType = 'pointer'
                offset = int(m.group(3))
                info = 'Pointer to %s' % m.group(4)
                depth = obj.depth+1
                startIdx = getDataIdx(dbgData, int(m.group(1)))
                endIdx = getDataIdx(dbgData, int(m.group(1)))
                if m.group(2) == "": anon = True
                else: anon = False
                arrayLen = [1]
                enum = False

                myObj = DataTypeObject(uid=uid, instance=instance, typedef=typedef, dataType=dataType, info=info, offset = offset,
                                       depth=depth, startIdx=startIdx, endIdx=endIdx, anon=anon, arrayLen=arrayLen, enum=enum, pack=obj.pack)
                myObj.pprint(enable=debugPrintEnabled, all=True)
                dprint('PRE-Matching Case  8.1: End-point pointer member with offset', enable=debugPrintEnabled)

                obj.memberList.append(myObj)
                obj.pprint(enable=debugPrintEnabled, all=True)
                pressReturnToContinue('POST-Matching Case  8.1: End-point pointer member with offset', obj.depth*4, enable=debugPrintEnabled)

            # Matching Case 8.2:
            # 2945:        "marketingProductName" offset 320, Member  Info Array of C Char [0..15]
            # 32:          "eventIdValid" offset 32, Member  Info Array of C Logical*1 [0..0]
            elif re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +Info Array of +(C\+*) +([\w\*\d]+) +\[(\d+)\.\.(\d+)\]', line):
                m = re.match('^(\d+): +\"(.*)\" +offset +(\d+), +Member +Info Array of +(C\+*) +([\w\*\d]+) +\[(\d+)\.\.(\d+)\]', line)
                uid = obj.uid
                instance = m.group(2)
                typedef = m.group(5)
                pack = self.getPackValue(typedef)
                if pack is None: pack = obj.pack
                dataType = m.group(5)
                offset = int(m.group(3))
                info = 'Array of %s' % m.group(4)
                depth = obj.depth+1
                startIdx = getDataIdx(dbgData, int(m.group(1)))
                endIdx = getDataIdx(dbgData, int(m.group(1)))
                if m.group(2) == "": anon = True
                else: anon = False
                arrayLen = [int(m.group(7))+1]
                enum = False

                myObj = DataTypeObject(uid=uid, instance=instance, typedef=typedef, dataType=dataType, info=info, offset = offset,
                                       depth=depth, startIdx=startIdx, endIdx=endIdx, anon=anon, arrayLen=arrayLen, enum=enum, pack=pack)
                # myObj.pprint(enable=debugPrintEnabled, all=True)
                dprint('PRE-Matching Case  8.2: End-point array member with offset', obj.depth*4, enable=debugPrintEnabled)
                obj.memberList.append(myObj)
                obj.pprint(enable=debugPrintEnabled, all=True)
                pressReturnToContinue('POST-Matching Case  8.2: End-point array member with offset', obj.depth*4, enable=debugPrintEnabled)

            # Matching Case #9.0:
            # 10:      "uint32_t" Typedef  Info C++ UInt
            # 5:       "int8_t" Typedef  Info C++ SChar
            # 6:       "uint8_t" Typedef  Info C++ UChar
            # 8:       "uint64_t" Typedef  Info C ULongLong
            elif re.match('^(\d+): +\"(.*)\" +Typedef +Info +(C.*) +(\w+)$', line):
                m = re.match('^(\d+): +\"(.*)\" +Typedef +Info +(C.*) +(\w+)$', line)
                obj.typedef = instance = m.group(2)
                obj.dataType = dataType = m.group(4)
                obj.info = m.group(3)

                if obj.typedef in BASE_CDATATYPE_SIZE_MAP.keys() and (obj.size is None or obj.size == 0):
                    obj.size = BASE_CDATATYPE_SIZE_MAP[obj.typedef]*8
                elif obj.dataType in BASE_CDATATYPE_SIZE_MAP.keys() and (obj.size is None or obj.size == 0):
                    obj.size = BASE_CDATATYPE_SIZE_MAP[obj.dataType]*8

                obj.pprint(enable=debugPrintEnabled, all=True)
                pressReturnToContinue('POST-Matching Case  9.0: End-point Base data type', obj.depth*4, enable=debugPrintEnabled)
                return obj

            # Matching Case 10.0:
            #   981:     ""      val:-1     ind:(970,-1)    Union-End  Info
            #   980:     ""      val:-1     ind:(973,-1)    Struct-End  Info
            #   2528:    ""      val:-1     ind:(2510,-1)   Enum-End  Info
            elif re.match('^(\d+): +\"(.*)\" +val:(-?\d+) +ind:\((.+),(.+)\) +(\w+)-End', line):
                m = re.match('^(\d+): +\"(.*)\" +val:(-?\d+) +ind:\((.+),(.+)\) +(\w+)-End', line)
                dprint('Matching Case 20.0: %s-End\n' % m.group(1), enable=debugPrintEnabled)
                pressReturnToContinue('Matching Case 10.0: %s-End' % m.group(1), obj.depth*4, enable=debugPrintEnabled)

            elif re.match('^(\d+):.+', line) and\
                 ("Function returning" not in line) and \
                 ("Prototype returning" not in line) and \
                 ("Pointer to C Void" not in line) and \
                 ("Pointer to C++ Void" not in line) and\
                 ("File-Begin" not in line):
                dprint("\n"+line, obj.depth*4, enable=1)
                self.log.warning("Unhandled data line <<<%s>>>" % line)
                pressReturnToContinue("<<<<ERROR>>>> Unhandled data line", obj.depth*4, enable=1)

            idx += 1

            #########################################################################################################
            # As we march down the structure processiong line by line, we do not expect any Struct-Begin,
            # Union-Begin, or Enum-Bgin text. So If we do, it's the end of the structure that we are processing.
            if "Struct-Begin" in dbgData[idx] or "Union-Begin" in dbgData[idx] or "Enum-Begin" in dbgData[idx]:
                dprint("", indent=0, enable=debugPrintEnabled)
                pressReturnToContinue("Complete analysis of %s" % obj.instance, obj.depth*4, enable=debugPrintEnabled)
                break
            #########################################################################################################

        return obj

    def __calculateMemberSizes(self, obj):
        for idx in range(len(obj.memberList)):
            if str(obj.memberList[idx].size) in ['None', '0']:
                arrayElements = 1
                for i in obj.memberList[idx].arrayLen: arrayElements = arrayElements * i

                if (obj.memberList[idx].width is not None):
                    obj.memberList[idx].size = obj.memberList[idx].width

                elif idx+1 == len(obj.memberList):
                    if (obj.size is not None) and (obj.size > 0) and (obj.memberList[idx].offset is not None):
                        obj.memberList[idx].size = (obj.size-obj.memberList[idx].offset) / arrayElements

                elif (obj.memberList[idx+1].offset is not None) and (obj.memberList[idx].offset is not None):
                    obj.memberList[idx].size = (obj.memberList[idx+1].offset - obj.memberList[idx].offset) / arrayElements

            elif obj.memberList[idx].width is not None and obj.memberList[idx] > 0:
                obj.memberList[idx].size = obj.memberList[idx].width

            if obj.memberList[idx].width is None and obj.memberList[idx].size is not None and obj.memberList[idx].size != 0:
                obj.memberList[idx].width = obj.memberList[idx].size

            if 'Logical*' in obj.memberList[idx].dataType and obj.memberList[idx].size is not None:
                obj.memberList[idx].typedef = obj.memberList[idx].dataType

            # if str(obj.memberList[idx].dataType) != 'enumval' and obj.memberList[idx].size < 0:
            #     obj.memberList[idx].pprint(enable=1, all=False)
            #     pressReturnToContinue('Negative size', enable=1)

            self.__calculateMemberSizes(obj.memberList[idx])

    def __calculateStructSize(self, obj):
        for m in obj.memberList:
            self.__calculateStructSize(m)

        if obj.dataType == 'struct' and (obj.size is None or obj.size == 0) and (obj.width is None or obj.width == 0):
            obj.size = 0
            for m in obj.memberList:
                if m.size is not None:
                    obj.size = obj.size + m.size
            obj.width = obj.size

    def __unionMemberSizeCheck(self, obj):
        for m in obj.memberList:
            self.__unionMemberSizeCheck(m)

        if obj.dataType == "union" and len(obj.memberList) > 0:
            for m in obj.memberList:
                arrayElements = 1
                for i in m.arrayLen: arrayElements = arrayElements * i
                m.status['EQUAL_UNION_SIZE'] = True
                if (m.size * arrayElements) != obj.size:
                    m.status['EQUAL_UNION_SIZE'] = False
                    logString = 'Union parent-member size mismatch ...\n'
                    logString += "uid:            %s\n" % str(obj.uid)
                    logString += "instance:       %s\n" % str(obj.instance)
                    logString += "typedef:        %s\n" % str(obj.typedef)
                    logString += "dataType:       %s\n" % str(obj.dataType)
                    logString += "info:           %s\n" % str(obj.info)
                    logString += "size:           %s\n" % str(obj.size)
                    logString += "offset:         %s\n" % str(obj.offset)
                    logString += "depth:          %s\n" % str(obj.depth)
                    logString += "startIdx:       %s\n" % str(obj.startIdx)
                    logString += "endIdx:         %s\n" % str(obj.endIdx)
                    logString += "width:          %s\n" % str(obj.width)
                    logString += "anon:           %s\n" % str(obj.anon)
                    logString += "unnamed:        %s\n" % str(obj.unnamed)
                    logString += "arrayLen:       %s\n" % str(obj.arrayLen)
                    logString += "enum:           %s\n" % str(obj.enum)
                    logString += "bitfield:       %s\n" % str(obj.bitfield)
                    logString += '\n'
                    logString += "uid:            %s\n" % str(m.uid)
                    logString += "instance:       %s\n" % str(m.instance)
                    logString += "typedef:        %s\n" % str(m.typedef)
                    logString += "dataType:       %s\n" % str(m.dataType)
                    logString += "info:           %s\n" % str(m.info)
                    logString += "size:           %s\n" % str(m.size)
                    logString += "offset:         %s\n" % str(m.offset)
                    logString += "depth:          %s\n" % str(m.depth)
                    logString += "startIdx:       %s\n" % str(m.startIdx)
                    logString += "endIdx:         %s\n" % str(m.endIdx)
                    logString += "width:          %s\n" % str(m.width)
                    logString += "anon:           %s\n" % str(m.anon)
                    logString += "unnamed:        %s\n" % str(m.unnamed)
                    logString += "arrayLen:       %s\n" % str(m.arrayLen)
                    logString += "enum:           %s\n" % str(m.enum)
                    logString += "bitfield:       %s\n" % str(m.bitfield)
                    self.log.warning(logString)

    def __inlinedCheck(self, obj):
        for o in obj.memberList:
            if o.anon: o.inlined = True
            elif not re.search("__Ut\d+$", str(o.instance)) and str(o.typedef) == "": o.inlined = True
            self.__inlinedCheck(o)

    def imprintFieldLocation(self, obj):
        if len(obj.memberList) > 0:
            for i in range(len(obj.memberList)):
                obj.memberList[i].location = copy.deepcopy(obj.location)
                obj.memberList[i].location.append(i+1)
                self.imprintFieldLocation(obj.memberList[i])

    def imprintFieldDataCheckUid(self, obj):
        obj.dataCheckUid = "%s.%s.%s" % (str(obj.instance), str(obj.typedef), str(obj.dataType))
        if len(obj.memberList) > 0:
            for i in range(len(obj.memberList)):
                obj.memberList[i].dataCheckUid = "%s.%s.%s" % (str(obj.memberList[i].instance), str(obj.memberList[i].typedef), str(obj.memberList[i].dataType))
                self.imprintFieldDataCheckUid(obj.memberList[i])

    def __generateCtypeParserFile(self, obj, outFile=None, generatedCtypeClasses=[], versioned=True):
        if obj.depth == 0:
            generatedCtypeClasses = []

        if outFile is None:
            if obj.versionMajor != 0xBADD and obj.versionMinor != 0xC0DE and versioned:
                outParserFile = os.path.join(self.versionedParserFolder, '%s_%s_%s.py' % (obj.instance, str(obj.versionMajor), str(obj.versionMinor)))
            else: outParserFile = os.path.join(self.unversionedParserFolder, '%s.py' % obj.instance)
            if os.path.exists(outParserFile): os.remove(outParserFile)
            with open(outParserFile, "wb") as pyParserFile:
                autoParserTxt  = "#!/usr/bin/python\n"
                autoParserTxt += "# -*- coding: utf-8 -*-\n"
                autoParserTxt += "\"\"\""
                autoParserTxt += "This file is automatically generated by autoParser.py per data object.  Please do not modify."
                autoParserTxt += "\"\"\"\n\n"
                autoParserTxt += "from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations\n"
                autoParserTxt += "import sys, os, copy\n"
                autoParserTxt += "from ctypes import *\n"
                #autoParserTxt += "from struct import Struct, Union\n"
                autoParserTxt += "\n"
                autoParserTxt += "try:\n"
                autoParserTxt += "    # Python 2\n"
                autoParserTxt += "    range  # @todo python 2 convert\n"
                autoParserTxt += "except NameError:\n"
                autoParserTxt += "    # Python 3\n"
                autoParserTxt += "    range = range\n"
                autoParserTxt += "\n"
                pyParserFile.write(autoParserTxt)
        else: outParserFile = outFile

        for m in obj.memberList:
            if len(m.memberList) > 0:
                self.__generateCtypeParserFile(m, outFile=outParserFile, generatedCtypeClasses=generatedCtypeClasses)

        obj.generateCtypeParserLib(outFile=outParserFile, generatedCtypeClasses=generatedCtypeClasses)

        return outParserFile

    def __generateCstructHeaderFile(self, obj, outFile=None):
        global alreadyGeneratedCstructs

        if obj.depth == 0:
            outPutLine("// This file was automatically generated by autoParser.", outFile=outFile, append=False)

        for m in obj.memberList:
            if len(m.memberList) > 0:
                self.__generateCstructHeaderFile(m, outFile=outFile)

        if (obj.dataType is not None) and (obj.dataType.lower() == 'enum'):
            enumStorageString = obj.cFormatter(indentBase=0)
            if enumStorageString != "":
                outPutLine(enumStorageString, outFile=outFile)

        elif (obj.dataType is not None) and (obj.dataType.lower() in ['union', 'struct']) and (not obj.inlined):
            nonAnonStorageString = obj.cFormatter(indentBase=0)
            if nonAnonStorageString != "":
                outPutLine(nonAnonStorageString, outFile=outFile)

    def __getVersionMajorMinor(self, vMajorMacro, vMinorMacro):
        vMajor = None
        vMinor = None
        foundMajorV = False
        foundMinorV = False

        if re.match('^\d+$', str(vMajorMacro)):
            vMajor = int(vMajorMacro)
            foundMajorV = True

        if re.match('^\d+$', str(vMinorMacro)):
            vMinor = int(vMinorMacro)
            foundMinorV = True

        with open(self.dbgDumpFile, 'r') as iFile:
            for l in iFile:
                if vMajorMacro is None:
                    vMajor = None
                    foundMajorV = True

                elif not foundMajorV and vMajorMacro in l:
                    # 168: "BIS_VERSION_MAJOR" -> "1019"
                    if re.match('^.+\"%s\" -> \"([\dxX]+)\"' % vMajorMacro,l.strip()):
                        m = re.match('^.+\".+\" -> \"([\dxX]+)\"', l.strip())
                        if 'x' in m.group(1):
                            vMajor = int(m.group(1), 16)
                        else: vMajor = int(m.group(1))
                        foundMajorV = True
                        continue

                if vMinorMacro is None:
                    vMinor = None
                    foundMinorV = True

                elif not foundMinorV and vMinorMacro in l:
                    # 169: "BIS_VERSION_MINOR" -> "0"
                    if re.match('^.+\"%s\" -> \"([\dxX]+)\"' % vMinorMacro,l.strip()):
                        m = re.match('^.+\".+\" -> \"([\dxX]+)\"', l.strip())
                        if 'x' in m.group(1):
                            vMinor = int(m.group(1), 16)
                        else: vMinor = int(m.group(1))
                        foundMinorV = True
                        continue

                if foundMajorV and foundMinorV: break

        # Only if both vMajor and vMinor cannot be found that we assign them BADDC0DE values.
        if vMajor is None and vMinor is None:
            vMajor = 0xBADD
            vMinor = 0xC0DE

        return vMajor, vMinor

    def __createInitFiles(self):
        initFileList = [os.path.join(self.versionedParserFolder, '__init__.py'),
                        os.path.join(self.unversionedParserFolder, '__init__.py'),
                        os.path.join(self.outDir, '__init__.py')]
        for f in initFileList:
            outputString = "#!/usr/bin/python\n"
            outputString += "# -*- coding: utf-8 -*-\n"
            outputString += "\"\"\""
            outputString += "This file is automatically generated by autoParser.py per.  Please do not modify."
            outputString += "\"\"\"\n\n"
            outputString += "import sys, os\n"
            outputString += "os.sys.path.insert(1,'..')"
            with open(f, "wb") as initFile: initFile.write(outputString)

        outputString = "#!/usr/bin/python\n"
        outputString += "# -*- coding: utf-8 -*-\n"
        outputString += "\"\"\""
        outputString += "This file is automatically generated by autoParser.py.  Please do not modify."
        outputString += "\"\"\"\n"
        outputString += "# Description:  This is the entry point for FIDL.\n"
        outputString += "# Author: Phuong P. Tran, Joseph D. Tarango\n"
        outputString += "# Date:   2/26/2019\n"
        outputString += "\n"
        outputString += "from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations\n"
        outputString += "import os\n"
        outputString += "import re\n"
        outputString += "import sys\n"
        outputString += "import subprocess\n"
        outputString += "\n"
        outputString += "try:\n"
        outputString += "    # Python 2\n"
        outputString += "    range  # @todo python 2 convert\n"
        outputString += "except NameError:\n"
        outputString += "    # Python 3\n"
        outputString += "    range = range\n"
        outputString += "\n"
        outputString += "CWD = os.path.abspath(os.path.dirname(__file__))\n"
        outputString += "\n"
        outputString += "def createFidlStartupFile():\n"
        outputString += "    moduleList = []\n"
        outputString += "    if os.path.exists(os.path.join(CWD, 'autoParsers')):\n"
        outputString += "        parserLibFolder = \"autoParsers\"\n"
        outputString += "    elif os.path.exists(os.path.join(CWD, 'versioned')):\n"
        outputString += "        parserLibFolder = \"versioned\"\n"
        outputString += "    else:\n"
        outputString += "        print(\"Cannot find compatible autoParser ctype library folder!\\n\")\n"
        outputString += "        os.exit(0)\n"
        outputString += "\n"
        outputString += "    outString += \"#!/usr/bin/python\\n\"\n"
        outputString += "    outString += \"# -*- coding: utf-8 -*-\\n\"\n"
        outputString += "    outString  = \"\\\"\\\"\\\"This file is automatically generated by autoParser.py.  Please do not modify.\\\"\\\"\\\"\\n\"\n"
        outputString += "    outString += \"# Description:  FIDL is an interactive parser tool used to demo the autoParser library.\\n\"\n"
        outputString += "    outString += \"# Author:       Phuong P. Tran, Joseph D. Tarango\\n\"\n"
        outputString += "    outString += \"# Date:         2/26/2019\\n\"\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    outString += \"from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations\\n\"\n"
        outputString += "    outString += \"import os\\n\"\n"
        outputString += "    outString += \"import re\\n\"\n"
        outputString += "    outString += \"import sys\\n\"\n"
        outputString += "    outString += \"import subprocess\\n\"\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    outString += \"try:\\n\"\n"
        outputString += "    outString += \"    # Python 2\\n\"\n"
        outputString += "    outString += \"    range  # @todo python 2 convert\\n\"\n"
        outputString += "    outString += \"except NameError:\\n\"\n"
        outputString += "    outString += \"    # Python 3\\n\"\n"
        outputString += "    outString += \"    range = range\\n\"\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    outString += \"### Additional imports to support interactive use case ######################################\\n\"\n"
        outputString += "    outString += \"try:\\n\"\n"
        outputString += "    outString += \"    import readline\\n\"\n"
        outputString += "    outString += \"    import rlcompleter\\n\"\n"
        outputString += "    outString += \"    import atexit\\n\"\n"
        outputString += "    outString += \"except ImportError:\\n\"\n"
        outputString += "    outString += \"    pass    # Dont print anything on failure\\n\"\n"
        outputString += "    outString += \"else:\\n\"\n"
        outputString += "    outString += \"    try:\\n\"\n"
        outputString += "    outString += \"        if os.name == \\\"nt\\\":\\n\"\n"
        outputString += "    outString += \"            homepath = os.path.join(os.environ[\\\"HOMEDRIVE\\\"], os.environ[\\\"HOMEPATH\\\"])\\n\"\n"
        outputString += "    outString += \"        else: homepath = os.environ[\\\"HOME\\\"]\\n\"\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    outString += \"        histfile = os.path.join(homepath, \\\".pythonhistory\\\")\\n\"\n"
        outputString += "    outString += \"        import rlcompleter\\n\"\n"
        outputString += "    outString += \"        readline.parse_and_bind(\\\"tab: complete\\\")\\n\"\n"
        outputString += "    outString += \"        if os.path.isfile(histfile):\\n\"\n"
        outputString += "    outString += \"            readline.read_history_file(histfile)\\n\"\n"
        outputString += "    outString += \"        atexit.register(readline.write_history_file, histfile)\\n\"\n"
        outputString += "    outString += \"    except Exception,e: \\n\"\n"
        outputString += "    outString += \"        pass    # Dont print anything on failure\\n\"\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    outString += \"class FidlPrompt(object):\\n\"\n"
        outputString += "    outString += \"    def __repr__ (self): return \\\"FIDL> \\\"\\n\"\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    outString += \"sys.ps1 = FidlPrompt()\\n\"\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    outString += \"THIS_FOLDER = os.path.abspath(os.path.dirname(__file__))\\n\"\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    outString += \"banner = \\\"\\\"\\\"\\n\"\n"
        outputString += "    outString += \"           _______ _____ ______        \\n\"\n"
        outputString += "    outString += \"           |______   |   |     \ |     \\n\"\n"
        outputString += "    outString += \"Welcome to |       __|__ |_____/ |____ \\n\"\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    outString += \"Your friendly autoParser-based Parser!\\n\"\n"
        outputString += "    outString += \"\\\"\\\"\\\"\\n\"\n"
        outputString += "    outString += \"print(banner)\\n\"\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    outString += \"### If TWIDL PYTHONPATH is defined, attempt to get the drive object #########################\\n\"\n"
        outputString += "    outString += \"twidl = None\\n\"\n"
        outputString += "    outString += \"if 'PYTHONPATH' in os.environ.keys() and 'twidl' in os.environ['PYTHONPATH'].lower():\\n\"\n"
        outputString += "    outString += \"    from scan import Scan\\n\"\n"
        outputString += "    outString += \"    from device import *\\n\"\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    outString += \"    def getDrive(drvIndex=None):\\n\"\n"
        outputString += "    outString += \"        ### Scan all drives\\n\"\n"
        outputString += "    outString += \"        myScan = Scan(extend=True)\\n\"\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    outString += \"        ### Ask user to select drive to use\\n\"\n"
        outputString += "    outString += \"        if (drvIndex is None):\\n\"\n"
        outputString += "    outString += \"            drvIndex = myScan.selectDevice(\\\"Select Device \\\")\\n\"\n"
        outputString += "    outString += \"            if (drvIndex is None): return None\\n\"\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    outString += \"        ### Get physical drive path of selected drive index\\n\"\n"
        outputString += "    outString += \"        drvPath = myScan.getDevicePath(drvIndex)\\n\"\n"
        outputString += "    outString += \"        if (drvPath is None):\\n\"\n"
        outputString += "    outString += \"            print(\\\"The specified drive index (\\\"+str(drvIndex)+\\\") is not valid!\\\" )\\n\"\n"
        outputString += "    outString += \"            return None\\n\"\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    outString += \"        ### Instantiate the drive object\\n\"\n"
        outputString += "    outString += \"        drive = Device().getDevice(devicePath=drvPath,flags = 1|2)\\n\"\n"
        outputString += "    outString += \"        if not drive.getCmdSet():\\n\"\n"
        outputString += "    outString += \"            print('Drive with INVALID CMD SET !!!')\\n\"\n"
        outputString += "    outString += \"            return None\\n\"\n"
        outputString += "    outString += \"        try:\\n\"\n"
        outputString += "    outString += \"            drive.unlock()\\n\"\n"
        outputString += "    outString += \"        except:\\n\"\n"
        outputString += "    outString += \"            print('Could not unlock drive!!!')\\n\"\n"
        outputString += "    outString += \"            return None\\n\"\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    outString += \"        return drive\\n\"\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    outString += \"    twidl = getDrive(drvIndex=None)\\n\"\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    outString += \"### If we have a twidl drive object, map some basic methods from TWIDL to FIDL ##############\\n\"\n"
        outputString += "    outString += \"if twidl is not None:\\n\"\n"
        outputString += "    outString += \"    dictNlog = twidl.dictNlog\\n\"\n"
        outputString += "    outString += \"    getId = twidl.getId\\n\"\n"
        outputString += "    outString += \"    listNlog = twidl.listNlog\\n\"\n"
        outputString += "    outString += \"    parseNlog = twidl.parseNlog\\n\"\n"
        outputString += "    outString += \"    parseFConfig = twidl.parseFConfig\\n\"\n"
        outputString += "    outString += \"    setFormatsFile = twidl.setFormatsFile\\n\"\n"
        outputString += "    outString += \"    unlock = twidl.unlock\\n\"\n"
        outputString += "    outString += \"    writeTokenValue = twidl.writeTokenValue\\n\"\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    outString += \"    print('\\\\nTWIDL commands are available in FIDL using the twidl prefix (example: twidl.getId())\\\\n')\\n\"\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    outString += \"    getId()\\n\"\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    outString += \"### Parser Lib Import #######################################################################\\n\"\n"
        outputString += "\n"
        outputString += "    modulePath = os.path.join(CWD, parserLibFolder)\n"
        outputString += "    fileList = os.listdir(modulePath)\n"
        outputString += "    fileList.reverse()\n"
        outputString += "    for f in fileList:\n"
        outputString += "        if re.match(\"^(\\w.+)_(\\w+)_(\\w+)\\.py$\", f):\n"
        outputString += "            m = re.match(\"^(\\w.+)_(\\w+)_(\\w+)\\.py$\", f)\n"
        outputString += "            if m.group(1) not in moduleList:\n"
        outputString += "                versionedParserModule = m.group(1) + '.py'\n"
        outputString += "                if os.path.exists(os.path.join(CWD, parserLibFolder, versionedParserModule)):\n"
        outputString += "                    moduleList.append(m.group(1))\n"
        outputString += "                    outString += \"import %s.%s as %s\\n\" % (parserLibFolder, m.group(1), m.group(1))\n"
        outputString += "\n"
        outputString += "    outString += \"\\n\"\n"
        outputString += "    maxNameLen = 0\n"
        outputString += "    for m in moduleList:\n"
        outputString += "        if len(m) > maxNameLen: maxNameLen = len(m)\n"
        outputString += "\n"
        outputString += "    for m in moduleList:\n"
        outputString += "        outString += \"### %s #############################################################%s\\n\" % (m, (maxNameLen-len(m))*\"#\")\n"
        outputString += "        outString += \"def union%s%s(inFile=None): return %s.getUnion(inFile=inFile, drive=twidl, verbose=True)\\n\" % (m[0].upper(), m[1:], m)\n"
        outputString += "        outString += \"def struct%s%s(inFile=None): return %s.getStruct(inFile=inFile, drive=twidl, verbose=True)\\n\" % (m[0].upper(), m[1:], m)\n"
        outputString += "        outString += \"def parse%s%s(inFile=None, outFile=None): return %s.parseStruct(inFile=inFile, drive=twidl, outFile=outFile)\\n\" % (m[0].upper(), m[1:], m)\n"
        outputString += "\n"
        outputString += "    with open(os.path.join(CWD, \"fidl_startup.py\"), \"wb\") as fidleStartup: fidleStartup.write(outString)\n"
        outputString += "\n"
        outputString += "if __name__ == '__main__':\n"
        outputString += "    os.chdir(CWD)\n"
        outputString += "    createFidlStartupFile()\n"
        outputString += "    cmd = 'python -i %s ' % os.path.join(CWD, 'fidl_startup.py')\n"
        outputString += "    try: retCode = subprocess.call(cmd, shell=True)\n"
        outputString += "    except KeyboardInterrupt: retCode = -1\n"
        outputString += "    os._exit(retCode)\n"
        with open(os.path.join(self.outDir, "fidl.py"), "wb") as apcFile: apcFile.write(outputString)

    def __createPerObjectWrapper(self, instance, readNlba=None, writeNlba=None):
        outputString = "#!/usr/bin/python\n"
        outputString += "# -*- coding: utf-8 -*-\n"
        outputString += "\"\"\""
        outputString += "This file was automatically generated by autoParser.py per specified data object."
        outputString += "\"\"\"\n"
        outputString += "from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations\n"
        outputString += "\n"
        outputString += "# standard library imports\n"
        outputString += "import os, re, sys\n"
        outputString += "from ctypes import sizeof\n"
        outputString += "\n"
        outputString += "try:\n"
        outputString += "    # Python 2\n"
        outputString += "    range  # @todo python 2 convert\n"
        outputString += "except NameError:\n"
        outputString += "    # Python 3\n"
        outputString += "    range = range\n"
        outputString += "\n"
        outputString += "BLOCK_SIZE = 512\n"
        outputString += "RNLBA = %s\n" % str(readNlba)
        outputString += "WNLBA = %s\n" % str(writeNlba)
        outputString += "\n"
        outputString += "def getUnion(inFile=None, drive=None, verbose=False):\n"
        outputString += "    cwd = os.getcwd()\n"
        outputString += "    modulePath = os.path.split(os.path.abspath(__file__))[0]\n"
        outputString += "    fileList = os.listdir(modulePath)\n"
        outputString += "    fileList.reverse()\n"
        outputString += "    dataVersionMajor = None\n"
        outputString += "    dataVersionMinor = None\n"
        outputString += "\n"
        outputString += "    inBuffer = None\n"
        outputString += "    # Read data from drive once now if inFile is None\n"
        outputString += "    if (inFile is None) and (drive is not None) and (RNLBA is not None):\n"
        outputString += "        maxStructBytes = 0\n"
        outputString += "        for f in fileList:\n"
        outputString += "            if re.match(\"^bis_(\\w+)_(\\w+)\\.py$\", f):\n"
        outputString += "                versionedParserModule = re.sub('\\.py', '', f)\n"
        #outputString += "                try:\n"
        #outputString += "                    exec ('import versioned.%s' % versionedParserModule)\n"
        #outputString += "                except:\n"
        #outputString += "                    eval ('import versioned.%s' % versionedParserModule)\n"
        #outputString += "                try:\n"
        #outputString += "                    exec ('u = %s.getUnion()' % versionedParserModule)\n"
        #outputString += "                except:\n"
        #outputString += "                    eval ('u = %s.getUnion()' % versionedParserModule)\n"
        outputString += "                exec ('import versioned.%s' % versionedParserModule)\n"
        outputString += "                exec ('u = %s.getUnion()' % versionedParserModule)\n"
        outputString += "                if sizeof(u) > maxStructBytes: maxStructBytes = sizeof(u)\n"
        outputString += "\n"
        outputString += "        if maxStructBytes > 0:\n"
        outputString += "            drive.nread(RNLBA, (maxStructBytes + BLOCK_SIZE - 1) / BLOCK_SIZE)\n"
        outputString += "            inBuffer = drive.getReadBuffer()\n"
        outputString += "        else: inBuffer = None\n"
        outputString += "\n"
        outputString += "    for f in fileList:\n"
        outputString += "        if re.match(\"^%s_(\w+)_(\w+)\.py$\", f):\n" % instance
        outputString += "            versionedParserModule = re.sub('\.py', '', f)\n"
        #outputString += "            try:\n"
        #outputString += "                exec ('import versioned.%s' % versionedParserModule)\n"
        #outputString += "            except:"
        #outputString += "                eval ('import versioned.%s' % versionedParserModule)\n"
        #outputString += "            if inFile is not None:\n"
        #outputString += "                try:\n"
        #outputString += "                    exec ('u = %s.getUnion(inFile=r\"%s\")' % (versionedParserModule, inFile))\n"
        #outputString += "                except:"
        #outputString += "                    eval ('u = %s.getUnion(inFile=r\"%s\")' % (versionedParserModule, inFile))\n"        
        #outputString += "            else:\n"
        #outputString += "                try:\n"
        #outputString += "                    exec ('u = %s.getUnion(inBuffer=inBuffer)' % versionedParserModule)\n"
        #outputString += "                except:\n"
        #outputString += "                    eval ('u = %s.getUnion(inBuffer=inBuffer)' % versionedParserModule)\n"
        outputString += "            exec ('import versioned.%s' % versionedParserModule)\n"
        outputString += "            if inFile is not None:\n"
        outputString += "                exec ('u = %s.getUnion(inFile=r\"%s\")' % (versionedParserModule, inFile))\n"
        outputString += "            else: exec ('u = %s.getUnion(inBuffer=inBuffer)' % versionedParserModule)\n"
        outputString += "\n"
        outputString += "            # Since we have reversed the parser files above, vMinor just has to be <= vMinor in bin data to parse.\n"
        outputString += "            # Note: The if statement below is coded as such because expectedMinor() and getVersionMinor() may both be None or Int.  \"<=\" will not work.\n"
        outputString += "            if u.expectedMajor() == u.getVersionMajor() and (u.expectedMinor() == u.getVersionMinor() or u.expectedMinor() < u.getVersionMinor()):\n"
        outputString += "                dataVersionMajor = u.getVersionMajor()\n"
        outputString += "                dataVersionMinor = u.getVersionMinor()\n"
        outputString += "                if verbose: print(\"Data version major: %s, data version minor: %s.\" % (str(dataVersionMajor), str(dataVersionMinor)))\n"
        outputString += "                if hasattr(u.Struct, 'tailMagic'):\n"
        outputString += "                    if int(u.Struct.tailMagic) == 0x600DF00D: print('GOOD tailMagic!')\n"
        outputString += "                    else: print('BAD tailMagic!')\n"
        outputString += "                else: print('NO tailMagic!')\n"
        outputString += "                if inBuffer: del inBuffer\n"
        outputString += "                return u\n"
        outputString += "\n"
        outputString += "            if dataVersionMajor is None and u.getVersionMajor() is not None:\n"
        outputString += "                dataVersionMajor = u.getVersionMajor()\n"
        outputString += "                dataVersionMinor = u.getVersionMinor()\n"
        outputString += "\n"
        outputString += "    if verbose: print(\"\\nData version major: %s, data version minor: %s.\" % (str(dataVersionMajor), str(dataVersionMinor)))\n"
        outputString += "    if verbose: print(\"No compatible parser found for the specified data bin.\")\n"
        outputString += "    if inBuffer: del inBuffer\n"
        outputString += "    return None\n"
        outputString += "\n"
        outputString += "def getStruct(inFile=None, drive=None, verbose=False):\n"
        outputString += "    u = getUnion(inFile=inFile, drive=drive, verbose=verbose)\n"
        outputString += "    if u is not None:\n"
        outputString += "       return u.Struct\n"
        outputString += "    else: return None\n"
        outputString += "\n"
        outputString += "def parseStruct(inFile=None, drive=None, outFile=None):\n"
        outputString += "    u = getUnion(inFile=inFile, drive=drive, verbose=True)\n"
        outputString += "    if u is not None:\n"
        outputString += "        s = u.getStruct().parse(outFile=outFile)\n"
        outputString += "        return True\n"
        outputString += "    else: return False\n"
        outputString += "\n"

        with open(os.path.join(self.versionedParserFolder, "%s.py" % instance), "wb") as wrapperFile:
            wrapperFile.write(outputString)

    def autoGenerateCtypes(self):
        """Performs the transformation of the fundamental type to Python c-type."""

        dprint('\nAnalyzing FW build ...')

        debugPrintEnabled = False
        ctypeHash = {}
        global SequenceNumber
        global alreadyGeneratedCstructs

        # If there is an input CFG file to guide parser lib generation, use it instead.
        if self.options.inputCfg is not None:
            inputCgfFile = os.path.abspath(self.options.inputCfg)
            print("Input CFG: %s" % inputCgfFile)
            try:
                exec(open(inputCgfFile).read())
                if not dataStructure.AUTOPARSER_DATA_OBJECT_LIST:     # After the exec() command, there should be a list named AUTOPARSER_DATA_OBJECT_LIST.
                    print("\nProblem importing the specified input CFG file (%s).\n" % inputCgfFile)
                    sys.exit(0)
            except:
                print("\nProblem importing the specified input CFG file (%s).\n" % inputCgfFile)
                sys.exit(0)
        else:
            self.AUTOPARSER_DATA_OBJECT_LIST = BUILT_IN_DATA_OBJECT_LIST

        # If we are to parse only the specified struct, check to see if it is in the data object list
        if self.options.structToParse is not None:
            foundStructToParse = False
            for idx in range(len(self.AUTOPARSER_DATA_OBJECT_LIST)):
                if self.AUTOPARSER_DATA_OBJECT_LIST[idx][0] == self.options.structToParse or self.AUTOPARSER_DATA_OBJECT_LIST[idx][1] == self.options.structToParse:
                    foundStructToParse = True
                    break
            if not foundStructToParse:
                print('The specified structure to parse (%s) does not exist in the CFG table/file.')
                return False

        # Dump debug data
        self.__doDebugDataDump()
        if not os.path.exists(self.dbgDumpFile):
            print("\nSomething is wrong.  %s does not exist!!!" % self.dbgDumpFile)
            sys.exit(0)

        # Create __init__.py in subfolders
        self.__createInitFiles()

        # Find max length
        maxInstanceLen = len('Instance')
        maxTypedefLen = len('Typedef')
        for idx in range(len(self.AUTOPARSER_DATA_OBJECT_LIST)):
            instance = self.AUTOPARSER_DATA_OBJECT_LIST[idx][0]
            typedef = self.AUTOPARSER_DATA_OBJECT_LIST[idx][1]
            if len(instance) > maxInstanceLen: maxInstanceLen = len(instance)
            if len(typedef) > maxTypedefLen: maxTypedefLen = len(typedef)

        # Processing each data object through the data dump data to generate its Python C-Type.
        dprint("\n%-*s  %-*s  %5s  %5s  %-12s %-12s %-12s %-12s" % (maxInstanceLen, 'Instance', maxTypedefLen, 'Typedef', 'Major', 'Minor', 'UnverImport', 'UnverSize', 'VerImport', 'VerSize'), enable=1)
        for idx in range(len(self.AUTOPARSER_DATA_OBJECT_LIST)):
            if self.AUTOPARSER_DATA_OBJECT_LIST[idx][0] == 'SUBSTRUCT_PACKING':
                continue
            elif self.options.structToParse is not None:
                if self.AUTOPARSER_DATA_OBJECT_LIST[idx][0] != self.options.structToParse and self.AUTOPARSER_DATA_OBJECT_LIST[idx][1] != self.options.structToParse:
                    continue

            uid = idx + 1
            instance = self.AUTOPARSER_DATA_OBJECT_LIST[idx][0]
            typedef = self.AUTOPARSER_DATA_OBJECT_LIST[idx][1]
            versionMajorMacro = self.AUTOPARSER_DATA_OBJECT_LIST[idx][2]
            versionMinorMacro = self.AUTOPARSER_DATA_OBJECT_LIST[idx][3]
            versionMajor, versionMinor = self.__getVersionMajorMinor(versionMajorMacro, versionMinorMacro)
            pack = self.AUTOPARSER_DATA_OBJECT_LIST[idx][4]
            versionMajorMemberName = self.AUTOPARSER_DATA_OBJECT_LIST[idx][5]
            versionMinorMemberName = self.AUTOPARSER_DATA_OBJECT_LIST[idx][6]
            readNlba = self.AUTOPARSER_DATA_OBJECT_LIST[idx][7]
            writeNlba = self.AUTOPARSER_DATA_OBJECT_LIST[idx][8]

            dbgData, symTypedefRow, symTypedefRefRow, startIdx, endIdx = self.__getBuildDbgData(typedef)
            if symTypedefRow is None and symTypedefRefRow is None and startIdx is None and endIdx is None:
                print("\nTypedef %s cannot be found in FW build debug data.\n" % typedef)
                continue

            obj = DataTypeObject(uid, instance, typedef, dataType=None, info=None, size=None, offset=None, depth=0, startIdx=startIdx, endIdx=endIdx,
                                 width=None, anon=False, arrayLen=[1], enum=False, versionMajor=versionMajor, versionMinor=versionMinor, pack=pack,
                                 versionMajorMemberName=versionMajorMemberName, versionMinorMemberName=versionMinorMemberName, readNlba=readNlba, writeNlba=writeNlba)

            # writeListToFile(dbgData, os.path.join(self.outDir, 'autoParser_%s.txt' % instance))
            ctypeHash[typedef] = self.__buildCtypeParser(obj, dbgData)

            # Printing out data object's member list for visual inspection
            dprint("\n=====================================================", enable=debugPrintEnabled)
            dprint("Printing out the ctypeHash object structural list ...", enable=debugPrintEnabled)
            dprint("=====================================================", enable=debugPrintEnabled)
            ctypeHash[typedef].pprint(enable=debugPrintEnabled, all=True)
            if debugPrintEnabled: print("")

            # Calculate depth=1 member sizes
            self.__calculateMemberSizes(ctypeHash[typedef])
            self.__calculateStructSize(ctypeHash[typedef])

            # Check and mark in-line defined substructs
            self.__inlinedCheck(ctypeHash[typedef])

            # Imprint field location
            self.imprintFieldLocation(ctypeHash[typedef])

            # Imprint field location
            self.imprintFieldDataCheckUid(ctypeHash[typedef])

            # Visually inspect the overall structure
            # ctypeHash[typedef].visualInspection(enable=1)

            # Generate JSON per FW data struct
            jsonOutFile = os.path.join(self.jsonParserFolder, '%s_%s_%s.json' % (ctypeHash[typedef].instance, str(ctypeHash[typedef].versionMajor), str(ctypeHash[typedef].versionMinor)))
            ctypeHash[typedef].generateCtypeJson(jsonOutFile)

            # Generate C-formatted structs
            alreadyGeneratedCstructs = []
            cFormatFile = os.path.join(self.cFormatHeaderFolder, '%s_%s_%s.h' % (ctypeHash[typedef].instance, str(ctypeHash[typedef].versionMajor), str(ctypeHash[typedef].versionMinor)))
            self.__generateCstructHeaderFile(ctypeHash[typedef], outFile=cFormatFile)

            # Generate Python C-type class parser
            SequenceNumber = 1
            PadSequenceNumber = 1

            unVersionedOutParserFile = self.__generateCtypeParserFile(ctypeHash[typedef], versioned=False)
            unversionedImportStatus, unversionedSizeStatus = sanityChecks(unVersionedOutParserFile, ctypeHash[typedef].versionMajorMemberName, ctypeHash[typedef].versionMinorMemberName)
            ctypeHash[typedef].status['UNVERSIONED_IMPORT'] = unversionedImportStatus
            ctypeHash[typedef].status['UNVERSIONED_SIZE'] = unversionedSizeStatus

            versionedImportStatus = None
            versionedSizeStatus = None
            versionedOutParserFile = None
            ctypeHash[typedef].status['VERSIONED_IMPORT'] = None
            ctypeHash[typedef].status['VERSIONED_SIZE'] = None
            if ctypeHash[typedef].versionMajor != 0xBADD and ctypeHash[typedef].versionMinor != 0xC0DE:
                versionedOutParserFile = self.__generateCtypeParserFile(ctypeHash[typedef], versioned=True)
                versionedImportStatus, versionedSizeStatus = sanityChecks(versionedOutParserFile, ctypeHash[typedef].versionMajorMemberName, ctypeHash[typedef].versionMinorMemberName)
                ctypeHash[typedef].status['VERSIONED_IMPORT'] = versionedImportStatus
                ctypeHash[typedef].status['VERSIONED_SIZE'] = versionedSizeStatus

            self.__createPerObjectWrapper(ctypeHash[typedef].instance, readNlba=ctypeHash[typedef].readNlba, writeNlba=ctypeHash[typedef].writeNlba)

            if unversionedImportStatus: 
                unversionedImportStatusString = "PASS"
            else: unversionedImportStatusString = "FAIL"
            statusString = "Unverioned-Import-%s" % unversionedImportStatusString

            if unversionedSizeStatus: 
                unversionedSizeStatusString = "PASS"
            else: unversionedSizeStatusString = "FAIL"
            statusString += "/Unverioned-Size-%s" % unversionedSizeStatusString

            if versionedImportStatus is not None:
                if versionedImportStatus:
                    versionedImportStatusString = "PASS"
                else: versionedImportStatusString = "FAIL"
            else: versionedImportStatusString = ""
            statusString += "/Verioned-Import-%s" % versionedImportStatusString

            if versionedSizeStatus is not None:
                if versionedSizeStatus:
                    versionedSizeStatusString = "PASS"
                else: versionedSizeStatusString = "FAIL"
            else: versionedSizeStatusString = ""
            statusString += "/Verioned-Size-%s" % versionedSizeStatusString

            if ctypeHash[typedef].versionMajor == 0xBADD:
                dprint("%-*s  %-*s  %-5s  %-5s  %-12s %-12s %-12s %-12s" % (maxInstanceLen, str(ctypeHash[typedef].instance), maxTypedefLen, str(typedef),           "",           "", 
                     unversionedImportStatusString, unversionedSizeStatusString, versionedImportStatusString, versionedSizeStatusString), enable=1)
            elif ctypeHash[typedef].versionMajor != 0xBADD and ctypeHash[typedef].versionMinor is None:
                dprint("%-*s  %-*s  %5s  %5s  %-12s %-12s %-12s %-12s" % (maxInstanceLen, str(ctypeHash[typedef].instance), maxTypedefLen, str(typedef), str(ctypeHash[typedef].versionMajor),        "", 
                    unversionedImportStatusString, unversionedSizeStatusString, versionedImportStatusString, versionedSizeStatusString), enable=1)
            else: 
                dprint("%-*s  %-*s  %5s  %5s  %-12s %-12s %-12s %-12s" % (maxInstanceLen, str(ctypeHash[typedef].instance), maxTypedefLen, str(typedef), str(ctypeHash[typedef].versionMajor), str(ctypeHash[typedef].versionMinor), 
                    unversionedImportStatusString, unversionedSizeStatusString, versionedImportStatusString, versionedSizeStatusString), enable=1)

            # Member size check
            self.__unionMemberSizeCheck(ctypeHash[typedef])

            # Generate pickle file per FW data struct
            pickleFile = os.path.join(self.pickleParserFolder, '%s_%s_%s.pkl' % (ctypeHash[typedef].instance, str(ctypeHash[typedef].versionMajor), str(ctypeHash[typedef].versionMinor)))
            savePickleObject(ctypeHash[typedef], pickleFile)

            # pressReturnToContinue(enable=1)

        # Delete working data files to save space.
        self.__deleteTempFiles()

def copyDirectory(src, dst):
    if not os.path.exists(src):
        print("Source location does not exist: {}".format(src))
        return

    if os.path.exists(dst):
        try:
            shutil.rmtree(dst)
        except Exception as e:
            print("Failed to remove {}".format(dst))
            print(e)

    try:
        shutil.copytree(src, dst)
    except Exception as e:
        print( "Failed to copy {} to {}".format(src, dst))
        print (e)

def main():
    parser = OptionParser(usage)
    parser.add_option("--cfg", dest='inputCfg', metavar='<CFG>', default=None, help='CFG file with specified FW structs to direct parser generation (default=None)')
    parser.add_option("--compiler", dest='ghsCompilerVersion', metavar='<COMPVER>', default=GHS_COMPILER_VERSION, help='GHS compiler version (default=comp_201754)')
    parser.add_option("--debug", action='store_true', dest='debug', default=False, help='Debug mode.')
    parser.add_option("--example", action='store_true', dest='example', default=False, help='Show command execution example.')
    parser.add_option("--fwbuilddir", dest='fwBuildOutputDir', metavar='<DIR>', default=None, help='FW build directory (ex: projects/objs/alderstream_02)')
    parser.add_option("--project", dest='projectName', metavar='<PROJ>', default=None, help='Project name (ex: alderstream_02)')
    parser.add_option("--verbose", action='store_true', dest='verbose', default=False, help='Verbose printing for debug use.')
    parser.add_option("--struct", dest='structToParse', metavar='<STRUCT>', default=None, help='Parse only the specified structure or named instance')
    (options, args) = parser.parse_args()

    if options.example:
        print('\nCommand-line execution example:')
        print('%s' % r'<<Process structures>> autoParser.py --fwbuilddir .\projects\objs\alderstream_dp_02 --project alderstream_02 --cfg autoParser.cfg')
        print('%s' % r'<<Process 1 struct>>   autoParser.py --fwbuilddir .\projects\objs\alderstream_dp_02 --project alderstream_02 --cfg autoParser.cfg --struct Bis_t')
        quit(22)

    if (options.fwBuildOutputDir is None):
        print('\nPlease specify options')
        print(options)
        print(args)
        quit(23)

    options.projectName = os.path.split(options.fwBuildOutputDir)[-1]

    fwBuildOutputDirCheck = os.path.abspath(options.fwBuildOutputDir)
    if not os.path.exists(fwBuildOutputDirCheck):
        print('\nPlease specify "--fwbuilddir" option to specify the folder with elf file')
        quit(24)

    print("\nBuild project name:          %s" % (options.projectName))
    print("Project build output dir:    %s" % (options.fwBuildOutputDir))

    # Extract FW C-structs #####################
    cag = AutoParser(options)
    cag.autoGenerateCtypes()

if __name__ == '__main__':
    """Performs execution delta of the process."""
    start_time = datetime.datetime.now()
    main()
    finish_time = datetime.datetime.now()
    print("\nExecution Start Time:", str(start_time))
    print("Execution End Time:  ", str(finish_time))
    print("Total Execution Time:", str(finish_time-start_time))
    quit(0)

## @}
