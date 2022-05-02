#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Daniel Garces, Andrea Chamorro
# *****************************************************************************/
# Purpose       : creates a dynamic dictionary of Telemetry cstructs, automates Telemetry flow

import re, os, sys, array, ctypes, time, glob, getopt, math
from optparse import OptionParser, OptionGroup
from operator import itemgetter
from subprocess import Popen, PIPE
from threading import Timer
import pprint
import traceback
from ctypes import Structure, Union

##### .exe extension patch for the compiled version of this script
if not re.search('\.PY$|\.PYC$|\.EXE$', os.path.split(sys.argv[0])[1].upper()):
    sys.argv[0] = os.path.join( os.path.split(sys.argv[0])[0] , os.path.split(sys.argv[0])[1]+'.exe' )

#### extend the Python search path to include TWIDL_tools directory
if __name__ == '__main__':
    twidlcore = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    sys.path.insert(0,twidlcore)

#### Path imports
sys.path.append(os.path.realpath('../../..'))                 # NAND tools library path
sys.path.append(os.path.realpath(os.path.join('..', '..')))              # NAND repository path
sys.path.append(os.path.realpath(os.path.join('..', '..', 'toolslib', 'bg3'))) # NAND Build generation engine library path

# Token objects
from src.software.parse.autoObjects import structDef
from src.software.parse.autoObjects import objectDefine
from src.software.parse.autoObjects import ctypedef

# Parser Generators
from src.software.parse.parserTwidlGen import *

#### import test utilities
from src.software.parse.structdefParser import structdefParser
from src.software.parse.output_log import *

# #################################################################################

# ======= Global Variables ========================================================
INIT_FILE_TEXT = ""

TOOL_VERSION = 1.0

# NOTE: ASSUMES THE RELATIVE LOCATION OF ALL THESE FILES
# If they change, this needs to be updated as well
VERSIONDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),"version")
REPODIR = os.path.abspath("../../../")
DATACONTROLGEN = os.path.abspath("../../dataControlGen.py")
TOOLSLIB = os.path.abspath(os.path.join(REPODIR, "toolslib"))
AUTOGEN = os.path.abspath(os.path.join(REPODIR,"tools", "telemetry", "ctypeAutoGen.py"))
REPOROOT = os.path.abspath("../../../../../../")
DATACONTROLCSV = os.path.abspath(os.path.join(REPOROOT,"tools", "lib", "datacontrol", "structures.csv"))

# ==================================================================================

'''
THIS SCRIPT ASSUMES USE OF ARBORDALEPLUS_CA BUILD FOR STRUCTURE EXTRACTION, EDIT FOR VARIABILITY LATER
NOTE: THIS RUNS ON NAND ONLY CURRENTLY
'''
# ===TEMPORARY HARD SETTTINGS===================
# NOTE: PROJECTNAME will use a BUILD directly made for TELEMETRY, being developed, that contains ALL structs in FW needed for Telemetry
PROJECTNAME = "arbordaleplus_t2"
PROJECTCODE = "APT2"
MULTIVERSION = "multi_716"
MULTIVERSION2 = "multi_616"


#which uids to get dictionary for, NO spaces, 24 passing
ITEMS_ALL = "4,5,6,7,8,9,10,12,15,16,17,18,19,20,21,22,23,24,25,26,27,29,30,31,32,33,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,58,61,62,66,67,68,69,70,71,72,73,74,75,76,78,80,82,83,85,86,87,88,90,92,93,94,95,96,100,101,102,109,110,126,127,132,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,171,175,176,177,179,180,181,182,183,186,187,190,191,192,193,194,195,198,199,202,208,209,210,211,214,215,217,218,219,220,221,222,223,227,228,230,231,232,233,240,241,248,253,291"
ITEMS_TELEMETRY = ""
ITEMS_CREATING = "4,6,8,9,42,53,60,67,87,88,94,95,96,100,101,102,126,127,180,181,182,183,240,253"
#most recent test
ITEMS_CREATING2 = "4,5,6,8,16,42,53,61,62,67,87,88,94,95,96,100,101,102,110,126,127,180,181,182,183,191,214,240,253,7,9,10,12,17,20,21,22,27,29,30,31,32,33,43,44,45,46,47,48,49,50,51,52,55,56,58,66,68,69,71,72,73,74,75,76,78,83,90,92,93,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,175,176,186,187,190,192,193,194,198,199,208,210,211,217,218,219,221,223,227,228,230,231,241,291"
ITEMS_CORRECT_SIZE = "4,8,182,183,53,67,88,95,96,101,253"
ITEMS_VERSIONED = "4,5,6,10,22,44,49,50,51,52,58,76,88,100,101,102,198,208,217,291"

#the following two should be the same
ITEMS_FAILING_BECAUSE_OF_THIS_SCRIPT = "217,215,210,211,218,219,132,137,136,135,139,138,24,25,26,27,20,21,22,23,160,29,161,58,55,54,56,51,50,52,291,199,179,195,194,190,193,192,68,145,69,82,83,80,86,85,7,109,241,248,33,32,31,30,66,177,176,175,171,198,186,187,228,227,90,93,92,223,222,221,220,10,12,15,17,19,18,151,150,153,152,155,154,157,156,159,158,230,231,232,233,48,49,46,47,44,45,43,9,146,147,144,202,142,143,140,141,209,208,148,149,76,75,74,73,72,71,70,78"
ITEMS_NOT_CREATED = "15,18,19,23,24,25,26,54,70,80,82,85,86,109,132,171,177,179,195,202,209,215,220,222,232,233,248"

ITEMS_SUPPORTED = "8,20,49,50,51,52,53" # Items to be supported.

ITEMS = ITEMS_SUPPORTED

class OpenFiles():
    """ Managing files
        files = OpenFiles()

        # use open method
        foo = files.open("text.txt", "r")

        # close all files
        files.close()
    """
    def __init__(self):
        self.files = []

    def open(self, *args):
        f = open(*args)
        self.files.append(f)
        return f

    def close(self):
        list(map(lambda f: f.close(), self.files))

# Global Files Open!
twidlDictGen_files = None


def getOverlappingSet(str1, str2):
    li1 = str1.split(',')
    li2 = str2.split(',')
    overlap = list(set(li1).intersection(set(li2)))
    print(overlap)
    return overlap


#fresh build, will take more time
REBUILD_FLAG = False #@todo: turn on when ready for TWIDL
# ===============================

# #################################################################################

# ======= Helper Functions ========================================================
def runCmd(multicmd):
    """Performs an execution of GHS program."""
    proc = Popen(multicmd, stdout=PIPE, stderr=PIPE, shell=True)
    stdout, stderr = proc.communicate()
    #could do proc.poll() here, but communicate waits for subprocess exit
    if proc.returncode != 0:
        # handle error case here
        print("command {} failed to execute. Exited with {}".format(multicmd, proc.returncode))
        sys.exit(proc.returncode)
    # all good here
    return stdout, stderr

# ==================================================================================

# #################################################################################

# ======= Class Begin ========================================================

class twidlDictGenerator:
    def __init__(self):
        self.dataControlFile = DATACONTROLCSV
        # dynamically Found
        self.destDir = None
        self.ghsStructsFile = None

        self.repodir = REPODIR
        self.versionDir = VERSIONDIR
        self.autoGenLocation = AUTOGEN

        self.errors = 0

        self.structsDefinable = []
        self.dictionary = dict()
        self.nameToUidConverter = dict()
        self.tNameToUidConverter = dict()

        self.unmappedNamesToUid = list()

        # ######## LOGICAL FLOW SPECIFIED HERE ##############
        self.auditAvailableStructures()
        self.runCtypeAutoGenScript()
        self.identifyLatestRunDestDirectory()
        self.createDictFromParserObjects()


        # ###################################################


    def auditAvailableStructures(self):
        '''
        @todo: Should audit which structure can run ctypeAutoGen successfully (can generate from c to python ctypes)
        '''
        self.items = ITEMS

    def runCtypeAutoGenScript(self):

        # build using buildGen3 (every time, so it's fresh info) OR only if it doesn't exist
        objDirLocation = os.path.abspath(os.path.join(self.repodir, "projects", "objs", PROJECTNAME))
        toolsDirLocation = os.path.abspath(os.path.join(self.repodir, "tools", "telemetry"))

        if not os.path.exists(objDirLocation) or (REBUILD_FLAG): #@ todo: assumes it's correctly built for now
            print("==Building %s==\n"% PROJECTNAME)
            bg3lib = os.path.realpath(TOOLSLIB)
            if bg3lib not in sys.path:
                sys.path.append(bg3lib)
            try:
                try:
                    from bg3 import build_engine
                except:
                    print("ERROR: cannot find gb3 module")
                    pass
                #from build_engine import buildEngineAPI
                bg3args = {
                    'repodir':self.repodir,
                    'skipall':True,
                    'targets':['APT2'],
                }
                build_engine.buildEngineAPI(bg3args)
            except Exception as e:
                print("Error importing or calling build_engine module:\n{}".format(e))
                quit(1)

        print("==Creating GHS Structures Transition File==\n")
        from src.software.parse.ctypeAutoGen import ctypeAutoGenerationAPI
        returnCode = ctypeAutoGenerationAPI( \
                fwBuildOutputDir = objDirLocation, \
                projectName = PROJECTNAME,\
                fwToolsDir = toolsDirLocation,\
                uidEnumFile = None,\
                multiExeVersion = MULTIVERSION,\
                extraDebug = False,\
                dataObjToProcess = self.items,\
                debug = False,\
                verbose = False,\
                tObjToDefine = str(self.items),\
                parse = True,\
                store = True, \
                media = "NAND" \
                )
        if returnCode != 0:
            quit(1)

    def identifyLatestRunDestDirectory(self):
        #get ctypeautogen run uPID
        if self.errors == 0:
            print("==Finding GHS Transitionary File and Destination Directory==\n")
            uPIDLogFile = os.path.abspath(os.path.join(self.versionDir, "uPIDLogFile.txt"))
            print("Log File: %s\n" % (uPIDLogFile))
            with open(uPIDLogFile, "r") as rFile:
                lines = rFile.readlines()

            #ignore if blank line, get last (latest) pUid
            while lines[-1].strip() == "":
                lines.pop()

            # RETURN VALUE FORMAT ex: uPIDName = 23b22080-bd3d-54f6-9cf5-d172ad52e4de
            uPIDName = lines[-1] # appended to end of file = latest run

            #strip EOL character and whitespace
            if uPIDName[-1] == "\n":
                uPIDName = uPIDName[:-1].strip()

            self.destDir = os.path.abspath(os.path.join(self.versionDir, uPIDName))
            structDefsFileName = "ctypeAutoGen_structDefs_" + str(uPIDName) + "_clean.txt"
            self.ghsStructsFile = os.path.abspath(os.path.join(self.versionDir, structDefsFileName))

            print("Run-Specific Dir: %s\n" % (self.destDir))
            print("Run-Specific GHS File: %s\n" % (self.ghsStructsFile))


    def createDictFromParserObjects(self):

        if self.errors == 0:
            print("==Running Parsing and Datacontrol Scripts==\n")

            parser = structdefParser()

            inputfile = open(self.ghsStructsFile, "r")
            errors = parser.parseDefFile(inputfile)
            inputfile.close()


            if not os.path.exists(self.destDir):
                os.mkdir(self.destDir)
            # write __init__.py file
            initDir = os.path.join(self.destDir, "__init__.py")
            if not os.path.exists(initDir):
                with open(initDir, 'w') as f:
                    f.write(INIT_FILE_TEXT)


            dictFileGenerator = twidlParserFileGenerator(self.destDir, "ctypeDict")

            dictionaryOutput = parserTwidlGenerator()

            # step 1, Create Py Struct Definition Files
            importDict = dictionaryOutput.CreateFiles(parser.GetObjectList(), self.destDir)

            # step 2, Import Data Control Information
            sys.path.append(os.path.dirname(self.dataControlFile))
            from src.software.datacontrol.dataControlGenMain import DatacontrolGenCSV

            dataControlObj = DatacontrolGenCSV(self.dataControlFile)
            dataControlDict = dataControlObj.getDict()
            self.nameToUidConverterGen(dataControlDict)

            dictionary = self.__CreateDictionary(parser.GetObjectList(), dataControlDict, importDict)

            if dictionary == None:
                self.errors += 1

            self.dictionary = dictionary


    def nameToUidConverterGen(self, dataControlDict):
        #print dataControlDict
        for uidNum, uid in dataControlDict.iteritems():
            self.nameToUidConverter[str(uid.structName)] = str(uidNum)
            self.tNameToUidConverter[str(uid.structName) + "_t"] = str(uidNum)

    ### TWIDL Dictionary Creation
    def __CreateDictionary(self, objList, dataControlDict, importDict):
        if self.errors == 0:
            print("==Creating Dictionary from Imports==\n")
            ctypeDictionary= dict()

            for i, objEntry in enumerate(objList):
                # Add basic information
                #objStruct = objEntry.getObjStruct() #information lost when this is done, deal directly
                # @todo: what is the best way to create keys
                '''
                need to be the _t version to be compatible with how imports are named
                '''
                uidName = objEntry.getName()
                uidNum = objEntry.getUid()

                if uidNum == None:
                    print("uid is None!")

                if i%5 == 0:
                    print ("\n")
                print("%s..." % uidName)

                major = int(objEntry.getMajorVersion())
                minor = int(objEntry.getMinorVersion())

                ctypeDictionary[uidNum] = dict(versionMajor= major, versionMinor = minor, sizeInBytes = int(objEntry.getSize()) )

                # Add dataControl information
                if dataControlDict.get(str(uidNum)):
                    description = dataControlDict[str(uidNum)].description
                    author = dataControlDict[str(uidNum)].owner
                else:
                    description = "Not available"
                    author = "Not available"

                ctypeDictionary[uidNum]["description"] = description
                ctypeDictionary[uidNum]["author"] = author

                # Add dynamic Object
                try:
                    importFileName, importName, twidlType = importDict[uidNum]
                    sys.path.append(self.destDir)
                    importObj = None
                    exec("from %s import %s"%(importFileName, importName))
                    exec("importObj = %s()" % importName)
                    obj = self.__getDynamic(importName, importObj._fields_, importObj._pack_, twidlType)
                except Exception as e:
                    print("ERROR: An exception occurred: {0}".format(e))
                    traceback.print_exc()
                    #quit(1)

                    obj = None
                ctypeDictionary[uidNum]["ctypeStructure"] = obj

            return ctypeDictionary

    def getUid(self, uidName):
        '''
        Map struct Name to appropriate Number uid
        '''
        uid = self.nameToUidConverter.get(uidName)
        if (uid is None):
            self.unmappedNamesToUid.append(uidName)
        try:
            uid = int(uid)
        except:
            pass
        return uid

    def getUidT(self, uidName):
        '''
        Map struct Name to appropriate Number uid, return int uid if possible, None if None, and string uid if not convertible to int
        '''
        uid = self.tNameToUidConverter.get(uidName)
        if (uid is None):
            self.unmappedNamesToUid.append(uidName)
        try:
            uid = int(uid)
        except:
            pass
        return uid


    def __getDynamic(self, ctypeName, fields, pack, twidlType):

        if twidlType == "struct":
            class CtypeStruct(Structure):
                _fields_ = fields
                _pack_ = pack

            CtypeStruct.__name__ = ctypeName

            return CtypeStruct

        elif twidlType == "union":
            class CtypeUnion(Union):
                 _pack_  =  ctypeObj._pack_
                 _fields_ = ctypeObj._fields_

            CtypeUnion.__name__ = ctypeName

            return CtypeUnion
        else:
            print("Unknown type: Unable to create Dynamic version of %s" % (twidlType))
            self.errors += 1
            return None

    def printDict(self):
        print("==Printing Dictionary==\n")
        pprint.pprint(self.dictionary)
        if self.errors == 0:
            outFile = os.path.abspath(os.path.join(self.destDir, "ctypeDict_printDict.py"))
            print("For file print, see: %s" % outFile)

            with open(outFile, "w+") as outFile:
                outFile.write("\'\'\'\nThis file is automatically generated by createTwidlDict.py.  Please do not modify.\n\'\'\'\n")
                outFile.write("Dict = {\n")
                for key, value in self.dictionary.iteritems():
                    outFile.write("    %s : %s,\n"%(key,value))

                outFile.write("}")
            return

    def getDictionary(self):
        return self.dictionary, self.errors



def getDictionary(uidList = None):
    # Set the debug level
    #OutputLog.setDebugLevel(options.debug)
    OutputLog.setDebugLevel(10)

    #change global
    if uidList is not None:
        global ITEMS
        ITEMS = uidList

    ### Perform Test ###
    OutputLog.Information("\nRunning Twidl Dictionary Gen... \n")
    ddg = twidlDictGenerator()
    dictionary, errors = ddg.getDictionary()

    #print output
    ddg.printDict()

    if(errors == 0):
        OutputLog.Information("passed.")
    else: OutputLog.Information("failed.")
    return dictionary

#===TEST: See which uids are creating ctypes===
def test():
    listAll = ITEMS
    listCorrect = ""
    listFailed = ""
    for i, uid in enumerate(listAll.split(',')):
        try:
            d = getDictionary(uid)
            if not d: #if empty dict
                listFailed = listFailed + str(uid) + ","
            else:
                listCorrect = listCorrect + str(uid) + ","
        except Exception as e:
            print ("%s: %s\n" % (uid,e))
            listFailed = listFailed + str(uid) + ","
    listCorrect = listCorrect[:-1]
    print("passed:", listCorrect, "failed:", listFailed)
    print(getDictionary(listCorrect))
    return listCorrect, listFailed

#=== TEST: test sizeof correctly matches ===
def testSize():
    listCorrect = ""
    listFailed = ""

    d = getDictionary()
    for uid, entry in d.iteritems():
        try:
            size = entry["sizeInBytes"]
            sizeExpected = ctypes.sizeof(entry["ctypeStructure"])
            print ("%s: expected: %s, true size = %s\n" %(uid, size, sizeExpected))
            if int(size) != sizeExpected:
                listFailed = listFailed + str(uid) + ","
            else:
                listCorrect = listCorrect + str(uid) + ","
        except Exception as e:
            print ("%s: %s\n" % (uid,e))
            listFailed = listFailed + str(uid) + ","
    print(listCorrect)
    return listCorrect, listFailed

#Test Funciton, @ todo: remove when testing is over
def getTelemetryItemsFromFileNameList(fileList):
    '''takes as input a text file with names of telemetry binaries'''
    li = []
    with open(fileList, 'r') as rfile:
        lines = rfile.readlines()

    for line in lines:
        name = re.findall('[a-zA-Z0-9-]+_[a-zA-Z0-9-]+_[a-zA-Z0-9-_]+.bin', line)
        li.append(name)
    print (li)
    return li



######## Test it #######
if __name__ == '__main__':
    from datetime import datetime
    p = datetime.now()
    getDictionary()
    #test()
    #testSize()
    #getOverlappingSet(ITEMS_VERSIONED, ITEMS_CORRECT_SIZE)
    q = datetime.now()
    OutputLog.Information("\nExecution time: "+str(q-p))

