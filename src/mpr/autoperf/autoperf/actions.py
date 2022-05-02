#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Brad McDonald, Mejbah ul Alam, Justin Gottschlich, Abdullah Muzahid
# *****************************************************************************/
"""actions.py

Actions triggered by user input in __main__.py.
"""

import os
import sys
import shutil
import subprocess
import time
import logging
import pprint
from tempfile import TemporaryFile

import numpy as np
from rich.progress import TimeElapsedColumn, BarColumn, Progress, track
from tqdm.rich import tqdm
from tensorflow.keras.utils import plot_model
from autoperf.autoperf import getPerfDataset, preprocessDataArray, getDatasetArray, \
    getReconstructionErrors, testModel, testAnomaly, writeTestLog
from autoperf import keras_autoencoder
from autoperf.config import loadConfig_TryDetect, Config
from autoperf.counters import get_num_counters
from autoperf.utils import getAutoperfDir, set_working_directory
from autoperf.plots import plot_histograms

log = logging.getLogger('rich')


def runDetect(nominal_dir: str, anomalous_dir: str):
    """Detect performance anomalies in the current branch.

    Args:
        nominal_dir: Nominal data directory
        anomalous_dir: Anomalous data directory
    """
    autoencoder = keras_autoencoder.loadTrainedModel()

    nominalRuns = os.listdir(nominal_dir)
    nominalDataset = list()
    for run in track(nominalRuns, description='Loading Training Data', transient=True):
        datadir = os.path.join(nominal_dir, run)
        _, dataset = getPerfDataset(datadir, get_num_counters())
        dataArray = preprocessDataArray(getDatasetArray(dataset))
        nominalDataset.extend(list(dataArray))
    nominalDataset = np.array(nominalDataset)

    anomalousRuns = os.listdir(anomalous_dir)
    anomalousDataset = list()
    for run in track(anomalousRuns, description='Loading Testing Data ', transient=True):
        datadir = os.path.join(anomalous_dir, run)
        _, dataset = getPerfDataset(datadir, get_num_counters())
        dataArray = preprocessDataArray(getDatasetArray(dataset))
        anomalousDataset.extend(list(dataArray))
    anomalousDataset = np.array(anomalousDataset)

    nominalTestErrors = getReconstructionErrors(nominal_dir, autoencoder)
    anomalousTestErrors = getReconstructionErrors(anomalous_dir, autoencoder)
    thresholdError = np.load(getAutoperfDir('threshold.npy'))[0]

    log.info('%d NOM reconstruction errors above threshold', np.sum(nominalTestErrors > thresholdError))
    log.info('%d ANOM reconstruction errors above threshold', np.sum(anomalousTestErrors > thresholdError))

    plot_histograms(test_nom=np.array(nominalTestErrors),
                    test_anom=np.array(anomalousTestErrors),
                    threshold=thresholdError,
                    flipped_axes=True)

    keras_autoencoder.visualizeLatentSpace(autoencoder, nominalDataset, anomalousDataset)
    return


def runEvaluate(train_dir: str, nominal_dir: str, anomalous_dir: str, debug: bool = False):
    """Evaluate the trained autoEncoderObj with various datasets.

    Args:
        train_dir: Training data directory
        nominal_dir: Nominal data directory
        anomalous_dir: Anomalous data directory
        debug: flag to turn on debug printing
    """
    autoencoder = keras_autoencoder.loadTrainedModel()

    trainRuns = os.listdir(train_dir)
    trainDataset = list()
    for run in trainRuns:
        datadir = os.path.join(train_dir, run)
        _, dataset = getPerfDataset(datadir, get_num_counters())
        dataArray = preprocessDataArray(getDatasetArray(dataset))
        trainDataset.extend(list(dataArray))
    trainDataset = np.array(trainDataset)
    if debug:
        pprint.pprint(trainDataset)

    nominalRuns = os.listdir(nominal_dir)

    nominalDataset = list()
    for run in nominalRuns:
        datadir = os.path.join(nominal_dir, run)
        _, dataset = getPerfDataset(datadir, get_num_counters())
        dataArray = preprocessDataArray(getDatasetArray(dataset))
        nominalDataset.extend(list(dataArray))
    nominalDataset = np.array(nominalDataset)
    if debug:
        pprint.pprint(nominalDataset)

    anomalousRuns = os.listdir(anomalous_dir)
    anomalousDataset = list()
    for run in anomalousRuns:
        datadir = os.path.join(anomalous_dir, run)
        _, dataset = getPerfDataset(datadir, get_num_counters())
        dataArray = preprocessDataArray(getDatasetArray(dataset))
        anomalousDataset.extend(list(dataArray))
    anomalousDataset = np.array(anomalousDataset)
    if debug:
        pprint.pprint(anomalousDataset)

    log.info('Collecting reconstruction errors for [training] data:')
    trainTestErrors = getReconstructionErrors(train_dir, autoencoder)
    log.info('Collecting reconstruction errors for [nominal test] data:')
    nominalTestErrors = getReconstructionErrors(nominal_dir, autoencoder)
    log.info('Collecting reconstruction errors for [anomalous test] data:')
    anomalousTestErrors = getReconstructionErrors(anomalous_dir, autoencoder)

    thresholdError = np.load(getAutoperfDir('threshold.npy'))[0]

    plot_histograms(train=np.array(trainTestErrors),
                    test_nom=np.array(nominalTestErrors),
                    test_anom=np.array(anomalousTestErrors),
                    threshold=thresholdError)

    with open(getAutoperfDir('report'), 'w') as report:
        test_result = testModel(autoencoder, thresholdError, nominal_dir, anomalous_dir, report)

        imageFile = getAutoperfDir('model_architecture.png')
        plot_model(autoencoder, to_file=imageFile, show_shapes=True, show_layer_names=True)

        print('\nConfusion Matrix: |  P  |  N  |', file=report)
        print('                P |{:^5}|{:^5}|'.format(test_result.true_positive, test_result.false_positive), file=report)
        print('                N |{:^5}|{:^5}|'.format(test_result.false_negative, test_result.true_negative), file=report)

        # calculate F score
        precision = 0
        if test_result.true_positive + test_result.false_positive != 0:
            precision = test_result.true_positive / (test_result.true_positive + test_result.false_positive)

        recall = test_result.true_positive / (test_result.true_positive + test_result.false_negative)
        fscore = 0
        if precision + recall != 0:
            fscore = 2 * (precision * recall) / (precision + recall)  # harmonic mean of precision and recall

        print("\nPrecision: ", precision, file=report)
        print("Recall: ", recall, file=report)
        print("Fscore: ", fscore, file=report)
    return


def runClean(cfg: Config = None):
    """Cleans the codebase using the user-specified instructions."""
    if cfg is None:
        cfg = loadConfig_TryDetect()
    with set_working_directory(cfg.build.dir), TemporaryFile('w+') as file:
        with Progress('[bright_magenta][progress.description]{task.description}[/bright_magenta]',
                      BarColumn(), '[', TimeElapsedColumn(), ']', transient=True) as progress:
            task = progress.add_task('Cleaning', start=False)
            from autoperf.utils import callCommand
            errorString = callCommand(cmd=cfg.clean.cmd,
                                      cwd=cfg.build.dir,
                                      env=os.environ.copy(),
                                      stdout=file, stderr=subprocess.STDOUT)

            if errorString != '':
                ExceptionOccurred = True
                log.error(f'Clean command failed.{os.linesep}{errorString}')
                file.seek(0)
                print(file.read())
                sys.exit(1)
            progress.update(task, total=0, start=True, description='Cleaning (Finished)')
            progress.start_task(task)
    return


def runBuild(cfg: Config = None):
    """Builds the code using the user-specified instructions.
        cfg:
    """
    if cfg is None:
        from autoperf.config import loadConfig_TryDetect
        cfg = loadConfig_TryDetect()
    with set_working_directory(cfg.build.dir), TemporaryFile('w+') as file:
        if cfg.clean.cmd:
            runClean(cfg=cfg)
        with Progress('[bright_magenta][progress.description]{task.description}[/bright_magenta]',
                      BarColumn(), '[', TimeElapsedColumn(), ']') as progress:
            task = progress.add_task('Building', start=False)
            from autoperf.utils import callCommand
            errorString = callCommand(cmd=cfg.build.cmd,
                                      cwd=cfg.build.dir,
                                      env=os.environ.copy(),
                                      stdout=file,
                                      stderr=subprocess.STDOUT)
            if errorString != '':
                log.error(f'Build command failed.{os.linesep}{errorString}')
                file.seek(0)
                print(file.read())
                sys.exit(1)

            progress.update(task, total=0, start=True, description='Building (Finished)')
            progress.start_task(task)
    return


def runWorkload(out_dir: str, run_count: int, filePerfData: str = "perf_data.csv", fileCounters: str = 'COUNTERS', cfg: Config = None):
    """Runs a specified workload and collects HPC measurements.

    Args:
        out_dir: Directory in which to save the measurements
        run_count: Run index (used for file names)
        filePerfData: Performance data file logs.
        fileCounters: Performance counters file.
        cfg:
    """
    # File prefix is: run_*
    currOutputDirName = f'{out_dir}/run_{run_count}'
    os.makedirs(currOutputDirName, exist_ok=True)
    if cfg is None:
        cfg = loadConfig_TryDetect()

    # fileCounterExactLocation = os.path.abspath(os.path.join(out_dir, fileCounters))
    fileCounterExactLocation = os.path.abspath(os.path.join(currOutputDirName, fileCounters))
    with set_working_directory(cfg.workload.dir):
        fileCountersLocation = os.path.join(cfg.build.dir, ".autoperf", fileCounters)
        print(os.path.abspath(fileCountersLocation))
        print(os.path.abspath(fileCounters))
        shutil.copyfile(fileCountersLocation, fileCounterExactLocation)

        log.info('Saving hardware telemetry data to %s', currOutputDirName)
        for i in tqdm(range(0, get_num_counters(cfg))):
            os.environ["PERFPOINT_EVENT_INDEX"] = str(i)
            from autoperf.utils import callCommand
            start_time = time.perf_counter()
            errorString = callCommand(cmd=cfg.workload.cmd,
                                      cwd=cfg.build.dir,
                                      env=os.environ.copy(),
                                      stdout=subprocess.DEVNULL,
                                      stderr=subprocess.STDOUT)
            if errorString != '':
                log.error(f'[ERROR] Run command failed.{os.linesep}{errorString}')
                sys.exit(1)
            end_time = time.perf_counter()

            if not os.path.exists(filePerfData):
                log.warning(f'Performance file does not exist {filePerfData} so creating it...')
                out_file_create = open(filePerfData, 'w')
                out_file_create.close()
            if os.path.exists(filePerfData):
                # copy data to a new file
                # File prefix is: event_*
                new_out_filename = f'{currOutputDirName}/event_{i}_{filePerfData}'
                log.info(f'Copying data from {filePerfData} to {new_out_filename}')
                out_file = open(new_out_filename, 'w')
                in_file = open(filePerfData, 'r')

                out_file.write(f'INPUT: {cfg.workload.cmd}\n')
                out_file.write(f'TIME: {end_time - start_time}\n')

                for line in in_file.readlines():
                    out_file.write(line)

                in_file.close()
                out_file.close()

            else:
                log.error(f'{filePerfData} not generated... Something went wrong.')

        os.unlink(fileCounterExactLocation)
    return


def runReport(directory=None, dirReport: str = 'report', fileThreshold: str = 'threshold.npy', cfg: Config = None):
    """Generates a performance regression report using a trained model.

    Args:
        directory: Path containing a series of AutoPerf runs.
        dirReport: Report folder name.
        fileThreshold: Thresholds of detection.
        cfg:
    """
    if cfg is None:
        cfg = loadConfig_TryDetect()
    model = keras_autoencoder.loadTrainedModel()
    report_dir = os.path.join(cfg.build.dir, '.autoperf', dirReport)
    with open(report_dir, 'w') as logFile:
        runs = os.listdir(directory)
        thresholdPath = os.path.abspath(os.path.join(cfg.build.dir, '.autoperf', fileThreshold))
        anomaly_summary, _ = testAnomaly(model, directory, runs, np.load(thresholdPath))
        writeTestLog(logFile, anomaly_summary)
    return
