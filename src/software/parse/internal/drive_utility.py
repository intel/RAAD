#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Randal Eike, Joseph Tarango
# *****************************************************************************/
"""
Brief:
    drive_utility.py - Test drive selection and identification utility for generric tests

Description:
    -

Classes:
    testDrive, driveList

Function(s):
    ScanDrives(option,opt_str,value,parser), SetUlink(ulinkCommand)

Related:
    -

Author(s):
    Randal Eike, Joe Tarango
"""

#### Base imports
import sys, re, os, time, platform

#### import Utility functions
from src.software.parse.output_log import OutputLog
from src.software.parse.output_log import promptUser


# from lun import LUN

################################################################################################################
################################################################################################################

def ScanDrives(option, opt_str, value, parser):
    #### import TWIDL modules
    try:
        from scan import Scan  # @todo TWIDL dependancy
        # Scan all drives
        myScan = Scan(extend=True)
        myScan.parse()
    except:
        pass
    sys.exit(0)


def SetUlink(ulinkCommand):
    try:
        from win.winulink import powerOn, powerOff
        if (ulinkCommand.upper() == 'PC'):
            powerOff(idleTime=1)
            powerOn(idleTime=1)
            return True
        elif (ulinkCommand.upper() == 'ON'):
            powerOn(idleTime=1)
            return True
        elif (ulinkCommand.upper() == 'OFF'):
            powerOff(idleTime=1)
            return True
        else:
            return False
    except:
        pass
        return False


class testDrive(object):
    """
    Brief:
        testDrive() - Test drive selection and identification utility class for python test scripts.

    Description:
        This class implements the generic utility functions required to select and identify a
        drive to be used to run a generic test script.

    Class(es):
        testDrive

    Method(s):
        __init__(self) - Constructor
        getDrive(self, drvIndex = None) - Scan the system for the requested drive

    Related: -

    Author(s):
        Randal Eike
    """

    def __getDrive(self, drvIndex=None):
        #### import TWIDL modules
        drive = None
        try:
            from scan import Scan  # @todo TWIDL dependancy
            from device import Device  # @todo TWIDL dependancy

            ### Scan all drives
            myScan = Scan(extend=True)

            ### Ask user to select drive to use
            if (drvIndex is None):
                drvIndex = myScan.selectDevice("\nSelect Device ")

            ### If we have an index, try to load the drive
            if (drvIndex is not None):
                ### Get physical drive path of selected drive index
                drvPath = myScan.getDevicePath(drvIndex)
                if (drvPath is None):
                    OutputLog.Error("The specified drive index (" + str(drvIndex) + ") is not valid!")
                else:
                    ### Instantiate the drive object
                    drive = Device().getDevice(devicePath=drvPath, flags=1 | 2)
                    if (not drive.getCmdSet()):
                        OutputLog.Error('Drive with INVALID CMD SET !!!')
            return drive
        except:
            pass
            return drive

    def __clearDriveData(self):
        self.hasBeenCalled = False
        self.serialNumber = ""
        self.productFamily = ""
        self.drvPath = ""
        self.busType = ""
        self.fw = ""
        self.model = ""
        self.vendor = ""
        self.byteCapacity = 0
        self.maxLba = 0

    def __getBasicInfo(self):
        ### initialize some basic drive info
        self.drvPath = self.drive.getLocation()
        self.busType = self.drive.getBusType()
        self.serialNumber = re.sub(' |\W', '', self.drive.getIdent().getSerial())
        self.fw = self.drive.getIdent().getFirmware()
        self.model = self.drive.getIdent().getModel()
        self.vendor = self.drive.getIdent().getVendor()
        self.byteCapacity = self.drive.getIdent().getCapacity()
        self.maxLba = self.drive.getIdent().getMaxLBA()
        self.productFamily = self.drive.getIdent().getProductFamily().upper()
        self.hasBeenCalled = True

    def toStr(self):
        ### print basic drive info
        retstring = "\nBasic Drive Info:\n"
        retstring += "=================\n"
        retstring += "Drive Path:  " + self.drvPath + "\n"
        retstring += "Vendor:      " + self.vendor + "\n"
        retstring += "Model:       " + self.model + "\n"
        retstring += "Firmware:    " + self.fw + "\n"
        retstring += "Serial:      " + self.serialNumber + "\n"
        retstring += "Bus:         " + self.busType + "\n"
        retstring += "Capacity:    " + str(self.byteCapacity) + "\n"
        retstring += "Max LBA:     " + str(self.maxLba) + "\n"
        retstring += "Product:     " + self.productFamily
        return retstring

    def __init__(self, drvIndex=None):
        self.__clearDriveData()
        self.drive = self.__getDrive(drvIndex)

    def getTestDrive(self):
        return self.drive

    def unlockDrive(self):
        if (self.drive is not None):
            ### Test normal drive connection
            OutputLog.DebugPrint(2, 'Unlock drive')
            try:
                self.drive.unlock()
                return True
            except:
                OutputLog.Error('Could not unlock drive!!!')
                return False
        else:
            OutputLog.Error('Invalid drive object!!!')
            return False

    def printBasicInfo(self):
        if (self.drive is None):
            OutputLog.Error('Invalid drive object!!!')
            return False
        else:
            ### initialize some basic drive info and print it
            self.__getBasicInfo()
            OutputLog.Information(self.toStr())

    def globalDriveSpecificParams(self):
        if (self.drive is None):
            OutputLog.Error("No drive passed in, can't read state")
            return False
        else:
            if (False == self.hasBeenCalled):
                self.drive.getIdent()
                self.__getBasicInfo()
                self.hasBeenCalled = True
            return True

    def isDriveAsserted(self):
        #### import TWIDL modules
        try:
            from scan import Scan  # @todo TWIDL dependancy
            from device import drive  # @todo TWIDL dependancy
            if (self.globalDriveSpecificParams()):
                if (self.busType.upper() in ['SCSI']):
                    if hasattr(drive, 'testUnit'):
                        drive.testUnit()
                        time.sleep(1)
                        drive.testUnit()
                        time.sleep(1)
                    if hasattr(drive, 'returnSense'):
                        uecCode, uecDesc = drive.returnSense()
                        OutputLog.Error(format("uecCode:     0x%04X" % uecCode))
                        if (uecCode in [0xF607, 0xF623]):
                            return True
                        else:
                            return False
                else:
                    if ('*ASSERT' in self.drive.getDriveStatus().upper()[:7]):
                        return True
                    else:
                        return False
        except:
            pass
            return False

    def getSerialNumber(self):
        if (False == self.hasBeenCalled): self.globalDriveSpecificParams()
        return self.serialNumber

    def getFamily(self):
        if (False == self.hasBeenCalled): self.globalDriveSpecificParams()
        return self.productFamily


class driveList(object):
    """
    Brief:
        driveList() - Utility functions to get a list of potential test drives in the system.

    Description:
        Class to abstract test drive list functions.

    Class(es):
        testDrive

    Method(s):
        __init__(self) - Constructor
        getDrive(self, drvIndex = None) - Scan the system for the requested drive

    Related: -

    Author(s):
        Randal Eike
    """

    def __init__(self):
        pass

    @staticmethod
    def validDrvIndexList(excludeSystemDrive=True):
        validIndexList = []
        try:
            #### import TWIDL modules
            from scan import Scan  # @todo TWIDL dependancy
            currentOSplatform = platform.system()
            driveList = Scan(extend=True).getDeviceList()

            if currentOSplatform == "Windows":
                devicePathId = "\\\\.\\"
            elif currentOSplatform == "Linux":
                devicePathId = "/dev/"

            for i in range(0, len(driveList)):
                if currentOSplatform == "Windows":
                    if ('NODRIVE' in driveList[i].getModel().upper()):
                        continue
                    elif ("\\\\.\\" not in driveList[i].getDevicePath().upper()):
                        continue
                    elif ("NONE" in driveList[i].getPassthrough().upper()) and \
                            ("RAID" not in driveList[i].getModel().upper()):
                        continue
                    elif (excludeSystemDrive):
                        if ("NONE" not in driveList[i].getPassthrough().upper()) and \
                                (devicePathId in driveList[i].getDevicePath().upper()) and \
                                (os.path.expandvars('%systemdrive%') == driveList[i].getDevicePath().upper()):
                            continue
                elif currentOSplatform == "Linux":
                    if ('NODRIVE' in driveList[i].getModel().upper()):
                        continue
                    elif ("/dev/" not in driveList[i].getDevicePath()):
                        continue
                    elif ("NONE" in driveList[i].getPassthrough().upper()) and \
                            ("RAID" not in driveList[i].getModel().upper()):
                        continue
                    elif (excludeSystemDrive):
                        if (driveList[i].getModel() == "SYSTEM BOOT DRIVE"):
                            continue

                validIndexList.append(driveList[i].getIndex())
            return validIndexList
        except:
            pass
            return validIndexList

    @staticmethod
    def displayDriveList():
        #### import TWIDL modules
        try:
            from scan import Scan  # @todo TWIDL dependancy
            ### Scan all drives return list of Drive objects
            validList = Scan(extend=True).getDeviceList()
            for x in validList:
                print(x)
        except:
            pass
            return

    @staticmethod
    def getDriveFromList(prompt):
        driveList.displayDriveList()
        driveIndex = promptUser(prompt)
        if ((driveIndex is None) or (driveIndex.upper() == 'Q')): sys.exit(0)
        return int(driveIndex)

    @staticmethod
    def checkDriveIndex(driveNumber=None):
        validDrvnums = driveList.validDrvIndexList(excludeSystemDrive=False)
        if (driveNumber is None):
            if (len(validDrvnums) > 0):
                driveIndex = driveList.getDriveFromList("Please enter drive num")
            else:
                OutputLog.Error("Not able to locate any compatible drives to FA.")
                driveIndex = None
        else:
            if (len(validDrvnums) == 0):
                OutputLog.Error("Not able to locate any compatible drives to FA.")
                driveIndex = None
            else:
                if (driveNumber not in validDrvnums):
                    OutputLog.Error("Specified drive number (" + str(driveNumber) + ") is not valid.")
                    driveIndex = driveList.getDriveFromList("Please enter valid drive num")
                else:
                    driveIndex = driveNumber
        return driveIndex

    @staticmethod
    def reattachDrive(serialNumber, excludeSystemDrive=True):
        #### import TWIDL modules
        try:
            from scan import Scan  # @todo TWIDL dependancy
            from device import Device  # @todo TWIDL dependancy
            driveList = Scan(extend=True).getDeviceList()
            for i in range(0, len(driveList)):
                if (driveList[i].getSerial() == serialNumber):
                    drive = Device().getDevice(devicePath=driveList[i].getDevicePath(), flags=1 | 2)
                    return drive
            return None
        except:
            pass
            return None
