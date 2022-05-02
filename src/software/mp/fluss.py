#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Yan Zhu, Chin-Chia Michael Yeh, Zachary Zimmerman, Kaveh Kamgar, Eamonn Keogh, Tyler Woods, Joseph Tarango
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, \
    unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations

import numpy as np


def _idealized_arc_curve(n, x):
    """
    Returns the value at x for the parabola of width n and height n / 2.
    Formula taken from https://www.desmos.com/calculator/awtnrxh6rk.

    Parameters
    ----------
    n: Length of the time series to calculate the parabola for.
    x: location to compute the parabola value at.
    """
    height = n / 2
    width = n
    c = width / 2
    b = height
    a = height / (width / 2) ** 2
    y = -(a * (x - c) ** 2) + b
    return y


def fluss(mpi, m=None):
    """
    Returns the corrected arc curve (CAC) for the matrix profile index (MPI).
    The FLUSS algorithm provides Fast Low-cost Unipotent Semantic Segmentation.

    Parameters
    ----------
    mpi: Matrix profile index accompanying a time series.
    m: Subsequence length that was used to compute the MPI. Note: leaving this empty omits the correction at the head
    and tail of the CAC.
    """
    n = len(mpi)
    nnmark = np.zeros(n)

    # find the number of additional arcs starting to cross over each index
    for i in range(0, n):
        mpi_val = mpi[i]
        small = int(min(i, mpi_val))
        large = int(max(i, mpi_val))
        nnmark[small + 1] = nnmark[small + 1] + 1
        nnmark[large] = nnmark[large] - 1

    # cumulatively sum all crossing arcs at each index
    cross_count = np.cumsum(nnmark)

    # compute ideal arc curve for all indices
    idealized = np.apply_along_axis(lambda ii: _idealized_arc_curve(n, ii), 0, np.arange(0, n))
    idealized = cross_count / idealized

    # correct the arc curve so that it is between 0 and 1
    idealized[idealized > 1] = 1
    corrected_arc_curve = idealized

    if m:
        corrected_arc_curve[:m] = 1
        corrected_arc_curve[-m:] = 1

    return corrected_arc_curve


if __name__ == "__main__":
    import doctest

    doctest.method()
