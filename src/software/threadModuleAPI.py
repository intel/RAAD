#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
# @package threadModuleAPI
import optparse, datetime, traceback, pprint, os, threading, subprocess, re, psutil, sys, concurrent.futures, itertools, time, typing

from src.software.debug import whoami


def getAvailableCPUCount():
    """ Number of available virtual or physical CPUs on this system, i.e.
    user/real as output by time(1) when called with an optimally scaling
    userspace-only program"""
    coreThreadsAvailable = 1
    # cpuset may restrict the number of *available* processors
    try:
        import multiprocessing
        coreThreadsAvailable = multiprocessing.cpu_count()
        return coreThreadsAvailable
    except (ImportError, NotImplementedError):
        pass

    try:
        coreThreadsAvailable = psutil.cpu_count()  # psutil.NUM_CPUS on old versions
        return coreThreadsAvailable
    except (ImportError, AttributeError):
        pass

    except OSError:
        pass

    # raise Exception('Can not determine.)
    print('Can not determine number of CPUs on this system, so defaulting to 1.')
    return coreThreadsAvailable


class MultiThreadFL():
    """
    Multi-thread a function with multible items.
    """

    @staticmethod
    def threadProcessLoop(items=None, start=None, end=None, threadFunction=None):
        if items is None:
            return
        negOne = (-1)
        if end > len(items) or start < (len(items) * negOne):
            return
        for item in items[start:end]:
            try:
                threadFunction(item)
            except Exception:
                print('error with item')
        return

    @staticmethod
    def threadSplitProcessing(items=None, num_splits=None, threadProcessFunction=None):
        if items is None:
            return
        if num_splits is None:
            numSplits = min(getAvailableCPUCount(), len(items))
        else:
            numSplits = num_splits
        split_size = len(items) // numSplits
        threads = []
        for i in range(numSplits):
            # Determine the indices of the list this thread will handle
            start = i * split_size
            # Special case on the last chunk to account for uneven splits
            end = None if i + 1 == numSplits else (i + 1) * split_size
            # Create the thread
            threads.append(threading.Thread(target=threadProcessFunction, args=(items, start, end)))
            threads[-1].start()  # Start the thread we just created

        # Wait for all threads to finish
        for thread in threads:
            thread.join()
        return

    def threadLoop(self, items=None, start=None, end=None, num_splits=None, functionProcess=None):
        self.threadSplitProcessing(items=items, num_splits=num_splits, threadProcessFunction=self.threadProcessLoop(items=items, start=start, end=end, threadFunction=functionProcess))
        return


class MassiveParallelismSingleFunctionManyParameters():
    # High performance massive parallelism class in which a single function context with a list of parameters to pass.

    def __init__(self,
                 debug: bool = False,
                 functionName=None,
                 fParameters: typing.List[dict] = None,
                 workers: int = None,
                 timeOut: int = (60 * 60 * 24),  # Default time is 60 seconds * 60 minutes * 24 hours = 1 day in seconds per thread
                 inOrder: bool = True,
                 runSequential: bool = False):
        self.debug = debug
        self.functionName = functionName
        self.fParameters = fParameters
        self.workers = workers  # Pool of workers
        self.timeOut = timeOut
        self.inOrder = inOrder
        self.resultsList = list()
        self.encounteredExceptions = 0
        self.exceptionFoundList = list()
        self.alreadyExecuted = False
        self.areResultsReady = False
        self.startTime = None
        self.endTime = None
        self.totalTime = None
        self.runSequential = runSequential
        return

    def setFunctionName(self, functionName):
        self.functionName = functionName
        return

    def setParametersList(self, fParameters: typing.List[dict]):
        """Sets parameter list from dictionary parameter context.
        Args:
            fParameters: list of dictionaries of parameters

        Returns: None

        Example
        kwargsList_input = [{'inputINI': dataFileNameA,
                             ...
                             'debug': debug,
                             'inParallel': inParallelA,
                             'requiredList': requiredListA},
                           ...
                            {'inputINI': dataFileNameZ,
                             ...
                             'debug': debugZ,
                             'inParallel': inParallelZ,
                             'requiredList': requiredListZ}]
        """
        self.fParameters = fParameters
        return

    def getExceptionInfo(self):
        return self.encounteredExceptions, self.exceptionFoundList

    def getExecutionTime(self):
        return self.startTime, self.endTime, self.totalTime

    def getResults(self):
        return self.resultsList

    def _inOrderConcurrentMap(self):
        """Function that utilises concurrent.futures.ProcessPoolExecutor.map returning inorder in a parallelised manner.

        Returns: results list in order of list given
        """
        self.alreadyExecuted = True
        # Local variables
        functionContextList = list()
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executer:
            # Discretise workload and submit to worker pool
            mapperMeta = executer.map(lambda parametersList: self.functionName(**parametersList), self.fParameters, timeout=self.timeOut)
            self.resultsList.append(mapperMeta)
            # Access results in order.
            for parallelProcessItem in functionContextList:
                try:
                    self.resultsList.append(parallelProcessItem)
                except BaseException as errorObj:
                    self.encounteredExceptions += 1
                    exceptionContext = f" {whoami()} with {errorObj}! Timeout={self.timeOut}"
                    self.exceptionFoundList.append(exceptionContext)
                    if self.debug:
                        print(exceptionContext)
        self.areResultsReady = True
        return self.resultsList

    def _anyOrderConcurrentMap(self):
        """Function that utilises concurrent.futures.ProcessPoolExecutor.map returning in any order in a parallelised manner.
            Returns: results list no particular order of list given.
        """
        self.alreadyExecuted = True
        # Local variables
        functionContextList = list()
        # Parallelization
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.workers) as executor:
            # Discretise workload and submit to worker pool
            for fParameterContext in self.fParameters:
                try:
                    functionContextList.append(executor.submit(self.functionName, fParameterContext))
                except BaseException as errorObj:
                    self.encounteredExceptions += 1
                    exceptionContext = f" {whoami()} with {errorObj}! Timeout={self.timeOut}"
                    self.exceptionFoundList.append(exceptionContext)
                    if self.debug:
                        print(exceptionContext)
        # Skip the copying of the data to another array and use itertools.chain.from_iterable to combine the results from execution to single iterable
        self.resultsList = itertools.chain.from_iterable(f.result() for f in concurrent.futures.as_completed(functionContextList, timeout=self.timeOut))
        self.areResultsReady = True
        return self.resultsList

    def _sequentialMap(self):
        """Function that executions a function with a list of parameters.
            Returns: results list in order of list given.
        """
        self.alreadyExecuted = True
        # Discretise workload and submit worker
        try:
            for fParameterContext in self.fParameters:
                sResult = self.functionName(**fParameterContext)
                (self.resultsList).append(sResult)
        except BaseException as errorObj:
            self.encounteredExceptions += 1
            exceptionContext = f" {whoami()} with {errorObj}! Timeout={self.timeOut}"
            self.exceptionFoundList.append(exceptionContext)
            if self.debug:
                print(exceptionContext)
        self.areResultsReady = True
        return self.resultsList

    def execute(self):
        if self.alreadyExecuted is False:
            self.startTime = time.time()
            if self.debug:
                print(f"Threads, start time token {self.startTime}")

            if self.runSequential is True:
                if self.debug:
                    print(" Processing sequentially in order of parameter list...")
                self._sequentialMap()
            elif self.runSequential is False and self.inOrder is True:
                if self.debug:
                    print(" Processing in-order of parameters list...")
                self._inOrderConcurrentMap()
            elif self.runSequential is False and self.inOrder is False:
                if self.debug:
                    print(" Processing out-of-order of parameters list...")
                self._anyOrderConcurrentMap()
            else:
                if self.debug:
                    print(" Fault in configuration... running sequentially...")
                self._sequentialMap()

            self.endTime = time.time()
            if self.debug:
                print(f"End time token {self.endTime}")
            self.totalTime = self.endTime - self.startTime
            if self.debug:
                print("Threads executed {0} at {1:.4f} seconds with {2} workers".format(len(self.resultsList), self.totalTime, self.workers))
        return self.resultsList


class MassiveParallelismanyFunctionManyParameters():
    # High performance massive parallelism class in which a single function context with a list of parameters to pass.

    def __init__(self,
                 debug: bool = False,
                 functionName_fParameters=None,
                 workers: int = None,
                 timeOut: int = (60 * 60 * 24),  # Default time is 60 seconds * 60 minutes * 24 hours = 1 day in seconds per thread
                 inOrder: bool = True,
                 runSequential: bool = False):
        self.debug = debug
        self.functionName_fParameters = functionName_fParameters
        self.workers = workers  # Pool of workers
        self.timeOut = timeOut
        self.inOrder = inOrder
        self.resultsList = list()
        self.encounteredExceptions = 0
        self.exceptionFoundList = list()
        self.alreadyExecuted = False
        self.areResultsReady = False
        self.startTime = None
        self.endTime = None
        self.totalTime = None
        self.runSequential = runSequential
        self.validInput = False

        # verify input types
        if isinstance(functionName_fParameters, list):
            for functionName, fParameters in functionName_fParameters:
                if isinstance(fParameters, list) and self.validInput is False:
                    for fParametersItem in fParameters:
                        if isinstance(fParametersItem, dict) and self.validInput is False:
                            self.validInput = True
                            break
                elif self.validInput is True:
                    break
        return

    def execute(self):
        if isinstance(self.functionName_fParameters, list):
            for functionName, fParameters in self.functionName_fParameters:
                try:
                    functionContext = MassiveParallelismSingleFunctionManyParameters(debug=self.debug,
                                                                                     functionName=functionName,
                                                                                     fParameters=fParameters,
                                                                                     workers=self.workers,
                                                                                     timeOut=self.timeOut,  # Default time is 60 seconds * 60 minutes * 24 hours = 1 day in seconds per thread
                                                                                     inOrder=self.inOrder,
                                                                                     runSequential=self.runSequential)
                    iResults = functionContext.execute()
                    self.resultsList.append(iResults)
                except BaseException as errorObj:
                    if self.debug:
                        print(f"{whoami()} with {errorObj}")
                    pass

        return


def API(options=None):
    """ API for the default application in the graphical interface.
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
    pprint.pformat(locals(), indent=3, width=100)
    return 0


def main():
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--example", action='store_true', dest='example', default=False, help='Show command execution example.')
    parser.add_option("--debug", action='store_true', dest='debug', default=True, help='Debug mode.')
    parser.add_option("--more", dest='more', default=False, help="Displays more options.")
    parser.add_option("--mode", dest='mode', default=1, help="Mode of Operation.")
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
