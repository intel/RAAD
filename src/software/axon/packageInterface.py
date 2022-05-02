#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
# @package packageInterface
import os, datetime, json, traceback, tempfile, tarfile, gnupg, zipfile
import base64, binascii, random, string
import Crypto  # conda install -c conda-forge pycryptodome
import Crypto.Random
import Crypto.Cipher.AES

from pprint import pprint

"""
Brief:

Description:
    Layout packageInterface.py
        <Text Template>
        <import items>
        myNameIdentify = templateUtility()
        myNameIdentify.execute()
        <Other Code>
"""


class packageInterface(object):
    _telemetryPayloadBytes = 33554432
    def __init__(self,
                 uid=(-1),
                 major=(-1),
                 minor=(1),
                 time=datetime.datetime.now(),
                 user="DarthVader",
                 debug=True,
                 absPath=None,
                 binaryFileList=None,
                 jsonFileList=None,
                 timeSeriesFile=None,
                 logFileList=None,
                 pdfFileList=None,
                 outFileName=None):

        if (debug is True):
            print('packageInterface init called')

        __origin__ = 'packageInterface.py :Joseph Tarango :05-12-2020 11:58:00'
        self.uid = uid
        self.major = major
        self.minor = minor

        # Meta tracking data
        self.time = time
        self.user = user
        self.debug = debug

        if os.path.exists(absPath):
            self.absPath = absPath
        else:
            self.absPath = os.path.dirname(os.path.abspath(__file__))

        if (binaryFileList is None):
            self.binaryFileList = self.__gatherFileList([".bin"])
        else:
            self.binaryFileList = []

        if (jsonFileList is None):
            self.jsonFileList = self.__gatherFileList([".json"])
        else:
            self.jsonFileList = []

        if (timeSeriesFile is None):
            self.timeSeriesFile = self.__gatherFileList([".ini", ".csv"])
        else:
            self.timeSeriesFile = [timeSeriesFile]

        if (logFileList is None):
            self.logFileList = self.__gatherFileList([".log", ".txt", ".rc", ".tex"])
        else:
            self.logFileList = [logFileList]

        if (pdfFileList is None):
            self.pdfFileList = self.__gatherFileList([".pdf"])
        else:
            self.pdfFileList = [pdfFileList]

        if (outFileName is None):
            self.zipFile = "telemetry_UTC.zip"
            self.encryptedZipFile = None
        else:
            self.zipFile = None
            self.encryptedZipFile = None

        if (self.debug):
            print("__origin__", ":", __origin__)

            print("self.uid", ":", self.uid)
            print("self.major", ":", self.major)
            print("self.minor", ":", self.minor)

            print("self.time", ":", self.time)
            print("self.user", ":", self.user)
            print("self.debug", ":", self.debug)

            print("self.absPath", ":", self.absPath)

            print("self.binaryFileList", ":", self.binaryFileList)
            print("self.jsonFileList", ":", self.jsonFileList)
            # print("self.zipFile",                      ":", self.path                        )
            print("self.encryptedZipFile", ":", self.encryptedZipFile)

            self.personIdentification = {'email': None,  # President.Skroob@spaceball.one
                                         'passphrase': None,  # 12345
                                         'gnupghome': None,  # Planet_Spaceball
                                         'keyFile': None,  # ludicrousSpeed.asc
                                         'key': None}  # luggage
            self.profilePopulated = False
        return

    #############################
    ####### PACKAGE TOOLS #######
    #############################
    def createTarball(self, tarFileName="tarBall.tar", mode='w'):
        """
        Mode  Description
        r      Opens a TAR file for reading.
        r:      Opens a TAR file for reading with no compression.
        w or w:  Opens a TAR file for writing with no compression.
        a or a:  Opens a TAR file for appending with no compression.
        r:gz  Opens a TAR file for reading with gzip compression.
        w:gz  Opens a TAR file for writing with gzip compression.
        r:bz2  Opens a TAR file for reading with bzip2 compression.
        w:bz2  Opens a TAR file for writing with bzip2 compression.
        """
        # Create Tar file
        tFile = tarfile.open(tarFileName, mode)
        for fileItem in self.jsonFileList:
            tFile.add(fileItem)
        for fileItem in self.binaryFileList:
            tFile.add(fileItem)

        # List files in tar
        for fileList in tFile.getnames():
            print("Added %s" % fileList)
        tFile.close()

    def createZIP(self, zipFileName='zipFile.zip'):
        """

        Args:
            zipFileName: Name of file that will hold the zipped directory

        Returns:
            None
        """
        Package_Zip = zipfile.ZipFile(zipFileName, 'w')

        unionSetFilelist = list(set(self.jsonFileList + self.binaryFileList + self.timeSeriesFile + self.logFileList))
        unionSetFilelist.sort()

        for fileItem in unionSetFilelist:
            Package_Zip.write(filename=fileItem, arcname=os.path.relpath(fileItem, self.absPath),
                              compress_type=zipfile.ZIP_DEFLATED)

        Package_Zip.close()
        return

    def extractTarball(self, pathToFiles="extraction", tarFile="compress.tar", encodingType='utf-8'):
        if tarfile.is_tarfile(tarFile):
            with tarfile.open(name=tarFile, mode='w|', bufsize=self._telemetryPayloadBytes) as tarball:
                tarList = tarball.getmembers()
                tarball.extractall(path=pathToFiles)
                tarball.close()
        return tarList

    def compressTarball(self, tarFile="compress.tar", mode='w:bz2', encodingType='utf-8'):
        tarFileName = None
        if os.path.exists(tarFile) and tarfile.is_tarfile(tarFile):
            cleanFileString = mode
            cleanFileString = cleanFileString.replace('a', '')
            cleanFileString = cleanFileString.replace('w', '')
            cleanFileString = cleanFileString.replace('r', '')
            cleanFileString = self.__cleanFileString(cleanFileString)
            tarFileName = tarFile + "." + cleanFileString
            # Create Tar file
            with tarfile.open(tarFileName, mode) as nutarFile:
                nutarFile.add(tarFile)
                nutarFile.close()
        else:
            if (self.debug):
                print(tarFile)
                assert ("compressTarball() invalid inputfile")
        return tarFileName

    def encryptTarball(self, dataToEncrypt="telemetry.bin", outfile="telemetry.bin.gpg"):
        if (self.profilePopulated):
            status = self.__encryptFile(inFile=dataToEncrypt,
                                        gnupghome=self.personIdentification.get('gnupghome'),
                                        email=self.personIdentification.get('email'),
                                        passphrase=self.personIdentification.get('passphrase'),
                                        outSecretFile=outfile)
        else:
            status = False
        return (status)

    def decryptTarball(self, dataToEncrypt="telemetry.bin.gpg", outfile="telemetry.bin"):
        if (self.profilePopulated):
            status = self.__decryptFile(outFile=outfile,
                                        gnupghome=self.personIdentification.get('gnupghome'),
                                        email=self.personIdentification.get('email'),
                                        passphrase=self.personIdentification.get('passphrase'),
                                        inSecretFile=dataToEncrypt)
        else:
            status = False
            encryptedFile = None
        return (status, encryptedFile)

    #############################
    ####### Profile Keying#######
    #############################
    def userProfileLoad(self, profileFile=None):
        key = None
        keyData = None
        profileData = self.__loadProfile(profileFile)
        (status, validCount) = self.__verifyProfile(profileData=profileData)
        if (os.path.exists(profileData.get('gnupghome'))):
            gpg = gnupg.GPG(gnupghome=profileData.get('gnupghome'))
            inputData = gpg.gen_key_input(
                name_email=profileData.get('email'),
                passphrase=profileData.get('passphrase'))
            key = gpg.gen_key(inputData)
            keyMatch = (key == profileData.get('key'))
            (publicKeys, privateKeys) = self.__listKeys(gnupghome=profileData.get('gnupghome'))
            (keyData, keyResults) = self.__importKey(profileData.get('gnupghome'), profileData.get('keyFile'))
            if (keyMatch and keyResults and self.debug):
                print("userProfileLoad() Key is Invalid", keyMatch, keyResults)
                assert ()
        else:
            if (self.debug):
                assert ("userProfileLoad() Profile data is Invalid")
        if (self.debug):
            print("Profile data", profileData)
            print("KeyData", keyData)
            print("Key", key)  # I.E. B0F4CF530036CE8CD1C064F17D32CEE72C015CD5
        return (profileData, keyData)

    def userProfileCreate(self, saveFile=None,
                          email='joseph.d.tarango@intel.com', passphrase='abc123',
                          gnupghome='/home/jdtarang/gpghome',
                          keyFile='mykeyfile.asc'):
        if (saveFile is None):
            temporaryFolder, saveFile = tempfile.mkstemp()
        (key, gpg) = self.__generateKey(passphrase=passphrase, gnupghome=gnupghome, email=email)
        (gpg, publicKeys, privateKeys) = self.__exportKey(gnupghome=gnupghome, key=key, keyFile=keyFile)
        # Populate JSON config file
        profileJSON = {'email': email,
                       'passphrase': passphrase,
                       'gnupghome': gnupghome,
                       'keyFile': keyFile,
                       'key': key}
        with open(saveFile, 'w') as fileJSON:
            json.dump(profileJSON, fileJSON)
            fileJSON.close()
        return (profileJSON, fileJSON)

    #############################
    ####### Helper Tools  #######
    #############################

    def __gatherFileList(self, extensionListCode: list = None):
        if extensionListCode is None:
            extensionListCode = list()
        rootdir = self.absPath
        fileList = []
        if isinstance(extensionListCode, str):
            extListCode = [extensionListCode]
        elif isinstance(extensionListCode, list):
            extListCode = extensionListCode
        else:
            return None
        for (folder, dirs, files) in os.walk(rootdir):
            for fileSelected in files:
                for (indexExtension, itemExtension) in enumerate(extListCode):
                    if (fileSelected.endswith(itemExtension)):
                        fullpath = os.path.join(folder, fileSelected)
                        fileList.append(fullpath)
                        # if (self.debug is True):
                        #    print("File: ", fileSelected, " Extension Index: ", indexExtension, " Postfix", itemExtension)
        return fileList

    def __saveJSON(self, saveFile=None, objectJSON=None):

        if (saveFile is None):
            temporaryFolder, saveFile = tempfile.mkstemp()

        if (objectJSON is None):
            objectJSON = self.zipTemplate()

        with open(saveFile, 'w') as fileJSON:
            json.dump(objectJSON, fileJSON)

        return (objectJSON, fileJSON)

    def __loadProfile(self, inJSONFile=None):
        if os.path.exists(inJSONFile):
            with open(inJSONFile) as openFile:
                metaData = json.loads(openFile)
        else:
            metaData = None
        return metaData

    def __verifyProfile(self, profileData=None):
        verifyList = ['email', 'passphrase', 'gnupghome', 'keyFile', 'key']
        validCount = 0
        for itemIndex, itemValue in enumerate(verifyList):
            if (itemValue in profileData):
                validCount += 1
        if validCount == enumerate(verifyList):
            status = True
        else:
            status = False
        return (status, validCount)

    def __cleanFileString(self, nameString=""):
        illegalChar = [
            '!', '@', '#', '%', '^', '&', '*', '(', ')', '=', '+',
            '{', '}', '[', ']', '|', '\\', ';', ':', '"', '\'', ',',
            '<', '>', '?', '/', '~', '`'
        ]
        cleanName = str(nameString)
        for itemChar in illegalChar:
            cleanName = cleanName.replace(itemChar, '')
        return cleanName

    def ___createDirectoryTarball(self, path='./tarBallFolder', tarName='tarBall.tar', mode='w'):
        with tarfile.open(tarName, mode) as tar_handle:
            for root, dirs, files in os.walk(path):
                for fileItem in files:
                    tar_handle.add(os.path.join(root, fileItem))

    def __addToTarball(self, pathToFiles=None, fileData="telemetry.bin", tarFile="compress.tar", encodingType='utf-8'):
        if os.path.isfile(fileData) and tarfile.is_tarfile(tarFile):
            with tarfile.open(name=tarFile, mode='w|', bufsize=self._telemetryPayloadBytes) as tarball:
                tarList = tarball.getmembers()
                if fileData not in tarList:
                    tarball.ENCODING
                    tarball.add(fileData)
                else:
                    print("Data is already included")
                tarball.close()
        return None

    #############################
    #######   Key TOOLS   #######
    #############################
    def __generateKey(self, passphrase='abc123', gnupghome='/home/jdtarang/gpghome',
                      email='joseph.d.tarango@intel.com'):
        gpg = gnupg.GPG(gnupghome=gnupghome)
        input_data = gpg.gen_key_input(
            name_email=email,
            passphrase=passphrase)
        key = gpg.gen_key(input_data)
        if (self.debug): print(key)  # I.E. B0F4CF530036CE8CD1C064F17D32CEE72C015CD5
        return key, gpg

    def __exportKey(self, gnupghome='/home/jdtarang/gpghome', key=None, keyFile='mykeyfile.asc'):
        """
        (venv)jdtarang@skynet:~$ cat mykeyfile.asc
        -----BEGIN PGP PUBLIC KEY BLOCK-----
        Version: GnuPG v1.4.10 (GNU/Linux)

        mI0ETqrVGAEEAP42Xs1vQv40MxA3/g/Le5B0VatnDYaSvAhiYfaub79HY4mjYcCD
        FPDo5b54PSzyhlVsz5RL46+RE9NpQ2JdvFofWi7eVzfdmmTtNYEaiUSmzLUq73Vz
        qu7P1RhOfwuAyW0otnw/Lw54MVjVZblvp3ln1Fcpleb9ZSrY1h61Y8pHABEBAAG0
        REF1dG9nZW5lcmF0ZWQgS2V5IChHZW5lcmF0ZWQgYnkgZ251cGcucHkpIDx0ZXN0
        Z3BndXNlckBteWRvbWFpbi5jb20+iLgEEwECACIFAk6q1RgCGy8GCwkIBwMCBhUI
        AgkKCwQWAgMBAh4BAheAAAoJEH0yzucsAVzVBjwD/1KgTx1y3cpuumu1HF0GtQV0
        Wn7l9OaSj98CqQ/f2emHD1l9rrjdt9jm1g7wSsWumpKs57vxz7NXwHw7mI4qZ5m0
        cvg/qRc/BBMP8v2WgzRsmls97Pplaate1k3QfvDCVs6F1qiIQyELffjxBHbmWPhx
        XEwhnpLcvk2l7NbNnEwA
        =exDD
        -----END PGP PUBLIC KEY BLOCK-----
        -----BEGIN PGP PRIVATE KEY BLOCK-----
        Version: GnuPG v1.4.10 (GNU/Linux)

        lQH+BE6q1RgBBAD+Nl7Nb0L+NDMQN/4Py3uQdFWrZw2GkrwIYmH2rm+/R2OJo2HA
        gxTw6OW+eD0s8oZVbM+US+OvkRPTaUNiXbxaH1ou3lc33Zpk7TWBGolEpsy1Ku91
        c6ruz9UYTn8LgMltKLZ8Py8OeDFY1WW5b6d5Z9RXKZXm/WUq2NYetWPKRwARAQAB
        /gMDAq5W6uxeU2hDYDPZ1Yy+e97ppNXmdAeq1urZHmiPr4+a36nOWd6j0R/HBjG3
        ELD8CqYiQ0vx8+F9rY/uwKga2bEkJsQXjvaaZtu97lzPyp2+avsaw2G+3jRAJWNL
        5YG4c/XwK1cfEajM23f7zz/t6TRWG+Ve2Dzi7+obA0LuF8czSlpiTTEzLDk8QJCK
        y2WmrZ+s+POWv3itVpI26o7PvTQESzwyKXdyCW2W66VnXTm4mQEL6kgyV0oO6xIl
        QUVSn2XWvwFMg2iL+02zA467rsr1x6Nl8hEQJgFwJCejD2z+4C4yzEeQGFP9WUps
        pbMedAjDHebhC9FzbW7yuQ3H7iTCK1mvidAFw2wTdrkH61ApzmSo/rSTSxXw7hLT
        M/ONgYZtvr+CpJj+mIu1XvVDiftvMhXlwcvM8c9PB3zv+086K7kJDTnzPgYvL0H/
        +V2b9X9BBfAax40MQuxZJWseaLtsxXyl/rhn8jSCFZoqtERBdXRvZ2VuZXJhdGVk
        IEtleSAoR2VuZXJhdGVkIGJ5IGdudXBnLnB5KSA8dGVzdGdwZ3VzZXJAbXlkb21h
        aW4uY29tPoi4BBMBAgAiBQJOqtUYAhsvBgsJCAcDAgYVCAIJCgsEFgIDAQIeAQIX
        gAAKCRB9Ms7nLAFc1QY8A/9SoE8dct3KbrprtRxdBrUFdFp+5fTmko/fAqkP39np
        hw9Zfa643bfY5tYO8ErFrpqSrOe78c+zV8B8O5iOKmeZtHL4P6kXPwQTD/L9loM0
        bJpbPez6ZWmrXtZN0H7wwlbOhdaoiEMhC3348QR25lj4cVxMIZ6S3L5NpezWzZxM
        AA==
        =v9Z7
        -----END PGP PRIVATE KEY BLOCK-----
        """
        gpg = gnupg.GPG(gnupghome=gnupghome)
        publicKeys = gpg.export_keys(key)
        privateKeys = gpg.export_keys(key, True)
        with open(keyFile, 'w') as openFile:
            openFile.write(publicKeys)
            openFile.write(privateKeys)
        return (gpg, publicKeys, privateKeys)

    def __importKey(self, gnupghome='/home/jdtarang/gpghome', keyFile='mykeyfile.asc'):
        """
        [{'fingerprint': u'B0F4CF530036CE8CD1C064F17D32CEE72C015CD5',
          'ok': u'0',
          'text': 'Not actually changed\n'},
         {'fingerprint': u'B0F4CF530036CE8CD1C064F17D32CEE72C015CD5',
          'ok': u'16',
          'text': 'Contains private key\nNot actually changed\n'}]
        """
        gpg = gnupg.GPG(gnupghome=gnupghome)
        keyData = open(keyFile).read()
        import_result = gpg.import_keys(keyData)
        if (self.debug): pprint(import_result.results)
        return keyData, import_result.results

    def __listKeys(self, gnupghome='/home/jdtarang/gpghome'):
        """
        public keys:
        [{'algo': u'1',
          'date': u'1319818520',
          'dummy': u'',
          'expires': u'',
          'fingerprint': u'B0F4CF530036CE8CD1C064F17D32CEE72C015CD5',
          'keyid': u'7D32CEE72C015CD5',
          'length': u'1024',
          'ownertrust': u'u',
          'trust': u'u',
          'type': u'pub',
          'uids': [u'Autogenerated Key (Generated by gnupg.py) ']}]
        private keys:
        [{'algo': u'1',
          'date': u'1319818520',
          'dummy': u'',
          'expires': u'',
          'fingerprint': u'B0F4CF530036CE8CD1C064F17D32CEE72C015CD5',
          'keyid': u'7D32CEE72C015CD5',
          'length': u'1024',
          'ownertrust': u'',
          'trust': u'',
          'type': u'sec',
          'uids': [u'Autogenerated Key (Generated by gnupg.py) ']}]
        """
        gpg = gnupg.GPG(gnupghome=gnupghome)
        publicKeys = gpg.list_keys()
        privateKeys = gpg.list_keys(True)
        if (self.debug):
            print('Public Keys')
            pprint(publicKeys)
            print('Private Keys')
            pprint(privateKeys)
        return (publicKeys, privateKeys)

    #############################
    ####### ENCRYPT TOOLS #######
    #############################
    def __encryptAString(self, gnupghome='/home/jdtarang/gpghome',
                         unencrypted_string='Who are you? How did you get in my house? *Opens Can of Molly Wop*...',
                         email='joseph.d.tarango@intel.com'):
        """
        Function: encryptAString()
        Okay:  True
        Status:  encryption ok
        STD Error:  [GNUPG:] BEGIN_ENCRYPTION 2 9
        [GNUPG:] END_ENCRYPTION

        Unencrypted string:  Who are you? How did you get in my house? *Opens Can of Molly Wop*...
        Encrypted string:  -----BEGIN PGP MESSAGE-----
        Version: GnuPG v1.4.10 (GNU/Linux)

        hIwDFuhrAS77HYIBBACXqZ66rkGQv8yE61JddEmad3fUNvbfkhBPUI9OSaMO3PbN
        Q/6SIDyi3FmhbM9icOBS7q3xddQpvFhwmrq9e3VLKnV3NSmWo+xJWosQ/GNAA/Hb
        cwF1pOtR6bRHFBkqtmpTYnBo9rMpokW8lp4WxFxMda+af8TlId8HC0WcRUg4kNJi
        AdV1fsd+sD/cGIp0cAltpaVuO4/uwV9lKd39VER6WigLDaeFUHjWhJbcHwTaJYHj
        qmy5LRciNSjwsqeMK4zOFZyRPUqPVKwWLiE9kImMni0Nj/K54ElWujgTttZIlBqV
        5+c=
        =SM4r
        -----END PGP MESSAGE-----
        """
        import gnupg

        gpg = gnupg.GPG(gnupghome=gnupghome)
        encrypted_data = gpg.encrypt(unencrypted_string, email)
        encrypted_string = str(encrypted_data)
        if (self.debug):
            print('Function: encryptAString()')
            print('Okay: ', encrypted_data.ok)
            print('Status: ', encrypted_data.status)
            print('STD Error: ', encrypted_data.stderr)
            print('Unencrypted string: ', unencrypted_string)
            print('Encrypted string: ', encrypted_string)

    def __decryptAString(self,
                         gnupghome='/home/jdtarang/gpghome',
                         unencrypted_string='Who are you? How did you get in my house? *Opens Can of Molly Wop*...',
                         email='joseph.d.tarango@intel.com',
                         passphrase='abc123'):
        """
        Function: decryptAString()
        Okay:  True
        Status:  decryption ok
        STD Error:  [GNUPG:] ENC_TO 16E86B012EFB1D82 1 0
        [GNUPG:] USERID_HINT 16E86B012EFB1D82 Autogenerated Key (Generated by gnupg.py)
        [GNUPG:] NEED_PASSPHRASE 16E86B012EFB1D82 16E86B012EFB1D82 1 0
        [GNUPG:] GOOD_PASSPHRASE
        gpg: encrypted with 1024-bit RSA key, ID 2EFB1D82, created 2011-11-02
              "Autogenerated Key (Generated by gnupg.py) "
        [GNUPG:] BEGIN_DECRYPTION
        [GNUPG:] PLAINTEXT 62 1320545729
        [GNUPG:] PLAINTEXT_LENGTH 41
        [GNUPG:] DECRYPTION_OKAY
        [GNUPG:] GOODMDC
        [GNUPG:] END_DECRYPTION

        Decrypted string:  Who are you? How did you get in my house? *Opens Can of Molly Wop*...
        """
        import gnupg

        gpg = gnupg.GPG(gnupghome=gnupghome)
        encrypted_data = gpg.encrypt(unencrypted_string, email)
        encrypted_string = str(encrypted_data)
        decrypted_data = gpg.decrypt(encrypted_string, passphrase=passphrase)
        print('Function: decryptAString()')
        print('Okay: ', decrypted_data.ok)
        print('Status: ', decrypted_data.status)
        print('STD Error: ', decrypted_data.stderr)
        print('Decrypted string: ', decrypted_data.data)

    def __encryptFile(self,
                      inFile='my-unencrypted.txt',
                      gnupghome='/home/jdtarang/gpghome',
                      email='joseph.d.tarango@intel.com',
                      passphrase='abc123',
                      outSecretFile='my-unencrypted.gpg'):
        """
        open('my-unencrypted.txt', 'w').write('We all have secrets...')
        Function: encryptFile()
        Okay:  True
        Status:  encryption ok
        STD Error:  [GNUPG:] BEGIN_ENCRYPTION 2 9
        [GNUPG:] END_ENCRYPTION
        (venv)jdtarang@skynet:~$  cat my-encrypted.txt.gpg
        -----BEGIN PGP MESSAGE-----
        Version: GnuPG v1.4.10 (GNU/Linux)

        hIwDfTLO5ywBXNUBBADo7trFZUD6Ir1vPRAJsoQXDiiw32N1m9/PXWCnQqX0nyzW
        LfluNMfLFQRclNPVEg+o91qhS71apKvagp8DW7SCDE2SdCYk8nAS3bwAg5+GUyDs
        XY2E6BQ1cLA1eK1V6D15ih6cq0laRzWuFkehH9PQ5Yp4ZZOmCbopw7dufnYPjdJb
        AVGLpZRq64SuN1BUWIHbO7vqQGFq7qhGQwuegblEMm4vyr6FBW6JA/x4G/PMfImZ
        1cH6KBrWGWrLCTiU/FKG9JvOm8mg8NXzd/TVjPs6rHRaKPFln37T7cLUwA==
        =FSQP
        -----END PGP MESSAGE-----
        """
        gpg = gnupg.GPG(gnupghome=gnupghome)
        with open(inFile, 'rb') as fileOpen:
            status = gpg.encrypt_file(
                fileOpen, recipients=[email],
                output=outSecretFile)

        if (self.debug):
            print('Function: encryptFile()')
            print('Okay: ', status.ok)
            print('Status: ', status.status)
            print('STD Error: ', status.stderr)
        return status

    def __decryptFile(self,
                      outFile='my-decrypted.txt',
                      gnupghome='/home/jdtarang/gpghome',
                      email='joseph.d.tarango@intel.com',
                      passphrase='abc123',
                      inSecretFile='my-unencrypted.gpg'):
        """
        Function: decryptFile()
        Okay:  True
        Status:  decryption ok
        STD Error:  [GNUPG:] ENC_TO 16E86B012EFB1D82 1 0
        [GNUPG:] USERID_HINT 16E86B012EFB1D82 Autogenerated Key (Generated by gnupg.py)
        [GNUPG:] NEED_PASSPHRASE 16E86B012EFB1D82 16E86B012EFB1D82 1 0
        [GNUPG:] GOOD_PASSPHRASE
        gpg: encrypted with 1024-bit RSA key, ID 2EFB1D82, created 2011-11-02
              "Autogenerated Key (Generated by gnupg.py) "
        [GNUPG:] BEGIN_DECRYPTION
        [GNUPG:] PLAINTEXT 62 1320546031
        [GNUPG:] PLAINTEXT_LENGTH 32
        [GNUPG:] DECRYPTION_OKAY
        [GNUPG:] GOODMDC
        [GNUPG:] END_DECRYPTION
        (venv)jdtarang@skynet:~$ cat my-decrypted.txt
        We all have secrets...
        """
        gpg = gnupg.GPG(gnupghome=gnupghome)
        with open(inSecretFile, 'rb') as openFile:
            status = gpg.decrypt_file(openFile, passphrase=passphrase, output=outFile)

        if (self.debug):
            print('Function: decryptFile()')
            print('Okay: ', status.ok)
            print('Status: ', status.status)
            print('STD Error: ', status.stderr)
            print('Decrypted string: ', status.data)
        return status


class Cipher_AES:
    pad_default = lambda x, y: x + (y - len(x) % y) * " ".encode("utf-8")
    unpad_default = lambda x: x.rstrip()
    pad_user_defined = lambda x, y, z: x + (y - len(x) % y) * z.encode("utf-8")
    unpad_user_defined = lambda x, z: x.rstrip(z)
    pad_pkcs5 = lambda x, y: x + (y - len(x) % y) * chr(y - len(x) % y).encode("utf-8")
    unpad_pkcs5 = lambda x: x[:-ord(x[-1])]

    def __init__(self,
                 key=None,
                 iv=Crypto.Random.new().read(Crypto.Cipher.AES.block_size),
                 cipher_method=None,
                 code_method=None,
                 paddingMethod=None,
                 debug=False):

        if key is None or not isinstance(key, str):
            N = 32
            key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(N))
        self.__key = key
        self.__iv = iv

        if cipher_method is None:
            self.cipher_method = "MODE_CBC"
        if code_method is None:
            self.code_method = "base64"
        if paddingMethod is None:
            self.paddingMethod = "PKCS5Padding"
        if isinstance(debug, bool):
            self.debug = debug
        # vars
        self.__x = None
        self.encryptedText = None
        return

    def set_key(self, key):
        self.__key = key

    def get_key(self):
        return self.__key

    def set_iv(self, iv):
        self.__iv = iv

    def get_iv(self):
        return self.__iv

    def get_encryptedText(self):
        return self.encryptedText

    def Cipher_MODE_ECB(self):
        if not isinstance(self.__iv, str):
            key = self.__key.encode("utf-8")
        else:
            key = self.__key
        self.__x = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_ECB)
        return

    def Cipher_MODE_CBC(self):
        if not isinstance(self.__iv, str):
            key = self.__key.encode("utf-8")
        else:
            key = self.__key
        if not isinstance(self.__iv, bytes):
            iv = self.__iv.encode("utf-8")
        else:
            iv = self.__iv
        self.__x = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CBC, iv)
        return

    def encrypt(self, text, cipher_method=None, pad_method=None, code_method=None):
        if cipher_method is None:
            cipher_method = self.cipher_method
        if code_method is None:
            code_method = self.code_method

        if cipher_method.upper() == "MODE_ECB":
            self.Cipher_MODE_ECB()
        elif cipher_method.upper() == "MODE_CBC":
            self.Cipher_MODE_CBC()

        cipher_text = b"".join([self.__x.encrypt(i) for i in self.text_verify(text.encode("utf-8"), pad_method)])

        if code_method.lower() == "base64":
            self.encryptedText = base64.encodebytes(cipher_text).decode("utf-8").rstrip()
        elif code_method.lower() == "hex":
            self.encryptedText = binascii.b2a_hex(cipher_text).decode("utf-8").rstrip()
        else:
            self.encryptedText = cipher_text.decode("utf-8").rstrip()

        return self.encryptedText

    def decrypt(self, cipher_text, cipher_method=None, pad_method=None, code_method=None):
        if cipher_method is None:
            cipher_method = self.cipher_method
        if code_method is None:
            code_method = self.code_method
        if pad_method is None:
            pad_method = self.paddingMethod

        if cipher_method.upper() == "MODE_ECB":
            self.Cipher_MODE_ECB()
        elif cipher_method.upper() == "MODE_CBC":
            self.Cipher_MODE_CBC()

        if code_method.lower() == "base64":
            cipher_text = base64.decodebytes(cipher_text.encode("utf-8"))
        elif code_method.lower() == "hex":
            cipher_text = binascii.a2b_hex(cipher_text.encode("utf-8"))
        else:
            cipher_text = cipher_text.encode("utf-8")

        return self._unpad_method(self.__x.decrypt(cipher_text).decode("utf-8"), pad_method)

    def text_verify(self, text, method=""):
        while len(text) > len(self.__key):
            text_slice = text[:len(self.__key)]
            text = text[len(self.__key):]
            yield text_slice
        else:
            if len(text) == len(self.__key):
                yield text
            else:
                yield self._pad_method(text, method)
        return

    def _pad_method(self, text, method=None):
        if method is None:
            method = self.paddingMethod

        if method == "":
            return Cipher_AES.pad_default(text, len(self.__key))
        elif method == "PKCS5Padding":
            return Cipher_AES.pad_pkcs5(text, len(self.__key))
        else:
            return Cipher_AES.pad_user_defined(text, len(self.__key), method)

    def _unpad_method(self, text, method=None):
        if method is None:
            method = self.paddingMethod

        if method == "":
            return Cipher_AES.unpad_default(text)
        elif method == "PKCS5Padding":
            return Cipher_AES.unpad_pkcs5(text)
        else:
            return Cipher_AES.unpad_user_defined(text, method)

    def testHarness(self):
        self.testCase("405862999990475",
                      "CI6MTU3ODQ4ODYyM30.SAjMKd0chcAWoFwMkfxJ-Z1lWRM9-AeSXuHZiXBTYyo")
        return

    @staticmethod
    def testCase(msg, token, debug=False):
        st_arr = []
        dy_arr = []
        static_str = 'Mu8weQyDvq1HlAzN'
        for b in bytearray(static_str, "utf-8"):
            st_arr.append(b)

        token_str = token[-16:]
        for b in bytearray(token_str, "utf-8"):
            dy_arr.append(b)

        res_byts = []
        for bt in bytes(a ^ b for (a, b) in zip(st_arr, dy_arr)):
            res_byts.append(bt)

        key = bytes(res_byts).decode()
        iv = key
        text = msg  # "7977099688"
        cipher_method = "MODE_CBC"
        pad_method = "PKCS5Padding"
        code_method = "base64"
        cipher_text = Cipher_AES(key, iv).encrypt(text, cipher_method, pad_method, code_method)
        cipher_text = cipher_text.replace('\n', '')
        if debug:
            print('[' + cipher_text + ']')
            print(type(cipher_text))
            text = Cipher_AES(key, iv).decrypt(cipher_text, cipher_method, pad_method, code_method)
            print(text)
        return


def setup(debug=True):
    state = None
    '''
    try:
        import setuptools, traceback
        state = setuptools.setup(
                      name='package Data Stream',
                      version='1.0',
                      author='Joseph Tarango',
                      author_email='no-reply@intel.com',
                      description='AXON Data Stream for Intel telemetry.',
                      url='http://github.com/intel/raad/src/software/axon/packageInterface.py',
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


# @todo add more functionality
""" Later usage for generating ECC Keys

    def getCredentials(self, defaultPasswordFile=".raadProfile/.credentials.conf"):
        NSGWikiUsername = None
        NSGWikiPassword = None
        if self._debug:
            NSGWikiUsername = input('Enter username: ')
            NSGWikiPassword = getpass.getpass(prompt='Enter password: ', stream=sys.stderr)
        else:
            if os.path.exists(os.path.join(os.getcwd(), defaultPasswordFile)):
                NSGWikiPassword = getpass.getpass(prompt=('Enter username and password file: I.E. {}'.format(defaultPasswordFile)), stream=sys.stderr)
            if NSGWikiPassword is None or NSGWikiPassword is "":
                NSGWikiPassword = defaultPasswordFile
            with open(NSGWikiPassword) as f:
                NSGWikiUsername, NSGWikiPassword = f.read().split('\n')  # Separator is \n
        self._username = NSGWikiUsername
        self._password = NSGWikiPassword
        return (NSGWikiUsername, NSGWikiPassword)

    def generatePasswordKeys(self, privateFile="private.pem", publicFile="public.pem"):
        import ecdsa
        # Check key existance
        publicFileExists = os.path.exists(os.path.join(os.getcwd(), privateFile))
        privateFileExists = os.path.exists(os.path.join(os.getcwd(), publicFile))
        # Create keys
        if publicFileExists and privateFileExists:
            signedKey = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
            validateKey = signedKey.get_verifying_key()
            validateKey.precompute()
            # Write temporary keys
            with open(privateFile, "wb") as openFile:
                openFile.write(ecdsa.SigningKey.to_pem())
            with open(publicFile, "wb") as openFile:
                openFile.write(ecdsa.SigningKey.to_pem())
            if self.debug:
                validateKeyString = validateKey.to_string()
                validateKeyPEM = validateKey.to_pem()
                print("vKey {}\n vPEM {}".format(validateKeyString, validateKeyPEM))
            return True
        return False

    def writePassword(self, messageMeta=None, messageEncodedFile="signature.encoded.msg", privateFile="private.pem", publicFile="public.pem"):
        import ecdsa
        # Encode message to file
        with open(privateFile) as openFile:
            signedKey = ecdsa.SigningKey.from_pem(openFile.read())
        validateKey = signedKey.get_verifying_key()
        validateKey.precompute()
        if self.debug:
            validateKeyString = validateKey.to_string()
            validateKeyPEM = validateKey.to_pem()
            print("vKey {}\n vPEM {}".format(validateKeyString, validateKeyPEM))
        messageSignature = signedKey.sign(messageMeta)
        with open(messageEncodedFile, "wb") as openFile:
            openFile.write(messageSignature)
        # Validate message
        assert validateKey.verify(messageSignature, messageMeta)
        # Give message encoding
        return messageSignature

    def readPassword(self, messageMeta=None, messageEncodedFile="signature.encoded.msg", privateFile="private.pem", publicFile="public.pem"):
        import ecdsa
        verifyKey = ecdsa.VerifyingKey.from_pem(open(publicFile).read())
        with open(messageEncodedFile, "rb") as f:
            messageSignature = f.read()
        verifyKey.from_pem(messageSignature, curve=ecdsa.SECP256k1)
        messageSignature.to_String()
"""


def hollowShell(options=None):
    print("Running hollow AXON instance")
    # referenceTest = packageInterface()
    (exitCode, cmdOutput, cmdError) = None, None, None
    print("Exit Code:", exitCode)
    print("Command line outpout:", cmdOutput)
    print("Command Error", cmdError)
    print("Data Transaction Output:", cmdOutput)
    return


def createTar(options):
    tarFileName = options.compressDirectory + "/" + "GatherData" + datetime.datetime.utcnow().strftime(
        "%Y-%m-%d-%H-%M-%S-%f") + ".tar"
    tarPack = packageInterface(absPath=options.compressDirectory, debug=options.debug)
    tarPack.createTarball(tarFileName=tarFileName, mode="w:gz")
    return tarPack, tarFileName


def compressTar(options, tarPack, tarFileName):
    tarPack.compressTarball(tarFile=tarFileName, mode="w:gz")


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
    parser.add_option("--compressDirectory", dest='compressDirectory', default=os.getcwd(),
                      help="Location of directory to operate on.")
    parser.add_option("--tarFile", dest='tarFile', default='', help="Name of tar file to use.")
    (options, args) = parser.parse_args()

    if not options.example:
        ##############################################
        # Main
        ##############################################
        setup()
        hollowShell(options)
    else:
        ##############################################
        # Example Usage
        ##############################################
        ExampleUsage(options)
    return 0


def ExampleUsage(options):
    ##############################################
    # Create and compress the directory
    ##############################################
    packing, tarName = createTar(options)
    compressTar(options, packing, tarName)
    return 0


if __name__ == '__main__':
    """Performs execution delta of the process."""
    p = datetime.datetime.now()
    try:
        cypherObj = Cipher_AES(debug=True)
        cypherObj.testHarness()
    except Exception as e:
        print("Fail End Process: ", e)
        traceback.print_exc()
    q = datetime.datetime.now()
    print("\nExecution time: " + str(q - p))
