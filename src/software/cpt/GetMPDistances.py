#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Tyler Woods, Joseph Tarango
# *****************************************************************************/

from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import os, json, sys
import numpy as np
# from matrixProfile import *
import src.software.mp.matrixProfile as matrixProfile
from scipy import signal, spatial, stats

MP_WINDOW = 8
GOOD_KEYS_FILE = ''
KEY_TO_COMPARE_TO = 'query_s_45'

def EuclidDist(query, template):
    if len(query) > len(template):
        template = signal.resample(template, len(query))
    elif len(query) < len(template):
        query = signal.resample(query, len(template))
    return spatial.distance.euclidean(query, template)

def GetMPDistances(qMP, tMP):

    dist = EuclidDist(qMP, tMP)

    return dist

def DMMatrix(query, template):
    matrix = []
    for feature1 in query:
        arr = []
        for feature2 in template:
            arr.append(GetMPDistances(query[feature1], template[feature2]))
        matrix.append(arr)
    return np.array(matrix)


def GetFullMatrix(shapelets, CompareKey):
    for run in shapelets:
        if run != CompareKey:
            matrixProfile.Dist[run] = DMMatrix(shapelets[run], shapelets[CompareKey])


def main():
    with open('runMPShapes_10.txt') as jF:
        shapelets = json.load(jF)


    CompareKey = KEY_TO_COMPARE_TO

    Dist = GetFullMatrix(shapelets, CompareKey)


    JSON_Dic = {key: Dist[key].tolist() for key in Dist}

    with open('QDist_1.txt', 'w+') as jF:
        json.dump(JSON_Dic, jF)


if __name__ == '__main__':
    main()
