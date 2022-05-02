#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: David Escamilla, Joseph Tarango
# *****************************************************************************/
## @package classJIRAIssues
"""
Scans the snapshot for things that happened this week and produces a report
jira_issues_lists class converts the fields read from the JSON
file into a groovy list for easier consumption by calling
routines.
"""
# , nested_scopes, generators, generator_stop, with_statement, annotations
import json
import re


class jira_issue(object):
    """
    # jira_issues class parses a single issue from JSON into variables
    # <p>
    # Note:  These variables are used by the jira_issues_list class to
    #        make the lists of issues
    #
    # @version     1.0
    #
    """

    def __init__(self):
        self.issueDictionary = {}

    def parseJson(self, jsonString):
        """
        # parseJson
        #
        # Parses a single Json string and extracts the parts of the issue we are interested in.
        # populates this classes variables with those part of interest
        # <p>
        #
        # @param jsonString       the string to parse
        """
        # Load the Json line into dictionary format
        jLine = json.loads(jsonString)

        #
        # Per line initialization
        #
        self.issueDictionary = {}
        self.issueDictionary["priority"] = "---"
        self.issueDictionary["description"] = ""
        self.issueDictionary["programs"] = []
        self.issueDictionary["labels"] = []
        self.issueDictionary["milestone"] = ""
        self.issueDictionary["fixVersions"] = []
        self.issueDictionary["assignee"] = ""
        self.issueDictionary["scrumTeam"] = ""
        self.issueDictionary["devOwner"] = ""
        self.issueDictionary["valOwner"] = ""
        self.issueDictionary["submitterOrg"] = ""
        self.issueDictionary["storyPoints"] = "0"
        self.issueDictionary["created"] = ""
        self.issueDictionary["updated"] = ""
        self.issueDictionary["problemArea"] = ""
        self.issueDictionary["type"] = jLine["fields"]["issuetype"]["name"]
        self.issueDictionary["key"] = jLine["key"]
        self.issueDictionary["id"] = jLine["id"]
        if ("priority" in jLine["fields"]):
            if (jLine["fields"]["priority"] != None):
                self.issueDictionary["priority"] = jLine["fields"]["priority"]["name"]
        if ("description" in jLine["fields"]):
            self.issueDictionary["description"] = jLine["fields"]["description"]
        self.issueDictionary["status"] = jLine["fields"]["status"]["name"]
        self.issueDictionary["summary"] = jLine["fields"]["summary"]
        #
        # The program field (customfield_12074) returns a list, so each element is read out for its value into a new list
        # Note: Program size has been removed (it was used in the groovy version of the code
        #
        if ("customfield_12074" in jLine["fields"]):
            tmpList = []
            for aField in jLine["fields"]["customfield_12074"]:
                #
                # Convert to string, since the field is unicode and will place a u'string' in the list if we don't.
                #
                tmpField = str(aField["value"])
                tmpList.append(tmpField)
            self.issueDictionary["programs"] = tmpList[:]

        if (jLine["fields"]["labels"]):
            for aItem in jLine["fields"]["labels"]:
                self.issueDictionary["labels"].append(str(aItem))

        #
        # The milestones field (customfield_10036) returns a list, so each element is read out for its value into a new list
        # Note: Program size has been removed (it was used in the groovy version of the code
        #
        if ("customfield_10036" in jLine["fields"]):
            if (jLine["fields"]["customfield_10036"] != None):
                self.issueDictionary["milestone"] = jLine["fields"]["customfield_10036"]["value"]
        #
        # The fixVersions field returns a list, so each element is read out for its value into a new list
        # Note: Program size has been removed (it was used in the groovy version of the code
        #
        if ("fixVersions" in jLine["fields"]):
            tmpList = []
            for aField in jLine["fields"]["fixVersions"]:
                tmpList.append(aField["name"])
            self.issueDictionary["fixVersions"] = tmpList[:]

        if ("assignee" in jLine["fields"]):
            self.issueDictionary["assignee"] = jLine["fields"]["assignee"]

        if ("customfield_10182" in jLine["fields"]):
            if (jLine["fields"]["customfield_10182"] != None):
                self.issueDictionary["scrumTeam"] = jLine["fields"]["customfield_10182"]["value"]

        if ("customfield_10034" in jLine["fields"]):
            if (jLine["fields"]["customfield_10034"] != None):
                self.issueDictionary["devOwner"] = jLine["fields"]["customfield_10034"]["displayName"]

        if ("customfield_10044" in jLine["fields"]):
            if (jLine["fields"]["customfield_10044"] != None):
                self.issueDictionary["valOwner"] = jLine["fields"]["customfield_10044"]["displayName"]

        if ("customfield_10137" in jLine["fields"]):
            if (jLine["fields"]["customfield_10137"] != None):
                self.issueDictionary["submitterOrg"] = jLine["fields"]["customfield_10137"]["value"]

        if ("customfield_10003" in jLine["fields"]):
            if (jLine["fields"]["customfield_10003"] != None):
                self.issueDictionary["storyPoints"] = str(int(jLine["fields"]["customfield_10003"]))

        if ("created" in jLine["fields"]):
            if (jLine["fields"]["created"] != None):
                self.issueDictionary["created"] = re.sub(r"T", " ", jLine["fields"]["created"])
                self.issueDictionary["created"] = re.sub(r"\..*", "", self.issueDictionary["created"])

        if ("updated" in jLine["fields"]):
            if (jLine["fields"]["updated"] != None):
                self.issueDictionary["updated"] = re.sub(r"T", " ", jLine["fields"]["updated"])
                self.issueDictionary["updated"] = re.sub(r"\..*", "", self.issueDictionary["updated"])

        if ("customfield_10039" in jLine["fields"]):
            if (jLine["fields"]["customfield_10039"] != None):
                self.issueDictionary["problemArea"] = jLine["fields"]["customfield_10039"]["value"]

        #
        # The histories is a list of dictionaries that has lists.
        # At the moment, we are only interested in the history events when the "status" changes from one state to another.
        # We record all of the transitions in a list of dictionaries instead of just recording specific dates of changes, like the groovy version.
        # Functions should be made to provided the date information that was extracted in the groovy version
        #
        if ("histories" in jLine["changelog"]):
            tmpList = []
            for aHistory in jLine["changelog"]["histories"]:
                if ("items" in aHistory):
                    itemGroup = 0
                    for aField in aHistory["items"]:
                        itemGroup += 1
                        if (aField["field"] == "status"):
                            tmpdict = {}
                            # Check to see if there is a create date.  If not then use the issue create date
                            # It is normal for the first entry not to have a create date, since it shares with the create of the jira
                            if ("created" in aHistory):
                                tmpDate = re.sub(r"T", " ", aHistory["created"])
                                tmpDate = re.sub(r"\..*", "", tmpDate)
                                tmpdict["created"] = tmpDate
                            else:
                                tmpdict["created"] = self.issueDictionary["created"]
                            tmpdict["fromString"] = aField["fromString"]
                            tmpdict["toString"] = aField["toString"]
                            tmpList.append(tmpdict)
            self.issueDictionary["changelog"] = tmpList[:]


if __name__ == '__main__':
    aJiraIssue = jira_issue()
    lineNumber = 0

    with open("JiraSnapshot.json", "r") as dataStoreFile:
        for aLine in dataStoreFile:
            lineNumber += 1
            aJiraIssue.parseJson(aLine.decode('latin1').encode('utf8'))
