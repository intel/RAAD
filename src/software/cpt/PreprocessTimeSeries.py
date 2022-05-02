#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Tyler Woods, Joseph Tarango
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import os, json, sys
import numpy as np
import src.software.mp.matrixProfile as mp
import src.software.getOptions as op
from datetime import datetime
from scipy import signal, spatial, stats

# Find the scalar Euclidean Distance between two time series
def Pearson(q, ts):
    if len(q) > len(ts):
        ts = signal.resample(ts, len(q))
    elif len(q) < len(ts):
        q = signal.resample(q, len(ts))
    num = stats.pearsonr(q, ts)[0]
    if np.isnan(num): return 0
    return num

# Find the scalar Euclidean Distance between two time series
def EuclidDist(q, ts):
    if len(q) > len(ts):
        ts = signal.resample(ts, len(q))
    elif len(q) < len(ts):
        q = signal.resample(q, len(ts))
    num = np.linalg.norm(np.array(q)-np.array(ts))
    if np.isnan(num): return 0
    return num

# Get the matrix profile of each time series in a dictionary
# The smallest noise possible is added to each point in the time series to negate
# problems with
def getMP(shapelets):
    MP = {}
    for run in shapelets['data']:
        print(run)
        MP[run] = {}
        for feature in shapelets['data'][run]['data']:
            try:
                arr = signal.resample(shapelets['data'][run]['data'][feature], 100)
                arr = np.random.normal(arr, np.finfo(float).eps)
                print(arr)
                MP[run][feature] = mp.stomp(arr,8)[0].tolist()
                #print(MP[run][feature])
            except OverflowError:
                continue

    return MP

def DTWCost(q, ts):
    if len(q) > len(ts):
        ts = signal.resample(ts, len(q))
    elif len(q) < len(ts):
        q = signal.resample(q, len(ts))
    return nD.DTWCost(q, ts)

def DTW(shapelets):
    runDTW = {}

    for run1 in shapelets.keys():
        runCompare = {}
        featureArr = [feature for feature in shapelets[run1]]
        for run2 in shapelets.keys():
            featureCompare = {}
            for feature1 in featureArr:
                feature = {}
                for feature2 in featureArr:
                    try:
                        signal1 = shapelets[run1]['data'][feature1]
                        signal2 = shapelets[run2]['data'][feature2]
                        minCost = DTWCost(signal1, signal2)
                        feature[feature2] = minCost
                    except KeyError as e:
                        print("had error:",e)

                featureCompare[feature1] = feature
            runCompare[run2] = featureCompare
        runDTW[run1] = runCompare

    return runDTW

def Pears(shapelets):
    runPears = {}

    for run1 in shapelets.keys():
        runCompare = {}
        featureArr = [feature for feature in shapelets[run1]]
        for run2 in shapelets.keys():
            featureCompare = {}
            for feature1 in featureArr:
                feature = {}
                for feature2 in featureArr:
                    try:
                        signal1 = shapelets[run1]['data'][feature1]
                        signal2 = shapelets[run2]['data'][feature2]
                        minCost = EuclidDist(signal1, signal2)
                        feature[feature2] = minCost
                    except KeyError as e:
                        #print "had error:",e
                        continue

                featureCompare[feature1] = feature
            runCompare[run2] = featureCompare
        runPears[run1] = runCompare

    return runPears

def getPears(dic, compare):
    runPears = {}

    for key in dic["data"]:
        runCompare = {}
        featureArr = [feature for feature in shapelets[run1]]
        for run2 in shapelets.keys():
            featureCompare = {}
            for feature1 in featureArr:
                feature = {}
                for feature2 in featureArr:
                    try:
                        signal1 = shapelets[run1]['data'][feature1]
                        signal2 = shapelets[run2]['data'][feature2]
                        minCost = EuclidDist(signal1, signal2)
                        feature[feature2] = minCost
                    except KeyError as e:
                        #print "had error:",e
                        continue

                featureCompare[feature1] = feature
            runCompare[run2] = featureCompare
        runPears[run1] = runCompare

    return runPears

def getED(dic, compare):
    EDic = {}
    for key in dic:
        EDic[key] = ED(dic[key], dic[compare])
    return EDic

def matED(dic):
    edDic = {}
    for key1 in dic:
        print('key: ', key1)
        edDic1 = {}
        for key2 in dic:
            edDic1[key2] = ED(dic[key1], dic[key2])
        edDic[key1] = edDic1
    return edDic

def ED(query, template):
    Compare = {}
    for feature in query:
        try:
            Compare[feature] = EuclidDist(query[feature], template[feature])
        except KeyError:
            continue
    return Compare

def PreprocessTimeSeries(data, options):
    print("data_repr: ", data["repr"])
    print('starting')
    MP = getMP(data)
    print('distance')
    if options.process == "ED":
        processed = getED(MP, data["repr"])
    elif options.process == "DTW":
        h
    elif options.process == "Pears":
        h
    else:
        print("Error in options")
        exit(1)
    print('finished')
    print("processed keys: ", processed.keys())
    return processed

def main():
    options, args = op.GetParser()
    with open(options.infile, 'r') as jF:
        dataDic = json.load(jF)
    processed = PreprocessTimeSeries(dataDic, options)
    with open(options.outfile, 'w+') as jF:
        json.dump(processed, jF)

######## Main Execution #######
if __name__ == '__main__':
    p = datetime.now()
    main()
    q = datetime.now()
    #OutputLog.Information("\nExecution time: "+str(q-p))

