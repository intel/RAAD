#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
# @package gatherMeta
from __future__ import annotations
import optparse, datetime, traceback, os, json, tempfile, random, sys, pprint, os.path, shutil, pathlib, fnmatch, hashlib, difflib, time, copy
from src.software.debug import whoami


def checkPythonVersion(expect_major=3, expect_minor=9):
    """ Checking Python version.
        To upgrade do the following with Anaconda:
            conda update conda
            conda install python=3.9
            conda install anaconda-client
            conda update anaconda
            conda install -c anaconda python
    Args:
        expect_major: python major value.
        expect_minor: python minor value.
    Returns: bool if version matches candidates.
    """
    current_version = str(sys.version_info[0]) + "." + str(sys.version_info[1]) + "." + str(sys.version_info[2])
    print("Python version is " + current_version)
    if sys.version_info[:2] == (expect_major, expect_minor):
        matchBool = True
    elif sys.version_info[:2] != (expect_major, expect_minor):
        matchBool = False
    else:
        print("Current version is different: Python " + current_version)
        matchBool = False
    return matchBool


def tryFolder(path=None, walkUpLimit=4):
    """
    Helper function to walk up a file path to the destination folder.
    Args:
        path: directory name
        walkUpLimit: levels allowed to walk up in directory chain

    Returns: Full path of the directory
    """
    if path is None:
        return
    try:
        pathExists = False
        fullPath = None
        pathWalkUp = path
        walkCount = 0
        while ((pathExists is False) and (walkCount < walkUpLimit)):
            fullPath = os.path.abspath(os.path.join(os.getcwd(), pathWalkUp))
            pathExists = os.path.exists(fullPath)
            pathWalkUp = f"../{pathWalkUp}"
            walkCount += 1
        if pathExists is False:
            return None
    except:
        fullPath = None
        pass
    return fullPath


def tryFile(path=None, fileName=None, walkUpLimit=4):
    """
    Helper function to walk up a file path to the destination folder.
    Args:
        path: directory to start with.
        fileName: file to look for in directory walk up path.
        walkUpLimit: levels allowed to walk up in directory chain

    Returns: Full path of the directory
    """
    if fileName is None:
        return
    faultFound = fileName[0] == '/'
    if faultFound:
        tokenFileName = fileName[0:]
        # assert not faultFound, f"Error in file path. Cannot have forwardslash as first character. For Example, '/path/file' should be 'path/file'.{os.linesep} {fileName[0]}"
    else:
        tokenFileName = fileName
    try:
        if path is None:
            startPath = os.getcwd()
        else:
            startPath = path
        fileExists = False
        fullPath = None
        pathWalkUp = ''
        walkCount = 0
        while ((fileExists is False) and (walkCount < walkUpLimit)):
            joinedPath = os.path.join(startPath, pathWalkUp, tokenFileName)
            fullPath = os.path.abspath(joinedPath)
            fileExists = os.path.isfile(fullPath)
            pathWalkUp = f'../{pathWalkUp}'
            walkCount += 1
        if fileExists is False:
            return None
    except BaseException as errorContext:
        pprint.pprint(whoami())
        print(errorContext)
        fullPath = None
        pass
    return fullPath


def getPathToRootCount(selectPath: str = None):
    if selectPath is None or not os.path.exists(selectPath):
        cPath = os.path.join(os.path.dirname(__file__))
    else:
        cPath = selectPath
    cCount = 0
    while (len(cPath) > 1):
        cPath = os.path.split(cPath)[0]
        cCount += 1
    return cCount


def tryFolderDetect(cPath: str = None):
    pathRootCount = getPathToRootCount(selectPath=cPath)
    return tryFolder(path=cPath, walkUpLimit=pathRootCount)


def tryFileDetect(cPath=None, fileName=None):
    pathRootCount = getPathToRootCount(selectPath=cPath)
    return tryFile(path=cPath, fileName=fileName, walkUpLimit=pathRootCount)


def findAll(fileType=None, directoryTreeRootNode=None, debug=False, verbose=False, doIt=False,
            excludeFolderList=None,
            excludeFileList=None):
    """
    Find all files of a type given a directory.
    Args:
        fileType: file extension to look for.
        directoryTreeRootNode: filesystem main root node
        debug: debug mode for adding functionality.
        verbose: Add more information to debug.
        doIt: Add to systempath.
        excludeFolderList: Folders to not look in.
        excludeFileList: files to not look in.

    Returns: fileTypeTree, directoryTree

    """
    if fileType is None:
        fileType = '.fpcore'
    if excludeFileList is None:
        excludeFileList = [".pyc", ".bin", ".svg", ".png", ".mbs", ".rc" ".cache", ".pdb", ".md", ".cs", ".bat"]
    if excludeFolderList is None:
        excludeFolderList = ["__pycache__", "exclude", "data"]
    if directoryTreeRootNode is None or os.path.exists(directoryTreeRootNode) is False:
        directoryTreeRootNode = (os.path.dirname(__file__) or '.')

    if debug is True:
        print('Directory Root Node: {0}'.format(directoryTreeRootNode), flush=True)

    # Walk Entire local tree and save contents
    directoryTree = []
    fileTypeTree = []
    for root, dirs, files in os.walk(directoryTreeRootNode):
        try:
            for dirSelect in dirs:
                if dirSelect not in excludeFolderList:
                    dirLocation = os.path.abspath(os.path.join(root, dirSelect))
                    directoryTree.append(dirLocation)
                    if debug is True and verbose is True:
                        print('Directory Node: {0}'.format(dirLocation), flush=True)
            for file in files:
                if file not in excludeFileList:
                    if file.endswith(fileType):
                        fileLocation = os.path.abspath(os.path.join(root, file))
                        fileTypeTree.append(fileLocation)
                        if debug is True and verbose is True:
                            print('{0} File Node: {1}'.format(fileType, fileLocation), flush=True)
                    else:
                        otherFileLocation = os.path.abspath(os.path.join(root, file))
                        if debug is True and verbose is True:
                            print('Other {0} File Node: {1}'.format(file.endswith(fileType), otherFileLocation), flush=True)
        except BaseException as ErrorContext:
            pprint.pprint(whoami())
            print('Exception {0}'.format(ErrorContext))
            pass

        systemPath = sys.path
        if debug is True and verbose is True:
            print('System path is: ')
            pprint.pprint(systemPath)

        if doIt is True:
            for loc in directoryTree:
                sys.path.append(loc)
    return (fileTypeTree, directoryTree)


def generateString(characterSet=None, fileStringNameSize=None):
    """
    Generate random string set when not set by user.
    Args:
        characterSet: Character set to be used.
        fileStringNameSize: File string name size maxima.

    Returns: Token generated.

    """
    if characterSet is None:
        characterSet = 'abcdef0123456789'

    if fileStringNameSize is None:
        fileStringNameSize = 16

    random.seed(1)
    generatedToken = ''.join(random.choice(characterSet) for _ in range(fileStringNameSize))
    return generatedToken


def getTempPathName(genPath=True):
    if genPath is True:
        generatedPath = tempfile.gettempdir()
    else:
        generatedPath = ""
    return generatedPath


def getDateTimeFileFormatString():
    return '%Y-%m-%d-%H-%M-%S-%f'


def getTempFileName(genFile=True):
    """
    Generate file name.
    Args:
        genFile: proceed flag with generation.

    Returns: file name token string.

    """
    utc_datetime = datetime.datetime.utcnow()
    utc_name = utc_datetime.strftime(getDateTimeFileFormatString())
    if genFile is True:
        pseudo = "".join([utc_name, "_"])
        fileConstruct = tempfile.mkstemp(suffix="", prefix=pseudo, dir=None)
    else:
        fileConstruct = ""
    return fileConstruct


def getTempPathAndFileName(extensionName=None, genPath=True, genFile=True):
    """
    Generate path and file name.
    Args:
        extensionName:Extension name desired.
        genPath: proceed flag with generation.
        genFile: proceed flag with generation.

    Returns: token generation of path and file name token string.

    """
    if extensionName is None:
        extensionName = "_debug.tex"
    outfileRef = "".join([getTempPathName(genPath=genPath), "/", getTempFileName(genFile=genFile), extensionName])
    return outfileRef


def createFilePath(requestPath):
    """
    Generate file path with existance okay.
    Args:
        requestPath: path to request creation.

    Returns: Void

    """
    os.makedirs(requestPath, exist_ok=True)
    return


def getTimeStamp(inTime=None):
    """
    Time stamp update or set for document.
    Args:
        inTime: date time desired to be set.

    Returns: Void

    """
    if inTime is None:
        timeToken = datetime.datetime.utcnow().strftime(getDateTimeFileFormatString())
    elif isinstance(inTime, str):
        timeToken = inTime
    else:
        timeToken = None
    return timeToken


def getFileNameUTCTime():
    """ Get timestamp for a file name
    Returns: string with UTC time
    """
    return getTimeStamp(inTime=None)


def getBytesSize(bytesIn=0, suffix="B"):
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    bytesValue = bytesIn
    if bytesValue is None or 0:
        return int(0)
    elif (isinstance(bytesValue, int) or isinstance(bytesValue, float)) and (int(bytesValue) > 0):
        factor = 1024
        for unit in ["", "K", "M", "G", "T", "P"]:
            if bytesValue < factor:
                return f"{bytesValue:.2f}{unit}{suffix}"
            bytesValue /= factor
        return bytesValue
    return int(0)


def strip_end(stringInput='', suffix=''):
    try:  # Requires python version 3.9+
        partitionedString = stringInput.removesuffix(suffix)
    except:
        if not stringInput.endswith(suffix):
            partitionedString = stringInput
        else:
            partitionedString = stringInput[:len(stringInput) - len(suffix)]
    return partitionedString


def strip_start(stringInput='', prefix=''):
    try:
        partitionedString = stringInput.removeprefix(prefix)
    except:
        if not stringInput.startswith(prefix):
            partitionedString = stringInput
        else:
            partitionedString = stringInput[len(prefix):len(stringInput)]
    return partitionedString


def strip_StartEnd(stringInput='', prefix='', suffix=''):
    cleanedStr = stringInput
    cleanedStr = strip_start(stringInput=cleanedStr, prefix=prefix)
    cleanedStr = strip_end(stringInput=cleanedStr, suffix=suffix)
    return cleanedStr


def cleanFileName(fileName='defaultName'):
    """ Processes a string name into a filename removing invalid tokens.
    Args:
        fileName: string name
    Returns: clean name
    """
    pdfName = fileName
    validchars = "-_.() "
    pdfNameClean = ""
    for charItem in pdfName:
        if str.isalpha(charItem) or str.isdigit(charItem) or (charItem in validchars):
            pdfNameClean += charItem
        else:
            pdfNameClean += "_"
    return pdfNameClean


def readFiles(directory_files):
    """

    Args:
        directory_files:

    Returns:

    """
    for File in directory_files:
        try:
            with open(File, 'r') as infile:
                print(infile.read())
        except:
            pass
    return


def matchFiles(ext, directory_files):
    """Prints files with extension ext
    Args:
        directory_files:
        ext:
    Returns:
    """
    # * matches everything
    # ? matches any single character
    # [seq] matches any character in seq
    # [!seq] matches any character not in seq
    charMatch = '*'
    for File in directory_files:
        if fnmatch.fnmatch(File, charMatch + ext):
            print(File)
    return


def cleanAndRecreatePath(locationOutput: str = None):
    if locationOutput is None:
        return
    # Delete output folder contents and recreate
    try:
        shutil.rmtree(path=locationOutput, ignore_errors=True)
    except OSError as errorOccurance:
        print(f"Error delete: {locationOutput} {errorOccurance.strerror}")
        pass
    try:
        os.makedirs(locationOutput, mode=0o777, exist_ok=True)
    except OSError as errorOccurance:
        print(f"Error create: {locationOutput} {errorOccurance.strerror}")
        pass
    return


def getFileFormats():
    """ Dictionary contains file types as keys and lists of their corresponding file formats
    Returns: Expected classes of files.
    """
    fileTypes = {"Images": ["jpg", "gif", "png", "jpeg", "bmp"],
                 "Audio": ["mp3", "wav", "aiff", "flac", "aac"],
                 "Video": ["m4v", "flv", "mpeg", "mov", "mpg", "mpe", "wmv", "MOV", "mp4"],
                 "Documents": ["doc", "docx", "txt", "ppt", "pptx", "pdf", "rtf", "epub", "xls", "xlsx"],
                 "Exe": ["exe", ".sh"],
                 "Compressed": ["zip", "tar", "7", "rar", "gz", "7z"],
                 "Virtual_Machine_and_iso": ["vmdk", "ova", "iso"]}
    return fileTypes


def organizeDirectory(downloadDirectory=None, fileTypes=None):
    """ Download of directory by file types.
    Args:
        downloadDirectory: Directory to download or copy files to.
        fileTypes: list of filetypes.
    Returns: None
    """
    # The second command line argument is the download directory
    downloadFiles = os.listdir(downloadDirectory)
    makeFoldersByFileType(downloadDirectory, fileTypes)

    for filename in downloadFiles:
        moveFile(filename, downloadDirectory, fileTypes)
    return


def makeFoldersByFileType(downloadDirectory=None, fileTypes=None):
    """Creates folders for different file types
    Args:
        downloadDirectory: Directory to download or copy files to.
        fileTypes: list of filetypes.
    Returns: None
    """
    for fileType in fileTypes.keys():
        directory = downloadDirectory + "\\" + fileType

        if not os.path.exists(directory):
            os.mkdir(directory)
    return


def moveFile(moveFiles=None, downloadDirectory=None, fileGroups=None):
    """ Moves file to its proper folder and delete any duplicates.
    Args:
        moveFiles: List of files to move.
        downloadDirectory: Directory to download or copy files to.
        fileGroups: File types to organize by.
    Returns:
    """
    # The file format is what is after the period in the file name
    if "." in moveFiles:
        temp = moveFiles.split(".")
        fileFormat = temp[-1]
    else:
        return

    for fileGroup in fileGroups.keys():
        fileTypes = fileGroup.keys()
        for fileType in fileTypes:
            if fileFormat in fileTypes:
                srcPath = downloadDirectory + "\\" + moveFiles
                dstPath = downloadDirectory + "\\" + fileType + "\\" + moveFiles

                # If the file doesn't have a duplicate in the new folder, move it
                if not os.path.isfile(dstPath):
                    os.rename(srcPath, dstPath)
                # If the file already exists with that name and has the same md5 sum
                elif os.path.isfile(dstPath) and checkSum(srcPath) == checkSum(dstPath):
                    os.remove(srcPath)
                    print("removed " + srcPath)
            return


def checkSum(fileDir=None, chunkSize=8192):
    """ Get md5 checksum of a file. Chunk size is how much of the file to read at a time.
    Args:
        fileDir: File directories.
        chunkSize: Chunk size of the files.
    Returns: MD5 hash.
    """
    md5 = hashlib.md5()
    f = open(fileDir)
    while True:
        chunk = f.read(chunkSize)
        # If the chunk is empty, reached end of file so stop
        if not chunk:
            break
        md5.update(chunk)
    f.close()
    return md5.hexdigest()


def organize_files_by_extension(ext=None, directory_files=None):
    """ Organize files by the extension.
    Args:
        ext: Extension of the file.
        directory_files: Directory containing the files.
    Returns: None
    """
    for File in directory_files:
        # If the extension of the file matches some text followed by ext...
        if fnmatch.fnmatch(File, '*' + ext):
            print(File)
            # If the file is truly a file...
            if os.path.isfile(File):
                try:
                    # Make a directory with the extension name...
                    os.makedirs(ext)
                except:
                    pass
                # Copy that file to the directory with that extension name
                shutil.copy(File, ext)
    return


def organize_files_by_letter(first_letter=None, directory_files=None):
    """ Organize files by letter.
    Args:
        first_letter: The letter order of the candiadate.
        directory_files: Directory containing the files.
    Returns: None
    """
    for File in directory_files:
        # If the first letter in the file name is equal to the first_letter parameter...
        if str(File[0]).capitalize() == first_letter.capitalize():
            # Print the file (will print as a string)...
            print(File)
            # Print if it is a file or not (This step and the prior is nor really needed)
            print(os.path.isfile(File))
            # If the file is truly a file...
            if os.path.isfile(File):
                try:
                    # Make a directory with the first letter of the file name...
                    os.makedirs(first_letter)
                except:
                    pass
                # Copy that file to the directory with that letter
                shutil.copy(File, first_letter)
    return


def organize_folders_by_letter(first_letter=None, directory_files=None):
    """
    Args:
        first_letter: The letter order of the candiadate.
        directory_files: Directory containing the files.
    Returns:
    """
    for File in directory_files:
        if str(File[0]).capitalize() == first_letter.capitalize():
            # If the file is truly a directory...
            if os.path.isdir(File):
                try:
                    # Move the directory to the directory with the first_letter
                    shutil.move(File, first_letter)
                except:
                    pass
    return


def organize_files_by_keyword(keyword=None, directory_files=None):
    """
    Args:
        keyword: keyword string to use in organizing.
        directory_files: Directory containing the files.
    Returns:
    """
    for File in directory_files:
        # If the name of the file contains a keyword
        if fnmatch.fnmatch(File, '*' + keyword + '*'):
            print(File)
            # If the file is truly a file...
            if os.path.isfile(File):
                try:
                    # Make a directory with the keyword name...
                    os.makedirs(keyword)
                except:
                    pass
                # Copy that file to the directory with that keyword name
                shutil.copy(File, keyword)
    return


def organize_folders_by_keyword(keyword=None, directory_files=None):
    """
    Args:
        keyword: keyword string to use in organizing.
        directory_files: Directory containing the files.
    Returns:
    """
    for File in directory_files:
        # If the name of the file contains a keyword
        if fnmatch.fnmatch(File, '*' + keyword + '*'):
            # If the file is truly a folder/directory...
            if os.path.isdir(File):
                try:
                    # Move the directory to the directory with that keyword name
                    shutil.move(File, keyword)
                except:
                    pass
    return


def organizeby(FILE_FORMATS: list[str] = None):
    """
    List of file formats to organize by.
    Args:
        FILE_FORMATS: list of lists related to file format.
    Returns: None
    """
    if FILE_FORMATS is None:
        FILE_FORMATS = getFileFormats()
    for entry in os.scandir():
        if entry.is_dir():
            continue
        file_path = pathlib.Path(entry)
        file_format = file_path.suffix.lower()
        if file_format in FILE_FORMATS:
            directory_path = pathlib.Path(str(FILE_FORMATS[file_format]))
            directory_path.mkdir(exist_ok=True)
            file_path.rename(directory_path.joinpath(file_path))

        for dirPath in os.scandir():
            try:
                os.rmdir(dirPath)
            except:
                pass
    return


def getProgramName(fileObj):
    """
    Pass a file object then extract the file name.
    Args:
        fileObj: file object

    Returns: file name.

    """
    programName = os.path.basename(fileObj.__file__)
    return programName


def getScriptName(programName):
    """
    Splits a given string suspected to be a file name and returns the prefix with out the file extension.
    Args:
        programName: String file name candidate.

    Returns: prefix of file.
    """
    # Script name
    scriptName = programName.split('.')[0].upper()
    return scriptName


def flattenList(inList=None):
    """ Reduces a list of lists to a single 1-dimension list.
    Args:
        inList: candidate list
    Returns: 1-D list
    """
    flat_list = []
    if inList is not None and inList is not []:
        _ = [flat_list.extend(item) if isinstance(item, list) else flat_list.append(item) for item in inList if item]
    return flat_list


def SimularityScoreCalculate(field_instanceName: str = '', itemOfInterest: str = ''):
    """
    Function to compute the distance simularity score between two candidates.
    Args:
        field_instanceName: Candidate
        itemOfInterest: query

    Returns: Float score [0.0 not similar, 1.0 exact match]

    """
    if (isinstance(field_instanceName, str) is False) or ((isinstance(itemOfInterest, str) is False)):
        simularityScore = 0.0
    else:
        simularityScore = difflib.SequenceMatcher(None, field_instanceName, itemOfInterest).ratio()
    return simularityScore  # [0.0 not similar, 1.0 exact match]


def DictionaryLower(dictionaryForward: dict):
    """
    Function to convert dictionaries with string entries to upper case.
    Args:
        dictionaryForward: Simple 1-dimensional dictionaries.

    Returns: dictionary forward in lower case key/values.

    """
    return dict((str(k).lower(), v.lower()) for k, v in dictionaryForward.items())


def DictionaryUpper(dictionaryForward: dict):
    """
    Function to convert dictionaries with string entries to upper case.
    Args:
        dictionaryForward: Simple 1-dimensional dictionaries.

    Returns: dictionary forward in upper case key/values.

    """
    return dict((str(k).lower(), v.lower()) for k, v in dictionaryForward.items())


def DictionaryReverse(dictionaryForward: dict):
    """
    Function to reverse key with value such that indexes can be used to lookup a key.
    Args:
        dictionaryForward: Simple 1-dimensional dictionaries.

    Returns: dictionaryForward with Key and Values reversed.

    """
    return {v: k for k, v in dictionaryForward.items()}


def DictionarySetReduce(selfDict: dict = None):
    """
    Assistive function to traverse a dictionary recursively then reduce any list to a set removing duplicate entries to comprehend uniqueness.
    Args:
        selfDict: Dictionary composed to fundamental types: dict, list, str, int, float, etc.

    Returns: Requested dictionary with lists reduced to sets then converted back to lists.
    """
    reducedDict = dict()
    try:
        for iKey, iValue in selfDict.items():
            try:
                if isinstance(iValue, dict) and iValue is not dict():
                    rValue = DictionarySetReduce(selfDict=iValue)
                    reducedDict[iKey] = rValue
                elif isinstance(iValue, list):
                    rValue = list(set(iValue))
                    reducedDict[iKey] = rValue
                elif iValue is not None:
                    rValue = iValue
                    reducedDict[iKey] = rValue
            except BaseException as ErrorInnerContext:
                print(f"{whoami()} {ErrorInnerContext}")
                # pass or continue
                continue
    except BaseException as ErrorContext:
        print(f"{whoami()} {ErrorContext}")
    return reducedDict


def DictionaryReduceAnnotator(queryDict: dict):
    """
    Assistive function to traverse a dictionary recursively then reduce any list to a set entries to comprehend uniqueness.
    Each dictionary entry contains the reduced size amount from the reference queryDict.
    Args:
        queryDict: Dictionary composed to fundamental types: dict, list, str, int, float, etc.

    Returns: Requested dictionary annotations of reduced entries and total entries reduced.
    """
    annotateDict = dict()
    reducedEntryCount = 0
    try:
        for iKey, iValue in queryDict.items():
            try:
                if isinstance(iValue, dict):
                    annotateSubDict, reducedSubEntryCount = DictionaryReduceAnnotator(queryDict=iValue)
                    annotateDict[iKey] = annotateSubDict
                    reducedEntryCount += reducedSubEntryCount
                elif isinstance(iValue, list):
                    rValue = set(iValue)
                    if len(rValue) < len(iValue):
                        annotateDict[iKey] = len(iValue) - len(rValue)
                        reducedEntryCount += 1
                else:
                    annotateDict[iKey] = 0
            except BaseException as ErrorInnerContext:
                print(f"{whoami()} {ErrorInnerContext}")
                # pass or continue
                continue
    except BaseException as ErrorContext:
        print(f"{whoami()} {ErrorContext}")
    return annotateDict, reducedEntryCount


def DictionaryPrune(queryDict: dict):
    """
    Assistive function to traverse a dictionary recursively then remove data any list to a set entries to comprehend uniqueness.
    Each dictionary entry contains the reduced size amount from the reference queryDict.
    Args:
        queryDict: Dictionary composed to fundamental types: dict, list, str, int, float, etc.

    Returns: Requested dictionary annotations of reduced entries and total entries reduced.
    """
    pruneDict = dict()
    isReduced = False

    try:
        for iKey, iValue in queryDict.items():
            try:
                if isinstance(iValue, dict):
                    pruneSubDict, isSubReduced = DictionaryPrune(queryDict=iValue)
                    pruneDict[iKey] = pruneSubDict
                    isReduced |= isSubReduced
                elif isinstance(iValue, list):
                    rValue = set(iValue)
                    if (len(rValue) != 1) or (len(rValue) == len(iValue)):
                        pruneDict[iKey] = iValue
                    else:
                        isReduced |= True
                elif iValue is None:
                    isReduced |= True
                else:
                    pruneDict[iKey] = iValue
            except BaseException as ErrorInnerContext:
                print(f"{whoami()} {ErrorInnerContext}")
                # pass or continue
                continue
    except BaseException as ErrorContext:
        print(f"{whoami()} {ErrorContext}")
    return pruneDict, isReduced


class DictionaryFlatten(object):
    debug: bool = False
    fdSize: int = 0
    originalData = None

    def __init__(self, inDictionary=None, debug=False, separator='.', prefix=''):
        if isinstance(debug, bool):
            self.debug = debug

        if isinstance(inDictionary, dict):
            self.originalData = inDictionary
            self.flatDictionary = self.getSuperDictionary(inDictionary=inDictionary, separator=separator, prefix=prefix)
            self.fdSize = len(self.flatDictionary)
        return

    def getSize(self):
        return self.fdSize

    def getFlatDictionary(self):
        return self.flatDictionary

    def getOriginalData(self):
        return self.originalData

    @staticmethod
    def anyObjectToDictionary(inDictionary):
        return json.loads(json.dumps(inDictionary, default=lambda o: o.__dict__))

    def getFlattenDictionary(self, dd, separator='.', prefix=''):
        return {prefix + separator + k if prefix else k: v
                for kk, vv in dd.items()
                for k, v in self.getFlattenDictionary(vv, separator, kk).items()
                } if isinstance(dd, dict) else {prefix: dd}

    def getSuperDictionary(self, inDictionary=None, separator='.', prefix=''):
        objDictAny = self.anyObjectToDictionary(inDictionary)
        if self.debug:
            print(objDictAny, flush=True)
        objDictAny = self.getFlattenDictionary(dd=objDictAny, separator=separator, prefix=prefix)
        return objDictAny


def organizeAPI(options):
    """
    Args:
        options: options from main file usage.
    Returns: None
    """
    if options.root_directory is None:
        root_directory = os.getcwd()
    else:
        root_directory = options.root_directory

    if options.directory_files is None:
        directory_files = os.listdir(root_directory)  # This is how you get the files and folders in a directory
    else:
        directory_files = options.directory_files

    root_size = os.path.getsize(root_directory)  # Just a tip on how to get the size of a directory
    print(f"The size of the directory is: {root_size}")
    # To organize files starting with all letters or numbers.
    organizeString = 'abcdefghijklmnopqrstuvwxyz0123456789'
    if options.mode == 1:

        for letter_or_number in organizeString:
            organize_files_by_letter(first_letter=letter_or_number, directory_files=directory_files)

    elif options.mode == 2:
        for folder in organizeString:
            organize_folders_by_letter(first_letter=folder, directory_files=directory_files)

    elif options.mode == 3:
        for ext in ['jpg', 'png', 'bmp', 'jpeg']:
            organize_files_by_extension(ext=ext, directory_files=directory_files)

    elif options.mode == 4:
        for keyword in ['uid', 'ARMA', 'RNN']:
            organize_files_by_keyword(keyword=keyword, directory_files=directory_files)

    elif options.mode == 5:
        for keyword in ['uid', 'ARMA', 'RNN']:
            organize_folders_by_keyword(keyword=keyword, directory_files=directory_files)
    return


class FunctionScheduleTimer():
    """
    Class to create a function self timer or period query context.
    """
    def __init__(self, debug: bool = False):
        self.debug = False
        self.utc_time_first = None
        self.utc_time_past = None
        self.utc_time_now = None
        self.utc_timestamp = None
        self.utc_time_drift = None
        self.utc_time_difference = None
        self.utc_time_period = None
        self.utc_time_second_delay: int = 1
        self.utc_function_num_calls: int = 0
        self.utc_time_index: int = 1
        self.Iterations = 0

        self.debug = debug
        self.setup()
        return

    def setup(self, functionExecutionTime: int = 1):
        import copy
        self.utc_time_first = datetime.datetime.now()
        self.utc_time_past = copy.deepcopy(self.utc_time_first)
        self.utc_time_now = copy.deepcopy(self.utc_time_first)
        self.utc_time_drift = datetime.timedelta()
        if functionExecutionTime < 1:
            self.utc_time_period = 1
        tmpReplace = copy.deepcopy(self.utc_time_now)
        tmpNow = tmpReplace.replace(tzinfo=datetime.timezone.utc)
        self.utc_timestamp = tmpNow.timestamp()  # tmpNow.utc_time.timestamp()
        self.utc_time_difference = self.utc_time_now - self.utc_time_first

        self.utc_time_period = datetime.timedelta(seconds=functionExecutionTime)
        self.utc_time_drift = self.utc_time_difference - self.utc_time_period * self.utc_function_num_calls
        return

    def calculateDrift(self, functionCall=None):
        if functionCall is not None:
            self.utc_time_first = datetime.datetime.now()
            self.utc_time_past = copy.deepcopy(self.utc_time_first)
            self.utc_time_now = copy.deepcopy(self.utc_time_first)
            self.utc_time_drift = datetime.timedelta()
            functionCall()
            self.utc_time_period = self.getPeriod(nSeconds=self.utc_time_second_delay)
        return

    def getUpdate(self, functionCall=None):
        self.performSleep()
        self.utc_time_now = datetime.datetime.now()
        if functionCall is not None:
            functionCall()
        self.utc_function_num_calls += 1
        self.utc_time_difference = self.utc_time_now - self.utc_time_past
        self.utc_time_drift = self.utc_time_difference - self.utc_time_period * self.utc_function_num_calls
        return

    def performSleep(self):
        time.sleep(self.utc_time_second_delay - self.utc_time_drift.microseconds / 1000000.0)
        return

    def getPeriod(self, nSeconds: int = None):
        if nSeconds is None:
            nSeconds = self.getPeriodExponentialBackoff()
        utc_time_drift = datetime.timedelta(seconds=nSeconds)
        return utc_time_drift

    def isPeriodReady(self):
        self.utc_time_now = datetime.datetime.now()
        self.utc_time_difference = self.utc_time_now - self.utc_time_past
        self.utc_time_drift = self.utc_time_difference - self.utc_time_period * self.utc_function_num_calls
        if self.debug:
            print(f"{whoami()}, call number {self.Iterations}, drift {self.utc_time_drift}.")
        if self.utc_time_difference >= self.utc_time_period:
            return True
        return False

    @staticmethod
    def getPeriodExponentialBackoff(baseTime: int = 1, exponentialValue: int = 2, selectedIndex: int = 1):
        nextSecondsTimeIndex = baseTime * exponentialValue ** selectedIndex
        return nextSecondsTimeIndex

    def doExampleWaitLoop(self, functionCall=None, iterations: int = 1, allowSleep: bool = False):
        self.Iterations = 0
        while self.Iterations <= iterations:
            if allowSleep:
                self.performSleep()
            self.getUpdate(functionCall=functionCall)
            if self.debug:
                print(f"{whoami()}, call number {self.Iterations}, drift {self.utc_time_drift}.")
        return

    def doExamplePeriod(self, functionCall=None, iterations: int = 1):
        self.Iterations = 0
        while self.Iterations <= iterations:
            periodReady = self.isPeriodReady()
            if self.debug:
                print(f"{whoami()}, call number {self.Iterations}, drift {self.utc_time_drift}, Period Ready := {str(periodReady)}.")
            if periodReady and functionCall is not None:
                functionCall()
        return

    def doExamplePeriodExponential(self, functionCall=None, iterations: int = 1, sleepTime: int = 1):
        self.Iterations = 0
        timeIndex = 1
        while self.Iterations <= iterations:
            time.sleep(sleepTime)
            periodReady = self.isPeriodReady()
            if self.debug:
                print(f"{whoami()}, call number {self.Iterations}, drift {self.utc_time_drift}, Period Ready := {str(periodReady)}.")
            if periodReady and functionCall is not None:
                self.utc_time_period = self.getPeriodExponentialBackoff(selectedIndex=timeIndex)
                functionCall()
        return


def API(options=None):
    """ API for the default application in the graphical interface.
    Args:
        options: Commandline inputs.
    Returns:
    """
    if options.debug:
        print("Options are:\n{0}\n".format(options))
    ###############################################################################
    # Graphical User Interface (GUI) Configuration
    ###############################################################################
    print("options: ", str(options.mode))

    if options.root_directory is None:
        root_directory = os.getcwd()
    else:
        root_directory = options.root_directory

    if options.directory_files is None:
        directory_files = os.listdir(root_directory)  # This is how you get the files and folders in a directory
    else:
        directory_files = options.directory_files

    root_size = os.path.getsize(root_directory)  # Just a tip on how to get the size of a directory
    print(f"The size of the directory is: {root_size}")

    # To organize files starting with all letters or numbers.
    organizeString = 'abcdefghijklmnopqrstuvwxyz0123456789'

    if options.mode == 1:
        for letter_or_number in organizeString:
            organize_files_by_letter(first_letter=letter_or_number, directory_files=directory_files)

    elif options.mode == 2:
        for folder in organizeString:
            organize_folders_by_letter(first_letter=folder, directory_files=directory_files)

    elif options.mode == 3:
        for ext in ['jpg', 'png', 'bmp', 'jpeg']:
            organize_files_by_extension(ext=ext, directory_files=directory_files)

    elif options.mode == 4:
        for keyword in ['uid', 'ARMA', 'RNN']:
            organize_files_by_keyword(keyword=keyword, directory_files=directory_files)

    elif options.mode == 5:
        for keyword in ['uid', 'ARMA', 'RNN']:
            organize_folders_by_keyword(keyword=keyword, directory_files=directory_files)
    else:
        print("Error in Selection")
        pprint.pformat(locals(), indent=3, width=100)


def main():
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--example", action='store_true', dest='example', default=False, help='Show command execution example.')
    parser.add_option("--debug", action='store_true', dest='debug', default=True, help='Debug mode.')
    parser.add_option("--more", dest='more', default=False, help="Displays more options.")
    parser.add_option("--mode", dest='mode', default=None, help="Mode of Operation.")
    parser.add_option("--root_directory", dest='root_directory', default=None, help="Root directory of operation.")
    parser.add_option("--directory_files", dest='directory_files', default=None, help="Directory file list.")
    (options, args) = parser.parse_args()

    ##############################################
    # Main
    ##############################################
    API(options)
    return 0


if __name__ == '__main__':
    """Performs execution delta of the process."""
    p = datetime.datetime.now()
    try:
        main()
    except Exception as e:
        print("Fail End Process: ", e)
        traceback.print_exc()
    q = datetime.datetime.now()
    print("Execution time: " + str(q - p))
