#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Abdullah Mueen, Yan Zhu, Michael Yeh, Kaveh Kamgar, Krishnamurthy Viswanathan, Chetan Kumar Gupta, and Eamonn Keogh.
# *****************************************************************************/
## @package simularityProfile

##################################
## General Python module imports
##################################
from __future__ import absolute_import, division, print_function, \
    unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations

from scipy.io import loadmat
import numpy as np
import matplotlib.pyplot as plt


# inf, nan, ErrorNotImplemented, error_, fft_, ifft_, rolling_window, movsum_, movavg_, movmean_, movstd_, sqrt_, mean_, std_, cumsum_

def ErrorNotImplemented(strError):
    print(strError)
    return


def error(object):
    print(object)


def inf():
    return float(np.inf)


def nan():
    return float(np.nan)


def sqrt(series, window=3):
    return np.sqrt(series)


def mean(series):
    return np.mean(series)


def std(series):
    return np.std(series)


def cumsum(series):
    return np.sum(series)


def isnan(keyValue):
    return np.isnan(keyValue)


def isinf(keyValue):
    return np.isinf(keyValue)


def fft(series):
    return np.fft.fft(series)


def ifft(series):
    return np.fft.ifft(series)


def rolling_window(series, window):
    """
    Provides a rolling window on a numpy array given an array and window size.
    Input
        a : array_like
            The array to create a rolling window on.
        window : int
            The window size.
    Output
        Strided array for computation.
    """
    shape = series.shape[:-1] + (series.shape[-1] - window + 1, window)
    strides = series.strides + (series.strides[-1],)

    return np.lib.stride_tricks.as_strided(series, shape=shape, strides=strides)


def movsum(series, window=3):
    return np.sum(rolling_window(series, window), -1)


def movavg(series, window=3):
    """
    Computes the moving average over an array given a window size.
    Parameters
    Input
        a : array_like
            The array to compute the moving average on.
        window : int
            The window size.
    Output
        The moving average over the array.
    """
    return np.mean(rolling_window(series, window), -1)


def movmean(series, window=3):
    return movavg(series, window)


def movstd(series, window=3):
    """
    Computes the moving std. over an array given a window size.
    Input
        a : array_like
            The array to compute the moving std. on.
        window : int
            The window size.
    Output
        The moving std. over the array.
    """
    return np.std(rolling_window(series, window), -1)


def figure(series=None, query=None, xLabel="Time in seconds", yLabel="Magnitude", title="Unknown Graph", filename=None):
    if series is None or query is None:
        return

    plt.plot(series, color="red", linewidth=2.5, linestyle="-")
    plt.plot(query, color="blue", linewidth=2.5, linestyle="-")
    plt.fill_between(series, query, facecolor='yellow')

    # The data limits are not updated automatically.
    plt.relim()

    # With tight True, graph flows smoothly.
    plt.autoscale_view(tight=True, scalex=True, scaley=True)

    # Label Figure
    plt.xlabel(xLabel)
    plt.ylabel(yLabel)
    plt.title(title)
    plt.legend()
    plt.show()

    if filename is not None:
        plt.savefig(filename, dpi=300)  # Save figure
    return plt


def figureList(series=[], xLabel="Time in seconds", yLabel="Magnitude", title="Unknown Graph", filename=None):
    if series is None:
        return

    for index, stream in enumerate(series):
        plt.plot(stream)

    plt.plot(subplots=True, legend=False, layout=(1, len(series)))

    # The data limits are not updated automatically.
    plt.relim()

    # With tight True, graph flows smoothly.
    plt.autoscale_view(tight=True, scalex=True, scaley=True)

    # Label Figure
    plt.xlabel(xLabel)
    plt.ylabel(yLabel)
    plt.title(title)
    plt.legend()
    plt.show()

    if filename is not None:
        plt.savefig(filename, dpi=300)  # Save figure
    return plt


def cell():
    pass


def copy():
    pass


def arange(inArgs):
    return np.arange(inArgs)


def sort():
    pass


def length(inA):
    return len(inA)


def zeros():
    return np.zeros()
    pass


def ones():
    return np.ones()


def floor():
    pass


def size(inA):
    return len(inA)


def find():
    pass
