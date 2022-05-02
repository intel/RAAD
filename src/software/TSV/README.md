# HOW TO USE THE SCRIPTS

## renameBinaryFiles.py
script for renaming the previously collected binaries so their names
follow the UTC convention required for the time series generation. 
The previous files had the date as a single number (no dashes between fields),
followed by the name of the data set. The UTC convention consists of the following elements: 
 1. Pre-determined file name, then underscore. I.E. 'Tv2HiTAC_'
 2. UTC 4 digit year, then dash. I.E. '2020'
 3. UTC 2-digit month Number, then dash. I.E. '05'
 4. UTC 2-digit day Number, then dash. I.E. '21'
 5. UTC 2-digit hour Number, then dash. I.E. '20'
 6. UTC 2-digit minute Number, then dash. I.E. '12'
 7. UTC 2-digit second Number, then dash. I.E. '19'
 8. UTC 6-digit milli-second Number. I.E. '246000'
 9. Dot, then File extension string. I.E. '.bin'
 
Note: the file name must not contain an underscore

#### Command-line Arguments:
| CL Option       | Description  |
| ---  | ---   |
|--inputDir | String for the path of the input directory where the binaries to be renamed are stored |
|--debug | Boolean flag to activate debug statements |

#### Command:
```console
$ python renameBinaryFiles.py --inputDir ./AllBinaries --debug True
```

## generateTSBinaries.py
script for generating the telemetry binary files for a time series. 
It is assumed that telemetry pulls take approximately the same amount of time and they are evenly
spaced during the iterations

#### Command-line Arguments:
| CL Option     | Description                                                                                                                |
|---------------|----------------------------------------------------------------------------------------------------------------------------|
| --driveNumber | Integer value for the number of the drive from which telemetry data will be pulled                                         |
| --driveName   | String for name of device interface to get data from                                                                       |
| --outputDir   | String for the path of the output directory where the binaries will be stored                                              |
| --inputDir    | String for the path of the input directory where the binaries to be parsed are stored                                      |
| --debug       | Boolean flag to activate debug statements                                                                                  |
| --modeSelect  | Integer value for run mode (1=hybrid/nvme-cli, 2=internal, 3=parse-only, 4=intelmas)                                       |
| --iterations  | Integer number of data points to be considered in the time series                                                          |
| --identifier  | String for the name of the data set that corresponds to the telemetry pull to be executed (should not include underscores) |
| --time        | Integer time (in seconds) for which data will be collected                                                                 |

### External Use:
If mode is set to 1, the script will generate the binary files using nvme-cli commands
#### Command:
```console
$ python generateTSBinaries.py --driveName /dev/nvme0n1 --outputDir sample-test1 --debug True --modeSelect 1 --iterations 4 --time 3
```

### Internal Use:
If mode is set to 2, the script will generate the binary files using TWIDL commands
#### Command:
```console
$ sudo python generateTSBinaries.py --driveNumber 0 --outputDir sample-test2 --debug True --modeSelect 2 --iterations 4 --time 3
```

### Parse Binaries Only:
If mode is set to 3, the script will only parse the binary files contained in the given input directory
#### Command:
```console
$ python generateTSBinaries.py --outputDir sample-test3 --inputDir sample-test3 --debug True --modeSelect 3
```

### IntelIMAS:
If mode is set to 4, the script will generate the binary files using intelmas commands
#### Command:
```console
$ sudo python generateTSBinaries.py --driveNumber 0 --outputDir sample-test4 --debug True --modeSelect 4 --iterations 4 --time 3
```

## formatTSFiles.py
Script for generating the plain text files and the configuration files for a time series.
The plain text files must have .txt suffix, while the configuration files must have .ini suffix.
The configuration files follow the ini format, storing objects as sections, and their fields as
options inside that section. The field's values are stored as the option's values.

#### Command-line Arguments:
| CL Option      | Description                                                                                                    |
|----------------|----------------------------------------------------------------------------------------------------------------|
| --outfile      | String for the name of the output file (must contain the .ini suffix and should not contain underscores)       |
| --outpath      | String for the path of the output directory where the intermediate files will be stored                        |
| --targetObject | String for the object name to be processed (if not specified all objects will be formatted into the .ini file) |
| --fwDir        | String for the path to the firmware build directory containing the python parsers                              |
| --binDir       | String for the path to the root directory containing the bin directories for the time series                   |
| --mode         | Integer value for run mode (1=buffDict, 2=autoParsers)                                                         |
| --debug        | Boolean flag to activate debug statements                                                                      |

#### Command:
```console
$ python formatTSFiles.py --outfile time-series.ini --outpath ./time-series --targetObject ThermalSensor --fwDir ../projects/arbordaleplus_t2 --binDir ./binaries --debug True
```

## visualizeTS.py
Script for plotting time series generated from a configuration file with ini syntax as specified in
the formatTSFiles.py section above. The time series could be plotted directly or transformed 
(matrix profile) before being plotted. To run this script you must use a GUI, as pyplot requires
the environment variable $DISPLAY to be set to generate the PDF files

#### Command-line Arguments:
| CL Option      | Description                                                                                                                    |
|----------------|--------------------------------------------------------------------------------------------------------------------------------|
| --outfile      | String for the name of the output file (without the suffix)                                                                    |
| --targetObject | String for the object names to be processed (if not specified all objects contained in the configuration file will be graphed) |
| --targetFields | String for the names of the object's fields to be processed (if not specified all the fields for the objects will be plotted)  |
| --inputFile    | String of the name for the configuration file containing the data for the time-series                                          |
| --combine      | Boolean flag to indicate whether or not all fields should be combined in a single plot                                         |
| --subSeqLen    | Integer value for the length of the sliding window to be used for generating the matrix profile                                |
| --transformTS  | Boolean flag to generate the matrix profile for the given time series                                                          |
| --debug        | Boolean flag to activate debug statements                                                                                      |

#### Command:
```console
$ python visualizeTS.py --outfile test1 --targetObject ThermalSensor --targetFields logtimer,secondstimer --inputFile time-series/time-series.ini --debug True
```

## DefragHistoryGrapher.py
Script for plotting DefragHistory time series generated from a configuration file.
To run this script you must use a GUI, as pyplot requires the environment variable $DISPLAY to be set
to generate the PDF files.

#### Command-line Arguments:
| CL Option        | Description                                                                                |
|------------------|--------------------------------------------------------------------------------------------|
| --outfile        | String for the name of the output file (without the suffix)                                |
| --inputFile      | String of the path name for the configuration file containing the data for the time-series |
| --numCores       | Integer for the number of cores from which data was pulled                                 |
| --mode           | Integer value for run mode (1=ADP, 2=CDR)                                                  |
| --encapStruct    | String for the name of the struct where the set points are contained (ADP)                 |
| --trackingName   | String for the name of the stat to be tracked in the graph                                 |
| --bandwidthVar   | String for the name of the field to be used to calculate the bandwidth                     |
| --headerName     | String for the name of the field associated with the header (ADP)                          |
| --indexName      | String for the name of the field associated with the index                                 |
| --timeLabel      | String for the name of the field associated with time                                      |
| --coreLabel      | String for the name of the struct associated with core number                              |
| --logTypeLabel   | String for the name of the field associated with the log type (ADP)                        |
| --setPointNames  | Comma-separated strings for the names of the set points to be used in the graph (ADP)      |
| --setPointValues | Comma-separated integers for the values of the set points to be used in the graph (CDR)    |
| --colors         | Comma-separated strings of the color names for the set points to be used in graph (ADP)    |
| --maxBandwidth   | Integer for the maximum value for the Bandwidth axis                                       |
| --debug          | Boolean flag to activate debug statements                                                  |

#### Command:
```console
$ python DefragHistoryGrapher.py --outfile test1 --inputFile time-series/time-series.ini --numCores 2 --debug True
```

## DefragHistoryGUI.py
Script for generating a GUI that displays the plots of DefragHistory time series generated from a configuration file.

#### Command:
```console
$ python DefragHistoryGUI.py
```

## genericObjectGUI.py
Script for generating a GUI that displays the plots of the time series for any generic object generated from a 
configuration file.

#### Command:
```console
$ python genericObjectGUI.py
```

## loadAndProbeSystem.py
Script for generating a load, preparing a drive and pulling telemetry data from it. It uses IOMeter when running on 
Windows and FIO when running in Linux. The input file must be a csv file when running on Windows and a bash script when 
running on Linux. The drive number of the device to be tested must be passed in both, the configuration file and as an 
argument. The configuration files must have time-based execution for proper telemetry extraction.

#### Command-line Arguments:
| CL Option         | Description                                                                                   |
|-------------------|-----------------------------------------------------------------------------------------------|
| --driveNumber     | Integer for the drive number from which to pull telemetry data                                |
| --inputFile       | String for the path to the input file where the workload configuration is stored              |
| --identifier      | String for the name of the data set that corresponds to the telemetry pull to be executed     |
| --outputDir       | String for the path to the output directory where the binaries will be stored                 |
| --parse           | Boolean flag to parse the telemetry binaries pulled from the drive                            |
| --volumeLabel     | String for the label to be used on the disk volume                                            |
| --volumeAllocUnit | String for the volume allocation unit size                                                    |
| --volumeFS        | String for the name of the file system to be used in the disk volume                          |
| --volumeLetter    | String for the letter to be assigned to the disk volume                                       |
| --partitionStyle  | String for the name of the partition style to be used in the specified disk                   |
| --partitionFlag   | Boolean flag to indicate if the program should partition the drive using the given parameters |
| --prepFlag        | Boolean flag to indicate if the program should prep the drive before loading it               |
| --debug           | Boolean flag to activate verbose printing for debug use                                       |

#### Command (Linux):
```console
$ sudo python loadAndProbeSystem.py --driveNumber 0 --inputFile complex.sh --identifier Tv2Hi --parse True --outputDir binaries --debug True
```
#### Command (Windows):
```console
$ python loadAndProbeSystem.py --driveNumber 1 --inputFile Thermal-4KSW1QD1W.csv --identifier Tv2Hi --parse True --outputDir binaries --debug True
```


## configToText.py
Script for turning a configuration file into multiple the plain text files
that each contain a single object structure to be turned back agin into its binary representation.
The plain text files have .txt suffix, while the configuration file has .ini suffix

#### Command-line Arguments:
| CL Option    | Description                                                                               |
|--------------|-------------------------------------------------------------------------------------------|
| --inputFile  | String of the name for the configuration file containing the data for the time-series     |
| --iterations | Integer number of data points to be considered in the time series                         |
| --identifier | String for the name of the data set that corresponds to the telemetry pull to be executed |
| --debug      | Boolean flag to activate debug statements                                                 |

#### Command:
```console
$ python configToText.py --inputFile ./time-series/time-series.ini --iterations 10 --identifier Tv2HiTAC --debug True
```

# Usage Examples with Output Logs

## renameBinaryFiles.py
<details><summary>Click to Expand</summary>
<p>

#### Log content below.

```console
$ python renameBinaryFiles.py --inputDir ./AllBinaries --debug True
Processing: /home/lab/Documents/parse/AllBinaries/20190913095256220000_workload_healthy12.bin
New name: workload-healthy12_2019-09-13-09-52-56-220000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190829130921007000_idle_healthy310.bin
New name: idle-healthy310_2019-08-29-13-09-21-007000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190913132937063000_workload_healthy712.bin
New name: workload-healthy712_2019-09-13-13-29-37-063000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190822171141941000_idle_healthy3921.bin
New name: idle-healthy3921_2019-08-22-17-11-41-941000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190822171141941000_idle_healthy3751.bin
New name: idle-healthy3751_2019-08-22-17-11-41-941000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190822171141941000_idle_healthy1798.bin
New name: idle-healthy1798_2019-08-22-17-11-41-941000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190826142715591000_idle_healthy353.bin
New name: idle-healthy353_2019-08-26-14-27-15-591000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190822171141941000_idle_healthy3775.bin
New name: idle-healthy3775_2019-08-22-17-11-41-941000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190912131830085000_idle_healthy897.bin
New name: idle-healthy897_2019-09-12-13-18-30-085000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190913103101063000_workload_healthy250.bin
New name: workload-healthy250_2019-09-13-10-31-01-063000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190913155230327000_workload_fail7.bin
New name: workload-fail7_2019-09-13-15-52-30-327000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190822171141941000_idle_healthy4773.bin
New name: idle-healthy4773_2019-08-22-17-11-41-941000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20200501202534654000_idle_healthy3.bin
New name: idle-healthy3_2020-05-01-20-25-34-654000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190822171141941000_idle_healthy2662.bin
New name: idle-healthy2662_2019-08-22-17-11-41-941000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190830101943246000_idle_healthy412.bin
New name: idle-healthy412_2019-08-30-10-19-43-246000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190822171141941000_idle_healthy4433.bin
New name: idle-healthy4433_2019-08-22-17-11-41-941000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190912131830085000_idle_healthy271.bin
New name: idle-healthy271_2019-09-12-13-18-30-085000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190829130921007000_idle_healthy2720.bin
New name: idle-healthy2720_2019-08-29-13-09-21-007000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190830101943246000_idle_healthy690.bin
New name: idle-healthy690_2019-08-30-10-19-43-246000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190822171141941000_idle_healthy4766.bin
New name: idle-healthy4766_2019-08-22-17-11-41-941000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190829130921007000_idle_healthy2839.bin
New name: idle-healthy2839_2019-08-29-13-09-21-007000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190826142715591000_idle_healthy475.bin
New name: idle-healthy475_2019-08-26-14-27-15-591000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190918111351885000_idle_healthy18.bin
New name: idle-healthy18_2019-09-18-11-13-51-885000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190826153149920000_idle_healthy232.bin
New name: idle-healthy232_2019-08-26-15-31-49-920000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190822171141941000_idle_healthy3621.bin
New name: idle-healthy3621_2019-08-22-17-11-41-941000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190904100758741000_idle_healthy2060.bin
New name: idle-healthy2060_2019-09-04-10-07-58-741000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190913141526434000_workload_healthy937.bin
New name: workload-healthy937_2019-09-13-14-15-26-434000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190912131830085000_idle_healthy1073.bin
New name: idle-healthy1073_2019-09-12-13-18-30-085000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190822171141941000_idle_healthy2174.bin
New name: idle-healthy2174_2019-08-22-17-11-41-941000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190822171141941000_idle_healthy2309.bin
New name: idle-healthy2309_2019-08-22-17-11-41-941000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190913132937063000_workload_healthy384.bin
New name: workload-healthy384_2019-09-13-13-29-37-063000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190912131830085000_idle_healthy904.bin
New name: idle-healthy904_2019-09-12-13-18-30-085000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190912131830085000_idle_healthy616.bin
New name: idle-healthy616_2019-09-12-13-18-30-085000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20200123163503972000_idle_healthy.bin
New name: idle-healthy_2020-01-23-16-35-03-972000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190822140539991000_idle_healthy188.bin
New name: idle-healthy188_2019-08-22-14-05-39-991000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190826142715591000_idle_healthy384.bin
New name: idle-healthy384_2019-08-26-14-27-15-591000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190913141526434000_workload_healthy192.bin
New name: workload-healthy192_2019-09-13-14-15-26-434000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20200126230541691000_idle_healthy3.bin
New name: idle-healthy3_2020-01-26-23-05-41-691000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190918115508003000_idle_healthy29.bin
New name: idle-healthy29_2019-09-18-11-55-08-003000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190913103101063000_workload_healthy49.bin
New name: workload-healthy49_2019-09-13-10-31-01-063000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190822171141941000_idle_healthy754.bin
New name: idle-healthy754_2019-08-22-17-11-41-941000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190912122020929000_idle_healthy990.bin
New name: idle-healthy990_2019-09-12-12-20-20-929000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190829130921007000_idle_healthy1920.bin
New name: idle-healthy1920_2019-08-29-13-09-21-007000.bin
...
Processing: /home/lab/Documents/parse/AllBinaries/20190822171141941000_idle_healthy2800.bin
New name: idle-healthy2800_2019-08-22-17-11-41-941000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190912122020929000_idle_healthy31.bin
New name: idle-healthy31_2019-09-12-12-20-20-929000.bin
Processing: /home/lab/Documents/parse/AllBinaries/20190917103125052000_idle_healthy16.bin
New name: idle-healthy16_2019-09-17-10-31-25-052000.bin
Execution time: 0:00:00.989278
```

 </p>
</details>

## generateTSBinaries.py (External command - nvme-cli)
<details><summary>Click to Expand</summary>
<p>

#### Log content below.

```console
$ python generateTSBinaries.py --driveName /dev/nvme0n1 --outputDir sample-test1 --debug True --modeSelect 1 --iterations 4 --time 3
Importing Paths:  /home/lab/Documents/parse /home/lab/Documents/parse/bin /home/lab/Documents/parse/ctypeautogen
Mode is: 1
Iterations: 4
OutputDir: sample-test1
inputDir: input_binaries
Writing to: Tv2HiTAC_2020-06-23-18-33-33-106060.bin
Writing to: Tv2HiTAC_2020-06-23-18-33-33-725295.bin
Writing to: Tv2HiTAC_2020-06-23-18-33-34-358938.bin
Writing to: Tv2HiTAC_2020-06-23-18-33-34-969547.bin
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  Tv2HiTAC_2020-06-23-18-33-33-106060.bin
outpath: Tv2HiTAC_2020-06-23-18-33-33-106060

Attempting to parsing file "Tv2HiTAC_2020-06-23-18-33-33-106060.bin"...
WARNING: Special ObjectID 1000090 found in TOC at offset 2792 in data area 1

WARNING: Special ObjectID 1000220 found in TOC at offset 2824 in data area 1

WARNING: Data area 1 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Parsed binary files stored in: Tv2HiTAC_2020-06-23-18-33-33-106060
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  Tv2HiTAC_2020-06-23-18-33-33-725295.bin
outpath: Tv2HiTAC_2020-06-23-18-33-33-725295

Attempting to parsing file "Tv2HiTAC_2020-06-23-18-33-33-725295.bin"...
WARNING: Special ObjectID 1000090 found in TOC at offset 2792 in data area 1

WARNING: Special ObjectID 1000220 found in TOC at offset 2824 in data area 1

WARNING: Data area 1 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Parsed binary files stored in: Tv2HiTAC_2020-06-23-18-33-33-725295
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  Tv2HiTAC_2020-06-23-18-33-34-358938.bin
outpath: Tv2HiTAC_2020-06-23-18-33-34-358938

Attempting to parsing file "Tv2HiTAC_2020-06-23-18-33-34-358938.bin"...
WARNING: Special ObjectID 1000090 found in TOC at offset 2792 in data area 1

WARNING: Special ObjectID 1000220 found in TOC at offset 2824 in data area 1

WARNING: Data area 1 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Parsed binary files stored in: Tv2HiTAC_2020-06-23-18-33-34-358938
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  Tv2HiTAC_2020-06-23-18-33-34-969547.bin
outpath: Tv2HiTAC_2020-06-23-18-33-34-969547

Attempting to parsing file "Tv2HiTAC_2020-06-23-18-33-34-969547.bin"...
WARNING: Special ObjectID 1000090 found in TOC at offset 2792 in data area 1

WARNING: Special ObjectID 1000220 found in TOC at offset 2824 in data area 1

WARNING: Data area 1 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Parsed binary files stored in: Tv2HiTAC_2020-06-23-18-33-34-969547
Execution time of hybrid mode: 0:00:02.672209
Execution time: 0:00:02.672510

```

 </p>
</details>

## generateTSBinaries.py (Internal command - TWIDL)
<details><summary>Click to Expand</summary>
<p>

#### Log content below.

```console
$ sudo python generateTSBinaries.py --driveNumber 0 --outputDir sample-test2 --debug True --modeSelect 2 --iterations 4 --time 3
Importing Paths:  /home/lab/Documents/parse /home/lab/Documents/parse/bin /home/lab/Documents/parse/ctypeautogen
Mode is: 2
Iterations: 4
OutputDir: sample-test2
inputDir: input_binaries
Writing to: Tv2HiTAC_2020-06-23-18-36-24-530275.bin
('Importing Paths: ', '/home/lab/Documents/parse/sample-test2', '/home/lab/Documents/parse/sample-test2/bin')
Extracting telemetry log from drive 0, nvme= True, sata = False
...
Get Id information

Basic Drive Info:
=================
Drive Path:  /dev/nvme0n1
Vendor:      0x8086:0x8086
Model:       INTEL SSDPF2KX960G9
Firmware:    2CAAY242
Serial:      PHAB94220018960DGN
Bus:         NVME
Capacity:    800166076416
Max LBA:     1562824367
Product:     ARBORDALE PLUS
Assert Status: False
Get log data... 
logDrive:<telemetry_drive.logDevice object at 0x7f58200b02d0>,telemetryData=<open file 'Tv2HiTAC_2020-06-23-18-36-24-530275.bin', mode 'wb' at 0x7f58175c5ae0>,secondaryBlockSize=4096,block0Size=512,createLog=True,doubleTOCRead=False

Read Telemetry Header:
IEE OUI: 0x00 0x00 0x00
Data Area 1 End: 173
Data Area 2 End: 2132
Data Area 3 End: 3778
Controller Initiated Data Available: 0
Controller Initiated Data Generation: 0

Reason Indentifier:
Version: 1.00
Reason Code: 0, Controller Initiated: 0, Excursion Detected: 0, Warning Detected: 0, Error Detected: 0
Drive Status: HEALTHY             
Firmware Revision: 2CAAY242-000
Bootloader Revision: 2CAA        
Serial Number: PHAB94220018960DGN  

Read Telemetry data area VUHeader, offset 0x200:
Read Telemetry data area VUHeader, offset 0x15c00:
Read Telemetry data area VUHeader, offset 0x10aa00:
passed.
Writing to: Tv2HiTAC_2020-06-23-18-36-30-139774.bin
Extracting telemetry log from drive 0, nvme= True, sata = False
...
Get Id information

Basic Drive Info:
=================
Drive Path:  /dev/nvme0n1
Vendor:      0x8086:0x8086
Model:       INTEL SSDPF2KX960G9
Firmware:    2CAAY242
Serial:      PHAB94220018960DGN
Bus:         NVME
Capacity:    800166076416
Max LBA:     1562824367
Product:     ARBORDALE PLUS
Assert Status: False
Get log data... 
logDrive:<telemetry_drive.logDevice object at 0x7f5815b1b910>,telemetryData=<open file 'Tv2HiTAC_2020-06-23-18-36-30-139774.bin', mode 'wb' at 0x7f5817c2fae0>,secondaryBlockSize=4096,block0Size=512,createLog=True,doubleTOCRead=False

Read Telemetry Header:
IEE OUI: 0x00 0x00 0x00
Data Area 1 End: 173
Data Area 2 End: 2132
Data Area 3 End: 3778
Controller Initiated Data Available: 0
Controller Initiated Data Generation: 0

Reason Indentifier:
Version: 1.00
Reason Code: 0, Controller Initiated: 0, Excursion Detected: 0, Warning Detected: 0, Error Detected: 0
Drive Status: HEALTHY             
Firmware Revision: 2CAAY242-000
Bootloader Revision: 2CAA        
Serial Number: PHAB94220018960DGN  

Read Telemetry data area VUHeader, offset 0x200:
Read Telemetry data area VUHeader, offset 0x15c00:
Read Telemetry data area VUHeader, offset 0x10aa00:
passed.
Writing to: Tv2HiTAC_2020-06-23-18-36-33-080765.bin
Extracting telemetry log from drive 0, nvme= True, sata = False
...
Get Id information

Basic Drive Info:
=================
Drive Path:  /dev/nvme0n1
Vendor:      0x8086:0x8086
Model:       INTEL SSDPF2KX960G9
Firmware:    2CAAY242
Serial:      PHAB94220018960DGN
Bus:         NVME
Capacity:    800166076416
Max LBA:     1562824367
Product:     ARBORDALE PLUS
Assert Status: False
Get log data... 
logDrive:<telemetry_drive.logDevice object at 0x7f5815b25190>,telemetryData=<open file 'Tv2HiTAC_2020-06-23-18-36-33-080765.bin', mode 'wb' at 0x7f58169450c0>,secondaryBlockSize=4096,block0Size=512,createLog=True,doubleTOCRead=False

Read Telemetry Header:
IEE OUI: 0x00 0x00 0x00
Data Area 1 End: 173
Data Area 2 End: 2132
Data Area 3 End: 3778
Controller Initiated Data Available: 0
Controller Initiated Data Generation: 0

Reason Indentifier:
Version: 1.00
Reason Code: 0, Controller Initiated: 0, Excursion Detected: 0, Warning Detected: 0, Error Detected: 0
Drive Status: HEALTHY             
Firmware Revision: 2CAAY242-000
Bootloader Revision: 2CAA        
Serial Number: PHAB94220018960DGN  

Read Telemetry data area VUHeader, offset 0x200:
Read Telemetry data area VUHeader, offset 0x15c00:
Read Telemetry data area VUHeader, offset 0x10aa00:
passed.
Writing to: Tv2HiTAC_2020-06-23-18-36-36-019018.bin
Extracting telemetry log from drive 0, nvme= True, sata = False
...
Get Id information

Basic Drive Info:
=================
Drive Path:  /dev/nvme0n1
Vendor:      0x8086:0x8086
Model:       INTEL SSDPF2KX960G9
Firmware:    2CAAY242
Serial:      PHAB94220018960DGN
Bus:         NVME
Capacity:    800166076416
Max LBA:     1562824367
Product:     ARBORDALE PLUS
Assert Status: False
Get log data... 
logDrive:<telemetry_drive.logDevice object at 0x7f58150d7390>,telemetryData=<open file 'Tv2HiTAC_2020-06-23-18-36-36-019018.bin', mode 'wb' at 0x7f5815013c90>,secondaryBlockSize=4096,block0Size=512,createLog=True,doubleTOCRead=False

Read Telemetry Header:
IEE OUI: 0x00 0x00 0x00
Data Area 1 End: 173
Data Area 2 End: 2132
Data Area 3 End: 3778
Controller Initiated Data Available: 0
Controller Initiated Data Generation: 0

Reason Indentifier:
Version: 1.00
Reason Code: 0, Controller Initiated: 0, Excursion Detected: 0, Warning Detected: 0, Error Detected: 0
Drive Status: HEALTHY             
Firmware Revision: 2CAAY242-000
Bootloader Revision: 2CAA        
Serial Number: PHAB94220018960DGN  

Read Telemetry data area VUHeader, offset 0x200:
Read Telemetry data area VUHeader, offset 0x15c00:
Read Telemetry data area VUHeader, offset 0x10aa00:
passed.
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  Tv2HiTAC_2020-06-23-18-36-24-530275.bin
outpath: Tv2HiTAC_2020-06-23-18-36-24-530275

Attempting to parsing file "Tv2HiTAC_2020-06-23-18-36-24-530275.bin"...
WARNING: Special ObjectID 1000090 found in TOC at offset 2792 in data area 1

WARNING: Special ObjectID 1000220 found in TOC at offset 2824 in data area 1

WARNING: Data area 1 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Parsed binary files stored in: Tv2HiTAC_2020-06-23-18-36-24-530275
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  Tv2HiTAC_2020-06-23-18-36-30-139774.bin
outpath: Tv2HiTAC_2020-06-23-18-36-30-139774

Attempting to parsing file "Tv2HiTAC_2020-06-23-18-36-30-139774.bin"...
WARNING: Special ObjectID 1000090 found in TOC at offset 2792 in data area 1

WARNING: Special ObjectID 1000220 found in TOC at offset 2824 in data area 1

WARNING: Data area 1 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Parsed binary files stored in: Tv2HiTAC_2020-06-23-18-36-30-139774
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  Tv2HiTAC_2020-06-23-18-36-33-080765.bin
outpath: Tv2HiTAC_2020-06-23-18-36-33-080765

Attempting to parsing file "Tv2HiTAC_2020-06-23-18-36-33-080765.bin"...
WARNING: Special ObjectID 1000090 found in TOC at offset 2792 in data area 1

WARNING: Special ObjectID 1000220 found in TOC at offset 2824 in data area 1

WARNING: Data area 1 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Parsed binary files stored in: Tv2HiTAC_2020-06-23-18-36-33-080765
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  Tv2HiTAC_2020-06-23-18-36-36-019018.bin
outpath: Tv2HiTAC_2020-06-23-18-36-36-019018

Attempting to parsing file "Tv2HiTAC_2020-06-23-18-36-36-019018.bin"...
WARNING: Special ObjectID 1000090 found in TOC at offset 2792 in data area 1

WARNING: Special ObjectID 1000220 found in TOC at offset 2824 in data area 1

WARNING: Data area 1 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Parsed binary files stored in: Tv2HiTAC_2020-06-23-18-36-36-019018
Execution time of internal mode: 0:00:14.649553
Execution time: 0:00:14.649845

```

 </p>
</details>

## generateTSBinaries.py (Parse-only)
<details><summary>Click to Expand</summary>
<p>

#### Log content below.

```console
$ python generateTSBinaries.py --outputDir workload-fail --inputDir ../test_t/AllBinaries/workload_fail --debug True --modeSelect 3 --iterations 10
Importing Paths:  /home/lab/Documents/parse /home/lab/Documents/parse/bin /home/lab/Documents/parse/ctypeautogen
Mode is: 3
Iterations: 10
OutputDir: workload-fail
inputDir: ../test_t/AllBinaries/workload_fail
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  /home/lab/Documents/parse/../test_t/AllBinaries/workload_fail/workload-fail0_2019-09-13-15-52-30-327000.bin
outpath: workload-fail/workload-fail0_2019-09-13-15-52-30-327000

Attempting to parsing file "/home/lab/Documents/parse/../test_t/AllBinaries/workload_fail/workload-fail0_2019-09-13-15-52-30-327000.bin"...
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 55, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 56, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 57, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 58, Data area: 3
WARNING: Data area 3 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Parsed binary files stored in: workload-fail/workload-fail0_2019-09-13-15-52-30-327000
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  /home/lab/Documents/parse/../test_t/AllBinaries/workload_fail/workload-fail1_2019-09-13-15-52-30-327000.bin
outpath: workload-fail/workload-fail1_2019-09-13-15-52-30-327000

Attempting to parsing file "/home/lab/Documents/parse/../test_t/AllBinaries/workload_fail/workload-fail1_2019-09-13-15-52-30-327000.bin"...
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 55, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 56, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 57, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 58, Data area: 3
WARNING: Data area 3 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Parsed binary files stored in: workload_fail/workload-fail1_2019-09-13-15-52-30-327000
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  /home/lab/Documents/parse/../test_t/AllBinaries/workload_fail/workload-fail2_2019-09-13-15-52-30-327000.bin
outpath: workload-fail/workload-fail2_2019-09-13-15-52-30-327000

Attempting to parsing file "/home/lab/Documents/parse/../test_t/AllBinaries/workload_fail/workload-fail2_2019-09-13-15-52-30-327000.bin"...
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 55, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 56, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 57, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 58, Data area: 3
WARNING: Data area 3 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Parsed binary files stored in: workload-fail/workload-fail2_2019-09-13-15-52-30-327000
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  /home/lab/Documents/parse/../test_t/AllBinaries/workload_fail/workload-fail3_2019-09-13-15-52-30-327000.bin
outpath: workload-fail/workload-fail3_2019-09-13-15-52-30-327000

Attempting to parsing file "/home/lab/Documents/parse/../test_t/AllBinaries/workload_fail/workload-fail3_2019-09-13-15-52-30-327000.bin"...
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 55, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 56, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 57, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 58, Data area: 3
WARNING: Data area 3 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Parsed binary files stored in: workload-fail/workload-fail3_2019-09-13-15-52-30-327000
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  /home/lab/Documents/parse/../test_t/AllBinaries/workload_fail/workload-fail4_2019-09-13-15-52-30-327000.bin
outpath: workload-fail/workload-fail4_2019-09-13-15-52-30-327000

Attempting to parsing file "/home/lab/Documents/parse/../test_t/AllBinaries/workload_fail/workload-fail4_2019-09-13-15-52-30-327000.bin"...
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 55, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 56, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 57, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 58, Data area: 3
WARNING: Data area 3 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Parsed binary files stored in: workload-fail/workload-fail4_2019-09-13-15-52-30-327000
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  /home/lab/Documents/parse/../test_t/AllBinaries/workload_fail/workload-fail5_2019-09-13-15-52-30-327000.bin
outpath: workload-fail/workload-fail5_2019-09-13-15-52-30-327000

Attempting to parsing file "/home/lab/Documents/parse/../test_t/AllBinaries/workload_fail/workload-fail5_2019-09-13-15-52-30-327000.bin"...
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 55, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 56, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 57, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 58, Data area: 3
WARNING: Data area 3 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Parsed binary files stored in: workload-fail/workload-fail5_2019-09-13-15-52-30-327000
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  /home/lab/Documents/parse/../test_t/AllBinaries/workload_fail/workload-fail6_2019-09-13-15-52-30-327000.bin
outpath: workload-fail/workload-fail6_2019-09-13-15-52-30-327000

Attempting to parsing file "/home/lab/Documents/parse/../test_t/AllBinaries/workload_fail/workload-fail6_2019-09-13-15-52-30-327000.bin"...
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 55, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 56, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 57, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 58, Data area: 3
WARNING: Data area 3 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Parsed binary files stored in: workload-fail/workload-fail6_2019-09-13-15-52-30-327000
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  /home/lab/Documents/parse/../test_t/AllBinaries/workload_fail/workload-fail7_2019-09-13-15-52-30-327000.bin
outpath: workload-fail/workload-fail7_2019-09-13-15-52-30-327000

Attempting to parsing file "/home/lab/Documents/parse/../test_t/AllBinaries/workload_fail/workload-fail7_2019-09-13-15-52-30-327000.bin"...
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 55, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 56, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 57, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 58, Data area: 3
WARNING: Data area 3 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Parsed binary files stored in: workload-fail/workload-fail7_2019-09-13-15-52-30-327000
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  /home/lab/Documents/parse/../test_t/AllBinaries/workload_fail/workload-fail8_2019-09-13-15-52-30-327000.bin
outpath: workload-fail/workload-fail8_2019-09-13-15-52-30-327000

Attempting to parsing file "/home/lab/Documents/parse/../test_t/AllBinaries/workload_fail/workload-fail8_2019-09-13-15-52-30-327000.bin"...
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 55, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 56, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 57, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 58, Data area: 3
WARNING: Data area 3 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Parsed binary files stored in: workload_fail/workload-fail8_2019-09-13-15-52-30-327000
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  /home/lab/Documents/parse/../test_t/AllBinaries/workload_fail/workload-fail9_2019-09-13-15-52-30-327000.bin
outpath: workload-fail/workload-fail9_2019-09-13-15-52-30-327000

Attempting to parsing file "/home/lab/Documents/parse/../test_t/AllBinaries/workload_fail/workload-fail9_2019-09-13-15-52-30-327000.bin"...
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid TOC entry offset 0 < minimum offset 24
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 55, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 56, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 57, Data area: 3
WARNING: Invalid entry found TOC offset: 0x0, TOC size: 0, TOC entry: 58, Data area: 3
WARNING: Data area 3 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Parsed binary files stored in: workload-fail/workload-fail9_2019-09-13-15-52-30-327000
Execution time of parse-only mode: 0:00:00.228295
Execution time: 0:00:00.228579

```

 </p>
</details>

## generateTSBinaries.py (intelmas)
<details><summary>Click to Expand</summary>
<p>

#### Log content below.

```console
$ sudo python generateTSBinaries.py --driveNumber 0 --outputDir sample-test3 --debug True --modeSelect 4 --iterations 4 --time 60
Importing Paths:  /home/lab/Documents/parse /home/lab/Documents/parse/bin /home/lab/Documents/parse/ctypeautogen
Mode is: 4
Iterations: 4
OutputDir: sample-test3
inputDir: input-binaries
Writing to: sample-test3/Tv2HiTAC_2020-06-29-23-31-29-572661.bin
Writing to: sample-test3/Tv2HiTAC_2020-06-29-23-31-30-611357.bin
Writing to: sample-test3/Tv2HiTAC_2020-06-29-23-31-31-754634.bin
Writing to: sample-test3/Tv2HiTAC_2020-06-29-23-31-32-826380.bin
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  sample-test3/Tv2HiTAC_2020-06-29-23-31-29-572661.bin
outpath: sample-test3/Tv2HiTAC_2020-06-29-23-31-29-572661

Attempting to parsing file "sample-test3/Tv2HiTAC_2020-06-29-23-31-29-572661.bin"...
WARNING: Special ObjectID 1000090 found in TOC at offset 2572 in data area 1

WARNING: Special ObjectID 1000220 found in TOC at offset 2604 in data area 1

WARNING: Data area 1 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Printing Split Binary Objects...
Read Data Area 1 at byte 512 of size 91136

Read Data Area 2 at byte 91648 of size 892928

Read Data Area 3 at byte 984576 of size 680960

uidInfoDict contains the following uids:
 ['1', '10', '1000090', '1000220', '109', '2', '20', '225', '247', '248', '252', '253', '254', '258', '259', '260', '261', '262', '263', '264', '265', '266', '267', '268', '269', '270', '271', '272', '273', '274', '275', '276', '277', '278', '279', '280', '281', '282', '283', '284', '285', '286', '287', '288', '290', '291', '296', '297', '313', '314', '315', '316', '317', '318', '319', '320', '321', '322', '323', '324', '325', '326', '327', '328', '329', '330', '331', '332', '333', '334', '335', '336', '337', '338', '339', '340', '341', '342', '343', '344', '345', '346', '347', '348', '349', '350', '351', '352', '353', '354', '355', '356', '41', '44', '45', '46', '47', '48', '49', '5', '50', '51', '52', '54', '55', '56', '57', '58', '6', '8', '86', '88', '89']

Parsed binary files stored in: sample-test3/Tv2HiTAC_2020-06-29-23-31-29-572661
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  sample-test3/Tv2HiTAC_2020-06-29-23-31-30-611357.bin
outpath: sample-test3/Tv2HiTAC_2020-06-29-23-31-30-611357

Attempting to parsing file "sample-test3/Tv2HiTAC_2020-06-29-23-31-30-611357.bin"...
WARNING: Special ObjectID 1000090 found in TOC at offset 2572 in data area 1

WARNING: Special ObjectID 1000220 found in TOC at offset 2604 in data area 1

WARNING: Data area 1 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Printing Split Binary Objects...
Read Data Area 1 at byte 512 of size 91136

Read Data Area 2 at byte 91648 of size 892928

Read Data Area 3 at byte 984576 of size 680960

uidInfoDict contains the following uids:
 ['1', '10', '1000090', '1000220', '109', '2', '20', '225', '247', '248', '252', '253', '254', '258', '259', '260', '261', '262', '263', '264', '265', '266', '267', '268', '269', '270', '271', '272', '273', '274', '275', '276', '277', '278', '279', '280', '281', '282', '283', '284', '285', '286', '287', '288', '290', '291', '296', '297', '313', '314', '315', '316', '317', '318', '319', '320', '321', '322', '323', '324', '325', '326', '327', '328', '329', '330', '331', '332', '333', '334', '335', '336', '337', '338', '339', '340', '341', '342', '343', '344', '345', '346', '347', '348', '349', '350', '351', '352', '353', '354', '355', '356', '41', '44', '45', '46', '47', '48', '49', '5', '50', '51', '52', '54', '55', '56', '57', '58', '6', '8', '86', '88', '89']

Parsed binary files stored in: sample-test3/Tv2HiTAC_2020-06-29-23-31-30-611357
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  sample-test3/Tv2HiTAC_2020-06-29-23-31-31-754634.bin
outpath: sample-test3/Tv2HiTAC_2020-06-29-23-31-31-754634

Attempting to parsing file "sample-test3/Tv2HiTAC_2020-06-29-23-31-31-754634.bin"...
WARNING: Special ObjectID 1000090 found in TOC at offset 2572 in data area 1

WARNING: Special ObjectID 1000220 found in TOC at offset 2604 in data area 1

WARNING: Data area 1 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Printing Split Binary Objects...
Read Data Area 1 at byte 512 of size 91136

Read Data Area 2 at byte 91648 of size 892928

Read Data Area 3 at byte 984576 of size 680960

uidInfoDict contains the following uids:
 ['1', '10', '1000090', '1000220', '109', '2', '20', '225', '247', '248', '252', '253', '254', '258', '259', '260', '261', '262', '263', '264', '265', '266', '267', '268', '269', '270', '271', '272', '273', '274', '275', '276', '277', '278', '279', '280', '281', '282', '283', '284', '285', '286', '287', '288', '290', '291', '296', '297', '313', '314', '315', '316', '317', '318', '319', '320', '321', '322', '323', '324', '325', '326', '327', '328', '329', '330', '331', '332', '333', '334', '335', '336', '337', '338', '339', '340', '341', '342', '343', '344', '345', '346', '347', '348', '349', '350', '351', '352', '353', '354', '355', '356', '41', '44', '45', '46', '47', '48', '49', '5', '50', '51', '52', '54', '55', '56', '57', '58', '6', '8', '86', '88', '89']

Parsed binary files stored in: sample-test3/Tv2HiTAC_2020-06-29-23-31-31-754634
DEBUG: If this fails, try checking that the telemetry file you input is from the correct drive and type (NVMe vs SATA)


infile:  sample-test3/Tv2HiTAC_2020-06-29-23-31-32-826380.bin
outpath: sample-test3/Tv2HiTAC_2020-06-29-23-31-32-826380

Attempting to parsing file "sample-test3/Tv2HiTAC_2020-06-29-23-31-32-826380.bin"...
WARNING: Special ObjectID 1000090 found in TOC at offset 2572 in data area 1

WARNING: Special ObjectID 1000220 found in TOC at offset 2604 in data area 1

WARNING: Data area 1 validity check failed
Phase 2 Parse (does nothing yet)
Passed!!!!
File Format: <Serial Number> <Core (Optional)> <eUID> <Major> <Minor> <Known GHS Firmware Variable Name> <Byte Size>
Printing Split Binary Objects...
Read Data Area 1 at byte 512 of size 91136

Read Data Area 2 at byte 91648 of size 892928

Read Data Area 3 at byte 984576 of size 680960

uidInfoDict contains the following uids:
 ['1', '10', '1000090', '1000220', '109', '2', '20', '225', '247', '248', '252', '253', '254', '258', '259', '260', '261', '262', '263', '264', '265', '266', '267', '268', '269', '270', '271', '272', '273', '274', '275', '276', '277', '278', '279', '280', '281', '282', '283', '284', '285', '286', '287', '288', '290', '291', '296', '297', '313', '314', '315', '316', '317', '318', '319', '320', '321', '322', '323', '324', '325', '326', '327', '328', '329', '330', '331', '332', '333', '334', '335', '336', '337', '338', '339', '340', '341', '342', '343', '344', '345', '346', '347', '348', '349', '350', '351', '352', '353', '354', '355', '356', '41', '44', '45', '46', '47', '48', '49', '5', '50', '51', '52', '54', '55', '56', '57', '58', '6', '8', '86', '88', '89']

Parsed binary files stored in: sample-test3/Tv2HiTAC_2020-06-29-23-31-32-826380
Execution time of intelmas mode: 0:00:04.470647
Execution time: 0:00:04.470939
```

 </p>
</details>

## formatTSFiles.py
<details><summary>Click to Expand</summary>
<p>

#### Log content below.

```console
$ python formatTSFiles.py --outfile workload-fail.ini --outpath ./workload-fail-txt --targetObject ThermalSensor --fwDir ./arbordaleplus_t2 --binDir ./workload-fail --debug True
Folder: /home/lab/Documents/parse/./workload-fail
Generating: /home/lab/Documents/parse/workload-fail/workload-fail0_2019-09-13-15-52-30-327000

Project Directory: /home/lab/Documents/parse/arbordaleplus_t2

Bin Files Directory: /home/lab/Documents/parse/workload-fail/workload-fail0_2019-09-13-15-52-30-327000

Creating Telemetry Objects from Binaries...
binFile:  BTLJ732600A41P0FGN.54.13.3.Defrag_ForcedReloQ.8.1.1.bin
binFile:  BTLJ732600A41P0FGN.169.3.0.pssRegs.88.1.0.bin
binFile:  BTLJ732600A41P0FGN.287.1.0.NLOG_OPAL.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.58.7.2.fConfigInfoTable.4016.2.1.bin
binFile:  BTLJ732600A41P0FGN.265.1.0.NLOG_10D.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.2.1.0.BlSideTrace.131072.3.0.bin
binFile:  BTLJ732600A41P0FGN.48.13.3.Defrag_WearLevelQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.51.13.3.Defrag_HistoricDustMixRate.44.1.1.bin
binFile:  BTLJ732600A41P0FGN.57.14.1.NandDiscovery.3576.2.0.bin
binFile:  BTLJ732600A41P0FGN.284.1.0.NLOG_NEI.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.1.0.bin
binFile:  BTLJ732600A41P0FGN.278.1.0.NLOG_RARE.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA3.txt
binFile:  BTLJ732600A41P0FGN.281.1.0.NLOG_UEC.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.265.1.0.NLOG_10D.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.263.1.0.NLOG_TEMP.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.3.0.bin
binFile:  BTLJ732600A41P0FGN.64.17.17.PliRestoreFooter.29184.2.0.bin
binFile:  BTLJ732600A41P0FGN.267.1.0.NLOG_BG.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.5.9.0.bis.1024.1.0.bin
binFile:  BTLJ732600A41P0FGN.41.5.1.DefragHistory.36300.2.0.bin
binFile:  BTLJ732600A41P0FGN.56.4.1.writeLatencyStats.4864.1.1.bin
binFile:  BTLJ732600A41P0FGN.9.1.1.LLFState.84.2.1.bin
binFile:  BTLJ732600A41P0FGN.280.1.0.NLOG_MRRf.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.258.5.1.DefragHistoryPart.4096.1.1.bin
binFile:  BTLJ732600A41P0FGN.261.1.0.NLOG_TC.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.284.1.0.NLOG_NEI.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.266.1.0.NLOG_HOST.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.271.1.0.NLOG_PLI.320.1.1.bin
binFile:  BTLJ732600A41P0FGN.61.29.4.PliRestoreHeader.51712.2.1.bin
binFile:  BTLJ732600A41P0FGN.270.1.0.NLOG_ERROR.1088.1.0.bin
binFile:  BTLJ732600A41P0FGN.286.1.0.NLOG_VAL.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.20.1.0.NplCmdStateInfo.96.1.0.bin
binFile:  BTLJ732600A41P0FGN.57.14.1.NandDiscovery.3576.2.1.bin
binFile:  BTLJ732600A41P0FGN.258.5.1.DefragHistoryPart.4096.1.0.bin
binFile:  BTLJ732600A41P0FGN.88.52.25.Stats.4096.2.0.bin
binFile:  BTLJ732600A41P0FGN.273.1.0.NLOG_STATS.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.264.1.0.NLOG_15M.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.288.1.0.NLOG_IRQ.320.3.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA2.txt
binFile:  BTLJ732600A41P0FGN.288.1.0.NLOG_IRQ.320.3.1.bin
binFile:  BTLJ732600A41P0FGN.255.1.0.NplMailboxState.32768.1.0.bin
binFile:  BTLJ732600A41P0FGN.169.3.0.pssRegs.88.2.0.bin
binFile:  BTLJ732600A41P0FGN.275.1.0.NLOG_HFR.4160.3.1.bin
binFile:  BTLJ732600A41P0FGN.250.1.0.BridgeStatus.12.1.0.bin
binFile:  BTLJ732600A41P0FGN.272.1.0.NLOG_IBM.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.282.1.0.NLOG_TRIM.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.45.13.3.Defrag_DustingQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN_NLOG_FILE_LIST.txt
binFile:  BTLJ732600A41P0FGN.281.1.0.NLOG_UEC.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.289.1.0.NplMailboxRegisters.284.2.0.bin
binFile:  BTLJ732600A41P0FGN.86.1.0.mrr_log.16128.2.0.bin
binFile:  BTLJ732600A41P0FGN.47.13.3.Defrag_WAQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.274.1.0.NLOG_TSTATS.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.49.13.3.DefragInfo.124.1.0.bin
binFile:  BTLJ732600A41P0FGN.61.29.4.PliRestoreHeader.51712.2.0.bin
binFile:  BTLJ732600A41P0FGN.277.1.0.NLOG_WARN.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.55.4.1.readLatencyStats.4864.1.0.bin
binFile:  BTLJ732600A41P0FGN.269.1.0.NLOG_SYS.576.1.1.bin
binFile:  BTLJ732600A41P0FGN.283.1.0.NLOG_MRRs.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.291.1.0.powerGov_Sysparam.224.2.0.bin
binFile:  BTLJ732600A41P0FGN.271.1.0.NLOG_PLI.320.1.0.bin
binFile:  BTLJ732600A41P0FGN.54.13.3.Defrag_ForcedReloQ.8.1.0.bin
binFile:  BTLJ732600A41P0FGN.89.1.0.mrr_state.768.2.0.bin
binFile:  BTLJ732600A41P0FGN.272.1.0.NLOG_IBM.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.DataArea3.bin
binFile:  BTLJ732600A41P0FGN.286.1.0.NLOG_VAL.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.269.1.0.NLOG_SYS.576.1.0.bin
binFile:  BTLJ732600A41P0FGN.283.1.0.NLOG_MRRs.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.276.1.0.NLOG_EHOST.2112.1.1.bin
binFile:  BTLJ732600A41P0FGN.282.1.0.NLOG_TRIM.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.50.13.3.Defrag_BandsDoneQueue.44.1.1.bin
binFile:  BTLJ732600A41P0FGN.274.1.0.NLOG_TSTATS.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.44.13.3.DefragInfoSlow.152.1.1.bin
binFile:  BTLJ732600A41P0FGN.275.1.0.NLOG_HFR.4160.3.0.bin
binFile:  BTLJ732600A41P0FGN.277.1.0.NLOG_WARN.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.260.1.0.NLOG_TEST.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.268.1.0.NLOG_UNIQUE.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.50.13.3.Defrag_BandsDoneQueue.44.1.0.bin
binFile:  BTLJ732600A41P0FGN.109.1.0.mrr_status.152832.2.0.bin
binFile:  BTLJ732600A41P0FGN.46.13.3.Defrag_LockedQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.56.4.1.writeLatencyStats.4864.1.0.bin
binFile:  BTLJ732600A41P0FGN.259.1.0.NLOG_ID.192.3.1.bin
binFile:  BTLJ732600A41P0FGN.259.1.0.NLOG_ID.192.3.0.bin
binFile:  BTLJ732600A41P0FGN.285.1.0.NLOG_DM.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.17.1.0.pssDebugTrace.528.2.0.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.2.0.bin
binFile:  BTLJ732600A41P0FGN.6.11.1.ThermalSensor.4740.2.0.bin
binFile:  BTLJ732600A41P0FGN.46.13.3.Defrag_LockedQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.278.1.0.NLOG_RARE.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.263.1.0.NLOG_TEMP.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.280.1.0.NLOG_MRRf.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.260.1.0.NLOG_TEST.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.DataArea2.bin
binFile:  BTLJ732600A41P0FGN.10.1.0.initState.48.2.0.bin
binFile:  BTLJ732600A41P0FGN.rc
binFile:  BTLJ732600A41P0FGN.257.1.0.NplSQueueRegisters.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.285.1.0.NLOG_DM.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.273.1.0.NLOG_STATS.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.251.1.0.nplInfoState.32.1.0.bin
binFile:  BTLJ732600A41P0FGN.225.1.0.InitStateCoreSync.12.2.0.bin
binFile:  BTLJ732600A41P0FGN.9.1.1.LLFState.84.2.0.bin
binFile:  BTLJ732600A41P0FGN.55.4.1.readLatencyStats.4864.1.1.bin
binFile:  BTLJ732600A41P0FGN.268.1.0.NLOG_UNIQUE.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.45.13.3.Defrag_DustingQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.44.13.3.DefragInfoSlow.152.1.0.bin
binFile:  BTLJ732600A41P0FGN.256.1.0.NplCQueueRegisters.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.279.1.0.NLOG_THERM.320.3.0.bin
binFile:  BTLJ732600A41P0FGN.88.52.25.Stats.4096.2.1.bin
binFile:  BTLJ732600A41P0FGN.225.1.0.InitStateCoreSync.12.2.1.bin
binFile:  BTLJ732600A41P0FGN.247.1.0.nvmeFeatures.56.1.0.bin
binFile:  BTLJ732600A41P0FGN.266.1.0.NLOG_HOST.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.267.1.0.NLOG_BG.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.254.1.0.qMgrSQList.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.52.1.2.DefragStateCounters.20.1.0.bin
binFile:  BTLJ732600A41P0FGN.51.13.3.Defrag_HistoricDustMixRate.44.1.0.bin
binFile:  BTLJ732600A41P0FGN.261.1.0.NLOG_TC.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.49.13.3.DefragInfo.124.1.1.bin
binFile:  BTLJ732600A41P0FGN.276.1.0.NLOG_EHOST.2112.1.0.bin
binFile:  BTLJ732600A41P0FGN.287.1.0.NLOG_OPAL.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.262.1.0.NLOG_DEBUG.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.64.17.17.PliRestoreFooter.29184.2.1.bin
binFile:  BTLJ732600A41P0FGN.264.1.0.NLOG_15M.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.41.5.1.DefragHistory.36300.2.1.bin
binFile:  BTLJ732600A41P0FGN.10.1.0.initState.48.2.1.bin
binFile:  BTLJ732600A41P0FGN.17.1.0.pssDebugTrace.528.1.0.bin
binFile:  BTLJ732600A41P0FGN.48.13.3.Defrag_WearLevelQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.1.1.0.FwSideTrace.131072.3.0.bin
binFile:  BTLJ732600A41P0FGN.DataArea1.bin
binFile:  BTLJ732600A41P0FGN.290.1.0.powerGov_Fconfig.188.2.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA1.txt
binFile:  BTLJ732600A41P0FGN.262.1.0.NLOG_DEBUG.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.270.1.0.NLOG_ERROR.1088.1.1.bin
binFile:  BTLJ732600A41P0FGN.8.11.1.ThermalStats.1024.2.0.bin
binFile:  BTLJ732600A41P0FGN.252.1.0.qMgrCQList.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.52.1.2.DefragStateCounters.20.1.1.bin
binFile:  BTLJ732600A41P0FGN.58.7.2.fConfigInfoTable.4016.2.0.bin
binFile:  BTLJ732600A41P0FGN.47.13.3.Defrag_WAQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.279.1.0.NLOG_THERM.320.3.1.bin
binFile:  BTLJ732600A41P0FGN.297.7.2.fConfigStream.3072.2.0.bin
binFile:  BTLJ732600A41P0FGN.297.7.2.fConfigStream.3072.2.1.bin
Generating: /home/lab/Documents/parse/workload-fail/workload-fail1_2019-09-13-15-52-30-327000

Project Directory: /home/lab/Documents/parse/arbordaleplus_t2

Bin Files Directory: /home/lab/Documents/parse/workload-fail/workload-fail1_2019-09-13-15-52-30-327000

Creating Telemetry Objects from Binaries...
binFile:  BTLJ732600A41P0FGN.54.13.3.Defrag_ForcedReloQ.8.1.1.bin
binFile:  BTLJ732600A41P0FGN.169.3.0.pssRegs.88.1.0.bin
binFile:  BTLJ732600A41P0FGN.287.1.0.NLOG_OPAL.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.58.7.2.fConfigInfoTable.4016.2.1.bin
binFile:  BTLJ732600A41P0FGN.265.1.0.NLOG_10D.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.2.1.0.BlSideTrace.131072.3.0.bin
binFile:  BTLJ732600A41P0FGN.48.13.3.Defrag_WearLevelQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.51.13.3.Defrag_HistoricDustMixRate.44.1.1.bin
binFile:  BTLJ732600A41P0FGN.57.14.1.NandDiscovery.3576.2.0.bin
binFile:  BTLJ732600A41P0FGN.284.1.0.NLOG_NEI.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.1.0.bin
binFile:  BTLJ732600A41P0FGN.278.1.0.NLOG_RARE.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA3.txt
binFile:  BTLJ732600A41P0FGN.281.1.0.NLOG_UEC.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.265.1.0.NLOG_10D.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.263.1.0.NLOG_TEMP.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.3.0.bin
binFile:  BTLJ732600A41P0FGN.64.17.17.PliRestoreFooter.29184.2.0.bin
binFile:  BTLJ732600A41P0FGN.267.1.0.NLOG_BG.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.5.9.0.bis.1024.1.0.bin
binFile:  BTLJ732600A41P0FGN.41.5.1.DefragHistory.36300.2.0.bin
binFile:  BTLJ732600A41P0FGN.56.4.1.writeLatencyStats.4864.1.1.bin
binFile:  BTLJ732600A41P0FGN.9.1.1.LLFState.84.2.1.bin
binFile:  BTLJ732600A41P0FGN.280.1.0.NLOG_MRRf.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.258.5.1.DefragHistoryPart.4096.1.1.bin
binFile:  BTLJ732600A41P0FGN.261.1.0.NLOG_TC.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.284.1.0.NLOG_NEI.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.266.1.0.NLOG_HOST.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.271.1.0.NLOG_PLI.320.1.1.bin
binFile:  BTLJ732600A41P0FGN.61.29.4.PliRestoreHeader.51712.2.1.bin
binFile:  BTLJ732600A41P0FGN.270.1.0.NLOG_ERROR.1088.1.0.bin
binFile:  BTLJ732600A41P0FGN.286.1.0.NLOG_VAL.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.20.1.0.NplCmdStateInfo.96.1.0.bin
binFile:  BTLJ732600A41P0FGN.57.14.1.NandDiscovery.3576.2.1.bin
binFile:  BTLJ732600A41P0FGN.258.5.1.DefragHistoryPart.4096.1.0.bin
binFile:  BTLJ732600A41P0FGN.88.52.25.Stats.4096.2.0.bin
binFile:  BTLJ732600A41P0FGN.273.1.0.NLOG_STATS.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.264.1.0.NLOG_15M.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.288.1.0.NLOG_IRQ.320.3.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA2.txt
binFile:  BTLJ732600A41P0FGN.288.1.0.NLOG_IRQ.320.3.1.bin
binFile:  BTLJ732600A41P0FGN.255.1.0.NplMailboxState.32768.1.0.bin
binFile:  BTLJ732600A41P0FGN.169.3.0.pssRegs.88.2.0.bin
binFile:  BTLJ732600A41P0FGN.275.1.0.NLOG_HFR.4160.3.1.bin
binFile:  BTLJ732600A41P0FGN.250.1.0.BridgeStatus.12.1.0.bin
binFile:  BTLJ732600A41P0FGN.272.1.0.NLOG_IBM.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.282.1.0.NLOG_TRIM.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.45.13.3.Defrag_DustingQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN_NLOG_FILE_LIST.txt
binFile:  BTLJ732600A41P0FGN.281.1.0.NLOG_UEC.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.289.1.0.NplMailboxRegisters.284.2.0.bin
binFile:  BTLJ732600A41P0FGN.86.1.0.mrr_log.16128.2.0.bin
binFile:  BTLJ732600A41P0FGN.47.13.3.Defrag_WAQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.274.1.0.NLOG_TSTATS.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.49.13.3.DefragInfo.124.1.0.bin
binFile:  BTLJ732600A41P0FGN.61.29.4.PliRestoreHeader.51712.2.0.bin
binFile:  BTLJ732600A41P0FGN.277.1.0.NLOG_WARN.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.55.4.1.readLatencyStats.4864.1.0.bin
binFile:  BTLJ732600A41P0FGN.269.1.0.NLOG_SYS.576.1.1.bin
binFile:  BTLJ732600A41P0FGN.283.1.0.NLOG_MRRs.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.291.1.0.powerGov_Sysparam.224.2.0.bin
binFile:  BTLJ732600A41P0FGN.271.1.0.NLOG_PLI.320.1.0.bin
binFile:  BTLJ732600A41P0FGN.54.13.3.Defrag_ForcedReloQ.8.1.0.bin
binFile:  BTLJ732600A41P0FGN.89.1.0.mrr_state.768.2.0.bin
binFile:  BTLJ732600A41P0FGN.272.1.0.NLOG_IBM.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.DataArea3.bin
binFile:  BTLJ732600A41P0FGN.286.1.0.NLOG_VAL.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.269.1.0.NLOG_SYS.576.1.0.bin
binFile:  BTLJ732600A41P0FGN.283.1.0.NLOG_MRRs.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.276.1.0.NLOG_EHOST.2112.1.1.bin
binFile:  BTLJ732600A41P0FGN.282.1.0.NLOG_TRIM.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.50.13.3.Defrag_BandsDoneQueue.44.1.1.bin
binFile:  BTLJ732600A41P0FGN.274.1.0.NLOG_TSTATS.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.44.13.3.DefragInfoSlow.152.1.1.bin
binFile:  BTLJ732600A41P0FGN.275.1.0.NLOG_HFR.4160.3.0.bin
binFile:  BTLJ732600A41P0FGN.277.1.0.NLOG_WARN.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.260.1.0.NLOG_TEST.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.268.1.0.NLOG_UNIQUE.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.50.13.3.Defrag_BandsDoneQueue.44.1.0.bin
binFile:  BTLJ732600A41P0FGN.109.1.0.mrr_status.152832.2.0.bin
binFile:  BTLJ732600A41P0FGN.46.13.3.Defrag_LockedQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.56.4.1.writeLatencyStats.4864.1.0.bin
binFile:  BTLJ732600A41P0FGN.259.1.0.NLOG_ID.192.3.1.bin
binFile:  BTLJ732600A41P0FGN.259.1.0.NLOG_ID.192.3.0.bin
binFile:  BTLJ732600A41P0FGN.285.1.0.NLOG_DM.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.17.1.0.pssDebugTrace.528.2.0.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.2.0.bin
binFile:  BTLJ732600A41P0FGN.6.11.1.ThermalSensor.4740.2.0.bin
binFile:  BTLJ732600A41P0FGN.46.13.3.Defrag_LockedQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.278.1.0.NLOG_RARE.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.263.1.0.NLOG_TEMP.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.280.1.0.NLOG_MRRf.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.260.1.0.NLOG_TEST.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.DataArea2.bin
binFile:  BTLJ732600A41P0FGN.10.1.0.initState.48.2.0.bin
binFile:  BTLJ732600A41P0FGN.rc
binFile:  BTLJ732600A41P0FGN.257.1.0.NplSQueueRegisters.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.285.1.0.NLOG_DM.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.273.1.0.NLOG_STATS.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.251.1.0.nplInfoState.32.1.0.bin
binFile:  BTLJ732600A41P0FGN.225.1.0.InitStateCoreSync.12.2.0.bin
binFile:  BTLJ732600A41P0FGN.9.1.1.LLFState.84.2.0.bin
binFile:  BTLJ732600A41P0FGN.55.4.1.readLatencyStats.4864.1.1.bin
binFile:  BTLJ732600A41P0FGN.268.1.0.NLOG_UNIQUE.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.45.13.3.Defrag_DustingQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.44.13.3.DefragInfoSlow.152.1.0.bin
binFile:  BTLJ732600A41P0FGN.256.1.0.NplCQueueRegisters.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.279.1.0.NLOG_THERM.320.3.0.bin
binFile:  BTLJ732600A41P0FGN.88.52.25.Stats.4096.2.1.bin
binFile:  BTLJ732600A41P0FGN.225.1.0.InitStateCoreSync.12.2.1.bin
binFile:  BTLJ732600A41P0FGN.247.1.0.nvmeFeatures.56.1.0.bin
binFile:  BTLJ732600A41P0FGN.266.1.0.NLOG_HOST.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.267.1.0.NLOG_BG.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.254.1.0.qMgrSQList.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.52.1.2.DefragStateCounters.20.1.0.bin
binFile:  BTLJ732600A41P0FGN.51.13.3.Defrag_HistoricDustMixRate.44.1.0.bin
binFile:  BTLJ732600A41P0FGN.261.1.0.NLOG_TC.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.49.13.3.DefragInfo.124.1.1.bin
binFile:  BTLJ732600A41P0FGN.276.1.0.NLOG_EHOST.2112.1.0.bin
binFile:  BTLJ732600A41P0FGN.287.1.0.NLOG_OPAL.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.262.1.0.NLOG_DEBUG.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.64.17.17.PliRestoreFooter.29184.2.1.bin
binFile:  BTLJ732600A41P0FGN.264.1.0.NLOG_15M.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.41.5.1.DefragHistory.36300.2.1.bin
binFile:  BTLJ732600A41P0FGN.10.1.0.initState.48.2.1.bin
binFile:  BTLJ732600A41P0FGN.17.1.0.pssDebugTrace.528.1.0.bin
binFile:  BTLJ732600A41P0FGN.48.13.3.Defrag_WearLevelQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.1.1.0.FwSideTrace.131072.3.0.bin
binFile:  BTLJ732600A41P0FGN.DataArea1.bin
binFile:  BTLJ732600A41P0FGN.290.1.0.powerGov_Fconfig.188.2.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA1.txt
binFile:  BTLJ732600A41P0FGN.262.1.0.NLOG_DEBUG.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.270.1.0.NLOG_ERROR.1088.1.1.bin
binFile:  BTLJ732600A41P0FGN.8.11.1.ThermalStats.1024.2.0.bin
binFile:  BTLJ732600A41P0FGN.252.1.0.qMgrCQList.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.52.1.2.DefragStateCounters.20.1.1.bin
binFile:  BTLJ732600A41P0FGN.58.7.2.fConfigInfoTable.4016.2.0.bin
binFile:  BTLJ732600A41P0FGN.47.13.3.Defrag_WAQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.279.1.0.NLOG_THERM.320.3.1.bin
binFile:  BTLJ732600A41P0FGN.297.7.2.fConfigStream.3072.2.0.bin
binFile:  BTLJ732600A41P0FGN.297.7.2.fConfigStream.3072.2.1.bin
Generating: /home/lab/Documents/parse/workload-fail/workload-fail2_2019-09-13-15-52-30-327000

Project Directory: /home/lab/Documents/parse/arbordaleplus_t2

Bin Files Directory: /home/lab/Documents/parse/workload-fail/workload-fail2_2019-09-13-15-52-30-327000

Creating Telemetry Objects from Binaries...
binFile:  BTLJ732600A41P0FGN.54.13.3.Defrag_ForcedReloQ.8.1.1.bin
binFile:  BTLJ732600A41P0FGN.169.3.0.pssRegs.88.1.0.bin
binFile:  BTLJ732600A41P0FGN.287.1.0.NLOG_OPAL.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.58.7.2.fConfigInfoTable.4016.2.1.bin
binFile:  BTLJ732600A41P0FGN.265.1.0.NLOG_10D.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.2.1.0.BlSideTrace.131072.3.0.bin
binFile:  BTLJ732600A41P0FGN.48.13.3.Defrag_WearLevelQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.51.13.3.Defrag_HistoricDustMixRate.44.1.1.bin
binFile:  BTLJ732600A41P0FGN.57.14.1.NandDiscovery.3576.2.0.bin
binFile:  BTLJ732600A41P0FGN.284.1.0.NLOG_NEI.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.1.0.bin
binFile:  BTLJ732600A41P0FGN.278.1.0.NLOG_RARE.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA3.txt
binFile:  BTLJ732600A41P0FGN.281.1.0.NLOG_UEC.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.265.1.0.NLOG_10D.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.263.1.0.NLOG_TEMP.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.3.0.bin
binFile:  BTLJ732600A41P0FGN.64.17.17.PliRestoreFooter.29184.2.0.bin
binFile:  BTLJ732600A41P0FGN.267.1.0.NLOG_BG.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.5.9.0.bis.1024.1.0.bin
binFile:  BTLJ732600A41P0FGN.41.5.1.DefragHistory.36300.2.0.bin
binFile:  BTLJ732600A41P0FGN.56.4.1.writeLatencyStats.4864.1.1.bin
binFile:  BTLJ732600A41P0FGN.9.1.1.LLFState.84.2.1.bin
binFile:  BTLJ732600A41P0FGN.280.1.0.NLOG_MRRf.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.258.5.1.DefragHistoryPart.4096.1.1.bin
binFile:  BTLJ732600A41P0FGN.261.1.0.NLOG_TC.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.284.1.0.NLOG_NEI.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.266.1.0.NLOG_HOST.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.271.1.0.NLOG_PLI.320.1.1.bin
binFile:  BTLJ732600A41P0FGN.61.29.4.PliRestoreHeader.51712.2.1.bin
binFile:  BTLJ732600A41P0FGN.270.1.0.NLOG_ERROR.1088.1.0.bin
binFile:  BTLJ732600A41P0FGN.286.1.0.NLOG_VAL.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.20.1.0.NplCmdStateInfo.96.1.0.bin
binFile:  BTLJ732600A41P0FGN.57.14.1.NandDiscovery.3576.2.1.bin
binFile:  BTLJ732600A41P0FGN.258.5.1.DefragHistoryPart.4096.1.0.bin
binFile:  BTLJ732600A41P0FGN.88.52.25.Stats.4096.2.0.bin
binFile:  BTLJ732600A41P0FGN.273.1.0.NLOG_STATS.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.264.1.0.NLOG_15M.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.288.1.0.NLOG_IRQ.320.3.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA2.txt
binFile:  BTLJ732600A41P0FGN.288.1.0.NLOG_IRQ.320.3.1.bin
binFile:  BTLJ732600A41P0FGN.255.1.0.NplMailboxState.32768.1.0.bin
binFile:  BTLJ732600A41P0FGN.169.3.0.pssRegs.88.2.0.bin
binFile:  BTLJ732600A41P0FGN.275.1.0.NLOG_HFR.4160.3.1.bin
binFile:  BTLJ732600A41P0FGN.250.1.0.BridgeStatus.12.1.0.bin
binFile:  BTLJ732600A41P0FGN.272.1.0.NLOG_IBM.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.282.1.0.NLOG_TRIM.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.45.13.3.Defrag_DustingQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN_NLOG_FILE_LIST.txt
binFile:  BTLJ732600A41P0FGN.281.1.0.NLOG_UEC.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.289.1.0.NplMailboxRegisters.284.2.0.bin
binFile:  BTLJ732600A41P0FGN.86.1.0.mrr_log.16128.2.0.bin
binFile:  BTLJ732600A41P0FGN.47.13.3.Defrag_WAQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.274.1.0.NLOG_TSTATS.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.49.13.3.DefragInfo.124.1.0.bin
binFile:  BTLJ732600A41P0FGN.61.29.4.PliRestoreHeader.51712.2.0.bin
binFile:  BTLJ732600A41P0FGN.277.1.0.NLOG_WARN.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.55.4.1.readLatencyStats.4864.1.0.bin
binFile:  BTLJ732600A41P0FGN.269.1.0.NLOG_SYS.576.1.1.bin
binFile:  BTLJ732600A41P0FGN.283.1.0.NLOG_MRRs.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.291.1.0.powerGov_Sysparam.224.2.0.bin
binFile:  BTLJ732600A41P0FGN.271.1.0.NLOG_PLI.320.1.0.bin
binFile:  BTLJ732600A41P0FGN.54.13.3.Defrag_ForcedReloQ.8.1.0.bin
binFile:  BTLJ732600A41P0FGN.89.1.0.mrr_state.768.2.0.bin
binFile:  BTLJ732600A41P0FGN.272.1.0.NLOG_IBM.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.DataArea3.bin
binFile:  BTLJ732600A41P0FGN.286.1.0.NLOG_VAL.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.269.1.0.NLOG_SYS.576.1.0.bin
binFile:  BTLJ732600A41P0FGN.283.1.0.NLOG_MRRs.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.276.1.0.NLOG_EHOST.2112.1.1.bin
binFile:  BTLJ732600A41P0FGN.282.1.0.NLOG_TRIM.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.50.13.3.Defrag_BandsDoneQueue.44.1.1.bin
binFile:  BTLJ732600A41P0FGN.274.1.0.NLOG_TSTATS.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.44.13.3.DefragInfoSlow.152.1.1.bin
binFile:  BTLJ732600A41P0FGN.275.1.0.NLOG_HFR.4160.3.0.bin
binFile:  BTLJ732600A41P0FGN.277.1.0.NLOG_WARN.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.260.1.0.NLOG_TEST.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.268.1.0.NLOG_UNIQUE.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.50.13.3.Defrag_BandsDoneQueue.44.1.0.bin
binFile:  BTLJ732600A41P0FGN.109.1.0.mrr_status.152832.2.0.bin
binFile:  BTLJ732600A41P0FGN.46.13.3.Defrag_LockedQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.56.4.1.writeLatencyStats.4864.1.0.bin
binFile:  BTLJ732600A41P0FGN.259.1.0.NLOG_ID.192.3.1.bin
binFile:  BTLJ732600A41P0FGN.259.1.0.NLOG_ID.192.3.0.bin
binFile:  BTLJ732600A41P0FGN.285.1.0.NLOG_DM.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.17.1.0.pssDebugTrace.528.2.0.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.2.0.bin
binFile:  BTLJ732600A41P0FGN.6.11.1.ThermalSensor.4740.2.0.bin
binFile:  BTLJ732600A41P0FGN.46.13.3.Defrag_LockedQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.278.1.0.NLOG_RARE.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.263.1.0.NLOG_TEMP.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.280.1.0.NLOG_MRRf.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.260.1.0.NLOG_TEST.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.DataArea2.bin
binFile:  BTLJ732600A41P0FGN.10.1.0.initState.48.2.0.bin
binFile:  BTLJ732600A41P0FGN.rc
binFile:  BTLJ732600A41P0FGN.257.1.0.NplSQueueRegisters.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.285.1.0.NLOG_DM.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.273.1.0.NLOG_STATS.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.251.1.0.nplInfoState.32.1.0.bin
binFile:  BTLJ732600A41P0FGN.225.1.0.InitStateCoreSync.12.2.0.bin
binFile:  BTLJ732600A41P0FGN.9.1.1.LLFState.84.2.0.bin
binFile:  BTLJ732600A41P0FGN.55.4.1.readLatencyStats.4864.1.1.bin
binFile:  BTLJ732600A41P0FGN.268.1.0.NLOG_UNIQUE.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.45.13.3.Defrag_DustingQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.44.13.3.DefragInfoSlow.152.1.0.bin
binFile:  BTLJ732600A41P0FGN.256.1.0.NplCQueueRegisters.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.279.1.0.NLOG_THERM.320.3.0.bin
binFile:  BTLJ732600A41P0FGN.88.52.25.Stats.4096.2.1.bin
binFile:  BTLJ732600A41P0FGN.225.1.0.InitStateCoreSync.12.2.1.bin
binFile:  BTLJ732600A41P0FGN.247.1.0.nvmeFeatures.56.1.0.bin
binFile:  BTLJ732600A41P0FGN.266.1.0.NLOG_HOST.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.267.1.0.NLOG_BG.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.254.1.0.qMgrSQList.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.52.1.2.DefragStateCounters.20.1.0.bin
binFile:  BTLJ732600A41P0FGN.51.13.3.Defrag_HistoricDustMixRate.44.1.0.bin
binFile:  BTLJ732600A41P0FGN.261.1.0.NLOG_TC.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.49.13.3.DefragInfo.124.1.1.bin
binFile:  BTLJ732600A41P0FGN.276.1.0.NLOG_EHOST.2112.1.0.bin
binFile:  BTLJ732600A41P0FGN.287.1.0.NLOG_OPAL.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.262.1.0.NLOG_DEBUG.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.64.17.17.PliRestoreFooter.29184.2.1.bin
binFile:  BTLJ732600A41P0FGN.264.1.0.NLOG_15M.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.41.5.1.DefragHistory.36300.2.1.bin
binFile:  BTLJ732600A41P0FGN.10.1.0.initState.48.2.1.bin
binFile:  BTLJ732600A41P0FGN.17.1.0.pssDebugTrace.528.1.0.bin
binFile:  BTLJ732600A41P0FGN.48.13.3.Defrag_WearLevelQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.1.1.0.FwSideTrace.131072.3.0.bin
binFile:  BTLJ732600A41P0FGN.DataArea1.bin
binFile:  BTLJ732600A41P0FGN.290.1.0.powerGov_Fconfig.188.2.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA1.txt
binFile:  BTLJ732600A41P0FGN.262.1.0.NLOG_DEBUG.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.270.1.0.NLOG_ERROR.1088.1.1.bin
binFile:  BTLJ732600A41P0FGN.8.11.1.ThermalStats.1024.2.0.bin
binFile:  BTLJ732600A41P0FGN.252.1.0.qMgrCQList.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.52.1.2.DefragStateCounters.20.1.1.bin
binFile:  BTLJ732600A41P0FGN.58.7.2.fConfigInfoTable.4016.2.0.bin
binFile:  BTLJ732600A41P0FGN.47.13.3.Defrag_WAQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.279.1.0.NLOG_THERM.320.3.1.bin
binFile:  BTLJ732600A41P0FGN.297.7.2.fConfigStream.3072.2.0.bin
binFile:  BTLJ732600A41P0FGN.297.7.2.fConfigStream.3072.2.1.bin
Generating: /home/lab/Documents/parse/workload-fail/workload-fail3_2019-09-13-15-52-30-327000

Project Directory: /home/lab/Documents/parse/arbordaleplus_t2

Bin Files Directory: /home/lab/Documents/parse/workload-fail/workload-fail3_2019-09-13-15-52-30-327000

Creating Telemetry Objects from Binaries...
binFile:  BTLJ732600A41P0FGN.54.13.3.Defrag_ForcedReloQ.8.1.1.bin
binFile:  BTLJ732600A41P0FGN.169.3.0.pssRegs.88.1.0.bin
binFile:  BTLJ732600A41P0FGN.287.1.0.NLOG_OPAL.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.58.7.2.fConfigInfoTable.4016.2.1.bin
binFile:  BTLJ732600A41P0FGN.265.1.0.NLOG_10D.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.2.1.0.BlSideTrace.131072.3.0.bin
binFile:  BTLJ732600A41P0FGN.48.13.3.Defrag_WearLevelQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.51.13.3.Defrag_HistoricDustMixRate.44.1.1.bin
binFile:  BTLJ732600A41P0FGN.57.14.1.NandDiscovery.3576.2.0.bin
binFile:  BTLJ732600A41P0FGN.284.1.0.NLOG_NEI.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.1.0.bin
binFile:  BTLJ732600A41P0FGN.278.1.0.NLOG_RARE.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA3.txt
binFile:  BTLJ732600A41P0FGN.281.1.0.NLOG_UEC.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.265.1.0.NLOG_10D.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.263.1.0.NLOG_TEMP.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.3.0.bin
binFile:  BTLJ732600A41P0FGN.64.17.17.PliRestoreFooter.29184.2.0.bin
binFile:  BTLJ732600A41P0FGN.267.1.0.NLOG_BG.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.5.9.0.bis.1024.1.0.bin
binFile:  BTLJ732600A41P0FGN.41.5.1.DefragHistory.36300.2.0.bin
binFile:  BTLJ732600A41P0FGN.56.4.1.writeLatencyStats.4864.1.1.bin
binFile:  BTLJ732600A41P0FGN.9.1.1.LLFState.84.2.1.bin
binFile:  BTLJ732600A41P0FGN.280.1.0.NLOG_MRRf.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.258.5.1.DefragHistoryPart.4096.1.1.bin
binFile:  BTLJ732600A41P0FGN.261.1.0.NLOG_TC.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.284.1.0.NLOG_NEI.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.266.1.0.NLOG_HOST.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.271.1.0.NLOG_PLI.320.1.1.bin
binFile:  BTLJ732600A41P0FGN.61.29.4.PliRestoreHeader.51712.2.1.bin
binFile:  BTLJ732600A41P0FGN.270.1.0.NLOG_ERROR.1088.1.0.bin
binFile:  BTLJ732600A41P0FGN.286.1.0.NLOG_VAL.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.20.1.0.NplCmdStateInfo.96.1.0.bin
binFile:  BTLJ732600A41P0FGN.57.14.1.NandDiscovery.3576.2.1.bin
binFile:  BTLJ732600A41P0FGN.258.5.1.DefragHistoryPart.4096.1.0.bin
binFile:  BTLJ732600A41P0FGN.88.52.25.Stats.4096.2.0.bin
binFile:  BTLJ732600A41P0FGN.273.1.0.NLOG_STATS.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.264.1.0.NLOG_15M.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.288.1.0.NLOG_IRQ.320.3.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA2.txt
binFile:  BTLJ732600A41P0FGN.288.1.0.NLOG_IRQ.320.3.1.bin
binFile:  BTLJ732600A41P0FGN.255.1.0.NplMailboxState.32768.1.0.bin
binFile:  BTLJ732600A41P0FGN.169.3.0.pssRegs.88.2.0.bin
binFile:  BTLJ732600A41P0FGN.275.1.0.NLOG_HFR.4160.3.1.bin
binFile:  BTLJ732600A41P0FGN.250.1.0.BridgeStatus.12.1.0.bin
binFile:  BTLJ732600A41P0FGN.272.1.0.NLOG_IBM.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.282.1.0.NLOG_TRIM.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.45.13.3.Defrag_DustingQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN_NLOG_FILE_LIST.txt
binFile:  BTLJ732600A41P0FGN.281.1.0.NLOG_UEC.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.289.1.0.NplMailboxRegisters.284.2.0.bin
binFile:  BTLJ732600A41P0FGN.86.1.0.mrr_log.16128.2.0.bin
binFile:  BTLJ732600A41P0FGN.47.13.3.Defrag_WAQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.274.1.0.NLOG_TSTATS.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.49.13.3.DefragInfo.124.1.0.bin
binFile:  BTLJ732600A41P0FGN.61.29.4.PliRestoreHeader.51712.2.0.bin
binFile:  BTLJ732600A41P0FGN.277.1.0.NLOG_WARN.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.55.4.1.readLatencyStats.4864.1.0.bin
binFile:  BTLJ732600A41P0FGN.269.1.0.NLOG_SYS.576.1.1.bin
binFile:  BTLJ732600A41P0FGN.283.1.0.NLOG_MRRs.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.291.1.0.powerGov_Sysparam.224.2.0.bin
binFile:  BTLJ732600A41P0FGN.271.1.0.NLOG_PLI.320.1.0.bin
binFile:  BTLJ732600A41P0FGN.54.13.3.Defrag_ForcedReloQ.8.1.0.bin
binFile:  BTLJ732600A41P0FGN.89.1.0.mrr_state.768.2.0.bin
binFile:  BTLJ732600A41P0FGN.272.1.0.NLOG_IBM.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.DataArea3.bin
binFile:  BTLJ732600A41P0FGN.286.1.0.NLOG_VAL.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.269.1.0.NLOG_SYS.576.1.0.bin
binFile:  BTLJ732600A41P0FGN.283.1.0.NLOG_MRRs.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.276.1.0.NLOG_EHOST.2112.1.1.bin
binFile:  BTLJ732600A41P0FGN.282.1.0.NLOG_TRIM.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.50.13.3.Defrag_BandsDoneQueue.44.1.1.bin
binFile:  BTLJ732600A41P0FGN.274.1.0.NLOG_TSTATS.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.44.13.3.DefragInfoSlow.152.1.1.bin
binFile:  BTLJ732600A41P0FGN.275.1.0.NLOG_HFR.4160.3.0.bin
binFile:  BTLJ732600A41P0FGN.277.1.0.NLOG_WARN.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.260.1.0.NLOG_TEST.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.268.1.0.NLOG_UNIQUE.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.50.13.3.Defrag_BandsDoneQueue.44.1.0.bin
binFile:  BTLJ732600A41P0FGN.109.1.0.mrr_status.152832.2.0.bin
binFile:  BTLJ732600A41P0FGN.46.13.3.Defrag_LockedQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.56.4.1.writeLatencyStats.4864.1.0.bin
binFile:  BTLJ732600A41P0FGN.259.1.0.NLOG_ID.192.3.1.bin
binFile:  BTLJ732600A41P0FGN.259.1.0.NLOG_ID.192.3.0.bin
binFile:  BTLJ732600A41P0FGN.285.1.0.NLOG_DM.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.17.1.0.pssDebugTrace.528.2.0.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.2.0.bin
binFile:  BTLJ732600A41P0FGN.6.11.1.ThermalSensor.4740.2.0.bin
binFile:  BTLJ732600A41P0FGN.46.13.3.Defrag_LockedQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.278.1.0.NLOG_RARE.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.263.1.0.NLOG_TEMP.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.280.1.0.NLOG_MRRf.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.260.1.0.NLOG_TEST.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.DataArea2.bin
binFile:  BTLJ732600A41P0FGN.10.1.0.initState.48.2.0.bin
binFile:  BTLJ732600A41P0FGN.rc
binFile:  BTLJ732600A41P0FGN.257.1.0.NplSQueueRegisters.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.285.1.0.NLOG_DM.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.273.1.0.NLOG_STATS.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.251.1.0.nplInfoState.32.1.0.bin
binFile:  BTLJ732600A41P0FGN.225.1.0.InitStateCoreSync.12.2.0.bin
binFile:  BTLJ732600A41P0FGN.9.1.1.LLFState.84.2.0.bin
binFile:  BTLJ732600A41P0FGN.55.4.1.readLatencyStats.4864.1.1.bin
binFile:  BTLJ732600A41P0FGN.268.1.0.NLOG_UNIQUE.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.45.13.3.Defrag_DustingQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.44.13.3.DefragInfoSlow.152.1.0.bin
binFile:  BTLJ732600A41P0FGN.256.1.0.NplCQueueRegisters.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.279.1.0.NLOG_THERM.320.3.0.bin
binFile:  BTLJ732600A41P0FGN.88.52.25.Stats.4096.2.1.bin
binFile:  BTLJ732600A41P0FGN.225.1.0.InitStateCoreSync.12.2.1.bin
binFile:  BTLJ732600A41P0FGN.247.1.0.nvmeFeatures.56.1.0.bin
binFile:  BTLJ732600A41P0FGN.266.1.0.NLOG_HOST.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.267.1.0.NLOG_BG.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.254.1.0.qMgrSQList.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.52.1.2.DefragStateCounters.20.1.0.bin
binFile:  BTLJ732600A41P0FGN.51.13.3.Defrag_HistoricDustMixRate.44.1.0.bin
binFile:  BTLJ732600A41P0FGN.261.1.0.NLOG_TC.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.49.13.3.DefragInfo.124.1.1.bin
binFile:  BTLJ732600A41P0FGN.276.1.0.NLOG_EHOST.2112.1.0.bin
binFile:  BTLJ732600A41P0FGN.287.1.0.NLOG_OPAL.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.262.1.0.NLOG_DEBUG.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.64.17.17.PliRestoreFooter.29184.2.1.bin
binFile:  BTLJ732600A41P0FGN.264.1.0.NLOG_15M.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.41.5.1.DefragHistory.36300.2.1.bin
binFile:  BTLJ732600A41P0FGN.10.1.0.initState.48.2.1.bin
binFile:  BTLJ732600A41P0FGN.17.1.0.pssDebugTrace.528.1.0.bin
binFile:  BTLJ732600A41P0FGN.48.13.3.Defrag_WearLevelQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.1.1.0.FwSideTrace.131072.3.0.bin
binFile:  BTLJ732600A41P0FGN.DataArea1.bin
binFile:  BTLJ732600A41P0FGN.290.1.0.powerGov_Fconfig.188.2.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA1.txt
binFile:  BTLJ732600A41P0FGN.262.1.0.NLOG_DEBUG.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.270.1.0.NLOG_ERROR.1088.1.1.bin
binFile:  BTLJ732600A41P0FGN.8.11.1.ThermalStats.1024.2.0.bin
binFile:  BTLJ732600A41P0FGN.252.1.0.qMgrCQList.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.52.1.2.DefragStateCounters.20.1.1.bin
binFile:  BTLJ732600A41P0FGN.58.7.2.fConfigInfoTable.4016.2.0.bin
binFile:  BTLJ732600A41P0FGN.47.13.3.Defrag_WAQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.279.1.0.NLOG_THERM.320.3.1.bin
binFile:  BTLJ732600A41P0FGN.297.7.2.fConfigStream.3072.2.0.bin
binFile:  BTLJ732600A41P0FGN.297.7.2.fConfigStream.3072.2.1.bin
Generating: /home/lab/Documents/parse/workload-fail/workload-fail4_2019-09-13-15-52-30-327000

Project Directory: /home/lab/Documents/parse/arbordaleplus_t2

Bin Files Directory: /home/lab/Documents/parse/workload-fail/workload-fail4_2019-09-13-15-52-30-327000

Creating Telemetry Objects from Binaries...
binFile:  BTLJ732600A41P0FGN.54.13.3.Defrag_ForcedReloQ.8.1.1.bin
binFile:  BTLJ732600A41P0FGN.169.3.0.pssRegs.88.1.0.bin
binFile:  BTLJ732600A41P0FGN.287.1.0.NLOG_OPAL.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.58.7.2.fConfigInfoTable.4016.2.1.bin
binFile:  BTLJ732600A41P0FGN.265.1.0.NLOG_10D.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.2.1.0.BlSideTrace.131072.3.0.bin
binFile:  BTLJ732600A41P0FGN.48.13.3.Defrag_WearLevelQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.51.13.3.Defrag_HistoricDustMixRate.44.1.1.bin
binFile:  BTLJ732600A41P0FGN.57.14.1.NandDiscovery.3576.2.0.bin
binFile:  BTLJ732600A41P0FGN.284.1.0.NLOG_NEI.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.1.0.bin
binFile:  BTLJ732600A41P0FGN.278.1.0.NLOG_RARE.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA3.txt
binFile:  BTLJ732600A41P0FGN.281.1.0.NLOG_UEC.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.265.1.0.NLOG_10D.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.263.1.0.NLOG_TEMP.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.3.0.bin
binFile:  BTLJ732600A41P0FGN.64.17.17.PliRestoreFooter.29184.2.0.bin
binFile:  BTLJ732600A41P0FGN.267.1.0.NLOG_BG.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.5.9.0.bis.1024.1.0.bin
binFile:  BTLJ732600A41P0FGN.41.5.1.DefragHistory.36300.2.0.bin
binFile:  BTLJ732600A41P0FGN.56.4.1.writeLatencyStats.4864.1.1.bin
binFile:  BTLJ732600A41P0FGN.9.1.1.LLFState.84.2.1.bin
binFile:  BTLJ732600A41P0FGN.280.1.0.NLOG_MRRf.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.258.5.1.DefragHistoryPart.4096.1.1.bin
binFile:  BTLJ732600A41P0FGN.261.1.0.NLOG_TC.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.284.1.0.NLOG_NEI.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.266.1.0.NLOG_HOST.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.271.1.0.NLOG_PLI.320.1.1.bin
binFile:  BTLJ732600A41P0FGN.61.29.4.PliRestoreHeader.51712.2.1.bin
binFile:  BTLJ732600A41P0FGN.270.1.0.NLOG_ERROR.1088.1.0.bin
binFile:  BTLJ732600A41P0FGN.286.1.0.NLOG_VAL.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.20.1.0.NplCmdStateInfo.96.1.0.bin
binFile:  BTLJ732600A41P0FGN.57.14.1.NandDiscovery.3576.2.1.bin
binFile:  BTLJ732600A41P0FGN.258.5.1.DefragHistoryPart.4096.1.0.bin
binFile:  BTLJ732600A41P0FGN.88.52.25.Stats.4096.2.0.bin
binFile:  BTLJ732600A41P0FGN.273.1.0.NLOG_STATS.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.264.1.0.NLOG_15M.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.288.1.0.NLOG_IRQ.320.3.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA2.txt
binFile:  BTLJ732600A41P0FGN.288.1.0.NLOG_IRQ.320.3.1.bin
binFile:  BTLJ732600A41P0FGN.255.1.0.NplMailboxState.32768.1.0.bin
binFile:  BTLJ732600A41P0FGN.169.3.0.pssRegs.88.2.0.bin
binFile:  BTLJ732600A41P0FGN.275.1.0.NLOG_HFR.4160.3.1.bin
binFile:  BTLJ732600A41P0FGN.250.1.0.BridgeStatus.12.1.0.bin
binFile:  BTLJ732600A41P0FGN.272.1.0.NLOG_IBM.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.282.1.0.NLOG_TRIM.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.45.13.3.Defrag_DustingQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN_NLOG_FILE_LIST.txt
binFile:  BTLJ732600A41P0FGN.281.1.0.NLOG_UEC.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.289.1.0.NplMailboxRegisters.284.2.0.bin
binFile:  BTLJ732600A41P0FGN.86.1.0.mrr_log.16128.2.0.bin
binFile:  BTLJ732600A41P0FGN.47.13.3.Defrag_WAQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.274.1.0.NLOG_TSTATS.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.49.13.3.DefragInfo.124.1.0.bin
binFile:  BTLJ732600A41P0FGN.61.29.4.PliRestoreHeader.51712.2.0.bin
binFile:  BTLJ732600A41P0FGN.277.1.0.NLOG_WARN.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.55.4.1.readLatencyStats.4864.1.0.bin
binFile:  BTLJ732600A41P0FGN.269.1.0.NLOG_SYS.576.1.1.bin
binFile:  BTLJ732600A41P0FGN.283.1.0.NLOG_MRRs.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.291.1.0.powerGov_Sysparam.224.2.0.bin
binFile:  BTLJ732600A41P0FGN.271.1.0.NLOG_PLI.320.1.0.bin
binFile:  BTLJ732600A41P0FGN.54.13.3.Defrag_ForcedReloQ.8.1.0.bin
binFile:  BTLJ732600A41P0FGN.89.1.0.mrr_state.768.2.0.bin
binFile:  BTLJ732600A41P0FGN.272.1.0.NLOG_IBM.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.DataArea3.bin
binFile:  BTLJ732600A41P0FGN.286.1.0.NLOG_VAL.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.269.1.0.NLOG_SYS.576.1.0.bin
binFile:  BTLJ732600A41P0FGN.283.1.0.NLOG_MRRs.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.276.1.0.NLOG_EHOST.2112.1.1.bin
binFile:  BTLJ732600A41P0FGN.282.1.0.NLOG_TRIM.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.50.13.3.Defrag_BandsDoneQueue.44.1.1.bin
binFile:  BTLJ732600A41P0FGN.274.1.0.NLOG_TSTATS.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.44.13.3.DefragInfoSlow.152.1.1.bin
binFile:  BTLJ732600A41P0FGN.275.1.0.NLOG_HFR.4160.3.0.bin
binFile:  BTLJ732600A41P0FGN.277.1.0.NLOG_WARN.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.260.1.0.NLOG_TEST.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.268.1.0.NLOG_UNIQUE.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.50.13.3.Defrag_BandsDoneQueue.44.1.0.bin
binFile:  BTLJ732600A41P0FGN.109.1.0.mrr_status.152832.2.0.bin
binFile:  BTLJ732600A41P0FGN.46.13.3.Defrag_LockedQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.56.4.1.writeLatencyStats.4864.1.0.bin
binFile:  BTLJ732600A41P0FGN.259.1.0.NLOG_ID.192.3.1.bin
binFile:  BTLJ732600A41P0FGN.259.1.0.NLOG_ID.192.3.0.bin
binFile:  BTLJ732600A41P0FGN.285.1.0.NLOG_DM.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.17.1.0.pssDebugTrace.528.2.0.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.2.0.bin
binFile:  BTLJ732600A41P0FGN.6.11.1.ThermalSensor.4740.2.0.bin
binFile:  BTLJ732600A41P0FGN.46.13.3.Defrag_LockedQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.278.1.0.NLOG_RARE.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.263.1.0.NLOG_TEMP.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.280.1.0.NLOG_MRRf.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.260.1.0.NLOG_TEST.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.DataArea2.bin
binFile:  BTLJ732600A41P0FGN.10.1.0.initState.48.2.0.bin
binFile:  BTLJ732600A41P0FGN.rc
binFile:  BTLJ732600A41P0FGN.257.1.0.NplSQueueRegisters.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.285.1.0.NLOG_DM.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.273.1.0.NLOG_STATS.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.251.1.0.nplInfoState.32.1.0.bin
binFile:  BTLJ732600A41P0FGN.225.1.0.InitStateCoreSync.12.2.0.bin
binFile:  BTLJ732600A41P0FGN.9.1.1.LLFState.84.2.0.bin
binFile:  BTLJ732600A41P0FGN.55.4.1.readLatencyStats.4864.1.1.bin
binFile:  BTLJ732600A41P0FGN.268.1.0.NLOG_UNIQUE.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.45.13.3.Defrag_DustingQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.44.13.3.DefragInfoSlow.152.1.0.bin
binFile:  BTLJ732600A41P0FGN.256.1.0.NplCQueueRegisters.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.279.1.0.NLOG_THERM.320.3.0.bin
binFile:  BTLJ732600A41P0FGN.88.52.25.Stats.4096.2.1.bin
binFile:  BTLJ732600A41P0FGN.225.1.0.InitStateCoreSync.12.2.1.bin
binFile:  BTLJ732600A41P0FGN.247.1.0.nvmeFeatures.56.1.0.bin
binFile:  BTLJ732600A41P0FGN.266.1.0.NLOG_HOST.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.267.1.0.NLOG_BG.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.254.1.0.qMgrSQList.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.52.1.2.DefragStateCounters.20.1.0.bin
binFile:  BTLJ732600A41P0FGN.51.13.3.Defrag_HistoricDustMixRate.44.1.0.bin
binFile:  BTLJ732600A41P0FGN.261.1.0.NLOG_TC.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.49.13.3.DefragInfo.124.1.1.bin
binFile:  BTLJ732600A41P0FGN.276.1.0.NLOG_EHOST.2112.1.0.bin
binFile:  BTLJ732600A41P0FGN.287.1.0.NLOG_OPAL.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.262.1.0.NLOG_DEBUG.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.64.17.17.PliRestoreFooter.29184.2.1.bin
binFile:  BTLJ732600A41P0FGN.264.1.0.NLOG_15M.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.41.5.1.DefragHistory.36300.2.1.bin
binFile:  BTLJ732600A41P0FGN.10.1.0.initState.48.2.1.bin
binFile:  BTLJ732600A41P0FGN.17.1.0.pssDebugTrace.528.1.0.bin
binFile:  BTLJ732600A41P0FGN.48.13.3.Defrag_WearLevelQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.1.1.0.FwSideTrace.131072.3.0.bin
binFile:  BTLJ732600A41P0FGN.DataArea1.bin
binFile:  BTLJ732600A41P0FGN.290.1.0.powerGov_Fconfig.188.2.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA1.txt
binFile:  BTLJ732600A41P0FGN.262.1.0.NLOG_DEBUG.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.270.1.0.NLOG_ERROR.1088.1.1.bin
binFile:  BTLJ732600A41P0FGN.8.11.1.ThermalStats.1024.2.0.bin
binFile:  BTLJ732600A41P0FGN.252.1.0.qMgrCQList.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.52.1.2.DefragStateCounters.20.1.1.bin
binFile:  BTLJ732600A41P0FGN.58.7.2.fConfigInfoTable.4016.2.0.bin
binFile:  BTLJ732600A41P0FGN.47.13.3.Defrag_WAQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.279.1.0.NLOG_THERM.320.3.1.bin
binFile:  BTLJ732600A41P0FGN.297.7.2.fConfigStream.3072.2.0.bin
binFile:  BTLJ732600A41P0FGN.297.7.2.fConfigStream.3072.2.1.bin
Generating: /home/lab/Documents/parse/workload-fail/workload-fail5_2019-09-13-15-52-30-327000

Project Directory: /home/lab/Documents/parse/arbordaleplus_t2

Bin Files Directory: /home/lab/Documents/parse/workload-fail/workload-fail5_2019-09-13-15-52-30-327000

Creating Telemetry Objects from Binaries...
binFile:  BTLJ732600A41P0FGN.54.13.3.Defrag_ForcedReloQ.8.1.1.bin
binFile:  BTLJ732600A41P0FGN.169.3.0.pssRegs.88.1.0.bin
binFile:  BTLJ732600A41P0FGN.287.1.0.NLOG_OPAL.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.58.7.2.fConfigInfoTable.4016.2.1.bin
binFile:  BTLJ732600A41P0FGN.265.1.0.NLOG_10D.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.2.1.0.BlSideTrace.131072.3.0.bin
binFile:  BTLJ732600A41P0FGN.48.13.3.Defrag_WearLevelQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.51.13.3.Defrag_HistoricDustMixRate.44.1.1.bin
binFile:  BTLJ732600A41P0FGN.57.14.1.NandDiscovery.3576.2.0.bin
binFile:  BTLJ732600A41P0FGN.284.1.0.NLOG_NEI.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.1.0.bin
binFile:  BTLJ732600A41P0FGN.278.1.0.NLOG_RARE.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA3.txt
binFile:  BTLJ732600A41P0FGN.281.1.0.NLOG_UEC.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.265.1.0.NLOG_10D.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.263.1.0.NLOG_TEMP.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.3.0.bin
binFile:  BTLJ732600A41P0FGN.64.17.17.PliRestoreFooter.29184.2.0.bin
binFile:  BTLJ732600A41P0FGN.267.1.0.NLOG_BG.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.5.9.0.bis.1024.1.0.bin
binFile:  BTLJ732600A41P0FGN.41.5.1.DefragHistory.36300.2.0.bin
binFile:  BTLJ732600A41P0FGN.56.4.1.writeLatencyStats.4864.1.1.bin
binFile:  BTLJ732600A41P0FGN.9.1.1.LLFState.84.2.1.bin
binFile:  BTLJ732600A41P0FGN.280.1.0.NLOG_MRRf.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.258.5.1.DefragHistoryPart.4096.1.1.bin
binFile:  BTLJ732600A41P0FGN.261.1.0.NLOG_TC.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.284.1.0.NLOG_NEI.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.266.1.0.NLOG_HOST.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.271.1.0.NLOG_PLI.320.1.1.bin
binFile:  BTLJ732600A41P0FGN.61.29.4.PliRestoreHeader.51712.2.1.bin
binFile:  BTLJ732600A41P0FGN.270.1.0.NLOG_ERROR.1088.1.0.bin
binFile:  BTLJ732600A41P0FGN.286.1.0.NLOG_VAL.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.20.1.0.NplCmdStateInfo.96.1.0.bin
binFile:  BTLJ732600A41P0FGN.57.14.1.NandDiscovery.3576.2.1.bin
binFile:  BTLJ732600A41P0FGN.258.5.1.DefragHistoryPart.4096.1.0.bin
binFile:  BTLJ732600A41P0FGN.88.52.25.Stats.4096.2.0.bin
binFile:  BTLJ732600A41P0FGN.273.1.0.NLOG_STATS.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.264.1.0.NLOG_15M.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.288.1.0.NLOG_IRQ.320.3.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA2.txt
binFile:  BTLJ732600A41P0FGN.288.1.0.NLOG_IRQ.320.3.1.bin
binFile:  BTLJ732600A41P0FGN.255.1.0.NplMailboxState.32768.1.0.bin
binFile:  BTLJ732600A41P0FGN.169.3.0.pssRegs.88.2.0.bin
binFile:  BTLJ732600A41P0FGN.275.1.0.NLOG_HFR.4160.3.1.bin
binFile:  BTLJ732600A41P0FGN.250.1.0.BridgeStatus.12.1.0.bin
binFile:  BTLJ732600A41P0FGN.272.1.0.NLOG_IBM.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.282.1.0.NLOG_TRIM.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.45.13.3.Defrag_DustingQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN_NLOG_FILE_LIST.txt
binFile:  BTLJ732600A41P0FGN.281.1.0.NLOG_UEC.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.289.1.0.NplMailboxRegisters.284.2.0.bin
binFile:  BTLJ732600A41P0FGN.86.1.0.mrr_log.16128.2.0.bin
binFile:  BTLJ732600A41P0FGN.47.13.3.Defrag_WAQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.274.1.0.NLOG_TSTATS.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.49.13.3.DefragInfo.124.1.0.bin
binFile:  BTLJ732600A41P0FGN.61.29.4.PliRestoreHeader.51712.2.0.bin
binFile:  BTLJ732600A41P0FGN.277.1.0.NLOG_WARN.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.55.4.1.readLatencyStats.4864.1.0.bin
binFile:  BTLJ732600A41P0FGN.269.1.0.NLOG_SYS.576.1.1.bin
binFile:  BTLJ732600A41P0FGN.283.1.0.NLOG_MRRs.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.291.1.0.powerGov_Sysparam.224.2.0.bin
binFile:  BTLJ732600A41P0FGN.271.1.0.NLOG_PLI.320.1.0.bin
binFile:  BTLJ732600A41P0FGN.54.13.3.Defrag_ForcedReloQ.8.1.0.bin
binFile:  BTLJ732600A41P0FGN.89.1.0.mrr_state.768.2.0.bin
binFile:  BTLJ732600A41P0FGN.272.1.0.NLOG_IBM.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.DataArea3.bin
binFile:  BTLJ732600A41P0FGN.286.1.0.NLOG_VAL.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.269.1.0.NLOG_SYS.576.1.0.bin
binFile:  BTLJ732600A41P0FGN.283.1.0.NLOG_MRRs.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.276.1.0.NLOG_EHOST.2112.1.1.bin
binFile:  BTLJ732600A41P0FGN.282.1.0.NLOG_TRIM.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.50.13.3.Defrag_BandsDoneQueue.44.1.1.bin
binFile:  BTLJ732600A41P0FGN.274.1.0.NLOG_TSTATS.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.44.13.3.DefragInfoSlow.152.1.1.bin
binFile:  BTLJ732600A41P0FGN.275.1.0.NLOG_HFR.4160.3.0.bin
binFile:  BTLJ732600A41P0FGN.277.1.0.NLOG_WARN.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.260.1.0.NLOG_TEST.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.268.1.0.NLOG_UNIQUE.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.50.13.3.Defrag_BandsDoneQueue.44.1.0.bin
binFile:  BTLJ732600A41P0FGN.109.1.0.mrr_status.152832.2.0.bin
binFile:  BTLJ732600A41P0FGN.46.13.3.Defrag_LockedQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.56.4.1.writeLatencyStats.4864.1.0.bin
binFile:  BTLJ732600A41P0FGN.259.1.0.NLOG_ID.192.3.1.bin
binFile:  BTLJ732600A41P0FGN.259.1.0.NLOG_ID.192.3.0.bin
binFile:  BTLJ732600A41P0FGN.285.1.0.NLOG_DM.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.17.1.0.pssDebugTrace.528.2.0.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.2.0.bin
binFile:  BTLJ732600A41P0FGN.6.11.1.ThermalSensor.4740.2.0.bin
binFile:  BTLJ732600A41P0FGN.46.13.3.Defrag_LockedQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.278.1.0.NLOG_RARE.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.263.1.0.NLOG_TEMP.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.280.1.0.NLOG_MRRf.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.260.1.0.NLOG_TEST.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.DataArea2.bin
binFile:  BTLJ732600A41P0FGN.10.1.0.initState.48.2.0.bin
binFile:  BTLJ732600A41P0FGN.rc
binFile:  BTLJ732600A41P0FGN.257.1.0.NplSQueueRegisters.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.285.1.0.NLOG_DM.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.273.1.0.NLOG_STATS.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.251.1.0.nplInfoState.32.1.0.bin
binFile:  BTLJ732600A41P0FGN.225.1.0.InitStateCoreSync.12.2.0.bin
binFile:  BTLJ732600A41P0FGN.9.1.1.LLFState.84.2.0.bin
binFile:  BTLJ732600A41P0FGN.55.4.1.readLatencyStats.4864.1.1.bin
binFile:  BTLJ732600A41P0FGN.268.1.0.NLOG_UNIQUE.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.45.13.3.Defrag_DustingQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.44.13.3.DefragInfoSlow.152.1.0.bin
binFile:  BTLJ732600A41P0FGN.256.1.0.NplCQueueRegisters.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.279.1.0.NLOG_THERM.320.3.0.bin
binFile:  BTLJ732600A41P0FGN.88.52.25.Stats.4096.2.1.bin
binFile:  BTLJ732600A41P0FGN.225.1.0.InitStateCoreSync.12.2.1.bin
binFile:  BTLJ732600A41P0FGN.247.1.0.nvmeFeatures.56.1.0.bin
binFile:  BTLJ732600A41P0FGN.266.1.0.NLOG_HOST.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.267.1.0.NLOG_BG.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.254.1.0.qMgrSQList.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.52.1.2.DefragStateCounters.20.1.0.bin
binFile:  BTLJ732600A41P0FGN.51.13.3.Defrag_HistoricDustMixRate.44.1.0.bin
binFile:  BTLJ732600A41P0FGN.261.1.0.NLOG_TC.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.49.13.3.DefragInfo.124.1.1.bin
binFile:  BTLJ732600A41P0FGN.276.1.0.NLOG_EHOST.2112.1.0.bin
binFile:  BTLJ732600A41P0FGN.287.1.0.NLOG_OPAL.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.262.1.0.NLOG_DEBUG.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.64.17.17.PliRestoreFooter.29184.2.1.bin
binFile:  BTLJ732600A41P0FGN.264.1.0.NLOG_15M.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.41.5.1.DefragHistory.36300.2.1.bin
binFile:  BTLJ732600A41P0FGN.10.1.0.initState.48.2.1.bin
binFile:  BTLJ732600A41P0FGN.17.1.0.pssDebugTrace.528.1.0.bin
binFile:  BTLJ732600A41P0FGN.48.13.3.Defrag_WearLevelQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.1.1.0.FwSideTrace.131072.3.0.bin
binFile:  BTLJ732600A41P0FGN.DataArea1.bin
binFile:  BTLJ732600A41P0FGN.290.1.0.powerGov_Fconfig.188.2.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA1.txt
binFile:  BTLJ732600A41P0FGN.262.1.0.NLOG_DEBUG.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.270.1.0.NLOG_ERROR.1088.1.1.bin
binFile:  BTLJ732600A41P0FGN.8.11.1.ThermalStats.1024.2.0.bin
binFile:  BTLJ732600A41P0FGN.252.1.0.qMgrCQList.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.52.1.2.DefragStateCounters.20.1.1.bin
binFile:  BTLJ732600A41P0FGN.58.7.2.fConfigInfoTable.4016.2.0.bin
binFile:  BTLJ732600A41P0FGN.47.13.3.Defrag_WAQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.279.1.0.NLOG_THERM.320.3.1.bin
binFile:  BTLJ732600A41P0FGN.297.7.2.fConfigStream.3072.2.0.bin
binFile:  BTLJ732600A41P0FGN.297.7.2.fConfigStream.3072.2.1.bin
Generating: /home/lab/Documents/parse/workload-fail/workload-fail6_2019-09-13-15-52-30-327000

Project Directory: /home/lab/Documents/parse/arbordaleplus_t2

Bin Files Directory: /home/lab/Documents/parse/workload-fail/workload-fail6_2019-09-13-15-52-30-327000

Creating Telemetry Objects from Binaries...
binFile:  BTLJ732600A41P0FGN.54.13.3.Defrag_ForcedReloQ.8.1.1.bin
binFile:  BTLJ732600A41P0FGN.169.3.0.pssRegs.88.1.0.bin
binFile:  BTLJ732600A41P0FGN.287.1.0.NLOG_OPAL.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.58.7.2.fConfigInfoTable.4016.2.1.bin
binFile:  BTLJ732600A41P0FGN.265.1.0.NLOG_10D.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.2.1.0.BlSideTrace.131072.3.0.bin
binFile:  BTLJ732600A41P0FGN.48.13.3.Defrag_WearLevelQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.51.13.3.Defrag_HistoricDustMixRate.44.1.1.bin
binFile:  BTLJ732600A41P0FGN.57.14.1.NandDiscovery.3576.2.0.bin
binFile:  BTLJ732600A41P0FGN.284.1.0.NLOG_NEI.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.1.0.bin
binFile:  BTLJ732600A41P0FGN.278.1.0.NLOG_RARE.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA3.txt
binFile:  BTLJ732600A41P0FGN.281.1.0.NLOG_UEC.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.265.1.0.NLOG_10D.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.263.1.0.NLOG_TEMP.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.3.0.bin
binFile:  BTLJ732600A41P0FGN.64.17.17.PliRestoreFooter.29184.2.0.bin
binFile:  BTLJ732600A41P0FGN.267.1.0.NLOG_BG.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.5.9.0.bis.1024.1.0.bin
binFile:  BTLJ732600A41P0FGN.41.5.1.DefragHistory.36300.2.0.bin
binFile:  BTLJ732600A41P0FGN.56.4.1.writeLatencyStats.4864.1.1.bin
binFile:  BTLJ732600A41P0FGN.9.1.1.LLFState.84.2.1.bin
binFile:  BTLJ732600A41P0FGN.280.1.0.NLOG_MRRf.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.258.5.1.DefragHistoryPart.4096.1.1.bin
binFile:  BTLJ732600A41P0FGN.261.1.0.NLOG_TC.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.284.1.0.NLOG_NEI.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.266.1.0.NLOG_HOST.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.271.1.0.NLOG_PLI.320.1.1.bin
binFile:  BTLJ732600A41P0FGN.61.29.4.PliRestoreHeader.51712.2.1.bin
binFile:  BTLJ732600A41P0FGN.270.1.0.NLOG_ERROR.1088.1.0.bin
binFile:  BTLJ732600A41P0FGN.286.1.0.NLOG_VAL.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.20.1.0.NplCmdStateInfo.96.1.0.bin
binFile:  BTLJ732600A41P0FGN.57.14.1.NandDiscovery.3576.2.1.bin
binFile:  BTLJ732600A41P0FGN.258.5.1.DefragHistoryPart.4096.1.0.bin
binFile:  BTLJ732600A41P0FGN.88.52.25.Stats.4096.2.0.bin
binFile:  BTLJ732600A41P0FGN.273.1.0.NLOG_STATS.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.264.1.0.NLOG_15M.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.288.1.0.NLOG_IRQ.320.3.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA2.txt
binFile:  BTLJ732600A41P0FGN.288.1.0.NLOG_IRQ.320.3.1.bin
binFile:  BTLJ732600A41P0FGN.255.1.0.NplMailboxState.32768.1.0.bin
binFile:  BTLJ732600A41P0FGN.169.3.0.pssRegs.88.2.0.bin
binFile:  BTLJ732600A41P0FGN.275.1.0.NLOG_HFR.4160.3.1.bin
binFile:  BTLJ732600A41P0FGN.250.1.0.BridgeStatus.12.1.0.bin
binFile:  BTLJ732600A41P0FGN.272.1.0.NLOG_IBM.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.282.1.0.NLOG_TRIM.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.45.13.3.Defrag_DustingQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN_NLOG_FILE_LIST.txt
binFile:  BTLJ732600A41P0FGN.281.1.0.NLOG_UEC.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.289.1.0.NplMailboxRegisters.284.2.0.bin
binFile:  BTLJ732600A41P0FGN.86.1.0.mrr_log.16128.2.0.bin
binFile:  BTLJ732600A41P0FGN.47.13.3.Defrag_WAQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.274.1.0.NLOG_TSTATS.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.49.13.3.DefragInfo.124.1.0.bin
binFile:  BTLJ732600A41P0FGN.61.29.4.PliRestoreHeader.51712.2.0.bin
binFile:  BTLJ732600A41P0FGN.277.1.0.NLOG_WARN.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.55.4.1.readLatencyStats.4864.1.0.bin
binFile:  BTLJ732600A41P0FGN.269.1.0.NLOG_SYS.576.1.1.bin
binFile:  BTLJ732600A41P0FGN.283.1.0.NLOG_MRRs.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.291.1.0.powerGov_Sysparam.224.2.0.bin
binFile:  BTLJ732600A41P0FGN.271.1.0.NLOG_PLI.320.1.0.bin
binFile:  BTLJ732600A41P0FGN.54.13.3.Defrag_ForcedReloQ.8.1.0.bin
binFile:  BTLJ732600A41P0FGN.89.1.0.mrr_state.768.2.0.bin
binFile:  BTLJ732600A41P0FGN.272.1.0.NLOG_IBM.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.DataArea3.bin
binFile:  BTLJ732600A41P0FGN.286.1.0.NLOG_VAL.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.269.1.0.NLOG_SYS.576.1.0.bin
binFile:  BTLJ732600A41P0FGN.283.1.0.NLOG_MRRs.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.276.1.0.NLOG_EHOST.2112.1.1.bin
binFile:  BTLJ732600A41P0FGN.282.1.0.NLOG_TRIM.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.50.13.3.Defrag_BandsDoneQueue.44.1.1.bin
binFile:  BTLJ732600A41P0FGN.274.1.0.NLOG_TSTATS.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.44.13.3.DefragInfoSlow.152.1.1.bin
binFile:  BTLJ732600A41P0FGN.275.1.0.NLOG_HFR.4160.3.0.bin
binFile:  BTLJ732600A41P0FGN.277.1.0.NLOG_WARN.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.260.1.0.NLOG_TEST.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.268.1.0.NLOG_UNIQUE.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.50.13.3.Defrag_BandsDoneQueue.44.1.0.bin
binFile:  BTLJ732600A41P0FGN.109.1.0.mrr_status.152832.2.0.bin
binFile:  BTLJ732600A41P0FGN.46.13.3.Defrag_LockedQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.56.4.1.writeLatencyStats.4864.1.0.bin
binFile:  BTLJ732600A41P0FGN.259.1.0.NLOG_ID.192.3.1.bin
binFile:  BTLJ732600A41P0FGN.259.1.0.NLOG_ID.192.3.0.bin
binFile:  BTLJ732600A41P0FGN.285.1.0.NLOG_DM.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.17.1.0.pssDebugTrace.528.2.0.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.2.0.bin
binFile:  BTLJ732600A41P0FGN.6.11.1.ThermalSensor.4740.2.0.bin
binFile:  BTLJ732600A41P0FGN.46.13.3.Defrag_LockedQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.278.1.0.NLOG_RARE.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.263.1.0.NLOG_TEMP.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.280.1.0.NLOG_MRRf.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.260.1.0.NLOG_TEST.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.DataArea2.bin
binFile:  BTLJ732600A41P0FGN.10.1.0.initState.48.2.0.bin
binFile:  BTLJ732600A41P0FGN.rc
binFile:  BTLJ732600A41P0FGN.257.1.0.NplSQueueRegisters.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.285.1.0.NLOG_DM.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.273.1.0.NLOG_STATS.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.251.1.0.nplInfoState.32.1.0.bin
binFile:  BTLJ732600A41P0FGN.225.1.0.InitStateCoreSync.12.2.0.bin
binFile:  BTLJ732600A41P0FGN.9.1.1.LLFState.84.2.0.bin
binFile:  BTLJ732600A41P0FGN.55.4.1.readLatencyStats.4864.1.1.bin
binFile:  BTLJ732600A41P0FGN.268.1.0.NLOG_UNIQUE.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.45.13.3.Defrag_DustingQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.44.13.3.DefragInfoSlow.152.1.0.bin
binFile:  BTLJ732600A41P0FGN.256.1.0.NplCQueueRegisters.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.279.1.0.NLOG_THERM.320.3.0.bin
binFile:  BTLJ732600A41P0FGN.88.52.25.Stats.4096.2.1.bin
binFile:  BTLJ732600A41P0FGN.225.1.0.InitStateCoreSync.12.2.1.bin
binFile:  BTLJ732600A41P0FGN.247.1.0.nvmeFeatures.56.1.0.bin
binFile:  BTLJ732600A41P0FGN.266.1.0.NLOG_HOST.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.267.1.0.NLOG_BG.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.254.1.0.qMgrSQList.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.52.1.2.DefragStateCounters.20.1.0.bin
binFile:  BTLJ732600A41P0FGN.51.13.3.Defrag_HistoricDustMixRate.44.1.0.bin
binFile:  BTLJ732600A41P0FGN.261.1.0.NLOG_TC.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.49.13.3.DefragInfo.124.1.1.bin
binFile:  BTLJ732600A41P0FGN.276.1.0.NLOG_EHOST.2112.1.0.bin
binFile:  BTLJ732600A41P0FGN.287.1.0.NLOG_OPAL.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.262.1.0.NLOG_DEBUG.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.64.17.17.PliRestoreFooter.29184.2.1.bin
binFile:  BTLJ732600A41P0FGN.264.1.0.NLOG_15M.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.41.5.1.DefragHistory.36300.2.1.bin
binFile:  BTLJ732600A41P0FGN.10.1.0.initState.48.2.1.bin
binFile:  BTLJ732600A41P0FGN.17.1.0.pssDebugTrace.528.1.0.bin
binFile:  BTLJ732600A41P0FGN.48.13.3.Defrag_WearLevelQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.1.1.0.FwSideTrace.131072.3.0.bin
binFile:  BTLJ732600A41P0FGN.DataArea1.bin
binFile:  BTLJ732600A41P0FGN.290.1.0.powerGov_Fconfig.188.2.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA1.txt
binFile:  BTLJ732600A41P0FGN.262.1.0.NLOG_DEBUG.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.270.1.0.NLOG_ERROR.1088.1.1.bin
binFile:  BTLJ732600A41P0FGN.8.11.1.ThermalStats.1024.2.0.bin
binFile:  BTLJ732600A41P0FGN.252.1.0.qMgrCQList.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.52.1.2.DefragStateCounters.20.1.1.bin
binFile:  BTLJ732600A41P0FGN.58.7.2.fConfigInfoTable.4016.2.0.bin
binFile:  BTLJ732600A41P0FGN.47.13.3.Defrag_WAQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.279.1.0.NLOG_THERM.320.3.1.bin
binFile:  BTLJ732600A41P0FGN.297.7.2.fConfigStream.3072.2.0.bin
binFile:  BTLJ732600A41P0FGN.297.7.2.fConfigStream.3072.2.1.bin
Generating: /home/lab/Documents/parse/workload-fail/workload-fail7_2019-09-13-15-52-30-327000

Project Directory: /home/lab/Documents/parse/arbordaleplus_t2

Bin Files Directory: /home/lab/Documents/parse/workload-fail/workload-fail7_2019-09-13-15-52-30-327000

Creating Telemetry Objects from Binaries...
binFile:  BTLJ732600A41P0FGN.54.13.3.Defrag_ForcedReloQ.8.1.1.bin
binFile:  BTLJ732600A41P0FGN.169.3.0.pssRegs.88.1.0.bin
binFile:  BTLJ732600A41P0FGN.287.1.0.NLOG_OPAL.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.58.7.2.fConfigInfoTable.4016.2.1.bin
binFile:  BTLJ732600A41P0FGN.265.1.0.NLOG_10D.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.2.1.0.BlSideTrace.131072.3.0.bin
binFile:  BTLJ732600A41P0FGN.48.13.3.Defrag_WearLevelQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.51.13.3.Defrag_HistoricDustMixRate.44.1.1.bin
binFile:  BTLJ732600A41P0FGN.57.14.1.NandDiscovery.3576.2.0.bin
binFile:  BTLJ732600A41P0FGN.284.1.0.NLOG_NEI.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.1.0.bin
binFile:  BTLJ732600A41P0FGN.278.1.0.NLOG_RARE.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA3.txt
binFile:  BTLJ732600A41P0FGN.281.1.0.NLOG_UEC.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.265.1.0.NLOG_10D.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.263.1.0.NLOG_TEMP.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.3.0.bin
binFile:  BTLJ732600A41P0FGN.64.17.17.PliRestoreFooter.29184.2.0.bin
binFile:  BTLJ732600A41P0FGN.267.1.0.NLOG_BG.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.5.9.0.bis.1024.1.0.bin
binFile:  BTLJ732600A41P0FGN.41.5.1.DefragHistory.36300.2.0.bin
binFile:  BTLJ732600A41P0FGN.56.4.1.writeLatencyStats.4864.1.1.bin
binFile:  BTLJ732600A41P0FGN.9.1.1.LLFState.84.2.1.bin
binFile:  BTLJ732600A41P0FGN.280.1.0.NLOG_MRRf.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.258.5.1.DefragHistoryPart.4096.1.1.bin
binFile:  BTLJ732600A41P0FGN.261.1.0.NLOG_TC.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.284.1.0.NLOG_NEI.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.266.1.0.NLOG_HOST.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.271.1.0.NLOG_PLI.320.1.1.bin
binFile:  BTLJ732600A41P0FGN.61.29.4.PliRestoreHeader.51712.2.1.bin
binFile:  BTLJ732600A41P0FGN.270.1.0.NLOG_ERROR.1088.1.0.bin
binFile:  BTLJ732600A41P0FGN.286.1.0.NLOG_VAL.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.20.1.0.NplCmdStateInfo.96.1.0.bin
binFile:  BTLJ732600A41P0FGN.57.14.1.NandDiscovery.3576.2.1.bin
binFile:  BTLJ732600A41P0FGN.258.5.1.DefragHistoryPart.4096.1.0.bin
binFile:  BTLJ732600A41P0FGN.88.52.25.Stats.4096.2.0.bin
binFile:  BTLJ732600A41P0FGN.273.1.0.NLOG_STATS.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.264.1.0.NLOG_15M.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.288.1.0.NLOG_IRQ.320.3.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA2.txt
binFile:  BTLJ732600A41P0FGN.288.1.0.NLOG_IRQ.320.3.1.bin
binFile:  BTLJ732600A41P0FGN.255.1.0.NplMailboxState.32768.1.0.bin
binFile:  BTLJ732600A41P0FGN.169.3.0.pssRegs.88.2.0.bin
binFile:  BTLJ732600A41P0FGN.275.1.0.NLOG_HFR.4160.3.1.bin
binFile:  BTLJ732600A41P0FGN.250.1.0.BridgeStatus.12.1.0.bin
binFile:  BTLJ732600A41P0FGN.272.1.0.NLOG_IBM.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.282.1.0.NLOG_TRIM.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.45.13.3.Defrag_DustingQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN_NLOG_FILE_LIST.txt
binFile:  BTLJ732600A41P0FGN.281.1.0.NLOG_UEC.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.289.1.0.NplMailboxRegisters.284.2.0.bin
binFile:  BTLJ732600A41P0FGN.86.1.0.mrr_log.16128.2.0.bin
binFile:  BTLJ732600A41P0FGN.47.13.3.Defrag_WAQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.274.1.0.NLOG_TSTATS.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.49.13.3.DefragInfo.124.1.0.bin
binFile:  BTLJ732600A41P0FGN.61.29.4.PliRestoreHeader.51712.2.0.bin
binFile:  BTLJ732600A41P0FGN.277.1.0.NLOG_WARN.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.55.4.1.readLatencyStats.4864.1.0.bin
binFile:  BTLJ732600A41P0FGN.269.1.0.NLOG_SYS.576.1.1.bin
binFile:  BTLJ732600A41P0FGN.283.1.0.NLOG_MRRs.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.291.1.0.powerGov_Sysparam.224.2.0.bin
binFile:  BTLJ732600A41P0FGN.271.1.0.NLOG_PLI.320.1.0.bin
binFile:  BTLJ732600A41P0FGN.54.13.3.Defrag_ForcedReloQ.8.1.0.bin
binFile:  BTLJ732600A41P0FGN.89.1.0.mrr_state.768.2.0.bin
binFile:  BTLJ732600A41P0FGN.272.1.0.NLOG_IBM.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.DataArea3.bin
binFile:  BTLJ732600A41P0FGN.286.1.0.NLOG_VAL.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.269.1.0.NLOG_SYS.576.1.0.bin
binFile:  BTLJ732600A41P0FGN.283.1.0.NLOG_MRRs.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.276.1.0.NLOG_EHOST.2112.1.1.bin
binFile:  BTLJ732600A41P0FGN.282.1.0.NLOG_TRIM.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.50.13.3.Defrag_BandsDoneQueue.44.1.1.bin
binFile:  BTLJ732600A41P0FGN.274.1.0.NLOG_TSTATS.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.44.13.3.DefragInfoSlow.152.1.1.bin
binFile:  BTLJ732600A41P0FGN.275.1.0.NLOG_HFR.4160.3.0.bin
binFile:  BTLJ732600A41P0FGN.277.1.0.NLOG_WARN.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.260.1.0.NLOG_TEST.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.268.1.0.NLOG_UNIQUE.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.50.13.3.Defrag_BandsDoneQueue.44.1.0.bin
binFile:  BTLJ732600A41P0FGN.109.1.0.mrr_status.152832.2.0.bin
binFile:  BTLJ732600A41P0FGN.46.13.3.Defrag_LockedQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.56.4.1.writeLatencyStats.4864.1.0.bin
binFile:  BTLJ732600A41P0FGN.259.1.0.NLOG_ID.192.3.1.bin
binFile:  BTLJ732600A41P0FGN.259.1.0.NLOG_ID.192.3.0.bin
binFile:  BTLJ732600A41P0FGN.285.1.0.NLOG_DM.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.17.1.0.pssDebugTrace.528.2.0.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.2.0.bin
binFile:  BTLJ732600A41P0FGN.6.11.1.ThermalSensor.4740.2.0.bin
binFile:  BTLJ732600A41P0FGN.46.13.3.Defrag_LockedQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.278.1.0.NLOG_RARE.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.263.1.0.NLOG_TEMP.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.280.1.0.NLOG_MRRf.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.260.1.0.NLOG_TEST.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.DataArea2.bin
binFile:  BTLJ732600A41P0FGN.10.1.0.initState.48.2.0.bin
binFile:  BTLJ732600A41P0FGN.rc
binFile:  BTLJ732600A41P0FGN.257.1.0.NplSQueueRegisters.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.285.1.0.NLOG_DM.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.273.1.0.NLOG_STATS.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.251.1.0.nplInfoState.32.1.0.bin
binFile:  BTLJ732600A41P0FGN.225.1.0.InitStateCoreSync.12.2.0.bin
binFile:  BTLJ732600A41P0FGN.9.1.1.LLFState.84.2.0.bin
binFile:  BTLJ732600A41P0FGN.55.4.1.readLatencyStats.4864.1.1.bin
binFile:  BTLJ732600A41P0FGN.268.1.0.NLOG_UNIQUE.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.45.13.3.Defrag_DustingQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.44.13.3.DefragInfoSlow.152.1.0.bin
binFile:  BTLJ732600A41P0FGN.256.1.0.NplCQueueRegisters.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.279.1.0.NLOG_THERM.320.3.0.bin
binFile:  BTLJ732600A41P0FGN.88.52.25.Stats.4096.2.1.bin
binFile:  BTLJ732600A41P0FGN.225.1.0.InitStateCoreSync.12.2.1.bin
binFile:  BTLJ732600A41P0FGN.247.1.0.nvmeFeatures.56.1.0.bin
binFile:  BTLJ732600A41P0FGN.266.1.0.NLOG_HOST.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.267.1.0.NLOG_BG.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.254.1.0.qMgrSQList.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.52.1.2.DefragStateCounters.20.1.0.bin
binFile:  BTLJ732600A41P0FGN.51.13.3.Defrag_HistoricDustMixRate.44.1.0.bin
binFile:  BTLJ732600A41P0FGN.261.1.0.NLOG_TC.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.49.13.3.DefragInfo.124.1.1.bin
binFile:  BTLJ732600A41P0FGN.276.1.0.NLOG_EHOST.2112.1.0.bin
binFile:  BTLJ732600A41P0FGN.287.1.0.NLOG_OPAL.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.262.1.0.NLOG_DEBUG.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.64.17.17.PliRestoreFooter.29184.2.1.bin
binFile:  BTLJ732600A41P0FGN.264.1.0.NLOG_15M.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.41.5.1.DefragHistory.36300.2.1.bin
binFile:  BTLJ732600A41P0FGN.10.1.0.initState.48.2.1.bin
binFile:  BTLJ732600A41P0FGN.17.1.0.pssDebugTrace.528.1.0.bin
binFile:  BTLJ732600A41P0FGN.48.13.3.Defrag_WearLevelQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.1.1.0.FwSideTrace.131072.3.0.bin
binFile:  BTLJ732600A41P0FGN.DataArea1.bin
binFile:  BTLJ732600A41P0FGN.290.1.0.powerGov_Fconfig.188.2.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA1.txt
binFile:  BTLJ732600A41P0FGN.262.1.0.NLOG_DEBUG.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.270.1.0.NLOG_ERROR.1088.1.1.bin
binFile:  BTLJ732600A41P0FGN.8.11.1.ThermalStats.1024.2.0.bin
binFile:  BTLJ732600A41P0FGN.252.1.0.qMgrCQList.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.52.1.2.DefragStateCounters.20.1.1.bin
binFile:  BTLJ732600A41P0FGN.58.7.2.fConfigInfoTable.4016.2.0.bin
binFile:  BTLJ732600A41P0FGN.47.13.3.Defrag_WAQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.279.1.0.NLOG_THERM.320.3.1.bin
binFile:  BTLJ732600A41P0FGN.297.7.2.fConfigStream.3072.2.0.bin
binFile:  BTLJ732600A41P0FGN.297.7.2.fConfigStream.3072.2.1.bin
Generating: /home/lab/Documents/parse/workload-fail/workload-fail8_2019-09-13-15-52-30-327000

Project Directory: /home/lab/Documents/parse/arbordaleplus_t2

Bin Files Directory: /home/lab/Documents/parse/workload-fail/workload-fail8_2019-09-13-15-52-30-327000

Creating Telemetry Objects from Binaries...
binFile:  BTLJ732600A41P0FGN.54.13.3.Defrag_ForcedReloQ.8.1.1.bin
binFile:  BTLJ732600A41P0FGN.169.3.0.pssRegs.88.1.0.bin
binFile:  BTLJ732600A41P0FGN.287.1.0.NLOG_OPAL.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.58.7.2.fConfigInfoTable.4016.2.1.bin
binFile:  BTLJ732600A41P0FGN.265.1.0.NLOG_10D.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.2.1.0.BlSideTrace.131072.3.0.bin
binFile:  BTLJ732600A41P0FGN.48.13.3.Defrag_WearLevelQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.51.13.3.Defrag_HistoricDustMixRate.44.1.1.bin
binFile:  BTLJ732600A41P0FGN.57.14.1.NandDiscovery.3576.2.0.bin
binFile:  BTLJ732600A41P0FGN.284.1.0.NLOG_NEI.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.1.0.bin
binFile:  BTLJ732600A41P0FGN.278.1.0.NLOG_RARE.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA3.txt
binFile:  BTLJ732600A41P0FGN.281.1.0.NLOG_UEC.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.265.1.0.NLOG_10D.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.263.1.0.NLOG_TEMP.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.3.0.bin
binFile:  BTLJ732600A41P0FGN.64.17.17.PliRestoreFooter.29184.2.0.bin
binFile:  BTLJ732600A41P0FGN.267.1.0.NLOG_BG.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.5.9.0.bis.1024.1.0.bin
binFile:  BTLJ732600A41P0FGN.41.5.1.DefragHistory.36300.2.0.bin
binFile:  BTLJ732600A41P0FGN.56.4.1.writeLatencyStats.4864.1.1.bin
binFile:  BTLJ732600A41P0FGN.9.1.1.LLFState.84.2.1.bin
binFile:  BTLJ732600A41P0FGN.280.1.0.NLOG_MRRf.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.258.5.1.DefragHistoryPart.4096.1.1.bin
binFile:  BTLJ732600A41P0FGN.261.1.0.NLOG_TC.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.284.1.0.NLOG_NEI.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.266.1.0.NLOG_HOST.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.271.1.0.NLOG_PLI.320.1.1.bin
binFile:  BTLJ732600A41P0FGN.61.29.4.PliRestoreHeader.51712.2.1.bin
binFile:  BTLJ732600A41P0FGN.270.1.0.NLOG_ERROR.1088.1.0.bin
binFile:  BTLJ732600A41P0FGN.286.1.0.NLOG_VAL.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.20.1.0.NplCmdStateInfo.96.1.0.bin
binFile:  BTLJ732600A41P0FGN.57.14.1.NandDiscovery.3576.2.1.bin
binFile:  BTLJ732600A41P0FGN.258.5.1.DefragHistoryPart.4096.1.0.bin
binFile:  BTLJ732600A41P0FGN.88.52.25.Stats.4096.2.0.bin
binFile:  BTLJ732600A41P0FGN.273.1.0.NLOG_STATS.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.264.1.0.NLOG_15M.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.288.1.0.NLOG_IRQ.320.3.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA2.txt
binFile:  BTLJ732600A41P0FGN.288.1.0.NLOG_IRQ.320.3.1.bin
binFile:  BTLJ732600A41P0FGN.255.1.0.NplMailboxState.32768.1.0.bin
binFile:  BTLJ732600A41P0FGN.169.3.0.pssRegs.88.2.0.bin
binFile:  BTLJ732600A41P0FGN.275.1.0.NLOG_HFR.4160.3.1.bin
binFile:  BTLJ732600A41P0FGN.250.1.0.BridgeStatus.12.1.0.bin
binFile:  BTLJ732600A41P0FGN.272.1.0.NLOG_IBM.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.282.1.0.NLOG_TRIM.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.45.13.3.Defrag_DustingQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN_NLOG_FILE_LIST.txt
binFile:  BTLJ732600A41P0FGN.281.1.0.NLOG_UEC.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.289.1.0.NplMailboxRegisters.284.2.0.bin
binFile:  BTLJ732600A41P0FGN.86.1.0.mrr_log.16128.2.0.bin
binFile:  BTLJ732600A41P0FGN.47.13.3.Defrag_WAQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.274.1.0.NLOG_TSTATS.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.49.13.3.DefragInfo.124.1.0.bin
binFile:  BTLJ732600A41P0FGN.61.29.4.PliRestoreHeader.51712.2.0.bin
binFile:  BTLJ732600A41P0FGN.277.1.0.NLOG_WARN.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.55.4.1.readLatencyStats.4864.1.0.bin
binFile:  BTLJ732600A41P0FGN.269.1.0.NLOG_SYS.576.1.1.bin
binFile:  BTLJ732600A41P0FGN.283.1.0.NLOG_MRRs.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.291.1.0.powerGov_Sysparam.224.2.0.bin
binFile:  BTLJ732600A41P0FGN.271.1.0.NLOG_PLI.320.1.0.bin
binFile:  BTLJ732600A41P0FGN.54.13.3.Defrag_ForcedReloQ.8.1.0.bin
binFile:  BTLJ732600A41P0FGN.89.1.0.mrr_state.768.2.0.bin
binFile:  BTLJ732600A41P0FGN.272.1.0.NLOG_IBM.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.DataArea3.bin
binFile:  BTLJ732600A41P0FGN.286.1.0.NLOG_VAL.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.269.1.0.NLOG_SYS.576.1.0.bin
binFile:  BTLJ732600A41P0FGN.283.1.0.NLOG_MRRs.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.276.1.0.NLOG_EHOST.2112.1.1.bin
binFile:  BTLJ732600A41P0FGN.282.1.0.NLOG_TRIM.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.50.13.3.Defrag_BandsDoneQueue.44.1.1.bin
binFile:  BTLJ732600A41P0FGN.274.1.0.NLOG_TSTATS.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.44.13.3.DefragInfoSlow.152.1.1.bin
binFile:  BTLJ732600A41P0FGN.275.1.0.NLOG_HFR.4160.3.0.bin
binFile:  BTLJ732600A41P0FGN.277.1.0.NLOG_WARN.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.260.1.0.NLOG_TEST.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.268.1.0.NLOG_UNIQUE.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.50.13.3.Defrag_BandsDoneQueue.44.1.0.bin
binFile:  BTLJ732600A41P0FGN.109.1.0.mrr_status.152832.2.0.bin
binFile:  BTLJ732600A41P0FGN.46.13.3.Defrag_LockedQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.56.4.1.writeLatencyStats.4864.1.0.bin
binFile:  BTLJ732600A41P0FGN.259.1.0.NLOG_ID.192.3.1.bin
binFile:  BTLJ732600A41P0FGN.259.1.0.NLOG_ID.192.3.0.bin
binFile:  BTLJ732600A41P0FGN.285.1.0.NLOG_DM.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.17.1.0.pssDebugTrace.528.2.0.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.2.0.bin
binFile:  BTLJ732600A41P0FGN.6.11.1.ThermalSensor.4740.2.0.bin
binFile:  BTLJ732600A41P0FGN.46.13.3.Defrag_LockedQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.278.1.0.NLOG_RARE.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.263.1.0.NLOG_TEMP.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.280.1.0.NLOG_MRRf.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.260.1.0.NLOG_TEST.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.DataArea2.bin
binFile:  BTLJ732600A41P0FGN.10.1.0.initState.48.2.0.bin
binFile:  BTLJ732600A41P0FGN.rc
binFile:  BTLJ732600A41P0FGN.257.1.0.NplSQueueRegisters.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.285.1.0.NLOG_DM.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.273.1.0.NLOG_STATS.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.251.1.0.nplInfoState.32.1.0.bin
binFile:  BTLJ732600A41P0FGN.225.1.0.InitStateCoreSync.12.2.0.bin
binFile:  BTLJ732600A41P0FGN.9.1.1.LLFState.84.2.0.bin
binFile:  BTLJ732600A41P0FGN.55.4.1.readLatencyStats.4864.1.1.bin
binFile:  BTLJ732600A41P0FGN.268.1.0.NLOG_UNIQUE.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.45.13.3.Defrag_DustingQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.44.13.3.DefragInfoSlow.152.1.0.bin
binFile:  BTLJ732600A41P0FGN.256.1.0.NplCQueueRegisters.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.279.1.0.NLOG_THERM.320.3.0.bin
binFile:  BTLJ732600A41P0FGN.88.52.25.Stats.4096.2.1.bin
binFile:  BTLJ732600A41P0FGN.225.1.0.InitStateCoreSync.12.2.1.bin
binFile:  BTLJ732600A41P0FGN.247.1.0.nvmeFeatures.56.1.0.bin
binFile:  BTLJ732600A41P0FGN.266.1.0.NLOG_HOST.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.267.1.0.NLOG_BG.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.254.1.0.qMgrSQList.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.52.1.2.DefragStateCounters.20.1.0.bin
binFile:  BTLJ732600A41P0FGN.51.13.3.Defrag_HistoricDustMixRate.44.1.0.bin
binFile:  BTLJ732600A41P0FGN.261.1.0.NLOG_TC.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.49.13.3.DefragInfo.124.1.1.bin
binFile:  BTLJ732600A41P0FGN.276.1.0.NLOG_EHOST.2112.1.0.bin
binFile:  BTLJ732600A41P0FGN.287.1.0.NLOG_OPAL.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.262.1.0.NLOG_DEBUG.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.64.17.17.PliRestoreFooter.29184.2.1.bin
binFile:  BTLJ732600A41P0FGN.264.1.0.NLOG_15M.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.41.5.1.DefragHistory.36300.2.1.bin
binFile:  BTLJ732600A41P0FGN.10.1.0.initState.48.2.1.bin
binFile:  BTLJ732600A41P0FGN.17.1.0.pssDebugTrace.528.1.0.bin
binFile:  BTLJ732600A41P0FGN.48.13.3.Defrag_WearLevelQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.1.1.0.FwSideTrace.131072.3.0.bin
binFile:  BTLJ732600A41P0FGN.DataArea1.bin
binFile:  BTLJ732600A41P0FGN.290.1.0.powerGov_Fconfig.188.2.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA1.txt
binFile:  BTLJ732600A41P0FGN.262.1.0.NLOG_DEBUG.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.270.1.0.NLOG_ERROR.1088.1.1.bin
binFile:  BTLJ732600A41P0FGN.8.11.1.ThermalStats.1024.2.0.bin
binFile:  BTLJ732600A41P0FGN.252.1.0.qMgrCQList.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.52.1.2.DefragStateCounters.20.1.1.bin
binFile:  BTLJ732600A41P0FGN.58.7.2.fConfigInfoTable.4016.2.0.bin
binFile:  BTLJ732600A41P0FGN.47.13.3.Defrag_WAQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.279.1.0.NLOG_THERM.320.3.1.bin
binFile:  BTLJ732600A41P0FGN.297.7.2.fConfigStream.3072.2.0.bin
binFile:  BTLJ732600A41P0FGN.297.7.2.fConfigStream.3072.2.1.bin
Generating: /home/lab/Documents/parse/workload-fail/workload-fail9_2019-09-13-15-52-30-327000

Project Directory: /home/lab/Documents/parse/arbordaleplus_t2

Bin Files Directory: /home/lab/Documents/parse/workload-fail/workload-fail9_2019-09-13-15-52-30-327000

Creating Telemetry Objects from Binaries...
binFile:  BTLJ732600A41P0FGN.54.13.3.Defrag_ForcedReloQ.8.1.1.bin
binFile:  BTLJ732600A41P0FGN.169.3.0.pssRegs.88.1.0.bin
binFile:  BTLJ732600A41P0FGN.287.1.0.NLOG_OPAL.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.58.7.2.fConfigInfoTable.4016.2.1.bin
binFile:  BTLJ732600A41P0FGN.265.1.0.NLOG_10D.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.2.1.0.BlSideTrace.131072.3.0.bin
binFile:  BTLJ732600A41P0FGN.48.13.3.Defrag_WearLevelQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.51.13.3.Defrag_HistoricDustMixRate.44.1.1.bin
binFile:  BTLJ732600A41P0FGN.57.14.1.NandDiscovery.3576.2.0.bin
binFile:  BTLJ732600A41P0FGN.284.1.0.NLOG_NEI.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.1.0.bin
binFile:  BTLJ732600A41P0FGN.278.1.0.NLOG_RARE.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA3.txt
binFile:  BTLJ732600A41P0FGN.281.1.0.NLOG_UEC.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.265.1.0.NLOG_10D.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.263.1.0.NLOG_TEMP.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.3.0.bin
binFile:  BTLJ732600A41P0FGN.64.17.17.PliRestoreFooter.29184.2.0.bin
binFile:  BTLJ732600A41P0FGN.267.1.0.NLOG_BG.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.5.9.0.bis.1024.1.0.bin
binFile:  BTLJ732600A41P0FGN.41.5.1.DefragHistory.36300.2.0.bin
binFile:  BTLJ732600A41P0FGN.56.4.1.writeLatencyStats.4864.1.1.bin
binFile:  BTLJ732600A41P0FGN.9.1.1.LLFState.84.2.1.bin
binFile:  BTLJ732600A41P0FGN.280.1.0.NLOG_MRRf.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.258.5.1.DefragHistoryPart.4096.1.1.bin
binFile:  BTLJ732600A41P0FGN.261.1.0.NLOG_TC.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.284.1.0.NLOG_NEI.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.266.1.0.NLOG_HOST.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.271.1.0.NLOG_PLI.320.1.1.bin
binFile:  BTLJ732600A41P0FGN.61.29.4.PliRestoreHeader.51712.2.1.bin
binFile:  BTLJ732600A41P0FGN.270.1.0.NLOG_ERROR.1088.1.0.bin
binFile:  BTLJ732600A41P0FGN.286.1.0.NLOG_VAL.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.20.1.0.NplCmdStateInfo.96.1.0.bin
binFile:  BTLJ732600A41P0FGN.57.14.1.NandDiscovery.3576.2.1.bin
binFile:  BTLJ732600A41P0FGN.258.5.1.DefragHistoryPart.4096.1.0.bin
binFile:  BTLJ732600A41P0FGN.88.52.25.Stats.4096.2.0.bin
binFile:  BTLJ732600A41P0FGN.273.1.0.NLOG_STATS.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.264.1.0.NLOG_15M.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.288.1.0.NLOG_IRQ.320.3.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA2.txt
binFile:  BTLJ732600A41P0FGN.288.1.0.NLOG_IRQ.320.3.1.bin
binFile:  BTLJ732600A41P0FGN.255.1.0.NplMailboxState.32768.1.0.bin
binFile:  BTLJ732600A41P0FGN.169.3.0.pssRegs.88.2.0.bin
binFile:  BTLJ732600A41P0FGN.275.1.0.NLOG_HFR.4160.3.1.bin
binFile:  BTLJ732600A41P0FGN.250.1.0.BridgeStatus.12.1.0.bin
binFile:  BTLJ732600A41P0FGN.272.1.0.NLOG_IBM.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.282.1.0.NLOG_TRIM.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.45.13.3.Defrag_DustingQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN_NLOG_FILE_LIST.txt
binFile:  BTLJ732600A41P0FGN.281.1.0.NLOG_UEC.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.289.1.0.NplMailboxRegisters.284.2.0.bin
binFile:  BTLJ732600A41P0FGN.86.1.0.mrr_log.16128.2.0.bin
binFile:  BTLJ732600A41P0FGN.47.13.3.Defrag_WAQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.274.1.0.NLOG_TSTATS.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.49.13.3.DefragInfo.124.1.0.bin
binFile:  BTLJ732600A41P0FGN.61.29.4.PliRestoreHeader.51712.2.0.bin
binFile:  BTLJ732600A41P0FGN.277.1.0.NLOG_WARN.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.55.4.1.readLatencyStats.4864.1.0.bin
binFile:  BTLJ732600A41P0FGN.269.1.0.NLOG_SYS.576.1.1.bin
binFile:  BTLJ732600A41P0FGN.283.1.0.NLOG_MRRs.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.291.1.0.powerGov_Sysparam.224.2.0.bin
binFile:  BTLJ732600A41P0FGN.271.1.0.NLOG_PLI.320.1.0.bin
binFile:  BTLJ732600A41P0FGN.54.13.3.Defrag_ForcedReloQ.8.1.0.bin
binFile:  BTLJ732600A41P0FGN.89.1.0.mrr_state.768.2.0.bin
binFile:  BTLJ732600A41P0FGN.272.1.0.NLOG_IBM.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.DataArea3.bin
binFile:  BTLJ732600A41P0FGN.286.1.0.NLOG_VAL.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.269.1.0.NLOG_SYS.576.1.0.bin
binFile:  BTLJ732600A41P0FGN.283.1.0.NLOG_MRRs.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.276.1.0.NLOG_EHOST.2112.1.1.bin
binFile:  BTLJ732600A41P0FGN.282.1.0.NLOG_TRIM.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.50.13.3.Defrag_BandsDoneQueue.44.1.1.bin
binFile:  BTLJ732600A41P0FGN.274.1.0.NLOG_TSTATS.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.44.13.3.DefragInfoSlow.152.1.1.bin
binFile:  BTLJ732600A41P0FGN.275.1.0.NLOG_HFR.4160.3.0.bin
binFile:  BTLJ732600A41P0FGN.277.1.0.NLOG_WARN.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.260.1.0.NLOG_TEST.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.268.1.0.NLOG_UNIQUE.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.50.13.3.Defrag_BandsDoneQueue.44.1.0.bin
binFile:  BTLJ732600A41P0FGN.109.1.0.mrr_status.152832.2.0.bin
binFile:  BTLJ732600A41P0FGN.46.13.3.Defrag_LockedQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.56.4.1.writeLatencyStats.4864.1.0.bin
binFile:  BTLJ732600A41P0FGN.259.1.0.NLOG_ID.192.3.1.bin
binFile:  BTLJ732600A41P0FGN.259.1.0.NLOG_ID.192.3.0.bin
binFile:  BTLJ732600A41P0FGN.285.1.0.NLOG_DM.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.17.1.0.pssDebugTrace.528.2.0.bin
binFile:  BTLJ732600A41P0FGN.296.1.0.telemetryObjectDAValidation.8.2.0.bin
binFile:  BTLJ732600A41P0FGN.6.11.1.ThermalSensor.4740.2.0.bin
binFile:  BTLJ732600A41P0FGN.46.13.3.Defrag_LockedQueue.132.1.1.bin
binFile:  BTLJ732600A41P0FGN.278.1.0.NLOG_RARE.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.263.1.0.NLOG_TEMP.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.280.1.0.NLOG_MRRf.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.260.1.0.NLOG_TEST.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.DataArea2.bin
binFile:  BTLJ732600A41P0FGN.10.1.0.initState.48.2.0.bin
binFile:  BTLJ732600A41P0FGN.rc
binFile:  BTLJ732600A41P0FGN.257.1.0.NplSQueueRegisters.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.285.1.0.NLOG_DM.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.273.1.0.NLOG_STATS.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.251.1.0.nplInfoState.32.1.0.bin
binFile:  BTLJ732600A41P0FGN.225.1.0.InitStateCoreSync.12.2.0.bin
binFile:  BTLJ732600A41P0FGN.9.1.1.LLFState.84.2.0.bin
binFile:  BTLJ732600A41P0FGN.55.4.1.readLatencyStats.4864.1.1.bin
binFile:  BTLJ732600A41P0FGN.268.1.0.NLOG_UNIQUE.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.45.13.3.Defrag_DustingQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.44.13.3.DefragInfoSlow.152.1.0.bin
binFile:  BTLJ732600A41P0FGN.256.1.0.NplCQueueRegisters.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.279.1.0.NLOG_THERM.320.3.0.bin
binFile:  BTLJ732600A41P0FGN.88.52.25.Stats.4096.2.1.bin
binFile:  BTLJ732600A41P0FGN.225.1.0.InitStateCoreSync.12.2.1.bin
binFile:  BTLJ732600A41P0FGN.247.1.0.nvmeFeatures.56.1.0.bin
binFile:  BTLJ732600A41P0FGN.266.1.0.NLOG_HOST.1088.3.0.bin
binFile:  BTLJ732600A41P0FGN.267.1.0.NLOG_BG.1088.3.1.bin
binFile:  BTLJ732600A41P0FGN.254.1.0.qMgrSQList.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.52.1.2.DefragStateCounters.20.1.0.bin
binFile:  BTLJ732600A41P0FGN.51.13.3.Defrag_HistoricDustMixRate.44.1.0.bin
binFile:  BTLJ732600A41P0FGN.261.1.0.NLOG_TC.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.49.13.3.DefragInfo.124.1.1.bin
binFile:  BTLJ732600A41P0FGN.276.1.0.NLOG_EHOST.2112.1.0.bin
binFile:  BTLJ732600A41P0FGN.287.1.0.NLOG_OPAL.576.3.0.bin
binFile:  BTLJ732600A41P0FGN.262.1.0.NLOG_DEBUG.2112.3.1.bin
binFile:  BTLJ732600A41P0FGN.64.17.17.PliRestoreFooter.29184.2.1.bin
binFile:  BTLJ732600A41P0FGN.264.1.0.NLOG_15M.576.3.1.bin
binFile:  BTLJ732600A41P0FGN.41.5.1.DefragHistory.36300.2.1.bin
binFile:  BTLJ732600A41P0FGN.10.1.0.initState.48.2.1.bin
binFile:  BTLJ732600A41P0FGN.17.1.0.pssDebugTrace.528.1.0.bin
binFile:  BTLJ732600A41P0FGN.48.13.3.Defrag_WearLevelQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.1.1.0.FwSideTrace.131072.3.0.bin
binFile:  BTLJ732600A41P0FGN.DataArea1.bin
binFile:  BTLJ732600A41P0FGN.290.1.0.powerGov_Fconfig.188.2.0.bin
binFile:  BTLJ732600A41P0FGN.validationtxt.DA1.txt
binFile:  BTLJ732600A41P0FGN.262.1.0.NLOG_DEBUG.2112.3.0.bin
binFile:  BTLJ732600A41P0FGN.270.1.0.NLOG_ERROR.1088.1.1.bin
binFile:  BTLJ732600A41P0FGN.8.11.1.ThermalStats.1024.2.0.bin
binFile:  BTLJ732600A41P0FGN.252.1.0.qMgrCQList.2080.1.0.bin
binFile:  BTLJ732600A41P0FGN.52.1.2.DefragStateCounters.20.1.1.bin
binFile:  BTLJ732600A41P0FGN.58.7.2.fConfigInfoTable.4016.2.0.bin
binFile:  BTLJ732600A41P0FGN.47.13.3.Defrag_WAQueue.132.1.0.bin
binFile:  BTLJ732600A41P0FGN.279.1.0.NLOG_THERM.320.3.1.bin
binFile:  BTLJ732600A41P0FGN.297.7.2.fConfigStream.3072.2.0.bin
binFile:  BTLJ732600A41P0FGN.297.7.2.fConfigStream.3072.2.1.bin
['/home/lab/Documents/parse/./workload-fail-txt/workload-fail0_2019-09-13-15-52-30-327000.txt', '/home/lab/Documents/parse/./workload-fail-txt/workload-fail1_2019-09-13-15-52-30-327000.txt', '/home/lab/Documents/parse/./workload-fail-txt/workload-fail2_2019-09-13-15-52-30-327000.txt', '/home/lab/Documents/parse/./workload-fail-txt/workload-fail3_2019-09-13-15-52-30-327000.txt', '/home/lab/Documents/parse/./workload-fail-txt/workload-fail4_2019-09-13-15-52-30-327000.txt', '/home/lab/Documents/parse/./workload-fail-txt/workload-fail5_2019-09-13-15-52-30-327000.txt', '/home/lab/Documents/parse/./workload-fail-txt/workload-fail6_2019-09-13-15-52-30-327000.txt', '/home/lab/Documents/parse/./workload-fail-txt/workload-fail7_2019-09-13-15-52-30-327000.txt', '/home/lab/Documents/parse/./workload-fail-txt/workload-fail8_2019-09-13-15-52-30-327000.txt', '/home/lab/Documents/parse/./workload-fail-txt/workload-fail9_2019-09-13-15-52-30-327000.txt']
Digesting file: /home/lab/Documents/parse/./workload-fail-txt/workload-fail0_2019-09-13-15-52-30-327000.txt
Digesting file: /home/lab/Documents/parse/./workload-fail-txt/workload-fail1_2019-09-13-15-52-30-327000.txt
Digesting file: /home/lab/Documents/parse/./workload-fail-txt/workload-fail2_2019-09-13-15-52-30-327000.txt
Digesting file: /home/lab/Documents/parse/./workload-fail-txt/workload-fail3_2019-09-13-15-52-30-327000.txt
Digesting file: /home/lab/Documents/parse/./workload-fail-txt/workload-fail4_2019-09-13-15-52-30-327000.txt
Digesting file: /home/lab/Documents/parse/./workload-fail-txt/workload-fail5_2019-09-13-15-52-30-327000.txt
Digesting file: /home/lab/Documents/parse/./workload-fail-txt/workload-fail6_2019-09-13-15-52-30-327000.txt
Digesting file: /home/lab/Documents/parse/./workload-fail-txt/workload-fail7_2019-09-13-15-52-30-327000.txt
Digesting file: /home/lab/Documents/parse/./workload-fail-txt/workload-fail8_2019-09-13-15-52-30-327000.txt
Digesting file: /home/lab/Documents/parse/./workload-fail-txt/workload-fail9_2019-09-13-15-52-30-327000.txt
Execution time: 0:00:00.264291

```

 </p>
</details>

## visualizeTS.py 
<details><summary>Click to Expand</summary>
<p>

#### Log content below.

```console
$ python visualizeTS.py --outfile workload-fail --targetObject ThermalSensor --targetFields nandtemperature.currenthighestnandtemp.nandtemp,asictemperature.currenttemp,compositetemperature.currenttemp --inputFile workload-fail-txt/workload-fail.ini --debug True
Processing .ini file...
Object being processed: uid-6
Field being processed: compositetemperature.currenttemp
Field being processed: asictemperature.currenttemp
Field being processed: nandtemperature.currenthighestnandtemp.nandtemp
Execution time: 0:00:00.309241

```

 </p>
</details>

## DefragHistoryGrapher.py 
<details><summary>Click to Expand</summary>
<p>

#### Log content below.

```console
$ python DefragHistoryGrapher.py

```

 </p>
</details>

## loadAndProbeSystem (Linux).py 
<details><summary>Click to Expand</summary>
<p>

#### Log content below.
```console
$ sudo python loadAndProbeSystem.py --driveNumber 0 --inputFile rand-write.sh --identifier test --parse False --outputDir binary-test --debug True
Importing Paths:  /home/lab/Documents/parse /home/lab/Documents/parse/bin /home/lab/Documents/parse/ctypeautogen
Running script for Linux based OS
Process will run for: 120 seconds after the drive has been prepped
Writing to: binary-test/test_2020-07-22-21-31-32-352817.bin
Writing to: binary-test/test_2020-07-22-21-31-33-577193.bin
Writing to: binary-test/test_2020-07-22-21-31-34-800537.bin
Writing to: binary-test/test_2020-07-22-21-31-36-069347.bin
Writing to: binary-test/test_2020-07-22-21-31-37-242269.bin
Writing to: binary-test/test_2020-07-22-21-31-38-509766.bin
Writing to: binary-test/test_2020-07-22-21-31-39-812732.bin
Writing to: binary-test/test_2020-07-22-21-31-41-114346.bin
Writing to: binary-test/test_2020-07-22-21-31-42-501112.bin
Writing to: binary-test/test_2020-07-22-21-31-43-788387.bin
Writing to: binary-test/test_2020-07-22-21-31-45-206110.bin
Writing to: binary-test/test_2020-07-22-21-31-46-470809.bin
Writing to: binary-test/test_2020-07-22-21-31-47-709131.bin
Writing to: binary-test/test_2020-07-22-21-31-48-981719.bin
Writing to: binary-test/test_2020-07-22-21-31-50-202654.bin
Writing to: binary-test/test_2020-07-22-21-31-51-421277.bin
Writing to: binary-test/test_2020-07-22-21-31-52-701498.bin
Writing to: binary-test/test_2020-07-22-21-31-54-057793.bin
Writing to: binary-test/test_2020-07-22-21-31-55-326096.bin
Writing to: binary-test/test_2020-07-22-21-31-56-551781.bin
Writing to: binary-test/test_2020-07-22-21-31-57-817412.bin
Writing to: binary-test/test_2020-07-22-21-31-59-114116.bin
Writing to: binary-test/test_2020-07-22-21-32-00-421791.bin
Writing to: binary-test/test_2020-07-22-21-32-01-723051.bin
Writing to: binary-test/test_2020-07-22-21-32-02-922179.bin
Writing to: binary-test/test_2020-07-22-21-32-04-171952.bin
Writing to: binary-test/test_2020-07-22-21-32-05-388462.bin
Writing to: binary-test/test_2020-07-22-21-32-06-688505.bin
Writing to: binary-test/test_2020-07-22-21-32-07-914780.bin
Writing to: binary-test/test_2020-07-22-21-32-09-157239.bin
Writing to: binary-test/test_2020-07-22-21-32-10-403670.bin
Writing to: binary-test/test_2020-07-22-21-32-11-535315.bin
Writing to: binary-test/test_2020-07-22-21-32-12-825576.bin
Writing to: binary-test/test_2020-07-22-21-32-14-110232.bin
Writing to: binary-test/test_2020-07-22-21-32-15-497468.bin
Writing to: binary-test/test_2020-07-22-21-32-16-763343.bin
Writing to: binary-test/test_2020-07-22-21-32-17-990208.bin
Writing to: binary-test/test_2020-07-22-21-32-19-323592.bin
Writing to: binary-test/test_2020-07-22-21-32-20-579166.bin
Writing to: binary-test/test_2020-07-22-21-32-21-830302.bin
Writing to: binary-test/test_2020-07-22-21-32-23-049512.bin
Writing to: binary-test/test_2020-07-22-21-32-24-315537.bin
Writing to: binary-test/test_2020-07-22-21-32-25-693373.bin
Writing to: binary-test/test_2020-07-22-21-32-26-923775.bin
Writing to: binary-test/test_2020-07-22-21-32-28-193842.bin
Writing to: binary-test/test_2020-07-22-21-32-29-475000.bin
Writing to: binary-test/test_2020-07-22-21-32-30-750866.bin
Writing to: binary-test/test_2020-07-22-21-32-32-043336.bin
Writing to: binary-test/test_2020-07-22-21-32-33-323610.bin
Writing to: binary-test/test_2020-07-22-21-32-34-572413.bin
Writing to: binary-test/test_2020-07-22-21-32-35-830712.bin
Writing to: binary-test/test_2020-07-22-21-32-37-072255.bin
Writing to: binary-test/test_2020-07-22-21-32-38-314010.bin
Writing to: binary-test/test_2020-07-22-21-32-39-550646.bin
Writing to: binary-test/test_2020-07-22-21-32-40-829264.bin
Writing to: binary-test/test_2020-07-22-21-32-42-164555.bin
Writing to: binary-test/test_2020-07-22-21-32-43-529931.bin
Writing to: binary-test/test_2020-07-22-21-32-44-834099.bin
Writing to: binary-test/test_2020-07-22-21-32-46-030020.bin
Writing to: binary-test/test_2020-07-22-21-32-47-301074.bin
Writing to: binary-test/test_2020-07-22-21-32-48-588327.bin
Writing to: binary-test/test_2020-07-22-21-32-49-889466.bin
Writing to: binary-test/test_2020-07-22-21-32-51-118816.bin
Writing to: binary-test/test_2020-07-22-21-32-52-356251.bin
Writing to: binary-test/test_2020-07-22-21-32-53-713190.bin
Writing to: binary-test/test_2020-07-22-21-32-54-970883.bin
Writing to: binary-test/test_2020-07-22-21-32-56-227441.bin
Writing to: binary-test/test_2020-07-22-21-32-57-450856.bin
Writing to: binary-test/test_2020-07-22-21-32-58-691475.bin
Writing to: binary-test/test_2020-07-22-21-32-59-946812.bin
Writing to: binary-test/test_2020-07-22-21-33-01-241295.bin
Writing to: binary-test/test_2020-07-22-21-33-02-528534.bin
Writing to: binary-test/test_2020-07-22-21-33-03-960652.bin
Writing to: binary-test/test_2020-07-22-21-33-05-341258.bin
Writing to: binary-test/test_2020-07-22-21-33-06-667514.bin
Writing to: binary-test/test_2020-07-22-21-33-08-016491.bin
Writing to: binary-test/test_2020-07-22-21-33-09-364117.bin
Writing to: binary-test/test_2020-07-22-21-33-10-581464.bin
Writing to: binary-test/test_2020-07-22-21-33-11-925629.bin
Writing to: binary-test/test_2020-07-22-21-33-13-187562.bin
Writing to: binary-test/test_2020-07-22-21-33-14-513340.bin
Writing to: binary-test/test_2020-07-22-21-33-15-854054.bin
Writing to: binary-test/test_2020-07-22-21-33-17-234613.bin
Writing to: binary-test/test_2020-07-22-21-33-18-479847.bin
Writing to: binary-test/test_2020-07-22-21-33-19-863941.bin
Writing to: binary-test/test_2020-07-22-21-33-21-150337.bin
Writing to: binary-test/test_2020-07-22-21-33-22-416275.bin
Writing to: binary-test/test_2020-07-22-21-33-23-760370.bin
Writing to: binary-test/test_2020-07-22-21-33-24-991496.bin
Writing to: binary-test/test_2020-07-22-21-33-26-203582.bin
Writing to: binary-test/test_2020-07-22-21-33-27-422578.bin
Writing to: binary-test/test_2020-07-22-21-33-28-732539.bin
Writing to: binary-test/test_2020-07-22-21-33-29-977543.bin
Writing to: binary-test/test_2020-07-22-21-33-31-253429.bin
```

 </p>
</details>

## loadAndProbeSystem (Windows).py 
<details><summary>Click to Expand</summary>
<p>

#### Log content below.
```console
$ python loadAndProbeSystem.py --driveNumber 1 --inputFile Thermal-4KSW1QD1W.csv --identifier test --parse False --outputDir binaries3 --debug True
Importing Paths:  C:\Users\lab\Documents\parse C:\Users\lab\Documents\parse\bin C:\Users\lab\Documents\parse\ctypeautogen
Running script for Windows OS
Time used for collecting telemetry: 120 seconds

Microsoft DiskPart version 6.3.9600

Copyright (C) 1999-2013 Microsoft Corporation.
On computer: LM-313-03-H1

Disk 1 is now the selected disk.

DiskPart succeeded in cleaning the disk.

DiskPart successfully converted the selected disk to MBR format.

DiskPart succeeded in creating the specified partition.


    0 percent completed
    0 percent completed
    0 percent completed
    0 percent completed
    0 percent completed
    0 percent completed
  100 percent completed


DiskPart successfully formatted the volume.

DiskPart successfully assigned the drive letter or mount point.

Leaving DiskPart...

The drive was partitioned successfully!
Parsing Schedule File - Thermal-4KSW1QD1W.csv
Parsing Complete
Preping drive(s) with 64KB sequential write.
Drive prep complete.
Pulling Telemetry from drive 1 for 120 seconds
Writing to: binaries3\test_2020-07-22-21-52-00-496000.bin
Writing to: binaries3\test_2020-07-22-21-52-02-248000.bin
Writing to: binaries3\test_2020-07-22-21-52-04-147000.bin
Writing to: binaries3\test_2020-07-22-21-52-06-045000.bin
Writing to: binaries3\test_2020-07-22-21-52-08-001000.bin
Writing to: binaries3\test_2020-07-22-21-52-09-924000.bin
Writing to: binaries3\test_2020-07-22-21-52-11-844000.bin
Writing to: binaries3\test_2020-07-22-21-52-13-778000.bin
Writing to: binaries3\test_2020-07-22-21-52-15-691000.bin
Writing to: binaries3\test_2020-07-22-21-52-17-610000.bin
Writing to: binaries3\test_2020-07-22-21-52-19-545000.bin
Writing to: binaries3\test_2020-07-22-21-52-21-500000.bin
Writing to: binaries3\test_2020-07-22-21-52-23-435000.bin
Writing to: binaries3\test_2020-07-22-21-52-25-350000.bin
Writing to: binaries3\test_2020-07-22-21-52-27-258000.bin
Writing to: binaries3\test_2020-07-22-21-52-29-182000.bin
Writing to: binaries3\test_2020-07-22-21-52-31-106000.bin
Writing to: binaries3\test_2020-07-22-21-52-33-041000.bin
Writing to: binaries3\test_2020-07-22-21-52-34-970000.bin
Writing to: binaries3\test_2020-07-22-21-52-36-868000.bin
Writing to: binaries3\test_2020-07-22-21-52-38-800000.bin
Writing to: binaries3\test_2020-07-22-21-52-40-711000.bin
Writing to: binaries3\test_2020-07-22-21-52-42-641000.bin
Writing to: binaries3\test_2020-07-22-21-52-44-559000.bin
Writing to: binaries3\test_2020-07-22-21-52-46-520000.bin
Writing to: binaries3\test_2020-07-22-21-52-48-538000.bin
Writing to: binaries3\test_2020-07-22-21-52-50-452000.bin
Writing to: binaries3\test_2020-07-22-21-52-52-344000.bin
Writing to: binaries3\test_2020-07-22-21-52-54-227000.bin
Writing to: binaries3\test_2020-07-22-21-52-56-140000.bin
Writing to: binaries3\test_2020-07-22-21-52-58-028000.bin
Writing to: binaries3\test_2020-07-22-21-52-59-926000.bin
Writing to: binaries3\test_2020-07-22-21-53-01-882000.bin
Writing to: binaries3\test_2020-07-22-21-53-03-826000.bin
Writing to: binaries3\test_2020-07-22-21-53-05-719000.bin
Writing to: binaries3\test_2020-07-22-21-53-07-638000.bin
Writing to: binaries3\test_2020-07-22-21-53-09-557000.bin
Writing to: binaries3\test_2020-07-22-21-53-11-492000.bin
Writing to: binaries3\test_2020-07-22-21-53-13-420000.bin
Writing to: binaries3\test_2020-07-22-21-53-15-314000.bin
Writing to: binaries3\test_2020-07-22-21-53-17-202000.bin
Writing to: binaries3\test_2020-07-22-21-53-19-120000.bin
Writing to: binaries3\test_2020-07-22-21-53-21-028000.bin
Writing to: binaries3\test_2020-07-22-21-53-22-910000.bin
Writing to: binaries3\test_2020-07-22-21-53-24-808000.bin
Writing to: binaries3\test_2020-07-22-21-53-26-696000.bin
Writing to: binaries3\test_2020-07-22-21-53-28-615000.bin
Writing to: binaries3\test_2020-07-22-21-53-30-533000.bin
Writing to: binaries3\test_2020-07-22-21-53-32-458000.bin
Writing to: binaries3\test_2020-07-22-21-53-34-376000.bin
Writing to: binaries3\test_2020-07-22-21-53-36-295000.bin
Writing to: binaries3\test_2020-07-22-21-53-38-235000.bin
Writing to: binaries3\test_2020-07-22-21-5Successful PortTCP::Connect
  - port name: 10.230.26.165
Importing Paths:  C:\Users\lab\Documents\parse C:\Users\lab\Documents\parse\bin C:\Users\lab\Documents\parse\ctypeautogen
Running test 0 - random-0_read-0_diskused-0_QD=1_4k
All testing complete
3-40-191000.bin
Writing to: binaries3\test_2020-07-22-21-53-42-126000.bin
Writing to: binaries3\test_2020-07-22-21-53-43-981000.bin
Writing to: binaries3\test_2020-07-22-21-53-45-921000.bin
Writing to: binaries3\test_2020-07-22-21-53-47-835000.bin
Writing to: binaries3\test_2020-07-22-21-53-49-785000.bin
Writing to: binaries3\test_2020-07-22-21-53-51-673000.bin
Writing to: binaries3\test_2020-07-22-21-53-53-602000.bin
Writing to: binaries3\test_2020-07-22-21-53-55-483000.bin
Writing to: binaries3\test_2020-07-22-21-53-57-414000.bin
Writing to: binaries3\test_2020-07-22-21-53-59-343000.bin
Telemetry pull finished ...
```

 </p>
</details>


## configToText.py 
<details><summary>Click to Expand</summary>
<p>

#### Log content below.
```console
$ python configToText.py --inputFile ./workload-fail-txt/workload-fail.ini --iterations 10 --identifier Tv2HiTAC --debug True
Processing .ini file...
Processing object: uid-8
Processing object: uid-20
Processing object: uid-58
Processing object: uid-45
Processing object: uid-46
Processing object: uid-54
Processing object: uid-290
Processing object: uid-297
Processing object: uid-50
Processing object: uid-51
Processing object: uid-88
Processing object: uid-10
Processing object: uid-52
Processing object: uid-55
Processing object: uid-86
Processing object: uid-247
Processing object: uid-57
Signature:
 ThermalStats, Core   0, Uid   8, Major   11, Minor   1, Data Area   2, byte Size   1024,  BTLJ732600A41P0FGN

Signature:
 nvmeFeatures, Core   0, Uid   247, Major   1, Minor   0, Data Area   1, byte Size   56,  BTLJ732600A41P0FGN

Signature:
 powerGov_Fconfig, Core   0, Uid   290, Major   1, Minor   0, Data Area   2, byte Size   188,  BTLJ732600A41P0FGN

Signature:
 fConfigInfoTable, Core   1, Uid   58, Major   7, Minor   2, Data Area   2, byte Size   4016,  BTLJ732600A41P0FGN

Signature:
 Defrag_DustingQueue, Core   1, Uid   45, Major   13, Minor   3, Data Area   1, byte Size   132,  BTLJ732600A41P0FGN

Signature:
 DefragStateCounters, Core   0, Uid   52, Major   1, Minor   2, Data Area   1, byte Size   20,  BTLJ732600A41P0FGN

Signature:
 Defrag_ForcedReloQ, Core   1, Uid   54, Major   13, Minor   3, Data Area   1, byte Size   8,  BTLJ732600A41P0FGN

Signature:
 Defrag_LockedQueue, Core   0, Uid   46, Major   13, Minor   3, Data Area   1, byte Size   132,  BTLJ732600A41P0FGN

Signature:
 fConfigStream, Core   0, Uid   297, Major   7, Minor   2, Data Area   2, byte Size   3072,  BTLJ732600A41P0FGN

Signature:
 Defrag_BandsDoneQueue, Core   1, Uid   50, Major   13, Minor   3, Data Area   1, byte Size   44,  BTLJ732600A41P0FGN

Signature:
 Defrag_HistoricDustMixRate, Core   1, Uid   51, Major   13, Minor   3, Data Area   1, byte Size   44,  BTLJ732600A41P0FGN

Signature:
 Stats, Core   0, Uid   88, Major   52, Minor   25, Data Area   2, byte Size   4096,  BTLJ732600A41P0FGN

Signature:
 initState, Core   0, Uid   10, Major   1, Minor   0, Data Area   2, byte Size   48,  BTLJ732600A41P0FGN

Signature:
 NandDiscovery, Core   0, Uid   57, Major   14, Minor   1, Data Area   2, byte Size   3576,  BTLJ732600A41P0FGN

Signature:
 readLatencyStats, Core   0, Uid   55, Major   4, Minor   1, Data Area   1, byte Size   4864,  BTLJ732600A41P0FGN

Signature:
 NplCmdStateInfo, Core   0, Uid   20, Major   1, Minor   0, Data Area   1, byte Size   96,  BTLJ732600A41P0FGN

Signature:
 mrr_log, Core   0, Uid   86, Major   1, Minor   0, Data Area   2, byte Size   16128,  BTLJ732600A41P0FGN

Signature:
 ThermalStats, Core   0, Uid   8, Major   11, Minor   1, Data Area   2, byte Size   1024,  BTLJ732600A41P0FGN

Signature:
 nvmeFeatures, Core   0, Uid   247, Major   1, Minor   0, Data Area   1, byte Size   56,  BTLJ732600A41P0FGN

Signature:
 powerGov_Fconfig, Core   0, Uid   290, Major   1, Minor   0, Data Area   2, byte Size   188,  BTLJ732600A41P0FGN

Signature:
 fConfigInfoTable, Core   0, Uid   58, Major   7, Minor   2, Data Area   2, byte Size   4016,  BTLJ732600A41P0FGN

Signature:
 Defrag_DustingQueue, Core   0, Uid   45, Major   13, Minor   3, Data Area   1, byte Size   132,  BTLJ732600A41P0FGN

Signature:
 DefragStateCounters, Core   1, Uid   52, Major   1, Minor   2, Data Area   1, byte Size   20,  BTLJ732600A41P0FGN

Signature:
 Defrag_ForcedReloQ, Core   0, Uid   54, Major   13, Minor   3, Data Area   1, byte Size   8,  BTLJ732600A41P0FGN

Signature:
 Defrag_LockedQueue, Core   1, Uid   46, Major   13, Minor   3, Data Area   1, byte Size   132,  BTLJ732600A41P0FGN

Signature:
 fConfigStream, Core   1, Uid   297, Major   7, Minor   2, Data Area   2, byte Size   3072,  BTLJ732600A41P0FGN

Signature:
 Defrag_BandsDoneQueue, Core   0, Uid   50, Major   13, Minor   3, Data Area   1, byte Size   44,  BTLJ732600A41P0FGN

Signature:
 Defrag_HistoricDustMixRate, Core   0, Uid   51, Major   13, Minor   3, Data Area   1, byte Size   44,  BTLJ732600A41P0FGN

Signature:
 Stats, Core   1, Uid   88, Major   52, Minor   25, Data Area   2, byte Size   4096,  BTLJ732600A41P0FGN

Signature:
 initState, Core   1, Uid   10, Major   1, Minor   0, Data Area   2, byte Size   48,  BTLJ732600A41P0FGN

Signature:
 NandDiscovery, Core   1, Uid   57, Major   14, Minor   1, Data Area   2, byte Size   3576,  BTLJ732600A41P0FGN

Signature:
 readLatencyStats, Core   1, Uid   55, Major   4, Minor   1, Data Area   1, byte Size   4864,  BTLJ732600A41P0FGN

Signature:
 NplCmdStateInfo, Core   0, Uid   20, Major   1, Minor   0, Data Area   1, byte Size   96,  BTLJ732600A41P0FGN

Signature:
 mrr_log, Core   0, Uid   86, Major   1, Minor   0, Data Area   2, byte Size   16128,  BTLJ732600A41P0FGN

Signature:
 ThermalStats, Core   0, Uid   8, Major   11, Minor   1, Data Area   2, byte Size   1024,  BTLJ732600A41P0FGN

Signature:
 nvmeFeatures, Core   0, Uid   247, Major   1, Minor   0, Data Area   1, byte Size   56,  BTLJ732600A41P0FGN

Signature:
 powerGov_Fconfig, Core   0, Uid   290, Major   1, Minor   0, Data Area   2, byte Size   188,  BTLJ732600A41P0FGN

Signature:
 fConfigInfoTable, Core   1, Uid   58, Major   7, Minor   2, Data Area   2, byte Size   4016,  BTLJ732600A41P0FGN

Signature:
 Defrag_DustingQueue, Core   1, Uid   45, Major   13, Minor   3, Data Area   1, byte Size   132,  BTLJ732600A41P0FGN

Signature:
 DefragStateCounters, Core   0, Uid   52, Major   1, Minor   2, Data Area   1, byte Size   20,  BTLJ732600A41P0FGN

Signature:
 Defrag_ForcedReloQ, Core   1, Uid   54, Major   13, Minor   3, Data Area   1, byte Size   8,  BTLJ732600A41P0FGN

Signature:
 Defrag_LockedQueue, Core   0, Uid   46, Major   13, Minor   3, Data Area   1, byte Size   132,  BTLJ732600A41P0FGN

Signature:
 fConfigStream, Core   0, Uid   297, Major   7, Minor   2, Data Area   2, byte Size   3072,  BTLJ732600A41P0FGN

Signature:
 Defrag_BandsDoneQueue, Core   1, Uid   50, Major   13, Minor   3, Data Area   1, byte Size   44,  BTLJ732600A41P0FGN

Signature:
 Defrag_HistoricDustMixRate, Core   1, Uid   51, Major   13, Minor   3, Data Area   1, byte Size   44,  BTLJ732600A41P0FGN

Signature:
 Stats, Core   0, Uid   88, Major   52, Minor   25, Data Area   2, byte Size   4096,  BTLJ732600A41P0FGN

Signature:
 initState, Core   0, Uid   10, Major   1, Minor   0, Data Area   2, byte Size   48,  BTLJ732600A41P0FGN

Signature:
 NandDiscovery, Core   0, Uid   57, Major   14, Minor   1, Data Area   2, byte Size   3576,  BTLJ732600A41P0FGN

Signature:
 readLatencyStats, Core   0, Uid   55, Major   4, Minor   1, Data Area   1, byte Size   4864,  BTLJ732600A41P0FGN

Signature:
 NplCmdStateInfo, Core   0, Uid   20, Major   1, Minor   0, Data Area   1, byte Size   96,  BTLJ732600A41P0FGN

Signature:
 mrr_log, Core   0, Uid   86, Major   1, Minor   0, Data Area   2, byte Size   16128,  BTLJ732600A41P0FGN

Signature:
 ThermalStats, Core   0, Uid   8, Major   11, Minor   1, Data Area   2, byte Size   1024,  BTLJ732600A41P0FGN

Signature:
 nvmeFeatures, Core   0, Uid   247, Major   1, Minor   0, Data Area   1, byte Size   56,  BTLJ732600A41P0FGN

Signature:
 powerGov_Fconfig, Core   0, Uid   290, Major   1, Minor   0, Data Area   2, byte Size   188,  BTLJ732600A41P0FGN

Signature:
 fConfigInfoTable, Core   0, Uid   58, Major   7, Minor   2, Data Area   2, byte Size   4016,  BTLJ732600A41P0FGN

Signature:
 Defrag_DustingQueue, Core   0, Uid   45, Major   13, Minor   3, Data Area   1, byte Size   132,  BTLJ732600A41P0FGN

Signature:
 DefragStateCounters, Core   1, Uid   52, Major   1, Minor   2, Data Area   1, byte Size   20,  BTLJ732600A41P0FGN

Signature:
 Defrag_ForcedReloQ, Core   0, Uid   54, Major   13, Minor   3, Data Area   1, byte Size   8,  BTLJ732600A41P0FGN

Signature:
 Defrag_LockedQueue, Core   1, Uid   46, Major   13, Minor   3, Data Area   1, byte Size   132,  BTLJ732600A41P0FGN

Signature:
 fConfigStream, Core   1, Uid   297, Major   7, Minor   2, Data Area   2, byte Size   3072,  BTLJ732600A41P0FGN

Signature:
 Defrag_BandsDoneQueue, Core   0, Uid   50, Major   13, Minor   3, Data Area   1, byte Size   44,  BTLJ732600A41P0FGN

Signature:
 Defrag_HistoricDustMixRate, Core   0, Uid   51, Major   13, Minor   3, Data Area   1, byte Size   44,  BTLJ732600A41P0FGN

Signature:
 Stats, Core   1, Uid   88, Major   52, Minor   25, Data Area   2, byte Size   4096,  BTLJ732600A41P0FGN

Signature:
 initState, Core   1, Uid   10, Major   1, Minor   0, Data Area   2, byte Size   48,  BTLJ732600A41P0FGN

Signature:
 NandDiscovery, Core   1, Uid   57, Major   14, Minor   1, Data Area   2, byte Size   3576,  BTLJ732600A41P0FGN

Signature:
 readLatencyStats, Core   1, Uid   55, Major   4, Minor   1, Data Area   1, byte Size   4864,  BTLJ732600A41P0FGN

Signature:
 NplCmdStateInfo, Core   0, Uid   20, Major   1, Minor   0, Data Area   1, byte Size   96,  BTLJ732600A41P0FGN

Signature:
 mrr_log, Core   0, Uid   86, Major   1, Minor   0, Data Area   2, byte Size   16128,  BTLJ732600A41P0FGN

Signature:
 ThermalStats, Core   0, Uid   8, Major   11, Minor   1, Data Area   2, byte Size   1024,  BTLJ732600A41P0FGN

Signature:
 nvmeFeatures, Core   0, Uid   247, Major   1, Minor   0, Data Area   1, byte Size   56,  BTLJ732600A41P0FGN

Signature:
 powerGov_Fconfig, Core   0, Uid   290, Major   1, Minor   0, Data Area   2, byte Size   188,  BTLJ732600A41P0FGN

Signature:
 fConfigInfoTable, Core   1, Uid   58, Major   7, Minor   2, Data Area   2, byte Size   4016,  BTLJ732600A41P0FGN

Signature:
 Defrag_DustingQueue, Core   1, Uid   45, Major   13, Minor   3, Data Area   1, byte Size   132,  BTLJ732600A41P0FGN

Signature:
 DefragStateCounters, Core   0, Uid   52, Major   1, Minor   2, Data Area   1, byte Size   20,  BTLJ732600A41P0FGN

Signature:
 Defrag_ForcedReloQ, Core   1, Uid   54, Major   13, Minor   3, Data Area   1, byte Size   8,  BTLJ732600A41P0FGN

Signature:
 Defrag_LockedQueue, Core   0, Uid   46, Major   13, Minor   3, Data Area   1, byte Size   132,  BTLJ732600A41P0FGN

Signature:
 fConfigStream, Core   0, Uid   297, Major   7, Minor   2, Data Area   2, byte Size   3072,  BTLJ732600A41P0FGN

Signature:
 Defrag_BandsDoneQueue, Core   1, Uid   50, Major   13, Minor   3, Data Area   1, byte Size   44,  BTLJ732600A41P0FGN

Signature:
 Defrag_HistoricDustMixRate, Core   1, Uid   51, Major   13, Minor   3, Data Area   1, byte Size   44,  BTLJ732600A41P0FGN

Signature:
 Stats, Core   0, Uid   88, Major   52, Minor   25, Data Area   2, byte Size   4096,  BTLJ732600A41P0FGN

Signature:
 initState, Core   0, Uid   10, Major   1, Minor   0, Data Area   2, byte Size   48,  BTLJ732600A41P0FGN

Signature:
 NandDiscovery, Core   0, Uid   57, Major   14, Minor   1, Data Area   2, byte Size   3576,  BTLJ732600A41P0FGN

Signature:
 readLatencyStats, Core   0, Uid   55, Major   4, Minor   1, Data Area   1, byte Size   4864,  BTLJ732600A41P0FGN

Signature:
 NplCmdStateInfo, Core   0, Uid   20, Major   1, Minor   0, Data Area   1, byte Size   96,  BTLJ732600A41P0FGN

Signature:
 mrr_log, Core   0, Uid   86, Major   1, Minor   0, Data Area   2, byte Size   16128,  BTLJ732600A41P0FGN

Signature:
 ThermalStats, Core   0, Uid   8, Major   11, Minor   1, Data Area   2, byte Size   1024,  BTLJ732600A41P0FGN

Signature:
 nvmeFeatures, Core   0, Uid   247, Major   1, Minor   0, Data Area   1, byte Size   56,  BTLJ732600A41P0FGN

Signature:
 powerGov_Fconfig, Core   0, Uid   290, Major   1, Minor   0, Data Area   2, byte Size   188,  BTLJ732600A41P0FGN

Signature:
 fConfigInfoTable, Core   0, Uid   58, Major   7, Minor   2, Data Area   2, byte Size   4016,  BTLJ732600A41P0FGN

Signature:
 Defrag_DustingQueue, Core   0, Uid   45, Major   13, Minor   3, Data Area   1, byte Size   132,  BTLJ732600A41P0FGN

Signature:
 DefragStateCounters, Core   1, Uid   52, Major   1, Minor   2, Data Area   1, byte Size   20,  BTLJ732600A41P0FGN

Signature:
 Defrag_ForcedReloQ, Core   0, Uid   54, Major   13, Minor   3, Data Area   1, byte Size   8,  BTLJ732600A41P0FGN

Signature:
 Defrag_LockedQueue, Core   1, Uid   46, Major   13, Minor   3, Data Area   1, byte Size   132,  BTLJ732600A41P0FGN

Signature:
 fConfigStream, Core   1, Uid   297, Major   7, Minor   2, Data Area   2, byte Size   3072,  BTLJ732600A41P0FGN

Signature:
 Defrag_BandsDoneQueue, Core   0, Uid   50, Major   13, Minor   3, Data Area   1, byte Size   44,  BTLJ732600A41P0FGN

Signature:
 Defrag_HistoricDustMixRate, Core   0, Uid   51, Major   13, Minor   3, Data Area   1, byte Size   44,  BTLJ732600A41P0FGN

Signature:
 Stats, Core   1, Uid   88, Major   52, Minor   25, Data Area   2, byte Size   4096,  BTLJ732600A41P0FGN

Signature:
 initState, Core   1, Uid   10, Major   1, Minor   0, Data Area   2, byte Size   48,  BTLJ732600A41P0FGN

Signature:
 NandDiscovery, Core   1, Uid   57, Major   14, Minor   1, Data Area   2, byte Size   3576,  BTLJ732600A41P0FGN

Signature:
 readLatencyStats, Core   1, Uid   55, Major   4, Minor   1, Data Area   1, byte Size   4864,  BTLJ732600A41P0FGN

Signature:
 NplCmdStateInfo, Core   0, Uid   20, Major   1, Minor   0, Data Area   1, byte Size   96,  BTLJ732600A41P0FGN

Signature:
 mrr_log, Core   0, Uid   86, Major   1, Minor   0, Data Area   2, byte Size   16128,  BTLJ732600A41P0FGN

Signature:
 ThermalStats, Core   0, Uid   8, Major   11, Minor   1, Data Area   2, byte Size   1024,  BTLJ732600A41P0FGN

Signature:
 nvmeFeatures, Core   0, Uid   247, Major   1, Minor   0, Data Area   1, byte Size   56,  BTLJ732600A41P0FGN

Signature:
 powerGov_Fconfig, Core   0, Uid   290, Major   1, Minor   0, Data Area   2, byte Size   188,  BTLJ732600A41P0FGN

Signature:
 fConfigInfoTable, Core   1, Uid   58, Major   7, Minor   2, Data Area   2, byte Size   4016,  BTLJ732600A41P0FGN

Signature:
 Defrag_DustingQueue, Core   1, Uid   45, Major   13, Minor   3, Data Area   1, byte Size   132,  BTLJ732600A41P0FGN

Signature:
 DefragStateCounters, Core   0, Uid   52, Major   1, Minor   2, Data Area   1, byte Size   20,  BTLJ732600A41P0FGN

Signature:
 Defrag_ForcedReloQ, Core   1, Uid   54, Major   13, Minor   3, Data Area   1, byte Size   8,  BTLJ732600A41P0FGN

Signature:
 Defrag_LockedQueue, Core   0, Uid   46, Major   13, Minor   3, Data Area   1, byte Size   132,  BTLJ732600A41P0FGN

Signature:
 fConfigStream, Core   0, Uid   297, Major   7, Minor   2, Data Area   2, byte Size   3072,  BTLJ732600A41P0FGN

Signature:
 Defrag_BandsDoneQueue, Core   1, Uid   50, Major   13, Minor   3, Data Area   1, byte Size   44,  BTLJ732600A41P0FGN

Signature:
 Defrag_HistoricDustMixRate, Core   1, Uid   51, Major   13, Minor   3, Data Area   1, byte Size   44,  BTLJ732600A41P0FGN

Signature:
 Stats, Core   0, Uid   88, Major   52, Minor   25, Data Area   2, byte Size   4096,  BTLJ732600A41P0FGN

Signature:
 initState, Core   0, Uid   10, Major   1, Minor   0, Data Area   2, byte Size   48,  BTLJ732600A41P0FGN

Signature:
 NandDiscovery, Core   0, Uid   57, Major   14, Minor   1, Data Area   2, byte Size   3576,  BTLJ732600A41P0FGN

Signature:
 readLatencyStats, Core   0, Uid   55, Major   4, Minor   1, Data Area   1, byte Size   4864,  BTLJ732600A41P0FGN

Signature:
 NplCmdStateInfo, Core   0, Uid   20, Major   1, Minor   0, Data Area   1, byte Size   96,  BTLJ732600A41P0FGN

Signature:
 mrr_log, Core   0, Uid   86, Major   1, Minor   0, Data Area   2, byte Size   16128,  BTLJ732600A41P0FGN

Signature:
 ThermalStats, Core   0, Uid   8, Major   11, Minor   1, Data Area   2, byte Size   1024,  BTLJ732600A41P0FGN

Signature:
 nvmeFeatures, Core   0, Uid   247, Major   1, Minor   0, Data Area   1, byte Size   56,  BTLJ732600A41P0FGN

Signature:
 powerGov_Fconfig, Core   0, Uid   290, Major   1, Minor   0, Data Area   2, byte Size   188,  BTLJ732600A41P0FGN

Signature:
 fConfigInfoTable, Core   0, Uid   58, Major   7, Minor   2, Data Area   2, byte Size   4016,  BTLJ732600A41P0FGN

Signature:
 Defrag_DustingQueue, Core   0, Uid   45, Major   13, Minor   3, Data Area   1, byte Size   132,  BTLJ732600A41P0FGN

Signature:
 DefragStateCounters, Core   1, Uid   52, Major   1, Minor   2, Data Area   1, byte Size   20,  BTLJ732600A41P0FGN

Signature:
 Defrag_ForcedReloQ, Core   0, Uid   54, Major   13, Minor   3, Data Area   1, byte Size   8,  BTLJ732600A41P0FGN

Signature:
 Defrag_LockedQueue, Core   1, Uid   46, Major   13, Minor   3, Data Area   1, byte Size   132,  BTLJ732600A41P0FGN

Signature:
 fConfigStream, Core   1, Uid   297, Major   7, Minor   2, Data Area   2, byte Size   3072,  BTLJ732600A41P0FGN

Signature:
 Defrag_BandsDoneQueue, Core   0, Uid   50, Major   13, Minor   3, Data Area   1, byte Size   44,  BTLJ732600A41P0FGN

Signature:
 Defrag_HistoricDustMixRate, Core   0, Uid   51, Major   13, Minor   3, Data Area   1, byte Size   44,  BTLJ732600A41P0FGN

Signature:
 Stats, Core   1, Uid   88, Major   52, Minor   25, Data Area   2, byte Size   4096,  BTLJ732600A41P0FGN

Signature:
 initState, Core   1, Uid   10, Major   1, Minor   0, Data Area   2, byte Size   48,  BTLJ732600A41P0FGN

Signature:
 NandDiscovery, Core   1, Uid   57, Major   14, Minor   1, Data Area   2, byte Size   3576,  BTLJ732600A41P0FGN

Signature:
 readLatencyStats, Core   1, Uid   55, Major   4, Minor   1, Data Area   1, byte Size   4864,  BTLJ732600A41P0FGN

Signature:
 NplCmdStateInfo, Core   0, Uid   20, Major   1, Minor   0, Data Area   1, byte Size   96,  BTLJ732600A41P0FGN

Signature:
 mrr_log, Core   0, Uid   86, Major   1, Minor   0, Data Area   2, byte Size   16128,  BTLJ732600A41P0FGN

Signature:
 ThermalStats, Core   0, Uid   8, Major   11, Minor   1, Data Area   2, byte Size   1024,  BTLJ732600A41P0FGN

Signature:
 nvmeFeatures, Core   0, Uid   247, Major   1, Minor   0, Data Area   1, byte Size   56,  BTLJ732600A41P0FGN

Signature:
 powerGov_Fconfig, Core   0, Uid   290, Major   1, Minor   0, Data Area   2, byte Size   188,  BTLJ732600A41P0FGN

Signature:
 fConfigInfoTable, Core   1, Uid   58, Major   7, Minor   2, Data Area   2, byte Size   4016,  BTLJ732600A41P0FGN

Signature:
 Defrag_DustingQueue, Core   1, Uid   45, Major   13, Minor   3, Data Area   1, byte Size   132,  BTLJ732600A41P0FGN

Signature:
 DefragStateCounters, Core   0, Uid   52, Major   1, Minor   2, Data Area   1, byte Size   20,  BTLJ732600A41P0FGN

Signature:
 Defrag_ForcedReloQ, Core   1, Uid   54, Major   13, Minor   3, Data Area   1, byte Size   8,  BTLJ732600A41P0FGN

Signature:
 Defrag_LockedQueue, Core   0, Uid   46, Major   13, Minor   3, Data Area   1, byte Size   132,  BTLJ732600A41P0FGN

Signature:
 fConfigStream, Core   0, Uid   297, Major   7, Minor   2, Data Area   2, byte Size   3072,  BTLJ732600A41P0FGN

Signature:
 Defrag_BandsDoneQueue, Core   1, Uid   50, Major   13, Minor   3, Data Area   1, byte Size   44,  BTLJ732600A41P0FGN

Signature:
 Defrag_HistoricDustMixRate, Core   1, Uid   51, Major   13, Minor   3, Data Area   1, byte Size   44,  BTLJ732600A41P0FGN

Signature:
 Stats, Core   0, Uid   88, Major   52, Minor   25, Data Area   2, byte Size   4096,  BTLJ732600A41P0FGN

Signature:
 initState, Core   0, Uid   10, Major   1, Minor   0, Data Area   2, byte Size   48,  BTLJ732600A41P0FGN

Signature:
 NandDiscovery, Core   0, Uid   57, Major   14, Minor   1, Data Area   2, byte Size   3576,  BTLJ732600A41P0FGN

Signature:
 readLatencyStats, Core   0, Uid   55, Major   4, Minor   1, Data Area   1, byte Size   4864,  BTLJ732600A41P0FGN

Signature:
 NplCmdStateInfo, Core   0, Uid   20, Major   1, Minor   0, Data Area   1, byte Size   96,  BTLJ732600A41P0FGN

Signature:
 mrr_log, Core   0, Uid   86, Major   1, Minor   0, Data Area   2, byte Size   16128,  BTLJ732600A41P0FGN

Signature:
 ThermalStats, Core   0, Uid   8, Major   11, Minor   1, Data Area   2, byte Size   1024,  BTLJ732600A41P0FGN

Signature:
 nvmeFeatures, Core   0, Uid   247, Major   1, Minor   0, Data Area   1, byte Size   56,  BTLJ732600A41P0FGN

Signature:
 powerGov_Fconfig, Core   0, Uid   290, Major   1, Minor   0, Data Area   2, byte Size   188,  BTLJ732600A41P0FGN

Signature:
 fConfigInfoTable, Core   0, Uid   58, Major   7, Minor   2, Data Area   2, byte Size   4016,  BTLJ732600A41P0FGN

Signature:
 Defrag_DustingQueue, Core   0, Uid   45, Major   13, Minor   3, Data Area   1, byte Size   132,  BTLJ732600A41P0FGN

Signature:
 DefragStateCounters, Core   1, Uid   52, Major   1, Minor   2, Data Area   1, byte Size   20,  BTLJ732600A41P0FGN

Signature:
 Defrag_ForcedReloQ, Core   0, Uid   54, Major   13, Minor   3, Data Area   1, byte Size   8,  BTLJ732600A41P0FGN

Signature:
 Defrag_LockedQueue, Core   1, Uid   46, Major   13, Minor   3, Data Area   1, byte Size   132,  BTLJ732600A41P0FGN

Signature:
 fConfigStream, Core   1, Uid   297, Major   7, Minor   2, Data Area   2, byte Size   3072,  BTLJ732600A41P0FGN

Signature:
 Defrag_BandsDoneQueue, Core   0, Uid   50, Major   13, Minor   3, Data Area   1, byte Size   44,  BTLJ732600A41P0FGN

Signature:
 Defrag_HistoricDustMixRate, Core   0, Uid   51, Major   13, Minor   3, Data Area   1, byte Size   44,  BTLJ732600A41P0FGN

Signature:
 Stats, Core   1, Uid   88, Major   52, Minor   25, Data Area   2, byte Size   4096,  BTLJ732600A41P0FGN

Signature:
 initState, Core   1, Uid   10, Major   1, Minor   0, Data Area   2, byte Size   48,  BTLJ732600A41P0FGN

Signature:
 NandDiscovery, Core   1, Uid   57, Major   14, Minor   1, Data Area   2, byte Size   3576,  BTLJ732600A41P0FGN

Signature:
 readLatencyStats, Core   1, Uid   55, Major   4, Minor   1, Data Area   1, byte Size   4864,  BTLJ732600A41P0FGN

Signature:
 NplCmdStateInfo, Core   0, Uid   20, Major   1, Minor   0, Data Area   1, byte Size   96,  BTLJ732600A41P0FGN

Signature:
 mrr_log, Core   0, Uid   86, Major   1, Minor   0, Data Area   2, byte Size   16128,  BTLJ732600A41P0FGN

Execution time: 0:00:00.813544
```
 </p>
</details>


