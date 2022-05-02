#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: David Escamilla, Joseph Tarango, Rogelio Macedo
# *****************************************************************************/
"""

Description: Get Jira Issue class performs steps need to query and retrieve issues from jira

Sample Usage for Jira data-preprocessing:
- Working Directory: raad
- command: python3 src/software/JIRA/classGetJiraIssues.py -k DF049 -a Data/jiraData/queries.txt
 - flags: -k: datakey, -a: all, perform all functions: query data -> output clean data

Construct the REST call (url to call) to get the information that is needed
REST API documentation can be found here:
https://developer.atlassian.com/display/REST/REST+API+Developer+Documentation

Examples of types of queries can be found here
http://extensions.xwiki.org/xwiki/bin/view/Extension/JIRA+REST+Integration

http://docs.atlassian.com/jira/REST/latest/

In general, for 4.3.1 the format follows:
${urlRoot}/rest/api/2.0.alpha1

In general, for 5.1 the format follows:
${urlRoot}/rest/api/2/

To perform the same type of queries that are used in the Jira GUI, the following is used:
  ${urlRoot}/rest/api/2.0.alpha1/search?jql=

For clarity, the query has been seperated onto a different line.  This makes cut and paste
from existing queries a lot easier.

Examples of queries:

addr = "${urlRoot}/rest/api/2/issue/$issueNumber?expand=changelog,schema"
addr = "${urlRoot}/rest/api/2/issue/NSGSE-8413?expand=changelog,schema"
addr = "${urlRoot}/rest/api/2/search?jql=issuekey=NSGSE-8413&expand=changelog,schema"

"""

# , nested_scopes, generators, generator_stop, with_statement, annotations
from classSupportFiles import support_file
from classJiraIssues import jira_issue
from classJiraIssuesList import jira_issues_lists
from src.software.utilsCommon import tryFolder
from classJiraIssuesList import issue_utility
from datetime import date
import base64
import getpass
import pandas as pd
import json
import os
import re
import sys
import datetime
import time
import urllib.request  # , urllib.parse, urllib.error
import urllib3
import requests
from atlassian import Jira
import argparse
import traceback
import pprint
from src.software.DP import flat2NestedDict as nestedDict


class get_jira_issues(object):
    """
    # get_jira_issues class retrieves the issues from Jira and stores them in a JSON format
    # <p>
    # The following are performed by this class
    #   - password input (username is hard coded to daescamx
    #   - Authentification with Jira Sever
    #   - Retrieval of issues matching the query 40 at a time
    #   - Retrieval and storage of detailed information for each of the matching issues
    #
    # Note: At this time, the detailed information for each issues can only be retrieved by
    #       querying each issue individually.  I have not been able to find a way to retrieve
    #       it defferently.
    # <p>
    """
    urlRoot = "https://nsg-jira.intel.com"  # Root url for JIRA api
    # urlRoot = "https://nsg-jira.intel.com/issues/?jql="  # Root url for Atlassian server
    outputFilename = ""
    authString = ""
    addr = urlRoot + "/rest/api/2/search?jql="
    jqlStr = ""
    allIssues = []
    keyAndUpdated = {}
    aJiraIssue = jira_issue()
    aIssuesList = jira_issues_lists()
    aSupportFile = support_file()

    def __init__(self, username=None, password=None, debug=False, defaultPasswordFile: str = None,
                 datakey: str = "None"):
        """

        Args:
            username: username
            password: pw
            debug:
            defaultPasswordFile: credentials.conf
        """

        self.debug = debug
        self.datakey = datakey
        self.authString = None
        self.username = None
        self.password = None

        if defaultPasswordFile is not None:
            self._read_passwordFile(defaultFile=defaultPasswordFile)
        elif (username is not None and password is not None):
            self._username = username
            self._password = password
        else:
            self.jiraLogin()
        return

    def setDatakey(self, name="None"):
        """

        Args:
            name: Name of content (otherwise thought of the label of the data search query

        Returns:

        """
        self.datakey = name
        return

    def sendRestRequest(self, url):
        """
        #
        # Connects to the url and returns raw response
        # Note: Assumes authorization string has already been set by jiraLogin
        #
        # @param url         the entire url and request information
        #
        # @return - the raw response from the server
        #
        """
        request = urllib.request.Request(url)
        request.add_header("Authorization", "Basic %s" % self.authString)
        try:
            response = urllib.request.urlopen(request)
        except urllib.request.HTTPError as e:
            print('The server couldn\'t fulfill the request.')
            print(('Error code: ', e.code))
            print(('URL:', urllib.request.url2pathname(url)))
            sys.exit(0)
        except urllib.request.URLError as e:
            print('We failed to reach a server.')
            print(('Reason: ', e.reason))
            print(('URL:', urllib.request.url2pathname(url)))
            sys.exit(0)
        else:
            # Load the Json reply into dictionary format
            return response.read()

    def setOutputFilename(self, filename, extension='json', mode=1):
        """
        Sets the output filename for the JSON Jira results and renames the current file to the highest
        available archive number

        Args:
            filename: arbitrary name for a file
            extension: file format
            mode: new methods use mode 2, any other value provides original behavior

        Returns:
            the new archive name that replaced the existing one
        """
        archiveNumber = 0
        finishedArcing = 0
        outputFilename = filename
        tmpFilename = filename

        while finishedArcing == 0:
            if mode == 2:
                var = os.path.abspath(os.path.join(os.getcwd(), tmpFilename)) + '.' + extension
                if os.path.isfile(var):
                    tmpFilename = outputFilename + "." + str(archiveNumber)
                    archiveNumber += 1
                else:
                    finishedArcing += 1
                    tmpFilename = var
            else:
                if os.path.isfile(tmpFilename):
                    tmpFilename = outputFilename + "." + str(archiveNumber)
                    archiveNumber += 1
                else:
                    finishedArcing += 1
        #
        # If we detected the file already exists, rename it to the next
        # available archive number.  The places the most recent archive
        # at the highest number
        #
        if archiveNumber > 0:
            # os.rename(outputFilename, tmpFilename) # rmacedo: this is not needed right now
            print(("Output file: " + filename + " exists.  Renaming existing file to: " + tmpFilename))
        self.outputFilename = filename
        return tmpFilename

    def jiraLogin(self):
        """
        #
        # Gathers the login information for Jira.
        # This allows us to filter the results based off of a single scrum team.
        #
        """
        userName = ""
        password = ""

        # Uncomment the user input for User Name if you are not daescamX
        userName = input("user: ")
        password = getpass.getpass(prompt='password: ')
        self._username = str.encode(userName)
        self._username = base64.b64encode(self._username)

        self._password = str.encode(password)
        self._password = base64.b64encode(self._password)
        userNameAndPassword = str.encode(userName + ":" + password)
        # # Construct the authorization string from the username and the password
        self.authString = base64.b64encode(userNameAndPassword)
        return

    def retrieveIssueDetails(self, issueKeyList):
        """
        #
        # Retrieve issues all of the information for each issue in the list passed in
        #
        # @param issueList      Issue to retrieve detailed information from in list form
        #
        # @returns  Returns the received json as a list of strings
        """
        detailIssueList = []
        totalIssues = len(issueKeyList)
        print(("Fetching details of: ", totalIssues, " issues"))

        #
        # Get issue details one at a time
        #
        lineNumber = 0
        for aIssueKey in issueKeyList:
            fullAddr = str(self.urlRoot) + "/rest/api/2/issue/" + str(aIssueKey) + "?expand=changelog,schema"
            # Load the raw reply into list
            detailIssueList.append(self.sendRestRequest(fullAddr))
            lineNumber += 1
            print((" Fetched:", (100 * lineNumber) / totalIssues, "%\r"), end=' ')
        print((" Fetched:", (100 * lineNumber) / totalIssues, "%\r"), end=' ')
        return detailIssueList

    def findMostRecentUpdate(self, updateFilename):
        """
        # Searches through all of the issues to fine the most recent last updated.  Currently will return the beginning of the day of the last update
        #
        # @param updateFilename         The JSON file to compare the query issues against.
        #
        """
        #
        # Read the number of lines in the file
        #
        fileLines = 0
        lineNumber = 0
        lastUpdated = ""
        for line in open("JiraSnapshot.json"):
            fileLines += 1

        #
        # Read the snapshot data and place fields of interest into database and then into a list in memory
        #
        with open("JiraSnapshot.json", "r") as dataStoreFile:
            for aLine in dataStoreFile:
                lineNumber += 1
                if (lineNumber % 107 == 0):
                    print((" Reading snapshot:", (100 * lineNumber) / fileLines, "%\r"), end=' ')
                self.aJiraIssue.parseJson(aLine.decode('latin1').encode('utf8'))
                self.aIssuesList.addIssue(self.aJiraIssue.issueDictionary)
                if (self.aJiraIssue.issueDictionary["updated"] > lastUpdated):
                    lastUpdated = self.aJiraIssue.issueDictionary["updated"]
        if (fileLines):
            print((" Reading snapshot:", (100 * lineNumber) / fileLines, "%\r"), end=' ')
            print(("\nDatabase Issues: ", lineNumber))
        else:
            print('No recent updates exist locally')
        #
        # Truncate it down to date only
        #
        lastUpdated = re.sub(r" .*", "", lastUpdated)
        print(("Last Updated: ", lastUpdated))
        return lastUpdated

    def retrieveIssueList(self, query):
        """
        #
        # Retrieve issues matching the query 40 at a time
        # Populates the dictionary of key and updated with that information
        #
        # @param query         query to use to retrieve issue summaries
        #
        """
        startAt = 0
        maxResults = 40
        totalIssues = 100  # Set a a number above the startAt so that it will execute the loop at least once
        self.keyAndUpdated = {}

        orgQuery = str.encode(query)
        query = urllib.request.pathname2url(orgQuery)
        fullAddr = self.addr + query + "&fields=changelog,updated&expand=changelog"

        print("Retrieving issue list:")
        while (startAt < totalIssues):
            # Load the Json reply into dictionary format
            jResponse = json.loads(
                self.sendRestRequest(fullAddr + "&startAt=" + str(startAt) + "&maxResults=" + str(maxResults)))
            if (startAt == 0):
                #  print jResponse
                print(("Fetching Keys for " + str(jResponse["total"]) + " issues. "))
                print(("Fetching: "), end=' ')
                totalIssues = int(jResponse["total"])
            print((str(jResponse["startAt"]) + " .."), end=' ')
            startAt += 40
            for aIssue in jResponse["issues"]:
                updated = re.sub(r"T", " ", aIssue["fields"]["updated"])
                updated = re.sub(r"\..*", "", updated)
                self.keyAndUpdated[aIssue["key"]] = updated

    def updateSnapshot(self, updateFilename, scrunTeamsToKeep):
        """
        #
        # Compares the updated date of the issues read from jira (in keyAndUpdate) to those in the snapshot (aIssuesList.issueList)
        # Issues are removed from the update list if the snapshot contains ones with the same or more recent date.
        # Each issue remaining in the update list is retrieved and added to the snapshot, with all non-updated issues added afterwards
        #
        # ** WARNING **
        # This function expects the snapshot to already have been read in by findMostRecentUpdate
        #
        # @param updateFilename         The JSON file to compare the query issues against.
        # @param scrunTeamsToKeep       A list of the scrum team issues to keep in the database
        #
        """
        #
        # Determine which issues need to be updated
        #
        lineNumber = 0
        totalIssues = len(self.aIssuesList.issueList)
        for aIssue in self.aIssuesList.issueList:
            lineNumber += 1
            if (lineNumber % 107 == 0):
                print(("\r Comparing to snapshot:", (100 * lineNumber) / totalIssues, "%"), end=' ')
            if (aIssue["key"] in self.keyAndUpdated):
                if (aIssue["updated"] >= self.keyAndUpdated[aIssue["key"]]):
                    #
                    #  Snapshot has the latest, remove from the update list
                    #
                    # print "removing:",aIssue["key"]
                    self.keyAndUpdated.pop(aIssue["key"])
                    # Write to the temp file

        print(("\r Comparing to snapshot:", (100 * lineNumber) / totalIssues, "%"))
        print(("\n Issues needed update: ", len(self.keyAndUpdated)))
        if (len(self.keyAndUpdated) == 0):
            print("\n No update needed. Snapshot Up-To-Date")
            return
        #
        # Get the details of the issues that need to be updated
        #
        keysToGet = []
        for key in self.keyAndUpdated:
            keysToGet.append(key)
        updatedIssuesList = []
        updatedIssuesList = self.retrieveIssueDetails(keysToGet)
        #
        # Rename existing file to an archive number and return the archive filename
        # This is done so that we maintain a copy of the existing file while writing the new one
        #
        archiveFilename = self.setOutputFilename(updateFilename)

        with open(updateFilename, "w") as dataStoreFile:
            #
            # Copy all of the updates to the file
            #
            print("Writing updated issues")
            for aIssue in updatedIssuesList:
                dataStoreFile.write(str(aIssue) + "\n")

            print("Writing updated issues - complete")
            #
            # Everything that was not updated from the archive file to the update file
            #
            lineNumber = 0
            with open(archiveFilename, "r") as archiveFile:
                for aLine in archiveFile:
                    lineNumber += 1
                    if (lineNumber % 107 == 0):
                        print((" Writing non-updated issues to snapshot:", (100 * lineNumber) / totalIssues, "%\r"),
                              end=' ')
                    #
                    # Decode the json to determine if the key matches one we have already written
                    # TO DO - Don't write those that are for scrum teams not of interest
                    #
                    self.aJiraIssue.parseJson(aLine.decode('latin1').encode('utf8'))
                    if (self.aJiraIssue.issueDictionary["key"] not in self.keyAndUpdated):
                        #
                        # Note: We need to keep the ones that are not in the scrum team anymore for at least
                        # one sprint, so that we can report the issues as moved out of team.
                        # A cleanup utility needs to be made to drop older issues and issues out of the team
                        #
                        dataStoreFile.write(str(aLine))
                print((" Writing non-updated issues to snapshot:", (100 * lineNumber) / totalIssues, "%\r",))
        print("\nSnapshot updated. ")
        return

    def _pageExists(self, urlAddress=None):
        """

        Args:
            urlAddress: webpage address in question

        Returns:
            status of existance/accessiblity

        """
        status = False
        try:
            urlAddress = str(urlAddress)
            # User agent for white/blacklist
            USER_AGENT = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
            authed_session = requests.Session()  # Create a Session to contain you basic AUTH, it will also persist your cookies

            authed_session.auth = (self._username, self._password)  # Add credentials

            # WARNING: You should point this to your cert file for the server to actually
            # verify the host. Skips verification if set to false
            CERT_FILE = False
            authed_session.verify = CERT_FILE  # Cert verification, will not verify on false
            authed_session.headers.update({'User-Agent': USER_AGENT})
            try:
                webpageResponse = authed_session.get(url=urlAddress, auth=(self._username, self._password))
            except:
                pass

            if self.debug:
                print(f"Webpage {urlAddress} Status: {webpageResponse.status_code}")

            if webpageResponse.status_code in [200, 201, 202, 203, 204, 205, 206]:
                status = True
            elif webpageResponse.status_code in [300, 301, 303, 304, 305, 307]:
                status = False
            elif webpageResponse.status_code in [400, 401, 404, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416,
                                                 417]:
                status = False
            elif webpageResponse.status_code in [500, 501, 502, 503, 504, 505]:
                status = False
            else:
                status = False

            if self.debug and status is True:
                print('Web site exists')
            elif self.debug and status is False:
                print('Web site does not exist')

        except Exception as ErrorFound:
            print(f"URL exception at {urlAddress}! Error is {ErrorFound}")

        return status

    def _read_passwordFile(self, defaultFile=".raadProfile/credentials.conf"):
        """

        Args:
            defaultFile: file containing newline separated credentials

        Returns:

        """
        defaultPasswordFile = os.path.abspath(os.path.join(os.getcwd(), defaultFile))
        if os.path.isfile(defaultPasswordFile):
            with open(defaultPasswordFile) as openFile:
                fileMeta = openFile.read()
                INFO = fileMeta.split('\n')  # Separator is \n
                self._username = base64.b64encode(str.encode(INFO[0]))
                self._password = base64.b64encode(str.encode(INFO[1]))
        return

    @staticmethod
    def writeFile(data, fileformat, filepath):
        if str.lower(fileformat) == 'json':
            # write in json
            with open(filepath, "w") as outfile:
                outfile.write(json.dumps(data, indent=4))
                print("Writing updated issues - complete")
        else:
            # write in text
            pass
        return

    def atlassianJira(self, query: str = None):
        """

        Description: Issues query for JIRAs based on query parameter

        Args:
            query: Formulated query string using JQL, then passed to the Jira urlRoot

        Returns: json response containing raw data matching the query

        """
        # Create a Session to contain your basic AUTH, it will also persist your cookies
        USER_AGENT = \
            "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
        authed_session = requests.Session()
        authed_session.headers.update({'User-Agent': USER_AGENT})

        # WARNING: You should point this to your cert file for the server to actually
        # verify the host. Skips verification if set to false
        # With setup from above, things are okay if it's set to false
        CERT_FILE = False
        authed_session.verify = CERT_FILE  # Cert verification, will not verify on false
        returnData = None

        # Create atlassian Jira instance (atlassian python api)
        # Decode username and password
        jira = Jira(
            url='https://nsg-jira.intel.com',
            username=(base64.b64decode(self._username)).decode('utf-8'),
            password=(base64.b64decode(self._password)).decode('utf-8'),
            verify_ssl=False,
            session=authed_session
        )

        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        except:
            urllib3.disable_warnings()
            pass

        if self.debug or query is None:
            JQL = 'reporter = currentUser() order by created DESC'
            returnData = jira.jql(JQL)
        else:
            # Perform query using atlassian python api
            maxResults = 1000
            returnData = jira.jql(jql=query, limit=maxResults)

        del jira
        return returnData

    @staticmethod
    def flattenJson(jsoninput=None, jsonoutput: str = None):
        """

        Description: flatten json input file

        Args:
            jsoninput: input for flattening
            jsonoutput: flattened output

        """
        # Required imports from main
        mainfile = os.path.dirname(r'src/main.py')
        sys.path.append(mainfile)
        from main import findAll
        findAll(
            fileType=".py",
            directoryTreeRootNode=mainfile,
            debug=False,
            doIt=True,
            verbose=False
        )
        from genericObjects import ObjectUtility

        # read json into dict
        with open(jsoninput) as jf:
            jj = json.load(jf)

        # flatten dict
        data = ObjectUtility.simpleFlatten(objNotFlat=jj, sep='.')

        with open(jsonoutput, 'w') as fjson:
            json.dump(data, fjson, indent=4)

        return

    @staticmethod
    def removeNullFields(filename, outfile='data/jiraData/removeNull/removeNull'):
        """

        Args:
            filename: filename of flat json object
            outfile: ouptut file name

        """
        with open(filename, 'r') as f:
            jdata = json.load(f)
        res = dict([(key, val) for key, val in jdata.items() if val is not None])
        with open(outfile, 'w') as of:
            json.dump(res, of, indent=4)
        return

    @staticmethod
    def createCSVFromJson(ifile='data/output/jiraDataStore/removeNUll/removeNullASSERT_DE003.json',
                          # 'data/jiraData/df049_Full_removeNull.json'
                          ofile='data/output/jiraDataStore/csv/jsonToCsv.csv',
                          fieldsFile='./data/jiraUtilMeta/fieldsMapping.csv',
                          unwanted: set = None):
        """

        Args:
            ifile: input FLAT json file
            ofile: output name
            fieldsFile: name of file containing desired newline separted JIRA fields, which are used as columns
            unwanted: set of unwanted features (i.e. noise)

        Returns:
            - When creating csv, need to get dictionary per complex field, then handle the dictionary comparison when
            doing sentance tokenization for word-embedding matrix generation

        """

        jiras = nestedDict.flat2NestedDict(datafile=ifile)
        jiras.parseInput()
        fieldFile = os.path.abspath(os.path.join(os.getcwd(), fieldsFile))
        fieldMapping = dict()
        customFieldDF = pd.read_csv(fieldFile)

        for i in range(customFieldDF['name'].size):
            key = customFieldDF.iloc[i][1]
            value = str(customFieldDF.iloc[i][2])
            fieldMapping[key] = value

        root = jiras.getTree()['issues']
        csvOut = {'expand': [], 'id': [], 'self': [], 'key': []}

        keyset = set()
        keyIndices = root.keys()

        for i in keyIndices:
            for j in root[i]['fields'].keys():
                keyset.add(str(j))

        for i in fieldMapping.keys():
            keyset.add(i)

        for i in keyset:
            csvOut[i] = list()

        accountedFor = {'expand', 'id', 'self', 'key'}
        for i in keyIndices:
            csvOut['expand'].append(root[i]['expand'])
            csvOut['id'].append(root[i]['id'])
            csvOut['self'].append(root[i]['self'])
            csvOut['key'].append(root[i]['key'])
            for field in (keyset - accountedFor):
                try:
                    value = root[i]['fields'][field]
                except KeyError:
                    value = 'none'
                csvOut[field].append(value)
        csvOut_sorted = sorted(csvOut.keys())  # @todo: update for reference
        fieldMapping_sorted = sorted(fieldMapping.keys())  # @todo: update for reference
        final = dict()
        for k, v in csvOut.items():
            if re.search('^customfield_', k) is not None:
                if k in fieldMapping.keys():
                    print('In fieldMapping')
                    final[fieldMapping[k]] = csvOut[k]
                else:
                    print('Outside of scope')  # @todo: how to deal with new customfield?
                    pass
            else:
                final[k] = csvOut[k]

        finalkeys = list(final.keys())
        length = len(final['key'])
        for k in finalkeys:
            if final[k].count('none') == length or k in unwanted:
                del final[k]
            else:
                pass

        outData = pd.DataFrame.from_dict(final)
        outData.to_csv(ofile, encoding='utf-8', index=False)
        return

    def jiraCollect(self, queryStr: str = None,
                    rawDataPath: str = 'data/output/jiraDataStore/raw',
                    flatDataPath: str = 'data/output/jiraDataStore/flat',
                    nullRemovedPath: str = 'data/output/jiraDataStore/removeNull',
                    csvPath: str = 'data/output/jiraDataStore/csv',
                    noiseTextPath: str = './data/jiraUtilMeta'):
        """

        Description: Issue a JQL query and perform all preprocessing

        Args:
            noiseTextPath: location of utility data used to reference which Jira fields are considered noise
            csvPath: location of where csv datasets will be stored
            nullRemovedPath: location of where intermediate null-removed datasets will be stored
            flatDataPath: location of where intermediate flattened datasets will be stored
            rawDataPath: location of raw crawled json data
            queryStr: String of text to pass as query for Jira searching

        """

        rawDataPath = tryFolder(path=rawDataPath)
        rawDataPath = os.path.join(rawDataPath, 'rawJsonData')

        flatDataPath = tryFolder(path=flatDataPath)
        flatDataPath = os.path.join(flatDataPath, 'flatIssues')

        nullRemovedPath = tryFolder(path=nullRemovedPath)
        nullRemovedPath = os.path.join(nullRemovedPath, 'removeNull')

        csvPath = tryFolder(path=csvPath)
        csvPath = os.path.join(csvPath, 'jsonToCsv')

        noiseTextPath = tryFolder(path=noiseTextPath)
        noiseTextFile = os.path.join(noiseTextPath, 'jiraNoiseFields.json')
        fieldsFile = os.path.join(noiseTextPath, 'fieldsMapping.csv')

        # utilize noise file
        with open(noiseTextFile) as f:
            noiseFile = json.load(f)

        # Issue query
        data = self.atlassianJira(query=queryStr)
        rawfile = self.setOutputFilename(filename=rawDataPath + self.datakey, extension='json', mode=2)
        self.writeFile(
            data=data,
            fileformat='json',
            filepath=rawfile
        )

        # Remove user credentials
        del self._username
        del self._password

        # flatten
        flatfile = self.setOutputFilename(filename=flatDataPath + self.datakey, extension='json', mode=2)
        self.flattenJson(
            jsoninput=rawfile,
            jsonoutput=flatfile
        )

        # remove null
        removefile = self.setOutputFilename(filename=nullRemovedPath + self.datakey, extension='json', mode=2)
        self.removeNullFields(
            filename=flatfile,
            outfile=removefile
        )

        # output csv
        csvfile = self.setOutputFilename(filename=csvPath + self.datakey, extension='csv', mode=2)
        self.createCSVFromJson(
            ifile=removefile,
            ofile=csvfile,
            fieldsFile=fieldsFile,
            unwanted=set(noiseFile['noiseKeys'])
        )
        return data['total']


def queryJira(_getJiraIssues, qry):
    """

    Args:
        _getJiraIssues: classGetJiraIssues object
        qry: query string

    Returns:

    """
    if _getJiraIssues.debug:
        if _getJiraIssues._pageExists(urlAddress=_getJiraIssues.urlRoot):
            print('page exists')
    data1 = _getJiraIssues.atlassianJira(query=qry)
    _getJiraIssues.writeFile(data=data1, fileformat='json')
    return


def main():
    ##############################################
    # Main function, Options
    ##############################################
    parser = argparse.ArgumentParser(description="Query JIRAs using REST API Wrappers")
    parser.add_argument("-d", "--debug", action='store_true', dest='debug', default=False, help='Debug mode')
    parser.add_argument("-j", "--jql", help="Issues JQL query. Requires one arg: (1) query",
                        nargs=1)

    parser.add_argument("-e", "--exists",
                        help="Reads and flattens existing json search results. Requires one arg: (1) input json file",
                        nargs=1)

    parser.add_argument("-n", "--discardnull", nargs=1,
                        help='Discard Null Fields. Requries two args: (1) input filename, (2) output filename')

    parser.add_argument("-c", "--csv",
                        help="Converts JSON to csv, Requries two args: (1) input filename, (2) fields filename",
                        nargs=2)

    parser.add_argument("-a", "--all",
                        help="Single command to query for Jiras, flatten, remove null,"
                             " and output csv. Requires queries.txt as argument",
                        nargs=1)

    parser.add_argument("-k", "--datakey", help="Identifier for context of query data", nargs=1)

    args = parser.parse_args()
    print("Output args:")
    pprint.pprint(args)
    ##############################################
    # Main
    ##############################################
    getJiraIssues = get_jira_issues(defaultPasswordFile='.raadProfile/credentials.conf')
    if args.datakey is not None and len(args.datakey) == 1:
        getJiraIssues.setDatakey(name=args.datakey[0])
    if args.jql is not None and len(args.jql) == 1:
        queryJira(_getJiraIssues=getJiraIssues, qry=args.jql[0])
    elif args.exists is not None and len(args.exists) == 1:
        getJiraIssues.flattenJson(jsoninput=args.exists[0])
    elif args.discardnull is not None and len(args.discardnull) == 1:
        getJiraIssues.removeNullFields(filename=args.discardnull[0])
    elif args.csv is not None and len(args.csv) == 2:
        getJiraIssues.createCSVFromJson(ifile=args.csv[0], fieldsFile=args.csv[1])
    elif args.all is not None and len(args.all) == 1:
        getJiraIssues.jiraCollect(queryStr=args.all[0])
    else:
        # For testing the below performs a updateSnapshot type function
        jqlStr = "("
        # Add updated since
        jqlStr += "(updated >= \"" + str(getJiraIssues.findMostRecentUpdate("JiraSnapshot.json")) + "\") and "
        # Get an entire program
        jqlStr += "(project = NSGSE) and "
        # Add issue types
        jqlStr += "issuetype in (Story, \"Development Task\", Sighting, HGST_Sighting) )"
        getJiraIssues = get_jira_issues()
        getJiraIssues.retrieveIssueList(jqlStr)
        getJiraIssues.updateSnapshot("JiraSnapshot.json", "scrunTeamsToKeep")


if __name__ == '__main__':
    """Performs execution delta of the process."""
    pStart = datetime.datetime.now()
    try:
        main()
    except Exception as errorMain:
        print("Fail End Process: {0}".format(errorMain))
        traceback.print_exc()
    qStop = datetime.datetime.now()
    print("Execution time: " + str(qStop - pStart))

#
#
#  /**
#   * removeDups
#   *
#   * Dups have found thier way into the snapshot.  This will remove them.
#   *
#   * @param updateFilename         The JSON file to compare the query issues against.
#   * @param scrunTeamsToKeep       A list of the scrum team issues to keep in the database
#   *
#   */
#  public void removeDups(updateFilename) {
#    def aJiraIssue = new jira_issue()
#    def aIssuesList = new jira_issues_lists()
#    def dataStoreFile = new File(updateFilename)
#    def tmpDataStoreFile = new File("tmpDataStore.json").delete()
#    def loopCount = 0
#    def lastIssue = ["",""]
#    def dupList = []
#    def theDups = []
#
#    tmpDataStoreFile = new File("tmpDataStore.json")
#    println "\nComparing to Database Snapshot "
#    dataStoreFile.eachLine { dataLine ->
#      aJiraIssue.parseJson(dataLine)
#      // Progress tick
#      if((loopCount % 12) == 0) {
#        print " "+loopCount+"\r"
#      }
#      aIssuesList.addIssue(aJiraIssue)
#      loopCount++
#    }
#    // Sort by key
#    aIssuesList.IssuesList = aIssuesList.IssuesList.sort{ a,b -> a[1].toString() <=> b[1].toString() }
#    aIssuesList.IssuesList.each() { aIssue ->
#      println aIssue[1]
#      if(lastIssue[1] == aIssue[1]) {
#        if(aIssue[1] in dupList) {
#          // Do nothing
#        } else {
#          dupList.add(aIssue[1])
#        }
#      }
#      lastIssue = aIssue
#    }
#
#    println "Dup list:"+dupList
#    // Note: this funciton is incomplete.  It simply lists the dups at this time.
# //  def fields = ["Type":0, "Key":1, "Summary":2, "Priority":3, "Status":4, "Program":5, "Program Size":6, "Scrum Team":7, "Dev Owner":8, "Val Owner":9, "Submitter Org":10, "Date New":11, "Date from In-Progress":12, "Date from FPV":13, "Last Updated":14, "Story Points":15, "Date to Close":16, "Date to FPV":17]
#  }
#
#

#  /**
#   * Modify the fixVersion field
#   *
#   * @param key         Jira issue key to act on
#   * @param action      Verb action to perform: "Set" - replace all existing with new value , "Add" - Add to existing, "Remove" - Remove a value
#   * @param versionName The version name string
#   *
#   * @see   https://developer.atlassian.com/display/JIRADEV/Updating+an+Issue+via+the+JIRA+REST+APIs
#   *
#   */
#  public void modFixVersion(key, action, versionName) {
#    String toWriteOut = "{ \"update\" : { \"fixVersions\" : [{\""+action+"\" : {\"name\": \""+versionName+"\"}}] } }"
#
#    addr = "${this.urlRoot}/rest/api/2/issue/"+key
#    def HttpURLConnection connw = null;
#    connw = addr.toURL().openConnection()
#    connw.doOutput = true
#    connw.setRequestProperty("Content-Type", "application/json");
#    connw.setRequestProperty("Accept", "application/json");
#    connw.setRequestMethod("PUT")
#    // If a authorization string has been provided use it.
#    if(authString.length() > 0) {
#      connw.setRequestProperty( "Authorization", "Basic ${authString}")
#    }
#    connw.connect();
#    OutputStreamWriter osw = new OutputStreamWriter(connw.getOutputStream());
#    osw.write(toWriteOut);
#    osw.close();
#
#    // Based on the response to the authorization, either continue or fail out
#    if( connw.responseCode == 204 ) { // All is good, continue (according to spec "204: No Content" is return on success  - Note: on 'removes' success is returned regardless of object found to remove
#      println "FixVersion - "+key+" - "+action+" - "+versionName+" - Success."
#
#    } else {  // All is not well with the authorization, display the resposne code
#      println "FixVersion - "+key+" - "+action+" - "+versionName
#      println "Something bad happened."
#      println "${connw.responseCode}: ${connw.responseMessage}"
#      println "=============================="
#      println "${connw}"
#      System.exit(0);
#    }
#  }
# }
#
# System.exit(0);
