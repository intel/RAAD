#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Brad McDonald, Mejbah ul Alam, Justin Gottschlich, Abdullah Muzahid
# *****************************************************************************/
"""utils.py

This file contains some utility function for data access, analyze, and
visualization.
"""

from __future__ import division, annotations

import os, shutil, git, errno, contextlib, numpy, subprocess, time, sys, pprint, tqdm
from typing import Tuple, Union

from string import Formatter
from collections import Mapping
from io import StringIO


class MagicFormatMapping(Mapping):
    """This class implements a dummy wrapper to fix a bug in the Python
    standard library for string formatting.
    See http://bugs.python.org/issue13598 for information about why
    this is necessary.
    """

    def __init__(self, args, kwargs):
        self._args = args
        self._kwargs = kwargs
        self._last_index = 0

    def __getitem__(self, key):
        if key == '':
            idx = self._last_index
            self._last_index += 1
            try:
                return self._args[idx]
            except LookupError:
                pass
            key = str(idx)
        return self._kwargs[key]

    def __iter__(self):
        return iter(self._kwargs)

    def __len__(self):
        return len(self._kwargs)


class SafeFormatter(Formatter):

    def get_field(self, field_name, args, kwargs):
        # This is a necessary API but it's undocumented and moved around between Python releases
        try:
            from _string import formatter_field_name_split
        except ImportError:
            formatter_field_name_split = lambda x: x._formatter_field_name_split()
        first, rest = formatter_field_name_split(field_name)
        obj = self.get_value(first, args, kwargs)
        for is_attr, i in rest:
            if is_attr:
                obj = safe_getattr(obj, i)
            else:
                obj = obj[i]
        return obj, first


def safe_getattr(obj, attr):
    # Expand the logic Python 3 will also need to hide
    # things like cr_frame and others.  Ideally have a list of
    # objects that are entirely unsafe to access.
    if attr[:1] == '_':
        raise AttributeError(attr)
    return getattr(obj, attr)


def safe_format(_string, *args, **kwargs):
    formatter = SafeFormatter()
    kwargs = MagicFormatMapping(args, kwargs)
    return formatter.vformat(_string, args, kwargs)


def getAllDirectories(dirPath):
    paths = list()
    paths.append(dirPath)
    for path in os.listdir(dirPath):
        rpath = os.path.join(dirPath, path)
        if os.path.isdir(rpath):
            subdirs = getAllDirectories(dirPath=rpath)
            if not subdirs == []:
                paths.extend(subdirs)
    return paths


def findFolder(dirSignature='.autoperf', dirPath=None):
    if dirPath is None:
        dirPath = os.getcwd()
    allPaths = getAllDirectories(dirPath)
    matchPathList = list()
    for pathItem in allPaths:
        matchItem = dirSignature in pathItem
        if matchItem:
            matchPath = os.path.abspath(pathItem)
            matchPathList.append(matchPath)
    return matchPathList


def mkdir_p(path: str):
    """Recursively makes a directory by also creating all intermediate dirs.

    Args:
        path: Directory path to create.
    """
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def compareDataset(datasetArrayBase: numpy.ndarray, datasetArray: numpy.ndarray) -> Union[float, numpy.ndarray]:
    """Compares the mean values between two datasets.

    Args:
        datasetArrayBase: Original data.
        datasetArray: New data.

    Returns:
        L2 norm of the differences between the input array means.

    """
    meanBase = numpy.mean(datasetArrayBase, axis=0)
    meanComp = numpy.mean(datasetArray, axis=0)

    diffVal = numpy.linalg.norm(meanBase - meanComp)
    return diffVal


def getPerfCounterData(counterId: str, dataDir: str, scale: float) -> Tuple[list, str]:
    """Get the performance counter from the 3rd column of the CSV data file.

    Args:
        counterId: The performance counter name / ID.
        dataDir: The parent folder of the performance counter data.
        scale: Scale factor post-normalization. Accessed via `cfg.training.scale_factor`.

    Returns:
        A list of normalized performance counter results.
        The counter's header.
    """
    filename = dataDir + "/event_" + counterId + "_perf_data.csv"
    perfCounter = []
    with open(filename, 'r') as fp:
        for linenumber, line in enumerate(fp):
            if linenumber == 2:
                headers = line.strip().split(
                    ",")  # last one is the counter, 1 and 2  is thd id and instcouunt , 0 is mark id
                datasetHeader = headers[-1]
            if linenumber > 2:
                perfCounters = line.strip().split(",")
                # mark = int(perfCounters[0])  # unused
                # threadCount = int(perfCounters[1])  # unused
                instructionCount = int(perfCounters[2])
                currCounter = int(perfCounters[3])
                normalizedCounter = (currCounter / instructionCount) * scale
                perfCounter.append(normalizedCounter)

    return perfCounter, datasetHeader


def getAutoperfDir(directory: str = None, repoDirectory: str = None) -> str:
    """Retrieves the full path to the repository's .autoperf directory.

    Args:
        directory: Path within the .autoperf dir.
        repoDirectory: repository directory
    Returns:
        str: Path to .autoperf
    """
    isRepoDirDefault = (repoDirectory is None)
    repoDirExists = os.path.exists(repoDirectory) if (False is isRepoDirDefault) else False
    if repoDirExists:
        repo = git.Repo(repoDirectory, search_parent_directories=False)
    else:
        repo = git.Repo(os.getcwd(), search_parent_directories=False)
    if directory:
        foundConfigPath = os.path.join(repo.working_tree_dir, '.autoperf', directory)
    else:
        foundConfigPath = os.path.join(repo.working_tree_dir, '.autoperf')
    return foundConfigPath


@contextlib.contextmanager
def set_working_directory(directory: str) -> str:
    """Temporarily cd into the working directory. After context is closed (e.g. the
    function is exited), returns to the previous working directory.

    Args:
        directory: Path to change to.

    Yields:
        New working directory.
    """
    owd = os.getcwd()
    try:
        os.chdir(directory)
        yield directory
    finally:
        os.chdir(owd)
    return


def callCommand(cmd=None, cwd=None, env=None, stdout=None, stderr=None,
                shell: bool = False,
                attempts: int = 4,
                waitTimeBetweenCalls: float = 0.001,
                debugLimit: int = 2):
    """
    Subprocess command caller.

    Args:
        cmd: string command broken into a list with command and list of args.
        cwd: Current working directory.
        env: environment to use for command execution.
        stdout: Standard IO stream redirection.
        stderr: Standard Error IO stream redirection.
        shell: Execute process in this shell or its own shell.
        attempts: Attempts to retry command before failing
        waitTimeBetweenCalls: Float wait value of wait time in seconds.
        debugLimit: Boolean value of debug redirection to switch to standard pipes.
    """
    errorStr: str = ''

    # Verify inputs, if error return early then assign defaults

    emptyArgs = not any(map(None.__ne__, [cmd, cwd, env, stdout, stderr]))
    if (cmd is None) or emptyArgs:
        return errorStr
    if cwd is None:
        cwd = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
    if env is None:
        env = os.environ.copy()
    if stdout is None:
        stdout = subprocess.PIPE
    if stderr is None:
        stderr = subprocess.PIPE
    runShell = shell

    # Handle incorrect inputs for attempts
    if attempts <= 2:
        attemptMax: int = 2
    else:
        attemptMax = attempts
    localDebugLimit = min(attemptMax, debugLimit, 2)
    localDebugLimit = max(localDebugLimit, 2)

    attemptCount: int = 0
    exceptionOccurred: bool = True

    while (exceptionOccurred is True) and (attemptCount < attemptMax):
        attemptCount += 1
        cmdSplit = cmd.split(' ')
        if attemptCount > localDebugLimit:
            p = subprocess.Popen(cmdSplit,
                                 cwd=cwd,
                                 env=env,
                                 shell=runShell,
                                 stdout=stdout,
                                 stderr=stderr)
        else:
            # Enable additional execution to pipe to command prompt.
            p = subprocess.Popen(cmdSplit,
                                 cwd=cwd,
                                 env=env,
                                 shell=runShell,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

        try:
            processWaitToken = p.wait()
            stdoutMeta, stderrMeta = p.communicate()
            processTokenFail = (processWaitToken != 0)
            if processTokenFail:
                errorStrPostfix = f'[ERROR] Command attempt={attemptCount} of {attemptMax}: status failed. ' \
                                  f'env={pprint.pformat(env)}{os.linesep}' \
                                  f'cmd={cmd}{os.linesep}' \
                                  f'shell={runShell}{os.linesep}' \
                                  f'stdout={stdoutMeta}{os.linesep}' \
                                  f'stderr={stderrMeta}{os.linesep}' \
                                  f'retcode={p.returncode}'
                # Append errors to string with two new lines between calls
                errorStr = f'{errorStr}{os.linesep}{os.linesep}{errorStrPostfix}'
                exceptionOccurred = True
                runShell = not runShell  # Production toggle back and forth between same thread its own process shell.
                if float(waitTimeBetweenCalls) != float(0.0):
                    time.sleep(waitTimeBetweenCalls)
            else:
                exceptionOccurred = False
                break
        except BaseException as errorContext:
            errorStr = f'{errorStr}{os.linesep}' \
                       f'[ERROR] Exception is {pprint.pformat(errorContext)}'
            exceptionOccurred = True
            runShell = not runShell  # Production Toggle back and forth between same thread its own process shell.
            p.kill()
    return errorStr


def git_getAllBranchesStatic(targetDirectory=None, remoteCandidate=None, debug=False):
    """
    Git repo manager branch retriever with match to candidate

    Args:
        targetDirectory: Directory of cloned repository.
        remoteCandidate: Remote branch name to match.
        debug: Flag to enable developer debugging.
    """
    # Note: replicates git branch -a with substring matching.
    # Execute from the repository root directory
    if targetDirectory is None:
        return None
    if os.path.exists(targetDirectory):
        try:
            repo = git.Repo(targetDirectory)
        except BaseException as errorContext:
            print(f"[ERROR] {errorContext}", file=sys.stderr)
            return None
    else:
        return None
    remote_refs = repo.remote().refs
    allBranches = list()
    if debug:
        print(f"Repo Path: {targetDirectory}{os.pathsep}")
    rIndex = 0
    baseRemoteCount = 0
    baseRemoteName = None
    remoteCandidateFull = None
    for refs in remote_refs:
        allBranches.append(refs.name)
        remoteString = str(refs.name)
        if remoteString.endswith(str(repo.head.ref)):
            baseRemoteCount = baseRemoteCount + 1
            baseRemoteName = remoteString
            if debug:
                print(f"  Branch Head Name [{rIndex}]: {refs.name}, {baseRemoteName}{os.pathsep}")
        if remoteCandidate is not None:
            if remoteString.endswith(str(remoteCandidate)):
                remoteCandidateFull = remoteString
                if debug:
                    print(f"  Branch Candidate name[{rIndex}]: {remoteCandidateFull}, {os.pathsep}")
        rIndex = rIndex + 1
    if baseRemoteCount > 1:
        print(f" Found more than one match to base name. Matches are {baseRemoteCount}")
    return baseRemoteName, remoteCandidateFull


class CloneProgress(git.RemoteProgress):
    def __init__(self):
        super().__init__()
        self.pbar = tqdm.tqdm()

    def update(self, op_code, cur_count, max_count=None, message=''):
        self.pbar.total = max_count
        self.pbar.n = cur_count
        self.pbar.refresh()


class GitOperations(object):
    def __init__(self,
                 targetPath: str = "test",
                 targetDirectoryName: str = "CPUBenchmark",
                 remote_url: str = "git@github.com:jtarango/CPUBenchmark.git",
                 debug: bool = False):
        self.debug = debug
        # Target path and directory
        self.targetPath = targetPath
        self.targetDirectoryName = targetDirectoryName
        # Remote URL to clone. URL looks "git@github.com:jtarango/CPUBenchmark.git"
        self.remote_url = remote_url  # Note: if you already connected with server you do not need to give any credentials
        self.allBranches = list()  # List of all branches
        if not os.path.exists(self.targetPath):
            os.makedirs(self.targetPath, exist_ok=True)
        if self.debug:
            print(f"Target path is: {self.targetPath}")
        self.targetDirectory = os.path.join(self.targetPath, self.targetDirectoryName)

        self.defaultNames = ['origin', 'master', 'main']
        self.baseRemoteName = None
        return

    def git_currentRemoteHead(self):
        if os.path.exists(self.targetDirectory):
            repo = git.Repo(self.targetDirectory)
        else:
            repo = git.Repo(self.remote_url)
        remote = repo.head.ref
        return remote

    def git_getAllBranches(self):
        # git branch -a
        # Execute from the repository root directory
        if os.path.exists(self.targetDirectory):
            repo = git.Repo(self.targetDirectory)
        else:
            repo = git.Repo(self.remote_url)
        remote_refs = repo.remote().refs
        self.allBranches = list()
        if self.debug:
            print(f"Repo access: {self.remote_url}{os.pathsep}"
                  f" Path: {self.targetDirectory}{os.pathsep}")
        rIndex = 0
        baseRemoteCount = 0
        for refs in remote_refs:
            self.allBranches.append(refs.name)
            remoteString = str(refs.name)
            if remoteString.endswith(str(repo.head.ref)):
                baseRemoteCount = baseRemoteCount + 1
                self.baseRemoteName = repo.head.ref
            if self.debug:
                print(f"  Branch name[{rIndex}]: {refs.name}{os.pathsep}")
            rIndex = rIndex + 1
        if baseRemoteCount > 1:
            print(f" Found more than one match to base name. Matches are {baseRemoteCount}")
        return

    def git_push_allfiles(self, remoteBranch: str = 'origin', mainBranch: str = 'main'):
        import git
        statusFlag = False
        try:
            repo = git.Repo(self.targetDirectory)
            commit_message = 'Automation Work in Progress Changeset'
            # repo.index.add(u=True)
            repo.git.add('--all')
            repo.index.commit(commit_message)
            origin = repo.remote(remoteBranch)
            origin.push(mainBranch)
            repo.git.add(update=True)
            if self.debug:
                print(f"Repo push successfully for {self.targetDirectory}")
            statusFlag = True
        except Exception as e:
            print(str(e))
        return statusFlag

    def _setupCloner(self, branchName=None):
        try:
            if branchName is None:
                self.baseRemoteName = self.git_currentRemoteHead()
            if os.path.isdir(self.targetDirectory):
                shutil.rmtree(self.targetDirectory)
            os.makedirs(self.targetDirectory, exist_ok=True)
        except Exception as e:
            print(str(e))
            pass
        return

    def git_clone(self, branchName=None):
        self._setupCloner(branchName=branchName)
        branchName = self.baseRemoteName
        statusFlag = False
        try:
            repoSelected = git.Repo.init(self.targetDirectory)
            origin = repoSelected.create_remote(branchName, self.remote_url)
            origin.fetch()
            origin.pull(origin.refs[0].remote_head)
            if self.debug:
                print(f"Clone of repository: {self.targetDirectory}")
            statusFlag = True
            self.git_getAllBranches()
            self.baseRemoteName = repoSelected.head.ref
        except Exception as e:
            print(str(e))
        return statusFlag

    def git_clone_simple(self, branchName=None):
        self._setupCloner(branchName=branchName)
        try:
            repo = git.Repo.clone_from(url=self.remote_url, to_path=self.targetDirectory, branch=branchName,
                                       recursive=True, progress=CloneProgress())
            self.git_getAllBranches()
            self.baseRemoteName = repo.head.ref  # self.git_currentRemoteHead()
        except Exception as e:
            print(str(e))
        return

    def testAccess(self):
        self.git_clone()
        self.git_getAllBranches()
        self.git_clone_simple()
        self.git_getAllBranches()
        # self.git_push_allfiles()
        return


def ubuntuInstaller(debug: bool = False):
    """
    Prepares library by finding shared library.
    Args:
        debug: debug mode for adding functionality.

    Returns: None
    """
    packageList = ["build-essential", "apt-transport-https", "aptitude", "ca-certificates", "cscope", "valgrind", "gdb"
                                                                                                                  "wget", "tar", "unzip", "p7zip-full", "p7zip-rar", "dtrx", "a2ps", "enscript", "python3",
                   "libncurses5-dev", "libipt-dev", "fakeroot", "msr-tools",
                   "linux-tools", "linux-tools-common", "linux-tools-virtual",
                   "libpapi-dev", "libpapi-dev", "papi-examples", "papi-tools",
                   "libpthread-stubs0-dev"]
    #  linux-tools-common linux-tools-generic  linux-tools-virtual
    # sudo apt-get install linux-tools-$(uname -r)
    prefix = "sudo apt-get install"
    postfixArgs = "-yf"
    errorString = callCommand(cmd="sudo apt update -y")
    for packageItem in packageList:
        sendCommand = f"{prefix} {packageItem} {postfixArgs}"
        errorString = callCommand(cmd=sendCommand)
        if debug:
            print(f"[DEBUG] {errorString}")
    return


def ubuntuEnableProfiling(debug: bool = False):
    """
    Enable CPU performance events
    Args:
        debug: debug mode for adding functionality.

    Returns: None
    """
    # Enable CPU performance events
    eventFile = os.path.abspath("/proc/sys/kernel/perf_event_paranoid")
    if os.path.exists(eventFile):
        enableCPUCounters = f"sudo sh -c 'echo  -1 >{eventFile}"
        errorString = callCommand(cmd=f"{enableCPUCounters}")
        if debug:
            print(f"[DEBUG] {errorString}")
    else:
        print(f"[ERROR] Event file cannot be found. {eventFile}.")
    return


def getIndentLevel(indentDepth: int = 1, separatorToken: str = '\t'):
    indentLevel = ''
    if indentDepth > 0:
        for _ in range(indentDepth):
            indentLevel = f'{indentLevel}{separatorToken}'
    return indentLevel


class MakefileCommonContext(object):
    # Note: https://www.gnu.org/software/make/manual/make.html

    def __init__(self, fileName: str = 'common.mk', opMode: str = 'file'):
        self.separatorToken: str = '\t'
        self.newlineToken: str = f'{os.linesep}'
        self.fileName = fileName
        if opMode == 'file':
            self.bufferContext = open(file=self.fileName, mode='w')
        else:
            self.bufferContext = StringIO('')
        return

    def _makefileWriteVar(self, varName=None, varValue=None):
        self.bufferContext.write(f'ifeq ($(origin {varName}),undefined){os.linesep}')
        self.bufferContext.write(f'    $(info {varName} is undefined){os.linesep}')
        self.bufferContext.write(f'    {varName} := {varValue}{os.linesep}')
        self.bufferContext.write(f'else{os.linesep}')
        self.bufferContext.write(f'    $({varName})+={varValue}{os.linesep}')
        self.bufferContext.write(f'endif{os.linesep}')
        return

    def makefileCreateCommon(self, profiler_path=''):
        self.bufferContext.write(f"LIBRARY_PATH:=$(LIBRARY_PATH){os.pathsep}{profiler_path}{os.linesep}")
        self.bufferContext.write(f"LD_LIBRARY_PATH:=$(LD_LIBRARY_PATH){os.pathsep}{profiler_path}{os.linesep}")
        self._makefileWriteVar(varName="LPATH", varValue=f"-L{profiler_path}")
        self._makefileWriteVar(varName="LIBS", varValue=f"-lperfpoint -lpapi -lpthread -ldl")
        self._makefileWriteVar(varName="CFLAGS",
                               varValue=f"-fno-strict-aliasing -I{profiler_path}")
        self._makefileWriteVar(varName='PERFPOINT_EVENT_INDEX', varValue='1')
        self.bufferContext.close()
        return

    def getInclude(self):
        makeCode = f'## ==== [ INJECTED BY AUTOPERF ] ==== ##{os.linesep}' \
                   f'ifeq(,$(wildcard {self.fileName})){os.linesep}' \
                   f'    include {self.fileName}{os.linesep}' \
                   f'else{os.linesep}' \
                   f'    $(warning Cannot find {self.fileName}{os.linesep}' \
                   f'endif{os.linesep}' \
                   f'## ==== [ INJECTED BY AUTOPERF ] ==== ##{os.linesep}'
        return makeCode

    def _makefileWriteVarStr(self, strList: list[str], varName=None, varValue=None):
        strList.append(f'ifeq ($(origin {varName}),undefined){os.linesep}')
        strList.append(f'    $(info {varName} is undefined){os.linesep}')
        strList.append(f'    {varName} := {varValue}{os.linesep}')
        strList.append(f'else{os.linesep}')
        strList.append(f'    $({varName})+={varValue}{os.linesep}')
        strList.append(f'endif{os.linesep}')
        return

    def injectMake(self, fileName, profiler_path=''):
        stringList = list()
        stringList.append(f"LIBRARY_PATH:=$(LIBRARY_PATH){os.pathsep}{profiler_path}{os.linesep}")
        stringList.append(f"LD_LIBRARY_PATH:=$(LD_LIBRARY_PATH){os.pathsep}{profiler_path}{os.linesep}")
        self._makefileWriteVarStr(strList=stringList, varName="LPATH", varValue=f"-L{profiler_path}")
        self._makefileWriteVarStr(strList=stringList, varName="LIBS", varValue=f"-lperfpoint -lpapi -lpthread -ldl")
        self._makefileWriteVarStr(strList=stringList, varName="CFLAGS", varValue=f"-fno-strict-aliasing -I{profiler_path}")
        self._makefileWriteVarStr(strList=stringList, varName='PERFPOINT_EVENT_INDEX', varValue='1')
        return stringList


def makefileWriteVarStr(strList: list[str], varName: str = None, varValue: str = None):
    strList.append(f'ifeq ($(origin {varName}),undefined){os.linesep}')
    strList.append(f'    $(info {varName} is undefined){os.linesep}')
    strList.append(f'    {varName} := {varValue}{os.linesep}')
    strList.append(f'else{os.linesep}')
    strList.append(f'    $({varName})+={varValue}{os.linesep}')
    strList.append(f'endif{os.linesep}')
    return


def prependMake(profiler_path: str = None, fileLocation: str = "Makefile"):
    if profiler_path is None:
        curFilePath = os.path.dirname(os.path.abspath(__file__))
        profiler_path = os.path.abspath(os.path.join(curFilePath, 'profiler', 'lib'))
    pathExists = os.path.exists(profiler_path)
    if pathExists:
        stringList = list()
        stringList.append(f'## ==== [ INJECTED BY AUTOPERF ] ==== ##{os.linesep}')
        stringList.append(f"export LIBRARY_PATH:=${{LIBRARY_PATH}}{os.pathsep}{profiler_path}{os.linesep}")
        stringList.append(f"export LD_LIBRARY_PATH:=${{LD_LIBRARY_PATH}}{os.pathsep}{profiler_path}{os.linesep}")
        makefileWriteVarStr(strList=stringList, varName="LPATH", varValue=f"-L{profiler_path}")
        makefileWriteVarStr(strList=stringList, varName="LIBS", varValue="-lperfpoint -lpapi -lpthread -ldl")
        makefileWriteVarStr(strList=stringList, varName="CFLAGS", varValue=f"-fno-strict-aliasing -I{profiler_path}")
        makefileWriteVarStr(strList=stringList, varName="PERFPOINT_EVENT_INDEX", varValue=f"1")
        stringList.append(f'## ==== [ INJECTED BY AUTOPERF ] ==== ##{os.linesep}')
        prepend_multiple_lines(file_name=fileLocation, list_of_lines=stringList)
    return


def prepend_line(file_name: str, line: str, addNewLine: bool = False):
    """ Insert given string as a new line at the beginning of a file """
    if addNewLine:
        strNewLine = os.linesep
    else:
        strNewLine = ''
    # define name of temporary dummy file
    dummy_file = f'{file_name}.bak'
    # open original file in read mode and dummy file in write mode
    with open(file_name, 'r') as read_obj, open(dummy_file, 'w') as write_obj:
        # Write given line to the dummy file
        write_obj.write(line + '\n')
        # Read lines from original file one by one and append them to the dummy file
        for line in read_obj:
            injectLine = f"{line}{strNewLine}"
            write_obj.write(injectLine)
    # remove original file
    os.remove(file_name)
    # Rename dummy file as the original file
    os.rename(dummy_file, file_name)
    return


def prepend_multiple_lines(file_name: str, list_of_lines: list[str], addNewLine: bool = False):
    """Insert given list of strings as a new lines at the beginning of a file"""
    # define name of temporary dummy file
    if addNewLine:
        strNewLine = os.linesep
    else:
        strNewLine = ''
    dummy_file = f'{file_name}.bak'
    # open given original file in read mode and dummy file in write mode
    with open(file_name, 'r') as read_obj, open(dummy_file, 'w') as write_obj:
        # Iterate over the given list of strings and write them to dummy file as lines
        for line in list_of_lines:
            injectLine = f"{line}{strNewLine}"
            write_obj.write(injectLine)
        # Read lines from original file one by one and append them to the dummy file
        for line in read_obj:
            write_obj.write(line)
    # remove original file
    os.remove(file_name)
    # Rename dummy file as the original file
    os.rename(dummy_file, file_name)
    return


class MakefileContext(object):

    def __init__(self, fileName: str = 'Makefile', opMode: str = 'file'):
        self.separatorToken: str = '\t'
        self.newlineToken: str = f'{os.linesep}'
        if opMode == 'file':
            self.bufferContext = open(file=fileName, mode='w')
        else:
            self.bufferContext = StringIO('')
        return

    def makefilePassArgs(self):
        default = f'{self.newlineToken}' \
                  f'args = $(foreach a,$($(subst -,_,$1)_args),$(if $(value $a),$a="$($a)")){self.newlineToken}' \
                  f'check_args = files{self.newlineToken}' \
                  f'release_args = version{self.newlineToken}' \
                  f'test_args = match{self.newlineToken}' \
                  f'TASKS = \\{self.newlineToken}' \
                  f'{self.separatorToken}check \\{self.newlineToken}' \
                  f'{self.separatorToken}release \\{self.newlineToken}' \
                  f'{self.separatorToken}test{self.newlineToken}' \
                  f'.PHONY: $(TASKS){self.newlineToken}' \
                  f'$(TASKS):{self.newlineToken}' \
                  f'{self.separatorToken}@make $@ $(call args,$@){self.newlineToken}' \
                  f'{self.newlineToken}'
        return default

    def dirTarget(self, indentDepth: int = 0, target_dir: str = 'project_dir'):
        indentLevel = getIndentLevel(indentDepth=indentDepth, separatorToken=self.separatorToken)
        default = f'' \
                  f'{indentLevel}if [ -d {target_dir} ]{self.newlineToken}' \
                  f'{indentLevel}then{self.newlineToken}' \
                  f'{indentLevel}{self.separatorToken}$(info Dir {target_dir} already generated.){self.newlineToken}' \
                  f'{indentLevel}else{self.newlineToken}' \
                  f'{indentLevel}{self.separatorToken}mkdir -p {target_dir}{self.newlineToken}' \
                  f'{self.newlineToken}'
        return default

    def pythonTarget(self, targetName: str = 'main_program', pythonFileName: str = 'compile', dependencies: str = 'math.pyc'):
        default = f'' \
                  f'{targetName}.pyc: {targetName}.py{self.newlineToken}' \
                  f'{self.separatorToken}python {pythonFileName}.py $<{self.newlineToken}' \
                  f'{self.newlineToken}' \
                  f'{targetName}.pyc: {dependencies}' \
                  f'{self.separatorToken}python {pythonFileName}.py $<{self.newlineToken}' \
                  f'{self.newlineToken}'
        return default


def add_environment_variable(key: str, sep: str, val: str):
    """Creates or appends a string to an environment variable.

    Args:
        key: The environment variable name.
        sep: The separator to use if appending a value.
        val: The value to assign to the environment variable.
    """
    if key in os.environ:
        os.environ[key] += sep + val
    else:
        os.environ[key] = val
    return


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
                            print('Other {0} File Node: {1}'.format(file.endswith(fileType), otherFileLocation),
                                  flush=True)
        except BaseException as ErrorContext:
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


def library_prepare(debug: bool = False):
    """
    Prepares library by finding shared library.
    Args:
        debug: debug mode for adding functionality.

    Returns: fileTypeTree, directoryTree
    """
    curFilePath = os.path.dirname(os.path.abspath(__file__))
    importPath = os.path.abspath(os.path.join(curFilePath, 'profiler', 'lib'))
    sys.path.insert(1, importPath)
    base_perflib_path = os.path.join('/'.join(__file__.split('/')[:-2]), 'profiler', 'lib')
    pathExists = os.path.exists(base_perflib_path)
    if not pathExists:
        base_perflib_path = os.path.join('/'.join(__file__.split('/')[:-2]), 'autoperf', 'profiler', 'lib')
        pathExists = os.path.exists(base_perflib_path)
        if not pathExists:
            print("[ERROR] Cannot find library path for perfpoint.")
            print(f'[DEBUG] loaded the perfpoint.so from {os.environ["LD_LIBRARY_PATH"]}')
            exit(1)

    # base_lib_static = os.path.join(base_perflib_path, 'libperfpoint.a')
    # base_lib_dynamic = os.path.join(base_perflib_path, 'libperfpoint.so')
    profiler_path = f"{base_perflib_path}"
    # Example addition to makefile
    # Static
    # -I../papi-5.4.1/src ../papi-5.4.1/src/libpapi.a
    # Dynamic
    # I../papi-5.4.1/src -L../papi-5.4.1/src/ -lpapi
    # export LD_LIBRARY_PATH=:../papi-5.4.1/src/
    add_environment_variable('LIBRARY_PATH', os.pathsep, profiler_path)
    add_environment_variable('LD_LIBRARY_PATH', os.pathsep, profiler_path)
    add_environment_variable('LPATH', ' ', f'-L{profiler_path}')
    add_environment_variable('LIBS', ' ', f'-lperfpoint -lpapi -lpthread -ldl')
    add_environment_variable('CFLAGS', ' ', f'-fno-strict-aliasing -I{profiler_path}')
    add_environment_variable('PERFPOINT_EVENT_INDEX', '', '1')
    add_environment_variable('TF_CPP_MIN_LOG_LEVEL', '', '3')
    # makeCommonObj = MakefileCommonContext(fileName='common.mk', opMode='file')
    # makeCommonObj.makefileCreateCommon(profiler_path=profiler_path)

    findAll(fileType=".py", directoryTreeRootNode='.', debug=debug, doIt=True, verbose=debug)
    return
