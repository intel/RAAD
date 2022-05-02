#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
"""NNStateBasedProcessing.py
This module contains the basic functions for state based batching of NNs.
"""
import datetime
import optparse
import traceback
import os
import pprint


class BigDataProcessing(object):

    def __init__(self, debug=False, dataFilesList=None, partitionSize=2 ** 16, machineLearningTechnique=None):
        self.debug = debug
        self.dataFilesList = dataFilesList
        self.partitionSize = partitionSize

        # State Machine Updates
        self.previousState = self.stateDictionary('default')
        self.nextState = self.stateDictionary('default')
        self.currentState = self.stateDictionary('state-init')

        # Used to process the data list
        self.currentFile = None
        self.actualFileList = []
        self.dataFileListEmpty = None
        self.machineLearningTechnique = None

        # Neural Network Snapshot
        self.neuralNetworkSnapshotFile = None

        # Multi-Thread
        self.parallelProcesses = None
        self.pendingThreads = None
        self.nextThreads = None
        self.workThreadPendingQueue = None
        self.workThreadContainers = None  # 1024
        self.workThreadCompletionQueue = None

        # Errors in processing.
        self.errorSignature = None
        self.errorFileList = []

    @staticmethod
    def stateDictionary(state):
        # Current -> Next State
        DFA_States = {
            0: 'default',
            # System initialization.
            1: 'state-init',
            # System parameter setup.
            2: 'state-setup',
            # Process the data based on the format, determine batch processing magnitude, and prepare checklists.
            3: 'state-determine_raw_data',
            # Batch pre-process data
            4: 'state-read_raw_data',

            5: 'state-partition_raw_data',
            6: 'state-partition_split_raw_data',
            7: 'state-continue_preprocess_raw_data',
            8: 'state-machine_learning_preprocessing',
            9: 'state-machine_learning_generate_partition',
            10: 'state-neural_network_model_prepare',
            11: 'state-configure_datasets',
            12: 'state-neural_network_frame_load',
            13: 'state-neural_network_process',
            14: 'state-neural_network_snapshot',
            15: 'state-plot_performance_metrics',
            16: 'state-generate_graphs'
        }
        DFA_States_Reverse = {v: k for k, v in DFA_States.items()}
        if state is None:
            return DFA_States['default']
        if isinstance(state, int) and state in DFA_States:
            return DFA_States[state]
        elif isinstance(state, str) and state in DFA_States_Reverse:
            return DFA_States_Reverse[state]
        else:
            return DFA_States['default']

    # State machine functions take in their current state as an argument and return the next state.
    def FSM_Transitions(self, state):
        # State machine transitions
        if state is self.stateDictionary('default'):
            nextState = self.stateDictionary('state-init')

        elif state is self.stateDictionary('state-init'):
            nextState = self.stateDictionary('state-setup')

        elif state is self.stateDictionary('state-setup'):
            nextState = self.stateDictionary('state-determine_raw_data')

        elif state is self.stateDictionary('state-determine_raw_data'):
            if self.currentFile.endswith('.ini'):
                print("Detect INI Data")
            elif self.currentFile.endswith('.cvs'):
                print("Detect CVS Data")
            else:
                self.errorSignature = f"Invalid file {self.currentFile}"
            nextState = -1

        elif state is self.stateDictionary('state-read_raw_data'):
            if self.currentFile.endswith('.ini'):
                print("Read INI Data")
            elif self.currentFile.endswith('.cvs'):
                print("Read CVS Data")
            nextState = -1

        elif state is self.stateDictionary('state-partition_raw_data'):
            if self.fileSize(self.currentFile) > self.partitionSize:
                nextState = self.stateDictionary('state-partition_split_raw_data')
            else:
                nextState = -1

        elif state is self.stateDictionary('state-partition_split_raw_data'):
            nextState = -1

        elif state is self.stateDictionary('state-continue_preprocess_raw_data'):
            nextState = -1

        elif state is self.stateDictionary('state-machine_learning_preprocessing'):
            nextState = -1

        elif state is self.stateDictionary('state-machine_learning_generate_partition'):
            nextState = -1

        elif state is self.stateDictionary('state-neural_network_model_prepare'):
            nextState = -1

        elif state is self.stateDictionary('state-configure_datasets'):
            nextState = -1

        elif state is self.stateDictionary('state-neural_network_frame_load'):
            nextState = -1

        elif state is self.stateDictionary('state-neural_network_process'):
            nextState = -1

        elif state is self.stateDictionary('state-neural_network_snapshot'):
            nextState = -1

        elif state is self.stateDictionary('state-plot_performance_metrics'):
            nextState = -1

        elif state is self.stateDictionary('state-generate_graphs'):
            nextState = -1

        else:
            nextState = -1

        return nextState

    def FSM_Action(self, state):
        # State Machine Actions
        if self.debug:
            print(f'Action State: {state}')

        if state is self.stateDictionary('default'):
            if self.debug:
                print('Default State')
        elif state is self.stateDictionary('state-setup'):
            state = -1
        elif state is self.stateDictionary('state-determine_raw_data'):
            state = -1
        elif state is self.stateDictionary('state-read_raw_data'):
            state = -1
        elif state is self.stateDictionary('state-partition_raw_data'):
            state = -1
        elif state is self.stateDictionary('state-partition_split_raw_data'):
            state = -1
        elif state is self.stateDictionary('state-continue_preprocess_raw_data'):
            state = -1
        elif state is self.stateDictionary('state-machine_learning_preprocessing'):
            state = -1
        elif state is self.stateDictionary('state-machine_learning_generate_partition'):
            state = -1
        elif state is self.stateDictionary('state-neural_network_model_prepare'):
            state = -1
        elif state is self.stateDictionary('state-configure_datasets'):
            state = -1
        elif state is self.stateDictionary('state-neural_network_frame_load'):
            state = -1
        elif state is self.stateDictionary('state-neural_network_process'):
            state = -1
        elif state is self.stateDictionary('state-neural_network_snapshot'):
            state = -1
        elif state is self.stateDictionary('state-plot_performance_metrics'):
            state = -1
        elif state is self.stateDictionary('state-generate_graphs'):
            state = -1
        else:
            state = -1
        return state

    def updateState(self):
        self.previousState = self.currentState
        self.currentState = self.nextState
        return

    def fileSize(self, currentFile):
        pass


def main():
    """
        main function to be called when the script is directly executed from the
        command line
    """
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--inFile",
                      dest='inFile',
                      default=None,
                      help='Path for the input CSV file separated by spaces.')
    parser.add_option("--outFile",
                      dest='outFile',
                      default=None,
                      help='Path for the tab separated format file where the time series ini')
    parser.add_option("--targetObject",
                      dest='targetObject',
                      default=None,
                      help='Data set name for the section field.')
    parser.add_option("--debug",
                      dest='debug',
                      default=False,
                      help='Verbose printing for debug use')
    (options, args) = parser.parse_args()

    ##############################################
    # Main
    ##############################################
    if (options.inFile is None):
        inFile = "time-series_media.csv"
        if not os.path.exists(os.path.abspath(inFile)):
            return 1
    else:
        inFile = options.inFile

    if (options.outFile is None):
        outFile = "time-series_media.ini"
    else:
        outFile = options.inFile

    if options.debug is True:
        debug = True
    else:
        debug = False

    if options.targetObject is not None:
        targetObject = options.targetObject
    else:
        targetObject = 'MEDIA_MADNESS'

    print("Column List:")
    pprint.pprint("Hi")
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
