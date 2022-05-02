# How to Run the Experiment
For running the experiment, you will first need to collect data and have it readily available in a configuration file to 
be fed into the neural network system. The mediaPredictionRNN.py script will load the configuration file into a
DataFrame and then partition it into windows of a specified length to be evaluated and generate the predictions.
The standard API will print three randomly chosen windows with the expected results (labels) before training the neural
network. After the network has been fully trained, the same three graph will be plotted to show the newly generated 
predictions as compared to the expected results (labels). The training of the neural network will fail if one of the 
fields being fed in is constant (representing an index rather than an actual numerical value), or if the time-series 
field contains strings rather than numerical values and such strings are not specified as categorical variables.


# How to Use Scripts

## mediaPredictionRNN.py
Script for  loading the content of a configuration file and utilizing a RNN model
to generate predictions on the time series values passed in as arguments into the main API. This script requires
python 3, and tensorflow version 2.3.0 or higher.

#### Command-line Arguments:
| CL Option             | Description                                                                                                   |
|-----------------------|---------------------------------------------------------------------------------------------------------------|
| --configFilePath      | Path for the configuration file where the time series data values for the media errors are contained          |
| --targetObject        | String for the name for the target Object to be considered for the time series prediction                     |
| --targetFields        | Comma-separated strings for the names of the object's fields to be considered for the time series prediction  |
| --plotColumn          | String for the name of the target field to be considered for plotting the input and predictions               |
| --matrixProfile       | Boolean flag to apply matrix profile to time series before using the RNN model                                |
| --subSeqLen           | Integer for the length of the sliding window for matrix profile (only relevant if matrix profile flag is set) |
| --inputWidth          | Integer for the length of the input sequence to be considered for the prediction                              |
| --labelWidth          | Integer for the length of the output sequence expected from the prediction                                    |
| --shift               | Integer for the shift to be considered when sliding the input window                                          |
| --batchSize           | Integer for the size of the batch to be considered when generating data sets to be fed into the RNN model     |
| --maxEpochs           | Integer for the maximum number of epochs to be considered when training the model                             |
| --hiddenLayers        | Integer for the number of neurons contained in each hidden layer                                              |
| --embeddedEncoding    | Boolean flag to apply embedded encoding to time series as the first layer in the RNN model                    |
| --categoricalEncoding | Boolean flag to apply label encoding to the time series values (usually used for categorical values)          |
| --debug               | Boolean flag to activate verbose printing for debug use                                                       |

#### Command:
```console
$ python mediaPredictionRNN.py --configFilePath C:\raad\src\software\time-series.ini --targetObject NandStats --targetFields 01-biterrors,02-biterrors --plotColumn 01-biterrors --matrixProfile True --subSeqLen 20 --inputWidth 80 --LabelWidth 20 --shift 2 --hiddenLayers 32 --debug True
```
