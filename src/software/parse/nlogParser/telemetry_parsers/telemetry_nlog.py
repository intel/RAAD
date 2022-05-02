#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors:Joseph Tarango, Randal Eike, Daniel Garces
# *****************************************************************************/


#### library includes
import sys, struct, re, os, time
import ctypes

#### import test utilities
from src.software.parse.nlogParser.test_util.output_log import OutputLog
from src.software.parse.nlogParser.telemetryutil.telemetry_util import openReadFile
from src.software.parse.nlogParser.telemetryutil.telemetry_util import GetTruncatedDataBuffer
from src.software.parse.nlogParser.telemetryutil.telemetry_util import BuildFileName

#### import translation helpers
from src.software.parse.nlogParser.telemetry_parsers.nlogEnum import nlogEnumTranslate

### import nlog triage helpers
from src.software.parse.nlogParser.nlog_triage.pssDebugTraceTriage import pssDebugTraceTriage
from src.software.parse.nlogParser.nlog_triage.hostTimeMarkerTriage import HostTimeMarkerTriage
from src.software.parse.nlogParser.nlog_triage.padrTriage import padrTriage

from unidecode import unidecode

# Version 1.0 : Initial release
# Version 2.0 : Enhanced enum name replacement
# Version 3.0 : Added triage parsing interface
# Version 3.1 : Added pssDebugTraceTriage parsing
# Version 3.2 : Added HostTimeMarkerTriage parsing
# Version 3.3 : Added padrTriage parsing
# Version 3.4 : Added select version 2 to deal with SATA telemetry nlogs
NLOG_PARSE_VERSION = 3.4

MAX_NUM_NLOGS = 64 # Currently, the max number of nlogs is 255 inclusive
                    # 256 is not a valid nlog number

NUM_CFG_NLOG_MAX = 64
HW_CLOCK_FREQUENCY = 781200
ASSERT_FILE_DWORDS = 64000

MAX_NLOG_BUFFER_KBLOCKS = 16
MAX_NLOG_BUFFER_SIZE = (MAX_NLOG_BUFFER_KBLOCKS * 1024)
MAX_NLOG_ENTRIES = (MAX_NLOG_BUFFER_SIZE / 8)

nlogNameDictionary = {
    0: "ID  ",
    1: "Test",
    2: "TC  ",
    3: "DBug",
    4: "Temp",
    5: "15M ",
    6: "10D ",
    7: "Host",
    8: "BG  ",
    9: "Uniq",
    10: "Sys ",
    11: "Err ",
    12: "PLI ",
    13: "IBM ",
    14: "Stat",
    15: "TSta",
    16: "HFR ",
    17: "EHst",
    18: "Warn",
    19: "Rare",
    20: "Thrm",
    21: "MRRf",  ## MRR Fast (high velocity)
    22: "UEC ",
    23: "Trim",
    24: "MRRs",  ## MRR Slow (Low velocity)
    25: "Nei ",  ## Nei
    26: "Dm  ",  ## Defect Map
    27: "VAL ",  ## VAL
    28: "OPAL",  ## Opal logs
    29: "IRQ ",  ## IRQ  logs
    30: "DCTV",  ## DIRECTIVES logs
    31: "STM ",  ## STM logs
    32: "MI  ",  ## NVMe MI Logs
    33: "IO  ",  ## Reserved
    34: "BGF ",  ## Background Fast (High Veilocity) Log
    35: "PMIC",  ## PMIC Log
    36: "XPT ",  ## XPT logs
    }

def NLogPoolArray(data):
    count = int(len(data) / struct.calcsize("I"))
    fmt = "I" * count
    return list(struct.unpack(fmt,data))


class UnionBase(ctypes.Union):
    def __init__(self, imageBuffer, blockSize):
        dataSize, dataBuffer = GetTruncatedDataBuffer(imageBuffer, blockSize, 512)
        for i in range(dataSize):
            self.Bytes[i] = dataBuffer[i]

    def parse(self):
        return str(self)

class NlogSelectVersion_struct(ctypes.Structure):
    """
    Brief:
        NlogSelectVersion_struct() - Data structure definition for TVE Nlog Select version identification

    Description:
        This is the structure class of the TVE Nlog select read/write test command.  Data read and write
        from the drive using TC -51.

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Phuong P Tran
    """

    _pack_      = 1
    _fields_    = [
                    ("VersionMajor",        ctypes.c_uint16),
                    ("VersionMinor",        ctypes.c_uint16) ]

    def __str__(self):
        """
        Brief:
            string representation of class, used by str() and print commands
        """
        # build up a string to return
        retString  = ""
        retString += "VersionMajor:         %d\n" % (self.VersionMajor)
        retString += "VersionMinor:         %d\n" % (self.VersionMinor)

class NlogSelect_struct(ctypes.Structure):
    """
    Brief:
        NlogSelect_struct() - Data structure definition for TVE Nlog Select read and write test command

    Description:
        This is the structure class of the TVE Nlog select read/write test command.  Data read and write
        from the drive using TC -51.

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Phuong P Tran
    """

    _pack_      = 1
    _fields_    = [
                    ("Version",             NlogSelectVersion_struct),
                    ("LogSelect",           ctypes.c_uint16 * int(MAX_NUM_NLOGS/16) ),
                    ("TimestampStart",      ctypes.c_uint64),
                    ("TimestampEnd",        ctypes.c_uint64),
                    ("Reserved",            ctypes.c_uint32 * 10) ]

    def __str__(self):
        """
        Brief:
            string representation of class, used by str() and print commands
        """

        # build up a string to return
        retString  = ""
        retString += str(self.Version)

        for i in range(MAX_NUM_NLOGS/16):
            retString += "Nlogs %03i..%03i:       %s %s %s %s\n" % ((i+1)*16-1, (i*16),
            bin(self.LogSelect[i])[2:].zfill(16)[:4], bin(self.LogSelect[i])[2:].zfill(16)[4:8],
            bin(self.LogSelect[i])[2:].zfill(16)[8:12], bin(self.LogSelect[i])[2:].zfill(16)[12:])

        retString += "TimestampStart:       %d\n" % (self.TimestampStart)
        retString += "TimestampEnd:         %d\n" % (self.TimestampEnd)

        return retString

    def __findIdNumber(self):
        for id in range(MAX_NUM_NLOGS):
            wordNumber, bitNumber = divmod(id, 16)
            if ((self.LogSelect[wordNumber] & (1 << bitNumber)) != 0): return id
        return -1

    def getLogName(self):
        # Find the ID number
        id = self.__findIdNumber()
        if ((id != -1) and (id < len(nlogNameDictionary))): return nlogNameDictionary[id]
        else: return "UNKN"

    def getLogId(self):
        id = self.__findIdNumber()
        if ((id != -1) and (id < len(nlogNameDictionary))): return id
        else: return MAX_NUM_NLOGS

    def getCoreSelected(self):
        return None

    def getLogByteSize(self):
        return 8*1024

    def getTicksPerSecond(self):
        return 200000000.0

class NlogSelectV2_struct(ctypes.Structure):
    """
    Brief:
        NlogSelectV2_struct() - Data structure definition for V2.0 TVE Nlog Select read and write test command

    Description:
        This is the structure class of the TVE Nlog select read/write test command.  Data read and write
        from the drive using TC -51.

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Phuong P Tran
    """

    _pack_      = 1
    _fields_    = [
                    ("Version",               NlogSelectVersion_struct), # offset 0x00
                    ("LogSelect",             ctypes.c_uint64),  # offset 0x04
                    ("totalNlogs",            ctypes.c_uint32),  # offset 0x0C, number of NLog IDs.
                    ("nlogId",                ctypes.c_uint32),  # offset 0x10, selected NLog ID.
                    ("nlogName",              ctypes.c_uint8*4), # offset 0x14, selected NLog name.
                    ("nlogByteSize",          ctypes.c_uint32),  # offset 0x18, selected NLog size in bytes.
                    ("nlogPrimaryBufferSize", ctypes.c_uint32),  # offset 0x1C, for variable size primary buffers, not yet supported.
                    ("ticksPerSecond",        ctypes.c_uint32),  # offset 0x20, System Clock Frequency.
                    ("coreCount",             ctypes.c_uint32),  # offset 0x24, core count.
                    ("nlogPauseStatus",       ctypes.c_uint64),  # offset 0x28, current NLog pause/unpause status bitmap
                    ("coreSelected",          ctypes.c_uint32),  # offset 0x30, selected core.
                    ("Reserved",              ctypes.c_uint32 * 6) ]

    def __str__(self):
        """
        Brief:
            string representation of class, used by str() and print commands
        """
        # build up a string to return
        retString  = ""
        retString += str(self.Version)
        retString += "Nlogs         %04x\n" % (self.LogSelect)
        retString += "Id:           %d\n" % (self.nlogId)
        retString += "Name:         %s\n" % (self.getLogName())
        retString += "Ticks/Second: %d\n" % (self.ticksPerSecond)
        retString += "Buffer Size:  %u\n" % (self.nlogPrimaryBufferSize)
        retString += "Core:         %u\n" % (self.coreSelected)
        retString += "Core count:   %u\n" % (self.coreCount)
        return retString

    def getLogName(self):
        retName = format("%c%c%c%c" % (self.nlogName[3], self.nlogName[2], self.nlogName[1], self.nlogName[0]))
        return retName.upper()

    def getLogId(self):
        return self.nlogId

    def getCoreSelected(self):
        return self.coreSelected

    def getLogByteSize(self):
        return self.nlogByteSize

    def getTicksPerSecond(self):
        return (self.ticksPerSecond * 1.0)

class NlogSelectV4_struct(ctypes.Structure):
    """
    Brief:
        NlogSelectV4_struct() - Data structure definition for V4.0 TVE Nlog Select read and write test command

    Description:
        This is the structure class of the TVE Nlog select read/write test command.  Data read and write
        from the drive using TC -51.

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Phuong P Tran
    """

    _pack_      = 1
    _fields_    = [
                    ("Version",               NlogSelectVersion_struct), # offset 0x00
                    ("LogSelect",             ctypes.c_uint32),  # offset 0x04
                    ("totalNlogs",            ctypes.c_uint32),  # offset 0x08, number of NLog IDs.
                    ("nlogId",                ctypes.c_uint32),  # offset 0x0C, selected NLog ID.
                    ("nlogName",              ctypes.c_uint8*4), # offset 0x10, selected NLog name.
                    ("nlogByteSize",          ctypes.c_uint32),  # offset 0x14, selected NLog size in bytes.
                    ("nlogPrimaryBufferSize", ctypes.c_uint32),  # offset 0x18, for variable size primary buffers, not yet supported.
                    ("ticksPerSecond",        ctypes.c_uint32),  # offset 0x1C, System Clock Frequency.
                    ("coreCount",             ctypes.c_uint32),  # offset 0x20, core count.
                    ("nlogPauseStatus",       ctypes.c_uint64),  # offset 0x24, current NLog pause/unpause status bitmap
                    ("selectOffsetRef",       ctypes.c_uint32),  # offset 0x2C, 0=Offset if relative to the oldest slice; 1=Offset is relative to the first slice.
                    ("selectNlogPause",       ctypes.c_uint32),  # offset 0x30, Host selected 0=NOP, 1=NLOG_PAUSE, 2=NLOG_UNPAUSE.
                    ("selectAddedOffset",     ctypes.c_uint32),  # offset 0x34, Added offset to access large NLog buffer without increasing the existing NLog direct access range.
                    ("nlogBufNum",            ctypes.c_uint32),  # offset 0x38, selected NLog buffer Number associated with NLog ID.
                    ("nlogBufNumMax",         ctypes.c_uint32),  # offset 0x3C, number of NLog buffers.
                    ("coreSelected",          ctypes.c_uint32),  # offset 0x40, selected core.
                    ("Reserved",              ctypes.c_uint32 * 2) ]

    def __str__(self):
        """
        Brief:
            string representation of class, used by str() and print commands
        """
        # build up a string to return
        retString  = ""
        retString += str(self.Version)
        retString += "Nlogs         %04x\n" % (self.LogSelect)
        retString += "Id:           %d\n" % (self.nlogId)
        retString += "Name:         %s\n" % (self.getLogName())
        retString += "Ticks/Second: %d\n" % (self.ticksPerSecond)
        retString += "Buffer Size:  %u\n" % (self.nlogPrimaryBufferSize)
        retString += "Core:         %u\n" % (self.coreSelected)
        retString += "Core count:   %u\n" % (self.coreCount)
        return retString

    def getLogName(self):
        retName = format("%c%c%c%c" % (self.nlogName[3], self.nlogName[2], self.nlogName[1], self.nlogName[0]))
        return retName.upper()

    def getLogId(self):
        return self.nlogId

    def getCoreSelected(self):
        return self.coreSelected

    def getLogByteSize(self):
        return self.nlogByteSize

    def getTicksPerSecond(self):
        return (self.ticksPerSecond * 1.0)
     

class NlogSelect_union(UnionBase):
    """
    Brief:
        NlogSelect_union() - Top level data structure for TVE Nlog select read/write

    Description:
        This class is the structure of TVE Nlog select data read from or write to
        the drive using TC -51.
    """

    _pack_        = 1
    _fields_    = [ ("Version",              NlogSelectVersion_struct),
                    ("Version1",             NlogSelect_struct),
                    ("Version2",             NlogSelectV2_struct),
                    ("Version4",             NlogSelectV4_struct),
                    ("Bytes",                ctypes.c_ubyte  *  ctypes.sizeof(NlogSelectV4_struct) ) ]

    def getStruct(self):
        if (self.Version.VersionMajor >= 4 ): return self.Version4
        elif (self.Version.VersionMajor == 2 ): return self.Version2
        else: return self.Version1

    def getStructSize(self):
        if (self.Version.VersionMajor >=4 ): return ctypes.sizeof(NlogSelectV4_struct)
        else: return ctypes.sizeof(NlogSelect_struct)


class _nlogHdr_struct(ctypes.Structure):
    """
    Brief:
        nlogHdr_struct() - Nlog header structure

    Description:
        This class is the structure of Event Header data read from the
        drive using Direct Access TC @ base address 0xFFF50000.

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Phuong P Tran
    """

    _pack_      = 1
    _fields_    = [
                    ("nlogName",              ctypes.c_uint8*4), # offset 0x00, NLog name.
                    ("nlogId",                ctypes.c_uint32),  # offset 0x04, NLog ID.
                    ("bufPtr",                ctypes.c_uint32),  # offset 0x08, Buffer pointer.
                    ("bufSize",               ctypes.c_uint32),  # offset 0x0C, Size of the nlog data.
                    ("cfgFlags",              ctypes.c_uint32)   # offset 0x10, Config Flags.
                  ]

    def getLogName(self):
        retName = format("%c%c%c%c" % (self.nlogName[3], self.nlogName[2], self.nlogName[1], self.nlogName[0]))
        return retName.upper()

    def getLogId(self):
        return self.nlogId

    def getCoreSelected(self):
        return -1

    def getLogByteSize(self):
        return self.bufSize


class EventHeader_struct(ctypes.Structure):
    """
    Brief:
        EventHeader_struct() - Data structure definition for Event Header

    Description:
        This class is the structure of Event Header data read from the
        drive using Direct Access TC @ base address 0xFFF50000.

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Phuong P Tran
    """

    _pack_      = 1
    _fields_    = [
                    ("NumParams",          ctypes.c_uint32,  8),
                    ("EventNum",           ctypes.c_uint32, 12),
                    ("SourceNum",          ctypes.c_uint32, 12) ]

class EventHeader_union(ctypes.Union):
    """
    Brief:
        EventHeader_union() - Union structure definition to load the Event Header structure (event ID) 
        with the data from the nlog dword list

    Description:
        Event ID definition (first 1 word) of the nlog entry.

    Class(es):
        EventHeader_struct

    Method(s):
        __init__(dwordList, currentOffset)
        object getStruct()

    Related:
        EventTimeStamp_struct, EventId_struct

    Author(s):
        Phuong P Tran, modified Randal Eike to include timestamp
    """

    _pack_      = 1
    _fields_    = [ ("header",      EventHeader_struct),
                    ("dword",       ctypes.c_uint32) ]
    #0xFFFFFE01: ('"Wall clock epoch time (seconds since 12:00am, January 1, 1970): %d\\n"', 'file.c', 0, ['param0']),
    #0xFFFFFE06: ('"-I- Nvme Host time since 12:00am, January 1, 1970: 0x%X:%08X msec,  0x%X:%08X seconds, power on time: 0x%X:%08X msec\\n"', 'file.c', 0, ['param0', 'param1', 'param2', 'param3', 'param4', 'param5']),
	#0xFFFFFF02: ('"Recovered power-down time: 0x%08X 0x%08X\\n"', 'file.c', 0, ['param0', 'param1']),

    WALL_CLOCK_EPOCH_TOKEN = 0xFFFFFE01
    HOST_TIME_SET_TOKEN    = 0xFFFFFE06
    TIME_ADJUSTMENT_TOKEN  = 0xFFFFFF02
    EMPTY_TOKEN            = 0
    MAX_PARAMETER_COUNT    = 8
    SOURCE0_EVENT_LIST     = [0xA82]

    def __init__(self, dwordList, currentOffset):
        """
        Constuctor

        @param dwordList - List of 32-bit word nlog buffer
        @param currentOffset - Current working offset where we expect to find the entry header
        """
        # Fill the structure
        tempDword = dwordList[currentOffset]
        #if sys.version[:3] == "2.3":
        #    if(tempDword & (1L << 31)): tempDword -= 1L << 32
        self.dword = tempDword

    def getNumParams(self):
        return self.header.NumParams

    def getEventNum(self):
        return self.header.EventNum

    def getSourceNum(self):
        return self.header.SourceNum

    def getFormatDictionaryKey(self):
        return self.dword

    def isEmpty(self):
        if (self.dword == EventHeader_union.EMPTY_TOKEN): return True
        else: return False

    def isValid(self):
        if (self.header.NumParams > EventHeader_union.MAX_PARAMETER_COUNT):
            OutputLog.DebugPrint(2, format("Invalid nlog event: 0x%x" % (self.dword)))
            return False
        elif ((self.header.SourceNum == 0) and (self.header.EventNum not in EventHeader_union.SOURCE0_EVENT_LIST)):
            OutputLog.DebugPrint(2, format("Invalid nlog source id, event: 0x%x" % (self.dword)))
            return False
        elif (self.header.EventNum == 0):
            OutputLog.DebugPrint(2, format("Invalid nlog event id, event: 0x%x" % (self.dword)))
            return False
        else:
            return True

    def isTimeAdjustEvent(self):
        if (self.dword == EventHeader_union.TIME_ADJUSTMENT_TOKEN): return True
        else: return False

    def isWallClockEpochTimeEvent(self):
        if (self.dword == EventHeader_union.WALL_CLOCK_EPOCH_TOKEN): return True
        else: return False

    def isHostTimeSetEvent(self):
        if (self.dword == EventHeader_union.HOST_TIME_SET_TOKEN): return True
        else: return False

    def getDwordCount(self):
        return 1

class EventTimeStamp_struct(ctypes.Structure):
    """
    Brief:
        EventTimeStamp_struct() - Data structure definition for Event Header timestamp

    Description:
        This class is the timestamp nlog event structure.

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Randal Eike
    """

    _pack_      = 1
    _fields_    = [ ("seconds",           ctypes.c_uint32,31),
                    ("time0Marker",       ctypes.c_uint32,1),
                    ("ticks",             ctypes.c_uint32)]

    def getTime(self):
        if (self.time0Marker == 1): time0Mark = True 
        else: time0Mark = False 
        return time0Mark, self.seconds, self.ticks


class EventTimeStamp_union(ctypes.Union):
    """
    Brief:
        EventTimeStamp_union() - Union structure definition to load the Event timestamp structure 
        with the data from the nlog dword list

    Description:
        Event definition and timestamp (first 3 words) of the nlog entry.

    Class(es):
        EventId_struct,EventTimeStamp_struct

    Method(s):
        __init__(dwordList, currentOffset)
        object getStruct()

    Related:
        EventTimeStamp_struct, EventId_struct

    Author(s):
        Phuong P Tran, modified Randal Eike to include timestamp
    """

    _pack_        = 1
    _fields_    = [ ("timeStamp",   EventTimeStamp_struct),
                    ("dword",       ctypes.c_uint32 * 2) ]

    def __init__(self, dwordList, currentOffset):
        """
        Constuctor

        @param dwordList - List of 32-bit word nlog buffer
        @param currentOffset - Current working offset where we expect to find the entry header
        """
        # Fill the structure
        self.dword[0] = dwordList[currentOffset]
        self.dword[1] = dwordList[currentOffset+1]

    def getStruct(self):
        """
        Get the entry header structure object

        @return object - Entry header data
        """
        return self.timeStamp

    @staticmethod
    def getDwordCount():
        return 2


class NlogEventPoolParser(object):
    """
    Brief:
        NlogEventPoolParser - Class to aid in the conversion of an nlog dword pool
        into a list of nlog event tuples

    Class(es):
        EventId_struct, EventTimeStamp_struct

    Method(s):
        __init__(nlogName)
        tuple list getEventTupleList(dwordList)

    Related:
        EventTimeStamp_struct, EventId_struct

    Author(s):
        Randal Eike
    """
    def __init__(self, nlogName, coreId = None):
        """
        Constructor

        @param nlogName - Nlog name to put in the event tuple list
        @param coreId - Core number associated with the log
        """
        self.nlogName = nlogName
        self.coreId = coreId
        self.events = []
        self.localTimeZone = None

    def __getTimeAndZone(self, tsSeconds, tsTicks, time0Mark = False, timeBaseSeconds = None, timeBaseTicks = None):
        zone = 1
        msgSeconds = tsSeconds
        msgTicks = tsTicks

        if (time0Mark == True):
            if (timeBaseSeconds is None):
                zone = 0
            else:
                msgSeconds = tsSeconds + timeBaseSeconds
                msgTicks = tsTicks + timeBaseTicks

        return zone, tsSeconds, tsTicks

    def setLocalTimeZone(self, timeZone):
        """
        Set the timezone according to the input local timezone specification from the log generator.

        If this function is not called or if the python version does not support the tzset
        then calander clock output remains set to UTC time.

        @param timeZone - Timezone environment variable
        """
        if ((sys.version_info[0] == 3) or ((sys.version_info[0] == 2) and (sys.version_info[1] >= 17))):
            # Can't do this if version less than 2.7.17
            self.localTimeZone = timeZone
            os.environ['TZ'] = timeZone
            time.tzset()

    def getEventTupleList(self, dwordList):
        """
        Read and translate the input nlog bin file into an ordered event tuple list.  Modified from nlogpost2.py extractEvents().

        @param dwordList - Dword list of nlog entries or None if we should use the constructor

        @return list - Chronologically ordered list of nlog events tuples (zone number 0 | 1, time stamp MSW, time stamp LSW, eventHeader ID structure, param tuple, nlog name string)
        """
        myPool = dwordList
        hostTimestampList = []

        # Find the events from most recent to least recent
        del self.events[:]
        offset = 0
        timeBaseSeconds, timeBaseTicks = None, None
        previousEvent = (-1, 0, 0, 0, [], self.nlogName, self.coreId)

        while (offset < len(myPool)):
            # Get the event haeder data
            eventHeader = EventHeader_union(myPool, offset)
            if (eventHeader.isEmpty()):
                # Normal if the log hasn't wrapped yet
                OutputLog.DebugPrint(4, format("Nlog %s, core %d, eventHeader[%d] empty" % (self.nlogName, self.coreId, offset)))
                offset += 1
                continue

            if (False == eventHeader.isValid()):
                # Invalid entry
                previousZone, prevSeconds, prevTicks, previousHeader, prevParams, prevnlogName, prevcoreId = previousEvent
                if (-1 != previousZone):
                    OutputLog.DebugPrint(1, "Invalid event header at offset (%d) of (%d), nlog %s, core %d" % (offset-1, len(myPool), self.nlogName, self.coreId))
                    OutputLog.DebugPrint(2, "Previous Entry: zone (%d) ts (0x%X:0x%x)" % (previousZone, prevSeconds, prevTicks))
                    OutputLog.DebugPrint(2, "Previous Entry: header (0x%x), nlog %s, core %d" % (previousHeader.getFormatDictionaryKey(), prevnlogName, prevcoreId))

                offset += 1
                continue

            # Check if this event has been partially overwritten and is no good.
            numParams = eventHeader.getNumParams()
            timeStampOffset = offset + eventHeader.getDwordCount()
            paramOffset = timeStampOffset + EventTimeStamp_union.getDwordCount()
            nextOffset = paramOffset + numParams

            if (nextOffset > len(myPool)):
                # Hit the end of the list
                OutputLog.DebugPrint(2, "nextOffset (%d) > len (%d)" % (nextOffset, len(myPool)))
                break

            # Get the timestamp
            timeStamp = EventTimeStamp_union(myPool, timeStampOffset)
            time0Mark, tsSeconds, tsTicks = timeStamp.getStruct().getTime()

            # Get the parameters
            params = tuple(myPool[paramOffset:nextOffset])

            # Check for 
            if (eventHeader.isTimeAdjustEvent()):
                timeBaseSeconds, timeBaseTicks = list(params)[0], list(params)[1]
                timeBaseSeconds &= 0x7fffffff
                OutputLog.DebugPrint(2, "Time-zero base 0x%08X 0x%08X" % (timeBaseSeconds, timeBaseTicks))

            if (eventHeader.isWallClockEpochTimeEvent()):
                wallClockSeconds = list(params)[0]
                OutputLog.DebugPrint(2, "Wall clock time %s" % (str(time.localtime(wallClockSeconds))))

            if (eventHeader.isHostTimeSetEvent()):
                utcHostTimeParamMs = (int(list(params)[0]) << 32) + int(list(params)[1])
                utcHostTimeParmSec = (int(list(params)[2]) << 32) + int(list(params)[3])
                utcHostTimeSec =  int(utcHostTimeParamMs / 1000.0)
                utcHostTimeMSec = utcHostTimeParamMs % 1000
                powerOnTimeMs = (int(list(params)[4]) << 32) + int(list(params)[5])

                if (utcHostTimeParmSec != utcHostTimeSec):
                    OutputLog.Warning(("FW param host seconds %u != calculated host time seconds %u", (utcHostTimeParmSec, utcHostTimeSec)))

                if (self.localTimeZone is None):
                    tmStruct = time.gmtime(utcHostTimeSec)
                    timeZoneName = "UTC"
                else:
                    tmStruct = time.localtime(utcHostTimeSec)
                    timeZoneName = time.tzname[tmStruct.tm_isdst]

                hostTimestamp = ("Host time marker %s.%03u %s, Power On time %u ms" % (time.asctime(tmStruct), utcHostTimeMSec, timeZoneName, powerOnTimeMs))
                OutputLog.DebugPrint(2, hostTimestamp)
                zone, msgSeconds, msgTicks = self.__getTimeAndZone(tsSeconds, tsTicks, time0Mark, timeBaseSeconds, timeBaseTicks)
                self.events.append( (zone, msgSeconds, msgTicks, None, [hostTimestamp], self.nlogName, self.coreId) )

            # Add the entry
            zone, msgSeconds, msgTicks = self.__getTimeAndZone(tsSeconds, tsTicks, time0Mark, timeBaseSeconds, timeBaseTicks)
            self.events.append( (zone, msgSeconds, msgTicks, eventHeader, params, self.nlogName, self.coreId) )
            previousEvent = (zone, tsSeconds, tsTicks, eventHeader, params, self.nlogName, self.coreId)
            offset = nextOffset

        # Switch Event list to chronological ordering
        self.events.reverse()
        return self.events

class EventTupleTranslate(object):
    """
    Brief:
        EventTupleTranslate() - Translate an input event tuple list into a list of strings

    Description:
        Using the specified nlog_format.py translate a list of nlog event tuples into 
        formatted nlog text strings.

    Class(es):
        nlogEnumTranslate

    Method(s):
        __init__(counterFreq, formatsFile)
        string list xlateEvents()

    Related:
        EventTupleTranslate - Used to generate the event tuple list that this class will translate
        OutputLog - Error, debug message handler

    Author(s):
        Randal Eike, Methods taken from nlogpost2.py and modified to use telemetry tools structures
    """
    def __getNLogFormats(self, formatsFile):
        """
        Import (read and execute) the NLog formats file into this script.  
        Stolen from nlogpost2.py getNLogFormats() and modified to work in the class

        @param formatsFile - Path and name of the nlog_formats.py file

        @return formats - Nlog format object
        """
        if (formatsFile is None):
            # Try the default file name and location (current working directory)
            formatsFile = BuildFileName('NLog_formats.py')

        # Get Format Strings
        try:
            # Use exec rather than import here.
            # Python maintains cached version of the imported files
            # that don't always get updated when the underlying file changes,
            # even if re-imported.
            myLocals = {}
            formatsFileObj = open(formatsFile)
            exec(formatsFileObj.read(), {}, myLocals)
            formats = myLocals["formats"]
            formatsFileObj.close()
            return formats

        except:
            OutputLog.Error(format("Couldn't load the formats file (%s): %s" % (formatsFile, sys.exc_info()[0])))
            return None

    def __init__(self, counterFreq = 200000000.0, formatsFile = None, enumParserFile = None, inlineTriage = False):
        """
        Constructor

        @param counterFreq - Frequency of the tuple timestamp counter
        @param formatsFile - Path and name of the nlog_formats.py file
        @param enumParserFile - Path and name of the nlogenumparser.py file
        """
        self.counterFreq = counterFreq
        self.formatsOld = False
        self.formats = self.__getNLogFormats(formatsFile)
        self.enumDictionary = nlogEnumTranslate(enumParserFile)
        self.basePath = os.path.abspath("..")
        self.triageObjectList = []  # empty list
        self.triageMessageList = []  # empty list
        self.triageHeader = []  # empty list
        self.inlineTriage = inlineTriage


    def __reformat(self, formatStr, params):
        """
        Handle some special formatting issues -- differences between Python and FW for printf.
        
        Stolen from nlogpost2.py reformat

        @param formatStr - Starting format string
        @param params - Parameter value tuple

        @return string - Updated format string
                tuple - New parameter tuple
        """
        # Return new, modified versions of given format and parameters.
        newFmt = formatStr
        newParams = []
        oldParams = list(params)
        oldIdx = 0

        # Hide any "%%" format-specs in the string from the RE searches below.
        newFmt = re.sub('%%','<<%>><<%>>', newFmt)

        # Find the next parameter specification in the format string.
        for match in re.finditer('(%[-\.\d]*?l*[cdfiusxX])',newFmt):
        
            try:
                # Check for "long" (64-bit) format.
                if re.match('%[-\.\d]*?l[cdfiusxX]',match.group(1)):
                    # Handle %ld, %lX, %lc, etc.  These take two parameters.
                    myParam = (oldParams[oldIdx] << 32) + oldParams[oldIdx+1]
                    oldIdx += 2
                    bits = 64
                else:
                    myParam = oldParams[oldIdx]
                    oldIdx += 1
                    bits = 32

            except IndexError:
                OutputLog.Warning("Index out of bounds encountered while processing the parameter list for:")
                OutputLog.Warning("  " + formatStr)
                if re.match('.*%l.*', formatStr):
                    OutputLog.Warning( "This is most likely cause by incorrect usage of %l* without the corresponding PARAM64().")
                    OutputLog.Warning( "Attempting to recover by stripping the 'l' out any instance of '%l*' in the original format string.")
                    OutputLog.Warning( "WARNING: This recovered log may have invalid param values!\n")
                    newFmt = formatStr.replace('%l', '%')
                    return self.__reformat(newFmt, params)
        
            # Handle differences between Python printf and C/NLog printf.
            if re.match('%[-\.\d]*?l*[di]',match.group(1)):
                # Handle sign for %d (and %i); Python treats everything as unsigned.
                if myParam & (1 << (bits - 1)):
                    myParam -= (1 << bits)

            elif re.match('%[-\.\d]*?l*[cs]',match.group(1)):
                # Handle multiple characters for %c (and %s) -- NLog-only extension.
                # Convert %c to %s in format.
                original = match.group(1)
                c2s = re.sub('c','s',original)
                newFmt = re.sub(original, c2s, newFmt)

                # Convert parameter to a string.
                chrStr = ""
                for chIdx in range(0, int(bits / 8)):
                    ch = chr((myParam >> (bits - (chIdx + 1) * 8)) & 0xFF)
                    if ch != chr(0):
                        chrStr += ch
                myParam = chrStr
            else:
                # Everything else is Python printf compatible; let Python handle it.
                pass

            # Updated the modified parameter list.
            newParams.append(myParam)

        # Un-Hide any "%%" format-specs in the string from the RE searches above.
        newFmt = re.sub('<<%>><<%>>','%%', newFmt)
        return newFmt, tuple(newParams)

    def __strTimestamp(self, zone, tsSeconds, tsTicks):
        """
        Convert the complex FW-style time into a hrs:mins:secs string.
        Stolen from nlogpost2.py reformat

        @param zone - Time zone, 0 = Pre time adjust or 1 = Post time adjust
        @param tsSeconds - Time stamp seconds value
        @param tsTicks - Time stamp tick value

        @return string - flagged hours, minutes, seconds timestamp value
        """
        if (zone == 0): flag = "*"    # Time-Zero Zone; 
        else: flag = " "              # Regular-Time Zone

        secs = (tsSeconds * 1.0) + (tsTicks / (self.counterFreq * 1.0))
        mins,secs = divmod(secs,60)
        hrs,mins  = divmod(mins,60)
        return "%9d:%02d:%011.8f%s" % (hrs, mins, secs, flag)

    def __getDefaultFormatString(self, lookupKey, paramCount):
        """
        Generate default format string. Original code from nlogpost2.py printEvents()

        @param lookupKey - Unknown key parameter
        @param paramCount - parameter count in case key lookup fails.  Used to generate unknown format string

        @return string - Default format string if not found
        """
        # NLog Formats file not up-to-date.  Generate a default format.
        # Example format: "Dco Freeze Lock 0x%02X 0x%02X\\n"
        self.formatsOld = True
        formatStr = "Unknown format key (EventHeader Key 0x%08X)" % (lookupKey)
        for numParam in range(0, paramCount):
            formatStr += ", p%d=0x%%08X" % (numParam)

        return formatStr

    def __getFormatString(self, lookupKey, paramCount):
        """
        Generate format string based on lookup key value.  Original code
        from nlogpost2.py printEvents()

        @param lookupKey - Key value for the dictionary lookup
        @param paramCount - parameter count in case key lookup fails.  Used to generate unknown format string

        @return string - Corresponding format string from the formats or the default format string if not found
        """
        if(self.formats is not None):
            try:
                formatStr = self.formats[lookupKey][0]

            except KeyError:
                if (EventHeader_union.TIME_ADJUSTMENT_TOKEN == lookupKey): formatStr = "Recovered power-down time: 0x%08X 0x%08X, base 0x%08X 0x%08X"
                else: formatStr = self.__getDefaultFormatString(lookupKey, paramCount)
                OutputLog.DebugPrint(4, format("exception eventHeader=0x%08X, format = '%s'" % (lookupKey, formatStr)))
        else:
            formatStr = self.__getDefaultFormatString(lookupKey, paramCount)

        return formatStr

    def __addEnums(self, formatStr, params):
        """
        Use the enum parser to insert the enum values into the format string

        @param formatStr - Starting format string
        @param params - Parameter value tuple

        @return string - new format string with enums inserted
        """
        if (self.enumDictionary is not None):
            # Try and add enum values
            retStr = self.enumDictionary.enumParser(formatStr, params)   
        else:
            # No enum parser just evaluate
            try:
                retStr = formatStr % params
            except TypeError:
                # Evaluation type error
                OutputLog.nlogFormatError("Eval TypeError", formatStr, params)
                retStr = None

        return retStr

    def __addTriageNlogEvent(self, formatStr, params, tsSeconds, tsTicks, coreId):
        """
        Add the event to the triage event lists

        @param formatStr - nlog format string
        @param params - nlog associated parameter tuple
        @param tsSeconds - nlog seconds timestamp
        @param tsTicks - nlog ticks timestamp
        @param coreId - core Id number
        """
        seconds = tsSeconds + (tsTicks / (self.counterFreq * 1.0))
        retMessageList = []
        for triageObject in self.triageObjectList:
            if ("Recovered power-down time:" in formatStr):
                seconds = params[0] + (params[1] / (self.counterFreq * 1.0))
                triageObject.updateTime(seconds)
            else:
                hostMessage = triageObject.addNlogEvent(formatStr, params, seconds, coreId)
                if (hostMessage is not None): retMessageList.append(hostMessage)

        self.triageMessageList.extend(retMessageList)
        return retMessageList

    def xlateEvents(self, events):
        """
        Translate the given NLog events tuples into a list of strings, formatting each as required.

        Based on nlogpost2.py printEvents

        @param events - Chronologically ordered list of nlog event tuples
        @param coreId - Core number associated with the log

        @return - list of strings, list of nlog output strings
        """
        nlogTextEvents = []
        del self.triageMessageList[0:]

        for zone, tsSeconds, tsTicks, eventHeader, params, logName, coreId, in events:
            # Look up the format string
            if (eventHeader is not None):
                lookupKey = eventHeader.getFormatDictionaryKey()
                formatStr = self.__getFormatString(lookupKey, len(params))

                # Base formatted string
                formatStr, params = self.__reformat(formatStr, params)
            else:
                formatStr = "%s"
            
            # Test if the message needs to be triaged
            inlineTriageMsgList = self.__addTriageNlogEvent(formatStr, params, tsSeconds, tsTicks, coreId)

            # try to add enum values
            enumStr = self.__addEnums(formatStr, params)
            if (enumStr is None):
                formatStr = "Translation Error:" + formatStr + str(params)
            else:
                formatStr = enumStr

            # Clean up the string
            if formatStr[:1]=='"' and formatStr[-1:]=='"': formatStr = formatStr[1:-1] # Remove double-quotes from beginning and end.
            if formatStr[-2:]=='\\n': formatStr = formatStr[:-2]                       # Remove (last) trailing newline, if any.

            # Take out any space in logName in order to make the output more predictable
            logName = re.sub(' ','',logName.upper())
            if (coreId is None):
                nlogTextEvents.append( " %25s (%4s) %s" % (self.__strTimestamp(zone, tsSeconds, tsTicks), logName, formatStr) )
            else:
                nlogTextEvents.append( " %25s %4s (%4s) %s" % (self.__strTimestamp(zone, tsSeconds, tsTicks), str(coreId), logName, formatStr) )

            # Add inline triage messages if enabled
            if (self.inlineTriage == True): 
                for triageMessage in inlineTriageMsgList: 
                    nlogTextEvents.append(triageMessage)

        return nlogTextEvents

    def generateHeader(self, counterFreq, coreId = None):
        # Print frequency
        retStr = format("Free Running Timer Frequency: %d\n" % (counterFreq))

        # Print output header
        if (coreId is None):
            retStr += format( " %25s %4s %s\n" % ('Time(H:M:S)               ','(NLog)', 'Event'))
            retStr += format( " %25s %4s %s\n" % ('==========================','======', '====='))
        else:
            retStr += format( " %25s %4s %4s %s\n" % ('Time(H:M:S)               ','Core','(NLog)', 'Event'))
            retStr += format( " %25s %4s %4s %s\n" % ('==========================','====','======', '====='))

        return retStr 

    def markFirstEntry(self, nlogTextEvents):
        # Sort the list
        nlogTextEvents.sort()
        markedList = []

        nlogFirstEntry = []
        for nlogText in nlogTextEvents:
            ### search for first entry per log buffer
            firstTag = ' '

            ### old format without core number
            if re.match(".{27}\((.{4})\)",nlogText):
                m = re.match(".{27}\((.{4})\)",nlogText)
                if (m.group(1).upper() not in nlogFirstEntry):
                    nlogFirstEntry.append(m.group(1).upper())
                    firstTag = '1'

            ### new format with core number
            elif re.match(".{32}\((.{4})\)",nlogText):
                m = re.match(".{32}\((.{4})\)",nlogText)
                if (m.group(1).upper() not in nlogFirstEntry):
                    nlogFirstEntry.append(m.group(1).upper())
                    firstTag = '1'    

            markedList.append(firstTag + nlogText)

        return markedList

    def RegisterTriageObject(self, nlogTriageObj):
        """
        Register an nlog triage object

        @param nlogTraigeObj - Nlog triage object to register
        """
        self.triageObjectList.append(nlogTriageObj)
        self.triageHeader.append(nlogTriageObj.getVersion())

    def RegisterTriageList(self, nlogTriageList):
        """
        Register an nlog triage object

        @param nlogTriageList - Nlog triage object to register
        """
        self.triageObjectList.extend(nlogTriageList)

    def GetTriageText(self):
        """
        Get the triage message list and header generated by the registered nlog triage objects
        """
        retMessageList = []
        for triageObject in self.triageObjectList:
            retMessageList.append("\n\n")
            triageMsgLst = triageObject.checkEvents()
            if (triageMsgLst is not None): retMessageList.extend(triageMsgLst)

        return retMessageList


class TelemetryV2NlogEventParserL2(object):
    """
    Brief:
        Telemetry nlog level 2 bin file parser.  This class will parse the input bin file and 
        generate a list of event tuples

    Class(es):
        EventId_struct,EventTimeStamp_struct

    Method(s):
        __init__(nlogFileName)
        tuple list getEventTupleList()
        int getCoreId()
        int getNlogId()
        string getNlogName()
        int getFrequency()

    Related:
        EventTimeStamp_struct, EventId_struct

    Author(s):
        Randal Eike
    """
    PACKED_DATA = 1
    ALIGNED_512 = 2
    ALIGNED_4K  = 3


    def __init__(self, nlogFileName = None, alignment = PACKED_DATA):
        """
        Constructor

        @param nlogFileName - Path and name of the telemetry level 1 nlog output file
        @param telemetryVersion - Telemetry version number
        """
        self.counterFreq = 200000000.0
        self.nlogFileName = nlogFileName
        self.events = []
        self.core = None
        self.nlogId = 0x7FFFFFFF
        self.nlogName = "UKWN"

        self.nlogBin = None
        self.currentFileOffset = 0
        self.fileSize = 0

        if (alignment == TelemetryV2NlogEventParserL2.PACKED_DATA): self.offsetAdjust = 0
        elif (alignment == TelemetryV2NlogEventParserL2.ALIGNED_512): self.offsetAdjust = 0x200
        elif (alignment == TelemetryV2NlogEventParserL2.ALIGNED_4K): self.offsetAdjust = 0x1000
        else: self.offsetAdjust = 0

        self.triageObjectList = []
        self.triageObjectList.append(pssDebugTraceTriage())
        self.triageObjectList.append(HostTimeMarkerTriage())
        self.triageObjectList.append(padrTriage())


    def setNlogBinFileName(self, nlogFileName):
        self.nlogFileName = nlogFileName

    def __openBinFile(self):
        # open the file
        self.nlogBin = openReadFile(self.nlogFileName)

        if (self.nlogBin is not None):
            # initialize the file pointer
            self.currentFileOffset = 0
            self.fileSize = os.path.getsize(self.nlogFileName)

    def __closeBinFile(self):
        if (self.nlogBin is not None):
            self.nlogBin.close()

        self.currentFileOffset = 0
        self.fileSize = 0

    def __adjustCurrentOffset(self, size):
        if (self.offsetAdjust > 0):
            blockCount = (self.currentFileOffset + size + self.offsetAdjust - 1) / self.offsetAdjust
            newOffset = blockCount * self.offsetAdjust
        else: 
            newOffset = self.currentFileOffset + size
        return newOffset

    def __readTelemetryNlogHeaderAndPool(self):
        """
        Open the nlog input file and parse the header and pool data.  Modified from nlogpost2.py extractEvents().

        @return list - nlog dword value list in proper order to parse or empty list if the file read failed
        """

        if (self.nlogBin is not None):
            # read the header
            self.nlogBin.seek(self.currentFileOffset)
            nlogSelect = NlogSelect_union(self.nlogBin, ctypes.sizeof(NlogSelect_union)).getStruct()

            # Read data
            self.counterFreq = nlogSelect.getTicksPerSecond()
            self.nlogName = nlogSelect.getLogName()
            self.nlogId = nlogSelect.getLogId()
            self.core = nlogSelect.getCoreSelected()
            byteSize = nlogSelect.getLogByteSize()

            # Move to the start of the nlog data
            self.currentFileOffset = self.__adjustCurrentOffset(ctypes.sizeof(nlogSelect))
            self.nlogBin.seek(self.currentFileOffset)

            # Read the nlog buffer and put it into the order we need
            myPool = NLogPoolArray( self.nlogBin.read(byteSize) )
            myPool.reverse()

            # Adjust the current offset to the next data section
            self.currentFileOffset = self.__adjustCurrentOffset(byteSize)
        else:
            myPool = []

        return myPool

    def getEventTupleList(self):
        """
        Read and translate the input nlog bin file into an ordered event tuple list.  Modified from nlogpost2.py extractEvents().

        @return list - Chronologically ordered list of nlog events tuples (zone number 0 | 1, time stamp MSW, time stamp LSW, eventHeader ID structure, param tuple, nlog name string)
        """
        # Read the Nlog pool and convert to events
        eventList = []
        self.__openBinFile()

        while (self.currentFileOffset < self.fileSize):
            # Read the current pool
            myPool = self.__readTelemetryNlogHeaderAndPool()

            # Convert to events
            eventGenerator = NlogEventPoolParser(self.nlogName, self.core)
            eventList.extend(eventGenerator.getEventTupleList(myPool))

        self.__closeBinFile()
        return eventList

    def xlateToText(self, eventList: list = None, nlogFormats = None, enumFile=None):
        if (len(eventList) > 0):
            xlate = EventTupleTranslate(self.counterFreq, nlogFormats, enumFile)

            # Register any triage objects          
            xlate.RegisterTriageList(self.triageObjectList)

            # Generate the nlog strings and header
            nlogTextList = xlate.xlateEvents(eventList)
            nlogTextList = xlate.markFirstEntry(nlogTextList)
            headerText = xlate.generateHeader(self.counterFreq, self.core)

            # Get the triage objects to report status text
            triageText = xlate.GetTriageText()
            return nlogTextList, headerText, triageText
        else:
            return None, None, None


    def WriteNlogStream(self, outputStream, headerText = None, nlogTextList = None):
        """
        Output Standard header, Nlog header and nlog text to the specified output stream

        @param outputStream - Output stream object to write the data to
        @param headerText   - Nlog Header text or None to skip header output
        @param nlogTextList - Nlog output string list or None
        """
        outputStream.write(format("Nlog output from telemetry_nlog parsing Version: %4.2f\n" % (NLOG_PARSE_VERSION)))
        if (headerText is not None):
            outputStream.write(headerText)
            outputStream.write("\n")
        if (nlogTextList is not None):
            for nlogStr in nlogTextList:
                outputStream.write(unidecode(nlogStr))
                outputStream.write("\n")
        else:
            outputStream.write("No input nlog text\n")

    def WriteTriageStream(self, outputStream, triageTextList = None):
        """
        Output Standard header, Nlog header and nlog text to the specified output stream

        @param outputStream - Output stream object to write the data to
        @param triageTextList - Triage output string list or None
        """
        outputStream.write(format("Triage output from telemetry_nlog parsing Version: %4.2f\n" % (NLOG_PARSE_VERSION)))
        if (triageTextList is not None):
            for triageStr in triageTextList:
                outputStream.write(triageStr)
                outputStream.write("\n")
        else:
            outputStream.write("No triage text\n")
                

    def XlateAndOutputNlog(self, formatsFile = None, outputStream = None, nlogFileName = None, triageStream = None):
        """
        Parse the nlog file and output the data

        @param formatsFile  - Path/File name of the Nlog_formats.py file to use for format translation
        @param outputStream - Stream object to output translated text to
        @param nlogFileName - Path/File name of the telemetry Nlog object to parse and translate
        @param triageStream - Stream object to output trage data or None to throw it away

        @return bool - True = parse and translation worked.  False = error
        """
        if (nlogFileName is not None): self.nlogFileName = nlogFileName

        if (self.nlogFileName is not None):
            # Open the bin file and convert to event list
            self.__openBinFile()
            eventList = self.getEventTupleList()
            self.__closeBinFile()

            # Test if the event list generation worked
            if (len(eventList) > 0):
                # Convert the event list to text strings
                nlogTextList, headerText, triageText = self.xlateToText(eventList, formatsFile)
                status = True
            else:
                status = False

            # Output to the stream
            if (outputStream is not None):
                self.WriteNlogStream(outputStream, headerText, nlogTextList)
            if (triageStream is not None):
                self.WriteTriageStream(triageStream, triageText)
        else:
            # No file name input
            OutputLog.Error("No input file name specified!!")
            status = False

        return status

    def XlateAndOutputMultipleNlog(self, nlogFileNameList = None, formatsFile = None, outputStream = None, triageStream = None):
        """
        Parse the nlog file and output the data

        @param nlogFileNameList - List of Path/File names of telemetry Nlog objects to parse and translate
        @param formatsFile  - Path/File name of the Nlog_formats.py file to use for format translation
        @param outputStream - Stream object to output translated text to
        @param triageStream - Stream object to output trage data or None to throw it away

        @return bool - True = parse and translation worked.  False = error
        """
        if (nlogFileNameList is not None):
            eventList = []
            for nlogFileName in nlogFileNameList:
                # Open the bin file and convert to event list
                self.nlogFileName = nlogFileName
                eventList.extend(self.getEventTupleList())

            # Test if the event list generation worked
            if (len(eventList) > 0):
                # Convert the event list to text strings
                nlogTextList, headerText, triageText = self.xlateToText(eventList=eventList, nlogFormats=formatsFile, enumFile=None)
                status = True
            else:
                nlogTextList = None
                headerText = None
                triageText = None
                status = False

            # Output to the stream
            if (outputStream is not None):
                self.WriteNlogStream(outputStream, headerText, nlogTextList)
            if (triageStream is not None):
                self.WriteTriageStream(triageStream, triageText)

        else:
            # No file name input list
            status = False

        return status





