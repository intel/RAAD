#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Daniel Garces
# *****************************************************************************/
# @package guiCommon
import re, math, dataclasses

import src.software.TSV.DefragHistoryGrapher as DHG
import src.software.TSV.visualizeTS as VTS
import src.software.MEP.mediaErrorPredictor as MEP
import src.software.autoAI.mediaPredictionRNN as RNN
import src.software.DP.preprocessingAPI as DP


@dataclasses.dataclass()
class dictElement:
    _key = None
    _value = None
    _type = None
    _possible = None
    _default = None
    _prompt = None
    _tooltip = None

    def __init__(self, nKey=None, nValue=None, nType=None, nPossible=None, nDefault=None, nPrompt=None, nTooltip=None):
        """
        User application configuration information
        """
        self._key = nKey  # Dictionary like key
        self._value = nValue  # Dictionary like value
        self._type = nType  # Type of item added. I.E. str, int, float
        self._possible = nPossible  # when the value is updated it will add possible values
        self._default = nDefault  # default for a given addition
        self._prompt = nPrompt  # User prompt information.
        self._tooltip = nTooltip  # Tool tip information for the given field.

    def getInputs(self):
        return dict(key=self._key,  # Dictionary like key
                    value=self._value,  # Dictionary like value
                    type=self._type,  # Type of item added. I.E. str, int, float
                    values=self._possible,  # when the value is updated it will add possible values
                    default_values=self._default,  # default for a given addition
                    prompt=self._prompt,  # User prompt information.
                    tooltip=self._tooltip  # Tool tip information for the given field.
                    )

    def getKey(self):
        return self._key

    def getValue(self):
        return self._value

    def setValue(self, value):
        self._value = value

    def getType(self):
        return self._type

    def getPossible(self):
        return self._possible

    def getDefault(self):
        return self._default

    def getPrompt(self):
        return self._prompt

    def getTooltip(self):
        return self._tooltip


@dataclasses.dataclass()
class collectGUI:
    # _dictSet = None  # Vector data object to contain all the GUI variables.
    _dictSet = list()  # Vector data object to contain all the GUI variables.
    _natural = tuple('123456789')  # Natural numbers for the interface.
    _inf = math.inf  # Infinity
    _supportedTypes = (_natural, str, bool, float)  # Supported types for the collection interface

    def __init__(self):
        import os
        """
        User application configuration information
        """
        # Tools - data.collect
        self._dictSet.append(dictElement(nKey='data.collect.toolChoice',
                                         nValue=None,
                                         nType=str,
                                         nPossible=['PARSE', 'CLI', 'TWIDL', 'IMAS'],
                                         nDefault='CLI',
                                         nPrompt='Usage Case for Intel',
                                         nTooltip='CLI is the NVMe-CLI Open Source Tool. TWIDL is the Intel internal tool. IMAS is the Intel Memory and Storage Tool'))
        self._dictSet.append(dictElement(nKey='data.collect.ssdChoice',
                                         nValue=None,
                                         nType=self._natural,
                                         nPossible=[1, '/dev/nvme0n1', self._inf],
                                         nDefault='/dev/nvme0n1',
                                         nPrompt='SSD Selection Number',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='data.collect.workingDirInput',
                                         nValue=None,
                                         nType=str,
                                         nPossible=None,
                                         nDefault=os.getcwd(),
                                         nPrompt='Input Working directory',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='data.collect.fwParsers',
                                         nValue=None,
                                         nType=str,
                                         nPossible=None,
                                         nDefault='Auto-Parse/decode/ADP_UV',
                                         nPrompt='Firmware parser directory',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='data.collect.workingDirOutput',
                                         nValue=None,
                                         nType=str,
                                         nPossible=None,
                                         nDefault=os.getcwd(),
                                         nPrompt='Output Working directory',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='data.collect.numberOfQueries',
                                         nValue=None,
                                         nType=self._natural,
                                         nPossible=[1, self._inf],
                                         nDefault='10',
                                         nPrompt='Number of Queries',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='data.collect.timeFrame',
                                         nValue=None,
                                         nType=self._natural,
                                         nPossible=[1, self._inf],
                                         nDefault='60',
                                         nPrompt='Time frame to collect',
                                         nTooltip=None))
        # Display 2D-Matrix - data.table
        self._dictSet.append(dictElement(nKey='data.table.telemetryDataTable',
                                         nValue=None,
                                         nType=None,
                                         nPossible=[],
                                         nDefault=None,
                                         nPrompt='Telemetry Meta Data',
                                         nTooltip='Telemetry Data Table'))
        # AXON data upload mode - data.upload
        self._dictSet.append(dictElement(nKey='data.upload.uploadMode',
                                         nValue=None,
                                         nType=str,
                                         nPossible=['test', 'development', 'production'],
                                         nDefault='test',
                                         nPrompt='Please enter your upload Destination',
                                         nTooltip='Database destination'))
        # Machine Learning Classify - ml.classify
        self._dictSet.append(dictElement(nKey='ml.classify.passes',
                                         nValue=None,
                                         nType=self._natural,
                                         nPossible=[1, self._inf],
                                         nDefault=20,
                                         nPrompt='Passes',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='ml.classify.steps',
                                         nValue=None,
                                         nType=self._natural,
                                         nPossible=[1, self._inf],
                                         nDefault=20,
                                         nPrompt='Steps',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='ml.classify.objectiveOrientedAssociation',
                                         nValue=None,
                                         nType=self._natural,
                                         nPossible=[1, self._inf],
                                         nDefault=6,
                                         nPrompt='OOA',
                                         nTooltip='Objective-Oriented Association'))
        self._dictSet.append(dictElement(nKey='ml.classify.nearestNeighbor',
                                         nValue=None,
                                         nType=self._natural,
                                         nPossible=[1, self._inf],
                                         nDefault=10,
                                         nPrompt='NN',
                                         nTooltip='ml.classify.nearestNeighbor'))
        # Set Friend-or-foe-Q (ff), mini-max-Q (mn), correlated Q-learning (ce)
        self._dictSet.append(dictElement(nKey='ml.classify.qLearning',
                                         nValue=None,
                                         nType=str,
                                         nPossible=['ff', 'mn', 'ce'],
                                         nDefault='ff',
                                         nPrompt='Q',
                                         nTooltip='Friend-or-foe-Q (ff), mini-max-Q (mn), correlated Q-learning (ce)'))
        self._dictSet.append(dictElement(nKey='ml.classify.nGram',
                                         nValue=None,
                                         nType=self._natural,
                                         nPossible=[0, self._inf],
                                         nDefault=5,
                                         nPrompt='N-Gram',
                                         nTooltip='Contiguous sequence of n items from a given sample'))
        self._dictSet.append(dictElement(nKey='ml.classify.learningRate',
                                         nValue=None,
                                         nType=float,
                                         nPossible=[0, 1.0],
                                         nDefault=0.4,
                                         nPrompt='L',
                                         nTooltip='Learning Rate'))
        # Set 'BatchNorm', 'other'
        self._dictSet.append(dictElement(nKey='ml.classify.layers',
                                         nValue=None,
                                         nType=str,
                                         nPossible=['batchNorm'],
                                         nDefault='batchNorm',
                                         nPrompt='Layers',
                                         nTooltip='Each layer learns by itself, more independently'))
        self._dictSet.append(dictElement(nKey='ml.classify.flags.normalize',
                                         nValue=None,
                                         nType=bool,
                                         nPossible=['True', 'False'],
                                         nDefault='False',
                                         nPrompt='Normalize',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='ml.classify.flags.verbose',
                                         nValue=None,
                                         nType=bool,
                                         nPossible=['True', 'False'],
                                         nDefault='False',
                                         nPrompt='Verbose',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='ml.classify.flags.cluster',
                                         nValue=None,
                                         nType=bool,
                                         nPossible=['True', 'False'],
                                         nDefault='False',
                                         nPrompt='Cluster',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='ml.classify.flags.flush',
                                         nValue=None,
                                         nType=bool,
                                         nPossible=['True', 'False'],
                                         nDefault='False',
                                         nPrompt='Flush',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='ml.classify.flags.write',
                                         nValue=None,
                                         nType=bool,
                                         nPossible=['True', 'False'],
                                         nDefault='False',
                                         nPrompt='Flush',
                                         nTooltip='Flush intermediate outputs'))
        self._dictSet.append(dictElement(nKey='ml.classify.flags.keep',
                                         nValue=None,
                                         nType=bool,
                                         nPossible=['True', 'False'],
                                         nDefault='False',
                                         nPrompt='Write',
                                         nTooltip='Write result Data'))
        self._dictSet.append(dictElement(nKey='ml.classify.lossFunction',
                                         nValue=None,
                                         nType=str,
                                         nPossible=['Cross-Entropy', 'Logistic', 'Hinge', 'Huber', 'Kullerback',
                                                    'MAE(L1)', 'MSE(L2)', 'MB(L0)'],
                                         nDefault='MB(L0)',
                                         nPrompt='Keep',
                                         nTooltip='Keep Intermediate Data'))
        self._dictSet.append(dictElement(nKey='profile.user.identify',
                                         nValue=None,
                                         nType=self._natural,
                                         nPossible=[1, self._inf],
                                         nDefault=1,
                                         nPrompt='Enter identity number',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='profile.user.name',
                                         nValue=None,
                                         nType=str,
                                         nPossible=['lab'],
                                         nDefault='lab',
                                         nPrompt='Enter username',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='profile.user.mode',
                                         nValue=None,
                                         nType=str,
                                         nPossible=['cmd', 'gui'],
                                         nDefault='gui',
                                         nPrompt='Enter mode',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='profile.user.keyLoc',
                                         nValue=None,
                                         nType=str,
                                         nPossible=[],
                                         nDefault=None,
                                         nPrompt='Key encrypt-decrypt location',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='profile.user.encryptionStatus',
                                         nValue=None,
                                         nType=bool,
                                         nPossible=['True', 'False'],
                                         nDefault='False',
                                         nPrompt='Enable Encryption',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='profile.user.workingDir',
                                         nValue=None,
                                         nType=str,
                                         nPossible=[],
                                         nDefault=os.getcwd(),
                                         nPrompt='Enter working directory',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='profile.application.raad.identify',
                                         nValue=None,
                                         nType=self._natural,
                                         nPossible=[],
                                         nDefault=None,
                                         nPrompt='Enter identity number',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='profile.application.raad.major',
                                         nValue=None,
                                         nType=self._natural,
                                         nPossible=[],
                                         nDefault=None,
                                         nPrompt='Enter major version number',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='profile.application.raad.minor',
                                         nValue=None,
                                         nType=self._natural,
                                         nPossible=[],
                                         nDefault=None,
                                         nPrompt='Enter minor version number',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='profile.application.raad.name',
                                         nValue=None,
                                         nType=str,
                                         nPossible=['raad'],
                                         nDefault='raad',
                                         nPrompt='Enter name',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='profile.application.raad.location',
                                         nValue=None,
                                         nType=str,
                                         nPossible=[],
                                         nDefault=os.getcwd(),
                                         nPrompt='Execution location',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='profile.application.raad.mode',
                                         nValue=None,
                                         nType=str,
                                         nPossible=['cmd', 'gui'],
                                         nDefault='gui',
                                         nPrompt='Enter mode',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='profile.application.raad.url',
                                         nValue=None,
                                         nType=str,
                                         nPossible=['https://github.com/intel/raad.git'],
                                         nDefault='https://github.com/intel/raad.git',
                                         nPrompt='Enter URL',
                                         nTooltip=None))
        self._dictSet.append(dictElement(nKey='user.feedback',
                                         nValue=None,
                                         nType=str,
                                         nPossible=[],
                                         nDefault=None,
                                         nPrompt='Please provide feedback based on experience.',
                                         nTooltip=None))

    def keyExists(self, key=None):
        """
        Determines if the keys exist in the current vector.
        Args:
            key: key string to search for in the array.

        Returns: If the key is found and the index found.

        """
        found = False
        index = -1
        if self._dictSet is not None and key is not None:
            for i in self._dictSet:
                if key == self._dictSet[i]:
                    found = True
                    index = i
                    break
        return found, index

    def getVector(self, key):
        """
        Returns the row of data for a given key.
        Args:
            key:

        Returns:

        """
        if self._dictSet is not None and key is not None:
            for element in self._dictSet:
                if key == element.getKey():
                    return element.getInputs()
        else:
            return None

    def valueSet(self, key=None, value=None):
        """
        Method to search for a key value pair then return the vector location.
        Args:
            key: Key to look for.
            value: Value to set for the given key.

        Returns: The vector location of the row for the given key.
        """
        location = -1
        if self._dictSet is not None and key is not None:
            for i in self._dictSet:
                if key == self._dictSet[i].getKey():
                    if self.isPossible(key=key, value=value):
                        # Update possible values if not in dictionary.
                        self._dictSet[i].getPossible().append(value)
                        self._dictSet[i].setValue(value)
                        location = i
                    break
        return location

    def getDictSet(self):
        return self._dictSet

    def isPossible(self, key=None, value=None):
        """
        Method to determine if we can set a value field to a given value from possible existing values
        Args:
            key: Key within the vector.
            value: Value with associated with the key.

        Returns: Returns if the assignment for a given key value pair is possible.

        """
        # Check to see if the dictionary is constructed, key and value are possible before searching for possible setting values.
        (exists, index) = self.keyExists(key=key)
        if ((self._dictSet is not None) and (value is not None) and (exists is True) and index >= 0):
            i = index
            status_str = self._checkInterval_str(i=i, value=value)
            status_natural = self._checkInterval_str(i=i, value=value)
            status_float = self._checkInterval_str(i=i, value=value)
            status_bool = self._checkInterval_str(i=i, value=value)
            if (status_str or status_natural or status_float or status_bool):
                return True
            else:
                AssertionError(IndexError)
        else:
            return False

    def _checkInterval_str(self, i=None, value=None):
        """
        Method to determine if the current value is within the possible string set from init.
        Args:
            i: Index location expected within the vector.
            value: Value to check if possible.

        Returns: Feasibility of the current assignment.
        """
        if self._dictSet[i].getType() == str:
            if value not in self._dictSet[i].getPossible():
                return True
            else:
                AssertionError(ValueError)
        else:
            return False

    def _checkInterval_natural(self, i=None, value=None):
        """
        Method to determine if the current value is within the possible natural set from init.
        Args:
            i: Index location expected within the vector.
            value: Value to check if possible.

        Returns: Feasibility of the current assignment.
        """
        if self._dictSet[i].getType() == self._natural:
            if (value >= self._dictSet[i].getPossible()[0]) and (value >= self._dictSet[i].getPossible()[1]):
                return True
            else:
                AssertionError(ValueError)
        return False

    def _checkInterval_float(self, i=None, value=None):
        """
        Method to determine if the current value is within the possible float set from init.
        Args:
            i: Index location expected within the vector.
            value: Value to check if possible.

        Returns: Feasibility of the current assignment.
        """
        if self._dictSet[i].getType() == float:
            if (value >= self._dictSet[i].getPossible()[0]) and (value >= self._dictSet[i].getPossible()[1]):
                return True
            else:
                AssertionError(ValueError)
        return False

    def _checkInterval_bool(self, i=None, value=None):
        """
        Method to determine if the current value is within the possible bool set from init.
        Args:
            i: Index location expected within the vector.
            value: Value to check if possible.

        Returns: Feasibility of the current assignment.
        """
        if self._dictSet[i].getType() == bool:
            if (str(value) == self._dictSet[i].getPossible()[0]) or (str(value) == self._dictSet[i].getPossible()[1]):
                return True
            else:
                AssertionError(ValueError)
        return False


class ObjectConfigGenericObject:
    objectFilePath = None
    objectIDs = []
    vizDict = None  # Dictionary containing all the time-series data with the appropriate nesting according to the fields
    vts = None
    objectIDDecode = None

    def __init__(self, configFilePath, debug=False):
        self.objectFilePath = configFilePath
        self.debug = debug
        self.readConfigContent()

    def readConfigContent(self, debug=None):
        """
        function for reading the configuration file into a dictionary and populating the ObjectConfig
        instance

        Returns:
            vts: visualizeTS instance
        """
        if debug is not None and isinstance(debug, bool):
            self.debug = debug
        vts = VTS.visualizeTS(self.debug)
        self.vizDict = DP.preprocessingAPI().loadDataDict(self.objectFilePath)
        self.objectIDs = list(map(lambda x: x.strip("uid-"), self.vizDict.keys()))
        self.objectIDDecode = {self.vizDict[uid]["name"]: uid for uid in self.vizDict.keys()}
        self.vts = vts
        return vts

    def GetObjectIDDecode(self):
        return self.objectIDDecode


# same as ObjectConfigARMAPredict
class ObjectConfigARMA:
    objectFilePath = None
    objectIDs = []
    trackingVars = []

    def __init__(self, configFilePath):
        self.objectFilePath = configFilePath
        self.dataDict = None

    def readConfigContent(self, debug=False):
        """
        function for reading the configuration file into a dictionary and populating the ObjectConfig
        instance

        Args:
            debug: Boolean flag to activate debug statements

        Returns:
            mep: MediaErrorPredictor instance
        """
        mep = MEP.MediaErrorPredictor(self.objectFilePath, debug=debug)
        self.dataDict = mep.dataDict
        self.objectIDs = self.dataDict.keys()

        return mep


class ObjectConfigRNN:
    objectFilePath = None
    objectIDs = []

    def __init__(self, configFilePath):
        self.objectFilePath = configFilePath
        self.dataDict = None
        self.objectIDs = None
        self.columns = None

    def readConfigContent(self, debug=False):
        """
        function for reading the configuration file into a dictionary and populating the ObjectConfig
        instance

        Args:
            debug: Boolean flag to activate debug statements

        Returns:
            rnn: mediaPredictionRNN instance
        """
        rnn = RNN.timeSeriesRNN(configFilePath=self.objectFilePath, debug=debug)
        if rnn.dataDict is not None:
            self.dataDict = rnn.dataDict
            self.objectIDs = list(self.dataDict.keys())
        else:
            self.dataDict = rnn.dataDF
            self.objectIDs = ["MEDIA_MADNESS"]
            self.columns = rnn.columns

        return rnn


class DefragConfig:
    dhFilePath = None
    setPoints = []
    trackingVars = []
    secondaryVars = []

    def __init__(self, configFilePath, mode):
        self.dhFilePath = configFilePath
        self.mode = mode
        self.vizDict = None

    def readConfigContent(self, debug=False):
        """
        function for reading the configuration file into a dictionary and populating the DefragConfig
        instance

        Args:
            debug: Boolean flag to activate debug statements

        Returns:
            dhg: DefragHistoryGrapher instance
        """
        dhg = DHG.DefragHistoryGrapher(mode=self.mode, encapsulatingStruct="__anuniontypedef115__")
        self.vizDict = dhg.generateDataDictFromConfig(self.dhFilePath)
        self.setPoints = dhg.getSetPointNames()
        object_t = "uid-41"
        try:
            subdict = self.vizDict[object_t]
        except Exception:
            print("DefragHistory object not found in the configuration file")
            return
        if debug is True:
            print("DefragHistory object found...")
        if self.mode == 1:
            litePattern = re.compile(pattern="LITE")
            normalPattern = re.compile(pattern="NORMAL")
            extendedPattern = re.compile(pattern="EXTENDED")
            logType = subdict["header"]["prevlogtype"][0]

            if litePattern.search(logType):
                logName = "loglite[0]"
            elif extendedPattern.search(logType):
                logName = "logextended[0]"
            elif normalPattern.search(logType):
                logName = "lognormal[0]"
            else:
                raise Exception("Log type not found " + logType)
            logDict = subdict["__anuniontypedef115__"][logName]
            self.trackingVars = logDict.keys()
            self.secondaryVars = logDict.keys()
        elif self.mode == 2:
            logName = "log[0]"
            logDict = subdict[logName]
            self.trackingVars = logDict.keys()
            self.secondaryVars = logDict.keys()

        return dhg


class GenericObjectGraph():
    """
    Generating the graphical interface window for graphing a generic object
    """
    primaryVarLabels = ["-PFVAR-", "-PSVAR-", "-PTVAR-"]
    secondaryVarLabels = ["-SFVAR-", "-SSVAR-", "-STVAR-"]

    @staticmethod
    def populate_object(windowVar, dirPathVar):
        """
        function for populating the ObjectConfig instance and updating the drop down menu for the objects
        available in the configuration file

        Args:
            windowVar: window instance
            dirPathVar: String for the path to the configuration file

        Returns:
            vtsVarLocal: visualizeTS instance
            objectFileVarLocal: ObjectConfig instance
            objectNamesDict: Dictionary of object identifiers (ex. uid-6) to object names (ex. ThermalSensor)
        """
        objectFileVarLocal = ObjectConfigGenericObject(configFilePath=str(dirPathVar))
        vtsVarLocal = objectFileVarLocal.readConfigContent()
        objectList = list(objectFileVarLocal.objectIDs)
        objectNamesDict = {}
        for key in objectList:
            currentObjectVarLocal = "uid-" + key
            currentNameVar = objectFileVarLocal.vizDict[currentObjectVarLocal]["name"]
            objectNamesDict[currentNameVar] = key
        windowVar["-OBJECT-"].Update(values=list(objectNamesDict.keys()))
        return vtsVarLocal, objectFileVarLocal, objectNamesDict

    def display_dir(self, windowVar, objectFileVar, currentObjectVar):
        """
        function for updating the values contained in the drop down menus for primary and secondary variables

        Args:
            windowVar: window instance
            objectFileVar: ObjectConfig instance
            currentObjectVar: String for the name of the current object (ex. uid-6)

        Returns:

        """
        trackingVars = objectFileVar.vizDict[currentObjectVar].keys()
        primaryVars = ["None"] + list(trackingVars)
        secondaryVars = ["None"] + list(trackingVars)
        for name in self.primaryVarLabels:
            windowVar[name].Update(values=primaryVars)
        for name in self.secondaryVarLabels:
            windowVar[name].Update(values=secondaryVars)
        return

    @staticmethod
    def is_data_selected_from_fields(listVar):
        """
        function for checking if data has been selected for a list

        Args:
            listVar: list of data values

        Returns:

        """
        return (len(listVar) > 0)

    def create_new_graph_window(self, valuesVar, vtsVar, objectFileVar, currentObjectVar):
        """
        function for generating a new graph window using the matplot functionality of PySimpleGUI

        Args:
            valuesVar: List of values collected from window
            vtsVar: visualizeTS instance
            objectFileVar: ObjectConfig instance
            currentObjectVar: String for the name of the current object (ex. uid-6)

        Returns:

        """
        trackingVars = []
        secondaryVars = []

        for name in self.primaryVarLabels:
            if valuesVar[name] != "None":
                trackingVars.append(valuesVar[name])

        for name in self.secondaryVarLabels:
            if valuesVar[name] != "None":
                secondaryVars.append(valuesVar[name])

        if self.is_data_selected_from_fields(trackingVars):
            currentObjects = [currentObjectVar.strip("uid-")]
            print(str(currentObjects))
            dataDict = objectFileVar.vizDict
            start = valuesVar['-START-']
            end = valuesVar['-END-']
            matrixProfile = valuesVar['-MATRIX-']
            matrixProfileFlag = False
            if matrixProfile == "Yes":
                matrixProfileFlag = True
            elif matrixProfile == "No":
                matrixProfileFlag = False

            if matrixProfileFlag:
                unionFields = trackingVars + secondaryVars
                dataDict = vtsVar.generateMP(dataDict, obj=currentObjects, fields=unionFields, subSeqLen=20,
                                             visualizeAllObj=False, visualizeAllFields=False)
            vtsVar.generateTSVisualizationGUI(currentObjectVar, dataDict[currentObjectVar], trackingVars, secondaryVars,
                                              start, end)
        return
