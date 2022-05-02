#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Yan Zhu, Chin-Chia Michael Yeh, Zachary Zimmerman, Kaveh Kamgar, Eamonn Keogh, Tyler Woods, Joseph Tarango
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, \
    unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations

import numpy, numpy.fft, matplotlib.pyplot


def utils_ErrorNotImplemented(strError):
    print(strError)
    return


def utils_error(dataObject):
    print(dataObject)


def utils_inf():
    return float(numpy.inf)


def utils_nan():
    return float(numpy.nan)


def utils_sqrt(series, window=3):
    return numpy.sqrt(series)


def utils_mean(series):
    return numpy.mean(series)


def utils_std(series):
    return numpy.std(series)


def utils_cumsum(series):
    return numpy.sum(series)


def utils_isnan(keyValue):
    return numpy.isnan(keyValue)


def utils_isinf(keyValue):
    return numpy.isinf(keyValue)


def utils_fft(series):
    """
    Computes the inverse fast foyer transform.
    Parameters
    Input
        series : array_like
    Output
        The transformed array.
    """
    return numpy.fft.fft(series)


def utils_ifft(series):
    """
    Computes the inverse fast foyer transform.
    Parameters
    Input
        series : array_like
    Output
        The transformed array.
    """
    return numpy.fft.ifft(series)


def utils_rolling_window(series, window):
    """
    Provides a rolling window on a numpy array given an array and window size.
    Input
        series : array_like
            The array to create a rolling window on.
        window : int
            The window size.
    Output
        Strided array for computation.
    """
    shape = series.shape[:-1] + (series.shape[-1] - window + 1, window)
    strides = series.strides + (series.strides[-1],)

    return numpy.lib.stride_tricks.as_strided(series, shape=shape, strides=strides)


def utils_movsum(series, window=3):
    """
    Computes the moving sum over an array given a window size.
    Parameters
    Input
        series : array_like
            The array to compute the moving average on.
        window : int
            The window size.
    Output
        The moving sum over the array.
    """
    return numpy.sum(utils_rolling_window(series, window), -1)


def utils_movavg(series, window=3):
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
    return numpy.mean(utils_rolling_window(series, window), -1)


def utils_movmean(series, window=3):
    return utils_movavg(series, window)


def utils_movstd(series, window=3):
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
    return numpy.std(utils_rolling_window(series, window), -1)


def validNumericalFloat(inValue):
    """
    Determines if the value is a valid numerical object.
    Args:
        inValue: floating point value

    Returns: Value in floating point or Not-A-Number.

    """
    try:
        return numpy.longdouble(inValue)
    except ValueError:
        return numpy.nan


def util_calculateMean(data):
    """
    Calculates the mean in a multiplication method since division produces a infinity or NaN
    Args:
        data: Input data set. We use a dataframe.

    Returns: Calculated mean for a vector dataframe.

    """
    try:
        n = data.size
    except BaseException:
        n = len(data)
    n = numpy.longdouble(n)
    if isinstance(data, list):
        dataArray = numpy.asarray(data)
    else:
        dataArray = data
    weightsMask = numpy.ones_like(numpy.longdouble(dataArray))
    avgVal = numpy.average(dataArray, weights=weightsMask)
    return avgVal


def util_calculateMeanStd(data):
    """
    Calculates the standard deviation in a multiplication method since division produces a infinity or NaN
    Args:
        data: Input data set. We use a dataframe.

    Returns: Calculated standard deviation for a vector dataframe.

    """
    zero = numpy.longdouble(0.0)
    try:
        n = data.size
    except BaseException:
        n = len(data)
    n = numpy.longdouble(n)
    if n <= 1:
        return (zero, zero)
    if isinstance(data, list):
        dataArray = numpy.asarray(data)
    else:
        dataArray = data
    # Use multiplication version of mean since numpy bug causes infinity.
    mean = util_calculateMean(dataArray)
    sd = zero
    # Calculate standard deviation
    for el in dataArray:
        diff = numpy.longdouble(el) - numpy.longdouble(mean)
        sd += (diff) ** 2
    points = numpy.longdouble(n - 1)
    sd = numpy.longdouble(numpy.sqrt(numpy.longdouble(sd) / numpy.longdouble(points)))
    return (mean, sd)


def utils_figure(series=None, query=None, xLabel="Time in seconds", yLabel="Magnitude", title="Unknown Graph",
                 filename=None):
    if series is None or query is None:
        return

    matplotlib.pyplot.plot(series, color="red", linewidth=2.5, linestyle="-")
    matplotlib.pyplot.plot(query, color="blue", linewidth=2.5, linestyle="-")
    matplotlib.pyplot.fill_between(series, query, facecolor='yellow')

    # The data limits are not updated automatically.
    matplotlib.pyplot.gca().relim()

    # With tight True, graph flows smoothly.
    matplotlib.pyplot.gca().autoscale_view(tight=True, scalex=True, scaley=True)

    # Label Figure
    matplotlib.pyplot.xlabel(xLabel)
    matplotlib.pyplot.ylabel(yLabel)
    matplotlib.pyplot.title(title)
    matplotlib.pyplot.legend()
    matplotlib.pyplot.show()

    if filename is not None:
        matplotlib.pyplot.savefig(filename, dpi=300)  # Save figure
    return


def utils_figureList(series, xLabel="Time in seconds", yLabel="Magnitude", title="Unknown Graph", filename=None):
    if series is None or series is []:
        return

    for index, stream in enumerate(series):
        matplotlib.pyplot.plot(stream)

    matplotlib.pyplot.plot(subplots=True, legend=False, layout=(1, len(series)))

    # The data limits are not updated automatically.
    matplotlib.pyplot.gca().relim()

    # With tight True, graph flows smoothly.
    matplotlib.pyplot.gca().autoscale_view(tight=True, scalex=True, scaley=True)

    # Label Figure
    matplotlib.pyplot.xlabel(xLabel)
    matplotlib.pyplot.ylabel(yLabel)
    matplotlib.pyplot.title(title)
    matplotlib.pyplot.legend()
    matplotlib.pyplot.show()

    if filename is not None:
        matplotlib.pyplot.savefig(filename, dpi=300)  # Save figure
    return

def zNormalize(ts):
    """
    Returns a z-normalized version of a time series.

    Parameters
    ----------
    ts: Time series to be normalized
    """

    ts -= numpy.mean(ts)
    std = numpy.std(ts)

    if std == 0:
        raise ValueError("The Standard Deviation cannot be zero")
    else:
        ts /= std

    return ts


def zNormalizeEuclidean(tsA, tsB):
    """
    Returns the z-normalized Euclidean distance between two time series.

    Parameters
    ----------
    tsA: Time series #1
    tsB: Time series #2
    """

    if len(tsA) != len(tsB):
        raise ValueError("tsA and tsB must be the same length")

    return numpy.linalg.norm(zNormalize(tsA.astype("float64")) - zNormalize(tsB.astype("float64")))


def movmeanstd(ts, m=0):
    """
    Calculate the mean and standard deviation within a moving window passing across a time series.

    Parameters
    ----------
    ts: Time series to evaluate.
    m: Width of the moving window.
    """
    if m <= 1:
        raise ValueError("Query length must be longer than one")
    mInt = int(m)
    zero = 0
    ts = ts.astype(numpy.longdouble)
    # Add zero to the beginning of the cumulative sum of ts
    s = numpy.insert(numpy.cumsum(ts), zero, zero)

    # Add zero to the beginning of the cumulative sum of ts ** 2
    sSq = numpy.insert(numpy.cumsum(ts ** 2), zero, zero)
    segSum = s[mInt:] - s[:-mInt]
    segSumSq = sSq[mInt:] - sSq[:-mInt]

    mov_mean = segSum / m
    mov_stdP = (segSumSq / m) - ((segSum / m) ** 2)
    if not numpy.all(mov_stdP == 0):
        mov_std = numpy.sqrt(numpy.abs(mov_stdP))
    else:
        mov_std = mov_stdP

    return [mov_mean, mov_std]


def movstd(ts, m):
    """
    Calculate the standard deviation within a moving window passing across a time series.

    Parameters
    ----------
    ts: Time series to evaluate.
    m: Width of the moving window.
    """
    if m <= 1:
        raise ValueError("Query length must be longer than one")

    ts = ts.astype("float")
    # Add zero to the beginning of the cumulative sum of ts
    s = numpy.insert(numpy.cumsum(ts), 0, 0)
    # Add zero to the beginning of the cumulative sum of ts ** 2
    sSq = numpy.insert(numpy.cumsum(ts ** 2), 0, 0)
    segSum = s[m:] - s[:-m]
    segSumSq = sSq[m:] - sSq[:-m]

    return numpy.sqrt(segSumSq / m - (segSum / m) ** 2)


def slidingDotProduct(query, ts):
    """
    Calculate the dot product between a query and all subsequences of length(query) in the timeseries ts. Note that we use Numpy's rfft method instead of fft.

    Parameters
    ----------
    query: Specific time series query to evaluate.
    ts: Time series to calculate the query's sliding dot product against.
    """
    m = len(query)
    n = len(ts)

    # If length is odd, zero-pad time series
    ts_add = 0
    if n % 2 == 1:
        ts = numpy.insert(ts, 0, 0)
        ts_add = 1

    q_add = 0
    # If length is odd, zero-pad query
    if m % 2 == 1:
        query = numpy.insert(query, 0, 0)
        q_add = 1

    # This reverses the array
    query = query[::-1]

    query = numpy.pad(query, (0, n - m + ts_add - q_add), 'constant')

    # Determine trim length for dot product. Note that zero-padding of the query has no effect on array length, which is solely determined by the longest vector
    trim = m - 1 + ts_add

    dot_product = numpy.fft.irfft(numpy.fft.rfft(ts) * numpy.fft.rfft(query))

    # Note that we only care about the dot product results from index m-1 onwards, as the first few values aren't true dot products (due to the way the FFT works for dot products)
    return dot_product[trim:]


def DotProductStomp(ts, m, dot_first, dot_prev, order):
    """
    Updates the sliding dot product for a time series ts from the previous dot product dot_prev.

    Parameters
    ----------
    ts: Time series under analysis.
    m: Length of query within sliding dot product.
    dot_first: The dot product between ts and the beginning query (QT1,1 in Zhu et.al).
    dot_prev: The dot product between ts and the query starting at index-1.
    order: The location of the first point in the query.
    """

    curLen = len(ts) - m + 1
    dot = numpy.roll(dot_prev, 1)

    dot += ts[order + m - 1] * ts[m - 1:curLen + m] - ts[order - 1] * numpy.roll(ts[:curLen], 1)

    # Update the first value in the dot product array
    dot[0] = dot_first[order]

    return dot


def mass(query, ts):
    """
    Calculates Mueen's ultra-fast Algorithm for Similarity Search (MASS): a Euclidean distance similarity search algorithm. Note that we are returning the square of MASS.

    Parameters
    ----------
    :query: Time series snippet to evaluate. Note that the query does not have to be a subset of ts.
    :ts: Time series to compare against query.
    """
    numericalResolution = numpy.finfo(float).eps
    # query_normalized = zNormalize(numpy.copy(query))
    mQFloat = numpy.longdouble(len(query))
    m = int(len(query))
    # Original
    # q_mean = numpy.mean(query)
    # q_std = numpy.std(query)
    # Multiply version, more robust
    q_mean, q_std = util_calculateMeanStd(data=query)
    mean, std = movmeanstd(ts, m)
    if q_std == 0:
        q_std = numericalResolution
    std = numpy.array(std)
    std[std == 0.0] = numericalResolution
    dot = slidingDotProduct(query, ts)

    # Original
    # res = numpy.sqrt(2*m*(1-(dot-m*mean*q_mean)/(m*std*q_std)))
    # Modified
    demoniator = (mQFloat * std * q_std)
    numerator = (dot - mQFloat * mean * q_mean)
    res = 2 * mQFloat * (1 - numerator / demoniator)
    res = numpy.sqrt(numpy.abs(res)) * numpy.sign(
        res)  # @todo note we are taking the absolute value then preserving the sign from before the square root.
    return res


def massStomp(query, ts, dot_first, dot_prev, index, mean, std):
    """
    Calculates Mueen's ultra-fast Algorithm for Similarity Search (MASS) between a query and timeseries using the STOMP dot product speedup. Note that we are returning the square of MASS.

    Parameters
    ----------
    query: Time series snippet to evaluate. Note that, for STOMP, the query must be a subset of ts.
    ts: Time series to compare against query.
    dot_first: The dot product between ts and the beginning query (QT1,1 in Zhu et.al).
    dot_prev: The dot product between ts and the query starting at index-1.
    index: The location of the first point in the query.
    mean: Array containing the mean of every subsequence in ts.
    std: Array containing the standard deviation of every subsequence in ts.
    """
    m = len(query)
    dot = DotProductStomp(ts, m, dot_first, dot_prev, index)
    std = numpy.array(std)
    std[std == 0.0] = 0.0001

    # Return both the MASS calculation and the dot product
    res = 2 * m * (1 - (dot - m * mean[index] * mean) / (m * std[index] * std))

    return res, dot


def apply_av(mp, av=None):
    """
    Applies an annotation vector to a Matrix Profile.

    Parameters
    ----------
    mp: Tuple containing the Matrix Profile and Matrix Profile Index.
    av: Numpy array containing the annotation vector.
    """

    if av is None:
        av = [1.0]

    if len(mp[0]) != len(av):
        raise ValueError(
            "Annotation Vector must be the same length as the matrix profile")
    else:
        av_max = numpy.max(av)
        av_min = numpy.min(av)
        if av_max > 1 or av_min < 0:
            raise ValueError("Annotation Vector must be between 0 and 1")
        mp_corrected = mp[0] + (1 - numpy.array(av)) * numpy.max(mp[0])
        return (mp_corrected, mp[1])


def is_self_join(tsA, tsB):
    """
    Helper function to determine if a self join is occurring or not. When tsA
    is absolutely equal to tsB, a self join is occurring.

    Parameters
    ----------
    tsA: Primary time series.
    tsB: Subquery time series.
    """
    return tsB is None or numpy.array_equal(tsA, tsB)
