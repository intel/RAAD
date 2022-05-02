#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
## @package genericObjects
# This python script is used to configure an interface for storage containers.
#  The code uses nested inner classes to not allow mutating of the internal workings and use the one API.

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
## Compatability of python 2 and 3.
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
class ObjectUtility(object):
    """
    Class used for handling data in a standardized manner to ease usage.

    Data Type(s) enumeration:
    c-type variable : Used to declare a variable which holds a value.
        variable_name = [char, int, bool, pointer, string, enumeration, struct, union, etc..]
    list : Lists are used to store multiple items sequentially in one variable. Equivalent of an array in other languages. Lists are mutable.
        list_name2 = [item1, item2]
    list comprehension : List comprehension is used to dynamically generate lists.
        list_name = [var for var in existing_list boolean_expression]
    tuples: Tuples are used to store multiple items sequentially in one variable. Similar to lists, but immutable.
        tuple_name = (item1, item2, item3)
    dictionaries : Used to store key-value pairs.
        dictionary_name = {"key1": value1, "key2": value2}
    sets : Used to store values like an array and ensure there are no duplicates.
        set_name = set([value1, value2])
    """
    __objEntry = None  # Hidden object entry point for any given object.

    def __init__(self, object=None):
        """
        Function Type: Constructor
        Description: Initalizes an object.
        """
        if object is not None:
            objectName = object.__name__
            if objectName is not None:
                self.__objEntry = self.__cloneAtKamino(object)
            else:
                print("No Object value set on construction for:" + str(self.__class__.__name__))
                raise NotImplementedError("The object is not included in the construction")
            print(self)

    def __unicode__(self):
        """
        Function Type: Accessor
        Access the object name, if it exists
        """
        objectName = self.__objEntry.__name__
        if objectName is not None:
            objectName = str(objectName)
        else:
            objectName = "None"
        return objectName

    def __identifyObject(self, object=None):
        """
        Function Type: Internal private accessor
        Uses the internal self object or passed object based if the input parameter is None.
        """
        if (object is None):
            objectVar = self.__objEntry
        else:
            objectVar = object
        return objectVar

    def getObject(self):
        """
        Function Type: Accessor
        Return the internal object.
        """
        return self.__objEntry

    def setObject(self, object=None):
        """
        Function Type: Accessor
        Sets the internal object.
        """
        return self.__init__(object)

    """
    Type Comprehension Methods
    """

    def isBool(self, object=None):
        """
        Function Type: Helper
        Determines if self or the object is an integer.
        """
        objectVar = self.__identifyObject(object)
        return isinstance(objectVar, bool)

    def isInt(self, object=None):
        """
        Function Type: Helper
        Determines if self or the object is an integer.
        """
        objectVar = self.__identifyObject(object)
        return isinstance(objectVar, numbers.Integral)

    def isInteger(self, object=None):
        """
        Function Type: Helper
        Determines if self or the object is an integer.
        """
        objectVar = self.__identifyObject(object)
        return objectVar.isInt()

    def isIntegral(self, object=None):
        """
        Function Type: Helper
        Determines if self or the object is an integer.
        """
        objectVar = self.__identifyObject(object)
        return objectVar.isInt()

    def isNumber(self, object=None):
        """
        Function Type: Helper
        Determines if self or the object is a number.
        """
        objectVar = self.__identifyObject(object)
        return isinstance(objectVar, numbers.Number)

    def isFloat(self, object=None):
        """
        Function Type: Helper
        Determines if self or the object is an floating point variable.
        """
        objectVar = self.__identifyObject(object)
        return isinstance(objectVar, float)

    def isString(self, object=None):
        """
        Function Type: Helper
        Determines if self or the object is a string.
        """
        objectVar = self.__identifyObject(object)
        return isinstance(objectVar, basestring)

    def isDictionary(self, object=None):
        """
        Function Type: Helper
        Determines if self or the object is a dictionary
        """
        objectVar = self.__identifyObject(object)
        return isinstance(objectVar, dict)

    def isType(self, object=None):
        """
        Function Type: Helper
        Determines if self or the object is an type or class.
        """
        objectVar = self.__identifyObject(object)
        return isinstance(objectVar, type) or isinstance(objectVar, _types.ClassType)

    def isList(self, orTuple=True, object=None):
        """
        Function Type: Helper
        Determines if self or the object is an list.
        """
        objectVar = self.__identifyObject(object)
        if orTuple:
            return isinstance(objectVar, (list, tuple))
        return isinstance(objectVar, list)

    def isTuple(self, object=None):
        """
        Function Type: Helper
        Determines if self or the object is an tuple.
        """
        objectVar = self.__identifyObject(object)
        return isinstance(objectVar, tuple)

    def isContainer(self, object=None):
        """
        Function Type: Helper
        True if object is a container object (list,tuple,dict,set), but NOT a string or custom iterable.
        """
        objectVar = self.__identifyObject(object)
        return isinstance(objectVar, collections.Container) and not isinstance(objectVar, basestring)

    def isIterable(self, object=None):
        """
        Function Type: Helper
        True if object is *any* iterable: list, tuple, dict, set, string (!), any object with __iter__ or __getitem__ method.
        """
        objectVar = self.__identifyObject(object)
        return isinstance(objectVar, collections.Iterable)

    def isRegex(self, object=None):
        """
        Function Type: Helper
        Determines if self or the object is an regular expression
        """
        objectVar = self.__identifyObject(object)
        return isinstance(objectVar, re._pattern_type)

    def isArray(self, isStrArray=False, isTuppleArray=True, object=None):
        """
        Function Type: Helper
        Determines if self or the object is an array.
        """
        objectVar = self.__identifyObject(object)

        resultant = hasattr(objectVar, "__len__") and hasattr(objectVar, '__getItem__')

        if resultant and not isStrArray and isinstance(objectVar, (str, collections.abc.ByteString)):
            resultant = False
        if resultant and not isTuppleArray and isinstance(objectVar, tuple):
            resultant = False

        return resultant

    def isFunction(self, funtypes=(
    _types.FunctionType, _types.BuiltinFunctionType, _types.MethodType, _types.BuiltinMethodType,
    getattr(_types, 'UnboundMethodType', _types.MethodType)), object=None):
        """
        Function Type: Helper
        True if object is any kind of a 'syntactic' function: function, method, built-in; but NOT any other callable (object with __call__ method is not a function).
        """
        objectVar = self.__identifyObject(object)
        return isinstance(objectVar, funtypes)

    def isGenerator(self, object=None):
        """
        Function Type: Helper
        Determines if self or the object is a generator, similar to an iterator except with recall of state.
        """
        objectVar = self.__identifyObject(object)
        return isinstance(objectVar,
                          (_types.GeneratorType, _types.MethodType, _types.BuiltinMethodType, _types.UnboundMethodType))

    def isSequence(self, object=None):
        """
        Function Type: Helper
        Determines if self or the object is a sequence class.
        """
        objectVar = self.__identifyObject(object)
        return isinstance(objectVar, (Sequence, Set))

    def isMapping(self, object=None):
        """
        Function Type: Helper
        Determines if self or the object is a mapping class.
        """
        objectVar = self.__identifyObject(object)
        return isinstance(objectVar, Mapping)

    def isMethod(self, object=None):
        """
        Function Type: Helper
        True if xobject is a method, bound, or unbound.
        """
        objectVar = self.__identifyObject(object)
        return isinstance(objectVar, (_types.MethodType, _types.BuiltinMethodType, _types.UnboundMethodType))

    def isBound(self, object=None):
        """
        Function Type: Helper
        True if a given method is bound, i.e., assigned to an instance (with 'self'), not a class method.
        """
        objectVar = self.__identifyObject(object)
        return getattr(objectVar, 'im_self', None) is not None

    def isClass(self, classEvalVal=None):
        """
        Function Type: Helper
        True if classEvalVar is a class and subclass of subClassIn (or self.object), False otherwise.
        """
        classVar = self.__identifyObject(classEvalVal)
        return isinstance(classVar, type)

    def isSubClass(self, classEvalVal=None, isSubClassIn=None):
        """
        Function Type: Helper
        True if classEvalVar is a class and subclass of subClassIn (or self.object), False otherwise.
        """
        classVar = self.__identifyObject(classEvalVal)
        return isinstance(classVar, type) and builtins.issubclass(classVar, isSubClassIn)

    """
    Class based characteristics access methods
    """

    def getClassName(self, classIn=None, hasContent=False, object=None):
        """
        Function Type: Helper
        Determines the fully qualified class name of the object 'object' or class 'classIn'.
        """
        if classIn is None:
            classVar = object.__name__
        elif object is None:
            classVar = self.object.__name__
        else:
            classVar = classIn

        if hasContent:
            return classVar.__module__ + "." + classVar.__name__
        return classVar.__name__

    def __determineBaseClasses(self, includeSelf=False, classIn=None):
        """
        Function Type: Internal private Helper
        Recursive Terminating function for object base class list.
        """
        classVar = self.__identifyObject(classIn)
        if classVar is object:
            return []
        listOfClasses = []
        for base in classVar.__bases__:
            listOfClasses.extend(self.__determineBaseClasses(base, True))

        if includeSelf:
            listOfClasses.append(classVar)
        return listOfClasses

    def determineBaseClasses(self, includeSelf=False, object=None):
        """
        Function Type: Internal Helper
        The function finds all of the base classes through traversing recursively.
        """
        objectVar = self.__identifyObject(object)
        if includeSelf:
            listOfClasses = self.__determineBaseClasses(objectVar, True)
        else:
            listOfClasses = self.__determineBaseClasses(objectVar, False)

        return listOfClasses

    def determineTypes(self, object=None):
        """
        Function Type: Helper
        The function finds all types of the base classes through traversing recursively.
        """
        objectVar = self.__identifyObject(object)
        typesDetermined = type(objectVar)
        return [typesDetermined] + self.determineBaseClasses(typesDetermined)

    def __determineSubClass(self, includeSelf=False, classIn=None):
        """
        Function Type: Internal Helper
        Recursive Terminating function for object base class list.
        """
        classVar = self.__identifyObject(classIn)
        listofSubClasses = []
        for child in classVar.__subclasses():
            listofSubClasses.extend(self.__determineSubclasses(child, True))
        if includeSelf:
            listofSubClasses.append(classVar)
        return listofSubClasses

    def determineSubClass(self, includeSelf=False, object=None):
        """
        Function Type: Internal Helper
        The function finds all of the base classes through traversing recursively.
        """
        objectVar = self.__identifyObject(object)
        if includeSelf:
            listOfClasses = self.__determineSubClass(objectVar, True)
        else:
            listOfClasses = self.__determineSubClass(objectVar, False)
        return listOfClasses

    """
    Object Mutator Methods for advanced sequencing.
    """

    def walking(self, path=(), momento=None, object=None):
        """
        Function Type: Accessor
        Yields the objects contained within and the path to reach them. Deserialized data-structure recursive object accessor. The class is useful for finding an instance within a struture.
        """
        objectVar = self.__identifyObject(object)

        if momento is None:
            momento = set()
        iterator = None

        # Python 2/3 compatability
        stringTypes = (str, unicode) if str is bytes else (str, bytes)
        iterateItems = lambda mapping: getattr(mapping, 'iterateItems', mapping.items)()

        if isinstance(objectVar, Mapping):
            iterator = iterateItems
        elif isinstance(objectVar, (Sequence, Set)) and not isinstance(objectVar, stringTypes):
            iterator = enumerate

        if iterator:
            if id(objectVar) not in momento:
                momento.add(id(objectVar))
                for pathComponent, value in iterator(objectVar):
                    for result in self.walking(value, path + (pathComponent,), momento):
                        yield result
                momento.remove(id(objectVar))
        else:
            yield path, objectVar

    def objectFlatten(self, *sequence):
        """
        Function Type: Mutator
        *sequenceIn is a repetition operator on sequenceIn. The star operator allows for a dictionary of key-value pairs and unpack
        @todo Need to have full name-path to reconstruct the original list.
        """
        sequenceIn = self.__identifyObject(sequence)
        resultant = []
        try:
            if len(sequenceIn) == 1:
                sequenceIn = sequenceIn[0]
        except:
            pass

        for seqItem in sequenceIn:
            if hasattr(seqItem, "__iter__"):
                resultant += self.objectFlatten(seqItem)
            else:
                resultant.append(seqItem)
        return resultant

    @staticmethod
    def simpleFlatten(objNotFlat, sep="_"):
        import collections

        obj = collections.OrderedDict()

        def recurse(t, parent_key=""):

            if isinstance(t, list):
                for i in range(len(t)):
                    recurse(t[i], parent_key + sep + str(i) if parent_key else str(i))
            elif isinstance(t, dict):
                for k, v in t.items():
                    recurse(v, parent_key + sep + k if parent_key else k)
            else:
                obj[parent_key] = t

        recurse(t=objNotFlat)

        return obj

    def __cloneAtKamino(self, object=None):
        """
        Function Type: Helper
        Exact deep copy a given object.
        """
        if (object is None):
            return None
        objectVar = object

        classInstance = self.__class__
        resultant = classInstance.__new__(classInstance)
        objectVar[id(self)] = resultant
        cloner = copy.deepcopy

        if self.__shared__:
            def nocopy(key, value):
                return key in self.__shared__ or self.isGenerator(value)
        else:
            def nocopy(key, value):
                return self.isGenerator(value)

        for key, value in self.__getstate__().iteritems():
            setattr(resultant, key, value \
                if nocopy(key, value) \
                else \
                cloner(value, objectVar) \
                    )
        return resultant

    def cloneObjectToSelf(self, object=None):
        """
        Function Type: Helper
        Performs an exact deep copy to self object.
        """
        self.object = self.__cloneAtKamino(object)

    def cloneSelfAndReturnCopy(self):
        """
        Function Type: Helper
        Exact deep copy of self to return.
        """
        return self.__cloneAtKamino(self.object)

    def keepUniqueAtTop(self, overWrite=False, object=None):
        """
        Function Type: Mutator
        Removes duplications of objects and keeps a unique set in order seen from beginning to the end of the set.
        The function only views the item from the top object and for a recursive version. Please use the deepdiff library.
        """
        objectVar = self.__identifyObject(object)
        if not objectVar:
            return []
        seenSequence = set()
        uniqueSequence = [item for item in objectVar if not (item in seenSequence and not seenSequence.deepcopy(item))]
        if overWrite:
            self.object = uniqueSequence
        return uniqueSequence

    def __transformToStr(self, \
                         object=None, \
                         nameJunction="-", \
                         nameTerminate=".", \
                         valIndex="=", \
                         valJunction=",", \
                         valTerminate=":", \
                         typeTerminate=";", \
                         rowterminate="\n", \
                         recursionPrefix="\t", \
                         depthLength=6):

        stringifyObject = ""
        if depthLength <= 0:
            return "ANOMOLY-IN-THE-MATRIX.NEO=(ONE,EON),AGENT_SMITH=(MACHINEPROGRAMMING,VIRUS):MATRIX_VERSION42BILLION_CONSTRUCT;"
        objectVal = self.__identifyObject(object)
        stringRow = ""
        for item in objectVal:
            """
            list_name2 = [item1, item2]
        tuples: Tuples are used to store multiple items sequentially in one variable. Similar to lists, but immutable.
            tuple_name = (item1, item2, item3)
        sets : Used to store values like an array and ensure there are no duplicates.
            set_name = set([value1, value2])
            @todo: FIXME!
            """
            # Name Format    - Name-SubName(s)
            # Value Format   - Index=Value
            # Overall Format - (Name(s)-). (Value(s),): type;
            if self.isBool(item) or self.isInt(item) or self.isNumber(item) or self.isString(item):
                stringRow = (item.__name__ + str(item) + valTerminate + type(item) + typeTerminate)
            elif self.isDict(item) or self.isList(item) or self.isArray(item):
                stringRow = (item.__name__ + nameTerminate)
                strList = ""
                ItemLen = len(item)
                for indexPos, itemValue in enumerate(item):
                    if ItemLen != 0:
                        ItemLen = ItemLen - 1
                        strList = strList + (indexPos + valIndex + itemValue + valJunction)
                    else:
                        strList = strList + (indexPos + valIndex + itemValue)
                stringRow = stringRow + (strList + valTerminate + type(item) + typeTerminate)
            elif self.isTuple(item):
                stringRow = ""
            elif self.isSet(item):
                stringRow = ""
            elif self.isSequence(item):
                stringRow = ""
            elif self.isMapping(item):
                stringRow = ""
            elif self.isSequence(item):
                stringRow = ""
            elif self.isMapping(item):
                stringRow = ""
            elif self.isIterable(item):
                stringRow = ""
            elif self.isRegex(item):
                stringRow = ""
            elif self.isFunction(item):
                stringRow = ""
            elif self.isMethod(item):
                stringRow = ""
            elif self.isClass(item):
                stringRow = recursionPrefix
            else:
                stringRow = (item.__name__ + str(item) + valTerminate + type(item) + typeTerminate)
        stringifyObject = stringifyObject + stringRow + rowterminate
        return stringifyObject

    def objectPrinter(self, object=None):
        """
        Function Type: Accessor
        Yields the objects contained within and the path to reach them. Deserialized data-structure recursive object accessor. The class is useful for finding an instance within a struture.
        """
        path = ()
        momento = set()
        iterator = None
        objectVar = self.__identifyObject(object)
        objectVar = objectVar.keys()

        # Python 2/3 compatability
        stringTypes = (str, unicode) if str is bytes else (str, bytes)
        iterateItems = lambda mapping: getattr(mapping, 'iterateItems', mapping.items)()

        if isinstance(objectVar, Mapping):
            iterator = iterateItems
        elif isinstance(objectVar, (Sequence, Set)) and not isinstance(objectVar, stringTypes):
            iterator = enumerate

        if iterator:
            if id(objectVar) not in momento:
                momento.add(id(objectVar))
                for pathComponent, value in iterator(objectVar):
                    for result in self.walking(value, path + (pathComponent,), momento):
                        yield result
                momento.remove(id(objectVar))
        else:
            yield path, objectVar
        return

    """
    Simple method reversal of operations. Does not take into account branch conditions
    """

    def __reverseFunctionExecution(self, reverseName, forwardName):
        """
        Function Type: Mutator
        Interprets a function by constructing a string block of  the execution in reverse. The following does not reverse all if else block branches.
        """
        import inspect
        src = inspect.getsource(forwardName)
        srcLines = src.split("\n")
        srcLines = srcLines[1:]  # Remove the forward function content definition
        srcLines = reverseName  # Reverse the operations

        # Function Definition reversed
        reverseFunction = "def " + reverseName + "():\n"
        for line in srcLines:
            if line.strip() != "":
                reverseFunction = line + "\n"
        return reverseFunction

    def reverseExecuteOfAFunction(self, reverseName, forwardName):
        """
        Function Type: Mutator
        Interprets a function by constructing a string block of  the execution in reverse. The following does not reverse all if else block branches.
        """
        # Create a string array of the reverse execution.
        reversedCode = self.__reverseFunctionExecution(reverseName, forwardName)

        # Execute the string block as python
        exec(reversedCode)

        # Execute function in reverse
        reverseName()

    @staticmethod
    def dictSearch(data, path=None, default=None, checknone=False, ignorecase=False, pathsep=".", search=None,
                   pretty=False):
        """
        Get a value or a list of values from a dictionary key using a path
        Args:
            data (dict): Input dictionary to be searched in.
            path (str, optional): Dictionary key search path (pathsep separated).
                Defaults to None.
            default (Any, optional): Default value to return if the key is not found.
                Defaults to None.
            checknone (bool, optional): If set, an exception is thrown if the value
                is None. Defaults to False.
            ignorecase (bool, optional): If set, upper/lower-case keys are treated
                the same. Defaults to False.
            pathsep (str, optional): Path separator for path parameter. Defaults to ".".
            search (Any, optional): Search for specific keys and output a list of values.
                Defaults to None.
            pretty (bool, optional): Pretty prints the result. Defaults to False.
        Raises:
            ValueError: Raises if checknone is set.
        Returns:
            Any: Returns one value or a list of values for the specified key.
        Examples:
            > dictSearch(data, "employees.John Doe.first_name")
            parse key index and fallback on default value if None,
        """
        import json
        def __format(data, pretty):
            """ formats output if pretty=True """
            if pretty:
                return json.dumps(data, indent=4, sort_keys=True)
            else:
                return data

        if search is None and (path is None or path == ''):
            return __format(data, pretty)

        try:
            if path:
                for key in path.split(pathsep):
                    if isinstance(data, (list, tuple)):
                        val = data[int(key)]
                    else:
                        if ignorecase:
                            for datakey in data.keys():
                                if datakey.lower() == key.lower():
                                    key = datakey
                                    break
                        if key in data:
                            val = data[key]
                        else:
                            val = None
                            break
                    data = val

            if search:
                search_ret = []
                if isinstance(data, (list, tuple)):
                    for d in data:
                        for key in d.keys():
                            if key == search:
                                try:
                                    search_ret.append(d[key])
                                except (KeyError, ValueError, IndexError, TypeError, AttributeError):
                                    pass
                else:
                    for key in data.keys():
                        if key == search:
                            try:
                                search_ret.append(data[key])
                            except (KeyError, ValueError, IndexError, TypeError, AttributeError):
                                pass
                if search_ret:
                    val = search_ret
                else:
                    val = default
        except (KeyError, ValueError, IndexError, TypeError, AttributeError):
            val = default

        if checknone:
            if val is None or val == default:
                raise ValueError('value not found for search path: "%s"' % path)

        if val is None or val == '':
            return default
        else:
            return __format(val, pretty)

    class RegressionUnitTestsCases:
        """
        Self regression testing class.
        """

        def assertWalking(self, objectToWalk, *expectedResults):
            """
            Function Type: Helper
            Testing of the object walker function.
            """
            return self.assertEqual(tuple(sorted(expectedResults)), tuple(sorted(self.walking(objectToWalk))))

        def testNilContainers(self):
            """
            Test Case
            """
            self.assertWalking({})
            self.assertWalking([])

        def testSingletonObjects(self):
            """
            Test Case
            """
            for obj in (None, 42, True, "Terminator"):
                self.assertWalking(obj, ((), obj))

        def testOrdinaryContainers(self):
            """
            Test Case
            """
            self.assertWalking([1, True, "Terminator"], ((0,), 1), ((1,), True), ((2,), "Terminator"))
            self.assertWalking({None: 'hips', 'bottom': 'legs', 'flesh': 1}, ((None,), 'hips'), (('parts',), 1),
                               (('bottom',), 'legs'))

            # The sets are unordered, thus we dont need to exercise the path, and only that no object is missing.
            self.assertEqual(set(obj for path, obj in self.walking(set((1, 2, 3)))), set((1, 2, 3)))

        def testNestedContainers(self):
            """
            Test Case
            """
            self.assertWalking([1, [2, [3, 4]]], ((0,), 1), ((1, 0), 2), ((1, 1, 0), 3), ((1, 1, 1), 4))
            self.assertWalking({1: {2: {3: 'parts'}}}, ((1, 2, 3), 'parts'))

        def testRecursiveContainers(self):
            """
            Test Case
            """
            recursiveSet = [1, 2]
            recursiveSet.append(recursiveSet)
            recursiveSet.append(3)
            self.assertWalking(recursiveSet, ((0,), 1), ((1,), 2), ((3,), 3))

        def setUp(self):
            """
            Function Type: Helper
            """
            self.filename = self.__class__.__name__ + '.db'
            # self.homeDir = get_new_environment_path()
            # self.env = db.DBEnv()
            # self.env.open(self.homeDir, db.DB_CREATE | db.DB_INIT_MPOOL)

        def tearDown(self):
            """
            Function Type: Helper
            """
            self.env.close()
            self.env = None
            # test_support.rmtree(self.homeDir)

        def run(self):
            """
            Function Type: Method
            Run all test cases.
            """
            tests = [self.testNilContainers, self.testSingletonObjects, \
                     self.testOrdinaryContainers, self.testNestedContainers, \
                     self.testRecursiveContainers]
            unittest.TestSuite(map(self, tests))
            self.tearDown
            pass

    def testSuite(self):
        """
        Function Type: Method
        Run all test for the class.
        """
        try:
            (self.RegressionUnitTestsCases).run()
            return True
        except:
            return False
        pass


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
