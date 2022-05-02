#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# Python API for execution of Control Flag.
# * Authors: Joseph Tarango
# *****************************************************************************/
# Future compatibility with base in python 3.9
from __future__ import absolute_import, division, print_function, unicode_literals
import sys, os, datetime, traceback, optparse, pprint,  subprocess, tempfile, \
    re, itertools, time, typing, inspect, shutil, copy, multiprocessing, math, \
    threading, json, random, functools

import concurrent.futures, faulthandler, pathlib

# Logic to gracefully handle package is optional.
import PySimpleGUI

try:
    import pwd, grp, github  # Linux only libraries
except:
    pass

try:
    import psutil
except:
    pass


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
        doIt: Add to system path.
        excludeFolderList: Folders to not look in.
        excludeFileList: files to not look in.

    Returns: fileTypeTree, directoryTree

    """
    if fileType is None:
        fileType = ['.c', '.h', '.cc', '.cxx', '.cpp', '.hpp', '.c++', '.inl']
    if excludeFileList is None:
        excludeFileList = [".pyc", ".bin", ".svg", ".png", ".mbs", ".rc" ".cache", ".pdb", ".md", ".cs", ".bat", ".sh"]
    if excludeFolderList is None:
        excludeFolderList = ["__pycache__", "exclude"]
    tPath = os.path.abspath(directoryTreeRootNode)
    tExists = os.path.exists(tPath)
    if (directoryTreeRootNode is None) or (not tExists):
        if debug:
            print(f"Root directory does not exist: candidate is {directoryTreeRootNode}")
        directoryTreeRootNode = (os.path.dirname(__file__) or '.')

    if debug is True and verbose is True:
        print('Directory Root Node: {0}'.format(directoryTreeRootNode), flush=True)

    # Walk Entire local tree and save contents
    directoryTree = list()
    fileTypeTree = list()
    otherFileTree = list()
    excludeFileTree = list()
    fileTypesFound = list()
    for root, dirs, files in os.walk(directoryTreeRootNode):
        try:
            for dirSelect in dirs:
                if dirSelect not in excludeFolderList:
                    dirLocation = os.path.abspath(os.path.join(root, dirSelect))
                    directoryTree.append(dirLocation)
                    if debug is True and verbose is True:
                        print('Directory Node: {0}'.format(dirLocation), flush=True)
            for file in files:
                # Split path, file, extension
                fileSplit = os.path.splitext(file)
                # Extract the file name and extension
                # fileName = fileSplit[0]
                fileExtension = fileSplit[1]
                fileTypesFound.append(fileExtension)
                fullFilePath = os.path.abspath(os.path.join(root, file))
                if fileExtension in fileType:
                    fileLocation = fullFilePath
                    fileTypeTree.append(fileLocation)
                    if debug is True and verbose is True:
                        print('{0} File Node: {1}'.format(fileExtension.lower(), fileLocation), flush=True)
                elif fileExtension in excludeFileList:
                    excludeFile = fullFilePath
                    excludeFileTree.append(excludeFile)
                    if debug is True and verbose is True:
                        print('Exclude {0} File Node: {1}'.format(fileExtension.lower(), excludeFile), flush=True)
                else:
                    otherFileLocation = fullFilePath
                    otherFileTree.append(otherFileLocation)
                    if debug is True and verbose is True:
                        print('Other {0} File Node: {1}'.format(fileExtension.lower(), otherFileLocation), flush=True)
        except BaseException as ErrorContext:
            pprint.pprint(whoami())
            print('Exception {0}'.format(ErrorContext))
            pass

    fileTypesFound = list(set(fileTypesFound))
    systemPath = sys.path
    if debug is True and verbose is True:
        print('System path is: ')
        pprint.pprint(systemPath)

    if debug is True and verbose is True:
        print(f'File list: size={len(fileTypeTree)} {os.linesep}items={pprint.pprint(fileTypeTree)}{os.linesep}')
        print(f'Other File list: size={len(otherFileTree)} {os.linesep}items={pprint.pprint(otherFileTree)}{os.linesep}')
        print(f'Exclude File list: size={len(excludeFileTree)} {os.linesep}items={pprint.pprint(excludeFileTree)}{os.linesep}')
        print(f'All file types: size={len(fileTypesFound)} {os.linesep}items={pprint.pprint(fileTypesFound)}{os.linesep}')

    if doIt is True:
        for loc in directoryTree:
            sys.path.append(loc)

    return (fileTypeTree, directoryTree)


def changePermissionsRecursive(path: str = None, mode=None):
    """
    Mutator to change the permissions of a directory and contents.
    Args:
        path: path to recursively change permissions.
        mode:

    Returns: status of operation.
    """
    cStatus = False
    if path is None:
        return cStatus
    if mode is None:
        mode = 0o755
    for iroot, idirs, ifiles in os.walk(path, topdown=False):
        for idir in [os.path.join(path, d) for d in idirs]:
            os.chmod(idir, mode)
        for ifile in [os.path.join(path, f) for f in ifiles]:
            os.chmod(ifile, mode)
    cStatus = True
    return cStatus


def changeOwnerGroup(cPath: str = None, setSelf: bool = False, debug: bool = False):
    """
    Mutator to change permissions of a given path/file.
    Args:
        cPath: active path.
        setSelf: set user and group to current thread id.
        debug: flag to enable debug info.

    Returns: status of operation.
    """
    info = pathlib.Path(cPath)
    user = info.owner()
    group = info.group()
    uid = pwd.getpwnam(user).pw_uid
    gid = grp.getgrnam(group).gr_gid
    cStatus = False
    if debug:
        print(f"Current owner and group of the specified path")
        print(f"Owner {user}, {uid}; Group {group} {gid}")
    if (cPath is not None):
        if (setSelf is True):
            os.chown(cPath, uid, gid)
        cStatus = True
    return cStatus


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


def getAvailableCPUCount():
    """
    Number of available virtual or physical CPUs on this system, i.e.
    user/real as output by time(1) when called with an optimally scaling
    userspace-only program.
     Args: None
     Returns: Max of CPU or Thread count.
    """
    coreThreadsAvailable = 1

    # Python 2.6+
    try:
        coreThreadsAvailable = multiprocessing.cpu_count()
        return coreThreadsAvailable
    except (ImportError, NotImplementedError):
        pass

    try:
        coreThreadsAvailable = psutil.cpu_count()  # psutil.NUM_CPUS on old versions
        return coreThreadsAvailable
    except (ImportError, AttributeError):
        pass

    # POSIX
    try:
        res = int(os.sysconf('SC_NPROCESSORS_ONLN'))

        if res > 0:
            coreThreadsAvailable = res
            return coreThreadsAvailable
    except (AttributeError, ValueError):
        pass

    # Windows
    try:
        res = int(os.environ['NUMBER_OF_PROCESSORS'])

        if res > 0:
            coreThreadsAvailable = res
            return coreThreadsAvailable
    except (KeyError, ValueError):
        pass

    # BSD
    try:
        sysctl = subprocess.Popen(['sysctl', '-n', 'hw.ncpu'], stdout=subprocess.PIPE)
        scStdout = sysctl.communicate()[0]
        res = int(scStdout)

        if res > 0:
            coreThreadsAvailable = res
            return coreThreadsAvailable
    except (OSError, ValueError):
        pass

    # Linux
    try:
        res = open('/proc/cpuinfo').read().count('processor\t:')

        if res > 0:
            coreThreadsAvailable = res
            return coreThreadsAvailable
    except IOError:
        pass

    # cpuset may restrict the number of *available* processors
    try:
        m = re.search(r'(?m)^Cpus_allowed:\s*(.*)$',
                      open('/proc/self/status').read())
        if m:
            res = bin(int(m.group(1).replace(',', ''), 16)).count('1')
            if res > 0:
                coreThreadsAvailable = res
                return coreThreadsAvailable
    except IOError:
        pass

    # Solaris
    try:
        pseudoDevices = os.listdir('/devices/pseudo/')
        res = 0
        for pd in pseudoDevices:
            if re.match(r'^cpuid@[0-9]+$', pd):
                res += 1

        if res > 0:
            coreThreadsAvailable = res
            return coreThreadsAvailable
    except OSError:
        pass

    # Other UNIXes (heuristic)
    try:
        try:
            dmesg = open('/var/run/dmesg.boot').read()
        except IOError:
            dmesgProcess = subprocess.Popen(['dmesg'], stdout=subprocess.PIPE)
            dmesg = dmesgProcess.communicate()[0]

        res = 0
        while '\ncpu' + str(res) + ':' in dmesg:
            res += 1

        if res > 0:
            coreThreadsAvailable = res
            return coreThreadsAvailable
    except OSError:
        pass

    print('Can not determine number of CPUs on this system, so defaulting to 1.')
    return coreThreadsAvailable


def getAvailableCPUCount_Nice(requestedCores: int = None):
    """
    Helper function to reduce the threads to not lock the client or host system.
    Args:
        requestedCores: cores to execute from request.

    Returns: thread count to use for pools of threads.

    """
    requestedCoresClean = requestedCores
    # Clean data type if string or float
    try:
        if isinstance(requestedCoresClean, (str, float)):
            requestedCoresClean = int(requestedCoresClean)
    except:
        pass

    try:
        # Verify type is as expected and greater than zero
        possibleCores = getAvailableCPUCount()
        if requestedCoresClean is not None and (isinstance(requestedCoresClean, int) and (0 < requestedCoresClean < possibleCores)):
            # Within bounds of reason.
            suggestCores = requestedCoresClean
            skipFixing = True
        elif requestedCoresClean is not None and (isinstance(requestedCoresClean, int) and (requestedCoresClean == possibleCores)):
            # If all cores requested reduce by one so no system freeze.
            suggestCores = requestedCoresClean - 1
            skipFixing = True
        else:
            # Error: Danger, Will Robinson!
            suggestCores = possibleCores
            skipFixing = False

        if skipFixing is False:
            # Add logic to not freeze the system depending on client or server.
            # Formula := floor(log(cores)/log(2)), use bits of representation to subtract from total count
            suggestCores = suggestCores - int(math.floor(math.log2(suggestCores)))
        # Catch all for fixing invalid values
        if suggestCores < 1:
            suggestCores = possibleCores
    except:
        suggestCores = 1
        pass
    return suggestCores


def getDateTimeFileFormatString():
    """
    String formatter of date library.
    Returns: formatter for date object.
    """
    return '%Y-%m-%d-%H-%M-%S-%f'


def getTimeStampNow():
    """
    Get current time stamp in desired format.
    Returns: string of UTC time.

    """
    utc_datetime = datetime.datetime.utcnow()
    utc_time = utc_datetime.strftime(getDateTimeFileFormatString())
    return utc_time


def getTempFileName(genFile=True, inDir=None, suffix=None):
    """
    Generate file name.
    Args:
        genFile: proceed flag with generation.
        inDir: directory to create.
        suffix: File extension.

    Returns: file name token string.
    """
    utc_datetime = datetime.datetime.utcnow()
    utc_name = utc_datetime.strftime(getDateTimeFileFormatString())
    if inDir is None:
        inDir = ''
    if suffix is None:
        suffix = '.txt'

    if genFile is True:
        pseudo = "".join([utc_name, '_'])
        if inDir != '':
            os.makedirs(inDir, exist_ok=True)
        fileConstruct = tempfile.mkstemp(suffix=suffix, prefix=pseudo, dir=inDir)
        if not os.path.exists(fileConstruct):
            fileReadContext = open(file=fileConstruct, mode='w', buffering=1)
            fileReadContext.close()
    else:
        tempName = getRandomFileStr()
        pseudo = "".join([inDir, utc_name, '_', tempName, suffix])
        fileConstruct = pseudo
    return fileConstruct


def getRandomFileStr(characters: str = "abcdefghijklmnopqrstuvwxyz0123456789", minWidth: int = 4, maxWidth: int = 8):
    """
    Function to usea character set to generate a random string of desired width
    Args:
        characters: Series of char candidates
        minWidth: Min random width window of chars.
        maxWidth: Max random width window of chars.

    Returns: string of random chars.

    """
    seqLetters = ''
    seqSize = random.randint(minWidth, maxWidth)
    for _ in range(seqSize):
        randValue = random.randint(0, len(characters)-1)
        seqLetters += characters[randValue]
    return seqLetters


def getTempDirName(genDir=True, inDir=None, suffix=""):
    """
    Generate file name in a nice manner using date and suffix.
    Args:
        genDir: proceed flag with directory generation.
        inDir: directory to create.
        suffix: File extension.

    Returns: directory name token string.

    """
    utc_datetime = datetime.datetime.utcnow()
    utc_name = utc_datetime.strftime(getDateTimeFileFormatString())
    if genDir is True:
        pseudo = "".join([utc_name, "_"])
        if inDir is not None:
            os.makedirs(name=inDir, exist_ok=True)
        dirConstruct = tempfile.mkdtemp(suffix=suffix, prefix=pseudo, dir=inDir)
        if not os.path.exists(dirConstruct):
            os.makedirs(name=dirConstruct, exist_ok=True)
    else:
        dirConstruct = ""
    return dirConstruct


def whoami(annotate: bool = True):
    """
    Accessor function used to access stack, file, function, and line of code to trace a execution path.
    Args:
        annotate: Flag to annotate in such as way easy to parse by print.

    Returns: file, function, line of code, access stack
    """
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


def debugErrorContext(debug: bool = False, errorContext: BaseException = None, localVars=None, stackVar=None):
    """
    Create debug error context string and print if requested.
    Args:
        debug: debug mode for adding functionality.
        errorContext: exception object
        localVars: variables local to calling function.
        stackVar: call stack of active error.
    Returns: error string
    """
    errorString = ""
    try:
        if errorContext is not None:
            errorString += f"Error Context {pprint.pformat(errorContext)}{os.linesep}"
        if localVars is not None:
            errorString += f"Local Variables {pprint.pformat(localVars)}{os.linesep}"
        if stackVar is not None:
            errorString += f"Stack Context {pprint.pformat(stackVar)}{os.linesep}"
    except:
        pass
    if debug:
        print(errorString)
    return errorString


def streamPrint(token: str = '', saveToken: str = '', printToken: bool = True):
    """
    Helper function to take a token candidate, save destination, and print if requested.
    Args:
        token: New string to append.
        saveToken: Save token string stream.
        printToken:

    Returns: appended string with new token.

    """
    saveToken += token
    if printToken:
        print(token)
    return saveToken


class GithubSimpleAPI(object):
    """
    Github base address search class for creating training sets.
    """

    def __init__(self, debug: bool = False):
        self.debug = debug
        return

    def getID(self, userName: str = None):
        """
        User identification number extractor for database lookup.
        Args:
            userName: string login username

        Returns: integer tracking identification value.
        """
        userLoginName = ""
        userID = 0
        if userName is None:
            userName = ""
        try:
            gitObject = github.Github(login_or_token=userName)
            userLoginName = gitObject.get_user()
            userID = gitObject.get_user().id
        except BaseException as errorContext:
            debugErrorContext(debug=self.debug, errorContext=errorContext, localVars=locals(), stackVar=whoami())
        return userID

    def getReposOfLanguage(self, userName=None, programmingLanguage: str = None):
        """
        Get  the repositories using a defined language type.
        Args:
            userName: github username
            programmingLanguage: language to search for.

        Returns: repositories found.

        """
        if userName is None:
            userName = self.getID(userName=userName)
        if programmingLanguage is None:
            programmingLanguage = "language:c++"
        gitObject = github.Github(login_or_token=userName)
        repositories = gitObject.search_repositories(query=programmingLanguage)
        return repositories

    def getReposOfLanguages(self, userName=None, programmingLanguages: set = None):
        """
        Get repositories of a language set using github or reference base address.
        Args:
            userName: current user name
            programmingLanguages: programming language list labels to search

        Returns: languages requested of repository.
        """
        if programmingLanguages is None:
            programmingLanguages = ["language:c", "language:c++"]
        repoSet = dict()
        for pl in programmingLanguages:
            repoSet[pl] = self.getReposOfLanguage(userName=userName, programmingLanguage=pl)
        return repoSet


class WorkerThread():
    """
    Assistive class for threading such that you do not need a class with *.run()
    The class is to make threading subprocesses easy and encapsulated.

    Example to use threading:

    def func(a, k):
        print("func(): a=%s, k=%s" % (a, k))
        return

    def perform_function():
        thread = WorkerThread(target=func, args=(1,), kwargs=("a": 1, "k": 2))
        # OR
        thread = WorkerThread(target=func, kwargs=(a=1, k= 2))
        thread.start()
        thread.join()
    """
    '''
    The basic idea is given a function create an object.
    The object can then run the function in a thread.
    It provides a wrapper to start it,check its status,and get data out the function.
    '''
    statusCodes = {-3: 'not_started',
                   -2: 'started',
                   -1: 'running',
                   0 : 'finished',
                   1 : 'error',
                   2 : 'unknown'}

    statusCodesInvert = {value: key for key, value in statusCodes.items()}

    def __init__(self, group=None, target=None, name=None, args=None, kwargs=None, daemon=False, areArgumentsRequired=True):
        """
        Initializer for preparing subprocess threader.
        target = my_function,
        args   = (my_function_arg1, my_function_arg2, ...)
        kwargs = (my_function_kwarg1=kwarg1_value, my_function_kwarg2=kwarg2_value, ...)
        """
        if not callable(target):
            raise ValueError("target must be a function.")

        # Determine what exists for arguments
        args_does_not_exist = args is None
        kwargs_does_not_exist = kwargs is None
        args_does_exist = args is not None
        kwargs_does_exist = kwargs is not None

        args_isTupple = isinstance(args, tuple)
        kwargs_isDictionary = isinstance(kwargs, dict)

        # Thread vars: args/kwargs
        if areArgumentsRequired:
            string_error_args = "args arguments must be a non-empty tuple"
            string_error_kwargs = "kwargs must be non-empty dictionary"
            if (args_does_not_exist) and (kwargs_does_not_exist):
                raise ValueError(f"Neither exist: {string_error_args} or {string_error_kwargs}.")
            elif (args_does_exist) or (kwargs_does_not_exist):
                if args_isTupple:
                    self.args = args
                    self.kwargs = kwargs
                    self.functionArgs = args
                else:
                    # args is wrong type
                    raise ValueError(f"args exist: {string_error_args}.")
            elif (args_does_not_exist) or (kwargs_does_exist):
                if kwargs_isDictionary:
                    self.args = ()
                    self.kwargs = kwargs
                    self.functionArgs = kwargs
                else:
                    # kwargs is wrong type
                    raise ValueError(f"kwargs exist: {string_error_kwargs}.")
            else:
                raise ValueError(f"Both exist: {string_error_args} or {string_error_kwargs}.")
        else:
            # Let thread inheritance handle nil objects.
            self.args = ()
            self.kwargs = kwargs
            # Set internal var for debug
            self.functionArgs = None

        # Thread vars
        self.group = group
        self.target = target
        self.name = name
        self.daemon = daemon

        # Actual tracking
        self.thread = None
        self.data = None
        self.function = self._functionSignature
        return

    def _getStatus(self, searchToken):
        """
        Use a forward and reverse dictionary to traverse either string to string or status code to string decoding.
        Args:
            searchToken: integer or string token to search for in status map.

        Returns: status of thread.
        """
        if isinstance(searchToken, int):
            if searchToken in self.statusCodesInvert:
                return self.statusCodes[searchToken]
        elif isinstance(searchToken, str):
            if searchToken in self.statusCodesInvert:
                return searchToken
        return 'unknown'

    def _functionSignature(self):
        """
        Function pointer constructor with nil arguments to be tokenized on thread start.
        Returns: None
        """
        self.result = self.target(*self.args, **self.kwargs)
        return

    def start(self):
        """
        Start the thread and prepare state tracking.
        Returns: status of thread execution.
        """
        self.data = None
        if self.thread is not None:
            if self.thread.is_alive():
                # Else could raise exception for unknown thread state, lets assume it is healthy.
                return self._getStatus(searchToken='running')
        # Unless thread exists and is alive start or restart it
        self.thread = threading.Thread(group=self.group, target=self.function, name=self.name, daemon=self.daemon)
        (self.thread).start()
        return self._getStatus(searchToken='started')

    def status(self):
        """
        Check the status of the given thread
        Returns: Thread state
        """
        if self.thread is None:
            return self._getStatus(searchToken='not_started')
        else:
            if self.thread.is_alive():
                return self._getStatus(searchToken='running')
            else:
                return self._getStatus(searchToken='finished')

    def get_results(self):
        """
        Get the results for the thread.
        Returns: Thread meta or status is still active. If the function has a callback or event interrupt then cleaner threading handling can occur.
        """
        if self.thread is None:
            # self._getStatus(searchToken='not_started'))  # Could return exception for not starting or handle gracefully.
            self.start()
        else:
            if self.thread.is_alive():
                return self._getStatus(searchToken='running')
            else:
                return self.data


class ThreadFutures():
    """
    Class for future thread instance execution in a non-blocking manner with returning results.
    """

    def __init__(self):
        # Thread instances
        self.threadPool = None
        self.threadFuture = None
        # Thread status
        self.isDone = False
        # Thread return data
        self.result = None
        # Tracking internal arguments
        self.max_workers = None
        self.mp_context = None
        self.initializer = None
        self.initargs = ()
        self.fn = None
        self.args = None
        self.kwargs = None

    def setWork(self, max_workers, mp_context, initializer, initargs, fn, args, kwargs):
        """Initializes a new ProcessPoolExecutor instance.
        Args:
           max_workers: The maximum number of processes that can be used to
               execute the given calls. If None or not given then as many
               worker processes will be created as the machine has processors.
           mp_context: A multiprocessing context to launch the workers. This
               object should provide SimpleQueue, Queue and Process.
           initializer: A callable used to initialize worker processes.
           initargs: A tuple of arguments to pass to the initializer.
           fn: function pointer
           args: arguments values
           kwargs: argument key, value pair tuple.
       """
        self.max_workers = max_workers
        self.mp_context = mp_context
        self.initializer = initializer
        self.initargs = initargs
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        return

    def createThreadPool(self):
        """
        Create a thread pool and context scope for management.
        Returns: None
        """
        self.threadPool = concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers, mp_context=self.mp_context, initializer=self.initializer, initargs=self.initargs)
        return

    def runWork(self):
        """
        Create thread instance and submit it to queue.
        Returns: None

        """
        self.threadFuture = self.threadPool.submit(self.fn, args=self.args, kwargs=self.kwargs)
        return

    def createAndRun(self, max_workers, mp_context, initializer, initargs, fn, args, kwargs):
        """Initializes a new ProcessPoolExecutor instance.
        Args:
           max_workers: The maximum number of processes that can be used to
               execute the given calls. If None or not given then as many
               worker processes will be created as the machine has processors.
           mp_context: A multiprocessing context to launch the workers. This
               object should provide SimpleQueue, Queue and Process.
           initializer: A callable used to initialize worker processes.
           initargs: A tuple of arguments to pass to the initializer.
           fn: function pointer
           args: arguments given in order without precise variable calls
           kwargs: dictionary form for positional precise calls
        """
        self.setWork(max_workers=max_workers, mp_context=mp_context, initializer=initializer, initargs=initargs, fn=fn, args=args, kwargs=kwargs)
        self.createThreadPool()
        self.runWork()
        return

    def isReady(self):
        """
        Check if the process result is ready.
        Returns: Status of return objects.
        """
        self.isDone = self.threadFuture.done()
        return self.isDone

    def getResult(self):
        """
        Check if the process result is ready.
        Returns: Return status output streams.
        """
        if self.isDone:
            self.result = self.threadFuture.result()
        return self.result


class SuperSubProcess(object):
    """
    External executable subprocess execution library to co-operate with futures
    thread manager for parallelism.
    """
    debug: bool = False
    sProgram = ''
    sArguments = list()
    sArgumentsMax = None
    sArgumentsCount: int = 0
    indexID: int = 0
    processPendingCout = None
    processPendingErr = None
    processPendingReturnCode = None
    processPendingResult = None
    startTime = None
    endTime = None
    totalTime = 0
    operationMode = None
    timeout = None
    runnningStatus: bool = False
    file_stdout = None
    file_stdout_stream = None
    file_stderr = None
    file_stderr_stream = None
    # Hidden Windows subprocess flags
    ABOVE_NORMAL_PRIORITY_CLASS = 0x00008000
    BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
    HIGH_PRIORITY_CLASS = 0x00000080
    IDLE_PRIORITY_CLASS = 0x00000040
    NORMAL_PRIORITY_CLASS = 0x00000020
    REALTIME_PRIORITY_CLASS = 0x00000100

    def __init__(self, debug: bool = False, operationMode: str = 'poll', sArgumentsMax: int = None):
        """
        Initialization of object.
        Args:
            debug: Boolean value for debug status.
            operationMode: Mode of poll or parallel execution of API.
            sArgumentsMax: Sum of expected tokens + values. I.E. ./program.exe -d directory -v := 2 + 1
        Returns: None
        """
        self.clear()
        self.setDebug(debug=debug)
        self.setOperationMode(operationMode=operationMode)
        self.setArgumentMax(sArgumentsMax=sArgumentsMax)
        # Hidden Windows subprocess flags
        self.ABOVE_NORMAL_PRIORITY_CLASS = 0x00008000
        self.BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
        self.HIGH_PRIORITY_CLASS         = 0x00000080
        self.IDLE_PRIORITY_CLASS         = 0x00000040
        self.NORMAL_PRIORITY_CLASS       = 0x00000020
        self.REALTIME_PRIORITY_CLASS     = 0x00000100
        return

    def clear(self):
        """Method to clear internal variables."""
        self.debug = False
        self.sProgram = ''
        self.sArguments = list()
        self.sArgumentsMax = None
        self.sArgumentsCount = 0
        self.indexID = 0
        self.processPendingCout = None
        self.processPendingErr = None
        self.processPendingReturnCode = None
        self.processPendingResult = None
        self.startTime = None
        self.endTime = None
        self.totalTime = 0
        self.operationMode = None
        self.timeout = None
        self.runnningStatus = False
        self.file_stdout = None
        self.file_stdout_stream = None
        self.file_stderr = None
        self.file_stderr_stream = None
        # Hidden Windows subprocess flags
        self.ABOVE_NORMAL_PRIORITY_CLASS = 0x00008000
        self.BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
        self.HIGH_PRIORITY_CLASS         = 0x00000080
        self.IDLE_PRIORITY_CLASS         = 0x00000040
        self.NORMAL_PRIORITY_CLASS       = 0x00000020
        self.REALTIME_PRIORITY_CLASS     = 0x00000100
        return

    def setDebug(self, debug: bool = False):
        """
        Mutator for debug status.
        Args:
            debug: Boolean value for debug status.

        Returns: None
        """
        self.debug = debug
        return

    def setOperationMode(self, operationMode: str = 'poll'):
        """
        Mutator for debug status.
        Args:
            operationMode: Value for Mode.

        Returns: None
        """
        self.operationMode = operationMode
        return

    def setArgumentMax(self, sArgumentsMax: int = None):
        """
        Mutator for debug status.
        Args:
            sArgumentsMax: Max values for programs.

        Returns: None
        """
        self.sArgumentsMax = sArgumentsMax
        return

    def validate_command(self):
        """
        Validates a given command and parameter set to provide program usage error catches.
        Returns: Command conforms to defined count or parameters.
        """
        statusFlag = True
        arg_size_actual = len(self.sArguments)
        arg_size_count = self.sArgumentsCount
        if self.sProgram != '':
            command_size = 1
        else:
            command_size = 0

        errorFlag_1_Case = arg_size_count > self.sArgumentsMax
        errorFlag_2_Case = arg_size_actual > self.sArgumentsMax
        errorFlag_3_Case = (arg_size_actual + command_size) > (self.sArgumentsMax + 1)
        errorFlag_4_Case = command_size != 1

        if errorFlag_1_Case or errorFlag_2_Case or errorFlag_3_Case:
            print("Error in token count.")
            statusFlag = False
        if errorFlag_4_Case:
            statusFlag = False
        return statusFlag

    def isRunning(self):
        """
        Status to determine if subprocess is active.
        Returns: status of the process.

        """
        return self.runnningStatus

    def getAll(self):
        """
        Accessor for state of the class.
        Returns: Dictionary containing state of class.
        """
        pItemDictionary = dict()
        pItemDictionary['Debug Status'] = self.debug
        pItemDictionary['Program Name'] = self.sProgram
        pItemDictionary['Arguments'] = self.sArguments
        pItemDictionary['Index'] = self.indexID
        pItemDictionary['Output'] = self.processPendingCout
        pItemDictionary['Error'] = self.processPendingErr
        pItemDictionary['Return Code'] = self.processPendingReturnCode
        pItemDictionary['Process Object'] = self.processPendingResult
        pItemDictionary['Start Time'] = self.startTime
        pItemDictionary['End Time'] = self.endTime
        pItemDictionary['Total Time'] = self.totalTime
        return pItemDictionary

    def reset(self):
        """
        Resets internal variables.
        Returns: None
        """
        self.sProgram = ''
        self.sArguments = list()
        self.indexID: int = 0
        self.processPendingCout = None
        self.processPendingErr = None
        self.processPendingReturnCode = None
        self.processPendingResult = None
        return

    def addParam(self, paramToken: str = '', paramField: str = None):
        """
        Mutator to add a parameter for subprocess execution.
        Args:
            paramToken: The token literal name.
            paramField: Token literal value defined.

        Returns: string with appended parameter if content is not None.
        """
        if self.sArgumentsMax is not None:
            if self.sArgumentsCount > self.sArgumentsMax:
                print("Error in token count.")
        paramTokenValid = (paramToken is not None and paramToken != '')
        paramFieldValid = (paramField is not None and paramField != '')
        if paramTokenValid and paramFieldValid:
            stringToken = [f'{paramToken}'] + [f'{paramField}']
        elif not paramTokenValid and paramFieldValid:
            stringToken = [f'{paramField}']
        elif paramTokenValid and not paramFieldValid:
            stringToken = [f'{paramToken}']
        else:
            stringToken = ''
        if paramTokenValid or paramFieldValid:
            if self.sArgumentsMax is not None:
                if (self.sArgumentsCount > self.sArgumentsMax) and (len(self.sArguments) > self.sArgumentsMax):
                    print("Error in token count.")
                else:
                    self.sArgumentsCount += 1
            self.sArguments.extend(stringToken)
        return stringToken

    def addExecutable(self, programPath: str = None, programName: str = None):
        """
        Add a program executable path and binary; if it is found.
        Args:
            programPath: Path to program.
            programName: Literal name of program.

        Returns: Success of finding and setting program.
        """
        pStatus = False
        if programName is None:
            return pStatus
        pathConstruct = tryFile(path=programPath, fileName=programName, walkUpLimit=4)
        if pathConstruct is not None:
            pStatus = True
            self.sProgram = pathConstruct
        return pStatus

    def getCommand(self):
        """
        Constructs a command variable from set content
        Returns: Command string.
        """
        if self.sProgram is not None and self.sArguments != list():
            cmd = self.sArguments
            cmd.insert(0, self.sProgram)
        else:
            cmd = None
        return cmd

    @staticmethod
    def pContextFormat(processPendingResult=None, debug: bool = True):
        """
        Function to tokenize process output, format is general so we can save context to file, if necessary.
        Args:
            processPendingResult: subprocess object.
            debug: Developer debug flag

        Returns: Output stream context of process execution.
        """
        processPendingCout = None
        processPendingErr = None
        processPendingReturnCode = None
        if processPendingResult is not None:
            try:
                processPendingCout = processPendingResult.stdout.decode('utf-8')
            except:
                processPendingCout = processPendingResult.stdout
                pass
            try:
                processPendingErr = processPendingResult.stderr.decode('utf-8')
            except:
                processPendingErr = processPendingResult.stderr
                pass
            processPendingReturnCode = processPendingResult.returncode
        if debug:
            pContextTxt = f"[NOTICE] Process execution."
            if processPendingCout is not None:
                pContextTxt += f" @Stream Return       :{os.linesep}{pprint.pformat(processPendingCout)}"
            if processPendingErr is not None:
                pContextTxt += f" *Error Stream Return :{os.linesep}{pprint.pformat(processPendingErr)}"
            if processPendingResult is not None:
                pContextTxt += f" $Return Code         :{os.linesep}{processPendingReturnCode}"
            print(pContextTxt)
        return (processPendingCout, processPendingErr, processPendingReturnCode)

    @staticmethod
    def set_low_priority():
        try:
            if psutil.LINUX:
                psutil.Process().nice(psutil.IOPRIO_CLASS_BE)
                os.nice(1)
            else:
                psutil.Process().nice(psutil.IOPRIO_LOW)
        except:
            pass
        return

    @staticmethod
    def set_normal_priority():
        try:
            if psutil.LINUX:
                psutil.Process().nice(psutil.IOPRIO_CLASS_NONE)
                os.nice(-1)
            else:
                psutil.Process().nice(psutil.IOPRIO_NORMAL)

        except:
            pass
        return

    @staticmethod
    def set_high_priority():
        try:
            if psutil.LINUX:
                psutil.Process().nice(psutil.IOPRIO_CLASS_RT)
                os.nice(-2)
            else:
                psutil.Process().nice(psutil.IOPRIO_HIGH)

        except:
            pass
        return

    def runProcess(self, indexID: int = 0, timeout: int = None):
        """
        Use the program using the internal flag for polling or periodic check.
           Arguments:
               indexID: track index (starts from 0)
               timeout: Process timeout. Default time is 60 seconds * 60 minutes * 24 hours = 1 day in seconds per thread
           Returns:
               A list containing the: trackid, cout, cerr, return value of program.
        """
        self.timeout = timeout
        if self.operationMode == 'poll':
            self.runnningStatus = True
            returnContainer = self.runProcessPoll(indexID=indexID, timeout=timeout)
            pStatus = 'complete'
        else:
            if self.runnningStatus is True:
                tStatus, stateCode, pItemDictionary = self.runProcessParallelCheck(timeout=timeout)
                returnContainer = pItemDictionary
                pStatus = tStatus
            elif self.runnningStatus is False:
                pStatus = 'pending'
                returnContainer = self.runProcessParallel(indexID=indexID)
            else:
                returnContainer = None
                pStatus = 'error'
        return pStatus, returnContainer

    def runProcessPoll(self, indexID: int = 0, timeout: int = None):
        """
        Use the program in a blocking call.
           Arguments:
               indexID: track index (starts from 0)
               timeout: Process timeout. Default time is 60 seconds * 60 minutes * 24 hours = 1 day in seconds per thread
           Returns:
               A list containing the: trackid, cout, cerr, return value of program.
        """
        self.runnningStatus = True
        self.startTime = time.time()
        if self.debug:
            print(f"[NOTICE] Threads, start time token {self.startTime}")

        self.indexID = indexID
        processPendingResult = None
        pItemDictionary = dict()
        command = self.getCommand()
        if timeout is None:
            timeout = (60 * 60 * 24 * 2)

        processPendingResult = None
        processPendingCout = None
        processPendingErr = None
        processPendingReturnCode = None
        try:
            if self.debug:
                print(f"[NOTICE] Command executed is:{os.linesep}{pprint.pformat(command)}")
            self.set_low_priority()
            if psutil.WINDOWS:
                processPendingResult = subprocess.run(command, capture_output=True, timeout=int(timeout), preexec_fn=self.set_low_priority(), creationflags=self.BELOW_NORMAL_PRIORITY_CLASS)
            else:
                processPendingResult = subprocess.run(command, capture_output=True, timeout=int(timeout), preexec_fn=self.set_low_priority())
            self.set_normal_priority()
            self.processPendingResult = processPendingResult
            (processPendingCout, processPendingErr, processPendingReturnCode) = self.pContextFormat(
                processPendingResult=processPendingResult, debug=self.debug)
        except BaseException as errorContext:
            pItemDictionary = dict()
            print(f"Error on subprocess poll: {whoami()} {debugErrorContext(errorContext=errorContext, localVars=locals(), stackVar=globals())}")

        # Dictionary return variant.
        pItemDictionary['Index'] = indexID
        pItemDictionary['Output'] = processPendingCout
        pItemDictionary['Error'] = processPendingErr
        pItemDictionary['Return Code'] = processPendingReturnCode
        pItemDictionary['Process Object'] = processPendingResult

        # Internal meta save.
        self.processPendingCout = processPendingCout
        self.processPendingErr = processPendingErr
        self.processPendingReturnCode = processPendingReturnCode
        self.processPendingResult = processPendingResult

        self.endTime = time.time()
        self.totalTime = self.endTime - self.startTime
        if self.debug:
            print(f"[NOTICE] Command Output={pprint.pformat(processPendingCout)}{os.linesep}")
            print(f"[NOTICE] Command Error Output={pprint.pformat(processPendingErr)}{os.linesep}")
            print(f"[NOTICE] Command Return Code={pprint.pformat(processPendingReturnCode)}")
            print(f"[NOTICE] End time token {self.endTime}")
            print(F"[NOTICE] Threads ID executed {self.indexID} at {self.totalTime:.4f} seconds.")
        return pItemDictionary

    def runProcessParallel(self, indexID: int = 0, debug: bool = None):
        """
        Use the program in parallel
           Arguments:
               indexID: track index (starts from 0)
               debug: debug status flag.
           Returns:
               Process pending object.
        """
        if debug is None:
            activeDebug = self.debug
        else:
            activeDebug = debug
        if self.runnningStatus is False:
            self.runnningStatus = True
            self.startTime = time.time()
            if activeDebug:
                print(f"[NOTICE] Threads, start time token {self.startTime}")

            self.indexID = indexID
            command = self.getCommand()
            if self.sArgumentsMax is not None:
                assert (len(command) == self.sArgumentsMax + 1), "Error in command"
            try:
                if activeDebug:
                    print(f"[NOTICE] Command executed is:{os.linesep}{pprint.pformat(command)}")
                self.set_low_priority()
                if psutil.WINDOWS:
                    processPendingResult = subprocess.Popen(command, preexec_fn=self.set_low_priority(), creationflags=self.BELOW_NORMAL_PRIORITY_CLASS)
                else:
                    processPendingResult = subprocess.Popen(command, preexec_fn=self.set_low_priority())
                self.set_normal_priority()
                self.processPendingResult = processPendingResult
            except BaseException as errorContext:
                if activeDebug:
                    print(f"[ERROR] Command execution error is:{os.linesep}{pprint.pformat(errorContext)}")
                processPendingResult = None
        else:
            processPendingResult = None
        return processPendingResult

    def runProcessParallelCheck(self, timeout: int = None, debug: bool = None):
        """
        Process status and completion checker for a non-blocking view of the subprocess.
        Args:
            timeout: Process timeout. Default time is 60 seconds * 60 minutes * 24 hours = 1 day in seconds per thread
            debug: Debug statement print flag.

        Returns: tStatus, stateCode[tStatus], pItemDictionary := status code, status string, process dictionary object.

        """
        pStates_pending = 'pending'
        pStates_complete = 'complete'
        pStates_timeout = 'timeout'
        pStates_error = 'error'
        stateCode = {pStates_pending : -1,
                     pStates_complete: 0,
                     pStates_timeout : 1,
                     pStates_error   : 2}

        pItemDictionary = dict()
        tStatus = pStates_error
        processPendingCout = ""
        processPendingErr = ""
        processPendingReturnCode = ""
        if debug is not None:
            activeDebug = debug
        else:
            activeDebug = self.debug

        try:
            processPendingCode = self.processPendingResult.poll()
        except BaseException as errorContext:
            tStatus = pStates_error
            if activeDebug:
                print(
                    f"[ERROR] Command execution pool error is:{os.linesep}{pprint.pformat(errorContext)}{os.linesep}{whoami()}")
            return tStatus, stateCode[tStatus], pItemDictionary

        cEndTime = time.time()
        try:
            if processPendingCode is None:
                tStatus = pStates_pending
            else:
                if self.processPendingResult.returncode == 0:
                    tStatus = pStates_complete
                else:
                    tStatus = pStates_error
                indexID = self.indexID
                (processPendingCout, processPendingErr, processPendingReturnCode) = self.pContextFormat(processPendingResult=self.processPendingResult, debug=activeDebug)

                # Internal meta save.
                self.processPendingCout = processPendingCout
                self.processPendingErr = processPendingErr
                self.processPendingReturnCode = processPendingReturnCode

                # Dictionary return variant.
                pItemDictionary['Index'] = indexID
                pItemDictionary['Output'] = processPendingCout
                pItemDictionary['Error'] = processPendingErr
                pItemDictionary['Return Code'] = processPendingReturnCode
                pItemDictionary['Process Object'] = self.processPendingResult

            self.totalTime = cEndTime - self.startTime

            if self.totalTime > timeout:
                tStatus = pStates_timeout
                self.endTime = cEndTime
                try:
                    self.processPendingResult.kill()
                except BaseException as errorContext:
                    if activeDebug:
                        print(f"[ERROR] Command execution kill error is:{os.linesep}{pprint.pformat(errorContext)}")
                    pass
            if tStatus == pStates_complete and activeDebug:
                print("Threads ID executed {0} at {1:.4f} seconds.".format(self.indexID, self.totalTime))
        except BaseException as dErrorContext:
            if activeDebug:
                print(
                    f"[ERROR] Thread status check{os.linesep}{pprint.pformat(dErrorContext)}{os.linesep}{pprint.pformat(whoami())}")
        return tStatus, stateCode[tStatus], pItemDictionary


class MassiveParallelismSingleFunctionManyParameters(object):
    """
    High performance massive parallelism class in which a single function context
    with a list of parameters to pass.
    """

    def __init__(self,
                 debug: bool = False,
                 functionName=None,
                 fParameters: typing.List[dict] = None,
                 workers: int = None,
                 timeOut: int = (60 * 60 * 24),
                 # Default time is 60 seconds * 60 minutes * 24 hours = 1 day in seconds per thread
                 inOrder: bool = True,
                 runSequential: bool = False):
        """
        Class initializer to prepare variables for thread execution.
        Args:
            debug: Developer debug flag to print content as the flow progresses.
            functionName: Function name to perform threading by just a callback versus a instance usage. I.E. function vs function(vars)
            fParameters: List of Dictionary parameters for each function call.
            workers: Number of threads to spawn in the pool scope for execution.
            timeOut: Duration before the process stopped.
            inOrder: Flag to process the completion of threads in order; which is useful for batch merging of data where order matters.
            runSequential: Thread execution engine to run in sequential order (1 at at time) versus run in parallel up to the worker count.
        """
        self.debug = debug
        self.functionName = functionName
        self.fParameters = fParameters
        self.workers = workers
        self.timeOut = timeOut
        self.inOrder = inOrder
        self.resultsList = list()
        self.encounteredExceptions = 0
        self.exceptionFoundList = list()
        self.alreadyExecuted = False
        self.areResultsReady = False
        self.startTime = None
        self.endTime = None
        self.totalTime = None
        self.runSequential = runSequential
        return

    def setFunctionName(self, functionName):
        """
        Mutator to set the internal function callback.
        Args:
            functionName: Function name without the parens.

        Returns: None

        Examples
        object = MassiveParallelismSingleFunctionManyParameters()
        object.setFunctionName(functionName=max)
        """
        self.functionName = functionName
        return

    def setParametersList(self, fParameters: typing.List[dict]):
        """
        Sets parameter list from dictionary parameter context.
        Args:
            fParameters: list of dictionaries of parameters

        Returns: None

        Example
        kwargsList_input = [{'inputINI': dataFileNameA,
                             ...
                             'debug': debug,
                             'inParallel': inParallelA,
                             'requiredList': requiredListA},
                             ...
                            {'inputINI': dataFileNameZ,
                             ...
                             'debug': debugZ,
                             'inParallel': inParallelZ,
                             'requiredList': requiredListZ}]
        """
        self.fParameters = fParameters
        return

    def getExceptionInfo(self):
        """
        Accessor to gather exception info from execution for analysis.
        Returns: Count of exceptions and exception details list.
        """
        return self.encounteredExceptions, self.exceptionFoundList

    def getExecutionTime(self):
        """
        Accessor to get the thread overall execution time.
        Returns: Start time, End time, and total time delta.
        """
        return self.startTime, self.endTime, self.totalTime

    def getResults(self):
        return self.resultsList

    def _inOrderConcurrentMap(self):
        """
        Function that utilises concurrent.futures.ProcessPoolExecutor.map returning inorder in a parallelised manner.
        Returns: results list in order of list given.
        """
        self.alreadyExecuted = True
        # Local variables
        functionContextList = list()
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executer:
            # Discretise workload and submit to worker pool
            mapperMeta = executer.map(lambda parametersList: self.functionName(**parametersList), self.fParameters,
                                      timeout=self.timeOut)
            self.resultsList.append(mapperMeta)
            # Access results in order.
            for parallelProcessItem in functionContextList:
                try:
                    self.resultsList.append(parallelProcessItem)
                except BaseException as errorObj:
                    self.encounteredExceptions += 1
                    exceptionContext = f" {whoami()} with {errorObj}! Timeout={self.timeOut}"
                    self.exceptionFoundList.append(exceptionContext)
                    if self.debug:
                        print(exceptionContext)
        self.areResultsReady = True
        return self.resultsList

    def _anyOrderConcurrentMap(self):
        """
        Function that utilises concurrent.futures.ProcessPoolExecutor.map returning in any order in a parallelised manner.
            Returns: results list no particular order of list given.
        """
        self.alreadyExecuted = True
        # Local variables
        functionContextList = list()
        # Parallelization
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.workers) as executor:
            # Discretise workload and submit to worker pool
            for fParameterContext in self.fParameters:
                try:
                    functionContextList.append(executor.submit(self.functionName, fParameterContext))
                except BaseException as errorObj:
                    self.encounteredExceptions += 1
                    exceptionContext = f" {whoami()} with {errorObj}! Timeout={self.timeOut}"
                    self.exceptionFoundList.append(exceptionContext)
                    if self.debug:
                        print(exceptionContext)
        # Skip the copying of the data to another array and use itertools.chain.from_iterable to combine the results from execution to single iterable
        self.resultsList = itertools.chain.from_iterable(
            f.result() for f in concurrent.futures.as_completed(functionContextList, timeout=self.timeOut))
        self.areResultsReady = True
        return self.resultsList

    def _sequentialMap(self):
        """
        Function that executions a function with a list of parameters.
            Returns: results list in order of list given.
        """
        self.alreadyExecuted = True
        # Discretise workload and submit worker
        try:
            for fParameterContext in self.fParameters:
                sResult = self.functionName(**fParameterContext)
                (self.resultsList).append(sResult)
        except BaseException as errorObj:
            self.encounteredExceptions += 1
            exceptionContext = f" {whoami()} with {errorObj}! Timeout={self.timeOut}"
            self.exceptionFoundList.append(exceptionContext)
            if self.debug:
                print(exceptionContext)
        self.areResultsReady = True
        return self.resultsList

    def execute(self):
        """
        Function to use the preset parameters and execute according to the defined task.
        Returns: None
        """
        if self.alreadyExecuted is False:
            self.startTime = time.time()
            if self.debug:
                print(f"Threads, start time token {self.startTime}")

            if self.runSequential is True:
                if self.debug:
                    print(" Processing sequentially in order of parameter list...")
                self._sequentialMap()
            elif self.runSequential is False and self.inOrder is True:
                if self.debug:
                    print(" Processing in-order of parameters list...")
                self._inOrderConcurrentMap()
            elif self.runSequential is False and self.inOrder is False:
                if self.debug:
                    print(" Processing out-of-order of parameters list...")
                self._anyOrderConcurrentMap()
            else:
                if self.debug:
                    print(" Fault in configuration... running sequentially...")
                self._sequentialMap()

            self.endTime = time.time()
            if self.debug:
                print(f"End time token {self.endTime}")
            self.totalTime = self.endTime - self.startTime
            if self.debug:
                print("Threads executed {0} at {1:.4f} seconds with {2} workers".format(len(self.resultsList),
                                                                                        self.totalTime, self.workers))
        return self.resultsList


class ILControlFlag(object):
    """
    Intel Labs Control Flag class API for mining and scanning a database. The class is built to be generic, multi-threaded, and non-blocking.
    """
    DESCRIPTION = f"Intel Labs Control Flag {os.linesep}" \
                  f"What’s New: Today, Intel unveiled ControlFlag – a machine programming research system that can autonomously detect errors in code. Even in its infancy, this novel, self-supervised system shows promise as a powerful productivity tool to assist software developers with the labor-intensive task of debugging. In preliminary tests, ControlFlag trained and learned novel defects on over 1 billion  unlabeled lines of production-quality code. Why It Matters: In a world increasingly run by software, developers continue to spend a disproportionate amount of time fixing bugs rather than coding. It’s estimated that of the $1.25 trillion that software development costs the IT industry every year, 50 percent is spent debugging code1. Debugging is expected to take an even bigger toll on developers and the industry at large. As we progress into an era of heterogenous architectures — one defined by a mix of purpose-built processors to manage the massive sea of data available today — the software required to manage these systems becomes increasingly complex, creating a higher likelihood for bugs. In addition, it is becoming difficult to find software programmers who have the expertise to correctly, efficiently and securely program across diverse hardware, which introduces another opportunity for new and harder-to-spot errors in code. When fully realized, ControlFlag could help alleviate this challenge by automating the tedious parts of software development, such as testing, monitoring and debugging. This would not only enable developers to do their jobs more efficiently and free up more time for creativity, but it would also address one of the biggest price tags in software development today. How It Works: ControlFlag’s bug detection capabilities are enabled by machine programming, a fusion of machine learning, formal methods, programming languages, compilers and computer systems. ControlFlag specifically operates through a capability known as anomaly detection. As humans existing in the natural world, there are certain  patterns we learn to consider 'normal' through observation. Similarly, ControlFlag learns from verified examples to detect normal coding patterns, identifying anomalies in code that are likely to cause a bug. Moreover, ControlFlag can detect these anomalies regardless of programming language. A key benefit of ControlFlag’s unsupervised approach to pattern recognition is that it can intrinsically learn to adapt to a developer’s style. With limited inputs for the control tools that the program should be evaluating, ControlFlag can identify stylistic variations in programming language, similar to the way that readers recognize the differences between full words or using contractions in English. The tool learns to identify and tag these stylistic choices and can customize error identification and solution recommendations based on its insights, which  minimizes ControlFlag’s characterizations of code in error that may simply be a stylistic deviation between two developer teams. Intel has even started evaluating using ControlFlag internally to identify bugs in its own software and firmware product development. It is a key element of Intel’s Rapid Analysis for Developers project, which aims to accelerate velocity by providing expert assistance.{os.linesep}" \
                  rf"Video: https://vimeo.com/intelpr/review/486109038/360d4e62c8 {os.linesep}" \
                  rf"Citation: https://arxiv.org/abs/2011.03616{os.linesep}"
    EPILOG = "Anomalous toolkit API used to mine or scan C/C++ code signatures"
    VERSION = "v1.0"
    AUTHORS = "Niranjan Hasabnis, Justin Gottschlich, Joseph Tarango"

    def __init__(self):
        # Shared command display output variables for GUI between threads.
        self.output_scan = "Scan=Nil"
        self.output_mine = "Mine=Nil"
        return

    @staticmethod
    def addParam(existingCommand: str = "", paramToken: str = "", paramField: str = None):
        """
        Mutator to add a parameter for subprocess execution.
        Args:
            existingCommand: Previous command to append parameter.
            paramToken: The token literal name.
            paramField: Token literal value defined.

        Returns: string with appended parameter if content is not None.
        """
        if paramField is not None:
            extendedCommand = copy.deepcopy(existingCommand)
            stringToken = [f'{paramToken}'] + [f'{paramField}']
            extendedCommand += stringToken
        else:
            extendedCommand = existingCommand
        return extendedCommand

    @staticmethod
    def _verifyParamBool(param):
        paramVal = param
        if isinstance(paramVal, str):
            try:
                if paramVal.upper() == 'TRUE':
                    paramVal = True
                elif paramVal.upper() == 'FALSE':
                    paramVal = False
                else:
                    paramVal = bool(paramVal)
            except:
                paramVal = True
                pass

        return paramVal

    def API_Tokenize_Common(self, defaults: dict = None):
        """
        Main API flags used across control flag instances.
        Args:
            defaults: default argument values for each option.
        Returns: parser object with common elements.
        """
        if defaults is None:
            defaults = {'faultSave': False,
                        'debug'    : False,
                        'more'     : False,
                        'timeout'  : int(60 * 60 * 24 * 2),
                        'mode'     : 'Mine'}

        # Handle python type confusion gracefully.
        defaults['faultSave'] = self._verifyParamBool(param=defaults['faultSave'])
        defaults['debug'] = self._verifyParamBool(param=defaults['debug'])
        defaults['more'] = self._verifyParamBool(param=defaults['more'])

        if isinstance(defaults['timeout'], str):
            try:
                defaults['timeout'] = int(defaults['timeout'])
            except:
                defaults['timeout'] = int(60 * 60 * 24 * 2)
                pass

        parser = optparse.OptionParser(version=self.VERSION, description=self.DESCRIPTION, prog=None,
                                       epilog=self.EPILOG)
        parser.add_option("--example", action='store_true', dest='example', default=False,
                          help='Example Parameters: -t data/c_lang_if_stmts_6000_gitrepos.ts -o data/tmp_results_anomalies -l data/adp.ilcf -v 2.')

        parser.add_option("--faultSave", dest='faultSave', default=defaults['faultSave'], help="Enable fault context save for debug.")
        parser.add_option("--debug", action='store_true', dest='debug', default=defaults['debug'], help='Enable Debug mode.')
        parser.add_option("--more", dest='more', default=defaults['more'], help="Displays more options.")
        parser.add_option("--timeout", dest='timeout', default=defaults['timeout'],
                          help="Amount of time in seconds before killing task. Default time is 60 seconds * 60 minutes * 24 hours * 2 = 2 days in seconds per thread")
        parser.add_option("--mode", dest='mode', default=defaults['mode'], help="Operation mode of main Intel Labs Control Flag [Mine, Scan]")
        return parser

    @staticmethod
    def API_MineMeta_Tokenize(parser, defaults: dict = None):
        """
        Main cAPI flags used for mining control flag instances.
        Args:
            parser: parser object with tokens.
            defaults: default argument values for each option.
        Returns: parser object with additional meta mining instances.
        """
        if defaults is None:
            defaults = {'directory_to_mine_patterns_from'        : '../../../../ADP/nand/gen3/src',
                        'directory_to_mine_patterns_from_default': '',
                        'number_of_processes_to_use_for_mining'  : None,
                        'output_directory_to_store_training_data': '../data/tmp_results_mine',
                        'output_file_to_store_training_data'     : None,
                        'tree_depth'                             : 100
                        }

        # Handle python type confusion gracefully.
        try:
            if isinstance(defaults['number_of_processes_to_use_for_mining'], str):
                defaults['number_of_processes_to_use_for_mining'] = int(defaults['number_of_processes_to_use_for_mining'])
            elif isinstance(defaults['number_of_processes_to_use_for_mining'], (int, float)):
                defaults['number_of_processes_to_use_for_mining'] = int(defaults['number_of_processes_to_use_for_mining'])
            else:
                defaults['number_of_processes_to_use_for_mining'] = None
        except:
            defaults['number_of_processes_to_use_for_mining'] = None
            pass

        if (defaults['directory_to_mine_patterns_from'] == '' or defaults['directory_to_mine_patterns_from'] is None) and \
                (defaults['directory_to_mine_patterns_from_default'] != '' and defaults['directory_to_mine_patterns_from_default'] is not None):
            defaults['directory_to_mine_patterns_from'] = defaults['directory_to_mine_patterns_from_default']

        if ('output_file_to_store_training_data' not in defaults) or \
                (defaults['output_file_to_store_training_data'] is None) or \
                (defaults['output_file_to_store_training_data'] == ''):
            defaults['output_file_to_store_training_data'] = getTempFileName(genFile=False, inDir=None, suffix='.ilsf')

        try:
            if isinstance(defaults['tree_depth'], str):
                defaults['tree_depth'] = int(defaults['tree_depth'])
            elif isinstance(defaults['tree_depth'], (int, float)):
                defaults['tree_depth'] = int(defaults['tree_depth'])
            else:
                defaults['tree_depth'] = 100
        except:
            defaults['tree_depth'] = 100
            pass

        parser.add_option("--d", dest='directory_to_mine_patterns_from', default=defaults['directory_to_mine_patterns_from'],
                          help="")
        parser.add_option("--n", dest='number_of_processes_to_use_for_mining', default=defaults['number_of_processes_to_use_for_mining'], help="")

        parser.add_option("--o", dest='output_file_to_store_training_data', default=defaults['output_file_to_store_training_data'], help="")
        tree_depth_comment = f"Tree level, representing the tokening format.{os.linesep}" \
                             f"LEVEL_MIN = 0,   // Basic Tree-sitter print{os.linesep}" \
                             f"LEVEL_ONE = 1,   // Same as MAX level. Diff is printing operators also.{os.linesep}" \
                             f"                 // Such as == or != in addition to binary_expression.{os.linesep}" \
                             f"LEVEL_TWO = 2,   // EXPR := TERM BINARY_OP TERM | UNARY_OP TERM | *TERM | TERM | FCALL | VAR.VAR | VAR[TERM] | anything_else{os.linesep}" \
                             f"                 // TERM := VAR | CONST | anything_else{os.linesep}" \
                             f"LEVEL_MAX = 3,   // (VAR), (CONST), (EXPR){os.linesep}"
        parser.add_option("--t", dest='tree_depth', default=defaults['tree_depth'], help=tree_depth_comment)

        return parser

    @staticmethod
    def API_ScanForAnomalies_Tokenize(parser, defaults: dict = None):
        """
        Main cAPI flags used for scanning control flag instances.
        Args:
            parser: parser object with tokens.
            defaults: default argument values for each option.
        Returns: parser object with additional meta scanning instances.
        """
        if defaults is None:
            defaults = {'training_data'                                   : '../data/c_lang_if_stmts_6000_gitrepos.ts',
                        'directory_to_scan_for_anomalous_patterns'        : '../../../../ADP/nand/gen3/src',
                        'max_cost_for_autocorrect'                        : 2,
                        'max_number_of_results_for_autocorrect'           : 5,
                        'number_of_scanning_threads'                      : None,
                        'output_log_dir'                                  : '../data/tmp_results_anomalies',
                        'anomaly_threshold'                               : float(5.0)}

        # Handle python type confusion gracefully.
        if isinstance(defaults['max_cost_for_autocorrect'], (int, float)):
            defaults['max_cost_for_autocorrect'] = f"{defaults['max_cost_for_autocorrect']}"

        if isinstance(defaults['max_number_of_results_for_autocorrect'], (int, float)):
            defaults['max_number_of_results_for_autocorrect'] = f"{defaults['max_number_of_results_for_autocorrect']}"

        if isinstance(defaults['number_of_scanning_threads'], (int, float)):
            defaults['number_of_scanning_threads'] = f"{defaults['number_of_scanning_threads']}"

        if isinstance(defaults['anomaly_threshold'], (int, float)):
            defaults['anomaly_threshold'] = f"{defaults['anomaly_threshold']:.1f}"

        if (defaults['directory_to_scan_for_anomalous_patterns'] == '' or defaults['directory_to_scan_for_anomalous_patterns'] is None) and \
                (defaults['directory_to_scan_for_anomalous_patterns_default'] != '' and defaults['directory_to_scan_for_anomalous_patterns_default'] is not None):
            defaults['directory_to_scan_for_anomalous_patterns'] = defaults['directory_to_scan_for_anomalous_patterns_default']

        parser.add_option("--t", dest='training_data', default=defaults['training_data'], help="")
        parser.add_option("--d", dest='directory_to_scan_for_anomalous_patterns', default=defaults['directory_to_scan_for_anomalous_patterns'], help="")
        parser.add_option("--c", dest='max_cost_for_autocorrect', default=defaults['max_cost_for_autocorrect'], help="")
        parser.add_option("--n", dest='max_number_of_results_for_autocorrect', default=defaults['max_number_of_results_for_autocorrect'], help="")
        parser.add_option("--j", dest='number_of_scanning_threads', default=defaults['number_of_scanning_threads'], help="")
        parser.add_option("--o", dest='output_log_dir', default=defaults['output_log_dir'], help="")
        parser.add_option("--a", dest='anomaly_threshold', default=defaults['anomaly_threshold'], help="")

        return parser

    @staticmethod
    def API_Tokenize(parser):
        """
        Function to parse input arguments into options object.
        Args:
            parser: parser object for flags.

        Returns: options for program usage.

        """
        (options, _) = parser.parse_args()
        return options

    def API_ScanForAnomalies_Do(self, options=None, applicationPath: str = None, applicationExe: str = None):
        """
        Python API for scanning a directory for anomalies.
        Args:
            options: expected program arguments.
            applicationPath: program path.
            applicationExe: application name.

        Returns: completion status code
        """
        outputString = ""
        outputString = streamPrint(token=f"Intel Labs Control Flag Code Scan {self.VERSION}", saveToken=outputString)
        raadImportBase = os.path.dirname(os.path.abspath(__file__))
        if options is None:
            api_fail = True
            statusNumber = 1
        else:
            api_fail = False
            statusNumber = 0

        if applicationExe is None:
            applicationExe = "cf_file_scanner"

        if applicationPath is None:
            defaultPath = '../bin'
            applicationPath = defaultPath
            foundExe = tryFile(path=defaultPath, fileName=applicationExe, walkUpLimit=4)
            if foundExe is None:
                api_fail = True
                statusNumber = 1
                outputString = streamPrint(token=f"[INPUT ERROR] Binary Exe does not exist {applicationExe} => {os.path.abspath(applicationExe)}", saveToken=outputString)

        trainingFileExists = os.path.exists(options.training_data)
        if not trainingFileExists:
            api_fail = True
            statusNumber = 1
            outputString = streamPrint(token=f"[INPUT ERROR] Training data file does not exist {options.training_data} => {os.path.abspath(options.training_data)}", saveToken=outputString)

        patternDirectoryExists = os.path.exists(options.directory_to_scan_for_anomalous_patterns)
        if not patternDirectoryExists:
            api_fail = True
            statusNumber = 1
            outputString = streamPrint(token=f"[INPUT ERROR] Search pattern directory does not exist {options.directory_to_scan_for_anomalous_patterns} => {os.path.abspath(options.directory_to_scan_for_anomalous_patterns)}", saveToken=outputString)

        if api_fail is False:
            if options.debug:
                outputString = streamPrint(token=f"[NOTICE] Basepath := {raadImportBase}", saveToken=outputString)
            (fileTypeTree, directoryTree) = findAll(
                directoryTreeRootNode=options.directory_to_scan_for_anomalous_patterns, debug=options.debug, doIt=False,
                verbose=options.more)

            shutil.rmtree(path=options.output_log_dir, ignore_errors=True)
            os.makedirs(options.output_log_dir, exist_ok=True)
            metaTmpFilePath = getTempFileName(genFile=True, inDir=os.path.abspath(options.output_log_dir),
                                              suffix='.ilcf')

            foundFilesWriteContext = open(file=metaTmpFilePath, mode='w', buffering=1)
            if options.debug or options.more:
                outputString = streamPrint(token=f"[NOTICE] Discovered files location: {metaTmpFilePath}", saveToken=outputString)
            for searchFile in fileTypeTree:
                foundFilesWriteContext.write(rf"{searchFile}{os.linesep}")
            foundFilesWriteContext.close()

            pThreadObject = SuperSubProcess(debug=options.debug)
            pThreadObject.addExecutable(programPath=applicationPath, programName=applicationExe)

            # Prepare thread for launch.
            # Required Args
            # -t '../c_lang_if_stmts_6000_gitrepos.ts' -d ../../../../ADP/nand/gen3/src -c 2 -n 5 -j 12 -o ../data/tmp_results_anomalies -a 5 -v 2 -l ../data/adp.ilcf
            pThreadObject.addParam(paramToken='-t', paramField=os.path.abspath(options.training_data))
            # Note the scan for patters directory is not needed since we create a file discovered list.
            #  command = self.addParam(existingCommand=command, paramToken='-d', paramField=os.path.abspath(options.directory_to_scan_for_anomalous_patterns))

            # Optional Args, note make sure to stringify integers and floats.
            pThreadObject.addParam(paramToken='-c', paramField=f"{options.max_cost_for_autocorrect}")
            pThreadObject.addParam(paramToken='-n', paramField=f"{options.max_number_of_results_for_autocorrect}")
            pThreadObject.addParam(paramToken='-a', paramField=f"{options.anomaly_threshold}")

            options.number_of_scanning_threads = getAvailableCPUCount_Nice(requestedCores=options.number_of_scanning_threads)
            pThreadObject.addParam(paramToken='-j', paramField=options.number_of_scanning_threads)

            if not os.path.exists(options.output_log_dir):
                os.makedirs(options.output_log_dir, exist_ok=True)
            pThreadObject.addParam(paramToken='-o', paramField=os.path.abspath(options.output_log_dir))

            pThreadObject.addParam(paramToken='-v', paramField=(f"{2}"))

            # Hidden Args
            pThreadObject.addParam(paramToken='-l', paramField=metaTmpFilePath)

            # Creation of process context to execute program
            _, pThreadDictionary = pThreadObject.runProcess(indexID=1, timeout=options.timeout)

            if pThreadDictionary is None:
                streamPrint(token=f"[ERROR] Scan thread subprocess failure{os.linesep}", saveToken=outputString)

            if options.more:
                outputString = streamPrint(token=f"[NOTICE] Used files location {metaTmpFilePath}{os.linesep}", saveToken=outputString)
            if options.debug:
                outputString = streamPrint(token=f"[DEBUG NOTICE]{os.linesep}{pprint.pformat(pThreadDictionary)}{os.linesep}", saveToken=outputString)
            else:
                os.remove(metaTmpFilePath)

            outputToken = self._createSummaryScan(output_log_dir=options.output_log_dir, fileType='.log', summaryFile="summaryFile_Scan.log")
            outputString = streamPrint(token=outputToken, saveToken=outputString)
            outputToken = self._createSummaryScan(output_log_dir=options.output_log_dir, fileType='.cvs', summaryFile="summaryFile_Scan.cvs")
            outputString = streamPrint(token=outputToken, saveToken=outputString)
            self.output_scan = outputString
        return statusNumber

    def _createSummaryScan(self, output_log_dir=None, fileType='.log', summaryFile="summaryFile_Scan.txt"):
        if (output_log_dir is not None) and (os.path.exists(output_log_dir)):
            scanDirectory = os.path.abspath(output_log_dir)
            logFiles, _ = findAll(fileType=[fileType], directoryTreeRootNode=scanDirectory, excludeFileList=[])
            cmp_items_py39 = functools.cmp_to_key(self._cvsFileSorter)
            logFiles.sort(key=cmp_items_py39)
            summaryFile = os.path.join(os.path.abspath(output_log_dir), summaryFile)
            summaryFileWriteContext = open(file=summaryFile, mode='w', buffering=1)
            for metaDataFile_fc in logFiles:
                if os.path.exists(metaDataFile_fc):
                    # Opening files in read only mode to read contents to append to summary.
                    fileReadContext = open(file=metaDataFile_fc, mode='r')
                    summaryFileWriteContext.write(fileReadContext.read())
                    fileReadContext.close()
            summaryFileWriteContext.close()  # Close final file.
            outputString = f"[NOTICE] Summary file is: {summaryFile}{os.linesep}"
        else:
            outputString = f"[ERROR] Scan aggregation path does not exist for: {summaryFile}{os.linesep}"
        return outputString

    @staticmethod
    def _cvsFileSorter(inA, inB, topToken: str = "HEADER"):
        """
        Function to sort files in alphabetical order except for header which should be first.
        Args:
            inA: File name
            inB: File Name
            topToken: Token to put at top of list.

        Returns:  Compare of alphabetical order except for header which should be first
        """
        inAHasTopToken = topToken in inA.upper()
        inBHasTopToken = topToken in inB.upper()
        inALarger = inA.upper() > inB.upper()
        inEqual = inA.upper() == inB.upper()
        inASmaller = inA.upper() < inB.upper()
        if (inAHasTopToken and inBHasTopToken) or (not inAHasTopToken and not inBHasTopToken):
            if inALarger:
                return 1
            elif inASmaller:
                return -1
            elif inEqual:
                return 0
        elif inAHasTopToken and not inBHasTopToken:
            return 1
        elif not inAHasTopToken and inBHasTopToken:
            return 0
        else:
            return 0

    def API_MineMeta_Do(self, options=None, applicationPath: str = None, applicationExe: str = None):
        """
        Python API for scanning a directory for anomalies.
        Args:
            options: expected program arguments.
            applicationPath: program path.
            applicationExe: application name.

        Returns: completion status code
        """
        outputString = ""
        outputString = streamPrint(token=f"Intel Labs Control Flag Code Miner {self.VERSION}", saveToken=outputString)
        raadImportBase = os.path.dirname(os.path.abspath(__file__))
        tmp_dir = None
        functionContextList = list()
        pThreadClass = dict()
        summaryFile = "summaryFile.ts"
        iResults = list()

        if options is None:
            api_fail = True
            statusNumber = 1
        else:
            api_fail = False
            statusNumber = 0

        if applicationExe is None:
            applicationExe = "cf_dump_conditional_exprs"
        if applicationPath is None:
            defaultPath = '../bin'
            applicationPath = defaultPath
            foundExe = tryFile(path=applicationPath, fileName=applicationExe, walkUpLimit=4)
            if foundExe is None:
                api_fail = True
                statusNumber = 1
                outputString = streamPrint(token=f"[INPUT ERROR] Binary Exe does not exist {applicationExe} => {os.path.abspath(applicationExe)}", saveToken=outputString)

        patternDirectoryExists = os.path.exists(os.path.abspath(options.directory_to_mine_patterns_from))
        if not patternDirectoryExists:
            api_fail = True
            statusNumber = 1
            outputString = streamPrint(token=f"[INPUT ERROR] Directory to mine pattern directory does not exist {options.directory_to_mine_patterns_from} => {os.path.abspath(options.directory_to_mine_patterns_from)}", saveToken=outputString)

        if api_fail is False:
            if options.debug:
                outputString = streamPrint(token=f"[NOTICE] Base path := {raadImportBase}", saveToken=outputString)
            (fileTypeTree, directoryTree) = findAll(directoryTreeRootNode=options.directory_to_mine_patterns_from,
                                                    debug=options.debug, doIt=False, verbose=options.more)

            shutil.rmtree(path=options.output_directory_to_store_training_data, ignore_errors=True)
            os.makedirs(name=options.output_directory_to_store_training_data, exist_ok=True)
            summaryFile = getTempFileName(genFile=True,
                                          inDir=os.path.abspath(os.path.join(options.output_directory_to_store_training_data, options.output_file_to_store_training_data)),
                                          suffix='_summaryFile.ts')
            foundFilesPath = getTempFileName(genFile=True,
                                             inDir=os.path.abspath(os.path.join(options.output_directory_to_store_training_data, options.output_file_to_store_training_data)),
                                             suffix='.ilsf')

            foundFilesWriteContext = open(file=foundFilesPath, mode='w+', buffering=1)
            if options.debug or options.more:
                outputString = streamPrint(token=f"[NOTICE] Discovered files location: {foundFilesPath}", saveToken=outputString)
            for searchFile in fileTypeTree:
                foundFilesWriteContext.write(f"{searchFile}{os.linesep}")
            foundFilesWriteContext.close()

            # Args are Nil and Optional Args
            getAvailableCPUCount_Nice(requestedCores=options.number_of_processes_to_use_for_mining)

            # Create a working directory
            tmp_dir = getTempDirName(genDir=True, inDir=os.path.abspath(options.output_directory_to_store_training_data), suffix='_tmp')
            if options.debug or options.more:
                outputString = streamPrint(token=f"[NOTICE] Temporary directory for files in data processing: {os.path.abspath(tmp_dir)}", saveToken=outputString)

            # Prepare futures threading with super subprocess thread
            pThreadObject = SuperSubProcess(debug=options.debug)
            for fIndex, iFile in enumerate(fileTypeTree):
                pThreadObject.clear()
                # Input format: <c_source_file> <tree_depth> <github_id> <output_file>
                pThreadObject = SuperSubProcess(debug=options.debug, operationMode='parallel', sArgumentsMax=4)
                pThreadObject.addExecutable(programPath=applicationPath, programName=applicationExe)

                # Prepare thread for launch.
                # Required Args
                pThreadObject.addParam(paramToken='', paramField=f"{iFile}")
                pThreadObject.addParam(paramToken='', paramField=str(100))
                pThreadObject.addParam(paramToken='', paramField=f"{fIndex}")  # @todo jdtarang github label.
                metaDataFile = os.path.join(tmp_dir, f"proc_{fIndex}.log")
                pThreadObject.addParam(paramToken='', paramField=f"{metaDataFile}")
                listGroup = list([copy.deepcopy(fIndex), copy.deepcopy(pThreadObject), copy.deepcopy(f"{metaDataFile}")])
                functionContextList.append(copy.deepcopy(listGroup))
            countCPUMax = options.number_of_processes_to_use_for_mining
            countCPU = 0
            for fIndex_fc, pThreadObject_fc, metaDataFile_fc in functionContextList:
                assert (pThreadObject_fc.validate_command() is True), "Error with Command construction"
            for fIndex_fc, pThreadObject_fc, metaDataFile_fc in functionContextList:
                if countCPU < countCPUMax:
                    countCPU += 1
                    pThreadObject_fc.runProcessParallel(indexID=fIndex_fc, debug=options.debug)

            while len(functionContextList) > 0:
                time.sleep(0.5)
                for listIndex, pActive in enumerate(functionContextList):
                    fIndex_fc, pThreadObject_fc, metaDataFile_fc = pActive
                    if pThreadObject_fc.isRunning():
                        tStatus, stateCode, pItemDictionary = pThreadObject_fc.runProcessParallelCheck(
                            timeout=options.timeout, debug=options.debug)
                        if stateCode >= 0:
                            completeItem = functionContextList.pop(listIndex)
                            if tStatus not in pThreadClass:
                                pThreadClass[tStatus] = list()
                            pThreadClass[tStatus].append([fIndex_fc, pThreadObject_fc, metaDataFile_fc, completeItem])
                            countCPU -= 1
                    else:
                        if countCPU < countCPUMax:
                            countCPU += 1
                            pThreadObject_fc.runProcessParallel(indexID=fIndex_fc, debug=options.debug)

            # Output contents to summary context file.
            if 'complete' in pThreadClass:
                iResults = pThreadClass['complete']
        else:
            iResults = None
        if iResults is not None and iResults is not list():
            summaryFileWriteContext = open(file=summaryFile, mode='w', buffering=1)
            for fIndex_fc, pThreadObject_fc, metaDataFile_fc, completeItem in iResults:
                if os.path.exists(metaDataFile_fc):
                    # Opening files in read only mode to read contents to append to summary.
                    fileReadContext = open(file=metaDataFile_fc, mode='r')
                    summaryFileWriteContext.write(fileReadContext.read())
                    fileReadContext.close()
            summaryFileWriteContext.close()  # Close final file.

        if not options.debug and tmp_dir is not None:
            shutil.rmtree(path=tmp_dir, ignore_errors=False)  # Delete intermediate files.
        if summaryFile is not None:
            outputString = streamPrint(token=f"[NOTICE] Summary File {summaryFile}.", saveToken=outputString)

        self.output_mine = outputString

        return statusNumber

    def API_ScanForAnomalies_Execute(self):
        """
        Main API to scan for anomalies on pretrained neural network context.
        Returns: process completion status.
        """
        parser = self.API_Tokenize_Common()
        parser = self.API_ScanForAnomalies_Tokenize(parser=parser)
        options = self.API_Tokenize(parser=parser)
        statusCode = self.API_ScanForAnomalies_Do(options=options)
        return statusCode

    def API_MineMeta_Execute(self):
        """
        Main API to Min for anomalies for neural network context.
        Returns: process completion status.
        """
        parser = self.API_Tokenize_Common()
        parser = self.API_MineMeta_Tokenize(parser=parser)
        options = self.API_Tokenize(parser=parser)
        statusCode = self.API_MineMeta_Do(options=options)
        return statusCode

    @staticmethod
    def _boxTraits(stringObject: str = "", maxWidth: int = 32, maxHeight: int = 4):
        """
        Determine a text box size given traits from the text context with ranges.
        Args:
            stringObject: String candidate.
            maxWidth: Width max of the desired text box.
            max Height: height max of the desired text box.
        Returns: tuple for width and height.
        """
        heightActual = math.ceil(len(stringObject) / maxWidth)
        if heightActual > maxHeight:
            height = maxHeight
        else:
            height = heightActual
        size = (maxWidth, height)
        return size

    def GUI_FileLoadSave(self,
                         returnLayout=False, charWidth=88, charHeight=4,
                         title: str = 'Default Title',
                         fileNameLabelKey: str = 'File name',
                         fileNameKey: str = 'FileNameKey',
                         fileNameToken: str = 'FileNameToken',
                         fileMode: str = None,
                         default_folder: str = None,
                         fileExtenstion: str = None,
                         visible: bool = True):
        """
        Layout construction for an independent mining control flag instances. Note Example Parameters: -t data/c_lang_if_stmts_6000_gitrepos.ts -o data/tmp_results_anomalies -l data/adp.ilcf -v 2.
        Args:
            returnLayout: Flag to return the flag or execute in independent mode.
            charWidth: Width of the text box.
            charHeight: Height of a given display box.
            title: Title to display on window.
            fileNameLabelKey: Display label for file information.
            fileNameToken: String to fill in the field.
            fileNameKey: Dictionary key for token to be stored.
            fileMode: Mode of operation being load or save.
            default_folder: Default folder to start browser in.
            fileExtenstion: File extenstion of configuration file.
            visible: Display boxes.


        Returns: layout or input box information.
        """
        ###############################################################################
        # Graphical User Interface (GUI) Configuration
        ###############################################################################
        if (returnLayout is False):
            PySimpleGUI.ChangeLookAndFeel('LightBlue')
        menu_def = [['&File', ['E&xit'], ], ]
        ###############################################################################
        # Basic collect form.
        # Return values as a list.
        ###############################################################################

        if default_folder is None:
            default_folder = os.curdir
        elif not os.path.exists(default_folder):
            default_folder = os.curdir
        default_folder = os.path.abspath(default_folder)
        if fileExtenstion is None:
            fileExtenstion = '.cfg'

        fileLabelSize = self._boxTraits(stringObject=fileNameLabelKey, maxWidth=charWidth, maxHeight=charHeight)
        titleSize = self._boxTraits(stringObject=title, maxWidth=charWidth, maxHeight=charHeight)
        filePath = os.path.join(default_folder, (fileNameToken + fileExtenstion))
        if fileMode == 'Save':
            layout = [[PySimpleGUI.Text(title, size=titleSize)],
                      [PySimpleGUI.Input(key=fileNameLabelKey, default_text=filePath, size=fileLabelSize, visible=visible),
                       PySimpleGUI.FileSaveAs(initial_folder=default_folder, key=fileNameKey, default_extension=fileExtenstion)]]
        elif fileMode == 'Open':
            layout = [[PySimpleGUI.Text(str(title), size=titleSize)],
                      [PySimpleGUI.Input(key=fileNameLabelKey, default_text=filePath, size=fileLabelSize, visible=visible),
                       PySimpleGUI.FileBrowse(initial_folder=default_folder, file_types=(("ALL Files", "*" + fileExtenstion),), )]]
        else:
            raise Exception(f"Error in layout mode. {whoami()}")

        if returnLayout is True:
            return layout

        layout.insert(0, [PySimpleGUI.Menu(menu_def, tearoff=True)])
        layout.append([PySimpleGUI.Button(button_text='Select')])
        programLabel = ''.join(
            'Intel Labs Control Flag Interface for Rapid Automation-Analysis for Developers (RAAD), '
            'by Prof. Joseph Tarango, '
        )
        # Display collect form
        windowActive = PySimpleGUI.Window(programLabel, layout)
        (collect_button, collect_values) = windowActive.read()

        while collect_button not in ('Select', 'Exit', None):
            (collect_button, collect_values) = windowActive.read()

        # Confirmation Box
        PySimpleGUI.Popup(collect_button, collect_values)

        # Close window
        windowActive.close()

        if collect_button == 'Select' and fileMode == 'Save':
            if collect_values[fileNameKey] == '':
                returnFile = collect_values[fileNameLabelKey]
            else:
                returnFile = collect_values[fileNameKey]
        elif collect_button == 'Select' and fileMode == 'Open':
            if collect_values['Browse'] == '':
                returnFile = collect_values[fileNameLabelKey]
            else:
                returnFile = collect_values['Browse']
        else:
            returnFile = None
        return returnFile

    def GUI_Info(self,
                 returnLayout=False, charWidth=88, charHeight=4,
                 # Application Specific
                 version: str = VERSION,
                 description: str = DESCRIPTION,
                 epilog: str = EPILOG,
                 authors: str = AUTHORS,
                 visible: bool = True):
        """
        Layout construction for an independent mining control flag instances. Note Example Parameters: -t data/c_lang_if_stmts_6000_gitrepos.ts -o data/tmp_results_anomalies -l data/adp.ilcf -v 2.
        Args:
            returnLayout: Flag to return the flag or execute in independent mode.
            charWidth: Width of the text box.
            charHeight: Height of a given display box.
            version: Application development version.
            description: Description of the application
            epilog: Conclusion to what is expected to happen.
            authors: Program authors.
            visible: Display boxes.

        Returns: layout or input box information.
        """
        ###############################################################################
        # Graphical User Interface (GUI) Configuration
        ###############################################################################
        if (returnLayout is False):
            PySimpleGUI.ChangeLookAndFeel('LightBlue')
        menu_def = [['&File', ['&Open', '&Save', 'E&xit', 'Properties']],
                    ['&Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
                    ['&Help', '&About...'], ]
        ###############################################################################
        # Basic collect form.
        # Return values as a list.
        ###############################################################################

        descriptionSize = self._boxTraits(stringObject=description, maxWidth=charWidth, maxHeight=charHeight)
        epilogSize = self._boxTraits(stringObject=epilog, maxWidth=charWidth, maxHeight=charHeight)
        versionSize = self._boxTraits(stringObject=version, maxWidth=charWidth, maxHeight=charHeight)
        authorsSize = self._boxTraits(stringObject=authors, maxWidth=charWidth, maxHeight=charHeight)
        layout = [
            # Program context information
            [PySimpleGUI.Multiline(default_text=str(description),
                                   size=descriptionSize,
                                   autoscroll=True,
                                   do_not_clear=True,
                                   visible=visible, key='app_description')],
            [PySimpleGUI.Multiline(default_text=str(epilog),
                                   size=epilogSize,
                                   autoscroll=True,
                                   do_not_clear=True,
                                   visible=visible, key='app_epilog')],
            [PySimpleGUI.Text(str(version), size=versionSize, key='app_version')],
            [PySimpleGUI.Text(str(authors), size=authorsSize, key='app_authors')]
        ]

        if returnLayout is True:
            return layout

        layout.insert(0, [PySimpleGUI.Menu(menu_def, tearoff=True)])
        layout.append([PySimpleGUI.Cancel()])
        programLabel = ''.join(
            'Intel Labs Control Flag Interface for Rapid Automation-Analysis for Developers (RAAD), '
            'by Prof. Joseph Tarango, '
        )
        # Display collect form
        windowActive = PySimpleGUI.Window(programLabel, layout)
        (collect_button, collect_values) = windowActive.read()

        # Confirmation Box
        PySimpleGUI.Popup(collect_button, collect_values)

        # Close window
        windowActive.close()

        returnTuple = (None)
        return returnTuple

    def GUI_ThreadStatus(self,
                         returnLayout=False, charWidth=88, charHeight=4,
                         threadToken: str = 'ThreadToken',
                         threadKey: str = 'threadKey',
                         visible: bool = True):
        """
        Layout construction for an independent mining control flag instances. Note Example Parameters: -t data/c_lang_if_stmts_6000_gitrepos.ts -o data/tmp_results_anomalies -l data/adp.ilcf -v 2.
        Args:
            returnLayout: Flag to return the flag or execute in independent mode.
            charWidth: Width of the text box.
            charHeight: Height of a given display box.

            threadToken: String to fill in the field.
            threadKey: Dictionary key for token to be stored.
            visible: Display boxes.

        Returns: layout or input box information.
        """
        ###############################################################################
        # Graphical User Interface (GUI) Configuration
        ###############################################################################
        if (returnLayout is False):
            PySimpleGUI.ChangeLookAndFeel('LightBlue')
        menu_def = [['&File', ['&Open', '&Save', 'E&xit', 'Properties']],
                    ['&Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
                    ['&Help', '&About...'], ]
        ###############################################################################
        # Basic collect form.
        # Return values as a list.
        ###############################################################################

        threadTokenSize = self._boxTraits(stringObject=threadToken, maxWidth=charWidth, maxHeight=charHeight)
        layout = [
            # Thread state information
            [PySimpleGUI.Multiline(default_text=str(threadToken),
                                   size=threadTokenSize,
                                   autoscroll=True,
                                   do_not_clear=True,
                                   visible=visible, key=threadKey)]
        ]

        if returnLayout is True:
            return layout

        layout.insert(0, [PySimpleGUI.Menu(menu_def, tearoff=True)])
        layout.append([PySimpleGUI.Cancel()])
        programLabel = ''.join(
            'Intel Labs Control Flag Interface for Rapid Automation-Analysis for Developers (RAAD), '
            'by Prof. Joseph Tarango, '
        )
        # Display collect form
        windowActive = PySimpleGUI.Window(programLabel, layout)
        (collect_button, collect_values) = windowActive.read()

        # Confirmation Box
        PySimpleGUI.Popup(collect_button, collect_values)

        # Close window
        windowActive.close()

        returnTuple = (None)
        return returnTuple

    def GUI_Common(self,
                   returnLayout=False, charWidth=32, charHeight=1,
                   faultSave: bool = False,
                   debug: bool = False,
                   more: bool = False,
                   timeout: int = (60 * 60 * 24 * 2)):
        """
        Layout construction for an independent mining control flag instances. Note Example Parameters: -t data/c_lang_if_stmts_6000_gitrepos.ts -o data/tmp_results_anomalies -l data/adp.ilcf -v 2.
        Args:
            returnLayout: Flag to return the flag or execute in independent mode.
            charWidth: Width of the text box.
            charHeight: Height of a given display box.

            faultSave: Enable fault context save for debug.
            debug: Enable Debug mode.
            more: Displays more options.
            timeout: Amount of time in seconds before killing task. Default time is 60 seconds * 60 minutes * 24 hours * 2 = 2 days in seconds per thread

        Returns: layout or input box information.
        """

        """
        Main API flags used across control flag instances.
        Returns: parser object with common elements.
        """
        if debug:
            print(f"Debug mode with version {self.VERSION}.")

        if charWidth < 15:
            charWidth = 25
        if charHeight < 1:
            charHeight = 2

        ###############################################################################
        # Graphical User Interface (GUI) Configuration
        ###############################################################################
        if (returnLayout is False):
            PySimpleGUI.ChangeLookAndFeel('LightBlue')
        menu_def = [['&File', ['&Open', '&Save', 'E&xit', 'Properties']],
                    ['&Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
                    ['&Help', '&About...'], ]
        ###############################################################################
        # Basic collect form.
        # Return values as a list.
        ###############################################################################
        layout = [
            # Common
            [PySimpleGUI.Text('Interface common flags and tokens.')],
            [PySimpleGUI.Text('Enable context fault dump', size=(charWidth, charHeight), tooltip='Enable fault context save used in debug'),
             PySimpleGUI.InputCombo(('True', 'False'), default_value=str(faultSave), key='faultSave',
                                    size=(charWidth, charHeight))],
            [PySimpleGUI.Text('Enter debug mode', size=(charWidth, charHeight), tooltip='Enhanced context information for debugging source and program.'),
             PySimpleGUI.InputCombo(('True', 'False'), default_value=str(debug), key='debug',
                                    size=(charWidth, charHeight))],
            [PySimpleGUI.Text('Display more debug information', size=(charWidth, charHeight), tooltip='Enhanced context information for live source and program.'),
             PySimpleGUI.InputCombo(('True', 'False'), default_value=str(more), key='more',
                                    size=(charWidth, charHeight))],
            [PySimpleGUI.Text('Time out for each thread execution (seconds).', size=(charWidth, charHeight + 1), tooltip='Amount of time in seconds before killing task. Default time is 60 seconds * 60 minutes * 24 hours * 2 = 2 days in seconds per thread.'),
             PySimpleGUI.InputText(default_text=timeout, key='timeout')]
        ]
        if returnLayout is True:
            return layout

        layout.insert(0, [PySimpleGUI.Menu(menu_def, tearoff=True)])
        layout.append([PySimpleGUI.Submit(), PySimpleGUI.Cancel()])
        programLabel = ''.join(
            'Intel Labs Control Flag Interface for Rapid Automation-Analysis for Developers (RAAD), '
            'by Prof. Joseph Tarango, '
        )
        # Display collect form
        windowActive = PySimpleGUI.Window(programLabel, layout)
        (collect_button, collect_values) = windowActive.read()

        # Assign Collect form Values
        if collect_button == 'Submit':
            faultSave = collect_values['faultSave']
            debug = collect_values['debug']
            more = collect_values['more']
            timeout = collect_values['timeout']

        # Confirmation Box
        PySimpleGUI.Popup(collect_button, collect_values)

        # Close window
        windowActive.close()

        # Printing Selection
        if debug:
            print(f"Debug Collection information{os.linesep}{pprint.pformat(collect_button)}{os.linesep}{pprint.pformat(collect_values)}{os.linesep}")
        returnTuple = (faultSave, debug, more, timeout)
        return returnTuple

    def GUI_Mine(self,
                 returnLayout=False, charWidth=32, charHeight=1,
                 debug: bool = False,
                 # Mine
                 number_of_processes_to_use_for_mining: int = None,
                 directory_to_mine_patterns_from: str = '../../../../ADP/nand/gen3/src',
                 output_file_to_store_training_data: str = None,
                 output_directory_to_store_training_data: str = '../data/tmp_results_training',
                 tree_depth: int = 100):
        """
        Layout construction for an independent mining control flag instances. Note Example Parameters: -t data/c_lang_if_stmts_6000_gitrepos.ts -o data/tmp_results_anomalies -l data/adp.ilcf -v 2.
        Args:
            returnLayout: Flag to return the flag or execute in independent mode.
            charWidth: Width of the text box.
            charHeight: Height of a given display box.

            debug: debug status flag for printing more information.

            number_of_processes_to_use_for_mining: Total processes used in mining.
            directory_to_mine_patterns_from: Directory to mine patterns from.
            output_file_to_store_training_data: Save data store file.
            output_directory_to_store_training_data: Save data directory.
            tree_depth: Tree level, representing the tokenizing format.
                        LEVEL_MIN = 0,   // Basic Tree-sitter
                        LEVEL_ONE = 1,   // Same as MAX level. Diff is printing operators also.
                                         // Such as == or != in addition to binary_expression.
                        LEVEL_TWO = 2,   // EXPR := TERM BINARY_OP TERM | UNARY_OP TERM | *TERM | TERM | FCALL | VAR.VAR | VAR[TERM] | anything_else
                                         // TERM := VAR | CONST | anything_else
                        LEVEL_MAX = 3,   // (VAR), (CONST), (EXPR)

        Returns: layout or input box information.
        """

        """
        Main API flags used across control flag instances.
        Returns: parser object with common elements.
        """
        number_of_processes_to_use_for_mining = getAvailableCPUCount_Nice(requestedCores=number_of_processes_to_use_for_mining)

        if debug:
            print(f"Debug mode with version {self.VERSION}.")

        if charWidth < 15:
            charWidth = 25
        if charHeight < 1:
            charHeight = 1

        if output_directory_to_store_training_data is None:
            output_directory_to_store_training_data = os.getcwd()

        if output_file_to_store_training_data is None:
            output_file_to_store_training_data = getTempFileName(genFile=False, inDir=None, suffix='.ilsf')

        ###############################################################################
        # Graphical User Interface (GUI) Configuration
        ###############################################################################
        if (returnLayout is False):
            PySimpleGUI.ChangeLookAndFeel('LightBlue')
        menu_def = [['&File', ['&Open', '&Save', 'E&xit', 'Properties']],
                    ['&Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
                    ['&Help', '&About...'], ]
        ###############################################################################
        # Basic collect form.
        # Return values as a list.
        ###############################################################################
        layout = [
            # Mine
            [PySimpleGUI.Text('Interface for Mining information to create a training set.')],
            [PySimpleGUI.Text('Number of processes to use for mining', size=(charWidth, charHeight), tooltip='Total processes used in mining'),
             PySimpleGUI.InputText(default_text=number_of_processes_to_use_for_mining, key='number_of_processes_to_use_for_mining')],

            [PySimpleGUI.Text('Directory to mine patterns from', size=(charWidth, charHeight), auto_size_text=False, tooltip='Directory to mine training data from'),
             PySimpleGUI.InputText(default_text=directory_to_mine_patterns_from, key='directory_to_mine_patterns_from_default'),
             PySimpleGUI.FolderBrowse(initial_folder=os.path.abspath(directory_to_mine_patterns_from), key='directory_to_mine_patterns_from')],

            [PySimpleGUI.Text('Output file to store training data', size=(charWidth, charHeight), tooltip='Save data store file'),
             PySimpleGUI.InputText(default_text=output_file_to_store_training_data, key='output_file_to_store_training_data', )],

            [PySimpleGUI.Text('Output directory to store training data', size=(charWidth, charHeight), auto_size_text=False),
             PySimpleGUI.InputText(default_text=output_directory_to_store_training_data, key='output_directory_to_store_training_data_default'),
             PySimpleGUI.FolderBrowse(initial_folder=os.path.abspath(output_directory_to_store_training_data), key='output_directory_to_store_training_data')],

            # directory_to_mine_patterns_from
            [PySimpleGUI.Text('Tree level depth for analysis', size=(charWidth, charHeight), tooltip='Tree level, representing the tokenizing format.'),
             PySimpleGUI.InputText(default_text=tree_depth, key='tree_depth')]
        ]
        if returnLayout is True:
            return layout

        layout.insert(0, [PySimpleGUI.Menu(menu_def, tearoff=True)])
        layout.append([PySimpleGUI.Submit(), PySimpleGUI.Cancel()])
        programLabel = ''.join(
            'Intel Labs Control Flag Interface for Rapid Automation-Analysis for Developers (RAAD), '
            'by Prof. Joseph Tarango, '
        )
        # Display collect form
        windowActive = PySimpleGUI.Window(programLabel, layout)
        (collect_button, collect_values) = windowActive.read()

        # Assign Collect form Values
        if collect_button == 'Submit':
            number_of_processes_to_use_for_mining = collect_values['number_of_processes_to_use_for_mining']
            output_file_to_store_training_data = collect_values['output_file_to_store_training_data ']
            output_directory_to_store_training_data = collect_values['output_directory_to_store_training_data']
            tree_depth = collect_values['tree_depth']
        # Confirmation Box
        PySimpleGUI.Popup(collect_button, collect_values)

        # Close window
        windowActive.close()

        # Printing Selection
        if debug:
            print(f"Debug Collection information{os.linesep}{pprint.pformat(collect_button)}{os.linesep}{pprint.pformat(collect_values)}{os.linesep}")
        returnTuple = (number_of_processes_to_use_for_mining, output_file_to_store_training_data, output_directory_to_store_training_data, tree_depth)
        return returnTuple

    def GUI_Scan(self,
                 returnLayout=False, charWidth=32, charHeight=1,
                 debug: bool = False,
                 # Scan
                 training_data: str = '../data/c_lang_if_stmts_6000_gitrepos.ts',
                 directory_to_scan_for_anomalous_patterns: str = '../../../../ADP/nand/gen3/src',
                 max_cost_for_autocorrect: int = 2,
                 max_number_of_results_for_autocorrect: int = 5,
                 number_of_scanning_threads: int = None,
                 output_log_dir: str = '../data/tmp_results_anomalies',
                 anomaly_threshold: float = 5.0):
        """
        Layout construction for an independent Scanning for control flag instances. Note Example Parameters: -t data/c_lang_if_stmts_6000_gitrepos.ts -o data/tmp_results_anomalies -l data/adp.ilcf -v 2.
        Args:
            returnLayout: Flag to return the flag or execute in independent mode.
            charWidth: Width of the text box.
            charHeight: Height of a given display box.
            debug: debug print flag.
            training_data: str = '../data/c_lang_if_stmts_6000_gitrepos.ts',
            directory_to_scan_for_anomalous_patterns: Source directory to scan for anomalies.
            max_cost_for_autocorrect: Magnitude value used for auto corrections.
            max_number_of_results_for_autocorrect: total results for autocorrect.
            number_of_scanning_threads: total threads used in scanning.
            output_log_dir: output directory of control flag.
            anomaly_threshold: threshold for control flag to detect anomalies
        Returns: layout or input box information.
        """
        if charWidth < 15:
            charWidth = 25
        if charHeight < 1:
            charHeight = 1

        number_of_scanning_threads = getAvailableCPUCount_Nice(requestedCores=number_of_scanning_threads)

        ###############################################################################
        # Graphical User Interface (GUI) Configuration
        ###############################################################################
        if (returnLayout is False):
            PySimpleGUI.ChangeLookAndFeel('LightBlue')
        menu_def = [['&File', ['&Open', '&Save', 'E&xit', 'Properties']],
                    ['&Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
                    ['&Help', '&About...'], ]
        ###############################################################################
        # Basic collect form.
        # Return values as a list.
        ###############################################################################
        layout = [
            # Scan
            [PySimpleGUI.Text('Interface to scan a source directory with reference training set.')],
            [PySimpleGUI.Text('Training Data file', size=(charWidth, charHeight), tooltip='Training data file postfix'),
             PySimpleGUI.InputText(default_text=training_data, key='training_data')],
            [PySimpleGUI.Text('Directory to scan for anomalous patterns', size=(charWidth, charHeight + 1), auto_size_text=False, tooltip='Source directory to scan for anomalies'),
             PySimpleGUI.InputText(default_text=directory_to_scan_for_anomalous_patterns, key='directory_to_scan_for_anomalous_patterns_default'),
             PySimpleGUI.FolderBrowse(initial_folder=os.path.abspath(directory_to_scan_for_anomalous_patterns), key='directory_to_scan_for_anomalous_patterns')],
            [PySimpleGUI.Text('Max cost for autocorrect', size=(charWidth, charHeight), tooltip='Magnitude value used for auto corrections.'),
             PySimpleGUI.InputText(default_text=max_cost_for_autocorrect, key='max_cost_for_autocorrect')],
            [PySimpleGUI.Text('Max Number of results for autocorrect', size=(charWidth, charHeight), tooltip='Total results for autocorrect'),
             PySimpleGUI.InputText(default_text=max_number_of_results_for_autocorrect, key='max_number_of_results_for_autocorrect')],
            [PySimpleGUI.Text('Number of processes to use for scanning', size=(charWidth, charHeight + 1), tooltip='Total threads used in scanning'),
             PySimpleGUI.InputText(default_text=number_of_scanning_threads, key='number_of_scanning_threads')],
            [PySimpleGUI.Text('Output directory to store anomalous data', size=(charWidth, charHeight + 1), auto_size_text=False),
             PySimpleGUI.InputText(default_text=output_log_dir, key='output_log_dir_default'),
             PySimpleGUI.FolderBrowse(initial_folder=os.path.abspath(output_log_dir), key='output_log_dir')],
            [PySimpleGUI.Text('Anomaly threshold', size=(charWidth, charHeight), tooltip='Threshold for control flag to detect anomalies'),
             PySimpleGUI.InputText(default_text=anomaly_threshold, key='anomaly_threshold')]
        ]
        if returnLayout is True:
            return layout

        layout.insert(0, [PySimpleGUI.Menu(menu_def, tearoff=True)])
        layout.append([PySimpleGUI.Submit(), PySimpleGUI.Cancel()])
        programLabel = ''.join(
            'Intel Labs Control Flag Interface for Rapid Automation-Analysis for Developers (RAAD), '
            'by Prof. Joseph Tarango, '
        )
        # Display collect form
        windowActive = PySimpleGUI.Window(programLabel, layout)
        (collect_button, collect_values) = windowActive.read()

        # Assign Collect form Values
        if collect_button == 'Submit':
            training_data = collect_values['training_data']
            directory_to_scan_for_anomalous_patterns = collect_values['directory_to_scan_for_anomalous_patterns']
            max_cost_for_autocorrect = collect_values['max_cost_for_autocorrect']
            max_number_of_results_for_autocorrect = collect_values['max_number_of_results_for_autocorrect']
            number_of_scanning_threads = collect_values['number_of_scanning_threads']
            output_log_dir = collect_values['output_log_dir']
            anomaly_threshold = collect_values['anomaly_threshold']

        # Confirmation Box
        PySimpleGUI.Popup(collect_button, collect_values)

        # Close window
        windowActive.close()

        # Printing Selection
        if debug:
            print(f"Debug Collection information{os.linesep}{pprint.pformat(collect_button)}{os.linesep}{pprint.pformat(collect_values)}{os.linesep}")
        returnTuple = (training_data, directory_to_scan_for_anomalous_patterns, max_cost_for_autocorrect, max_number_of_results_for_autocorrect, number_of_scanning_threads, output_log_dir, anomaly_threshold)
        return returnTuple

    @staticmethod
    def debugComments(returnLayout=False, displayInput=None, charWidth=93, charHeight=26, visible=True, keyName="debugComments"):
        """
        Layout construction for an independent comments.
        Args:
            returnLayout: Flag to return the flag or execute in independent mode.
            displayInput: Strings variables to Display.
            charWidth: Width of the text box.
            charHeight: Height of a given display box.
            visible: Visibility of the given object.
            keyName: Debug key to update tokens.
        Returns: layout or input box information.
        """
        if charWidth < 15:
            charWidth = 25
        if charHeight < 1:
            charHeight = 1
        ###############################################################################
        # Graphical User Interface (GUI) Configuration
        ###############################################################################
        if returnLayout is False:
            PySimpleGUI.ChangeLookAndFeel('LightBlue')
        menu_def = [['&File', ['&Open', '&Save', 'E&xit', 'Properties']],
                    ['&Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
                    ['&Help', '&About...'], ]
        ###############################################################################
        # Basic User feedback form.
        # Return values as a list.
        ###############################################################################
        layout = [[PySimpleGUI.Text(keyName, visible=visible)],
                  [PySimpleGUI.Multiline(default_text=str(displayInput),
                                         size=(charWidth, charHeight),
                                         autoscroll=True,
                                         do_not_clear=True,
                                         visible=visible,
                                         key=keyName)],
                  ]

        if returnLayout is True:
            return layout

        layout.insert(0, [PySimpleGUI.Menu(menu_def, tearoff=True)])
        layout.append([PySimpleGUI.Submit(), PySimpleGUI.Cancel()])
        programLabel = ''.join(
            'Rapid Automation-Analysis for Developers (RAAD), '
            'by Prof. Joseph Tarango, '
        )

        # Display collect form
        windowActiveFeedback = PySimpleGUI.Window(programLabel, layout)
        (layout_button, layout_values) = windowActiveFeedback.read()

        # Close window
        windowActiveFeedback.close()

        # Printing Selection
        print(layout_button, layout_values)

        return None

    def GUI_UpdateTime(self, windowActive):
        """
        Pull current time stamp into desired format.
        Args:
            windowActive: Current display values to user.

        Returns:

        """
        windowActive.Element('currentTime').Update(getTimeStampNow())
        return

    def _GUI_Mine(self, collect_values, windowActive):
        """
        Control flag Scan reading collected values, prepare input parameters, then perform a code mine training set of anomalies, then set event when complete to handle thread lock.
        Args:
            collect_values: Collected values from tabbed graphical interface.
            windowActive: Displayed values in graphical window.

        Returns: None

        """
        # Overwrite meta data if user is not filling input to use actively displayed default.
        if collect_values['output_file_to_store_training_data'] == '':
            collect_values['output_file_to_store_training_data'] = collect_values['output_file_to_store_training_data_default']
        if collect_values['directory_to_scan_for_anomalous_patterns'] == '':
            collect_values['directory_to_scan_for_anomalous_patterns'] = collect_values['directory_to_scan_for_anomalous_patterns_default']
        collect_values['mode'] = 'Mine'  # Set API mode for mining.
        parser = self.API_Tokenize_Common(defaults=collect_values)
        parser = self.API_MineMeta_Tokenize(parser=parser, defaults=collect_values)
        options = self.API_Tokenize(parser=parser)
        statusCode = self.API_MineMeta_Do(options=options)
        eventMessage = f'Mine thread status is: thread execution complete at {getTimeStampNow()} with status code {str(statusCode)}\n'
        windowActive.write_event_value('THREAD-MINE', eventMessage)  # Put a message into queue for GUI
        # windowActive.Element('mineThreadActive').Update(eventMessage)
        return

    def _GUI_Scan(self, collect_values, windowActive):
        """
        Control flag Scan reading collected values, prepare input parameters, then perform a code scan for anomalies, then set event when complete to handle thread lock.
        Args:
            collect_values: Collected values from tabbed graphical interface.
            windowActive: Displayed values in graphical window.

        Returns: None

        """
        # Overwrite data if user is not filling input to use actively displayed default.
        if collect_values['output_log_dir'] == '':
            collect_values['output_log_dir'] = collect_values['output_log_dir_default']
        if collect_values['directory_to_mine_patterns_from'] == '':
            collect_values['directory_to_mine_patterns_from'] = collect_values['directory_to_mine_patterns_from_default']
        collect_values['mode'] = 'Scan'  # Set API for scanning.
        parser = self.API_Tokenize_Common(defaults=collect_values)
        parser = self.API_ScanForAnomalies_Tokenize(parser=parser, defaults=collect_values)
        options = self.API_Tokenize(parser=parser)
        statusCode = self.API_ScanForAnomalies_Do(options=options)
        eventMessage = f'Scan thread status is: thread execution complete at {getTimeStampNow()} with status code {str(statusCode)}\n'
        windowActive.write_event_value('THREAD-SCAN', eventMessage)  # Put a message into queue for GUI
        return

    @staticmethod
    def _GUI_load_settings(settings_file=None):
        """
        Load a settings file into a settings structure.
        Args:
            settings_file: String file full location, name, and extension of a configuration file.

        Returns: Configuration file data object.

        """
        settings = None
        if settings_file is None and settings_file == '':
            settings_file = os.path.join(os.path.dirname(__file__), r'ControlFlag_Settings.cfg')
        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)
        except Exception as e:
            PySimpleGUI.popup_quick_message(f'Exception {e}', 'Settings file is not found or is invalid.', keep_on_top=True, background_color='red', text_color='white')
        return settings

    @staticmethod
    def _GUI_save_settings(settings_file: str = None, settings: dict = None):
        """
        Save a settings into a file.
        Args:
            settings_file: String file full location, name, and extension of a configuration file.
            settings: settings input data structure.

        Returns:

        """
        if settings_file is None or settings_file == '':
            settings_file = os.path.join(os.path.dirname(__file__), r'ControlFlag_Settings.cfg')
        with open(settings_file, 'w') as f:
            json.dump(obj=settings, fp=f, indent=4, sort_keys=True)
        PySimpleGUI.popup('Settings saved')
        return

    def GUI(self, debug: bool = False):
        """
        Grapical tabbed interface using threading to call subprocesses for control flag.
        Args:
            debug: Boolean flag for debug information of GUI.

        Returns: None.
        """
        statusCode = -1

        ##############################################################################
        # Graphical User Interface (GUI) Configuration
        ###############################################################################
        PySimpleGUI.ChangeLookAndFeel('LightBlue')
        menu_def = [['&File', ['&Open', '&Save', 'E&xit']]]
        programLabel = ''.join(
            'Intel Labs Control Flag for Rapid Automation-Analysis for Developers (RAAD), '
            'by Prof. Joseph Tarango, '
        )
        ###############################################################################
        # Basic collect form.
        # Return values as a list.
        ###############################################################################
        layoutInfo = self.GUI_Info(returnLayout=True)
        # Current Time
        layoutCurrentTime = self.GUI_ThreadStatus(returnLayout=True, threadToken=getTimeStampNow(), threadKey='currentTime')
        # Inputs
        layoutCommon = self.GUI_Common(returnLayout=True)
        # Inputs/Task
        layoutMine = self.GUI_Mine(returnLayout=True)
        layoutScan = self.GUI_Scan(returnLayout=True)
        # Status
        layoutMineThread = self.GUI_ThreadStatus(returnLayout=True, threadToken='Mine thread status is: waiting for inputs', threadKey='mineThreadActive')
        layoutScanThread = self.GUI_ThreadStatus(returnLayout=True, threadToken='Scan thread status is: waiting for inputs', threadKey='scanThreadActive')
        layoutInfoMine = self.debugComments(returnLayout=True, displayInput=self.output_mine, charWidth=88, charHeight=4, keyName='outputMine', visible=True)
        layoutInfoScan = self.debugComments(returnLayout=True, displayInput=self.output_scan, charWidth=88, charHeight=4, keyName='outputScan', visible=True)

        layout = [
            [PySimpleGUI.Menu(menu_def, size=(len(programLabel[0]), len(programLabel)), tearoff=True,
                              key='menuOptions')],
            [PySimpleGUI.TabGroup([[
                PySimpleGUI.Tab('App-Control_Flag-Info', layoutInfo, key='App-Control_Flag-Info', tooltip='Application context.')
            ]], key='dataProfile')],
            [PySimpleGUI.TabGroup([[
                PySimpleGUI.Tab('Current-Time', layoutCurrentTime, key='CurrentTime-Info', tooltip='Current Time.')
            ]], key='dataCurrentTime')],
            [PySimpleGUI.TabGroup([[
                PySimpleGUI.Tab('Mine-Thread', layoutMineThread, key='Mine-Thread', tooltip='Mine thread status.'),
                PySimpleGUI.Tab('Mine-Output', layoutInfoMine, key='Mine-Output', tooltip='Application context output mine.'),
                PySimpleGUI.Tab('Scan-Thread', layoutScanThread, key='Scan-Thread', tooltip='Scan thread status.'),
                PySimpleGUI.Tab('Scan-Output', layoutInfoScan, key='Scan-Output', tooltip='Application context output scan.'),
            ]], key='dataThread')],
            [PySimpleGUI.TabGroup([[
                PySimpleGUI.Tab('Inputs-Common', layoutCommon, key='Inputs-Common', tooltip="Common flags for applications."),
                PySimpleGUI.Tab('Inputs-Mine', layoutMine, key='Inputs-Mine', tooltip='Mine training data from repository.'),
                PySimpleGUI.Tab('Inputs-Scan', layoutScan, key='Inputs-Scan', tooltip='Scan source repository with training set.')
            ]], key='dataInfoExtract')],
            [PySimpleGUI.Button('Mine', button_color=('white', 'blue')),
             PySimpleGUI.Button('Scan', button_color=('white', 'green')),
             PySimpleGUI.Button('Inspect', button_color=('grey', 'black')),
             PySimpleGUI.Button('Exit', button_color=('black', 'white'))
             ]
        ]

        if debug:
            debugLocal = pprint.pformat(locals(), indent=3, width=100)
            debugGlobals = pprint.pformat(globals(), indent=3, width=100)
            layoutDebugLocalsInfo = self.debugComments(returnLayout=True, displayInput=debugLocal, charWidth=75, charHeight=8, keyName='debugLocals', visible=debug)
            layoutDebugGlobalsInfo = self.debugComments(returnLayout=True, displayInput=debugGlobals, charWidth=75, charHeight=8, keyName='debugGlobals', visible=debug)
            layout.append([PySimpleGUI.TabGroup([[PySimpleGUI.Tab('Debug-Locals', layoutDebugLocalsInfo, key='debugLocalsTab'),
                                                  PySimpleGUI.Tab('Debug-Globals', layoutDebugGlobalsInfo, key='debugGlobalsTab')]],
                                                key='debugInfo'
                                                )])

        # Display collect form
        windowActive = PySimpleGUI.Window(title=programLabel, layout=layout,
                                          grab_anywhere=True, finalize=True)

        validLoadKeys = ["faultSave",
                         "debug",
                         "more",
                         "timeout",
                         "number_of_processes_to_use_for_mining",
                         "directory_to_mine_patterns_from",
                         "directory_to_mine_patterns_from_default",
                         "output_file_to_store_training_data",
                         "output_directory_to_store_training_data_default",
                         "output_directory_to_store_training_data",
                         "tree_depth",
                         "training_data",
                         "directory_to_scan_for_anomalous_patterns_default",
                         "directory_to_scan_for_anomalous_patterns",
                         "max_cost_for_autocorrect",
                         "max_number_of_results_for_autocorrect",
                         "number_of_scanning_threads",
                         "output_log_dir_default",
                         "output_log_dir",
                         "anomaly_threshold"]

        continueRun = True
        collect_button = 'Run'
        collect_values = None
        threadMine = None
        threadScan = None
        while (continueRun):
            (collect_button, collect_values) = windowActive.read(timeout=2047)
            if collect_button in (PySimpleGUI.WIN_CLOSED, 'Exit', None):
                continueRun = False
                break

            # Assign Collect form Values
            if collect_button == 'Save':
                fileSave = self.GUI_FileLoadSave(
                    returnLayout=False,
                    fileMode=collect_button,
                    title="Save Application Configuration",
                    default_folder='..',
                    fileNameLabelKey='File save name',
                    fileNameKey='FileNameKey_Save',
                    fileNameToken='ControlFlag_Settings')
                self._GUI_save_settings(settings_file=fileSave, settings=collect_values)
                del fileSave
            elif collect_button == 'Open':
                fileLoad = self.GUI_FileLoadSave(
                    returnLayout=False,
                    fileMode=collect_button,
                    title="Load Application Configuration",
                    default_folder='..',
                    fileNameLabelKey='File load name',
                    fileNameKey='FileNameKey_Load',
                    fileNameToken='ControlFlag_Settings')
                newLoadSettings = self._GUI_load_settings(settings_file=fileLoad)
                if newLoadSettings is not None:
                    for loadSettingsKey, loadSettingsValue in newLoadSettings.items():
                        loadInAppContext = loadSettingsKey in collect_values
                        loadInAppValidContext = loadSettingsKey in validLoadKeys
                        if loadInAppContext and loadInAppValidContext:
                            collect_values[loadSettingsKey] = newLoadSettings[loadSettingsKey]
                            windowActive.Element(loadSettingsKey).Update(newLoadSettings[loadSettingsKey])
                del fileLoad, newLoadSettings
            elif collect_button == 'Mine':
                mineThreadInActive = (collect_values['mineThreadActive'] == 'Mine thread status is: waiting for inputs\n')
                if mineThreadInActive:
                    if debug:
                        print("[NOTICE] Starting Mine thread(s)...")
                    threadMine = WorkerThread(target=self._GUI_Mine, kwargs={'collect_values': collect_values, 'windowActive': windowActive})
                    threadMine.start()  # thread.join()
                    windowActive.Element('mineThreadActive').Update('Mine thread status is: running')
            elif collect_button == 'Scan':
                if debug:
                    print("[NOTICE] Starting Scan thread(s)...")
                scanThreadInActive = (collect_values['scanThreadActive'] == 'Scan thread status is: waiting for inputs\n')
                if scanThreadInActive:
                    threadScan = WorkerThread(target=self._GUI_Scan, kwargs={"collect_values": collect_values, "windowActive": windowActive})
                    threadScan.start()  # thread.join()
                    windowActive.Element('scanThreadActive').Update('Scan thread status is: running')
            elif collect_button == 'THREAD-MINE':
                windowActive.Element('mineThreadActive').Update('Mine thread status is: waiting for inputs')
                mineReturn = threadMine.get_results()
                if mineReturn is None:
                    mineReturn = "Nil"
                else:
                    mineReturn = pprint.pformat(mineReturn)
                stringMineReturn = str(f"[{getTimeStampNow()}] " + self.output_mine + f"{os.linesep}Thread results:{os.linesep}" + mineReturn + f"{os.linesep}" + collect_values['THREAD-MINE'])
                windowActive.Element('outputMine').Update(stringMineReturn)
                del stringMineReturn, mineReturn
            elif collect_button == 'THREAD-SCAN':
                windowActive.Element('scanThreadActive').Update('Scan thread status is: waiting for inputs')
                scanReturn = threadScan.get_results()
                if scanReturn is None:
                    scanReturn = "Nil"
                else:
                    scanReturn = pprint.pformat(scanReturn)
                stringScanReturn = str(f"[{getTimeStampNow()}] " + self.output_scan + f"{os.linesep}Thread results:{os.linesep}" + scanReturn + f"{os.linesep}" + collect_values['THREAD-SCAN'])
                windowActive.Element('outputScan').Update(stringScanReturn)
                del stringScanReturn, scanReturn
            elif collect_button == 'Inspect':
                # Confirmation Box
                PySimpleGUI.PopupScrolled(pprint.pformat(collect_button, indent=3, width=100),
                                          pprint.pformat(collect_values, indent=3, width=100),
                                          size=(128, 32))
                if debug:
                    print(f"Status code: {statusCode}{os.linesep}")
                    collect_values['debugLocals'] = debugLocal = pprint.pformat(locals(), indent=3, width=100)
                    collect_values['debugGlobals'] = debugGlobal = pprint.pformat(globals(), indent=3, width=100)
                    PySimpleGUI.show_debugger_popout_window()
            else:
                # Display Current Time
                windowActive.Element('currentTime').Update(getTimeStampNow())

        # Close window
        PySimpleGUI.PopupAutoClose("Exiting all jobs.", auto_close_duration=0.001)
        windowActive.close()
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
        ILCF = ILControlFlag()
        # statusCode_Mine = ILCF.API_MineMeta_Execute()
        # statusCode = statusCode_Mine
        # statusCode_Scan = ILCF.API_ScanForAnomalies_Execute()
        # statusCode = statusCode_Scan
        ILCF.GUI()
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
    mainFaultContext()
    q = datetime.datetime.now()
    print("Execution time: " + str(q - p))
