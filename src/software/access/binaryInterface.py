#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Andrea Chamorro, Joseph Tarango
# *****************************************************************************/
"""
Brief:
A script that extracts uid-specific telemetry data from device or binary file dynamically.

Description:
    Uses binary header to tell data area offset (telemetry binaries are self describing).
    Nvme-cli and getTelemetry-dependent variations available.
    Returns telemetry data.
"""
from __future__ import absolute_import, division, print_function, \
    unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations

import os, subprocess, tempfile
import src.software.parse.parseTelemetryBin


class binProcesses(object):
    """The class binProcesses class is set up to provide ready interface to parseTelemetryBin and getTelemetry
    functionality

    Attributes:
        uidToUidObjectInfoDict(dic): uid Object is a Telemetry Object whose structure is defined by a unique Uid
        telemetryBinary(str): Path to the telemetry binary
        serialNumber(str): Solid State Drive drive identification serial number.
        telemetryHeader(array): Header identification information.
        telemetryBinSplitter(obj): Information from the split binary.
        sataDriveFlag(boolean): Flag to determine if the device is on SATA or NVMe.
        debug(boolean): Flag to determine if in developer mode.
    """

    def __init__(self, telemetryBinary="telemetry.bin", debug=False):
        """
        Initializes the object.

        Args:
            telemetryBinary:    Temporary file where entire telemetry binary is stored

        Returns:
            None.

        Raises:
            None

        Examples:
            #>>> binProcesses("myTempBin2")
        """
        self.uidToUidObjectInfoDict = dict()  # uid Object is a Telemetry Object whose structure is defined by a unique Uid
        self.telemetryBinary = telemetryBinary
        self.serialNumber = None
        self.telemetryHeader = None
        self.telemetryBinSplitter = None
        self.sataDriveFlag = False
        self.debug = debug

    def getObject(self, uid, outputFileName=None):
        """
        Main access point. Return uid Object with payload.binData set.

        Args:
            uid:                Telemetry object unique identifier, as String
            outputFileName:      What to name the output file where binary will print

        Returns:
            object: ObjectListEntry object with binData set

        Raises:
            None

        Examples:
            #>>> object = binProcesses.getObject("5")
            #>>> payload = object.getBinData()
        """
        if (outputFileName):
            outputData = self.__getPayloadFromUid(uid, outputFileName=outputFileName)
        else:
            outputData = self.__getPayloadFromUid(uid)
        structObject = self.uidToUidObjectInfoDict[uid]
        outputStr = str(structObject)
        outputStr += "rawData: %s\n" % (outputData)
        if self.debug:
            print(outputStr)
        structObject.setBinData(outputStr)

        return structObject

    @staticmethod
    def getPayload(uid):
        """
        Main Access Point. Get and return a binary payload
        Args:
            uid: Telemetry object unique identifier, as String

        Returns:
            payload: uids-specific binary payload

        Raises:
            None

        Examples:
            #>>> payload = binProcesses.getPayload("5")
        """
        uidObject = binProcesses().getObject(uid)  # @todo self.getObject(uid)
        try:
            payload = uidObject.ObjectListEntry().getBinData()  # @todo uidObject.getBinData()
        except Exception as seenError:
            print("getPayload Failed for uid {0}\nError is {1}\n".format(uid, seenError))
            payload = None
        return payload

    def getPayloads(self, uidList):
        """
        Main access point. Print payloads retrieved, returns dictionary with desired payloads
        Args:
            uidList     Comma-separated string of unique identifiers to get payloads for

        Returns:
            uidPayloads:     uid->payload dictionary

        Raises:
            None

        Examples:
            #>>> payloads = binProcesses.getPayloads("5,6,7")
            #>>> payload5 = payloads["5"]
        """
        uidPayloads = dict()
        for uid in uidList.split(","):
            payload = self.getPayload(uid)
            uidPayloads[uid] = payload

        return uidPayloads

    def getLocationForUid(self, uid):
        """
        a wrapper for uidToUidObjectInfoDict

        Args:
        uid     uidNum, specified as String

        Returns:
            dataOffset      offset in bytes for object in telemetry
            dataSize        size in bytes of telemetry data for object specified by uid

        Raises:
            None

        Examples:
            #>>> dataOffset, dataSize = binProcesses().getLocationForUid("5")

        """
        try:
            dataOffset, dataSize = self.uidToUidObjectInfoDict[uid].getBinLocation()
            return dataOffset, dataSize
        except KeyError:
            print("Uid {0} not in uidToUidObjectInfoDict, and not in this Telemetry Binary\n".format(uid))
            return None, None

    def readDrive(self, driveNum, sataDriveFlag=False):
        """
        Wrapper for a basic call to getTelemetryAPI. Downside: uses Twidl, (internal tool cannot be used by customer)

        Args:
            driveNum        which Drive number to Query
            sataDriveFlag   if True, specify sata drive, else, specify NVME drive (default)

        Returns:
            returncode      if 0, readDrive passed, if 1, readDrive Failed

        Changes:
            File at self.telemetryBinary now contains telemetry binary

        Notes:
            Assumes host-initiated, telemetry version 2, Additionally assumes all default values

        Examples:
            #>>> dataOffset, dataSize = binProcesses().getLocationForUid("5")

        """
        import src.software.parse.internal.getTelemetry
        # @TODO: still needs debugging
        self.sataDriveFlag = sataDriveFlag

        print("Extracting telemetry log from drive %s, nvme= %s, sata = %s\n..." % (
            driveNum, not sataDriveFlag, sataDriveFlag))
        status, outFile = src.software.parse.internal.getTelemetry.getTelemetryAPI(outFile=self.telemetryBinary,
                                                                                   drvnum=int(driveNum),
                                                                                   debug=1, prepend=False)
        return status

    def parseTelemetryBinaryFile(self, outpath):
        """
        Wrapper for parseTelemetryBinAPI to get telemetry object with telemetry binary info

        Args:
            outpath: output path

        Dependencies:
            self.telemetryBinary    file needs to contain telemetry binary

        Returns:
            None

        Changes:
            self.uidToUidObjectInfoDict is now filled with ObjectListEntry
                objects containing binary info

        Examples:
            #>>> binIn = binProcesses()
            #>>> #fill file with self.readDrive or nvmeCliProcesses.readDrive()
            #>>> binIn.parseTelemetryBinaryFile()

        """
        # Get Binary Uid Info
        print(
            "DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)\n\n")
        parseStatus, telemetryParser = src.software.parse.parseTelemetryBin.parseTelemetryBinAPI(self.telemetryBinary,
                                                                                                 checkOnly=False,
                                                                                                 outpath=outpath)
        self.serialNumber = telemetryParser.getSerialNumber()
        # @ TODO: validity checks fail (see printouts), but this might not be bad in this context. Check this

        if (parseStatus is False):
            print("WARNING: Telemetry Binary Validity Check Failed. ")

        if self.debug:
            print("Printing Split Binary Objects..." % (telemetryParser.telemetrySplit.splitObjectList))
            for startByte, size, dataArea in telemetryParser.telemetrySplit.dataAreaList:
                print("Read Data Area %s at byte %s of size %s\n" % (dataArea, startByte, size))

        # Save as dictionary
        for obj in telemetryParser.telemetrySplit.splitObjectList:
            uid = obj.getObjectId()
            self.uidToUidObjectInfoDict[str(uid)] = obj

        if self.debug:
            print("uidInfoDict contains the following uids:\n {0}\n".format(
                str(sorted(self.uidToUidObjectInfoDict.keys()))))

        self.telemetryBinSplitter = telemetryParser.telemetrySplit
        return

    def __getPayloadFromUid(self, uid, outputFileName=None):
        """
        Put it all together.

        Args:
            uid                 uid of Object would Like to Print, as a String
            outputFileName      file Name to write payload out to

        Dependencies:
            self.telemetryBinary            file needs to contain telemetry binary
            self.uidToUidObjectInfoDict     should be filled with ObjectListEntry objects containing binary info

        Returns:
            outputData

        Changes:
            Results in payload written out to outputFile

        Example:
            Not meant for external usage, see self.getPayload() for this
        """
        dataOffset, dataSize = self.getLocationForUid(uid)

        if self.debug:
            print('Acccessing uid {0}: dataOffset: {1}, dataSize: {2}\n'.format(uid, dataOffset, dataSize))

        if (dataOffset is None or dataSize is None):
            print("Uid Telemetry Data Not Accessible\n")
            return None

        if (not self.telemetryBinary):
            print("Could not find telemetry Binary...\n")
            return None

        if (self.serialNumber):
            prefix = self.serialNumber
        else:
            prefix = "log"

        telemetryBinary = open(self.telemetryBinary)
        if (outputFileName is None):
            outputFileName = self.telemetryBinSplitter.constructFileName(prefix, self.uidToUidObjectInfoDict[uid])

        # @todo: a method to get dynamically but not print out

        outputData = self.telemetryBinSplitter.writeOutputData(telemetryBinary, dataOffset, dataSize, outputFileName)

        print("Storing Payload in : {0} ...\n".format(outputFileName))
        return outputData

    def cleanUp(self):
        """
        Cleanup and remove temporary telemetry binary files

        Examples:
            #>>> binIn = binProcesses()
            #>>> #fill file with self.readDrive or nvmeCliProcesses.readDrive()
            #>>> binIn.parseTelemetryBinaryFile()

            #>>> binIn.getPayloadFromUid("5")
            #>>> #do this as many times as needed
            #...
            #>>> binIn.cleanUp()

        """
        os.remove(self.telemetryBinary)

    def testPayloadMatchesTwidl(self, textLogName):
        pass


class nvmeCliProcesses:
    """
    Abstract:
        get telemetry log via open source implementation

    Description:
        This nvmeCliProcesses class is set up to integrate
        nvme-cli library functionalities, needed for interacting with drive logs.
        NVMe-Cli is an open sourced library used for directly accessing drive, including
        reading and writing operations, retrieving log data.
        NVME-cli includes an intel specific extension for intel specifications

        For the ncmi-cli source code, see https://github.com/linux-nvme/nvme-cli

    Args:
        device          the name of the device to read from
        startAddress    64-bit addr of first block to access
        size            size of data to read in bytes
        numBlocks       number of blocks (zero based) on device to access (??)
        tempFile        File to read data out to
    """

    def __init__(self, debug=False):
        self.outFile = "telemetry_access.bin"
        self.debug = debug

    def readDrive(self, device, startAddress, size, numBlocks, tempFile="tempFile.bin"):
        """
        wrapper for nvme read of regular data (not logs)
        for specs and more functionality, run: sudo nvme read --help

        Args:
            device          the name of the device to read from
            startAddress    64-bit addr of first block to access
            size            size of data to read in bytes
            numBlocks       number of blocks (zero based) on device to access (??)
            tempFile        File to read data out to

        Returns:
            returncode      if 0, readDrive passed, if 1, readDrive Failed

        Example:
            #>>>

        """
        out = subprocess.Popen(['sudo', 'nvme', 'read', str(device),
                                '--start-block', str(startAddress),
                                '--block-count', str(numBlocks),
                                '--data-size', str(size),
                                '-d', str(tempFile)],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)

        stdout, stderr = out.communicate()
        if (stderr is not None):
            print(stderr)
        if self.debug:
            print(str(stdout))

        return out.returncode

    def readTelemetry(self, device, hostGenerate=True, dataArea=3, outFile='telemetry.bin'):
        """
            Wrapper for nvme-cli telemetry-log.

        Args:
            device             The name of the device to get telemetry log from
            hostGenerate       If True, capture telemetry host-init data of internal state of controller
                                at the time get log page command is processed. If False, don't update data
            dataArea           Defaults to dataArea 3, which returns all data areas. Options: 1,2,3
            outFile            File to print log out to

        Returns:
            returncode      if 0, readDrive passed, if 1, readDrive Failed

        Example:
            #>>>
        """
        commandList = ['sudo', 'nvme', 'telemetry-log', str(device), '--output-file', str(outFile)]

        commandList.append("--host-generate")
        if (hostGenerate is True):
            commandList.append(str(1))
        else:
            commandList.append(str(0))
            # Assuming that --host-generate 0 is equivalent to --controller-init

        commandList.append("--data-area")
        if ((int(dataArea) <= 3) and (int(dataArea) >= 1)):
            commandList.append(str(dataArea))
        else:
            print("Invalid data area: {0}\n".format(dataArea))
            return 1

        print(commandList)
        # run subprocess
        # out = subprocess.Popen(commandList, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = subprocess.Popen(commandList, stdout=tempfile.TemporaryFile(), stderr=subprocess.STDOUT)

        # communicate
        stdout, stderr = out.communicate()
        if (stderr is not None):
            print(stderr)
        if self.debug:
            print(str(stdout))

        return out.returncode

    def testReadDrive(self):
        """
        Assert test for readDrive
        """
        device = '/dev/nvme0n1'
        size = 512
        numBlocks = 0
        startAddress = 0
        assert self.readDrive(device, startAddress, size, numBlocks) == 0, "Failed read {0}".format(device)

    def testReadTelemetry(self):
        """
        Assert test for readTelemetry
        """
        device = '/dev/nvme0n1'
        outFile = "telemetry.bin"
        assert self.readTelemetry(device, outFile=outFile) == 0, "Failed read {0}, telemetry".format(device)

    def testSuite(self):
        """
        One stop call to run tests

        Returns:
            Prints wether tests passed

        Example:
            #>>> ncp = nvmeCliProcesses()
            #>>> ncp.testSuite()
        """
        self.testReadDrive()
        self.testReadTelemetry()


class openParse(object):

    def __init__(self, debug=False):
        """
        Initializes the object.

        Args:
            debug(boolean): Flag to determine if in developer mode.

        Returns:
            None.

        Raises:
            None

        """
        self.debug = debug

    def hybridBinParse(self, uid=None, device="/dev/nvme0n1", outpath="./binaries"):
        """
        Call nvme-cli -> parseTelemetryBin process

        Args:
            uid     Unique identifier of telemetry object
            device  Name of device interface to get data from

        Returns:
            binCache    binaryProcesses object for faster mapping of uid next time
            payload     payload of requested uid

        Example:
                #>>> binCache, payload = hybridBinParse("5", "/dev/nvme0n1")

        """
        p = datetime.datetime.now()
        ncp = nvmeCliProcesses()
        ncp.readTelemetry(device, hostGenerate=True)
        binCache = binProcesses()
        binCache.parseTelemetryBinaryFile(outpath=outpath)

        if uid is not None:
            if self.debug: print("Printing Payload..\n\n")
            payload = binCache.getPayload(uid)
            q = datetime.datetime.now()
            if self.debug: print("\nExecution time: " + str(q - p))
            return binCache, payload
        q = datetime.datetime.now()
        if self.debug: print("\nExecution time: " + str(q - p))
        return binCache, None

    def hybridChachedBinParse(self, binaryCache, uid):
        p = datetime.datetime.now()
        if self.debug: print("Printing Payload..\n\n")
        payload = binaryCache.getPayload(uid)
        q = datetime.datetime.now()
        if self.debug: print("\nExecution time: " + str(q - p))
        return payload

    def nvmeCliBinParse(self, uid="1", telemetryBin="telemetry.bin"):
        """
        get telemetry via nvme-cli, extract uid info only
        """
        if self.debug: print("Not implemented yet")
        pass
        # @TODO: only read from nvme-cli for minimum reads possible

    def nvmeCliPerformanceBinParse(self, uid="1", telemetryBin="telemetry.bin"):
        """
        get telemetry via nvme-cli, extract uid info, but fast
        """
        print("Not implemented yet")
        pass
        # @TODO: only read from nvme-cli for minimum reads possible

    def binParse(self, uid=None, telemetryBin=None, driveNumber=None, outpath="./binaries"):
        """
        Call getTelemetry -> parseTelemetryBin process

        Args:
            uid                Unique identifier of object would like to parse
            telemetryBin       specific file containing telemetry binary to use for read

        Returns:
            binCache    binaryProcesses object for faster mapping of uid next time
            payload     payload of requested uid

        Example:
                #>>> binCache, payload = binParse("5")

        """
        pStartTime = datetime.datetime.now()
        uid = str(uid)
        if (telemetryBin is not None):
            binaryCache = binProcesses(telemetryBin)
        else:
            if driveNumber is None:
                driveNum = input(
                    "Open Twidl Command Prompt to see drive listing\nWhich drive would you like to parse (ex:0-2):")
            else:
                driveNum = driveNumber
            binaryCache = binProcesses()
            binaryCache.readDrive(driveNum=driveNum)
        binaryCache.parseTelemetryBinaryFile(outpath=outpath)
        if uid is not None:
            if self.debug: print("Printing Payload..\n\n")
            payload = binaryCache.getPayload(uid)
            qStopTime = datetime.datetime.now()
            if self.debug: print("\nExecution time: " + str(qStopTime - pStartTime))
            return binaryCache, payload
        qStopTime = datetime.datetime.now()
        if self.debug: print("\nExecution time: " + str(qStopTime - pStartTime))
        return binaryCache, None

    def cachedBinParse(self, binaryCache, uid):
        """
        Faster lookup of getTelemetry -> parseTelemetryBin process, because cached

        Args:
            binCache        binaryProcesses object for faster mapping of uid next time
            uid                Unique identifier of object would like to parse

        Returns:
            payload     payload of requested uid

        Example:
                #>>> binCache, payload = binParse("5")
                #>>> payload = cachedBinParse(binCache, "5")
        """
        p = datetime.datetime.now()
        if self.debug: print("Printing Payload..\n\n")
        payload = binaryCache.getPayload(uid)
        q = datetime.datetime.now()
        if self.debug: print("\nExecution time: " + str(q - p))
        return payload

    def mainAPI(self, debug=False, modeSelect=2, inFile=None):
        """
        A suite of top level tests. Run to see functionality.
        Turn TESTNUM to the desired test.
        """
        selectMin = 1
        selectMax = 4
        selectDefault = 2
        selectTest = None
        payload = None
        if (modeSelect > selectMin) and (modeSelect < selectMax):
            selectTest = modeSelect
        else:
            selectTest = selectDefault

        if self.debug is True or self.debug is False:
            self.debug = debug
        else:
            self.debug = True

        if (selectTest == 1):
            print("== Testing Hybrid and Cached Hybrid Bin Parse==\n")
            binCache, payload = openParse(self.debug).hybridBinParse(uid="5", device="/dev/nvme0n1")
            payload = openParse().hybridChachedBinParse(binCache, "6")
        elif (selectTest == 2):
            print("== Testing Internal and Cached Internal Bin Parse ==\n")
            print("Requires admin permissions.\nRun this with: sudo python {0}\n\n".format(__file__))
            if (inFile is None):
                binaryCache, payload = openParse(self.debug).binParse(uid="5")
            else:
                binaryCache, payload = openParse(self.debug).binParse(uid="5", telemetryBin=inFile)
            payload = openParse(self.debug).cachedBinParse(binaryCache, "6")
        elif (selectTest == 3):
            print("== Testing NVMeCli Bin Parse ==\n")
            openParse().nvmeCliBinParse("5")
        elif (selectTest == 4):
            print("== Testing NVMeCli Performance Bin Parse ==\n")
            openParse().nvmeCliPerformanceBinParse("5")


def main():
    import optparse
    parser = optparse.OptionParser()
    parser.add_option('-d', '--debug', dest='debug', action="store", default=0, help='Enable debug level')
    parser.add_option('-s', '--modeSelect', dest='modeSelect', type="string", default=None, help='Output File Prefix')
    parser.add_option('-inFile', '--inFile', dest='inFile', type="string", default=None, help='Output File Prefix')
    (options, args) = parser.parse_args()
    openParse().mainAPI(debug=options.debug, modeSelect=options.modeSelect, inFile=options.inFile)


if __name__ == '__main__':
    import datetime, traceback

    pStart = datetime.datetime.now()
    try:
        main()
    except Exception as e:
        print("Fail End Process: ", e)
        traceback.print_exc()
    qStop = datetime.datetime.now()
    print("Total Execution time: " + str(qStop - pStart))
