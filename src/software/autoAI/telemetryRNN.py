#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Daniel Garces
# *****************************************************************************/
## @package telemetryRNN
from __future__ import absolute_import, division, print_function, \
    unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations

"""
Brief:
    Library for Recurrent Neural Networks time series analysis proposed by Hochreiter and Schmidhuber, 1997.
Description:
    Class library is designed to be used as a tracking template file to ease use across all files and ensure tracking.
Requires: 
    Python 3
Usage Documentation:
    https://www.tensorflow.org/tutorials/keras
    
"""


class Transformer:

    @staticmethod
    def get(transformType='AsIs'):
        if transformType == 'AsIs':
            return 1
        if transformType == 'Noise':
            return 2
        elif transformType == 'Chaos':
            return 3
        elif transformType == 'Novel':
            return 4
        else:
            return 1


class itemObject(object):
    def __init__(self, data=None,
                 itemFrequency=None,
                 itemInterval=None,
                 itemOffset=None,
                 itemMin=None,
                 itemMax=None):

        if itemFrequency is None:
            itemFrequency = 1
        elif itemFrequency < 1:
            itemFrequency = 1
        if itemMin is None:
            itemMin = 0
        if itemMax is None:
            itemMax = 1
        if itemMin > itemMax:
            itemMin = (itemMax - 1)
        if itemInterval is None:
            itemInterval = [itemMin, itemMax]

        self.interval = itemInterval
        if itemOffset is None:
            itemOffset = itemInterval.min
        else:
            itemOffset = (itemOffset % itemInterval.max) + itemInterval.min

        self.itemSet = [itemFrequency, itemInterval, itemOffset]
        self.payload = data

    def __getitem__(self):
        return self

    @staticmethod
    def getType():
        return 'itemObject'

    def applyEntropy(self, newItem=None, transformType='AsIs'):
        return newItem


class itemSet(itemObject):
    def __init__(self, data, superSet=None, item=None):
        super().__init__(data)
        if superSet is None:
            itemSetObject = itemObject(item)
            self.superSet = [itemSetObject, itemSetObject, itemSetObject]
        else:
            self.superSet = superSet
        return

    def getType(self):
        return 'itemSet'

    def applyEntropy(self, newItem=itemObject(), transformType='AsIs'):
        import numpy

        if transformType == 'Noise' or transformType == 'Chaos' or transformType == 'Novel':
            totalItems = len(newItem)
            arraySet = []
            for iterator in range(totalItems):
                arraySet.append(float(newItem.payload))
            averageSet = numpy.average(arraySet)
            standardDeviationSet = numpy.std(arraySet)
            noise = numpy.random.normal(averageSet, standardDeviationSet, totalItems)
            for iterator in range(totalItems):
                newItem[iterator].payload = newItem.payload + noise
        else:  # 'As Is' means to not modify the item.
            newItem = newItem
        return newItem


class itemSequence(itemObject, itemSet):
    def __init__(self, superSet=None):
        self.data = superSet

    @staticmethod
    def getType():
        return 'itemSequence'

    def applyEntropy(self, newItem, signature):
        return


class seriesRNNPredict(object):
    import ctypes, datetime, os

    maxPath = 256
    maxTime = 32
    maxName = 16

    _pack_ = 1
    _fields_ = [
        ("absPath", ctypes.c_wchar * maxPath, ctypes.sizeof(ctypes.c_char * maxPath)),  # Path to the file.
        ("filename", ctypes.c_uint32, ctypes.sizeof(ctypes.c_uint32)),  # Identification file.
        ("major", ctypes.c_uint16, ctypes.sizeof(ctypes.c_uint16)),  # Major version number of the file.
        ("minor", ctypes.c_uint16, ctypes.sizeof(ctypes.c_uint16)),  # Minor version number of the file.
        ("time", ctypes.c_wchar * maxTime, ctypes.sizeof(ctypes.c_char * maxTime)),  # Time of execution or creation.
        ("user", ctypes.c_wchar * maxName, ctypes.sizeof(ctypes.c_char * maxName)),  # Name of the creator.
    ]

    def __init__(self, absPath=os.path.abspath(os.getcwd()),
                 filename=__file__, major=0, minor=0, time=datetime.datetime.now(), user="jdtarang",
                 uid=1,
                 trainingInFileName="data/training/data.cvs",
                 delimiterToken=',',
                 headerRowLocation=0,
                 missingDataFill='0',
                 dateLabel='year-month-day_hour-minute-second-milliseconds',
                 dateFormat='%Y-%m-%d_%H-%M-%S-%f',
                 trainingDataStream=None,
                 dataSetEnumerationMap=None,
                 dataSetEnumerationMapTranslated=None,
                 vocabulary=None,
                 sequenceLength=100,
                 predictionLength=1,
                 trainingNetworkInput=None,
                 trainingNetworkOutput=None,
                 patterns=None,
                 hiddenLayers=128,
                 dropoutRate=0.2,
                 model=None,
                 epochs=200,
                 batch_size=32,
                 bestWeightsFile=None,
                 trainingHistoryCheckpoint=None,
                 checkpoint=None,
                 seedDataPoint=None,
                 generateWidth=500,
                 predictionOutput=None,
                 predictTrainingData='data/trainingData/dataSeries_predicted.dat',
                 splittingDelimiter='.',
                 transformType='AsIs',
                 predictedDataStream=None):
        """
        Initalizes an object.
        The parameters have default values to ensure all fields have a setting. The setting of variable  by the user will allow for customization on tracking of meta data.

        Args:
            uid: Applicaiton Unique Identifier.
            absPath: absoilute path of current file.
            filename: curernt file name.
            major: The major field is used for detection of structural ordering.
            minor: The minor field is used for detection of extensions.
            time: Creation time.
            user: The organization user information.
            trainingInFileName: Name of the cvs format file with training data.
            delimiterToken = Token in delimiting the data.
            headerRowLocation: Indication of labels for data set
            missingDataFill: In the case data is missing fill it with this field.
            dateLabel: Data label to look for in columns
            dateFormat: Format parsing function for data column.
            trainingDataStream: Prepared data stream of values.
            dataSetEnumerationMap: Conversion of data to strings in a unique list.
            dataSetEnumerationMapTranslated: Encoding of data into one-hot encoding.
            vocabulary: the scope of generating from input set.
            sequenceLength: based on the properties of the data, define the sequence length for the best nearest neighbor sequence prediction.
            predictionLength: Forward window of prediction based on trained inputs.
            trainingNetworkInput: Neural network input size of sequences.
            trainingNetworkOutput: Neural network input size of sequences.
            patterns: Sequence encoding length.
            hiddenLayers: Depth of the neural network.
            dropoutRate: Rate define to ensure over fitting does not occur.
            model: Neural network construction for the application.
            epochs: Forward and backward pass of all training data.
            batch_size: The number of training data samples in one forward and backwards pass. Note the larger the value the more memory consumed.
            bestWeightsFile: Hierarchical Data Format version 5 (HDF5).
            trainingHistoryCheckpoint: History table of the data in the case of failure.
            checkpoint: Neural network snapshot in the case of failure.
            seedDataPoint: The starting data point in which prediction is to occur.
            generateWidth: In the prediction process, we want to specify the width of data generated.
            predictionOutput: Prediction stream generated.
            predictTrainingData: Prediction training data stream generation file save location.
            splittingDelimiter: Depending on the data layout, if subsequences dual data exist then we will want to know the delimiter. If this does not exist ignore.
            transformType: When predicting data, we may want to apply a transformation on the data to generate simularity, chaos in noise, or nothing. Specify the types here.
        Returns:
            None.
        Raises:
            None
        Format:
            Contents:
                Labels
                Data
            Example:
                year-month-day_hour-minute-second-milliseconds, dataStructure.itemOne, dataStructure.itemTwo, dataStructure.itemN
                2009-01-06_15-08-24-789150,                     1,                   100,                 15,                   1
        Examples:
            $ python telemetryRNN.py
        """
        import os
        __origin__ = ''
        self.uid = uid
        self.absPath = absPath
        self.filename = filename
        self.major = major
        self.minor = minor
        self.time = time
        self.user = user
        self.debugStatus = True
        print("Filepath ", absPath)
        print("Origin ", __origin__)
        print("Absolute Path ", absPath)
        print("Filename ", filename)
        print("Major ", major)
        print("Minor ", minor)
        print("Time ", time)
        print("User ", user)
        print("Debug Status", self.debugStatus)
        self.debugPath = os.path.join(absPath, "CrashDump")

        self.trainingInFileName = trainingInFileName
        self.delimiterToken = delimiterToken
        self.headerRowLocation = headerRowLocation
        self.missingDataFill = missingDataFill
        self.dateLabel = dateLabel
        self.dateFormat = dateFormat
        self.trainingDataStream = trainingDataStream
        self.dataSetEnumerationMap = dataSetEnumerationMap
        self.dataSetEnumerationMapTranslated = dataSetEnumerationMapTranslated
        self.vocabulary = vocabulary
        self.sequenceLength = sequenceLength
        self.predictionLength = predictionLength
        self.trainingNetworkInput = trainingNetworkInput
        self.trainingNetworkOutput = trainingNetworkOutput
        self.patterns = patterns
        self.hiddenLayers = hiddenLayers
        self.dropoutRate = dropoutRate
        self.model = model
        self.epochs = epochs
        self.batch_size = batch_size
        if bestWeightsFile is None:
            self.bestWeightsFile = (self.dataFormatter() + '.weights.best.hdf5')
        self.trainingHistoryCheckpoint = trainingHistoryCheckpoint
        self.checkpoint = checkpoint
        self.seedDataPoint = seedDataPoint
        self.generateWidth = generateWidth
        self.predictionOutput = predictionOutput
        self.predictTrainingData = predictTrainingData
        self.splittingDelimiter = splittingDelimiter
        self.transformType = transformType
        self.predictedDataStream = predictedDataStream
        return

    def enableDebug(self):
        self.debugStatus = True
        return

    def disableDebug(self):
        self.debugStatus = True
        return

    def executeAll(self,
                   trainingInFileName="data/training/data.cvs",
                   delimiterToken=',',
                   headerRowLocation=0,
                   missingDataFill='0',
                   dateLabel='year-month-day_hour-minute-second-milliseconds',
                   dateFormat='%Y-%m-%d_%H-%M-%S-%f',
                   trainingDataStream=None,
                   dataSetEnumerationMap=None,
                   dataSetEnumerationMapTranslated=None,
                   vocabulary=None,
                   sequenceLength=100,
                   predictionLength=1,
                   trainingNetworkInput=None,
                   trainingNetworkOutput=None,
                   patterns=None,
                   hiddenLayers=128,
                   dropoutRate=0.2,
                   model=None,
                   epochs=200,
                   batch_size=32,
                   bestWeightsFile=('UnknownTime.{epoch:02d}-{val_accuracy:.2f}.weights.best.hdf5'),
                   trainingHistoryCheckpoint=None,
                   checkpoint=None,
                   seedDataPoint=None,
                   generateWidth=500,
                   predictionOutput=None,
                   predictTrainingData='run/predicted/dataSeries_predicted.dat',
                   splittingDelimiter='.',
                   transformType='AsIs'):

        trainingDataStream = self.prepareCVS(trainingInFileName, delimiterToken, headerRowLocation, missingDataFill,
                                             dateLabel='year-month-day_hour-minute-second-milliseconds',
                                             dateFormat='%Y-%m-%d_%H-%M-%S-%f')

        (dataSetEnumerationMap, dataSetEnumerationMapTranslated, vocabulary) = self.dataMaps(trainingDataStream)

        (trainingNetworkInput, trainingNetworkOutput, patterns) = self.normalizeEncodingSequence(trainingDataStream,
                                                                                                 dataSetEnumerationMap,
                                                                                                 dataSetEnumerationMapTranslated,
                                                                                                 vocabulary,
                                                                                                 sequenceLength,
                                                                                                 predictionLength)

        model = self.createRecurrentNeuralNetworkModel(trainingNetworkInput, vocabulary, trainingNetworkOutput,
                                                       hiddenLayers, dropoutRate)

        (trainingHistoryCheckpoint, checkpoint) = self.fitRecurrentNeuralNetworkModel(model, trainingNetworkInput,
                                                                                      trainingNetworkOutput, epochs,
                                                                                      batch_size, bestWeightsFile)

        predictionOutput = self.generatePredictSequences(seedDataPoint, generateWidth, dataSetEnumerationMapTranslated,
                                                         trainingNetworkInput, patterns, vocabulary, model)

        predictedDataStream = self.predictionTransformAndSave(predictTrainingData, predictionOutput, splittingDelimiter,
                                                              transformType)
        return predictedDataStream

    @staticmethod
    def dataFormatter(timeValue=None, dateFormat='%Y-%m-%d_%H-%M-%S-%f'):
        import datetime, time
        if timeValue is None:
            timeValue = datetime.datetime.now()
        # Note: dateLabel = 'year-month-day_hour-minute-second-milliseconds'
        return time.strftime(dateFormat, timeValue)

    def weightFileName(self, time=None):
        dateTag = self.dataFormatter(time)
        filename = (dateTag + "-{epoch:02d}-{val_accuracy:.2f}")
        return filename

    @staticmethod
    def loadModelFolder(modelFolder):
        import tensorflow
        model = tensorflow.keras.models.load_model(modelFolder)
        # Check its architecture
        model.summary()
        return model

    @staticmethod
    def loadModelFile(weightsFile):
        import tensorflow
        model = tensorflow.keras.Model().load_weights(filepath=weightsFile)
        # Check its architecture
        model.summary()
        return model

    @staticmethod
    def showDataStream(trainingDataStream):
        for batch, label in trainingDataStream.take(1):
            for key, value in batch.items():
                print("{:20s}: {}".format(key, value.numpy()))
        return

    def prepareCVS(self, filename="data.cvs", delimiterToken=',', headerRowLocation=0, missingDataFill='0',
                   dateLabel='year-month-day_hour-minute-second-milliseconds',
                   dateFormat='%Y-%m-%d_%H-%M-%S-%f'):
        import pandas
        ''' Example File Format, with all data in integer form.
        year-month-day_hour-minute-second-milliseconds, dataStructure.itemOne, dataStructure.itemTwo, dataStructure.itemN
        2009-01-06_15-08-24-789150,                     1,                   100,                 15,                   1
        '''
        dataStream = pandas.read_csv(filename, delimiter=delimiterToken, header=headerRowLocation,
                                     na_values=[missingDataFill], verbose=self.debugStatus)
        dataStream[dateLabel] = pandas.to_datetime(dataStream[dateLabel], format=dateFormat)
        pandas.setIndex(dateLabel)
        trainingDataStream = dataStream

        if self.debugStatus is True:
            rowStart = 0
            rowStop = 2
            print("Sample rows \n", trainingDataStream[rowStart:rowStop:])
            self.showDataStream(trainingDataStream)

        return trainingDataStream

    @staticmethod
    def dataTypeEncoding(encoderType=None):
        # @todo in progress
        # Integer Encoding: Where each unique label is mapped to an integer. Used when fields have relation.
        if encoderType == 'Integer':
            return
        # One Hot Encoding: Where each label is mapped to a binary vector. Used for no relationship
        #   Two main drawbacks:
        #    For high-cardinality variables — those with many unique categories — the dimensionality of the transformed vector becomes unmanageable.
        #    The mapping is completely uninformed: “similar” categories are not placed closer to each other in embedding space.
        elif encoderType == 'OneHot':
            return
        # Learned Embedding: Where a distributed representation of the categories is learned.
        #   Neural network embeddings have 3 primary purposes:
        #   Finding nearest neighbors in the embedding space. These can be used to make recommendations based on user interests or cluster categories.
        #   As input to a machine learning model for a supervised task.
        #   For visualization of concepts and relations between categories.
        else:
            return

    @staticmethod
    def dataIndependantEncoding(inputDataStream=None, isOutputNetwork=False):
        # inputDataStream: can be inputs to the neural network or output.
        import sklearn, numpy
        inputLabelsEncoded = None
        trainingEncoding = None
        inputTrainingEncoding = list()
        for i in range(len(inputDataStream)):
            # Label encode each column
            for j in range(inputDataStream.shape[1:]):
                inputLabelsEncoded = sklearn.preprocessing.LabelEncoder()
                inputLabelsEncoded.fit(inputDataStream[:, j])
                # Encode
                trainingEncoding = inputLabelsEncoded.transform(inputDataStream[:, j])
                # Store
                inputTrainingEncoding.append(trainingEncoding)
        if (isOutputNetwork is True):
            # Make output d-Dimensional
            inputTrainingEncoding = numpy.reshape(inputTrainingEncoding, (len(inputTrainingEncoding), 1, 1))
        return (inputTrainingEncoding, inputLabelsEncoded, trainingEncoding)

    @staticmethod
    def createEmbeddingEncoding(inputTrainingEncoding):
        #  Depends on data from dataIndependantEncoding() and result is the input stream
        import numpy, tensorflow
        inputLayer = list()
        embeddedLayer = list()
        for i in range(len(inputTrainingEncoding)):
            # calculate the number of unique inputs
            uniquelabels = len(numpy.unique(inputTrainingEncoding[i]))
            # define input layer
            inputLayer = tensorflow.keras.layers.Input(shape=(1,))
            # define embedding layer
            embeddedLayer = tensorflow.keras.layers.Embedding(uniquelabels, 10)(inputLayer)
            # store layers
            inputLayer.append(inputLayer)
            embeddedLayer.append(embeddedLayer)
        # concat all embeddings
        merge = tensorflow.keras.layers.concatenate(embeddedLayer)
        return inputLayer, merge

    def learnedEmbedding(self, inputDataStream, isOutputNetwork=False):
        # Depends on data from createEmbeddingEncoding() and result is the input stream
        # Each category is mapped to a distinct vector, and the properties of the vector are adapted or learned while training a neural network. The vector space provides a projection of the categories, allowing those categories that are close or related to cluster together naturally.
        inputTrainingEncoding = self.dataIndependantEncoding(inputDataStream, isOutputNetwork)
        inputLayer, merge = self.createEmbeddingEncoding(inputTrainingEncoding)
        return (inputTrainingEncoding, inputLayer, merge)

    def genericNeuralNetwork(self, merge, inputLayer, inputTrainingEncoding, inputTestingEncoding, hiddenLayers, epochs,
                             batchSize):
        #  Depends on data from dataIndependantEncoding(), createEmbeddingEncoding(), learnedEmbedding()
        # @todo in progress
        import tensorflow
        # model = tensorflow.keras.models.Sequential()
        dense = tensorflow.keras.layers.Dense(hiddenLayers * 2, activation='relu', kernel_initializer='he_normal')(
            merge)
        output = tensorflow.keras.layers.Dense(1, activation='sigmoid')(dense)
        model = tensorflow.keras.models.Model(inputs=inputLayer, outputs=output)
        # compile the keras model
        model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
        # plot graph
        tensorflow.keras.utils.plot_model(model, show_shapes=True, to_file='embeddings.png')
        # fit the keras model on the dataset
        model.fit(inputTrainingEncoding, inputTestingEncoding, epochs=epochs, batch_size=batchSize,
                  verbose=self.debugStatus)
        # evaluate the keras model
        _, accuracy = model.evaluate(inputTrainingEncoding, inputTestingEncoding, verbose=0)
        print('Accuracy: %.2f' % (accuracy * 100))
        return (model, dense, output, accuracy)

    @staticmethod
    def dataLabelHiearchyEncoding(trainingDataStream):
        import sklearn  # @todo in progress
        # Categorical encoding is a process of converting categories to numbers.
        # Assigned a value from 1 through N
        # Limitation of label encoding are possible relationships between other variables in another column.
        encodeLabels = sklearn.preprocessing.LabelEncoder()
        encodedHiearchyDataStream = sklearn.preprocessing.fit_transform(trainingDataStream)
        return encodeLabels, encodedHiearchyDataStream

    @staticmethod
    def dataLabelOneHotEncoding(trainingDataStream, column):
        # @todo in progress
        # One-Hot Encoding is the process of creating dummy variables.
        #  We create additional features based on the number of unique values in
        #  the categorical feature. Every unique value in the category will be added as a feature.
        import sklearn
        encodeLabels = sklearn.preprocessing.OneHotEncoder(categorical_features=[column])
        trainingOneHotDataStream = sklearn.preprocessing.OneHotEncoder().fit_transform(trainingDataStream).toarray()
        encodedOneHotDataStreamArray = sklearn.preprocessing.fit_transform(trainingOneHotDataStream).toarray()
        return encodeLabels, encodedOneHotDataStreamArray

    def ExecuteAll_Agnostic(self,
                            isOutputNetwork=False,
                            epochs=200,
                            batchSize=32,
                            filename="data.cvs",
                            delimiterToken=',',
                            headerRowLocation=0,
                            missingDataFill='0',
                            dateLabel='year-month-day_hour-minute-second-milliseconds',
                            dateFormat='%Y-%m-%d_%H-%M-%S-%f',
                            hiddenLayers=None):
        # @todo jtarango
        trainingDataStream = self.prepareCVS(filename, delimiterToken, headerRowLocation, missingDataFill, dateLabel,
                                             dateFormat)
        inputTrainingEncoding = self.dataIndependantEncoding(inputDataStream=trainingDataStream,
                                                             isOutputNetwork=isOutputNetwork)
        (inputLayer, merge) = self.createEmbeddingEncoding(inputTrainingEncoding)
        (inputTrainingEncoding, inputLayer, merge) = self.learnedEmbedding(inputDataStream=trainingDataStream,
                                                                           isOutputNetwork=isOutputNetwork)
        (model, dense, output, accuracy) = self.genericNeuralNetwork(merge, inputLayer, inputTrainingEncoding,
                                                                     inputTestingEncoding=inputTrainingEncoding,
                                                                     hiddenLayers=hiddenLayers, epochs=epochs,
                                                                     batchSize=batchSize)

        return trainingDataStream, inputTrainingEncoding, inputLayer, merge, model, dense, output, accuracy

    @staticmethod
    def dataMaps(trainingDataStream):
        # Extract the unique items in the list of dataSeries.
        dataSetEnumerationMap = sorted(set(item for item in trainingDataStream))
        print('EnumerationMap generated')

        # Create a dictionary to map items to numeric type integers.
        #  The following transformation takes each of the disjoint items into an enumerated structure.
        #  I.E. a b c d becomes a=1, b=2, c=3, d=4. When it comes recursive sets we use encoding to provide subsequences.
        dataSetEnumerationMapTranslated = dict(
            (dataSet, number) for number, dataSet in enumerate(dataSetEnumerationMap))

        vocabulary = len(set(trainingDataStream))
        print('Vocabulary generated')
        return dataSetEnumerationMap, dataSetEnumerationMapTranslated, vocabulary

    @staticmethod
    def normalizeEncodingSequence(trainingDataStream=None, dataSetEnumerationMap=None,
                                  dataSetEnumerationMapTranslated=None, vocabulary=None, sequenceLength=100,
                                  predictionLength=1):
        import numpy
        from tensorflow.keras.utils import to_categorical
        # From the data, we instationate the input date vector and
        #  create an output vector that is the sequence length with the prediction window.
        # Default: data In is 100 and predict is 1.
        trainingNetworkInput = []
        trainingNetworkOutput = []
        # Create input sequences and the corresponding outputs.
        for i in range(0, len(trainingDataStream) - sequenceLength, predictionLength):
            sequenceIn = trainingDataStream[i: i + sequenceLength]
            sequenceOut = trainingDataStream[i + sequenceLength]
            trainingNetworkInput.append([dataSetEnumerationMapTranslated[char] for char in sequenceIn])
            trainingNetworkOutput.append(dataSetEnumerationMapTranslated[sequenceOut])
        # Pattern length
        patterns = len(trainingNetworkInput)
        # Reshape the input into a format compatible with LSTM layers
        trainingNetworkInput = numpy.reshape(trainingNetworkInput, (patterns, sequenceLength, 1))
        # Normalize input
        trainingNetworkInput = trainingNetworkInput / float(vocabulary)
        # One hot encode the output vector.
        trainingNetworkOutput = to_categorical(trainingNetworkOutput)

        return trainingNetworkInput, trainingNetworkOutput, patterns

    @staticmethod
    def createRecurrentNeuralNetworkModel(trainingNetworkInput=None, vocabulary=None, trainingNetworkOutput=None,
                                          hiddenLayers=128, dropoutRate=0.2, modelSave='saved/model'):
        print('Input and Output processed')
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import Activation, Dense, LSTM, Dropout, Flatten
        from tensorflow.keras.utils import plot_model
        model = Sequential()
        model.add(LSTM(hiddenLayers, input_shape=trainingNetworkInput.shape[1:], return_sequences=True))
        model.add(Dropout(dropoutRate))
        model.add(LSTM(hiddenLayers, return_sequences=True))
        model.add(Flatten())
        model.add(Dense(hiddenLayers * 2))
        model.add(Dropout((dropoutRate / 2) * 3))
        model.add(Dense(vocabulary))
        model.add(Activation('softmax'))
        model.compile(loss='categorical_crossentropy', optimizer='adam')
        # plot graph
        plot_model(model, show_shapes=True, to_file='RNN_embeddings.png')
        print('Model created')
        model.summary()  # Display the model's architecture.
        """Create the model architecture, Defaults construct the following.
        Layer (Type),             (Output, Shape),  Parameter Number
        ===============================================
        lstm_3 (LSTM)             (None, 100, 128), 66560
        dropout_3 (Dropout),      (None, 100, 128), 0
        lstm_4 (LSTM)             (None, 100, 128), 131584
        flatten_2 (Flatten)       (None, 12800),    0
        dense_3 (Dense)           (None, 256),      3277056
        dropout_4 (Dropout),      (None, 256),      35466
        dense_4 (Dense),          (None, 138),      35466
        Activation_2 (Activation) (None, 138),      0
        ===============================================
        Total Parameters: 3510666
        Trainable Parameters: 3510666
        Non-Trainable Parameters: 0
        """
        # Plot graph
        plot_model(model, show_shapes=True, to_file='embeddings.png')
        model.save(modelSave)  # Contains an assets folder, saved/model.pb, and variables folder.
        return model

    def fitRecurrentNeuralNetworkModel(self, model, trainingNetworkInput=None, trainingNetworkOutput=None, epochs=200,
                                       batch_size=32,
                                       bestWeightsFile='UnknownTime-{epoch:02d}-{val_accuracy:.2f}weights.best.hdf5'):
        print('Training in progress')
        """
        Train the neural network  
        """
        from tensorflow.keras.callbacks import ModelCheckpoint
        # Website: https://keras.io/models/model/
        # Create checkpoint of best fitting model weights.
        # bestWeightsFile is a Hierarchical Data Format version 5 (HDF5)
        checkpoint = ModelCheckpoint(bestWeightsFile, monitor='loss', verbose=self.debugStatus, save_best_only=True)
        # Checkpoint the model fitting and training
        trainingHistoryCheckpoint = model.fit(trainingNetworkInput, trainingNetworkOutput, epochs=epochs,
                                              batch_size=batch_size, callbacks=[checkpoint])

        if self.debugStatus is True:
            print("Training History... \n", trainingHistoryCheckpoint)

        print('Training completed')
        return trainingHistoryCheckpoint, checkpoint

    def generatePredictSequences(self, seedDataPoint=None, generateWidth=500, dataSetEnumerationMapTranslated=None,
                                 trainingNetworkInput=None, patterns=None, vocabulary=None, model=None):
        print('Generating Prediction Sequences')
        """ Generate dataSeries from the neural network based on a sequence of dataSeries """
        import numpy

        if (seedDataPoint is not None) and (seedDataPoint in dataSetEnumerationMapTranslated):
            # Pick a random integer or starting point
            start = seedDataPoint
        else:
            start = numpy.random.randint(0, len(trainingNetworkInput) - 1)
            if self.debugStatus is True:
                print("Generating random seed", start)

        # Pick a random sequence from the input as a starting point for the prediction
        pattern = trainingNetworkInput[start]
        predictionOutput = []
        print('Generating %d dataSeries points...', generateWidth)
        # Generate generateWidth dataSeries
        for itemIndex in range(generateWidth):
            predictionInput = numpy.reshape(pattern, (1, len(patterns), 1))
            predictionInput = predictionInput / float(vocabulary)
            prediction = model.predict(predictionInput, verbose=0)
            # Predicted output is the argmax(P(h|D))
            # Bayes Theorem
            #  (P(h|D)) = (P(D|h)P(h))/P(D)
            #   P(h) prior probability of hypothesis h
            #   P(D) = prior probability of training data D
            #   P(h|D) = probability of h given D
            #   P(D|h) = probability of D given h
            # Reference: https://www.cs.cmu.edu/~dgovinda/pdf/bayes.pdf
            index = numpy.argmax(prediction)  # determine the index from the prediction.
            # Mapping the predicted interger back to the corresponding item
            result = dataSetEnumerationMapTranslated[index]
            # Storing the predicted output
            predictionOutput.append(result)
            pattern.append(index)
            # Next input to the model
            pattern = pattern[1:len(pattern)]
            if self.debugStatus is True:
                print("At item ", itemIndex)

        print('Stream Generated...')
        return predictionOutput

    def predictionTransformAndSave(self,
                                   predictTrainingData='data/trainingData/dataSeries_predicted.dat',
                                   predictionOutput=None, splittingDelimiter='.', transformType='AsIs'):
        ### Converts the predicted output to singleDataStream format or in a specified way.
        """ Convert the output from the prediction to items and create a new file from the items
        itemSet is a tupple of default default
        """
        predictedDataStream = []

        print("Using prediction file ", predictTrainingData)

        # Create itemObject and itemSet of objects based on the values generated by the model
        for pattern in predictionOutput:
            # The itemSet is a pattern (generated sequence), we need to decode the pattern into the itemObject.
            if pattern.getType() == 'itemSet':
                itemsInSet = pattern.split(splittingDelimiter)  # patterns are separated with dots, we break these up
                createdItems = []
                for currentItem in itemsInSet:
                    newItem = itemObject(currentItem)  # Need to create translator for your own intepretation, reverse
                    # Create an entropy by modifying the item with noise.
                    #  if you are using one item to create an item from a different library.
                    newItem = newItem.applyEntropy(newItem, transformType)
                    createdItems.append(newItem)
                predictedDataStream.append(createdItems)
            else:  # pattern.getType() is 'itemObject'
                # Single itemObject
                newItem = itemObject(pattern)
                # Create an entropy by modifying the item with noise.
                #  if you are using one item to create an item from a different library.
                newItem = newItem.applyEntropy(newItem, transformType)
                predictedDataStream.append(newItem)

        print('Formatting predicted data stream to destination')
        predictedTrainingData = self.saveDataFormat(predictedDataStream)

        print('Saving Output file as ', predictedTrainingData)
        predictedData = self.saveData(predictedTrainingData)

        if self.debugStatus is True:
            print("Predicted Data File is ", predictedData)

        return predictedDataStream

    @staticmethod
    def evaluateAccuracy(inputEncoding, testingEncoding, model):
        # evaluate the keras model
        _, accuracy = model.evaluate(inputEncoding, testingEncoding, verbose=0)
        aVal = ('%.2f' % (accuracy * 100))
        print(f'Accuracy: {aVal}')
        return aVal

    @staticmethod
    def graphFile(fileInput='test_output.dat'):
        from pandas import read_csv
        from matplotlib import pyplot
        series = read_csv(fileInput, header=0, index_col=0, squeeze=True)
        pyplot.plot(series)
        pyplot.title(fileInput)
        pyplot.ylabel(series.__name__)
        pyplot.xlabel('S-Axis Unit(s)')
        pyplot.show()
        return

    @staticmethod
    def saveDataFormat(predictedDataStream):
        import pandas
        preds = predictedDataStream  # YOUR_LIST_OF_PREDICTION_FROM_NN
        result = pandas.DataFrame(data={
            'PREDICTIONS': preds})  # pandas.DataFrame(data={'Id': YOUR_TEST_DATAFRAME['Id'], 'PREDICTIONS': preds})
        # Tensorflow data format extract
        # pred = forward_propagation(X, parameters)
        # predictions = pred.eval(feed_dict={X: X_test})
        return result

    @staticmethod
    def saveData(predictedTrainingData, filename='predictedMeta.csv'):
        predictedTrainingData.to_csv(path_or_buf=filename, index=False, header=True)
        return predictedTrainingData


def setup(debug=True):
    state = None
    '''
    try:
        import setuptools, traceback
        state = setuptools.setup(
                      name='Recurrent Neural Network (RNN)',
                      version='1.0',
                      author='Joseph Tarango',
                      author_email='no-reply@intel.com',
                      description='Data Stream RNN',
                      url='http://github.com/StorageRelationalLibrary',
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
    if debug:
        print(state)
    return state


def main():
    try:
        exitCode = 0
        setup()
        referenceTest = seriesRNNPredict()
        referenceTest.executeAll()
    except:
        exitCode = 1
    quit(exitCode)
    return


if __name__ == '__main__':
    """Performs execution delta of the process."""
    import datetime, traceback

    p = datetime.datetime.now()
    try:
        main()
    except Exception as e:
        print("Fail End Process: ", e)
        traceback.print_exc()
    q = datetime.datetime.now()
    print("\nExecution time: " + str(q - p))
