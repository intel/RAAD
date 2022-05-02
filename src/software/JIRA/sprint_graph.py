#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: David Escamilla, Joseph Tarango
# *****************************************************************************/
""" 
Creates a color coded table representation of the long range plan.
The table is based on the sprint tags that are on the issues.
"""

from classCommonReports import common_reports
from classGetJiraIssues import get_jira_issues
from classHtmlGen import htmlGen
from classJiraIssues import jira_issue
from classJiraIssuesList import issue_utility
from classJiraIssuesList import jira_issues_lists
from classSupportFiles import support_file
from datetime import date, timedelta
from datetime import datetime
from collections import defaultdict
from copy import deepcopy

import datetime
import json
import re
import sys
import time


def MilestoneReport(aIssuesList, milestoneList, sprintRange, htmlFile):
    """ 
    # 
    # MilestoneReport
    # Display the color coded milestones with the tag to search for and target date
    # NOTE: This is almost identical to the MilestoneReport in team_progress.py.  
    #       Need to create a common fuction to gather the common information in both of these 
    # 
    # @param aIssueList       List of the issues to work with
    # @param milestones       List of Milestones
    # @param sprintRange      List with the first element as the first sprint to have in the table, and second element the last sprint in the table produced
    # @param htmlFile         The HTML output file for the results
    # 
    """
    milestoneIssueLists = {}
    milestoneIssueLists = defaultdict(list)
    sprintTagIssuesList = {}
    sprintTagIssuesListPerMilestone = {}
    sprintTagIssuesList = defaultdict(list)
    sprintTagMap = {}
    sprintTagMap = defaultdict(list)
    milestoneTags = []
    sprintTagList = []
    tableHeaderList = []
    tableIndex = []
    numberOfColumns = 25

    for aMilestone in milestoneList:
        milestoneTags.append(aMilestone["tag"])

    #
    # Start by creating a list of dictionaries with the spritn tag in them.  
    # initialize the list with a longer list of columns than we expect to use
    #
    for aSprint in range(((sprintRange[1] - sprintRange[0]) / 2) + 1):
        sprintTagMap["2013.WW" + str(sprintRange[0] + (aSprint * 2)) + ".Sprint"] = [
            {"text": "", "key": "", "color": "FFFFFF", "title": ""} for x in range(50)]
        sprintTagMap["2013.WW" + str(sprintRange[0] + (aSprint * 2)) + ".Sprint"][0] = {
            "text": str("2013.WW" + str(sprintRange[0] + (aSprint * 2)) + ".Sprint"), "key": "", "color": "FFFFFF",
            "title": str("2013.WW" + str(sprintRange[0] + (aSprint * 2)) + ".Sprint")}
        sprintTagList.append("2013.WW" + str(sprintRange[0] + (aSprint * 2)) + ".Sprint")

    #
    # Scan the snapshot of those issues specific to the team and seperate into milestone lists
    #
    for aIssue in aIssuesList.teamIssueList:
        #
        # Since the CLE team is a part of this list, remove them from this report
        #
        if (aIssue["scrumTeam"] in aIssuesList.whichScrumTeam):
            #
            # We only are interested in those in dev or val and only stories
            #
            if ((aIssue["status"] in aIssuesList.inDevVal) and (aIssue["type"] in ["Story"])):
                #
                # We calture only one milestone tag to pass on to the graph
                #
                aSingleMilestoneTag = ""
                #
                # Check for any milestone tag in the labels, milestone or fixVersions field
                # Multiple milestones may appear so we add to the appropriate dictionary lists
                #
                if (set(milestoneTags).intersection(aIssue["labels"])):
                    for aTag in set(milestoneTags).intersection(aIssue["labels"]):
                        milestoneIssueLists[str(aTag)].append(aIssue)
                        aSingleMilestoneTag = str(aTag)
                if (set(milestoneTags).intersection(aIssue["milestone"])):
                    for aTag in set(milestoneTags).intersection(aIssue["milestone"]):
                        milestoneIssueLists[str(aTag)].append(aIssue)
                        aSingleMilestoneTag = str(aTag)
                if (set(milestoneTags).intersection(aIssue["fixVersions"])):
                    for aTag in set(milestoneTags).intersection(aIssue["fixVersions"]):
                        milestoneIssueLists[str(aTag)].append(aIssue)
                        aSingleMilestoneTag = str(aTag)

                #
                # Record the information we need into a smaller list
                #
                for aTag in set(sprintTagList).intersection(aIssue["fixVersions"]):
                    if (len(aSingleMilestoneTag) > 0):
                        sprintTagIssuesList[aIssue["key"]] = {
                            "text": str(aIssue["key"]) + "(" + str(aIssue["storyPoints"]) + ")", "key": aIssue["key"],
                            "color": milestoneList[milestoneTags.index(aSingleMilestoneTag)]["color"],
                            "title": milestoneList[milestoneTags.index(aSingleMilestoneTag)]["name"], "tag": aTag,
                            "sprints": set(sprintTagList).intersection(aIssue["fixVersions"]), "mapped": 0,
                            "milestoneTag": milestoneList[milestoneTags.index(aSingleMilestoneTag)]["tag"]}
                    else:
                        sprintTagIssuesList[aIssue["key"]] = {
                            "text": str(aIssue["key"]) + "(" + str(aIssue["storyPoints"]) + ")", "key": aIssue["key"],
                            "color": "FFFFFF", "title": "", "tag": "",
                            "sprints": set(sprintTagList).intersection(aIssue["fixVersions"]), "mapped": 0,
                            "milestoneTag": ""}

    #
    # Find a spot in the table for the issues
    # Note: We used sprintTagList, since it is an ordered list, unlike dictionary keys
    #
    numberOfColumns = 0
    for aSprintTag in sprintTagList:
        for aIssueKey in sprintTagIssuesList.keys():
            if ((aSprintTag in sprintTagIssuesList[aIssueKey]["sprints"]) and (
                    sprintTagIssuesList[aIssueKey]["mapped"] == 0)):
                #
                # Issue has the sprint tag and has not been mapped yet into the table
                #
                #
                # Since we fill in from the lowest to highest sprint, we just need to look for the first open slot and place it there.
                # Note: We assume that the stories are completed without a break.  for example a story is done in sprint X and X+1, not sprint X and X+2
                #
                for aColumn in range(1, 50):
                    if (sprintTagMap[aSprintTag][aColumn]["key"] == ""):
                        for aTag in set(sprintTagList).intersection(sprintTagIssuesList[aIssueKey]["sprints"]):
                            sprintTagIssuesList[aIssueKey]["mapped"] = 1
                            sprintTagMap[aTag][aColumn] = deepcopy(sprintTagIssuesList[aIssueKey])
                            if (aColumn > numberOfColumns):
                                numberOfColumns = aColumn
                        break
    #
    # Clear all mapped flags
    #
    for aIssueKey in sprintTagIssuesList.keys():
        sprintTagIssuesList[aIssueKey]["mapped"] = 0

    #
    # With the numberOfColumns in the map, pop all of the empty columns off the list
    #
    for aTag in sprintTagList:
        for aPop in range(int(49 - numberOfColumns)):
            sprintTagMap[aTag].pop()

    #
    # Setup Sprint header.  Note: need to fix up this section so it grows and shrinks.
    #
    percentPerColumn = int(100 / numberOfColumns)
    listOfPercentage = []
    for aColumn in range(numberOfColumns + 1):
        if (aColumn == 0):
            tableHeaderList.append("Sprint")
        else:
            tableHeaderList.append("")
        listOfPercentage.append(percentPerColumn)
        tableIndex.append(aColumn)

    htmlFile.BeginTable()
    htmlFile.TableHeader(tableHeaderList, listOfPercentage)

    for aSprint in sprintTagList:
        htmlFile.TableDataColor(sprintTagMap[aSprint])
    htmlFile.EndTable()

    #
    # We want the milestones in a particular order so we use the original list
    #
    for aMilestone in milestoneList:
        if (aMilestone["name"] != "Sprint Commits"):
            if (len(milestoneIssueLists[aMilestone["tag"]]) > 0):
                milestoneKeyList = []
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
                    milestoneKeyList.append(aIssue["key"])
                htmlFile.EndTable()
                htmlFile.RawHtlmOutput("<br>" + "\n")
                #
                # Clear the table
                #
                for aSprint in range(((sprintRange[1] - sprintRange[0]) / 2) + 1):
                    sprintTagMap["2013.WW" + str(sprintRange[0] + (aSprint * 2)) + ".Sprint"] = [
                        {"text": "", "key": "", "color": "FFFFFF", "title": ""} for x in range(numberOfColumns + 1)]
                    sprintTagMap["2013.WW" + str(sprintRange[0] + (aSprint * 2)) + ".Sprint"][0] = {
                        "text": str("2013.WW" + str(sprintRange[0] + (aSprint * 2)) + ".Sprint"), "key": "",
                        "color": "FFFFFF", "title": str("2013.WW" + str(sprintRange[0] + (aSprint * 2)) + ".Sprint")}
                    #
                # Find a spot in the table for the issues
                # Note: We used sprintTagList, since it is an ordered list, unlike dictionary keys
                #
                for aSprintTag in sprintTagList:
                    for aIssueKey in sprintTagIssuesList.keys():
                        if ((aSprintTag in sprintTagIssuesList[aIssueKey]["sprints"]) and
                                (sprintTagIssuesList[aIssueKey]["mapped"] == 0) and
                                (aMilestone["tag"] == sprintTagIssuesList[aIssueKey]["milestoneTag"])):
                            #
                            # Issue has the sprint tag and has not been mapped yet into the table
                            #
                            #
                            # Since we fill in from the lowest to highest sprint, we just need to look for the first open slot and place it there.
                            # Note: We assume that the stories are completed without a break.  for example a story is done in sprint X and X+1, not sprint X and X+2
                            #
                            for aColumn in range(1, 50):
                                if (sprintTagMap[aSprintTag][aColumn]["key"] == ""):
                                    for aTag in set(sprintTagList).intersection(
                                            sprintTagIssuesList[aIssueKey]["sprints"]):
                                        sprintTagIssuesList[aIssueKey]["mapped"] = 1
                                        sprintTagMap[aTag][aColumn] = deepcopy(sprintTagIssuesList[aIssueKey])
                                    break
                #
                # Clear all mapped flags
                #
                for aIssueKey in sprintTagIssuesList.keys():
                    sprintTagIssuesList[aIssueKey]["mapped"] = 0

                htmlFile.BeginTable()
                htmlFile.TableHeader(tableHeaderList, listOfPercentage)

                for aSprint in sprintTagList:
                    htmlFile.TableDataColor(sprintTagMap[aSprint])
                htmlFile.EndTable()


if __name__ == '__main__':
    aSupportFile = support_file()
    aJiraIssue = jira_issue()
    aIssuesList = jira_issues_lists()
    aSupportFile = support_file()
    getJiraIssues = get_jira_issues()
    htmlFile = htmlGen()
    start_time = time.time()

    milestoneIssueDict = {}

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
        htmlFile.openHtmlOutput(aIssuesList.whichScrumTeam[0:4].lower() + "_graph.html")
        htmlFile.BeginHtlmOutput(aSupportFile.scrumTeam + " Graph as of ww" + str(wwNumber),
                                 aSupportFile.scrumTeam + " Graph as of ww" + str(wwNumber))

        # --------------------------------
        # Construct Reports
        # --------------------------------

        #
        # Sort the list so it display prettier
        #
        aSupportFile.milestoneList.sort(key=lambda x: x["target"])

        #
        # Table of all milestones, tags, and target dates
        #
        MilestoneReport(aIssuesList, aSupportFile.milestoneList, [17, 52], htmlFile)

    elapsed_time = time.time() - start_time
    print("\nRun time: ", int(elapsed_time), "seconds")
