#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: David Escamilla, Joseph Tarango
# *****************************************************************************/
"""
Update the local jira snapshot with the latest information based on when the file was last changed and the team commits
"""

from classSupportFiles import support_file
from classGetJiraIssues import get_jira_issues

import sys
import time

if __name__ == '__main__':
    aSupportFile = support_file()
    getJiraIssues = get_jira_issues()
    commitFiles = []
    commitList = []
    scrumTeamList = []

    print("Update Snapshot:")
    getJiraIssues.jiraLogin()

    start_time = time.time()

    #
    # Form the query
    # Note: We get updates from all scrum teams.  If we did not, then things moved to other teams would get stale in the local database and never update
    #

    jqlStr = "("
    # Add updated since
    jqlStr += "(updated >= \"" + str(getJiraIssues.findMostRecentUpdate("JiraSnapshot.json")) + "\") and "
    # Get an entire program
    jqlStr += "(project = NSGSE) and "
    # Add issue types
    jqlStr += "issuetype in (Story, \"Development Task\", Sighting, HGST_Sighting) )"

    #
    # List the commit files to read
    #
    commitFiles.append("commit_PROD.txt")
    commitFiles.append("commit_PROA.txt")

    #
    # Add each team's commits and stretches to the query 
    #
    for aCommitFile in commitFiles:
        aSupportFile.getCommitFile(aCommitFile)
        scrumTeamList.append(aSupportFile.scrumTeam)
        for aDev in aSupportFile.commitList:
            for aIssue in aDev["commit"]:
                if (len(aIssue) > 0):
                    jqlStr += " or issuekey=" + str(aIssue)
            for aIssue in aDev["stretch"]:
                if (len(aIssue) > 0):
                    jqlStr += " or issuekey=" + str(aIssue)

    getJiraIssues.retrieveIssueList(jqlStr)
    getJiraIssues.updateSnapshot("JiraSnapshot.json", scrumTeamList)

    elapsed_time = time.time() - start_time
    print("Run time: ", int(elapsed_time), " seconds")
