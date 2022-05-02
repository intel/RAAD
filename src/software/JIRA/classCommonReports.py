#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: David Escamilla, Joseph Tarango
# *****************************************************************************/
"""
Common reports
Retrieves data for common reports
"""


# , nested_scopes, generators, generator_stop, with_statement, annotations

class common_reports(object):
    """
    # Generates all of the html output
    # <p>
    """
    htmlOutputFileName = ""
    htmlOutput = None
    urlRoot = "http://nsg-jira.intel.com"  # Root url for Atlassian server

    def sightingsSummaryByProgram(self, aIssuesList):
        """
        #
        # Gathers count of issues in each priority by program
        # Note: Uses the team list of issues, so that we don't have to filter by team
        #
        # @param aIssuesList         Filename to open
        #
        # @Returns Returns a dictionary with keys of the program name and list of number of priority of sightings
        #
        """
        sightingsSummary = {}
        #
        # Scan the snapshot of those issues specific to the team and seperate into milestone lists
        #
        for aIssue in aIssuesList.teamIssueList:
            #
            # Since the CLE team is a part of this list, remove them from this report
            #
            if (aIssue["scrumTeam"] in aIssuesList.whichScrumTeam):
                #
                # We only are interested in sightings with suspected problem areas of FW and unknown
                #
                if ((aIssue["type"] in ["Sighting", "HGST_Sighting"]) and
                        ((aIssue["problemArea"] == "FW") or (aIssue["problemArea"] == "Unknown")) and
                        ((aIssue["status"] in aIssuesList.inFPV) or (aIssue["status"] in aIssuesList.inDevVal))):
                    #
                    # if new program initialize it
                    #
                    if str(aIssue["programs"]) not in list(sightingsSummary.keys()):
                        priorityTypes = {"bch": 0, "med": 0, "fpv": 0}
                        sightingsSummary[str(aIssue["programs"])] = priorityTypes
                    #
                    # Determine which grouping the sighting goes in
                    #
                    if (aIssue["status"] in aIssuesList.inFPV):
                        sightingsSummary[str(aIssue["programs"])]["fpv"] = sightingsSummary[str(aIssue["programs"])][
                                                                               "fpv"] + 1
                    elif (aIssue["status"] in aIssuesList.inDevVal):
                        if (aIssue["priority"] in aIssuesList.inBCH):
                            sightingsSummary[str(aIssue["programs"])]["bch"] = \
                            sightingsSummary[str(aIssue["programs"])]["bch"] + 1
                        else:
                            sightingsSummary[str(aIssue["programs"])]["med"] = \
                            sightingsSummary[str(aIssue["programs"])]["med"] + 1
        #       for key in sightingsSummary:
        #           print key, sightingsSummary[key]
        return sightingsSummary

    def sightingsBCH(self, aIssuesList):
        """
        #
        # Gathers a list of all BCH sightings in dev, val or FPV.
        # Note: Uses the team list of issues, so that we don't have to filter by team
        #
        # @param aIssuesList         Filename to open
        #
        # @Returns Returns a list of all BCH issues in dev, val, or FPV
        #
        """
        bchSightingList = []
        #
        # Scan the snapshot of those issues specific to the team and seperate into milestone lists
        #
        for aIssue in aIssuesList.teamIssueList:
            #
            # Since the CLE team is a part of this list, remove them from this report
            #
            if (aIssue["scrumTeam"] in aIssuesList.whichScrumTeam):
                #
                #
                # We only are interested in sightings with suspected problem areas of FW and unknown
                #
                if ((aIssue["type"] in ["Sighting", "HGST_Sighting"]) and
                        ((aIssue["problemArea"] == "FW") or (aIssue["problemArea"] == "Unknown")) and
                        ((aIssue["status"] in aIssuesList.inFPV) or (aIssue["status"] in aIssuesList.inDevVal))):
                    #
                    # Check for any milestone tag in the labels, milestone or fixVersions field
                    #
                    if (aIssue["priority"] in aIssuesList.inBCH):
                        bchSightingList.append(aIssue)

        return bchSightingList

    def issuesByDev(self, aIssuesList, aSupportFile):
        """
        #
        # Seperates the list of issues by developer (dev Owner, Val Owner (if in FPV))
        # This represents only things they are currently working (have their name not) not commits/stretches
        # The priority is not filtered in the returns, so all priority levels are in the list
        # Note: Uses the team list of issues, so that we don't have to filter by team
        #
        # @param aIssuesList         Filename to open
        #
        # @Returns Returns a dictionary of list developers and list of the issues that they are working on
        #
        """
        devIssues = {}
        devList = []
        #
        # Scan the snapshot of those issues specific to the team and seperate into milestone lists
        #
        for aDev in aSupportFile.commitList:
            devIssues[aDev["name"]] = []
            devList.append(aDev["name"])

        #
        # Compile the list of issues that the developer is currently working on
        #
        for aIssue in aIssuesList.teamIssueList:
            if (aIssue["status"] in aIssuesList.inDevVal):
                if (aIssue["devOwner"] in devList):
                    devIssues[str(aIssue["devOwner"])].append(aIssue)
            elif (aIssue["status"] in aIssuesList.inFPV):
                if (aIssue["valOwner"] in devList):
                    devIssues[str(aIssue["valOwner"])].append(aIssue)

        return devIssues

    def commitsByDev(self, aIssuesList, aSupportFile):
        """
        #
        # Seperates the list of issues by developer (dev Owner, Val Owner (if in FPV))
        # This represents only things they are currently working (have their name not) not commits/stretches
        # The priority is not filtered in the returns, so all priority levels are in the list
        # Note: Uses the team list of issues, so that we don't have to filter by team
        #
        # @param aIssuesList         Filename to open
        #
        # @Returns Returns a dictionary of list developers and list of the issues that they are working on
        #
        """
        devIssues = {}
        #
        # Scan the snapshot of those issues specific to the team and seperate into milestone lists
        #
        for aDev in aSupportFile.commitList:
            devIssues[aDev["name"]] = []

        #
        # Compile the list of issues that the developer is currently working on
        #
        for aIssue in aIssuesList.teamIssueList:
            #
            # Determine if issues is commit or stretch goal
            #
            for aDev in aSupportFile.commitList:
                if (len(aDev["commit"]) > 0):
                    if (aIssue["key"] in aDev["commit"]):
                        tmpIssue = {}
                        tmpIssue["issueCommit"] = "Commit"
                        tmpIssue["issueColor"] = aSupportFile.commitColor
                        tmpIssue["issueTitle"] = "Commit"
                        #
                        # Add to commit dictionary the issue dictionary so we have all the information in one spot
                        #
                        tmpIssue.update(aIssue)
                        devIssues[str(aDev["name"])].append(tmpIssue)

                if (len(aDev["stretch"]) > 0):
                    if (aIssue["key"] in aDev["stretch"]):
                        tmpIssue = {}
                        tmpIssue["issueCommit"] = "Stretch"
                        tmpIssue["issueColor"] = aSupportFile.stretchColor
                        tmpIssue["issueTitle"] = "Stretch"
                        #
                        # Add to commit dictionary the issue dictionary so we have all the information in one spot
                        #
                        tmpIssue.update(aIssue)
                        devIssues[str(aDev["name"])].append(tmpIssue)
        return devIssues

    def allDevCommits(self, aIssuesList, aSupportFile):
        """
        #
        # Seperates the list of issues by developer (dev Owner, Val Owner (if in FPV))
        # This represents only things they are currently working (have their name not) not commits/stretches
        # The priority is not filtered in the returns, so all priority levels are in the list
        # Note: Uses the team list of issues, so that we don't have to filter by team
        #
        # @param aIssuesList         Filename to open
        #
        # @Returns Returns a dictionary of list developers and list of the issues that they are working on
        #
        """
        devIssues = []

        #
        # Compile the list of issues that the developer is currently working on
        #
        for aIssue in aIssuesList.teamIssueList:
            #
            # Determine if issues is commit or stretch goal
            #
            for aDev in aSupportFile.commitList:
                if (len(aDev["commit"]) > 0):
                    if (aIssue["key"] in aDev["commit"]):
                        tmpIssue = {}
                        tmpIssue["issueCommit"] = "Commit"
                        tmpIssue["issueColor"] = aSupportFile.commitColor
                        tmpIssue["issueTitle"] = "Commit"
                        #
                        # Add to commit dictionary the issue dictionary so we have all the information in one spot
                        #
                        tmpIssue.update(aIssue)
                        devIssues.append(tmpIssue)

                if (len(aDev["stretch"]) > 0):
                    if (aIssue["key"] in aDev["stretch"]):
                        tmpIssue = {}
                        tmpIssue["issueCommit"] = "Stretch"
                        tmpIssue["issueColor"] = aSupportFile.stretchColor
                        tmpIssue["issueTitle"] = "Stretch"
                        #
                        # Add to commit dictionary the issue dictionary so we have all the information in one spot
                        #
                        tmpIssue.update(aIssue)
                        devIssues.append(tmpIssue)
        return devIssues
