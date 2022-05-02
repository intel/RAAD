#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Daniel Garces
# *****************************************************************************/
"""nlogPrediction.py

This module contains the basic functions for generating training data, instantiating all the stages, and training
 the nlog engine used for nlog event forecasting and failure prediction. This script requires
python 3, and tensorflow version 2.3.0 or higher.


Args:
    --nlogFolder: Path for the nlog Folder in which the nlog event files are contained
    --nlogParserFolder: Path for the folder in which the NLogFormats.py script is contained
    --numComponents: Integer for the number of dimensions to be used in the NLOG description embeddings
    --maxNumParams: Integer for the maximum number of parameters that can be contained in an NLOG description
                    for the specified formats file
    --inputSize: Integer for the number of NLOG events to be considered as the input for the predictive models
    --maxOutputSize: Integer for the maximum number of NLOG events to be predicted with the models
    --debug: Verbose printing for debug use
    --widthModelType: name of the model type to be used in the linear regression model for determining the number
                      of NLOG events to be predicted. Must be selected from the following:
                      ['elastic', 'lasso', 'ridge', 'default']
    --timeHiddenUnits: Integer for the number of neurons contained in each hidden layer for the NLOG time stamp
                         predictor model
    --eventsHiddenUnits: Integer for the number of neurons contained in each hidden layer for the NLOG event
                         predictor model
    --paramsHiddenUnits: Integer for the number of neurons contained in each hidden layer for the NLOG parameter
                         predictor mode
    --eventsMaxEpochs: Integer for the maximum number of epochs to be considered when training the NLOG time stamp
                       predictor model
    --eventsMaxEpochs: Integer for the maximum number of epochs to be considered when training the NLOG event
                       predictor model
    --paramsMaxEpochs: Integer for the maximum number of epochs to be considered when training the NLOG parameter
                       predictor model
    --timeOptimizer: name of the optimizer to be used in the NLOG time stamp predictor model. Must be selected
                       from the following: ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']
    --eventsOptimizer: name of the optimizer to be used in the NLOG event predictor model. Must be selected
                       from the following: ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']
    --paramsOptimizer: name of the optimizer to be used in the NLOG parameter predictor model. Must be selected
                       from the following: ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']
    --timeLstmActivation: name of the activation function to be used in the LSTM layers of the NLOG time stamp predictor
                            model. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
    --eventsLstmActivation: name of the activation function to be used in the LSTM layers of the NLOG event predictor
                            model. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
    --paramsLstmActivation: name of the activation function to be used in the LSTM layers of the NLOG parameter
                           'predictor model. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
    --timeLstmInitializer: name of the weight initializer function to be used in the LSTM layers of the NLOG time stamp
                             predictor model. Must be selected from the following:
                             ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                             'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
    --eventsLstmInitializer: name of the weight initializer function to be used in the LSTM layers of the NLOG event
                             predictor model. Must be selected from the following:
                             ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                             'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
    --paramsLstmInitializer: name of the weight initializer function to be used in the LSTM layers of the NLOG
                             parameter predictor model. Must be selected from the following:
                             ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                             'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
    --timeDropout: Boolean flag that indicates if dropout in between layers should be applied to the NLOG time stamp
                     predictor model
    --eventsDropout: Boolean flag that indicates if dropout in between layers should be applied to the NLOG event
                     predictor model
    --paramsDropout: Boolean flag that indicates if dropout in between layers should be applied to the NLOG parameter
                     predictor model

Example:
    Default usage:
        $ python nlogPrediction.py
    Specific usage:
        $ python nlogPrediction.py --nlogFolder data/output/nlog --nlogParserFolder software/parse/nlogParser
          --numComponents 50 --maxNumParams 8 --inputSize 4000 --maxOutputSize 1000 --debug True --widthModelType
          elastic --eventsHiddenUnits 128 --paramsHiddenUnits 128 --eventsMaxEpochs 2000 --paramsMaxEpochs 2000
          --eventsOptimizer SGD --paramsOptimizer SGD --eventsLstmActivation relu --paramLstmActivation relu
          --eventsLstmInitializer random_normal --paramsLstmInitializer random_normal --eventsDropout True
          --paramsDropout True

"""
import ast
import sys, os, datetime, optparse, traceback, re, pprint
import tensorflow, tensorflow.keras
import matplotlib.pyplot as plt
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, RidgeCV, LassoCV, ElasticNetCV
from src.software.utilsCommon import getDateTimeFileFormatString
from src.software.utilsCommon import tryFolder
from src.software.debug import whoami


# PCA is used as the choice of dimensionality reduction algorithm because we are assuming that the sentence embeddings
# are dense. If the sentence embeddings were sparse, we should consider using Singular Vector Decomposition

class NlogUtils(object):

    @staticmethod
    def getDateFromFileName(fileName="sample"):
        """
        function to extract datetime object from directory name. File naming must follow the right format for this
        function to work (e.g. tag_date.txt)

        Args:
            fileName: String representation of the file name

        Returns:
            datetime object containing the date parsed in the dirName

        """
        components = fileName.replace("_NLOG.txt", "").split("_")
        print("components: ", components)

        if len(components) > 2:
            return None
        elif len(components) > 1:
            date = components[-1][0:26 - 4]
            return datetime.datetime.strptime(date, getDateTimeFileFormatString())
        else:
            return datetime.datetime.now()

    @staticmethod
    def extractNlogComponents(lineComponents, initialPos):
        """
        function for extracting the NLOG components from the list of strings generated after splitting a line from the
        original NLOG files

        Args:
            lineComponents: list of strings containing all the NLOG fields after they have been separated using
                            blank spaces
            initialPos: integer for the position that contains the date element

        Returns:
            nlogComponents: list of NLOG fields with the right format for processing

        """
        date = lineComponents[initialPos]
        core = lineComponents[initialPos + 1]
        if lineComponents[initialPos + 2] == '(':
            nlogType = lineComponents[initialPos + 2] + lineComponents[initialPos + 3]
            nlogDescription = lineComponents[initialPos + 4:]
            nlogDescription = " ".join(nlogDescription)
        else:
            nlogType = lineComponents[initialPos + 2]
            nlogDescription = lineComponents[initialPos + 3:]
            nlogDescription = " ".join(nlogDescription)
        nlogComponents = [date, core, nlogType, nlogDescription]
        return nlogComponents

    @staticmethod
    def splitDataSet(x, y, testSize=0.1, randomState=None):
        """
        Function for splitting the dataset into testing and training data sets

        Args:
            x: input values
            y: output values
            testSize: fraction of values to be used for the testing set
            randomState: integer denoting random seed for consistency across trials

        Returns:
            xTrain: numpy array of x values to be used for training
            xTest: numpy array of x values to be used for testing
            yTrain: numpy array of y values to be used for training
            yTest: numpy array of x values to be used for testing

        """
        if randomState is None:
            xTrain, xTest, yTrain, yTest = train_test_split(x, y, test_size=testSize)
        elif isinstance(randomState, int):
            xTrain, xTest, yTrain, yTest = train_test_split(x, y, test_size=testSize, random_state=randomState)
        else:
            xTrain = xTest = yTrain = yTest = None

        xTrain = np.array(xTrain)
        xTest = np.array(xTest)
        yTrain = np.array(yTrain)
        yTest = np.array(yTest)

        return xTrain, xTest, yTrain, yTest

    @staticmethod
    def add_value_labels(ax, spacing=5):
        """Add labels to the end of each bar in a bar chart.

        Arguments:
            ax (matplotlib.axes.Axes): The matplotlib object containing the axes
                of the plot to annotate.
            spacing (int): The distance between the labels and the bars.
        """

        # For each bar: Place a label
        for rect in ax.patches:
            # Get X and Y placement of label from rect.
            y_value = rect.get_height()
            x_value = rect.get_x() + rect.get_width() / 2

            # Number of points between bar and label. Change to your liking.
            space = spacing
            # Vertical alignment for positive values
            va = 'bottom'

            # If value of bar is negative: Place label below bar
            if y_value < 0:
                # Invert space to place label below
                space *= -1
                # Vertically align label at top
                va = 'top'

            # Use Y value as label and format number with one decimal place
            label = "{:.3f}".format(y_value)

            # Create annotation
            ax.annotate(
                label,  # Use `label` as label
                (x_value, y_value),  # Place label at end of the bar
                xytext=(0, space),  # Vertically shift label by `space`
                textcoords="offset points",  # Interpret `xytext` as offset in points
                ha='center',  # Horizontally center label
                va=va)  # Vertically align label differently for positive and negative values.

    @staticmethod
    def extractNlogTime(line):
        """
        function for extracting the date from on NLOG event line

        Args:
            line: string for an NLOG event extracted from the parsed NLOG text files

        Returns:
            list of floats for [hours, minutes, seconds]

        """
        hours = 0
        minutes = 0
        seconds = 0
        if not isinstance(line, str):
            line = str(line)
        components = line.replace("*", "").split()
        dateComp = components[0]
        if dateComp.isdigit():
            dateComp = components[1]
        try:
            timeList = dateComp.split(":")
            hours = float(timeList[0])
            minutes = float(timeList[1])
            seconds = float(timeList[2])
        except BaseException as ErrorContext:
            pprint.pprint(f"{ErrorContext}{os.linesep}{pprint.pformat(whoami())}")
            print("Bad input line in extractNlogTime: ", line)
        return [hours, minutes, seconds]

    @staticmethod
    def formatNlogTime(time):
        """
        Function for generating a string representation for the time

        Args:
            time: list floats for [hours, minutes, seconds]

        Returns:
            timeStr: string with the string representation for the time

        """
        if not np.numpy.isfinite(time[2]):
            seconds = time[2]
        else:
            seconds = 0

        if not np.numpy.isfinite(time[1]):
            minutes = int(round(time[1]))
        else:
            minutes = 0

        if not np.numpy.isfinite(time[0]):
            hours = int(round(time[0]))
        else:
            hours = 0

        if hours == 0 and minutes == 0 and seconds == 0:
            seconds = (2 * sys.float_info.min)

        timeStr = str(hours) + ":" + str(minutes) + ":" + str(seconds)
        return timeStr

    def extractNlogTable(self, nlogFilePath):
        """
        Function for generating the list of elements to be included in the report's NLOG table

        Args:
            nlogFilePath: Path to the NLOG file that contains the summarized NLOG events

        Returns:
            nlogTable: list of rows to be included in the NLOG table of the report

        """
        nlogTable = list()
        try:
            nlogFile = open(nlogFilePath, "r")
            index = 0
            for line in nlogFile:
                if index < 5:
                    index += 1
                else:
                    lineComponents = line.split()
                    if lineComponents[0].isdigit():
                        initialPos = 1
                    else:
                        initialPos = 0
                    nlogComponents = self.extractNlogComponents(lineComponents, initialPos)
                    if nlogComponents[2] == "(ERR)":
                        nlogTable.append(nlogComponents)

        except BaseException as ErrorContext:
            pprint.pprint(f"{ErrorContext}{os.linesep}{pprint.pformat(whoami())}")
            nlogTable = None
            print("Failure while reading NLOG file...")

        return nlogTable


class NlogTokenizer(object):
    def __init__(self, nlogParserFolder="software/parse/nlogParser", numComponents=50, debug=False):
        """
        Function for initializing a NlogTokenizer instance

        Args:
            nlogParserFolder: Path for the folder in which the NLogFormats.py script is contained
            numComponents: Integer for the number of dimensions to be used in the NLOG description embeddings
            debug: Verbose printing for debug use

        Returns:

        """
        self.nlogParserFolder = tryFolder(path=nlogParserFolder)
        self.nlogFormatFile = None
        self.numComponents = numComponents
        self.debug = debug
        nlogSignatures, nlogParsers, nlogEncodings, nlogLabelIndices = self.encodeNlogEvents()
        self.nlogSignatures = nlogSignatures
        self.nlogStringParsers = nlogParsers
        self.nlogEncodings = nlogEncodings
        self.nlogLabelIndices = nlogLabelIndices
        self.reduceDimensionalityOfEmbeddings(numComponents=numComponents)
        self.nlogNeighbors = self.getSignaturesNeighbors()

    def __repr__(self):
        """
        function that overwrites the representation for the window instance

        Returns:
            String with the representative fields for the window

        """
        return '\n'.join([
            f'NLOG Parser Folder: {self.nlogParserFolder}',
            f'NLOG Format File : {self.nlogFormatFile}'])

    @staticmethod
    def _getNLogFormats(formatsFile):
        """
        Function for importing (read and execute) the NLog formats file into this script.
        Stolen from nlogpost2.py getNLogFormats() and modified to work in the class

        Args:
            formatsFile: Path and name of the nlog_formats.py file

        Returns:
            formats: Nlog format object
        """

        # Get Format Strings
        try:
            # Use exec rather than import here.
            # Python maintains cached version of the imported files
            # that don't always get updated when the underlying file changes,
            # even if re-imported.
            myLocals = {}
            formatsFileObj = open(formatsFile)
            exec(formatsFileObj.read(), {}, myLocals)
            formats = myLocals["formats"]
            formatsFileObj.close()
            return formats

        except BaseException as ErrorContext:
            pprint.pprint(f"{ErrorContext}{os.linesep}{pprint.pformat(whoami())}")
            print("Couldn't load the formats file (%s): %s" % (formatsFile, sys.exc_info()[0]))
            return None

    def reformatString(self, formatStr, params):
        """
        Function for handling some special formatting issues -- differences between Python and FW for printf.

        Stolen from nlogpost2.py reformat

        Args:
            formatStr: Starting format string
            params: Parameter value tuple

        Returns:
            string: Updated format string
            tuple: New parameter tuple
        """
        # Return new, modified versions of given format and parameters.
        newFmt = formatStr
        newParams = []
        oldParams = list(params)
        oldParams = np.around(oldParams)
        oldParams = oldParams.astype(int)
        oldIdx = 0
        bits = 0
        myParam = None

        # Hide any "%%" format-specs in the string from the RE searches below.
        newFmt = re.sub('%%', '<<%>><<%>>', newFmt)

        # Find the next parameter specification in the format string.
        for match in re.finditer('(%[-\.\d]*?l*[cdfiusxX])', newFmt):

            try:
                # Check for "long" (64-bit) format.
                if re.match('%[-\.\d]*?l[cdfiusxX]', match.group(1)):
                    # Handle %ld, %lX, %lc, etc.  These take two parameters.
                    myParam = (oldParams[oldIdx] << 32) + oldParams[oldIdx + 1]
                    oldIdx += 2
                    bits = 64
                else:
                    myParam = oldParams[oldIdx]
                    oldIdx += 1
                    bits = 32

            except IndexError:
                pprint.pprint(f"{pprint.pformat(whoami())}")
                print("Index out of bounds encountered while processing the parameter list for:")
                print("  " + formatStr)
                if re.match('.*%l.*', formatStr):
                    print("This is most likely cause by incorrect usage of %l* without the corresponding PARAM64().")
                    print(
                        "Attempting to recover by stripping the 'l' out any instance of '%l*' in the original format string.")
                    print("WARNING: This recovered log may have invalid param values!\n")
                    newFmt = formatStr.replace('%l', '%')
                    return self.reformatString(newFmt, params)

            # Handle differences between Python printf and C/NLog printf.
            if re.match('%[-\.\d]*?l*[di]', match.group(1)):
                # Handle sign for %d (and %i); Python treats everything as unsigned.
                if myParam & (1 << (bits - 1)):
                    myParam -= (1 << bits)

            elif re.match('%[-\.\d]*?l*[cs]', match.group(1)):
                # Handle multiple characters for %c (and %s) -- NLog-only extension.
                # Convert %c to %s in format.
                original = match.group(1)
                c2s = re.sub('c', 's', original)
                newFmt = re.sub(original, c2s, newFmt)

                # Convert parameter to a string.
                chrStr = ""
                for chIdx in range(0, int(bits / 8)):
                    ch = chr((myParam >> (bits - (chIdx + 1) * 8)) & 0xFF)
                    if ch != chr(0):
                        chrStr += ch
                myParam = chrStr
            else:
                # Everything else is Python printf compatible; let Python handle it.
                pass

            # Updated the modified parameter list.
            newParams.append(myParam)

        # Un-Hide any "%%" format-specs in the string from the RE searches above.
        newFmt = re.sub('<<%>><<%>>', '%%', newFmt)
        return newFmt, tuple(newParams)

    def replaceFormattingForRegex(self, matchobj):
        """
        Function for replacing a format specifier with its corresponding regex pattern

        Args:
            matchobj: formatting specifier extracted from the original formatting string for an NLOG event

        Returns:
            repStr: regex expression to capture potential values written by the format specifier

        """
        formatPattern = matchobj.group(0)

        digitMatch = re.search('[0-9]+', formatPattern)
        if digitMatch is not None:
            typeMatch = formatPattern[-1]
            repNum = int(digitMatch.group(0))
            if typeMatch in ['d', 'i', 'u']:
                repStr = "(-?\w{" + str(repNum) + "})"
            elif typeMatch in ['f']:
                repStr = "(\w{" + str(repNum) + "})"
            elif typeMatch in ['x', 'X']:
                repStr = "(\w{" + str(repNum) + "," + str(2 * repNum) + "}?)"
            else:
                # case for c and s
                repStr = "(.{" + str(repNum) + "})"

        else:
            typeMatch = formatPattern[-1]
            if typeMatch in ['d', 'i', 'u']:
                repStr = "(-?\w+)"
            elif typeMatch in ['x', 'X', 'f']:
                repStr = "(\w+)"
            elif typeMatch in ['c']:
                repStr = "(.{1})"
            else:
                repStr = "(\w+)"

        return repStr

    def encodeNlogEvents(self):
        """
        Function for reading NLOG events and generating encodings for each of their descriptions based on the natural
        language used in them. Encodings are generated utilizing a pretrained BERT model

        Returns:
            labelsToDescriptions: dictionary mapping labels (first ten characters of description) to a tuple containing
                                  relevant details about the NLOG event parsing and pattern maching to it
            encodingsToParsers: dictionary of description encodings to formatting strings for NLOG descriptions
            encodings: list of encodings for NLOG event descriptions
            labelIndices: list of tuples containing the label associated with each NLOG event and the index that such
                          event occupies inside the list of events inside that label collection

        """
        if self.nlogParserFolder is None:
            return None
        else:
            self.nlogFormatFile = self.nlogParserFolder + '/NLog_formats.py'

        formats = self._getNLogFormats(self.nlogFormatFile)

        if formats is None:
            return None

        nlogEventTuples = formats.values()
        labelsToDescriptions = dict()
        encodingsToParsers = dict()
        encodings = list()
        labelIndices = list()
        pos = 0
        bert_encoder = SentenceTransformer('bert-base-nli-mean-tokens')

        for eventTuple in nlogEventTuples:
            eventDescriptionParser = eventTuple[0]
            paramNum = len(eventTuple[3])
            print("Encoding Event: " + eventDescriptionParser)
            newEventDescription = re.sub('%%', '<<%>><<%>>', eventDescriptionParser)

            matchList = re.findall('(%[-\.\d]*?l*[cdfiusxX])', newEventDescription)
            match = re.search('(%[-\.\d]*?l*[cdfiusxX])', newEventDescription)
            if match is not None:
                if match.start() < 7:
                    label = 'generic'
                else:
                    label = newEventDescription[1:8]
            else:
                label = newEventDescription[1:8]

            print("Label: " + label)
            print("Param formats: " + str(matchList))

            paramTypes = []
            for i in range(paramNum):
                # Add type checking to turn everything into unsigned integer
                premParam = matchList[i]
                typeMatch = premParam[-1]
                if typeMatch in ['d', 'i', 'u']:
                    paramTypes.append('int')
                elif typeMatch in ['x', 'X', 'f']:
                    paramTypes.append('hex')
                elif typeMatch in ['s']:
                    paramTypes.append('str')
                else:
                    paramTypes.append('chr')

            newEventDescription = re.sub('\+', "\+", newEventDescription)
            newEventDescription = re.sub('\*', "\*", newEventDescription)
            newEventDescription = re.sub('\?', "\?", newEventDescription)
            newEventDescription = re.sub('\\\\n', "", newEventDescription)
            newEventDescription = re.sub('\(', "\(", newEventDescription)
            newEventDescription = re.sub('\)', "\)", newEventDescription)
            newEventDescription = re.sub('\{', "\{", newEventDescription)
            newEventDescription = re.sub('\}', "\}", newEventDescription)
            newEventDescription = newEventDescription[1:-1]
            newEventDescription = newEventDescription.strip()

            newEventDescription = re.sub('(%[-\.\d]*?l*[cdfiusxX])', self.replaceFormattingForRegex,
                                         newEventDescription)

            bert_description = re.sub('(%[-\.\d]*?l*[cdfiusxX])', "", newEventDescription)

            descriptionEncoding = bert_encoder.encode(bert_description, show_progress_bar=True)
            encodings.append(descriptionEncoding)

            if label in labelsToDescriptions:
                labelsToDescriptions[label].append(
                    (newEventDescription, paramNum, [0], pos, paramTypes, eventDescriptionParser))
            else:
                labelsToDescriptions[label] = [
                    (newEventDescription, paramNum, [0], pos, paramTypes, eventDescriptionParser)]

            index = len(labelsToDescriptions[label]) - 1
            labelIndices.append((label, index))

            pos += 1

        return labelsToDescriptions, encodingsToParsers, encodings, labelIndices

    def reduceDimensionalityOfEmbeddings(self, numComponents=50):
        """
        Function for reducing the vector dimensionality for the description encodings utilizing PCA

        Args:
            numComponents: number of dimensions for the output encodings

        Returns:

        """
        if self.nlogEncodings is None:
            return
        print("Performing PCA ...")
        pca = PCA(n_components=numComponents)
        newEncodings = pca.fit_transform(self.nlogEncodings)
        self.nlogEncodings = newEncodings
        print("PCA was succesfully performed on the encodings")

        print("Replacing Encoding values...")
        for i in range(len(newEncodings)):
            label, index = self.nlogLabelIndices[i]
            newEventDescription, paramNum, descriptionEncoding, pos, paramTypes, eventDescriptionParser = \
            self.nlogSignatures[label][index]
            print("Replacing Encoding for: " + newEventDescription)
            self.nlogSignatures[label][index] = (
            newEventDescription, paramNum, newEncodings[i], pos, paramTypes, eventDescriptionParser)
            self.nlogStringParsers[str(newEncodings[i])] = (eventDescriptionParser, paramNum)

    def getSignaturesNeighbors(self):
        """
        Function for initializing a nearest neighbor model to match event signatures (encodings) with the list of
        events encodings generated from the list of events contained in NLogFormats.py

        Returns:
            neighbors: NearestNeighbors instance to be used for obtaining the closest neighbor to a given encoding

        """
        if self.nlogEncodings is None:
            return None

        neighbors = NearestNeighbors(n_neighbors=1)
        neighbors = neighbors.fit(self.nlogEncodings)
        return neighbors

    def obtainEventSignature(self, nlogDescription=None):
        """
        Function for obtaining an event encoding based on the given description

        Args:
            nlogDescription: string for the NLOG event

        Returns:
            nlogEncoding: dimensionality-reduced vector representing the NLOG description
            params: list of parameter values extracted from the specified nlogDescription
            finalPos: index of the NLOG event as specified in NLogFormats.py to be used as input for the parameter
                      predictor

        """
        if nlogDescription is None or self.nlogSignatures is None:
            return None

        label = nlogDescription[:7]
        if self.debug:
            print("Obtaining signature for: " + nlogDescription)
            print("Label: " + label)
        if label not in self.nlogSignatures:
            label = 'generic'

        potentialDescriptions = self.nlogSignatures[label]
        params = list()
        finalPos = 0
        nlogEncoding = [0] * self.numComponents
        for newEventDescription, paramNum, descriptionEncoding, pos, paramTypes, eventDescriptorParser in potentialDescriptions:
            eventMatch = re.match(newEventDescription, nlogDescription)
            if eventMatch is None:
                if newEventDescription == nlogDescription:
                    nlogEncoding = descriptionEncoding
                    finalPos = pos
                    break
                else:
                    continue
            else:
                if self.debug:
                    print("Event Description has been matched with: ")
                    print(newEventDescription)
                for i in range(paramNum):
                    # Add type checking to turn everything into unsigned integer
                    premParam = eventMatch.group(i + 1)
                    paramType = paramTypes[i]
                    if paramType == 'int':
                        digitMatch = re.search('[1-9]+', premParam)
                        if digitMatch is None:
                            premParam = 0
                        else:
                            premParam = int(digitMatch.group(0))
                    elif paramType == 'chr':
                        charLen = len(premParam)
                        power = 0
                        tempParam = 0
                        for character in premParam:
                            tempParam += ord(character) * (2 ** power)
                            power += 32 / charLen
                        premParam = tempParam
                    elif paramType == 'hex':
                        premParam = ast.literal_eval('0x' + premParam)
                    else:
                        premParam = int(premParam)

                    params.append(premParam)
                nlogEncoding = descriptionEncoding
                finalPos = pos
                break

        return nlogEncoding, params, finalPos

    def decodeEventEncoding(self, nlogSignature):
        """
        Function for decoding an event encoding to obtain the formatting string and the number of parameters to be used

        Args:
            nlogSignature: dimensionality-reduced vector produced by the predictor model

        Returns:
            nlogEncoding[0]: encoding for closest neighbor to nlogSignature
            parseString: formatting string associated with closest neighbor to nlogSignature
            paramNum: number of parameters to be included in the formatting string
        """
        # perform closest signature from formats to each element in the list
        if self.nlogNeighbors is None or self.nlogEncodings is None:
            return None

        nlogEncodingIndexList = self.nlogNeighbors.kneighbors([nlogSignature], return_distance=False)
        nlogEncodingIndex = nlogEncodingIndexList[0]
        nlogEncoding = self.nlogEncodings[nlogEncodingIndex]
        parseString, paramNum = self.nlogStringParsers[str(nlogEncoding[0])]
        return nlogEncoding[0], parseString, paramNum


class NlogDataProcessor(object):
    def __init__(self, nlogFolder="data/output/nlog", nlogParserFolder="software/parse/nlogParser", numComponents=50,
                 maxNumParams=8, debug=False):
        """
        Function for instantiating a NlogDataProcessor instance

        Args:
            nlogFolder: Path for the nlog Folder in which the nlog event files are contained
            nlogParserFolder: Path for the folder in which the NLogFormats.py script is contained
            numComponents: Integer for the number of dimensions to be used in the NLOG description embeddings
            maxNumParams: Integer for the maximum number of parameters that can be contained in an NLOG description
                          for the specified formats file
            debug: Verbose printing for debug use

        Returns:

        """
        self.nlogFolder = tryFolder(path=nlogFolder)
        self.nlogFiles = self.extractFilesFromFolder()
        self.nlogParserFolder = tryFolder(path=nlogParserFolder)
        self.tokenizerNumComponents = numComponents
        self.tokenizer = NlogTokenizer(nlogParserFolder=self.nlogParserFolder, numComponents=50, debug=debug)
        self.maxNumParams = maxNumParams

    def __repr__(self):
        """
        function that overwrites the representation for the window instance

        Returns:
            String with the representative fields for the window

        """
        return '\n'.join([
            f'NLOG Folder: {self.nlogFolder}',
            f'NLOG Files : {str(self.nlogFiles)}'])

    @staticmethod
    def paddParams(params, maxNumParams=8):
        """
        Function for padding a parameter vector

        Args:
            params: list of parameter values
            maxNumParams: integer for the maximum number of parameters to be used for the parameter vector

        Returns:
            params: vector of parameter values with maxNumParams dimensionality

        """
        # Add padding for output
        if len(params) < maxNumParams:
            padding = [0] * (maxNumParams - len(params))
            params = params + padding

        return params

    @staticmethod
    def paddParamList(paramList, maxNumParams=8, maxListLength=4000):
        """
        Function for padding (or truncating) the parameter vector list so that it can be fed into a fixed input neural
        network

        Args:
            paramList: list of variable length containing the parameter vectors extracted so far
            maxNumParams: integer for the maximum number of parameters to be used for the parameter vector
            maxListLength: integer for the maximum length of the list to be considered as input for the neural network

        Returns:
            paramsList: padded (or truncated) list of parameter vectors

        """
        paddingList = list()
        if len(paramList) < maxListLength:
            difference = maxListLength - len(paramList)
            for i in range(difference):
                paramVector = [0] * maxNumParams
                paddingList.append(np.array(paramVector))
            paramList = paramList + paddingList
        else:
            paramList = paramList[-maxListLength:]

        return paramList

    @staticmethod
    def paddTimeList(timeList, maxListLength=4000):
        """
        Function for padding (or truncating) the time vector list so that it can be fed into a fixed input
        neural network

        Args:
            timeList: list of variable length containing the time vectors extracted so far
            maxListLength: integer for the maximum length of the list to be considered as input for the neural network

        Returns:
            timeList: padded (or truncated) list of time vectors

        """
        paddingList = list()
        if len(timeList) < maxListLength:
            difference = maxListLength - len(timeList)
            for i in range(difference):
                timeVector = [0] * 3
                paddingList.append(np.array(timeVector))
            timeList = timeList + paddingList
        else:
            timeList = timeList[:maxListLength]

        return timeList

    @staticmethod
    def paddEncodingList(encodingList, maxDimensionForEncoding=50, maxListLength=4000):
        """
        Function for padding (or truncating) the events encoding vector list so that it can be fed into a fixed input
        neural network

        Args:
            encodingList: list of variable length containing the events encoding vectors extracted so far
            maxDimensionForEncoding: integer for the maximum number of dimensions used for the events encoding vectors
            maxListLength: integer for the maximum length of the list to be considered as input for the neural network

        Returns:
            encodingList: padded (or truncated) list of events encoding vectors

        """
        paddingList = list()
        if len(encodingList) < maxListLength:
            difference = maxListLength - len(encodingList)
            for i in range(difference):
                encodingVector = [0] * maxDimensionForEncoding
                paddingList.append(np.array(encodingVector))
            encodingList = encodingList + paddingList
        else:
            encodingList = encodingList[:maxListLength]

        return encodingList

    @staticmethod
    def readFileContentIntoDict(tempFile):
        """
        Function for reading NLOG file content into a dictionary mapping line content to line index in the file

        Args:
            tempFile: string for the path of the NLOG file containing the NLOG events to be read

        Returns:
            tempFileContent: dictionary mapping line content to line index in the file for the specified file

        """
        openFile = open(tempFile, 'r')
        tempFileContent = dict()
        index = 0
        for line in openFile:
            if index > 4:
                tempFileContent[line] = index
            index += 1
        openFile.close()

        return tempFileContent

    def extractFilesContent(self, firstFile, secondFile, thirdFile, firstFileContent=None, secondFileContent=None,
                            thirdFileContent=None):
        """
        Function for extracting the content of three adjacent files if no content has been read or shifting the content
        for extracting the sliding window data

        Args:
            firstFile: string for the path of the first NLOG file containing the NLOG events to be read
            secondFile: string for the path of the second NLOG file containing the NLOG events to be read
            thirdFile: string for the path of the third NLOG file containing the NLOG events to be read
            firstFileContent: None or dictionary mapping line content to line index in the first file
            secondFileContent: None or dictionary mapping line content to line index in the second file
            thirdFileContent: None or dictionary mapping line content to line index in the third file

        Returns:
            firstFileContent: dictionary mapping line content to line index in the first file or shifted content
            secondFileContent: dictionary mapping line content to line index in the second file or shifted content
            thirdFileContent: dictionary mapping line content to line index in the third file or shifted content

        """
        if firstFileContent is None:
            firstFileContent = self.readFileContentIntoDict(firstFile)
        else:
            firstFileContent = secondFileContent

        if secondFileContent is None:
            secondFileContent = self.readFileContentIntoDict(secondFile)
        else:
            secondFileContent = thirdFileContent

        thirdFileContent = self.readFileContentIntoDict(thirdFile)

        return firstFileContent, secondFileContent, thirdFileContent

    def extractFilesFromFolder(self):
        """
        function for generating a list of nlog files to be used as inputs for data generation

        Returns:
            fileList: list of the names of the nlog files

        """

        if self.nlogFolder is None:
            return None

        if os.path.exists(self.nlogFolder):
            fileList = [os.path.join(self.nlogFolder, fileName) for fileName in os.listdir(self.nlogFolder) if
                        os.path.isfile(os.path.join(self.nlogFolder, fileName)) and
                        NlogUtils().getDateFromFileName(fileName) is not None]
        else:
            fileList = None

        return fileList

    def extractEventSignatures(self, nlogEvents, maxListLength=4000):
        """
        Function for extracting NLOG events encodings and parameter values from a list of NLOG event descriptions

        Args:
            nlogEvents: list of strings for the NLOG event descriptions
            maxListLength:  integer for the maximum length of the list to be considered as input for the neural network

        Returns:
            nlogEncodings: padded (or truncated) list of events encoding vectors
            paramsList: padded (or truncated) list of parameter vectors
            timeList: padded (or truncated) list of time vectors

        """
        # todo @dgarces include a new system for predicting time-stamps
        if nlogEvents is None or self.nlogParserFolder is None:
            return None

        timeList = list()
        nlogEncodings = list()
        paramList = list()

        for event in nlogEvents:
            lineComponents = event.split()
            if lineComponents[0].isdigit():
                initialPos = 1
            else:
                initialPos = 0
            nlogComponents = NlogUtils().extractNlogComponents(lineComponents, initialPos)
            description = nlogComponents[-1]
            timeStamp = NlogUtils().extractNlogTime(event)
            nlogEncoding, params, finalPos = self.tokenizer.obtainEventSignature(nlogDescription=description)
            params = self.paddParams(params, maxNumParams=self.maxNumParams)
            params = params + [finalPos]
            timeList.append(np.array(timeStamp))
            nlogEncodings.append(np.array(nlogEncoding))
            paramList.append(np.array(params))

        timeList = self.paddTimeList(timeList, maxListLength=maxListLength)
        nlogEncodings = self.paddEncodingList(nlogEncodings, maxDimensionForEncoding=self.tokenizerNumComponents,
                                              maxListLength=maxListLength)
        # Add 1 to maxNumParams to account for the concatenation of the nlogDescription index to the vector
        paramList = self.paddParamList(paramList, maxNumParams=self.maxNumParams + 1, maxListLength=maxListLength)
        timeList = np.stack(timeList)
        print(timeList.shape)
        nlogEncodings = np.stack(nlogEncodings)
        print(nlogEncodings.shape)
        paramList = np.stack(paramList)
        print(paramList.shape)

        return nlogEncodings, paramList, timeList

    def generateDataSets(self, inputSize=4000, maxOutputSize=1000):
        """
        Function for generating the data sets to be fed into the neural network. Please bear in mind that the returned
        lists might still need to be converted to np.arrays and reshaped before being fed into any neural network model

        Args:
            inputSize: integer for the total number of NLOG events to be considered as inputs for the predictive models
            maxOutputSize: integer for the total number of NLOG events to be considered in the prediction

        Returns:
            nlogDeltaTimes: list of time deltas (in seconds) between different NLOG files
            nlogDeltaEventNums: list of number of events changed between different NLOG files
            nlogEventsInputs: list of NLOG event encodings to be used as input to the predictive model
            nlogEventsOutputs: list of NLOG event encodings to be used as reference output for the predictive model
            nlogParamsInputs: list of NLOG parameter vectors to be used as input to the predictive model
            nlogParamsOutputs: list of NLOG parameter vectors to be used as reference output to the predictive model
            nlogTimesInputs: list of NLOG time stamp vectors to be used as input to the predictive model
            nlogTimesOutputs: list of NLOG time stamp vectors to be used as reference output to the predictive model


        """
        # TODO @dgarces add permutation option for matching pairs of files
        if self.nlogFiles is None:
            return None

        nlogDeltaTimes = list()
        nlogDeltaEventNums = list()
        nlogTimesInputs = list()
        nlogTimesOutputs = list()
        nlogEventsInputs = list()
        nlogEventsOutputs = list()
        nlogParamsInputs = list()
        nlogParamsOutputs = list()
        firstFileContent = None
        secondFileContent = None
        thirdFileContent = None
        print("Generating DataSets...")
        for i in range(len(self.nlogFiles) - 2):
            firstFile = self.nlogFiles[i]
            secondFile = self.nlogFiles[i + 1]
            thirdFile = self.nlogFiles[i + 2]

            firstTimeDelta = NlogUtils.getDateFromFileName(secondFile) - NlogUtils.getDateFromFileName(firstFile)
            firstTimeDelta = firstTimeDelta.total_seconds()
            secondTimeDelta = NlogUtils.getDateFromFileName(thirdFile) - NlogUtils.getDateFromFileName(firstFile)
            secondTimeDelta = secondTimeDelta.total_seconds()

            firstFileContent, secondFileContent, thirdFileContent = self.extractFilesContent(firstFile, secondFile,
                                                                                             thirdFile,
                                                                                             firstFileContent,
                                                                                             secondFileContent,
                                                                                             thirdFileContent)

            firstFileSet = set(firstFileContent.keys())
            secondFileSet = set(secondFileContent.keys())
            thirdFileSet = set(thirdFileContent.keys())

            firstIntersection = firstFileSet.intersection(secondFileSet)
            secondIntersection = firstFileSet.intersection(thirdFileSet)

            firstOutputSet = secondFileSet.difference(firstIntersection)
            secondOutputSet = thirdFileSet.difference(secondIntersection)

            firstEventDelta = len(list(firstOutputSet))
            secondEventDelta = len(list(secondOutputSet))
            nlogDeltaTimes.append(firstTimeDelta)
            nlogDeltaTimes.append(secondTimeDelta)
            nlogDeltaEventNums.append(firstEventDelta)
            nlogDeltaEventNums.append(secondEventDelta)

            firstInput = sorted(firstFileContent.keys(), key=lambda line: firstFileContent[line])
            secondInput = sorted(secondFileContent.keys(), key=lambda line: secondFileContent[line])
            firstInputEvents, firstInputParams, firstInputTimes = self.extractEventSignatures(firstInput,
                                                                                              maxListLength=inputSize)
            secondInputEvents, secondInputParams, secondInputTimes = self.extractEventSignatures(secondInput,
                                                                                                 maxListLength=inputSize)
            nlogTimesInputs.append(firstInputTimes)
            nlogTimesInputs.append(secondInputTimes)
            nlogEventsInputs.append(firstInputEvents)
            nlogEventsInputs.append(secondInputEvents)
            nlogParamsInputs.append(firstInputParams)
            nlogParamsInputs.append(secondInputParams)

            firstOutput = sorted(list(firstOutputSet), key=lambda line: secondFileContent[line])
            secondOutput = sorted(list(secondOutputSet), key=lambda line: thirdFileContent[line])
            firstOutputEvents, firstOutputParams, firstOutputTimes = self.extractEventSignatures(firstOutput,
                                                                                                 maxListLength=maxOutputSize)
            secondOutputEvents, secondOutputParams, secondOutputTimes = self.extractEventSignatures(secondOutput,
                                                                                                    maxListLength=maxOutputSize)
            nlogTimesOutputs.append(firstOutputTimes)
            nlogTimesOutputs.append(secondOutputTimes)
            nlogEventsOutputs.append(firstOutputEvents)
            nlogEventsOutputs.append(secondOutputEvents)
            nlogParamsOutputs.append(firstOutputParams)
            nlogParamsOutputs.append(secondOutputParams)

        return (nlogDeltaTimes, nlogDeltaEventNums, nlogEventsInputs, nlogEventsOutputs, nlogParamsInputs,
                nlogParamsOutputs, nlogTimesInputs, nlogTimesOutputs)

    def extractInputDataForSingleFile(self, fileOfInterest, timeDelta, inputSize=4000):
        """
        Function for extracting input data from a specified NLOG file

        Args:
            fileOfInterest: string for the path of the NLOG file containing the NLOG events to be read
            timeDelta: time delta to be used for prediction
            inputSize: integer for the total number of NLOG events to be considered as inputs for the predictive models

        Returns:
            nlogDeltaTimes: list of time deltas (in seconds) between specified NLOG file and desired prediction range
            nlogEventsInputs: list of NLOG event encodings to be used as input to the predictive model
            nlogParamsInputs: list of NLOG parameter vectors to be used as input to the predictive model
            nlogTimesInputs: list of NLOG time vectors to be used as input to the predictive model

        """

        nlogDeltaTimes = list()
        nlogTimesInputs = list()
        nlogEventsInputs = list()
        nlogParamsInputs = list()

        fileContent = self.readFileContentIntoDict(fileOfInterest)

        nlogDeltaTimes.append(timeDelta)

        firstInput = sorted(fileContent.keys(), key=lambda line: fileContent[line])
        inputEvents, inputParams, inputTimes = self.extractEventSignatures(firstInput, maxListLength=inputSize)
        nlogTimesInputs.append(inputTimes)
        nlogEventsInputs.append(inputEvents)
        nlogParamsInputs.append(inputParams)

        return nlogDeltaTimes, nlogEventsInputs, nlogParamsInputs, nlogTimesInputs

    def generateDemoData(self, inputSize=4000):
        """
        Function for generating demo data to demonstrate the predictive capabilities of the system

        Args:
            inputSize: integer for the total number of NLOG events to be considered as inputs for the predictive models

        Returns:
            nlogDeltaTimes: list of time deltas (in seconds) between the last two NLOG files
            nlogEventsInputs: list of NLOG event encodings to be used as input to the predictive model
            nlogParamsInputs: list of NLOG parameter vectors to be used as input to the predictive model
            nlogTimesInputs: list of NLOG time vectors to be used as input to the predictive model
            firstOutput: list of NLOG descriptions unique to the last file (expected output of predictive model)

        """

        nlogDeltaTimes = list()
        nlogTimesInputs = list()
        nlogEventsInputs = list()
        nlogParamsInputs = list()

        firstFile = self.nlogFiles[len(self.nlogFiles) - 2]
        secondFile = self.nlogFiles[len(self.nlogFiles) - 1]

        firstTimeDelta = NlogUtils.getDateFromFileName(secondFile) - NlogUtils.getDateFromFileName(firstFile)
        firstTimeDelta = firstTimeDelta.total_seconds()

        firstFileContent = self.readFileContentIntoDict(firstFile)
        secondFileContent = self.readFileContentIntoDict(secondFile)

        firstFileSet = set(firstFileContent.keys())
        secondFileSet = set(secondFileContent.keys())

        firstIntersection = firstFileSet.intersection(secondFileSet)

        firstOutputSet = secondFileSet.difference(firstIntersection)

        nlogDeltaTimes.append(firstTimeDelta)

        firstInput = sorted(firstFileContent.keys(), key=lambda line: firstFileContent[line])
        firstInputEvents, firstInputParams, firstInputTimes = self.extractEventSignatures(firstInput,
                                                                                          maxListLength=inputSize)
        nlogTimesInputs.append(firstInputTimes)
        nlogEventsInputs.append(firstInputEvents)
        nlogParamsInputs.append(firstInputParams)

        firstOutput = sorted(list(firstOutputSet), key=lambda line: secondFileContent[line])

        return nlogDeltaTimes, nlogEventsInputs, nlogParamsInputs, nlogTimesInputs, firstOutput


class NlogWidthPredictor(object):

    def __init__(self, timeDeltaSeries, eventDeltaSeries):
        """
        Function for instantiating a NlogWidthPredictor instance

        Args:
            timeDeltaSeries: list of floats for the time deltas (in seconds) between different NLOG files
            eventDeltaSeries: list of integers for the number of events changed for a given time delta

        """
        timeDeltaTrain, timeDeltaTest, eventDeltaTrain, eventDeltaTest = NlogUtils().splitDataSet(timeDeltaSeries,
                                                                                                  eventDeltaSeries,
                                                                                                  randomState=42)
        self.timeDeltaTrain = timeDeltaTrain.reshape((-1, 1))
        self.timeDeltaTest = timeDeltaTest.reshape((-1, 1))
        self.eventDeltaTrain = eventDeltaTrain
        self.eventDeltaTest = eventDeltaTest

    def defaultLinearModel(self):
        """
        function for creating a generic linear model

        Returns:
            clf: linear regression model to be used for prediction
            score: R^2 score for the correlation between time deltas and number of events changed


        """
        clf = LinearRegression()
        clf.fit(self.timeDeltaTrain, self.eventDeltaTrain)
        score = clf.score(self.timeDeltaTest, self.eventDeltaTest)

        return clf, score

    def ridgeLinearModel(self):
        """
        function for creating a generic Ridge linear model with cross validation

        Returns:
            clf: ridge linear regression model to be used for prediction
            score: R^2 score for the correlation between time deltas and number of events changed

        """
        clf = RidgeCV(alphas=[1e-3, 1e-2, 1e-1, 1])
        clf.fit(self.timeDeltaTrain, self.eventDeltaTrain)
        score = clf.score(self.timeDeltaTest, self.eventDeltaTest)

        return clf, score

    def lassoLinearModel(self):
        """
        function for creating a generic Lasso linear model with cross validation

        Returns:
            reg: lasso linear regression model to be used for prediction
            score: R^2 score for the correlation between time deltas and number of events changed


        """
        reg = LassoCV(cv=5, random_state=0)
        reg.fit(self.timeDeltaTrain, self.eventDeltaTrain)
        score = reg.score(self.timeDeltaTest, self.eventDeltaTest)

        return reg, score

    def elasticNetLinearModel(self):
        """
        function for creating a generic ElasticNet linear model with cross validation

        Returns:
            reg: elastic net linear regression model to be used for prediction
            score: R^2 score for the correlation between time deltas and number of events changed
        """
        reg = ElasticNetCV(cv=5, random_state=0)
        reg.fit(self.timeDeltaTrain, self.eventDeltaTrain)
        score = reg.score(self.timeDeltaTest, self.eventDeltaTest)

        return reg, score

    def genericLinearPredictor(self, modelType='elastic'):
        """
        function for selecting and training a linear regression model for number of event changes. It also predicts
        output for the testing set

        Args:
            modelType: name of the model type to be used in the linear regression model for determining the number
                       of NLOG events to be predicted. Must be selected from the following:
                       ['elastic', 'lasso', 'ridge', 'default']

        Returns:
            model: linear regression model to be used for prediction
            score: R^2 score for the correlation between time deltas and number of events changed
            predictions: list of number of predicted number of event changes for each time delta in the testing set

        """
        if modelType == 'elastic':
            model, score = self.elasticNetLinearModel()
        elif modelType == 'lasso':
            model, score = self.lassoLinearModel()
        elif modelType == 'ridge':
            model, score = self.ridgeLinearModel()
        else:
            model, score = self.defaultLinearModel()

        predictions = model.predict(self.timeDeltaTest)

        return model, score, predictions


class NlogTimePredictor(object):
    class RNNUtility:
        """
        utility class containing functions for processing a configuration file and loading it into a dictionary
        """

        @staticmethod
        def compileAndFit(model, inputData, outputData, patience=20, maxEpochs=2000, optimizer='Adam'):
            """
            function for configuring a model, compiling it, and fitting it to the specified training and validation
            data

            Args:
                model: Tensorflow model to be compiled and fitted
                inputData: np.array with the time stamps to be used for the input of the neural network
                outputData: np.array with the time stamps to be used as reference output for the neural network
                patience: Number of epochs with no improvement after which training will be stopped.
                maxEpochs: Number of trials to be run
                optimizer: optimizer to be used for the model, must be selected from the following
                          ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']

            Returns:
                history: list of loss values and metrics for each epoch
                model: Tensorflow model with the new trained weights

            """
            print("Number of inputs to the model: " + str(len(inputData)))
            print("Number of outputs to the model: " + str(len(outputData)))
            if len(inputData) < 32:
                batchSize = 1
            else:
                batchSize = 32

            try:
                earlyStopping = tensorflow.keras.callbacks.EarlyStopping(monitor='loss', patience=patience, mode='min')
                modelCheckpoint = tensorflow.keras.callbacks.ModelCheckpoint('best_time_model.h5',
                                                                             monitor='mean_absolute_error',
                                                                             mode='min', save_best_only=True)

                model.compile(loss=tensorflow.losses.MeanSquaredError(), optimizer=optimizer,
                              metrics=[tensorflow.metrics.MeanAbsoluteError()])
                history = model.fit(x=inputData, y=outputData, epochs=maxEpochs, validation_split=0.1, verbose=1,
                                    batch_size=batchSize, callbacks=[earlyStopping, modelCheckpoint])
                del model
                model = tensorflow.keras.models.load_model('best_time_model.h5')

            except BaseException as ErrorContext:
                pprint.pprint(f"{ErrorContext}{os.linesep}{pprint.pformat(whoami())}")
                history = None
                model = None

            return history, model

    def __init__(self, inputSeries, outputSeries):
        """
        Function for instantiating a NlogTimePredictor instance

        Args:
            inputSeries: list of 2D np.arrays containing the vectors for the time stamps to be used as
                         inputs to the model
            outputSeries: list of 2D np.arrays containing the vectors for the time stamps to be used as
                          reference outputs for training
        """
        inputTimeTrain, inputTimeTest, outputTimeTrain, outputTimeTest = NlogUtils().splitDataSet(inputSeries,
                                                                                                  outputSeries,
                                                                                                  randomState=42)
        self.inputTimeTrain = inputTimeTrain
        self.inputTimeTest = inputTimeTest
        self.outputTimeTrain = outputTimeTrain
        self.outputTimeTest = outputTimeTest
        self.inputWidth = self.inputTimeTrain[0].shape[0]
        self.outputWidth = self.outputTimeTrain[0].shape[0]
        self.timeDimensions = self.inputTimeTrain[0].shape[1]

    def sequentialNet(self, hiddenUnits, lstm_activation='tanh', lstm_initializer='glorot_uniform', dropout=False):
        """
        function for creating a generic RNN model using the sequential keras architecture

        Args:
            hiddenUnits: Integer for the number of neurons contained in each hidden layer
            lstm_activation: activation function for LSTM layers. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
            lstm_initializer: weight initializer for the lstm layers. Must be selected from the following:
                           ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                           'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
            dropout: Boolean flag to indicate if dropout should be applied in between layers in the model

        Returns:
            lstmModel: Tensorflow RNN model containing the desired topology

        """
        if dropout:
            lstmModel = tensorflow.keras.Sequential(
                [tensorflow.keras.layers.Dropout(0.2, input_shape=(self.inputWidth, self.timeDimensions)),
                 tensorflow.keras.layers.LSTM(hiddenUnits,
                                              return_sequences=True,
                                              kernel_initializer=lstm_initializer,
                                              activation=lstm_activation),
                 tensorflow.keras.layers.Dropout(0.2),
                 tensorflow.keras.layers.LSTM(hiddenUnits,
                                              return_sequences=False,
                                              kernel_initializer=lstm_initializer,
                                              activation=lstm_activation),
                 tensorflow.keras.layers.Dropout(0.2),
                 tensorflow.keras.layers.Dense(self.timeDimensions * self.outputWidth),
                 tensorflow.keras.layers.Reshape([self.outputWidth, self.timeDimensions])])
        else:
            lstmModel = tensorflow.keras.Sequential([tensorflow.keras.layers.LSTM(units=hiddenUnits,
                                                                                  return_sequences=True,
                                                                                  kernel_initializer=lstm_initializer,
                                                                                  activation=lstm_activation,
                                                                                  input_shape=(self.inputWidth,
                                                                                               self.timeDimensions)),
                                                     tensorflow.keras.layers.LSTM(units=hiddenUnits,
                                                                                  return_sequences=False,
                                                                                  kernel_initializer=lstm_initializer,
                                                                                  activation=lstm_activation),
                                                     tensorflow.keras.layers.Dense(
                                                         (self.timeDimensions * self.outputWidth)),
                                                     tensorflow.keras.layers.Reshape(
                                                         [self.outputWidth, self.timeDimensions])])
        return lstmModel

    def genericPredictor(self, hiddenUnits, maxEpochs=2000, optimizer='Adam', lstm_activation='tanh',
                         lstm_initializer='glorot_uniform', dropout=False):
        """
        wrapper function for generating, training, and evaluating an Nlog Time predictive model

        Args:
            hiddenUnits: Integer for the number of neurons contained in each hidden layer
            maxEpochs: Integer for the maximum number of epochs to be considered when training the model
            optimizer: optimizer to be used for the model, must be selected from the following
                      ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']
            lstm_activation: activation function for LSTM layers. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
            lstm_initializer: weight initializer for the lstm layers. Must be selected from the following:
                           ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                           'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
            dropout: Boolean flag to indicate if dropout should be applied in between layers in the model

        Returns:
            model: Tensorflow NLOG time predictive model
            predictionEmbeddings: list of 2D np.arrays containing the vectors for the time stamps predicted by
                                  the model

        """

        model = self.sequentialNet(hiddenUnits, lstm_activation=lstm_activation, lstm_initializer=lstm_initializer,
                                   dropout=dropout)
        history = self.RNNUtility.compileAndFit(model, self.inputTimeTrain, self.outputTimeTrain,
                                                maxEpochs=maxEpochs, optimizer=optimizer)

        metrics = model.evaluate(x=self.inputTimeTest, y=self.outputTimeTest)
        predictionTimes = model.predict(self.inputTimeTest)
        print(str(metrics))

        return model, predictionTimes


class NlogEventsPredictor(object):
    class RNNUtility:
        """
        utility class containing functions for processing a configuration file and loading it into a dictionary
        """

        @staticmethod
        def compileAndFit(model, inputData, outputData, patience=20, maxEpochs=2000, optimizer='Adam'):
            """
            function for configuring a model, compiling it, and fitting it to the specified training and validation
            data

            Args:
                model: Tensorflow model to be compiled and fitted
                inputData: list of 2D np.arrays containing the encodings for the event descriptions to be used as inputs
                           to the model
                outputData: list of 2D np.arrays containing the encodings for the event descriptions to be used as
                            reference outputs for training
                patience: Number of epochs with no improvement after which training will be stopped.
                maxEpochs: Number of trials to be run
                optimizer: optimizer to be used for the model, must be selected from the following
                          ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']

            Returns:
                history: list of loss values and metrics for each epoch
                model: Tensorflow model with the new trained weights

            """
            print("Number of inputs to the model: " + str(len(inputData)))
            print("Number of outputs to the model: " + str(len(outputData)))
            if len(inputData) < 32:
                batchSize = 1
            else:
                batchSize = 32

            try:
                earlyStopping = tensorflow.keras.callbacks.EarlyStopping(monitor='loss', patience=patience, mode='min')
                modelCheckpoint = tensorflow.keras.callbacks.ModelCheckpoint('best_event_model.h5',
                                                                             monitor='mean_absolute_error',
                                                                             mode='min', save_best_only=True)

                model.compile(loss=tensorflow.losses.MeanSquaredError(), optimizer=optimizer,
                              metrics=[tensorflow.metrics.MeanAbsoluteError()])
                history = model.fit(x=inputData, y=outputData, epochs=maxEpochs, validation_split=0.1, verbose=1,
                                    batch_size=batchSize, callbacks=[earlyStopping, modelCheckpoint])
                del model
                model = tensorflow.keras.models.load_model('best_event_model.h5')

            except BaseException as ErrorContext:
                pprint.pprint(f"{ErrorContext}{os.linesep}{pprint.pformat(whoami())}")
                history = None
                model = None

            return history, model

    def __init__(self, inputEventSeries, outputEventSeries):
        """
        Function for instantiating a NlogEventPredictor instance

        Args:
            inputEventSeries: list of 2D np.arrays containing the encodings for the event descriptions to be used as
                              inputs to the model
            outputEventSeries: list of 2D np.arrays containing the encodings for the event descriptions to be used as
                               reference outputs for training
        """
        inputEventsTrain, inputEventsTest, outputEventsTrain, outputEventsTest = NlogUtils().splitDataSet(
            inputEventSeries,
            outputEventSeries,
            randomState=42)
        self.inputEventsTrain = inputEventsTrain
        self.inputEventsTest = inputEventsTest
        self.outputEventsTrain = outputEventsTrain
        self.outputEventsTest = outputEventsTest
        self.eventEncodingSize = self.inputEventsTrain[0].shape[1]
        self.inputWidth = self.inputEventsTrain[0].shape[0]
        self.outputWidth = self.outputEventsTrain[0].shape[0]

    def sequentialNet(self, hiddenUnits, lstm_activation='tanh', lstm_initializer='glorot_uniform', dropout=False):
        """
        function for creating a generic RNN model using the sequential keras architecture

        Args:
            hiddenUnits: Integer for the number of neurons contained in each hidden layer
            lstm_activation: activation function for LSTM layers. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
            lstm_initializer: weight initializer for the lstm layers. Must be selected from the following:
                           ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                           'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
            dropout: Boolean flag to indicate if dropout should be applied in between layers in the model

        Returns:
            lstmModel: Tensorflow RNN model containing the desired topology

        """
        if dropout:
            lstmModel = tensorflow.keras.Sequential([
                tensorflow.keras.layers.Dropout(0.2, input_shape=(self.inputWidth, self.eventEncodingSize)),
                tensorflow.keras.layers.LSTM(hiddenUnits, return_sequences=True, kernel_initializer=lstm_initializer,
                                             activation=lstm_activation),
                tensorflow.keras.layers.Dropout(0.2),
                tensorflow.keras.layers.LSTM(hiddenUnits, return_sequences=False, kernel_initializer=lstm_initializer,
                                             activation=lstm_activation),
                tensorflow.keras.layers.Dropout(0.2),
                tensorflow.keras.layers.Dense(self.eventEncodingSize * self.outputWidth),
                tensorflow.keras.layers.Reshape([self.outputWidth, self.eventEncodingSize])
            ])
        else:
            lstmModel = tensorflow.keras.Sequential([
                tensorflow.keras.layers.LSTM(hiddenUnits, return_sequences=True, kernel_initializer=lstm_initializer,
                                             activation=lstm_activation, input_shape=(self.inputWidth,
                                                                                      self.eventEncodingSize)),
                tensorflow.keras.layers.LSTM(hiddenUnits, return_sequences=False, kernel_initializer=lstm_initializer,
                                             activation=lstm_activation),
                tensorflow.keras.layers.Dense(self.eventEncodingSize * self.outputWidth),
                tensorflow.keras.layers.Reshape([self.outputWidth, self.eventEncodingSize])
            ])
        return lstmModel

    def genericPredictor(self, hiddenUnits, maxEpochs=2000, optimizer='Adam', lstm_activation='tanh',
                         lstm_initializer='glorot_uniform', dropout=False):
        """
        wrapper function for generating, training, and evaluating an Nlog event predictive model

        Args:
            hiddenUnits: Integer for the number of neurons contained in each hidden layer
            maxEpochs: Integer for the maximum number of epochs to be considered when training the model
            optimizer: optimizer to be used for the model, must be selected from the following
                      ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']
            lstm_activation: activation function for LSTM layers. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
            lstm_initializer: weight initializer for the lstm layers. Must be selected from the following:
                           ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                           'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
            dropout: Boolean flag to indicate if dropout should be applied in between layers in the model

        Returns:
            model: Tensorflow NLOG event predictive model
            predictionEmbeddings: list of 2D np.arrays containing the encodings for the event descriptions predicted by
                                  the model

        """

        model = self.sequentialNet(hiddenUnits, lstm_activation=lstm_activation, lstm_initializer=lstm_initializer,
                                   dropout=dropout)
        history = self.RNNUtility.compileAndFit(model, self.inputEventsTrain, self.outputEventsTrain,
                                                maxEpochs=maxEpochs, optimizer=optimizer)

        metrics = model.evaluate(x=self.inputEventsTest, y=self.outputEventsTest)
        predictionEmbeddings = model.predict(self.inputEventsTest)
        print(str(metrics))

        return model, predictionEmbeddings


class NlogParameterPredictor(object):
    class RNNUtility:
        """
        utility class containing functions for processing a configuration file and loading it into a dictionary
        """

        @staticmethod
        def compileAndFit(model, inputData, outputData, patience=20, maxEpochs=2000, optimizer='Adam'):
            """
            function for configuring a model, compiling it, and fitting it to the specified training and validation
            data

            Args:
                model: Tensorflow model to be compiled and fitted
                inputData: list of 2D np.arrays containing the parameter vectors from the event descriptions to be used
                           as inputs to the model
                outputData: list of 2D np.arrays containing the parameter vectors for the event descriptions to be used
                            as reference outputs for training
                patience: Number of epochs with no improvement after which training will be stopped.
                maxEpochs: Number of trials to be run
                optimizer: optimizer to be used for the model, must be selected from the following
                          ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']

            Returns:
                history: list of loss values and metrics for each epoch
                model: Tensorflow model with the new trained weights

            """
            print("Number of inputs to the model: " + str(len(inputData)))
            print("Number of outputs to the model: " + str(len(outputData)))
            if len(inputData) < 32:
                batchSize = 1
            else:
                batchSize = 32

            try:
                earlyStopping = tensorflow.keras.callbacks.EarlyStopping(monitor='loss', patience=patience, mode='min')
                modelCheckpoint = tensorflow.keras.callbacks.ModelCheckpoint('best_param_model.h5',
                                                                             monitor='mean_absolute_error',
                                                                             mode='min', save_best_only=True)
                model.compile(loss=tensorflow.losses.MeanSquaredError(), optimizer=optimizer,
                              metrics=[tensorflow.metrics.MeanAbsoluteError()])
                history = model.fit(x=inputData, y=outputData, epochs=maxEpochs, batch_size=batchSize, verbose=1,
                                    validation_split=0.1, callbacks=[earlyStopping, modelCheckpoint])
                del model
                model = tensorflow.keras.models.load_model('best_param_model.h5')

            except Exception as ErrorContext:
                pprint.pprint(f"{ErrorContext}{os.linesep}{pprint.pformat(whoami())}")
                history = None
                model = None

            return history, model

    def __init__(self, inputParamSeries, outputParamSeries):
        """
        Function for instantiating a NlogParamPredictor instance

        Args:
            inputParamSeries: list of 2D np.arrays containing the parameter vectors from the event descriptions to be
                              used as inputs to the model
            outputParamSeries: list of 2D np.arrays containing the parameter vectors for the event descriptions to be
                               used as reference outputs for training
        """
        inputParamsTrain, inputParamsTest, outputParamsTrain, outputParamsTest = NlogUtils().splitDataSet(
            inputParamSeries, outputParamSeries, randomState=42)
        self.inputParamsTrain = inputParamsTrain
        self.inputParamsTest = inputParamsTest
        self.outputParamsTrain = outputParamsTrain
        self.outputParamsTest = outputParamsTest
        self.paramDimensions = self.inputParamsTrain[0].shape[1]
        self.inputWidth = self.inputParamsTrain[0].shape[0]
        self.outputWidth = self.outputParamsTrain[0].shape[0]

    def sequentialNet(self, hiddenUnits, lstm_activation='tanh', lstm_initializer='glorot_uniform', dropout=False):
        """
        function for creating a generic RNN model using the sequential keras architecture

        Args:
            hiddenUnits: Integer for the number of neurons contained in each hidden layer
            lstm_activation: activation function for LSTM layers. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
            lstm_initializer: weight initializer for the lstm layers. Must be selected from the following:
                           ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                           'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
            dropout: Boolean flag to indicate if dropout should be applied in between layers in the model

        Returns:
            lstmModel: Tensorflow RNN model containing the desired topology

        """
        if dropout:
            lstmModel = tensorflow.keras.Sequential([
                tensorflow.keras.layers.Dropout(0.2, input_shape=(self.inputWidth, self.paramDimensions)),
                tensorflow.keras.layers.LSTM(hiddenUnits, return_sequences=True, kernel_initializer=lstm_initializer,
                                             activation=lstm_activation),
                tensorflow.keras.layers.Dropout(0.2),
                tensorflow.keras.layers.LSTM(hiddenUnits, return_sequences=False, kernel_initializer=lstm_initializer,
                                             activation=lstm_activation, input_shape=(self.paramDimensions,
                                                                                      self.inputWidth)),
                tensorflow.keras.layers.Dropout(0.2),
                tensorflow.keras.layers.Dense(self.paramDimensions * self.outputWidth),
                tensorflow.keras.layers.Reshape([self.outputWidth, self.paramDimensions])
            ])
        else:
            lstmModel = tensorflow.keras.Sequential([
                tensorflow.keras.layers.LSTM(hiddenUnits, return_sequences=True, kernel_initializer=lstm_initializer,
                                             activation=lstm_activation, input_shape=(self.inputWidth,
                                                                                      self.paramDimensions)),
                tensorflow.keras.layers.LSTM(hiddenUnits, return_sequences=False, kernel_initializer=lstm_initializer,
                                             activation=lstm_activation),
                tensorflow.keras.layers.Dense(self.paramDimensions * self.outputWidth),
                tensorflow.keras.layers.Reshape([self.outputWidth, self.paramDimensions])
            ])
        return lstmModel

    def genericPredictor(self, hiddenUnits, maxEpochs=2000, optimizer='Adam', lstm_activation='tanh',
                         lstm_initializer='glorot_uniform', dropout=False):
        """
        wrapper function for generating, training, and evaluating an Nlog parameter predictive model

        Args:
            hiddenUnits: Integer for the number of neurons contained in each hidden layer
            maxEpochs: Integer for the maximum number of epochs to be considered when training the model
            optimizer: optimizer to be used for the model, must be selected from the following
                      ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']
            lstm_activation: activation function for LSTM layers. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
            lstm_initializer: weight initializer for the lstm layers. Must be selected from the following:
                           ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                           'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
            dropout: Boolean flag to indicate if dropout should be applied in between layers in the model

        Returns:
            model: Tensorflow NLOG parameter predictive model
            predictionEmbeddings: list of 2D np.arrays containing the parameter vectors for the event descriptions
                                  predicted by the model

        """

        model = self.sequentialNet(hiddenUnits, lstm_activation=lstm_activation, lstm_initializer=lstm_initializer,
                                   dropout=dropout)
        history = self.RNNUtility.compileAndFit(model, self.inputParamsTrain, self.outputParamsTrain,
                                                maxEpochs=maxEpochs, optimizer=optimizer)

        metrics = model.evaluate(x=self.inputParamsTest, y=self.outputParamsTest)
        predictedParams = model.predict(self.inputParamsTest)
        print(str(metrics))

        return model, predictedParams


class NlogPredictor(object):
    def __init__(self, nlogFolder="data/output/nlog", nlogParserFolder="software/parse/nlogParser",
                 numComponents=50, maxNumParams=8, inputSize=4000, maxOutputSize=1000, debug=False):
        """
        function for initializing a the overarching NlogPredictor instance

        Args:
            nlogFolder: Path for the nlog Folder in which the nlog event files are contained
            nlogParserFolder: Path for the folder in which the NLogFormats.py script is contained
            numComponents: Integer for the number of dimensions to be used in the NLOG description embeddings
            maxNumParams: Integer for the maximum number of parameters that can be contained in an NLOG description
                          for the specified formats file
            inputSize: Integer for the number of NLOG events to be considered as the input for the predictive models
            maxOutputSize: Integer for the maximum number of NLOG events to be predicted with the models
            debug: Verbose printing for debug use

        """
        self.nlogFolder = tryFolder(path=nlogFolder)
        self.nlogParserFolder = tryFolder(path=nlogParserFolder)
        self.inputSize = inputSize
        self.numComponents = numComponents
        self.maxNumParams = maxNumParams
        self.maxOutputSize = maxOutputSize
        self.nlogDataProcessor = NlogDataProcessor(nlogFolder=self.nlogFolder, nlogParserFolder=self.nlogParserFolder,
                                                   numComponents=self.numComponents, maxNumParams=self.maxNumParams,
                                                   debug=debug)
        self.nlogTokenizer = self.nlogDataProcessor.tokenizer
        (nlogDeltaTimes, nlogDeltaEventNums, nlogEventsInputs, nlogEventsOutputs, nlogParamsInputs, nlogParamsOutputs,
         nlogTimesInputs, nlogTimesOutputs) = self.nlogDataProcessor.generateDataSets(inputSize=self.inputSize,
                                                                                      maxOutputSize=self.maxOutputSize)
        self.nlogWidthPredictor = NlogWidthPredictor(nlogDeltaTimes, nlogDeltaEventNums)
        self.nlogTimePredictor = NlogTimePredictor(nlogTimesInputs, nlogTimesOutputs)
        self.nlogEventsPredictor = NlogEventsPredictor(nlogEventsInputs, nlogEventsOutputs)
        self.nlogParamsPredictor = NlogParameterPredictor(nlogParamsInputs, nlogParamsOutputs)

    def generateOptimizer(self, optimizer="Adam", learningRate=0.1):
        """
        function for generating an optimizer with a specified learning rate

        Args:
            optimizer: optimizer to be used for the model, must be selected from the following
                            ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']
            learningRate: float value for the learning rate to be used in the model

        Returns:
            opt: optimizer structure with specified learning rate

        """
        if optimizer == "Adam":
            opt = tensorflow.keras.optimizers.Adam(learning_rate=learningRate)
        elif optimizer == "SGD":
            opt = tensorflow.keras.optimizers.SGD(learning_rate=learningRate)
        elif optimizer == "RMSprop":
            opt = tensorflow.keras.optimizers.RMSprop(learning_rate=learningRate)
        elif optimizer == "Adagrad":
            opt = tensorflow.keras.optimizers.Adagrad(learning_rate=learningRate)
        elif optimizer == "Adadelta":
            opt = tensorflow.keras.optimizers.Adadelta(learning_rate=learningRate)
        else:
            opt = tensorflow.keras.optimizers.Adamax(learning_rate=learningRate)

        return opt

    def widthPredictorAPI(self, widthModelType='elastic'):
        """
        Function for generating, training and evaluating a width predictive model

        Args:
            widthModelType: name of the model type to be used in the linear regression model for determining the number
                            of NLOG events to be predicted. Must be selected from the following:
                            ['elastic', 'lasso', 'ridge', 'default']

        Returns:
            widthPredictorModel: linear regression model to be used for prediction
            widthPredictorScore: R^2 score for the correlation between time deltas and number of events changed
            widthPredictorAccuracy: accuracy score for the number of predicted changes that was within 5% of the right
                                    value

        """
        widthPredictorModel, widthPredictorScore, widthPredictions = self.nlogWidthPredictor.genericLinearPredictor(
            modelType=widthModelType)
        print("Width Predictor Score: " + str(widthPredictorScore))

        widthExpectations = self.nlogWidthPredictor.eventDeltaTest

        widthTotalClassifications = 0
        widthCorrectClassifications = 0
        for i in range(len(widthExpectations)):
            tempScore = abs(widthPredictions[i] - widthExpectations[i]) / widthPredictions[i]
            if tempScore < 0.05:
                widthCorrectClassifications += 1
            widthTotalClassifications += 1

        widthPredictorAccuracy = widthCorrectClassifications / widthTotalClassifications
        print("Width Predictor Accuracy: " + str(widthPredictorAccuracy))

        return widthPredictorModel, widthPredictorScore, widthPredictorAccuracy

    def timePredictorAPI(self, timeHiddenUnits=128, timeMaxEpochs=2000, timeOptimizer='Adam',
                         timeLstmActivation='tanh', timeLstmInitializer='glorot_uniform', timeDropout=False):
        """
        Function for generating, training and evaluating a Nlog event predictive model

        Args:
            timeHiddenUnits: Integer for the number of neurons contained in each hidden layer
            timeMaxEpochs: Integer for the maximum number of epochs to be considered when training the model
            timeOptimizer: optimizer to be used for the model, must be selected from the following
                            ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']
            timeLstmActivation: activation function for LSTM layers. Must be selected from the following:
                                  ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu',
                                  'exponential']
            timeLstmInitializer: weight initializer for the lstm layers. Must be selected from the following:
                                   ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones',
                                   'glorot_normal', 'glorot_uniform', 'identity', 'orthogonal', 'constant',
                                   'variance_scaling']
            timeDropout: Boolean flag to indicate if dropout should be applied in between layers in the model

        Returns:
            timePredictorModel: Tensorflow NLOG event predictive model
            timePredictorAccuracy: accuracy score for the number of predicted events that were actually correctly
                                    predicted

        """
        timePredictorModel = None
        timePredictorAccuracy = None
        timePredictorModel, timePredictions = self.nlogTimePredictor.genericPredictor(hiddenUnits=timeHiddenUnits,
                                                                                      maxEpochs=timeMaxEpochs,
                                                                                      optimizer=timeOptimizer,
                                                                                      lstm_activation=timeLstmActivation,
                                                                                      lstm_initializer=timeLstmInitializer,
                                                                                      dropout=timeDropout)

        timeExpectations = self.nlogTimePredictor.outputTimeTest

        timeTotalClassifications = 0
        timeCorrectClassifications = 0

        for index in range(len(timeExpectations)):
            print("Evaluating Time Set # " + str(index))
            for i in range(len(timeExpectations[index])):
                predictedTimes = timePredictions[index][i]
                expectedTimes = timeExpectations[index][i]
                for j in range(len(expectedTimes)):
                    tempScore = abs(expectedTimes[j] - predictedTimes[j]) / (expectedTimes[j] + 0.1)
                    if tempScore < 0.05:
                        timeCorrectClassifications += 1
                    timeTotalClassifications += 1

        timePredictorAccuracy = timeCorrectClassifications / timeTotalClassifications
        print("Time Predictor Accuracy: " + str(timePredictorAccuracy))

        return timePredictorModel, timePredictorAccuracy

    def eventPredictorAPI(self, eventsHiddenUnits=128, eventsMaxEpochs=2000, eventsOptimizer='Adam',
                          eventsLstmActivation='tanh', eventsLstmInitializer='glorot_uniform', eventsDropout=False):
        """
        Function for generating, training and evaluating a Nlog event predictive model

        Args:
            eventsHiddenUnits: Integer for the number of neurons contained in each hidden layer
            eventsMaxEpochs: Integer for the maximum number of epochs to be considered when training the model
            eventsOptimizer: optimizer to be used for the model, must be selected from the following
                            ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']
            eventsLstmActivation: activation function for LSTM layers. Must be selected from the following:
                                  ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu',
                                  'exponential']
            eventsLstmInitializer: weight initializer for the lstm layers. Must be selected from the following:
                                   ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones',
                                   'glorot_normal', 'glorot_uniform', 'identity', 'orthogonal', 'constant',
                                   'variance_scaling']
            eventsDropout: Boolean flag to indicate if dropout should be applied in between layers in the model

        Returns:
            eventPredictorModel: Tensorflow NLOG event predictive model
            eventPredictorAccuracy: accuracy score for the number of predicted events that were actually correctly
                                    predicted

        """
        eventPredictorModel = None
        eventPredictorAccuracy = None
        eventPredictorModel, eventPredictions = \
            self.nlogEventsPredictor.genericPredictor(hiddenUnits=eventsHiddenUnits, maxEpochs=eventsMaxEpochs,
                                                      optimizer=eventsOptimizer, lstm_activation=eventsLstmActivation,
                                                      lstm_initializer=eventsLstmInitializer, dropout=eventsDropout)

        eventExpectations = self.nlogEventsPredictor.outputEventsTest

        eventTotalClassifications = 0
        eventCorrectClassifications = 0

        for index in range(len(eventExpectations)):
            print("Evaluating Event Set # " + str(index))
            for i in range(len(eventExpectations[index])):
                nlogEncoding, parseString, paramNum = self.nlogTokenizer.decodeEventEncoding(eventPredictions[index][i])
                if np.allclose(nlogEncoding, eventExpectations[index][i]):
                    eventCorrectClassifications += 1
                eventTotalClassifications += 1

        eventPredictorAccuracy = eventCorrectClassifications / eventTotalClassifications
        print("Event Predictor Accuracy: " + str(eventPredictorAccuracy))
        return eventPredictorModel, eventPredictorAccuracy

    def paramPredictorAPI(self, paramsHiddenUnits=128, paramsMaxEpochs=2000, paramsOptimizer='Adam',
                          paramsLstmActivation='tanh', paramsLstmInitializer='glorot_uniform', paramsDropout=False):
        """
        Function for generating, training and evaluating a Nlog parameter predictive model

        Args:
            paramsHiddenUnits: Integer for the number of neurons contained in each hidden layer
            paramsMaxEpochs: Integer for the maximum number of epochs to be considered when training the model
            paramsOptimizer: optimizer to be used for the model, must be selected from the following
                             ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']
            paramsLstmActivation: activation function for LSTM layers. Must be selected from the following:
                                  ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu',
                                  'exponential']
            paramsLstmInitializer: weight initializer for the lstm layers. Must be selected from the following:
                                   ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones',
                                   'glorot_normal', 'glorot_uniform', 'identity', 'orthogonal', 'constant',
                                   'variance_scaling']
            paramsDropout: Boolean flag to indicate if dropout should be applied in between layers in the model

        Returns:
            paramsPredictorModel: Tensorflow NLOG parameter predictive model
            paramPredictorAccuracy: accuracy score for the number of predicted parameters that were actually correctly
                                    predicted

        """
        paramsPredictorModel = None
        paramPredictorAccuracy = None
        paramsPredictorModel, paramsPredictions = \
            self.nlogParamsPredictor.genericPredictor(hiddenUnits=paramsHiddenUnits, maxEpochs=paramsMaxEpochs,
                                                      optimizer=paramsOptimizer, lstm_activation=paramsLstmActivation,
                                                      lstm_initializer=paramsLstmInitializer, dropout=paramsDropout)
        paramExpectations = self.nlogParamsPredictor.outputParamsTest

        paramTotalClassifications = 0
        paramCorrectClassifications = 0

        for index in range(len(paramExpectations)):
            print("Evaluating Param Set # " + str(index))
            for i in range(len(paramExpectations[index])):
                predictedParams = paramsPredictions[index][i]
                expectedParams = paramExpectations[index][i]
                for j in range(len(expectedParams)):
                    tempScore = abs(expectedParams[j] - predictedParams[j]) / (expectedParams[j] + 0.1)
                    if tempScore < 0.05:
                        paramCorrectClassifications += 1
                    paramTotalClassifications += 1

        paramPredictorAccuracy = paramCorrectClassifications / paramTotalClassifications
        print("Param Predictor Accuracy: " + str(paramPredictorAccuracy))
        return paramsPredictorModel, paramPredictorAccuracy

    def nlogPredictorAPI(self, widthModelType='elastic', timeHiddenUnits=128, timeMaxEpochs=2000,
                         timeOptimizer='Adam', timeLstmActivation='tanh', timeLstmInitializer='glorot_uniform',
                         timeDropout=False, eventsHiddenUnits=128, eventsMaxEpochs=2000,
                         eventsOptimizer='Adam', eventsLstmActivation='tanh', eventsLstmInitializer='glorot_uniform',
                         eventsDropout=False, paramsHiddenUnits=128, paramsMaxEpochs=2000, paramsOptimizer='Adam',
                         paramsLstmActivation='tanh', paramsLstmInitializer='glorot_uniform', paramsDropout=False):
        """
        Function for executing the entrie NLOG prediction system

        Args:
            timeDropout:
            timeLstmActivation:
            timeLstmInitializer:
            timeMaxEpochs:
            timeHiddenUnits:
            timeOptimizer:
            widthModelType: name of the model type to be used in the linear regression model for determining the number
                            of NLOG events to be predicted. Must be selected from the following:
                            ['elastic', 'lasso', 'ridge', 'default']
            eventsHiddenUnits: Integer for the number of neurons contained in each hidden layer for the event predictive
                               model
            eventsMaxEpochs: Integer for the maximum number of epochs to be considered when training the event
                             predictive model
            eventsOptimizer: optimizer to be used for the event predictive model, must be selected from the following:
                             ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']
            eventsLstmActivation: activation function for LSTM layers in the event predictive model. Must be selected
                                  from the following: ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh',
                                  'selu', 'elu', 'exponential']
            eventsLstmInitializer: weight initializer for the lstm layers in the event predictive model. Must be
                                   selected from the following: ['random_normal', 'random_uniform', 'truncated_normal',
                                   'zeros', 'ones', 'glorot_normal', 'glorot_uniform', 'identity', 'orthogonal',
                                   'constant', 'variance_scaling']
            eventsDropout: Boolean flag to indicate if dropout should be applied in between layers in the event
                           predictive model
            paramsHiddenUnits: Integer for the number of neurons contained in each hidden layer for the parameter
                               predictive model
            paramsMaxEpochs: Integer for the maximum number of epochs to be considered when training the parameter
                             predictive model
            paramsOptimizer: optimizer to be used for the parameter predictive model, must be selected from the
                             following: ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']
            paramsLstmActivation: activation function for LSTM layers in the parameter predictive model. Must be
                                  selected from the following: ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign',
                                  'tanh', 'selu', 'elu', 'exponential']
            paramsLstmInitializer: weight initializer for the lstm layers in the parameter predictive model. Must be
                                   selected from the following: ['random_normal', 'random_uniform', 'truncated_normal',
                                   'zeros', 'ones', 'glorot_normal', 'glorot_uniform', 'identity', 'orthogonal',
                                   'constant', 'variance_scaling']
            paramsDropout: Boolean flag to indicate if dropout should be applied in between layers in the parameter
                           predictive model

        Returns:
            widthPredictorModel: linear regression model to be used for prediction
            eventPredictorModel: Tensorflow NLOG event predictive model
            paramsPredictorModel: Tensorflow NLOG parameter predictive model

        """
        widthPredictorModel = None
        timePredictorModel = None
        eventPredictorModel = None
        paramsPredictorModel = None

        try:
            widthPredictorModel, widthPredictorScore, widthPredictorAccuracy = self.widthPredictorAPI(
                widthModelType=widthModelType)

            timeOptimizer = self.generateOptimizer(optimizer=timeOptimizer, learningRate=0.1)
            eventsOptimizer = self.generateOptimizer(optimizer=eventsOptimizer, learningRate=0.01)
            paramsOptimizer = self.generateOptimizer(optimizer=paramsOptimizer, learningRate=0.1)

            timePredictorModel, timePredictorAccuracy = self.timePredictorAPI(timeHiddenUnits=timeHiddenUnits,
                                                                              timeMaxEpochs=timeMaxEpochs,
                                                                              timeOptimizer=timeOptimizer,
                                                                              timeLstmActivation=timeLstmActivation,
                                                                              timeLstmInitializer=timeLstmInitializer,
                                                                              timeDropout=timeDropout)

            eventPredictorModel, eventPredictorAccuracy = self.eventPredictorAPI(eventsHiddenUnits=eventsHiddenUnits,
                                                                                 eventsMaxEpochs=eventsMaxEpochs,
                                                                                 eventsOptimizer=eventsOptimizer,
                                                                                 eventsLstmActivation=eventsLstmActivation,
                                                                                 eventsLstmInitializer=eventsLstmInitializer,
                                                                                 eventsDropout=eventsDropout)

            paramsPredictorModel, paramPredictorAccuracy = self.paramPredictorAPI(paramsHiddenUnits=paramsHiddenUnits,
                                                                                  paramsMaxEpochs=paramsMaxEpochs,
                                                                                  paramsOptimizer=paramsOptimizer,
                                                                                  paramsLstmActivation=paramsLstmActivation,
                                                                                  paramsLstmInitializer=paramsLstmInitializer,
                                                                                  paramsDropout=paramsDropout)

            nlogDeltaTimes, nlogEventsInputs, nlogParamsInputs, nlogTimesInputs, firstOutput = \
                self.nlogDataProcessor.generateDemoData(self.inputSize)

            nlogDeltaTimes = np.array(nlogDeltaTimes).reshape((-1, 1))
            nlogEventDelta = np.array(widthPredictorModel.predict(nlogDeltaTimes))
            nlogTimeStamps = timePredictorModel.predict(np.array(nlogTimesInputs))
            nlogEvents = eventPredictorModel.predict(np.array(nlogEventsInputs))
            nlogParams = paramsPredictorModel.predict(np.array(nlogParamsInputs))

            outputStrings = []
            for index in range(len(nlogEventDelta)):
                for i in range(int(nlogEventDelta[index])):
                    if i > self.maxOutputSize - 1:
                        continue
                    nlogEncoding, parseString, paramNum = self.nlogTokenizer.decodeEventEncoding(nlogEvents[index][i])
                    newParams = nlogParams[index][i][:paramNum]
                    newTimeStamp = nlogTimeStamps[index][i]
                    newParseString, newParamsTuple = self.nlogTokenizer.reformatString(parseString, newParams)
                    line = str(newParseString) % newParamsTuple
                    timeStampStr = NlogUtils().formatNlogTime(newTimeStamp)
                    line = timeStampStr + "\t" + line
                    outputStrings.append(line)

            for i in range(len(firstOutput)):
                print("Expected Output: ")
                print(firstOutput[i].strip())
                print("Predicted Output: ")
                print(outputStrings[i])
                print("############################################################################ \n")
        except BaseException as ErrorContext:
            pprint.pprint(f"{ErrorContext}{os.linesep}{pprint.pformat(whoami())}")
        return widthPredictorModel, timePredictorModel, eventPredictorModel, paramsPredictorModel


def main():
    """
        main function to be called when the script is directly executed from the
        command line
    """
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--nlogFolder",
                      dest='nlogFolder',
                      default=None,
                      help='Path for the nlog Folder in which the nlog event files are contained')
    parser.add_option("--nlogParserFolder",
                      dest='nlogParserFolder',
                      default=None,
                      help='Path for the folder in which the NLogFormats.py script is contained')
    parser.add_option("--numComponents",
                      dest='numComponents',
                      default=None,
                      help='Integer for the number of dimensions to be used in the NLOG description embeddings')
    parser.add_option("--maxNumParams",
                      dest='maxNumParams',
                      default=None,
                      help='Integer for the maximum number of parameters that can be contained in an NLOG description'
                           'for the specified formats file')
    parser.add_option("--inputSize",
                      dest='inputSize',
                      default=None,
                      help='Integer for the number of NLOG events to be considered as the input for the predictive '
                           'models')
    parser.add_option("--maxOutputSize",
                      dest='maxOutputSize',
                      default=None,
                      help='Integer for the maximum number of NLOG events to be predicted with the models')
    parser.add_option("--debug",
                      dest='debug',
                      default=False,
                      help='Verbose printing for debug use')
    parser.add_option("--widthModelType",
                      dest='widthModelType',
                      default=None,
                      help='name of the model type to be used in the linear regression model for determining the number'
                           'of NLOG events to be predicted. Must be selected from the following: '
                           '[\'elastic\', \'lasso\', \'ridge\', \'default\']')
    parser.add_option("--timeHiddenUnits",
                      dest='timeHiddenUnits',
                      default=None,
                      help='Integer for the number of neurons contained in each hidden layer for the NLOG time stamp '
                           'predictor model')
    parser.add_option("--eventsHiddenUnits",
                      dest='eventsHiddenUnits',
                      default=None,
                      help='Integer for the number of neurons contained in each hidden layer for the NLOG event '
                           'predictor model')
    parser.add_option("--paramsHiddenUnits",
                      dest='paramsHiddenUnits',
                      default=None,
                      help='Integer for the number of neurons contained in each hidden layer for the NLOG parameter '
                           'predictor model')
    parser.add_option("--timeMaxEpochs",
                      dest='timeMaxEpochs',
                      default=None,
                      help='Integer for the maximum number of epochs to be considered when training the NLOG time stamp'
                           ' predictor model')
    parser.add_option("--eventsMaxEpochs",
                      dest='eventsMaxEpochs',
                      default=None,
                      help='Integer for the maximum number of epochs to be considered when training the NLOG event '
                           'predictor model')
    parser.add_option("--paramsMaxEpochs",
                      dest='paramsMaxEpochs',
                      default=None,
                      help='Integer for the maximum number of epochs to be considered when training the NLOG parameter '
                           'predictor model')
    parser.add_option("--timeOptimizer",
                      dest='timeOptimizer',
                      default=None,
                      help='name of the optimizer to be used in the NLOG time stamp predictor model. Must be selected '
                           'from the following: [\'SGD\', \'RMSprop\', \'Adagrad\', \'Adadelta\', \'Adam\', \'Adamax\']')
    parser.add_option("--eventsOptimizer",
                      dest='eventsOptimizer',
                      default=None,
                      help='name of the optimizer to be used in the NLOG event predictor model. Must be selected '
                           'from the following: [\'SGD\', \'RMSprop\', \'Adagrad\', \'Adadelta\', \'Adam\', \'Adamax\']')
    parser.add_option("--paramsOptimizer",
                      dest='paramsOptimizer',
                      default=None,
                      help='name of the optimizer to be used in the NLOG parameter predictor model. Must be selected '
                           'from the following: [\'SGD\', \'RMSprop\', \'Adagrad\', \'Adadelta\', \'Adam\', \'Adamax\']')
    parser.add_option("--timeLstmActivation",
                      dest='timeLstmActivation',
                      default=None,
                      help='name of the activation function to be used in the LSTM layers of the NLOG time stamp '
                           'predictor model. Must be selected from the following: '
                           '[\'relu\', \'sigmoid\', \'softmax\', \'softplus\', \'softsign\', \'tanh\', \'selu\', '
                           '\'elu\', \'exponential\']')
    parser.add_option("--eventsLstmActivation",
                      dest='eventsLstmActivation',
                      default=None,
                      help='name of the activation function to be used in the LSTM layers of the NLOG event predictor '
                           'model. Must be selected from the following: '
                           '[\'relu\', \'sigmoid\', \'softmax\', \'softplus\', \'softsign\', \'tanh\', \'selu\', '
                           '\'elu\', \'exponential\']')
    parser.add_option("--paramsLstmActivation",
                      dest='paramsLstmActivation',
                      default=None,
                      help='name of the activation function to be used in the LSTM layers of the NLOG parameter '
                           'predictor model. Must be selected from the following: '
                           '[\'relu\', \'sigmoid\', \'softmax\', \'softplus\', \'softsign\', \'tanh\', \'selu\', '
                           '\'elu\', \'exponential\']')
    parser.add_option("--timeLstmInitializer",
                      dest='timeLstmInitializer',
                      default=None,
                      help='name of the weight initializer function to be used in the LSTM layers of the NLOG time '
                           'stamp predictor model. Must be selected from the following: '
                           '[\'random_normal\', \'random_uniform\', \'truncated_normal\', \'zeros\', \'ones\', '
                           '\'glorot_normal\', \'glorot_uniform\', \'identity\', \'orthogonal\', \'constant\', '
                           '\'variance_scaling\']')
    parser.add_option("--eventsLstmInitializer",
                      dest='eventsLstmInitializer',
                      default=None,
                      help='name of the weight initializer function to be used in the LSTM layers of the NLOG event '
                           'predictor model. Must be selected from the following: '
                           '[\'random_normal\', \'random_uniform\', \'truncated_normal\', \'zeros\', \'ones\', '
                           '\'glorot_normal\', \'glorot_uniform\', \'identity\', \'orthogonal\', \'constant\', '
                           '\'variance_scaling\']')
    parser.add_option("--paramsLstmInitializer",
                      dest='paramsLstmInitializer',
                      default=None,
                      help='name of the weight initializer function to be used in the LSTM layers of the NLOG parameter'
                           ' predictor model. Must be selected from the following: '
                           '[\'random_normal\', \'random_uniform\', \'truncated_normal\', \'zeros\', \'ones\', '
                           '\'glorot_normal\', \'glorot_uniform\', \'identity\', \'orthogonal\', \'constant\', '
                           '\'variance_scaling\']')
    parser.add_option("--timeDropout",
                      dest='timeDropout',
                      default=True,
                      help='Boolean flag that indicates if dropout in between layers should be applied to the NLOG '
                           'time stamp predictor model')
    parser.add_option("--eventsDropout",
                      dest='eventsDropout',
                      default=True,
                      help='Boolean flag that indicates if dropout in between layers should be applied to the NLOG '
                           'event predictor model')
    parser.add_option("--paramsDropout",
                      dest='paramsDropout',
                      default=True,
                      help='Boolean flag that indicates if dropout in between layers should be applied to the NLOG '
                           'parameter predictor model')

    (options, args) = parser.parse_args()
    if options.nlogFolder is None:
        nlogFolder = "data/output/nlog"
    else:
        nlogFolder = options.nlogFolder

    if options.nlogParserFolder is None:
        nlogParserFolder = "software/parse/nlogParser"
    else:
        nlogParserFolder = options.nlogParserFolder

    if options.numComponents is None:
        numComponents = 50
    else:
        numComponents = options.numComponents

    if options.maxNumParams is None:
        maxNumParams = 8
    else:
        maxNumParams = options.maxNumParams

    if options.inputSize is None:
        inputSize = 4000
    else:
        inputSize = options.inputSize

    if options.maxOutputSize is None:
        maxOutputSize = 1000
    else:
        maxOutputSize = options.maxOutputSize

    if options.debug == "True":
        debug = True
    else:
        debug = False

    if options.widthModelType is None:
        widthModelType = 'elastic'
    else:
        widthModelType = options.widthModelType

    if options.timeHiddenUnits is None:
        timeHiddenUnits = 128
    else:
        timeHiddenUnits = int(options.timeHiddenUnits)

    if options.eventsHiddenUnits is None:
        eventsHiddenUnits = 128
    else:
        eventsHiddenUnits = int(options.eventsHiddenUnits)

    if options.paramsHiddenUnits is None:
        paramsHiddenUnits = 128
    else:
        paramsHiddenUnits = int(options.paramsHiddenUnits)

    if options.timeMaxEpochs is None:
        timeMaxEpochs = 2000
    else:
        timeMaxEpochs = int(options.timeMaxEpochs)

    if options.eventsMaxEpochs is None:
        eventsMaxEpochs = 2000
    else:
        eventsMaxEpochs = int(options.eventsMaxEpochs)

    if options.paramsMaxEpochs is None:
        paramsMaxEpochs = 2000
    else:
        paramsMaxEpochs = int(options.paramsMaxEpochs)

    if options.timeOptimizer is None:
        timeOptimizer = 'Adam'
    else:
        timeOptimizer = options.timeOptimizer

    if options.eventsOptimizer is None:
        eventsOptimizer = 'Adam'
    else:
        eventsOptimizer = options.eventsOptimizer

    if options.paramsOptimizer is None:
        paramsOptimizer = 'Adam'
    else:
        paramsOptimizer = options.paramsOptimizer

    if options.timeLstmActivation is None:
        timeLstmActivation = 'tanh'
    else:
        timeLstmActivation = options.timeLstmActivation

    if options.eventsLstmActivation is None:
        eventsLstmActivation = 'tanh'
    else:
        eventsLstmActivation = options.eventsLstmActivation

    if options.paramsLstmActivation is None:
        paramsLstmActivation = 'tanh'
    else:
        paramsLstmActivation = options.paramsLstmActivation

    if options.timeLstmInitializer is None:
        timeLstmInitializer = 'glorot_uniform'
    else:
        timeLstmInitializer = options.timeLstmInitializer

    if options.eventsLstmInitializer is None:
        eventsLstmInitializer = 'glorot_uniform'
    else:
        eventsLstmInitializer = options.eventsLstmInitializer

    if options.paramsLstmInitializer is None:
        paramsLstmInitializer = 'glorot_uniform'
    else:
        paramsLstmInitializer = options.paramsLstmInitializer

    if options.timeDropout == "True":
        timeDropout = True
    else:
        timeDropout = False

    if options.eventsDropout == "True":
        eventsDropout = True
    else:
        eventsDropout = False

    if options.paramsDropout == "True":
        paramsDropout = True
    else:
        paramsDropout = False

    nlogPredictor = NlogPredictor(nlogFolder=nlogFolder, nlogParserFolder=nlogParserFolder,
                                  numComponents=numComponents, maxNumParams=maxNumParams, inputSize=inputSize,
                                  maxOutputSize=maxOutputSize, debug=debug)
    nlogPredictor.nlogPredictorAPI(widthModelType=widthModelType, timeHiddenUnits=timeHiddenUnits,
                                   timeMaxEpochs=timeMaxEpochs, timeOptimizer=timeOptimizer,
                                   timeLstmActivation=timeLstmActivation, timeLstmInitializer=timeLstmInitializer,
                                   timeDropout=timeDropout, eventsHiddenUnits=eventsHiddenUnits,
                                   eventsMaxEpochs=eventsMaxEpochs, eventsOptimizer=eventsOptimizer,
                                   eventsLstmActivation=eventsLstmActivation,
                                   eventsLstmInitializer=eventsLstmInitializer, eventsDropout=eventsDropout,
                                   paramsHiddenUnits=paramsHiddenUnits, paramsMaxEpochs=paramsMaxEpochs,
                                   paramsOptimizer=paramsOptimizer, paramsLstmActivation=paramsLstmActivation,
                                   paramsLstmInitializer=paramsLstmInitializer, paramsDropout=paramsDropout)

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
