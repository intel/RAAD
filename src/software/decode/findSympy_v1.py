#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
# @package findSympy_v1
# *****************************************************************************/
"""
Brief:
    Extract compiled code control/data flow into interpreted code.
    See Also for symbols in object files, libraries, and shared objects.

Author(s):
    Joe Tarango

Requirement(s):
    Firmware project must be built prior to running the tool.

Documentation:
    https://llvm.org/docs/CommandGuide/llvm-dwarfdump.html
    https://en.wikipedia.org/wiki/DWARF
    https://nil-wiki/Telemetry+Parsing+Guide

    Green Hills Compiler
    Compiling hello.c executable file called a.out is generated, together with the
    following additional files:hello.o, a.map, a.dnm & a.dla
    The a.map file is a map file produced by the linker. The a.dnm & a.dla files
    contain basic debugging information.

    Source		Assembly Files (.s)		Object Files (.o)		Libraries (.a)
       ||              ||                     ||                    ||
       \/              \/                     |===================> \/
    Compiler =====> Assembler ====================================> Linker =========> Executable

    The following table describes data type alignments for C and C++.C/C++
      data type		Size		Alignment
      char			8			8
      short			16			16
      int			32			32
      long			32			32
      long long		64			32
      float			32			32
      double		64			32
      long double	64			32
      *(pointer)	32			32
      enum(default)	32			32
"""
import os, re, sys, optparse, datetime, tempfile, csv


class SymLocation():
    symbolType = None
    rootDirectory = None
    fileName = None
    symbolLineNumber = None
    symbolLineContent = None

    def __init__(self, symbolType, rootDirectory, fileName, symbolLineNumber, symbolLineContent):
        self.symbolType = symbolType
        self.rootDirectory = rootDirectory
        self.fileName = fileName
        self.symbolLineNumber = symbolLineNumber
        self.symbolLineContent = symbolLineContent
        return

    def getList(self):
        listItem = [self.symbolType, self.rootDirectory, self.fileName, self.symbolLineNumber, self.symbolLineContent]
        return listItem


class SymProbe(object):
    # Class to search for symbols in object files, libraries, and shared objects.
    # Find weak symbols by default, since they're used frequently in INTEGRITY
    #  code and are a source of confusion when not found on a search

    path = None
    sym = None
    refs = None
    dodecode = True
    allow_weak = True
    debug = False
    verbose = False
    savePath = None
    saveFilePrefix = None
    gnmbinary = "gnm.exe"  # I.E. C:\\ghs\\424all\\gnm.exe
    decodebinary = "decode.exe"  # I.E. C:\\ghs\\424all\\decode.exe

    findlibs = None
    findobjs = None
    findsharedlibs = None
    findsym = None
    verifyglob = None
    verifydef = None
    verifybof = None

    symbolRefGlobal = None
    symbolLocGlobal = None

    def __init__(self):
        return

    def usage(self):
        usage = f"Usage: {__file__}.py --sym <symbol> [--path <directory>] [--refs] [--nodecode]"
        parser = optparse.OptionParser(usage)
        parser.add_option("--path", dest='path', metavar='<PATH>', default=None,
                          help='Where to search (defaults to current directory.')
        parser.add_option("--sym", dest='sym', metavar='<SYM>', default=None, help='What symbol to search for.')
        parser.add_option("--refs", dest='refs', metavar='<REFS>', default=None,
                          help='Search for references instead of definitions.')
        parser.add_option("--nodecode", dest='refs', metavar='<REFS>', default=True, help='Do not decode C++ symbol.')
        parser.add_option("--noweak", dest='noweak', metavar='<NOWEAK>', default=True,
                          help='Do not allow weak symbols in place of GLOB symbols.')
        parser.add_option("--gnmbinary", dest='gnmbinary', metavar='<GNMBINARY>', default=None,
                          help='Provided binary to probe gnm.')
        parser.add_option("--decodebinary", dest='decodebinary', metavar='<DECODEBINARY>', default=None,
                          help='Provided binary to decode binary.')
        parser.add_option("--savePath", dest='savepath', metavar='<SAVEPATH>', default=None,
                          help='File save directory.')
        parser.add_option("--saveFilePrefix", dest='savefileprefix', metavar='<SAVEFILEPREFIX>', default=None,
                          help='File save prefix.')
        parser.add_option("--debug", action='store_true', dest='debug', default=False, help='Debug mode.')
        parser.add_option("--verbose", action='store_true', dest='verbose', default=False,
                          help='Verbose printing for debug use.')
        (options, args) = parser.parse_args()

        if options.path is not None:
            self.path = options.path
        if options.sym is not None:
            self.sym = options.sym
        if options.refs is not None:
            self.refs = options.refs
        if self.dodecode:
            self.dodecode = options.nodecode
        if options.allow_weak is None:
            self.allow_weak = options.noweak
        if options.gnmbinary is not None:
            self.gnmbinary = options.gnmbinary
        if options.decodebinary is not None:
            self.decodebinary = options.decodebinary

        self.savePath = options.savePath
        self.saveFilePrefix = options.saveFilePrefix
        self.debug = options.debug
        self.verbose = options.verbose
        return (options, args)

    def verifyBinaries(self):
        try:
            os.stat(self.gnmbinary)
        except:
            print("Could not stat gnm executable!")
            sys.exit()

        try:
            os.stat(self.decodebinary)
        except:
            print("Could not stat decode executable!")
            sys.exit()
        return

    def setContext(self):
        self.findlibs = re.compile('\.a$')
        self.findobjs = re.compile('((\.obj)|(\.o))$')
        self.findsharedlibs = re.compile('\.so$')
        self.findsym = re.compile(self.sym)
        if (self.allow_weak):
            self.verifyglob = re.compile('(GLOB)|(WEAK)')
        else:
            self.verifyglob = re.compile('GLOB')
        self.verifydef = re.compile('UNDEF')
        self.verifybof = re.compile('\.\.[b,e]of')
        return

    def findReference(self, root, name):
        symbolReference = []
        symbolLocation = []

        if self.debug:
            print("CURRENT FILE: " + os.path.join(root, name))

        if self.dodecode:
            (inputStream, outputStream) = os.popen2(
                self.gnmbinary + ' ' + os.path.join(root, name) + ' | ' + self.decodebinary, "t", -1)
        else:
            (inputStream, outputStream) = os.popen2(self.gnmbinary + ' ' + os.path.join(root, name), "t", -1)

        lineNumber = 0
        line = outputStream.readline()
        while (line):
            candidateSym = self.findsym.search(line, 1)
            candidateVerifyGlob = self.verifyglob.search(line, 1)
            candidateVerifyDef = self.verifydef.search(line, 1)
            candidateVerifyBof = self.verifybof.search(line, 1)

            if self.refs:
                if candidateSym and candidateVerifyGlob and candidateVerifyDef and not candidateVerifyBof:
                    if self.debug:
                        print("Symbol reference found in " + os.path.join(root, name) + "\n" + line)
                    symItem = SymLocation(symbolType="Reference", rootDirectory=root, fileName=name,
                                          symbolLineNumber=lineNumber, symbolLineContent=line)
                    symbolReference.append(symItem)
            else:
                if candidateSym and candidateVerifyGlob and not candidateVerifyDef and not candidateVerifyBof:
                    if self.debug:
                        print("Symbol found in " + os.path.join(root, name) + "\n" + line)
                    symItem = SymLocation(symbolType="Location", rootDirectory=root, fileName=name,
                                          symbolLineNumber=lineNumber, symbolLineContent=line)
                    symbolReference.append(symItem)
            line = outputStream.readline()
            lineNumber += 1

        return (symbolReference, symbolLocation)

    def crawl(self):
        symbolRefGlobal = []
        symbolLocGlobal = []
        for root, dirs, files in os.walk(self.path):
            for name in files:
                itemObj = self.findobjs.search(name, 1)
                libObj = self.findlibs.search(name, 1)
                sharedLibObj = self.findsharedlibs.search(name, 1)
                if itemObj or libObj or sharedLibObj:
                    (symbolReference, symbolLocation) = self.findReference(root=root, name=name)
                    symbolRefGlobal.extend(symbolReference)
                    symbolLocGlobal.extend(symbolLocation)
        self.symbolRefGlobal = symbolRefGlobal
        self.symbolLocGlobal = symbolLocGlobal
        return

    @staticmethod
    def getTempPathName(genPath=True):
        if genPath is True:
            generatedPath = tempfile.gettempdir()
        else:
            generatedPath = ""
        return generatedPath

    @staticmethod
    def getTempFileName(genFile=True):
        utc_datetime = datetime.datetime.utcnow()
        utc_datetime.strftime("%Y-%m-%d-%H%MZ")
        if genFile is True:
            fileConstruct = utc_datetime + next(tempfile._get_candidate_names())
        else:
            fileConstruct = ""
        return fileConstruct

    @staticmethod
    def saveContent(filename, symList):
        with open(filename, 'wb') as myfile:
            wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
            for _, writeItem in enumerate(symList):
                itemList = writeItem.getList()
                wr.writerow(itemList)
        return

    def saveResultsFiles(self):
        genSavePath = (self.savePath is None)
        if genSavePath:
            self.savePath = self.getTempPathName(genSavePath)

        genSaveFile = (self.saveFilePrefix is None)
        if genSaveFile:
            self.saveFilePrefix = self.getTempFileName(genSavePath)

        os.makedirs(self.savePath, exist_ok=True)
        outfileRef = "".join([self.savePath, self.saveFilePrefix, "_ref.cvs"])
        outfileLoc = "".join([self.savePath, self.saveFilePrefix, "_loc.cvs"])

        self.saveContent(filename=outfileRef, symList=self.symbolRefGlobal)
        self.saveContent(filename=outfileLoc, symList=self.symbolLocGlobal)
        return

    def probe(self):
        self.usage()
        self.verifyBinaries()
        self.setContext()
        self.crawl()
        self.saveResultsFiles()
        return


def main():
    SymProbe().probe()
    return


if __name__ == '__main__':
    """Performs execution delta of the process."""
    start_time = datetime.datetime.now()
    main()
    finish_time = datetime.datetime.now()
    print("\nExecution Start Time:", str(start_time))
    print("Execution End Time:  ", str(finish_time))
    print("Total Execution Time:", str(finish_time - start_time))
    quit(0)

## @}
