#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors:Joseph Tarango, Randal Eike, Daniel Garces
# *****************************************************************************/
"""
Brief:
    telemetryHostTime.py - Current timestamp from the device

Description:
    Timestamp structure from the device.  Timestamp could be UTC time from the host + power on time or just power on time

Classes:
    telemetryHostTime.
"""

import time
from ctypes import *
from array import *
from src.software.parse.nlogParser.telemetryutil.telemetry_util import openWriteFile

class hostTimeFlags(Structure):
    """
    Brief:
        hostTimeFlags() - Flags data used to determine how to interpret the timestamp value 

    Description:

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Randal Eike
    """

    _fields_ = [
                ("origin",                c_uint32, 1),     # Origin of the timestamp value, 1 = UTC time from host + power on milliseconds, 0 = power on milliseconds
                ("reserved",              c_uint32, 31),    # Reserved for future use
               ]

    def __init__(self):
        self.origin = 0
        self.reserved = 0

    def loadData(self, dataBuffer, offset = 0):
        shift = 8
        temp = c_uint32()
        temp = dataBuffer[offset]
        for index in range(1, sizeof(c_uint32)):
            temp |= (dataBuffer[offset+index] << shift)
            shift += 8

        self.origin = (temp & 0x01)
        self.reserved = (temp >> 1)

    def isHostTimeStamp(self):
        if (self.origin == 0):
            return False
        else:
            return True


class telemetryHostTimeV1_0(LittleEndianStructure):
    """
    Brief:
        telemetryHostTimeV1_0() - Telemetry host timestamp data object parser

    Description:

    Class(es):
        None

    Method(s):
        None

    Related: -

    Author(s):
        Randal Eike
    """
    _pack_ = 1
    _fields_ = [
                ("timestamp",                c_uint64),                 # byte 07-00: Time in milliseconds
                ("flags",                    hostTimeFlags),            # byte 11-08: Status flags
               ]

    def __init__(self):
        self.timestamp = 0

    def loadData(self, dataBuffer, offset = 0):
        shift = 8
        self.timestamp = dataBuffer[offset]
        for index in range(1, sizeof(c_uint64)):
            self.timestamp |= (dataBuffer[offset+index] << shift)
            shift += 8

        self.flags.loadData(dataBuffer, sizeof(c_uint64))

    def __str__(self):
        # convert to seconds and milliseconds
        hostTimeSec, hostTimeMSec =  divmod(self.timestamp, 1000)

        # Determine the base value source
        if (self.flags.isHostTimeStamp()):
            # Host UTC time base
            tmStruct = time.gmtime(hostTimeSec)
            formatString = "Host time marker + Power on time: %s.%03u %s\n"
            formatTuple = (time.asctime(tmStruct), hostTimeMSec, "UTC")
        else:
            # Internal time counter base
            minutes, seconds = divmod(hostTimeSec, 60)
            hours, minutes  = divmod(minutes, 60)
            formatString = "Power on time: %d:%02d:%02d.%03u\n"
            formatTuple = (hours, minutes % 60, seconds, hostTimeMSec)

        return format(formatString % formatTuple)

    def tofile(self, fileName = None):
        if (fileName is not None):
            outputFile = openWriteFile(fileName, text = True)
            if (outputFile is not None):
                outputFile.write(str(self))
                outputFile.close()
            else:
                print(str(self))
        else:
            print(str(self))




