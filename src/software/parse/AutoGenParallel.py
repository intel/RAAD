#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
################################################################################################################
################################################################################################################
## Explicit Library
################################################################################################################
################################################################################################################
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
from builtins import (bytes, str, open, super, range, zip, round, input, int, pow, object)
import os, os.path, subprocess, sys, platform, threading, uuid, queue, time, signal
################################################################################################################
################################################################################################################
## Explicit importing of headers
################################################################################################################
################################################################################################################
from threading import Timer
from optparse import OptionParser

################################################################################################################
################################################################################################################
#  OS specific declarations
################################################################################################################
################################################################################################################
myenv = os.environ.copy()
platformname = platform.system()
if platformname == 'Linux':
    ghsPath = '/usr/ghs'
    exeSuffix = ''
elif (platformname == 'Windows') or ('CYGWIN_NT' in platformname):
    ghsPath = 'c:/ghs'
    exeSuffix = '.exe'
else:  # No supported environment
    sys.stdout.write("Fault in OS support" + str(platform.system()) + "\n")
    sys.stdout.write("Env paths : " + str(myenv) + "\n")
    sys.stdout.write("Sys paths : " + str(sys.path) + "\n")

################################################################################################################
################################################################################################################
##   Global Constants
################################################################################################################
################################################################################################################
extTXT = ".txt"
# GHS Compiler Interfaces
MULTIVERSION_1 = "comp_201416"
MULTIVERSION_2 = "comp_201516"
MULTIVERSION_3 = "comp_201754"
MULTIVERSION_4 = "comp_201814"
MULTIVERSION_5 = "comp_201914"

# Multi Debugger Interfaces
MULTI_DEBUGGER_VERSION_1 = "multi_614"
MULTI_DEBUGGER_VERSION_2 = "multi_616"
MULTI_DEBUGGER_VERSION_3 = "multi_714"
MULTI_DEBUGGER_VERSION_4 = "multi_716"

# Configuration to use for now.
DEFAULT_MULTI_DEBUGGER_VERSION = MULTI_DEBUGGER_VERSION_4
DEFAULT_MULTIVERSION = MULTIVERSION_4
DEFAULT_CONCURRENT = 2

ENABLE_SHELL = False  # Global shell execution mode. When enabled OS process terminate will have undesired behavior.
GO_MINOBJS = 1
GO_MAXOBJS = 342
GO_timeout = 10
GO_sleeptime = 2

GO_fwbuilddir = None
GO_projectname = None
GO_tools = None
GO_uidenumfile = None
GO_multiexeversion = None
GO_defineobjs = None
GO_media = None
GO_shell = None
GO_uidStart = 1
GO_uidStop = GO_MAXOBJS
GO_concurrent = None
GO_extradb = None
GO_debug = None
GO_verbose = None
GO_repodir = None

usage = "%s --projectname PROJ_NAME --fwbuilddir FW_BUILD_DIR --tools TELEMETRY_TOOLS_DIR --multiexeversion MULTI_VER" % (sys.argv[0])

# listADP = [4 ,5 ,6 ,8 ,9 ,10 ,12 ,15 ,16 ,17 ,18 ,19 ,20 ,21 ,22 ,23 ,24 ,25 ,26 ,27 ,29 ,30 ,31 ,32 ,33 ,42 ,43 ,44 ,45 ,46 ,47 ,48 ,49 ,50 ,51 ,52 ,53 ,54 ,55 ,56 ,58 ,61 ,62 ,66 ,67 ,68 ,69 ,70 ,71 ,72 ,73 ,74 ,75 ,76 ,78 ,80 ,82 ,83 ,85 ,86 ,87 ,88 ,90 ,92 ,93 ,94 ,95 ,96 ,100 ,101 ,102 ,109 ,110 ,126 ,127 ,132 ,135 ,136 ,137 ,138 ,139 ,140 ,141 ,142 ,143 ,144 ,145 ,146 ,147 ,148 ,149 ,150 ,151 ,152 ,153 ,154 ,155 ,156 ,157 ,158 ,159 ,160 ,161 ,171 ,175 ,176 ,177 ,179 ,180 ,181 ,182 ,183 ,186 ,187 ,190 ,191 ,192 ,193 ,194 ,195 ,198 ,199 ,202 ,208 ,209 ,210 ,211 ,214 ,215 ,217 ,218 ,219 ,220 ,221 ,222 ,223 ,227 ,228 ,230 ,231 ,232 ,233 ,240 ,241 ,248 ,253 ,291]
listADP = [8, 20, 49, 50, 51, 52, 53]


################################################################################################################
################################################################################################################
##   Global Mutators
################################################################################################################
################################################################################################################
def redefineGlobals(fwbuilddir=None, \
                    projectname=None, \
                    tools=None, \
                    uidenumfile=None, \
                    multiexeversion=None, \
                    defineobjs=None, \
                    dataobj=None, \
                    media=None, \
                    shell=None, \
                    uidStart=None, \
                    uidStop=None, \
                    concurrent=None, \
                    extradb=None, \
                    debug=None, \
                    verbose=None, \
                    repodir=None):
    global GO_fwbuilddir
    global GO_projectname
    global GO_tools
    global GO_uidenumfile
    global GO_multiexeversion
    global GO_defineobjs
    global GO_media
    global GO_shell
    global GO_uidStart
    global GO_uidStop
    global GO_concurrent
    global GO_extradb
    global GO_debug
    global GO_verbose
    global GO_repodir

    GO_fwbuilddir = fwbuilddir
    GO_projectname = projectname
    GO_tools = tools
    GO_uidenumfile = uidenumfile
    GO_multiexeversion = multiexeversion
    GO_defineobjs = defineobjs
    GO_media = media
    GO_shell = shell
    GO_uidStart = uidStart
    GO_uidStop = uidStop
    GO_concurrent = concurrent
    GO_extradb = extradb
    GO_debug = debug
    GO_verbose = verbose
    GO_repodir = repodir
    return


################################################################################################################
################################################################################################################
## Function for generating all
################################################################################################################
################################################################################################################

def procKiller(ctypeAutoGenBuild, killAllProcess=False):
    """

    Args:
        ctypeAutoGenBuild:
        killAllProcess:

    Returns:

    """

    try:
        PID = ctypeAutoGenBuild.pid
        isUnix = platform.system() != 'Windows'
        if isUnix:
            platformSignal = signal.SIGKILL
            PGID = os.getpgid(PID)
        else:
            platformSignal = signal.SIGTERM
            PGID = PID
        for childPGID in PGID.children(recursive=True):
            print("Child Process", childPGID)
            if isUnix:
                os.killpg(childPGID, platformSignal)
            else:
                os.kill(childPGID, platformSignal)
        if isUnix:
            os.killpg(PGID, platformSignal)
        else:
            os.kill(PID, platformSignal)
    except:
        # print("Failed process kill")
        if killAllProcess == True:
            allPID = os.getpid()
            procKiller(allPID)
        pass


def pAutogenAll():
    """ Example Usage:
        python A:\Source\hg\CDRLB_T2-DC\telemetry_tools> python A:\Source\hg\CDRLB_T2-DC\telemetry_tools\ctypeAutoGen.py --fwbuilddir A:\Source\hg\CDRLB_T2-DC\projects\objs\cliffdale_da --projectname cliffdale_da --tools A:\Source\hg\CDRLB_T2-DC\telemetry_tools --multiexeversion multi_716 --media NAND --defineobjs default
    """
    multidebuggerversion = DEFAULT_MULTI_DEBUGGER_VERSION
    output = None
    timeout = GO_timeout
    repodir = GO_repodir
    projectname = GO_projectname
    ctypeMedia = GO_media
    ctypeObjects = GO_defineobjs

    uidStart = None
    uidStop = None
    # if (GO_uidStart > 0) and (GO_uidStart < GO_uidStop) and GO_uidStop < GO_MAXOBJS:
    #    uidStart = GO_uidStart
    #    uidStop = GO_uidStop
    # else:
    #    uidStart = 1
    #    uidStop = GO_MAXOBJS

    # Spawn a subprocess to generate the Python C-Type parser library and wait for it to complete
    print("%s: auto gen parser dispatched." % str(projectname))
    ctypeStart = datetime.now()
    ctypePyFile = os.path.abspath(os.path.join(repodir, 'tools', 'telemetry', 'ctypeAutoGen.py'))
    ctypeBuildDir = os.path.abspath(os.path.join(repodir, 'projects', 'objs', projectname))
    ctypeToolsDir = os.path.abspath(os.path.join(repodir, 'tools', 'telemetry'))

    # Declair max size.
    ctypeObjectItemList_Pass = [] * GO_MAXOBJS
    ctypeObjectItemList_Fail = [] * GO_MAXOBJS
    # for uid in xrange(uidStart, uidStop):
    for uid in listADP:
        ctypeStartElement = datetime.now()
        print("project %s, uid %s: auto gen parser dispatch." % (str(projectname), str(uid)))
        ctypeObjects = "[" + str(uid) + "]"

        ctypeAutoGenInputs = ' --fwbuilddir ' + str(ctypeBuildDir) + \
                             ' --projectname ' + str(projectname) + \
                             ' --tools ' + str(ctypeToolsDir) + \
                             ' --multiexeversion ' + str(multidebuggerversion) + \
                             ' --media ' + str(ctypeMedia) + \
                             ' --defineobjs ' + str(ctypeObjects) + \
                             ' --parse '
        print("python ctypeautogen.py" + ctypeAutoGenInputs)

        try:
            if GO_debug is True:  ## Output all to command line!
                ctypeAutoGenBuild = subprocess.Popen([sys.executable, ctypePyFile, '--fwbuilddir', ctypeBuildDir, '--projectname', projectname, '--tools', ctypeToolsDir, '--multiexeversion', multidebuggerversion, '--media', ctypeMedia, '--defineobjs', ctypeObjects, '--parse'], shell=ENABLE_SHELL, env=myenv)
            else:  ## Output nada to command line!
                ctypeAutoGenBuild = subprocess.Popen([sys.executable, ctypePyFile, '--fwbuilddir', ctypeBuildDir, '--projectname', projectname, '--tools', ctypeToolsDir, '--multiexeversion', multidebuggerversion, '--media', ctypeMedia, '--defineobjs', ctypeObjects, '--parse'], stdin=subprocess.PIPE, stdout=output if output else subprocess.PIPE, shell=ENABLE_SHELL, env=myenv)

            timer = Timer(timeout, ctypeAutoGenBuild.kill)
            timer.start()
            ctypeAutoGenBuildCout, ctypeAutoGenBuildErr = ctypeAutoGenBuild.communicate()
            ctypeAutoGenBuild.poll()
        except:
            print("Terminated Process ID " + str(uid))
            procKiller(ctypeAutoGenBuild, True)
        finally:
            print("Normal termination Process ID " + str(uid))
            procKiller(ctypeAutoGenBuild, False)
            timer.cancel()

        if ctypeAutoGenBuild.returncode != 0:
            ctypeObjectItemList_Fail.append(str(uid))
            print("project %s, uid %s: auto gen parser fail time %s seconds" % (str(projectname), str(uid), str(datetime.now() - ctypeStartElement)))
            print("Please execute command: ")
            print("python " + ctypePyFile + ' ' + ctypeAutoGenInputs)
        else:
            ctypeObjectItemList_Pass.append(str(uid))
            print("project %s, uid %s: auto gen parser complete time %s seconds" % (str(projectname), str(uid), str(datetime.now() - ctypeStartElement)))
    print(str(projectname) + ": auto gen parser total elapsed " + str(datetime.now() - ctypeStart) + " seconds")

    # Pass list output construction
    if ctypeObjectItemList_Pass is not None:
        ObjectListPassStr = ("[")
        isFirst = True
        for item in ctypeObjectItemList_Pass:
            if isFirst:
                isFirst = False
                ObjectListPassStr = (ObjectListPassStr + item)
            else:
                ObjectListPassStr = (ObjectListPassStr + "," + item)
        ObjectListPassStr = (ObjectListPassStr + "]")
        print("PassList: " + ObjectListPassStr)
    else:
        print("PassList: Nil")

    # Fail list output construction
    if ctypeObjectItemList_Fail is not None:
        ObjectListFailStr = ("[")
        isFirst = True
        for item in ctypeObjectItemList_Fail:
            if isFirst:
                isFirst = False
                ObjectListFailStr = (ObjectListFailStr + item)
            else:
                ObjectListFailStr = (ObjectListFailStr + "," + item)
        ObjectListFailStr = (ObjectListFailStr + "]")
        print("FailList: " + ObjectListFailStr)
    else:
        print("FailList: Nil")


################################################################################################################
################################################################################################################
## Threading version (WIP)
################################################################################################################
################################################################################################################
def CAThread_construct(multidebuggerversion, timeout, uid, repodir, projectname, ctypeMedia):
    ctypeStartTime = datetime.now()
    tag = str(os.getpid()) + str(ctypeStartTime)
    uPIDName = str(uuid.uuid5(uuid.NAMESPACE_DNS, tag))
    fnameCmdline = ("ctypeAutoGen_objlog" + str(uPIDName) + extTXT)
    ctypePyFile = os.path.abspath(os.path.join(repodir, 'telemetry_tools', 'ctypeAutoGen.py'))
    ctypeBuildDir = os.path.abspath(os.path.join(repodir, 'projects', 'objs', projectname))
    ctypeToolsDir = os.path.abspath(os.path.join(repodir, 'telemetry_tools'))

    if (uid > 0) and (uid <= GO_MAXOBJS) and \
            os.path.exists(ctypePyFile) and \
            os.path.exists(ctypeBuildDir) and \
            os.path.exists(ctypeToolsDir):
        ctypeObject = "[" + str(uid) + "]"
        ctypeAutoGenInputs = ' --fwbuilddir ' + str(ctypeBuildDir) + \
                             ' --projectname ' + str(projectname) + \
                             ' --tools ' + str(ctypeToolsDir) + \
                             ' --multiexeversion ' + str(multidebuggerversion) + \
                             ' --media ' + str(ctypeMedia) + \
                             ' --defineobjs ' + str(ctypeObject)
        ctypeAutoGenBuild = subprocess.Popen([sys.executable, ctypePyFile, '--fwbuilddir', ctypeBuildDir, '--projectname', projectname, '--tools', ctypeToolsDir, '--multiexeversion', multidebuggerversion, '--media', ctypeMedia, '--defineobjs', ctypeObject], stdin=subprocess.PIPE, stdout=fnameCmdline, stderr=fnameCmdline, shell=ENABLE_SHELL, env=myenv)

        return (True, ctypeAutoGenInputs, ctypeStartTime, ctypeAutoGenBuild, fnameCmdline, multidebuggerversion, timeout, uid, repodir, projectname, ctypeMedia, ctypeObject)
    else:
        return (False, None, None, None, None, multidebuggerversion, timeout, uid, repodir, projectname, ctypeMedia, None)


def CAThread_checkConstruct(Status, ctypeAutoGenInputs, ctypeStart, ctypeAutoGenBuild, fnameCmdline, multidebuggerversion, timeout, uid, repodir, projectname, ctypeMedia, ctypeObjects):
    try:
        if (Status is False or ctypeAutoGenInputs is None or ctypeStart is None or ctypeAutoGenBuild is None or fnameCmdline is None):
            return ("Fail", multidebuggerversion, timeout, uid, repodir, projectname, ctypeMedia, ctypeObjects)
        elif (datetime.now() - ctypeStart):
            return ("Timeout", multidebuggerversion, timeout, uid, repodir, projectname, ctypeMedia, ctypeObjects)
        else:
            return ("Pending", multidebuggerversion, timeout, uid, repodir, projectname, ctypeMedia, ctypeObjects)
    except:
        return ("Fail", multidebuggerversion, timeout, uid, repodir, projectname, ctypeMedia, ctypeObjects)


def CAThreadReader(proc, outq):
    for line in iter(proc.stdout.readline, b''):
        outq.put(line.decode('utf-8'))


def CAThread_Start(StateBool, ctypeAutoGenInputs, ctypeStart, ctypeAutoGenBuild, fnameCmdline, multidebuggerversion, timeout, uid, repodir, projectname, ctypeMedia, ctypeObjects):
    outputQueue = queue.Queue()
    threadElement = threading.Thread(target=CAThreadReader, args=(ctypeAutoGenBuild, outputQueue))
    threadElement.start()
    return (queue, outputQueue, threadElement)


def CAThread_CheckLine(queue, outputQueue):
    try:
        lineRead = outputQueue.get(block=False)
        print("Reading: " + str(lineRead))
        return True
    except queue.Empty:
        print('Could not get line from output queue')
        return False


def CAThreads(multidebuggerversion, timeout, repodir, projectname, ctypeMedia, uidStart, uidStop):
    uidList = [] * (uidStop - uidStart)

    for uidElement in range(uidStart, uidStop):
        uidList.append(uidElement)

    uidThreadsActive = []
    uidThreadsComplete = []

    while (len(uidList) > 0 or len(uidThreadsActive) > 0):
        if (len(uidList) > 0) and (len(uidThreadsActive) <= GO_concurrent):
            uid = uidList.remove()
            CAThread_constructElement = CAThread_construct(multidebuggerversion, timeout, uid, repodir, projectname, ctypeMedia)
            CAThread_checkConstructElement = CAThread_checkConstruct(CAThread_constructElement.Status, \
                                                                     CAThread_constructElement.ctypeAutoGenInputs, \
                                                                     CAThread_constructElement.ctypeStartTime, \
                                                                     CAThread_constructElement.ctypeAutoGenBuild, \
                                                                     CAThread_constructElement.fnameCmdline, \
                                                                     CAThread_constructElement.multidebuggerversion, \
                                                                     CAThread_constructElement.timeout, \
                                                                     CAThread_constructElement.uid, \
                                                                     CAThread_constructElement.repodir, \
                                                                     CAThread_constructElement.projectname, \
                                                                     CAThread_constructElement.ctypeMedia, \
                                                                     CAThread_constructElement.ctypeObjects)
            CAThread_StartElement = CAThread_Start(CAThread_checkConstructElement.StateBool, \
                                                   CAThread_checkConstructElement.ctypeAutoGenInputs, \
                                                   CAThread_checkConstructElement.ctypeStart, \
                                                   CAThread_checkConstructElement.ctypeAutoGenBuild, \
                                                   CAThread_checkConstructElement.fnameCmdline, \
                                                   CAThread_checkConstructElement.multidebuggerversion, \
                                                   CAThread_checkConstructElement.timeout, \
                                                   CAThread_checkConstructElement.uid, \
                                                   CAThread_checkConstructElement.repodir, \
                                                   CAThread_checkConstructElement.projectname, \
                                                   CAThread_checkConstructElement.ctypeMedia, \
                                                   CAThread_checkConstructElement.ctypeObjects)
            CAThread_Set = (CAThread_constructElement, CAThread_checkConstructElement, CAThread_StartElement)
            print(len(CAThread_Set))
            uidThreadsActive.append(CAThread_Set)
            print("Thread for uid " + uid + " started")
        else:
            for evalThread in uidThreadsActive:
                if (evalThread.CAThread_StartElement.threadElement.isAlive()):
                    print("UID " + evalThread.CAThread_constructElement.uid, + " is Alive!")
                else:
                    uidThreadsComplete = evalThread.pop(evalThread)
                    print("Thread for uid " + uid + " started")
            time.sleep(GO_sleeptime)

    print("Active Thread Count" + len(uidThreadsActive))
    print("Complete Thread Count" + len(uidThreadsComplete))
    return


def pathParts(path):
    p, f = os.path.split(path)
    return pathParts(p) + [f] if f else [p]


################################################################################################################
################################################################################################################
## MAIN
################################################################################################################
################################################################################################################
def main():
    """Performs the auto parsing of data control to generate telemetry definitions within a python c-type."""
    parser = OptionParser(usage)
    parser.add_option("--fwbuilddir", dest='fwbuilddir', metavar='<DIR>', action='store', default=None, help='FW build directory (ex: projects/objs/alderstream_02)')
    parser.add_option("--projectname", dest='projectname', metavar='<PROJ>', action='store', default=None, help='Project name (ex: alderstream_02)')
    parser.add_option("--tools", dest='tools', metavar='<TOOLSDIR>', action='store', default=None, help='FW telemetry tools dir where bufdict.py is (ex: tools/telemetry)')
    parser.add_option("--uidenumfile", dest='uidenumfile', metavar='<UIDFILE>', action='store', default=None, help='FW file where eUniqueIdentifier enum is defined (default=datacontrol.h)')
    parser.add_option("--multiexeversion", dest='multiexeversion', metavar='<MULTIEXEVER>', action='store', default=None, help='multi.exe version (Ex: multi_716, default=auto)')
    parser.add_option("--defineobjs", dest='defineobjs', metavar='<OBJDEF>', action='store', default=None, help='Manual imput for telemetry Objects from datacontrol.h that should be defined, by euid. (ex: [0,8,9,115]). NO SPACES. If "all" defaults to ALL. ')
    parser.add_option("--dataobj", dest='dataobj', metavar='<OBJECT>', action='store', default=None, help='Process specified data object.')
    parser.add_option("--media", dest='media', metavar='<MEDIA>', action='store', default=None, help='Select media destination I.E. NAND, SXP.')
    parser.add_option("--shell", dest='shell', metavar='<SHELL>', action='store', default=False, help='Shell execution of the script.')
    parser.add_option("--uidStart", dest='uidStart', metavar='<UIDSTART>', action='store', default=None, help='Unique ID to start for range.')
    parser.add_option("--uidStop", dest='uidStop', metavar='<UIDSTOP>', action='store', default=None, help='UID to start for range.')
    parser.add_option("--concurrent", dest='concurrent', metavar='<THREADS>', action='store', default=None, help='Threads to execute on.')
    parser.add_option("--extradb", dest='extradb', metavar='<EDEBUG>', action='store_true', default=False, help='Output additional debug info.')
    parser.add_option("--debug", dest='debug', metavar='<DEBUG>', action='store_true', default=False, help='Debug mode.')
    parser.add_option("--verbose", dest='verbose', metavar='<VERBOSE>', action='store_true', default=False, help='Verbose printing for debug use.')
    parser.add_option("--repodir", dest='repodir', metavar='<RDIR>', action='store', default=None, help='FW build directory (ex: projects/objs/alderstream_02)')

    (options, args) = parser.parse_args()

    """ Example Usage:
    python AutoGenParallel.py --fwbuilddir A:\Source\hg\CDRLB_T2-DC\projects\objs\arbordaleplus_ca --projectname arbordaleplus_t2 --tools A:\Source\Code_Telemetry\telemetry-version_comments\nand\gen3\tools\telemetry --multiexeversion multi_716 --media NAND --defineobjs default
    """

    if options.fwbuilddir is None:

        # Attempt to construct path.
        cwd = os.getcwd()
        parts = pathParts(cwd)
        print("PARTS: " + str(parts))
        partsLen = len(parts)
        if partsLen >= 2:
            print(partsLen)
            partsLen = len(parts) - 2  # Remove tools and telemetry folders
            print(partsLen)
            scatteredParts = []
            for i in range(1, partsLen):
                scatteredParts.append(parts[i])
            print("Scattered parts: " + str(scatteredParts))
            print("Drive Letter: " + str(parts[0]))
            constructedPath = os.path.join(parts[0])
            for i in range(1, partsLen):
                constructedPath = os.path.join(constructedPath, parts[i])
            print("Constructed Path: " + str(constructedPath))
            if not os.path.exists(constructedPath):
                print("Path Does not exist!")
                quit(1)
            else:
                fwbuilddir = constructedPath
        else:
            print("Error in default path construction!")
            quit(1)

        if not os.path.exists(fwbuilddir):
            print("Dir " + str(fwbuilddir))
            print("Exception 1")
            quit(1)
        print("FW Build Dir: " + str(fwbuilddir))
        options.fwbuilddir = fwbuilddir

    if options.projectname is None:
        projectname = "arbordaleplus_t2"
        options.projectname = projectname

    if options.tools is None:
        tools = os.path.join(fwbuilddir, 'tools', 'telemetry')
        # tools = os.path.abspath(tools)
        if not os.path.exists(tools):
            print("Exception 2")
            quit(1)
        print("Tools Dir: " + str(tools))
        options.tools = tools
    else:
        if not os.path.exists(options.tools):
            print("Exception 3")
            quit(1)

    if options.uidenumfile is None:
        uidennumfile = "datacontrol.h"
        options.uidennumfile = uidennumfile

    if options.multiexeversion is None:
        multiexeversion = DEFAULT_MULTI_DEBUGGER_VERSION
        options.multiexeversion = multiexeversion

    if options.defineobjs is None and options.dataobj is None and options.uidStart is None and options.uidStop is None:
        uidStart = GO_MINOBJS
        options.uidStart = uidStart
        uidStop = GO_MAXOBJS
        options.uidStop = uidStop
    elif options.dataobj is not None:
        uidStart = options.dataobj
        options.uidStart = uidStart
        uidStop = options.dataobj
        options.uidStop = uidStop
    elif options.uidStart is not None and options.uidStop is not None:
        if options.uidStart > options.uidStart:
            uidStart = GO_MINOBJS
            options.uidStart = uidStart

            uidStop = GO_MAXOBJS
            options.uidStop = uidStop
    elif options.defineobjs is not None:
        print("Not handled yet " + str(options.defineobjs))
        quit(1)

    if options.media is None:
        media = "NAND"
        options.media = media

    if options.shell is None:
        shell = True
        options.shell = shell

    if options.concurrent is None:
        concurrent = DEFAULT_CONCURRENT
        options.concurrent = concurrent

    if options.extradb is None:
        extradb = False
        options.extradb = extradb

    if options.debug is None:
        debug = False
        options.debug = debug

    if options.verbose is None:
        verbose = False
        options.verbose = verbose

    if options.repodir is None:
        repodir = options.fwbuilddir
        os.path.exists(repodir)

        if not os.path.exists(repodir):
            print("Exception 4")
            quit(1)
        print("Repo Dir: " + str(repodir))
        options.repodir = repodir
    else:
        if not os.path.exists(options.repodir):
            print("Exception 5")
            quit(1)

    redefineGlobals( \
        options.fwbuilddir, \
        options.projectname, \
        options.tools, \
        options.uidenumfile, \
        options.multiexeversion, \
        options.defineobjs, \
        options.dataobj, \
        options.media, \
        options.shell, \
        options.uidStart, \
        options.uidStop, \
        options.concurrent, \
        options.extradb, \
        options.debug, \
        options.verbose, \
        options.repodir, \
        )

    pAutogenAll()
    # todo the threading code is still a work in progress
    # CAThreads(multidebuggerversion=DEFAULT_MULTI_DEBUGGER_VERSION , timeout=GO_timeout, repodir=GO_repodir,  projectname=GO_projectname, ctypeMedia=GO_ctypeMedia, uidStart = GO_uidStart, uidStop = GO_uidStop):
    quit(0)


if __name__ == '__main__':
    """Performs execution delta of the process."""
    from datetime import datetime

    p = datetime.now()
    print("\nStart Execution time: " + str(p))
    main()
    q = datetime.now()
    print("\nStop Execution time: " + str(q - p))

## @}
