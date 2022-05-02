#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
# Purpose: Automates reserving and updating local and master datacontrol.h file when new structure instances appear

import sys, os, re, copy, argparse, shutil, platform, getpass, csv, stat
import time, datetime, traceback
# from tqdm import tqdm

# import validation.dataControlValidation as dataControlValidation
from validation.dataControlValidation import *

##########Flag Modes######################
UNIT_TESTING = True
DEBUG = False
REPODIR = None
##########Global Variables######################
# For Telemetry Versions, see test/datacontrolValidation

DOXYGEN_COMMENT_SYMBOL = "///<"
E_UNIQUE_IDENTIFIER_END_SYMBOL = "} eUniqueIdentifier"
TAB = "    "
CSV_EXPECTED_NUMBER_OF_COLUMNS = 19
H_EXPECTED_NUMBER_OF_COLUMNS = 5

# for ssddev-meta handling
REMOTE_GIT_REPO = r"ssh://git@nsg-bit.intel.com:7999/fsedev/ssddev-meta.git"  # \DATACONTROL to manage uids
dataControlGenVersion = 1

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Sequences used in matching. Use precompiled version to accelerate code.
matchSequence = [None] * 12  # Assign size  to the array

matchSequence[2] = re.compile(
    "(?:\/\/ *(TEMP|DEPRECATED) *:)? *(.*?) *= * (.*?) *, *\/\/\/< *([0-9]+) *, *(.*), *([a-zA-Z]*)")
matchSequence[3] = re.compile("\/\/\/<.*?version *([a-z0-9._]+)")

matchSequence[5] = re.compile("^temp_[a-zA-Z0-9_]+$")
matchSequence[6] = re.compile("((?:.*)),((?:.*)),((?:.*)),((?:.*)),((?:.*)),((?:.*))")
matchSequence[7] = re.compile("((?:.*)),((?:.*)),((?:.*))")
matchSequence[8] = re.compile("(.*) *: *\((?:.*)\)\Z")


############Supporting Function Definitions###############

def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def uidSort(uidNum):
    try:
        return int(uidNum)  # sort numerically
    except ValueError:
        return uidNum  # sort alphabetically
    throwUidError()


def uidTempSort(uidNum):
    if (matchSequence[5].match(uidNum)):
        try:
            return int(uidNum.replace("temp_", ""))  # sort numerically
        except:  # could not convert to int
            return uidNum  # sort alphabetically
    else:
        throwUidError(uidNum)


def sizeInDec(sizeInHex):
    try:
        if sizeInHex == "":
            return sizeInHex
        else:
            size = sizeInHex.replace("0x", "")
            size = int(size, 16)
            return size
    except Exception as e:
        throwTraceback(e)


##################################################


# A class to represent a uid in the datacontrol and source files
# The ordering and equivalence between two uid objects is soley determined by the uid
class UID:
    def __init__(self, uidNum, structName, dataArea, dataGroup, version=TELEMETRY_VERSION_2, implemented=False,
                 deprecated=False, temp=False):
        self.uidNum = validateString(uidNum)
        self.structName = validateString(structName)
        self.dataArea = validateString(dataArea)
        self.dataGroup = validateString(dataGroup)
        self.version = validateVersion(version)

        self.implemented = implemented
        self.deprecated = deprecated
        # temp validation
        if matchSequence[5].match(self.uidNum):
            temp = True
        self.temp = temp

        self.classVariables = ["uidNum", "structName", "dataArea", "dataGroup", "version"]

    def varConstructor(self):
        printList = []
        for var in self.classVariables:
            exec("printList.append(self.%s)" % var)
        return printList

    # Alternate representations
    def __gt__(self, other):
        try:
            return int(self.uidNum) > int(other.uidNum)  # sort numerically
        except ValueError:
            return self.uidNum > other.uidNum  # sort alphabetically
        throwUidError(other)

    def __lt__(self, other):
        try:
            return int(self.uidNum) < int(other.uidNum)  # sort numerically
        except ValueError:
            return self.uidNum < other.uidNum  # sort alphabetically
        throwUidError(other)

    def __eq__(self, other):
        try:  # @todo: test this works
            for var in self.classVariables:
                exec("if self.%s != other.%s: return False" % var)
            return True
        except AttributeError:
            return False
        except Exception as e:
            throwTraceback(e)


class cUID(UID):
    def __init__(self, uidNum, structName, dataArea, dataGroup, product, autoparsability="", \
                 major=0, minor=0, persistence="unknownPersistence", dependency="unknownDependency", \
                 securityClass="unknownClassification", byteSize="", structDup="unknownDuplication", \
                 size="", withinAssert="", domain="unknownDomain", \
                 owner="", description="", autoParse="No", version=TELEMETRY_VERSION_2, implemented=False,
                 deprecated=False, temp=False):

        # required at initialization
        UID.__init__(self, uidNum, structName, dataArea, dataGroup, version=version, implemented=implemented,
                     deprecated=deprecated, temp=temp)
        self.product = validateString(product)

        # Used to maintain ordering of class variables
        self.classVariables = ["uidNum", "version", "autoparsability", "major", "minor", \
                               "persistence", "dependency", "securityClass", "byteSize", "dataArea", \
                               "structDup", "dataGroup", "structName", "size", "withinAssert", \
                               "product", "domain", "owner", "description"]
        if len(self.classVariables) != CSV_EXPECTED_NUMBER_OF_COLUMNS:
            failString = "Make sure CSV class Variables matches expected number of Columns: %s! See code.." % CSV_EXPECTED_NUMBER_OF_COLUMNS
            throwFormatError(failString)

        # optional at initialization
        self.autoparsability = validateString(autoparsability)
        self.major = validateString(major)
        self.minor = validateString(minor)
        self.persistence = validateString(persistence)
        self.dependency = validateString(dependency)
        self.securityClass = validateString(securityClass)

        self.size = validateString(size)
        if self.size != "":
            self.byteSize = sizeInDec(validateString(size))
        else:
            self.byteSize = validateString(byteSize)

        self.structDup = validateString(structDup)
        self.withinAssert = validateString(withinAssert)
        self.domain = validateString(domain)
        self.owner = validateString(owner)
        self.description = validateString(description)

    def __str__(self):  # @todo: check this prints correct formatting
        uidString = ""

        formatTable = ["%5s", "%4s", "%10s", "%3s", "%5s", \
                       "%22s", "%20s", "%16s", "%7s", "%4s", \
                       "%20s", "%14s", "%23s", "%10s", "%5s", \
                       "%10s", "%12s", "%21s", "%s"]
        for i, var in enumerate(self.varConstructor()):
            formattedString = ((formatTable[i] + ",") % var)
            uidString += formattedString
        # uidString += "\n"
        return uidString

    def asDict(self):
        dictString = "dict("
        dictionaryItems = ["major", "minor", "ctypeStructure", "owner", "description", "byteSize"]
        for i, item in enumerate(dictionaryItems):
            if item == "ctypeStructure":
                formattedEntry = "%s = r'%s'," % (item, self.structName)  # todo: identify with uid rather than name
            else:
                exec("itemLiteral = self.%s" % (item))
                formattedEntry = "%s= '%s'," % (item, itemLiteral)
            dictString += formattedEntry
        dictString += ")"
        return dictString


class hUID(UID):
    def __init__(self, uidNum, structName, dataArea, dataGroup, autoParse="No", line=None, version=TELEMETRY_VERSION_2,
                 implemented=False, deprecated=False, temp=False):
        UID.__init__(self, uidNum, structName, dataArea, dataGroup, version=version, implemented=implemented,
                     deprecated=deprecated, temp=temp)
        self.autoParse = validateString(autoParse)
        self.line = validateString(line)

        # 5 per line for easy counting
        self.classVariables = ["structName", "uidNum", "dataArea", "dataGroup", "autoParse"]

        if len(self.classVariables) != H_EXPECTED_NUMBER_OF_COLUMNS:
            failString = "Make sure H class Variables matches expected number of Columns: %s! See code.." % H_EXPECTED_NUMBER_OF_COLUMNS
            throwFormatError(failString)

    def __str__(self):
        uidString = "%s" % TAB

        statusFlag = ""
        if self.temp:
            statusFlag = "// TEMP: "
        if self.deprecated:
            statusFlag = "// DEPRECATED: "
        uidString += statusFlag

        formatTable = ["%-41s", "=%21s,", "%11s,", "%19s,", "%13s"]
        for i, var in enumerate(self.varConstructor()):
            if i == 2:
                uidString += " %4s" % DOXYGEN_COMMENT_SYMBOL
            formattedString = (formatTable[i] % var)
            uidString += formattedString
        uidString += "\n"
        return uidString

    def __repr__(self):
        uidString = "%s" % TAB
        formatTable = ["%-41s", "=%21s,", "%11s,", "%19s,", "%13s"]
        for i, var in enumerate(self.varConstructor()):
            if i == 2:
                uidString += " %4s" % DOXYGEN_COMMENT_SYMBOL
            formattedString = (formatTable[i] % var)
            uidString += formattedString
        # uidString += "\n"
        return uidString


class DatacontrolGen:

    # ==================================================
    # Initializing Methods
    # ==================================================

    def __init__(self, file):
        self.file = file
        self.fileHeader = ""

        self.uidMasterDictV1 = {}
        self.uidMasterDictV2 = {}

        # Classifies the uids information extracted from datacontrol.h
        # self.implemented              =[]

        self.editViolations = []
        self.createViolations = []
        self.implementViolations = []

    # ==================================================
    # Supporting Methods
    # ==================================================
    # def used(self):
    # return self.deprecated + self.implemented

    # ==================================================
    # Comparing Instances of dataControlGen class
    # ==================================================

    def compareDicts(self, local, remote):
        local_adds = []
        remote_adds = []
        diffs = []
        if DEBUG:
            print("===UID Local vs Remote ===\n")
        if len(local.keys()) > len(remote.keys()):
            for uidNum in local.keys():
                if uidNum not in remote.keys():
                    uid_remote = ""
                    local_adds.append(uidNum)
                else:
                    uid_remote = remote[uidNum]
                if not local[uidNum].compare(uid_remote):
                    diffs.append(uidNum)
                    if DEBUG:
                        print("===local===\n")
                        print(local[uidNum])
                        print("===remote===\n")
                        print(uid_remote)
                        print("============\n")
        else:
            for uidNum in remote.keys():
                if uidNum not in local.keys():
                    uid_local = ""
                    remote_adds.append(uidNum)
                else:
                    uid_local = local[uidNum]
                if not uid_local.compare(remote[uidNum]):
                    diffs.append(uidNum)
                    if DEBUG:
                        print("===local===\n")
                        print(uid_local)
                        print("===remote===\n")
                        print(remote[uidNum])
                        print("============\n")
        return local_adds, remote_adds, diffs

    def compareObjs(self, remote):
        '''
        Could be used to automatically resolve local and remote datacontrol.h merge conflicts
        '''
        v1_local_adds, v1_remote_adds, diffs1 = self.compareDicts(self.uidMasterDictV1, remote.uidMasterDictV1)

        v2_local_adds, v2_remote_adds, diffs2 = self.compareDicts(self.uidMasterDictV2, remote.uidMasterDictV2)

        (v1_local_adds + v2_local_adds), (v1_remote_adds + v2_remote_adds), (diffs1 + diffs2)


class DatacontrolGenH(DatacontrolGen):
    def __init__(self, file, overwrite=None):
        DatacontrolGen.__init__(self, file)  # not working for some reason

        self.eUidEnumStart = 0
        self.eUidEnumEnd = 0

        self.overwrite = overwrite
        self.readFile()

    # ==================================================
    # Read/Input Methods
    # ==================================================

    def readFile(self):
        """
        Extracts telemetry uid objects from datacontrol.h
        Pass in no argument to automatically search for local datacontrol.h, pass in argument for master datacontrol.h location"""

        print("==Reading H File.")

        if not self.file or not os.path.exists(self.file):
            print("Could not generate telemetry Object List \n%s file not found\n" % self.file)
            quit(1)

        version = ""
        commentFlag = ""

        # Process datacontrol.h to extract complete uid list
        try:
            with open(self.file, 'r') as iFile:
                lines = iFile.readlines()

            for i in range(len(lines)):
                if ('typedef enum' in lines[i]):
                    self.eUidEnumStart = i + 1
                # ========Edit Local Functinality============
                if not self.overwrite:
                    if (matchSequence[3].match(lines[i].lower().strip())):  # match " ///< ... version XX.XX "
                        m = matchSequence[3].match(lines[i].lower().strip())
                        version = validateVersion(m.group(1))
                    elif (matchSequence[2].match(lines[
                                                     i].strip())):  # match "uid_(NAME)_e ... (or optionally (NAME) ...) = ... (NUM), ... ///< ... (AREA), ... (GROUP), optionally "//RESERVED: uid_NAME_e... "
                        m = matchSequence[2].match(lines[i].strip())
                        commentFlag = validateString(m.group(1))
                        structName = validateString(m.group(2))
                        uidNum = validateString(m.group(3))  # not necessarily an int
                        dataArea = validateString(m.group(4))
                        dataGroup = validateString(m.group(5))
                        autoParse = validateString(m.group(6))
                        line = i + 1
                        if DEBUG:
                            print("%s %s %s %s %s %s %s" % (
                            uidNum, structName, dataArea, dataGroup, version, line, commentFlag))

                        if version == TELEMETRY_VERSION_1:
                            self.uidMasterDictV1[uidNum] = uid
                        elif version == TELEMETRY_VERSION_2:
                            self.uidMasterDictV2[uidNum] = uid
                        else:
                            throwVersionError(version)
                        # end goal #1, allows us to have list of datacontrol objs.

                        # create uid
                        uid = hUID(uidNum, structName, dataArea, dataGroup, autoParse, line, version)

                        # classify uid
                        if commentFlag == "":
                            uid.implemented = True
                        elif commentFlag == "// DEPRECATED":
                            uid.deprecated = True
                        elif commentFlag == "// TEMP":
                            uid.temp = True
                        else:
                            throwClassificationError(uidNum)

                        # self.implemented.append(uidNum)

                # ======================================
                if (E_UNIQUE_IDENTIFIER_END_SYMBOL in lines[i]):
                    self.eUidEnumEnd = i
                    break
            return self.eUidEnumStart, self.eUidEnumEnd
        except Exception as e:
            print("Failed while reading H File")
            throwTraceback(e)

    # ==================================================
    # CSV Editing Methods
    # ==================================================
    def convertToH(self, dict):
        tempDict = {}
        for uidNum in dict.keys():
            uid = dict[uidNum]
            tempDict[uidNum] = hUID(uid.uidNum, uid.structName, uid.dataArea, uid.dataGroup, uid.product,
                                    version=uid.version, implemented=uid.implemented, deprecated=uid.deprecated,
                                    temp=uid.temp)
        return tempDict

    def matchWithCSV(self, csvObject):
        self.uidMasterDictV1 = self.convertToH(csvObject.uidMasterDictV1)
        self.uidMasterDictV2 = self.convertToH(csvObject.uidMasterDictV2)

        # self.editViolations = csvObject.editViolations
        # self.createViolations = csvObject.createViolations

        # self.implemented = csvObject.implemented

    # ==================================================
    # Write/Output Methods
    # ==================================================

    def updateFile(self):
        uids_outV1 = sorted(self.uidMasterDictV1.keys(), key=uidSort)
        uids_outV2 = sorted(self.uidMasterDictV2.keys(), key=uidSort)
        uids_out = uids_outV1 + uids_outV2
        # todo: move towards only having telemetry v2

        dicts = [self.uidMasterDictV1, self.uidMasterDictV2]
        uidList = [uids_outV1, uids_outV2]

        if DEBUG:
            print("UIDs Found\n")
            print(uids_out)

        if uids_out is None or uids_out == []:
            print("No UIDs read, aborting...\n")
            quit(8)

        # @todo: might be nice to support creating datacontrol.h from scratch        

        try:
            with open(self.file, "r") as file:
                lines = file.readlines()

            filename, file_extension = os.path.splitext(self.file)
            copyFile = filename + "_dup" + file_extension  # todo: update name correctly
            if DEBUG:
                print("Writing to location: %s" % copyFile)

            with open(copyFile, "w") as f:
                i = 0
                while i < len(lines):
                    # rewrite when get to datacontrol struct
                    if (i > self.eUidEnumStart) and (i < self.eUidEnumEnd):
                        for i, uidDict in enumerate(dicts):
                            # print every time new version encountered
                            f.write("%s///< Telemetry version %s.0 backwards compatibility.\n" % (TAB, str(i + 1)) + \
                                    "%s//****************************************************************************************************************\n" % (
                                        TAB) + \
                                    "%s//   Structure Instance,                                    UID, ///<  Data Area,         Data Group,   Auto-parse\n" % (
                                        TAB) + \
                                    "%s//****************************************************************************************************************\n" % (
                                        TAB))

                            for uidNum in uidList[i]:
                                try:
                                    uid = uidDict[uidNum]

                                    if "temp_" in uidNum:  # @todo: sequence search
                                        # TEMP UIDs AS COMMENT
                                        f.write("%s// TEMP:%s\n" % (TAB, uidNum))
                                    elif uid.deprecated:
                                        # DEPRECATED UIDs AS COMMENT
                                        f.write("%s// DEPRECATED:%s\n" % (TAB, uidNum))
                                    else:
                                        f.write(str(uid))  # see hUID for print formatting
                                except:
                                    f.write("%s// ERROR:%s\n" % (TAB, uidNum))
                                    continue
                        i = self.eUidEnumEnd
                    else:
                        line = lines[i]
                        f.write(line)
                        i += 1
            # copyFile close

            # replace original if writing was successfull
            os.remove(self.file)
            os.rename(copyFile, self.file)

            print("Completed updating datacontrol.h\n\n")
        except Exception as e:
            # keep original version
            print("Failed while updating datacontrol.h\n\n")
            file.close()
            f.close()
            if os.path.exists(copyFile):
                os.remove(copyFile)
            throwTraceback(e)


class DatacontrolGenCSV(DatacontrolGen):
    def __init__(self, file, tempMetaRepo=None):
        DatacontrolGen.__init__(self, file)

        self.tempMetaRepo = tempMetaRepo

        self.deprecateViolations = []

        self.readFile()

    def getDicts(self):
        return self.uidMasterDictV1, self.uidMasterDictV2

    def getDict(self):
        return self.uidMasterDictV2

    def uidInitByList(self, list):
        '''
        Performs List Validation. Whenever creating UIDs, ensure Input Validation
        '''

        c_dict = {'uidNum': 0,
                  'structName': 12,
                  'dataArea': 9,
                  'dataGroup': 11,
                  'product': 15,
                  }

        uid = cUID(list[c_dict['uidNum']], list[c_dict['structName']], list[c_dict['dataArea']],
                   list[c_dict['dataGroup']], list[c_dict['product']])

        # Initialize object information
        uid.uidNum = validateString(list[0])
        uid.version = validateVersion(list[1])
        uid.autoparsability = validateString(list[2])
        uid.major = validateString(list[3])
        uid.minor = validateString(list[4])
        uid.persistence = validateString(list[5])
        uid.dependency = validateString(list[6])
        uid.securityClass = validateString(list[7])
        uid.dataArea = validateString(list[9])
        uid.structDup = validateString(list[10])
        uid.dataGroup = validateString(list[11])
        uid.structName = validateString(list[12])
        # @review: what is the maximum hex that would be logical?
        uid.size = validateString(list[13])
        try:
            uid.byteSize = sizeInDec(validateString(list[13]))
        except ValueError:  # input not in dec convertable format
            uid.byteSize = validateString(list[8])
        uid.withinAssert = validateString(list[14])
        uid.product = validateString(list[15])
        uid.domain = validateString(list[16])
        uid.owner = validateString(list[17])
        uid.description = validateString(list[18])

        return uid

    # ==================================================
    # Read/Input Methods
    # ==================================================

    def readFile(self):
        '''
        Reads CSV file to create uid objects
        '''
        print("==Reading CSV.", )

        try:
            with open(self.file, "r") as csv_file:
                reader = csv.reader(csv_file)
                # pop first header line
                self.csvHeader = reader.next()

                for i, csvLineAsList in enumerate(reader):
                    if len(csvLineAsList) - 1 != CSV_EXPECTED_NUMBER_OF_COLUMNS:  # @todo: fix EOL logic
                        failString = "CSV line %s does not have number of columns expected(%s): %s. Fix before Proceeding.." % (
                        i + 1, CSV_EXPECTED_NUMBER_OF_COLUMNS, len(csvLineAsList))
                        throwFormatError(failString)

                    # Step 1: Create uid, Validate list
                    uid = self.uidInitByList(csvLineAsList)

                    # Step 2: Set UID status
                    if uid.product == "Deprecated":  # @todo: Deprecated turns product to deprecated
                        uid.deprecated = True
                        # self.deprecated.append(uid.uidNum)
                    else:
                        uid.implemented = True
                        # self.implemented.append(uid.uidNum)

                    # Step 3: add UID to respective Dictionary
                    if uid.version == TELEMETRY_VERSION_1:
                        uid_dict = self.uidMasterDictV1
                    elif uid.version == TELEMETRY_VERSION_2:
                        uid_dict = self.uidMasterDictV2
                    else:
                        throwVersionError(uid.version)

                    uid_dict[uid.uidNum] = uid
                print("done.==\n")
        except Exception as e:
            print("Failed while reading csv. No changes made.")
            throwTraceback(e)

    # ==================================================
    # CSV Editing Methods
    # ==================================================
    def getAvailableTemp(self):
        '''
        Parse list of UID's to find next available UIDs. It is vital that UIDs, even if deprecated, never get reused, for consistency across versions and appropriate tagging.
        '''
        try:
            usedNums = []
            usedStrings = []
            # classify into string or number string

            tempListV1 = [uidNum.replace("temp_", "") for uidNum in self.uidMasterDictV1.keys() if
                          matchSequence[5].match(uidNum)]
            tempListV2 = [uidNum.replace("temp_", "") for uidNum in self.uidMasterDictV2.keys() if
                          matchSequence[5].match(uidNum)]
            tempList = set(tempListV1 + tempListV2)

            for uidNum in tempList:  # growth occurs only in lastest Version
                try:
                    uidToInt = int(uidNum)
                    usedNums.append(uidNum)
                except ValueError:
                    usedStrings.append(uidNum)

            if DEBUG:
                print("===UIDs Not Available===")
                print(usedNums, usedStrings)

            # look through sorted set of nums
            usedNums = sorted(list(set(usedNums)), key=uidSort)

            # @todo: check for empty datacontrol struct
            # check each one is sequential
            for i, uid in enumerate(usedNums):
                if uid != str(i):
                    if str(i) not in set(tempList):
                        uidNext = "temp_" + str(i)  # found open UID
                        return uidNext
                    else:
                        print(
                            "Found duplicate UID temp_%s. Fix error before proceeding\n" % uid)  # todo: will never trigger because set
                        print("No changes made\n")
                        quit(7)
            # went through all and found no open spot. Append to end
            uidNext = "temp_" + str(len(usedNums))
            return uidNext
        except Exception as e:
            print("Failed while getting Temp uid")
            throwTraceback(e)

    def implement(self):
        '''
        Responsible for assigning uids to newly defined structs in CSV file  and editing uid meta information in remote database to include newly created uids.
        '''
        # @todo: compare local with remote, ask to confirm changes made

        # import Meta Functionalities
        newlyImplemented = []
        print("\n==Implementing...")
        try:
            dataControlRepo = os.path.join(self.tempMetaRepo, "DATACONTROL")
            sys.path.append(dataControlRepo)
            from src.software.datacontrol.dataControlGen import dataControlGenMeta

            # read remote
            uidMetaFile = os.path.join(dataControlRepo, 'structures_meta.csv')
            if os.path.exists(uidMetaFile):
                dcm = dataControlGenMeta(uidMetaFile, debug=DEBUG)

                # update CSV,assigning permanent UIDs to temps
                for uidNum in self.uidMasterDictV2.keys():
                    uid = self.uidMasterDictV2[uidNum]
                    if uid.temp == True:
                        newNum = dcm.getAvailableUID()
                        if newNum is None:
                            print("\nFAILED to implement: %s, skipping...\n" % (uidNum))
                            continue
                        # add to Master List
                        if newNum not in self.uidMasterDictV2.keys():
                            newUid = uid
                            newUid.uidNum = newNum
                            newUid.implemented = True
                            self.uidMasterDictV2[newNum] = newUid
                        else:
                            print(
                                "\nERROR:tried to implement uid that already exists in local CSV: %s. Should never happen (fix before proceeding)\n" % newNum)
                            quit(5)

                        # delete temporary
                        # self.implemented.append(uidNum)
                        self.uidMasterDictV2[uidNum].deprecated = True
                        # self.deprecated.append(uidNum)

                        # update meta Dict
                        dcm.create(newNum)
                        newlyImplemented.append((uidNum, newNum))
                        if DEBUG:
                            print("\nSUCCESS Implementing (%s): %s\n" % (newNum, newUid.structName))
                    else:
                        continue
                dcm.updateMeta()
                print("done.==\n")
                return newlyImplemented
            else:
                throwIOError(uidMetaFile)
        except Exception as e:
            # keep original version
            print("Failed while Implementing. No Changes Made.==\n")
            throwTraceback(e)

    def create(self, tempUid, structName, dataArea, dataGroup, product):
        '''
        Similar to edit, but creates new uid if temp and if not previously defined. Call BEFORE creating FW code to ensure compatibility of uid with code.
        '''
        tempUid = validateString(tempUid)

        if tempUid not in self.uidMasterDictV1.keys() and tempUid not in self.uidMasterDictV2.keys():
            if matchSequence[5].match(tempUid):  # todo: make a call-time check
                uid = cUID(tempUid, structName, dataArea, dataGroup, product, temp=True)
                self.uidMasterDictV2[tempUid] = uid
                # self.implemented.append(tempUid)
                return True
            print(
                "Edit not made: new uid referenced: %s, and it was not a tempUid. If you want to create a new uid, you must use a uid in format: 'temp_UIDNUMBER'\n" % tempUid)
        else:
            print("Can't create a uid with uid %s because it already exists. Skipping..." % (tempUid))
        # self.createViolations.append(tempUid) # @review: Don't know whether to hard stop or push through
        # return False

    def edit(self, uidNum, currVersion, autoparsability=None, \
             major=None, minor=None, persistence=None, dependency=None, \
             securityClass=None, byteSize=None, dataArea=None, structDup=None, \
             dataGroup=None, structName=None, size=None, withinAssert=None, product=None, domain=None, \
             owner=None, description=None):
        '''
        Makes local changes only. Call implement to push changes to remote database
        '''
        # get uid
        uidNum = validateString(uidNum)
        currVersion = validateVersion(currVersion)

        if str(currVersion) == TELEMETRY_VERSION_1:
            uid = self.uidMasterDictV1.get(uidNum)
        elif str(currVersion) == TELEMETRY_VERSION_2:  # version 2.0
            uid = self.uidMasterDictV2.get(uidNum)
        else:
            throwVersionError(uidNum)

        if uid:
            # uid.edited = True

            if structName:
                uid.structName = validateString(structName)
            if dataArea:
                uid.dataArea = validateString(dataArea)
            if dataGroup:
                uid.dataGroup = validateString(dataGroup)
                # @todo: make version editable
            """if version:
                uid.version = version"""

            if autoparsability:
                uid.autoparsability = validateString(autoparsability)
            if major:
                uid.major = validateString(major)
            if minor:
                uid.minor = validateString(minor)
            if persistence:
                uid.persistence = validateString(persistence)
            if dependency:
                uid.dependency = validateString(dependency)
            if securityClass:
                uid.securityClass = validateString(securityClass)
            if structDup:
                uid.structDup = validateString(structDup)
            if size:
                uid.size = validateString(size)
                uid.byteSize = sizeInDec(validateString(size))
            elif byteSize:
                uid.byteSize = validateString(byteSize)
            if withinAssert:
                uid.withinAssert = validateString(withinAssert)
            if product:
                uid.product = validateString(product)
            if domain:
                uid.domain = validateString(domain)
            if owner:
                uid.owner = validateString(owner)
            if description:
                uid.description = validateString(description)
        else:
            print("UID %s not found in Version %s Master Dict. Not edited...\n" % (uidNum, curr_version))
            self.editViolations.append((uidNum, curr_version))  # todo: Add edit string?
            throwUidError(uidNum)

    def deprecate(self, uidNum, version):
        '''
        Deprecating is merely a state where there is no product/subbuilds information for a structure.
        '''
        uidNum = validateString(uidNum)
        version = validateVersion(version)
        if version == TELEMETRY_VERSION_1:
            uid = self.uidMasterDictV1.get(uidNum)
            uidDict = self.uidMasterDictV1
        elif version == TELEMETRY_VERSION_2:
            uid = self.uidMasterDictV2.get(uidNum)
            uidDict = self.uidMasterDictV2
        else:
            throwVersionError(version)

        if uid:
            if uid.implemented:
                print("Deprecating object (%s): %s.. " % (uidNum, uid.structName))
                # self.deprecated.append(uidNum)
                uidDict[uidNum].product = "Deprecated"  # not implemented in any product
                uidDict[uidNum].deprecated = True
                # uid.implemented = True
                # uid.reserved = False
                print("done. \n")
                return uidNum
            else:
                print("Cannot deprecate uid (%s) because it has not been implemented\n" % uidNum)

        print(
            "DEPRECATE CONFLICT: uid (%s) in Telemetry version %s not found, cannot implement uid that has not been implemented\n" % (
            uidNum, version))
        self.deprecateViolations.append((uidNum, version))
        return None

    # ==================================================
    # Write/Output Methods
    # ==================================================
    def updateFile(self):
        # Step 1: Create CSV File
        if not os.path.exists(self.file):
            throwIOError(self.file)

        uids_outV1 = sorted(self.uidMasterDictV1.keys(), key=uidSort)
        uids_outV2 = sorted(self.uidMasterDictV2.keys(), key=uidSort)
        uids_out = uids_outV1 + uids_outV2
        # todo: move towards only having telemetry v2

        dicts = [self.uidMasterDictV1, self.uidMasterDictV2]
        uidList = [uids_outV1, uids_outV2]

        if uids_out is None or uids_out == []:
            print("No UIDs read, quitting...\n")
            throwIOError(self.file)

        print("==Updating CSV...")
        filename, file_extension = os.path.splitext(self.file)
        csv_copy_name = filename + "_dup" + file_extension
        try:
            csv_copy = open(csv_copy_name, "w")
            csv_writer = csv.writer(csv_copy)
            csv_writer.writerow(self.csvHeader)

            # Step 2:
            # all_uids = sorted(list(set(self.used())), key = uidSort)

            if DEBUG:
                print("UIDs Found\n")
                print(uids_out)

            filename, file_extension = os.path.splitext(self.file)
            copyFile = filename + "_dup" + file_extension  # todo: update name correctly
            if DEBUG:
                print("Writing to location: %s" % copyFile)
            for i, uid_dict in enumerate(dicts):
                # Permanent UIDs
                for uidNum in uidList[i]:
                    uid = uid_dict[uidNum]

                    # @ todo: handle deprecated temp UIDs. If temp and deprecated, remove from tracker file, don't implement

                    if DEBUG:
                        print(uid)
                    csv_writer.writerow(uid.varConstructor())  # @todo: Format output
            csv_copy.close()  # vital before remove, rename

            os.remove(self.file)
            os.rename(csv_copy_name, self.file)
            print("Completed updating structures.csv.\n\n")
        except Exception as e:
            csv_copy.close()
            throwTraceback(e)
            print("Failed while updating structures.csv\n\n")

    def updatePythonDict(self):
        '''
        Function to initialize uid python dicts in REMOTE location
        '''
        sys.path.append(self.tempMetaRepo)
        from structures_dict import dataControlDict

        appendList = []
        t = datetime.datetime.now()
        time = t.strftime("%d-%m-%Y %H:%M:%S")
        # pyOutFile.write("'''Auto Generated by dataControlGenMain.py. Current as of %s'''\n\n. Do not edit manually." % time)
        # pyOutFile.write("dataControlDict = {\n")
        for uidNum in sorted(self.uidMasterDictV2.keys(), key=uidSort):
            uid = self.uidMasterDictV2[uidNum]
            versioningKey = "(%s,%s,%s)" % (uidNum, uid.major, uid.minor)
            # REMOTE
            if not dataControlDict.get(versioningKey):
                appendList.append("%s : %s\n" % (versioningKey, str(uid)))  # @todo: account for multiple spaces

        dictPyFile = os.path.join(self.tempMetaRepo, "DATACONTROL\structures_dict.py")

        if UNIT_TESTING:
            # DICT PY
            filename, file_extension = os.path.splitext(dictPyFile)
            testDictPyFile = filename + "_test" + file_extension
            if not os.path.exists(testDictPyFile):
                shutil.copyfile(dictPyFile, testDictPyFile)
            dictPyFile = testDictPyFile

        with open(dictPyFile, "r") as pyInFile:
            lines = pyInFile.readlines()
        with open(dictPyFile, "w+") as pyOutFile:
            for i, line in enumerate(lines):
                if "} #end" in line:
                    # @todo: print out in order for easy indexing
                    for item in appendList:
                        pyOutFile.write(item)
                    pyOutFile.write("} #end\n")
                else:
                    pyOutFile.write(line)

            '''versionUIDList = []
            lines = pyInFile.readlines()
            for line in lines:
                m = matchSequence[8].match(line)
                versioningKey = m.group(1).strip()
                versionUIDList.append(versioningKey)'''
            # @todo: implement hash for faster lookup

    def genLocalPythonDict(self):
        '''
        For local use for TWIDL tstructor and dynamic structures
        '''
        print("==Generating Local Py Dict File==")
        pythonFileDir = os.path.abspath(os.path.join(REPODIR, "tools/telemetry/TWIDL"))
        if not os.path.exists(pythonFileDir):
            os.mkdir(pythonFileDir)
        pythonFile = os.path.join(pythonFileDir, "twidlDictBase.py")
        with open(pythonFile, "w+") as pyFile:
            pyFile.write(
                "\'\'\'\nThis file is automatically generated by dataControlGen.py.  Please do not modify.\n\'\'\'\n")
            pyFile.write("\ndataControlDict = {\n")

            for uidNum in sorted(self.uidMasterDictV2.keys(), key=uidSort):
                uid = self.uidMasterDictV2[uidNum]
                pyFile.write("    %s : %s,\n" % (uidNum, uid.asDict()))

            pyFile.write("}\n")
        print("..done")


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Main Functions
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Directory Naming Convention examples:
#    repodir = r"C:\Users\achamorr\Intel\mono_telemetry-major2-minor0_decode\nand\gen3"
#    repoRoot = r"C:\Users\achamorr\Intel\mono_telemetry-major2-minor0_decode"
#    tempMetaRepo = r"C:\Users\achamorr\Intel\mono_telemetry-major2-minor0_decode\tools\lib\datacontrol\ssddev-meta"


def dataControlGenWrapper(output=sys.stdout, to_create=None, to_deprecate=None, to_edit=None, implement=None,
                          repodir=None, repoRoot=None, file=None, debug=False, update_h=False, update_dict=False):
    '''
    Wrapper builds dataControlGen instance, executes and cleanup
    '''
    # Step 1: Initalize Variables    
    args_to_edit = set()
    args_to_create = set()
    args_to_deprecate = set()

    if to_edit:
        args_to_edit = set(to_edit)
    if to_create:
        args_to_create = set(to_create)
    if to_deprecate:
        args_to_deprecate = set(to_deprecate)

    # debug
    global DEBUG
    DEBUG = debug

    # repodir
    global REPODIR
    REPODIR = repodir

    srcPath = os.path.abspath(os.path.join(repodir, "src"))

    # set file paths
    currRepo = os.path.dirname(os.path.realpath(__file__))
    tempMetaRepo = os.path.abspath(os.path.join(currRepo, "ssddev-meta"))

    if file:
        dataControlCSVFile = os.path.abspath(os.path.join(currRepo, file))
        if not os.path.exists(dataControlCSVFile):
            print("The file %s does not exits. Fix before proceeding." % dataControlCSVFile)
            print("No changes made\n")
            quit(2)
    else:
        dataControlCSVFile = os.path.abspath(os.path.join(currRepo, 'structures.csv'))
    # dataControlRemoteFile = os.path.join(currRepo, 'datacontrol.h')
    dataControlLocalFile = os.path.abspath(os.path.join(srcPath, "datacontrol.h"))

    if UNIT_TESTING:
        # CSV
        filename, file_extension = os.path.splitext(dataControlCSVFile)
        testDataControlCSVFile = filename + "_test" + file_extension
        if not os.path.exists(testDataControlCSVFile):
            shutil.copyfile(dataControlCSVFile, testDataControlCSVFile)
        dataControlCSVFile = testDataControlCSVFile
        # H
        filename, file_extension = os.path.splitext(dataControlLocalFile)
        testDataControlLocalFile = filename + "_test" + file_extension
        if not os.path.exists(testDataControlLocalFile):
            shutil.copyfile(dataControlLocalFile, testDataControlLocalFile)
        dataControlLocalFile = testDataControlLocalFile

    # import for git functionality
    scmlibRepo = os.path.join(repoRoot, "tools/lib")
    print("importing from %s" % scmlibRepo)
    sys.path.append(scmlibRepo)
    from scmlib import scm

    print("Source Path: %s\n" % srcPath)
    print("Structures.csv File: %s\n" % dataControlCSVFile)
    print("Datacontrol.h : %s\n" % dataControlLocalFile)

    # Step  2: init structures.csv
    output.write("Parsing structures.csv for database uids...\n\n")
    dgc = DatacontrolGenCSV(dataControlCSVFile, tempMetaRepo)

    # Step 3: perform updates
    if to_create:
        print("==Creating UIDs...")
        for tempUID, structName, dataArea, dataGroup, product, editString in args_to_create:  # @todo: tqdm addition
            if DEBUG:
                print(tempUID)
            created = False
            if tempUID.lower() == 'auto':
                tempUID = dgc.getAvailableTemp()
                print("YOUR STRUCTURE WAS ASSIGNED UID %s :%s,%s,%s,%s" % (
                tempUID, structName, dataArea, dataGroup, product))
            exec("created = dgc.create('%s','%s','%s','%s','%s')" % (
            str(tempUID), structName, dataArea, dataGroup, product))
            # call edit uid
            if created:
                exec("edited = dgc.edit('%s','%s',%s)" % (str(tempUID), TELEMETRY_LATEST_VERSION, editString))

        print("done.==\n")
    if to_deprecate:
        print("==Deprecating UIDs...")
        for uidNum, version in args_to_deprecate:  # @todo: tqdm addition
            # create edit command
            if DEBUG:
                print(uidNum)
            exec("deprecated = dgc.deprecate('%s','%s')" % (str(uidNum), version))
        print("done.==\n")
    if to_edit:
        print("==Editing UIDs...")
        for uidNum, version, editString in args_to_edit:  # @todo: tqdm addition
            if DEBUG:
                print(uidNum)
            # create edit command
            exec("edited = dgc.edit('%s','%s',%s)" % (str(uidNum), version, editString))
        print("done.==\n")

    # Step 4: Count errors
    to_edit_successes = (args_to_edit - set(dgc.editViolations))
    to_create_successes = (args_to_create - set(dgc.createViolations))
    to_deprecate_successes = (args_to_deprecate - set(dgc.deprecateViolations))

    numberOfErrors = len(dgc.editViolations) + len(dgc.createViolations) + len(dgc.deprecateViolations)

    # Step 7: Implement by creating a branch with local CSV replacing remote in ssddev-meta and tempUids made into permanents.
    # Needs to be reviewed by relevant parties and merged to trunk.

    if implement:
        print("==Implementing UIDs...", )
        # ==================================
        # Remote Repo Time :)
        # ==================================
        itime = time.time()
        # STAGE 1: pre-checks

        # Clean up temp master repo dir if present
        if os.path.exists(tempMetaRepo):
            shutil.rmtree((tempMetaRepo), onerror=remove_readonly)

        # STAGE 2: clone ssdev-meta
        try:
            print("tempMetaRepo: ", tempMetaRepo)
            print("remoteGitRepo:", REMOTE_GIT_REPO)
            repo = scm.ScmFactory(tempMetaRepo, REMOTE_GIT_REPO)
            output.write("Cloning ssddev-meta repository...")

            repo.clone()

            branch = "feature/telemetry/NSGSE-128093-4"
            repo.gotoBranch(branch)  # @todo: remove once in main repo
            output.write("Branch %s ..." % branch)

            output.write("done.\n")

        except Exception as e:
            output.write(
                "\nERROR: Failed to clone, verify that you have the required AGS role NSG Repos - ssddev-meta - Read-Write. See https://nsg-wiki.intel.com/display/NSE/AGS+-+NSG+Infrastructure+Managed+Roles  \n")
            print("\nImplementation Failed\n")
            throwTraceback(e)

        # STAGE 3: execute
        if DEBUG:
            print("\nrepodir: %s\nrepoRoot: %s\ntempMetaRepo: %s\n" % (repodir, repoRoot, tempMetaRepo))
        newlyImplementedList = dgc.implement()
        dgc.updatePythonDict()

        if not newlyImplementedList:  # if list is empty
            sys.stdout.write("\nNo differences between repos\n")
            numberOfErrors += 1

        # STAGE 4: commiting results
        if numberOfErrors == 0:
            # do not push if any errors detected!!

            if repo.status():
                # prepRepo for the push
                repo.addFile()

                try:
                    txtChangeLog = os.path.abspath(os.path.join(tempMetaRepo, "DATACONTROL/changeLog.txt"))
                    if os.path.exists(txtChangeLog):
                        append_write = 'a'
                    else:
                        append_write = 'w'

                    with open(txtChangeLog,
                              append_write) as txtChangeLog:  # IMPORTANT! required to make git recognize changes
                        # @todo: if datacontrolFlag: elif assertgenFlag:
                        txtChangeLog.write(
                            "\n===LOG CREATED ON %s===\n" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        # commit to temp repo
                        output.write("Committing...")
                        sys.stdout.write("Committing...")
                        for tempNum, uidNum in newlyImplementedList:
                            out = "AUTO: UID " + str(tempNum) + " -> " + str(uidNum) + " was implemented by " + \
                                  repo.getConfig()['username']
                            if DEBUG:
                                txtChangeLog.write("DEBUG MODE: COMPLETED BUT DID NOT COMMIT:")
                                sys.stdout.write("DEBUG MODE: COMPLETED BUT DID NOT COMMIT:")
                                sys.stdout.write(out)
                            else:
                                """repo.commit(out)"""  # todo: uncomment once good @jdtarang
                            txtChangeLog.write(out)
                        output.write("done.\n")
                        sys.stdout.write("done.\n")

                        # push to remote.
                        output.write("Pushing to remote datacontrol H repo...")
                        sys.stdout.write("Pushing to remote datacontrol H repo...")
                        if DEBUG == False:
                            txtChangeLog.write("WOULD HAVE PUSHED")  # todo: remove once good @jdtarang
                            """repo.push()"""  # todo: uncomment once good @jdtarang
                        output.write("done.\n")
                        sys.stdout.write("done.\n")

                except Exception as e:
                    # file handling
                    txtChangeLog.close()
                    output.write(
                        "\nERROR failed to update remote datacontrol H repo; First check if you have datacontrol META repo RW access. If you do the likely cause is a reservation conflict, try running again. No changes pushed to remote datacontrol H repository.\n")
                    sys.stdout.write(
                        "\nERROR failed to update remote datacontrol H repo; First check if you have datacontrol META repo RW access. If you do the likely cause is a reservation conflict, try running again. No changes pushed to remote datacontrol H repository.\n")
                    throwTraceback(e)
            else:
                output.write(
                    "INFO: No changes to datacontrol code reservations detected. No changes pushed to remote datacontrol Hrepository.\n")
                sys.stdout.write(
                    "INFO: No changes to datacontrol code reservations detected. No changes pushed to remote datacontrol H repository.\n")
        else:
            print("==Encountered %s Errors==" % numberOfErrors)
            output.write("INFO: No changes pushed to remote datacontrol H repository.\n")
            sys.stdout.write("INFO: No changes pushed to remote datacontrol H repository.\n")

        itime = time.time() - itime
        print("Finished Implementing in %s seconds." % itime)

    if numberOfErrors == 0:
        # Step 5: update datacontrol CSV file to match new additions
        dgc.updateFile()

        # Step 6: update local H if specified
        if update_h or implement:
            dgh = DatacontrolGenH(dataControlLocalFile, overwrite=True)
            dgh.matchWithCSV(dgc)
            dgh.updateFile()

        # Step 7: update local Py dict file if specified
        if update_dict or implement:
            dgc.genLocalPythonDict()

    else:
        print(
            "Reservation, Implementation, or Deprecation errors encountered, datacontrol H and structures CSV remain unchanged")

    # STAGE 7: clean up
    if os.path.exists(tempMetaRepo):
        if DEBUG == False:
            shutil.rmtree((tempMetaRepo), onerror=remove_readonly)
    # ============================
    # ============================

    return numberOfErrors


def main():
    description = 'Datacontrol code management tool to reserve, implement and retire structure uids.\n' \
                  'Documented at https://nsg-wiki.intel.com/display/FW/datacrontrolGen.py\n'
    parser = argparse.ArgumentParser(prog='dataControlGen.py',
                                     description=description)
    parser.add_argument('--create', dest="to_create", default=None,
                        metavar=('<tempUID> (<editString>)'))
    parser.add_argument('--edit', dest='to_edit', default=None,
                        metavar=('<uidNum> <version> (<editString>)'))
    parser.add_argument('--deprecate', dest='to_deprecate', default=None,
                        metavar=('<uidNum> <version>'))
    parser.add_argument('--implement', action='store_true', default=False)
    parser.add_argument('--h', dest='update_h', action='store_true', default=False)  # @todo: change to specify build
    parser.add_argument('--dict', dest='update_dict', action='store_true', default=False)

    parser.add_argument('--debug', action='store_true', dest='debug', default=False)
    parser.add_argument('--file', dest='structuresFile', default=None,
                        help="Use to specify structures_meta, NAME ONLY. Should be in same directory.")
    args = parser.parse_args()

    to_deprecate = None
    to_edit = None
    to_create = None
    if args.to_create:
        to_create = []
        print("<temp-uid>,<structName>,<dataArea>,<dataGroup>,<product>,(<editString>)\n")
        # get rid of brackets
        args.to_create = withoutBoundingChars(args.to_create, "[", "]")

        for uidInfo in args.to_create.split(';'):  # separate into uids
            print(uidInfo)
            if matchSequence[6].match(uidInfo):
                m = matchSequence[6].match(uidInfo)
                tempUid = validateString(m.group(1))
                structName = validateString(m.group(2))
                dataArea = validateString(m.group(3))
                dataGroup = validateString(m.group(4))
                product = validateString(m.group(5))
                editString = validateEditString(m.group(6))
                argList = [tempUid, structName, dataArea, dataGroup, product, editString]
                if args.debug:
                    print("tempUid: ", tempUid, ",structName: ", structName, ",dataArea: ", dataArea, ",dataGroup: ",
                          ",product: ", product, ",editString: ", editString)
                to_create.append(tuple(a for a in argList))  # store in tuple
            else:
                print(
                    "Create takes six (6) arguments, please specify '--create [<temp-uid>,<structName>,<dataArea>,<dataGroup>,<product>,(<editString>)]'.\n NO SPACES. Multiple instances: separated by ';'.")
                quit(0)
    if args.to_deprecate:
        to_deprecate = []
        print("<uidNum> <version>\n")
        args.to_deprecate = withoutBoundingChars(args.to_deprecate, "[", "]")
        for uidInfo in args.to_deprecate.split(';'):  # separate into uids
            print(uidInfo)
            uidInfo = uidInfo.split(',')  # separate info
            uidNum = validateString(uidInfo[0])
            version = validateVersion(uidInfo[1])
            if len(uidInfo) != 2:
                print(
                    "Deprecate takes two (2) arguments, please specify '--deprecate [<uidNum><version>]'.\n NO SPACES. Multiple instances: separated by ';'.")
                quit(0)
            to_deprecate.append(tuple(a for a in uidInfo))  # store in tuple
    if args.to_edit:
        to_create = []
        print("<temp-uid>,<version>,(<editString>)\n")
        # get rid of brackets
        args.to_edit = withoutBoundingChars(args.to_edit, "[", "]")

        for uidInfo in args.to_edit.split(';'):  # separate into uids
            print(uidInfo)
            if matchSequence[6].match(uidInfo):
                m = matchSequence[6].match(uidInfo)
                uidNum = validateString(m.group(1))
                version = validateVersion(m.group(2))
                editString = validateEditString(m.group(3))
                argList = [tempUid, version, editString]
                if args.debug:
                    print("uidNum: ", uidNum, ",version: ", version, ",editString: ", editString)
                to_edit.append(tuple(a for a in argList))  # store in tuple
            else:
                print(
                    "Create takes three (3) arguments, please specify '--create [<temp-uid>,<version>,(<editString>)]'.\n NO SPACES. Multiple instances: separated by ';'.")
                quit(0)

    # repoRoot init
    if UNIT_TESTING:
        repoRoot = os.path.join(os.path.realpath(__file__), '..')
        repoRoot = os.path.join(os.path.realpath(repoRoot), '..')
        repoRoot = os.path.join(os.path.realpath(repoRoot), '..')
        repoRoot = os.path.dirname(os.path.realpath(repoRoot))
        repodir = os.path.join(repoRoot, "nand/gen3")

    numberOfErrors = dataControlGenWrapper(to_create=to_create, to_deprecate=to_deprecate, to_edit=to_edit,
                                           implement=args.implement, repodir=repodir, repoRoot=repoRoot,
                                           file=args.structuresFile, debug=args.debug, update_h=args.update_h,
                                           update_dict=args.update_dict)

    if numberOfErrors > 0:
        sys.stdout.write(str(numberOfErrors) + " error(s) found, see output\n")
    else:
        sys.stdout.write(str(numberOfErrors) + " error(s) found\n")


if __name__ == '__main__':
    if UNIT_TESTING:
        main()
