#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Randal Eike, Joseph Tarango
# *****************************************************************************/
"""
Brief:
    headerTelemetry.py - Holds special parsers for Telemetry Log Page Header Data

Description:
    -

Classes:
    Enter GetHeaders("parsers\\nvme\\headerTelemetry.py") to display Class listings.
"""
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import sys

from ctypes import *
from src.software.parse.telemetry_util import MAX_BLOCK_SIZE
from src.software.parse.telemetry_util import GetTruncatedDataBuffer
from src.software.parse.output_log import OutputLog
from src.software.parse.intelVUTelemetryReason import intelTelemetryReasonV1_0_Struct


class NvmeHostInitiatedLogPageHeader_struct(Structure):
    """
    Brief:
        HostInitiatedLogPageHeader_struct() - Definition of the NVMe Get Host Initiated Log Page header structure for Intel drives.

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
        ("logIdentifier", c_uint8),  # byte 00: Log identifier = 0x07
        ("reserved", c_uint8 * 4),  # byte 01-04: reserved in NVMe 1.3 specification
        ("IEEE_OUI_id", c_uint8 * 3),  # byte 05-07:Contains the Organization Unique Identifier (OUI) for the controller vendor.
        ("dataArea1EndBlock", c_uint16),  # byte 08-09:Last block of data area 1
        ("dataArea2EndBlock", c_uint16),  # byte 10-11:Last block of data area 2
        ("dataArea3EndBlock", c_uint16),  # byte 12-13:Last block of data area 3
        ("reserved2", c_uint8 * 368),  # byte 14-381: reserved in NVMe 1.3 specification
        ("ctrlInitiatedDataAvail", c_uint8),  # byte 382: Telemetry Controller Initiated Data available
        ("ctrlInitiatedGeneration", c_uint8),  # byte 383: Telemetry Controller Initiated Data generation
        ("reasonId", intelTelemetryReasonV1_0_Struct),  # byte 384-511: Vendor unique reason identification data
        # End More Intel
    ]

    def IsHostInitiated(self):
        return True

    def tostr(self):
        retString = ""
        retString += "Name        : NvmeHostInitiatedLogPageHeader\n"
        retString += "serialNumber         : %s\n" % self.getSerialNumber()
        retString += "logIdentifier         : %d\n" % self.logIdentifier
        for i in range(4):
            retString += "reserved[%i]        : %d\n" % (i, self.reserved[i])
        for i in range(3):
            retString += "IEE_OUI_id[%i]        : %d\n" % (i, self.IEEE_OUI_id[i])
        retString += "dataArea1EndBlock         : %d\n" % self.dataArea1EndBlock
        retString += "dataArea2EndBlock         : %d\n" % self.dataArea2EndBlock
        retString += "dataArea3EndBlock         : %d\n" % self.dataArea3EndBlock
        for i in range(368):
            retString += "reserved2[%i]        : %d\n" % (i, self.reserved2[i])
        retString += "ctrlInitiatedDataAvail         : %d\n" % self.ctrlInitiatedDataAvail
        retString += "ctrlInitiatedGeneration         : %d\n" % self.ctrlInitiatedGeneration
        retString += "reasonId         : %s" % "\n" + self.reasonId.tostr()
        return retString

    def getStr(self):
        return self.tostr()

    def validate(self):
        valid = True
        if (7 != self.logIdentifier):
            OutputLog.Error("Log identifier = " + str(self.logIdentifier) + ", Expected 7")
            valid = False

        if (self.dataArea2EndBlock < self.dataArea1EndBlock):
            OutputLog.Error("Data Area 2 last block (" + str(self.dataArea2EndBlock) + ") less than Data 1 last block (" + str(self.dataArea1EndBlock) + ")")
            valid = False

        if (self.dataArea3EndBlock < self.dataArea2EndBlock):
            OutputLog.Error("Data Area 3 last block (" + str(self.dataArea3EndBlock) + ") less than Data 2 last block (" + str(self.dataArea2EndBlock) + ")")
            valid = False

        for x in range(0, 3):
            if (self.reserved[x] != 0):
                OutputLog.Warning("Reserved field1[" + str(x) + "] != 0")

        for x in range(0, 367):
            if (self.reserved2[x] != 0):
                OutputLog.Warning("Reserved field2[" + str(x) + "] != 0")

        if (self.reasonId.getMajorVersion() != 0):
            if (False == self.reasonId.validate(True)):
                valid = False

        return valid

    def getSerialNumber(self):
        return self.reasonId.getSerialNumber()

    def getLastBlock(self):
        dataAreaList = []
        lastBlock = max(self.dataArea1EndBlock, self.dataArea2EndBlock, self.dataArea3EndBlock)
        lastBlock += 1
        if (0 != self.dataArea1EndBlock):
            dataAreaList.append(self.dataArea1EndBlock + 1)
            if (self.dataArea2EndBlock > self.dataArea1EndBlock): dataAreaList.append(self.dataArea2EndBlock + 1)
            if (self.dataArea3EndBlock > self.dataArea2EndBlock): dataAreaList.append(self.dataArea3EndBlock + 1)
        elif (0 != self.dataArea2EndBlock):
            dataAreaList.append(self.dataArea2EndBlock + 1)
            if (self.dataArea3EndBlock > self.dataArea2EndBlock): dataAreaList.append(self.dataArea3EndBlock + 1)
        else:
            dataAreaList.append(self.dataArea3EndBlock + 1)
        return lastBlock, dataAreaList

    def getDataAreaLastBlock(self, dataArea):
        if (1 == dataArea):
            return self.dataArea1EndBlock + 1
        elif (2 == dataArea):
            return self.dataArea2EndBlock + 1
        elif (3 == dataArea):
            return self.dataArea3EndBlock + 1
        else:
            return self.dataArea3EndBlock + 1

    def getCIdata(self):
        return self.ctrlInitiatedDataAvail, self.ctrlInitiatedGeneration

    def IsVersion1(self):
        if (self.reasonId.getMajorVersion() == 0):
            return True
        else:
            return False

    def getVersionInfo(self):
        return self.reasonId.getMajorVersion(), self.reasonId.getMinorVersion()

    def tofile(self, filename):
        self.reasonId.tofile(filename)


class SataHostInitiatedLogPageHeader_struct(Structure):
    """
    Brief:
        SataHostInitiatedLogPageHeader_struct() - Definition of the SATA Get Host Initiated Log Page header structure for Intel drives.

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
        ("logIdentifier", c_uint8),  # byte 00: Log identifier = 0x07
        ("reserved", c_uint8 * 4),  # byte 01-04: reserved in NVMe 1.3 specification
        ("IEEE_OUI_id", c_uint8 * 3),  # byte 05-07:Contains the Organization Unique Identifier (OUI) for the controller vendor.
        ("dataArea1EndBlock", c_uint16),  # byte 08-09:Last block of data area 1
        ("dataArea2EndBlock", c_uint16),  # byte 10-11:Last block of data area 2
        ("dataArea3EndBlock", c_uint16),  # byte 12-13:Last block of data area 3
        ("reserved2", c_uint8 * 368),  # byte 14-381: reserved in NVMe 1.3 specification
        ("ctrlInitiatedDataAvail", c_uint8),  # byte 382: Telemetry Controller Initiated Data available
        ("ctrlInitiatedGeneration", c_uint8),  # byte 383: Telemetry Controller Initiated Data generation
        ("reasonId", intelTelemetryReasonV1_0_Struct),  # byte 384-511: Vendor unique reason identification data
        # End More Intel
    ]

    def IsHostInitiated(self):
        return True

    def tostr(self):
        retString = ""
        retString += "Name        : SataHostInitiatedLogPageHeader\n"
        retString += "serialNumber         : %s\n" % self.getSerialNumber()
        retString += "logIdentifier         : %d\n" % self.logIdentifier
        for i in range(4):
            retString += "reserved[%i]        : %d\n" % (i, self.reserved[i])
        for i in range(3):
            retString += "IEE_OUI_id[%i]        : %d\n" % (i, self.IEEE_OUI_id[i])
        retString += "dataArea1EndBlock         : %d\n" % self.dataArea1EndBlock
        retString += "dataArea2EndBlock         : %d\n" % self.dataArea2EndBlock
        retString += "dataArea3EndBlock         : %d\n" % self.dataArea3EndBlock
        for i in range(368):
            retString += "reserved2[%i]        : %d\n" % (i, self.reserved2[i])
        retString += "ctrlInitiatedDataAvail         : %d\n" % self.ctrlInitiatedDataAvail
        retString += "ctrlInitiatedGeneration         : %d\n" % self.ctrlInitiatedGeneration
        retString += "reasonId         : %s" % "\n" + self.reasonId.tostr()
        return retString

    def getStr(self):
        return self.tostr()

    def validate(self):
        valid = True
        if (0x24 != self.logIdentifier):
            OutputLog.Error(format("Log identifier = 0x%x, Expected 0x24" % (self.logIdentifier)))
            valid = False

        if (self.dataArea2EndBlock < self.dataArea1EndBlock):
            OutputLog.Error("Data Area 2 last block (" + str(self.dataArea2EndBlock) + ") less than Data 1 last block (" + str(self.dataArea1EndBlock) + ")")
            valid = False

        if (self.dataArea3EndBlock < self.dataArea2EndBlock):
            OutputLog.Error("Data Area 3 last block (" + str(self.dataArea3EndBlock) + ") less than Data 2 last block (" + str(self.dataArea2EndBlock) + ")")
            valid = False

        for x in range(0, 3):
            if (self.reserved[x] != 0):
                OutputLog.Warning("Reserved field1[" + str(x) + "] != 0")

        for x in range(0, 367):
            if (self.reserved2[x] != 0):
                OutputLog.Warning("Reserved field2[" + str(x) + "] != 0")

        if (self.reasonId.getMajorVersion() != 0):
            if (False == self.reasonId.validate(True)):
                valid = False

        return valid

    def getSerialNumber(self):
        return self.reasonId.getSerialNumber()

    def getLastBlock(self):
        dataAreaList = []
        lastBlock = max(self.dataArea1EndBlock, self.dataArea2EndBlock, self.dataArea3EndBlock)
        lastBlock += 1
        if (0 != self.dataArea1EndBlock):
            dataAreaList.append(self.dataArea1EndBlock + 1)
            if (self.dataArea2EndBlock > self.dataArea1EndBlock): dataAreaList.append(self.dataArea2EndBlock + 1)
            if (self.dataArea3EndBlock > self.dataArea2EndBlock): dataAreaList.append(self.dataArea3EndBlock + 1)
        elif (0 != self.dataArea2EndBlock):
            dataAreaList.append(self.dataArea2EndBlock + 1)
            if (self.dataArea3EndBlock > self.dataArea2EndBlock): dataAreaList.append(self.dataArea3EndBlock + 1)
        else:
            dataAreaList.append(self.dataArea3EndBlock + 1)
        return lastBlock, dataAreaList

    def getDataAreaLastBlock(self, dataArea):
        if (1 == dataArea):
            return self.dataArea1EndBlock + 1
        elif (2 == dataArea):
            return self.dataArea2EndBlock + 1
        elif (3 == dataArea):
            return self.dataArea3EndBlock + 1
        else:
            return self.dataArea3EndBlock + 1

    def getCIdata(self):
        return self.ctrlInitiatedDataAvail, self.ctrlInitiatedGeneration

    def IsVersion1(self):
        if (self.reasonId.getMajorVersion() == 0):
            return True
        else:
            return False

    def tofile(self, filename):
        self.reasonId.tofile(filename)


class NvmeControllerInitiatedLogPageHeader_struct(Structure):
    """
    Brief:
        ControllerInitiatedLogPageHeader_struct() - Definition of the NVMe Get Controller Initiated Log Page header structure for Intel drives.

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
        ("logIdentifier", c_uint8),  # byte 00: Log identifier = 0x08
        ("reserved", c_uint8 * 4),  # byte 01-04: reserved in NVMe 1.3 specification
        ("IEEE_OUI_id", c_uint8 * 3),  # byte 05-07:Contains the Organization Unique Identifier (OUI) for the controller vendor.
        ("dataArea1EndBlock", c_uint16),  # byte 08-09:Last block of data area 1
        ("dataArea2EndBlock", c_uint16),  # byte 10-11:Last block of data area 2
        ("dataArea3EndBlock", c_uint16),  # byte 12-13:Last block of data area 3
        ("reserved2", c_uint8 * 368),  # byte 14-381: reserved in NVMe 1.3 specification
        ("ctrlInitiatedDataAvail", c_uint8),  # byte 382: Telemetry Controller Initiated Data available
        ("ctrlInitiatedGeneration", c_uint8),  # byte 383: Telemetry Controller Initiated Data generation
        ("reasonId", intelTelemetryReasonV1_0_Struct),  # byte 384-511: Vendor unique reason identification data
        # End More Intel
    ]

    def IsHostInitiated(self):
        return False

    def tostr(self):
        retString = ""
        retString += "Name        : NvmeControllerInitiatedLogPageHeader\n"
        retString += "serialNumber         : %s\n" % self.getSerialNumber()
        retString += "logIdentifier         : %d\n" % self.logIdentifier
        for i in range(4):
            retString += "reserved[%i]        : %d\n" % (i, self.reserved[i])
        for i in range(3):
            retString += "IEE_OUI_id[%i]        : %d\n" % (i, self.IEEE_OUI_id[i])
        retString += "dataArea1EndBlock         : %d\n" % self.dataArea1EndBlock
        retString += "dataArea2EndBlock         : %d\n" % self.dataArea2EndBlock
        retString += "dataArea3EndBlock         : %d\n" % self.dataArea3EndBlock
        for i in range(368):
            retString += "reserved2[%i]        : %d\n" % (i, self.reserved2[i])
        retString += "ctrlInitiatedDataAvail         : %d\n" % self.ctrlInitiatedDataAvail
        retString += "ctrlInitiatedGeneration         : %d\n" % self.ctrlInitiatedGeneration
        retString += "reasonId         : %s" % "\n" + self.reasonId.tostr()
        return retString

    def getStr(self):
        return self.tostr()

    def validate(self):
        valid = True
        if (8 != self.logIdentifier):
            OutputLog.Error("Log identifier = " + str(self.logIdentifier) + ", Expected 8")
            valid = False

        if (self.dataArea2EndBlock < self.dataArea1EndBlock):
            OutputLog.Error("Data Area 2 last block (" + str(self.dataArea2EndBlock) + ") less than Data 1 last block (" + str(self.dataArea1EndBlock) + ")")
            valid = False

        if (self.dataArea3EndBlock < self.dataArea2EndBlock):
            OutputLog.Error("Data Area 3 last block (" + str(self.dataArea3EndBlock) + ") less than Data 2 last block (" + str(self.dataArea2EndBlock) + ")")
            valid = False

        for x in range(0, 3):
            if (self.reserved[x] != 0):
                OutputLog.Warning("Reserved field1[" + str(x) + "] != 0")

        for x in range(0, 367):
            if (self.reserved2[x] != 0):
                OutputLog.Warning("Reserved field2[" + str(x) + "] != 0")

        if (self.reasonId.getMajorVersion() != 0):
            if (False == self.reasonId.validate(False)):
                valid = False

        return valid

    def getLastBlock(self):
        dataAreaList = []
        lastBlock = max(self.dataArea1EndBlock, self.dataArea2EndBlock, self.dataArea3EndBlock)
        lastBlock += 1
        if (0 != self.dataArea1EndBlock):
            dataAreaList.append(self.dataArea1EndBlock + 1)
            if (self.dataArea2EndBlock > self.dataArea1EndBlock): dataAreaList.append(self.dataArea2EndBlock + 1)
            if (self.dataArea3EndBlock > self.dataArea2EndBlock): dataAreaList.append(self.dataArea3EndBlock + 1)
        elif (0 != self.dataArea2EndBlock):
            dataAreaList.append(self.dataArea2EndBlock + 1)
            if (self.dataArea3EndBlock > self.dataArea2EndBlock): dataAreaList.append(self.dataArea3EndBlock + 1)
        else:
            dataAreaList.append(self.dataArea3EndBlock + 1)
        return lastBlock, dataAreaList

    def getDataAreaLastBlock(self, dataArea):
        if (1 == dataArea):
            return self.dataArea1EndBlock + 1
        elif (2 == dataArea):
            return self.dataArea2EndBlock + 1
        elif (3 == dataArea):
            return self.dataArea3EndBlock + 1
        else:
            return self.dataArea3EndBlock + 1

    def getSerialNumber(self):
        return self.reasonId.getSerialNumber()

    def getCIdata(self):
        return self.ctrlInitiatedDataAvail, self.ctrlInitiatedGeneration

    def IsVersion1(self):
        if (self.reasonId.getMajorVersion() == 0):
            return True
        else:
            return False

    def tofile(self, filename):
        self.reasonId.tofile(filename)


class SataControllerInitiatedLogPageHeader_struct(Structure):
    """
    Brief:
        SataControllerInitiatedLogPageHeader_struct() - Definition of the SATA Get Controller Initiated Log Page header structure for Intel drives.

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
        ("logIdentifier", c_uint8),  # byte 00: Log identifier = 0x08
        ("reserved", c_uint8 * 4),  # byte 01-04: reserved in NVMe 1.3 specification
        ("IEEE_OUI_id", c_uint8 * 3),  # byte 05-07:Contains the Organization Unique Identifier (OUI) for the controller vendor.
        ("dataArea1EndBlock", c_uint16),  # byte 08-09:Last block of data area 1
        ("dataArea2EndBlock", c_uint16),  # byte 10-11:Last block of data area 2
        ("dataArea3EndBlock", c_uint16),  # byte 12-13:Last block of data area 3
        ("reserved2", c_uint8 * 368),  # byte 14-381: reserved in NVMe 1.3 specification
        ("ctrlInitiatedDataAvail", c_uint8),  # byte 382: Telemetry Controller Initiated Data available
        ("ctrlInitiatedGeneration", c_uint8),  # byte 383: Telemetry Controller Initiated Data generation
        ("reasonId", intelTelemetryReasonV1_0_Struct),  # byte 384-511: Vendor unique reason identification data
        # End More Intel
    ]

    def IsHostInitiated(self):
        return False

    def tostr(self):
        retString = ""
        retString += "Name        : SataControllerInitiatedLogPageHeader\n"
        retString += "serialNumber         : %s\n" % self.getSerialNumber()
        retString += "logIdentifier         : %d\n" % self.logIdentifier
        for i in range(4):
            retString += "reserved[%i]        : %d\n" % (i, self.reserved[i])
        for i in range(3):
            retString += "IEE_OUI_id[%i]        : %d\n" % (i, self.IEEE_OUI_id[i])
        retString += "dataArea1EndBlock         : %d\n" % self.dataArea1EndBlock
        retString += "dataArea2EndBlock         : %d\n" % self.dataArea2EndBlock
        retString += "dataArea3EndBlock         : %d\n" % self.dataArea3EndBlock
        for i in range(368):
            retString += "reserved2[%i]        : %d\n" % (i, self.reserved2[i])
        retString += "ctrlInitiatedDataAvail         : %d\n" % self.ctrlInitiatedDataAvail
        retString += "ctrlInitiatedGeneration         : %d\n" % self.ctrlInitiatedGeneration
        retString += "reasonId         : %s" % "\n" + self.reasonId.tostr()
        return retString

    def getStr(self):
        return self.tostr()

    def validate(self):
        valid = True
        if (0x25 != self.logIdentifier):
            OutputLog.Error(format("Log identifier = 0x%x, Expected 0x25" % (self.logIdentifier)))
            valid = False

        if (self.dataArea2EndBlock < self.dataArea1EndBlock):
            OutputLog.Error("Data Area 2 last block (" + str(self.dataArea2EndBlock) + ") less than Data 1 last block (" + str(self.dataArea1EndBlock) + ")")
            valid = False

        if (self.dataArea3EndBlock < self.dataArea2EndBlock):
            OutputLog.Error("Data Area 3 last block (" + str(self.dataArea3EndBlock) + ") less than Data 2 last block (" + str(self.dataArea2EndBlock) + ")")
            valid = False

        for x in range(0, 3):
            if (self.reserved[x] != 0):
                OutputLog.Warning("Reserved field1[" + str(x) + "] != 0")

        for x in range(0, 367):
            if (self.reserved2[x] != 0):
                OutputLog.Warning("Reserved field2[" + str(x) + "] != 0")

        if (self.reasonId.getMajorVersion() != 0):
            if (False == self.reasonId.validate(False)):
                valid = False

        return valid

    def getLastBlock(self):
        dataAreaList = []
        lastBlock = max(self.dataArea1EndBlock, self.dataArea2EndBlock, self.dataArea3EndBlock)
        lastBlock += 1
        if (0 != self.dataArea1EndBlock):
            dataAreaList.append(self.dataArea1EndBlock + 1)
            if (self.dataArea2EndBlock > self.dataArea1EndBlock):
                dataAreaList.append(self.dataArea2EndBlock + 1)
            if (self.dataArea3EndBlock > self.dataArea2EndBlock):
                dataAreaList.append(self.dataArea3EndBlock + 1)
        elif (0 != self.dataArea2EndBlock):
            dataAreaList.append(self.dataArea2EndBlock + 1)
            if (self.dataArea3EndBlock > self.dataArea2EndBlock):
                dataAreaList.append(self.dataArea3EndBlock + 1)
        else:
            dataAreaList.append(self.dataArea3EndBlock + 1)
        return lastBlock, dataAreaList

    def getDataAreaLastBlock(self, dataArea):
        if (1 == dataArea):
            return self.dataArea1EndBlock + 1
        elif (2 == dataArea):
            return self.dataArea2EndBlock + 1
        elif (3 == dataArea):
            return self.dataArea3EndBlock + 1
        else:
            return self.dataArea3EndBlock + 1

    def getSerialNumber(self):
        return self.reasonId.getSerialNumber()

    def getCIdata(self):
        return self.ctrlInitiatedDataAvail, self.ctrlInitiatedGeneration

    def IsVersion1(self):
        if (self.reasonId.getMajorVersion() == 0):
            return True
        else:
            return False

    def tofile(self, filename):
        self.reasonId.tofile(filename)


class TelemetryLogPageHeader_union(Union):
    """
    Brief:
        getControllerInitiatedLogPageHeader_union() - Definition of the NVMe Get Controller Initiated Log Page header structure for Intel drives.

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
        ("NvmeHostInitiated", NvmeHostInitiatedLogPageHeader_struct),  # Header data
        ("NvmeCtrlInitiated", NvmeControllerInitiatedLogPageHeader_struct),  # Header data
        ("SataHostInitiated", SataHostInitiatedLogPageHeader_struct),  # Header data
        ("SataCtrlInitiated", SataControllerInitiatedLogPageHeader_struct),  # Header data
        ("NvmeLogId", c_ubyte),  # NVMe log page number
        ("SataLogId", c_ubyte),  # SATA log page number
        ("Bytes", c_ubyte * MAX_BLOCK_SIZE),  # fill
        # End More Intel
    ]

    def __init__(self, imageBuffer, blockSize):
        dataSize, dataBuffer = GetTruncatedDataBuffer(imageBuffer, blockSize, MAX_BLOCK_SIZE)
        for i in range(0, dataSize):
            self.Bytes[i] = dataBuffer[i]
        self.isNVMe = True
        self.isSATA = False
        return

    def __getitem__(self, item):
        return getattr(self, item)

    def getStr(self):
        retString = ""
        if (self.NvmeLogId == 7):
            retString += self.NvmeHostInitiated.getStr()
            self.isNVMe = True
            self.isSATA = False
        elif (self.NvmeLogId == 8):
            retString += self.NvmeCtrlInitiated.getStr()
            self.isNVMe = True
            self.isSATA = False
        elif (self.SataLogId == 0x24):
            retString += self.SataHostInitiated.getStr()
            self.isNVMe = False
            self.isSATA = True
        elif (self.SataLogId == 0x25):
            retString += self.SataCtrlInitiated.getStr()
            self.isNVMe = False
            self.isSATA = True
        else:
            self.isNVMe = False
            self.isSATA = False
        if self.isNvme:
            retString += f"NvmeLogId       : {self.NvmeLogId}"
        if self.isSATA:
            retString += f"SataLogId       : {self.SataLogId}"
        for i in range(MAX_BLOCK_SIZE):
            retString += f"Bytes[{i}]      : {c_char(self.Bytes[i])}\n"
        return retString

    def parse(self, outFile=None):
        if outFile is not None:
            with open(outFile, 'wb') as oFile:
                oFile.write('%s\n' % self.getStr())
        else:
            print(self.getStr())

    def getNvmeHostInitiatedStruct(self):
        return self.NvmeHostInitiated

    def getNvmeControllerInitiatedStruct(self):
        return self.NvmeCtrlInitiated

    def getNvmeLogPageId(self):
        return (self.NvmeLogId)

    def getInterfaceLogPageId(self, sata=False):
        if (sata):
            return (self.SataLogId)
        else:
            return (self.NvmeLogId)

    def getInterfaceTelemetryHeaderStruct(self):
        if (self.NvmeLogId == 7):
            self.isNVMe = True
            self.isSATA = False
            return self.NvmeHostInitiated
        elif (self.NvmeLogId == 8):
            self.isNVMe = True
            self.isSATA = False
            return self.NvmeCtrlInitiated
        elif (self.SataLogId == 0x24):
            self.isNVMe = False
            self.isSATA = True
            return self.SataHostInitiated
        elif (self.SataLogId == 0x25):
            self.isNVMe = False
            self.isSATA = True
            return self.SataCtrlInitiated
        else:
            OutputLog.Error("getTelemetryLogPageHeader_union: unknown log page number {}".format(str(self.NvmeLogId)))
            return None
