#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
# Future Python API for execution of Control Flag through binary hooks.
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, unicode_literals

import os, datetime, shutil, faulthandler, traceback
import argparse, re, subprocess


class DlaSection:
    pass


class BuildCFG():

    def cmd_exists(self, native_Cmd=''):
        if native_Cmd is not None:
            return_Obj = subprocess.call("type " + native_Cmd, shell=True, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE) == 0
        else:
            return_Obj = 0
        return return_Obj

    def main(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-f", "--fpga", help="Parse the map and dla file", action="store_true")
        parser.add_argument("-r", "--repo", help="Parse HG file for functions", action="store_true")
        parser.add_argument("-d", "--dla", help="DLA file to parse")
        parser.add_argument("-func", "--function", nargs='+', help="Output call tree for these functions")
        parser.add_argument("-e", "--enum", nargs='+', help="Output call three for these enums")
        parser.add_argument("-g", "--globalsym", nargs='+', help="Output call tree for these global symbols")
        args = parser.parse_args()
        dlaFileToOpen = args.dla
        # Get static call table & parse the map file
        print("--- Parsing DLA file ---\n");

        print("-I- Parsing " + dlaFileToOpen + "\n")

        print("-I- Started DLA dump")

        dlaDumpFile = open("dlaDump.txt", "w")
        commandString = "gdump.exe"
        ghs_exists = self.cmd_exists(commandString)
        # grab the gdump output and output it to a text file
        if ghs_exists != 0:
            subprocess.call([commandString, dlaFileToOpen], stdout=dlaDumpFile)

        dlaDumpFile.close()

        print("-I- Finished DLA dump")
        print("-I- Started DLA file parsing")

        dlaDumpFile = open("dlaDump.txt", "r")
        actualCallFile = open("actualCalls.txt", "w")
        staticCallFile = open("staticCalls.txt", "w")
        enumRefs = open("enumRefs.txt", "w")
        cppRefs = open("cppRefs.txt", "w")
        globalSymbolRefs = open("globalSymbolRefs.txt", "w")

        # iterate through gdump output and grab all static calls
        dlaSection = DlaSection.NONE
        prevLine = ""

        functions = []
        lastFunction = ""

        enums = {}
        globalSymbols = {}

        for line in dlaDumpFile:
            parsedLine = filter(None, line.strip().split())

            # we are entering a new section
            if "----------------" in line:
                if "Actual Calls" in prevLine:
                    dlaSection = DlaSection.ACTUAL_CALLS
                elif "Static Calls" in prevLine:
                    dlaSection = DlaSection.STATIC_CALLS
                elif "Global Symbols" in prevLine:
                    dlaSection = DlaSection.GLOBAL_SYMBOLS
                    globalSymbols = {}
                elif "Symbols" in prevLine:
                    dlaSection = DlaSection.SYMBOLS
                    enums = {}
                    lastFunction = ""
                elif "Procs" in prevLine:
                    dlaSection = DlaSection.PROCS
                    functions = []
                    lastFunction = ""
                elif "Cross References" in prevLine:
                    dlaSection = DlaSection.CROSS_REFERENCE
                else:
                    dlaSection = DlaSection.OTHER

            if dlaSection == DlaSection.ACTUAL_CALLS:
                actualCallFile.write("%s" % line)
            elif dlaSection == DlaSection.STATIC_CALLS:
                staticCallFile.write("%s" % line)
            elif dlaSection == DlaSection.SYMBOLS:
                if "Typedef  Info C++ Enum" in line:
                    # we have found the start of an enum
                    cppEnumSearch = re.search('^\s*\(\"\w+::(\w+)\"\,', parsedLine[1])

                    if cppEnumSearch:
                        enums[parsedLine[0].replace(":", "")] = cppEnumSearch.group(1)
                    else:
                        enums[parsedLine[0].replace(":", "")] = parsedLine[1].replace("\"", "")
                elif "Procedure-Begin" in line:
                    # we have found the start of a function - grab the name
                    cppFunctionSearch = re.search('^\s*\(\"(\w+::\w+)\(', parsedLine[1])

                    if cppFunctionSearch:
                        lastFunction = cppFunctionSearch.group(1)
                    else:
                        lastFunction = parsedLine[1].replace("\"", "")
                elif "Procedure-End" in line:
                    # we have exited a function
                    lastFunction = ""
                elif (lastFunction != "") & ("Param" in line) & ("ref =" in line) & ("Optimized-Away" not in line):
                    # have we found an enum?
                    enumReferenced = parsedLine[-1]
                    if (enums.has_key(enumReferenced)):
                        enumRefs.write("%s %s\n" % (enums[enumReferenced], lastFunction))
            elif dlaSection == DlaSection.GLOBAL_SYMBOLS:
                globalSymbolSearch = re.search('^(\d+):\"(\w+)\"', line)

                if globalSymbolSearch:
                    globalSymbols[globalSymbolSearch.group(1)] = globalSymbolSearch.group(2)
            elif dlaSection == DlaSection.PROCS:
                # we have found the start of a function - grab the name
                cppFunctionSearch = re.search('^\d+:\s*\(\"([\w<>, ]+::[\w<>, ]+)\([\w<>, ]*\)[\w ]*\",\"([\w]+)\"',
                                              line)

                if cppFunctionSearch:
                    cppRefs.write("\"%s\" \"%s\"\n" % (cppFunctionSearch.group(1), cppFunctionSearch.group(2)))
                    lastFunction = cppFunctionSearch.group(1)
                elif "adrs:" in line:
                    lastFunction = line.split()[1].replace("\"", "")

                functionDetailsSearch = re.search(
                    '\s+[\w:,\-\+ \(\)]+srcline:\(\d+,(\d+),(\d+)\)[\w:,\-\+ \(\)]+file:(\d)', line)

                if functionDetailsSearch:
                    functions.append([lastFunction, functionDetailsSearch.group(3), functionDetailsSearch.group(1),
                                      functionDetailsSearch.group(2)])
            elif dlaSection == DlaSection.CROSS_REFERENCE:
                referenceSearch = re.search('^\d+:\s*iSym:(\d+) [\w:]+ file:(\d+) line:(\d+)', line)

                if referenceSearch:
                    if globalSymbols.has_key(referenceSearch.group(1)):
                        globalSymbol = globalSymbols[referenceSearch.group(1)]
                        file = referenceSearch.group(2)
                        lineNumber = referenceSearch.group(3)

                        for function in functions:
                            if (function[1] == file) & (function[2] <= lineNumber) & (function[3] >= lineNumber):
                                globalSymbolRefs.write("%s %s\n" % (globalSymbol, function[0]))
                                break

            prevLine = line

        actualCallFile.close()
        staticCallFile.close()
        dlaDumpFile.close()
        enumRefs.close()
        cppRefs.close()
        globalSymbolRefs.close()

        print("  -I- Initial parsing complete")

        staticFile = open("staticCalls.txt", "r")
        staticRefined = open("staticReferences.txt", "w")

        # iterate through static calls to grab and format details on who calls what
        while 1:
            line = staticFile.readline()

            if (line != "\n"):
                if (not line):
                    break;

            if ("  calls" in line) & ("<<address_taken>>" not in line):
                caller = re.findall(r'\"(.+?)\"', line);
                while 1:
                    line = staticFile.readline()

                    if line == "\n":
                        break;

                    line = line.strip().split()[0] + " " + caller[0] + "\n"
                    staticRefined.write("%s" % line)

        staticFile.close()
        staticRefined.close()

        actualFile = open("actualCalls.txt", "r")
        actualRefined = open("actualReferences.txt", "w")

        # iterate through static calls to grab and format details on who calls what
        while 1:
            line = actualFile.readline()

            if (line != "\n"):
                if (not line):
                    break;

            if ((" calls" in line) & ("no calls" not in line) | ("(typeref)" in line)) & ("." not in line) & (
                    "<<address_taken>>" not in line):
                caller = re.findall(r'\"(.+?)\"', line);
                while 1:
                    line = actualFile.readline()

                    if line == "\n":
                        break;

                    line = line.strip().split()[0] + " " + caller[0] + "\n"
                    actualRefined.write("%s" % line)

        actualFile.close()
        actualRefined.close()

        os.remove("actualCalls.txt")
        os.remove("staticCalls.txt")
        os.remove("dlaDump.txt")

        print("  -I- Refining complete")
        print("-I- Finished DLA file parsing")
        print("\n-I- DONE\n")

        output = open("output.txt", "w")

        functions = set([])
        functionCount = []

        enums = set([])
        globalSymbols = set([])
        return


def mainFaultContext():
    """
    Main stand alone script function.
    Returns: status of execution.
    """
    ##############################################
    # Main and fault context save
    ##############################################
    faultSave = True
    segfaultFile = None
    if faultSave:
        faultFolder = "../data/faultContext"
        shutil.rmtree(path=faultFolder, ignore_errors=True)
        os.makedirs(faultFolder, mode=0o777, exist_ok=True)
        faultFolder = os.path.abspath(faultFolder)
        faultFile = "fault.dump"
        faultLocation = os.path.abspath(os.path.join(faultFolder, faultFile))
        segfaultFile = open(file=faultLocation, mode='w+', buffering=1)
        faulthandler.enable(file=segfaultFile, all_threads=True)

    statusCode = -1
    try:
        # @todo jdtarang Create GUI
        print()
    except Exception as errorContext:
        print("Fail End Process: ", errorContext)
        traceback.print_exc()
        if faultSave and segfaultFile is not None:
            faulthandler.dump_traceback(file=segfaultFile, all_threads=True)
    finally:
        if faultSave:
            faulthandler.disable()
            segfaultFile.close()
        print(f"Exiting with code {statusCode}.")
    return statusCode


if __name__ == '__main__':
    """Performs execution delta of the process."""
    p = datetime.datetime.now()
    status_code = mainFaultContext()
    q = datetime.datetime.now()
    print(f"Execution time: {str(q - p)} with code {status_code}")
