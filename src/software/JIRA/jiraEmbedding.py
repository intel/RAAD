#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Rogelio Macedo, Joseph Tarango
# *****************************************************************************/

import os, datetime, pprint, csv, json
import pickle
import traceback
import pandas as pd
from scipy import stats
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
from src.software.utilsCommon import tryFolder


# Since we already have a list of tokens per document, we simply bypass TfidfVectorizer tokenization step by
# using this function to simply return the tokenized doc itself.


def placeholder(doc):
    return doc


class jiraEmbedding(object):
    def __init__(self,
                 csvInputFile: str = None,
                 distanceFunction=None,
                 numClusters: int = None,
                 unwantedNoiseFile: str = 'data/jiraUtilMeta'):
        """

            Args:
                csvInputFile:       (required) csv file containing data for jiras and it's fields
                distanceFunction:   (optional) desired function to measure distance between data-points
                numClusters:        (optional) if performing unsupervised analysis, desired number of clusters to create
                unwantedNoiseFile:  (required) json file looking exactly like this:
                    {
                        "noiseKeys": [... list of string-type keys/fields/features classifying as noise in the data ...]
                    }

        """
        unwantedNoiseFile = tryFolder(path=unwantedNoiseFile)
        unwantedNoiseFile = os.path.join(unwantedNoiseFile, 'jiraNoiseFields.json')
        with open(unwantedNoiseFile) as f:
            noiseFile = json.load(f)

        self.csvInputFile = os.path.abspath(csvInputFile)
        self.distanceFunction = distanceFunction
        self.numClusters = numClusters
        self.unwanted = set(noiseFile['noiseKeys'])
        self.X = None
        self.vectorizer = None
        self.jiraFields = None
        self.getFieldSet()
        return

    def getFieldSet(self):
        lines = (line for line in open(self.csvInputFile))
        topJiras = (s.rstrip().split(',') for s in lines)
        self.jiraFields = next(topJiras)
        return

    def getTokenizedDocs(self):
        """
        Returns:
            documents: 2-D list of N rows; N corresponds to the number of data-points in the dataset;
                       each n_i is the list of tokens (i.e. words) per data-point
        """

        jdata = pd.read_csv(self.csvInputFile)
        documents = list()

        for index, row in jdata.iterrows():
            doc = self.getFieldDocument(row=row, noiseSet=self.unwanted)
            documents.append(doc)
        return documents

    def getFieldDocument(self, row, noiseSet: set = None):
        retDoc = list()
        for index, value in row.items():
            if index not in noiseSet:
                thisList = list()
                try:
                    di = eval(value)
                    if type(di) == dict:
                        thisList = self.getSentences(thisList, di, noiseSet)
                except:
                    if value != 'none':
                        thisList.append(str(value))
                retDoc += thisList
        return retDoc

    def getSentences(self, inlist: list = None, d: dict = None, skiplist: set = None):
        outlist = list()
        for k, value in d.items():
            if k not in skiplist:
                if type(value) == dict:
                    outlist = self.getSentences(outlist, value, skiplist)
                else:
                    tokens = value.split(' ')
                    outlist += tokens
        return inlist + outlist

    def getFieldMessege(self):
        """
        Returns:
            documents: list of size N where N is the number of data-points in the csv dataset;
                          each n_i is a string containing all of the data-point's text

            docFields: 2-D list with N rows and L columns; N is the number of data-points in the csv dataset;
                          each n_i is itself a list of size L where L is the number of features per data-point;
                          each n_ij is a string containing the text for feature j of data-point i
            labelNeededIndices: indices for columns 'summary', 'description', 'Resolution Description', 'Fixed in Component'
        """

        jdata = pd.read_csv(self.csvInputFile)
        documents = list()
        docFields = list()
        i = 0
        labelNeededIndices = list()
        for item in jdata.columns:
            if item not in self.unwanted:
                if item in ('summary', 'description', 'Resolution Description', 'Fixed in Component'):
                    labelNeededIndices.append(i)
                i += 1

        for index, row in jdata.iterrows():
            doc, dfields = self.getFieldDocString(row=row, noiseSet=self.unwanted)
            documents.append(doc)
            docFields.append(dfields)
        return documents, docFields, labelNeededIndices

    def getFieldDocString(self, row, noiseSet: set):
        """

        Args:
            row:      a row in the dataframe of jiras, each row is a jira
            noiseSet: set of unwanted jira fields which we do not tokeinze

        Returns:      returnDoc: string of all text in jira,
                      fields:    list of strings where each element is the text for a field

        """
        retDoc = ''
        fields = list()
        for ind, value in row.items():
            if ind not in noiseSet:
                thisList = ''
                try:
                    di = eval(value)
                    if type(di) == dict:
                        thisList = self.getSentenceString(thisList, di, noiseSet)
                    else:
                        if value != 'none':
                            thisList += ' ' + str.lower(value)
                except:
                    if value != 'none':
                        thisList += ' ' + str.lower(str(value))
                retDoc += thisList
                fields.append(thisList)

        return retDoc, fields

    def getSentenceString(self, inlist, d: dict = None, skiplist: set = None):
        """

        Recursive function to grab text values from a dictionary of dictionaries

        Args:
            inlist:     list containing previously populated text for a field
            d:          dictionary item which we traverse and grab text from
            skiplist:   fields to skip

        Returns:        result string of text after walking down to the deepest level of the dictionary of dictionaries

        """
        outlist = ''
        for k, value in d.items():
            if k not in skiplist:
                if type(value) == dict:
                    outlist = self.getSentenceString(outlist, value, skiplist)
                else:
                    outlist += ' ' + str.lower(value)
        return inlist + ' ' + outlist

    def tfidfVectorization(self, outputName: str = None, writeData: bool = True):
        """
        Args:
            writeData:        option to allow for writing of data to file
            outputName:       name for output csv of embedded data
        """
        finalOfile = os.path.abspath(os.path.join(os.getcwd(), outputName))
        # docs = self.getTokenizedDocs()
        # tfidf = TfidfVectorizer(
        #     analyzer='word',
        #     tokenizer=placeholder,
        #     preprocessor=placeholder,
        #     token_pattern=None,
        #     use_idf=True,
        #     sublinear_tf=True)

        tfidf = TfidfVectorizer(
            analyzer='word',
            use_idf=True,
            sublinear_tf=True)
        docs, docFields = self.getFieldMessege()
        self.X = tfidf.fit_transform(docs)
        self.vectorizer = tfidf
        if writeData:
            pd.DataFrame(self.X.toarray()).to_csv(finalOfile, encoding='utf-8', index=False)
        return self.X

    def bertEmbedJira(self, labels=None):
        """

        Args:
            labels: set of known causes associted with the assert signature

        Returns:
            docFields: embedding 3D matrix, where each jira is a matrix of jira-field embeddings,
            labels:    labeled jiras in order of how they are organized in the original csv dataset

        """
        docs, docFields, relevantFields = self.getFieldMessege()
        totalDocs = len(docFields)

        # load pretrained model
        sbert_model = SentenceTransformer('bert-base-nli-mean-tokens')
        for i in range(totalDocs):
            docFields[i] = sbert_model.encode(docFields[i], show_progress_bar=False)
            print(f'{i}th Jira embedded')
        print('done creating embeddings')
        return docFields, list(
            self.getJiraLabels(docs=docFields, jiraLabels=labels, model=sbert_model, relevantFields=relevantFields))

    @staticmethod
    def getJiraLabels(docs=None, jiraLabels=None, model=None, relevantFields=None):
        """

        Generator function which computes the accumulated similarity between the embedded label vector, and
        the vectors for the fields in relevantFields. It then generates the highest scoring/matching label.

        Args:
            docs:           embedding 3D matrix, where each jira is a matrix of jira-field embeddings
            jiraLabels:     labeled jiras in order of how they are organized in the original csv dataset
            model:          model used to create embeddings
            relevantFields: indices for field columns: 'summary', 'description', 'Resolution Description', 'Fixed in Component'

        Returns:            (label, accumulated similarity score) of most similar label per Jira

        """

        def cosineSim(u, v):
            """

            Args:
                u: vector u of d dimensions
                v: vector v of d dimensions

            Returns: cosine similarity between u and v

            """
            return np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v))

        j = 0
        encodedLabels = dict()
        for label in jiraLabels:
            encodedLabels[label] = model.encode([item.lower() for item in label], show_progress_bar=False)[0]

        for doc in docs:
            labelDict = {item: 0 for item in jiraLabels}
            for label in jiraLabels:
                cumulativeScore: float = 0
                queryVector = encodedLabels[label]
                for i in relevantFields:
                    cumulativeScore += cosineSim(queryVector, doc[i, :])
                labelDict[label] = cumulativeScore
            j += 1
            print(f'Label: {j}')
            labelItems = sorted(labelDict.items(), key=(lambda k: labelDict[k[0]]), reverse=True)
            labelsOnly = [item[0] for item in labelItems]
            yield labelsOnly


def distanceMeasure(contextA: np.ndarray = None, contextB: np.ndarray = None, evaluationFunction=stats.pearsonr):
    sim = validNumericalFloat(0.0)
    if contextA is None or contextB is None or evaluationFunction is None:
        return sim
    for i in range(contextA.shape[0]):
        score = evaluationFunction(contextA[i, :], contextB[i, :])
        sim += score[0]
    return sim / contextA.shape[0]


def setPairScore(contextA: dict = None, contextB: dict = None, evaluationFunction=stats.pearsonr, debug: bool = False):
    """
    description:
        computes the intersection of keys between contextA and contextB, and then
        for each of the keys in the intersection, compute the similarity scoring
        based on the parameter function.

    Args:
        contextA:           dictionary of a particular nonuniform metadata
        contextB:           dictionary of a particular nonuniform metadata
        evaluationFunction: Similarity score function pointer
        debug:              WHEN TRUE, the function will use double the memory for subobjects,
                            and push more data onto the stack; this can lead to a segmentation fault/memory-leak for
                            garbage collection (GC).
                            WHEN FALSE, the function will inplace-update subobjects and can potentially still push data
                            onto the stack due to the recursive nature of the function.

    Returns:
        sim:                cumulative similarity score of the dictionary key-value intersection
        dictofSims:         dictionary of key to similarity scores found for intersection
        intersectionList:   intersection of keys of two dictionary sets
        excludedListA:      list of keys not in A
        excludedlistB:      list of keys not in B

    Complexity:
        Theta: TBD
        Big-O: f(n, k) = 4n + n*k
                    k  = f(k, l)
                    l  = f(l, m)
                    f(n, f(n, n')) = 4n + n(4n + n')
                                   = 4n(1 + (1/4n)(n + n')
                                   assumption: n = n'
                                       lim(n=0, n'=inf) | 4(inf) + inf(4(inf) + inf)
                                            = 4q + q(4q + q) = 5q^2 + 4q = O(q^2 + q)
                                  assumption: n < n'
                                    interval: [n' <= n'', n' > n'']
                                        = q'' ^ (q')
                f(n, k) = [n^2 + n, n^(n^f(n, k)]
        Omega(f) = n
        Theta(f) = n^2 + n
        Big-O(f) = n^(
    """
    intersectionList = list()
    excludedListA = list()
    excludedListB = list()
    dictofSims = dict()
    sim = validNumericalFloat(0.0)

    if contextA is None or contextB is None or evaluationFunction is None:
        sim = None
        intersectionList = None
        excludedListA = None
        excludedListB = None
        dictofSims = None
        return sim, dictofSims, intersectionList, excludedListA, excludedListB

    for k, v in contextA.items():
        if k in contextB.keys():
            intersectionList.append(k)
        else:
            excludedListA.append(k)

    for k, v in contextB.items():
        if k not in contextA.keys():
            excludedListB.append(k)

    for _, item in enumerate(intersectionList):
        if isinstance(contextA[item], dict) and isinstance(contextB[item], dict):
            # As an alternative to recursion, we instead yeild for the scores of the dict values of the top-level dict
            simTemp, dictofSimsTemp, intersectionListTemp, excludedListATemp, excludedListBTemp = \
                yield setPairScore(contextA[item], contextB[item])
            if all(v is not None for v in
                   [simTemp, dictofSimsTemp, intersectionListTemp, excludedListATemp, excludedListB]):
                sim += simTemp
                intersectionList.extend(intersectionListTemp)
                excludedListA.extend(excludedListATemp)
                excludedListB.extend(excludedListBTemp)
                if debug:
                    temp = dict()
                for k, v in dictofSimsTemp.items():
                    if debug:
                        temp[str(item) + '.' + k] = dictofSimsTemp[k]
                    else:
                        dictofSims[str(item) + '.' + k] = dictofSims[k]
                        del dictofSims[k]

    # hypothesis: for values that are dicts, sim already accounted for their simlarity scores, so we don't have to
    # worry about recalculating their scores below, and thus we can simply add a score of 0 for those cases.
    for _, name in enumerate(intersectionList):
        try:
            score = evaluationFunction(contextA[name], contextB[name])
        except:
            score = validNumericalFloat(0.0)
        finally:
            sim += score
        if name not in dictofSims.keys():
            dictofSims[name] = score

    if len(intersectionList) > 0:
        sim /= len(intersectionList)

    return sim, dictofSims, intersectionList, excludedListA, excludedListB


def distFuncTest():
    # filePath = os.path.abspath(os.path.join(os.getcwd(), "data/jiraData/TestCase0-0SubDicts.json"))
    # jiras = nestedDict.flat2NestedDict(datafile=filePath)
    # jiras.parseInput()
    # root = jiras.getTree()['issues']
    # distances = [[validNumericalFloat(0.0) for j in range(len(root.keys()))] for i in range(len(root.keys()))]

    docs = pickle.load(open('EmbeddedJiras.p', 'rb'))
    distances = np.zeros(shape=(len(docs), len(docs)))
    # for i, kvi in enumerate(root.items()):
    #     for j, kvj in enumerate(root.items()):
    #         if kvi[0] != kvj[0]:
    #             simIJ, dictofSimsIJ, intersectionListIJ, excludedListAIJ, excludedListBIJ = setPairScore(kvi[1], kvj[1])
    #             distances[i, j] = simIJ
    #         else:
    #             distances[i, j] = validNumericalFloat(1.0)

    for i in range(len(docs)):
        for j in range(len(docs)):
            if i != j:
                distances[i, j] = distanceMeasure(contextA=docs[i], contextB=docs[j])
            else:
                distances[i, j] = validNumericalFloat(1.0)
    return


def validNumericalFloat(inValue):
    try:
        return np.longdouble(inValue)
    except ValueError:
        return np.nan


def main():
    ##############################################
    # Main function, Options
    ##############################################

    # None

    ##############################################
    # Main
    ##############################################
    with open('data/jiraData/jiraNoiseFields.json') as f:
        noiseFile = json.load(f)

    noise = set(noiseFile['noiseKeys'])
    # docs = getTokenizedDocs()

    # pickle.dump(docs, open('TokenizedDocs.p', 'wb'))
    return


if __name__ == '__main__':
    """Performs execution delta of the process."""
    pStart = datetime.datetime.now()
    try:
        # unittest.main()
        # main()
        # tfidfCosineSim()
        # clusterJiras()
        # distFuncTest()
        jEmbed = jiraEmbedding(csvInputFile='data/jiraData/csv/jsonToCsvDE003.csv',
                               # 'data/jiraData/csv/jsonToCsvDF049.csv'
                               unwantedNoiseFile='data/jiraData/jiraNoiseFields.json')
        jEmbed.tfidfVectorization(outputName='data/jiraData/embedded/tfidfTermDocumentMatrix.csv')
        # jEmbed.lsaPipeline()
        # jEmbed.bertEmbedJira()
    except Exception as errorMain:
        print("Fail End Process: {0}".format(errorMain))
        traceback.print_exc()
    qStop = datetime.datetime.now()
    print("Execution time: " + str(qStop - pStart))
