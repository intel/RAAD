#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
## @package abordaleplus
# This Python script was written for NSG to automate the debug-and-trace setup for ArbordalePlus target.
#  The following assumes executing via the mpythonrun utility program provided from greenhills software.

##################################
## General Python module imports
##################################
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import os, sys, argparse, textwrap

##################################
## Global Variables
##################################
# sample usage:
# --probe 192.168.1.1
# --path C:\source\ssddev\nand\gen3
# --scripts C:\source\ssddev\nand\gen3\scripts\GHS\config
# --project C:\source\ssddev\nand\gen3\abordaleplus_da
# --executable C:\source\ssddev\nand\gen3\abordaleplus_da\abordaleplus_da.elf
# --outputfile PerformanceTraceMessages.log

class traceConfiguration(object):
    ''' Class used to generate create and fill configuration. '''
    def __init__(self):
        # Define and run argument parser
        self.parser = None
        self.parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                         epilog=textwrap.dedent('''
            Environment Variables:
                Definitions:
                    $MULTI         - Green Hills Software Debugger path.
                    $MULTI_PATH    - Green hills software root path.
                    $PROBE         - Probe type being used. The main probes are V3-V4 serial super trace.
                    $CS_ROOT       - Repository location on the development machine.
                    $WORKING_PATH  - Repository path to the built projects.
                    $PROJECT_PATH  - Repository path to the build object.
                    $PROBE_SCRIPTS - Repository path to the source code for probe automation.
                    $ELF_EXE       - Project type from compiled source code.
                    $ELF_PATH      - Project path for the target build elf file.

                Examples:
                    $MULTI         = multi_714
                    $MULTI_PATH    = c:\ghs
                    $PROBE         = hsst
                    $CS_ROOT       =  C:\Source\ssddev
                    $WORKING_PATH  = $CS_ROOT\nand\gen3\projects
                    $PROJECT_PATH  = $WORKING_PATH\projects\objs
                    $PROBE_SCRIPTS = scripts\GHS\config
                    $ELF_EXE       = abordaleplus_da
                    $ELF_PATH      = $PROJECT_PATH\$ELF_EXEC\$ELF_EXEC.elf
                                 '''))
        (self.argGrp) = None
        (self.argGrp) = (self.parser).add_argument_group(title='Trace Target Configuration')
        (self.argGrp).add_argument("--probe",                           dest='probeParam',   metavar='<BINDIR>',     default= None,  help='Probe IP address or name. 168.192.1.1 or DarthVader')
        (self.argGrp).add_argument("--path",                            dest='pathParam',    metavar='<REPOLOC>',    default= None,  help='Repository Location folder. C:\source\ssddev\nand\gen3')
        (self.argGrp).add_argument("--scripts",                         dest='scriptParam',  metavar='<SCRIPTLOC>',  default= None,  help='Script location folder. C:\source\ssddev\nand\gen3\scripts\GHS\config')
        (self.argGrp).add_argument("--project",                         dest='projectParam', metavar='<PROJECTLOC>', default= None,  help='Project folder location. C:\source\ssddev\nand\gen3\abordaleplus_da')
        (self.argGrp).add_argument("--executable",                      dest='exeParam',     metavar='<EXELOC>',     default= None,  help='Executable location. C:\source\ssddev\nand\gen3\abordaleplus_da\abordaleplus_da.elf')
        (self.argGrp).add_argument("--debug",      action='store_true', dest='debugParam',                           default= False, help='Option to use debug mode.')
        (self.argGrp).add_argument("--verbose",    action='store_true', dest='verboseParam',                         default= False, help='Enhanced messages of execution.')
        (self.argGrp).add_argument("--outputfile",                      dest='outfileParam', metavar='<OUTFILE>',    default= None,  help='Saved file for logging. PerformanceTraceMessages.log')
        return

    def getArgs(self):
        (self.parser).parse_args()
        return

    def parseArgs(self):
        return (self.parser).parse_args()

    def printHelp(self):
        return (self.parser).print_help()

    def parseKnownArgs(self):
        return (self.parser).parse_known_args()

    def printAll(self):
        print(self.parser)
        print(self.argGrp) # argConfig

class probeAutomation(object):
        def __init__(self):
            print("Init of probeAutomation class")
            self.productFamily = 'ADP'
            self.asicFamily = 'SRP'
            self.asicStepping = 'C0'
            self.probeVendor = 'GHS'
            self.probeType = 'hsst'
            self.options = traceConfiguration()

        def traceEngineMain(self, argConfig=None):
            '''
            Main trace engine.
            '''
            ##################################
            # Set default values, if not specified, then normalize the path.
            ##################################
            if argConfig.probeParam is None:
                argConfig.probeParam = '10.232.113.228' # V3 = 10.232.113.228 V4 = 10.232.113.41
                print("The IP address selected is for Joe Tarango. Please reserve an IP for your probe. https://nsg-wiki.intel.com/display/NSGFWO/Longmont+Network+Information")
            if argConfig.pathParam is None:
                argConfig.pathParam     = 'C:\source\ssddev\nand\gen3'
            argConfig.pathParam = os.path.normpath(argConfig.pathParam)

            if argConfig.scriptParam is None:
                argConfig.scriptParam   = '%s\scripts\GHS\config'             % (argConfig.pathParam)
            argConfig.scriptParam = os.path.normpath(argConfig.scriptParam)

            if argConfig.projectParam is None:
                argConfig.projectParam  = '%s\projects\objs\abordaleplus_da'  % (argConfig.pathParam)
            argConfig.projectParam = os.path.normpath(argConfig.projectParam)

            if argConfig.exeParam is None:
                argConfig.exeParam      = '%s\abordaleplus_da.elf'            % (argConfig.projectParam)
            argConfig.exeParam = os.path.normpath(argConfig.exeParam)

            if argConfig.outfileParam is None:
                argConfig.outfileParam = '%s\PerformanceTraceMessages.log'    % (argConfig.pathParam)
            argConfig.outfileParam = os.path.normpath(argConfig.outfileParam)

            ##################################
            # Check for existance of path or file.
            ##################################
            if argConfig.probeParam is None:
                raise Exception("\n--probe not defined.")
            if not os.path.exists(argConfig.pathParam):
                raise Exception("\n--path not found.")
            if not os.path.exists(argConfig.scriptParam):
                raise Exception("\n--scripts not found.")
            if not os.path.exists(argConfig.projectParam):
                raise Exception("\n--project not found.")
            if not os.path.exists(argConfig.exeParam):
                raise Exception("\n--executable not found. Make sure to build firmware.")

            # Dependant files for execution of script.
            traceMBS = os.path.join(argConfig.scriptParam, 'ArbordalePlus_a0_trace.mbs')
            traceMBS = os.path.normpath(traceMBS)
            probeConfiguration = os.path.join(argConfig.scriptParam, 'probe_options_srp.ghpcfg')
            probeConfiguration = os.path.normpath(probeConfiguration)
            if not os.path.exists(traceMBS):
                raise Exception("\nMissing dependant file ArbordalePlus_a0_trace.mbs")
            if not os.path.exists(probeConfiguration):
                raise Exception("\nMissing dependant file probe_options_srp.ghpcfg")

            ##################################
            # Print the variables.
            ##################################
            if (argConfig.debugParam is True) or (argConfig.verboseParam is True):
                print('\nPrinting Parameters:')
                print('Probe='        + argConfig.probeParam)
                print(',Path='        + argConfig.pathParam)
                print(',ScriptPath='  + argConfig.scriptParam)
                print(',projectPath=' + argConfig.projectParam)
                print(',ExeFile='     + argConfig.exeParam)
                print(',OutputFile='  + argConfig.outfileParam)

            try:
                db = GHS_Debugger(workingDir=os.getcwd()) # @todo: Record working directory, greenhills function.
            except:
                pass

            ##################################
            # Print the variables.
            # Per output of components, the 4 Cortex-A53s corresponds to debugger.pid.{2, 3, 4, 5}
            # All the content within the "" of the following cmds.append() are equivalent to Arbordale.rc
            ##################################
            cmds=[]
            print("Connect to Probe/mpserv")
            cmds.append("disconnect")
            cmds.append("connect -noprocess setup=\"%s/ArbordalePlus_a0_trace.mbs\" mpserv -cfgload \"%s/probe_options_srp.ghpcfg\" -synccores -no_trace_registers %s" % (argConfig.scriptParam, argConfig.scriptParam, argConfig.probeParam))

            print("Remove previous instances of executables, if exist.")
            cmds.append("route program.core.1 {;}; if (_LAST_COMMAND_STATUS == 0x1) {echo \"Command succeed\"; route program.core.1 {quit entry}; route program.core.2 {quit entry}; route program.core.3 {quit entry}; route program.core.4 {quit entry}}")

            print("Attach %s to 4 Cortex-A53s" % argConfig.exeParam)
            cmds.append("route debugger.pid.2 {new -alias program.core.1 -bind debugger.pid.2 %s}" % argConfig.exeParam)
            cmds.append("route debugger.pid.3 {new -alias program.core.2 -bind debugger.pid.3 %s}" % argConfig.exeParam)
            cmds.append("route debugger.pid.4 {new -alias program.core.3 -bind debugger.pid.4 %s}" % argConfig.exeParam)
            cmds.append("route debugger.pid.5 {new -alias program.core.4 -bind debugger.pid.5 %s}" % argConfig.exeParam)

            if argConfig.debugParam is True:
                cmds.append("route program.core.1 {halt; load}")

            cmds.append("route program.core.1 {halt; prepare_target -verify=none}")
            cmds.append("route program.core.2 {halt; prepare_target -verify=none}")
            cmds.append("route program.core.3 {halt; prepare_target -verify=none}")
            cmds.append("route program.core.4 {halt; prepare_target -verify=none}")

            for line in cmds:
                print("MULTI> %s" % line)
                db.RunCommands(line)

            # Do not close the windows or connection in debug mode.
            if argConfig.debugParam is False:
                db.Disconnect()
                try:
                    con.CloseWindow() #@todo greenhills function.
                except:
                    pass

        def traceEngineAPI(self, argConfig):
            '''
                API to argConfig for external library usage.
                argConfig parameter is a dictionary of argConfig to override the default configuration values.
            '''
            parser = probeAutomation.traceEngineConfiguration(self)
            parser.parseArgs([]) #  Ensures the argparse.Namespace is clear.
            #print parameterList
            parser.overrideOptions(argConfig)
            return self.traceEngineMain(parser.getArgs())

def main():
    '''
        Main entrypoint for command-line.
    '''
    parser = traceConfiguration()
    parser.parseArgs()
    inArgs = parser.getArgs()
    return probeAutomation.traceEngineMain(inArgs)

if __name__ == '__main__':
    '''
        Performs execution delta of the process.
    '''
    from datetime import datetime
    p = datetime.now()
    main()
    q = datetime.now()
    print("\nExecution time: " + str(q-p))
    sys.exit(0)
