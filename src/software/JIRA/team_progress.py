#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: David Escamilla, Joseph Tarango
# *****************************************************************************/
"""
Generate a report for use during DSU
"""
from classCommonReports import common_reports
from classGetJiraIssues import get_jira_issues
from classHtmlGen import htmlGen
from classJiraIssues import jira_issue
from classJiraIssuesList import issue_utility
from classJiraIssuesList import jira_issues_lists
from classSupportFiles import support_file
from collections import defaultdict
from datetime import date, timedelta
from datetime import datetime

import datetime
import sys
import time


def MilestoneReport(aIssuesList, milestoneList, htmlFile):
    """ 
    # 
    # MilestoneReport
    # Display the color coded milestones with the tag to search for and target date
    # 
    # @param aIssueList       List of the issues to work with
    # @param milestones       List of Milestones
    # @param htmlFile         The HTML output file for the results
    # 
    """
    milestoneIssueLists = {}
    milestoneIssueLists = defaultdict(list)
    milestoneTags = []

    for aMilestone in milestoneList:
        milestoneTags.append(aMilestone["tag"])

    #
    # Scan the snapshot of those issues specific to the team and seperate into milestone lists
    #
    for aIssue in aIssuesList.teamIssueList:
        #
        # We only are interested in those in dev or val
        #
        if (aIssue["status"] in aIssuesList.inDevVal):
            #
            # Check for any milestone tag in the labels, milestone or fixVersions field
            # Multiple milestones may appear so we add to the appropriate dictionary lists
            #
            if (set(milestoneTags).intersection(aIssue["labels"])):
                for aTag in set(milestoneTags).intersection(aIssue["labels"]):
                    milestoneIssueLists[str(aTag)].append(aIssue)
            if (set(milestoneTags).intersection(aIssue["milestone"])):
                for aTag in set(milestoneTags).intersection(aIssue["milestone"]):
                    milestoneIssueLists[str(aTag)].append(aIssue)
            if (set(milestoneTags).intersection(aIssue["fixVersions"])):
                for aTag in set(milestoneTags).intersection(aIssue["fixVersions"]):
                    milestoneIssueLists[str(aTag)].append(aIssue)

    #
    # We want the milestones in a particular order so we use the original list
    #
    for aMilestone in milestoneList:
        if (aMilestone["name"] != "Sprint Commits"):
            if (len(milestoneIssueLists[aMilestone["tag"]]) > 0):
                htmlFile.RawHtlmOutput(
                    "<h2><u>" + aMilestone["name"] + " - " + aMilestone["target"] + "</u></h2>" + "\n")
                htmlFile.BeginTable()
                for index, aIssue in enumerate(milestoneIssueLists[aMilestone["tag"]]):
                    if ((index % 16) == 0):
                        htmlFile.TableHeader(
                            ["Type", "Key", "Dev Owner", "Summary", "Priority", "Status", "Story Points"],
                            [8, 10, 8, 39, 8, 14, 8, 7, 7])
                    htmlFile.TableData(aIssue,
                                       ["type", "key", "devOwner", "summary", "priority", "status", "storyPoints"], 1,
                                       aMilestone["color"], "");
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


def IssuesByTeamMember(aIssuesList, aSupportFile, htmlFile, oneNoteFile):
    """ 
    # 
    #  List all of the issues that the team member is:
    #       The devOwner on (that is not in FPV, VC, or closed)
    #       The valOwner on (that is in FPV)
    # 
    # @param aIssueList       List of the issues to work with
    # @param aSupportFile     The support file information.  Scrum team, milestones, etc.
    # @param htmlFile         The HTML output file for the results
    # @param oneNoteFile      The HTML output file for the OneNote notes
    # 
    """
    aCommonReport = common_reports()
    devIssues = {}
    issueAttributes = {}
    milestoneIssueLists = {}

    #
    # Issues are color coded by milestone so we need the milestone lists and tags
    #
    milestoneIssueLists = defaultdict(list)
    milestoneTags = []

    for aMilestone in aSupportFile.milestoneList:
        milestoneTags.append(aMilestone["tag"])

    issueAttributes["color"] = ""
    issueAttributes["title"] = ""
    #
    # Get list of issues assigned to team members 
    #
    devIssues = aCommonReport.issuesByDev(aIssuesList, aSupportFile)

    print("Issues by Team Member")
    htmlFile.RawHtlmOutput("<br>" + "\n")
    htmlFile.RawHtlmOutput("<h2><u>Issues by Team Member</u></h2>" + "\n")
    #
    # Produce the html and oneNote notes
    #
    for aDev in aSupportFile.commitList:
        htmlFile.RawHtlmOutput("    <h3>" + aDev["name"] + "</h3>\n")
        oneNoteFile.RawHtlmOutput("    <h4>" + aDev["name"] + "</h4>\n")
        htmlFile.BeginTable()
        htmlFile.TableHeader(["Commit?", "Type", "Key", "Summary", "Priority", "Status", "Program", "Story Points"],
                             [7, 7, 10, 40, 7, 15, 7, 7])
        #
        # Go through issues list specific to that dev
        #
        #
        # Sort the list so it display prettier
        #
        devIssues[aDev["name"]].sort(key=lambda x: x["programs"])
        for aIssue in devIssues[aDev["name"]]:
            #
            # Initialize issue display attributes
            #
            issueAttributes["color"] = ""
            issueAttributes["title"] = ""
            tmpIssue = {}
            tmpIssue["commit"] = " - - - "
            #
            # Determine Coloration by checking for commit, stretch, and milestone
            #
            #
            # Determine if issues is commit or stretch goal
            #
            for aDev in aSupportFile.commitList:
                if (len(aDev["commit"]) > 0):
                    if (aIssue["key"] in aDev["commit"]):
                        tmpIssue["commit"] = "Commit"
                        issueAttributes["color"] = aSupportFile.commitColor
                        issueAttributes["title"] = "Commit"
                if (len(aDev["stretch"]) > 0):
                    if (aIssue["key"] in aDev["stretch"]):
                        tmpIssue["commit"] = "Stretch"
                        issueAttributes["color"] = aSupportFile.stretchColor
                        issueAttributes["title"] = "Stretch"

            #
            # Check for any milestone tag in the labels, milestone or fixVersions field
            # Multiple milestones may appear so we add to the appropriate dictionary lists
            # Note: Need to make a utility function to do this and return all of the matches
            #
            if (set(milestoneTags).intersection(aIssue["labels"])):
                for aTag in set(milestoneTags).intersection(aIssue["labels"]):
                    for aMilestone in aSupportFile.milestoneList:
                        if (str(aTag) in aMilestone["tag"]):
                            issueAttributes["color"] = aMilestone["color"]
                            issueAttributes["title"] = aMilestone["name"]
            if (set(milestoneTags).intersection(aIssue["milestone"])):
                for aTag in set(milestoneTags).intersection(aIssue["milestone"]):
                    for aMilestone in aSupportFile.milestoneList:
                        if (str(aTag) in aMilestone["tag"]):
                            issueAttributes["color"] = aMilestone["color"]
                            issueAttributes["title"] = aMilestone["name"]
            if (set(milestoneTags).intersection(aIssue["fixVersions"])):
                for aTag in set(milestoneTags).intersection(aIssue["fixVersions"]):
                    for aMilestone in aSupportFile.milestoneList:
                        if (str(aTag) in aMilestone["tag"]):
                            issueAttributes["color"] = aMilestone["color"]
                            issueAttributes["title"] = aMilestone["name"]

            #
            # Add to commit dictionary the issue dictionary so we have all the information in one spot
            #
            tmpIssue.update(aIssue)

            #
            # need function to find milestone name and color
            #
            htmlFile.TableData(tmpIssue,
                               ["commit", "type", "key", "summary", "priority", "status", "programs", "storyPoints"], 2,
                               issueAttributes["color"], issueAttributes["title"]);
            oneNoteFile.RawHtlmOutput("&nbsp;&nbsp;&nbsp;&nbsp;" + aIssue["key"] + "&nbsp;-&nbsp;<br>" + "\n")

        oneNoteFile.RawHtlmOutput("&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;<br>" + "\n")
        oneNoteFile.RawHtlmOutput("&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;<br>" + "\n")
        oneNoteFile.RawHtlmOutput("&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;<br>" + "\n")
        htmlFile.EndTable()


def TeamMemberCommits(aIssuesList, aSupportFile, htmlFile):
    """ 
    # 
    # List the commits by team member
    # 
    # @param aIssueList       List of the issues to work with
    # @param aSupportFile     The support file information.  Scrum team, milestones, etc.
    # @param htmlFile         The HTML output file for the results
    # 
    """
    aCommonReport = common_reports()
    devIssues = {}
    issueAttributes = {}
    milestoneIssueLists = {}
    #
    # Get list of issues assigned to team members 
    #
    devIssues = aCommonReport.commitsByDev(aIssuesList, aSupportFile)

    print("Commits by Team Member")
    htmlFile.RawHtlmOutput("<br>" + "\n")
    htmlFile.RawHtlmOutput("<h2><u>Commits by Team Member</u></h2>" + "\n")
    #
    # Produce the html 
    #
    for aDev in aSupportFile.commitList:
        htmlFile.RawHtlmOutput("    <h3>" + aDev["name"] + "</h3>\n")
        htmlFile.BeginTable()
        htmlFile.TableHeader(["Commit?", "Type", "Key", "Summary", "Priority", "Status", "Program", "Story Points"],
                             [7, 7, 10, 40, 7, 15, 7, 7])
        #
        # Go through issues list specific to that dev
        #
        #
        # Sort the list so it display prettier
        #
        devIssues[aDev["name"]].sort(key=lambda x: x["programs"])
        for aIssue in devIssues[aDev["name"]]:
            #
            # Initialize issue display attributes
            #
            #
            # need function to find milestone name and color
            #
            htmlFile.TableData(aIssue, ["issueCommit", "type", "key", "summary", "priority", "status", "programs",
                                        "storyPoints"], 2, aIssue["issueColor"], aIssue["issueTitle"]);
        htmlFile.EndTable()


def IssueProgramByTeamMember(aIssuesList, aSupportFile, htmlFile):
    """ 
    # 
    # List all of the issues that the developer has worked on so far this sprint
    # This list will contain issues that are in progress, and issues that have passed to FPV or closed this sprint
    # 
    # @param aIssueList       List of the issues to work with
    # @param aSupportFile     The support file information.  Scrum team, milestones, etc.
    # @param htmlFile         The HTML output file for the results
    # 
    """
    aCommonReport = common_reports()
    issueUtility = issue_utility()
    devIssues = {}
    workedIssuesList = []
    sprintBeginDate = datetime.datetime.strptime(str(aSupportFile.sprintEndDate), "%m-%d-%Y") - datetime.timedelta(
        days=14)

    print("Creating Dev Work By Program ")
    htmlFile.RawHtlmOutput("<br>" + "\n")
    htmlFile.RawHtlmOutput("<h2><u>Dev Work By Program</u></h2>" + "\n")

    for aIssue in aIssuesList.teamIssueList:
        #
        # Make list of things in progress or that progressed into any of the states we care about
        #
        if ((issueUtility.getLastToDate(aIssue, "Validation Complete") >= str(sprintBeginDate)) or
                (issueUtility.getLastToDate(aIssue, "In Progress") >= str(sprintBeginDate)) or
                (issueUtility.getLastToDate(aIssue, "Groomed") >= str(sprintBeginDate)) or
                (issueUtility.getLastToDate(aIssue, "Fixed Pending Validation") >= str(sprintBeginDate)) or
                (aIssue["status"] in ["In Progress"])):
            workedIssuesList.append(aIssue)

            #
    # Sort the list so it display prettier
    #
    workedIssuesList.sort(key=lambda x: x["programs"])

    #
    # Produce the html 
    #
    for aDev in aSupportFile.commitList:
        htmlFile.RawHtlmOutput("    <h3>" + aDev["name"] + "</h3>\n")
        htmlFile.BeginTable()
        htmlFile.TableHeader(["Type", "Key", "Summary", "Priority", "Status", "Program", "Story Points"],
                             [7, 10, 40, 7, 15, 7, 7])
        #
        # Go through issues list specific to that dev
        #
        for aIssue in workedIssuesList:
            if (aIssue["devOwner"] == aDev["name"]):
                htmlFile.TableData(aIssue, ["type", "key", "summary", "priority", "status", "programs", "storyPoints"],
                                   1, "", "");
        htmlFile.EndTable()


if __name__ == '__main__':
    aSupportFile = support_file()
    aJiraIssue = jira_issue()
    aIssuesList = jira_issues_lists()
    aSupportFile = support_file()
    getJiraIssues = get_jira_issues()
    htmlFile = htmlGen()
    oneNoteFile = htmlGen()
    start_time = time.time()

    commitFiles = []
    commitList = []
    scrumTeamList = []
    lineNumber = 0

    #
    # Read the number of lines in the file
    #
    fileLines = 0
    for line in open("JiraSnapshot.json"):
        fileLines += 1

    #
    # Read the snapshot data and place fields of interest into database and then into a list in memory
    #
    with open("JiraSnapshot.json", "r") as dataStoreFile:
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

    #
    # List the commit files to read
    #
    commitFiles.append("commit_PROD.txt")
    commitFiles.append("commit_PROA.txt")

    #
    # Cenerate report for each commit file
    #
    for commitIndex, aCommitFile in enumerate(commitFiles):
        aSupportFile.getCommitFile(aCommitFile)
        aIssuesList.setScrumTeam(aSupportFile.scrumTeam)
        print("\n==== Creating reports for ", aSupportFile.scrumTeam)

        #
        # Get work week #
        #
        wwNumber = datetime.date.today().isocalendar()[1]

        #
        # Output filename - First 4 characters of team name with additional filename identification after it
        #
        htmlFile.openHtmlOutput(aIssuesList.whichScrumTeam[0:4].lower() + "_dsu.html")
        htmlFile.BeginHtlmOutput(aSupportFile.scrumTeam + " DSU ww" + str(wwNumber),
                                 aSupportFile.scrumTeam + " DSU ww" + str(wwNumber))

        # --------------------------------
        # Construct Reports
        # --------------------------------

        #
        # Milestones
        #
        htmlFile.RawHtlmOutput("<h1>Milestones </h1>")
        htmlFile.BeginTable()
        htmlFile.TableHeader(["Milestone", "Tag", "Target Date"], [33, 33, 34])
        for aMilestone in aSupportFile.milestoneList:
            htmlFile.TableData(aMilestone, ["name", "tag", "target"], 0, aMilestone["color"], "");
        htmlFile.EndTable()

        #
        # Setup OneNote file
        #
        oneNoteFile.openHtmlOutput(aIssuesList.whichScrumTeam[0:4].lower() + "_onenote.html")
        oneNoteFile.BeginHtlmOutput(aSupportFile.scrumTeam + " DSU - OneNote - Notes - ww" + str(wwNumber),
                                    "OneNote Notes ww" + str(wwNumber))
        oneNoteFile.RawHtlmOutput("<h4>General Information</h4>")
        oneNoteFile.RawHtlmOutput("&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;<br>" + "\n")
        oneNoteFile.RawHtlmOutput("&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;<br>" + "\n")
        oneNoteFile.RawHtlmOutput("&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;<br>" + "\n")
        oneNoteFile.RawHtlmOutput("<h4>Other Items</h4>")
        oneNoteFile.RawHtlmOutput("&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;<br>" + "\n")
        oneNoteFile.RawHtlmOutput("&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;<br>" + "\n")
        oneNoteFile.RawHtlmOutput("&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;<br>" + "\n")

        #
        # Table of all milestones, tags, and target dates
        #
        MilestoneReport(aIssuesList, aSupportFile.milestoneList, htmlFile)
        #
        # Snapshot of sightings
        #
        ProgramSightingSummaryReport(aIssuesList, aSupportFile, htmlFile)
        #
        # Issues being worked by team members
        #
        IssuesByTeamMember(aIssuesList, aSupportFile, htmlFile, oneNoteFile);
        #
        # Display team commits
        #
        TeamMemberCommits(aIssuesList, aSupportFile, htmlFile)

        #
        # Display team commits
        #
        IssueProgramByTeamMember(aIssuesList, aSupportFile, htmlFile)

        #
        # Close the html files
        #
        htmlFile.EndHtlmOutput()
        oneNoteFile.EndHtlmOutput()

    elapsed_time = time.time() - start_time
    print("\nRun time: ", int(elapsed_time), "seconds")
