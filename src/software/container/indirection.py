#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
# @package indirection

##################################
# General Python module imports
##################################
from __future__ import absolute_import, division, print_function, \
    unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import os, re, sys, math, traceback, numbers, collections, copy
import types as _types
import string, time, unittest, ctypes, shutil, errno, logging, unittest  # @todo Explicit Usage
# import platform, telemetry # @todo

from os import listdir  # @todo
from pprint import pprint  # @todo
from optparse import OptionParser
from collections import Mapping, Set, Sequence

# from test_all import db, dbshelve, test_support, verbose, have_threads, get_new_environment_path # @todo
# from commands.telemetryCmd import TelemetryObjectCommands # @todo Explicit Usage

#####
# Compatibility of python 2 and 3.
#####
# Python 2
try:
    import builtins as builtins
    from StringIO import StringIO

# Python 3
except ImportError:
    import builtins, io
    from io import StringIO  # @todo
    from functools import reduce  # @todo

    basestring = str
    unicode = str
    file = io.IOBase

#####
## sample usage: "python PacmanIC.py --bindir .\sample --objdir C:\Users\achamorr\Intel\mono_telemetry-major2-minor0_decode\nand\gen3\projects\objs\arbordaleplus_ca"
#####

##################################
## Global Variables
##################################
usage = "%s --bindir BINFILESDIRECTORY --bin BINFILELOC --objdir PROJECTOBJECTDIRECTORY --outloc OUTPUTDIR" % (
sys.argv[0])


##################################
## Classes for Objects
##################################
class OneAPI(object):
    """
    Class for accessing One API for storage data containers.
    """
    creationTime = None
    protocolIdentification = None
    telemetryVersion = None
    telemetryBinary = None
    sourceContext = None

    def __init__(self, object=None):
        """
        Initalized the parameters based on the object.

        Parameters
        ----------
        object : Tuple, optional
            Contains the object to init the object based on the input (default is None).

        Raises
        ------
        NotImplementedError
             If data is not set or pass parameter.
        """
        self.creationTime = datetime.datetime.utcnow()
        if object is None:
            raise NotImplementedError("The object is not included in the construction")
        else:
            self.nvmeIdentification = object.nvmeIdentification
            self.telemetryVersion = object.telemetryVersion
            self.telemetryVersion = object.telemetryVersion

    class Indirection(object):
        """
        A dictionary which can lookup values by key, and keys by value.
        All values and keys must be hashable, and unique.
        """
        uidObject = None
        forwardDirectionDict = None
        reverseDirectionDict = None

        class Reflect(object):  # buffdict
            """
            Construction of a dynamic list by reflecting the order by swapping the context (reversing).
            A dictionary which can lookup values by key, and keys by value.
            All values and keys must be hashable, and unique.
            """

            def __init__(self, object):
                dict.__init__(self)
                self.reverse = dict((reversed(list(i)) for i in self.items()))

            def __setitem__(self, key, value):
                dict.__setitem__(self, key, value)
                self.reverse[value] = key

        class Lookup(object):  # indirection
            """
            A dictionary which can lookup values by key, and keys by value. The lookup method returns a list of keys with matching values to the value argument.
            """

            def __init__(self, Indirection):
                dict.__init__(self)

            def lookup(self, value):
                return [item[0] for item in self.items() if item[1] == value]

        def __init__(self, object):
            self.uidObject = object
            self.forwardDirectionDict = object.bufdict.name
            self.reverseDirectionDict = self.Reflect(object.bufdict.name)

        def getUID(self):
            return self.forwardDirectionDict.bufdict.uid

        def getVersion(self):
            return (self.forwardDirectionDict.bufdict.majorVersion, self.forwardDirectionDict.bufdict.minorVersion)

        def getName(self):
            return self.forwardDirectionDict.bufdict.name

        def getByteSize(self):
            objectByteSize = 0
            objectDict = self.forwardDirectionDict.bufdict.desc_dict
            for (name, size, signed, default, style, token, desc) in objectDict:
                objectByteSize += size
            return objectByteSize

        def dictionaryForward(self):
            return self.forwardDirectionDict.bufdict.description.desc_dict

        def dictionaryReverse(self):
            return self.reverseDirectionDict.bufdict.description.desc_dict


def main(usage):
    """Performs the auto parsing of data control to generate telemetry definitions within a python c-type for valid structures."""
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

    return


if __name__ == '__main__':
    """Performs execution delta of the process."""
    from datetime import datetime

    p = datetime.now()
    main()
    q = datetime.now()
    print("\nExecution time: " + str(q - p))

## @}
