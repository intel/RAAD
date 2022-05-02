#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors:Joseph Tarango
# *****************************************************************************/
"""
Brief:
    hostTimeMarkerTriage.py - Parse the host time marker message

Description:
    Host timestamp marker triage

Classes:
    HostTimeMarkerTriage.
"""

import time
from src.software.parse.nlogParser.nlog_triage.nlogTriageBase import nlogTriageBase

# Version Table
# Version 1.0 : Initial release
TOOL_VERSION = 1.0


class HostTimeMarkerTriage(nlogTriageBase):
    localTimeZone = None

    @staticmethod
    def GetNlogTimestamp(tsSeconds, flag):
        mins,secs = divmod(tsSeconds,60)
        hrs,mins  = divmod(mins,60)
        return "%9d:%02d:%011.8f%s" % (hrs, mins, secs, flag)

    @staticmethod
    def ConvertToWallClock(utcHostTimeMs, utcHostTimeSec, powerOnTimeMs):
        # Convert the parameters to times
        powerOnSeconds = powerOnTimeMs / 1000.0

        # Determine if the local timezone where the log was generated is set
        if (HostTimeMarkerTriage.localTimeZone is None):
            tmStruct = time.gmtime(utcHostTimeSec)
            timeZoneName = "UTC"
        else:
            tmStruct = time.localtime(utcHostTimeSec)
            timeZoneName = time.tzname[tmStruct.tm_isdst]

        # Construct the string
        powerOnTimeStamp = HostTimeMarkerTriage.GetNlogTimestamp(powerOnSeconds, "")
        return format("Host time marker: %s %s, Power On time: %s" % (time.asctime(tmStruct), timeZoneName, powerOnTimeStamp))

    def __init__(self):
        super(HostTimeMarkerTriage, self).__init__('host_time', TOOL_VERSION)

    def addNlogEvent(self, formatStr, params, tsSeconds, coreId):
        """
        Determine if this a pss debug trace nlog entry and record the state transition 
        in the list if it is

        @param formatStr - nlog format string
        @param params - nlog associated parameter tuple
        @param tsSeconds - nlog timestamp in seconds (floating point value)
        @param coreId - Core number for the NLOG
        """
        self.hostMessage = None

        if (("Nvme Host time since 12:00am, January 1, 1970" in formatStr) and (len(params) >= 6)):
            utcHostTimeParamMs = (int(list(params)[0]) << 32) + int(list(params)[1])
            utcHostTimeParmSec = (int(list(params)[2]) << 32) + int(list(params)[3])
            powerOnTimeMs = (int(list(params)[4]) << 32) + int(list(params)[5])
            timeMessage = HostTimeMarkerTriage.ConvertToWallClock(utcHostTimeParamMs, utcHostTimeParmSec, powerOnTimeMs)

            self._message(nlogTriageBase.information, timeMessage)

        return self.hostMessage
