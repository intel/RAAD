#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Randal Eike, Joseph Tarango
# *****************************************************************************/
"""
Brief:
    telemetry_drive.py - Telemetry test drive
Classes:
    logDevice
"""
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations

#### import TWIDL modules
try:
    from device import *
except:
    print("ERROR: cannot find TWIDL")
    pass

#### import Utility functions
from src.software.parse.output_log import OutputLog
from src.software.parse.internal.drive_utility import *

#### import telemetry header data
from src.software.parse.telemetry_util import *
from src.software.parse.headerTelemetry import *

################################################################################################################
################################################################################################################
## Python 2 and 3 redefines
################################################################################################################
################################################################################################################
# if (sys.version_info[0] < 3):
#     # Python 3 code in this block
#     range = xrange
#
# if (sys.version[:3] > "2.3"):
#     import hashlib # @todo cleanup explicit usage

# try:
#     # Python 2
#     xrange
# except NameError:
#     # Python 3
#     xrange = range

################################################################################################################
################################################################################################################

class logDevice(object):
    """
    Telemetry Log device.  Abstracts NVMe/SATA differences
    """
    NvmeHostInitiatedLogId = 7
    NvmeControllerInitiatedLogId = 8
    SataHostInitiatedLogId = 0x24
    SataControllerInitiatedLogId = 0x25

    cmdnsid = 0xFFFFFFFF

    def __init__(self, testDrive, hiLog = True):
        self.tstDrive = testDrive

        if (testDrive.getCmdSet() == 'NVME'): self.sataIntf = False
        else: self.sataIntf = True

        self.hiLog = hiLog
        self.cmdnsid = logDevice.cmdnsid
        self.block0Size = TelemetryLogBlockSize

        if (hiLog):
            if (self.sataIntf): self.logid = logDevice.SataHostInitiatedLogId
            else: self.logid = logDevice.NvmeHostInitiatedLogId
        else:
            if (self.sataIntf): self.logid = logDevice.SataControllerInitiatedLogId
            else: self.logid = logDevice.NvmeControllerInitiatedLogId


    def setBlock0Size(self, byteCount):
        self.block0Size = byteCount

    def isHiLogTest(self):
        return self.hiLog

    def getDrive(self):
        return self.tstDrive

    def getReadBuffer(self):
        return self.tstDrive.getReadBuffer()

    def setHiLog(self):
        self.hiLog = True
        if (self.sataIntf): self.logid = logDevice.SataHostInitiatedLogId
        else: self.logid = logDevice.NvmeHostInitiatedLogId

    def setCiLog(self):
        self.hiLog = False
        if (self.sataIntf): self.logid = logDevice.SataControllerInitiatedLogId
        else: self.logid = logDevice.NvmeControllerInitiatedLogId

    def getLogPage(self, byteCount, startOffset, create, retainAER):
        # Check if we need to use SQE
        if (byteCount > 4096): self.tstDrive.setCommandPathSQE()

        # Determine the interface
        if (self.sataIntf == False):
            numDwords = (byteCount / BYTES_PER_DWORD) - 1

            OutputLog.DebugPrint(6,format("Read Log, offset=%u, numd=%u, lid=%d, create=%d, retainAER=%d nsid=%x" %(startOffset, numDwords, self.logid, create, retainAER, self.cmdnsid)))
            if (False == self.tstDrive.getLogPage(NUMD=numDwords,LID=self.logid,LPO=startOffset,LSP=create,RAE=retainAER,NSID=self.cmdnsid)):
                OutputLog.Error(format("Read Log failed, offset=%u, numd=%u, lid=%d, create=%d, nsid=%x" %(startOffset, numDwords, self.logid, create, self.cmdnsid)))
                return False
            else:
                return True
        else:
            #   Page number to start reading from based on the current index
            pg_num = startOffset / TelemetryLogBlockSize
            lba = ((pg_num / 256) << 32) | ((pg_num & 0xFF) << 8) | self.logid
            block_cnt = byteCount / TelemetryLogBlockSize

            OutputLog.DebugPrint(6,format("Read Log Ext, lba=%u, blockcount=%u, feature=%d" %(lba, block_cnt, create)))
            if (False == self.tstDrive.readLogExt(LBA=lba, blockcount=block_cnt, feature=create)):
                OutputLog.Error(format("Read Log Ext failed, lba=%u, blockcount=%u, feature=%d" %(lba, block_cnt, create)))
                return False
            else:
                return True

    def getLogPage0(self, create, retainAER):
        return self.getLogPage(self.block0Size, 0, create, retainAER)

    def writeBlock(self, telemetryDataFile, blockSize, offset = None):
        if (telemetryDataFile is not None):
            buffData = self.tstDrive.getReadBuffer()
            outData = bytearray(blockSize)

            for i in range(0, blockSize): outData[i] = buffData[i]
            if (offset is not None): telemetryDataFile.seek(offset)
            telemetryDataFile.write(outData)

    def getInterfaceHeader(self):
        telemetryUnion = TelemetryLogPageHeader_union(self.tstDrive.getReadBuffer(), TelemetryLogBlockSize)
        telemetryHeader = telemetryUnion.getInterfaceTelemetryHeaderStruct()

        if(telemetryHeader is not None):
            if (telemetryUnion.getInterfaceLogPageId() != self.logid):
                OutputLog.Error(format("Invalid log id %d, expected %d" % (telemetryUnion.getInterfaceLogPageId(), self.logid)))
                telemetryHeader =  None

        return telemetryHeader

    def getLogNameBase(self):
        if (self.hiLog): basename = "v2hi"
        else:  basename = "v2ci"

        if(self.sataIntf == False): basename += "_nvme"
        else: basename += "_sata"
        return basename

    def generateEvent(self):
        if(False == self.tstDrive.testEventDump()):
            OutputLog.Error("Event dump generation failed!")
            return False

    def setCiNotification(self, notify):
        if (self.sataIntf == False):
            # Enable Telemtery log notification
            return self.tstDrive.setFeatureAsyncEventConfig(NSID=0,TLN=notify)
        else:
            return False

    def queueAsynchronousEventRequest(self, callback):
        if (self.sataIntf == False):
            # Queue AER command for return
            return self.tstDrive.asynchronousEventRequest(callBackRef=callback)
        else:
            return False

    def getAsyncManager(self):
        return self.tstDrive.getAsyncManager()

    def resetRecover(self):
        if (self.sataIntf == False):
            # Reset the NVMe device
            return self.tstDrive.nvmeReset()
        else:
            # Reset the SATA device
            return self.tstDrive.softReset()

    def assertDrive(self):
        sn = self.tstDrive.getIdent().getSerial()
        self.tstDrive.assertDumpTest()
        if ((self.sataIntf == True) and (self.ulink is not None)):
            # SATA with ulink
            SetUlink('PC')
            self.tstDrive = driveList.reattachDrive(sn)
        else:
            self.tstDrive.warmReset()

    def recoverAssertedDrive(self):
        status = True
        complete = False
        step = 1
        errorMsg = ""

        while ((status == True) and (complete == False)):
            if (1 == step):
                status = self.tstDrive.unlock()
                errorMsg = "Unable to unlock drive for assert recovery"
            elif(2 == step):
                status = self.tstDrive.eDump()
                errorMsg = "Erase dump failed in assert recovery"
            elif(3 == step):
                status = self.tstDrive.loadSlowContext()
                errorMsg = "Load Slow context failed in assert recovery"
            elif(4 == step):
                status = self.tstDrive.llf()
                errorMsg = "LLF failed in assert recovery"
            elif(5 == step):
                status = self.tstDrive.warmReset()
                errorMsg = "WarmReset failed in assert recovery"
            else:
                complete = True

            if (False == status):
                complete = True
                OutputLog.Error(errorMsg)

            step += 1

        return status





