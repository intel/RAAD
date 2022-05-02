# !/usr/bin/python
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/

""" findClasses.py

This module contains the basic functions for parsing the current repo, and
generating a .rst file with all the structures for the documentation.

Args:
    --debug: boolean flag to display debug messages
    --projectDirectory: relative path to the project directory from where the
    traversal will start
    --projectName: string representation of the directory name for the the
    project directory
    --outfilePath: relative path to the output file to be created (must include
    the name of the output file)

Example:
    Default usage:
        $ python findClasses.py
    Specific usage:
        $ python findClasses.py --debug <bool> --projectDirectory <string>
        --projectName <string> --outfilePath <string>
"""

import glob
import importlib
import inspect
import os
import sys
import fnmatch
import traceback
import ast
import pathlib
import typing
import string

# Used for function typing
PathLike = typing.Union[str, pathlib.Path]


def import_plugins(plugins_package_directory_path, base_class=None, create_instance=True, filter_abstract=True):
    # Usage
    # SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    # print("Script Dir {}".format(SCRIPT_DIR))
    # plugins_directory_path = os.path.join(SCRIPT_DIR, 'src')
    # plugins = import_plugins(plugins_directory_path)
    plugins_package_name = os.path.basename(plugins_package_directory_path)

    # -----------------------------
    # Iterate all python files within that directory
    plugin_file_paths = glob.glob(os.path.join(plugins_package_directory_path, "*.py"))
    for plugin_file_path in plugin_file_paths:
        plugin_file_name = os.path.basename(plugin_file_path)

        module_name = os.path.splitext(plugin_file_name)[0]

        if module_name.startswith("__"):
            continue

        # -----------------------------
        # Import python file

        module = importlib.import_module("." + module_name, package=plugins_package_name)

        # -----------------------------
        # Iterate items inside imported python file

        for item in dir(module):
            value = getattr(module, item)
            if not value:
                continue

            if not inspect.isclass(value):
                continue

            if filter_abstract and inspect.isabstract(value):
                continue

            if base_class is not None:
                if type(value) != type(base_class):
                    continue

            # -----------------------------
            # Instantiate / return type (depends on create_instance)

            yield value() if create_instance else value


def _filter(paths, includeItems, excludeItems):
    """
    filtering function that will produce a list of accepted items based on whether
    or not they matched with the includeItems list

    Args:
        paths: list of paths to traverse
        includeItems: list of names for the items to be included
        excludeItems: list of names for the items to be excluded

    Returns: list of elements within paths that matched with regex in includeItems

    """
    matches = []

    if includeItems is None or excludeItems is None:
        return matches

    for path in paths:
        append = None

        for include in includeItems:
            if os.path.isdir(path):
                append = True
                break

            if fnmatch.fnmatch(path, include):
                append = True
                break

        for exclude in excludeItems:
            if os.path.isdir(path) and path == exclude:
                append = False
                break

            if fnmatch.fnmatch(path, exclude):
                append = False
                break

        if append:
            matches.append(path)

    return matches


def addAll(startPath='../../', importAll=False, debug=True, includeList=None, excludeList=None):
    """
    function for traversing the root directory looking for files that match the items
    in the includeList

    Args:
        startPath: the relative path to the root directory where the traversal will start
        importAll: flag to include all found files in the sys path
        debug: flag to display debug messages
        includeList: list of files or regex for items to be included
        excludeList: list of files or regex for items to be excluded

    Returns: list of file paths to all the files matched within the root directory

    """
    searchRootPathDir = os.path.abspath(startPath)
    print("Search Root Path Directory {}".format(searchRootPathDir))
    sourceList = []
    for root, dirs, files in os.walk(searchRootPathDir):
        files[:] = _filter(map(lambda f: os.path.join(root, f), files), includeList, excludeList)
        dirs[:] = _filter(map(lambda d: os.path.join(root, d), dirs), includeList, excludeList)
        filesReduced = files
        for filename in filesReduced:
            filename = os.path.join(root, filename)
            if debug is True:
                print("Added Path Directory {}".format(filename))
            sourceList.append(filename)
    if importAll is True:
        for sourceFile in sourceList:
            sys.path.insert(0, os.path.abspath(sourceFile))
    return sourceList


def showFunctionInfo(functionNode=None, debug=False):
    if functionNode is None:
        return
    try:
        for fNode in functionNode:
            if debug is True:
                print(f"Function name:{fNode.name}")
                print("Args:")
            for arg in fNode.args.args:
                if debug is True:
                    import pdb
                    pdb.set_trace()
                    print(f"\tParameter name:{arg.arg}")
    except Exception as errorInFindClasses:
        traceback.print_tb(errorInFindClasses.__traceback__)
        return None
    return


def showClassInfo(classesNode=None, debug=False):
    if classesNode is None:
        return
    try:
        for class_ in classesNode:
            if debug is True:
                print(f"Class name: {class_.name}")
            methods = [n for n in class_.body if isinstance(n, ast.FunctionDef)]
            showFunctionInfo(functionNode=methods, debug=debug)
    except Exception as errorInFindClasses:
        traceback.print_tb(errorInFindClasses.__traceback__)
        return None
    return


def findClasses(source=None, fileFound=None, debug=False):
    """
    function for obtaining the names for the classes contained within a file

    Args:
        source: file content to be parsed by AST in order to identify the classes
        contained inside
        fileFound: file of the content for AST parse
        debug: allow for printing as executing

    Returns: list of all the names of the classes contained in the file source

    """
    if source is None:
        return None
    try:
        if fileFound is None:
            fileFound = '<unknown>'

        source = ''.join(x for x in source if x in string.printable)
        astAllnodes = ast.parse(source=source, filename=fileFound, type_comments=False)
        functions = [n for n in astAllnodes.body if isinstance(n, ast.FunctionDef)]
        classNodes = [n for n in astAllnodes.body if isinstance(n, ast.ClassDef)]
        classes = [node.name for node in ast.walk(astAllnodes) if isinstance(node, ast.ClassDef)]
        existFunctions = len(functions) != 0
        if existFunctions:
            showFunctionInfo(functionNode=functions, debug=debug)
        existClasses = len(classNodes) != 0
        if existClasses:
            showClassInfo(classesNode=classNodes, debug=debug)
        # ['test', 'test2', 'inner_class']
        existClass = len(classes) != 0
        if existClass:
            return classes
        else:
            return None
    except Exception as errorInFindClasses:
        traceback.print_tb(errorInFindClasses.__traceback__)
        return None


def checkDebugOption(debugOptions):
    """
    function to set the default value for debugOptions and turn it from
    a string into a boolean value

    Args:
        debugOptions: string representation of boolean value for debug flag

    Returns: boolean value for debug flag

    """
    if debugOptions is None:
        return False
    elif debugOptions == "True":
        return True
    else:
        return False


def checkOutfileOption(outfileOption):
    """
    function to set the default value for outfileOptions

    Args:
        outfileOption: relative path to output location or None

    Returns: relative path to output location

    """
    if outfileOption is None:
        return './index.rst'
    else:
        return outfileOption


def checkProjectDirOption(projectDirOption):
    """
        function to set the default value for projectDirOption

        Args:
            projectDirOption: relative path to the location of the project
            directory, or None

        Returns: relative path to the location of the project directory

        """
    if projectDirOption is None:
        return '../../'
    else:
        return projectDirOption


def checkProjectNameOption(projectNameOption):
    """
        function to set the default value for projectNameOption

        Args:
            projectNameOption: name for the project directory (root directory)

        Returns: name for the project directory

        """
    if projectNameOption is None:
        return 'RAAD'
    else:
        return projectNameOption


def windowsPathParser(strPath):
    """
    function for turning the absolute path for a file from normal notation to
    dot separated notation on Windows OS

    Args:
        strPath: string representation of the absolute path for a file

    Returns: parsed dot notation of the absolute path for a file

    """
    nuFileDD = ''
    count = 0
    for idxChar, itemChar in enumerate(strPath):
        if itemChar == ':':
            nuFileDD = ''
        elif itemChar == '\\' and count == 0:
            count = 1
        elif itemChar == '\\' and count == 1:
            nuFileDD = nuFileDD + '.'
            count = 0
        elif itemChar == '.':
            break
        else:
            nuFileDD = nuFileDD + itemChar
    return nuFileDD


def replace_ext(path: PathLike, new_ext: str = "") -> pathlib.Path:
    """
    function for turning the absolute path of a file and remove extension

    Args:
        path: string representation of the absolute path for a file
        new_ext: extension to be added. I.E. .py

    Returns: replaced extension or no extension to input

    """
    extensions = "".join(pathlib.Path(path).suffixes)
    newPath = pathlib.Path(str(path).replace(extensions, new_ext))
    return newPath


def linuxPathParser(strPath):
    """
    function for turning the absolute path for a file from normal notation to
    dot separated notation on Linux

    Args:
        strPath: string representation of the absolute path for a file

    Returns: parsed dot notation of the absolute path for a file

    """
    strPathClean = replace_ext(strPath)
    nuFileDD = ''
    strPathClean = str(strPathClean)
    for idxChar, itemChar in enumerate(strPathClean):
        isValidChar = itemChar.isalpha()
        isDigitChar = itemChar.isdigit()
        isPathChar = itemChar == '/'
        invalidChars = r'[]\;,><&*:%=+@!#^()|?^'
        isInvalidChar = itemChar in invalidChars
        if isValidChar or isDigitChar:
            nuFileDD = nuFileDD + itemChar
        elif isPathChar:
            nuFileDD = nuFileDD + '.'
        elif isInvalidChar:
            nuFileDD = nuFileDD + ''
        else:
            nuFileDD = nuFileDD + itemChar

    return nuFileDD


def createBlockDirectoryRegex(pathSet: list[str] = None):
    """
    function taking a path then creating a regex for exclusion

    Args:
        pathSet: list of string representation of the path for a file

    Returns: regex token
    """
    if pathSet is None:
        return None
    blockDirectory = os.path.join(*pathSet)
    blockDirectoryPath = os.path.abspath(blockDirectory)
    blockDirectoryPathRegx = os.path.join(blockDirectoryPath, '*')
    return blockDirectoryPathRegx


def main():
    """
    main function to be called when the script is directly executed from the
    command line
    """
    import optparse
    parser = optparse.OptionParser()
    parser.add_option("--outfilePath", dest='outfilePath', metavar='<OUTFILEPATH>', default=None,
                      help='path for the creation of outfile containing structures for the found classes')
    parser.add_option("--projectDirectory", dest='projectDirectory', metavar='<PROJECTDIR>', default=None,
                      help='Project directory path used as the initial point for traversal')
    parser.add_option("--projectName", dest='projectName', metavar='<PROJECTNAME>', default=None,
                      help='Project directory name used as the identifier for the root node')
    parser.add_option("--debug", dest='debug', metavar='<DEBUG>', default=None,
                      help='Enter mode for developer debugging printing more information.')

    (options, args) = parser.parse_args()

    try:
        thisFile = str(os.path.basename(__file__))
        blockList = list()
        blockList.append(createBlockDirectoryRegex(pathSet=['..', '..', 'src', '_dev_tools']))
        blockList.append(createBlockDirectoryRegex(pathSet=['..', '..', 'src', 'mpr', 'controlflag', 'src', 'tree-sitter', 'tree-sitter']))
        blockList.append(createBlockDirectoryRegex(pathSet=['..', '..', 'src', 'mpr', 'autoperf', 'autoperf', 'test']))
        blockList.append(createBlockDirectoryRegex(pathSet=['..', '..', 'src', 'software', 'decode']))
        blockList.append(createBlockDirectoryRegex(pathSet=['..', '..', 'src', 'software', 'twidl']))
        blockList.append(createBlockDirectoryRegex(pathSet=['..', '..', 'src', 'software', 'probeTrace']))

        excludesList = [".", "_", "__", "*external*", "__pycache__", "__init__.py", '*__.py', 'bufdict.py', f"*{thisFile}", *blockList]

        includesList = ['*.py']

        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        debug = checkDebugOption(options.debug)
        outfilePath = checkOutfileOption(options.outfilePath)
        projectDir = checkProjectDirOption(options.projectDirectory)
        # projectName = checkProjectNameOption(options.projectName)

        classListFoundForRun = list()
        allFileList = list()
        startingRootPathDir = os.path.abspath(projectDir)
        print("Starting Root Path Directory {}".format(startingRootPathDir))
        foundList = addAll(startPath=projectDir, importAll=False, debug=debug,
                           includeList=includesList, excludeList=excludesList)
        for foundFile in foundList:
            # Open a file: file
            file = open(foundFile, mode='r', encoding='utf8', errors='ignore')
            # read all lines at once
            all_of_it = file.read()
            # close the file
            file.close()
            if debug is True:
                print("File {0}.\n".format(foundFile))
            foundClassList = findClasses(source=all_of_it, fileFound=foundFile, debug=debug)
            if debug is True:
                print("Class Set in {0}.\n{1}".format(foundFile, foundClassList))
            if foundClassList is not None and len(foundClassList) > 0:
                fileObj = list()
                classObj = list()
                fileObj.append(foundFile)
                for cItemFound in foundClassList:
                    classObj.append(cItemFound)
                classListFoundForRun.append((fileObj, classObj))
                allFileList.extend(fileObj)

        if debug is True:
            for indexObj, (_, _) in enumerate(classListFoundForRun):
                print("Index {0}".format(indexObj))
                print("File {0}".format(classListFoundForRun[indexObj][0]))
                print("Classes {0}".format(classListFoundForRun[indexObj][1]))

        fileName = os.path.abspath(outfilePath)
        print("Filename out {}".format(fileName))
        file = open(fileName, "w")
        file.write("Welcome to Rapid Automated-Analysis for Developers (RAAD)'s documentation!\n")
        file.write("===============================================================================")
        file.write("\n")
        file.write(".. toctree::\n")
        file.write("   :maxdepth: 2\n")
        file.write("   :caption: Contents:\n")
        file.write("\n")
        # When more docummenation is added then add the filename here to perserve order
        file.write("   Introduction\n")
        file.write("   Server\n")
        file.write("   Anaconda\n")
        file.write("   NVMe_Telemetry\n")
        file.write("   NVMe-CLI\n")
        file.write("   NVMe-CLI_Debug\n")
        file.write("   RAAD\n")
        file.write("   Background_Time_Series\n")
        file.write("   API_Direction\n")
        file.write("   RAAD_Getting_Started\n")
        file.write("   RAAD_Workloads\n")
        file.write("   Fault_Analysis\n")
        file.write("   Data_Control\n")
        file.write("   Accelerating_Code_Velocity\n")
        file.write("   Security_Detection\n")
        file.write("   Mentoring\n")
        file.write("\n")
        file.write("Indices and tables\n")
        file.write("=====================\n")
        file.write("\n")
        file.write("* :ref:`genindex`\n")
        file.write("* :ref:`modindex`\n")
        file.write("* :ref:`search`\n")
        file.write("\n")
        # Repeat start here...
        print("Starting Repeat")
        for indexObj, fileDD in enumerate(allFileList):
            print(fileDD)
            strStripper = ''
            fileDD_Len = len(fileDD)
            if fileDD_Len >= 1:
                for fItem in fileDD:
                    strStripper = f"{strStripper}{str(fItem)}"

            relPath = os.path.relpath(strStripper, startingRootPathDir)
            strStripper = relPath

            if (sys.platform == 'win32' or os.name == 'os2'):
                candidateDox = windowsPathParser(strStripper)
            else:
                candidateDox = linuxPathParser(strStripper)

            if debug:
                print("CandidateDox Before {}".format(candidateDox))
            # rootPattern = projectName + '.'
            # newCandidate = candidateDox.partition(rootPattern)[2]
            # candidateDox = newCandidate
            if debug:
                print("CandidateDox  After {}".format(candidateDox))
            file.write(".. automodule:: {}\n".format(candidateDox))
            file.write("    :members:\n")
            file.write("    :undoc-members:\n")
            file.write("    :show-inheritance:\n")
            file.write("    :inherited-members:\n")
            file.write("\n")
            file.write("\n")
        # Repeat end...
        file.close()
    except Exception as e:
        traceback.print_tb(e.__traceback__)


if __name__ == '__main__':
    """Performs execution delta of the process."""
    from datetime import datetime

    pStart = datetime.now()
    main()
    qStop = datetime.now()
    print("Execution time: " + str(qStop - pStart))
