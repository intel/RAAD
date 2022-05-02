#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Randal Eike, Joseph Tarango
# *****************************************************************************/
"""
Brief:
    intelVUTelemetryReason.py - Intel VU reason code structure

Description:
    -

Classes:
    Enter GetHeaders("intelVUTelemetryReason.py") to display Class listings.
"""
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import sys

from ctypes import *
from src.software.parse.telemetry_util import openWriteFile


class intelTelemetryReasonCode(Structure):
    """
    Brief:
        intelTelemetryReasonCode() - Reason code data

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
        ("reasonCode", c_uint32, 16),  # Reason code
        ("controllerInitiated", c_uint32, 1),  # Controller initiated flag 0 = host initiated telemetry log, 1 = controller initiated telemetry log
        ("excursionDetected", c_uint32, 1),  # Excursion detected, 1 = excursion level controller inititated error detected, 0 = no excursion level error detected
        ("warningDetected", c_uint32, 1),  # Warning detected, 1 = warning level controller inititated error detected, 0 = no warning level error detected
        ("errorDetected", c_uint32, 1),  # Error detected, 1 = error level controller inititated error detected, 0 = no error level error detected
        ("reserved", c_uint32, 12),  # Reserved for future use
    ]

    def tostr(self):
        retString = ""
        retString += f"reasonCode           : {self.reasonCode}\n"
        retString += f"controllerInitiated  : {self.controllerInitiated}\n"
        retString += f"excursionDetected    : {self.excursionDetected}\n"
        retString += f"warningDetected      : {self.warningDetected}\n"
        retString += f"errorDetected        : {self.errorDetected}\n"

    def getStr(self):
        return self.tostr()

    def tofile(self, filename):
        reasonText = openWriteFile(filename, True)
        if (reasonText is not None):
            reasonText.write(self.tostr())
            reasonText.close()


class intelTelemetryReasonV1_0_Struct(LittleEndianStructure):
    """
    Brief:
        intelTelemetryReasonV1_0_Struct() - Definition of the NVMe Reason data for intel get telemetry log page commands

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
        ("majorVersion", c_uint16),  # byte 01-00: Major version
        ("minorVersion", c_uint16),  # byte 03-02: Minor version
        ("reason", intelTelemetryReasonCode),  # byte 07-04: Reason field, reason code
        ("failureModeString", c_uint8 * 20),  # byte 27-08: Failure mode string
        ("fwRevision", c_uint8 * 12),  # byte 39-28: Main FW revision string
        ("blRevision", c_uint8 * 12),  # byte 51-40: BL FW revision string
        ("serialNumber", c_uint8 * 20),  # byte 71-52: Drive serial number
        ("intelReserved", c_uint8 * 16),  # byte 87-72: Reserved for future use
        ("aplReserved", c_uint8 * 40),  # byte 127-88: Reserved for dual port APL usage
    ]

    def tostr(self):
        if (self.majorVersion > 0):
            retString = ""
            retString += "    majorVersion               : %u\n" % self.majorVersion
            retString += "    minorVersion               : %u\n" % self.minorVersion
            retString += "    reason.reasonCode          : %u\n" % self.reason.reasonCode
            retString += "    reason.controllerInitiated : %u\n" % self.reason.controllerInitiated
            retString += "    reason.excursionDetected   : %u\n" % self.reason.excursionDetected
            retString += "    reason.warningDetected     : %u\n" % self.reason.warningDetected
            retString += "    reason.errorDetected       : %u\n" % self.reason.errorDetected
            retString += "    failureModeString          : "
            for charIndex in range(0, 20):
                retString += format("%c" % (self.failureModeString[charIndex]))
            retString += "\n"
            retString += "    fwRevision         : "
            for charIndex in range(0, 12):
                retString += format("%c" % (self.fwRevision[charIndex]))
            retString += "\n"
            retString += "    blRevision         : "
            for charIndex in range(0, 12):
                retString += format("%c" % (self.blRevision[charIndex]))
            retString += "\n"
            retString += "    serialNumber       : "
            for charIndex in range(0, 20):
                retString += format("%c" % (self.serialNumber[charIndex]))
            retString += "\n"
            retString += "    intelReserved      : "
            for charIndex in range(0, 16):
                retString += format("%c" % (self.intelReserved[charIndex]))
            retString += "\n"
            retString += "    aplReserved        : "
            for charIndex in range(0, 40):
                retString += format("%c" % (self.aplReserved[charIndex]))
            retString += "\n"
        else:
            retString = "Version 0.0\n"
        return retString

    def getStr(self):
        return self.tostr()

    def validate(self, hiLog):
        if ((self.majorVersion != 1)):
            errorString = format("ERROR! Reason Version: %u.%02u, Expected 1.0\n" % (self.majorVersion, self.minorVersion))
            print(errorString)
            return False
        if (hiLog and (1 == self.reason.controllerInitiated)):
            print("ERROR! Reason controllerInitiated flag true in host initiated log.\n")
            return False
        return True

    def tofile(self, filename):
        reasonText = openWriteFile(filename, True)
        if (reasonText is not None):
            reasonText.write(self.tostr())
            reasonText.close()

    def getFamilyID(self):
        retString = None
        retString += format("%c%c" % ((self.fwRevision[0] / 0x100), (self.fwRevision[0] & 0x0FF)))
        return retString

    def getSerialNumber(self):
        if (self.majorVersion > 0):
            retString = ""
            for charIndex in range(0, 20):
                if (0x20 != self.serialNumber[charIndex]):
                    retString += format("%c" % (self.serialNumber[charIndex]))
        else:
            retString = "NoSerialNumber1.x"
        return retString

    def getVersion(self):
        return self.majorVersion + (self.minorVersion / 100)

    def getMajorVersion(self):
        return self.majorVersion

    def getMinorVersion(self):
        return self.minorVersion

    def getReasonCode(self):
        return self.reason.reasonCode

    def isControllerInitiated(self):
        if (0 != self.reason.controllerInitiated):
            return True
        else:
            return False

    def excursionDetected(self):
        if (0 != self.reason.excursionDetected):
            return True
        else:
            return False

    def warningDetected(self):
        if (0 != self.reason.warningDetected):
            return True
        else:
            return False

    def errorDetected(self):
        if (0 != self.reason.errorDetected):
            return True
        else:
            return False
