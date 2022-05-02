# HOW TO USE THESE TELEMETRY SCRIPTS

## binaryInterface.py
A script that extracts uid-specific telemetry data from device or binary file, dynamically.

pretty self-documenting. Feel free to take a look at the code.

## command to run
Need to import nvme-cli library
```console
git clone https://github.com/linux-nvme/nvme-cli
```

Run a sample test demo-ing pull:
```console
python binaryInterface.py
```

## use the API in your code
```console
python
>> from binaryInterface import *
>> binCache, payload = hybridBinParse("5", "/dev/nvme0n1")
>> payload = hybridChachedBinParse(binCache, "6")
```

OR

```console
python
>> from binaryInterface import *
>> binaryCache, payload = binParse("5", "<NameOfSampleBinHere>")
>> payload = hybridChachedBinParse(binCache, "6")
```

### For Internal Use Only:
Flow that uses getTelemetry.py:
```console
>> from binaryInterface import *
>> binaryCache, payload = binParse("5")
>> payload = cachedBinParse(binaryCache, "6")
```

## getTelemetry.py
a script that uses TWIDL modules to extract telemetry data from a drive. Must be connected to the drive and have access to TWIDL. Generates a binary (ex: sample.bin) file in this directory. Error messages and output print to telemetryGet_log.txt

## command to run
```console
python getTelemetry.py -d 1 sample.bin --nvme --debug=1 > telemetryGet_log.txt 2>&1
```

or 
```console
python getTelemetry.py -d 1 sample.bin --nvme --debug=1 
```

## to print to command prompt

| CL Option       | Description  |
| ---  | ---   |
| -d             | specify drive            |
| sample.bin     | specify output .bin name |


==========================

## parseTelemetryBin.py
a script that splits the telemetry data extracted into individual bin files by data structure name. For example, bis, initState, etc. have their own bin file, found in generated ./sample folder above. 

## command to run
```console
python parseTelemetryBin.py sample.bin -o sample --debug=1 > telemetryParse_log.txt 2>&1
```

or 

```console
python parseTelemetryBin.py sample.bin -o sample --debug=1 
```

## to print to command prompt

| CL Option       | Description  |
| ---  | ---   |
| sample.bin     | bin file to parse            |
| -o,            | name of folder to output to  |

==========================


## cTypeAutoGen.py
a script that uses a compiled .elf file and MULTI functionalities to extract telemetry data structures from firmware of a specific project (ex: arbondale_plus_t2) and stores these in an interpreted, C-type format. Prints output and erros to telemetryGenParse_log.txt

## command to run
```console
python ctypeAutoGen.py --projectname <PROJNAME> --defineobjs \[ALL|DEFAULT|<ENUMERATE_OBJS>] --fwbuilddir <PROJDIR> --tools <TOOLSDIR> --multiexeversion <MULTIVERSION> [--media NAND|NVME] \[--verbose]
```

| Shortcut |   CL Option       | Description  |
| ---  | ---   | ---  |
| -h    | --help                | show this help message and exit           |
|	    | --elf=<ELFPATH>       | Project output dir where .elf is          |
|       | --gpj=<GPJNAME>       | GPJ target (one per target)               |
|       | --src=<SRCDIR>        | Source dir (one per source dir)           |
|       | --tools=<TOOLSDIR>    | FW tools directory where bufdict.py is.   |
|       | --extradb             | Output additional debug info.             |
|       | --dataobj=<OBJECT>    | Process specified data object.            |
|       | --debug               | Debug mode.                               |
|       | --verbose             | Verbose printing for debug use.           |
|       | --defineobjs          | Specify which UIDS you'd like to run as a list individually, or ALL, or RANGE |
|       | --parse               | To run Parsing scripts                    |
|       | --store               | Required parameter to run twidlDictGen.py |

## example
```console
python ctypeAutoGen.py --verbose --projectname arbordaleplus_t2 --fwbuilddir ..\..\projects\objs\arbordaleplus_t2 --tools ctypeautogen --multiexeversion multi_716 --media NAND --defineobjs all> Step_3_autoGenCType_log.txt 2>&1
```

or to print to command prompt:
```console
python ctypeAutoGen.py --verbose --projectname arbordaleplus_t2 --fwbuilddir ..\..\projects\objs\arbordaleplus_t2 --tools ctypeautogen --multiexeversion multi_716 --media NAND --defineobjs [5] 
```


### success indicator
Look for Normal End Process to return as last line

==========================


# pacmanIC.py
a script that takes pulled bin and parsed data structs and prints the telemetry structures with valid .bin information. Saves to specified --outloc, or PacManIC.py_telemetryObjectsGenerated.txt if it does not exist.

## general format
```console
python pacmanIC.py --projdir <PROJDIR> --bin <BINDIRECTORY> [--verbose] 
```

## command to run
```console
python pacmanIC.py --projdir arbordaleplus_t2 --bin ./sample --verbose > Step_4_PacManText_log.txt 2>&1
```

### or to print to command prompt
```console
python pacmanIC.py --projdir arbordaleplus_t2 --bin ./sample --verbose
```


### COMMANDS TO RUN AUTOMATED SCRIPTS

# buildgen3.py
centralized place to run all step 2-4 (parseTelemetryBin, cTypeAutoGen, pacmanIC.py) scripts above and pre-requisites from

## Prior to running
Make sure pulled telemetry bin file (generated by getTelemetry.py) is (copied or generated) in /nand/tools/telemetry folder!

## To run
```console
ssddev\nand\gen3> python buildgen3.py --targets [TARGETS] --keepgoing --ctypeautogen --defineobjs [LISTOBOBJIDS] --printtelemetry --bin [BINFILE]
```

## Example
```console
python buildgen3.py --targets APCA --keepgoing --ctypeautogen --defineobjs [8,9] --printtelemetry --bin sample.bin
```


# runNVME.bat
automates getTelemetry and parseTelemetry only. 

```console
ssddev\nand\gen3\tools\telemetry> runNVME.bat 
```
