#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: David Escamilla, Joseph Tarango
# *****************************************************************************/
"""
Report the sprint review, Retrospective, and plan for the upcoming sprint.
Note: This information is based off of a copy of the standard jirasnapshot made at the end of the sprint and
      the previous sprint and this sprint's commits.
"""

from classCommonReports import common_reports
from classHtmlGen import htmlGen
from classJiraIssues import jira_issue
from classJiraIssuesList import issue_utility
from classJiraIssuesList import jira_issues_lists
from classSupportFiles import support_file
from datetime import date, timedelta
from datetime import datetime
from classJiraIssuesList import issue_utility

import datetime
import json
import sys
import time


def issuesToFPV(aIssuesList, sprintEndDate, milestones, htmlFile):
    """ 
    # issuesToFPV
    # Tables listing issues moved to FPV
    # 
    # @param aIssueList       List of the issues to work with
    # @param milestones       Milestone
    # @param htmlFile         The HTML output file for the results
    # 
    """
    #
    # Find the beginning of the Sprint
    #
    startOfSprint = datetime.datetime.strptime(sprintEndDate, '%m-%d-%Y')
    startOfSprint = startOfSprint - timedelta(days=14)

    toFpvSightingList = []
    inProgressList = []
    toVcStoryList = []
    toVcStoryPoints = 0
    issueUtility = issue_utility()

    for aIssue in aIssuesList.teamIssueList:
        #
        # Since the CLE team is a part of this list, remove them from this report
        #
        if (aIssue["scrumTeam"] in aIssuesList.whichScrumTeam):
            #
            # Make list of stories to VC
            #
            if ((issueUtility.getLastToDate(aIssue, "Validation Complete") >= str(startOfSprint)) and (
                    aIssue["type"] in ["Story"])):
                toVcStoryList.append(aIssue)

                #
            # Make list of sightings to FPV
            #
            if ((issueUtility.getLastToDate(aIssue, "Fixed Pending Validation") >= str(startOfSprint)) and (
                    aIssue["type"] in ["Sighting", "HGST_Sighting"])):
                toFpvSightingList.append(aIssue)

                #
    # Exclude all stories from with only SC listed.   At this time white box testing is completeing, so we don't want to count those points
    #
    toVcStoryList = [aIssue for aIssue in toVcStoryList if "['SC']" != str(aIssue["programs"])]

    #
    # Total the story points
    #
    for aIssue in toVcStoryList:
        toVcStoryPoints += int(aIssue["storyPoints"])

    #
    # Sort the lists by program so it is prettier
    #
    toVcStoryList = sorted(toVcStoryList, key=lambda k: k['programs'])
    toFpvSightingList = sorted(toFpvSightingList, key=lambda k: k['programs'])

    #
    #  Summary section of total of sightings to FPV
    #
    if (len(toFpvSightingList) == 1):
        htmlFile.RawHtlmOutput("<h4>" + str(len(toFpvSightingList)) + " Sighting to FPV</br></h4>" + "\n")
    else:
        htmlFile.RawHtlmOutput("<h4>" + str(len(toFpvSightingList)) + " Sightings to FPV</br></h4>" + "\n")

    #
    # Detailed FPV Sightings
    #
    htmlFile.BeginTable()
    htmlFile.TableHeader(["Program", "Type", "Status", "Key", "Summary"], [10, 15, 15, 15, 40])
    for aIssue in toFpvSightingList:
        htmlFile.TableData(aIssue, ["programs", "type", "status", "key", "summary"], 3, "", "");

    htmlFile.EndTable()

    #
    #  Summary section of total of stories to VC
    #
    if (len(toVcStoryList) == 1):
        htmlFile.RawHtlmOutput(
            "<h4>" + str(len(toVcStoryList)) + " Story (" + str(toVcStoryPoints) + " pts) to VC</br></h4>" + "\n")
    else:
        htmlFile.RawHtlmOutput(
            "<h4>" + str(len(toVcStoryList)) + " Stories (" + str(toVcStoryPoints) + " pts) to VC</br></h4>" + "\n")

    #
    # Detailed FPV stories
    #
    htmlFile.BeginTable()
    htmlFile.TableHeader(["Program", "Type", "Points", "Status", "Key", "Summary"], [10, 15, 5, 15, 15, 40])
    for aIssue in toVcStoryList:
        htmlFile.TableData(aIssue, ["programs", "type", "storyPoints", "status", "key", "summary"], 4, "", "");
    htmlFile.EndTable()


def SightingSourceSummaryReport(aIssuesList, sprintEndDate, htmlFile):
    """ 
    # Create the sightings Source information
    # 
    # @param aIssueList       List of the issues to work with
    # @param htmlFile         The HTML output file for the results
    # 
    # 
    """
    issueUtility = issue_utility()
    newSightingList = []
    submitterOrgCount = {}
    #
    # Find the beginning of the Sprint
    #
    startOfSprint = datetime.datetime.strptime(sprintEndDate, '%m-%d-%Y')
    startOfSprint = startOfSprint - timedelta(days=14)

    htmlFile.RawHtlmOutput("<h3>Incoming Sightings By Source Summary</h3>" + "\n")

    for aIssue in aIssuesList.teamIssueList:
        #
        # Make list of sighting to new after start of sprint
        # Since the CLE team is a part of this list, remove them from this report
        #
        if (aIssue["scrumTeam"] in aIssuesList.whichScrumTeam):
            if ((aIssue["created"] >= str(startOfSprint)) and (aIssue["type"] in ["Sighting", "HGST_Sighting"])):
                newSightingList.append(aIssue)
                if (aIssue["submitterOrg"] in submitterOrgCount):
                    submitterOrgCount[aIssue["submitterOrg"]] += 1
                else:
                    submitterOrgCount[aIssue["submitterOrg"]] = 1

    #
    # Sort the lists by program so it is prettier
    #
    newSightingList = sorted(newSightingList, key=lambda k: k['programs'])

    #
    # Construct the graph & table
    #
    htmlFile.googlePieChart("Sightings By Source Graph", "sightingsBySourceId", submitterOrgCount)
    htmlFile.BeginTable()
    htmlFile.TableHeader(["Submitter Org", "Total"], [50, 50])
    for key, value in submitterOrgCount.iteritems():
        tmpDictionary = {}
        tmpDictionary["key"] = key
        tmpDictionary["value"] = value
        htmlFile.TableData(tmpDictionary, ["key", "value"], -1, "", "");
    htmlFile.EndTable()
    # Now list the specific Jira issues
    htmlFile.RawHtlmOutput("<br>" + "\n")
    htmlFile.BeginTable()
    htmlFile.TableHeader(["Key", "Summary", "Program", "Submutter Org"], [20, 35, 10, 25])
    for aIssue in newSightingList:
        htmlFile.TableData(aIssue, ["key", "summary", "programs", "submitterOrg"], 0, "", "");
    htmlFile.EndTable()


def ProgramSightingSummaryReport(aIssuesList, aSupportFile, htmlFile):
    """ 
    # 
    # Combination of sightings table by program, sightings stacked bar graph, BCH sightings and sightigns in FPV
    # 
    # @param aIssueList       List of the issues to work with
    # @param aSupportFile     This class has the thresholds in it that we need
    # @param htmlFile         The HTML output file for the results
    # 
    """
    aCommonReport = common_reports()
    sightingsSummaryList = []
    sightingsBCHList = []
    totalBCHCount = 0
    rowColor = 0xFFFFFF

    print("Creating Program Sightings Summary.")
    #
    # Get the summary sightings data
    #
    sightingsSummary = aCommonReport.sightingsSummaryByProgram(aIssuesList)

    #
    # Convert to a list so we can sort by program
    #
    for key in sightingsSummary:
        tmpList = []
        tmpList.append("\"" + str(key) + "\"")
        tmpList.append(sightingsSummary[key]["bch"])
        tmpList.append(sightingsSummary[key]["med"])
        tmpList.append(sightingsSummary[key]["fpv"])
        sightingsSummaryList.append(tmpList)
        # Scrum Teams count B/C/H of interest differently
        if ("Prod" in aSupportFile.scrumTeam):
            if (("FD" in str(key)) or ("SP" in str(key))):
                totalBCHCount += int(sightingsSummary[key]["bch"])
        else:
            totalBCHCount += int(sightingsSummary[key]["bch"])
    #
    # Sort the list so it display prettier
    #
    sightingsSummaryList.sort()

    #
    # Format the data in table format and gather the data for the graph
    #
    htmlFile.RawHtlmOutput("<h3>Program Sightings Summaries</h3>" + "\n")
    htmlFile.BeginTable()
    htmlFile.TableHeader(["Program", "Blocker/Critical/High", "Medium", "Fixed Pending Validation"], [10, 10, 10, 10])
    for aSummary in sightingsSummaryList:
        htmlFile.TableData(aSummary, [0, 1, 2, 3], -1, "", "");
    htmlFile.EndTable()

    #
    # Display stacked bar graph 
    #
    htmlFile.googleStackedColumn("Sighting Summary Graph", "sightingSummaryId",
                                 ["Program", "Blocker/Critical/High", "Medium", "Fixed Pending Validation"],
                                 sightingsSummaryList, ["hotpink", "cyan", "lightgreen"])

    sightingsSummaryList = []

    #
    # Display Threshold Gauage and table
    #
    htmlFile.googleGauge("Threshold", totalBCHCount, int(aSupportFile.threshold[1]) * 2, int(aSupportFile.threshold[0]),
                         int(aSupportFile.threshold[1]), int(aSupportFile.threshold[1]),
                         int(aSupportFile.threshold[1]) * 2)
    htmlFile.BeginTable()
    if ("Prod" in aSupportFile.scrumTeam):
        htmlFile.TableHeader(["Current B/C/H in Trunk Programs", "Warning Threshold", "Alert Threshold"], [10, 10, 10])
    else:
        htmlFile.TableHeader(["Current B/C/H in All Programs", "Warning Threshold", "Alert Threshold"], [10, 10, 10])
    tmpList = []
    tmpList.append(totalBCHCount)
    tmpList.append(aSupportFile.threshold[0])
    tmpList.append(aSupportFile.threshold[1])
    htmlFile.TableData(tmpList, [0, 1, 2], -1, "", "");
    htmlFile.EndTable()

    sightingsBCHList = aCommonReport.sightingsBCH(aIssuesList)

    #
    # Sort the list so it display prettier
    #
    sightingsBCHList.sort(key=lambda x: x["programs"])

    #
    # B/C/H sightings Format the data into table format
    #
    htmlFile.RawHtlmOutput("<h4>Blocker/Critical/High Sightings</h4>" + "\n")
    htmlFile.BeginTable()
    htmlFile.TableHeader(["Program", "Priority", "Key", "Summary", "Label", "Status", "Dev Owner"],
                         [5, 5, 5, 15, 5, 5, 10])

    #
    # Change to different shades per program to help read-ability
    #
    lastProgram = ""
    indexColor = -1
    for aIssue in sightingsBCHList:
        if (aIssue["status"] not in aIssuesList.inFPV):
            if (str(lastProgram) != str(aIssue["programs"])):
                lastProgram = str(aIssue["programs"])
                indexColor += 1
            htmlFile.TableData(aIssue, ["programs", "priority", "key", "summary", "labels", "status", "devOwner"], 2,
                               "%X" % (rowColor - (0x222222 * (indexColor % 4))), "");
    htmlFile.EndTable()

    #
    # FPV sightings Format the data into table format
    #

    htmlFile.RawHtlmOutput("<h4>FPV Sightings</h4>" + "\n")
    htmlFile.BeginTable()
    htmlFile.TableHeader(["Program", "Priority", "Key", "Summary", "Val Owner"], [5, 5, 5, 20, 10])

    #
    # Change to different shades per program to help read-ability
    #
    lastProgram = ""
    indexColor = -1
    for aIssue in sightingsBCHList:
        if (aIssue["status"] in aIssuesList.inFPV):
            if (str(lastProgram) != str(aIssue["programs"])):
                lastProgram = str(aIssue["programs"])
                indexColor += 1
            htmlFile.TableData(aIssue, ["programs", "priority", "key", "summary", "valOwner"], 2,
                               "%X" % (rowColor - (0x222222 * (indexColor % 4))), "");
    htmlFile.EndTable()


def CommitResults(aIssuesList, aSupportFile, htmlFile):
    """ 
    # 
    # List the commits results
    # 
    # @param aIssueList       List of the issues to work with
    # @param aSupportFile     The support file information.  Scrum team, milestones, etc.
    # @param htmlFile         The HTML output file for the results
    # 
    """
    aCommonReport = common_reports()
    issueUtility = issue_utility()
    devIssues = {}
    issueAttributes = {}
    milestoneIssueLists = {}
    aComment = {}
    rowCount = 0
    sprintBeginDate = datetime.datetime.strptime(str(aSupportFile.sprintEndDate), "%m-%d-%Y") - datetime.timedelta(
        days=14)

    #
    # Get list of issues assigned to team members 
    #
    devIssues = aCommonReport.allDevCommits(aIssuesList, aSupportFile)

    #
    # Sort the list so it display prettier
    #
    devIssues.sort(key=lambda x: x["programs"])

    print("Commit Results")
    htmlFile.RawHtlmOutput("<br>" + "\n")
    htmlFile.RawHtlmOutput("<h2><u>Commit Results</u></h2>" + "\n")
    #
    # Produce the html 
    #
    htmlFile.BeginTable()

    for aIssue in devIssues:
        #
        # Every 15 rows add the header for readability
        #
        if ((rowCount % 15) == 0):
            htmlFile.TableHeader(["Type", "Key", "Summary", "Status", "Program", "Comment"], [10, 10, 30, 10, 10, 30])
        rowCount += 1

        aComment["issueComment"] = ""
        aIssue.update(aComment)

        #
        # Colorscheme is based off different criteria than the default.  Start by marking everything as a miss
        #
        aIssue["issueColor"] = "FFFF99"
        aComment["issueComment"] = "Commit Miss - Please comment"

        #
        # Mark all stretch goals with the right initial color
        #
        if (aIssue["issueTitle"] == "Stretch"):
            aIssue["issueColor"] = "CCFFCC"
            aComment["issueComment"] = "Stretch goal"

        #
        # All sightings that made it to FPV are commit success
        #
        if ((issueUtility.getLastToDate(aIssue, "Fixed Pending Validation") >= str(sprintBeginDate)) and (
                aIssue["type"] in ["Sighting"])):
            aIssue["issueColor"] = "66FF66"
            aComment["issueComment"] = ""

        #
        # All stories that made it to VC are commit success
        #
        if ((issueUtility.getLastToDate(aIssue, "Validation Complete") >= str(sprintBeginDate)) and (
                aIssue["key"] in ["Story"])):
            aIssue["issueColor"] = "66FF66"
            aComment["issueComment"] = ""

        #
        # All issues in closed are commit success
        #
        if ((aIssue["status"] in ["Closed"])):
            aIssue["issueColor"] = "66FF66"
            aComment["issueComment"] = ""

        #
        # No longer displaying issues moved to other teams
        # aIssue["issueColor"] = "99CCFF"
        # aComment["issueComment"] = "Moved to another team"
        #
        htmlFile.TableData(aIssue, ["type", "key", "summary", "status", "programs", "issueComment"], 1,
                           aIssue["issueColor"], aIssue["issueTitle"]);
    htmlFile.EndTable()


def CommitPlan(aIssuesList, aSupportFile, htmlFile):
    """ 
    # 
    # List the commits Plan
    # Note: This is extremely similar to the commitResults function, but using a different file and coloring them differently
    # 
    # @param aIssueList       List of the issues to work with
    # @param aSupportFile     The support file information.  Scrum team, milestones, etc.
    # @param htmlFile         The HTML output file for the results
    # 
    """
    aCommonReport = common_reports()
    issueUtility = issue_utility()
    devIssues = {}
    issueAttributes = {}
    milestoneIssueLists = {}
    aComment = {}
    rowCount = 0
    sprintBeginDate = datetime.datetime.strptime(str(aSupportFile.sprintEndDate), "%m-%d-%Y") - datetime.timedelta(
        days=14)

    #
    # Get list of issues assigned to team members 
    #
    devIssues = aCommonReport.allDevCommits(aIssuesList, aSupportFile)

    #
    # Sort the list so it display prettier
    #
    devIssues.sort(key=lambda x: x["programs"])

    #
    # Get commit sprint date and the work week of the sprint
    #
    date_object = datetime.datetime.strptime(aSupportFile.sprintEndDate, '%m-%d-%Y')
    wwNumber = date_object.isocalendar()[1]

    print("Sprint Plan ww", wwNumber)
    htmlFile.RawHtlmOutput("<br>" + "\n")
    htmlFile.RawHtlmOutput("<h2><u>Sprint Plan ww" + str(wwNumber) + "</u></h2>" + "\n")
    #
    # Produce the html 
    #
    htmlFile.BeginTable()

    for aIssue in devIssues:
        #
        # Every 15 rows add the header for readability
        #
        if ((rowCount % 15) == 0):
            htmlFile.TableHeader(["Type", "Key", "Summary", "Status", "Program"], [10, 10, 60, 10, 10])
        rowCount += 1
        htmlFile.TableData(aIssue, ["type", "key", "summary", "status", "programs"], 1, aIssue["issueColor"],
                           aIssue["issueTitle"]);
    htmlFile.EndTable()


def StoryPointSnapshotPerProgram(aIssuesList, aSupportFile, htmlFile):
    """ 
    # 
    # Graphs of the story points in each program divided by remaining (anything not FPV, VC, or close), FPV, and Closed (VC and Closed)
    # 
    # @param aIssueList       List of the issues to work with
    # @param aSupportFile     The support file information.  Scrum team, milestones, etc.
    # @param htmlFile         The HTML output file for the results
    # 
    """
    aCommonReport = common_reports()

    #
    # The story points count in each program was taken when the commit file was read in.
    # All we have to do is output it to the pie charts.  No calculations needed
    #
    print("Creating Program Story Points Summary.")
    htmlFile.RawHtlmOutput("<h3>Program Story Points Summaries</h3>" + "\n")
    programKeyList = aIssuesList.programDict.keys()
    programKeyList.sort()
    for aProgram in programKeyList:
        #
        # Construct pie chart
        #
        htmlFile.googlePieChart("Story Points" + str(aProgram) + " by state", "Story_Point_Graph_" + aProgram,
                                aIssuesList.programDict[aProgram])
        htmlFile.RawHtlmOutput("<br>" + "\n")
        #
        # Construct the table with the numbers
        #
        htmlFile.BeginTable()
        htmlFile.TableHeader([str(aProgram), "Total Points"], [50, 50])
        htmlFile.TableData(["Remaining", aIssuesList.programDict[aProgram]["Remaining"]], [0, 1], -1, "", "");
        htmlFile.TableData(["FPV", aIssuesList.programDict[aProgram]["FPV"]], [0, 1], -1, "", "");
        htmlFile.TableData(["Closed", aIssuesList.programDict[aProgram]["Closed"]], [0, 1], -1, "", "");
        htmlFile.EndTable()
        htmlFile.RawHtlmOutput("<br>" + "\n")


def PMAsks(aIssuesList, aSupportFile, htmlFile):
    """ 
    # 
    # Asks from program management
    # 
    # @param aIssueList       List of the issues to work with
    # @param aSupportFile     The support file information.  Scrum team, milestones, etc.
    # @param htmlFile         The HTML output file for the results
    # 
    """
    aCommonReport = common_reports()
    issueUtility = issue_utility()
    askIssuesList = []
    #
    # Get commit sprint date and the work week of the sprint
    #
    date_object = datetime.datetime.strptime(aSupportFile.sprintEndDate, '%m-%d-%Y')
    wwNumber = date_object.isocalendar()[1]

    print("\tCreating Program Management Asks ww", wwNumber)
    htmlFile.RawHtlmOutput("<br>" + "\n")
    htmlFile.RawHtlmOutput("<h2><u>Program Management Asks for ww" + str(wwNumber) + "</u></h2>")

    #
    # Get list of issues assigned to team members 
    #
    devIssues = aCommonReport.allDevCommits(aIssuesList, aSupportFile)

    #
    # Get the information for each ask
    #
    for aIssue in aIssuesList.issueList:
        if (aIssue["key"] in aSupportFile.asksList):
            tmpIssue = {}
            tmpIssue["issueCommit"] = "- - - Not In Commits - - - "
            tmpIssue["issueColor"] = "FF8080"
            tmpIssue["issueTitle"] = "Not In Commits"
            tmpIssue.update(aIssue)
            askIssuesList.append(tmpIssue)

    for aIssue in askIssuesList:
        for aDev in aSupportFile.commitList:
            if (len(aDev["commit"]) > 0):
                if (aIssue["key"] in aDev["commit"]):
                    aIssue["issueCommit"] = "Commit"
                    aIssue["issueColor"] = "66FF66"
                    aIssue["issueTitle"] = "Commit"
            if (len(aDev["stretch"]) > 0):
                if (aIssue["key"] in aDev["stretch"]):
                    aIssue["issueCommit"] = "Stretch goal"
                    aIssue["issueColor"] = "CCFFCC"
                    aIssue["issueTitle"] = "Stretch goal"

    htmlFile.BeginTable()
    for index, aIssue in enumerate(aSupportFile.asksList):
        if ((index % 16) == 0):
            htmlFile.TableHeader(["Program", "Type", "Key", "Summary", "Status", "Comment"], [10, 10, 10, 40, 10, 20])
        for aAsk in askIssuesList:
            if (aAsk["key"] == aIssue):
                htmlFile.TableData(aAsk, ["programs", "type", "key", "summary", "status", "issueCommit"], 2,
                                   aAsk["issueColor"], "");
    htmlFile.EndTable()


if __name__ == '__main__':
    start_time = time.time()
    aJiraIssue = jira_issue()
    aIssuesList = jira_issues_lists()
    aSupportFile = support_file()
    aOldSupportFile = support_file()
    milestoneList = []
    commitList = []
    oldCommitList = []
    commitFiles = []
    oldCommitFiles = []
    DEBUG = 10
    lineNumber = 0
    oneNoteFile = htmlGen()
    htmlFile = htmlGen()
    htmlFilename = ""

    #
    # Read the number of lines in the file
    #
    fileLines = 0
    for line in open("JiraSnapshot_eos.json"):
        fileLines += 1

    #
    # Read the snapshot data and place fields of interest into database and then into a list in memory
    #
    with open("JiraSnapshot_eos.json", "r") as dataStoreFile:
        for aLine in dataStoreFile:
            lineNumber += 1
            if (lineNumber % 107 == 0):
                print(" Reading snapshot:", (100 * lineNumber) / fileLines, "%\r", )
            aJiraIssue.parseJson(aLine.decode('latin1').encode('utf8'))
            aIssuesList.addIssue(aJiraIssue.issueDictionary)
    print(" Reading snapshot:", (100 * lineNumber) / fileLines, "%\r", )
    print("\nDatabase Issues: ", lineNumber)

    #
    # Read Milestones & Commits from tab delimited files
    #
    print("\nReading Milestones and Commits: ")
    aSupportFile.getMilestoneFile("milestones.txt")
    aOldSupportFile.getMilestoneFile("milestones.txt")

    #
    # List the commit files to read
    #
    commitFiles.append("commit_PROD.txt")
    commitFiles.append("commit_PROA.txt")
    oldCommitFiles.append("commit_PROD_end.txt")
    oldCommitFiles.append("commit_PROA_end.txt")

    #
    # Cenerate report for each commit file
    #
    for commitIndex, aCommitFile in enumerate(commitFiles):
        aSupportFile.getCommitFile(aCommitFile)
        aOldSupportFile.getCommitFile(oldCommitFiles[commitIndex])
        aIssuesList.setScrumTeam(aSupportFile.scrumTeam)

        #
        # Get commit sprint date and the work week of the sprint
        #
        date_object = datetime.datetime.strptime(aSupportFile.sprintEndDate, '%m-%d-%Y')
        wwNumber = date_object.isocalendar()[1]

        #
        # Output filename
        #
        htmlFilename = "eos_rrp_ww" + str(wwNumber) + "_" + aIssuesList.whichScrumTeam[0:4].lower() + ".html"
        htmlFile.openHtmlOutput(htmlFilename)
        htmlFile.BeginHtlmOutput(aSupportFile.scrumTeam + " Planning ww" + str(wwNumber),
                                 aSupportFile.scrumTeam + " Planning ww" + str(wwNumber))

        htmlFile.RawHtlmOutput("<h3>Sprint ww" + str(wwNumber - 2) + " Review</h2>")

        #
        # Construct Reports
        #

        #
        # The stories and sightings to FPV section
        #
        htmlFile.RawHtlmOutput("<h3>Progress</h2>")
        aOldSupportFile.getCommitFile(oldCommitFiles[commitIndex])

        issuesToFPV(aIssuesList, aOldSupportFile.sprintEndDate, aOldSupportFile.milestoneList, htmlFile)

        #
        # Incomming sightings report graph and table
        #
        SightingSourceSummaryReport(aIssuesList, aOldSupportFile.sprintEndDate, htmlFile)

        #
        # Sightings snapshot graph and table - need to get the thresholds int othe sprint planning support file 
        #
        ProgramSightingSummaryReport(aIssuesList, aOldSupportFile, htmlFile)

        #
        # Commits in table marked in green and yellow (yellow = miss)
        #
        CommitResults(aIssuesList, aOldSupportFile, htmlFile)

        # 
        # Story Snapshot per program (Remaining, FPV, and closed)
        # 
        StoryPointSnapshotPerProgram(aIssuesList, aOldSupportFile, htmlFile)

        #
        # Retrospective area
        # 

        htmlFile.RawHtlmOutput("<h2><u>Retrospective</u></h2>" + "\n")
        htmlFile.RawHtlmOutput("  <ul>" + "\n")
        htmlFile.RawHtlmOutput("   <li><b>What Went Well</b>" + "\n")
        htmlFile.RawHtlmOutput("     <ul>" + "\n")
        htmlFile.RawHtlmOutput("       <li>" + "\n")
        htmlFile.RawHtlmOutput("       <li>" + "\n")
        htmlFile.RawHtlmOutput("       <li>" + "\n")
        htmlFile.RawHtlmOutput("     </ul>" + "\n")
        htmlFile.RawHtlmOutput("   </li>" + "\n")
        htmlFile.RawHtlmOutput(" </ul>" + "\n")
        htmlFile.RawHtlmOutput(" <ul>" + "\n")
        htmlFile.RawHtlmOutput("   <li><b>What needs to change</b>" + "\n")
        htmlFile.RawHtlmOutput("     <ul>" + "\n")
        htmlFile.RawHtlmOutput("       <li>" + "\n")
        htmlFile.RawHtlmOutput("       <li>" + "\n")
        htmlFile.RawHtlmOutput("       <li>" + "\n")
        htmlFile.RawHtlmOutput("     </ul>" + "\n")
        htmlFile.RawHtlmOutput("   </li>" + "\n")
        htmlFile.RawHtlmOutput(" </ul>" + "\n")
        htmlFile.RawHtlmOutput("<br>" + "\n")

        #
        # Program Management asks
        #
        PMAsks(aIssuesList, aSupportFile, htmlFile)

        #
        # Commits and stretch plan 
        #
        CommitPlan(aIssuesList, aSupportFile, htmlFile)

    elapsed_time = time.time() - start_time
    print("\nRun time: ", int(elapsed_time), "seconds")
