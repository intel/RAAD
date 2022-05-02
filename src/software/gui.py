#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Daniel Garces
# *****************************************************************************/
# @package gui
import optparse, datetime, traceback, pprint
# import hashlib, time, base64
# from Crypto.Cipher import AES
# from Crypto.Hash import SHA256
# from Crypto import Random

# Pass any command line argument for Web use
# if web is False:  # default uses the tkinter GUI
# import PySimpleGUI
# import PySimpleGUIWeb as PySimpleGUI
# else:  # if there is use the Web Interface
#    import remi
#    import PySimpleGUIWeb as PySimpleGUI
import src.software.TSV.generateTSBinaries
import src.software.TSV.formatTSFiles
import src.software.axon.packageInterface
import src.software.axon.axonInterface
import src.software.axon.axonMeta
import src.software.axon.axonProfile
import src.software.access.DriveInfo
import src.software.container.basicTypes
import src.software.guiLayouts
import src.software.guiCommon
import src.software.guiOneShot
import src.software.guiDeveloper
import src.software.guiTests
from src.software.debug import whoami


def API(options=None):
    """
    API for the default application in the graphical interface.
    Args:
        options: Commandline inputs.
    Returns:
    """
    if options.debug:
        print("Options are:\n{0}\n".format(options))
    ###############################################################################
    # Graphical User Interface (GUI) Configuration
    ###############################################################################
    print("options: ", str(options.mode))

    if options.mode.isnumeric():
        if int(options.mode) in [1, 2, 3]:
            src.software.guiDeveloper.GUIDeveloper(debug=options.debug).webAPI()  # Default simple one API
        elif int(options.mode) == 2:
            guiObj = src.software.guiLayouts.GUILayouts()
            guiObj.tabAPI()  # Tab based API
        elif int(options.mode) == 3:
            # Generic layouts for all APIs
            guiObj = src.software.guiLayouts.GUILayouts()
            guiObj.collect()
            guiObj.defragHistoryGraph()
            guiObj.RNNPredictorGraph()
            guiObj.ARMAPredictionGraph()
            guiObj.neuralNetClassify()
            guiObj.upload()
            guiObj.download()
            guiObj.profileUser()
            guiObj.profileApplication()
            guiObj.userFeedback()
            guiObj = src.software.guiLayouts.GUILayouts()
            guiObj.debugComments(displayInput=pprint.pformat(locals(), indent=3, width=100))
            # Data Table Objects
            src.software.guiLayouts.GUILayouts().objectTimeSeriesVisualizer()
            src.software.guiLayouts.dataTablePopulate()
        elif int(options.mode) == 4:
            src.software.guiOneShot.GUIOneShot(debug=False).Window()  # Tab based API
        elif int(options.mode) == 5:
            src.software.guiOneShot.GUIOneShot(debug=False).OneShotExecuteAPI()
        else:
            print("Error in Selection Numeric")
            pprint.pprint(whoami())
            src.software.guiDeveloper.GUIDeveloper(debug=options.debug).webAPI()  # Default simple one API

    if options.mode == "Test":
        src.software.guiTests.API(options)
    else:
        print("Error in Selection String")
        pprint.pprint(whoami())
        src.software.guiDeveloper.GUIDeveloper(debug=options.debug).webAPI()  # Default simple one API


def main():
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--example", action='store_true', dest='example', default=False,
                      help='Show command execution example.')
    parser.add_option("--debug", action='store_true', dest='debug', default=True, help='Debug mode.')
    parser.add_option("--more", dest='more', default=False, help="Displays more options.")
    parser.add_option("--mode", dest='mode', default="1", help="Mode of Operation.")
    (options, args) = parser.parse_args()

    ##############################################
    # Main
    ##############################################
    API(options)
    return 0


if __name__ == '__main__':
    """Performs execution delta of the process."""
    p = datetime.datetime.now()
    try:
        main()
    except Exception as e:
        print("Fail End Process: ", e)
        traceback.print_exc()
    q = datetime.datetime.now()
    print("Execution time: " + str(q - p))
