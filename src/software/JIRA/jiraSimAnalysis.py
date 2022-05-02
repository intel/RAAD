#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Rogelio Macedo, Joseph Tarango
# *****************************************************************************/

import os, datetime, pprint
import pickle
import traceback
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from scipy import sparse
from sklearn.cluster import MiniBatchKMeans, KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.model_selection import train_test_split

from src.software.utilsCommon import tryFile, tryFolder
from sklearn import mixture
from sklearn.metrics import silhouette_score


class jiraSimAnalysis(object):
    def __init__(self, embeddingData=None, embeddingFile: str = None, fullDataFile: str = None,
                 embeddingType: str = None):
        """

            Args:
                embeddingData: matrix data structure of embeddings
                embeddingFile: csv file containing embeddings for a crawled and cleaned set of Jiras
                fullDataFile:  csv file containing the pre-embedded data; used to extract the set of
                               uniquely-identifiable Jira keys

        """
        inputCSVPath = os.path.abspath(os.path.join(os.getcwd(), fullDataFile))
        # self.dataKeys: list of jira keys from the data
        self.dataKeys = list(pd.read_csv(filepath_or_buffer=inputCSVPath, usecols=['key']).values[:, 0])
        if embeddingFile is not None:
            self.dataFile = os.path.abspath(embeddingFile)
        else:
            self.dataFile = None
        self.similarityMatrix = None
        self.dimReduce = None
        self.embeddingType = embeddingType
        if embeddingData is not None:
            self.X = embeddingData
        else:
            self.X = None
        return

    def setDataset(self, csvFile: str = None):
        """

        Args:
            csvFile: file name to store in self.dataFile member variable

        """
        self.dataFile = csvFile
        return

    def readData(self, dataMatrix: np.ndarray = None):
        """

        Description:
            read embedded data into self.X and store as a sparse.csr_matrix

        """
        self.freeData()
        if dataMatrix is None:
            if self.dataFile is None:
                raise ValueError('readData: dataFile has not been set')
            else:
                self.dataFile = os.path.abspath(os.path.join(os.getcwd(), self.dataFile))
                self.X = sparse.csr_matrix(pd.read_csv(filepath_or_buffer=self.dataFile).values)
        else:
            self.X = sparse.csr_matrix(dataMatrix)
        return

    def freeData(self):
        """

        Description:
            free data used by all data matrices

        """
        if self.X is not None:
            del self.X
            self.X = None
        if self.similarityMatrix is not None:
            del self.similarityMatrix
            self.similarityMatrix = None
        return

    def singularVectorDecomp(self, need2read: bool = True, numFeatures: int = None, numIters: int = None):
        """

        Args:
            need2read:   (optional) boolean to read data if it hasn't been read
            numFeatures: (optional) number of features used to reduce the dimensionality to
            numIters:    (optional) number of iterations for singular vector decomposition

        Description:
            performs singular vector decomposition on a sparse data matrix; if paired with a tfidf term-document matrix,
            as the embedding method, then the result method is latent semantic analysis

        """
        if need2read:
            self.readData()
        if numFeatures is None:
            numFeatures = 100
        if numIters is None:
            numIters = 42
        self.dimReduce = TruncatedSVD(n_components=numFeatures, n_iter=numIters)
        return self.dimReduce.fit_transform(self.X)

    def cosineSimilarityKNN(self, data: np.ndarray = None, need2read: bool = True, k: int = 3,
                            outputFile: str = 'data/output/jiraDataStore/nearestNeighbors.csv', dimReduce='SVD'):
        """

        Args:
            dimReduce:
            outputFile:       (optional) rel path and filename for output .csv
            data:             (optional) predefined np.ndarray matrix
            need2read:        (optional) boolean to read data if it hasn't been read
            k:                (optional) maximum number of nearest neighbors

        Returns: Success boolean flag, and a dataframe of k-nearest neighbors per Jira ID

        """
        outputFile = tryFile(fileName=outputFile)
        if outputFile is None:
            outputFile = 'nearestNeighbors.csv'

        try:
            if data is not None:
                need2read = False
                self.readData(dataMatrix=data)
            if need2read:
                self.readData()

            if dimReduce == 'PCA':
                dataMatrix = PCA(n_components=100).fit_transform(X=self.X)
            elif dimReduce == 'SVD':
                dataMatrix = self.singularVectorDecomp(need2read=False, numFeatures=100, numIters=25)
            else:
                dataMatrix = self.X

            sim = cosine_similarity(dataMatrix, dataMatrix)
            topDocs = dict()
            topScoresPerJira = list()
            for i in range(sim.shape[0]):
                topKeys = list()
                currentRow = sim[i][:]
                rows = ((j, currentRow[j]) for j in range(currentRow.shape[0]))
                top = sorted(rows, key=lambda x: x[1], reverse=True)[1:k + 1]
                topScoresPerJira.append(top)
                for item in top:
                    topKeys.append(self.dataKeys[item[0]])
                topDocs[self.dataKeys[i]] = topKeys

            # we don't have to store the matrix in memory, we can store it in a file and read it if we need it
            # self.similarityMatrix = sim
            finalOfile = os.path.abspath(outputFile)
            nearNeighDF = pd.DataFrame.from_dict(data=topDocs,
                                                 orient='index',
                                                 columns=['Nearest Neighbor ' + str(i) for i in range(1, k + 1)])
            nearNeighDF.to_csv(finalOfile, encoding='utf-8', index_label='JIRA ID')
            print(f'Created Nearest Neighbor file: {finalOfile}')
        except Exception as e:
            print(f'Exception {e} occured during jiraSimAnalysis.cosineSimilarityKNN()')
            return False, None
        return True, nearNeighDF

    def snippetExtraction(self, fullDataFile=None, kNNSet=None,
                          outputFile: str = 'data/output/jiraDataStore/nearestNeighborContext.csv',
                          need2write: bool = True):
        outputFile = tryFile(fileName=outputFile)
        if outputFile is None:
            outputFile = './nearestNeighborContext.csv'

        # find what row the key is in
        cols = ['summary', 'description', 'Resolution Description']
        inputCSVPath = os.path.abspath(os.path.join(os.getcwd(), fullDataFile))
        data = pd.read_csv(filepath_or_buffer=inputCSVPath,
                           usecols=cols)
        snippets = dict()
        for line in kNNSet:
            neighborRows = (self.dataKeys.index(item) for item in line[1:])
            output = ''
            for n in neighborRows:
                for col in range(len(cols)):
                    fieldText = (s for s in data.iloc[n, col].split(' '))
                    try:
                        output += data.columns[col] + ': ' + ' '.join(list(fieldText)[:25]) + '...'
                    except IndexError:
                        output += data.columns[col] + ': ' + ' '.join(list(fieldText))
                    output += '\n#######################################################\n'
                output += 'link: https://nsg-jira.intel.com/browse/' + self.dataKeys[n] + '\n\n\n'
            snippets[line[0]] = output

        if need2write:
            finalOfile = os.path.abspath(os.path.join(os.getcwd(), outputFile))
            pd.DataFrame.from_dict(data=snippets,
                                   orient='index',
                                   columns=['Nearest Neighbor Context']
                                   ).to_csv(finalOfile, encoding='utf-8', index_label='JIRA ID')
            return True, None
        else:
            return True, pd.DataFrame.from_dict(data=snippets, orient='index', columns=['Nearest Neighbor Context'])

    def find_optimal_clusters(self, max_k: int = None, plotFile: str = 'ChooseClusterCount.pdf', max_iter: int = 11,
                              dataMatrix=None):
        """

        Args:
            dataMatrix: data to analyze, array-like, shape (n_samples, n_features)
            max_iter: max training iterations
            max_k:    maximum number of clusters
            plotFile: file name for plot file

        """
        print("Evaluate Clustering: K-Means")
        plotPath = tryFolder(path='data/output/jiraDataStore')
        if plotPath is None:
            plotPath = './ChooseClusterCount.pdf'
        else:
            plotPath = os.path.join(plotPath, plotFile)

        iters = range(2, max_k + 1, 2)
        sse = list()
        sseERR = list()
        for k in iters:
            tempSSE = list()

            for i in range(max_iter):
                mbKM = MiniBatchKMeans(n_clusters=k, random_state=np.random.RandomState()).fit(dataMatrix)
                tempSSE.append(mbKM.inertia_)

            sse.append(np.mean(tempSSE))
            sseERR.append(np.std(tempSSE))
            print('Fit {} clusters'.format(k))

        self.plotClusterCurve(plotName=plotPath, dataX=iters, dataY=sse, xlabel='# of Clusters', ylabel='SSE',
                              title="Sum of Sqaured Error by N. Clusters", yErr=sseERR)
        return

    def kMeansClustering(self, randState: int = None, assertLabels=None, dimReduce='SVD'):
        """

        Args:
            dimReduce:    choice for dimensionality reduction
            assertLabels: dictionairy with key: encoded label number, and value: known cause text label
            randState:    state to start at
        Description:
            plots clusters using K-Means clustering, and plots sum of squared error per number of clusters

        """
        # todo: find optimal clusters by tracking the range right after the SSE curve decreases the fastest
        if dimReduce == 'PCA':
            dataMatrix = PCA(n_components=200).fit_transform(X=self.X)
        elif dimReduce == 'SVD':
            dataMatrix = self.singularVectorDecomp(need2read=False, numFeatures=100, numIters=25)
        else:
            dataMatrix = self.X
        self.find_optimal_clusters(max_k=20, dataMatrix=dataMatrix)
        km = KMeans(n_clusters=len(assertLabels), random_state=25)
        clusters = km.fit_predict(dataMatrix)
        clusterDistanceSpace = km.transform(dataMatrix)
        sortedDistances = list()
        for curColumn in range(clusterDistanceSpace.shape[1]):
            sortedDistances.append([])
            columns = ((i, clusterDistanceSpace[i, curColumn]) for i in range(clusterDistanceSpace.shape[0]))
            top = sorted(columns, key=lambda x: x[1])
            sortedDistances[curColumn] = top
        # @todo rmacedo: used sortedDistances to get 10-25% closest nodes to plot per cluster
        self.plot_tsne_pca(labels=clusters, knownCauses=assertLabels, dataMatrix=dataMatrix)
        return

    @staticmethod
    def plot_tsne_pca(labels, knownCauses, plotFile: str = 'ClusterPlotPCA.pdf', plotFile2: str = 'ClusterPlotTSNE.pdf',
                      dataMatrix=None):
        """

        Args:
            dataMatrix:  data to plot, array-like, shape (n_samples, n_features)
            labels:      clusters returned from KMeans
            knownCauses: speculated cluster labels
            plotFile:    file name for cluster plot PCA
            plotFile2:   file name for cluster plot TSNE

        """
        plotPath = tryFolder(path='data/output/jiraDataStore')
        if plotPath is None:
            plotPath = './'
            plotFile = plotPath + plotFile
            plotFile2 = plotPath + plotFile2
        else:
            plotFile = os.path.join(plotPath, plotFile)
            plotFile2 = os.path.join(plotPath, plotFile2)
        # @todo rmace001: calculate the value for nodesInPlot based on the 10-25% closest nodes within each cluster
        if 300 <= dataMatrix.shape[0]:
            nodesInPlot = 300
        else:
            nodesInPlot = dataMatrix.shape[0]
        max_items = np.random.choice(range(dataMatrix.shape[0]), size=nodesInPlot, replace=False)

        pca = PCA(n_components=3).fit_transform(dataMatrix[max_items, :])
        tsne = TSNE(n_components=3).fit_transform(pca)
        label_subset = labels[max_items]

        fig = plt.figure()
        axKM = fig.add_subplot(projection='3d')

        for i, val in knownCauses.items():
            axKM.scatter(pca[label_subset == i, 0], pca[label_subset == i, 1], pca[label_subset == i, 2], label=val)
        axKM.set_title('PCA Cluster Plot 3D')
        axKM.legend(loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=2)
        plt.savefig(plotFile)
        plt.close()

        fig2 = plt.figure()
        axTSNE = fig2.add_subplot(projection='3d')

        for i, val in knownCauses.items():
            axTSNE.scatter(tsne[label_subset == i, 0], tsne[label_subset == i, 1], tsne[label_subset == i, 2],
                           label=val)
        axTSNE.legend(loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=2)
        axTSNE.set_title('TSNE Cluster Plot 3D')
        plt.savefig(plotFile2)
        plt.close()
        return

    def reshape3Dto2D(self):
        """

        Returns: embedding 2D matrix from a 3D matrix-represented set of embeddings for jiras, returns array-like, shape (n_samples, n_features)

        """
        if self.X is not None:
            data = np.empty(shape=(0, self.X[0].shape[0] * self.X[0].shape[1]))
            for matrix in self.X:
                row = np.append(np.empty(shape=(0, 0)), [matrix[i, :] for i in range(matrix.shape[0])])
                data = np.vstack((data, row))
            del self.X
            self.X = data
            return True
        else:
            return False

    @staticmethod
    def gmm_js(gmmP, gmmQ, n_samples=10 ** 5):
        """

        Args:
            gmmP: model P
            gmmQ: model Q
            n_samples: number of random samples to generate from gaussians

        Returns: Similarity score between two Gaussian Mixture Models trained with disjoint datasets

        """
        X = gmmP.sample(n_samples)[0]
        logP_X = gmmP.score_samples(X)
        logQ_X = gmmQ.score_samples(X)
        logMix_X = np.logaddexp(logP_X, logQ_X)

        Y = gmmQ.sample(n_samples)[0]
        logP_Y = gmmP.score_samples(Y)
        logQ_Y = gmmQ.score_samples(Y)
        logMix_Y = np.logaddexp(logP_Y, logQ_Y)

        return np.sqrt((logP_X.mean() - (logMix_X.mean() - np.log(2))
                        + logQ_Y.mean() - (logMix_Y.mean() - np.log(2))) / 2)

    @staticmethod
    def SelBest(arr: list, X: int) -> list:
        """

        Args:
            arr: data array
            X: max number of items to return

        Returns: set of X configurations with shortest distance

        """
        dx = np.argsort(arr)[:X]
        return arr[dx]

    def pickNClustersGMM(self, max_k: int = None,
                         plotFile0: str = 'DistanceBetweenGMMs.pdf',
                         plotFile1: str = 'SilhouetteClusterCount.pdf',
                         plotFile2: str = 'GradientBicScores.pdf',
                         max_iter: int = 11,
                         dataMatrix=None, ):
        """

        Args:
            max_k: max number of clusters
            plotFile0: filename
            plotFile1: filename
            plotFile2: filename
            max_iter: max training iterations
            dataMatrix: data to analyze, array-like, shape (n_samples, n_features)

        Returns:

        """
        plotPath = tryFolder(path='data/output/jiraDataStore')
        if plotPath is None:
            plotPath0 = './DistanceBetweenGMMs.pdf'
            plotPath1 = './SilhouetteClusterCount.pdf'
            plotPath2 = './GradientBicScores.pdf'
        else:
            plotPath0 = os.path.join(plotPath, plotFile0)
            plotPath1 = os.path.join(plotPath, plotFile1)
            plotPath2 = os.path.join(plotPath, plotFile2)

        print("Evaluate Clustering: Gaussian Mixture Model")
        n_clusters = np.arange(2, max_k)
        results = list()
        res_sigs = list()
        sil = list()
        silErr = list()
        bicScores = list()
        bicErr = list()
        for n in n_clusters:
            dist = list()
            tempSil = list()
            tempBic = list()
            for iteration in range(max_iter):
                # distance bw GMMs
                train, test = train_test_split(dataMatrix, test_size=0.5)
                gmm_train = mixture.GaussianMixture(n_components=n, n_init=2).fit(train)
                gmm_test = mixture.GaussianMixture(n_components=n, n_init=2).fit(test)

                # silhouette_score & BIC (Baysian information criterion)
                model = mixture.GaussianMixture(n_components=n).fit(X=dataMatrix)
                labels = model.predict(X=dataMatrix)

                dist.append(self.gmm_js(gmmP=gmm_train, gmmQ=gmm_test))
                tempSil.append(silhouette_score(X=dataMatrix, labels=labels))
                tempBic.append(model.bic(X=dataMatrix))

            sil.append(np.mean(tempSil))
            silErr.append(np.std(tempSil))
            bicScores.append(np.mean(tempBic))
            bicErr.append(np.std(tempBic))
            results.append(np.mean(dist))
            res_sigs.append(np.std(dist))
            print(f'Fit {n} clusters')

        self.plotClusterCurve(plotName=plotPath0, dataX=n_clusters, dataY=results, xlabel='# of Clusters',
                              ylabel='Distance',
                              title="Distance between Train and Test GMMs", yErr=res_sigs)

        self.plotClusterCurve(plotName=plotPath1, dataX=n_clusters, dataY=sil, xlabel='# of Clusters',
                              ylabel='Average Silhouette Score',
                              title='Avg. Silhouette by N. Clusters', yErr=silErr)

        self.plotClusterCurve(plotName=plotPath2, dataX=n_clusters, dataY=np.gradient(bicScores),
                              xlabel='# of Clusters', ylabel='gradient(BIC Scores)',
                              title='Gradient of BIC Scores by N. Clusters', yErr=bicErr)
        return

    @staticmethod
    def plotClusterCurve(plotName: str = None, dataX=None, dataY=None, xlabel=None, ylabel=None, title=None, yErr=None):
        """

        Args:
            xlabel: label for x-axis
            plotName: name of pdf file
            dataX: x-axis data
            dataY: y-axis data
            ylabel: label for y-axis
            title: label for title
            yErr: standard deviation for dataY

        Returns:

        """
        if plotName is None:
            plotName = "plot.pdf"
        f, ax = plt.subplots(1, 1)
        if yErr is not None:
            ax.errorbar(dataX, dataY, yerr=yErr)
        else:
            ax.plot(dataX, dataY, marker='o')
        ax.set_xlabel(xlabel)
        ax.set_xticks(dataX)
        ax.set_xticklabels(dataX)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        plt.savefig(plotName)
        plt.close()
        return

    def gaussianMixClusters(self, assertLabels=None, labeledDataset=None, dimReduce='SVD'):
        """

        Args:
            dimReduce:      choice for dimensionality reduction
            assertLabels:   list of associated labels to an assert signature
            labeledDataset: 2D-list of jira label-assignments; one list per jira sorted from highest to least probable label

        Returns:
            groupedIndices: dictionary with key: encoded label number, and value: list of Jiras assigned to the label key,
            mapping:        dictionairy with key: encoded label number, and value: known cause text label

        """

        if dimReduce == 'PCA':
            dataMatrix = PCA(n_components=200).fit_transform(X=self.X)
        elif dimReduce == 'SVD':
            dataMatrix = self.singularVectorDecomp(need2read=False, numFeatures=100, numIters=25)
        else:
            dataMatrix = self.X

        self.pickNClustersGMM(max_k=20, max_iter=5, dataMatrix=PCA(n_components=3).fit_transform(X=dataMatrix))
        nClusters = len(assertLabels)

        model = mixture.GaussianMixture(n_components=nClusters)
        model.fit(dataMatrix)
        labels = model.predict(dataMatrix)
        mapping = {i: '' for i in range(nClusters)}
        groupedIndices = {i: [] for i in range(nClusters)}
        for i in range(len(labels)):
            groupedIndices[labels[i]].append(i)

        allAssigned = False
        iteration = 0

        # labelRank == 0 means we check for the highest-ranking label assignment for a jira
        # labelRank == 1 means we check for the second-highest-ranking label assignment for a jira, etc.
        labelRank = 0
        encodedLabels = list(range(nClusters))
        knownCauses = list(assertLabels)
        while not allAssigned:
            bestOverall = (-1, 0, '')
            for kc in knownCauses:
                bestSoFar = (0, 0, kc)
                for labelNum in encodedLabels:
                    # find the best labelNum for kc
                    kcCount = 0
                    for i in groupedIndices[labelNum]:
                        currentLabel = labeledDataset[i][labelRank]
                        if currentLabel == kc:
                            kcCount += 1
                    if bestSoFar[1] < kcCount:
                        bestSoFar = (labelNum, kcCount, kc)
                if bestSoFar[1] > bestOverall[1]:
                    bestOverall = bestSoFar
            # assign the bestOverall mapping, and remove from sets
            if bestOverall[0] != -1:
                mapping[bestOverall[0]] = bestOverall[2]
                encodedLabels.remove(bestOverall[0])
                knownCauses.remove(bestOverall[2])

            if len(encodedLabels) == 0:
                allAssigned = True
            elif not iteration < nClusters:
                iteration = 0
                labelRank += 1
            else:
                iteration += 1

        # arrange the weighted log probabilities with the associated index in the dataset
        weightedLogProb = model.score_samples(dataMatrix)
        for i in range(nClusters):
            logProbTuples = dict()
            for j in groupedIndices[i]:
                logProbTuples[j] = weightedLogProb[j]
            groupedIndices[i] = logProbTuples

        # ranksort each index-probability dict by log probability
        for i in range(nClusters):
            groupedIndices[i] = {k: v for k, v in
                                 sorted(groupedIndices[i].items(), key=lambda item: item[1], reverse=True)}
        return groupedIndices, mapping


def main():
    ##############################################
    # Main function, Options
    ##############################################

    # None

    ##############################################
    # Main
    ##############################################
    emfile = '../data/jiraUtilMeta/embedded/tfidfTermDocumentMatrix.csv'
    fullfile = '../data/jiraUtilMeta/csv/jsonToCsvDE003.csv'  # '../data/jiraUtilMeta/csv/jsonToCsvDF049.csv'
    jiraSims = jiraSimAnalysis(embeddingFile=emfile,
                               fullDataFile=fullfile)
    jiraSims.readData()
    jiraSims.singularVectorDecomp(need2read=False, numFeatures=300, numIters=7)
    topScores, topJiras = jiraSims.cosineSimilarityKNN(need2read=False)
    jiraSims.kMeansClustering(assertLabels=topJiras)
    # @todo rogelio error in updating APIs
    # jiraSims.kMeansClustering(topJiras, optimalPlotFile = '../data/output/jiraDataStore/ChooseClusterCount.pdf',
    #                           kMeansPlotFile = '../data/output/jiraDataStore/ClusterPlot.pdf')
    # the above can be put into a unit/integration test regarding similarity analysis

    # Extract snippets
    # jiraSims = jiraSimAnalysis(embeddingFile='data/jiraUtilMeta/embedded/tfidfTermDocumentMatrix.csv',
    #                            fullDataFile='data/jiraUtilMeta/csv/jsonToCsvDF049.csv')
    # filename = os.path.abspath(os.path.join(os.getcwd(), 'data/jiraData/nearestNeighbors.csv'))
    # lines = (line for line in open(filename))
    # topJiras = (s.rstrip().split(',') for s in lines)
    # cols = next(topJiras)
    # jiraSims.snippetExtraction(fullDataFile='data/jiraData/csv/jsonToCsvDF049.csv', kNNSet=topJiras)
    return


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
