#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Yan Zhu, Chin-Chia Michael Yeh, Zachary Zimmerman, Kaveh Kamgar, Eamonn Keogh, Tyler Woods, Joseph Tarango
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, \
    unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations

import numpy as np
from .utils import movmeanstd


def make_complexity_AV(ts, m):
    """
    returns a complexity annotation vector for timeseries ts with window m.
    The complexity of a window is the average absolute difference between consecutive data points.
    """
    diffs = np.diff(ts, append=0) ** 2
    diff_mean, diff_std = movmeanstd(diffs, m)

    complexity = np.sqrt(diff_mean)
    complexity = complexity - complexity.min()
    complexity = complexity / complexity.max()
    return complexity


def make_meanstd_AV(ts, m):
    """ returns boolean annotation vector which selects windows with a standard deviation greater than average """
    _, std = movmeanstd(ts, m)
    mu = std.mean()
    return (std < mu).astype(int)


def make_clipping_AV(ts, m):
    """
    returns an annotation vector proportional to the number if mins/maxs in the window
    """
    av = (ts == ts.min()) | (ts == ts.max())
    av, _ = movmeanstd(av, m)
    return av
