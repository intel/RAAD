#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Daniel Garces
# *****************************************************************************/
# @package condaEnvironment
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import os, subprocess, sys, platform, signal, inspect, ctypes, datetime, traceback, tarfile, zipfile, optparse
import wgetter
from shlex import quote as shlex_quote

"""
Brief:

Description:

    Layout condaEnvironment.py
        <Text Template>
        <import items>
        myNameIdentify = templateUtility()
        myNameIdentify.execute()
        <Other Code>

        Wiki
            https://wiki.ith.intel.com/display/Conda

        Anaconda
            Saving Environment
                conda list --export > package-list.txt
                conda create --clone base -p /path/to/new/location --copy

            Loading Enviroment
                conda create -n base --file package-list.txt

            To package an environment named 'base':
                NOTE '/anaconda3/pkgs/*.tar.bz2' is the location of all packages. You can filter out packages in order not to download the whole repo by:
                    wget -r --no-parent -R --regex-type pcre --reject-regex '(.*py2[67].*)|(.*py[34].*)' https://repo.continuum.io/pkgs/free/linux-64/
                    wget -r --no-parent -R --regex-type pcre --reject-regex '(.*py2[67].*)|(.*py[34].*)' https://repo.anaconda.com/pkgs/main/win-64/
                
                SOURCE MACHINE
                pip install conda-pack
                
                ## Pack environment base into base.tar.gz
                $ conda pack -n base
                
                ## Pack environment base into out_name.tar.gz
                $ conda pack -n base -o out_name.tar.gz
                
                ## Pack environment located at an explicit path into base.tar.gz
                $ conda pack -p /explicit/path/to/base
                
                TARGET MACHINE
                # After following above approach, you will end up with a tar.gz file. Now to install package from this zip file follow below approach.
                ## To install the environment:
                ## Unpack environment into directory `base`
                $ mkdir -p base
                $ tar -xzf base.tar.gz -C base
                
                ## Use Python without activating or fixing the prefixes. Most Python libraries will work fine, but things that require prefix cleanups will fail.
                $ ./base/bin/python
                
                ## Activate the environment. This adds `base/bin` to your path
                $ source base/bin/activate
                
                ## Run Python from in the environment
                (base) $ python
                
                ## Cleanup prefixes from in the active environment.
                ## Note that this command can also be run without activating the environment as long as some version of Python is already installed on the machine.
                (base) $ conda-unpack
                
                ## At this point the environment is exactly as if you installed it here using conda directly. All scripts should work fine.
                (base)$ ipython --version
                Deactivate the environment to remove it from your path
                (base)$ source base/bin/deactivate
    """

class condaEnvironment(object):
    _pack_ = 1
    _fields_ = [
        ("uID-API", ctypes.c_uint32, ctypes.sizeof(ctypes.c_uint32)),  # API Identifier
        ("major", ctypes.c_uint16, ctypes.sizeof(ctypes.c_uint16)),  # Major version number of the file.
        ("minor", ctypes.c_uint16, ctypes.sizeof(ctypes.c_uint16)),  # Minor version number of the file.
    ]

    _urlLinux = 'https://repo.anaconda.com/archive/Anaconda3-2020.11-Linux-ppc64le.sh'
    _urlWindows64 = 'https://repo.anaconda.com/archive/Anaconda3-2020.11-Windows-x86_64.exe'
    _urlWindows86 = 'https://repo.anaconda.com/archive/Anaconda3-2020.11-Windows-x86.exe'

    def __init__(self,
                 uid=(-1),
                 major=(-1),
                 minor=(1),
                 time=datetime.datetime.now(),
                 user="",
                 debug=True,
                 condaPath=None,
                 saveLocal=True):

        if (debug is True):
            print('condaEnvironment Interface init called')
        (head, tail) = os.path.split(os.path.dirname(os.path.abspath(__file__)))
        __origin__ = 'condaEnvironment.py :Joseph Tarango :05-12-2020 11:58:00'
        self.uid = uid
        self.major = major
        self.minor = minor
        # Meta tracking data
        self.time = time
        self.user = user
        self.absPath = os.path.dirname(os.path.abspath(__file__))
        self.path = head
        self.filename = tail
        self.debug = debug
        self.saveLocal = saveLocal

        # Internal tracking variables hidden
        # Interface variables
        self.url = None
        self.anacondaPath = None
        self.anacondaImportPath = None
        self.outFileSave = None
        self.earlyReturn = None
        # Internal method variables
        self.platformType = None
        self.homeDirectory = None
        self.architectureType = None
        self.anacondaBinPath = None

        exeName = 'python'
        basePath = os.environ['PATH']
        if condaPath is None:
            foundExe = self._findExecutable(executable=exeName, path=os.path.abspath(basePath))
        else:
            foundExe = self._findExecutable(executable=exeName, path=condaPath)

        if (self.debug):
            print("__origin__", ":", __origin__)

            print("self.uid", ":", self.uid)
            print("self.major", ":", self.major)
            print("self.minor", ":", self.minor)
            # Meta tracking data
            print("self.time", ":", self.time)
            print("self.user", ":", self.user)
            print("self.absPath", ":", self.absPath)
            print("self.path", ":", self.path)
            print("self.filename", ":", self.filename)
            print("self.debug", ":", self.debug)
            print("self.saveLocal,                      :", self.saveLocal)
            print("python status                        :", foundExe)

        return

    def _procKiller(self, processName=None, processID=None, killAllProcess=False):
        """
        Function to kill a subprocess.
        Args:
            processName: Name of the process executing.
            processID: Process ID if name is None.
            killAllProcess: Flag to kill all processes in chain.

        Returns: None
        """
        try:
            if (processName is not None):
                PID = processName.pid
            else:
                PID = processID
            isUnix = sys.platform != 'win32'
            if isUnix:
                platformSignal = signal.SIGKILL
                PGID = os.getpgid(PID)
            else:
                platformSignal = signal.SIGTERM
                PGID = PID
            for childPGID in PGID.children(recursive=True):
                print("Child Process", childPGID)
                if isUnix:
                    os.killpg(childPGID, platformSignal)
                else:
                    os.kill(childPGID, platformSignal)
            if isUnix:
                os.killpg(PGID, platformSignal)
            else:
                os.kill(PID, platformSignal)
        except Exception as errorContext:
            if self.debug:
                print("Failed process kill. {0}".format(errorContext))
            if (killAllProcess is True):
                allPID = os.getpid()
                self._procKiller(processName=None, processID=allPID, killAllProcess=killAllProcess)
            pass

    @staticmethod
    def _findExecutable(executable='', path=None):
        """
            Tries to find 'executable' in the directories listed in 'path'.
                A string listing directories separated by 'os.pathsep'; defaults to
                os.environ['PATH'].  Returns the complete filename or None if not found.
        Args:
            executable: executable basename does not need .exe, .bat, or .sh
            path: Operating system path to start searching.
        """
        if path is None:
            path = os.environ.get('PATH', os.defpath)

        paths = path.split(os.pathsep)
        # base, ext = os.path.splitext(executable)

        if (sys.platform == 'win32' or os.name == 'os2'):
            exts = ['.exe', '.bat', '']
        else:
            exts = ['', '.sh']

        if not os.path.isfile(executable):
            for ext in exts:
                newExecute = executable + ext
                if os.path.isfile(newExecute):
                    return newExecute
                else:
                    for pathVar in paths:
                        fileVar = os.path.join(pathVar, newExecute)
                        if os.path.isfile(fileVar):
                            # The file exists, we have a shot at spawn working.
                            return fileVar
        else:
            return executable
        return None

    @staticmethod
    def _getFunctionName():
        """
        When a fault occurs get a function name
        Returns: function stack to inspect in string format
        """
        nameString = (inspect.stack()[0][0].f_code.co_name) + \
                     (inspect.stack()[0][3]) + \
                     (inspect.currentframe().f_code.co_name) + \
                     (sys._getframe().f_code.co_name)
        return nameString

    @staticmethod
    def _runSH(script=''):
        """
        Execution of command line in Linux
        Args:
            script: Name of the script or binary to execute.

        Returns: None
        """
        scriptContext = f"bash -c '{script}'"
        os.system(shlex_quote(scriptContext))
        return

    @staticmethod
    def _runCMD(script=''):
        """
        Execution of command line in Windows.
        Args:
            script: Name of the script or binary to execute.

        Returns: None
        """
        os.system(shlex_quote(script))
        return

    def _runCommandLine(self, script=''):
        """
        Execution of command line in Windows or Linux.
        Args:
            script: Name of the script or binary to execute.

        Returns: None
        """
        platformType = sys.platform
        if platformType == 'linux':
            print("Executing command on linux: " + script)
            self._runSH(script=script)
        elif platformType == 'win32':
            print("Executing command on windows: " + script)
            self._runCMD(script=script)
        return

    @staticmethod
    def _unTAR(tarName='packedCondaLibs.tar.gz', path='.', toDirectory='.'):
        """
        Method to aid in unpacking anaconda environment.
        Args:
            tarName: Compressed file name.
            path: Path to operate out of.
            toDirectory: Path to target for decompress.

        Returns: None
        """
        if tarName.endswith('.zip'):
            opener, mode = zipfile.ZipFile, 'r'
        elif path.endswith('.tar'):
            opener, mode = tarfile.open, 'r:'
        elif path.endswith('.tar.gz') or path.endswith('.tgz'):
            opener, mode = tarfile.open, 'r:gz'
        elif path.endswith('.tar.bz2') or path.endswith('.tbz'):
            opener, mode = tarfile.open, 'r:bz2'
        else:
            raise (ValueError, "Could not extract {0} as no appropriate extractor is found".format(path))

        file = opener(path, mode)
        try:
            file.extractall(path=toDirectory)
        finally:
            file.close()
        return

    def _preparePaths(self):
        """
        Determines for the machine the default Anaconda information.
        Returns:
                anacondaPath: Path of anaconda install.
                anacondaImportPath: Path of hte main import script for anaconda.
                outFileSave: File name to save the downloaded installer.
                url: Address of the installer.
                earlyReturn: If there is an error the flag is set to true.
        """
        earlyReturn = False

        platformType = sys.platform
        architectureType = ('64' in platform.machine())
        if platformType == 'linux':
            url = self._urlLinux
            outFileSave = 'anaconda.sh'
            homeDirectory = os.environ['HOME']
            anacondaPath = os.path.abspath(os.path.join(homeDirectory, 'anaconda3'))
            anacondaImportPath = os.path.abspath(os.path.join(anacondaPath, 'etc/profile.d/conda.sh'))
            anacondaBinPath = None
        elif platformType == 'win32':
            if (architectureType is True):
                url = self._urlWindows64
            else:
                url = self._urlWindows86
            outFileSave = 'anaconda.exe'
            homeDirectory = os.environ['USERPROFILE']
            anacondaPath = os.path.abspath(os.path.join(homeDirectory, r'Anaconda3'))
            anacondaImportPath = os.path.abspath(os.path.join(anacondaPath, r'Scripts/'))
            anacondaBinPath = os.path.abspath(os.path.join(anacondaPath, r'Library/bin'))
        else:
            url = outFileSave = homeDirectory = anacondaPath = anacondaImportPath = anacondaBinPath = None
            print("Error system not supported. Please see https://repo.anaconda.com/archive/")
            earlyReturn = True

        if self.saveLocal:
            # Passed variables
            self.url = url
            self.anacondaPath = anacondaPath
            self.anacondaImportPath = anacondaImportPath
            self.anacondaBinPath = anacondaBinPath
            self.outFileSave = outFileSave
            self.earlyReturn = earlyReturn
            # Internal variables
            self.platformType = platformType
            self.homeDirectory = homeDirectory
            self.architectureType = architectureType

        return (anacondaPath, anacondaImportPath, outFileSave, url, earlyReturn, anacondaBinPath)

    def _installAnaconda(self, outFileSave=None, url=None, anacondaPath=None,
                         anacondaImportPath=None, env=None, outFilePath='.'):
        """
        Install Anaconda environment.

        Args:
            outFileSave: File name to save the downloaded installer.
            url: Address of the installer.
            anacondaPath: Path of anaconda install.
            anacondaImportPath: Path of hte main import script for anaconda.
            env: Current system environment.
            outFilePath: Path for the saving of the installer.

        Returns: None
        """

        if outFileSave is None or \
                url is None or \
                anacondaPath is None or \
                anacondaImportPath is None or \
                env is None:
            print("Error on inputs")
            return

        # Run the anaconda installer
        outFileSave = wgetter.download(link=url, outdir=outFilePath)
        try:
            subprocess.call([outFileSave])
        except Exception as errorContext:
            print("Terminated Process ID {0}".format(errorContext))
        finally:
            print("Normal termination Process ID ")

        return

    def anacondaUpdate(self, anacondaPath=None, anacondaImportPath=None, anacondaBinPath=None, condaLog='condaEnvInstall.log'):
        """
        Updating of anaconda environment.
        Args:
            anacondaBinPath: Binary path for anaconda
            anacondaPath: Path of anaconda install.
            anacondaImportPath: Path of hte main import script for anaconda.
            condaLog: Log file if in debug mode.

        Returns: None
        """
        if anacondaPath is None or anacondaImportPath is None:
            # Prepare install information
            (anacondaPath, anacondaImportPath, outFileSave, url, earlyReturn, anacondaBinPath) = self._preparePaths()

        earlyReturn = False
        platformType = sys.platform
        # Run the conda init script to setup the shell
        if platformType == 'linux':
            if os.path.exists(anacondaImportPath):
                os.system(shlex_quote(". {}".format(anacondaImportPath)))
            elif os.path.exists(anacondaImportPath):
                anacondaBinPath = os.path.abspath(os.path.join(anacondaPath, 'bin'))
                os.system(shlex_quote("export PATH = \"{0}:$PATH\"".format(anacondaBinPath)))
            else:
                earlyReturn = True
        elif platformType == 'win32':
            if os.path.exists(anacondaImportPath):
                os.environ['PATH'] += os.pathsep + anacondaPath + os.pathsep + anacondaImportPath + os.pathsep + anacondaBinPath
            else:
                earlyReturn = True

        # Update Anaconda
        if earlyReturn is False:
            if self.debug:
                stdFileOutput = ''
            else:
                stdFileOutput = '2>>&1 {0}'.format(condaLog)
                if os.path.exists(condaLog):
                    os.remove(condaLog)
            self._runCommandLine(script="set PATH=%PATH%;{0};{1};{2}".format(anacondaPath, anacondaImportPath,
                                                                             anacondaBinPath))
            # self._runCommandLine(script='conda update -n base --all -y {0}'.format(stdFileOutput))
            # self._runCommandLine(script='conda update python -y {0}'.format(stdFileOutput))
            # self._runCommandLine(script='conda update --all -y {0}'.format(stdFileOutput))
            self._runCommandLine(script='conda update conda {0}'.format(stdFileOutput))
            self._runCommandLine(script='conda list {0}'.format(stdFileOutput))
            # Install additional Channel
            self._runCommandLine(script='conda config --add channels conda-forge {0}'.format(stdFileOutput))
            # self._runCommandLine(script='conda config --set channel_priority strict {0}'.format(stdFileOutput))
            self._runCommandLine(script='conda update -n base -c defaults conda -y {0}'.format(stdFileOutput))

        if self.saveLocal:
            # Passed variables
            # Internal variables
            self.anacondaBinPath = anacondaBinPath

        return

    def installFresh(self, enableShell=False, env=None, timeout=600, output=False):
        """
        Installs assuming a fresh system with no anaconda.
        Args:
            enableShell: Flag to determine if to execute in separate shell.
            env: Current system environment.
            timeout: Timeout for the executing program
            output: Standard output flag to print to command line.

        Returns: None
        """
        if (env is None):
            env = os.environ.copy()
        updateOnly = False

        # Prepare install information
        (anacondaPath, anacondaImportPath, outFileSave, url, earlyReturn, anacondaBinPath) = self._preparePaths()

        if os.path.exists(anacondaPath):
            updateOnly = True

        # Install Anaconda
        if earlyReturn is False and updateOnly is False:
            self._installAnaconda(outFileSave=outFileSave, url=url, anacondaPath=anacondaPath,
                                  anacondaImportPath=anacondaImportPath, env=env)
        # Update Anaconda
        elif earlyReturn is False:
            self.anacondaUpdate(anacondaPath=anacondaPath, anacondaImportPath=anacondaImportPath, anacondaBinPath=anacondaBinPath)

        return

    def condaCreateEnv(self, specificationFile='environment.yml'):
        print('Creating Conda Environment...')
        (anacondaPath, anacondaImportPath, outFileSave, url, earlyReturn, anacondaBinPath) = self._preparePaths()
        os.environ['PATH'] += os.pathsep + anacondaPath + os.pathsep + anacondaImportPath + os.pathsep + anacondaBinPath
        self._runCommandLine('conda env create -f {0}'.format(specificationFile))

    def condaUpdateEnv(self, specificationFile='environment.yml'):
        self._runCommandLine('conda env update --prefix ./env --file {0} --prune'.format(specificationFile))

    def condaDeleteEnv(self, envName="RAAD_1.0"):
        """
        Commands to delete anaconda environment.
        Args:
            envName: Name of the environment to be deleted

        Returns: None
        """
        self._runCommandLine('conda remove --name {0} --all'.format(envName))

    def condaCloneEnv(self, envName='base', newEnv='RAAD_2.0'):
        """
        Commands to clone current anaconda environment.
        Args:
            envName:
            newEnv:

        Returns: None
        """
        self._runCommandLine('conda create --name {0} --clone {1}'.format(newEnv, envName))

    def condaExportEnv(self, outFile='environment.yml'):
        """
        Commands to export current anaconda environment.
        Args:
            outFile: outputfile for current configuration.

        Returns: None
        """
        (anacondaPath, anacondaImportPath, outFileSave, url, earlyReturn, anacondaBinPath) = self._preparePaths()
        os.environ['PATH'] += os.pathsep + anacondaPath + os.pathsep + anacondaImportPath + os.pathsep + anacondaBinPath
        self._runCommandLine('conda env export > {0}'.format(outFile))

    def condaSaveEnv(self, outFile='anacondaPackages.txt'):
        """
        Commands to save current anaconda environment.
        Args:
            outFile: outputfile for current configuration.

        Returns: None
        """
        (anacondaPath, anacondaImportPath, outFileSave, url, earlyReturn, anacondaBinPath) = self._preparePaths()
        os.environ['PATH'] += os.pathsep + anacondaPath + os.pathsep + anacondaImportPath + os.pathsep + anacondaBinPath
        self._runCommandLine('conda list --explicit > {0}'.format(outFile))

    def condaLoadEnv(self, outFile='anacondaPackages.txt', envName="RAAD_1.0"):
        """
        Commands to load current anaconda environment.
        Args:
            envName: Enviroment name
            outFile: Input package file list.

        Returns: None
        """
        (anacondaPath, anacondaImportPath, outFileSave, url, earlyReturn, anacondaBinPath) = self._preparePaths()
        os.environ['PATH'] += os.pathsep + anacondaPath + os.pathsep + anacondaImportPath + os.pathsep + anacondaBinPath
        self._runCommandLine('conda create -n {0} --file {1}'.format(envName, outFile))

    def condaInstallDependecies(self, outFile='anacondaPackages.txt', envName="RAAD_1.0"):
        self._runCommandLine('conda create -n {0} --file {1}'.format(envName, outFile))

    def sourceMachinePack(self, tarName='packedCondaLibs.tar.gz', envName='base'):
        """
        Function to pack a source environment.
        Args:
            tarName: Compressed file name.
            envName: Environment name to save for example base is the default.

        Returns: None
        """
        # Pack environment base into base.tar.gz
        self._runCommandLine('conda pack -n {0}'.format(envName))
        # Pack environment base into out_name.tar.gz
        self._runCommandLine('conda pack -n {0} -o {1}'.format(envName, tarName))
        return

    def targetMachineUnPack(self, homeCondaPath=None, tarName='packedCondaLibs.tar.gz', path='tmp'):
        """
        Function to unpack a source environment.
        Args:
            homeCondaPath: Anaconda home path.
            tarName: Name of the compressed file.
            path: System path to decompress files.

        Returns: None
        """
        platformType = sys.platform
        if homeCondaPath is None or homeCondaPath == "":
            if platformType == 'linux':
                homeDirectory = os.environ['HOME']
                anacondaPath = os.path.abspath(os.path.join(homeDirectory, 'anaconda3'))
            elif platformType == 'win32':
                homeDirectory = os.environ['USERPROFILE']
                anacondaPath = os.path.abspath(os.path.join(homeDirectory, 'Anaconda3'))
            else:
                raise (ValueError, "Could not extract {0} as no appropriate extractor is found".format(homeCondaPath))
        else:
            anacondaPath = homeCondaPath

        if (os.path.exists(anacondaPath)):
            raise (ValueError, "Path exists {0}".format(homeCondaPath))

        # After following above approach, you will end up with a tar.gz file. Now to install package from this zip file follow below approach.
        # To install the environment:
        # Unpack environment into directory `~/anaconda3/` or `C:/users/lab/anaconda3/
        os.mkdir(anacondaPath)

        # Linux I.E.self.runCommandLine('tar -xzf {0} -C base'.format(tarName))
        self._unTAR(tarName=tarName, path=path, toDirectory=anacondaPath)

        # Use Python without activating or fixing the prefixes. Most Python libraries will work fine, but things that require prefix cleanups will fail.
        cmdPath = os.path.abspath(os.path.join(anacondaPath, 'bin/python'))
        self._runCommandLine('. {0}'.format(cmdPath))

        # Activate the environment. This adds `base/bin` to your path
        cmdPath = os.path.abspath(os.path.join(anacondaPath, 'condabin/activate'))
        if platformType == 'linux':
            self._runCommandLine('source {0}'.format(cmdPath))
        elif platformType == 'win32':
            self._runCommandLine('source {0}.bat'.format(cmdPath))

        # Run Python from in the environment
        self._runCommandLine('python')

        # Cleanup prefixes from in the active environment.
        # Note that this command can also be run without activating the environment as long as some version of Python is already installed on the machine.
        self._runCommandLine('conda-unpack')

        # At this point the environment is exactly as if you installed it here using conda directly. All scripts should work fine.
        self._runCommandLine('ipython --version')

        # Deactivate the environment to remove it from your path
        if platformType == 'linux':
            cmdPath = os.path.abspath(os.path.join(anacondaPath, 'bin/deactivate'))
            self._runCommandLine('source {0}'.format(cmdPath))
        elif platformType == 'win32':
            cmdPath = os.path.abspath(os.path.join(anacondaPath, 'condabin/conda.exe'))
            self._runCommandLine('{0} deactivate'.format(cmdPath))

        return

    @staticmethod
    def printHelp():
        """
        Prints out complex help documentation.
        Returns: None

        """
        print("Please Review these pages for complex installs")
        print("https://docs.anaconda.com/anaconda/install/windows/")
        print("https://docs.anaconda.com/anaconda/install/linux/")
        print("https://docs.anaconda.com/anaconda/install/verify-install/")
        print("https://docs.anaconda.com/anaconda/user-guide/tasks/move-directory/")
        print("https://www.jetbrains.com/pycharm/promo/anaconda/")
        return


def harnessCondaEnvironment(options=None):
    """
    Default main execution with options.
    Args:
        options: Options from commandline

    Returns:

    """
    print("Running harness of Anaconda Environment.")
    instanceConda = condaEnvironment(debug=options.debug)

    if options.more is True:
        print("More options")
        print("--select definitions")
        print(" 1: Save anaconda environment.")
        print(" 2: Load anaconda environment.")
        print(" 3: Clone anaconda environment.")
        print(" 4: Update anaconda.")
        print(" 5: Source machine packing of environment.")
        print(" 6: Target machine unpacking of environment.")
        print(" 7: Complex help web pages.")

    returnCode = 0
    if options.select == 1:
        instanceConda.condaSaveEnv()
    elif options.select == 2:
        instanceConda.condaLoadEnv()
    elif options.select == 3:
        instanceConda.condaCloneEnv()
    elif options.select == 4:
        instanceConda.installFresh()
    elif options.select == 5:
        instanceConda.anacondaUpdate()
    elif options.select == 6:
        instanceConda.sourceMachinePack()
    elif options.select == 7:
        instanceConda.targetMachineUnPack()
    elif options.select == 8:
        instanceConda.printHelp()
    else:
        returnCode = 1

    return returnCode


def main():
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--example", action='store_true', dest='example', default=False,
                      help='Show command execution example.')
    parser.add_option("--debug", action='store_true', dest='debug', default=False, help='Debug mode.')
    parser.add_option("--select", dest='select', default=None, help='Selection of operation.')
    parser.add_option("--more", dest=help, default=False, help="Displays more options.")
    (options, args) = parser.parse_args()

    ##############################################
    # Main
    ##############################################
    harnessCondaEnvironment(options)
    return 0


if __name__ == '__main__':
    """Performs execution delta of the process."""
    pStart = datetime.datetime.now()
    try:
        main()
    except Exception as errorMainContext:
        print("Fail End Process: ", errorMainContext)
        traceback.print_exc()
    qStop = datetime.datetime.now()
    print("Execution time: " + str(qStop - pStart))
