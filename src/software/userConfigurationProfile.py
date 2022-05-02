#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
# from __future__ import absolute_import, division, print_function, unicode_literals
# from __future__ import nested_scopes, generators, generator_stop, with_statement, annotations
import platform, os, dataclasses, traceback, datetime, optparse, configparser


class userConfigurationProfile(object):
    _windows64 = 'C:\\Program Files\\Intel\\Intel(R) Memory And Storage Tool\\IntelMAS.exe'
    _windows86 = 'C:\\Program Files (x86)\\Intel\\Intel(R) Memory And Storage Tool\\IntelMAS.exe'
    _linux8664 = '/usr/bin/Intel/IntelMAS'
    configFolderName = '.raadProfile/'
    configFileName = 'config.ini'
    applicationList = ["access", "cloud", "raad"]
    debug = True

    @dataclasses.dataclass()
    class applicationIdentifier:
        # Main RAAD application information, Interface
        # Telemetry application information, CLI
        # AXON application information, Cloud
        def __init__(self):
            self.identity = None  # Application identification number.
            self.major = None  # Application major version.
            self.minor = None  # Application minor version.
            self.name = None  # Application display name.
            self.location = None  # Application location in system.
            self.mode = None  # Application operation mode.
            self.url = None  # Application Uniform Resource Locator; meaning address of a World Wide Web page.

    @dataclasses.dataclass()
    class userIdentifier:
        # User application information, I.E. Joe Tarango
        def __init__(self):
            """
            User application configuration information
            """
            self.identity = None  # User identification number
            self.name = None  # User login
            self.mode = None  # interaction mode
            self.keyLoc = None  # User key location
            self.encryptionStatus = None  # Enable package encryption
            self.workingDir = None  # Working directory for intermediate files

    def __init__(self, debug):
        """
        Creates the baseline information for a the application profile.
        """
        # Main RAAD application information, Interface
        self.raad = self.applicationIdentifier()
        # Telemetry application information, CLI
        self.access = self.applicationIdentifier()  # mode options are: 'unknown', 'openSource', 'intel'
        # AXON application information, Cloud
        self.cloud = self.applicationIdentifier()
        # Additional Apps
        self.otherApps = None
        # User application information, I.E. Joe
        self.user = self.userIdentifier()

        if debug is False:
            self.debug = False

        return

    def _getAll(self, printInfo=False, typeReturn='array', itemIn=None):
        """
        Operation to get the values of a given item in array or pair form.
        Args:
            printInfo: Flag to print the content to console for debug
            typeReturn: Flag to determine to return an array or pair
            itemIn: Parameter to access content

        Returns: Key, Value in array or pair form.

        """
        if typeReturn == 'array':
            return self._attrArrays(itemIn=itemIn, printInfo=printInfo)
        else:
            return self._attrPairs(itemIn=itemIn, printInfo=printInfo)

    @staticmethod
    def _attrArrays(itemIn=None, printInfo=False):
        """
        Operation to get the values of a given item in array form.
        Args:
            printInfo: Flag to print the content to console for debug
            itemIn: Parameter to access content

        Returns: Key, Value in array form.

        """
        setKey = []
        setValue = []
        for k in itemIn.__dict__.keys():
            setKey.append(k)
            v = itemIn.__dict__.__getitem__(k)
            setValue.append(v)
            if printInfo:
                print("attr: {k}    value: {v}")
        return (setKey, setValue)

    @staticmethod
    def _attrPairs(itemIn=None, printInfo=False):
        """
        Operation to get the values of a given item in array or pair form.
        Args:
            printInfo: Flag to print the content to console for debug
            itemIn: Parameter to access content

        Returns: Key, Value in pair form.

        """
        pairs = [(k, v) for k, v in itemIn.__dict__.items()]
        if printInfo:
            [print("attr: {0}    value: {1}".format(item[0], item[1])) for item in pairs]
        return pairs

    @staticmethod
    def _getApplication(app=None):
        """
        Method to gather the sections populated with a non None value.
        Args:
            app: the applicationIdentifier variable to look at.

        Returns: The total count of non None type.

        """
        updateCount = 0
        if app is None:
            return updateCount

        if app.identity is not None:
            updateCount += 1
        if app.major is not None:
            updateCount += 1
        if app.minor is not None:
            updateCount += 1
        if app.name is not None:
            updateCount += 1
        if app.location is not None:
            updateCount += 1
        if app.mode is not None:
            updateCount += 1
        if app.url is not None:
            updateCount += 1
        return updateCount

    @staticmethod
    def _setApplication(app=None,
                        identity=None,
                        major=None,
                        minor=None,
                        name=None,
                        location=None,
                        mode=None,
                        url=None):
        """
        Determines if the input is not none then updates the field.
        Args:
            app: the applicationIdentifier variable to look at.
            identity: unique identification number for a  given application.
            major: Major version section to represent a unique organization of app-data.
            minor: Minor version section to represent an extension of the organization of app-data.
            name: String name of the application.
            location: Location on the user system of the application.
            mode: Operation mode of the given application.
            url: Application address for accessing data.

        Returns: Total count of updated items.

        """
        updateCount = 0
        if identity is not None:
            app.identity = identity
            updateCount += 1
        if major is not None:
            app.major = major
            updateCount += 1
        if minor is not None:
            app.minor = minor
            updateCount += 1
        if name is not None:
            app.name = name
            updateCount += 1
        if location is not None:
            app.location = location
            updateCount += 1
        if mode is not None:
            app.mode = mode
            updateCount += 1
        if url is not None:
            app.url = url
            updateCount += 1
        return updateCount

    def setApplication(self,
                       select='raad',
                       identity=None,
                       major=None,
                       minor=None,
                       name=None,
                       location=None,
                       mode=None,
                       url=None):
        """
        Determines if the input is not none then updates the field.
        Args:
            select: the applicationIdentifier string variable to look at.
            identity: unique identification number for a  given application.
            major: Major version section to represent a unique organization of app-data.
            minor: Minor version section to represent an extension of the organization of app-data.
            name: String name of the application.
            location: Location on the user system of the application.
            mode: Operation mode of the given application.
            url: Application address for accessing data.

        Returns: Total count of updated items.

        """
        if select == 'raad':
            # Main RAAD application information, Interface
            return self._setApplication(app=self.raad,
                                        identity=identity,
                                        major=major,
                                        minor=minor,
                                        name=name,
                                        location=location,
                                        mode=mode,
                                        url=url)
        elif select == 'access':
            # Telemetry application information, CLI
            return self._setApplication(app=self.access,
                                        identity=identity,
                                        major=major,
                                        minor=minor,
                                        name=name,
                                        location=location,
                                        mode=mode,
                                        url=url)
        elif select == 'cloud':
            # AXON application information, Cloud
            return self._setApplication(app=self.cloud,
                                        identity=identity,
                                        major=major,
                                        minor=minor,
                                        name=name,
                                        location=location,
                                        mode=mode,
                                        url=url)
        else:
            return 0

    def getApplicationDefaults(self, select=None):
        """
        Gather the default values for given applications.
        Args:
            select: the applicationIdentifier string variable to look at.

        Returns: default return values for the current application version.

        """
        if select == 'raad':
            # Main RAAD application information, Interface
            return(str(select),  # "app"
                   1,  # identity
                   1,  # major
                   0,  # minor
                   str(select),  # name
                   self.getDefaultHomeSave(),  # location
                   'cmd',  # mode
                   'https://github.com/intel/raad.git')  # url
        elif select == 'access':
            # Telemetry application information, CLI
            return (str(select),  # "app"
                    2,  # identity
                    1,  # major
                    0,  # minor
                    str(select),  # name
                    self.getDefaultHomeSave(),  # location
                    'cmd',  # mode
                    'https://downloadcenter.intel.com/download/29337/Intel-Memory-and-Storage-Tool-CLI-Command-Line-Interface-')  # url
        elif select == 'cloud':
            # AXON application information, Cloud
            return(str(select),  # "app"
                   3,  # identity
                   1,  # major
                   0,  # minor
                   str(select),  # name
                   self.getDefaultHomeSave(),  # location
                   'cmd',  # mode
                   'https://axon-dev.intel.com')  # url
        else:
            return(None,  # app
                   None,  # identity
                   None,  # major
                   None,  # minor
                   None,  # name
                   None,  # location
                   None,  # mode
                   None)  # url

    @staticmethod
    def getApplications(self):
        """
        Gathers the list of short names of applications.
        Args:
            self: Container with internal items.

        Returns: String list of application short names.

        """
        return self.applicationList

    def getApplicationMeta(self):
        """
        Gathers applications meta data.
        Args:
            self: Container with internal items.

        Returns: String list all application data.
        """
        applications = [['raad',
                         self.raad.identity,
                         self.raad.major,
                         self.raad.minor,
                         self.raad.name,
                         self.raad.location,
                         self.raad.mode,
                         self.raad.url],
                        ['access',
                         self.access.identity,
                         self.access.major,
                         self.access.minor,
                         self.access.name,
                         self.access.location,
                         self.access.mode,
                         self.access.url],
                        ['cloud',
                         self.cloud.identity,
                         self.cloud.major,
                         self.cloud.minor,
                         self.cloud.name,
                         self.cloud.location,
                         self.cloud.mode,
                         self.cloud.url]]
        return applications

    def setUser(self,
                identity=None,
                name=None,
                mode=None,
                keyLoc=None,
                encryptionStatus=None,
                workingDir=None):
        """
        Determines if the input is not none then updates the field.
        Args:
            identity: unique identification number for a  given application.
            name: String name of the application.
            mode: Operation mode of the given application.
            keyLoc: Location on the user system of the application.
            encryptionStatus: Flag to determine if the user is currently using encryption on the telemetry data.
            workingDir: The preferred working location for saving and managing telemetry data.

        Returns: Total count of updated items.

        """
        # User application information, I.E. Joe Tarango
        updateCount = 0
        if identity is not None:
            self.user.identity = None
            updateCount += 1
        if name is not None:
            self.user.name = None
            updateCount += 1
        if mode is not None:
            self.user.mode = None
            updateCount += 1
        if keyLoc is not None:
            self.user.keyLoc = None
            updateCount += 1
        if encryptionStatus is not None:
            self.user.encryptionStatus = None
            updateCount += 1
        if workingDir is not None:
            self.user.workingDir = None
            updateCount += 1
        return updateCount

    def getUserMeta(self):
        """
        Determines if the input is not none then updates the field.
        Args: None

        Returns:
            identity: unique identification number for a  given application.
            name: String name of the application.
            mode: Operation mode of the given application.
            keyLoc: Location on the user system of the application.
            encryptionStatus: Flag to determine if the user is currently using encryption on the telemetry data.
            workingDir: The preferred working location for saving and managing telemetry data.

        """
        return (self.user.identity,
                self.user.name,
                self.user.mode,
                self.user.keyLoc,
                self.user.encryptionStatus,
                self.user.workingDir)

    def getDefaultAccessCLI(self):
        """
        Function to gather the default access application os system environment.
        Returns: The path the default paths of given access applications.

        """
        platformType = platform.system()
        architectureType = ('64' in platform.machine())
        if platformType == 'linux':
            pathCLI = self._linux8664
        elif platformType == 'windows' and architectureType is True:
            pathCLI = self._windows64
        elif platformType == 'windows' and architectureType is False:
            pathCLI = self._windows86
        else:
            pathCLI = None
        return pathCLI

    def getUserHome(self):
        """
        Determines the current user home directory.
        Args:
            self: Container with internal items.

        Returns: home directory location in current operating system.
        """
        platformType = platform.system()
        if self.debug:
            homeDirectory = os.environ['PWD']
        elif platformType == 'linux':
            homeDirectory = os.environ['HOME']
        elif platformType == 'windows':
            homeDirectory = os.environ['USERPROFILE']
        else:
            homeDirectory = os.environ['PWD']

        if os.path.exists(homeDirectory):
            return homeDirectory
        return None

    def profileExists(self):
        """
        Function to determine if a profile already exists.
        Returns: Returns the boolean value of existence.
        """
        profilePath = self.getProfileLocation()
        return os.path.exists(profilePath)

    def getDefaultHomeSave(self):
        """
        Determines the current user home configuration directory.
        Args:
            self: Container with internal items.

        Returns: home directory configuration save location in current operating system.

        """
        profilePath = os.path.join(self.getUserHome(), self.configFolderName)
        return profilePath

    def getProfileLocation(self):
        """
        Determines the current user home configuration directory.
        Args:
            self: Container with internal items.

        Returns: home directory configuration save location in current operating system.

        """
        profilePath = os.path.join(self.getUserHome(), self.configFolderName, self.configFileName)
        profilePath = os.path.realpath(profilePath)
        return profilePath

    def readProfile(self):
        """
        Gathers information from existing profile and populates configuration.
        Returns: configuration ini and user information read.
        """
        # Load the configuration file
        profilePath = self.getProfileLocation()
        print("profile loc {0}".format(profilePath))
        config = configparser.RawConfigParser(allow_no_value=True)
        userConfig = config.read(profilePath)
        config.read(userConfig)
        return (config, userConfig)

    def printProfile(self):
        """
        Prints the existing content items in a given profile flushed to the filesystem.
        Returns: None
        """
        # List all contents
        config, userConfig = self.readProfile()
        print("List profile contents")
        for section in config.sections():
            print("Section: %s" % section)
            for options in config.options(section):
                print(" {0} {1} {2}".format(options, config.get(section, options), str(type(options))))
        return

    def modifyProfile(self, changeSection=None, changeVar=None, changeValue=None):
        """
        Modifies a given section variables and value in a rprogile.
        Args:
            changeSection: Section in the ini file.
            changeVar: Option variable name.
            changeValue: Value to change for a given profile.

        Returns:

        """
        # Print the configuration file
        if self.debug:
            self.printProfile()
        # Load the configuration file
        config, userConfig = self.readProfile()
        for section in config.sections():
            for options in config.options(section):
                if changeSection == section and changeVar == options:
                    config.set(changeSection, changeVar, str(changeValue))
                    print(" {0} {1} {2}".format(options, config.get(section, options), str(type(options))))
        # Print the configuration file
        if self.debug:
            self.printProfile()
        profilePath = self.getProfileLocation()
        with open(profilePath, "w") as openFile:
            config.write(openFile)
        return

    def searchProfile(self, changeSection=None, changeVar=None, raw=False):
        """
        Modifies a given section variables and value in a rprogile.
        Args:
            changeSection: Section in the ini file.
            changeVar: Option variable name.
            raw: All the '%' interpolations are expanded in the return values, unless the raw argument is true.
                 Values for interpolation keys are looked up in the same manner as the option.

        Returns: Boolean if found, value, option, section, and configuration object.

        """
        foundItem = False
        changeValue = None
        changeVarLocation = None
        changeSectionLocation = None
        # Print the configuration file
        if self.debug:
            self.printProfile()
        # Load the configuration file
        config, userConfig = self.readProfile()
        for section in config.sections():
            for options in config.options(section):
                if changeSection == section and changeVar == options and foundItem is False:
                    foundItem = True
                    changeSectionLocation = section
                    changeVarLocation = options
                    changeValue = config.get(section=section, option=options, raw=raw)
                    break
            else:
                continue  # Only executed if the inner loop did NOT break.
            break  # Only executed if the inner loop DID break.
        if self.debug:
            print(" {0} {1} {2}".format(changeVarLocation,
                                        config.get(changeSectionLocation, changeVarLocation),
                                        str(type(changeVarLocation))))
        return (foundItem, changeValue, changeVarLocation, changeSectionLocation, config)

    @staticmethod
    def _updateMetaAppSection(Config=None, app=None, sectionTag="application"):
        """
        Method to generically update application meta data.
        Args:
            Config: configuration container.
            app: application name
            sectionTag: prefix for the ini identifier for example 'application_#'

        Returns: configuration container updated

        """
        if Config is not None and app is not None:
            sectionTag = str(sectionTag + "_" + str(app.identity))
            Config.add_section(sectionTag)
            Config.set(sectionTag, "identity", str(app.identity))
            Config.set(sectionTag, "major", str(app.major))
            Config.set(sectionTag, "minor", str(app.minor))
            Config.set(sectionTag, "name", str(app.name))
            Config.set(sectionTag, "location", str(app.location))
            Config.set(sectionTag, "mode", str(app.mode))
            Config.set(sectionTag, "url", str(app.url))
        return Config

    def writeMetaProfile(self):
        """
        Function to create the meta data for a user given the existance of a profile.
        Returns: None

        """
        saveHome = self.getDefaultHomeSave()
        saveHome = os.path.abspath(saveHome)
        if not os.path.exists(saveHome):
            os.mkdir(saveHome)
        cfgProfileLocation = self.getProfileLocation()

        # Check if there is already a configuration file
        if not os.path.isfile(cfgProfileLocation):
            Config = configparser.ConfigParser()  # Add content to the file

            sectionTag = "application"

            # Main RAAD application information, Interface
            appCount = self._getApplication(app=self.raad)
            if appCount == 0:
                print("RAAD application not set value is {0}".format(appCount))
                (appD, identityD, majorD, minorD, nameD, locationD, modeD, urlD) = self.getApplicationDefaults(select="raad")
                self.setApplication(select=appD,
                                    identity=identityD,
                                    major=majorD,
                                    minor=minorD,
                                    name=nameD,
                                    location=locationD,
                                    mode=modeD,
                                    url=urlD)
            Config = self._updateMetaAppSection(Config=Config, app=self.raad, sectionTag=sectionTag)

            # Telemetry application information, CLI
            appCount = self._getApplication(app=self.access)
            if appCount == 0:
                print("Access application not set value is {0}".format(appCount))
                (appD, identityD, majorD, minorD, nameD, locationD, modeD, urlD) = self.getApplicationDefaults(select="access")
                self.setApplication(select=appD,
                                    identity=identityD,
                                    major=majorD,
                                    minor=minorD,
                                    name=nameD,
                                    location=locationD,
                                    mode=modeD,
                                    url=urlD)
            Config = self._updateMetaAppSection(Config=Config, app=self.access, sectionTag=sectionTag)

            # AXON application information, Cloud
            appCount = self._getApplication(app=self.cloud)
            if appCount == 0:
                print("cloud application not set value is {0}".format(appCount))
                (appD, identityD, majorD, minorD, nameD, locationD, modeD, urlD) = self.getApplicationDefaults(select="cloud")
                self.setApplication(select=appD,
                                    identity=identityD,
                                    major=majorD,
                                    minor=minorD,
                                    name=nameD,
                                    location=locationD,
                                    mode=modeD,
                                    url=urlD)
            Config = self._updateMetaAppSection(Config=Config, app=self.cloud, sectionTag=sectionTag)

            # User application information, Joe
            Config.add_section("user")
            Config.set("user", "identity", str(self.user.identity))
            Config.set("user", "name", str(self.user.name))
            Config.set("user", "mode", str(self.user.mode))  # Interaction mode
            Config.set("user", "keysLocation", str(self.user.keyLoc))
            Config.set("user", "encryptionStatus", str(self.user.encryptionStatus))
            Config.set("user", "workingDirectory", str(self.user.workingDir))

            # Create the configuration file as it doesn't exist yet
            with open(cfgProfileLocation, 'w') as cfgFile:
                # cfgFile = open(cfgProfileLocation, "w")
                print(cfgFile)
                Config.write(cfgFile)  # Update file
                cfgFile.close()

        if self.debug:
            self.printProfile()
        return

    @staticmethod
    def getInputCommandLine(self, prompt="Enter information", default=None, sizeMax=256):
        """
        Method to accept user input and use it in the creation of a configuration file.
        Args:
            self: Container with internal items.
            prompt: User display information for the command prompt.
            default: default value in the case of user pressing 'Enter'.
            sizeMax: Total string size

        Returns: The user returned input based on valid inputs of limited size.
        """
        userPrompt = (prompt, " default={0}".format(default))
        print(userPrompt)
        inputConsole = str(input())
        if inputConsole == '' or (len(inputConsole) == 0 and len(inputConsole) == sizeMax):
            inputConsole = default
        else:
            try:
                inputConsole = str(inputConsole)
            except Exception as errorEncountered:
                # handle input error or assign default for invalid input
                inputConsole = None
                print("Exception occurred {0}".format(errorEncountered))
        if self.debug:
            print('Captured {0}'.format(inputConsole))
        return inputConsole

    def _verifyMeta(self, printInfo=False):
        """
        Verifies all of the inputs keys within the given variable.
        Args:
            printInfo: Flag to determine if we are printing the found dictionary items.

        Returns: Return the pairs of information found, total count, total valid populated.
        """
        itemIn = self
        countAll = 0
        countValid = 0
        pairs = []
        for k, v in itemIn.__dict__.items():
            pairs.append([k, v])
            if k is not None and v is not None:
                countValid += 1
            countAll += 1
        if printInfo:
            [print("attr: {0}    value: {1}".format(item[0], item[1])) for item in pairs]
        return (pairs, countAll, countValid)

    def newUser(self):
        """
        The method to capture user information for a new profile.
        Returns: None
        """

        displayPrompt = ("Overwrite profile?, (y,n) ")
        capturedInput = self.getInputCommandLine(self=self, prompt=displayPrompt, default='y', sizeMax=256)
        if capturedInput == 'y':
            overwrite = True
        else:
            overwrite = False

        if (self.profileExists() and overwrite is False):
            self.printProfile()
        else:
            displayPrompt = ("Enter user identity number, ")
            capturedInput = self.getInputCommandLine(self=self, prompt=displayPrompt, default=os.getlogin(), sizeMax=256)
            self.user.identity = capturedInput

            displayPrompt = ("Enter user name, ")
            capturedInput = self.getInputCommandLine(self=self, prompt=displayPrompt, default=os.getlogin(), sizeMax=256)
            self.user.name = capturedInput

            displayPrompt = ("Enter user mode (cmd, gui), ")
            capturedInput = self.getInputCommandLine(self=self, prompt=displayPrompt, default="cmd", sizeMax=256)
            self.user.mode = capturedInput

            displayPrompt = ("Enter user key location, ")
            capturedInput = self.getInputCommandLine(self=self, prompt=displayPrompt, default=self.getDefaultHomeSave(), sizeMax=256)
            self.user.keyLoc = capturedInput

            displayPrompt = ("Enter user encryption enable, ")
            capturedInput = self.getInputCommandLine(self=self, prompt=displayPrompt, default=False, sizeMax=256)
            self.user.encryptionStatus = capturedInput

            displayPrompt = ("Enter user working directory, ")
            capturedInput = self.getInputCommandLine(self=self, prompt=displayPrompt, default=self.getDefaultHomeSave(), sizeMax=256)
            self.user.workingDir = capturedInput

            for application in enumerate(self.applicationList):
                # Selection set {raad, cloud, access}
                (select, identity, major, minor, name, location, mode, url) = self.getApplicationDefaults(select=str(application[1]))
                updateCount = self.setApplication(select=select, identity=identity, major=major, minor=minor, name=name, location=location, mode=mode, url=url)
                if self.debug:
                    print('{0} update number {1}'.format(select, updateCount))

            self.writeMetaProfile()

            self._verifyMeta()
            return

    def validateInput(self, inputConsole=None, default=False, sizeMax=256):
        """
        Method to accept user input and use it in the creation of a configuration file.
        Args:
            self: Container with internal items.
            inputConsole: Input to validate.
            default: default value in the case of user pressing 'Enter'.
            sizeMax: Total string size

        Returns: The user returned input based on valid inputs of limited size.
        """
        if inputConsole == '' or \
           inputConsole is None or \
           (len(inputConsole) == 0 and len(inputConsole) == sizeMax):
            inputConsole = default
        else:
            try:
                inputConsole = str(inputConsole)
            except Exception as errorEncountered:
                # Handle input error or assign default for invalid input
                inputConsole = None
                print("Exception occurred {0}".format(errorEncountered))
        if self.debug:
            print('Captured {0}'.format(inputConsole))
        return inputConsole

    def newUserGUI(self, user_identity, user_name, user_mode, user_keyLoc, user_encryptionStatus, user_workingDir):
        return

    def addApplication(self):
        """
        The method to capture user information for a new profile.
        Returns: None
        """
        applicationValid = False
        print(" Preparing for Application Input, current apps are: {0}".format(self.applicationList))

        displayPrompt = ("Enter select name, ")
        capturedInput = self.getInputCommandLine(self=self, prompt=displayPrompt, default=os.getlogin(), sizeMax=256)
        selectD = capturedInput

        (select, identity, major, minor, name, location, mode, url) = self.getApplicationDefaults(select=selectD)

        displayPrompt = ("Enter identify number, ")
        capturedInput = self.getInputCommandLine(self=self, prompt=displayPrompt, default=identity, sizeMax=256)
        identityD = capturedInput

        displayPrompt = ("Enter major number, ")
        capturedInput = self.getInputCommandLine(self=self, prompt=displayPrompt, default=major, sizeMax=256)
        majorD = capturedInput

        displayPrompt = ("Enter minor number, ")
        capturedInput = self.getInputCommandLine(self=self, prompt=displayPrompt, default=minor, sizeMax=256)
        minorD = capturedInput

        displayPrompt = ("Enter name, ")
        capturedInput = self.getInputCommandLine(self=self, prompt=displayPrompt, default=name, sizeMax=256)
        nameD = capturedInput

        displayPrompt = ("Enter location, ")
        capturedInput = self.getInputCommandLine(self=self, prompt=displayPrompt, default=location, sizeMax=256)
        locationD = capturedInput

        displayPrompt = ("Enter mode, ")
        capturedInput = self.getInputCommandLine(self=self, prompt=displayPrompt, default=mode, sizeMax=256)
        modeD = capturedInput

        displayPrompt = ("Enter URL, ")
        capturedInput = self.getInputCommandLine(self=self, prompt=displayPrompt, default=url, sizeMax=256)
        urlD = capturedInput

        if selectD is not None and \
           identityD is not None and \
           majorD is not None and \
           minorD is not None and \
           nameD is not None and \
           locationD is not None and \
           modeD is not None and \
           urlD is not None:
            applicationValid = True

        if applicationValid is True and selectD in self.applicationList:
            updateCount = self.setApplication(select=selectD, identity=identityD, major=majorD, minor=minorD, name=nameD, location=locationD, mode=modeD, url=urlD)
        elif applicationValid is True:
            # @todo we will want to add extensions and for now blindly add another application.
            print("New application not supported in newApplication() creation...")
            # self.otherApps.append(self.applicationIdentifier())
            # updateCount = self._setApplication(app=self.otherApps[len(self.otherApps)], identity=identityD, major=majorD, minor=minorD, name=nameD, location=locationD, mode=modeD, url=urlD)
            return  # Early exit
        else:
            updateCount = 0
            print("Invalid newApplication() creation...")
            return  # Early exit

        if self.debug:
            print('{0} update number {1}'.format(selectD, updateCount))
        self.writeMetaProfile()  # @todo we do not write other applications yet so we need to add this functionality later.
        return

    def readProfileAsDictionary(self):
        """
        For a given, read profile into dictionary format.
        Returns: dictionary constructed from the  internal meta.
        """
        config, userConfig = self.readProfile()
        profileDictionary = {}
        for section in config.sections():
            profileDictionary[section] = {}
            for option in config.options(section):
                profileDictionary[section][option] = config.get(section, option)
        if self.debug:
            print('Dictionary \n{0}'.format(profileDictionary))
        return profileDictionary


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
    (options, args) = parser.parse_args()

    ##############################################
    # Main
    ##############################################
    testUser = userConfigurationProfile(debug=options.debug)
    testUser.newUser()
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
