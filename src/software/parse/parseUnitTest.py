#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Randal Eike, Phuong Tran, Joseph Tarango
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import re, os, sys, array, ctypes, time, glob, getopt, math
from optparse import OptionParser, OptionGroup
from operator import itemgetter

##### .exe extension patch for the compiled version of this script
if not re.search('\.PY$|\.PYC$|\.EXE$', os.path.split(sys.argv[0])[1].upper()):
    sys.argv[0] = os.path.join( os.path.split(sys.argv[0])[0] , os.path.split(sys.argv[0])[1]+'.exe' )

#### extend the Python search path to include TWIDL_tools directory
if __name__ == '__main__':
    twidlcore = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    sys.path.insert(0,twidlcore)

# Token objects
from src.software.parse.autoObjects import structDef
from src.software.parse.autoObjects import objectDefine
from src.software.parse.autoObjects import ctypedef

# Parser Generators
from src.software.parse.parserDictionaryGen import parserDictionaryGenerator
from src.software.parse.parserTwidlGen import parserTwidlGenerator
from src.software.parse.parserXmlGen import parserXmlGenerator

#### import test utilities
from src.software.parse.structdefParser import structdefParser
from src.software.parse.output_log import *

TOOL_VERSION = 1.0

def parserUnitTest(fileName, destDir, destDir1, destDir2):
    parser = structdefParser()

    inputfile = open(fileName, "rt")
    errors = parser.parseDefFile(inputfile)
    inputfile.close()

    # Debug output
    parser.GetStructList().debugPrint()

    dictOutput = parserDictionaryGenerator()
    dictOutput.CreateFiles(parser.GetObjectList(), destDir)

    twidlOutput = parserTwidlGenerator()
    twidlOutput.CreateFiles(parser.GetObjectList(), destDir1)

    twidlOutput = parserXmlGenerator()
    twidlOutput.CreateFiles(parser.GetObjectList(), destDir2)

    return errors

def main():
    #### Command-line arguments ####
    #parser = OptionParser(usage="usage: %prog [options] outputFile", version="%prog Version: "+str(TOOL_VERSION))
    #parser.add_option('--debug',type="int", dest='debug', action="store", default=0, help='Enable debug level')
    #(options, args) = parser.parse_args()

    # Set the debug level
    #OutputLog.setDebugLevel(options.debug)
    OutputLog.setDebugLevel(10)

    # Set the input file
    #if (len(args) >= 1):
    #    srcFile = args[0]
    #else:

    srcFile = "C:\\source\\TV2_adp\\telemetry\\nand\\gen3\\projects\\objs\\cdrr_ca\\telemetry\\ctypeAutoGen_structDefs.txt"
    destDir = "C:\\source\\TV2_adp\\telemetry\\nand\\gen3\\projects\\objs\\cdrr_ca\\telemetry\\tokenParsers"
    destDir1 = "C:\\source\\TV2_adp\\telemetry\\nand\\gen3\\projects\\objs\\cdrr_ca\\telemetry\\twidlParsers"
    destDir2 = "C:\\source\\TV2_adp\\telemetry\\nand\\gen3\\projects\\objs\\cdrr_ca\\telemetry\\xmlParsers"

    ### Perform Test ###
    OutputLog.Information("Start unit test... " )
    errors = parserUnitTest(srcFile, destDir, destDir1, destDir2)

    if(errors == 0): OutputLog.Information("passed.")
    else: OutputLog.Information("failed.")
    return errors

######## Test it #######
if __name__ == '__main__':
    from datetime import datetime
    p = datetime.now()
    main()
    q = datetime.now()
    OutputLog.Information("\nExecution time: "+str(q-p))
