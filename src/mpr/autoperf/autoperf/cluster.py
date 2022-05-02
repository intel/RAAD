#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Brad McDonald, Mejbah ul Alam, Justin Gottschlich, Abdullah Muzahid
# *****************************************************************************/
"""cluster.py

Script to generate clusters of functions.

Example:
    `$ python cluster.py /top/dir num_clusters`
"""

from __future__ import division

import sys
import os
import numpy as np
from sklearn.cluster import KMeans

from autoperf import autoperf
from autoperf.counters import get_num_counters

topDir = sys.argv[1]
NCLUSTER = 2
if len(sys.argv) > 2:
    NCLUSTER = int(sys.argv[2])

apps = os.listdir(topDir)

meanDatasetList = []
for app in apps:
    print(app)
    appDir = os.path.join(topDir, app)
    dataDir = os.path.join(appDir, "no_false_sharing")
    runs = os.listdir(dataDir)
    dataset = None
    for run in runs:
        rundir = os.path.join(dataDir, run)
        datasetHeader, newData = autoperf.getPerfDataset(rundir, get_num_counters())
        if dataset is None:
            dataset = newData
        else:
            dataset.extend(newData)

        meanDataset = np.mean(dataset, axis=0)
        print(meanDataset)
        meanDatasetList.append(meanDataset)

    clusters = KMeans(n_clusters=NCLUSTER, random_state=0).fit(meanDatasetList)

    print(clusters.labels_)
    print(clusters.predict(meanDatasetList))
