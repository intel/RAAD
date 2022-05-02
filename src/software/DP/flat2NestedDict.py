#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Rogelio Macedo, Joseph Tarango
# *****************************************************************************/

import json, os, sys, re, datetime, pprint
import traceback
from getpass import getpass

# from blist import sorteddict
import unittest
import requests
import urllib3
import pandas as pd


class flat2NestedDict(object):
    """
    Description:
        * Data structure of embedded dict of keys and their values
        * Values are at the leaves, keys are the internal nodes
        * There is only a single root node
        * keys are sorted at each level of the tree
    """

    rootNode = None
    inputData = None
    keySet = None

    def __init__(self, datafile="data/jiraData/testInput.json"):
        """
        Description: Class Constructor

        Args:
            datafile: filename of flat dictionary to nest
        """
        keySet = set()
        self.rootNode = {}

        # Read input data
        inputPath = os.path.abspath(os.path.join(os.getcwd(), datafile))
        with open(inputPath) as ip:
            self.inputData = json.load(ip)
        return

    def parseInput(self):

        if self.inputData is None:
            return -1

        dictItems = self.inputData.items()
        for key, value in dictItems:
            keySplit = [str(i) for i in key.split('.')]

            if len(keySplit) == 1:
                self.rootNode[keySplit[0]] = value

            else:
                keyPath = []
                for innerNode in keySplit:
                    try:
                        number = int(innerNode)
                        keyPath.append(number)
                    except ValueError:
                        keyPath.append(innerNode)

                level = 0
                alias = self.rootNode
                for innerNode in keySplit:
                    try:
                        if innerNode in alias:
                            alias = alias[innerNode]
                        elif level == len(keyPath) - 1:
                            alias[innerNode] = str(value)
                        else:
                            alias[innerNode] = dict()
                            alias = alias[innerNode]
                    except TypeError:
                        print(innerNode)
                    level += 1
        return

    def getTree(self):
        return self.rootNode


def main():
    ##############################################
    # Main function, Options
    ##############################################

    # None

    ##############################################
    # Main
    ##############################################
    # btree = flat2NestedDict()
    # btree.parseInput()
    # print('done')
    inFields = os.path.abspath(os.path.join(os.getcwd(), "data/jiraData/fieldsInfo.json"))
    with open(inFields, 'r') as infile:
        fieldsDict = json.load(infile)
    print('yes')
    out = {"id": [], "name": [], "type": []}
    for obj in fieldsDict:
        out["id"].append(obj['id'])
        out["name"].append(obj["name"])
        try:
            out["type"].append(obj["schema"]["type"])
        except KeyError:
            out["type"].append('string')
    finalOfile = os.path.abspath(os.path.join(os.getcwd(), "data/jiraData/fieldsMapping.csv"))
    outData = pd.DataFrame.from_dict(out)
    outData.to_csv(finalOfile, encoding='utf-8')


class TestTreeGen(unittest.TestCase):

    def test_buildTree(self):
        stringDict = ('{"expand": "schema,names","startAt": 0,"maxResults": 1000,"total": 393,"issues": '
                      '{"0":{"expand": "operations,versionedRepresentations,editmeta,changelog,renderedFields",'
                      '"id": "408697","self": "https://nsg-jira.intel.com/rest/api/2/issue/408697",'
                      '"key": "NSGSE-104871","fields":{"customfield_21521": "None","customfield_19322": '
                      '{"self": "https://nsg-jira.intel.com/rest/api/2/customFieldOption/32854",'
                      '"value": "Born on Trunk"}}}}}')

        """
        {
            "expand": "schema,names",
            "startAt": 0,
            "maxResults": 1000,
            "total": 393,
            "issues": {
                "0":
                {
                    "expand": "operations,versionedRepresentations,editmeta,changelog,renderedFields",
                    "id": "408697",
                    "self": "https://nsg-jira.intel.com/rest/api/2/issue/408697",
                    "key": "NSGSE-104871",
                    "fields":
                    {
                        "customfield_19322": {
                            "self": "https://nsg-jira.intel.com/rest/api/2/customFieldOption/32854",
                            "value": "Born on Trunk"
                        }
                    }
                }
            }
        }
        """
        # Goal is to generate this (above) from this (below)
        """
        {
            "expand": "schema,names",
            "startAt": 0,
            "maxResults": 1000,
            "total": 393,
            "issues.0.expand": "operations,versionedRepresentations,editmeta,changelog,renderedFields",
            "issues.0.id": "408697",
            "issues.0.self": "https://nsg-jira.intel.com/rest/api/2/issue/408697",
            "issues.0.key": "NSGSE-104871",
            "issues.0.fields.customfield_21521": null,
            "issues.0.fields.customfield_19322.self": "https://nsg-jira.intel.com/rest/api/2/customFieldOption/32854",
            "issues.0.fields.customfield_19322.value": "Born on Trunk"
        }
        """

        treeToMatch = json.loads(stringDict)
        btree = flat2NestedDict(datafile='data/jiraData/unitTestInput.json')
        btree.parseInput()
        thisDataStruct = btree.getTree()

        # uncomment for visuals
        # pprint.pprint(thisDataStruct)
        # print("above: btree ... below: tree to match:")
        # pprint.pprint(treeToMatch)

        self.assertDictEqual(thisDataStruct, treeToMatch)


if __name__ == '__main__':
    """Performs execution delta of the process."""
    pStart = datetime.datetime.now()
    try:
        main()
        # unittest.main()
    except Exception as errorMain:
        print("Fail End Process: {0}".format(errorMain))
        traceback.print_exc()
    qStop = datetime.datetime.now()
    print("Execution time: " + str(qStop - pStart))
