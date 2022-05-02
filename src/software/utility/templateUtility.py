#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
"""
Brief:
    Utility function to template all python files.

Description:
    Class ibrary is designed to be used as a tracking template file to ease use across all files and ensure tracking.

    Layout __init__.py
        <Text Template>
        <import items>
        myNameIdentify = templateUtility("C:/Path", "__init__.py", 1, 0, "04-09-2020 11:58:00", "")
        myNameIdentify.uInit(self)
        <Other Code>

    Layout myName.py
        <Text Template>
        <import items>
        myNameIdentify = templateUtility("C:/Path", "myName.py", 1, 0, "04-09-2020 11:58:00", "")
        myNameIdentify.uPy2toPy3Convert()
        myNameIdentify.uImportDirectoryTree(True,False)
        myNameIdentify.uEXE()
        <Other Code>
        myNameIdentify.uMain()
"""
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import datetime, ctypes, sys, os

class templateUtility(object):
    """templateUtility are documented in the same way as classes.

    The __init__ method may be documented in either the class level
    docstring, or as a docstring on the __init__ method itself.

    Either form is acceptable, but the two should not be mixed. Choose one
    convention to document the __init__ method and be consistent with it.

    Note:
        Do not include the `self` parameter in the ``Args`` section.

    Args:
        msg (str): Human readable string describing the exception.
        code (:obj:`int`, optional): Error code.

    Attributes:
        msg (str): Human readable string describing the exception.
        code (int): Exception error code.

    """
    maxPath = 256
    maxTime = 32
    maxName = 16

    _pack_ = 1
    _fields_ = [
		("absPath" , ctypes.c_wchar * maxPath, ctypes.sizeof(ctypes.c_char * maxPath)), # Path to the file.
        ("filename", ctypes.c_uint32         , ctypes.sizeof(ctypes.c_uint32        )), # Identification file.
        ("major"   , ctypes.c_uint16         , ctypes.sizeof(ctypes.c_uint16        )), # Major version number of the file.
        ("minor"   , ctypes.c_uint16         , ctypes.sizeof(ctypes.c_uint16        )), # Minor version number of the file.
        ("time"    , ctypes.c_wchar * maxTime, ctypes.sizeof(ctypes.c_char * maxTime)), # Time of execution or creation.
        ("user"    , ctypes.c_wchar * maxName, ctypes.sizeof(ctypes.c_char * maxName)), # Name of the creator.
		]

    def __init__(self, absPath=None, filename="unknown.py", major=0, minor=0, time=datetime.datetime.now(), user=""):
        """
        Initalizes an object.

        The parameters have default values to ensure all fields have a setting. The setting of variable  by the user will allow for customization on tracking of meta data.

        Args:
            absPath: A positional argument.
            filename: Another positional argument.
            major: The major field is used for detection of structural ordering.
            minor: The minor field is used for detection of extensions.
            time: Creation time.
            user: The organization user information.

        Returns:
            None.

        Raises:
            None

        Examples:
            #>>> templateUtility(None, "unknown.py", 1, minor=0, datetime.datetime.now(), "")
        """
        __origin__    =  'templateUtility.py :Joseph Tarango :04-09-2020 11:58:00'
        self.absPath  = absPath
        self.filename = filename
        self.major    = major
        self.minor    = minor
        self.time     = time
        self.user     = user

    def __getattribute__(self, attr):
        """
        Initalizes an object.

        The parameters have default values to ensure all fields have a setting. The setting of variable  by the user will allow for customization on tracking of meta data.

        Args:
            attr:   A positional argument.

        Returns:
            Object's decoded key value.

        Raises:
            BaseException

        Examples:
            #>>> templateUtility(None, "unknown.py", 1, minor=0, datetime.datetime.now(), "")
        """
        try:
            return object.__getattribute__(self, attr)
        except BaseException as error:
            print('An exception occurred: {}'.format(error))
            return None
        except:
            return None

    def __setattr__(self, attr):
        try:
            return object.__get__(self, attr)
        except BaseException as error:
            print('An exception occurred: {}'.format(error))
            return None
        except:
            return None

    def printer(self):
        try:
            retstr = ""
            for (itemId, itemSize) in self._fields_:
                retstr += "{0}: {1}\n".format(itemId, getattr(self, itemId))
                return retstr
        except BaseException as error:
            print('An exception occurred: {}'.format(error))
            return None
        except:
            return None

    def uEXE(self):
        import os, re
        ##### .exe extension patch for the compiled version of this script
        if not re.search('\.PY$|\.PYC$|\.EXE$', os.path.split(sys.argv[0])[1].upper()):
            sys.argv[0] = os.path.join( os.path.split(sys.argv[0])[0] , os.path.split(sys.argv[0])[1]+'.exe' )
        return

    def uInit(self):
        # Used for __init__.py file
        import os, sys

        os.sys.path.insert(1,'..')
        # We want to include the following folders in the system path
        root_folder = os.path.abspath('../../')
        os_folder = os.path.join(root_folder, ("win" if 'nt' == os.name else 'linux'))
        if len(os.sys.path) > 2 and os.sys.path[2] == root_folder:
            del os.sys.path[1]
        else:
            os.sys.path[1] = root_folder
        # Add os specific folder
        if 2 >= len(os.sys.path) or os.sys.path[2] != os_folder:
            os.sys.path.insert(2,os_folder)
        del (root_folder,os_folder)
        return

    def uImportDirectoryTree(self, doIt=True, debug=False):
        # Python Assistance for adding top absolute path.
        # Better walking method for Firmware paths
        # Chuck Norris can simply walk into Mordor.
        # Root Node
        directoryTreeRootNode = os.path.dirname(__file__) or '.'
        if debug is True: print ('Directory Root Node:', directoryTreeRootNode)
        # Walk Entire local tree and save contents
        directoryTree = []
        pyfileTree = []
        for root, dirs, files in os.walk(directoryTreeRootNode):
            try:
                for dir in dirs:
                    dirLocation = os.path.abspath( os.path.join(root, dir) )
                    directoryTree.append(dirLocation)
                    if debug is True: print('Directory Node:', dirLocation)
                for file in files:
                    if file.endswith(".py"):
                        pyFileLocation = os.path.abspath( os.path.join(root, file) )
                        pyfileTree.append(pyFileLocation)
                        if debug is True: print('Python File Root Node:', pyFileLocation)
                    else:
                        otherFileLocation = os.path.abspath( os.path.join(root, file) )
                        if debug is True: print('Other File Node:', otherFileLocation)
            except:
                pass
        # Cleanup unused variables in the case of global conflict
        dirLocation = None
        pyFileLocation = None
        otherFileLocation = None
        # Helper to import file tree
        try:
            if debug == True:
                print("Before", sys.path)
            if doIt == True:
                for loc in directoryTree:
                    if os.path.exists(loc):
                        for sysLoc in sys.path:
                            if loc in (sysLoc, sysLoc + os.sep):
                                doNotAdd = True
                            else:
                                doNotAdd = False
                            if doNotAdd == False:
                                sys.path.append(loc)
                            if debug is True:
                                print("After", sys.path)
                            doNotAdd = None
                    loc = None
                    sysLoc = None
        except:
            pass
        return

    def uMain(self):
    ######## Main function #######
        if __name__ == '__main__':
            import datetime
            from datetime import datetime
            p = datetime.now()
            print("Entered uMain()")
            q = datetime.now()
            print("\nExecution time: "+str(q-p))
        return
