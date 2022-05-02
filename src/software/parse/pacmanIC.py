#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Andrea Chamorro, Joseph Tarango, Daniel Garces
# *****************************************************************************/
"""
This module overlays telemetry binary data over generated data structs and
returns a plain text file, or dynamic initialized object python dictionary
containing the objects' metadata and payload

@author: achamorr, jdtarang, reike, ptran, jmadasse, ssekara, dgarces

Args:
    --bin: String for the path to the directory containing the bin files to be parsed
    --outloc: String for the name of the output file where the Objects' information will be stored as plain text
    --projdir: String for the path to the firmware build directory containing the python parsers
    --debug: Flag to activate debug statements
    --verbose: Flag to activate longer debug statements
    --modeSelect: Integer value for run mode (1=buffDict, 2=autoParsers)

Examples:
    python pacmanIC.py --projdir arbordaleplus_t2 --bin ./sample --debug --verbose --modeSelect 1

"""
from __future__ import absolute_import, division, print_function, unicode_literals
# nested_scopes, generators, generator_stop, with_statement, annotations

import os, re, sys, traceback, datetime
# import ctypes, shutil, time, errno, logging, platform  # telemetry @todo Explicit Usage

### DEBUG LINE ###
# import StringIO, contextlib

from optparse import OptionParser
from src.software.parse.telemetryCmd import TelemetryObjectCommands
from src.software.parse.nlogParser.parseTelemetryNlog import nlogParserAPI


class pacManIC():
    """
    overlays telemetry binary data over generated data structs by ctypeAutoGen

    To use:
    ----------
        pic = pacManIC(bin, projDir, outLoc)
        pic.generateTelemetryObjects()
        pic.printTelemetryObjects()

    or to return Dynamic Dictionary of objects:
        pic.getRunDictionary()

    Attributes:
            binDirectory: String for the path to the directory containing the bin files to be parsed
            projectDir: String for the path to the firmware build directory containing the python parsers
            versionedDir: String for the path to the firmware build directory containing the versioned autoParsers
            unversionedDir: String for the path to the firmware build directory containing the unversioned autoParsers
            outLoc: String for the name of the output file where the Objects' information will be stored as plain text
            debug: Boolean flag to activate debug statements
            verbose: Boolean flag to activate longer debug statements
            mode: Integer value for run mode (1=buffDict, 2=autoParsers)
            moduleList: List of python autoParser modules imported so far
            listFailedObj: List of object names that failed during parsing
            listPassedObjs: List of object names that were successfully parsed
            telemetryObjectsGenerated: List of telemetry objects succesfully parsed
            passedBinFileMetadata: List of bin file metadata for objects that were successfully parsed
            failedBinFileMetadata: List of bin file metadata for objects that were not successfully parsed
            runDictionary: Dictionary containing the parsed objects metadata and payload

    """

    def __init__(self, bin_t=None, projDir=None, nlogLoc=None, nlogDir=None, outLoc=None, debug=False, verbose=False, mode=1):
        """
        function for initializing a pacManIC instance

        Args:
            bin_t: String for the path to the directory containing the bin files to be parsed
            projDir: String for the path to the firmware build directory containing the python parsers
            outLoc: String for the name of the output file where the Objects' information will be stored as plain text
            debug: Boolean flag to activate debug statements
            verbose: Boolean flag to activate longer debug statements
            mode: Integer value for run mode (1=buffDict, 2=autoParsers)

        """
        self.binDirectory = None
        self.projectDir = None
        self.versionedDir = None
        self.unversionedDir = None
        self.outLoc = outLoc
        self.nlogLoc = nlogLoc
        self.nlogDir = nlogDir
        self.debug = debug
        self.verbose = verbose
        self.mode = mode
        self.moduleList = list()
        self.listFailedObj = list()
        self.listPassedObjs = list()
        self.telemetryObjectsGenerated = list()
        self.telemetryHeaders = list()
        self.passedBinFileMetadata = list()
        self.failedBinFileMetadata = list()
        self.runDictionary = dict()

        self.setProjDirectory(projDir)
        self.setBinDirectory(bin_t)

    def setBinDirectory(self, bin_t=None):
        """
        function for checking and setting the path to the directory containing the bin files to be parsed

        Args:
            bin_t: String for the path to the directory containing the bin files to be parsed

        Returns:

        """
        if bin_t is None:
            raise Exception("Please specify binary directory")
        bin_t = os.path.abspath(bin_t)
        if os.path.exists(bin_t):
            self.binDirectory = bin_t
        else:
            raise Exception(f'\nFailed to locate specified bin location: ({bin_t}).')

        print("\nBin Files Directory: %s" % self.binDirectory)

    def setProjDirectory(self, projdir=None):
        """
        function for checking and setting the path to the firmware build directory containing the python parsers

        Args:
            projdir: String for the path to the firmware build directory containing the python parsers

        Returns:

        """
        if projdir is None:
            raise Exception("\nProject object directory not specified. Please specify project directory.")
        else:
            projDir = os.path.abspath(projdir)
            if os.path.exists(projDir):
                self.projectDir = projDir
                sys.path.insert(0, self.projectDir)
            else:
                raise Exception(f'Specified project directory location {self.projectDir} does not exist.')

        print(f"\nProject Directory: {self.projectDir}")

        if self.mode == 1:
            projTelemetryFile = os.path.join(self.projectDir, "telemetry")
            if os.path.exists(projTelemetryFile):
                sys.path.insert(1, r'%s' % (projTelemetryFile))
            else:
                print("\nTelemetry dir %s does not exist" % projTelemetryFile)

        elif self.mode == 2:
            projAutoParsersDir = os.path.join(self.projectDir, "autoParsers")
            if os.path.exists(projAutoParsersDir):
                sys.path.insert(1, r'%s' % projAutoParsersDir)
                projVersionedDir = os.path.join(projAutoParsersDir, "versioned")
                projUnversionedDir = os.path.join(projAutoParsersDir, "unversioned")
                if os.path.exists(projVersionedDir):
                    self.versionedDir = projVersionedDir
                else:
                    print("versioned dir %s does not exist" % projVersionedDir)
                if os.path.exists(projUnversionedDir):
                    self.unversionedDir = projUnversionedDir
                else:
                    print("unversioned dir %s does not exist" % projUnversionedDir)
            else:
                print("autoParsers dir %s does not exist" % projAutoParsersDir)

    def getTelemetryObjects(self):
        """
        function for getting the list of telemetry objects succesfully parsed

        Returns:
            List of telemetry objects succesfully parsed

        """
        return self.telemetryObjectsGenerated

    def getRunDictionary(self):
        """
        function for getting the dictionary with objects' metadata and payload

        Returns:
            Dictionary with objects' metadata and payload

        """
        return self.runDictionary

    def getEntry(self, uid, major, minor, core):
        """
        function for getting an entry in the dictionary for objects' metadata and payload

        Returns:
            Entry in the dictionary for objects' metadata and payload

        """
        return self.runDictionary[uid]["%s.%s" % (major, minor)][core]

    def getModuleList(self):
        """
        function for getting the list of python autoParser modules imported so far

        Returns:
            List of python autoParser modules imported so far

        """
        return self.moduleList

    def getListFailedObjects(self):
        """
        function for getting the list of object names that failed during parsing

        Returns:
            List of object names that failed during parsing

        """
        return self.listFailedObj

    def getListPassedObjects(self):
        """
        function for getting the list of object names that were parsed successfully

        Returns:
            List of object names that were parsed successfully

        """
        return self.listPassedObjs

    def generateTelemetryObjectsAutoParsers(self):
        """
        function for parsing the binary files and extracting their payloads into the run dictionary.
        Assumes that pacManIC instance is running in mode 2 and that the firmware build directory has
        all the parsers contained inside autoParsers/versioned and autoParsers/unversioned

        Returns:

        """
        # specialValidateList = [
        #     'transportStateInfoCTL2_DBank',  # Does not exist in main build.
        #     # 'telemetryHostTime',   Does not exist in main build.
        #     # 'ThermalTelemetry', Does not exist in main build.
        # ]

        if self.mode == 1:
            raise Exception("Running autoParsers method in the wrong mode for the instance of pacmanIC")
        print("\nCreating Telemetry Objects from Binaries...")

        binFilesList = [binFile for binFile in os.listdir(self.binDirectory) if
                        os.path.isfile(os.path.join(self.binDirectory, binFile))]
        if not binFilesList:
            print("\nNo valid bin files in bin file directory!")

        # ===STEP 1: Find Parsers ====
        cwd = self.projectDir
        print("cwd: ", cwd)
        print("versionedDir: ", self.versionedDir)

        # ===STEP 1a: Find Versioned Parsers ====
        modulePath = self.versionedDir
        fileList = os.listdir(modulePath)
        fileList.reverse()
        newFileList = []
        for f in fileList:
            if not f.startswith('NLOG_'):
                newFileList.append(f)
        fileList = newFileList

        for f in fileList:
            if not f.startswith('NLOG_') and re.match("^(\w.+)_(\w+)_(\w+)\.py$", f):
                m = re.match("^(\w.+)_(\w+)_(\w+)\.py$", f)
                if m.group(1) not in self.moduleList:
                    # versionedParserModule = f # @todo does not work if we try to import the file...
                    versionedParserModule = m.group(1)
                    if os.path.exists(os.path.join(modulePath, versionedParserModule)):
                        print(
                            f"Trying to import versioned.{versionedParserModule} as {m.group(1)} @ ModulePath {modulePath}")
                        if self.debug:
                            # if m.group(1) in specialValidateList:
                            #    print("Observe...")
                            print(f" versioned: {versionedParserModule}")
                        self.moduleList.append(m.group(1))  # adds the parser to module list
                        exec(f"import versioned.{versionedParserModule} as {m.group(1)}\n")  # exec, eval

        # ===STEP 1b: Find Unversioned Parsers ====
        modulePath = self.unversionedDir
        fileList = os.listdir(modulePath)
        fileList.reverse()
        for f in fileList:
            if not f.startswith('NLOG_') and re.match("^(\w+)\.py$", f):
                m = re.match("^(\w+)\.py$", f)
                if m.group(1) not in self.moduleList:  # checks if a versioned parser has already been included
                    unversionedParserModule = m.group(1) + '.py'
                    if os.path.exists(os.path.join(modulePath, unversionedParserModule)):
                        print(f"Trying to import unversioned.{m.group(1)} as {m.group(1)} @ ModulePath {modulePath}")
                        if self.debug:
                            # if m.group(1) in specialValidateList:
                            #     print("Observe...")
                            print(f" unversioned: {unversionedParserModule}")
                        self.moduleList.append(m.group(1))  # adds the parser to module list
                        exec(f"import unversioned.{m.group(1)} as {m.group(1)}\n")  # exec, eval

        nlogFiles = []
        for binFile in binFilesList:
            print("binFile: ", binFile)
            objectFilled = False
            myObj = None

            telemetryHeaderName = re.compile('([a-zA-Z0-9_]*)\.TelemetryHeader.txt')

            headerCheck = telemetryHeaderName.match(binFile)

            if headerCheck is None:
                try:
                    # ===STEP 2: Parse Bin File for Meta Data ====
                    # .bin fileName format: <Serial Number> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size> <Data Area> <Core>
                    extractInfoFromFileName = re.compile('([a-zA-Z0-9_]*)\.([0-9]*)\.([0-9]*)\.([0-9]*)\.([a-zA-Z0-9_]*)\.([0-9]*).([0-9]*).([0-9]*)\.bin')
                    fn = extractInfoFromFileName.match(binFile)
                    serial = fn.group(1)
                    uid = fn.group(2)
                    major = fn.group(3)
                    minor = fn.group(4)
                    fwVarName = fn.group(5)
                    byteSize = fn.group(6)
                    dataArea = fn.group(7)
                    core = fn.group(8)
                    version = "%s.%s" % (major, minor)
                except:
                    if self.debug:
                        print("\nFailed to parse meta data from %s" % (binFile))
                    continue

                # if fwVarName in specialValidateList:
                #     print("Observe...")

                # ===STEP 3: parse Telemetry Data from binFile and Fill in Parser ====
                if not fwVarName.startswith('NLOG_'):
                    try:
                        binFilePath = os.path.join(self.binDirectory, binFile)
                        if self.debug:
                            print(f' myObj = {fwVarName}.getUnion(inFile=r"{binFilePath}")')
                        if sys.platform.startswith('win32'):
                            binFilePath = binFilePath.replace("\\", "\\\\")
                        try:
                            myObj = eval(f'{fwVarName}.getUnion(inFile=r"{binFilePath}")')
                        except:
                            exec(f'myObj = {fwVarName}.getUnion(inFile=r"{binFilePath}")')
                        if self.debug:
                            print(" Execution ran successfully...")
                            print(" My object returned to me as: ", myObj)
                        if myObj is not None:
                            objectFilled = True
                    except NameError as e:
                        objectFilled = False
                        if self.debug:
                            print(f" NameError Exception in Pacman!!\n {e}")
                        pass
                    except SyntaxError as e:
                        objectFilled = False
                        if self.debug:
                            print(f" SyntaxError Exception in Pacman!!\n {e}")
                        pass

                    # ===STEP 4: Classify Object and Append to runDictionary ====
                    newVersionDict = dict()
                    newObjDict = dict()
                    newCoreDict = dict()

                    newObjDict["sizeInBytes"] = byteSize
                    newObjDict["bufDictObj"] = myObj  # parser returned
                    newCoreDict[core] = newObjDict
                    newVersionDict[version] = newCoreDict
                    if myObj:
                        self.runDictionary[uid] = newVersionDict

                    if objectFilled:
                        if self.debug:
                            print(" myObj: ", myObj)
                        self.listPassedObjs.append(fwVarName)
                        self.telemetryObjectsGenerated.append(myObj)
                        self.passedBinFileMetadata.append(
                            [serial, uid, major, minor, fwVarName, byteSize, dataArea, core])
                    else:
                        self.listFailedObj.append(fwVarName)
                        self.failedBinFileMetadata.append(
                            [serial, uid, major, minor, fwVarName, byteSize, dataArea, core])
                else:
                    binFilePath = os.path.join(self.binDirectory, binFile)
                    nlogFiles.append(binFilePath)
            else:
                binFilePath = os.path.join(self.binDirectory, binFile)
                self.telemetryHeaders.append(binFilePath)

        nlogStatus = nlogParserAPI(inputfiles=nlogFiles, outputFile=self.nlogLoc,
                                   nlogFormats=self.nlogDir+'/NLog_formats.py',
                                   nlogenum=self.nlogDir+'/nlogEnumParser.py')
        if nlogStatus is False:
            print("NLOG parsing failed |||")

        return

    def printTelemetryObjectsAutoParsers(self, headerUID: int = 240):
        """
        function for printing the telemetry objects and their payloads as plain text. It assumes that pacManIC instance
        is running in mode 2.

        Returns:

        """
        successString = "\n#####################Objects Created Successfully###############################################################\n"
        endString = "\n################################################################################################################\n"
        failString = "\n#####################Objects Not Created Successfully###########################################################\n"

        if self.mode == 1:
            raise Exception("Running autoParsers method in the wrong mode for the instance of pacmanIC")

        if self.verbose:
            print(successString)
            for obj in self.listPassedObjs:
                print(obj, end=', ')
            print(endString)
            print(failString)

            for obj in self.listFailedObj:
                print(obj, end=', ')
            print(endString)

        if self.outLoc:
            print(self.outLoc)
            telemetryObjectsGeneratedFile = open(os.path.abspath(self.outLoc), "w+")
        else:
            telemetryObjectsGeneratedFile = open("telemetryObjectsGenerated.txt", "w+")

        for telemetryHeader in self.telemetryHeaders:
            telemetryHeaderFile = open(telemetryHeader, "r")
            telemetryHeaderContent = telemetryHeaderFile.readlines()
            telemetryHeaderFile.close()
            headerNameFields = telemetryHeaderContent[0].split(":")
            headerSerialFields = telemetryHeaderContent[1].split(":")
            headerName = headerNameFields[1].strip()
            headerSerialNumber = headerSerialFields[1].strip()
            if str(headerSerialNumber) == '0':
                headerSerialNumber = 'IOUNKNOWNSERIALNUM'
            titleStr = f"\n {headerName}, Core   101, Uid   {headerUID}, Major   1, Minor   0, Data Area   0, byte Size   512, {headerSerialNumber} \n"
            telemetryObjectsGeneratedFile.write(endString)
            telemetryObjectsGeneratedFile.write(titleStr)
            telemetryObjectsGeneratedFile.write(endString)
            headerUID += 1
            try:
                telemetryObjectsGeneratedFile.writelines(telemetryHeaderContent)
            except KeyError:
                print("Failed in writing telemetry header")

        for i, successfulObj in enumerate(self.telemetryObjectsGenerated):
            binf = self.passedBinFileMetadata[i]
            titleStr = f"\n {binf[4]}, " \
                       f"Core   {binf[7]}, " \
                       f"Uid   {binf[1]}, " \
                       f"Major   {binf[2]}, " \
                       f"Minor   {binf[3]}, " \
                       f"Data Area   {binf[6]}, " \
                       f"byte Size   {binf[5]},  " \
                       f"{binf[0]} \n"

            telemetryObjectsGeneratedFile.write(endString)
            telemetryObjectsGeneratedFile.write(titleStr)
            telemetryObjectsGeneratedFile.write(endString)

            try:
                dataTemp = successfulObj.getStruct().getStr()
            except Exception as ErrorFound:
                errorString = (f"ERROR in {__file__} @{sys._getframe().f_lineno} with {ErrorFound}\n")
                print(f"{errorString}")

            try:
                dataTemp = successfulObj.getStruct().getStr()
            except Exception as ErrorFound:
                errorString = (f"ERROR in {__file__} @{sys._getframe().f_lineno} with {ErrorFound}\n")
                print(f"{errorString}")

            try:
                telemetryObjectsGeneratedFile.write(successfulObj.getStruct().getStr())
            except KeyError:
                print("Failed in writing")

        # print object report to file
        if self.verbose:
            print(successString)
            for i, obj in enumerate(self.telemetryObjectsGenerated):
                core = self.passedBinFileMetadata[i][7]
                printout = '%s  %s' % (obj, core)
                printout = printout + ","
                if (i + 1) % 5 == 0:
                    printout = printout + "\n"
                print(printout, end='')
            print(endString, failString)

        # PRINT FAILED
        telemetryObjectsGeneratedFile.write(failString)
        countFailedPrint = 0
        printFailWidth = 1
        for i, obj in enumerate(self.listFailedObj):
            if not obj.startswith('NLOG_'):  # @todo
                core = self.failedBinFileMetadata[i][7]
                printout = '%s,  %s' % (obj, core)
                printout = printout + ", "
                if (countFailedPrint + 1) % printFailWidth == 0:
                    printout = printout + "\n"
                telemetryObjectsGeneratedFile.write(printout)
                if self.verbose:
                    print(printout, end='')
                countFailedPrint += 1

        if self.verbose:
            print(endString)
        telemetryObjectsGeneratedFile.write(endString)

        # todo: append new fwVarName.py fwVarName_dict instance if new versioning observed
        return

    def generateTelemetryObjectsBuffDict(self):
        """
        function for parsing the binary files and extracting their payloads into the run dictionary.
        Assumes that pacManIC instance is running in mode 1 and that the firmware build directory has
        all the parsers contained inside telemetry/parsers

        Returns:

        """
        if self.mode == 2:
            raise Exception("Running buffDict method in the wrong mode for the instance of pacmanIC")

        print("\nCreating Telemetry Objects from Binaries...")

        binFilesList = [binFile for binFile in os.listdir(self.binDirectory)
                        if os.path.isfile(os.path.join(self.binDirectory, binFile))]
        if not binFilesList:
            print("\nNo valid bin files in bin file directory!")

        # ===STEP 1: Find Parser ====
        toc = TelemetryObjectCommands()  # todo: store my Objects for later reference

        if toc:
            # ===STEP 2: Parse Bin File for Meta Data ====
            for binFile in binFilesList:
                print("binFile: ", binFile)
                objectFilled = False
                myObj = None

                newVersionDict = dict()
                newObjDict = dict()
                newCoreDict = dict()
                try:
                    # .bin fileName format: <Serial Number> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size> <Data Area> <Core>
                    extractInfoFromFileName = re.compile(
                        "([a-zA-Z0-9_]*)\.([0-9]*)\.([0-9]*)\.([0-9]*)\.([a-zA-Z0-9_]*)\.([0-9]*).([0-9]*).([0-9]*)\.bin")
                    fn = extractInfoFromFileName.match(binFile)
                    serial = fn.group(1)
                    uid = fn.group(2)
                    major = fn.group(3)
                    minor = fn.group(4)
                    fwVarName = fn.group(5)
                    byteSize = fn.group(6)
                    dataArea = fn.group(7)
                    core = fn.group(8)
                    version = f"{major}.{minor}"
                except:
                    if self.debug:
                        print(f"\nFailed to parse meta data from {binFile}")
                    continue

                # ===STEP 3: parse Telemetry Data from binFile and Fill in Parser ====
                try:
                    binFilePath = os.path.join(self.binDirectory, binFile)
                    myObj = toc.parseTelemetry(int(uid), binFilePath, self.projectDir)
                    objectFilled = True

                except Exception as e:
                    if self.debug:
                        print(e)

                # ===STEP 4: Classify Object and Append to runDictionary ====
                newObjDict["sizeInBytes"] = byteSize
                newObjDict["bufDictObj"] = myObj  # parser returned
                newCoreDict[core] = newObjDict
                newVersionDict[version] = newCoreDict
                if myObj:
                    self.runDictionary[uid] = newVersionDict

                if objectFilled:
                    self.listPassedObjs.append(fwVarName)
                    self.telemetryObjectsGenerated.append(myObj)
                    self.passedBinFileMetadata.append([serial, uid, major, minor, fwVarName, byteSize, dataArea, core])
                else:
                    self.listFailedObj.append(fwVarName)
                    self.failedBinFileMetadata.append([serial, uid, major, minor, fwVarName, byteSize, dataArea, core])
        return

    def printTelemetryObjectsBuffDict(self):
        """
        function for printing the telemetry objects and their payloads as plain text. It assumes that pacManIC instance
        is running in mode 1.

        Returns:

        """
        successString = "\n#####################Objects Created Successfully###############################################################\n"
        endString = "\n################################################################################################################\n"
        failString = "\n#####################Objects Not Created Successfully###########################################################\n"

        if self.mode == 2:
            raise Exception("Running buffDict method in the wrong mode for the instance of pacmanIC")

        if self.verbose:
            print(successString)
            for obj in self.listPassedObjs:
                print(obj, end='')
            print(endString)
            print(failString)

            for obj in self.listFailedObj:
                print(obj, end='')
            print(endString)

        if self.outLoc:
            telemetryObjectsGeneratedFile = open(os.path.abspath(self.outLoc), "w+")
        else:
            telemetryObjectsGeneratedFile = open("telemetryObjectsGenerated.txt", "w+")

        for i, successfulObj in enumerate(self.telemetryObjectsGenerated):
            binf = self.passedBinFileMetadata[i]
            titleStr = "\n %s, Core   %s, Uid   %s, Major   %s, Minor   %s, Data Area   %s, byte Size   %s,  %s \n" % \
                       (binf[4], binf[7], binf[1], binf[2], binf[3], binf[6], binf[5], binf[0])
            telemetryObjectsGeneratedFile.write(endString)
            telemetryObjectsGeneratedFile.write(titleStr)
            telemetryObjectsGeneratedFile.write(endString)
            telemetryObjectsGeneratedFile.write(str(successfulObj))

        if self.verbose:
            print(successString)
            for i, obj in enumerate(self.telemetryObjectsGenerated):
                core = self.passedBinFileMetadata[i][7]
                printout = '%s  %s' % (obj, core)
                printout = printout + ","
                if (i + 1) % 5 == 0:
                    printout = printout + "\n"
                print(printout, end='')
            print(endString, failString)

        # PRINT FAILED
        self.listFailedObj = sorted(self.listFailedObj)
        telemetryObjectsGeneratedFile.write(failString)
        for i, obj in enumerate(self.listFailedObj):
            core = self.failedBinFileMetadata[i][7]
            printout = f"{obj}, {core}"
            printout = printout + "; "
            if (i + 1) % 5 == 0:
                printout = printout + "\n"
            telemetryObjectsGeneratedFile.write(printout)
            if self.verbose:
                print(printout, end='')

        if self.verbose:
            print(endString)
        telemetryObjectsGeneratedFile.write(endString)

        # todo: append new fwVarName.py fwVarName_dict instance if new versioning observed
        return

    def getDictionary(self):
        """
        API to create dictionary containing the parsed objects metadata and payload

        Returns:
            Dictionary containing the parsed objects metadata and payload

        """
        self.generateTelemetryObjectsBuffDict()
        d = self.getRunDictionary()
        return d

    def generateTelemetryObjects(self):
        """
        API for parsing the binary files and extracting their payloads into the run dictionary.

        Returns:

        """
        if self.mode == 1:
            self.generateTelemetryObjectsBuffDict()
        elif self.mode == 2:
            self.generateTelemetryObjectsAutoParsers()
        return

    def printTelemetryObjects(self):
        """
        API for printing the telemetry objects and their payloads as plain text.

        Returns:

        """
        if self.mode == 1:
            self.printTelemetryObjectsBuffDict()
        elif self.mode == 2:
            self.printTelemetryObjectsAutoParsers()
        return

    def pacmanICAPI(self):
        """
        API to replace standard command line call (the pacManIC class has to instantiated before calling
        this method)

        Returns:

        """
        self.generateTelemetryObjects()
        self.printTelemetryObjects()
        return


def main():
    """ Parse options and run PacManIC """
    parser = OptionParser()
    parser.add_option("--bin", dest='bin', metavar='<BIN>',
                      help='Binary to parse name')
    parser.add_option("--outloc", dest='outloc', metavar='<OUTLOC>', default=None,
                      help='File to output the created telemetry objects')
    parser.add_option("--projdir", dest='projdir', metavar='<PROJDIR>', default=None,
                      help='Project Location')
    parser.add_option("--debug", action='store_true', dest='debug', default=False, help='Debug mode.')
    parser.add_option("--verbose", action='store_true', dest='verbose', default=False,
                      help='Print Objs Data to Command Prompt')
    parser.add_option("--modeSelect", dest='mode', default=False,
                      help='Integer for parsing mode (1=buffDict, 2=autoParsers)')

    (options, args) = parser.parse_args()

    pic = pacManIC(outLoc=options.outloc, debug=options.debug, verbose=options.verbose, bin_t=options.bin,
                   projDir=options.projdir, mode=options.mode)
    pic.pacmanICAPI()


if __name__ == '__main__':
    """Performs execution delta of the process."""
    pStart = datetime.datetime.now()
    try:
        main()
    except Exception as errorMain:
        print("Fail End Process: {0}".format(errorMain))
        traceback.print_exc()
    qStop = datetime.datetime.now()
    print("Execution time: " + str(qStop - pStart))
