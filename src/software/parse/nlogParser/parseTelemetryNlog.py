#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors:Joseph Tarango, Daniel Garces, Randal Eike
# *****************************************************************************/

import re, os, sys, codecs, array, ctypes, time, glob, math
import argparse

#### import Telemetry modules
from src.software.parse.nlogParser.telemetryutil.telemetry_util import openWriteFile
from src.software.parse.nlogParser.telemetryutil.telemetry_util import GetDefaultFileName
from src.software.parse.nlogParser.test_util.output_log import OutputLog
from src.software.parse.nlogParser.telemetry_parsers.telemetry_nlog import TelemetryV2NlogEventParserL2

##### .exe extension patch for the compiled version of this script
if not re.search('\.PY$|\.PYC$|\.EXE$', os.path.split(sys.argv[0])[1].upper()):
    sys.argv[0] = os.path.join( os.path.split(sys.argv[0])[0] , os.path.split(sys.argv[0])[1]+'.exe' )

### Get the build base directory
buildBaseDirectory = os.path.abspath("./")

#### extend the Python search path to include TWIDL_tools directory
if __name__ == '__main__':
    twidlcore = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    sys.path.insert(0, twidlcore)


### Global variables
TOOL_VERSION    = 5.0
DEBUG_VERSION   = 0

def ReadNlogList(listFileName):
    """
    Read the nlog file list and return the file name contents as list

    @param listFileName - Path/Filename of filename list

    @return list - List of nlog path/file .bin names to parse
    """
    ### open input file ###
    try:
        listFile = open(listFileName,"rt")
    except IOError:
        OutputLog.Error(format("Unable to open file \"%s\" for reading\n" % (listFileName)))
        listFile = None

    # Create List
    nlogFileList = []
    if (listFile is not None):
        for nlogBinName in listFile:
            nlogBinName = nlogBinName.replace(',','')
            nlogBinName = nlogBinName.replace('\n','')
            nlogBinName = nlogBinName.replace('\\','/')
            nlogBinName = nlogBinName.replace('\"','')
            nlogFileList.append(nlogBinName)

    # return list
    return nlogFileList

def nlogParserAPI(inputfiles=None, nlogListFile=None, nlogFormats=buildBaseDirectory+'/Nlog_formats.py',
                  nlogenum=buildBaseDirectory+'/nlogEnumParser.py', outputFile='nlog.txt', triageFileName=None,
                  inputVersion=2.0, debug=0):
    returnStatus = False

    # Assign the argument values
    OutputLog.setDebugLevel(debug)

    # Get the input file version
    if (inputVersion >= 2.0): binPack = TelemetryV2NlogEventParserL2.PACKED_DATA
    elif (inputVersion <= 1.6): binPack = TelemetryV2NlogEventParserL2.ALIGNED_512
    else:
        OutputLog.Error(format("Invalid telemetry version value %1.1f.  Allowed values: 1.4, 1.5, 1.6 and 2.x" % (inputVersion)))

    # Check for input file list file
    inputfiles = inputfiles
    if (nlogListFile is not None):
        inputfiles.extend(ReadNlogList(nlogListFile))

    # File list created, parse the data
    OutputLog.Information(format("\nAttempting to parse file nlogs, File alignment type: %1.1f..." % (inputVersion)))
    masterEventList = []

    parser = TelemetryV2NlogEventParserL2(None, binPack)

    for fileName in inputfiles:
        parser.setNlogBinFileName(fileName)

        # Parse the input file
        OutputLog.DebugPrint(1, format("\nAttempting to parse file \"%s\", File alignment type: %1.1f..." % (fileName, inputVersion)))

        # Generate the event list
        eventList = parser.getEventTupleList()

        # Add the list to the master
        if (len(eventList) > 0): masterEventList.extend(eventList)

    # Translate the master event tuple list into text
    nlogTextList, headerText, triageText = parser.xlateToText(masterEventList, nlogFormats, nlogenum)

    # Output the text file(s)
    if (outputFile is not None):
        outputStream = openWriteFile(outputFile, True)
    else:
        outputStream = sys.stdout

    if (outputStream is not None):
        parser.WriteNlogStream(outputStream, headerText, nlogTextList)
        outputStream.close()
        returnStatus = True

    if (triageFileName is not None):
        outputStream = openWriteFile(triageFileName, True)
    else:
        outputStream = None

    if (outputStream is not None):
        parser.WriteTriageStream(outputStream, triageText)
        outputStream.close()

    return returnStatus

def main():
    #### Command-line arguments ####
    parser = argparse.ArgumentParser(description="Translate the input nlog.bin files into text and save to a file")
    parser.add_argument('--version', action='version', version='%(prog)s Version:'+str(TOOL_VERSION))
    parser.add_argument('--verbose', '-v', action='count', dest='debug', default=0, help='Increase debug message level')
    parser.add_argument('--debug', action='store', dest='debug', type=int, default=0, help='Set debug message level')
    parser.add_argument('-t', '--type', action='store', dest='inputVersion', type=float, default=2.0, help='Telemetry file version.  Allowed values - 1.4, 1.5, 1.6 and 2.x, Default = 2.0')
    parser.add_argument('-o', action='store', dest='outputFile', type=str, default='nlog.txt', help='Output file path/name, default = nlog.txt')
    parser.add_argument('--formats', action='store', dest="nlogFormats", type=str, default=buildBaseDirectory+'/Nlog_formats.py', help='Path/filename of Nlog_formats.py file for this build, default = <buildBase>/Nlog_formats.py')
    parser.add_argument('--enum', action='store', dest="nlogenum", type=str, default=buildBaseDirectory+'/nlogEnumParser.py', help='Path/filename of nlogEnumParser.py file for this build, default = <buildBase>/nlogEnumParser.py')
    parser.add_argument('-i', action='store', dest="nlogListFile", type=str, default=None, help='File containing Path/filename nlog bin files to parse')
    parser.add_argument('--triage', action='store', dest="triageFileName", type=str, default=None, help='File containing Path/filename of triage output')
    parser.add_argument('inputfiles', action='store', nargs='*', type=str, help='List of Path/filename nlog bin files to parse')
    options = parser.parse_args()

    print(options.inputfiles)
    returnStatus = nlogParserAPI(inputfiles=options.inputfiles, nlogListFile=options.nlogListFile,
                                 nlogFormats=options.nlogFormats, nlogenum=options.nlogenum,
                                 outputFile=options.outputFile, triageFileName=options.triageFileName,
                                 inputVersion=options.inputVersion, debug=options.debug)
    return returnStatus

######## Test it #######
if __name__ == '__main__':
    from datetime import datetime
    p = datetime.now()
    main()
    q = datetime.now()
    OutputLog.DebugPrint(2, "\nExecution time: "+str(q-p))

