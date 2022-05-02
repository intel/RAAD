#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Brad McDonald, Mejbah ul Alam, Justin Gottschlich, Abdullah Muzahid
# *****************************************************************************/
"""Main entrypoint to Autoperf. Routes user commands to the correct functions."""
from __future__ import absolute_import

import configparser
import os, sys, argparse, logging, warnings

from typing import List

from rich.logging import RichHandler
from rich import traceback

from autoperf.annotation import annotation
from autoperf.fsm.machine import Modes
from autoperf.config import loadConfig_TryDetect, loadConfig
from autoperf.utils import mkdir_p

FORMAT = "%(message)s"
# noinspection PyArgumentList
logging.basicConfig(format=FORMAT, datefmt="[%X]", level="NOTSET",
                    handlers=[RichHandler(rich_tracebacks=True, markup=True)])
traceback.install()

logging.getLogger('tensorflow').disabled = True
logging.getLogger('matplotlib').disabled = True
logging.getLogger('subprocess.Popen').disabled = True
logging.getLogger('matplotlib.pyplot').disabled = True
logging.getLogger('matplotlib.font_manager').disabled = True
log = logging.getLogger("rich")

# Filter out this warning about Rich TQDM progress bars
warnings.filterwarnings("ignore", message="rich is experimental/alpha")


def mainUnitTestConfig(args):
    try:
        from autoperf.config import CLI_UnitTest
        # autoperf init - generates .autoperf, .autoperf/config.ini, .autoperf/COUNTERS
        #   .autoperf/threshold.npy
        #   .autoperf/[branch].json
        #   .autoperf/detect
        #   .autoperf/logs
        #   .autoperf/trained_network
        #   .autoperf/train
        #   .autoperf/bad_ma.json
        #   .autoperf/report
        CLI_UnitTest()

    except BaseException as ErrorContext:
        print(f"{args}{os.pathsep}{ErrorContext}")
    return


def init(args):
    """Initializes the .autoperf directory at the root of the git repo.

    Args:
        args: Unused, but required by argparse.
    """
    try:
        from autoperf.config import CLI
        CLI()
    except BaseException as ErrorContext:
        print(f"{args}{os.pathsep}{ErrorContext}")
    return


def annotate_perform(args):
    """Apply Autoperf HPC annotations to C/C++ code.

    Args:
        args: Provided by argparse.
    """
    from autoperf.annotation.annotation import annotate
    annotate(args)
    return


def measure(args):
    """Run the specified workload and collect HPC measurements.

    Args:
        args: Provided by argparse.
    """
    from .actions import runBuild, runWorkload
    runBuild()
    for r in args.run_count:
        runWorkload(args.out_dir, r)
    return


def train(args=None, RawConfig: configparser.RawConfigParser = None):
    """Train a Keras autoEncoderObj using collected HPC measurements.

    Args:
        args: Provided by argparse.
        RawConfig:
    """
    from autoperf import autoperf, keras_autoencoder
    from autoperf.counters import get_num_counters
    # from autoperf.config import cfg
    cfg = RawConfig
    autoencoder = keras_autoencoder.getAutoEncoder(get_num_counters(), cfg.model.encoding, cfg.model.hidden)
    if args.hidden is not None and args.encoding is not None:
        autoencoder = keras_autoencoder.getAutoEncoder(get_num_counters(), args.encoding, args.hidden)

    log.info('Autoencoder Summary:')
    for line in autoencoder.summary():
        log.info(line)
    autoperf.trainAndEvaluate(autoencoder, args.train_dir)
    return


def evaluate(args):
    """Evaluate an autoEncoderObj with train (nominal) + test (nominal/anomalous)
    HPC measurements.

    Args:
        args: Provided by argparse.
    """
    from .actions import runEvaluate
    runEvaluate(args.train, args.nominal, args.anomalous)
    return


def detect(args):
    """Detect performance anomalies using a previously trained autoEncoderObj.

    Args:
        args: Provided by argparse.
    """
    from autoperf.fsm.machine import Modes
    runMachineAPI(Modes.DETECT, args)
    return


def clean(args):
    """Clean up the .autoperf directory, besides configuration files.

    Args:
        args: Provided by argparse.
    """
    try:
        import shutil
        from glob import glob
        from autoperf.utils import getAutoperfDir

        # This would force the user to give explicit permission before clearing the
        # directory. Temporarily disabled, to match other common CLI apps.
        #   from rich.prompt import Confirm
        #   if Confirm.ask("[red]Would you like to remove all non-configuration files in \
        # the [code].autoperf[/code] directory?"):

        for file in glob(getAutoperfDir('*')):
            if file.split('/')[-1] not in ['config.ini', 'COUNTERS']:
                log.info('Removing [code]%s', file)
                try:
                    os.unlink(file)
                except IsADirectoryError:
                    shutil.rmtree(path=file, ignore_errors=True)
    except BaseException as ErrorContext:
        print(f"{args}{os.pathsep}{ErrorContext}")
    return


def runMachineAPI(mode, run_count: int = 16, cfg: configparser.RawConfigParser = None):
    """Run the finite state machine until all states are exhausted.

    Args:
        mode: What the machine should do: (TRAIN | DETECT).
        run_count:
        cfg:
    """
    from git import Repo
    from autoperf.fsm.machine import AutoPerfMachineAPI, States, Modes
    from autoperf.utils import getAutoperfDir

    if cfg is None:
        cfg: configparser.RawConfigParser = loadConfig_TryDetect()

    ap_fsm = AutoPerfMachineAPI(mode=mode, runs=run_count, cfg=cfg)
    for state in ap_fsm:
        log.info('[bold green]State - [%s]', state)

        # -------------------------------------------------------------------------
        if state in str(States.DIFF):
            from .annotation.annotation import annotate as run_annotate
            from .annotation.annotation import configure_args

            annotate_arg_str = f'{cfg.build.dir} --diff {cfg.git.main} --recursive'
            annotate_arg_parser = configure_args()
            annotate_args = annotate_arg_parser.parse_args(annotate_arg_str.split(' '))
            run_annotate(input_args=annotate_args, cfg=cfg)

        # -------------------------------------------------------------------------
        elif state in str(States.STASH):
            repo = Repo(cfg.build.dir, search_parent_directories=False)
            repo.git.stash()
            repo.git.checkout(cfg.git.main)

        # -------------------------------------------------------------------------
        elif state in str(States.ANNOTATE):
            from .annotation.annotation import annotate as run_annotate
            from .annotation.annotation import configure_args

            repo = Repo(cfg.build.dir, search_parent_directories=False)
            tempRepoJSON = str(repo.head.ref) + '.json'
            onlyfile = os.path.join(cfg.build.dir, '.autoperf', tempRepoJSON)

            if os.path.exists(onlyfile):
                anno_arg_str = f'{cfg.build.dir} --only {onlyfile} --recursive --apply --inject'
                anno_arg_parser = configure_args()
                anno_args = anno_arg_parser.parse_args(anno_arg_str.split(' '))
                run_annotate(input_args=anno_args, cfg=cfg)
            else:
                log.error(f'  git file JSON {onlyfile} does not exist.')
                # diff should have been performed... Error...
                # annotate_perform(input_args=None, cfg=cfg)

        # -------------------------------------------------------------------------
        elif state in str(States.BUILD):
            from autoperf.actions import runBuild
            runBuild(cfg=cfg)

        # -------------------------------------------------------------------------
        elif state in str(States.MEASURE):
            from autoperf.actions import runWorkload
            from glob import glob

            out_dir = os.path.join(cfg.build.dir, '.autoperf')
            if Modes.TRAIN in ap_fsm.mode:
                out_dir = os.path.join(out_dir, 'train')
            elif Modes.DETECT in ap_fsm.mode:
                out_dir = os.path.join(out_dir, 'detect')
            mkdir_p(out_dir)
            workload_run = 0
            for folder in glob(out_dir + '/run_*'):
                run = int(folder.split('_')[-1])
                if run > workload_run:
                    workload_run = run
            filePerfData = "perf_data.csv"
            runWorkload(out_dir=out_dir, run_count=(workload_run + 1), filePerfData=filePerfData, cfg=cfg)

        # -------------------------------------------------------------------------
        elif state in str(States.CLUSTER):
            log.warning('  Not yet implemented.')


        # -------------------------------------------------------------------------
        elif state in str(States.TRAIN):
            from autoperf import autoperf, keras_autoencoder
            from autoperf.counters import get_num_counters

            autoEncoderModel = keras_autoencoder.getAutoEncoder(get_num_counters(), cfg.model.encoding, cfg.model.hidden)
            trainDataDir = getAutoperfDir(directory='train', repoDirectory=cfg.build.dir)
            autoperf.trainAndEvaluate(model=autoEncoderModel, trainDataDir=trainDataDir)

        # -------------------------------------------------------------------------
        elif state in str(States.POP):
            repo = Repo(cfg.build.dir, search_parent_directories=False)
            repo.git.reset('--hard')
            repo.git.checkout('-')
            try:
                repo.git.stash('pop')
            except BaseException as ErrorContext:
                print(f"{run_count}{os.pathsep}{ErrorContext}")
                # Just means the previous stash didn't save anything, that's okay.
                pass

        # -------------------------------------------------------------------------
        elif state in (States.DETECT):
            from autoperf.actions import runDetect
            out_dir = os.path.join(cfg.build.dir, '.autoperf')
            train_dir = os.path.join(out_dir, 'train')
            detect_dir = os.path.join(out_dir, 'detect')
            runDetect(train_dir, detect_dir)

        # -------------------------------------------------------------------------
        elif state in str(States.REPORT):
            from autoperf.actions import runReport
            out_dir = os.path.join(cfg.build.dir, '.autoperf')
            detect_dir = os.path.join(out_dir, 'detect')
            runReport(directory=detect_dir, cfg=cfg)

        # -------------------------------------------------------------------------
        elif state in str(States.FINISHED):
            from autoperf.annotation.annotation import annotate as run_annotate
            from autoperf.annotation.annotation import configure_args

            log.info('Cleaning...')
            repoDirExists = os.path.exists(cfg.build.dir)
            if repoDirExists:
                repo = Repo(cfg.build.dir, search_parent_directories=False)
            else:
                repo = Repo(os.getcwd(), search_parent_directories=False)
            onlyFile = getAutoperfDir(str(repo.head.ref) + '.json')

            if os.path.exists(onlyFile):
                annotate_arg_str = f'{cfg.build.dir} --only {onlyFile} --recursive --erase'
                annotate_arg_parser = configure_args()
                annotate_args = annotate_arg_parser.parse_args(annotate_arg_str.split(' '))
                run_annotate(annotate_args)
    return

def main(argv: List[str] = None):
    """Main Autoperf entrypoint, routes user commands to function calls.

    Args:
        argv: Argument vector, typically derived from user input.
    """
    parser = argparse.ArgumentParser(prog='autoperf',
                                     description='AutoPerf is a performance regression monitoring system.')
    parser.set_defaults(func=lambda x: parser.print_help())
    subparsers = parser.add_subparsers(title='commands')

    # --------------------------------------------------------------------------

    parser_detect = subparsers.add_parser('detect',
                                          help='run AutoPerf end-to-end and report any discovered anomalies',
                                          description='Run AutoPerf end-to-end and report any discovered anomalies.')
    parser_detect.add_argument('run_count', metavar='R', type=int, help='Number of workload runs to execute')
    parser_detect.set_defaults(func=detect)

    # --------------------------------------------------------------------------

    parser_init = subparsers.add_parser('init',
                                        help='initialize the .autoperf folder + configs',
                                        description='Initialize the .autoperf folder + configs.')
    parser_init.set_defaults(func=init)

    # --------------------------------------------------------------------------

    parser_clean = subparsers.add_parser('clean',
                                         help='clean the .autoperf folder except for configs',
                                         description='Clean the .autoperf folder except for configs.')
    parser_clean.set_defaults(func=clean)

    # --------------------------------------------------------------------------

    parser_measure = subparsers.add_parser('measure',
                                           help='run the program under test and collect measurements',
                                           description='Run the program under test and collect measurements.')
    parser_measure.add_argument('out_dir', type=str, help='Output directory for HPC results')
    parser_measure.add_argument('run_count', metavar='R', nargs='+', type=int, help='Run index')
    parser_measure.set_defaults(func=measure)

    # --------------------------------------------------------------------------

    parser_train = subparsers.add_parser('train',
                                         help='train an autoEncoderObj with collected measurements',
                                         description='Train an autoEncoderObj with collected measurements.')
    parser_train.add_argument('--hidden', metavar='H', type=int, default=None,
                              nargs='+', help='List of hidden layer dimensions')
    parser_train.add_argument('--encoding', metavar='E', type=int, default=None,
                              help='Encoding layer dimension')
    parser_train.add_argument('train_dir', type=str, help='Nominal training data directory')
    parser_train.set_defaults(func=train)

    # --------------------------------------------------------------------------

    parser_evaluate = subparsers.add_parser('evaluate',
                                            help='evaluate a trained autoEncoderObj with test data',
                                            description='Evaluate a trained autoEncoderObj with test data.')
    parser_evaluate.add_argument('train', type=str, help='Training data directory')
    parser_evaluate.add_argument('nominal', type=str, help='Nominal test data directory')
    parser_evaluate.add_argument('anomalous', type=str, help='Anomalous test data directory')
    parser_evaluate.set_defaults(func=evaluate)

    # --------------------------------------------------------------------------

    parser_init = subparsers.add_parser('mainUnitTestConfig',
                                        help='initialize .autoperf folder, configs, and execute unit test.',
                                        description='initialize .autoperf folder, configs, and execute unit test.')
    parser_init.set_defaults(func=mainUnitTestConfig)

    # --------------------------------------------------------------------------

    annotation.configure_args(subparsers)

    # --------------------------------------------------------------------------

    # Execute the user command
    try:
        anyArgs = sys.argv[1:] != list()
        if anyArgs:
            args = parser.parse_args(argv)
            args.func(args)
        else:  # 'unit_test':
            parser.print_help()
            print(f"{os.linesep}Running unit test...")

            # args = parser.parse_args(args=['mainUnitTestConfig'])  # ['init'])
            # args.func(args)
            from autoperf.config import CLI_UnitTest
            # autoperf init - generates .autoperf, .autoperf/config.ini, .autoperf/COUNTERS
            #   .autoperf/threshold.npy
            #   .autoperf/[branch].json
            #   .autoperf/detect
            #   .autoperf/logs
            #   .autoperf/trained_network
            #   .autoperf/train
            #   .autoperf/bad_ma.json
            #   .autoperf/report
            configFile = CLI_UnitTest()
            cfgObj = loadConfig(configFile)
            runMachineAPI(Modes.DETECT, run_count=16, cfg=cfgObj)
            # args = parser.parse_args(args=['detect', '16'])
            # args.func(args)

    # Handle Ctrl-C gracefully
    except KeyboardInterrupt:
        print(f"{argv}{os.linesep}")
        sys.exit(0)

    return sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
