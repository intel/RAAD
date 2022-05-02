#!/usr/bin/python
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Rogelio Macedo, Daniel Garces, Joseph Tarango
# *****************************************************************************/
import json, os, sys, re, datetime, pprint, csv, ast
import numpy as np
import scipy.signal as sp
import pandas as pd
import src.software.mp.matrixProfile as mp
from src.software.utilsCommon import getDateTimeFileFormatString

if sys.version_info.major > 2:
    import configparser as cF
else:
    import ConfigParser as cF  # @todo python 2 variant

class preprocessingAPI(object):
    """
    Utility class for handling data preprocessing tasks

    """

    def setOutputFilename(self, filename, extension='json', mode=1):
        """
        Sets the output filename for the JSON Jira results and renames the current file to the highest
        available archive number

        Args:
            filename: arbitrary name for a file
            extension: file format
            mode: new methods use mode 2, any other value provides original behavior

        Returns:
            the new archive name that replaced the existing one
        """
        archiveNumber = 0
        finishedArcing = 0
        outputFilename = filename
        tmpFilename = filename

        while finishedArcing == 0:
            if mode == 2:
                var = os.path.abspath(os.path.join(os.getcwd(), tmpFilename)) + '.' + extension
                if os.path.isfile(var):
                    tmpFilename = outputFilename + "." + str(archiveNumber)
                    archiveNumber += 1
                else:
                    finishedArcing += 1
            else:
                if (os.path.isfile(tmpFilename)):
                    tmpFilename = outputFilename + "." + str(archiveNumber)
                    archiveNumber += 1
                else:
                    finishedArcing += 1
        #
        # If we detected the file already exists, rename it to the next
        # available archive number.  The places the most recent archive
        # at the highest number
        #
        if (archiveNumber > 0):
            # os.rename(outputFilename, tmpFilename) # rmacedo: this is not needed right now
            print(("Output file: " + filename + " exists.  Renaming existing file to: " + tmpFilename))
        return tmpFilename + '.' + extension if mode == 2 else tmpFilename

    def flattenJson(self, jsoninput, dataID, jsonoutput='data/jiraData/flat/flatIssues.json'):
        """

        Args:
            jsoninput: String for the file name of the input for flattening
            dataID: String for the ID of the data stored in the json object
            jsonoutput: String for the file name of the flattened output

        Returns:
            data: flatten dictionary containing the data stored in the jason file

        """
        # extract output file name without '.json' file extension
        finalJsonOutput = self.setOutputFilename(
            filename=jsonoutput.split('.json')[0] + dataID,
            extension='json',
            mode=2
        )

        # Required imports from main
        mainfile = os.path.dirname(r'src/main.py')
        sys.path.append(mainfile)
        from src.main import findAll
        findAll(
            fileType=".py",
            directoryTreeRootNode=mainfile,
            debug=False,
            doIt=True,
            verbose=False
        )
        from src.software.container.genericObjects import ObjectUtility

        # read json into dict
        filepath = os.path.abspath(os.path.join(os.getcwd(), jsoninput))
        with open(filepath) as jf:
            jj = json.load(jf)

        # flatten dict
        data = ObjectUtility.simpleFlatten(objNotFlat=jj, sep='.')

        with open(finalJsonOutput, 'w') as fjson:
            json.dump(data, fjson, indent=4)

        return data

    def removeNullFields(self, filename, dataID, outfile='data/jiraData/removeNull/removeNull.json'):
        """
        Make sure that JSON is flatten

        Args:
            filename: String for the filename for flat json object
            dataID: String for the ID of the data stored in the json object
            outfile: string for the name of the output file

        Returns:

        """
        finalOutfile = self.setOutputFilename(
            filename=outfile.split('.json')[0] + dataID,
            extension='json',
            mode=2
        )
        ifile = os.path.abspath(os.path.join(os.getcwd(), filename))
        with open(ifile, 'r') as f:
            jdata = json.load(f)
        res = dict([(key, val) for key, val in jdata.items() if val is not None])
        ofile = os.path.abspath(os.path.join(os.getcwd(), finalOutfile))
        with open(ofile, 'w') as of:
            json.dump(res, of, indent=4)
        return

    @staticmethod
    def readFileIntoConfig(configFileName):
        """
        function for reading a file into a config

        Args:
            configFileName: String of the path name for the configuration file containing the data for the time-series

        Returns:
            config object with the data of the file already inside it

        """
        config = cF.ConfigParser()
        config.read(configFileName)
        return config

    @staticmethod
    def loadConfigIntoDict(config, debug):
        """
        function that loads the ConfigParser object values into a dictionary

        Args:
            config: ConfigParser that contains the object values
            debug: Boolean flag to activate debug statements

        Returns:
            Dictionary with the object values from the ConfigParser

        """
        digits = re.compile("\d+")
        sections = config.sections()
        resultDict = {}
        if debug is True:
            print("Processing .ini file...")
        for section in sections:
            subdict = {}

            for option in config.options(section):
                value = config.get(section, option)
                if option == 'name' or option == 'ref' or option == 'uid':
                    subdict[option] = value
                else:
                    elemList = digits.findall(value)
                    finalList = list(map(int, elemList))
                    tempList = value.split(",")
                    if not finalList or len(finalList) != len(tempList):
                        newLine = value.replace("[", "")
                        newLine = newLine.replace("]", "")
                        newLine = newLine.replace("\'", "")
                        finalList = newLine.split(",")
                        finalList = list(map(lambda x: x.strip(), finalList))
                    subdict[option] = finalList
            resultDict[section] = subdict
        return resultDict

    @staticmethod
    def transformDict(intermediateDict, debug):
        """
        function for transforming the dictionary from a flat structure into the nested structure required for
        generating the right format for the plain text files

        Args:
            intermediateDict: Dictionary containing the flat structure for all the objects contained in the
            configuration file
            debug: Boolean flag to activate debug statements

        Returns:
            Dictionary containing the expanded structure for all the objects contained in the configuration file

        """
        resultDict = {}
        for object_t in intermediateDict.keys():
            if debug:
                print(f"Processing object: {object_t}")
            resultDict[object_t] = {}
            objectDict = resultDict[object_t]
            for option in intermediateDict[object_t]:
                optionFields = option.split(".")
                subdict = objectDict
                for i in range(len(optionFields) - 1):
                    if optionFields[i] not in subdict:
                        subdict[optionFields[i]] = {}
                    subdict = subdict[optionFields[i]]
                subdict[optionFields[len(optionFields) - 1]] = intermediateDict[object_t][option]
        return resultDict

    @staticmethod
    def getDateFromName(dirName="sample"):
        """
        function to extract datetime object from directory name

        Args:
            dirName: String representation of the directory name

        Returns:
            datetime object containing the date parsed in the dirName

        """
        components = dirName.replace(".bin", "").split("_")
        print("components: ", components)
        date = components[-1][0:26-4]  # @todo dgarges. We should use a regular expression tokenizer to best fit fields and ignore bad formats.
        if len(components) > 1:
            return datetime.datetime.strptime(date, getDateTimeFileFormatString())
        else:
            return datetime.datetime.now()

    @staticmethod
    def anyObjectToDictionary(self):
        """
        function for turning an object into a dictionary using the __dict__ field

        Args:
            self: object of interest

        Returns:
            Dictionary representation of self - object of interest

        """
        import json
        return json.loads(json.dumps(self, default=lambda o: o.__dict__))

    @staticmethod
    def objectToDictionary(objectToWalk):
        """
           function for turning an object into a dictionary using iteration

           Args:
               objectToWalk: object to be turned into dictionary

           Returns:
               Dictionary representation of objectToWalk

           """
        return dict(
            (key, getattr(objectToWalk, key)) for key in dir(objectToWalk) if key not in dir(objectToWalk.__class__))

    @staticmethod
    def classToDictionary(objectToWalk, filterData=True):
        """
           function for turning a class into a dictionary using iteration and the wrapper function vars()

           Args:
               objectToWalk: object to be turned into dictionary
               filterData: Boolean value to ignore atttributes that start with underscore

           Returns:
               Dictionary representation of self - object of interest

           """
        listStr = {}
        if filterData is True:
            all_vars = listStr
            inst_vars = vars(objectToWalk)  # get any attrs defined on the instance (self)
            all_vars.update(inst_vars)
            # filter out private attributes
            public_vars = {k: v for k, v in all_vars.items() if not k.startswith('_') and "dataDict" not in k}
        else:
            class_vars = vars(objectToWalk.__class__)  # get any "default" attrs defined at the class level
            all_vars = dict(class_vars)
            inst_vars = vars(objectToWalk)  # get any attrs defined on the instance (self)
            all_vars.update(inst_vars)
            public_vars = {k: v for k, v in all_vars.items()}
        listStr = public_vars
        # pprint.pprint(pprint.pformat(listStr))
        return listStr

    @staticmethod
    def loadCSVIntoDict(configFileName, debug=False):
        """
        function that loads the CSV object values into a dictionary

        Args:
            configFileName: String of the path name for the csv file containing the data for the time-series
            debug: Boolean flag to activate debug statements

        Returns:
            Dictionary with the object values from the ConfigParser

        """
        df = pd.read_csv(configFileName, names=['names', 'values'], sep='\t', header=None, quotechar='|',
                         quoting=csv.QUOTE_MINIMAL)
        resultDict = {}
        if debug is True:
            print("Processing .csv file...")

        for i, row in df.iterrows():
            value = row['values']
            sectionFields = row['names'].split(".")
            objectName = sectionFields[0]
            try:
                extractedValue = ast.literal_eval(value)
            except BaseException as errorFound:
                extractedValue = str(value)
            sectionFields.pop(0)
            newName = ".".join(sectionFields)

            if objectName not in resultDict:
                resultDict[objectName] = {}
            resultDict[objectName][newName] = extractedValue

        return resultDict

    @staticmethod
    def loadDictIntoConfig(config, resultDict):
        """
        function that loads the previous objects values into a new dictionary

        Args:
            config: ConfigParser that will contain the object values
            resultDict: Dictionary containing the object values to be transferred to config

        Returns:

        """
        for section in sorted(resultDict.keys()):
            config.add_section(section)
            subdict = resultDict[section]

            for option in sorted(subdict.keys()):
                try:
                    config.set(section, option, str(subdict[option]))
                except Exception as ErrorFound:
                    print(f"Error in loadDictIntoConfig() {ErrorFound}")
                    pass
        return

    def loadDataDict(self, configFilePath, debugStatus=False):
        """
        function for loading all datas from a the configuration file into a dictionary

        Args:
            configFilePath: String for the file path containing the .ini file to be processed
            debugStatus: Boolean flag to activate debug statements

        Returns:
            intermediateDict: Dictionary containing all the timeseries data

        """
        config = self.readFileIntoConfig(configFilePath)
        intermediateDict = self.loadConfigIntoDict(config, debugStatus)

        return intermediateDict

    def populateMPStruct(self, MP, subdict, object_t, subSeqLen):
        """
        function for generating the dictionary with the matrix profile values for the time-series

        Args:
            MP: Dictionary where all the data lists will be stored
            subdict: Dictionary where the unprocessed data lists are contained
            object_t: String for the name of the object for which we are extracting the matrix profiles (ex. uid-6)
            subSeqLen: Integer for the window size to be used in the matrix profile generation

        Returns:

        """
        MP[object_t] = {}

        for column in subdict.keys():
            if type(subdict[column][0]) is int:
                arr = sp.resample(subdict[column], len(subdict[column]))
                arr = np.random.normal(arr, np.finfo(float).eps)
                MP[object_t][column] = mp.stomp(arr, subSeqLen)[0].tolist()
                continue

            elif subdict[column][0].lower().islower():
                MP[object_t][column] = subdict[column]
                continue
            else:
                arr = sp.resample(subdict[column], len(subdict[column]))
                arr = np.random.normal(arr, np.finfo(float).eps)
                MP[object_t][column] = mp.stomp(arr, subSeqLen)[0].tolist()

    def generateMP(self, dataDict, subSeqLen=20, debugStatus=False):
        """
        function for generating a matrix profile for multiple time series contained in dataDict

        Args:
            debugStatus:
            dataDict: Dictionary containing all the time-series data
            subSeqLen: Integer value for the length of the sliding window to be used to generate the matrix profile

        Returns:
            MP: Dictionary containing all the data for the matrix profiles associated with the given fields of the
                specified objects

        """
        MP = {}
        if debugStatus is True:
            print("Generating MP...")
        for object_t in dataDict.keys():
            subdict = dataDict[object_t]
            self.populateMPStruct(MP, subdict, object_t, subSeqLen)
        return MP
