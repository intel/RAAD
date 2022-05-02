#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: David Escamilla, Joseph Tarango
# *****************************************************************************/
"""
classSupportFiles
Reads the tab delimited support files.
Provides access to the data within those files
Currently support files are of the following types:
    Milestones
    Commits
The expected column format for each of the supported file types is
described in the get function for it.
"""
# , nested_scopes, generators, generator_stop, with_statement, annotations
import sys
import time
import re
import datetime


class support_file(object):
    """
    # parses the support files and provides easy access to the data therein
    # <p>
    # Note:  Dependent on commits being entered in a fixed format as defined for each support file.
    #
    # @version     1.0
    #
    """
    issueDictionary = {}
    milestoneList = []
    commitList = []
    threshold = []
    scrumTeam = ""
    sprintEndDate = ""
    asksList = []
    commitColor = "CC99FF"
    stretchColor = "F0E0FF"

    def __init__(self):
        self.issueDictionary = {}
        self.mileStoneList = []
        self.commitList = []
        self.scrumTeam = ""

    def tabDelimitedToList(self, filename, expectedColumns):
        """
        # tabDelimitedToList
        #
        # Reads the tab delimited commits file and converts it to a list
        # <p>
        #
        # @param filename              filename to parse
        # @param expectedColumns       the expected columns to read.  also used to name those columns
        """
        completeList = []
        tmpList = []
        tmpDictionary = {}
        currentColumn = 0
        with open(filename, "r") as delimitedFile:
            for aLine in delimitedFile:
                currentColumn += 1
                tmpList = []
                tmpList = aLine.strip().split("\t")
                tmpDictionary = {}
                for index, aColumn in enumerate(expectedColumns):
                    if (index < len(tmpList)):
                        tmpDictionary[aColumn] = tmpList[index]
                    else:
                        tmpDictionary[aColumn] = ""
                completeList.append(tmpDictionary)
        return completeList[:]

    def getCommitFile(self, filename):
        """
        # getCommitFile
        #
        # Performs all the functions to get the commitfile data and parse it into a easy to use form
        # <p>
        #
        # @param filename              filename to parse
        """
        expectedColumns = ["name", "commit", "stretch"]
        #
        # Read in the data from the file
        #
        self.commitList = self.tabDelimitedToList(filename, expectedColumns)
        #
        # The first line in the commit contains the header information, the scrum team, and the thresholds
        #
        self.scrumTeam = re.sub("\/.*", "", self.commitList[0]["name"])
        self.scrumTeam = re.sub("\"", "", self.scrumTeam)
        self.threshold = re.split(",", (re.sub(".*\/", "", re.sub("\"", "", self.commitList[0]["name"]))))
        self.sprintEndDate = re.sub("\/", "-", self.commitList[0]["commit"])
        self.commitList.pop(0)

        #
        # Format the list of commits and stretch goals into lists
        #
        for aRow in self.commitList:
            tmpString = ""
            aRow["name"] = str.strip(aRow["name"], "\"")
            tmpString = str.strip(aRow["commit"], "\"")
            # Remove all white space
            tmpString = ''.join(tmpString.split())
            aRow["commit"] = str.split(tmpString, ",")
            tmpString = str.strip(aRow["stretch"], "\"")
            # Remove all white space
            tmpString = ''.join(tmpString.split())
            aRow["stretch"] = str.split(tmpString, ",")

        #
        # Remove the asks into a seperate list
        #
        self.asksList = self.commitList[len(self.commitList) - 1]["commit"]
        self.commitList.pop()

    def getMilestoneFile(self, filename):
        """
        # getFile
        #
        # Performs all the functions to get the milestonefile data and parse it into a easy to use form
        # <p>
        #
        # @param filename              filename to parse
        """
        expectedColumns = ["name", "tag", "target", "color"]
        mileStoneList = []
        #
        # Read in the data from the file
        #
        self.milestoneList = self.tabDelimitedToList(filename, expectedColumns)
