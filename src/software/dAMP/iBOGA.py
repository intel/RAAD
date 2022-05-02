#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
# @package iBOGA
from __future__ import absolute_import, division, print_function, \
    unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations

import datetime, traceback, numpy
from math import pi, sin
from warnings import catch_warnings, simplefilter

from matplotlib import pyplot
from numpy import arange, argmax, asarray, vstack
from numpy.random import normal, random
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessRegressor


class iBOGA(object):
    """
    Bayesian optimization finds the value that minimizes an objective function by building a surrogate function (probability model) based on past evaluation results of the objective. Bayesian methods differ from random or grid search in that they use past evaluation results to choose the next values to evaluate. The concept is: limit expensive evaluations of the objective function by choosing the next input values based on those that have done well in the past.

    In the case of hyperparameter optimization, the objective function is the validation error of a machine learning model using a set of hyperparameters. The aim is to find the hyperparameters that yield the lowest error on the validation set in the hope that these results generalize to the testing set. Evaluating the objective function is expensive because it requires training the machine learning model with a specific set of hyperparameters. Ideally, we want a method that can explore the search space while also limiting evaluations of poor hyperparameter choices. Bayesian hyperparameter tuning uses a continually updated probability model to “concentrate” on promising hyperparameters by reasoning from past results.

    Objective Function: 
        Features to minimize, in this case the validation error of a machine learning model with respect to the hyperparameters
    Domain Space: 
        Hyperparameter values to search over
    Optimization algorithm: 
        Method for constructing the surrogate model and choosing the next hyperparameter values to evaluate
    Result history: 
        stored outcomes from evaluations of the objective function consisting of the hyperparameters and validation loss

     Note: Instead of using a n-by-m rectangular grid, you can use a layout where each cell in the SOM is a hexagon.
      You can use a toroidal geometry where edges of the SOM connect. You can use three dimensions instead of two.
      There are many ways to define a close neighborhood for nodes.
    Reference: 
        "A Tutorial on Bayesian Optimization" https://arxiv.org/pdf/1807.02811.pdf
        "On hyperparameter optimization of machine learning algorithms: Theory and practice" https://doi.org/10.1016/j.neucom.2020.07.061
        "Optuna: A Next-generation Hyperparameter Optimization Framework"  https://arxiv.org/pdf/1907.10902.pdf https://optuna.readthedocs.io/en/stable/tutorial/10_key_features/003_efficient_optimization_algorithms.html


    """
    debug = False
    Dim = None
    Rows = None
    Cols = None
    RangeMax = None
    LearnMax = None
    StepsMax = None
    data_x_shadow = None
    data_y_shadow = None

    def __init__(self, debug: bool):
        self.debug = debug
        return

    @staticmethod
    def _objective(parameters: dict = None, equation=None):
        """
        Method to minimize hyper parameters get validation loss through metrics in ROC AUC.
        """
        noise = numpy.random.normal(loc=0, scale=parameters['noise'])
        hPara = equation + noise
        return hPara

    @staticmethod
    def _surrogate(model, xData):
        """
        Surrogate or approximation for the objective function
        """
        # catch any warning generated when making a prediction
        with catch_warnings():
            # ignore generated warnings
            simplefilter("ignore")
            return model.predict(xData, return_std=True)

    def _acquisition(self, xData, xSamples, model):
        """
        # probability of improvement acquisition function
        """
        # calculate the best surrogate score found so far
        yHat, _ = self._surrogate(model, xData)
        best = max(yHat)
        # calculate mean and standard deviation via surrogate function
        mu, std = self._surrogate(model, xSamples)
        mu = mu[:, 0]
        # calculate the probability of improvement
        probability = norm.cdf((mu - best) / (std + 1E-9))
        return probability

    # optimize the acquisition function
    def _opt_acquisition(self, xData, model):
        # random search, generate random samples
        xSamples = random(100)
        xSamples = xSamples.reshape(len(xSamples), 1)
        # calculate the acquisition function for each sample
        scores = self._acquisition(xData, xSamples, model)
        # Locate the index of the largest scores
        ix = argmax(scores)
        return xSamples[ix, 0]

    # plot real observations vs surrogate function
    def _plot(self, X, y, model):
        # scatter plot of inputs and real objective function
        pyplot.scatter(X, y)
        # line plot of surrogate function across domain
        xSamples = asarray(arange(0, 1, 0.001))
        xSamples = xSamples.reshape(len(xSamples), 1)
        ySamples, _ = self._surrogate(model, xSamples)
        pyplot.plot(xSamples, ySamples)
        # show the plot
        pyplot.show()
        return

    @staticmethod
    def runPhaseExample(self):
        # Domain Space: in this case integers
        # sample the domain sparsely with noise
        X = random(100)

        yList = list()
        for x in X:
            parameters = {'x': x, 'noise': 0.1}
            equation = (x ** 2 * sin(5 * pi * x) ** 6.0)
            yIter = self._objective(parameters=parameters, equation=equation)
            yIterList = list(yIter)
            yList.append(yIterList)
        y = asarray(yList)

        # reshape into rows and cols
        X = X.reshape(len(X), 1)
        y = y.reshape(len(y), 1)

        # Define the model
        model = GaussianProcessRegressor()  # KNeighborsClassifier()
        # fit the model
        model.fit(X, y)

        # Plot before hand
        self._plot(X, y, model)

        # perform the optimization process
        for i in range(100):
            # Select the next point to sample
            x = self._opt_acquisition(X, model)
            # Objective Function: sample the point
            parameters = {'x': x, 'noise': 0.1}
            equation = (x ** 2 * sin(5 * pi * x) ** 6.0)
            actual = self._objective(parameters=parameters, equation=equation)
            # Summarize the finding
            est, _ = self._surrogate(model, [[x]])

            # Result history: found data.
            print('>x=%.3f, f()=%3f, actual=%.3f' % (x, est, actual))
            # add the data to the dataset
            X = vstack((X, [[x]]))
            y = vstack((y, [[actual]]))
            # update the model
            model.fit(X, y)

        # plot all samples and the final surrogate function
        self._plot(X, y, model)
        # best result
        ix = argmax(y)
        # Note: Nearest Neighbor by access next.
        tokenStr = ('Best Result: x=%.3f, y=%.3f' % (X[ix], y[ix]))
        return tokenStr


if __name__ == '__main__':
    """Performs execution delta of the process."""
    p = datetime.datetime.now()
    try:
        print("")
    except Exception as e:
        print("Fail End Process: ", e)
        traceback.print_exc()
    q = datetime.datetime.now()
    print("Execution time: " + str(q - p))
