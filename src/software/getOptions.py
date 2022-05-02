#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Tyler Woods, Joseph Tarango
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import optparse


def GetParser():
    # todo: fwbuilddir might need to be updated to default='arbordaleplus_t2' or similar, to integrate new t2 compiler options

    #### Command-line arguments ####
    parser = optparse.OptionParser(usage="usage: ")
    parser.add_option('--getTelemetryOptions', dest='getTelOpt', default='-d 1 sample.bin --nvme --debug=1', help='Pass the options that are passed to getTelemetry.py')
    parser.add_option('--parseTelemetryBinOptions', dest='parTelOpt', default='sample.bin -o sample --debug=1', help='Pass the options that are passed to parseTelemetryBin.py')
    parser.add_option('--ctypeautogenOptions', dest='ctypeOpt', help='Pass the options that are passed to ctypeautogen.py')
    parser.add_option('--pacManICOptions', dest='pacManOpt', default='--projdir arbordaleplus_ca --bin ./sample --verbose', help='Pass the options that are passed to getTelemetry.py')
    parser.add_option('--runtime', dest='runtime', default=0, help='time in seconds to run data collection')
    parser.add_option('--numIterations', dest='numIter', default=100, help='number of iterations of data collection to run')
    parser.add_option('--device', dest='device', default=1, help='device to profile')
    parser.add_option('--debug', dest='debug', default=1, help='debug level')
    parser.add_option('--ulink', metavar='on|off|pc', default='', help='ULINK Control: ON, OFF, or Power Cycle (OFF+ON)')
    parser.add_option('--nocreate', action='store_false', dest="createLog", default=True, help='Issue command with create bit = 0')
    parser.add_option('--hi', action='store_true', dest="hilog", default=True, help='Pull Host Initiated log (this is the default case)')
    parser.add_option('--ci', action='store_false', dest="hilog", help='Pull Controller Initiated log')
    parser.add_option('--v1', action='store_true', dest="version1", default=False, help='Version 1 pull (default = false)')
    parser.add_option('-b', '--blockSize', type='int', action='store', dest="readBlockSize", default=None, help='Read Block size in bytes(default = 4096)')
    parser.add_option('--block0Size', type='int', action='store', dest="readBlock0Size", default=None, help='Read Block 0 size in bytes(default = None)')
    parser.add_option('--tocreread', action='store_true', dest="doubleTOCRead", default=False, help='Do a double read and validate on the VU TOC (default = False)')
    parser.add_option('--sata', action='store_true', dest="sata", default=False, help='Perform SATA log page pull')
    parser.add_option('--nvme', action='store_false', dest="sata", help='Perform NVMe log page pull')
    parser.add_option('--fwbuilddir', dest='fwbuilddir', default='cdrefresh_da', help='directory for the firmware build. i.e. the project file in root/projects/objs that you are measuring and building for')
    parser.add_option('--objects', dest='objects', default=['ThermalSensor', 'ThermalStats'], help='List of objects to measure')
    parser.add_option("--prune", action='store_true', dest='prune', default='False', help='value whether to prune constant time series')
    parser.add_option("--time", dest='time', metavar='<TIME>', help='time to run time series')
    parser.add_option('--traindata', action='store_true', dest="traindata", help='If run is for data mining and training')
    parser.add_option("--label", dest='label', metavar='<LABEL>', default='json', help='label of run for training')
    parser.add_option("--traindest", dest='traindest', metavar='<TRAINDEST>', default='TrainingData', help='directory to store training data as a simple json file')
    parser.add_option("--infile", dest='infile', metavar='<infile>', help='file to input')
    parser.add_option("--outfile", dest='outfile', metavar='<outfile>', help='file to output')
    parser.add_option('--process', dest="process", metavar='<PROCESS>', default="ED", help='Process to perform on data before putting through neural network. Accepted inputs: ED, DTW, Pears')
    return parser.parse_args()
