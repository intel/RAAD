#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Daniel Garces
# *****************************************************************************/
"""mediaPredictionRNN.py

This module contains the basic functions for loading the content of a configuration file and utilizing a RNN model
to generate predictions on the time series values passed in as arguments into the main API. This script requires
python 3, and tensorflow version 2.3.0 or higher.

Args:
    --configFilePath: Path for the configuration file where the time series data values for the media errors are contained
    --targetObject: String for the name for the target Object to be considered for the time series prediction
    --targetFields: Comma-separated strings for the names of the object's fields to be considered for the time series prediction
    --plotColumn: String for the name of the target field to be considered for plotting the input and predictions
    --matrixProfile: Boolean flag to apply matrix profile to time series before using the RNN model
    --subSeqLen: Integer for the length of the sliding window for matrix profile (only relevant if matrix profile flag is set)
    --inputWidth: Integer for the length of the input sequence to be considered for the prediction
    --labelWidth: Integer for the length of the output sequence expected from the prediction
    --shift: Integer for the shift to be considered when sliding the input window
    --batchSize: Integer for the size of the batch to be considered when generating data sets to be fed into the RNN model.
    --maxEpochs: Integer for the maximum number of epochs to be considered when training the model
    --hiddenUnits: Integer for the number of neurons contained in each hidden layer
    --embeddedEncoding: Boolean flag to apply embedded encoding to time series as the first layer in the RNN model
    --categoricalEncoding: Boolean flag to apply label encoding to the time series values (usually used for categorical values)
    --lstm_activation: activation function for LSTM layers. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
    --dense_activation: activation function for dense layer. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
    --lstm_initializer: weight initializer for the lstm layers. Must be selected from the following:
                           ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                           'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
    --dense_initializer: weight initializer for the dense layer. Must be selected from the following:
                           ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                           'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
    --debug: Boolean flag to activate verbose printing for debug use

Example:
    Default usage:
        $ python mediaPredictionRNN.py
    Specific usage:
        $ python mediaPredictionRNN.py --configFilePath C:\raad\src\software\time-series.ini
          --targetObject NandStats --targetFields 01-biterrors,02-biterrors --plotColumn 01-biterrors
          --matrixProfile True --subSeqLen 20 --inputWidth 80 --LabelWidth 20 --shift 2 --hiddenUnits 32 --debug True

"""

import sys, datetime, optparse, traceback, pprint
import tensorflow, tensorflow.keras, statistics
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn import preprocessing
import matplotlib.backends.backend_pdf as be
from statsmodels.tsa.stattools import adfuller

import software.autoAI.transformCSV as csv
import software.DP.preprocessingAPI as DP
import software.mp.utils

from software.debug import whoami
from software.utilsCommon import DictionaryPrune

mpl.rcParams['figure.figsize'] = (8, 6)
mpl.rcParams['axes.grid'] = False


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


class WindowGenerator(object):
    def __init__(self, inputWidth, labelWidth, shift, batchSize,
                 trainDataStream, valDataStream, testDataStream,
                 labelColumns=None, embeddedEncoding=False):
        """
        Class for generating a time-series window for processing

        Args:
            inputWidth: Integer for the length of the input to be considered for the window
            labelWidth: Integer for the length of the expected values sequence for the window
            shift: Integer for the shift to be considered when sliding the input window
            batchSize: Integer for the size of the batch to be considered when generating data sets to be fed into the
                       RNN model
            trainDataStream: DataFrame containing all the training data
            valDataStream: DataFrame containing all the validation data
            testDataStream: DataFrame containing all the testing data
            labelColumns: List of strings with the names of the columns inside the DataFrames
            embeddedEncoding: Boolean flag to apply embedded encoding to time series as the first layer in the RNN model

        Returns:

        """
        # Store the raw data.
        self.trainDataStream = trainDataStream
        self.valDataStream = valDataStream
        self.testDataStream = testDataStream

        # Work out the label column indices.
        self.labelColumns = labelColumns
        if labelColumns is not None:
            self.labelColumnsIndices = {name: i for i, name in
                                        enumerate(labelColumns)}
        self.columnIndices = {name: i for i, name in
                              enumerate(trainDataStream.columns)}

        # Work out the window parameters.
        self.inputWidth = inputWidth
        self.labelWidth = labelWidth
        self.shift = shift

        self.batchSize = batchSize

        self.totalWindowSize = inputWidth + shift

        self.inputSlice = slice(0, inputWidth)
        self.inputIndices = np.arange(self.totalWindowSize)[self.inputSlice]

        self.labelStart = self.totalWindowSize - self.labelWidth
        self.labelsSlice = slice(self.labelStart, None)
        self.labelIndices = np.arange(self.totalWindowSize)[self.labelsSlice]
        self.embeddedEncoding = embeddedEncoding
        self._example = None

    def __repr__(self):
        """
        function that overwrites the representation for the window instance

        Returns:
            String with the representative fields for the window

        """
        return '\n'.join([
            f'Total window size: {self.totalWindowSize}',
            f'Input indices: {self.inputIndices}',
            f'Label indices: {self.labelIndices}',
            f'Label column name(s): {self.labelColumns}'])

    def splitWindow(self, features):
        """
        function for splitting a window into two independent DataFrames, one for input and one for labels (expected
        results)

        Args:
            features: DataFrame containing all the data values for a set

        Returns:
            inputs: DataFrame with the data values for inputs
            labels: DataFrame with the data values for labels (expected results)

        """
        inputs = features[:, self.inputSlice, :]
        labels = features[:, self.labelsSlice, :]
        if self.labelColumns is not None:
            labels = tensorflow.stack(
                [labels[:, :, self.columnIndices[name]] for name in self.labelColumns], axis=-1)

        # Slicing doesn't preserve static shape information, so set the shapes
        # manually. This way the `tensorflow.data.Datasets` are easier to inspect.
        try:
            inputs.set_shape([None, self.inputWidth, None])
            labels.set_shape([None, self.labelWidth, None])
        except:
            print("There were issues while changing the shape of the dataset tensors")

        return inputs, labels

    def plotEmbedded(self, numFeatures, encoders=None, model=None, plotColumn='02-biterrors', maxSubplots=3, pdf=None):
        """
        function for plotting a specified window for an embedded model

        Args:
            numFeatures: Integer for the number of object fields included in the model
            encoders: Dictionary of label encoders for the data
            model: tensorflow model containing the desired embedded and RNN topology for producing the predictions
            plotColumn: String for the name of the field to be plotted
            maxSubplots: Integer for the maximum number of subplots to be generated
            pdf: pdf file name to save.

        Returns:

        """
        if self.example is None:
            return
        inputs, labels = self.example
        plt.figure(figsize=(12, 8))
        plotColIndex = self.columnIndices[plotColumn]
        maxNum = min(maxSubplots, len(inputs))
        currentEncoder = None
        if encoders is not None:
            currentEncoder = encoders[plotColumn]
        errorDifference = {}
        expectedOutputThreshold = {}
        secondaryGraph = False
        for n in range(maxNum):
            plt.subplot(3, 1, n + 1)
            plt.ylabel(f'{plotColumn} ')
            if currentEncoder is not None:
                currentInput = inputs[n, :, plotColIndex].numpy().astype('int32')
                currentInput = list(currentEncoder.inverse_transform(currentInput))
            else:
                currentInput = inputs[n, :, plotColIndex]
            plt.plot(self.inputIndices, currentInput, label='Inputs', marker='.', zorder=-10)

            if self.labelColumns:
                labelColIndex = self.labelColumnsIndices.get(plotColumn, None)
            else:
                labelColIndex = plotColIndex

            if labelColIndex is None:
                continue

            if currentEncoder is not None:
                currentLabels = labels[n, :, labelColIndex].numpy().astype('int32')
                currentLabels = list(currentEncoder.inverse_transform(currentLabels))
            else:
                currentLabels = labels[n, :, labelColIndex].numpy()
            plt.scatter(self.labelIndices, currentLabels, edgecolors='k', label='Labels', c='#2ca02c', s=64)

            if model is not None:
                inputs_t = tensorflow.unstack(inputs, num=numFeatures, axis=2)
                predictions = model(inputs_t)
                if currentEncoder is not None:
                    currentPredictions = predictions[n, :, labelColIndex].numpy().astype('int32')
                    currentPredictions = list(currentEncoder.inverse_transform(currentPredictions))
                else:
                    currentPredictions = predictions[n, :, labelColIndex].numpy()
                plt.scatter(self.labelIndices, currentPredictions, marker='X', edgecolors='k', label='Predictions',
                            c='#ff7f0e', s=64)
                errorDifference_t = [(currentPredictions[i] - currentLabels[i]) / currentLabels[i] for i in
                                     range(len(currentLabels))]
                errorDifference[n] = list(map(abs, errorDifference_t))
                expectedOutputThreshold[n] = [(currentLabels[i] * 0.05) / currentLabels[i] for i in
                                              range(len(currentLabels))]
                secondaryGraph = True

            if n == 0:
                plt.legend()

        if pdf is None:
            plt.show()
        else:
            pdf.savefig()
        plt.close()

        plt.figure(figsize=(24, 8))
        accuracy = {}
        for n in errorDifference.keys():
            if n == 0:
                pos = 1
            elif n == 1:
                pos = 3
            else:
                pos = 5
            plt.subplot(3, 2, pos)
            plt.plot(self.labelIndices, errorDifference[n], color='orange', label='Absolute Difference')
            if n == 0:
                plt.legend()
            if n == 1:
                plt.ylabel("Percentage Difference between predicted and expected")
            if n == 2:
                plt.xlabel("Time Step")

            relevantStats = list()
            meanCal, stdCal = software.mp.utils.util_calculateMeanStd(errorDifference[n])
            relevantStats.append(meanCal)
            relevantStats.append(statistics.median(errorDifference[n]))
            relevantStats.append(stdCal)
            relevantStats.append(max(errorDifference[n]))
            relevantStats.append(min(errorDifference[n]))
            succesfulClassifications = 0
            for i in range(len(errorDifference[n])):
                if errorDifference[n][i] <= abs(expectedOutputThreshold[n][i]):
                    succesfulClassifications += 1
            relevantStats.append(succesfulClassifications / len(errorDifference[n]))
            accuracy[n] = succesfulClassifications / len(errorDifference[n])
            relevantStatsLabels = ['Mean', 'Median', 'StDev', 'Max', 'Min', 'Accuracy']
            relevantStatsCoordinates = [1, 2, 3, 4, 5, 6]

            plt.subplot(3, 2, pos + 1)
            plt.bar(relevantStatsCoordinates, relevantStats, 0.8, tick_label=relevantStatsLabels)
            add_value_labels(plt.gca())

            if n == 0:
                plt.legend()
            if n == 2:
                plt.xlabel("Metric Name")

        if secondaryGraph:
            if pdf is None:
                plt.show()
            else:
                pdf.savefig()
        plt.close()
        return accuracy

    def plot(self, model=None, encoders=None, plotColumn='02-biterrors', maxSubplots=3, normalize=False, pdf=None):
        """
        function for plotting example windows for a specified column

        Args:
            model: Tensorflow model containing the desired topology for producing the predictions
            encoders: Dictionary of label encoders for the data
            plotColumn: String for the name of the DataFrame column to be graphed
            maxSubplots: Integer for the maximum number of subplots to be graphed
            normalize: Boolean flag to indicate whether the data has been normalized (and therefore the encoders should
                       not be used)
            pdf: pdf file name to save.

        Returns:

        """
        if self.example is None:
            return
        inputs, labels = self.example
        plt.figure(figsize=(12, 8))
        plotColIndex = self.columnIndices[plotColumn]
        maxNum = min(maxSubplots, len(inputs))
        if encoders is not None and normalize is False:
            currentEncoder = encoders[plotColumn]
        else:
            currentEncoder = None
        errorDifference = {}
        expectedOutputThreshold = {}
        secondaryGraph = False
        for n in range(maxNum):
            plt.subplot(3, 1, n + 1)
            # plt.subplots(3, 1)

            if normalize is False:
                plt.ylabel(f'{plotColumn}')
            else:
                plt.ylabel(f'{plotColumn} [normed]')

            if currentEncoder is not None:
                currentInputs = inputs[n, :, plotColIndex].numpy().astype('int32')
                currentInputs = list(currentEncoder.inverse_transform(currentInputs))
                print(str(currentInputs))
            else:
                currentInputs = inputs[n, :, plotColIndex]

            plt.plot(self.inputIndices, currentInputs, label='Inputs', marker='.', zorder=-10)

            if self.labelColumns:
                labelColIndex = self.labelColumnsIndices.get(plotColumn, None)
            else:
                labelColIndex = plotColIndex

            if labelColIndex is None:
                continue

            if currentEncoder is not None:
                currentLabels = labels[n, :, labelColIndex].numpy().astype('int32')
                currentLabels = list(currentEncoder.inverse_transform(currentLabels))
            else:
                currentLabels = labels[n, :, labelColIndex].numpy()

            plt.scatter(self.labelIndices, currentLabels, edgecolors='k', label='Labels', c='#2ca02c', s=64)

            if model is not None:
                predictions = model(inputs)
                if currentEncoder is not None:
                    currentPredictions = predictions[n, :, labelColIndex].numpy().astype('int32')
                    currentPredictions = list(currentEncoder.inverse_transform(currentPredictions))
                else:
                    currentPredictions = predictions[n, :, labelColIndex].numpy()
                plt.scatter(self.labelIndices, currentPredictions, marker='X', edgecolors='k', label='Predictions',
                            c='#ff7f0e', s=64)
                errorDifference_t = [(currentPredictions[i] - currentLabels[i]) for i in range(len(currentLabels))]
                errorDifference[n] = list(map(abs, errorDifference_t))
                expectedOutputThreshold[n] = [0.1 for _ in range(len(currentLabels))]
                secondaryGraph = True

            if n == 0:
                plt.legend()
        if pdf is None:
            plt.show()
        else:
            pdf.savefig()
        plt.close()

        # Bar graph generation
        plt.figure(figsize=(24, 8))
        accuracy = {}
        for n in errorDifference.keys():
            if n == 0:
                pos = 1
            elif n == 1:
                pos = 3
            else:
                pos = 5
            plt.subplot(3, 2, pos)
            plt.plot(self.labelIndices, errorDifference[n], color='orange', label='Absolute Difference')
            if n == 0:
                plt.legend()
            if n == 1:
                plt.ylabel("Percentage Difference between predicted and expected")
            if n == 2:
                plt.xlabel("Time Step")

            relevantStats = list()
            meanCal, stdCal = software.mp.utils.util_calculateMeanStd(errorDifference[n])
            relevantStats.append(meanCal)
            relevantStats.append(statistics.median(errorDifference[n]))
            relevantStats.append(stdCal)
            relevantStats.append(max(errorDifference[n]))
            relevantStats.append(min(errorDifference[n]))
            succesfulClassifications = 0
            for i in range(len(errorDifference[n])):
                if abs(errorDifference[n][i]) <= abs(expectedOutputThreshold[n][i]):
                    succesfulClassifications += 1
            relevantStats.append(succesfulClassifications / len(errorDifference[n]))
            accuracy[n] = succesfulClassifications / len(errorDifference[n])
            relevantStatsLabels = ['Mean', 'Median', 'StDev', 'Max', 'Min', 'Accuracy']
            relevantStatsCoordinates = [1, 2, 3, 4, 5, 6]

            plt.subplot(3, 2, pos + 1)
            plt.bar(relevantStatsCoordinates, relevantStats, 0.8, tick_label=relevantStatsLabels)
            add_value_labels(plt.gca())

            if n == 0:
                plt.legend()
            if n == 2:
                plt.xlabel("Metric Name")

        if secondaryGraph:
            if pdf is None:
                plt.show()
            else:
                pdf.savefig()
        plt.close()
        return accuracy

    def makeDataset(self, data, batchSize=32):
        """
        function for generating a timeseries dataset for the specified data

        Args:
            data: DataFrame containing the values of interest
            batchSize: Integer for the size of the batch to be considered in each data set

        Returns:
            ds: dataset containing pairs of inputs and outputs for the specified timeseries

        """
        try:
            import tensorflow.keras.preprocessing
            data = np.array(data, dtype=np.float32)
            ds = tensorflow.keras.preprocessing.timeseries_dataset_from_array(
                data=data,
                targets=None,
                sequence_length=self.totalWindowSize,
                sequence_stride=1,
                shuffle=True,
                batch_size=batchSize)
            ds = ds.map(self.splitWindow)
        except:
            import tensorflow
            print("Error in makeDataSet() {}. \n Stack: {}".format(tensorflow.__version__, traceback.extract_stack()))
            ds = None
            pass
        return ds

    @property
    def train(self):
        return self.makeDataset(self.trainDataStream, self.batchSize)

    @property
    def val(self):
        return self.makeDataset(self.valDataStream, self.batchSize)

    @property
    def test(self):
        return self.makeDataset(self.testDataStream, self.batchSize)

    @property
    def example(self):
        """Get and cache an example batch of `inputs, labels` for plotting."""
        try:
            result = getattr(self, '_example', None)
            if result is None:
                # No example batch was found, so get one from the `.train` dataset
                result = next(iter(self.train))
                # And cache it for next time
                self._example = result
        except:
            result = None
            pass
        return result


class mediaPredictionRNN(object):
    # Second Stage neural network TODO

    def __init__(self, targetFields):
        self.targetFields = targetFields


class timeSeriesRNN(object):
    class RNNUtility:
        """
        utility class containing functions for processing a configuration file and loading it into a dictionary
        """

        @staticmethod
        def compileAndFit(model, window, patience=5, maxEpochs=200, optimizer='Adam'):
            """
            function for configuring a model, compiling it, and fitting it to the specified training and validation
            data

            Args:
                model: Tensorflow model to be compiled and fitted
                window: window instance containing the training and validation data
                patience: Number of epochs with no improvement after which training will be stopped.
                maxEpochs: Number of trials to be run
                optimizer: optimizer to be used for the model, must be selected from the following
                          ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']

            Returns:
                history: Fitted Tensorflow model

            """
            try:
                earlyStopping = tensorflow.keras.callbacks.EarlyStopping(monitor='loss', patience=patience, mode='min')
                model.compile(loss=tensorflow.losses.MeanSquaredError(), optimizer=optimizer,
                              metrics=[tensorflow.metrics.MeanAbsoluteError()])

                history = model.fit(window.train, epochs=maxEpochs, validation_data=window.val,
                                    callbacks=[earlyStopping])
                model.summary()
                model.save("{0}_{1}.h5".format("standard-model",
                                               datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f")))
            except:
                history = None
                pass
            return history, model

    def __init__(self, configFilePath, matrixProfileFlag=False, subSeqLen=20, embeddedEncoding=False,
                 categoricalEncoding=False, debug=True):
        """
        function for initializing a mediaPredictionRNN instance

        Args:
            configFilePath: Path for the configuration file where the time series data values for the media errors are
                            contained
            matrixProfileFlag: Boolean flag to apply matrix profile to time series before using the RNN model
            subSeqLen: Integer for the length of the sliding window for matrix profile (only relevant if matrix
                       profile flag is set)
            embeddedEncoding:Boolean flag to apply embedded encoding to time series as the first layer in the RNN model
            categoricalEncoding: Boolean flag to apply label encoding to the time series values (usually used for
                                 categorical values)
            debug: Boolean flag to activate verbose printing for debug use

        Returns:

        """
        self.configFilePath = configFilePath
        self.matrixProfileFlag = matrixProfileFlag
        self.subSeqLen = subSeqLen
        self.embeddedEncoding = embeddedEncoding
        self.categoricalEncoding = categoricalEncoding
        self.debugStatus = debug
        self.MPData = None
        self.numFeatures = None
        if ".ini" in configFilePath:
            self.dataDict = DP.preprocessingAPI().loadDataDict(configFilePath=configFilePath, debugStatus=debug)
            self.dataDF = None
            self.columns = None
        elif ".csv" in configFilePath:
            DF = csv.TransformMetaData(inputFileName=configFilePath, debug=debug)
            self.dataDF = DF.getAnalysisFrame()
            self.columns = DF.getColumnList()
            self.dataDict = None
        else:
            print("input file does not have the right format")
            self.dataDF = None
            self.dataDict = None
            self.columns = None

    def setMatrixProfile(self, value, subSeqLen=20):
        """
        function for setting the matrixProfileFlag and generating the matrix profile dataDict if the subSeqLen has
        changed or none has been generated before

        Args:
            value: Boolean value for matrixProfileFlag
            subSeqLen: Integer for the new subSeqLen value

        Returns:

        """
        if value:
            if self.MPData is None or self.subSeqLen != subSeqLen:
                self.subSeqLen = subSeqLen
                self.MPData = DP.preprocessingAPI().generateMP(self.dataDict, subSeqLen, self.debugStatus)
        self.matrixProfileFlag = value

    def setCategoricalEncoding(self, value=True):
        """
        function for setting the categoricalEncoding flag

        Args:
            value: Boolean value for the categoricalEncoding flag

        Returns:

        """
        self.categoricalEncoding = value

    def setEmbeddedEncoding(self, value=True):
        """
        function for setting the embeddedEncoding flag

        Args:
            value: Boolean value for the embeddedEncoding flag

        Returns:

        """
        self.embeddedEncoding = value

    def dataIndependantEncoding(self, inputDataStream=None, inputDataLabels=None):
        """
        function for generating a numerical encoding for the input passed in as the inputDataStream

        Args:
            inputDataStream: DataFrame containing the values to be encoded
            inputDataLabels: List of strings containing the name of the fields to be processed

        Returns:
            encoders: Dictionary with the training encoders for the specified DataFrame fields
            inputEncodings: DataFrame with all the encoding results

        """
        # inputDataStream: can be inputs to the neural network or output.
        encoders = {}
        inputEncodings = []
        for label in inputDataLabels:
            inputLabelsEncoder = preprocessing.LabelEncoder()
            inputLabelsEncoder.fit(inputDataStream[label].values)
            # Encode
            inputEncoding = inputLabelsEncoder.transform(inputDataStream[label].values)
            # Store
            inputEncoding = pd.DataFrame(inputEncoding, columns=[label])
            inputEncodings.append(inputEncoding)
            encoders[label] = inputLabelsEncoder
        inputEncodings = pd.concat(inputEncodings, axis=1)
        return encoders, inputEncodings

    def partitionDataFrame(self, targetFields=None):
        """
        function for dividing the dataframe into train, validation, and testing sets

        Args:
            targetFields: Fields inside the Data Frame to be considered for the RNN model

        Returns:
            dataStream: DataFrame containing the entirety of the population space
            trainDataStream: DataFrame containing all the training data
            valDataStream: DataFrame containing all the validation data
            testDataStream: DataFrame containing all the testing data
            encoders: Dictionary for label encoders for each object field

        """
        self.categoricalEncoding = True
        if targetFields is None:
            targetFields = ["BitErrorsHost1", "BitErrorsHost2"]

        dataFrames = []
        targetFields = sorted(targetFields)
        for field in targetFields:
            print(field)
            fieldSeries = self.dataDF[field].values
            currentDataFrame = pd.DataFrame(fieldSeries, columns=[field])
            dataFrames.append(currentDataFrame)
        dataStream = pd.concat(dataFrames, axis=1)
        dataStream = dataStream.fillna(value=0)

        encoders, dataStream = self.dataIndependantEncoding(inputDataStream=dataStream, inputDataLabels=targetFields)

        numberOfItems = len(dataStream)
        if numberOfItems >= 5:
            rangeSet_Bottom = 0
            rangeSet_Train = max(int(numberOfItems * 0.7), 1)
            rangeSet_Test = max(int(numberOfItems * 0.9), 3)
            trainDataStream = dataStream[rangeSet_Bottom:rangeSet_Train]
            valDataStream = dataStream[rangeSet_Train:rangeSet_Test]
            testDataStream = dataStream[rangeSet_Test:]
        else:
            print(f"Error in {whoami()} data sets are too small at length of {numberOfItems}")
            trainDataStream = dataStream
            valDataStream = dataStream
            testDataStream = dataStream

        if self.debugStatus is True:
            rowStart = 0
            rowStop = 2
            print("Sample rows for train data stream \n", trainDataStream[rowStart:rowStop:])
            print("Sample rows for validation data Stream \n", valDataStream[rowStart:rowStop:])
            print("Sample rows for test data stream \n", testDataStream[rowStart:rowStop:])

        return dataStream, trainDataStream, valDataStream, testDataStream, encoders

    def loadDictIntoDataFrames(self, targetObject="NandStats", targetFields=None):
        """
        function for loading a configuration file into a pandas DataFrame to be used as input for the neural network

        Args:
            targetObject: String for the name for the target Object to be considered for the time series prediction
            targetFields: List of strings for the names of the object's fields to be considered for the time
                          series prediction

        Returns:
            dataStream: DataFrame containing the entirety of the population space
            trainDataStream: DataFrame containing all the training data
            valDataStream: DataFrame containing all the validation data
            testDataStream: DataFrame containing all the testing data
            encoders: Dictionary for label encoders for each object field

        """

        if targetFields is None:
            targetFields = ["01-biterrors", "02-biterrors"]

        if self.matrixProfileFlag:
            intermediateDict = self.MPData
        else:
            intermediateDict = self.dataDict
        subdict = intermediateDict[targetObject]

        dataFrames = list()
        usedLabels = list()
        targetFields = sorted(targetFields)
        fieldSeries = None
        for field in targetFields:
            try:
                fieldSeries = subdict[field]
                if self.check_stationarity(timeseriesCandidate=fieldSeries) is False:
                    # @todo only keep data streams that change overtime to reduce dimensionality.
                    currentDataFrame = pd.DataFrame(data=fieldSeries, columns=[field])
                    dataFrames.append(currentDataFrame)
                    usedLabels.append(field)
            except BaseException as errorObj:
                print(f"Error with field {field}, with data {fieldSeries}, {whoami()}, error: {errorObj}")
                continue
        # Prepare data
        try:
            dataStream = pd.concat(dataFrames, axis=1)
        except:
            dataStream = None
            pass
        # @todo https://pandas.pydata.org/pandas-docs/stable/user_guide/missing_data.html
        dataStream = dataStream.fillna(
            value='ffill')  # @todo Fill missing data with last known state. Another approach is to drop a sub series...

        encoders = None
        if self.categoricalEncoding:
            encoders, dataStream = self.dataIndependantEncoding(inputDataStream=dataStream,
                                                                inputDataLabels=usedLabels)

        numberOfItems = len(dataStream)
        if numberOfItems >= 5:
            # @todo dgarces & RAMP team.
            # @todo We need at least 5 data points to do a simple set; however, with large data we want to divide it up using various proven methods.
            # @todo  Small data sets are fundamentally flawed since machine learning requires adquate data to characterize.
            # Please note articles:
            #  https://machinelearningmastery.com/backtest-machine-learning-models-time-series-forecasting/
            #  https://machinelearningmastery.com/difference-test-validation-datasets/
            #  https://mlbook.explained.ai/bulldozer-testing.html
            #  https://stats.stackexchange.com/questions/346907/splitting-time-series-data-into-train-test-validation-sets
            # @todo IMPORTANT: Please note a model that remembered the timestamps and value for each observation would achieve perfect performance.
            # @todo Model Fault! Please note using a *Random Forest Regressor*, the predicted values are never outside the training set values for the target variable! When your data is in time series form. Time series problems require identification of a growing or decreasing trend that a Random Forest Regressor will not be able to formulate.
            # Definitions of Train, Validation, and Test Datasets
            #  Training Dataset: The sample of data used to fit the model.
            #  Validation Dataset: The sample of data used to provide an unbiased evaluation of a model fit on the training dataset while tuning model hyperparameters. The evaluation becomes more biased as skill on the validation dataset is incorporated into the model configuration.
            #  Test Dataset: The sample of data used to provide an unbiased evaluation of a final model fit on the training dataset.
            #
            # Scientific questions to ask:
            #  What are the limitations of traditional methods of model evaluation from machine learning and why evaluating models on out of sample data is required.
            #  How do we create train-test splits and multiple train-test splits of time series data for model evaluation in Python.
            #  How do we use walk-forward validation to provide the most realistic evaluation of machine learning models on time series data.
            #
            # For Time series, we want to do any of the following:
            #  1. Train-Test split that respect temporal order of observations.
            #  2. Multiple Train-Test splits that respect temporal order of observations.
            #  3a. Walk-Forward Validation where a model may be updated each time step new data is received.
            #  3b. K-Fold where training-validation-test are combinations of previous training-validation-test sets.

            # Method 1: Train-Test Split
            # Separate data sets into uniform size desired buckets.
            # For three data sets use: 33%-33%-33%, 33%-66%-100% and 70%-90%-100% using precise intervals.
            rangeSet_Bottom = 0
            rangeSet_Train = max(int(numberOfItems * 0.7), 1)
            rangeSet_Test = max(int(numberOfItems * 0.9), 3)
            trainDataStream = dataStream[rangeSet_Bottom:rangeSet_Train]
            valDataStream = dataStream[rangeSet_Train:rangeSet_Test]
            testDataStream = dataStream[rangeSet_Test:]

            # Method 2: Multiple Train-Test-Validation (3 sets) splits
            # Exclude the last 8 to 32% of data for the test data stream.
            #   Note (int): Base-2 numerical systems are binary computation type system friendly (I.E. computer integers)
            #   Note (float): Base-2 with resolution(bottom fraction bit, mantissa) and range (exponent) bias is best for IEEE floating point. Please read Joseph Tarango Dynamic Point Library (type system) for clarification.
            # Range for Train Test is
            #  T := Entire time series.
            #  B := Bottom data range value or index 0.
            #  N := Top data range value or index maxima.
            #  E := Selected exclude percentage from top 8% (0.08) to 32% (0.32)
            #  S := train and validation data set range.
            #  P := test data set range
            #  n_samples :=  total number of observations
            #  n_splits := total number of splits
            #  B = 0
            #  N = len(T)
            #  E = random.SystemRandom().uniform(0.08, 0.32), please use secure random numbers so for cryotographically secure execution.
            #
            #  trainDataStream_size = (i * n_samples / (n_splits + 1) + n_samples % (n_splits + 1)) * E
            #  valDataStream_size = (n_samples / (n_splits + 1)) * E
            #  testDataStream = 1-(trainDataStream_size + valDataStream_size)
            #  trainRange = [0, N * trainDataStream_size)
            #  valRange =   ( N * trainDataStream_size, N * (trainDataStream_size + valDataStream_size) )
            #  testRange =  (N * (trainDataStream_size + valDataStream_size), N)
            # Code Example
            #  from pandas import read_csv
            #  from sklearn.model_selection import TimeSeriesSplit
            #  from matplotlib import pyplot
            #  series = read_csv('data.csv', header=0, index_col=0)
            #  T = series.values
            #  X = T[:len(T)*(1-random.SystemRandom().uniform(0.08, 0.32))]
            #  splits = TimeSeriesSplit(n_splits=3)
            #  pyplot.figure(1)
            #  index = 1
            #  startPoint = 0 # Can be somewhere in the series... within reason.
            #  for train_index, test_index in splits.split(X):
            #  	train = X[train_index]
            #  	test = X[test_index]
            #  	print('Observations: %d' % (len(train) + len(test)))
            # 	print('Training Observations: %d' % (len(train)))
            # 	print('Testing Observations: %d' % (len(test)))
            # 	pyplot.subplot(310 + index)
            # 	pyplot.plot(train)
            # 	pyplot.plot([None for i in train] + [x for x in test])
            # 	index += 1
            #  pyplot.plot(T)
            # pyplot.show()

            # Method 3: Walk-Forward Validation or K-Fold with Cross validation
            #  The idea is to create a rolling expanding window of test, validation up to the peak or start of the testing data set.
            # from matplotlib import pyplot
            # series = read_csv('data.csv', header=0, index_col=0)
            #  T = series.values
            #  X = T[:len(T)*(1-random.SystemRandom().uniform(0.08, 0.32))]
            # n_train = random.SystemRandom().uniform(len(X)*0.02, len(X)*0.20)
            # n_records = len(X)
            # for i in range(n_train, n_records):
            # 	train, test = X[0:i], X[i:i+1]
            # 	print('train=%d, test=%d' % (len(train), len(test)))

            if self.debugStatus is True:
                rowStart = 0
                rowStop = 2
                print("Sample rows for train data stream \n", trainDataStream[rowStart:rowStop:])
                print("Sample rows for validation data Stream \n", valDataStream[rowStart:rowStop:])
                print("Sample rows for test data stream \n", testDataStream[rowStart:rowStop:])
        else:
            print(f"Error in {whoami()} data sets are too small at length of {numberOfItems}")
            trainDataStream = dataStream
            valDataStream = dataStream
            testDataStream = dataStream

        return dataStream, trainDataStream, valDataStream, testDataStream, encoders

    @staticmethod
    def check_stationarity(timeseriesCandidate, debug: bool = False):
        """
        Augmented Dickey-Fuller (ADF) test can be used to test the null hypothesis that the series is non-stationary.
        The ADF test helps to understand whether a change in Y is a linear trend or not. If there is a linear trend but
        the lagged value cannot explain the change in Y over time, then our data will be deemed non-stationary.
        The value of test statistics is less than 5% critical value and p-value is also less than 0.05 so we can reject
        the null hypothesis and Alternate Hypothesis that time series is Stationary seems to be true. When there is
        nothing unusual about the time plot and there appears to be no need to do any data adjustments. There is no
        evidence of changing variance also so we will not do a Box-Cox transformation.
        Args:
            timeseriesCandidate: Time series
            debug: developer debug flag

        Returns: Determination of whether the data is stationary or not?

        """
        # Early abandon exit for same exact values in series.
        if len(set(timeseriesCandidate)) == 1:
            return True

        pValueThreshold = 0.05
        result = adfuller(timeseriesCandidate, autolag='AIC')
        if debug:
            dfoutput = pd.Series(result[0:4],
                                 index=['Test Statistic', 'p-value', '#Lags Used', 'Number of Observations Used'])
            print('The test statistic: %f' % result[0])
            print('p-value: %f' % result[1])
            print('Critical Values:')
            for key, value in result[4].items():
                print('%s: %.3f' % (key, value))
            pprint.pprint(dfoutput)
        if result[1] > pValueThreshold:
            return False
        else:
            return True

    def generateDecompElemLists(self, initialList, inputData, outputData, inputWidth, labelWidth, batchSize):
        """
        function for decomposing the initial tuple list into two independent lists of inputs and outputs with the
        desired shapes

        Args:
            initialList: List of tuples (input, output) containing the desired data
            inputData: List where the resulting input sequences will be stored
            outputData: List where the resulting output sequences will be stored
            inputWidth: Integer for the length of the input sequence to be considered for the prediction
            labelWidth: Integer for the length of the output sequence expected from the prediction
            batchSize: Integer for the size of the batch to be considered when generating data sets to be fed into the RNN
                       model

        Returns:

        """
        inputDFList = []
        outputDFList = []
        for elem in initialList:
            if len(elem[0].numpy()) != batchSize:
                print("Inconsistent Batch Size. Ignoring last batch...")
                continue
            currentInputDF = tensorflow.constant(elem[0].numpy().reshape(batchSize, inputWidth))
            currentOutputDF = tensorflow.constant(elem[1].numpy().reshape(batchSize, labelWidth).T)
            inputDFList.append(currentInputDF)
            outputDFList.append(currentOutputDF)
        inputData.append(np.array(inputDFList))
        outputData.append(np.array(outputDFList))

    def decomposeDataSets(self, trainDataStream, valDataStream, testDataStream, targetFields, inputWidth,
                          labelWidth, shift, batchSize):
        """
        function for decomposing the entire train, validation, and testing data sets into independent lists for inputs
        and outputs

        Args:
            trainDataStream: DataFrame containing all the training data
            valDataStream: DataFrame containing all the validation data
            testDataStream: DataFrame containing all the testing data
            targetFields: List of strings for the names of the object's fields to be considered for the time
                          series prediction
            inputWidth: Integer for the length of the input sequence to be considered for the prediction
            labelWidth: Integer for the length of the output sequence expected from the prediction
            shift: Integer for the shift to be considered when sliding the input window
            batchSize: Integer for the size of the batch to be considered when generating data sets to be fed into the RNN
                       model

        Returns:
            trainInputData: List containing all the training input data
            trainOutputData: List containing all the training output data
            valInputData: List containing all the validation input data
            valOutputData: List containing all the validation output data
            testInputData: List containing all the testing input data
            testOutputData: List containing all the testing output data

        """
        trainInputData = []
        trainOutputData = []
        valInputData = []
        valOutputData = []
        testInputData = []
        testOutputData = []

        for label in targetFields:
            partialTrainDataStream = pd.DataFrame(trainDataStream[label].values, columns=[label])
            partialValDataStream = pd.DataFrame(valDataStream[label].values, columns=[label])
            partialTestDataStream = pd.DataFrame(testDataStream[label].values, columns=[label])
            wideWindow = WindowGenerator(inputWidth=inputWidth, labelWidth=labelWidth, shift=shift, batchSize=batchSize,
                                         trainDataStream=partialTrainDataStream, valDataStream=partialValDataStream,
                                         testDataStream=partialTestDataStream,
                                         embeddedEncoding=self.embeddedEncoding)
            trainList = list(wideWindow.train)
            valList = list(wideWindow.val)
            testList = list(wideWindow.test)
            self.generateDecompElemLists(trainList, trainInputData, trainOutputData, inputWidth, labelWidth, batchSize)
            if len(valList) > 2:
                self.generateDecompElemLists(valList, valInputData, valOutputData, inputWidth, labelWidth, batchSize)
            if len(testList) > 2:
                self.generateDecompElemLists(testList, testInputData, testOutputData, inputWidth, labelWidth, batchSize)
        return trainInputData, trainOutputData, valInputData, valOutputData, testInputData, testOutputData

    def formatDataSets(self, inputData, outputData, numFeatures):
        """
        function for adjusting the shape of input and output lists so that they can be fed into the RNN model

        Args:
            inputData: List containing input data
            outputData: List containing output data
            numFeatures: Integer for the number of object fields included in the model

        Returns:
            inputList: List of input data values in the right shape to be fed into the RNN model
            expectedResults: List of output data values in the right shape to be fed into the RNN model

        """
        outputDict = {}
        inputList = []
        expectedResults = []

        first = True
        for row in inputData:
            i = 0
            for elem in row:
                if first:
                    inputList.append([elem])
                else:
                    inputList[i].append(elem)
                i += 1
            first = False

        for row in outputData:
            i = 0
            for elem in row:
                if i in outputDict:
                    outputDict[i].append(elem)
                else:
                    outputDict[i] = [elem]
                i += 1

        for key in outputDict.keys():
            currentArray = np.array(outputDict[key])
            expectedResults.append(currentArray.T)

        print("inputList: ", str(inputList))
        inputList = tensorflow.data.Dataset.from_tensor_slices(inputList)
        inputList = inputList.map(lambda x: tensorflow.unstack(x, num=numFeatures, axis=0))
        expectedResults = tensorflow.data.Dataset.from_tensor_slices(expectedResults)

        return inputList, expectedResults

    def embeddingNet(self, inputEncodings, targetFields, hiddenUnits, inputWidth, labelWidth, numFeatures, batchSize,
                     lstm_activation='tanh', dense_activation='sigmoid', lstm_initializer='glorot_uniform',
                     dense_initializer='glorot_uniform', dropout=False):
        """
        function for creating an embedded RNN model

        Args:
            inputEncodings: DataFrame containing numerical values to be turned into vectors through the embedded
                            encoding
            targetFields: List of strings for the names of the object's fields to be considered for the time
                          series prediction
            hiddenUnits: Integer for the number of neurons contained in each hidden layer
            inputWidth: Integer for the length of the input sequence to be considered for the prediction
            labelWidth: Integer for the length of the output sequence expected from the prediction
            numFeatures: Integer for the number of object fields included in the model
            batchSize: Integer for the size of the batch to be considered when generating data sets to be fed into'
                       the RNN model
            lstm_activation: activation function for LSTM layers. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
            dense_activation: activation function for dense layer. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
            lstm_initializer: weight initializer for the lstm layers. Must be selected from the following:
                           ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                           'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
            dense_initializer: weight initializer for the dense layer. Must be selected from the following:
                           ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                           'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
            dropout: Boolean flag to indicate if dropout should be applied in between layers in the model

        Returns:
            model: Tensorflow model containing the indicated embedded layers and LSTMs

        """
        #  Depends on data from dataIndependantEncoding() and result is the input stream
        inputLayers = []
        embeddedLayers = []
        for label in targetFields:
            # calculate the number of unique inputs
            uniquelabels = len(np.unique(inputEncodings[label]))
            embeddingSize = min(50, (uniquelabels + 1) // 2)
            # define input layer
            inputLayer = tensorflow.keras.layers.Input(shape=(inputWidth, 1), batch_size=batchSize)  # input width
            print(str(inputLayer.shape))
            # define embedding layer
            embeddedLayer = tensorflow.keras.layers.Embedding(input_dim=uniquelabels + 1, output_dim=embeddingSize)(
                inputLayer)
            print(str(embeddedLayer.shape))
            embeddedLayer = tensorflow.keras.layers.Reshape(target_shape=(inputWidth, embeddingSize))(embeddedLayer)
            print(str(embeddedLayer.shape))
            # store layers
            inputLayers.append(inputLayer)
            embeddedLayers.append(embeddedLayer)
        # concat all embeddings
        merge = tensorflow.keras.layers.Concatenate()(embeddedLayers)
        print(str(merge.shape))

        if dropout:
            merge = tensorflow.keras.layers.Dropout(0.2)(merge)
        else:
            merge = tensorflow.keras.layers.Dropout(0.02)(merge)

        x = tensorflow.keras.layers.LSTM(hiddenUnits, return_sequences=True, kernel_initializer=lstm_initializer,
                                         activation=lstm_activation)(merge)
        if dropout:
            x = tensorflow.keras.layers.Dropout(0.2)(x)

        x = tensorflow.keras.layers.LSTM(hiddenUnits, return_sequences=False, kernel_initializer=lstm_initializer,
                                         activation=lstm_activation)(x)
        if dropout:
            x = tensorflow.keras.layers.Dropout(0.2)(x)

        x = tensorflow.keras.layers.Dense(labelWidth * numFeatures, kernel_initializer=dense_initializer)(x)

        x = tensorflow.keras.layers.Reshape([labelWidth, numFeatures])(x)
        print(str(x.shape))
        model = tensorflow.keras.models.Model(inputs=inputLayers, outputs=x)
        return model

    def sequentialNet(self, hiddenUnits, labelWidth, numFeatures, lstm_activation='tanh', dense_activation='sigmoid',
                      lstm_initializer='glorot_uniform', dense_initializer='glorot_uniform', dropout=False):
        """
        function for creating a generic RNN model

        Args:
            hiddenUnits: Integer for the number of neurons contained in each hidden layer
            labelWidth: Integer for the length of the output sequence expected from the prediction
            numFeatures: Integer for the number of object fields included in the model
            lstm_activation: activation function for LSTM layers. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
            dense_activation: activation function for dense layer. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
            lstm_initializer: weight initializer for the lstm layers. Must be selected from the following:
                           ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                           'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
            dense_initializer: weight initializer for the dense layer. Must be selected from the following:
                           ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                           'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
            dropout: Boolean flag to indicate if dropout should be applied in between layers in the model

        Returns:
            multi_lstm_model: Tensorflow RNN model containing the desired topology

        """
        if dropout:
            multi_lstm_model = tensorflow.keras.Sequential([
                tensorflow.keras.layers.Dropout(0.2),
                # Shape [batch, time, features] => [batch, lstm_units]
                # Adding more `lstm_units` just overfits more quickly.
                # Documents https://faroit.com/keras-docs/0.3.3/layers/advanced_activations/
                tensorflow.keras.layers.LSTM(hiddenUnits, return_sequences=True, kernel_initializer=lstm_initializer,
                                             activation=lstm_activation),
                tensorflow.keras.layers.Dropout(0.2),
                tensorflow.keras.layers.LSTM(hiddenUnits, return_sequences=False, kernel_initializer=lstm_initializer,
                                             activation=lstm_activation),
                tensorflow.keras.layers.Dropout(0.2),
                # Shape => [batch, labelWidth*features]
                tensorflow.keras.layers.Dense(labelWidth * numFeatures),
                # Shape => [batch, labelWidth, features]
                tensorflow.keras.layers.Reshape([labelWidth, numFeatures])
            ])
        else:
            multi_lstm_model = tensorflow.keras.Sequential([
                # Shape [batch, time, features] => [batch, lstm_units]
                # Adding more `lstm_units` just overfits more quickly.
                # Documents https://faroit.com/keras-docs/0.3.3/layers/advanced_activations/
                tensorflow.keras.layers.LSTM(hiddenUnits, return_sequences=True, kernel_initializer=lstm_initializer,
                                             activation=lstm_activation),
                tensorflow.keras.layers.LSTM(hiddenUnits, return_sequences=False, kernel_initializer=lstm_initializer,
                                             activation=lstm_activation),
                # Shape => [batch, labelWidth*features]
                tensorflow.keras.layers.Dense(labelWidth * numFeatures),
                # Shape => [batch, labelWidth, features]
                tensorflow.keras.layers.Reshape([labelWidth, numFeatures])
            ])

        return multi_lstm_model

    def generateNormalizedWindow(self, trainDataStream, valDataStream, testDataStream, inputWidth, labelWidth, shift,
                                 batchSize):
        """
        function for generating a window containing normalized data for a generic model

        Args:
            trainDataStream: DataFrame containing all the training data
            valDataStream: DataFrame containing all the validation data
            testDataStream: DataFrame containing all the testing data
            inputWidth: Integer for the length of the input sequence to be considered for the prediction
            labelWidth: Integer for the length of the output sequence expected from the prediction
            shift: Integer for the shift to be considered when sliding the input window
            batchSize: Integer for the size of the batch to be considered when generating data sets to be fed into the RNN
                       model

        Returns:
            wideWindow: WindowGenerator instance containing normalized data

        """
        # Normalize data
        trainMean = trainDataStream.mean()
        trainStd = trainDataStream.std()

        trainDataStream = (trainDataStream - trainMean) / trainStd
        valDataStream = (valDataStream - trainMean) / trainStd
        testDataStream = (testDataStream - trainMean) / trainStd

        wideWindow = WindowGenerator(inputWidth=inputWidth, labelWidth=labelWidth, shift=shift, batchSize=batchSize,
                                     trainDataStream=trainDataStream, valDataStream=valDataStream,
                                     testDataStream=testDataStream)

        return wideWindow

    def embeddedPredictor(self, multiPerformance, inputWidth, labelWidth, shift, batchSize, hiddenUnits, numFeatures,
                          dataStream, trainDataStream, valDataStream, testDataStream, plotColumn, targetFields,
                          encoders, maxEpochs=2000, pdf=None, optimizer='Adam', lstm_activation='tanh',
                          dense_activation='sigmoid', lstm_initializer='glorot_uniform',
                          dense_initializer='glorot_uniform', dropout=False):
        """
        function for generating a window and an embedded RNN model for a given data set, and training the model on the
        specified data

        Args:
            multiPerformance: Dictionary where the performance metric results will be stored
            inputWidth: Integer for the length of the input sequence to be considered for the prediction
            labelWidth: Integer for the length of the output sequence expected from the prediction
            shift: Integer for the shift to be considered when sliding the input window
            batchSize: Integer for the size of the batch to be considered when generating data sets to be fed into the RNN
                       model
            hiddenUnits: Integer for the number of neurons contained in each hidden layer
            numFeatures: Integer for the number of object fields included in the model
            dataStream: DataFrame containing the entirety of the population space
            trainDataStream: DataFrame containing all the training data
            valDataStream: DataFrame containing all the validation data
            testDataStream: DataFrame containing all the testing data
            plotColumn: String for the name of the target field to be considered for plotting the input and predictions
            targetFields: List of strings for the names of the object's fields to be considered for the time
                          series prediction
            encoders: Dictionary of label encoders for the data
            maxEpochs: Integer for the maximum number of epochs to be considered when training the model
            pdf: pdf file name to save.
            optimizer: optimizer to be used for the model, must be selected from the following
                       ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']
            lstm_activation: activation function for LSTM layers. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
            dense_activation: activation function for dense layer. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
            lstm_initializer: weight initializer for the lstm layers. Must be selected from the following:
                           ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                           'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
            dense_initializer: weight initializer for the dense layer. Must be selected from the following:
                           ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                           'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
            dropout: Boolean flag to indicate if dropout should be applied in between layers in the model

        Returns:
            multi_lstm_model: Tensorflow embedded RNN model containing the desired topology

        """
        entireWindow = WindowGenerator(inputWidth=inputWidth, labelWidth=labelWidth, shift=shift,
                                       batchSize=batchSize, trainDataStream=trainDataStream,
                                       valDataStream=valDataStream, testDataStream=testDataStream)

        entireWindow.plot(plotColumn=plotColumn, encoders=encoders, normalize=False, pdf=pdf)

        trainInputData, trainOutputData, \
        valInputData, valOutputData, \
        testInputData, testOutputData = self.decomposeDataSets(trainDataStream, valDataStream, testDataStream,
                                                               targetFields, inputWidth, labelWidth, shift, batchSize)

        multi_lstm_model = self.embeddingNet(dataStream, targetFields, hiddenUnits, inputWidth,
                                             labelWidth, numFeatures, batchSize, lstm_activation=lstm_activation,
                                             dense_activation=dense_activation, lstm_initializer=lstm_initializer,
                                             dense_initializer=dense_initializer, dropout=dropout)
        earlyStopping = tensorflow.keras.callbacks.EarlyStopping(monitor='loss', patience=5, mode='min')
        # @todo We want to possibly explore ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']
        multi_lstm_model.compile(loss=tensorflow.losses.MeanSquaredError(), optimizer=optimizer,
                                 metrics=[tensorflow.metrics.MeanAbsoluteError()])

        trainInputList, trainExpectedResults = self.formatDataSets(trainInputData, trainOutputData, numFeatures)

        history = multi_lstm_model.fit(x=list(trainInputList), y=list(trainExpectedResults), epochs=maxEpochs,
                                       callbacks=[earlyStopping])
        if len(testInputData) > 0:
            testInputList, testExpectedResults = self.formatDataSets(testInputData, testOutputData, numFeatures)
            multiPerformance['LSTM'] = multi_lstm_model.evaluate(x=list(testInputData), y=list(testExpectedResults),
                                                                 verbose=0)
        else:
            multiPerformance['LSTM'] = multi_lstm_model.evaluate(x=list(trainInputList),
                                                                 y=list(trainExpectedResults), verbose=0)
        multi_lstm_model.summary()
        multi_lstm_model.save(
            "{0}_{1}.h5".format("lstm-model-embedded", datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f")))

        accuracy = entireWindow.plotEmbedded(numFeatures, encoders=encoders, model=multi_lstm_model,
                                             plotColumn=plotColumn, pdf=pdf)

        return multi_lstm_model, accuracy

    def genericPredictor(self, multiPerformance, inputWidth, labelWidth, shift, batchSize, hiddenUnits, numFeatures,
                         trainDataStream, valDataStream, testDataStream, plotColumn, encoders, maxEpochs=200, pdf=None,
                         optimizer='Adam', lstm_activation='tanh', dense_activation='sigmoid',
                         lstm_initializer='glorot_uniform', dense_initializer='glorot_uniform', dropout=False):
        """
        function for generating a window and a generic RNN model for a given data set, and training the model on the
        specified data

        Args:
            multiPerformance: Dictionary where the performance metric results will be stored
            inputWidth: Integer for the length of the input sequence to be considered for the prediction
            labelWidth: Integer for the length of the output sequence expected from the prediction
            shift: Integer for the shift to be considered when sliding the input window
            batchSize: Integer for the size of the batch to be considered when generating data sets to be fed into the RNN
                       model
            hiddenUnits: Integer for the number of neurons contained in each hidden layer
            numFeatures: Integer for the number of object fields included in the model
            trainDataStream: DataFrame containing all the training data
            valDataStream: DataFrame containing all the validation data
            testDataStream: DataFrame containing all the testing data
            plotColumn: String for the name of the target field to be considered for plotting the input and predictions
            encoders: Dictionary of label encoders for the data
            maxEpochs: Integer for the maximum number of epochs to be considered when training the model
            pdf: Save data graph to PDF.
            optimizer: optimizer to be used for the model, must be selected from the following
                      ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']
            lstm_activation: activation function for LSTM layers. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
            dense_activation: activation function for dense layer. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
            lstm_initializer: weight initializer for the lstm layers. Must be selected from the following:
                           ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                           'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
            dense_initializer: weight initializer for the dense layer. Must be selected from the following:
                           ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                           'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
            dropout: Boolean flag to indicate if dropout should be applied in between layers in the model

        Returns:
            multi_lstm_model: Tensorflow generic RNN model containing the desired topology

        """
        wideWindow = self.generateNormalizedWindow(trainDataStream, valDataStream, testDataStream, inputWidth,
                                                   labelWidth, shift, batchSize)
        wideWindow.plot(plotColumn=plotColumn, encoders=encoders, normalize=True, pdf=pdf)

        multi_lstm_model = self.sequentialNet(hiddenUnits, labelWidth, numFeatures, lstm_activation=lstm_activation,
                                              dense_activation=dense_activation, lstm_initializer=lstm_initializer,
                                              dense_initializer=dense_initializer, dropout=dropout)
        history = self.RNNUtility.compileAndFit(multi_lstm_model, wideWindow, maxEpochs=maxEpochs, optimizer=optimizer)

        if len(wideWindow.test) > 0:
            multiPerformance['LSTM'] = multi_lstm_model.evaluate(wideWindow.test, verbose=0)
        else:
            multiPerformance['LSTM'] = multi_lstm_model.evaluate(wideWindow.train, verbose=0)
        accuracy = wideWindow.plot(model=multi_lstm_model, plotColumn=plotColumn, encoders=encoders, normalize=True,
                                   pdf=pdf)

        return multi_lstm_model, accuracy

    def plotPerformanceMetrics(self, multiPerformance, multi_lstm_model, pdf=None):
        """
        function for plotting the performance metric results contained in multiPerformance as a bar graph

        Args:
            multiPerformance: Dictionary containing the model name and the metric result
            multi_lstm_model: Tensorflow model from which the performance metrics were obtained
            pdf: Save data graph to PDF.

        Returns:

        """
        try:
            x = np.arange(float(len(multiPerformance)))
            print(str(x))
            width = 0.3
            metric_index = multi_lstm_model.metrics_names.index('mean_absolute_error')

            test_mae = [v[metric_index] for v in multiPerformance.values()]

            plt.bar((x + 0.17), test_mae, width, label='Test')
            add_value_labels(plt.gca())
            plt.xticks(ticks=x, labels=multiPerformance.keys(), rotation=45)
            plt.ylabel('MAE (average over all outputs)')
            plt.xlabel('Metric Name')
            _ = plt.legend()
            if pdf is None:
                plt.show()
            else:
                pdf.savefig()
            plt.close()
        except:
            pass

    def writeRNNtoPDF(self, inputWidth, labelWidth, shift, batchSize, hiddenUnits, targetObject, targetFields,
                      plotColumn, maxEpochs, pdfFileName=None):
        if pdfFileName is None:
            pdfFile = "RNN_" + targetObject + ".pdf"
        else:
            pdfFile = pdfFileName
        with be.PdfPages(pdfFile) as pp:
            accuracy = self.timeSeriesPredictorAPI(inputWidth, labelWidth, shift, batchSize, hiddenUnits, targetObject,
                                                   targetFields, plotColumn, maxEpochs, pp)
        return pdfFile, accuracy

    def timeSeriesPredictorAPI(self, inputWidth, labelWidth, shift, batchSize, hiddenUnits, targetObject, targetFields,
                               plotColumn, maxEpochs, pdf=None, removeConstantFeatures=True, optimizer='Adam',
                               lstm_activation='tanh', dense_activation='sigmoid', lstm_initializer='glorot_uniform',
                               dense_initializer='glorot_uniform', dropout=False):
        """
        API to replace standard command line call (the mediaPredictionRNN class has to instantiated before calling
        this method).

        Args:
            inputWidth: Integer for the length of the input sequence to be considered for the prediction
            labelWidth: Integer for the length of the output sequence expected from the prediction
            shift: Integer for the shift to be considered when sliding the input window
            batchSize: Integer for the size of the batch to be considered when generating data sets to be fed into the RNN
                       model
            hiddenUnits: Integer for the number of neurons contained in each hidden layer
            targetObject: Name for the target Object to be considered for the time series prediction
            targetFields: List of strings for the names of the object's fields to be considered for the time
                          series prediction
            plotColumn: String for the name of the target field to be considered for plotting the input and predictions
            maxEpochs: Integer for the maximum number of epochs to be considered when training the model
            pdf: pdf file name to save.
            removeConstantFeatures: Remove features from dict which are non-changing.
            optimizer: optimizer to be used for the model, must be selected from the following
                      ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']
            lstm_activation: activation function for LSTM layers. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
            dense_activation: activation function for dense layer. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
            lstm_initializer: weight initializer for the lstm layers. Must be selected from the following:
                           ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                           'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
            dense_initializer: weight initializer for the dense layer. Must be selected from the following:
                           ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                           'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
            dropout: Boolean flag to indicate if dropout should be applied in between layers in the model
            removeConstantFeatures: Remove features from dict which are non-changing.

        Returns:

        """
        accuracy = -1
        multiPerformance = dict()
        # multiValPerformance = {}
        print("Target Object: " + str(targetObject))
        print("Target Fields: " + str(targetFields))

        if removeConstantFeatures is True:
            selectDict, isReduced = DictionaryPrune(queryDict=self.dataDict)
            if isReduced is True:
                self.dataDict = selectDict
                print(f"Reduced meta constants...")

        if (self.dataDict is None) and (self.dataDF is None):
            print("Input File had the wrong format. Re-instantiate Object with the right file")
            return accuracy
        elif self.dataDict is None and self.dataDF is not None:
            dataStream, trainDataStream, valDataStream, testDataStream, encoders = self.partitionDataFrame(targetFields)
        else:
            dataStream, trainDataStream, valDataStream, testDataStream, encoders = self.loadDictIntoDataFrames(
                targetObject,
                targetFields)

        numFeatures = dataStream.shape[1]
        self.numFeatures = numFeatures
        print("Num of Features: " + str(numFeatures))

        if self.embeddedEncoding:
            multi_lstm_model, accuracy = self.embeddedPredictor(multiPerformance, inputWidth, labelWidth, shift,
                                                                batchSize, hiddenUnits, numFeatures, dataStream,
                                                                trainDataStream, valDataStream, testDataStream,
                                                                plotColumn, targetFields, encoders, maxEpochs, pdf,
                                                                optimizer=optimizer, lstm_activation=lstm_activation,
                                                                dense_activation=dense_activation,
                                                                lstm_initializer=lstm_initializer,
                                                                dense_initializer=dense_initializer,
                                                                dropout=dropout)

        else:
            multi_lstm_model, accuracy = self.genericPredictor(multiPerformance, inputWidth, labelWidth, shift,
                                                               batchSize, hiddenUnits, numFeatures, trainDataStream,
                                                               valDataStream, testDataStream, plotColumn, encoders,
                                                               maxEpochs, pdf, optimizer=optimizer,
                                                               lstm_activation=lstm_activation,
                                                               dense_activation=dense_activation,
                                                               lstm_initializer=lstm_initializer,
                                                               dense_initializer=dense_initializer,
                                                               dropout=dropout)
        self.plotPerformanceMetrics(multiPerformance=multiPerformance, multi_lstm_model=multi_lstm_model, pdf=pdf)
        return accuracy

    def timeSeriesPredictorAllAPI(self,
                                  matrixProfileFlag=False,
                                  embeddedEncodingFlag=False,
                                  categoricalEncodingFlag=False,
                                  inputWidth=70, labelWidth=20, shift=2, batchSize=32, hiddenUnits=128, maxEpochs=2096,
                                  subSequenceLength=1,
                                  targetObject=None, targetFields=None,
                                  plotColumn=None, pdf=None, currDataDict=None,
                                  debug=False,
                                  optimizer='Adam', lstm_activation='tanh', dense_activation='sigmoid',
                                  lstm_initializer='glorot_uniform', dense_initializer='glorot_uniform', dropout=False,
                                  removeConstantFeatures=False):
        """
        API to replace standard command line call (the mediaPredictionRNN class has to instantiated before calling this method).
        Args:
            matrixProfileFlag: Boolean value for matrixProfileFlag
            embeddedEncodingFlag: Boolean value for the embeddedEncoding flag
            categoricalEncodingFlag: Boolean value for the categoricalEncoding flag
            inputWidth: Integer for the length of the input sequence to be considered for the prediction
            labelWidth: Integer for the length of the output sequence expected from the prediction
            shift: Integer for the shift to be considered when sliding the input window
            batchSize: Integer for the size of the batch to be considered when generating data sets to be fed into the RNN model
            hiddenUnits: Integer for the number of neurons contained in each hidden layer
            maxEpochs: Integer for the maximum number of epochs to be considered when training the model
            subSequenceLength:  Integer for the new subSeqLen value
            targetObject: Name for the target Object to be considered for the time series prediction
            targetFields: List of strings for the names of the object's fields to be considered for the time series prediction
            plotColumn: String for the name of the target field to be considered for plotting the input and predictions
            pdf: pdf file name to save.
            currDataDict: dictionary containing flattened structures to be fed into RNN. Use None when not feeding entire telemetry payload into RNN
            debug: developer debug flag
            optimizer: optimizer to be used for the model, must be selected from the following
                      ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']
            lstm_activation: activation function for LSTM layers. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
            dense_activation: activation function for dense layer. Must be selected from the following:
                           ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
            lstm_initializer: weight initializer for the lstm layers. Must be selected from the following:
                           ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                           'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
            dense_initializer: weight initializer for the dense layer. Must be selected from the following:
                           ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal',
                           'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
            dropout: Boolean flag to indicate if dropout should be applied in between layers in the model.
            removeConstantFeatures: Remove features from dict which are non-changing.
        Returns:

        """
        if isinstance(debug, bool):
            self.debugStatus = debug
        if currDataDict is not None:
            self.dataDict = currDataDict
            if removeConstantFeatures is True:
                selectDict, isReduced = DictionaryPrune(queryDict=self.dataDict)
                if isReduced is True:
                    self.dataDict = selectDict
                    print(f"Reduced meta constants...")
        self.setMatrixProfile(value=matrixProfileFlag, subSeqLen=subSequenceLength)
        self.setEmbeddedEncoding(value=embeddedEncodingFlag)
        self.setCategoricalEncoding(value=categoricalEncodingFlag)
        accuracy = self.timeSeriesPredictorAPI(inputWidth=inputWidth, labelWidth=labelWidth, shift=shift,
                                               batchSize=batchSize, hiddenUnits=hiddenUnits,
                                               targetObject=targetObject, targetFields=targetFields,
                                               plotColumn=plotColumn, maxEpochs=maxEpochs, pdf=pdf, optimizer=optimizer,
                                               lstm_activation=lstm_activation, dense_activation=dense_activation,
                                               lstm_initializer=lstm_initializer, dense_initializer=dense_initializer,
                                               dropout=dropout, removeConstantFeatures=removeConstantFeatures)
        return accuracy


def main():
    """
        main function to be called when the script is directly executed from the
        command line
    """
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--configFilePath",
                      dest='configFilePath',
                      default=None,
                      help='Path for the configuration file where the time series data values for the media '
                           'errors are contained')
    parser.add_option("--targetObject",
                      dest='targetObject',
                      default=None,
                      help='Name for the target Object to be considered for the time series prediction')
    parser.add_option("--targetFields",
                      dest='targetFields',
                      default=None,
                      help='comma-separated strings for the names of the object\'s fields to be considered for the time'
                           ' series prediction')
    parser.add_option("--plotColumn",
                      dest='plotColumn',
                      default=None,
                      help='Name for the target field to be considered for plotting the input and predictions')
    parser.add_option("--matrixProfile",
                      dest='matrixProfile',
                      default=None,
                      help='Boolean flag to apply matrix profile to time series before using the RNN model')
    parser.add_option("--subSeqLen",
                      dest='subSeqLen',
                      default=None,
                      help='Integer for the length of the sliding window for matrix profile (only relevant if matrix '
                           'profile flag is set)')
    parser.add_option("--inputWidth",
                      dest='inputWidth',
                      default=None,
                      help='Integer for the length of the input sequence to be considered for the prediction')
    parser.add_option("--labelWidth",
                      dest='labelWidth',
                      default=None,
                      help='Integer for the length of the output sequence expected from the prediction')
    parser.add_option("--shift",
                      dest='shift',
                      default=None,
                      help='Integer for the shift to be considered when sliding the input window')
    parser.add_option("--batchSize",
                      dest='batchSize',
                      default=None,
                      help='Integer for the size of the batch to be considered when generating data sets to be fed into'
                           'the RNN model')
    parser.add_option("--maxEpochs",
                      dest='maxEpochs',
                      default=None,
                      help='Integer for the maximum number of epochs to be considered when training the model')
    parser.add_option("--hiddenUnits",
                      dest='hiddenUnits',
                      default=None,
                      help='Integer for the number of neurons contained in each hidden layer')
    parser.add_option("--embeddedEncoding",
                      dest='embeddedEncoding',
                      default=False,
                      help='Boolean flag to apply embedded encoding to time series as the first layer in the RNN model')
    parser.add_option("--categoricalEncoding",
                      dest='categoricalEncoding',
                      default=False,
                      help='Boolean flag to apply label encoding to the time series values (usually used for '
                           'categorical values)')
    parser.add_option("--debug",
                      dest='debug',
                      default=False,
                      help='Verbose printing for debug use')
    parser.add_option("--optimizer",
                      dest='optimizer',
                      default=None,
                      help='name of the optimizer to be used in the model. Must be selected '
                           'from the following: [\'SGD\', \'RMSprop\', \'Adagrad\', \'Adadelta\', \'Adam\', \'Adamax\']')
    parser.add_option("--lstm_activation",
                      dest='lstm_activation',
                      default=None,
                      help='name of the activation function to be used in the LSTM layers of the model. Must be '
                           'selected from the following: '
                           '[\'relu\', \'sigmoid\', \'softmax\', \'softplus\', \'softsign\', \'tanh\', \'selu\', '
                           '\'elu\', \'exponential\']')
    parser.add_option("--dense_activation",
                      dest='dense_activation',
                      default=None,
                      help='name of the activation function to be used in the dense layer of the model. Must be '
                           'selected from the following: '
                           '[\'relu\', \'sigmoid\', \'softmax\', \'softplus\', \'softsign\', \'tanh\', \'selu\', '
                           '\'elu\', \'exponential\']')
    parser.add_option("--lstm_initializer",
                      dest='lstm_initializer',
                      default=None,
                      help='name of the weight initializer function to be used in the LSTM layers of the model. '
                           'Must be selected from the following: '
                           '[\'relu\', \'sigmoid\', \'softmax\', \'softplus\', \'softsign\', \'tanh\', \'selu\', '
                           '\'elu\', \'exponential\']')
    parser.add_option("--dense_initializer",
                      dest='dense_initializer',
                      default=None,
                      help='name of the weight initializer function to be used in the dense layer of the model. '
                           'Must be selected from the following: '
                           '[\'relu\', \'sigmoid\', \'softmax\', \'softplus\', \'softsign\', \'tanh\', \'selu\', '
                           '\'elu\', \'exponential\']')
    parser.add_option("--dropout",
                      dest='dropout',
                      default=True,
                      help='Boolean flag that indicates if dropout in between layers should be applied to the model')

    (options, args) = parser.parse_args()

    ##############################################
    # Main
    ##############################################
    if options.configFilePath is None:
        configFilePath = "time-series.ini"
    else:
        configFilePath = options.configFilePath

    if options.targetObject is None:
        targetObject = "NandStats"
    else:
        targetObject = options.targetObject

    if options.targetFields is None:
        targetFields = ["01-biterrors", "02-biterrors"]
    else:
        targetFields = options.targetFields.split(",")

    if options.plotColumn is None:
        plotColumn = "01-biterrors"
    else:
        plotColumn = options.plotColumn

    if options.matrixProfile == "True":
        matrixProfile = True
    else:
        matrixProfile = False

    if options.subSeqLen is None:
        subSeqLen = 20
    else:
        subSeqLen = int(options.subSeqLen)

    if options.inputWidth is None:
        inputWidth = 76
    else:
        inputWidth = int(options.inputWidth)

    if options.labelWidth is None:
        labelWidth = 20
    else:
        labelWidth = int(options.labelWidth)

    if options.shift is None:
        shift = 1
    else:
        shift = int(options.shift)

    if options.batchSize is None:
        batchSize = 32
    else:
        batchSize = int(options.batchSize)

    if options.maxEpochs is None:
        maxEpochs = 2000
    else:
        maxEpochs = int(options.maxEpochs)

    if options.hiddenUnits is None:
        hiddenUnits = 124
    else:
        hiddenUnits = int(options.hiddenUnits)

    if options.embeddedEncoding == "True":
        embeddedEncoding = True
    else:
        embeddedEncoding = False

    if options.categoricalEncoding == "True":
        categoricalEncoding = True
    else:
        categoricalEncoding = False

    if options.debug == "True":
        debug = True
    else:
        debug = False

    if options.optimizer is None:
        optimizer = 'Adam'
    else:
        optimizer = options.optimizer

    if options.lstm_activation is None:
        lstm_activation = 'tanh'
    else:
        lstm_activation = options.lstm_activation

    if options.dense_activation is None:
        dense_activation = 'sigmoid'
    else:
        dense_activation = options.dense_activation

    if options.lstm_initializer is None:
        lstm_initializer = 'glorot_uniform'
    else:
        lstm_initializer = options.lstm_initializer

    if options.dense_initializer is None:
        dense_initializer = 'glorot_uniform'
    else:
        dense_initializer = options.dense_initializer

    if options.dropout == "True":
        dropout = True
    else:
        dropout = False

    RNN = timeSeriesRNN(configFilePath=configFilePath, matrixProfileFlag=matrixProfile, subSeqLen=subSeqLen,
                        embeddedEncoding=embeddedEncoding, categoricalEncoding=categoricalEncoding, debug=debug)
    RNN.timeSeriesPredictorAPI(inputWidth=inputWidth, labelWidth=labelWidth, shift=shift, batchSize=batchSize,
                               hiddenUnits=hiddenUnits, targetObject=targetObject, targetFields=targetFields,
                               plotColumn=plotColumn, maxEpochs=maxEpochs, optimizer=optimizer,
                               lstm_activation=lstm_activation, lstm_initializer=lstm_initializer,
                               dense_activation=dense_activation, dense_initializer=dense_initializer,
                               dropout=dropout)

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
