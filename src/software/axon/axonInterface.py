#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Pallavi Dhumal, Joseph Tarango
# *****************************************************************************/
# @package axonInterface

from __future__ import absolute_import, division, print_function, \
    unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations

# Standard Classes
import ctypes, datetime, hashlib, json, ntpath, os, re, subprocess, sys, tempfile, traceback, unittest

# Created Classes
# projDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
# sys.path.append('/raad/src/software')
import src.software.axon.axonMeta
import src.software.container.basicTypes

"""
Brief:
    AXON is eXtended Object Notation (AXON). AXON helps to implement
    applications with CQRS (Command Query Responsibility Segregation) and Event
    Sourcing in mind. It's a simple text based format for interchanging of
    objects, documents, and data. AXON attempts to combine the best of: JSON,
    XML, and YAML. The AXON Framework and AXON Server will be utilized. The
    former will contain our implementation and the latter will be our dedicated
    Event Store and Message Routing solution.

Description:
    Utility library for uploading and downloading telemetry objects to the AXON
    system. Class library is designed to be used as a tracking template file to
    ease use across all files and ensure tracking.

    Layout axon.py
        <Text Template>
        <import items>
        myNameIdentify = templateUtility()
        myNameIdentify.execute()
        <Other Code>

        Wiki
            https://wiki.ith.intel.com/display/Axon/Axon-Ingest

        AGS
            AGS access Engineering Product Development - PEG - PEG BB Current Technology Functional Design
    """


class Axon_Interface(object):
    _maxPath = 256  # Total path character size.
    _maxTime = 32  # Time character size.
    _maxName = 16  # Name character size expected.
    _telemetryPayloadBytes = 33554432  # Telemetry specification size constraint 32 MegaBytes.
    _number_of_found_keys = 0  # Total number of keys.
    _number_of_limiter_keys = 1024  # Soft limit for testing.
    # Linux   : "Y:/fast-tools/bin/NSGTools/DriveInfoTools/lib/exe/axon/v1.0.21/axon-linux-x64"
    # Windows : "Y:/fast-tools/bin/NSGTools/DriveInfoTools/lib/exe/axon/v1.0.17/axon-windows-x64.exe"
    _AXON_EXE_FILE = "Y:/fast-tools/bin/NSGTools/DriveInfoTools/lib/exe/axon/v1.0.17/axon-windows-x64.exe"
    _AXON_DEV_URL = "https://axon-dev.intel.com"
    _AXON_TEST_URL = "https://axon-test.intel.com"
    _AXON_PROD_URL = "https://axon-prod.intel.com"
    _AXON_URL = "https://axon.intel.com"
    _received_meta_name = "record-intel-driveinfo-zip-v1.json"
    _received_content_file = "intel-driveinfo-zip-v1.zip"

    _pack_ = 1
    _fields_ = [
        ("uID-API", ctypes.c_uint32, ctypes.sizeof(ctypes.c_uint32)),  # API Identifier
        ("major", ctypes.c_uint16, ctypes.sizeof(ctypes.c_uint16)),  # Major version number of the file.
        ("minor", ctypes.c_uint16, ctypes.sizeof(ctypes.c_uint16)),  # Minor version number of the file.
        ("data", ctypes.c_wchar * _telemetryPayloadBytes, ctypes.sizeof(ctypes.c_char * _telemetryPayloadBytes)),
        # Name of the creator.
    ]

    def __init__(self,
                 uid=(-1),
                 major=(-1),
                 minor=(1),
                 time=datetime.datetime.now(),
                 user="DarthVader",
                 debug=True,
                 mode='base',
                 axonPath=None):

        if (debug is True):
            print('AxonInterface init called')
        (head, tail) = os.path.split(os.path.dirname(os.path.abspath(__file__)))
        __origin__ = 'axonInterface.py :Joseph Tarango :05-13-2020 11:58:00'
        self.uid = uid
        self.major = major
        self.minor = minor
        self.data = None
        # Meta tracking data
        self.time = time
        self.user = user
        self.absPath = os.path.dirname(os.path.abspath(__file__))
        self.path = head
        self.filename = tail
        self.debug = debug
        if mode == 'production':
            self.URL = self._AXON_PROD_URL
        elif mode == 'test':
            self.URL = self._AXON_TEST_URL
        elif mode == 'development':
            self.URL = self._AXON_DEV_URL
        elif mode == 'base':
            self.URL = self._AXON_URL
        else:
            self.URL = self._AXON_DEV_URL

        self.axonID = None

        if os.name == 'nt':
            self._AXON_EXE_FILE = 'axon-windows-x64.exe'
            exeName = 'axon-windows-x64'
            if os.path.exists(r"../lib/exe/axon/v1.0.17/axon-windows-x64.exe"):
                self._AXON_EXE_FILE = os.path.abspath(r"../lib/exe/axon/v1.0.17/axon-windows-x64.exe")
            elif os.path.exists(r"C:/fast-tools/bin/NSGTools/DriveInfoTools/lib/exe/axon/v1.0.17/axon-windows-x64.exe"):
                self._AXON_EXE_FILE = os.path.abspath(
                    r"C:/fast-tools/bin/NSGTools/DriveInfoTools/lib/exe/axon/v1.0.17/axon-windows-x64.exe")
            else:
                raise ValueError(
                    "Windows: Axon executable could not be found, set the location of the axon executable with the variable AXON_EXECUTE")
        elif os.name == 'posix':
            exeName = 'axon-linux-x64'
            if os.path.exists(r"../lib/exe/axon/v1.0.21/axon-linux-x64"):
                self._AXON_EXE_FILE = os.path.abspath(r"../lib/exe/axon/v1.0.21/axon-linux-x64")
            if os.path.exists(r"/home/DarthVader/axon/v1.0.21/axon-linux-x64"):
                self._AXON_EXE_FILE = os.path.abspath(r"../lib/exe/axon/v1.0.21/axon-linux-x64")
            elif os.getenv("AXON_EXECUTE") is not None:
                self._AXON_EXE_FILE = os.getenv("AXON_EXECUTE")
            else:
                raise ValueError(
                    "Linux: Axon executable could not be found, set the location of the axon executable with the variable AXON_EXECUTE")
        else:
            raise ValueError(
                "Other OS: Axon executable could not be found, set the location of the axon executable with the variable AXON_EXECUTE")

        (head, tail) = os.path.split(self._AXON_EXE_FILE)
        importPath = os.path.abspath(head)
        print("Importing Paths: ", str(importPath))
        sys.path.insert(1, importPath)

        if axonPath is None:
            foundExe = self.findExecutable(executable=exeName, path=os.path.abspath(
                r"C:/fast-tools/bin/NSGTools/DriveInfoTools/lib/exe/axon"))
        else:
            foundExe = self.findExecutable(executable=exeName, path=axonPath)

        if (self.debug):
            print("__origin__", ":", __origin__)

            print("self.uid", ":", self.uid)
            print("self.major", ":", self.major)
            print("self.minor", ":", self.minor)
            print("self.data", ":", self.data)

            print("self.time", ":", self.time)
            print("self.user", ":", self.user)
            print("self.absPath", ":", self.absPath)
            print("self.path", ":", self.path)
            print("self.filename", ":", self.filename)
            print("self.debug", ":", self.debug)
            print("self.URL", ":", self.URL)
            print("Found Exe", ":", foundExe)

            # Initiate version tracking
            # self.versioning = software.container.basicTypes.UID_Application(uid=self.uid, major=self.major, minor=self.minor)
        return

    def GetVersion(self):
        return self.versioning

    def GetURL(self):
        return self.URL

    def readFileBytes(self, fileInput=None, BUFFER_SIZE=4096):
        """Reads en entire file and returns file bytes."""
        byteSignature = b""
        print("fileInput: ", fileInput)
        with open(fileInput, "rb") as fileOpen:
            while True:
                # Read BUFFER_SIZE bytes from the file
                bytes_read = fileOpen.read(BUFFER_SIZE)  # Default buffer is 4096 bytes
                if bytes_read:
                    # If there is bytes, append them
                    byteSignature += bytes_read
                else:
                    # if not, nothing to do here, break out of the loop
                    break
        return byteSignature

    def secureHash(self, fileInput=None, BUFFER_SIZE=4096, secureMode="BLAKE2c"):
        file_content = self.readFileBytes(fileInput=fileInput, BUFFER_SIZE=BUFFER_SIZE)
        try:
            import pyblake2
            if secureMode == "BLAKE2c":
                # 256-bit BLAKE2 (or BLAKE2s)
                byteSignature = pyblake2.blake2s(file_content).hexdigest()
            else:
                byteSignature = hashlib.sha256(file_content).hexdigest()  # @todo insecure hash.
        except:
            byteSignature = hashlib.sha256().hexdigest()  # @todo insecure hash.
        return byteSignature

    def defaultHash(self, contentFile=None, BUFFER_SIZE=4096):
        computedHash = None
        sha256_hash = hashlib.sha256()  # @todo insecure hash.
        with open(contentFile, "rb") as openFile:
            # Read and update hash string value in blocks of 4K
            for byte_block in iter(lambda: openFile.read(BUFFER_SIZE), b""):
                sha256_hash.update(byte_block)
        computedHash = sha256_hash.hexdigest()
        if (self.debug is True):
            print("File is {}, sha256 {}".format(contentFile, computedHash))
        return computedHash

    #############################
    ####### Database CMD  #######
    #############################

    def findExecutable(self, executable='', path=None):
        """Tries to find 'executable' in the directories listed in 'path'.
        A string listing directories separated by 'os.pathsep'; defaults to
        os.environ['PATH'].  Returns the complete filename or None if not found.
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
                newexe = executable + ext
                if os.path.isfile(newexe):
                    return newexe
                else:
                    for p in paths:
                        f = os.path.join(p, newexe)
                        if os.path.isfile(f):
                            # The file exists, we have a shot at spawn working
                            return f
        else:
            return executable
        return None

    def createContentsMetaData(self, metaDataDictionary, contentFile):
        """
        Creates a metadata file for use in uploading to AXON
        Args:
            metaDataDictionary: Dictionary containing the fields and entries to the metadata file

        Returns: Path to metadata file
        """
        # Compute a secure hash for the metadata file
        computedHash = self.secureHash(fileInput=contentFile, secureMode="BLAKE2c")

        print("hash: ", computedHash)

        # Add this field to the aggragated metadata
        metaDataDictionary["sha"] = computedHash

        # Filename for metadata has filename for content file as well as descriptor
        metaDataFile = "contentMeta_" + ntpath.basename(contentFile) + ".json"

        # Open the file we have and populate the file
        with open(metaDataFile, 'w') as openmetaDataFile:
            strArray = src.software.axon.axonMeta.AXON_Meta().contents(fileName=contentFile,
                                                                   sha=computedHash)
            print("strArray: ", strArray)
            for indexStr, valueStr in enumerate(strArray):
                openmetaDataFile.write(valueStr)  # Nil content
                openmetaDataFile.write("\n")

        print("metaDataFile created: ", os.path.abspath(metaDataFile))

        return os.path.abspath(metaDataFile)

    def sendCmd(self, fileType=None, failureFile=None, metaDataFile=None, contentFile=None):

        if failureFile is None or metaDataFile is None:
            template = src.software.axon.axonMeta.AXON_Meta()

        if (failureFile is None):
            failureFile = 'failure.json'
            with open(failureFile, 'w') as openFile:
                strArray = template.failure()
                for indexStr, valueStr in enumerate(strArray):
                    openFile.write(valueStr)  # Nil content
                    openFile.write("\n")
                # json.dump(self.RADTemplate(), openFile, ensure_ascii=False, indent=4)  # Template content
                openFile.close()

        if (fileType is None):
            fileType = 'intel-driveinfo-zip-v1'

        if (contentFile is None):
            contentFile = 'intel-driveinfo-zip-v1.zip'  # telemetry.tar.gpg.zip
            with open(contentFile, 'w') as openFile:
                # strArray = self.RADTemplateString()
                # for indexStr, valueStr in enumerate(strArray):
                #    openFile.write(valueStr) # Nil content
                #    openFile.write("\n")
                # json.dump(self.RADTemplate(), openFile, ensure_ascii=False, indent=4)  # Template content
                openFile.write("")
                openFile.close()

        computedHash = self.secureHash(fileInput=contentFile, secureMode="BLAKE2c")

        if (metaDataFile is None):
            metaDataFile = 'metadata.json'
            with open(metaDataFile, 'w') as openFile:
                strArray = template.contents(fileName=contentFile,
                                             sha=computedHash)
                for indexStr, valueStr in enumerate(strArray):
                    openFile.write(valueStr)  # Nil content
                    openFile.write("\n")
                # json.dump(self.RADTemplate(), openFile, ensure_ascii=False, indent=4)  # Template content
                openFile.close()

        if os.path.exists(self._AXON_EXE_FILE) and os.path.exists(failureFile) and os.path.exists(
                metaDataFile) and os.path.exists(contentFile):
            print("All exists")

        # I.E. axon create --url https://axon-dev.intel.com --type zip --failure failureInfo.json --metadata metadatainfo.json --content telemetry.tar.gpg 2>&1 RunLogOfOutput.log
        if self.debug is False:
            # axon.exe create --url {} --type {} --failure @{} --metadata @{} --content @{}
            cmd = '{0} create --url {1} --type {2} --failure @{3}  --metadata @{4} --content @{5}' \
                .format(
                self._AXON_EXE_FILE,  # {0} Executable
                self.URL,  # {1} Internal URL to upload content
                fileType,  # {2} Upload Type
                failureFile,  # {3} Failure file
                metaDataFile,  # {4} Meta file
                contentFile,  # {5} Content file
            )
        else:
            # cmd = '"{0}" create --url {1} --type {2} --failure @{3}  --metadata @{4} --content @{5} -vvvvvv  2>&1 {6}' \
            # cmd = '{0} create --url {1} --type {2} --failure @{3}  --metadata @{4} --content @{5} -vvvvvv' \
            #     .format(
            #             self._AXON_EXE_FILE,  # {0} Executable
            #             self.URL,  # {1} Internal URL to upload content
            #             fileType,  # {2} Upload Type
            #             failureFile,  # {3} Failure file
            #             metaDataFile,  # {4} Meta file
            #             contentFile,  # {5} Content file
            #     )
            cmd = '{0} create --url {1} --type {2}  --metadata @{3} --content @{4} ' \
                .format(
                self._AXON_EXE_FILE,  # {0} Executable
                self.URL,  # {1} Internal URL to upload content
                fileType,  # {2} Upload Type
                metaDataFile,  # {4} Meta file
                contentFile,  # {5} Content file
            )

        if (self.debug):
            print("Command is: ", cmd)

        if (sys.platform == 'win32' or os.name == 'os2'):
            args = cmd.split(' ')
            processCommand = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                              universal_newlines=True, shell=True)
        else:
            processCommand = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                              universal_newlines=True, shell=True)

        cmdOutput, cmdError = processCommand.communicate()
        exitCode = processCommand.returncode

        return (exitCode, cmdOutput, cmdError)

    def sendInfo(self, fileType='intel-driveinfo-zip-v1', failureFile=None, metaDataFile=None, contentFile=None):
        """
        API for send Command function that returns the AXON ID for a successful upload
        Args:
            fileType(str): file type of content file for upload
            failureFile(json): json file containing data about a failure encountered in the accompanying telemetry binary
            metaDataFile(json): metadata containing information about the content file
            contentFile(fileType): file containing a binary or binaries of telemetry data gained from some drive

        Returns:
            success(bool): Containes whether the upload was successful
            line(str): Contains output line from Axon about AXON ID

        """
        success = False
        self.axonID = None
        AXON_OUTPUT_DECODE = "(AxonID)\s*:\s*(\S*)"

        # Run command and grab output from AXON
        (exitCode, cmdOutput, cmdError) = self.sendCmd(fileType=fileType,
                                                       failureFile=failureFile,
                                                       metaDataFile=metaDataFile,
                                                       contentFile=contentFile)

        # Store AXON Codes in object
        self.exitCode = exitCode
        self.cmdOutput = cmdOutput
        self.cmdError = cmdError

        print("exitCode: ", exitCode)
        print("cmdOutput: ", cmdOutput)
        print("cmdError: ", cmdError)

        # Gather Axon ID and line containing report of Axon ID
        for line in cmdOutput.splitlines():
            match = re.search(AXON_OUTPUT_DECODE, line)
            if match is not None:
                self.axonID = str(match.group(2))
                success = True
                if self.debug:
                    print("acquired Axon ID from AXON: ", self.axonID)

        return success, self.axonID

    def sendAPI(self, tarball=None, metadata=None):
        """
        @summary: uses pyaxon to upload a record to Axon
        @param tarball: the collected zip data which will be uploaded to Axon
        @param metadata: the metadata dictionary associated with the packet. If None, packet will be extracted and the existing metadata file will be used.
        """
        """ @todo work in progress
        try:
            from svtools import axon_ingest as axon
            from svtools.axon_ingest import Failure
            axon_ingest_dir = os.path.join(self.path, "lib", "python", "packages", "axon_ingest")
            if os.path.exists(axon_ingest_dir):
                subprocess.check_call([sys.executable,
                                       "-m",
                                       "pip",
                                       "install",
                                       "--no-input",
                                       "--find-links",
                                       axon_ingest_dir,
                                       "svtools.axon_ingest"])
            axon.settings.DB_CLIENT = 'axon'
            axon.settings.LOGFILE_PATH = os.path.join(self.working_dir, 'axon_log.log')
            axon.settings.AXON_DB_SERVER = self.axon_env
            metadata = self.metaTemplate()
        except:
            print("Failure to import axon_ingest modules.")
            print(traceback.format_exc())
        """
        return metadata

    def receiveCmd(self, axonID=None, outputDirectory=os.getcwd()):
        """
        Sends AXON request to download a record based on the ID of the record
        Args:
            axonID[string]: the AXON Identification string that uniquely identifies a specific AXON record

        Returns:

        """
        if self.debug is False:
            # axon.exe create --url {} --type {} --failure @{} --metadata @{} --content @{}
            cmd = '{0} download --url {1} --id {2} --path {3}' \
                .format(
                self._AXON_EXE_FILE,  # {0} Executable
                self.URL,  # {1} Internal URL to upload content
                axonID,  # {2} Upload Type
                outputDirectory  # {3} Output directory for the downloaded content type
            )
        else:
            cmd = '{0} download --url {1} --id {2} --path {3} -vvvvv' \
                .format(
                self._AXON_EXE_FILE,  # {0} Executable
                self.URL,  # {1} Internal URL to upload content
                axonID,  # {2} Upload Type
                outputDirectory  # {3} Output directory for the downloaded content type
            )

        if (self.debug):
            print("Command is: ", cmd)

        if (sys.platform == 'win32' or os.name == 'os2'):
            args = cmd.split(' ')
            processCommand = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                              universal_newlines=True, shell=True)
        else:
            processCommand = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                              universal_newlines=True, shell=True)

        cmdOutput, cmdError = processCommand.communicate()
        exitCode = processCommand.returncode

        return exitCode, cmdOutput, cmdError

    def getIdentify(self):
        identify = {
            'uid': self.uid,
            'major': self.major,
            'minor': self.minor
        }
        return identify

    def saveIdentifyJSON(self, idenfityFile=None):

        if (idenfityFile is None):
            temporaryFolder, identifyFile = tempfile.mkstemp()
        else:
            with open(idenfityFile, 'w') as openFile:
                openFile.write("")
                openFile.close()

        identify = self.getIdentify()

        with open(idenfityFile, 'w') as fileJSON:
            json.dump(identify, fileJSON)

        return (identify, fileJSON)

    def saveJSON(self, saveFile=None, objectJSON=None):

        if (saveFile is None):
            temporaryFolder, saveFile = tempfile.mkstemp()

        if (objectJSON is None):
            objectJSON = self.zipTemplate()  # @todo extend

        with open(saveFile, 'w') as fileJSON:
            json.dump(objectJSON, fileJSON)

        return (objectJSON, fileJSON)

    def loadJSON(self, inJSONFile=None):
        metadata = json.loads(inJSONFile)
        metadataString = json.dumps(metadata)
        return metadataString

    def getHashFromCotentMetaData(self, metaDataFile):

        with open(metaDataFile, "r") as contentFile:
            metaData = json.load(contentFile)

            return metaData["sha256"]

    def validateDownload(self, outputLocation, axonID):
        """
        Function to return whether the received file is valid
        Args:
            outputLocation:
            axonID:

        Returns:

        """
        # Get hash from the created file
        ReceivedHash = self.secureHash(fileInput=os.path.join(outputLocation, axonID, self._received_content_file))

        # Get expected hash from the metadata file
        ExpectedHash = self.getHashFromCotentMetaData(os.path.join(outputLocation, axonID, self._received_meta_name))

        print("Received Hash: ", ReceivedHash)
        print("Expected Hash: ", ExpectedHash)

        return ReceivedHash == ExpectedHash

    class TestAxonProducer(unittest.TestCase):
        def setUp(self):
            print("Setup in test called")

        def tearDown(self):
            pass

        def test_create_large_file(self, fileName="largeFile.txt"):
            # This can be used to create a dummy JSON file
            axon_dir_location = os.path.join(self.path, self._AXON_NAME)
            full_path = os.path.join(axon_dir_location, fileName)
            number_of_keys = self._number_of_limiter_keys
            number_of_found_keys = self._number_of_found_keys
            with open(os.path.expanduser(full_path), "w") as f:
                f.write('{' + "\n")
                for x in range(number_of_keys):
                    f.write('"Key' + str(x) + '": ' + '"This is some value for a key"')
                    if (x != number_of_keys - 1):
                        f.write(',' + "\n")
                    number_of_found_keys = (number_of_found_keys + 1)
                f.write("\n" + '}')
                f.close()

        def test_send_page_data(self):
            drive_info_producer = src.software.axon.axonMeta.AXON_Meta()
            count = range(1)
            import time
            start_time = time.time()
            for n in count:
                self.assertNotEqual(drive_info_producer.sendInfo(""), None)
            print("Total time in seconds = %s" % (time.time() - start_time))


def setup(debug=True):
    state = None
    '''
    try:
        import setuptools, traceback
        state = setuptools.setup(
                      name='AXON Data Stream',
                      version='1.0',
                      author='Joseph Tarango',
                      author_email='no-reply@intel.com',
                      description='AXON Data Stream for Intel telemetry.',
                      url='http://github.com/StorageRelationalLibrary/src/software/axon/axonInterface.py',
                      packages=setuptools.find_packages(),
                      # classifiers
                      install_requires=[
                                        'keras',
                                        'numpy',
                                        'pandas',
                                        'matplotlib',
                                        'tensorflow',
                                       ],
                      classifiers=[
                                   # Optional
                                   # How mature is this project? Common values are
                                   #   3 - Alpha
                                   #   4 - Beta
                                   #   5 - Production/Stable
                                   'Development Status :: 3 - Alpha',
                                   # Indicate who your project is intended for
                                   'Intended Audience :: Developers',
                                   'Topic :: Software Development :: Build Tools',
                                   # Specify the Python versions you support here. In particular, ensure
                                   # that you indicate whether you support Python 2, Python 3 or both.
                                   # These classifiers are *not* checked by 'pip install'. See instead
                                   # 'python_requires' below.
                                   'Programming Language :: Python :: 3.7.7',
                                  ],
                      data_files=[
                                  ('my_data', ['trainingData/indata_file.dat'])
                                 ],  # Optional, In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
                     )
        if(debug is True):
                print("Setup State ", state)
    except:
        print("Exception within Install path.")
        print("The execution of the file requires setup tools. The command is pip install setup findpackages")
        print("Setup State ", state)
        traceback.print_exc()
    '''
    return state


def hollowShell(options=None):
    print("Running hollow AXON instance")
    # referenceTest = axon.axonMeta.AXON_Meta()
    # (exitCode, cmdOutput, cmdError) = referenceTest.sendCmd()

    referenceTest = Axon_Interface()
    (exitCode, cmdOutput, cmdError) = referenceTest.sendCmd(
        contentFile='/home/DarthVader/gui_tests/test_gui/test4/GatherData2020-07-30-19-56-14-123693.tar.gz')

    print("*" * 20, "Exit Code:", exitCode)
    print("*" * 20, "Command line output:", cmdOutput)
    print("*" * 20, "Command Error", cmdError)
    return


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

    ##############################################
    # Main
    ##############################################
    setup()
    hollowShell(options)
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
    print("\nExecution time: " + str(q - p))
