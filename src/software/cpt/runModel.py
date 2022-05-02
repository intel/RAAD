#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Tyler Woods, Joseph Tarango
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import tensorflow as tf
import sklearn
from tensorflow import keras

from sklearn.metrics import classification_report
from sklearn.linear_model import LinearRegression

import numpy as np
import os, json, random
import matplotlib.pyplot as plt
def main():
    try:
        try:
            test
        except NameError:
            test = None
        if test is not None:
            predictions = sklearn.linear_model.LinearRegression.predict(test)  # @todo fix destination model

            with open("QDist_2.txt") as jF:
                shapelets = json.load(jF)

            with open("labels_1.txt") as jF:
                labels = json.load(jF)

            dists = []

            for key in shapelets:
                dists.append(shapelets[key])

            dists = np.array(dists)

            model = keras.models.load_model('my_model_new_data.h5')

            pred_label = model.predict(dists)

            pred_label = [np.argmax(arr) for arr in pred_label]

            print(classification_report(labels, pred_label))
    finally:
        pass

if __name__ == '__main__':
    main()
