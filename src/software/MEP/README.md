# How to Run the Experiment
For running the experiment, you will first need to collect data (run the loadAndProbeDrive.py script with the prepDrive
flag set) and then feed it into the ARMA model to generate a set of predictions (run the mediaErrorPredictor.py script 
or the GUI). The resulting three graphs should contain the expected values, the predicted values and the percentage
difference between expected and predicted results. To modify the type of workload to be run while collecting data, 
you will need to modify the complex.sh FIO script contained in the workloads subfolder and use the new script as the 
input file for the loadAndProveDrive script.


# How to Use Scripts

## loadAndProbeDrive.py
Script for generating a load, preparing a drive and pulling data values from it, using
test commands. The load is generated using FIO, so the input file must be a bash script (.sh file extension).The drive
number of the device to be tested must be passed in both, the load configuration file and as an argument. The load
configuration files must have time-based execution for proper execution of the script.

#### Command-line Arguments:
| CL Option       | Description                                                                                                           |
|-----------------|-----------------------------------------------------------------------------------------------------------------------|
| --driveNumber   | String representation for the drive number from which to pull the data values                                         |
| --driveName     | String representation for the name of device interface to get data from                                               |
| --inputFile     | String representation for the name of the input file where the workload configuration is stored                       |
| --identifier    | String representation for the name of the data set that corresponds to the data pull to be executed                   |
| --iterations    | String representation for the number of data points to be considered in the time series                               |
| --outputDir     | String representation for the name of the output directory where the text files will be stored                        |
| --outFile       | Output configuration file suffix (including .ini file extension) where the aggregated data will be stored             |
| --prepFlag      | Boolean flag to indicate if the program should prep the drive before loading it                                       |
| --aggregateFlag | Boolean flag to indicate if the program should aggregate all the data into a configuration file (.ini file extension) |
| --debug         | Boolean flag to activate verbose printing for debug use                                                               |

#### Command:
```console
$ sudo python loadAndProbeDrive.py --driveNumber 0 --driveName /dev/nvme0n1 --inputFile rand-write.sh --identifier Tv2Hi --iterations 200 --outputDir test1 outFile test1.ini --prepFlag True -- aggregateFlag True --debug True
```

## mediaErrorPredictor.py
Script for loading the content of a configuration file and utilizing the ARMA model
to generate predictions on the time series values passed in as arguments into the main API. Please note that the 
input configuration file must have a .ini file extension, and the script must be run from a graphical
desktop, as the $DISPLAY global variable must be defined for matplotlib to work properly.

#### Command-line Arguments:
| CL Option       | Description                                                                                                                |
|-----------------|----------------------------------------------------------------------------------------------------------------------------|
| --inputFile     | String representation for the name of the configuration file where the time series data values for the media are contained |
| --targetObject  | String representation for the name of the target object to be used for the prediction model                                |
| --targetField   | String representation of the name for the target field to be used for the prediction model                                 |
| --matrixProfile | Boolean flag to apply matrix profile to time series before using the ARMA model                                            |
| --subSeqLen     | Integer for the length of the sliding window for matrix profile (only relevant if matrix profile flag is set)              |
| --debug         | Boolean flag to activate verbose printing for debug use                                                                    |

#### Command:
```console
$ python mediaErrorPredictor.py --inputFile time-series.ini --targetObject NandStats --targetField 01-biterrors --matrixProfile True --subSeqLen 20 --debug True```
```

## mediaErrorGUI.py
Script for  generating a window-based GUI for mediaErrorPredictor. Most of the implementation is based on
tkinter objects.

#### Command:
```console
$ python mediaErrorGUI.py 
```
