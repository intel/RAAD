# IOMeter

IOMeter is a disk I/O benchmark (http://www.iometer.org/). You can measure e.g. your harddisk's speed for 4K block size, 50% read, 0% random, and so on. The Github Repo for detailed information (https://github.com/iometer-org/iometer). A little known fact about iometer is that it's actually the interface to a workload generator called dynamo. When iometer is executed in Windows, dynamo is executed in the background and it connected to the iometer interface automatically. To run an iometer workload on Linux, you actually have to run dynamo manually on Linux and then connect it to an iometer instance running on Windows. Prebuild binaries are located (http://www.iometer.org/doc/downloads.html).

# Table of Contents

* Dynamo.exe - Dynamo is the IO workload engine of IOMeter.
* Iometer.exe - Precompiled binary of IOMeter engine
* IOMeterLauncher.py - Main launcher for workloads
* IometerResultParser.py - Results parser for visualization generation
* IometerTestSchedule.py - Testing Harness of scripts.
* csvZipper.py - Script to zip results.
* Thermal-4KSW1QD1W.bat - Windows Script example
* Workloads - Folder containing predefined workloads in CVS format.
* Results - Folder containing results in excel format.

# General Usage Description

* Create Volume or RAID target
* Assign Letter or Location
* Start 'Dynamo.exe' with affinity set to Socket 0 CPU (command line: start /node 0 dynamo.exe).
* Run IOMeterLauncher.py with desired workload.
* Review parsed results in the Results folder.

# Usage of IOMeterLauncher.py

```
python IOMeterLauncher.py Thermal-4KSW1QD1W.csv Thermal-4KSW1QD1W.xlsx
       	                             ^Config file           ^Output file
								 
python IOMeterLauncher.py C:/IOMeter/Workloads/Thermal-4KSW1QD1W.csv C:/IOMeter/Workloads/Thermal-4KSW1QD1W.xlsx
```
	
# Example Windows Script

* Thermal-4KSW1QD1W.bat

# General Technical Information

* Persistent memory devices are required to be written fully before you will achieve stable performance. Background Data Refresh is a “periodic refresh” of the data stored on the drive to prevent the cell voltage levels from shifting outside the stability point. With this, Intel recommends minimum power-on time of 3 hours before running performance evaluations.
	
# Execution Detailed Information

For in multi-socket environment there are some additional recommendations. In case of multi-socket environment (more than one CPU available). Due to technical constraints, there is need to set the affinity of application generating IOs to the CPU0 when using multi-CPU configuration. If it is not set this way, performance will be bottlenecked by communication between sockets. It can be set either manually via task manager during test. You can also set the processes affinity by starting the application from a command line prompt. 
## Manual Windows Exeuction

The syntax is >>> start /AFFINITY <CORE MASK> <APPLICATION> <APPLICATION ARGS>. The core mask is a 32bit mask in which each bit represents selecting the core affinity. If you wanted to run IOMeter on Core 1 and Core 2, you would set /AFFINITY 0x3 (0b0011).
	
### GUI
Find process generating IO in 'Details' tab of task manager (for IOMeter it will be Dynamo.exe). Right-click it and click 'Set affinity'. Then uncheck all processors which doesn't have "(Node 0)" suffix. If you have more than 64 logical processors (in summary on all CPUs), you might need to switch between appropriate groups from drop down list. Go through all groups (Group 0, Group 1 …). Logical cores from Group 0 should have suffix (Node 0) and only this logical cores should be checked. Uncheck all other from all other groups (nodes different than Node 0).

### Commandline Example

Note: To do this via commandline you need to use "start" command to run the IO generator with syntax "start /node 0 /affinity <affinity_mask> <IO_generator_exe>" where <affinity_mask> should be set to appropriate value to choose only logical cores related with CPU0 processor (for more information, http://ss64.com/nt/start.html). With IOMeter performance test on multi-socket setups we are using following command: "start /node 0 dynamo.exe" and then we start IOMeter itself. With multi NUMBA CPUs sockets (I.E. two sockets with 64+ cores) systems with hyper threading on, use shorter form, specifying only node without affinity mask.

```
cd IOMeter
start /node 0 dynamo.exe
python IOMeterLauncher.py C:/IOMeter/Workloads/Thermal-4KSW1QD1W.csv C:/IOMeter/Workloads/Thermal-4KSW1QD1W.xlsx
```

## Manual Linux Execution Ubuntu Example

```
sudo apt install wine64
mkdir unpack
cd unpack
wget https://sourceforge.net/projects/iometer/files/iometer-stable/1.1.0/iometer-1.1.0-linux.x86_64-bin.tar.bz2
tar xvzf iometer-1.1.0-linux.x86_64-bin.tar.bz2
cd iometer-1.1.0-linux.x86_64-bin/src
./dynamo
wine iometer-1.1.0-linux.x86_64-bin-setup.exe
cd ".wine/drive_c/Program Files/Iometer-1.1.0"
cp -avr ./IOMeter/. ./wine/drive_c/Program Files/Iometer-1.1.0/
python IOMeterLauncher.py
wine Iometer.exe
```

# Internal Wiki
https://nsg-wiki.intel.com/display/FA/Best+Known+Configuration+%28BKC%29+and+Method+%28BKM%29+for+Performance+IOMeter+Test+Execution
