# !/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Daniel Garces, Joseph Tarango
# *****************************************************************************/
""" configToText.py

This module contains the basic functions for turning a configuration file into multiple the plain text files
that each contain a single object structure to be turned back agin into its binary representation.
The plain text files have .txt suffix, while the configuration file has .ini suffix

Args:
     --inputFile: String of the name for the configuration file containing the data for the time-series
     --iterations: Integer number of data points to be considered in the time series
     --identifier: String for the name of the data set that corresponds to the telemetry pull to be executed
     --debug: Boolean flag to activate debug statements

Example:
    Default usage:
        $ python configToText.py
    Specific usage:
        $ python configToText.py --inputFile time-series.ini --iterations 100 --identifier Tv2HiTAC --debug True

"""
import sys
import datetime
import traceback
import optparse
import utilityTSV
import src.software.DP.preprocessingAPI as DP

if sys.version_info.major > 2:
    import configparser as cF
else:
    import ConfigParser as cF


class configToText(object):
    def __init__(self, debug=False):
        """
        function for initializing a configToText structure

        Args:
            debug: Boolean flag to activate debug statements

        Attributes:
            debug: Boolean flag to activate debug statements

        """
        self.debug = debug

    def getDebug(self):
        """
        function for reading the debug flag stored in the visualizeTS attributes

        Returns:
            Boolean flag to activate debug statements

        """
        return self.debug

    def setDebug(self, debug):
        """
        function for setting the debug flag stored in the visualizeTS attributes

        Args:
            debug: Boolean flag to activate debug statements

        Returns:

        """
        self.debug = debug

    def generateTextFromDict(self, tempDict, accumStr, indentLevel, index):
        """
        Recursive function to process a single entry of the expanded dictionary and turn it into a plain text line

        Args:
            tempDict: Expanded dictionary containg the fields for an object
            accumStr: String storing the lines processed so far
            indentLevel: Integer indicating the nesting level of the current line
            index: Integer for the index of the current stamp in the time-series

        Returns:
            String of the lines processed so far

        """
        for key in sorted(tempDict.keys()):
            for i in range(indentLevel):
                accumStr += "   "
            if isinstance(tempDict[key], dict):
                accumStr += key + "   :   \n"
                accumStr = self.generateTextFromDict(tempDict[key], accumStr, indentLevel+1, index)
            elif isinstance(tempDict[key], list):
                accumStr += key + "   :   " + str(tempDict[key][index]) + "\n"
            else:
                accumStr += key + "   :   " + str(tempDict[key]) + "\n"
        return accumStr

    def generateTextFromConfigFile(self, inputFile="time-series.ini", identifier="Tv2HiTAC", iterations=100):
        """
        function for turning a configuration file into multiple plain text files, each containing all the objects for
        a single time stamp in the time-series of the configuration file

        Args:
            inputFile: String of the path to the configuration file to be used for processing
            identifier: String of the identifier for the name of the plain text files

        Returns:

        """
        endString = "\n################################################################################################################\n"
        config = cF.ConfigParser()
        config.read(inputFile)
        intermediateDict = DP.preprocessingAPI.loadConfigIntoDict(config, True)
        resultDict = DP.preprocessingAPI.transformDict(intermediateDict, True)
        for i in range(iterations):
            currentTimeUTCString = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f")
            outFile = identifier + "-" + str(i) + "_" + currentTimeUTCString + ".txt"
            openFile = open(outFile, "w+")
            for key in resultDict.keys():
                objectDict = resultDict[key]
                name = resultDict[key]["name"]
                ref = resultDict[key]["ref"]
                minor = resultDict[key]["minor"][i]
                major = resultDict[key]["major"][i]
                uid = resultDict[key]["uid"]
                data_area = resultDict[key]["data-area"][i]
                byte_size = resultDict[key]["byte-size"][i]
                core = resultDict[key]["core"][i]
                titleStr = "\n %s, Core   %s, Uid   %s, Major   %s, Minor   %s, Data Area   %s, byte Size   %s,  %s \n"\
                            % (name, core, uid, major, minor, data_area, byte_size, ref)
                tempStr = ""
                tempStr = self.generateTextFromDict(objectDict, tempStr, indentLevel=0, index=i)
                if self.debug:
                    print("Signature: " + titleStr)
                openFile.write(endString)
                openFile.write(titleStr)
                openFile.write(endString)
                openFile.write(tempStr)
            openFile.close()


def main():
    """
        main function to be called when the script is directly executed from the
        command line
    """
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--identifier",
                      dest='identifier',
                      default=None,
                      help='Name of the data set that corresponds to the telemetry pull to be executed')
    parser.add_option("--inputFile",
                      dest='inputFile',
                      default=None,
                      help='Path of the file containing the config that describes the DefragHistory time series')
    parser.add_option("--iterations",
                      dest='iterations',
                      default=None,
                      help='Number of data points to be considered in the time series')
    parser.add_option("--debug",
                      dest='debug',
                      default=False,
                      help='Verbose printing for debug use')
    (options, args) = parser.parse_args()

    ##############################################
    # Main
    ##############################################
    input_t = utilityTSV.utilityTSV().checkInputFile(options.inputFile)
    debug = utilityTSV.utilityTSV().checkDebugOption(options.debug)
    identifier = utilityTSV.utilityTSV().checkIdentifier(options.identifier)
    iterations = utilityTSV.utilityTSV().checkIterations(options.iterations)

    viz = configToText(debug=debug)
    viz.generateTextFromConfigFile(inputFile=input_t, identifier=identifier, iterations=iterations)

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
