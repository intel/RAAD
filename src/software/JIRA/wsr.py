#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, David A Escamilla
# *****************************************************************************/
"""
Scans the snapshot for things that happened this week and produces a report
jira_issues_lists class converts the fields read from the JSON 
file into a groovy list for easier consumption by calling
routines.
"""

import json
import sys
import time
import datetime
from classHtmlGen import htmlGen
from classSupportFiles import support_file
from classJiraIssues import jira_issue
from classJiraIssuesList import jira_issues_lists
from classJiraIssuesList import issue_utility

"""
NEW requested format as of 7/12/2013:  See email for 7/12/2013.  New format has colors, and text formatting.  Need to produce HTML format of it

Recognitions
*         Good work by HWF Team unlocking the Ramdisk developers and enabling them to complete their work prior to transitioning to SXP.
Highlights
*         FD: Several Test Commands for Fultondale implemented by Productization team, along with implementation of Erase Dwell time story handling invalid bands; 3 stories/ 23 story points transitioned to Validation Complete this week. Reactive team making good progress towards mini-RDT, on track to keep previously communicated delay to one week. Last two development stories in progress, and the team is preparing to complete validation by ww28.5 (also needed for SP). HWF team released BL (FD1.07) addressing a number of sightings and delivered DRAM ECC and inject DRAM bit error functionality, unblocking the Ramdisk team before their transition to SXP. NVMe team continues to make good progress on DMA, Get Native Max LBA vendor unique command, and MAXLBA support and resolved a number of issues including Linux failing to re-initialize, GPBuffer management to prevent blocking
*         WL: Productization team fixed sighting which hindered debug of Wolfsville drives.
General:
*         NTR

Low Lights
*         FD: NVMe team root caused PatinPF failures, an issue with A0 on DMA reads with respect to host memory alignment. KSW team is investigating possible workarounds with B0 fix likely required. Team has completed 2 person months of work that are waiting for efuse (security) test capability prior to closure. FD BL 1.06 released by HWF team last week caused issues with PCIe on the 2 terabyte B3 build A0 board. Issue was subsequently resolved in the 1.07 release.
*         All Programs: Proactive and Productization teams progress slowed due to HCL training in LM this week
"""


def WSRReport(aIssuesList, milestones, lastSunday, htmlFile):
    """ 
    # WSRReport
    # Gather all of the information for the Weekly Status Report
    #
    # @param aIssueList       List of the issues to work with
    # @param milestones       Milestone
    # @param htmlFile         The HTML output file for the results
    # 
    #######
    # 
    # Example of desired output format:
    #  <b><u>Productization</b></u></br>
    #  3 Sightings FPV</br>
    #  2 Stories FPV (3 pts)</br>
    #  <dl>
    #  <dt><u>Highlights</u></dt>
    #  <dd> - Bennettsville Phase 3 story moved to FPV </dd>
    #  <dd> - Story to update TWDL with new tokens moved to FPV</dd>
    #  <dt><u>Lowlights</u></dt>
    #  <dd> - Continued difficulty getting FD test boxes in a stable state for development.</dd>
    #  <dd> - Jira Spam noted as a problem, since it is hard to tell what is an important change to a jira item versus one which does not matter to developers.</dd>
    #  </dl
    # 
    """
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
            if ((issueUtility.getLastToDate(aIssue, "Validation Complete") >= str(lastSunday)) and (
                    aIssue["type"] in ["Story"])):
                toVcStoryList.append(aIssue)

                #
            # Make list of In Progress
            #
            if ((aIssue["status"] in ["In Progress"]) and (aIssue["type"] in ["Story", "Sighting", "HGST_Sighting"])):
                inProgressList.append(aIssue)
                #
            # Make list of sightings to FPV
            #
            if ((issueUtility.getLastToDate(aIssue, "Fixed Pending Validation") >= str(lastSunday)) and (
                    aIssue["type"] in ["Sighting"])):
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
    # Summary section of total of sightings and stories to FPV
    #
    if (len(toFpvSightingList) == 1):
        htmlFile.RawHtlmOutput(" " + str(len(toFpvSightingList)) + " Sighting to FPV</br>" + "\n")
    else:
        htmlFile.RawHtlmOutput(" " + str(len(toFpvSightingList)) + " Sightings to FPV</br>" + "\n")

    if (len(toFpvSightingList) == 1):
        htmlFile.RawHtlmOutput(
            " " + str(len(toVcStoryList)) + " Story (" + str(toVcStoryPoints) + " pts) to VC</br>" + "\n")
    else:
        htmlFile.RawHtlmOutput(
            " " + str(len(toVcStoryList)) + " Stories (" + str(toVcStoryPoints) + " pts) to VC</br>" + "\n")

    #
    # Detailed highlights
    #
    htmlFile.RawHtlmOutput("<dl>" + "\n")
    htmlFile.RawHtlmOutput("<dt><u>Highlights</u></dt>" + "\n")
    for aIssue in toFpvSightingList:
        htmlFile.RawHtlmOutput(
            "<dd> - " + str(aIssue["summary"]) + " moved to FPV (" + str(aIssue["type"]) + ", " + str(
                aIssue["programs"]) + ") (" + str(aIssue["key"]) + ")</dd>" + "\n")

    for aIssue in toVcStoryList:
        htmlFile.RawHtlmOutput("<dd> - " + str(aIssue["summary"]) + " moved to VC (" + str(aIssue["type"]) + " (" + str(
            aIssue["storyPoints"]) + " pts), " + str(aIssue["programs"]) + ") (" + str(aIssue["key"]) + ")</dd>" + "\n")

    #
    # Detailed highlights
    #
    htmlFile.RawHtlmOutput("<dt><u>Work In-Progress</u></dt>" + "\n")
    for aIssue in inProgressList:
        if (aIssue["type"] in ["Sighting", "HGST_Sighting"]):
            htmlFile.RawHtlmOutput("<dd> - " + str(aIssue["summary"]) + " (" + str(aIssue["type"]) + ", " + str(
                aIssue["programs"]) + ")  (" + str(aIssue["key"]) + ")</dd>" + "\n")
        else:
            htmlFile.RawHtlmOutput("<dd> - " + str(aIssue["summary"]) + " (" + str(aIssue["type"]) + " (" + str(
                aIssue["storyPoints"]) + " pts), " + str(aIssue["programs"]) + ")  (" + str(
                aIssue["key"]) + ")</dd>" + "\n")

    #
    # Lowlights left blank to fill in manually
    #
    htmlFile.RawHtlmOutput("<dt><u>Lowlights</u></dt>" + "\n")
    htmlFile.RawHtlmOutput("<dd> - </dd>" + "\n")
    htmlFile.RawHtlmOutput("<dd> - </dd>" + "\n")
    htmlFile.RawHtlmOutput("<dd> - </dd>" + "\n")
    htmlFile.RawHtlmOutput("</dl>" + "\n")


if __name__ == '__main__':
    start_time = time.time()
    aJiraIssue = jira_issue()
    aIssuesList = jira_issues_lists()
    aSupportFile = support_file()
    milestoneList = []
    commitList = []
    commitFiles = []
    DEBUG = 10
    lineNumber = 0
    oneNoteFile = htmlGen()

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
    # Determine the date range that we are working with
    #
    print("    Today's Date: ", datetime.date.today())
    deltaFromSunday = datetime.date.today()
    wwNumber = deltaFromSunday.isocalendar()[1]
    print("              WW: ", wwNumber)

    #
    # Calculate last Sunday's date
    #
    deltaFromSunday = datetime.timedelta(days=((deltaFromSunday.timetuple().tm_wday) + 1))
    lastSunday = datetime.date.today() - deltaFromSunday

    #
    # Zero out the hours, minutes, and seconds
    #
    lastSunday = datetime.datetime(lastSunday.year, lastSunday.month, lastSunday.day)
    print(" Week Begin Date: ", lastSunday)

    #
    # Open filename for writing
    #
    fileName = "WSR_WW" + str(wwNumber) + "_onenote.html"
    oneNoteFile.openHtmlOutput(fileName)
    oneNoteFile.BeginHtlmOutput("WSR - " + str(wwNumber) + " - OneNote - Notes", "OneNote Notes")

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
    for aCommitFile in commitFiles:
        aSupportFile.getCommitFile(aCommitFile)
        aIssuesList.setScrumTeam(aSupportFile.scrumTeam)
        print("Scrum Team: ", aSupportFile.scrumTeam)
        print("Sprint End Date: ", aSupportFile.sprintEndDate)
        aIssuesList.setScrumTeam(aSupportFile.scrumTeam)
        print("set Scrum team : ", aIssuesList.whichScrumTeam)

        oneNoteFile.RawHtlmOutput("<b><u>" + str(aIssuesList.whichScrumTeam) + "</b></u></br>")
        WSRReport(aIssuesList, aSupportFile.milestoneList, lastSunday, oneNoteFile)
    oneNoteFile.EndHtlmOutput()
    elapsed_time = time.time() - start_time
    print("Run time: ", elapsed_time)
