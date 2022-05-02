#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import re, sys, os, datetime, inspect, traceback, pprint

##############################################
# Python generic info
##############################################
"""
Requires
    https://graphviz.gitlab.io/_pages/Download/windows/graphviz-2.38.msi
    install path https://graphviz.gitlab.io/_pages/Download/windows/graphviz-2.38.msi
    Add to path C:\\Program Files (x86)\\Graphviz2.38\\bin\\dot.exe
"""
# .exe extension patch for the compiled version of this script
if not re.search(pattern='\.PY$|\.PYC$|\.EXE$', string=os.path.split(sys.argv[0])[1].upper()):
    sys.argv[0] = os.path.join(os.path.split(sys.argv[0])[0], os.path.split(sys.argv[0])[1] + '.exe')


##############################################
# Libraries
##############################################

def whoami(annotate=True):
    frame = inspect.currentframe().f_back
    fileName = inspect.getframeinfo(frame).filename
    functionName = inspect.getframeinfo(frame).function
    lineNumber = inspect.getframeinfo(frame).lineno
    traceContext = pprint.pformat(traceback.format_exc(limit=None, chain=True))
    if annotate:
        fileName = ''.join(["File=", fileName])
        functionName = ''.join(["Function=", functionName])
        lineNumber = ''.join(["Line=", str(lineNumber)])

    return fileName, functionName, lineNumber, traceContext


def devGraphAll(options, args):
    ##############################################
    # Debug Graphing
    ##############################################
    # import necessary paths
    importPath = os.path.abspath(os.getcwd())
    importPathNext = os.path.abspath(os.path.join(importPath, "pycallgraph"))
    print("Importing Paths: ", str(importPath), str(importPathNext))
    sys.path.insert(1, importPath)
    sys.path.insert(1, importPathNext)

    importPathNext = os.path.abspath(os.path.join(importPath, "pycallgraph", "output"))
    print("Importing Paths: ", str(importPath), str(importPathNext))
    sys.path.insert(1, importPath)
    sys.path.insert(1, importPathNext)

    try:
        importPathNext = os.path.abspath('C:\\Program Files (x86)\\Graphviz2.38\\bin\\dot.exe')
        print("Importing Paths: ", str(importPath), str(importPathNext))
        sys.path.insert(1, importPath)
        sys.path.insert(1, importPathNext)
    except Exception as ErrorContext:
        print(ErrorContext)
        pass

    status = 0
    ##############################################
    # Library
    ##############################################
    try:
        from pycallgraph2 import PyCallGraph
        from pycallgraph2.output import GraphvizOutput
        from pycallgraph2 import Config

        ##############################################
        # Configuration
        ##############################################
        graphviz = GraphvizOutput()
        graphviz.output_type = 'svg'
        graphviz.output_file = 'pycallgraph.svg'

        configList = Config()
        configList.output = None
        configList.verbose = True
        configList.debug = False
        configList.groups = True
        configList.threaded = False
        configList.max_depth = 2 ** 31

        print(options, args)
        with PyCallGraph(output=graphviz, config=configList):
            callReturn = 1
            print("PyCallGraphReturn", callReturn)
            # status = testDrive(driveNumber) # Debug code goes here
    except:
        pass
    return status


def main():
    ##############################################
    # Main function, Options
    ##############################################
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--example", action='store_true', dest='example', default=False,
                      help='Show command execution example.')
    parser.add_option("--debug", action='store_true', dest='debug', default=False, help='Debug mode.')
    parser.add_option("--verbose", action='store_true', dest='verbose', default=False,
                      help='Verbose printing for debug use.')
    (options, args) = parser.parse_args()
    devGraphAll(options=options, args=args)
    return 0


# Main Execute
if __name__ == '__main__':
    p = datetime.datetime.now()
    main()
    q = datetime.datetime.now()
    print("Execution time: " + str(q - p))
