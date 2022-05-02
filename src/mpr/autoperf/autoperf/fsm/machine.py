#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Brad McDonald, Mejbah ul Alam, Justin Gottschlich, Abdullah Muzahid
# *****************************************************************************/
"""machine.py

This file contains all code regarding the finite state machine that drives the
order of execution.
"""

import os, hashlib, hmac, pickle, secrets, logging, json
from enum import IntFlag, Enum, auto

from transitions import Machine
# from transitions.extensions import GraphMachine as Machine

from autoperf.config import loadConfig_TryDetect
from autoperf.utils import getAutoperfDir, mkdir_p
from autoperf.config import Config

logging.getLogger('transitions').setLevel(logging.CRITICAL)
log = logging.getLogger("rich")


class AutoName(Enum):
    """Automatically name Enums using the `auto()` function."""

    # noinspection PyMethodParameters
    def _generate_next_value_(name, start, count, last_values):
        return name


class Modes(IntFlag):
    """Mode of operation flags. More than one can be active at a time."""
    TRAIN = auto()
    DETECT = auto()


class States(str, Enum):
    """Underlying state names of the FSM."""
    DIFF = auto()
    STASH = auto()
    ANNOTATE = auto()
    BUILD = auto()
    MEASURE = auto()
    CLUSTER = auto()
    TRAIN = auto()
    POP = auto()
    DETECT = auto()
    REPORT = auto()
    FINISHED = auto()


class AutoPerfMachineNIL(Machine):
    """Full sequential FSM with checkpoints and recovery."""

    transitions = [
        {'trigger': 'next', 'source': States.DIFF, 'dest': States.STASH},

        {'trigger': 'next', 'source': States.STASH, 'dest': States.ANNOTATE},

        {'trigger': 'next', 'source': States.POP, 'dest': States.ANNOTATE,
         'conditions': 'do_detect'},

        {'trigger': 'next', 'source': States.POP, 'dest': States.FINISHED,
         'unless': 'do_detect'},

        {'trigger': 'next', 'source': States.ANNOTATE, 'dest': States.BUILD},

        {'trigger': 'next', 'source': States.BUILD, 'dest': States.MEASURE,
         'after': 'reset_workload_runs'},

        {'trigger': 'next', 'source': States.MEASURE, 'dest': States.CLUSTER,
         'conditions': 'do_train', 'unless': 'keep_collecting', 'after': 'increment_workload'},

        {'trigger': 'next', 'source': States.MEASURE, 'dest': '=',
         'conditions': 'keep_collecting', 'after': 'increment_workload'},

        {'trigger': 'next', 'source': States.CLUSTER, 'dest': States.TRAIN},

        {'trigger': 'next', 'source': States.TRAIN, 'dest': States.POP,
         'after': 'stop_train'},

        {'trigger': 'next', 'source': States.MEASURE, 'dest': States.DETECT,
         'conditions': 'do_detect', 'unless': ['keep_collecting', 'do_train'],
         'after': 'increment_workload'},

        {'trigger': 'next', 'source': States.DETECT, 'dest': States.REPORT},

        {'trigger': 'next', 'source': States.REPORT, 'dest': States.FINISHED}
    ]

    mode = None
    max_workload_runs = None
    workload_run = None

    def _save_checkpoint(self, debug: bool = False):
        payloadValid = self._save_checkpoint_secure()
        if payloadValid is False and debug is True:
            log.info(f"Entering file save insecure mode with debugging")
            with open(getAutoperfDir('checkpoint.p'), 'wb') as checkpoint:
                pickle.dump(self, checkpoint, 4)
        return

    def _save_checkpoint_secure(self, saveFile='checkpoint.p', uniqueKey='unique-key-here'):
        payloadValid = False
        try:
            with open(getAutoperfDir(saveFile), 'wb') as checkpoint:
                data = pickle.dumps(obj=self, protocol=4)
                uniqueKeyBytes = str.encode(uniqueKey)
                digest = hmac.new(uniqueKeyBytes,
                                  data,
                                  hashlib.blake2b).hexdigest()
                bytesString = str.encode(str(digest) + ' ')
                checkpoint.write(bytesString + data)
                payloadValid = True
        except BaseException as ErrorContext:
            log.info(f"Error in saving checkpoint {saveFile} with:{os.pathsep}{ErrorContext}")
        return payloadValid

    def _load_checkpoint(self, debug: bool = False):
        payloadValid = self._load_checkpoint_secure()
        if payloadValid is False and debug is True:
            apDir = getAutoperfDir('checkpoint.p')
            if not os.path.exists(apDir):
                from autoperf.utils import findFolder
                foldersFound = findFolder(dirSignature='.autoperf')
                for folderItem in foldersFound:
                    apDir = os.path.join(folderItem, 'checkpoint.p')
                    if (os.path.exists(apDir)):
                        break
            with open(apDir, 'rb') as checkpoint:
                log.info(f"Entering file load insecure mode with debugging")
                # @todo security risk of loading raw files, use secure function above
                # noinspection PickleLoad,PickleLoad
                tmp_dict = pickle.load(checkpoint)
                self.__dict__.clear()
                self.__dict__.update(tmp_dict.__dict__)
        return

    def _load_checkpoint_secure(self, loadFile='checkpoint.p', uniqueKey='unique-key-here'):
        payloadValid = False
        with open(loadFile, 'rb') as loadFileObject:
            data = loadFileObject.read()
        encodeSpace = str.encode(' ')
        digest, pickle_data = data.split(encodeSpace)
        uniqueKey = str.encode(uniqueKey)
        expected_digest = hmac.new(uniqueKey, pickle_data, hashlib.blake2b).hexdigest()

        if not secrets.compare_digest(digest, expected_digest):
            log.info(f'Invalid HMAC signature. Cannot load data in {loadFile}')
        else:
            # Security hole fixed with HMAC verify
            # noinspection PickleLoad,PickleLoad
            tmp_dict = pickle.loads(pickle_data)
            self.__dict__.clear()
            self.__dict__.update(tmp_dict.__dict__)
            payloadValid = True
        return payloadValid

    def do_train(self):
        """Check if we should train the model."""
        return Modes.TRAIN in self.mode

    def stop_train(self):
        """Disable training; useful in TRAIN|DETECT mode."""
        self.mode &= ~Modes.TRAIN

    def do_detect(self):
        """Check if we should try to detect anomalies."""
        return Modes.DETECT in self.mode

    def stop_detect(self):
        """Disable anomaly detection."""
        self.mode &= ~Modes.DETECT

    def increment_workload(self):
        """Increment the current (active) workload ID."""
        self.workload_run += 1

    def keep_collecting(self):
        """Check if more data should be collected."""
        return self.workload_run < self.max_workload_runs

    def reset_workload_runs(self):
        """Change back to the default workload ID."""
        self.workload_run = 1

    def __init__(self, mode: Modes, runs: int = 0, checkpoint: bool = True, repoPath: str = None):
        """Initialize the FSM!

        Args:
            mode: Mode of operation.
            runs: Number of workload runs to conduct.
            checkpoint: Whether checkpoints should be saved / recovered from.
        """
        cfg = loadConfig_TryDetect()

        if checkpoint:
            try:
                self._load_checkpoint()
                log.info('[yellow]Recovering from checkpoint.')

            except FileNotFoundError:
                log.warning('Checkpoint not found, starting from scratch.')

        # Either the checkpoint load failed, or checkpoints are not active.
        if self.mode is None:

            self.mode = mode
            self.max_workload_runs = runs
            self.workload_run = 1
            initial_state = States.DIFF

            if self.mode == Modes.DETECT:
                if repoPath is None:
                    if cfg is None:
                        cfg = loadConfig_TryDetect()
                    if cfg is None:
                        print(f"AutoPerf config cannot be found{os.linesep}")
                        exit(1)
                    accessFolder = cfg.workload.dir
                else:
                    accessFolder = repoPath
                usageDirectory = accessFolder
                if not os.path.exists(usageDirectory):
                    self.mode |= Modes.TRAIN

                elif runs > 0:
                    initial_state = States.ANNOTATE

                else:
                    initial_state = States.DETECT

            Machine.__init__(self, states=States, transitions=self.transitions,
                             initial=initial_state, after_state_change='_save_checkpoint')

    def __iter__(self):
        """Turn the FSM into an iterable."""
        return AutoPerfIteratorNIL(self)


class AutoPerfIteratorNIL():
    """Iterator of the AutoPerf FSM, allowing the machine to be executed through
    a `for state in fsm` loop."""

    def __init__(self, obj):
        """Start at the initial state."""
        self._autoperf = obj
        self._index = 0

    def __next__(self):
        """Advance to the next state."""
        if self._index == 0:
            self._index += 1
            return self._autoperf.model.state.name

        if self._autoperf.is_FINISHED():
            os.unlink(getAutoperfDir('checkpoint.p'))
            raise StopIteration

        self._index += 1
        self._autoperf.next()
        return self._autoperf.model.state.name


######################################################
# APIs
######################################################
class AutoPerfMachineAPI(Machine):
    """Full sequential FSM with checkpoints and recovery."""

    transitions = [
        {'trigger': 'next', 'source': States.DIFF, 'dest': States.STASH},

        {'trigger': 'next', 'source': States.STASH, 'dest': States.ANNOTATE},

        {'trigger': 'next', 'source': States.POP, 'dest': States.ANNOTATE,
         'conditions': 'do_detect'},

        {'trigger': 'next', 'source': States.POP, 'dest': States.FINISHED,
         'unless': 'do_detect'},

        {'trigger': 'next', 'source': States.ANNOTATE, 'dest': States.BUILD},

        {'trigger': 'next', 'source': States.BUILD, 'dest': States.MEASURE,
         'after': 'reset_workload_runs'},

        {'trigger': 'next', 'source': States.MEASURE, 'dest': States.CLUSTER,
         'conditions': 'do_train', 'unless': 'keep_collecting', 'after': 'increment_workload'},

        {'trigger': 'next', 'source': States.MEASURE, 'dest': '=',
         'conditions': 'keep_collecting', 'after': 'increment_workload'},

        {'trigger': 'next', 'source': States.CLUSTER, 'dest': States.TRAIN},

        {'trigger': 'next', 'source': States.TRAIN, 'dest': States.POP,
         'after': 'stop_train'},

        {'trigger': 'next', 'source': States.MEASURE, 'dest': States.DETECT,
         'conditions': 'do_detect', 'unless': ['keep_collecting', 'do_train'],
         'after': 'increment_workload'},

        {'trigger': 'next', 'source': States.DETECT, 'dest': States.REPORT},

        {'trigger': 'next', 'source': States.REPORT, 'dest': States.FINISHED}
    ]

    mode = None
    max_workload_runs = None
    workload_run = None
    saveInProgress = False
    loadInProgress = False
    cfg = None
    configDirectory = None
    autoPerfDirectory = None
    checkpointFile = None

    def __init__(self, mode: Modes, runs: int = 0, checkpoint: bool = True, cfg: Config = None):
        """Initialize the FSM!

        Args:
            mode: Mode of operation.
            runs: Number of workload runs to conduct.
            checkpoint: Whether checkpoints should be saved / recovered from.
        """
        self.saveInProgress = False
        self.loadInProgress = False

        if checkpoint:
            try:
                self._load_checkpoint()
                log.info('[yellow]Recovering from checkpoint.')

            except FileNotFoundError:
                log.warning('Checkpoint not found, starting from scratch.')

        if cfg is None:
            log.error('Configuration not found. Run init.')
            exit(1)
        else:
            self.cfg = cfg
            self.configDirectory = cfg.workload.dir
            self.autoPerfDirectory = os.path.join(self.configDirectory, ".autoperf")

            if self.configDirectory is not None:
                mkdir_p(self.autoPerfDirectory)
                self.checkpointFile = os.path.join(self.autoPerfDirectory, "checkpoint.p")
            else:
                self.autoPerfDirectory = ".autoperf"
                mkdir_p(self.autoPerfDirectory)
                self.checkpointFile = os.path.join(self.autoPerfDirectory, "checkpoint.p")

            # Either the checkpoint load failed, or checkpoints are not active.
            if self.mode is None:
                self.mode = mode
                self.max_workload_runs = runs
                self.workload_run = 1
                initial_state = States.DIFF

                if self.mode == Modes.DETECT:
                    self.configDirectory = cfg.workload.dir
                    configModelFile = cfg.model.filename
                    configModelFilePath = os.path.join(self.autoPerfDirectory, configModelFile)
                    if not os.path.exists(configModelFilePath):
                        self.mode |= Modes.TRAIN
                    elif runs > 0:
                        initial_state = States.ANNOTATE
                    else:
                        initial_state = States.DETECT

                Machine.__init__(self, states=States, transitions=self.transitions,
                                 initial=initial_state, after_state_change='_save_checkpoint')
            return

    def __iter__(self):
        """Turn the FSM into an iterable."""
        return AutoPerfIteratorAPI(obj=self, configDirectory=self.configDirectory)

    def toJSON(self):
        try:
            data = json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
        except:
            data = self.__dict__
        return data

    def _save_checkpoint(self, debug: bool = True):
        if self.saveInProgress is True:
            return
        self.saveInProgress = True
        payloadValid = self._save_checkpoint_secure()
        if payloadValid is False and debug is True:
            log.info(f"Entering file save insecure mode with debugging")
            with open(getAutoperfDir('checkpoint.p'), 'wb') as checkpoint:
                pickle.dump(self, checkpoint, 4)
        self.saveInProgress = False
        return

    def _save_checkpoint_secure(self, uniqueKey='unique-key-here'):
        payloadValid = False
        # try:
        dictDump = self
        mkdir_p(self.autoPerfDirectory)
        with open(self.checkpointFile, 'wb+') as checkpoint:
            checkpoint.write(str.encode(""))
            checkpoint.close()
        #with open(self.checkpointFile, 'w+') as checkpoint:
        #    # dictJSON = self.toJSON()
        #    # sDict = self.__dict__
        #    sDict = dict()
        #    sDict.update(vars(self))
        #    json.dump(sDict, checkpoint)
        #with open(self.checkpointFile, 'r+') as checkpoint:
        #    data = json.load(checkpoint)
        #    checkpoint.close()
        with open(self.checkpointFile, 'wb+') as checkpoint:
            # obj, protocol=None, *, fix_imports=True, buffer_callback=None
            data = pickle.dumps(obj=list(self.__dict__), protocol=4)
            uniqueKeyBytes = str.encode(uniqueKey)
            digest = hmac.new(uniqueKeyBytes,
                              data,
                              hashlib.blake2b).hexdigest()
            bytesString = str.encode(str(digest) + ' ')
            checkpoint.write(bytesString + data)
            payloadValid = True
            checkpoint.close()
        # except BaseException as ErrorContext:
        #    log.info(f"Error in saving checkpoint {self.checkpointFile} with:{os.pathsep}{ErrorContext}")
        return payloadValid

    def _load_checkpoint(self, debug: bool = True):
        if self.loadInProgress:
            return
        if self.checkpointFile is None:
            return
        if not os.path.exists(self.checkpointFile):
            return
        self.loadInProgress = True
        payloadValid = self._load_checkpoint_secure()
        if payloadValid is False and debug is True:
            apDir = self.checkpointFile
            if not os.path.exists(apDir):
                print("Error cannot find configuration checkpoint file.")
                exit(1)
            with open(apDir, 'rb') as checkpoint:
                log.info(f"Entering file load insecure mode with debugging")
                # @todo security risk of loading raw files, use secure function above
                # noinspection PickleLoad,PickleLoad
                tmp_dict = pickle.load(checkpoint)
                self.__dict__.clear()
                self.__dict__.update(tmp_dict.__dict__)
        self.loadInProgress = False
        return

    def _load_checkpoint_secure(self, uniqueKey='unique-key-here'):
        payloadValid = False
        with open(self.checkpointFile, 'rb') as loadFileObject:
            data = loadFileObject.read()
        encodeSpace = str.encode(' ')
        digest, pickle_data = data.split(encodeSpace)
        uniqueKey = str.encode(uniqueKey)
        expected_digest = hmac.new(uniqueKey, pickle_data, hashlib.blake2b).hexdigest()

        if not secrets.compare_digest(digest, expected_digest):
            log.info(f'Invalid HMAC signature. Cannot load data in {self.checkpointFile}')
        else:
            # Security hole fixed with HMAC verify
            # noinspection PickleLoad,PickleLoad
            tmp_dict = pickle.loads(pickle_data)
            self.__dict__.clear()
            self.__dict__.update(tmp_dict.__dict__)
            payloadValid = True
        return payloadValid

    def do_train(self):
        """Check if we should train the model."""
        return Modes.TRAIN in self.mode

    def stop_train(self):
        """Disable training; useful in TRAIN|DETECT mode."""
        self.mode &= ~Modes.TRAIN

    def do_detect(self):
        """Check if we should try to detect anomalies."""
        return Modes.DETECT in self.mode

    def stop_detect(self):
        """Disable anomaly detection."""
        self.mode &= ~Modes.DETECT

    def increment_workload(self):
        """Increment the current (active) workload ID."""
        self.workload_run += 1

    def keep_collecting(self):
        """Check if more data should be collected."""
        return self.workload_run < self.max_workload_runs

    def reset_workload_runs(self):
        """Change back to the default workload ID."""
        self.workload_run = 1


class AutoPerfIteratorAPI():
    """Iterator of the AutoPerf FSM, allowing the machine to be executed through
    a `for state in fsm` loop."""

    def __init__(self, obj, configDirectory=None):
        """Start at the initial state."""
        self._autoperf = obj
        self._index = 0
        self.configDirectory = configDirectory
        return

    def __next__(self):
        """Advance to the next state."""
        if self._index == 0:
            self._index += 1
            return self._autoperf.model.state.name

        if self._autoperf.is_FINISHED():
            checkPointFile = os.path.join(self.configDirectory, ".autoperf", "checkpoint.p")
            try:
                os.unlink(checkPointFile)
            except BaseException as errorContext:
                log.warning(f"Error in nextState file delete of {checkPointFile} with {errorContext}.")
            raise StopIteration

        self._index += 1
        self._autoperf.next()
        return self._autoperf.model.state.name
