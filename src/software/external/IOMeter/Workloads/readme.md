The following is for variable configurations of workload files. The file format is in CVS format. The variables listed are not a complete set of options; please refer to the python code and IOMeter documentation for your release.
---------------------------------------------------------------------------------------------------------------
| CVS HEADER
---------------------------------------------------------------------------------------------------------------
IOMETER LAUNCHER SCHEDULE,2,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
DESCRIPTION,PerfOvernightNIT,9/22/2010,,,,,,,,,,,,,,,,,,,,,,,,,,,,
---------------------------------------------------------------------------------------------------------------
The field 'PerfOvernightNIT' is the label given to the given execution set execution.

---------------------------------------------------------------------------------------------------------------
| Settings
---------------------------------------------------------------------------------------------------------------
SETTINGS LIST,Drive Letter,Prep Drive,Use Random Data,,,,,,,,,,,,,,,,,,,,,,,,,,,
SETTINGS,G,0,0,,,,,,,,,,,,,,,,,,,,,,,,,,,
---------------------------------------------------------------------------------------------------------------
The second Field in the settings Line 'G' corresponds to the assigned windows drive letter or destination location.

---------------------------------------------------------------------------------------------------------------
| Variables for the configuration of execution for a particular run.
---------------------------------------------------------------------------------------------------------------
RUN LIST,Percent Random, Percent Read, Access Size, Queue Depth, Span Size, Run Time (s),Avg Range,Target Iops,QoS Time Range (s),<50 uS,<100 uS,<200 uS,<500 uS,<1 mS,<2 mS,<5 mS,<10 mS,<15 mS,<20 mS,<30 mS,<50 mS,<100 mS,<200 mS,<500 mS,<1 S,<2 S,<4.7 S,<5 S,<10 S,> 10 S
RUN,100,0,8192,128,0,120,60,0,10,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
---------------------------------------------------------------------------------------------------------------
RUN LIST - Command for execution
Percent Random - Percentage of the workload to be random or sequential; the values are compliments of eachother.
Examples:
100 - 100% random and   0% sequential
 50 -  50% random and  50% sequential
  0 -   0% random and 100% sequential

Percent Read - Percentage of the workload to be read or writes; the values are compliments of eachother.
Examples:
100 - 100% reads and   0% writes
 50 -  50% reads and  50% writes
  0 -   0% reads and 100% writes

Access Size - The access size of the read or writes. The specification of the device should be read for the optimized granularity size for a desired performance.
Examples:
   512 - The size of the requests are  512 Kilo Bytes.
  4096 - The size of the requests are 4092 Kilo Bytes.
  8192 - The size of the requests are 8192 Kilo Bytes.
...
126976 - The size of the requests are 126976 Kilo Bytes.

Queue Depth - Total commands within the queue for the protocal. For a given specification, these will be restricted by the device driver. In NVMe, these are restricted to a range of [0, 128]. In SATA, these are restricted to a range of [0, 32].
0   -   0 queued commands.
16  -  16 queued commands.
32  -  32 queued commands.
128 - 128 queued commands.

Span Size - Given the total partitioned space the span size is the total amount of local space to be  written to.

Run Time (s) - The total runtime for a given run based in seconds.

Avg Range - The time span to average the workload. The average range is to give a target for steady state operation.

Target Iops - The target of expected of Inputs and Outputs per second.

QoS Time Range (s) - The time span of sampling to see quality of service.

<50 uS,<100 uS,<200 uS,<500 uS,<1 mS,<2 mS,<5 mS,<10 mS,<15 mS,<20 mS,<30 mS,<50 mS,<100 mS,<200 mS,<500 mS,<1 S,<2 S,<4.7 S,<5 S,<10 S,> 10 S - These are the given expectations for the qualiy of service ranges to count outstanding completions of commands. Ideally with a perfect set of media, device, system all commands should be a the lowest completion timeframe.