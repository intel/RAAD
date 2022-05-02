#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Randal Eike, Joseph Tarango
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import re, os, sys, time
from optparse import OptionParser

##### .exe extension patch for the compiled version of this script
if not re.search('\.PY$|\.PYC$|\.EXE$', os.path.split(sys.argv[0])[1].upper()):
    sys.argv[0] = os.path.join( os.path.split(sys.argv[0])[0] , os.path.split(sys.argv[0])[1]+'.exe' )

#### extend the Python search path to include TWIDL_tools directory
if __name__ == '__main__':
    twidlcore = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    sys.path.insert(0,twidlcore)

#### import TWIDL modules
try:
    from device import *
    from device_api import *
    from devices.protocol_bases.nvme_base import *
except:
    print("ERROR: cannot find TWIDL")
    pass

#### import test utilities
from src.software.parse.internal.drive_utility import testDrive
from src.software.parse.internal.drive_utility import SetUlink
from src.software.parse.internal.drive_utility import ScanDrives
from src.software.parse.internal.drive_utility import driveList

#### import telemetry modules
from src.software.parse.telemetry_util import *
from src.software.parse.telemetry_drive import logDevice
from src.software.parse.headerTelemetry import *
from src.software.parse.parseTelemetryBin import checkLogListValidity
from src.software.parse.internal.getTelemetry import readTelemetryLog
from src.software.parse.output_log import OutputLog

TOOL_VERSION = 1.1

cmdnsid = 0xFFFFFFFF
ASYNC_TIMEOUT = 10
EVENT_DUMP_COUNT = 16
CORE_COUNT = 2
outputLogs = []

# Global to track if an async notification occured
global asyncNotificationReceived
asyncNotificationReceived = False

global logPageToRead
logPageToRead = 0

def openFile(outdir, basename):
    ### open outputfile ###
    telemetryData = None
    if(basename is not None):
        if(outdir is not None):
            outFile = os.path.join(outdir, basename+"_log.bin")
        else:
            outFile = basename+"_log.bin"

        OutputLog.DebugPrint(2, format("Opening file \"%s\" for CI log pull" % (outFile)))
        telemetryData = openWriteFile(outFile)

    return telemetryData

def myAERCallBackFunction(callBackPtr):
    """
    Brief:
        myAERCallBackFunction(callBackPtr)

    Description:
        NVMe AER Callback function that is called when an async notification is triggered

    Argument(s):
        callBackPtr - Pointer to a call back structure

    Return Value(s):
        None

    Example:
        cbAERFunc = call_back_func_t(myAERCallBackFunction)

    Author(s):
        Craig Deitering
    """
    #Get the callback structure info
    callBack = cast(callBackPtr, POINTER(call_back_t)).contents

    #Check if an error occured"
    if callBack.errorCode :
        OutputLog.Error(format("Async Notification Event received with ErrorCode=%d" % (callBack.errorCode)))
    else:
        OutputLog.DebugPrint(1,"Async Notification Event received with good status!")

        #Set the Last Completion so that you can get the completion outside of this callback function if need be
        completionEntry = CompletionEntry(callBack.commandCompletion)
        OutputLog.DebugPrint(2, format("NVMe Completion:\n%s" % completionEntry.toString()))

        #Parse DWORD 0
        dword0 = completionEntry.getStruct().DW0
        asyncEventType = dword0 & 0b111
        asyncEventInfo = ((dword0 >> 8) & 0xFF)
        associatedLogPage = ((dword0 >> 16) & 0xFF)
        OutputLog.DebugPrint(1, format("AsyncEventType     = 0x%X" % (asyncEventType)))
        OutputLog.DebugPrint(1, format("AsyncEventInfo     = 0x%X" % (asyncEventInfo)))
        OutputLog.DebugPrint(1, format("AssociatedLogPage  = 0x%X" % (associatedLogPage)))

        global logPageToRead
        logPageToRead = associatedLogPage

    #Set the python global signaling that an async notification was recieved
    global asyncNotificationReceived
    asyncNotificationReceived = True

def SetupAER(drive, notify = 1):
    """
    Brief:
        SetupAER(drive)

    Description:
        Setup an asynchronous event request for the telemetry log change notification

    Argument(s):
        drive - Drive object to send commands to

    Return Value(s):
        True if AER was generated, False if not

    Example:
        pasFail = SetupCallbackAndWait(drive, False)

    Author(s):
        Randal Eike, based on Craig Deitering AER example code
    """
    # Enable Telemtery log notification
    if (False == drive.setCiNotification(notify)):
        OutputLog.Error("Enable telemetry log notification set feature failed!")
        return False

    # Setup callBack
    asyncNotificationRecieved = False
    cbAERFunc = call_back_func_t(myAERCallBackFunction)
    cbStruct = call_back_t()
    cbStruct.callBack = cbAERFunc
    drive.getAsyncManager().saveAsyncStruct(cbStruct)
    callBackRef = byref(cbStruct)

    #Issue Features Async Notifications Control passing in CallBack created above
    if(False == drive.queueAsynchronousEventRequest(callBackRef)):
        OutputLog.Error("Asynchronous Event Request (AER) command failed!")
        return False

    OutputLog.DebugPrint(1,"Issued Async Event Request... ")
    return True

def WaitForAER(timeout = ASYNC_TIMEOUT, expectTimeout=False):
    """
    Brief:
        WaitForAER(drive)

    Description:
        Wait for the AER event request to complete or timeout

    Argument(s):
        timeout - Time in seconds to wait for the event

    Return Value(s):
        True if AER was returned, False if not

    Example:
        pasFail = SetupCallbackAndWait(drive, False)

    Author(s):
        Randal Eike, based on Craig Deitering AER example code
    """
    startTime = time.time()
    deathTime = time.time() + timeout
    returnStatus = True
    OutputLog.DebugPrint(1,format("Waiting for async notification to occur (Timeout = %d seconds)... " % (deathTime - time.time())))

    # Wait for the AER to come back
    global asyncNotificationReceived
    while ((False == asyncNotificationReceived) and (True == returnStatus)):
        time.sleep(1)
        OutputLog.DebugPrint(3, format("waiting... (%d seconds remaining)" % (deathTime - time.time())))

        if (time.time() > deathTime):
            # process time-out
            returnStatus = False
            if (True == expectTimeout):
                OutputLog.DebugPrint(1,"Async notification wait time-out as expected")

    # AER returned before timeout
    if (True == asyncNotificationReceived): asyncNotificationReceived = False
    if (True == returnStatus): OutputLog.DebugPrint(1, "Async notification wait received")
    return returnStatus


def PullCILog(drive, outFile, outDir):
    """
    Brief:
        PullCILog(drive, outFile, outDir)

    Description:
        Pull the Controller initiated log and save it in the filename specified by outFile

    Argument(s):
        drive - Drive object to send commands to
        outFile - Event log output file name
        outDir - Directory to output file to

    Return Value(s):
        True if log pulled and saved with no error, False if an error occured

    Example:
        PullCILog(drive, filename)

    Author(s):
        Randal Eike
    """
    # Pull the log into a file to be checked later
    telemetryData = openFile(outDir, outFile)
    if (telemetryData is not None):
        OutputLog.DebugPrint(1, format("Pull CI log %s" % (outFile)))
        status, ciGeneration = readTelemetryLog(tstDrive = drive, telemetryData = telemetryData, blockSize = 4096, createLog = False)
        if(False == status):
            OutputLog.Error("Read CI log failed!!")
            return False, ciGeneration
        else:
            OutputLog.DebugPrint(1, "Exiting, good status!")
            return True, ciGeneration


def ClearAERLog(drive):
    """
    Brief:
        ClearAER(drive)

    Description:
        Clear the AER event

    Argument(s):
        drive - Drive object to send commands to

    Return Value(s):
        True if log pulled and saved with no error, False if an error occured

    Example:
        ClearAERLog(drive)

    Author(s):
        Randal Eike
    """
    global logPageToRead
    returnStatus = False  # assume failure
    retGeneration = -1

    if(False == drive.getLogPage0(0, 1)):
        OutputLog.Error("Clear AER generation read failed!")
        header1 = None
    else:
        header1 = drive.getInterfaceHeader()

    if(False == drive.getLogPage0(0, 0)):
        OutputLog.Error("Clear AER log read failed!")
        header2 = None
    else:
        header2 = drive.getInterfaceHeader()

    # Verify that the generation matches
    if((header1 is not None) and (header2 is not None)):
        # Check the Generation number
        ciAvailable1, ciGeneration1 = header1.getCIdata()
        ciAvailable2, ciGeneration2 = header2.getCIdata()
        if (ciGeneration1 != ciGeneration2):
            OutputLog.Error("Generation mismatch, initial=%d, end=%d\n" % (ciGeneration1, ciGeneration2))
        else:
            # Only passing path
            returnStatus = True
            retGeneration = ciGeneration2

    return returnStatus, retGeneration

def PullLogAndClear(drive, outFile, outDir):
    """
    Pull the log and clear the status
    """
    status, ciGeneration = PullCILog(drive, outFile, outDir)
    if(True == status):
        status, clrCiGeneration = ClearAERLog(drive)
        if(True == status):
            if (ciGeneration != clrCiGeneration):
                OutputLog.Error(format("Clear log generation number (%d) != read generation number (%d)" % (clrCiGeneration, ciGeneration)))
                status = False
        return status
    else:
        return False


def TestAsyncNotification(drive, outFile, outDir = None):
    """
    Brief:
        TestAsyncNotification(drive, outFile, outDir = None)

    Description:
        Setup an asynchronous event request for the telemetry log change notification and trigger an event to trigger the AER return

    Argument(s):
        drive - Drive object to send commands to
        outFile - Event log output file name
        outDir - Directory to output file to, default = None

    Return Value(s):
        True if AER was generated, False if not

    Example:
        pass = TestAsyncNotification(drive)

    Author(s):
        Randal Eike, based on Craig Deitering AER example code
    """
    # Enable Telemtery log notification
    if (False == SetupAER(drive, 1)):
        OutputLog.Error("AER setup failed, TestAsyncNotification")
        return False

    # Generate the event
    OutputLog.DebugPrint(1, "Generate event dump to trigger the callback")
    if(False == drive.generateEvent()):
        OutputLog.Error("Event dump generation failed!")
        return False

    # Wait for the AER to come back
    if (False == WaitForAER()):
        OutputLog.Error("Async notification wait time-out. Issuing a device reset() and trying to get the drive back to normal")
        drive.resetRecover() # issue the reset to get the AER to get called back by the OS/driver
        return False

    # Pull the log and erase the event
    return PullLogAndClear(drive, outFile, outDir)


def TestAsyncNotificationNoticeDisabled(drive, outFile, outDir = None):
    """
    Brief:
        TestAsyncNotificationNoticeDisabled(drive, outFile, outDir = None)

    Description:
        Setup a disabled asynchronous event request for the telemetry log change notification and trigger an event.
        Make sure that the AER does not occur.  Then enable the notification to trigger the AER return and verify it does
        occur.

    Argument(s):
        drive - Drive object to send commands to
        outFile - Event log output file name
        outDir - Directory to output file to, default = None

    Return Value(s):
        True if AER was generated, False if not

    Example:
        pass = TestAsyncNotification(drive)

    Author(s):
        Randal Eike, based on Craig Deitering AER example code
    """
    # Setup the disabled AER
    if (False == SetupAER(drive, 0)):
        OutputLog.Error("AER setup failed, TestAsyncNotificationNoticeDisabled")
        return False

    # Generate the event
    OutputLog.DebugPrint(1, "Generate event dump to trigger the callback")
    if(False == drive.generateEvent()):
        OutputLog.Error("Event dump generation failed!")
        return False

    # Wait for the AER to come back
    if (True == WaitForAER(expectTimeout = True)):
        OutputLog.Error ("Async notification received when notification was disabled.")
        return False

    # Enable Telemtery log notification
    OutputLog.DebugPrint(1, "Enable notification now and it should trigger....")
    if (False == drive.setCiNotification(1)):
        OutputLog.Error("Enable telemetry log notification set feature failed!")
        return False

    # Wait for the AER to come back
    if (False == WaitForAER()):
        OutputLog.Error("Async notification wait time-out. Issuing a device reset() and trying to get the drive back to normal")
        drive.resetRecover() # issue the reset to get the AER to get called back by the OS/driver
        return False

    # Pull the log and erase the event
    return PullLogAndClear(drive, outFile, outDir)


def TestAsyncNotificationNoticeDoubleEvent(drive, outFile1, outFile2, outDir = None):
    """
    Brief:
        TestAsyncNotificationNoticeDoubleEvent(drive, outFile1, outFile2, outDir = None)

    Description:
        Setup an asynchronous event request for the telemetry log change notification and trigger an event.
        Make sure that the AER does occur but do not clear. Queue a second AER, generate new event and verify
        that the AER does not fire.  Then clear the original AER event and make sure the second AER request
        returns.

    Argument(s):
        drive - Drive object to send commands to
        outFile1 - Event 1 log output file name
        outFile1 - Event 2 log output file name
        outDir - Directory to output file to, default = None

    Return Value(s):
        True if AER was generated, False if not

    Example:
        pass = TestAsyncNotification(drive)

    Author(s):
        Randal Eike, based on Craig Deitering AER example code
    """
    # Enable Telemtery log notification
    if (False == SetupAER(drive, 1)):
        OutputLog.Error("AER setup failed, TestAsyncNotificationNoticeDoubleEvent, event 1")
        return False

    # Generate the event
    OutputLog.DebugPrint(1, "Generate event dump to trigger the callback")
    if(False == drive.generateEvent()):
        OutputLog.Error("Event dump generation failed!")
        return False

    # Wait for the AER to come back
    if (False == WaitForAER()):
        OutputLog.Error("Async notification wait time-out. Issuing a device reset() and trying to get the drive back to normal")
        drive.resetRecover() # issue the reset to get the AER to get called back by the OS/driver
        return False

    # New AER Telemtery log notification
    if (False == SetupAER(drive, 1)):
        OutputLog.Error("AER setup failed, TestAsyncNotificationNoticeDoubleEvent, event 2")
        return False

    # Generate a new event
    OutputLog.DebugPrint(1, "Generate event dump to trigger the callback")
    if(False == drive.generateEvent()):
        OutputLog.Error("Event dump generation failed!")
        return False

    # Make sure AER does not occur
    if (True == WaitForAER(expectTimeout = True)):
        OutputLog.Error ("Async notification received when notification was masked.")
        return False

    # Clear the original event
    status = PullLogAndClear(drive, outFile1, outDir)
    if(True == status):
        # Wait for the new event notice
        if (False == WaitForAER()):
            OutputLog.Error("Async notification wait time-out. Issuing a device reset() and trying to get the drive back to normal")
            drive.resetRecover() # issue the reset to get the AER to get called back by the OS/driver
            status = False
        else:
            # Clear the second event
            # Pull the log and erase the event
            status = PullLogAndClear(drive, outFile2, outDir)

    return status

def clearOldLogs(drive, bigHammer = False):
    returnStatus = True
    for clearCount in range(0, EVENT_DUMP_COUNT):
        if(False == drive.getLogPage0(1, 1)):
            OutputLog.Error("Clear old eventdump RAE=1 read failed!")
            returnStatus = False
        elif(False == drive.getLogPage0(0, 0)):
            OutputLog.Error("Clear old eventdump RAE=0 read failed!")
            returnStatus = False

    if (bigHammer == True):
        twidldrv = drive.getDrive()
        twidldrv.unlock()
        for cmdRoute in range(0, CORE_COUNT):
            eventNumber = 0
            twidldrv.setTestCommandRouting(cmdRoute + 1)

            # Clear old dumps
            while (True == twidldrv.eraseEventDump(eventNumber)):
                eventNumber += 1

    return returnStatus

def CIAER_Test(drive, outFile, outDir):
    del outputLogs[:]
    runTest = True
    finalTestStatus = True
    testNumber = 0

    while ((True == finalTestStatus) and (True == runTest)):
        # Clear old event dumps and start testing
        if (testNumber == 0):
            OutputLog.Information ("\n\nClear old eventdumps... ")
            finalTestStatus = clearOldLogs(drive, False)
        elif (testNumber == 1):
            OutputLog.Information ("\nRun Basic AER test... ")
            finalTestStatus = TestAsyncNotification(drive, outFile+"basic", outDir)
        elif (testNumber == 2):
            OutputLog.Information ("\nRun Disabled AER test... ")
            finalTestStatus = TestAsyncNotificationNoticeDisabled(drive, outFile+"noticeOff", outDir)
        elif (testNumber == 3):
            OutputLog.Information ("\nRun Double Event test... ")
            finalTestStatus = TestAsyncNotificationNoticeDoubleEvent(drive, outFile+"event1", outFile+"event2", outDir)
        elif (testNumber == 4):
            OutputLog.Information ("\nCheck output log validity... ")
            finalTestStatus = checkLogListValidity(outputLogs, False)
        else:
            runTest = False

        # Print test status
        if (True == runTest):
            if (False == finalTestStatus): OutputLog.Information ("FAILED!")
            else: OutputLog.Information ("passed!")

        # Next test
        testNumber += 1

    return finalTestStatus


def main():
    #### Command-line arguments ####
    parser = OptionParser(usage="usage: %prog [options] <baseLogName>", version="%prog Version: "+str(TOOL_VERSION))
    parser.add_option('--debug',type="int", dest='debug', action="store", default=0, help='Enable debug level')
    parser.add_option('-d',type='int', dest='drvnum', metavar='<DRVNUM>', default=None, help='Drive number to analyze')
    parser.add_option('-q',action='callback', callback=ScanDrives, help='Query system for the drive list')
    parser.add_option('-o',action='store',dest="outDir", default=None, help='Output directory')
    parser.add_option('--ulink',metavar='on|off|pc', default='', help='ULINK Control: ON, OFF, or Power Cycle (OFF+ON)')
    (options, args) = parser.parse_args()

    # Set the debug level
    OutputLog.setDebugLevel(options.debug)

    if (len(args) >= 1):
        outFile = args[0]
    else:
        outFile = "telemetry_ci"

    # check for ulink power cycle
    if (options.ulink):
        if(False == SetUlink(options.ulink)):
            OutputLog.Error("INVALID --ulink argument")
            sys.exit(1)

    #if no options specified use drive
    driveNumber = driveList.checkDriveIndex(options.drvnum)
    if(driveNumber is None): sys.exit(1)

    ### Select drive to analyze
    drive = testDrive(driveNumber)
    if (drive is None): sys.exit(1)

    ### Determine what to do
    OutputLog.Information("Get Id information")
    drive.globalDriveSpecificParams()
    OutputLog.Information(drive.toStr())
    if(False == drive.unlockDrive()): sys.exit(1)

    ### Verify drive is not asserted
    if (drive.isDriveAsserted()):
        OutputLog.Information("\nDrive is asserted!!!")
        AssertedDrive = True
    else:
        OutputLog.Information("\nDrive is NOT asserted!!!")
        AssertedDrive = False

    ### Perform Test ###
    if(False == AssertedDrive):
        logDrive = logDevice(drive.getTestDrive(), False)
        finalTestStatus = CIAER_Test(logDrive, outFile, options.outDir)

        if (True == finalTestStatus):
            OutputLog.Information ("\nAll test complete, no errors!")
            exitCode = 0
        else:
            OutputLog.Information ("\nTest incomplete, FAILED!!")
            exitCode = 1

    else:
        finalTestStatus = False
        OutputLog.Information ("\n\nUnable to run test on asserted drive!")
        exitCode = 2
    return exitCode

######## Test it #######
if __name__ == '__main__':
    from datetime import datetime
    p = datetime.now()
    exitCode = main()
    q = datetime.now()
    OutputLog.Information("\nExecution time: "+str(q-p))
    sys.exit(exitCode)


