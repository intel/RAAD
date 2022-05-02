#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Daniel Garces
# *****************************************************************************/
# @package basicTypes
# This python script is used to basic data types.
#  The code uses nested inner classes to not allow mutating of the internal workings and use the one API.

##################################
# General Python module imports
##################################
from __future__ import absolute_import, division, print_function, \
    unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import sys, re, platform, socket, uuid, psutil, datetime, pprint, GPUtil, os
from optparse import OptionParser
import src.software.TSV.generateTSBinaries as TSVgen
import src.software.TSV.formatTSFiles as TSVformat
import src.software.TSV.DefragHistoryGrapher as TSVDefragHistory
import src.software.TSV.visualizeTS as TSVGenericGraph
import src.software.autoAI.mediaPredictionRNN as RNN
import src.software.MEP.mediaErrorPredictor as ARMA
import src.software.DP.preprocessingAPI as DP
from src.software.utilsCommon import getTimeStamp

##################################
# Classes for Objects
##################################
"""
    @todo Add type precision based usage...
        import numpy library
            np.half / np.float16 
                Half precision float: sign bit, 5 bits exponent, 10 bits mantissa.
            np.single float
                Platform-defined single precision float: typically sign bit, 8 bits exponent, 23 bits mantissa.
            np.double double
                Platform-defined double precision float: typically sign bit, 11 bits exponent, 52 bits mantissa.
            np.longdouble long double
                Platform-defined extended-precision float.
            np.csingle float complex
                Complex number, represented by two single-precision floats (real and imaginary components).
            np.cdouble
                double complex Complex number, represented by two double-precision floats (real and imaginary components).
            np.clongdouble long double complex
                Complex number, represented by two extended-precision floats (real and imaginary components).
            np.float32
                float
            np.float64 / np.float_ 
                double
                Note that this matches the precision of the builtin python float.
            np.complex64
                float complex
                Complex number, represented by two 32-bit floats (real and imaginary components).
            np.complex128 / np.complex_
                double complex
                Note that this matches the precision of the builtin python complex.
            Example minimum resolution 
                Note: precision type in numpy has β=2; p=53
                (np.finfo(np.float64).eps == 2**(1-53)) == True        
"""

"""
    Class for the data components collected.

        Attributes
        ----------
        ObjectContainer: The data object to describe components of collected data.
            Protocol: The specific protocol used.
                Interface: = ["NVMe", "SATA-ACS"]
                Major: [1 to N]
                Minor: [0 to K]
            Telemetry: Telemetry information in respect the current payload
                Internal: Telemetry version is the internal tracking across all products.
                    Major: [1 to M]
                    Minor: [0 to K]
                Type: ["Host", "Controller"] - Host or controller-initiated telemetry asynchronous command.
                Snapshots: Telemetry binary payloads names and path pairs.
                    Filenames: "PHAB8506001G3P8AGN_sample.bin" - File name on the host system.
                    Paths: "C:/Source/SSDDev/NAND/gen3/tools/telemetry/sample" - Path on the host system to binary.
                    PayloadValidity: ["Verified", "Unknown", "Corrupted"]
                    creationTime: [year, month, day[, hour[, minute[, second[, microsecond[, tzinfo]]]]]] - Represents the time at which the data object was imported to the tool.
            System: The host operating system the device is connected to.
                CPU: ["Intel Xeon Platinum 9282"]
                Platform: ["Intel S9200WK"] - The system PCB designed.
                Chipset: ["Intel C629"] - The system peripherals and capabilities.
                EPOCHSystemTime: ["UTC 23:59:59:000"] - The current time of the system for access.
                OperatingSystem: ["Windows 10", "Windows Server 2012", "Ubuntu 18.04", "Ubuntu 20.04"] - Operating system for the host system.
                    ExtractionType: ["AutoExtract"] - Name of the extraction method best known method.
                        Major: [1 to M]
                        Minor: [0 to K]
                        Updates: ["Service Pack 1", "Service Pack 2"] - Update packages for the operating system.
                        Packages: ["Linux Subsystem", "Python 2.7", "FAST"] - Software packages installed from 3rd parties.
                        Devices: ["Intel® SSD DC P3700 1TB","Xeon Phi Coprocessor", "Intel UHD Graphics Gen12 HP DG2", "Intel Network x550"]
                            Status: ["Healthy", "Fault", "Degraded", "Anomaly"] - The active state of the context.
                Status: ["Healthy", "Fault", "Degraded", "Anomaly"] - The active state of the context.
                EventTime: ["now", "UTC 8-8-2020 12:59:01:001"] - The date and time of the anomoly occurance.
               UpTime: [1 year, 2 months, 3 days, 4 hours, 5 minutes] - Total time the device has been executing.
            Context:
                UserIdentification: ["Dell", "IBM", "Channel"] - External Customer (Dell, IBM); Internal (ConVal, RDT, EBT, Developer Bench); Parallel BU (DCG, CCG, PEG, Labs, etc.).
                JIRA:
                   Identifier: “NSGSE-12345”
                   URL:  https://nsg-jira.intel.com/browse/
                    Major: [1 to M]
                    Minor: [0 to K]
               Data Lake:
                   Identifier: “123456789”
                   URL:  https://datalake.intel.com/browse/key=
                   Major: [1 to M]
                   Minor: [0 to K]
                Source: [Active, Previous] - Active is for current executing workload and previous device State space before execution context.
                        UsageName: ["Telemetry-HiTAC_Performance"] - Execution Workload, Focused Feature Test, Platform Test, etc.
                            Major: [1 to M]
                            Minor: [0 to K]
                            Documentation: ["T:/Documentation/Telemetry/Tests/Telemetry-HiTAC_Performance.docx"] - Documentation for the test, execution, or prototype.
                            Status: ["Running", "Pass", "Fail"] - The active state of the context.
                            Description: Description of the test execution.
                                Performance: In the event performance executation is manually executed.
                                    WorkloadType: [Write, Read, Trim]
                                    Percentage: [15,80,5]
                                    QueueDepth: [1 to 128]
                                    Workers: [1 to J]
                            Runtime: [TimeNow - TimeStart]
                Interactions: ["technician", "engineer", "automation"] - Human involves Connecting Probe, Pulling Parallel Devices (Hot-Plug), Firmware upgrade, etc. Machine involves AI controlled Bot to simulate device hot plug every 10 seconds, control arm exposure to Alpha and Beta Particle generating radioactive material to simulate space, etc.
                    Contact: "joseph.d.tarango@gmail.com"
                    Description: "Engineer connected probe to analyze failure."
"""


def uniqueIdentifierTypes_e(otype=None):
    """
    unique identifier lookup function
    Args:
        otype: str, int

    Returns: if is int then return string; otherwise, if the type is string return int

    """
    uniqueIdentifierTypes_t = {
        "unknown": 0,
        "telemetryObject": 1,
        "application": 2
    }
    reverse_uniqueIdentifierTypes_t = {v: k for k, v in uniqueIdentifierTypes_t.items()}

    if otype is None:
        return uniqueIdentifierTypes_t["unknown"]
    elif isinstance(otype, int) and otype in uniqueIdentifierTypes_t:
        return reverse_uniqueIdentifierTypes_t[otype]
    elif isinstance(otype, str) and otype in reverse_uniqueIdentifierTypes_t:
        return uniqueIdentifierTypes_t[otype]
    else:
        return uniqueIdentifierTypes_t["unknown"]


class VersionTracking(object):
    """ Information to track the version of any generic object.
    otype: type of object to identify.
    UID: unique identifier.
    Major: Represents a unique structure organization of a given object.
    Minor: Represents an extension of an object to the end of the current payload without any additional changes.
    """

    def __verify(self, value):
        # ObjectUtility(value) # @todo
        if hasattr(value, str(value)) is False and value is not None:
            print("Incorrect interval for:" + str(self.__class__.__name__))
            raise NotImplementedError("Object set fail.")
        return True

    def __verifySet(self, major, minor):
        self.__verify(major)
        self.__verify(minor)

    def __init__(self, otype=None, uid=None, major=None, minor=None):
        # self.__verifySet(major=major, minor=minor)
        self._otype = uniqueIdentifierTypes_e(otype=otype)
        self._uid = uid  # integer value
        self._major = major
        self._minor = minor

    def __repr__(self):
        selfDict = {
            'Version Tracking': {
                'type': self._otype,
                'uid': self._uid,
                'major': self._major,
                'minor': self._minor
            }
        }
        return selfDict

    def __iter__(self):
        return self.__repr__().items()

    def __str__(self, indent=1, spaces=4):
        spacesIndent = ' ' * (indent * spaces)
        internalIndent = ' ' * spaces
        spacesIndentNested = spacesIndent + internalIndent
        stringParagraph = f"{spacesIndent}Version Tracking{os.linesep}"
        stringParagraph += f"{spacesIndentNested}type: {str(self._otype)}{os.linesep}"
        stringParagraph += f"{spacesIndentNested}uid: {str(self._uid)}{os.linesep}"
        stringParagraph += f"{spacesIndentNested}major: {str(self._major)}{os.linesep}"
        stringParagraph += f"{spacesIndentNested}minor: {str(self._minor)}{os.linesep}"
        return stringParagraph

    def getType(self):
        return self._otype

    def getTypeHuman(self):
        return uniqueIdentifierTypes_e(self._otype)

    def getUID(self):
        return self._uid

    def getMajor(self):
        return self._major

    def getMinor(self):
        return self._minor

    def setType(self, varIn=None):
        self.__verify(varIn)
        self._otype = uniqueIdentifierTypes_e(varIn)
        return self._otype

    def setUID(self, varIn=None):
        self.__verify(varIn)
        self._uid = varIn
        return self._uid

    def setMajor(self, varIn=None):
        self.__verify(varIn)
        self._major = varIn
        return self._major

    def setMinor(self, varIn=None):
        self.__verify(varIn)
        self._minor = varIn
        return self._minor

    def getWalkList(self):
        listStr = list()
        listStr.append(self._otype)
        listStr.append(self._uid)
        listStr.append(self._major)
        listStr.append(self._minor)
        return listStr


class TelemetryData(object):
    """Telemetry: Telemetry information in respect the the current payload
        Internal: Telemetry Firmware version is the internal tracking across all products.
            Major: [1 to M]
            Minor: [0 to K]
        Type: ["Host", "Controller"] - Host or controller initiated telemetry asyncronous command.
        Snapshots: Telemetry binary payloads names and path pairs.
            Filenames: "PHAB8506001G3P8AGN_sample.bin" - File name on the host system.
            Paths: "C:/Source/SSDDev/NAND/gen3/tools/telemetry/sample" - Path on the host system to binary.
            PayloadValidity: ["Verified", "Unknown", "Corrupted"]
            creationTime: [year, month, day[, hour[, minute[, second[, microsecond[, tzinfo]]]]]] - Represents the time at which the data object was imported to the tool.
    """

    def __init__(self, typeOfTelemetry=None, filename=None, path=None):
        self.version = VersionTracking()
        self.typeOfTelemetry = typeOfTelemetry
        self.filename = filename
        self.path = path
        self.payloadValidity = "Unknown"
        self.creationTime = getTimeStamp(inTime=None)

    def __repr__(self):
        verDict = self.version.__repr__()
        selfDictSub = {
            'Telemetry Data':
                {'Telemetry Type': self.typeOfTelemetry,
                 'filename': self.filename,
                 'path': self.path,
                 'payload validity': self.payloadValidity,
                 'creation time': self.creationTime
                 }
        }
        selfDict = verDict
        selfDict.update(selfDictSub)
        return selfDict

    def __iter__(self):
        return self.__repr__().items()

    def __str__(self, indent=1, spaces=4):
        spacesIndent = ' ' * (indent * spaces)
        internalIndent = ' ' * spaces
        spacesIndentNested = spacesIndent + internalIndent
        stringParagraph = f"{spacesIndent}Telemetry Data{os.linesep}"
        stringParagraph += f"{self.version.__str__(indent=indent + 1, spaces=spaces)}"
        stringParagraph += f"{spacesIndentNested}Telemetry Type: {str(self.typeOfTelemetry)}{os.linesep}"
        stringParagraph += f"{spacesIndentNested}filename: {str(self.filename)}{os.linesep}"
        stringParagraph += f"{spacesIndentNested}path: {str(self.path)}{os.linesep}"
        stringParagraph += f"{spacesIndentNested}payload validity: {str(self.payloadValidity)}{os.linesep}"
        stringParagraph += f"{spacesIndentNested}creation time: {str(self.creationTime)}{os.linesep}"
        return stringParagraph

    def getWalkList(self):
        listStr = []
        for eachItem in self.version.getWalkList():
            listStr.append(eachItem)
        listStr.append(self.typeOfTelemetry)
        listStr.append(self.filename)
        listStr.append(self.path)
        listStr.append(self.payloadValidity)
        listStr.append(self.creationTime)
        return listStr

    def getWalkDictionary(self):
        class_vars = vars(self.__class__)  # get any "default" attrs defined at the class level
        inst_vars = vars(self)  # get any attrs defined on the instance (self)
        all_vars = dict(class_vars)
        all_vars.update(inst_vars)
        # filter out private attributes
        public_vars = {k: v for k, v in all_vars.items() if not k.startswith('_')}
        listStr = public_vars
        pprint.pformat(listStr)
        return listStr


class UID_Data(object):
    """Meta Description - The meta data for the data object.
           VersionTracking(object): Version information.
           Data Object - The data payload with defined content.
    """

    def __init__(self, uid=None, major=None, minor=None, data=None):
        self.version = VersionTracking(otype="telemetryObject", uid=uid, major=major, minor=minor)
        self.data = data

    def __repr__(self):
        selfDictSub = {'UID Data': {'Data': self.data}}
        verDict = self.version.__repr__()
        selfDictSub['UID Data'].update(verDict)
        return selfDictSub

    def __iter__(self):
        return self.__repr__().items()

    def __str__(self, indent=1, spaces=4):
        spacesIndent = ' ' * (indent * spaces)
        internalIndent = ' ' * spaces
        spacesIndentNested = spacesIndent + internalIndent
        stringParagraph = f"{spacesIndent}UID Data{os.linesep}"
        stringParagraph += f"{self.version.__str__(indent=indent + 1, spaces=spaces)}"
        stringParagraph += f"{spacesIndentNested}Data: {str(self.data)}{os.linesep}"
        return stringParagraph

    def getUID(self):
        return self.version.getUID()

    def getMajor(self):
        return self.version.getMajor()

    def getMinor(self):
        return self.version.getMinor()

    def getData(self):
        return self.data

    def setUID(self, objectIn=None):
        self.version.setUID(objectIn)

    def setMajor(self, objectIn=None):
        self.version.setMajor(objectIn)

    def setMinor(self, objectIn=None):
        self.version.setMinor(objectIn)

    def setData(self, objectIn=None):
        self.data = objectIn

    def getWalkList(self):
        listStr = []
        for eachItem in self.version.getWalkList():
            listStr.append(eachItem)
        listStr.append(self.getData())
        return listStr


class UID_Application(object):
    """Meta Description - The meta data for the data object.
           VersionTracking(object): Version information.
           Class Object - The class used.
    """

    def __init__(self, uid=None, major=None, minor=None, data=None):
        self.version = VersionTracking(otype="application", uid=uid, major=major, minor=minor)
        self.data = data

    def __repr__(self, indent=1, spaces=4):
        selfDict = {'UID Application (RAAD version number)': {'Data': self.data}}
        verDict = self.version.__repr__()
        selfDict['UID Application (RAAD version number)'].update(verDict)
        return selfDict

    def __iter__(self):
        return self.__repr__().items()

    def __str__(self, indent=1, spaces=4):
        spacesIndent = ' ' * (indent * spaces)
        internalIndent = ' ' * spaces
        spacesIndentNested = spacesIndent + internalIndent
        stringParagraph = f"{spacesIndent}UID Application{os.linesep}"
        stringParagraph += f"{self.version.__str__(indent=indent + 1, spaces=spaces)}"
        stringParagraph += f"{spacesIndentNested}Data: {str(self.data)}{os.linesep}"
        return stringParagraph

    def getUID(self):
        return self.version.getUID()

    def getMajor(self):
        return self.version.getMajor()

    def getMinor(self):
        return self.version.getMinor()

    def getData(self):
        return self.data

    def setUID(self, objectIn=None):
        self.version.setUID(objectIn)

    def setMajor(self, objectIn=None):
        self.version.setMajor(objectIn)

    def setMinor(self, objectIn=None):
        self.version.setMinor(objectIn)

    def setData(self, objectIn=None):
        self.data = objectIn

    def getWalkList(self):
        listStr = []
        for eachItem in self.version.getWalkList():
            listStr.append(eachItem)
        listStr.append(self.data)
        return listStr


class UID_Org(object):
    """Organization - Identification of the source-destination of the data.
            Vendor - High level organization.
            Bussiness Unit - Individual business group within the organization.
            Group - Group within the bussiness unit.
            Team - Team whithin the group.
    """

    def __init__(self, vendor="Intel", bussinessUnit="NSG", group="STG", team="AMPERE"):
        self.vendor = vendor
        self.bussinessUnit = bussinessUnit
        self.group = group
        self.team = team

    def __repr__(self):
        selfDict = {"UID Organization": {'vendor': self.vendor,
                                         'bussiness unit': self.bussinessUnit,
                                         'group': self.group,
                                         'team': self.team
                                         }
                    }
        return selfDict

    def __iter__(self):
        return self.__repr__().items()

    def __str__(self, indent=1, spaces=4):
        spacesIndent = ' ' * (indent * spaces)
        internalIndent = ' ' * spaces
        spacesIndentNested = spacesIndent + internalIndent
        stringParagraph = f"{spacesIndentNested}{spacesIndent}UID Organization{os.linesep}"
        stringParagraph += f"{spacesIndentNested}vendor: {str(self.vendor)}{os.linesep}"
        stringParagraph += f"{spacesIndentNested}bussiness unit: {str(self.bussinessUnit)}{os.linesep}"
        stringParagraph += f"{spacesIndentNested}group: {str(self.group)}{os.linesep}"
        stringParagraph += f"{spacesIndentNested}team: {str(self.team)}{os.linesep}"
        return stringParagraph

    def getVendor(self):
        return self.vendor

    def getbusinessUnit(self):
        return self.bussinessUnit

    def getGroup(self):
        return self.group

    def getTeam(self):
        return self.team

    def setVendor(self, objectIn=None):
        self.vendor = objectIn

    def setBusinessUnit(self, objectIn=None):
        self.bussinessUnit = objectIn

    def setGroup(self, objectIn=None):
        self.group = objectIn

    def setTeam(self, objectIn=None):
        self.team = objectIn

    def getWalkList(self):
        listStr = [self.vendor, self.bussinessUnit, self.group, self.team]
        return listStr


def main():
    """Performs the auto parsing of data control to generate telemetry definitions within a python c-type for valid structures."""
    ##################################
    # sample usage: "python basicTypes.py --bindir .\sample --objdir C:\Users\jdtarang\Intel\mono_telemetry-major2-minor0_decode\nand\gen3\projects\objs\arbordaleplus_ca"
    ##################################
    # Global Variables
    ##################################
    usage = "%s --bindir --bin --objdir --outloc" % (sys.argv[0])
    parser = OptionParser(usage)
    parser.add_option("--bindir", dest='bindir', metavar='<BINDIR>',
                      help='Bin Files Directory (ex: C://../tools/telemetry/sample or ./sample). use if separated Bin Files Folder has already been generated.')
    parser.add_option("--bin", dest='bin', metavar='<BIN>',
                      help='Binary to parse name (ex: C://../tools/telemetry/sample.bin or sample.bin')
    parser.add_option("--outloc", dest='outloc', metavar='<OUTLOC>', default=None,
                      help='File to Print Telemetry Objects out to')
    parser.add_option("--objdir", dest='objdir', metavar='<OBJDIR>', default=None,
                      help='Project Object Location: (ex: C://..gen3/projects/objs/arbordaleplus_ca)')
    parser.add_option("--debug", action='store_true', dest='debug', default=False, help='Debug mode.')
    parser.add_option("--verbose", action='store_true', dest='verbose', default=False,
                      help='Print Objs Data to Command Prompt')
    parser.add_option("--output_file", dest='outfile', metavar='<OUTFILE>', default='',
                      help='File to output the created telemetry objects')

    (options, args) = parser.parse_args()
    pprint.pprint(options)
    pprint.pprint(args)

    return


if __name__ == '__main__':
    """Performs execution delta of the process."""
    p = datetime.datetime.now()
    main()
    q = datetime.datetime.now()
    print("\nExecution time: " + str(q - p))
