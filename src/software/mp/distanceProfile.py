#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Yan Zhu, Chin-Chia Michael Yeh, Zachary Zimmerman, Kaveh Kamgar, Eamonn Keogh, Tyler Woods, Joseph Tarango
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, \
    unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations

from .utils import *
import numpy


def _clean_nan_inf(ts):
    search = numpy.isnan(ts)
    ts[search] = numpy.inf

    return ts


def naiveDistanceProfile(tsA, idx, m, tsB=None):
    """
    Returns the distance profile of a query within tsA against the time series tsB using the naive all-pairs comparison.

    Parameters
    ----------
    tsA: Time series containing the query for which to calculate the distance profile.
    idx: Starting location of the query within tsA
    m: Length of query.
    tsB: Time series to compare the query against. Note that, if no value is provided, tsB = tsA by default.
    """

    selfJoin = False
    if tsB is None:
        selfJoin = True
        tsB = tsA

    query = tsA[idx: (idx + m)]
    distanceProfile = []
    n = len(tsB)

    for i in range(n - m + 1):
        distanceProfile.append(zNormalizeEuclidean(query, tsB[i:i + m]))

    dp = numpy.array(distanceProfile)

    if selfJoin:
        trivialMatchRange = (int(max(0, idx - numpy.round(m / 2, 0))), int(min(idx + numpy.round(m / 2 + 1, 0), n)))

        dp[trivialMatchRange[0]: trivialMatchRange[1]] = numpy.inf

    return (dp, numpy.full(n - m + 1, idx, dtype=numpy.float128))


def massDistanceProfile(tsA, idx, m, tsB=None):
    """
    Returns the distance profile of a query within tsA against the time series tsB using the more efficient MASS comparison.

    Parameters
    ----------
    tsA: Time series containing the query for which to calculate the distance profile.
    idx: Starting location of the query within tsA
    m: Length of query.
    tsB: Time series to compare the query against. Note that, if no value is provided, tsB = tsA by default.
    """

    selfJoin = False
    if tsB is None:
        selfJoin = True
        tsB = tsA

    query = tsA[idx:(idx + m)]
    n = len(tsB)
    distanceProfile = numpy.real(numpy.sqrt(mass(query, tsB).astype(complex)))

    if selfJoin:
        trivialMatchRange = (int(max(0, idx - numpy.round(m / 2, 0))), int(min(idx + numpy.round(m / 2 + 1, 0), n)))
        distanceProfile[trivialMatchRange[0]:trivialMatchRange[1]] = numpy.inf

    # Both the distance profile and corresponding matrix profile index (which should just have the current index)
    return (distanceProfile, numpy.full(n - m + 1, idx, dtype=numpy.float128))


def mass_distance_profile_parallel(indices, tsA=None, tsB=None, m=None):
    """
    Computes distance profiles for the given indices either via self join or similarity search.

    Parameters
    ----------
    indices: Array of indices to compute distance profile for.
    tsA: Time series containing the query for which to calculate the distance profile.
    tsB: Time series to compare the query against. Note that, for the time being, only tsB = tsA is allowed
    m: Length of query.
    """
    distance_profiles = []

    for index in indices:
        distance_profiles.append(massDistanceProfile(tsA, index, m, tsB=tsB))

    return distance_profiles


def STOMPDistanceProfile(tsA, idx, m, tsB, dot_first, dp, mean, std):
    """
    Returns the distance profile of a query within tsA against the time series tsB using the even more efficient iterative STOMP calculation. Note that the method requires a pre-calculated 'initial' sliding dot product.

    Parameters
    ----------
    tsA: Time series containing the query for which to calculate the distance profile.
    idx: Starting location of the query within tsA
    m: Length of query.
    tsB: Time series to compare the query against. Note that, for the time being, only tsB = tsA is allowed
    dot_first: The 'initial' sliding dot product, or QT(1,1) in Zhu et.al
    dp: The dot product between tsA and the query starting at index m-1
    mean: Array containing the mean of every subsequence of length m in tsA (moving window)
    std: Array containing the mean of every subsequence of length m in tsA (moving window)
    """
    # print('HI')

    selfJoin = is_self_join(tsA, tsB)
    if selfJoin:
        tsB = tsA

    query = tsA[idx:(idx + m)]
    n = len(tsB)

    # Calculate the first distance profile via MASS
    if idx >= 0:
        distanceProfile = numpy.real(numpy.sqrt(mass(query, tsB).astype(complex)))

        # Currently re-calculating the dot product separately as opposed to updating all of the mass function...
        dot = slidingDotProduct(query, tsB)

    # Calculate all subsequent distance profiles using the STOMP dot product shortcut
    else:
        res, dot = massStomp(query, tsB, dot_first, dp, idx, mean, std)
        distanceProfile = numpy.real(numpy.sqrt(res.astype(complex)))
    # print(distanceProfile)

    distanceProfile = _clean_nan_inf(distanceProfile)

    if selfJoin:
        trivialMatchRange = (int(max(0, idx - numpy.round(m / 2, 0))), int(min(idx + numpy.round(m / 2 + 1, 0), n)))
        distanceProfile[trivialMatchRange[0]:trivialMatchRange[1]] = numpy.inf

    # print(distanceProfile)
    distanceProfile = _clean_nan_inf(distanceProfile)

    # Both the distance profile and corresponding matrix profile index (which should just have the current index)
    return (distanceProfile, numpy.full(n - m + 1, idx, dtype=numpy.float128)), dot


if __name__ == "__main__":
    import doctest

    doctest.method()
