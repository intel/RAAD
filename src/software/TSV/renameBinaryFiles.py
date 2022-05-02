# !/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Daniel Garces, Joseph Tarango
# *****************************************************************************/
"""renameBinaryFiles.py

This module contains the basic functions for renaming the previously collected binaries so their names
follow the UTC convention required for the time series generation

Args:
    --inputDir: String for the path of the input directory where the binaries to be renamed are stored
    --debug: Boolean flag to activate debug statements

Example:
    Default usage:
        $ python renameBinaryFiles.py
    Specific usage:
        $ python renameBinaryFiles.py --inputDir ./AllBinaries --debug True

"""

# from __future__ import absolute_import, division, print_function, unicode_literals
# from __future__ import nested_scopes, generators, generator_stop, with_statement, annotations
import os, traceback, datetime, optparse


def checkInputDir(inputDir):
    """
    function to set the default value for inputDir

    Args:
        inputDir: String of the path to the directory where the binaries are stored

    Returns:
        String representation of the path to the input directory

    """
    if inputDir is None:
        return "input-binaries"
    else:
        return inputDir


def renameFiles(inputDir="input-binaries", debug=False):
    """
    function for renaming all files in a given directory following the UTC convention

    Args:
        inputDir: path to the input directory where all the binary files to be renamed are stored

    Returns:

    """
    folder = os.path.join(os.getcwd(), inputDir)
    if os.path.exists(folder) and os.path.isdir(folder):
        os.chdir(folder)
        presentDir = os.getcwd()
        for fileName in os.listdir(presentDir):
            candidate = os.path.join(presentDir, fileName)
            if os.path.isfile(candidate):
                if debug is True:
                    print("Processing: " + candidate)
                nameElements = fileName.replace(".bin", "").split("_")
                if nameElements[0].isdigit():
                    date = datetime.datetime.strptime(nameElements[0][0: 20], '%Y%m%d%H%M%S%f')
                    dateString = date.strftime("%Y-%m-%d-%H-%M-%S-%f")
                    newName = nameElements[1] + "-" + nameElements[2] + "_" + dateString + ".bin"
                    if debug is True:
                        print("New name: " + newName)
                    os.rename(fileName, newName)


def checkDebugOption(debugOptions):
    """
    function to set the default value for debugOptions and turn it from
    a string into a boolean value

    Args:
        debugOptions: string representation of boolean value for debug flag

    Returns:
        Boolean value for debug flag

    """
    if debugOptions is None:
        return False
    elif debugOptions == "True":
        return True
    else:
        return False


def main():
    """
        main function to be called when the script is directly executed from the
        command line
    """
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--inputDir",
                      dest='inputDir',
                      default=None,
                      help='Path of the directory containing the binary files to be renamed')
    parser.add_option("--debug",
                      dest='debug',
                      default=False,
                      help='Verbose printing for debug use')
    (options, args) = parser.parse_args()

    ##############################################
    # Main
    ##############################################
    inputDir = checkInputDir(options.inputDir)
    debug = checkDebugOption(options.debug)
    renameFiles(inputDir, debug)


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
