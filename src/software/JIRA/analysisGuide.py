#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: David Escamilla, Joseph Tarango
# *****************************************************************************/
# from __future__ import absolute_import, division, print_function, unicode_literals
# from __future__ import nested_scopes, generators, generator_stop, with_statement, annotations
import sys, requests, re, urllib3, os, dataclasses, traceback, datetime, optparse, pprint, getpass, difflib, \
    configparser, json, ast, tempfile, shutil

from bs4 import BeautifulSoup
from src.software.utilsCommon import tryFile, DictionaryFlatten
from src.software.debug import whoami


def anyObjectToDictionary(obj):
    """

    Args:
        obj:

    Returns:

    """
    return json.loads(json.dumps(obj, default=lambda o: o.__dict__))


def objectToDictionary(objectToWalk):
    """

    Args:
        objectToWalk:

    Returns:

    """
    return dict(
        (key, getattr(objectToWalk, key)) for key in dir(objectToWalk) if key not in dir(objectToWalk.__class__))


def getFlattenDictionary(dd, separator='_', prefix=''):
    """

    Args:
        dd:
        separator:
        prefix:

    Returns:

    """
    return {prefix + separator + k if prefix else k: v
            for kk, vv in dd.items()
            for k, v in getFlattenDictionary(vv, separator, kk).items()
            } if isinstance(dd, dict) else {prefix: dd}


def getSuperDictionary(obj=None, debug=False):
    """

    Args:
        obj:
        debug:

    Returns:

    """
    objDictAny = anyObjectToDictionary(obj)
    if debug:
        print(objDictAny, flush=True)
    objDictAny = getFlattenDictionary(dd=objDictAny, separator='_', prefix='')
    return objDictAny


class HandbookMeta(object):
    def __init__(self, code=None, analysisUIDs=None, knownCauses=None, url=None):
        self.code = code
        self.analysisUIDs = analysisUIDs
        self.knownCauses = knownCauses
        self.url = url

    def set_code(self, extractedValue=None):
        """

        Args:
            extractedValue:

        Returns:

        """
        self.code = extractedValue

    def set_analysisUIDs(self, extractedValue=None):
        """

        Args:
            extractedValue:

        Returns:

        """
        self.analysisUIDs = extractedValue

    def set_knownCauses(self, extractedValue=None):
        """

        Args:
            extractedValue:

        Returns:

        """
        self.knownCauses = extractedValue

    def set_url(self, extractedValue=None):
        """

        Args:
            extractedValue:

        Returns:

        """
        self.url = extractedValue


class AnalysisGuide(object):
    _debug = False
    _username = "PresidentSkroob@spaceballs.one"
    _password = "12345"
    handbookInfo = None
    loadedINI = None

    _proxyDict = {
        "http": "http://proxy-us.intel.com:911/",
        "https": "https://proxy-us.intel.com:912/",
        "ftp": "http://proxy-chain.intel.com:1080",
        "no_proxy": "127.0.0.1,localhost,.local",
        "pacfile": "http://autoproxy.iglb.intel.com/wpad.dat"
    }

    _urlDict = {
        "default": "https://nsg-wiki.intel.com/",
        "handbook": "https://nsg-wiki.intel.com/display/DH/Debug+Handbook",
        "assert": "https://nsg-wiki.intel.com/display/DH/Assert+Full+Listing",
        "assertDecode": "https://nsg-wiki.intel.com/display/DH/ASSERT_",
        "assertView": "https://nsg-wiki.intel.com/pages/viewpage.action?spaceKey=DH&title=ASSERT_",
        "badContext": "https://nsg-wiki.intel.com/display/DH/Bad+Context#BadContext-BadContext",
        "wiki": "https://nsg-wiki.intel.com/pages/viewpage.action?spaceKey=DH&title=",
        "wearLevel": "https://nsg-wiki.intel.com/display/DH/Wear+Leveling+Issues",
        "healthy": "https://nsg-wiki.intel.com/display/FW/PQ+Working+on+Performance"
        # Add content evaluation for healthy systems. Comprehension of health status without execution of a test.
    }

    _testDict = ["DE003", "DF013", "DF049", "DF064", "DF081", "DF082", "DF083", "DF084", "MB049"]

    _ppIndent = 3
    _ppWidth = 100

    @dataclasses.dataclass()
    class FirmwareDataForAnalysis:
        def __init__(self, uid, name):
            self.uid = uid
            self.name = name

        def __repr__(self):
            return f"  {self.uid}, {self.name}"

        def __str__(self):
            return f"  {self.uid}, {self.name}"

    @dataclasses.dataclass()
    class FirmwareAssert:
        def __init__(self, assertCodeValue, debug=False):
            self.name = f"Assert_{assertCodeValue}"
            self.url = f"https://nsg-wiki.intel.com/pages/viewpage.action?spaceKey=DH&title=ASSERT_{assertCodeValue}"
            self.isFoundOnWeb = True
            self.knownCauses = []
            self.firmwareDataForAnalysis = []
            self._debug = debug

        def __repr__(self):
            return DictionaryFlatten().getSuperDictionary(self)

        def getDebugInfo(self):
            if self._debug:
                print(" Webpage Found? {}".format(str(self.isFoundOnWeb)))
                if self.isFoundOnWeb is True:
                    causeError = self.knownCauses is [] or self.knownCauses is None
                    dataError = self.firmwareDataForAnalysis is [] or self.firmwareDataForAnalysis is None
                    if causeError or dataError:
                        print("  Error detected: cause={}, data={}".format(self.knownCauses,
                                                                           self.firmwareDataForAnalysis))
                    else:
                        print("  Known Causes:", end='')
                        for itemCause in self.knownCauses:
                            if (itemCause is not None or itemCause != ''):
                                print("   {}".format(itemCause), end=',')

                        print("\n  FW_Data_For_Analysis:")
                        for itemData in self.firmwareDataForAnalysis:
                            if (itemData is not None and itemData != "None" and itemData != ''):
                                print(f"  [{itemData}],")

            return (self.knownCauses, self.firmwareDataForAnalysis)

        def __str__(self):
            return self.__repr__()

    def __init__(self, username=None, password=None, debug=False,
                 defaultPasswordFile="../../../.raadProfile/credentials.conf"):
        self.debug = debug
        self._debug = debug
        self.handbookInfo = None
        self.loadedINI = None

        if username is not None:
            self._username = username
        if password is not None:
            self._password = password
        if username is None and password is None:
            self._read_passwordFile(defaultFile=defaultPasswordFile)
        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        except BaseException as errorContext:
            urllib3.disable_warnings()
            print(errorContext)
            pprint.pprint(whoami())
            pass
        return

    def _read_passwordFile(self, defaultFile="../../../.raadProfile/credentials.conf"):
        """

        Args:
            defaultFile:

        Returns:

        """
        tryFile(fileName=defaultFile)
        defaultPasswordFile = os.path.abspath(os.path.join(os.getcwd(), defaultFile))
        if os.path.isfile(defaultPasswordFile):
            with open(defaultPasswordFile) as openFile:
                fileMeta = openFile.read()
                NSGWIKI = fileMeta.split('\n')  # Separator is \n 3
                self._username = NSGWIKI[0]
                self._password = NSGWIKI[1]
        return

    def setUsernamePassword(self, username=None, password=None):
        self._username = username
        self._password = password
        return

    def _get_urlHandbook(self):
        return self._urlDict["handbook"]

    def _get_urlAssert(self):
        return self._urlDict["assertDecode"]

    def _get_urlAssertCode(self, aTag, aValue):
        return "{}{}{}".format(self._urlDict["assertDecode"], aTag, aValue)

    def _get_urlAssertView(self, fullCode):
        return "{}{}".format(self._urlDict["assertView"], fullCode)

    def _get_urlBadContext(self, aValue):
        return "{}{}".format(self._urlDict["badContext"], aValue)

    def _get_urlWiki(self):
        return self._urlDict["wiki"]

    def _get_urlWearLevel(self):
        return self._urlDict["wearLevel"]

    def _handleData(self, FWAssertObj, data):
        """

        Args:
            FWAssertObj:
            data:

        Returns:

        """

        # Title
        title = data.partition('<title>')[-1].partition('</title>')[0]
        if str(title).lower().startswith("page not found"):
            FWAssertObj.isFoundOnWeb = False
            return

        # All known signatures for ending the data sections.
        cleaningTags = ["Known Causes</h3>",
                        "Firmware Data Necessary for Analysis</h3>",
                        "Firmware Software Prevention</h3>",
                        "Firmware Data Necessary for Analysis</h3>",
                        "ASIC - Hardware Components</h3>",
                        "Jiras</h3>"]

        # Shrink the data to limit the search
        # Processing known causes for developers. #
        known_causes = data.partition("Known Causes</h3>")[-1].partition("Firmware Data Necessary for Analysis</h3>")[0]

        # Cleans for all known ending tags.
        known_causes_New = known_causes
        for _, valueCleaner in enumerate(cleaningTags):
            known_causes_New = known_causes_New.partition(valueCleaner)[0]
        known_causes = known_causes_New
        # Clean HTML tags
        cleanCause = re.compile('<.*?>')
        cleanedCause = re.sub(cleanCause, '**', known_causes)
        cleanedCause = cleanedCause.split("**")

        # Processing data into data class format.
        for elem in cleanedCause:
            if elem and not '':
                FWAssertObj.knownCauses.append(elem)  # @todo These need to have accessors...

        # Processing known data to use. #
        fw_data_for_analysis = data.partition("Firmware Data Necessary for Analysis</h3>")[-1].partition("Jiras</h3>")[
            0]

        # Cleans for all known ending tags.
        fw_data_for_analysis_New = fw_data_for_analysis
        for _, valueCleaner in enumerate(cleaningTags):
            fw_data_for_analysis_New = fw_data_for_analysis_New.partition(valueCleaner)[0]
        fw_data_for_analysis = fw_data_for_analysis_New

        cleanAnalysis = re.compile('<.*?>')
        cleanedData = re.sub(cleanAnalysis, '**', fw_data_for_analysis)
        cleanedData = cleanedData.split("**")

        # Processing data into data class format.
        for elem in cleanedData:
            if elem and elem != '':
                fw_data = [x.strip() for x in elem.split(',')]
                fw_data_name = fw_data[-1]
                uid = 0 if len(fw_data) < 2 else fw_data[0]
                currentData = self.FirmwareDataForAnalysis(fw_data_name, uid)
                FWAssertObj.firmwareDataForAnalysis.append(currentData)  # @todo These need to have accessors...
        return

    def verifyAccess(self):
        """

        Returns:

        """
        return self._pageExists()

    def _pageExists(self, urlAddress=None):
        """

        Args:
            urlAddress:

        Returns:

        """
        status = False
        try:
            if urlAddress is None:
                urlAddress = self._get_urlHandbook()

            urlAddress = str(urlAddress)
            # User agent for white/blacklist
            USER_AGENT = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
            authed_session = requests.Session()  # Create a Session to contain you basic AUTH, it will also persist your cookies

            authed_session.auth = (self._username, self._password)  # Add credentials

            # WARNING: You should point this to your cert file for the server to actually
            # verify the host. Skips verification if set to false
            CERT_FILE = False
            authed_session.verify = CERT_FILE  # Cert verification, will not verify on false
            authed_session.headers.update({'User-Agent': USER_AGENT})

            # User details
            webpageResponse = authed_session.get(url=urlAddress, auth=(self._username, self._password))
            if self._debug:
                print(f"Webpage {urlAddress} Status: {webpageResponse.status_code}")

            if webpageResponse.status_code in [200, 201, 202, 203, 204, 205, 206]:
                status = True
            elif webpageResponse.status_code in [300, 301, 303, 304, 305, 307]:
                status = False
            elif webpageResponse.status_code in [400, 401, 404, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416,
                                                 417]:
                status = False
            elif webpageResponse.status_code in [500, 501, 502, 503, 504, 505]:
                status = False
            else:
                status = False

            if self._debug and status is True:
                print('Web site exists')
            elif self._debug and status is False:
                print('Web site does not exist')

        except Exception as ErrorFound:
            print(f"URL exception at {urlAddress}! Error is {ErrorFound}")

        return status

    def _setProxy(self):
        """

        Returns:

        """
        if self._pageExists():
            for key, value in self._proxyDict.items():
                os.environ[key] = value
        return

    def setUser(self, username=None, password=None):
        """

        Args:
            username:
            password:

        Returns:

        """
        if username is not None:
            self._username = username
        if password is not None:
            self._password = password
        return

    def queryWebpage(self, assertCode=None, outFileData="queryResult.txt"):
        """

        Args:
            assertCode:
            outFileData:

        Returns:

        """
        firmwareAssertMeta = None
        try:
            if assertCode is not None:
                # Set Proxy if needed (not sure)
                # self._setProxy()
                session = requests.Session()
                session.verify = False

                # To ignore errors
                try:
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                except:
                    urllib3.disable_warnings()
                    pass

                # User details
                if self._username is not None and self._password:
                    firmwareAssertMeta = self.FirmwareAssert(assertCodeValue=assertCode, debug=self._debug)
                    if firmwareAssertMeta is not None:
                        webpageResponse = session.get(url=firmwareAssertMeta.url, auth=(self._username, self._password))
                        metaData = webpageResponse.text
                        self._handleData(firmwareAssertMeta, metaData)
                        if self._debug:
                            print("Known Causes:")
                            pprint.pprint(firmwareAssertMeta.knownCauses)
                            print("Analysis Data:")
                            pprint.pprint(firmwareAssertMeta.firmwareDataForAnalysis)
                        if outFileData is not None:
                            with open(outFileData, 'a') as openFile:
                                if self._debug:
                                    print("Appending to file: {}".format(outFileData))
                                openFile.write("[TAG-RAD_START]\n")
                                openFile.write("[{}]\n".format(firmwareAssertMeta.name))  # Fault tag

                                openFile.write("[Known_Causes]\n")  # Known Cause tags
                                openFile.write(
                                    pprint.pformat(object=firmwareAssertMeta.knownCauses, indent=self._ppIndent,
                                                   width=self._ppWidth))

                                openFile.write("\n[Analysis_Data]\n")  # Telemetry Meta tags
                                openFile.write(pprint.pformat(object=firmwareAssertMeta.firmwareDataForAnalysis,
                                                              indent=self._ppIndent,
                                                              width=self._ppWidth))
                                openFile.write("\n[TAG-RAD_STOP]\n\n")
        except BaseException as ErrorContext:
            pprint.pprint(f"WARNING: {whoami()}{os.linesep}{ErrorContext}")
            pass
        return firmwareAssertMeta

    def get_allMeta(self, username=None, password=None, outFileData="queryTesting.txt", debug=True):
        """
        F
        Args:
            username:
            password:
            outFileData:
            debug:

        Returns:

        """
        status = False
        if username is not None and password is not None:
            internalUser = self._username
            internalPassword = self._password
            self._username = username
            self._password = password
            handbookInfo = []
            if username is not None and password is not None:
                for codeIndex, codeValue in enumerate(self._testDict):
                    if self._debug or debug is True:
                        print("Info {}: {}".format(str(codeIndex), str(codeValue)))
                    decodedInfo = self.queryWebpage(assertCode=codeValue, outFileData=outFileData)
                    handbookInfo.append(decodedInfo)
                self.handbookInfo = handbookInfo
            self._username = internalUser
            self._password = internalPassword
            status = True
        return status

    def pageLogin(self, urlPageBase, urlPageExtLogin, login, password):
        """

        Args:
            urlPageBase:
            urlPageExtLogin:
            login:
            password:

        Returns:

        """
        if urlPageBase is None:
            urlPageBase = 'https://site.com/'
        if urlPageExtLogin is None:
            urlPageExtLogin = 'accounts/login/'

        HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
            'origin': urlPageBase,
            'referer': urlPageBase + urlPageExtLogin}
        activeSession = requests.session()
        csrf_token = activeSession.get(urlPageBase).cookies['csrftoken']
        login_payload = {'login': login,
                         'password': password,
                         'csrfmiddlewaretoken': csrf_token}
        login_req = activeSession.post(urlPageBase + urlPageExtLogin, headers=HEADERS, data=login_payload)
        print(login_req.status_code)
        cookies = login_req.cookies
        soup = BeautifulSoup(activeSession.get(urlPageBase + 'watchlist').text, 'html.parser')
        tbody = soup.find('table', id='companies')
        print(tbody)
        return

    def getAllLinks(self, startURL: str = None, findTag: str = None):
        """

        Args:
            startURL:
            findTag:

        Returns:

        """
        from bs4 import BeautifulSoup
        from urllib.request import Request, urlopen

        if startURL is None:
            findURL = self._urlDict["handbook"]
        else:
            findURL = startURL

        req = Request(findURL)
        html_page = urlopen(req)

        soup = BeautifulSoup(html_page, "lxml")

        webLinks = list()
        for link in soup.findAll(findTag):
            webLinks.append(link.get('href'))
        if self.debug:
            print(webLinks)
        return webLinks

    @staticmethod
    def create_temporary_fileSplit_copy(path='.', fileCopyName='real.dump', tempFileName='temp_file_name.dump'):
        """

        Args:
            path:
            fileCopyName:
            tempFileName:

        Returns:

        """
        realFilePath = os.path.abspath(os.path.join(path, fileCopyName))
        if os.path.exists(realFilePath):
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, tempFileName)
            shutil.copy2(realFilePath, temp_path)
            fileToUse = temp_path
        else:
            fileToUse = None
        return fileToUse

    @staticmethod
    def create_temporary_file_copy(fileCopyName=None, tempFileName=None):
        """

        Args:
            fileCopyName:
            tempFileName:

        Returns:

        """
        if fileCopyName is None:
            fileCopyName = '../real.dump'
        if tempFileName is None:
            tempFileName = (fileCopyName + "tmp.dump")
        realFilePath = os.path.abspath(fileCopyName)
        if os.path.exists(realFilePath):
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, tempFileName)
            shutil.copy2(realFilePath, temp_path)
            fileToUse = temp_path
        else:
            fileToUse = None
        return fileToUse

    def pythonAPI(self,
                  selectedMode=2,
                  defaultFile=".raadProfile/credentials.conf",
                  default_username="PresidentSkroob@spaceballs.one",
                  default_password="12345",
                  outputFile=".raadProfile/debugHandbookCache.ini",
                  searchString="ASSERT_DE003",  # "ASSERT_DF049"
                  simularityScoreThreshold=0.95):
        """

        Args:
            selectedMode:
            defaultFile:
            default_username:
            default_password:
            outputFile:
            searchString:
            simularityScoreThreshold:

        Returns:

        """
        tempFileExists = False
        backupFile = None
        defaultTestFile = None
        try:
            NSGWikiUsername = None
            NSGWikiPassword = None
            defaultFile = tryFile(fileName=defaultFile)
            defaultPasswordFile = os.path.isfile(defaultFile)
            default_UP = (default_username == "PresidentSkroob@spaceballs.one" and default_password == "12345")
            none_UP = (default_username is None and default_password is None)
            if int(selectedMode) == 1:
                # Mode 1 use given username and password
                if default_UP is False and none_UP is False:
                    NSGWikiUsername = default_username
                    NSGWikiPassword = default_password
                    self.setUsernamePassword(username=default_username, password=default_password)
                elif os.path.isfile(defaultFile):
                    with open(defaultPasswordFile) as openFile:
                        fileMeta = openFile.read()
                        NSGWIKI = fileMeta.split('\n')  # Separator is \n 3
                        NSGWikiUsername = NSGWIKI[0]
                        NSGWikiPassword = NSGWIKI[1]
                        self.setUsernamePassword(username=NSGWikiUsername, password=NSGWikiPassword)
            elif int(selectedMode) == 2:
                # Mode 2 use password file then update...
                with open(defaultFile) as openFile:
                    fileMeta = openFile.read()
                    NSGWIKI = fileMeta.split('\n')  # Separator is \n 3
                    NSGWikiUsername = NSGWIKI[0]
                    NSGWikiPassword = NSGWIKI[1]
                    self.setUsernamePassword(username=NSGWikiUsername, password=NSGWikiPassword)
            elif int(selectedMode) == 3:
                # Mode 3 Create User password file then update...
                if not default_UP:
                    with open(defaultFile, "w") as file:
                        file.write(default_username)
                        file.write(default_password)
                    NSGWikiUsername = default_username
                    NSGWikiPassword = default_password
                    self.setUsernamePassword(username=default_username, password=default_password)
            webPageExists = self._pageExists()
            if webPageExists is True:
                if not os.path.isfile(outputFile):
                    with open(outputFile, 'w') as f:
                        pass
                defaultTestFile = tryFile(fileName=outputFile)

                tempCacheFile = (defaultTestFile + ".cache.ini")
                if os.path.isfile(defaultTestFile):
                    if self._debug:
                        print("Copying and Deleting previous ini file {}...".format(defaultTestFile))
                    backupFile = self.create_temporary_file_copy(fileCopyName=defaultTestFile,
                                                                 tempFileName=tempCacheFile)
                    tempFileExists = True
                    os.remove(defaultTestFile)
                downloadFile = (defaultTestFile + ".download.ini")
                testingValid = self.get_allMeta(username=NSGWikiUsername, password=NSGWikiPassword,
                                                outFileData=downloadFile)
                if testingValid and searchString is not None:
                    dataMatch = self.searchForSignature(signature=searchString,
                                                        similarityScore=simularityScoreThreshold)
                    self.writeINIFile(saveFile=defaultTestFile)
                    if self.debug:
                        print(f"Data found through crawling:")
                        dataFoundDictionary = getSuperDictionary(obj=self.handbookInfo, debug=False)
                        pprint.pprint(dataFoundDictionary)
                        print(f"Data Match {searchString} with threshold {simularityScoreThreshold} with results:")
                        pprint.pprint(dataMatch)

                foundMetaDictionary = self.getINIFileDictionary(loadFile=defaultTestFile)
                foundMetaClass = self.getINIFileClass(loadFile=defaultTestFile)
                if self.debug:
                    print("Found Meta Dictionary:")
                    pprint.pprint(foundMetaDictionary)
                    print("Found Meta Class:")
                    pprint.pprint(getSuperDictionary(obj=foundMetaClass, debug=False))
        except BaseException as ErrorFound:
            pprint.pprint(whoami())
            print(f"ERROR with {ErrorFound}.\n Possible invalid username, password, file, etc.")
            try:
                if tempFileExists is True:
                    shutil.copy2(defaultTestFile, backupFile)
            except BaseException as ErrorFoundDoubleRainbow:
                pprint.pprint(whoami())
                print(f"ERROR with {ErrorFoundDoubleRainbow}.\n Backup file does not exist.")
            return None

        return self.handbookInfo

    def performUserInputAPI(self,
                            selectedMode=2,
                            defaultFile="../../../.raadProfile/credentials.conf",
                            default_username="PresidentSkroob@spaceballs.one",
                            default_password="12345",
                            outputFile="../../../data/queryTesting.txt"):
        """

        Args:
            selectedMode:
            defaultFile:
            default_username:
            default_password:
            outputFile:

        Returns:

        """
        defaultPasswordFile = None
        if selectedMode == 1:
            NSGWikiUsername = input('Enter username: ')
            NSGWikiPassword = getpass.getpass(prompt='Enter password: ', stream=sys.stderr)
            with open(defaultFile, "w") as file:
                file.write(NSGWikiUsername)
                file.write(NSGWikiPassword)
        else:  # selectedMode = 2 or 3
            tryCount = 0
            if self._debug:
                print("Default file example location {}".format(defaultFile))
            defaultPasswordFile = os.path.abspath(os.path.join(os.getcwd(), defaultFile))

            if self._debug:
                print("Default content of file format:\n{}\n{}".format(default_username, default_password))

            passwordFileExists = os.path.isfile(defaultPasswordFile)
            if selectedMode == 3 and not passwordFileExists:  # Allow interactive mode with a file
                while os.path.exists(defaultPasswordFile) is False:
                    defaultPasswordFile = getpass.getpass(prompt=(
                        'Try Count {}, Previous input {}\n Enter file with username and password:'.format(tryCount,
                                                                                                          defaultPasswordFile)),
                                                          stream=sys.stderr)
            elif ((selectedMode == 2 or selectedMode == 3) and passwordFileExists):
                if self._debug:
                    print(f"Entering Mode {selectedMode}")
            else:
                return None  # No password file found return nil.
        try:
            print("File Location {}".format(defaultPasswordFile))
            with open(defaultPasswordFile) as openFile:
                fileMeta = openFile.read()
                NSGWIKI = fileMeta.split('\n')  # Separator is \n 3
                NSGWikiUsername = NSGWIKI[0]
                NSGWikiPassword = NSGWIKI[1]
            defaultTestFile = os.path.abspath(os.path.join(os.getcwd(), outputFile))
            if os.path.isfile(defaultTestFile):
                if self._debug:
                    print("Deleting previous test file {}...".format(defaultTestFile))
                os.remove(defaultTestFile)
            testingValid = self.get_allMeta(username=NSGWikiUsername, password=NSGWikiPassword,
                                            outFileData=defaultTestFile)
            if testingValid is True and self._debug:
                print("Passed testing...")
            elif testingValid is False and self._debug:
                print("Failed testing...")
        except:
            pass
        return self.handbookInfo

    def getHandbookInfo(self):
        return self.handbookInfo

    def searchForSignature(self,
                           signature="ASSERT_DE003",  # "ASSERT_DF049"
                           similarityScore=1.0):
        """
        Searches for specific signature
        Args:
            signature:
            similarityScore:

        Returns:

        """
        if self.handbookInfo is not None:
            for indexAt, handbookSignature in enumerate(self.handbookInfo):
                signatureUpper = str(signature).upper()
                handbookUpper = handbookSignature.name.upper()
                sScore = difflib.SequenceMatcher(None, handbookUpper, signatureUpper).ratio()
                if (sScore >= similarityScore):
                    uidValueList = list()
                    uidNameList = list()
                    for indexItem, rowItem in enumerate(handbookSignature.firmwareDataForAnalysis):
                        if rowItem is not None:
                            uidValueExtracted = int(rowItem.name)
                            if isinstance(uidValueExtracted, int):
                                uidValueList.append(uidValueExtracted)
                            uidNameExtracted = str(rowItem.uid)
                            if isinstance(uidNameExtracted, str):
                                uidNameList.append(uidNameExtracted)
                    return (uidNameList, uidValueList, handbookSignature.knownCauses, handbookSignature.url)
        return (None, None, None, None)

    def searchForSignatureFromCode(self,
                                   signature="ASSERT_DE003",  # "ASSERT_DF049"
                                   similarityScore=1.0):
        """
        Signature search and match threshold
        Args:
            signature:
            similarityScore:

        Returns:

        """
        if self.handbookInfo is not None:
            for indexAt, handbookSignature in enumerate(self.handbookInfo):
                signatureUpper = str(signature).upper()
                handbookUpper = handbookSignature.code.upper()
                sScore = difflib.SequenceMatcher(None, handbookUpper, signatureUpper).ratio()
                if (sScore >= similarityScore):
                    # handbookSignature.analysisUIDs, handbookSignature.knownCauses, handbookSignature.url
                    if hasattr(handbookSignature, 'analysisUIDs'):
                        uidObj = handbookSignature.analysisUIDs
                    else:
                        uidObj = [5, 6, 8, 10, 20, 41, 52, 55, 56, 58, 88, 247]
                        print(f"WARNING: UIDs cannot be found.{os.linesep}{whoami()}")

                    if hasattr(handbookSignature, 'knownCauses'):
                        knownCausesObj = handbookSignature.knownCauses
                    else:
                        knownCausesObj = ["Device functional in current state.",
                                          "Silent failure.",
                                          "Performance Analysis.",
                                          "Manufacturing preparation."]
                        print(f"WARNING: Known Causes cannot be found.{os.linesep}{whoami()}")

                    if hasattr(handbookSignature, 'url'):
                        urlObj = handbookSignature.url
                    else:
                        urlObj = "https://nsg-wiki.intel.com/display/DH/HEALTHY"
                        print(f"WARNING: URL cannot be found.{os.linesep}{whoami()}")

                    signatureMeta = {"uid": uidObj,
                                     "knownCauses": knownCausesObj,
                                     "url": urlObj}
                    return signatureMeta
        signatureMeta = {"uids": None,
                         "knownCauses": None,
                         "url": None}
        return signatureMeta

    def writeINIFile(self, saveFile='../../../.raadProfile/debugHandbookCache.ini'):
        """

        Args:
            saveFile:

        Returns:

        """
        write_config = configparser.ConfigParser()

        # Access Time of File
        # dt = datetime.datetime.now()
        # utc_time = dt.replace(tzinfo=datetime.timezone.utc)
        # utc_timestamp = utc_time.timestamp()
        # write_config.add_section('TIME')
        # write_config.set('TIME', 'LAST_UPDATE', str(utc_timestamp))

        # Create a section for each known signature code
        for indexAt, handbookSignature in enumerate(self.handbookInfo):
            # Fault Signature
            handbookSignatureName = (handbookSignature.name).upper()
            write_config.add_section(handbookSignatureName)

            # Webpage URL for content
            write_config.set(handbookSignatureName, 'url', f"'{handbookSignature.url}'")

            # UIDs to Analyze list
            uidValueList = []
            uidNameList = []
            for indexItem, rowItem in enumerate(handbookSignature.firmwareDataForAnalysis):
                if rowItem is not None:
                    uidValueExtracted = int(rowItem.name)
                    if isinstance(uidValueExtracted, int):
                        uidValueList.append(uidValueExtracted)
                    uidNameExtracted = str(rowItem.uid)
                    if isinstance(uidNameExtracted, str):
                        uidNameList.append(uidNameExtracted)
            uidValueList = list(sorted(set(uidValueList)))  # Keep unique items.
            uidNameList = list(sorted(set(uidNameList)))  # Keep unique items.
            if self._debug:
                print("Name list of uids are: ")
                pprint.pprint(uidNameList)
            uidList = "["
            for uidIndex, uidValue in enumerate(uidValueList):
                if uidValue is not None and isinstance(uidValue, int):
                    uidList = f"{uidList}{uidValue}"
                    if uidIndex < len(uidValueList) - 1:
                        uidList = f"{uidList}, "
            uidList = f"{uidList}]"
            write_config.set(handbookSignatureName, "uids", uidList)

            # Reasons List
            reasonList = []
            for indexItem, rowItem in enumerate(handbookSignature.knownCauses):
                if rowItem is not None:
                    knownCauseExtracted = str(rowItem)
                    if isinstance(knownCauseExtracted, str):
                        reasonList.append(knownCauseExtracted)
            if handbookSignatureName == 'ASSERT_DF049':  # @todo: stella hardcode to eliminate extra text from website, need to be automated
                reasonList = reasonList[0:7]
            reasonList = list(sorted(set(reasonList)))  # Keep unique items. #@todo: stella update reasonlist
            # knownCausesList = "["
            knownCausesList = []
            for knownCauseIndex, knownCauseItem in enumerate(reasonList):
                if knownCauseItem is not None and isinstance(knownCauseItem, str):
                    # knownCausesList = f"{knownCausesList}'{knownCauseItem}', "
                    # if knownCauseIndex < len(reasonList) - 1:
                    #    knownCausesList = f"{knownCausesList}, "
                    knownCausesList.append(knownCauseItem)
            # knownCausesList = f"{knownCausesList}]"
            if len(knownCausesList) > 1:
                knownCausesList = list(sorted(set(knownCausesList)))  # @todo: stella update knownCauses
            # knownCausesList = f"{knownCausesList}"
            knownCausesList = f"{reasonList}"
            write_config.set(handbookSignatureName, "known_causes", knownCausesList)
        saveFile = 'data/output/debugHandbookCache.ini'  # @todo stella, hard coding
        cfgfile = open(saveFile, 'w')
        write_config.write(cfgfile)
        cfgfile.close()
        return

    def getINIFileDictionary(self, loadFile='../../../.raadProfile/debugHandbookCache.ini'):
        """
        returns a dictionary with keys of the form
        <section>.<option> and the corresponding values
        """
        if not os.path.exists(os.path.join(os.getcwd(), loadFile)):
            return
        config = {}
        loadedConfig = configparser.ConfigParser()
        loadedConfig.read(loadFile)

        for sec in loadedConfig.sections():
            for option, value in loadedConfig.items(sec):
                try:
                    extractedValue = ast.literal_eval(value)
                except:
                    extractedValue = str(value)
                config[f"{sec}.{option}"] = extractedValue
        self.loadedINI = config
        return config

    def getINIFileClass(self, loadFile='../../../.raadProfile/debugHandbookCache.ini'):
        """

        Args:
            loadFile:

        Returns:

        """
        if not os.path.exists(os.path.join(os.getcwd(), loadFile)):
            return
        loadedConfig = configparser.ConfigParser()
        loadedConfig.read(loadFile)

        handBookInfoList = []
        for sec in loadedConfig.sections():
            handBookItem = HandbookMeta()  # Create handbook object
            handBookItem.set_code(sec)
            for option, value in loadedConfig.items(sec):
                try:
                    extractedValue = ast.literal_eval(value)
                except:
                    extractedValue = str(value)
                strOption = str(option)
                # Add values to class
                typeKC = (strOption == 'known_causes')
                typeURL = (strOption == 'url')
                typeAUID = (strOption == 'uids')
                if typeKC:
                    handBookItem.set_knownCauses(extractedValue)
                elif typeURL:
                    handBookItem.set_url(extractedValue)
                elif typeAUID:
                    handBookItem.set_analysisUIDs(extractedValue)
            handBookInfoList.append(handBookItem)

        self.handbookInfo = handBookInfoList
        return handBookInfoList

    def loadAll(self, loadFile='../../../.raadProfile/debugHandbookCache.ini'):
        """

        Args:
            loadFile:

        Returns:

        """
        if self._pageExists() is False:
            # Skip steps and see if cache file exists
            statusFlag = self.loadCache(loadFile=loadFile)
        else:
            statusFlag = self.loadLive(saveFile=loadFile)
        return statusFlag

    def loadLive(self, saveFile='../../../.raadProfile/debugHandbookCache.ini'):
        """

        Args:
            saveFile:

        Returns:

        """
        statusFlag = False
        try:
            dataFound = self.performUserInputAPI(selectedMode=2)
            self.writeINIFile(saveFile=saveFile)
            foundMetaDictionary = self.getINIFileDictionary(loadFile=saveFile)
            foundMetaClass = self.getINIFileClass(loadFile=saveFile)
            if self._debug:
                print(f"Data found through crawling:")
                dataFoundDictionary = getSuperDictionary(obj=dataFound, debug=False)
                pprint.pprint(dataFoundDictionary)
                print("Found Meta Dictionary:")
                pprint.pprint(foundMetaDictionary)
                print("Found Meta Class:")
                pprint.pprint(getSuperDictionary(obj=foundMetaClass, debug=False))
        except:
            statusFlag = False
        else:
            statusFlag = True
        finally:
            return statusFlag

    def loadCache(self, loadFile='../../../.raadProfile/debugHandbookCache.ini'):
        """

        Args:
            loadFile:

        Returns:

        """
        statusFlag = False
        if os.path.exists(os.path.join(os.getcwd(), loadFile)):
            foundMetaDictionary = self.getINIFileDictionary(loadFile=loadFile)  # config
            foundMetaClass = self.getINIFileClass(loadFile=loadFile)  # handBookInfoList
            if self._debug:
                print("Found Meta Dictionary:")
                pprint.pprint(foundMetaDictionary)
                print("Found Meta Class:")
                pprint.pprint(getSuperDictionary(obj=foundMetaClass, debug=False))
            statusFlag = True
        return statusFlag

    def loadCacheAndSearch(self, loadFile='../../../.raadProfile/debugHandbookCache.ini',
                           signature="ASSERT_DE003",  # "ASSERT_DF049"
                           similarityScore=0.95):
        """

        Args:
            loadFile:
            signature:
            similarityScore:

        Returns:

        """
        uidNameList = uidValueList = knownCauses = url = None
        if self.handbookInfo is None or self.loadedINI is None:
            statusFlag = self.loadCache(loadFile=loadFile)
            if statusFlag is False:
                return (statusFlag, uidNameList, uidValueList, knownCauses, url)
        dataMatch = self.searchForSignature(signature=signature, similarityScore=similarityScore)
        statusFlag = all(dataMatchToken is None for dataMatchToken in dataMatch)
        (uidNameList, uidValueList, knownCauses, url) = dataMatch
        return (statusFlag, uidNameList, uidValueList, knownCauses, url)


def unitTest(options):
    """

    Args:
        options:

    Returns:

    """
    testInterface = AnalysisGuide(debug=options.debug)
    dataFound = None
    tryCount = 0
    maxTryCount = 3
    tryAgain = True

    if testInterface._pageExists() is False:
        if options.debug:
            print("NSG URL does not exist!")
        # Skip steps and see if cache file exists
        loadFile = ('../../../.raadProfile/debugHandbookCache.ini')
        if not os.path.exists(os.path.join(os.getcwd(), loadFile)):
            return False  # Cache file does not exist
    else:
        # We can attach to the URL so download latest
        while tryAgain is True:
            dataFound = testInterface.performUserInputAPI(selectedMode=3)
            if dataFound is None and tryCount <= maxTryCount:
                tryAgain = True
            else:
                tryAgain = False
            if options.debug is True:
                print(f"Try Attempt {tryCount} of {maxTryCount} and trying Again is {tryAgain}")
            tryCount += 1
        searchString = "ASSERT_DE003"  # "ASSERT_DF049"
        similarityScoreThreshold = 0.95
        dataMatch = testInterface.searchForSignature(signature=searchString, similarityScore=similarityScoreThreshold)
        testInterface.writeINIFile()
        if options.debug:
            print(f"Data found through crawling:")
            dataFoundDictionary = getSuperDictionary(obj=dataFound, debug=False)
            pprint.pprint(dataFoundDictionary)
            print(f"Data Match {searchString} with threshold {similarityScoreThreshold} with results:")
            pprint.pprint(dataMatch)

    foundMetaDictionary = testInterface.getINIFileDictionary()
    foundMetaClass = testInterface.getINIFileClass()
    if options.debug:
        print("Found Meta Dictionary:")
        pprint.pprint(foundMetaDictionary)
        print("Found Meta Class:")
        pprint.pprint(getSuperDictionary(obj=foundMetaClass, debug=False))
    return True


def main():
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("-e", "--example",
                      default=False,
                      help='Show command execution example.')
    parser.add_option("-d", "--debug",
                      action='store_true',
                      dest='debug',
                      default=True,
                      help='Debug mode.')
    parser.add_option("-v", "--verbose",
                      action='store_true',
                      dest='verbose',
                      default=False,
                      help='Verbose printing for debug use.')
    parser.add_option("-m", "--mode",
                      dest='mode',
                      default=2,
                      help='Mode for password reading: 1=Commandline enter, 2=File read.')
    (options, args) = parser.parse_args()

    print("Output Options:")
    pprint.pprint(options)
    print("Output Args:")
    pprint.pprint(args)
    ##############################################
    # Main
    ##############################################
    print(f"Unit Testing Status: {unitTest(options)}")
    return 0


if __name__ == '__main__':
    """Performs execution delta of the process."""
    pStart = datetime.datetime.now()
    try:
        main()
    except Exception as errorMain:
        print("Fail End Process: {0}".format(errorMain))
        traceback.print_exc()
    qStop = datetime.datetime.now()
    print("Execution time: " + str(qStop - pStart))
