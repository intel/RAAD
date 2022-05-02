#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: David Escamilla, Joseph Tarango
# *****************************************************************************/
## @package classJIRAIssuesList
"""
jira_issues_lists class converts the fields read from the JSON
file into a list for easier consumption.
Also contains common helper functions.
"""
# , nested_scopes, generators, generator_stop, with_statement, annotations
import time
from datetime import date


class jira_issues_lists(object):
    """
    # jira_issues_lists class converts the fields read from the JSON
    # file into a groovy list for easier consumption by calling
    # routines.
    # <p>
    """
    whichScrumTeam = ""
    issueList = []
    teamIssueList = []
    programDict = {}
    #
    # Variables to describe different general states of the issue
    #
    inBCH = ["Blocker", "Critical", "High"]
    inDevVal = ["Assigned Development", "Assigned Validation", "Confirmed Defect", "In Progress", "New", "Reopened",
                "Groomed"]
    inFixed = ["Duplicate Pending Validation", "Fixed Pending Execution", "Fixed Pending Validation"]
    inFPV = ["Fixed Pending Validation"]
    inClosed = ["Validation Complete", "Closed"]
    inHold = ["On Hold"]

    inBCH = ["Blocker", "Critical", "High"]

    def __init__(self):
        #
        # List of all of the issues in the snapshot.  Note: These issues are dictionaries
        #
        self.issueList = []
        self.whichScrumTeam = ""
        pastSprintStartDate = date.today()

    def reset(self):
        """
        #
        # Resets and clears all of the data
        # Note: likely obsolete function
        #
        """

    def setSprintStartDateFromEnd(self, pastSprintEndDate):
        """
        # Takes the spring end date, calculated the start date, and records it.
        # <p>
        # Note:  We calculate back to the start, since initially the scripts were
        # used to summarize the previous sprint.   Going forward, the scripts
        # are fed the sprint end date for the commits and calculate backward from
        # there to get the start date to look for issues.
        #
        # @param pastSprintEndDate	   The end date of the sprint (data type of Date)
        #
        """
        self.pastSprintStartDate = (pastSprintEndDate - 14)

    def setSprintStartDate(self, startDate):
        """
        # Records it given start date.
        # <p>
        # Note:  We calculate back to the start, since initially the scripts were
        # used to summarize the previous sprint.   Going forward, the scripts
        # are fed the sprint end date for the commits and calculate backward from
        # there to get the start date to look for issues.
        #
        # @param startDate	   The end date of the sprint (data type of Date)
        #
        """
        self.pastSprintStartDate = startDate

    def setScrumTeam(self, aScrumTeam):
        """
        # Sets the scrum team that the report is being made for.
        # <p>
        # This allows us to filter the results based off of a single scrum team.
        #
        # @param aScrumTeam	 the scrum team name
        #
        """
        self.whichScrumTeam = aScrumTeam
        self.teamIssueList = []
        self.programDict = {}
        #
        # Note: this would be a good point to add in the commits/Stretch/ - - - to the dictionary.   A "commitBy" field is needed to since the commit may not be completed by the person committing or they may not have their name on it yet as the dev owner
        #		Further modification to this list to add milestones would be good.  That would need to be a list of milestones, tags and color attributes
        # Note: Since we have CLE Team members on each team, we pull in CLE team as well in this filter
        #
        for aIssue in self.issueList:
            if (((aIssue["scrumTeam"] == aScrumTeam) or (aIssue["scrumTeam"] == "CLE Team")) and (
                    aIssue["type"] in ["Story", "Sighting", "HGST_Sighting", "Development Task"])):
                self.teamIssueList.append(aIssue)
                #
                # Populate the program list and counts of Remaining, FPV, and Closed
                # Note: This likely needs to move out to a stand alone function.  It would be more useful that way.
                #
                for aProgram in aIssue["programs"]:
                    if (aProgram not in self.programDict):
                        self.programDict[str(aProgram)] = {"Remaining": 0, "FPV": 0, "Closed": 0}
                    if (aIssue["type"] in ["Story"]):
                        if (aIssue["status"] in ["Duplicate Pending Validation", "Fixed Pending Execution",
                                                 "Fixed Pending Validation"]):
                            self.programDict[str(aProgram)]["FPV"] = self.programDict[str(aProgram)]["FPV"] + int(
                                aIssue["storyPoints"])
                        elif (aIssue["status"] in ["Validation Complete", "Closed"]):
                            self.programDict[str(aProgram)]["Closed"] = self.programDict[str(aProgram)]["Closed"] + int(
                                aIssue["storyPoints"])
                        else:
                            self.programDict[str(aProgram)]["Remaining"] = self.programDict[str(aProgram)][
                                                                               "Remaining"] + int(aIssue["storyPoints"])

    def addIssue(self, theIssue):
        """
        # Adds the Jira information of interest to the list.
        # Note: This is much different than the groovy version.
        #	   The statistic gathering routines have been removed too.
        #
        # <p>
        #
        # @param theIssue  the class that parsed a single line of the JSON
        #
        """
        self.issueList.append(theIssue)

    def test(self):
        """
        # Adds the Jira information of interest to the list.
        # Note: This is much different than the groovy version.
        #	   The statistic gathering routines have been removed too.
        #
        # <p>
        #
        # @param theIssue  the class that parsed a single line of the JSON
        #
        """
        print("-------------- Test")


class issue_utility(object):
    """
    # A set of helper function for accessing information about a issue
    # <p>
    """

    def getLastToDate(self, aIssue, stateToMatch):
        """
        # Returns the last date that a issue transistioned to the matching state
        #
        # <p>
        #
        # @param aIssue  A single issue
        # @param stateToMatch  string of the state transition to match
        #
        """
        transitionDate = ""
        for transition in aIssue["changelog"]:
            if (transition["toString"] == stateToMatch):
                transitionDate = transition["created"]
        return transitionDate
