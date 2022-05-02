# !/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Daniel Garces
# *****************************************************************************/
"""mediaErrorPredictor.py

This module contains the basic functions for loading the content of a configuration file and utilizing the ARMA model
to generate predictions on the time series values passed in as arguments into the main API

Args:
    --inputFile: String representation for the name of the configuration file where the time series data values for the
                 media are contained
    --targetObject: String representation for the name of the target object to be used for the prediction model
    --targetField: String representation of the name for the target field to be used for the prediction model
    --matrixProfile: Boolean flag to apply matrix profile to time series before using the ARMA model
    --subSeqLen: Integer for the length of the sliding window for matrix profile (only relevant if matrix profile flag
                 is set)
    --debug: Boolean flag to activate verbose printing for debug use

Example:
    Default usage:
        $ python mediaErrorPredictor.py
    Specific usage:
        $ python mediaErrorPredictor.py --inputFile time-series.ini --targetObject NandStats --targetField 01-biterrors
        --matrixProfile True --subSeqLen 20 --debug True


"""
import datetime, pprint, traceback, optparse, statistics, pandas, os
import src.software.mp.utils
import matplotlib.backends.backend_pdf as be
import src.software.DP.preprocessingAPI as DP
from pandas import concat, DataFrame
from matplotlib import pyplot
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.ar_model import AR
from sklearn.metrics import mean_squared_error


def add_value_labels(ax, spacing=5):
    """Add labels to the end of each bar in a bar chart.

    Arguments:
        ax (matplotlib.axes.Axes): The matplotlib object containing the axes
            of the plot to annotate.
        spacing (int): The distance between the labels and the bars.
    """

    # For each bar: Place a label
    for rect in ax.patches:
        # Get X and Y placement of label from rect.
        y_value = rect.get_height()
        x_value = rect.get_x() + rect.get_width() / 2

        # Number of points between bar and label. Change to your liking.
        space = spacing
        # Vertical alignment for positive values
        va = 'bottom'

        # If value of bar is negative: Place label below bar
        if y_value < 0:
            # Invert space to place label below
            space *= -1
            # Vertically align label at top
            va = 'top'

        # Use Y value as label and format number with one decimal place
        label = "{:.3f}".format(y_value)

        # Create annotation
        ax.annotate(
            label,  # Use `label` as label
            (x_value, y_value),  # Place label at end of the bar
            xytext=(0, space),  # Vertically shift label by `space`
            textcoords="offset points",  # Interpret `xytext` as offset in points
            ha='center',  # Horizontally center label
            va=va)  # Vertically align label differently for positive and negative values.


class MediaErrorPredictor(object):
    """
    Class for media failure prediction

    Attributes:
            inputFile: String representation for the name of the configuration file where all the data values are
                       contained
            debug: Boolean flag to activate debug statements
            dataDict: Dictionary with the object values from the ConfigParser
    """

    def __init__(self, inputFile, matrixProfile=False, subSeqLen=20, debug=False):
        """
        function for initializing the MediaErrorPredictor class

        Args:
            inputFile: String representation for the name of the configuration file where all the data values are
                       contained
            matrixProfile: Boolean flag to apply matrix profile to time series before using the ARMA model
            subSeqLen: Integer for the length of the sliding window for matrix profile (only relevant if matrix profile
                       flag is set)
            debug: Boolean flag to activate debug statements

        Returns:

        """
        self.inputFile = inputFile
        self.debug = debug
        self.dataDict = DP.preprocessingAPI().loadDataDict(inputFile, debug)
        self.matrixProfileFlag = matrixProfile
        if isinstance(matrixProfile, bool) and matrixProfile is True:
            self.MPDict = DP.preprocessingAPI.generateMP(self.dataDict, subSeqLen)
        else:
            self.MPDict = None
        self.isStationary = False

    def setMatrixProfileFlag(self, value, subSeqLen=20):
        if value:
            if self.MPDict is None:
                self.MPDict = DP.preprocessingAPI.generateMP(self.dataDict, subSeqLen)
        self.matrixProfileFlag = value

    def check_stationarity(self, timeseriesCandidate):
        """
        Augmented Dickey-Fuller (ADF) test can be used to test the null hypothesis that the series is non-stationary. The ADF test helps to understand whether a change in Y is a linear trend or not. If there is a linear trend but the lagged value cannot explain the change in Y over time, then our data will be deemed non-stationary. The value of test statistics is less than 5% critical value and p-value is also less than 0.05 so we can reject the null hypothesis and Alternate Hypothesis that time series is Stationary seems to be true. When there is nothing unusual about the time plot and there appears to be no need to do any data adjustments. There is no evidence of changing variance also so we will not do a Box-Cox transformation.
        Args:
            timeseriesCandidate: Time series

        Returns: Determination of whether the data is stationary or not?

        """
        # Early abandon exit for same exact values in series.
        if len(set(timeseriesCandidate)) == 1:
            return True

        pValueThreshold = 0.05
        result = adfuller(timeseriesCandidate, autolag='AIC')
        if self.debug:
            dfoutput = pandas.Series(result[0:4],
                                     index=['Test Statistic', 'p-value', '#Lags Used', 'Number of Observations Used'])
            print('The test statistic: %f' % result[0])
            print('p-value: %f' % result[1])
            print('Critical Values:')
            for key, value in result[4].items():
                print('%s: %.3f' % (key, value))
            pprint.pprint(dfoutput)
        if result[1] > pValueThreshold:
            return False
        else:
            return True

    def ARMAModel(self, currentObject, currentField, pdf=None):
        """
        function for using the ARMA model on a specified time-series and producing a graph comparing predicted values
        with expected values

        Args:
            pdf: file to save to PDF format.
            currentObject: String representation for the name of the object to be processed
            currentField: String representation for the name of the object's field to be processed

        Returns:

        """

        if self.matrixProfileFlag:
            timeSeries = self.MPDict[currentObject][currentField]
        else:
            timeSeries = self.dataDict[currentObject][currentField]

        if self.check_stationarity(timeseriesCandidate=timeSeries):
            self.isStationary = True
            return
        # Create lagged dataset for given timeSeries
        values = DataFrame(timeSeries)
        dataframe = concat([values.shift(1), values], axis=1)
        dataframe.columns = ['t-1', 't+1']

        # Split into train and test sets
        X = dataframe.values
        train_size = int(len(X) * 0.66)
        train, test = X[1:train_size], X[train_size:]
        train_X, train_y = train[:, 0], train[:, 1]
        test_X, test_y = test[:, 0], test[:, 1]

        # Persistence model on training set
        train_pred = [x for x in train_X]

        # Calculate residuals
        train_resid = [train_y[idx] - train_pred[idx] for idx, _ in enumerate(train_pred)]

        # Model the training set residuals
        model = AR(train_resid)
        model_fit = model.fit()
        window = model_fit.k_ar
        coef = model_fit.params

        # Walk forward over time steps in test
        history = train_resid[len(train_resid) - window:]
        history = [history[i] for i in range(len(history))]
        predictions = list()
        for t in range(len(test_y)):
            # Persistence
            yhat = test_X[t]
            error = test_y[t] - yhat

            # Predict Error
            length = len(history)
            lag = [history[i] for i in range(length - window, length)]
            pred_error = coef[0]
            for d in range(window):
                pred_error += coef[d + 1] * lag[window - d - 1]

            # Correct the Prediction
            yhat = yhat + pred_error
            predictions.append(yhat)
            history.append(error)
            print('predicted=%f, expected=%f' % (yhat, test_y[t]))

        # Error
        mse = mean_squared_error(test_y, predictions)
        print('Test MSE: %.3f' % mse)

        # Plot Predicted values without zoom
        fig1, ax1 = pyplot.subplots()
        ax1.plot(test_y, color="blue", label="Expected Value")
        ax1.plot(predictions, color='red', label="Predicted Value")
        ax1.set_title(currentObject + "-" + currentField + " (Standard)")
        ax1.set_xlabel("Time Stamp")
        ax1.set_ylabel("Count")
        ax1.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
        maxExpected = max(test_y)
        maxPredicted = max(predictions)
        ax1.set_ylim([0, 1.5 * max(maxExpected, maxPredicted)])
        fig1.tight_layout()

        if pdf is not None:
            pdf.savefig()
            pyplot.close()

        # Plot Predicted values with zoom
        fig2, ax2 = pyplot.subplots()
        ax2.plot(test_y, color="blue", label="Expected Value")
        ax2.plot(predictions, color='red', label="Predicted Value")
        ax2.set_title(currentObject + "-" + currentField + " (Zoom-in)")
        ax2.set_xlabel("Time Stamp")
        ax2.set_ylabel("Count")
        ax2.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
        fig2.tight_layout()

        if pdf is not None:
            pdf.savefig()
            pyplot.close()

        # Plot prediction error
        if self.matrixProfileFlag:
            testErrors = [((predictions[i] - test_y[i])) for i in range(len(test_y))]
        else:
            testErrors = [((predictions[i] - test_y[i]) / test_y[i]) * 100 for i in range(len(test_y))]
        fig3, ax3 = pyplot.subplots()
        ax3.plot(testErrors, color="orange", label="Difference predicted and expected")
        ax3.set_title(currentObject + "-" + currentField + " (Percentage Diff)")
        ax3.set_xlabel("Time Stamp")
        ax3.set_ylabel("Percentage Difference (%)")
        ax3.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
        fig3.tight_layout()

        if pdf is not None:
            pdf.savefig()
            pyplot.close()

        # Plot prediction error metrics
        testErrors = list(map(abs, testErrors))
        relevantStats = list()
        meanCal, stdCal = software.mp.utils.util_calculateMeanStd(testErrors)
        relevantStats.append(meanCal)
        relevantStats.append(statistics.median(testErrors))
        relevantStats.append(stdCal)
        relevantStats.append(max(testErrors))
        relevantStats.append(min(testErrors))
        succesfulClassifications = 0
        for i in range(len(testErrors)):
            if self.matrixProfileFlag:
                if testErrors[i] <= 0.05:
                    succesfulClassifications += 1
            else:
                if testErrors[i] <= (test_y[i] * 0.05) / test_y[i]:
                    succesfulClassifications += 1
        relevantStats.append(succesfulClassifications / len(testErrors))
        relevantStatsLabels = ['Mean', 'Median', 'StDev', 'Max', 'Min', 'Accuracy']
        relevantStatsCoordinates = [1, 2, 3, 4, 5, 6]

        fig4, ax4 = pyplot.subplots()
        ax4.bar(relevantStatsCoordinates, relevantStats, 0.8, tick_label=relevantStatsLabels)
        add_value_labels(ax4)
        ax4.set_title(currentObject + "-" + currentField + " (Diff Relevant Stats)")
        ax4.set_xlabel("Metric Name")
        ax4.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
        fig4.tight_layout()

        if pdf is None:
            pyplot.show()
        else:
            pdf.savefig()
        pyplot.close()
        return True

    def writeARMAToPDF(self, targetObject, targetField, outFile=None):
        """

        Args:
            outFile:
            targetObject:
            targetField:

        Returns:

        """
        if self.isStationary:
            return None

        # Determine if the data is changing
        if self.matrixProfileFlag:
            timeSeries = self.MPDict[targetObject][targetField]
        else:
            timeSeries = self.dataDict[targetObject][targetField]
        if self.check_stationarity(timeseriesCandidate=timeSeries):
            self.isStationary = True
            return None

        if outFile is None:
            pdfFile = "ARMA_" + targetObject + "_" + targetField + ".pdf"
        else:
            pdfFile = outFile
        if not os.path.exists(path=pdfFile):
            os.makedirs(pdfFile, mode=0o777, exist_ok=True)
        with be.PdfPages(pdfFile) as pp:
            self.ARMAModel(currentObject=targetObject, currentField=targetField, pdf=pp)

        return pdfFile

    def predictorAPI(self, targetObject, targetField):
        """
        API to replace standard command line call (the MediaErrorPredictor class has to instantiated before calling
        this method).

        Args:
            targetObject: String representation for the name of the object to be processed
            targetField: String representation for the name of the object's field to be processed

        Returns:

        """

        self.ARMAModel(targetObject, targetField)


def main():
    """
        main function to be called when the script is directly executed from the
        command line
    """
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--inputFile",
                      dest='inputFile',
                      default=None,
                      help='Name for the configuration file where the time series data values for the media '
                           'errors are contained')
    parser.add_option("--targetObject",
                      dest='targetObject',
                      default=None,
                      help='Name for the target object to be used for the prediction model')
    parser.add_option("--targetField",
                      dest='targetField',
                      default=None,
                      help='Name for the target field to be used for the prediction model')
    parser.add_option("--matrixProfile",
                      dest='matrixProfile',
                      default=None,
                      help='Boolean flag to apply matrix profile to time series before using the ARMA model')
    parser.add_option("--subSeqLen",
                      dest='subSeqLen',
                      default=None,
                      help='Integer for the length of the sliding window for matrix profile (only relevant if matrix '
                           'profile flag is set)')
    parser.add_option("--debug",
                      dest='debug',
                      default=False,
                      help='Verbose printing for debug use')
    (options, args) = parser.parse_args()

    ##############################################
    # Main
    ##############################################
    if options.inputFile is None:
        inputFile = "MediaErrorRateoverTime.ini"
    else:
        inputFile = options.inputFile

    if options.targetObject is None:
        targetObject = "NandStats"
    else:
        targetObject = options.targetObject

    if options.targetField is None:
        targetField = "01-biterrors"
    else:
        targetField = options.targetField

    if options.debug == "True":
        debug = True
    else:
        debug = False

    if options.matrixProfile == "True":
        matrixProfile = True
    else:
        matrixProfile = False

    if options.subSeqLen is None:
        subSeqLen = 20
    else:
        subSeqLen = int(options.subSeqLen)

    MEP = MediaErrorPredictor(inputFile=inputFile, matrixProfile=matrixProfile, subSeqLen=subSeqLen, debug=debug)
    MEP.predictorAPI(targetObject, targetField)

    return 0


if __name__ == '__main__':
    """Performs execution delta of the process."""
    pStart = datetime.datetime.now()
    try:
        main()
    except Exception as errorMain:
        print("Fail End Process: {0}".format(errorMain))
        traceback.print_exc()
    qStop = datetime.datetime.now()
    print("Execution time: " + str(qStop - pStart))
