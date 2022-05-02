#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Tyler Woods, Joseph Tarango
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import numpy
import src.software.mp.matrixProfile

def retMP(shapelets):
    runMP = {}
    storeMP = {}

    for run in shapelets.keys():
        print(run)
        runMP[run] = {}
        storeMP[run] = {}
        for feature in shapelets[run].keys():
            arr = numpy.random.normal(shapelets[run][feature], numpy.finfo(float).eps)
            runMP[run][feature] = software.mp.matrixProfile.stomp(arr, 8)[0]
            storeMP[run][feature] = runMP[run][feature].tolist()
