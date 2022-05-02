#!/usr/bin/python
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Jordan Howes, Joseph Tarango
# *****************************************************************************/
# IometerTestSchedule.py
# IOMeter Gen3 Launcher and Parser
# Supporting IOMeter w/ QoS and Randomization

import sys, os, csv, time

class IometerTestSchedule:
    """Holds IOMeter Test Info"""

    def __init__(self, filename, outFilename):
        self.testList = []
        self.testList = self.readSchedule(filename)

        # If readSchedule didn't like what it parsed.
        if (self.testList is None):
            print("CRITICAL ERROR - SCHEDULE FILE UNEXPECTED ERROR")

        self.index = 0
        self.maxIndex = len(self.testList) - 1
        self.physDrive = 0
        self.driveLetter = self.testList[0]['driveLetter'].split("-")
        self.currTestName = None
        self.physDrive = 0
        for idx, item in enumerate(self.driveLetter):  # This is a bit of a hack, someday replace with a better conversion from string to dec.  Can't typecast because it might be a letter.
            if ((self.driveLetter[idx] == '0') or (self.driveLetter[idx] == '1') or (self.driveLetter[idx] == '2') or (self.driveLetter[idx] == '3') or (self.driveLetter[idx] == '4') or (self.driveLetter[idx] == '5')):
                self.driveLetter[idx] = "PHYSICALDRIVE:%d" % (int(self.driveLetter[idx]))  # Uses the IOMeter method for noting a physical drive.
                if ((idx != 0) and (self.physDrive == 0)):
                    print("CRITICAL ERROR - ALL DRIVES MUST BE PHYSICAL OR WITH A FILE SYSTEM.  YOU CANNOT MIX TYPES.")
                    break
                self.physDrive = 1
            else:
                if (self.physDrive == 1):
                    print("CRITICAL ERROR - ALL DRIVES MUST BE PHYSICAL OR WITH A FILE SYSTEM.  YOU CANNOT MIX TYPES.")
                    break
        self.prepDrive = self.testList[0]['prepDrive']
        self.useRandom = self.testList[0]['useRandom']

        # Create the output file and heads
        self.outFilename = outFilename
        outFile = open(outFilename, "w")
        sys.stdout = outFile
        print("RESULT METADATA, TEST FILE USED, %s, DRIVE TARGET, %s, DRIVE PREP, %s, RANDOM DATA, %s"
              % (filename, '-'.join(self.driveLetter), self.prepDrive, self.useRandom))
        print("IOMETER SCHEDULE RESULTS,Percent Random,Percent Read,Request Size,QD,Span Size,Run Time,Average Range,"
              "Target Iops,Result File,QoS Time Range (s),<50 uS,<100 uS,<200 uS,<500 uS,<1 mS,<2 mS,<5 mS,<10 mS,"
              "<15 mS,<20 mS,<30 mS,<50 mS,<100 mS,<200 mS,<500 mS,<1 S,<2 S,<4.7 S,<5 S,<10 S,> 10 S")
        sys.stdout = sys.__stdout__
        outFile.close()

    # Returns a Dictionary of tests to run in the format:
    # [SETTINGS,(char)Drive Letter,(bool)Prep Drive,(bool)Use Random Data]
    # [RUN,(int)Percent Random,(int)Percent Read,(int)Request Size,(int)Queue Depth,(int)Span Size,(int)Run Time,(int)Average Range,(int)Target Iops,(int)Qos Time Range,[QOS]]
    # [RUN,(int)Percent Random,(int)Percent Read,(int)Request Size,(int)Queue Depth,(int)Span Size,(int)Run Time,(int)Average Range,(int)Target Iops,(int)Qos Time Range,[QOS]]
    # ...
    def readSchedule(self, filename):
        scheduleCsv = csv.reader(open(filename))
        rsResults = []

        ######################
        ### Version Number ###
        ######################
        VERSION = 5
        VERSIONCOMP = 2
        ## 1 = Initial build, no QOS
        ## 2 = Added QOS
        ## 3 = Added PREP/DELETE
        ## 4 = Added IDLE
        ## 5 = Added ADDWORKER
        ######################
        ######################

        for row in scheduleCsv:
            # Check for the current CSV version for this build.  Version = current version, versioncomp = oldest version we can currently use.
            if (row[0] == 'IOMETER LAUNCHER SCHEDULE'):
                if (int(row[1]) < VERSIONCOMP):
                    print("CRITICAL ERROR - SCHEDULE FILE VERSION INCORRECT")
                    print("               - CSV Version %d, expected version %d or greater" % (int(row[1]), VERSIONCOMP))
                    return None
            # If the setting lines insert it, both this and the version are at fixed locations and there might be faster ways to do this.
            elif (row[0] == 'SETTINGS'):
                rsResults.append({'type': row[0], 'driveLetter': row[1], 'prepDrive': int(row[2]), 'useRandom': int(row[3])})
            elif (row[0] == 'RUN'):
                rsResults.append({'type': row[0],
                                  'pRandom': int(row[1]),
                                  'pRead': int(row[2]),
                                  'requestSize': int(row[3]),
                                  'qd': int(row[4]),
                                  'spanSize': int(row[5]),
                                  'time': int(row[6]),
                                  'avgRng': int(row[7]),
                                  'target': int(row[8]),
                                  'qosTime': int(row[9]),
                                  'qos': [float(row[10]), float(row[11]), float(row[12]), float(row[13]), float(row[14]), float(row[15]), float(row[16]), float(row[17]), float(row[18]), float(row[19]), float(row[20]), float(row[21]), float(row[22]), float(row[23]), float(row[24]), float(row[25]), float(row[26]), float(row[27]), float(row[28]), float(row[29]), float(row[30])]})
            elif (row[0] == 'DELETE'):
                rsResults.append({'type': row[0]})
            elif (row[0] == 'PREP'):
                rsResults.append({'type': row[0]})
            elif (row[0] == 'IDLE'):
                if (len(row) == 2):
                    rsResults.append({'type': row[0], 'time': int(row[1])})
                else:
                    print("ERROR - No time for idle (or error in schedule) , using 1.")
                    rsResults.append({'type': row[0], 'time': 1})
            elif (row[0] == 'ADDWORKER'):
                if (len(row) != ''):  # Why did I do this.. shouldn't it be = 2?
                    rsResults.append({'type': row[0], 'driveLetter': row[1]})
                    rsResults[0]['driveLetter'] = rsResults[0]['driveLetter'] + '-%s' % (row[1])
                else:
                    print("CRITICAL ERROR - NO DRIVE ASSIGNED TO WORKER OR ERROR IN SCHEDULE.")
                    return None
            elif (row[0] == 'RUNCMD'):
                rsResults.append({'type': row[0], 'cmd': row[1]})

        if (rsResults[0]['type'] == 'SETTINGS'):
            return rsResults
        else:
            return None

    # Workers is for internal use, not designed to be called directly!
    def nextTestFile(self, filename, workers=1):
        if (self.index == self.maxIndex):
            return None
        self.index += 1

        if (self.testList[self.index]['type'] == 'RUN'):
            self.currTestName = self.createFile(filename, workers=workers)
            ##
            # self.currTestName = self.createFile(filename, self.driveLetter, self.testList[self.index]['requestSize'], self.testList[self.index]['pRead'],
            # self.testList[self.index]['pRandom'], self.testList[self.index]['qd'], self.testList[self.index]['spanSize'],
            # self.testList[self.index]['time'], self.useRandom)
            ##

            return self.currTestName
        elif (self.testList[self.index]['type'] == 'DELETE'):
            if (self.physDrive == 0):
                print("Deleting test file(s).")
                for dl in self.driveLetter:  # loop though each drive letter and delete it.
                    os.system("del /F %s:\iobw.tst" % (dl))
                time.sleep(7)  # Probably not nessisary, but it doesn't hurt.
            else:
                print("Accessing physical drive, no test file to delete.")
            return self.nextTestFile(filename)
        elif (self.testList[self.index]['type'] == 'PREP'):
            if (self.physDrive == 0):
                print("Preping drive with a full span sequential write.")
                self.createPrepFile("driveprep.icf")
                os.system("iometer.exe driveprep.icf driveprep.csv")
                print("Drive prep complete.")
            else:
                print("Accessing physical drive, drive prep must be done manually.")
            return self.nextTestFile(filename, workers)
        elif (self.testList[self.index]['type'] == 'IDLE'):
            print("Idle for %d seconds." % (self.testList[self.index]['time']))
            time.sleep(self.testList[self.index]['time'])
            return self.nextTestFile(filename, workers)
        elif (self.testList[self.index]['type'] == 'ADDWORKER'):
            print("Adding a worker to next test on drive %s" % (self.testList[self.index]['driveLetter']))
            return self.nextTestFile(filename, workers + 1)
        elif (self.testList[self.index]['type'] == 'RUNCMD'):
            print("Running custom command.")
            ccExitCode = os.system(self.testList[self.index]['cmd'])
            print("Custom command complete with code - %d" % (ccExitCode))
            return self.nextTestFile(filename)

    # Currently this just generates the file, no checking to see if you should prep.  Leaving that in Launcher.
    def createPrepFile(self, filename, prep=-1):
        if (prep == -1):  # default to whatever is in the prep option in the schedule file
            prep = self.prepDrive
        if (prep == 1):  # if 1, assume use wants a full span prep for backwards compatability
            prep = 0
        return self.createFile(filename, self.driveLetter, requestSize=512, pRead=100, pRandom=0, qd=1, spanSize=prep, time=5, isRandom=self.useRandom, workers=len(self.driveLetter))

    # Set the index to a given index with some sanity checking.
    def setIndex(self, newIndex):
        if (newIndex < 1):
            self.index = 1
        if (newIndex > self.maxIndex):
            self.index = self.maxIndex

        self.index = newIndex

    # Reset the index to 1.
    def resetIndex(self):
        self.index = 1

    # Insert a result in the output file for the current indexed test.
    def insertResult(self, resultFilename):
        if (self.index == 0):
            print("ERROR - INSERT RESULT WITH INDEX 0")
            return None
        # Open Output File
        outFile = open(self.outFilename, "a")
        sys.stdout = outFile

        print("RESULT,%d,%d,%d,%d,%d,%d,%d,%d,%s,%d,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f"
              % (self.testList[self.index]['pRandom'], self.testList[self.index]['pRead'],
                 self.testList[self.index]['requestSize'], self.testList[self.index]['qd'],
                 self.testList[self.index]['spanSize'], self.testList[self.index]['time'],
                 self.testList[self.index]['avgRng'], self.testList[self.index]['target'],
                 resultFilename, self.testList[self.index]['qosTime'], self.testList[self.index]['qos'][0],
                 self.testList[self.index]['qos'][1], self.testList[self.index]['qos'][2],
                 self.testList[self.index]['qos'][3], self.testList[self.index]['qos'][4],
                 self.testList[self.index]['qos'][5], self.testList[self.index]['qos'][6],
                 self.testList[self.index]['qos'][7], self.testList[self.index]['qos'][8],
                 self.testList[self.index]['qos'][9], self.testList[self.index]['qos'][10],
                 self.testList[self.index]['qos'][11], self.testList[self.index]['qos'][12],
                 self.testList[self.index]['qos'][13], self.testList[self.index]['qos'][14],
                 self.testList[self.index]['qos'][15], self.testList[self.index]['qos'][16],
                 self.testList[self.index]['qos'][17], self.testList[self.index]['qos'][18],
                 self.testList[self.index]['qos'][19], self.testList[self.index]['qos'][20]))

        sys.stdout = sys.__stdout__
        outFile.close()

    # The function call can override the default values, or just use them as is.  Not as clean as normal defaults, but not sure how to do that in an object.
    def createFile(self, filename, driveLetter=-1, requestSize=-1, pRead=-1, pRandom=-1, qd=-1, spanSize=-1, time=-1, isRandom=-1, workers=1):
        # Initial Values, optional defaults.
        if (driveLetter == -1):
            driveLetter = self.driveLetter
        if (requestSize == -1):
            requestSize = self.testList[self.index]['requestSize']
        if (pRead == -1):
            pRead = self.testList[self.index]['pRead']
        if (pRandom == -1):
            pRandom = self.testList[self.index]['pRandom']
        if (qd == -1):
            qd = self.testList[self.index]['qd']
        if (spanSize == -1):
            spanSize = self.testList[self.index]['spanSize']
        if (time == -1):
            time = self.testList[self.index]['time']
        if (isRandom == -1):
            isRandom = self.useRandom

        # Data santization
        requestSize = requestSize - (requestSize % 512)

        if (pRead > 100):
            pRead = 100
        elif (pRead < 0):
            pRead = 0

        if (pRandom > 100):
            pRandom = 100
        elif (pRandom < 0):
            pRandom = 0

        if (qd < 1):
            qd = 1

        if (spanSize < 0):
            spanSize = 0

        if (time < 1):
            time = 1

        # Check workers vs. drives.
        if (workers == 0):
            print("CRITICAL ERROR - WORKERS = 0 in random-%d_read-%d_diskused-%d_QD=%d_%dk"
                  % (pRandom, pRead, spanSize, qd, (float(requestSize) / 1024)))
        if (workers > len(driveLetter)):
            print("Minor Error - More workers than drives.  Using the first drive letter for all extra workers.")
            for i in range(workers, len(driveLetter)):
                driveLetter.append(driveLetter[0])

        # Open ICF File
        outFile = open(filename, "w")
        sys.stdout = outFile

        print("Version 2007.09.26")
        print("'TEST SETUP ====================================================================")
        print("'Test Description")
        print("")
        print("'Run Time")
        print("'\thours\tminutes\tseconds")
        print("\t0\t0\t%d" % (time))
        print("'Ramp Up Time (s)")
        print("\t0")
        print("'Default Disk Workers to Spawn")
        print("\tNUMBER_OF_CPUS")
        print("'Default Network Workers to Spawn")
        print("\t0")
        print("'Record Results")
        print("\tALL")
        print("'Worker Cycling")
        print("'\tstart\tstep\tstep type")
        print("\t1\t1\tLINEAR")
        print("'Disk Cycling")
        print("'\tstart\tstep\tstep type")
        print("\t1\t1\tLINEAR")
        print("'Queue Depth Cycling")
        print("'\tstart\tend\tstep\tstep type")
        print("\t1\t32\t2\tEXPONENTIAL")
        print("'Test Type")
        print("\tNORMAL")
        print("'END test setup")
        print("'RESULTS DISPLAY ===============================================================")
        print("'Update Frequency,Update Type")
        print("\t1,LAST_UPDATE")
        print("'Bar chart 1 statistic")
        print("\tTotal I/Os per Second")
        print("'Bar chart 2 statistic")
        print("\tTotal MBs per Second")
        print("'Bar chart 3 statistic")
        print("\tAverage I/O Response Time (ms)")
        print("'Bar chart 4 statistic")
        print("\tMaximum I/O Response Time (ms)")
        print("'Bar chart 5 statistic")
        print("\t% CPU Utilization (total)")
        print("'Bar chart 6 statistic")
        print("\tTotal Error Count")
        print("'END results display")
        print("'ACCESS SPECIFICATIONS =========================================================")
        print("'Access specification name,default assignment")
        print("\trandom-%d_read-%d_diskused-%d_QD=%d_%dk,NONE"
              % (pRandom, pRead, spanSize, qd * workers, (float(requestSize) / 1024)))
        print("'size,% of size,% reads,% random,delay,burst,align,reply")
        print("\t%d,100,%d,%d,0,1,%d,0" % (requestSize, pRead, pRandom, requestSize))
        print("'END access specifications")
        print("'MANAGER LIST ==================================================================")
        print("'Manager ID, manager name")
        print("\t1,iometer-test")
        print("'Manager network address")
        print("\t10.24.25.159")

        for i in range(workers):
            print("'Worker")
            print("\t%dof%d" % (i + 1, workers))
            print("'Worker type")
            print("\tDISK")
            print("'Default target settings for worker")
            print("'Number of outstanding IOs,test connection rate,transactions per connection")
            print("\t%d,DISABLED,1" % (qd))
            print("'Disk maximum size,starting sector,Use Random Data")
            print("\t%d,0,%d" % (spanSize, isRandom))
            print("'End default target settings for worker")
            print("'Assigned access specs")
            print("\trandom-%d_read-%d_diskused-%d_QD=%d_%dk"
                  % (pRandom, pRead, spanSize, qd * workers, (float(requestSize) / 1024)))
            print("'End assigned access specs")
            print("'Target assignments")
            print("'Target")
            if (self.physDrive):
                print("\t%s" % (driveLetter[i]))
            else:
                print("\t%s:" % (driveLetter[i]))
            print("'Target type")
            print("\tDISK")
            print("'End target")
            print("'End target assignments")
            print("'End worker")

        print("'End manager")
        print("'END manager list")
        print("Version 2007.09.26 ")

        sys.stdout = sys.__stdout__
        outFile.close()
        return "random-%d_read-%d_diskused-%d_QD=%d_%dk" % (pRandom, pRead, spanSize, qd * workers, (float(requestSize) / 1024))
