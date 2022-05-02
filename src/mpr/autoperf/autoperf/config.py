#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Brad McDonald, Mejbah ul Alam, Justin Gottschlich, Abdullah Muzahid
# *****************************************************************************/
"""config.py

This file contains configuration variables and utility functions for
accessing network parameters and topologies.
"""

import os, ast, sys, configparser, shutil, git
from dataclasses import dataclass
from string import Template
from rich import print as rprint
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, FloatPrompt, Confirm

from autoperf.counters import save_counters, save_counters_path
from autoperf.utils import getAutoperfDir, mkdir_p, findFolder


class ConfigTemplate(Template):
    """Template of the configuration file, serving as a bridge between the
    dataclass implementation and the on-disk `config.ini`."""

    defaults = {
        'build': 'make',
        'build_dir': '.',
        'clean': 'make clean',
        'workload': 'make eval-perfpoint',
        'workload_dir': '.',
        'branch': 'master',
        'noise': 0.25,
        'hidden': [16, 8],
        'encoding': 4,
        'activation': 'tanh',
        'filename': 'trained_network',
        'epochs': 12,
        'batch_size': 64,
        'optimizer': 'Adam',
        'learning_rate': 0.00001,
        'loss': 'mean_squared_error',
        'scale_factor': 1.0,
        'threshold': 0.05
    }

    config_str = Template("""
[build]
  cmd = ${build}
  dir = ${build_dir}

[clean]
  cmd = ${clean}

[workload]
  cmd = ${workload}
  dir = ${workload_dir}

[git]
  main = ${branch}

[model]
  hidden = ${hidden}
  encoding = ${encoding}
  activation = ${activation}
  filename = ${filename}

[training]
  epochs = ${epochs}
  batch_size = ${batch_size}
  optimizer = ${optimizer}
  learning_rate = ${learning_rate}
  loss = ${loss}
  noise = ${noise}
  scale_factor = ${scale_factor}

[detection]
  threshold = ${threshold}
""")

    def __init__(self):
        super(Template, self).__init__()
        return

    def update(self, settings: dict) -> str:
        """Update the template with new settings and return the substituted string.

        Args:
            settings: Dictionary containing key-value pairs of config settings.

        Returns:
            Substituted string with combination of default + configured options.
        """
        return self.config_str.substitute({**self.defaults, **settings})

    def default(self, o):
        try:
            iterable = iter(o)
        except TypeError:
            pass
        else:
            return list(iterable)


@dataclass
class Sections:
    """INI `[section]` headings."""
    raw_sections: dict

    def __post_init__(self):
        rsDict = ((self.raw_sections)._sections).items()
        for section_key, section_value in rsDict:
            setattr(self, section_key, SectionContent(section_value))
        return

    def __dict__(self):
        rsDict = ((self.raw_sections)._sections).items()
        return rsDict

    def default(self, o):
        try:
            iterable = iter(o)
        except TypeError:
            pass
        else:
            return list(iterable)

@dataclass
class SectionContent:
    """INI key-value configuration mappings."""
    raw_section_content: dict

    def __post_init__(self):
        for section_content_k, section_content_v in self.raw_section_content.items():
            v = section_content_v
            try:
                v = ast.literal_eval(section_content_v)
            except BaseException as ErrorContext:
                try:
                    v = section_content_v
                except BaseException as ErrorContextInception:
                    import inspect
                    print(f"file={__file__} line={inspect.currentframe().f_lineno} "
                          f"error={ErrorContext}=>error={ErrorContextInception} "
                          f"for K={section_content_k} V={section_content_v}{os.linesep}")
                pass
            setattr(self, section_content_k, v)

    def default(self, o):
        try:
            iterable = iter(o)
        except TypeError:
            pass
        else:
            return list(iterable)


class Config(Sections):
    """Configuration dataclass wrapper, allowing the following:
      [section]
        key = value

    To be accessed programatically like:
      cfg.section.key
    """

    def __init__(self, raw_config_parser):
        super(Config, self).__init__(raw_config_parser)
        return

    def __dict__(self):
        selfDict = {}
        stringName = str(self.__name__)
        selfDict[stringName] = self.raw_sections
        return selfDict

    def default(self, o):
        try:
            iterable = iter(o)
        except TypeError:
            pass
        else:
            return list(iterable)

# ------------------------------------------------------------------------------


# Read the config file + load into a dataclass that can be accessed in any module
# cfg = configparser.ConfigParser()
# cfg.read(getAutoperfDir('config.ini'))
# cfg = Config(cfg._sections)

# ------------------------------------------------------------------------------

class CreateConfiguration(object):
    banner: str = r"""[bright_green]
                                                    
        ___         __        ____            ____
       /   | __  __/ /_____  / __ \___  _____/ __/
      / /| |/ / / / __/ __ \/ /_/ / _ \/ ___/ /_
     / ___ / /_/ / /_/ /_/ / ____/  __/ /  / __/
    /_/  |_\__,_/\__/\____/_/    \___/_/  /_/
    """
    bannerTest: str = r"""[bright_green]
                                                                            
        ___         __        ____            ____   _____            _____
       /   | __  __/ /_____  / __ \___  _____/ __/  /_   _\___   ___ /_   _\  
      / /| |/ / / / __/ __ \/ /_/ / _ \/ ___/ /_      | | / _ \ /   /  | |    
     / ___ / /_/ / /_/ /_/ / ____/  __/ /  / __/      | |/  __/ \   \  | |    
    /_/  |_\__,_/\__/\____/_/    \___/_/  /_/         |_|\___/  /___/  |_|                                                                              
    """
    defaultCFGFileName: str = "config.ini"

    def __init__(self, inFile: str = None):
        isFileNone = (inFile is None)
        fileExists = False if (isFileNone is True) else os.path.exists(inFile)
        if fileExists:
            self.cfg = self._loadConfigFile(inFile=inFile)
            self.inFile = self.inFile
        else:
            self.cfg = None
            self.inFile = None
        return

    def getFile(self):
        return self.inFile

    def isValid(self):
        return self._verifyConfigFile(inFile=self.inFile)

    def getConfig(self):
        return self.cfg

    def loadConfiguration(self, fileOrFolder=None):
        isFileOrFolderNone = (fileOrFolder is None)
        isFile = os.path.isfile(fileOrFolder) if (isFileOrFolderNone is False) else False
        isDirectory = os.path.isdir(fileOrFolder) if (isFileOrFolderNone is False) else False
        if isFile:
            cfgLoad = self._loadConfigFile(inFile=fileOrFolder)
        elif isDirectory:
            cfgLoad = self._loadConfigDir(inDirectory=fileOrFolder)
        else:
            cfgLoad = None
        self.cfg = cfgLoad
        return cfgLoad

    @staticmethod
    def _verifyConfigFile(inFile: str = None):
        config_template = ConfigTemplate()
        config = configparser.ConfigParser()
        config.read(inFile)
        cfgKeys = config.default.keys()
        isValidType = True
        for key, value in config_template.defaults:
            if key in cfgKeys:
                matchTypes = isinstance(config.default[key], type(value))
                isValidType = (isValidType and matchTypes)
        return isValidType

    def _loadConfigFile(self, inFile: str = None):
        # Read the config file + load into a dataclass that can be accessed in any module
        if inFile is not None and os.path.exists(inFile):
            cfgLoad = configparser.ConfigParser()
            cfgLoad.read(inFile)
            # noinspection PyProtectedMember
            cfgLoad = Config(raw_config_parser=cfgLoad)
            self.inFile = inFile
        else:
            cfgLoad = None
        return cfgLoad

    def _loadConfigDir(self, inDirectory: str = None):
        autoPerfDirectory = getAutoperfDir(directory=inDirectory)
        self.inFile = os.path.join(autoPerfDirectory, self.defaultCFGFileName)
        cfgLoad = self._loadConfigFile(inFile=self.inFile)
        return cfgLoad

    @staticmethod
    def _addGitIgnore(inDirectory: str = None):
        if inDirectory is None:
            inDirectory = os.getcwd()
        repoDirExists = os.path.exists(inDirectory)
        if repoDirExists:
            repo = git.Repo(inDirectory, search_parent_directories=False)
        else:
            repo = git.Repo(os.getcwd(), search_parent_directories=False)
        gitIgnoreFile = os.path.join(repo.working_tree_dir, '.gitignore')
        if os.path.exists(gitIgnoreFile):
            with open(gitIgnoreFile, 'a+') as f:
                f.seek(0, os.SEEK_SET)
                if len(f.read()) > 0:
                    f.write('\n')
                f.write('# ------------ Added by AutoPerf ------------ #\n')
                f.write('.autoperf\n')
                f.write('# To track configs, uncomment the following:\n')
                f.write('# .autoperf/*\n')
                f.write('# !.autoperf/config.ini\n')
                f.write('# !.autoperf/COUNTERS\n')
                f.write('# ------------------------------------------- #')
        return

    def CLI(self, inConfigFile: str = "config.ini"):
        """A CLI for initialization / configuration."""

        print()
        rprint(Panel(self.banner, padding=(0, 2), title='Welcome To', expand=False, border_style='green'))

        configfile = getAutoperfDir(inConfigFile)
        if os.path.exists(configfile):
            if not Confirm.ask(f"[red]AutoPerf has already been configured in this repository.{os.pathsep}"
                               "Would you like to start from scratch?"):
                print()
                sys.exit()
        else:
            rprint('[bright_blue]Before we can get started, we need some information.')
        print()

        mkdir_p(getAutoperfDir())

        # settings
        config_template = ConfigTemplate()
        s = dict()

        s['build'] = Prompt.ask('[italic]Enter the command you use to build your codebase',
                                default=config_template.defaults['build'])
        s['build_dir'] = Prompt.ask('[italic]Enter the path where this command should be run',
                                    default=config_template.defaults['build_dir'])
        if Confirm.ask('[italic][yellow]Would you like to clean the repository before building?'):
            s['clean'] = Prompt.ask('↪ [italic]Enter the command you use to clean your codebase',
                                    default=config_template.defaults['clean'])
        else:
            s['clean'] = ''

        s['workload'] = Prompt.ask('\n[italic]Enter the workload under test',
                                   default=config_template.defaults['workload'])
        s['workload_dir'] = Prompt.ask('[italic]Enter the path where this command should be run',
                                       default=config_template.defaults['workload_dir'])

        s['branch'] = Prompt.ask('\n[italic]Enter the name of your repository\'s main branch',
                                 default=config_template.defaults['branch'])

        if Confirm.ask("[green]\nWould you like to configure some additional advanced options?"):

            if Confirm.ask("[yellow]↪ Would you like to configure the architecture of the autoencoders?"):
                s['hidden'] = Prompt.ask('  ↪ [italic]Configure the hidden layers arranged prior to the '
                                         'latent space', default=str(config_template.defaults['hidden']))
                s['encoding'] = IntPrompt.ask('  ↪ [italic]Configure the size of the latence space',
                                              default=config_template.defaults['encoding'])
                s['activation'] = Prompt.ask('  ↪ [italic]Select the activation function to use throughout '
                                             'the network', default=config_template.defaults['activation'],
                                             choices=['tanh', 'sigmoid', 'relu', 'swish'])
                s['filename'] = Prompt.ask('  ↪ [italic]Set the name of the trained autoEncoderObj',
                                           default=config_template.defaults['filename'])

            if Confirm.ask("[yellow]↪ Would you like to configure how the autoencoders are trained?"):
                s['epochs'] = IntPrompt.ask('  ↪ [italic]Configure the number of training epochs',
                                            default=config_template.defaults['epochs'])
                s['batch_size'] = IntPrompt.ask('  ↪ [italic]Configure the minibatch size',
                                                default=config_template.defaults['batch_size'])
                s['optimizer'] = Prompt.ask('  ↪ [italic]Configure the optimizer',
                                            default=config_template.defaults['optimizer'])
                s['learning_rate'] = FloatPrompt.ask('  ↪ [italic]Configure the optimizer\'s learning rate',
                                                     default=config_template.defaults['learning_rate'])
                s['loss'] = Prompt.ask('  ↪ [italic]Configure the loss function',
                                       default=config_template.defaults['loss'])
                s['noise'] = FloatPrompt.ask('  ↪ [italic]Configure the intensity of noise added during training',
                                             default=config_template.defaults['noise'])
                s['scale_factor'] = FloatPrompt.ask('  ↪ [italic]Configure the scale factor of the HPC samples',
                                                    default=config_template.defaults['scale_factor'])

            if Confirm.ask("[yellow]↪ Would you like to configure the detection process?"):
                s['threshold'] = FloatPrompt.ask('  ↪ [italic]Set the % anomalous detection threshold',
                                                 default=config_template.defaults['threshold'])

        parser = configparser.ConfigParser()
        parser.read_string(config_template.update(s))

        with open(configfile, 'w') as f:
            parser.write(f)

        save_counters()

        self._addGitIgnore()

        rprint('\n[bright_blue]Your responses (along with some default parameters) have been saved to:')
        rprint(f'  {configfile}\n')
        return configfile

    def CLI_UnitTest(self):
        print()
        rprint(Panel(self.bannerTest, padding=(0, 1), title='Welcome To', expand=False, border_style='green'))
        testDir = os.path.abspath("autoperf/test")
        if not os.path.exists(testDir):
            testDir = os.path.abspath("test")
        repoTestDir = "CPUBenchmark"
        repoDirectoryCheck = os.path.join(testDir, repoTestDir)
        if os.path.exists(repoDirectoryCheck):
            shutil.rmtree(repoDirectoryCheck)

        from autoperf.utils import GitOperations
        testRepoClone = GitOperations(targetPath=testDir,
                                      targetDirectoryName=repoTestDir,
                                      remote_url="git@github.com:jtarango/CPUBenchmark.git",
                                      debug=False)
        testRepoClone.git_clone_simple(branchName="test")

        autoPerfDir = os.path.join(repoDirectoryCheck, '.autoperf')
        mkdir_p(autoPerfDir)
        configfile = os.path.join(autoPerfDir, 'config.ini')

        repoTestDir = os.path.join(testDir, repoTestDir)
        if not os.path.exists(repoTestDir):
            print(f"Error in cloning {repoTestDir}")

        # settings
        config_template = ConfigTemplate()
        s = dict()
        s['build'] = "make cpuBenchmark"  # config_template.defaults['build']  # @todo make all
        s['build_dir'] = repoDirectoryCheck  # testDir  # config_template.defaults['build_dir']
        s['clean'] = config_template.defaults['clean']
        s['workload'] = "make run_cpuBenchmark"  # config_template.defaults['build']  # config_template.defaults['workload']
        s['workload_dir'] = repoDirectoryCheck  # testDir  # config_template.defaults['workload_dir']
        s['branch'] = 'main'  # config_template.defaults['branch'] # @todo str(testRepoClone.baseRemoteName)
        s['hidden'] = str(config_template.defaults['hidden'])
        s['encoding'] = config_template.defaults['encoding']
        s['activation'] = config_template.defaults['activation']
        s['filename'] = config_template.defaults['filename']
        s['epochs'] = config_template.defaults['epochs']
        s['batch_size'] = config_template.defaults['batch_size']
        s['optimizer'] = config_template.defaults['optimizer']
        s['learning_rate'] = config_template.defaults['learning_rate']
        s['loss'] = config_template.defaults['loss']
        s['noise'] = config_template.defaults['noise']
        s['scale_factor'] = config_template.defaults['scale_factor']
        s['threshold'] = config_template.defaults['threshold']

        parser = configparser.ConfigParser()
        parser.read_string(config_template.update(s))

        with open(configfile, 'w') as f:
            parser.write(f)

        save_counters_path(fileLocation=autoPerfDir)

        rprint('\n[bright_blue]default parameters have been saved to:')
        rprint(f'  {configfile}\n')
        return configfile


def loadConfig(inFile: str = None):
    configObj = CreateConfiguration(inFile=inFile)
    configSettings: Config = configObj.loadConfiguration(fileOrFolder=inFile)
    return configSettings


def loadConfig_TryDetect():
    detectFileDirectory = getAutoperfDir()
    cfg: Config = None
    if os.path.exists(detectFileDirectory):
        cfg: Config = loadConfig(inFile=detectFileDirectory)
    else:
        try:
            foldersFound = findFolder(dirSignature='.autoperf')
            for folderItem in foldersFound:
                cfg: Config = loadConfig(inFile=folderItem)
        except BaseException as errorContext:
            print(f"{errorContext}")
            cfg: Config = None
    return cfg


def CLI():
    CreateConfiguration().CLI()
    return


def CLI_UnitTest():
    testCfg = CreateConfiguration()
    testCfg = testCfg.CLI_UnitTest()
    return testCfg
