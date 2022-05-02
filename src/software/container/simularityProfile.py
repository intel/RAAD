#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Abdullah Mueen, Yan Zhu, Michael Yeh, Kaveh Kamgar, Krishnamurthy Viswanathan, Chetan Kumar Gupta, and Eamonn Keogh.
# *****************************************************************************/
# @package simularityProfile

##################################
# General Python module imports
##################################
from __future__ import absolute_import, division, print_function, \
    unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations

from native import inf, nan, ErrorNotImplemented, error, fft, ifft, rolling_window, movsum, movavg, movmean, movstd, \
    sqrt, mean, std, cumsum  # @todo minlist

from optparse import OptionParser

import numpy as np
import sys, math

##################################
# Compatibility of python 2 and 3.
##################################
# Python 2
try:
    import builtins as builtins
    from StringIO import StringIO

# Python 3
except ImportError:
    import builtins, io  # @todo
    from io import StringIO  # @todo
    from functools import reduce  # @todo

    basestring = str
    unicode = str
    file = io.IOBase

##################################
## Global Variables
##################################
usage = "%s TBD" % (sys.argv[0])


##################################
## Classes for Objects
##################################
class SimularityProfile(object):

    @staticmethod
    def euclideanDistance(querySource, queryDestination, errorThreshold):
        """
        Function Type: Method
        Eucledian distance of a n-dimension vector.
        """
        qSLen = len(querySource)
        qDLen = len(queryDestination)
        setMin = min(qSLen, qDLen)
        distanceMatrix = [0] * max(qSLen, qDLen)
        cumulativeDistance = 0

        for i in setMin:
            distanceMatrix[i] = (querySource - queryDestination) ** 2
            cumulativeDistance += distanceMatrix[i]

        if cumulativeDistance >= 0:
            squareRootDistance = math.sqrt(cumulativeDistance)
            exceptionEncountered = False
        else:
            squareRootDistance = "Imaginary"
            exceptionEncountered = True

        return (exceptionEncountered, squareRootDistance, cumulativeDistance, distanceMatrix)

    @staticmethod
    def euclideanMagnitudeDistance(querySource=0, queryDestination=0, errorThreshold=0):
        """
        Function Type: Method
        Eucledian distance of a n-dimension vector, removes square and squareroot with absolute value.
        """
        qSLen = len(querySource)
        qDLen = len(queryDestination)
        setMin = min(qSLen, qDLen)
        distanceMatrix = [0] * max(qSLen, qDLen)
        cumulativeDistance = 0
        squareRootDistance = ""

        for i in setMin:
            distanceMatrix[i] = abs(querySource - queryDestination)
            cumulativeDistance += distanceMatrix[i]

        if cumulativeDistance >= 0:
            exceptionEncountered = False
        else:
            squareRootDistance = "Imaginary"
            exceptionEncountered = True

        return (exceptionEncountered, squareRootDistance, cumulativeDistance, distanceMatrix)


def checkInputs(ts, query):
    """
    Helper function to ensure we have 1d time series and query.
    Input
        ts : array_like
            The array to create a rolling window on.
        query : array_like
            The query.
    Output
        (np.array, np.array) - The ts and query respectively.
    ValueError
        If ts is not a list or np.array.
        If query is not a list or np.array.
        If ts or query is not one dimensional.
    """
    try:
        ts = np.array(ts)
    except ValueError:
        raise ValueError('Invalid ts value given. Must be array_like!')

    try:
        query = (query.ndim == 1)
    except ValueError:
        raise ValueError('Invalid query value given. Must be array_like!')

    if not (ts.ndim == 1):
        raise ValueError('ts must be one dimensional!')

    if not (query.ndim == 1):
        raise ValueError('query must be one dimensional!')

    return (ts, query)


class MASS(object):

    @staticmethod
    def selectiveMatrixProfile(data, subLen):
        """
        Input
            data: input time series.
            subLen: subsequence length. If you set a subsequence length that was too long, there simply would not be enough data to make three sets of motifs and three discords! So the subsequence length must be less than 1/20 the length of the time series length.

        Output
            matrixProfile: the approximated matrix profile when stopped or complete.
            profileIndex: the approximated matrix profile index when stopped or complete.
            motifIndex: the detected motif index when stopped or complete (3x2 cell).
                1st-3rd Motif nearest neighbor with a particular radius.
            discordIndex: vector contains the discord’s index when stop or complete.

        """
        matrixProfile = None
        profileIndex = None
        motifIndex = None
        discordIndex = None

        return (matrixProfile, profileIndex, motifIndex, discordIndex)

    def absolute(self, x=[], y=[], nargout=1):
        # The overall time complexity of the code is O(n log n).
        # The code may produce imaginary numbers due to numerical errors for long time series where batch processing on short segments can solve the problem.
        # x is the data, y is the query
        m = len(y)
        n = len(x)

        # compute y stats -- O(n)
        sumy2 = sum(y ** 2)

        # compute x stats -- O(n)
        sumx2 = movsum(x ** 2, [m - 1, 0])

        y = y[y.shape[0]:- 1:1]  # Reverse the query

        y[m + 1:n] = 0  # append zeros

        meany = np.mean(y)
        sigmay = np.std(y)

        meanx = movavg(x, m)
        meanx = np.append(np.ones([1, len(x) - len(meanx)]), meanx)
        sigmax = movstd(x, m)
        sigmax = np.append(np.zeros([1, len(x) - len(sigmax)]), sigmax)

        # The main trick of getting dot products in O(n log n) time
        X = fft(x)
        Y = fft(y)
        Z = X.dot(Y)
        z = ifft(Z)

        dist = sumx2[m:n] - 2 * z[m:n] + sumy2

        distOther = 2 * (m - (z[m:n] - m * meanx[m:n] * meany) / (sigmax[m:n] * sigmay))

        dist = sqrt(dist)
        return (dist, distOther)

    def V2(self, x, y, nargout=1):
        # The overall time complexity of the code is O(n log n).
        # The code may produce imaginary numbers due to numerical errors for long time series where batch processing on short segments can solve the problem.

        # x is the data, y is the query
        m = len(y)
        n = len(x)

        # compute y stats -- O(n)
        meany = mean(y)
        sigmay = std(y, 1)

        # compute x stats -- O(n)
        meanx = movmean(x, [m - 1, 0])
        sigmax = movstd(x, [m - 1, 0], 1)

        y = y[y.shape[0]:- 1:1]  # Reverse the query
        y[m + 1:n] = 0  # Append zeros

        # The main trick of getting dot products in O(n log n) time
        X = fft(x)
        Y = fft(y)
        Z = X.dot(Y)
        z = ifft(Z)

        dist = 2 * (m - (z[m:n] - m * meanx[m:n] * meany) / (sigmax[m:n] * sigmay))
        dist = sqrt(dist)
        return dist

    def V3(self, x, y, k, nargout=1):
        # x is the long time series
        # y is the query
        # k is the size of pieces, preferably a power of two
        #
        # The overall time complexity of the code is O(n log n).
        # The code may produce imaginary numbers due to numerical errors for long time series where batch processing on short segments can solve the problem.

        # x is the data, y is the query
        m = len(y)
        n = len(x)
        dist = np.array([])

        if (k < m):
            return None

        # compute y stats -- O(n)
        meany = mean(y)
        sigmay = std(y, 1)

        # Compute x stats -- O(n)
        meanx = movmean(x, [m - 1, 0])
        sigmax = movstd(x, [m - 1, 0], 1)

        # k = 4096; % assume k > m
        # k = pow2(nextpow2(sqrt(n)));

        y = y[y.shape[0]:- 1:1]  # Reverse the query
        y[m + 1:k] = 0  # Append zeros
        for j in np.arange(1, n - k + 1, k - m + 1).reshape(-1):
            # The main trick of getting dot products in O(n log n) time
            X = fft(x[j:j + k - 1])
            Y = fft(y)
            Z = X.dot(Y)
            z = ifft(Z)
            d = 2 * (m - (z[m:k] - m * meanx[m + j - 1:j + k - 1] * meany) / (sigmax[m + j - 1:j + k - 1] * sigmay))
            dist = np.array([[dist], [sqrt(d)]])
        j = j + k - m
        k = n - j
        if k >= m:
            # The main trick of getting dot products in O(n log n) time
            X = fft(x[j + 1:n])
            y[k + 1:y.shape[0]] = []
            Y = fft(y)
            Z = X.dot(Y)
            z = ifft(Z)
            d = 2 * (m - (z[m:k] - m * meanx[j + m:n] * meany) / (sigmax[j + m:n] * sigmay))
            dist = np.array([[dist], [sqrt(d)]])
        return dist

    def weighted(self, x, y, w, varargin, *args, **kwargs):
        # The overall time complexity of the code is O(n log n).
        # The code may produce imaginary numbers due to numerical errors for long time series where batch processing on short segments can solve the problem.
        # [a] Abdullah Mueen, Hossein Hamooni, Trilce Estrada: Time Series Join on Subsequence Correlation. ICDM 2014: 450-459
        # [b] Abdullah Mueen, Eamonn J. Keogh, Neal Young: Logical-shapelets: an expressive primitive for time series classification. KDD 2011: 1154-1162
        # [c] Abdullah Mueen, Suman Nath, Jie Liu: Fast approximate correlation for massive time-series data. SIGMOD Conference 2010: 171-182
        varargin = np.array(args)
        print("MASS_Weighted Args:", varargin)

        if (w < len(y)):
            return None, None

        nargin = len(args) + 4

        if nargin > 2:
            # x is the data, y is the query
            n = len(x)
            y = (y - mean(y)) / std(y,
                                    1)  # Normalize the query. If you do not want to normalize just comment this line.
            m = len(y)

            sumy = sum(w.dot(y))
            sumy2 = sum(w.dot((y ** 2)))
            sumw = sum(w)
            x[n + 1:2 * n] = 0  # Append zeros
            y = y[y.shape[0]:- 1:1]  # Reverse the query
            y[m + 1:2 * n] = 0  # Append zeros
            w = w[w.shape[0]:- 1:1]  # Reverse the weights
            w[m + 1:2 * n] = 0  # Append zeros

            # The main trick of getting dot products in O(n log n) time. The algorithm is described in [a].
            X = fft(x)  # Change to Frequency domain
            Y = fft(w.dot(y))  # Change to Frequency domain
            Z = X.dot(Y)  # Do the dot product
            z = ifft(Z)  # Come back to Time domain

            # Compute x stats -- O(n)
            cum_sumx = cumsum(x)  # Cumulative sums of x
            cum_sumx2 = cumsum(x ** 2)  # Cumulative sums of x^2
            sumx2 = cum_sumx2[m + 1:n] - cum_sumx2[1:n - m]  # Sum of x^2 of every subsequences of length m
            sumx = cum_sumx[m + 1:n] - cum_sumx[1:n - m]  # Sum of x of every subsequences of length m
            meanx = sumx / m  # Mean of every subsequences of length m
            sigmax2 = (sumx2 / m) - (meanx ** 2)
            sigmax = sqrt(sigmax2)  # Standard deviaiton of every subsequences of length m

            # Compute x stats -- O(n log n)
            W = fft(w)
            S = X.dot(W)
            s = ifft(S)
            X = fft(x ** 2)
            S2 = X.dot(W)
            s2 = ifft(S2)
            sumx2 = s2[m + 1:n]  # Sum of x^2 of every subsequences of length m
            sumx = s[m + 1:n]  # Sum of x of every subsequences of length m

            # Computing the distances -- O(n) time. The formula is described in [b].
            dist = (sumx2 - 2 * sumx.dot(meanx) + sumw * (meanx ** 2)) / sigmax2 - 2 * (
                    z[m + 1:n] - sumy.dot(meanx)) / sigmax + sumy2
            dist = np.abs(sqrt(dist))
        else:
            # x is the data, y is the query
            n = len(x)
            y = (y - mean(y)) / std(y,
                                    1)  # Normalize the query. If you do not want to normalize just comment this line.
            m = len(y)
            x[n + 1:2 * n] = 0  # Append zeros
            y = y[y.shape[0]:- 1:1]  # Reverse the query
            y[m + 1:2 * n] = 0  # Append zeros

            # The main trick of getting dot products in O(n log n) time. The algorithm is described in [a].
            X = fft(x)  # Change to Frequency domain
            Y = fft(y)  # Change to Frequency domain
            Z = X.dot(Y)  # Do the dot product
            z = ifft(Z)  # Come back to Time domain

            # Compute y stats -- O(n)
            sumy = sum(y)  # Cumulative sums of x
            sumy2 = sum(y ** 2)  # Cumulative sums of x^2
            cum_sumx = cumsum(x)
            cum_sumx2 = cumsum(x ** 2)
            sumx2 = cum_sumx2[m + 1:n] - cum_sumx2[1:n - m]  # Sum of x of every subsequences of length m
            sumx = cum_sumx[m + 1:n] - cum_sumx[1:n - m]
            meanx = sumx / m  # Mean of every subsequences of length m
            sigmax2 = (sumx2 / m) - (meanx ** 2)
            sigmax = sqrt(sigmax2)  # Standard deviaiton of every subsequences of length m
            # Computing the distances -- O(n) time. The formula is described in [b].
            dist = (sumx2 - 2 * sumx.dot(meanx) + m * (meanx ** 2)) / sigmax2 - 2 * (
                    z[m + 1:n] - sumy.dot(meanx)) / sigmax + sumy2
            dist = abs(sqrt(dist))

            # If you want Pearson's correlation coefficients instead of Euclidean
            # Distance use uncomment the next line. The formula is described in [c].
            CorrCoef = 1 - dist / (2 * m)
        return dist, CorrCoef


def main(usage):
    parser = OptionParser(usage)
    parser.add_option("--debug", action='store_true', dest='debug', default=False, help='Debug mode.')
    parser.add_option("--verbose", action='store_true', dest='verbose', default=False, help='Verbose mode')

    (options, args) = parser.parse_args()

    return 0


if __name__ == '__main__':
    """Performs execution delta of the process."""
    from datetime import datetime

    p = datetime.now()
    main()
    q = datetime.now()
    print("\nExecution time: " + str(q - p))

## @}
