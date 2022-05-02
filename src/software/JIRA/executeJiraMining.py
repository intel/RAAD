#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Rogelio Macedo, Joseph Tarango
# *****************************************************************************/

import os, datetime, pprint
# import pickle, sys
import traceback
from jiraEmbedding import jiraEmbedding
from src.software.utilsCommon import tryFolder
from classGetJiraIssues import get_jira_issues
from jiraSimAnalysis import jiraSimAnalysis
from src.software.utilsCommon import tryFile
import re
from src.software.debug import whoami


# BADASSERTTAGS = {'df0049': 'df049'}


def cleanSearchString(searchString: str = None):
    """

    Args:
        searchString: Assert signature which may potentially contain other noise

    Returns: Assert signature string which begins with "ASSERT_"

    """
    final = ''
    s2 = re.sub(r'[^\w\s]', '', searchString)
    s2 = s2.split(' ')
    for string in s2:
        try:
            mat = re.search('^ASSERT.*', string).group(0)
            if mat.find('ASSERT') != -1:
                final = mat
                break
        except:
            final = 'ASSERT_DE003'  # final = 'ASSERT_DF049'
            pass
    return final


class executeJiraMining(object):
    """

    Class-member variables
        datakey: the name of the assert to querying Jiras
        searchkey: actual string to query which uses datakey as base
        getJiras: reference to classGetJiraIssues
        outputDir: name of output directory storing Jira data extraced/computed
        outputDirPath: path of outputDir
        rawDataDir: directory storing raw crawled data
        flatDataDir: directory storing flattened data
        nullRemovedDir: directory storing null-removed data
        csvDir: directory storing data as csv
        embeddingDir: directory storing embedding matrix csv
        labels: reference to list of labels

    """

    def __init__(self, datakey: str = None):
        """

        Args:
            datakey: Assert signature query for Jira collection/analysis

        """
        self.datakey = cleanSearchString(searchString=datakey)
        self.searchkey = str.lower(self.datakey.replace('ASSERT_', ''))

        # if self.searchkey in BADASSERTTAGS:
        #    self.searchkey = BADASSERTTAGS[self.searchkey]
        self.searchkey = re.findall(r'([a-z]{2}).*([\d]{3}$)', self.searchkey)[0][0] + \
                         re.findall(r'([a-z]{2}).*([\d]{3}$)', self.searchkey)[0][1]

        self.getJiras = None
        self.outputDir = 'jiraDataStore'
        self.outputDirPath = tryFolder(path='data/output')
        if self.outputDirPath is None:
            self.outputDirPath = os.path.abspath("../data/output")
        self.outputDirPath = os.path.join(self.outputDirPath, self.outputDir)
        self.rawDataDir = os.path.join(self.outputDirPath, 'raw')
        self.flatDataDir = os.path.join(self.outputDirPath, 'flat')
        self.nullRemovedDir = os.path.join(self.outputDirPath, 'removeNull')
        self.csvDir = os.path.join(self.outputDirPath, 'csv')
        self.embeddingDir = os.path.join(self.outputDirPath, 'embedded')
        self.labels = None

        if not os.path.isdir(self.outputDirPath):
            os.mkdir(path=self.outputDirPath)

        if not os.path.isdir(self.rawDataDir):
            os.mkdir(path=self.rawDataDir)

        if not os.path.isdir(self.flatDataDir):
            os.mkdir(path=self.flatDataDir)

        if not os.path.isdir(self.nullRemovedDir):
            os.mkdir(path=self.nullRemovedDir)

        if not os.path.isdir(self.csvDir):
            os.mkdir(path=self.csvDir)

        if not os.path.isdir(self.embeddingDir):
            os.mkdir(path=self.embeddingDir)
        return

    def createDataStore(self, credFile: str = None):
        """

        Args:
            credFile: path to hidden credentials file

        Returns:

        """
        if self.getJiras is None:
            self.getJiras = get_jira_issues(datakey=self.datakey, defaultPasswordFile=credFile)

        total = None
        try:
            total = self.getJiras.jiraCollect(queryStr='text ~ \"' + self.searchkey + '\"')
        except (OSError, KeyError, Exception) as e:
            print(
                f'Exception {e} occured during execution of Jira Mining::Phase1 DataStore{os.linesep}{pprint.pformat(whoami())}')
            # @todo rmace001: check for http error in exception string and if found, check if cached csv exists
            #                 then check return a bool or something of that nature and ensure the rest of the mining
            #                 process uses the cached csv
            pass

        return total

    def embedJira(self, csvInput: str = None, unwantedNoiseJsonFile: str = None, embeddingFunction='bert',
                  potentialLabels: str = None):
        """

        Args:
            csvInput: desired csv dataset to utilize
            unwantedNoiseJsonFile: desired noise dataset to utilize for noise detection/removal
            embeddingFunction: desired embedding to utilize
            potentialLabels: associated set of known causes for the assert signature which was used to query Jiras

        Returns:
            embedding:  embedding matrix of jiras,
            labeledSet: list of assigned labels based on similarity comparison between known cause embedding vectors

        """
        embedding = None
        labeledSet = None
        jEmbed = None
        try:
            if csvInput is None:
                # get latest csv in csv folder
                files = sorted(os.listdir(path=self.outputDirPath + '/csv'))
                csvInput = files[-2] if len(files) > 1 else files[0]
                jEmbed = jiraEmbedding(csvInputFile=self.outputDirPath + '/csv/' + csvInput)
        except (OSError, IndexError, Exception) as e:
            print(
                f'Exception {e} occured during execution of embedding generation... Trying cached data...{os.linesep}{pprint.pformat(whoami())}')
            if csvInput is None:
                csvInput = tryFile(fileName='../data/jiraUtilMeta/csv/jsonToCsvDE003.csv')  # @todo HARD CODE # '../data/jiraUtilMeta/csv/jsonToCsvDF049.csv'
                jEmbed = jiraEmbedding(csvInputFile=csvInput)
                print(f'Using cached datafile: {csvInput}')
        print(f'Creating embeddings for: {csvInput}')

        if embeddingFunction.lower() == 'tfidf' or embeddingFunction.lower() == 'tf-idf':
            embedding = jEmbed.tfidfVectorization(outputName=self.embeddingDir + '/tfidfTermDocumentMatrix.csv',
                                                  writeData=False)
        elif embeddingFunction.lower() == 'bert' or embeddingFunction == 'sentancebert':
            embedding, labeledSet = jEmbed.bertEmbedJira(labels=potentialLabels)
        else:
            embedding, labeledSet = self.embedJira(csvInput=csvInput, unwantedNoiseJsonFile=unwantedNoiseJsonFile, embeddingFunction=embeddingFunction)
        return embedding, labeledSet

    def analyzeJira(self,
                    embeddedFile: str = None,
                    csvInput: str = None,
                    outputFile: str = 'data/output/jiraDataStore/nearestNeighbors.csv',
                    embeddingType: str = None,
                    embeddingData=None,
                    labeledDataset=None):
        """

        Args:
            embeddedFile:   path to embedding file
            csvInput:       path to csv input file
            outputFile:     path to nearest neighbor file which will be created
            embeddingType:  choice for embedding
            embeddingData:  embedding matrix data structure to use instead of reading in file
            labeledDataset: list of assigned labels based on similarity comparison between known cause embedding vectors

        Returns:
               finalTables: dict  = known-cause-indexed tables of jiras and their 3-nearest neigbors,
               tableHeaders: dict = key: encoded label number, value = known cause sentence with % of contained data

        """
        jiraSims = None
        outputFile = tryFile(fileName=outputFile)
        if outputFile is None:
            outputFile = tryFile(fileName='data/jiraUtilMeta/csv/nearestNeighbors.csv', walkUpLimit=5)

        if embeddingData is None:
            if embeddedFile is None:
                # embeddedFile = latest csv in embedded folder
                files = sorted(os.listdir(path=self.outputDirPath + '/embedded'))
                embeddedFile = files[-2] if len(files) > 1 else files[0]

        try:
            if csvInput is None:
                # csvInput = latest csv in csv folder
                files = sorted(os.listdir(path=self.outputDirPath + '/csv'))
                csvInput = files[-2] if len(files) > 1 else files[0]
                jiraSims = jiraSimAnalysis(embeddingData=embeddingData,
                                           fullDataFile=self.outputDirPath + '/csv/' + csvInput,
                                           embeddingType=embeddingType)
        except (OSError, IndexError, Exception) as e:
            print(
                f'Exception {e} occured during execution of similarity analysis.{os.linesep}{pprint.pformat(whoami())}')
            if csvInput is None:
                csvInput = tryFile(fileName='data/jiraUtilMeta/csv/jsonToCsvDE003.csv',
                                   walkUpLimit=5)  # '../data/jiraUtilMeta/csv/jsonToCsvDF049.csv'
                print(f'Using cached datafile: {csvInput}')
                jiraSims = jiraSimAnalysis(embeddingData=embeddingData,
                                           fullDataFile=csvInput,
                                           embeddingType=embeddingType)

        # need to transform the shape of the dataset via embedding concatenation
        if not jiraSims.reshape3Dto2D():
            print('Error reshaping 3D data matrix into 2D in executeJiraMining::analyzeJira()')
            return None, None
        success, nearNeigborsDF = jiraSims.cosineSimilarityKNN(need2read=False, outputFile=outputFile, dimReduce='SVD')
        groupedIndices, mapping = jiraSims.gaussianMixClusters(assertLabels=self.labels, labeledDataset=labeledDataset,
                                                               dimReduce='SVD')
        groupedIndices = {k: v for k, v in sorted(groupedIndices.items(), key=lambda elem: len(elem[1]), reverse=True)}
        jiraSims.kMeansClustering(assertLabels=mapping)

        tableHeaders = dict()
        for k in groupedIndices.keys():
            v = float(len(groupedIndices[k]) / nearNeigborsDF.shape[0])
            tableHeaders[
                k] = f'Speculated Known Cause: {mapping[k]}, {round(v * 100, 3)}% of {len(embeddingData)} mined Jiras'

        # get only top 25%
        probLists = dict()
        for k, v in groupedIndices.items():
            probLists[k] = list()
            lastIndex = int(len(v) * .25)
            i = 0
            for key, item in v.items():
                if i < lastIndex:
                    probLists[k].append((key, item))
                    i += 1
                else:
                    break

        nnNestedList = nearNeigborsDF.values.tolist()
        for i in range(len(nnNestedList)):
            nnNestedList[i] = [nearNeigborsDF.index[i]] + nnNestedList[i]

        finalTables = dict()
        for k, v in probLists.items():
            finalTables[k] = list()
            for item in v:
                finalTables[k].append(nnNestedList[item[0]] + [item[1]])

        del mapping
        del nearNeigborsDF
        del groupedIndices
        del jiraSims
        del labeledDataset
        del nnNestedList

        return finalTables, tableHeaders

    def presentNearestNeighborsSetAndContext(
            self,
            embeddedFile: str = None,
            realDataFile: str = None,
            inputFile: str = 'data/output/jiraDataStore/nearestNeighbors.csv',
            outputFile: str = 'data/output/jiraDataStore/nearestNeighborContext.csv',
            need2write: bool = False,
            embeddingData=None
    ):
        inputFile = tryFile(fileName=inputFile)
        outputFile = tryFile(fileName=outputFile)

        if embeddingData is None:
            if embeddedFile is None:
                # embeddedFile = latest csv in csv folder
                files = sorted(os.listdir(path=self.outputDirPath + '/embedded'))
                embeddedFile = files[-2] if len(files) > 1 else files[0]

        if realDataFile is None:
            # realDataFile = latest csv in csv folder
            files = sorted(os.listdir(path=self.outputDirPath + '/csv'))
            realDataFile = files[-2] if len(files) > 1 else files[0]

        jiraSims = jiraSimAnalysis(embeddingData=embeddingData,
                                   fullDataFile=self.outputDirPath + '/csv/' + realDataFile)
        filename = os.path.abspath(os.path.join(os.getcwd(), inputFile))
        lines = (line for line in open(filename))
        topJiras = (s.rstrip().split(',') for s in lines)
        cols = next(topJiras)
        success, snippets = jiraSims.snippetExtraction(fullDataFile=self.outputDirPath + '/csv/' + realDataFile,
                                                       kNNSet=topJiras, outputFile=outputFile, need2write=need2write)
        return snippets

    def executeAllJobs(self, embeddingType: str = None, knownCauses: list = None, credFile: str = None):
        """

        Args:
            embeddingType: option for choosing which embedding transformation type: ['tfidf' | 'bert']
            knownCauses: list of strings of known-causes set wrt the assert signature
            credFile: path to .raadProfile/credentials.conf

        Returns:
            upon success: (True,
                           finalTables: dict  = known-cause-indexed tables of jiras and their 3-nearest neigbors,
                           tableHeaders: dict = key: encoded label number, value = known cause sentence with % of contained data)
            otherwise:
                          (False, None, None)

        """
        if knownCauses is not None:
            self.labels = knownCauses
        if tryFile(fileName=credFile) is None:
            print(".raadProfile/credintials.conf not found")

        if self.datakey is None:
            self.datakey = input('Please provide a datakey for the jiras to mine: ')

            self.datakey = cleanSearchString(searchString=self.datakey)
            self.searchkey = str.lower(self.datakey.replace('ASSERT_', ''))

        print('Phase 1: Data Gathering and Preprocessing')
        try:
            total = self.createDataStore(credFile=credFile)
            if total is not None:
                print(f'\tCompleted data collection and preprocessing. Total {self.datakey} JIRAs collected: {total}\n')
            else:
                print('Could not complete querying of Jiras')
            # pass
        except (OSError, KeyError, Exception) as e:
            print(
                f'Exception {e} occured during execution of Jira Mining::Phase1 executeAllJobs{os.linesep}{pprint.pformat(whoami())}')
            return False, None, None

        try:
            print('Phase 2: Embedding Generation')
            embedding, labeledSet = self.embedJira(embeddingFunction=embeddingType, potentialLabels=knownCauses)

            # for debugging: ###################
            # pickle.dump(embedding, open('EmbeddedBertJiras.p', 'wb'))
            # pickle.dump(labeledSet, open('labeledSet.p', 'wb'))
            # embedding = pickle.load(open('EmbeddedBertJiras.p', 'rb'))
            # labeledSet = pickle.load(open('labeledSet.p', 'rb'))
            # end for debugging: ###############

            print(f'\tCompleted embedding phase using {embeddingType} vectorization\n')
        except (OSError, KeyError, Exception) as e:
            print(
                f'Exception {e} occured during execution of Jira Mining::Phase2{os.linesep}{pprint.pformat(whoami())}')
            return False, None, None

        try:
            print('Phase 3: Data Learning, Simimilarity Analysis, and Clustering Visualization\n')
            finalTables, tableHeaders = self.analyzeJira(embeddingType=embeddingType,  # @todo ensure file is created!
                                                         embeddingData=embedding,
                                                         labeledDataset=labeledSet)
            # snippets = self.presentNearestNeighborsSetAndContext(need2write=False, embeddingData=embedding)
        except (OSError, KeyError, Exception) as e:
            print(
                f'Exception {e} occured during execution of Jira Mining::Phase3{os.linesep}{pprint.pformat(whoami())}')
            return False, None, None
        return True, finalTables, tableHeaders


def main():
    ##############################################
    # Main function, Options
    ##############################################

    # None

    ##############################################
    # Main
    ##############################################
    print('Welcome')
    testLabels = [
        'Fast L2P context saves',
        'Low effective spare',  # this means slow defect growth overtime
        'High BDR rates',
        'High read disturb events',
        'Significant rapid defect growth',
        'Band selection policy change'
    ]

    execute = executeJiraMining(datakey='de003')  # 'df049'
    # tfidf
    success, nnDF2DList, snip2DList = execute.executeAllJobs(embeddingType='tfidf', knownCauses=testLabels)

    # bert
    # execute.executeAllJobs(embeddingType='bert', knownCauses=testLabels)
    return


if __name__ == '__main__':
    """Performs execution delta of the process."""
    pStart = datetime.datetime.now()
    try:
        main()
    except Exception as errorMain:
        print(f"Fail End Process: {errorMain}{os.linesep}{pprint.pformat(whoami())}")
        traceback.print_exc()
    qStop = datetime.datetime.now()
    print("Execution time: " + str(qStop - pStart))
