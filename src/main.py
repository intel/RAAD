#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, \
    unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import sys, os, datetime, traceback, optparse, pprint, faulthandler
import tensorflow
import pathlib, time
from src.software.utilsCommon import findAll, tryFolderDetect
from src.software.debug import whoami

# Setup base twidl directory
twidl_dir_name = 'twidl'
twidl_active_set = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'software', twidl_dir_name))
twidl_active_path = twidl_active_set if os.path.isdir(twidl_active_set) else None

# Research and Development Product lists
pTokenADP = 'ADP'
pTokenCDR = 'CDR'
supportedDevices = {pTokenADP: 'ADP_UV',
                    pTokenCDR: 'CDR_DA'}


def findAutoParser(autoParsePath: str = None, deviceType: str = None):
    """
    Using the parser path parameter, will use scan utility to get the devices model and firmware. Based on the devices it will return a path.

    Args:
        autoParsePath: path of the ctype auto parsers
        deviceType: product class supported

    Returns:
        Returns the found path or None
    """
    trySets = [['Auto-Parse', 'decode'],
               ['src', 'software', 'decode'],
               ['software', 'decode'],
               ['decode']]

    if deviceType is None:
        devicePath = supportedDevices[pTokenADP]
    elif str(deviceType) == str(pTokenADP):
        devicePath = supportedDevices[pTokenADP]
    elif str(deviceType) == str(pTokenCDR):
        devicePath = supportedDevices[pTokenCDR]
    else:
        devicePath = supportedDevices[pTokenADP]

    ## Potential Paths
    # Relative Path(s)
    #   src/software/twidl
    #   Auto-Parse/decode
    ## Windows
    # Local C Drive - C:/users/lab/Auto-Parse/decode
    # Mount U Drive - /mnt/udrive/jdtarang/Telemetry/Auto-Parse/decode
    ## Linux
    # Local Home Drive - /home/lab/Auto-Parse/decode
    # Mount U Drive    - /mnt/udrive/jdtarang/Telemetry/Auto-Parse/decode
    foundPath = autoParsePath if ((autoParsePath is not None) and os.path.isdir(autoParsePath)) else None
    if autoParsePath is None:
        for tlist in trySets:
            autoParsePath = os.path.join(*tlist)
            cPath = os.path.join(autoParsePath, devicePath)
            if not os.path.exists(cPath):
                foundPath = tryFolderDetect(cPath)
                if foundPath is None:
                    foundPath = os.path.abspath(os.path.join(os.path.dirname(__file__), autoParsePath, devicePath))
                    foundPath = tryFolderDetect(foundPath)
                else:
                    foundPath = cPath
                    break
                if foundPath is None:
                    foundPath = os.path.abspath(os.path.join(pathlib.Path.home(), autoParsePath, devicePath))
                    foundPath = tryFolderDetect(foundPath)
                else:
                    foundPath = cPath
                    break
            else:
                foundPath = cPath
                break
    return foundPath


def raad_importAutoParser(autoParsePath=None, deviceType=pTokenADP):
    """
    Using the parser path parameter, will use scan utility to get the devices model and firmware. Based on the devices it will return a path.

    Args:
        autoParsePath: path of the ctype auto parsers
        deviceType: product class supported

    Returns:
        Returns the found path or None
    """
    autoParsePath = findAutoParser(autoParsePath=autoParsePath, deviceType=deviceType)

    if os.path.exists(autoParsePath):
        sys.path.insert(1, autoParsePath)
    else:
        print("Auto-Parse Path Error... {} cannot find auto parser. ".format(autoParsePath))
    return autoParsePath


def findTWIDL(debug=False, twidlPath=twidl_active_path):
    """
    Using the parser path parameter, will use scan utility to get the devices model and firmware. Based on the devices it will return a path.

    Args:
        twidlPath: path of the tool helper parsers
        debug: flag used for development

    Returns:
        Returns the found path or None
    """
    if twidlPath is not None:
        twidlPath = os.path.abspath(twidlPath)
    else:
        # Assumed the twidl is global location
        twidlPath = os.path.abspath(os.path.join(os.path.dirname(__file__), twidl_active_path))

    if (os.path.exists(twidlPath) is False):
        # Try relative path.
        twidlPath = os.path.abspath(os.path.join(os.path.dirname(__file__), twidl_dir_name))

    if (os.path.exists(twidlPath) is False):
        # Try twidl at home.
        twidlPath = os.path.abspath(os.path.join(pathlib.Path.home(), twidl_dir_name))

    if (os.path.exists(twidlPath) is False):
        print(f"Developer note:: {twidl_dir_name} candidates are:")
        for hroot, hdirs, hfiles in os.walk(pathlib.Path.home()):
            for cdir in hdirs:
                print(os.path.join(hroot, cdir))
        time.sleep(10)
    if debug is True:
        pprint.pprint(twidlPath)
    return twidlPath


def raad_importTWIDL(debug=False, twidlPath=None):
    """
    Using the parser path parameter, will use scan for helper tools.

    Args:
        twidlPath: path of the tool helper parsers
        debug: flag used for development

    Returns:
        Returns the found path or None
    """
    twidlPath = findTWIDL(debug=debug, twidlPath=twidlPath)

    if os.path.exists(twidlPath):
        sys.path.insert(1, twidlPath)

        # we want to include the following folders in the system path
        root_folder = twidlPath
        os_folder = os.path.join(root_folder, ("win" if 'nt' == os.name else 'linux'))

        if len(sys.path) > 2 and sys.path[2] == root_folder:
            del sys.path[1]
        else:
            sys.path[1] = root_folder

        # add TWIDL os specific folder
        if 2 >= len(sys.path) or sys.path[2] != os_folder:
            sys.path.insert(2, os_folder)

        THIS_DIR = twidlPath
        while 'device.py' not in os.listdir(root_folder):
            THIS_DIR = os.path.abspath(os.path.join(THIS_DIR, os.pardir))

        sys.path.insert(0, THIS_DIR)
        print("TWIDL Path is: {}".format(twidlPath))
        del (root_folder, os_folder)
    else:
        print("TWIDL Path Error... {} cannot find TWIDL. ".format(twidlPath))
    return twidlPath


def main(options):
    ##############################################
    # Main
    ##############################################
    # print('__file__={0:<35} | __name__={1:<20} | __package__={2:<20}'.format(__file__, __name__, str(__package__)))
    # print("Path before \n{0}".format(os.environ['PATH']))
    # sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    """
    # Variable pointing to AXON executable
    export AXON_EXECUTE=$HOME/fast-tools/bin/NSGTools/DriveInfoTools/lib/exe/axon/v1.0.21/axon-linux-x64
    # AXON Token
    export AXON_TOKEN=8ff1e05b-a603-456c-8da7-0f890839016b
    # RAAD path
    export RAADBASE=~/raad/
    export RAADPATH=${RAADBASE}/src/software/TSV:${RAADBASE}/src/software/access:${RAADBASE}/src/software/parse
    export PYTHONPATH=${PYTHONPATH}:${RAADPATH}
    """
    raadImportBase = os.path.dirname(os.path.abspath(__file__))
    if options.debug:
        print("\nAdding basepath...")
        pprint.pprint(raadImportBase)
    findAll(fileType=".py", directoryTreeRootNode=None, debug=options.debug, doIt=True, verbose=options.more)

    # Add TWIDL
    if options.debug:
        print("\nAdding TWIDL path...")
    if options.twidlPath is None:
        options.twidlPath = twidl_active_path
    importTWIDLPath = tryFolderDetect(cPath=options.twidlPath)
    osPath = raad_importTWIDL(debug=options.debug, twidlPath=importTWIDLPath)
    findAll(fileType=".py", directoryTreeRootNode=osPath, debug=options.debug, doIt=True, verbose=options.more)
    if options.debug:
        print("OSPATH:{}".format(osPath))

    # Add Auto Parsers
    if options.debug:
        print("\nAdding AutoParser...")
    importAutoParsePath = tryFolderDetect(cPath=options.autoParsePath)
    osPath = raad_importAutoParser(autoParsePath=importAutoParsePath, deviceType=options.deviceType)
    findAll(fileType=".py", directoryTreeRootNode=osPath, debug=options.debug, doIt=True, verbose=options.more)
    if options.debug:
        print("OSPATH:{}".format(osPath))

    print("------------------------------------------------------------------------------------------")
    print("CPU, GPU, and attached compute device detection...")
    print("------------------------------------------------------------------------------------------")
    try:
        tensorflowVersion = tensorflow.version.VERSION
        vList = tensorflowVersion.split('.')
        bMajorVersion = int(vList[0]) == 2
        bMinorVersion = int(vList[1]) >= 4
        bMinorSubVersion = int(vList[2]) >= 0
        tensorFlowVersionValid = bMajorVersion and bMinorVersion and bMinorSubVersion
        if tensorFlowVersionValid:
            from tensorflow.python.client.device_lib import list_local_devices
            allDevices = list_local_devices()
            pprint.pprint(f"All devices are {allDevices}")
            from tensorflow._api.v2.config.experimental import list_physical_devices
            foundCPUs = len(list_physical_devices('CPU'))
            foundGPUs = len(list_physical_devices('GPU'))
            from tensorflow._api.v2.test import is_gpu_available
            isGPUReady = is_gpu_available(cuda_only=True)
            print(f"* Num CPUs Available: {foundCPUs}")
            print(f"# Num GPUs Available: {foundGPUs} and GPU CUDA driver ready status is {isGPUReady}")
            if foundGPUs > 0:
                computeType = 'GPU'
            else:
                computeType = 'CPU'
            physical_devices = list_physical_devices(computeType)
            tensorflow.config.experimental.set_memory_growth(physical_devices[0], enable=True)
            print(f"Loaded {computeType} config")
    except BaseException as ErrorContext:
        pprint.pprint(ErrorContext)
        pprint.pprint(whoami())
    print("------------------------------------------------------------------------------------------")

    if options.mode == 'autoModuleAPI':
        import src.software.autoModuleAPI
        src.software.autoModuleAPI.API(options)
    elif (options.mode == 'JIRACluster'):
        import src.software.autoModuleAPI
        default_faultSignature = "ASSERT_DE003"
        default_dataCntrlFolder = "Auto-Parse/datacontrol"
        default_outputFolder = "data/output"
        default_credentialsFile = ".raadProfile/credentials.conf"
        src.software.autoModuleAPI.generateJIRAClusters(debug=True,
                                                        faultSignature=default_faultSignature,
                                                        dataCntrlFolder=default_dataCntrlFolder,
                                                        outputFolder=default_outputFolder,
                                                        credentialsFile=default_credentialsFile)
    else:
        import software.gui
        software.gui.API(options=options)
    return 0


def mainFaultContext():
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--example", action='store_true', dest='example', default=False,
                      help='Show command execution example.')
    parser.add_option("--debug", action='store_true', dest='debug', default=False, help='Debug mode.')
    parser.add_option("--more", dest='more', default=False, help="Displays more options.")
    parser.add_option("--mode", dest='mode', default='JIRACluster',
                      help="Mode of Operation are: autoModuleAPI, JIRACluster, or GUI")  #
    parser.add_option("--twidlPath", dest='twidlPath', default=twidl_active_path, help="TWIDL path to import.")
    parser.add_option("--device", dest='deviceType', default=pTokenADP, help=f"Device types are [{pTokenADP}, {pTokenCDR}].")
    parser.add_option("--autoParsePath", dest='autoParsePath', default=os.path.join('Auto-Parse', 'decode'), help="Auto Parser Path.")
    parser.add_option("--faultSave", dest='faultSave', default=False, help="Enable fault context save for debug.")
    (options, args) = parser.parse_args()

    if options.faultSave:
        faultFolder = "../data/output/faultContext"
        os.makedirs(faultFolder, mode=0o777, exist_ok=True)
        faultFolder = os.path.abspath(faultFolder)
        faultFile = "fault.dump"
        faultLocation = os.path.abspath(os.path.join(faultFolder, faultFile))
        segfaultFile = open(faultLocation, 'w+')
        faulthandler.enable(file=segfaultFile, all_threads=True)
    else:
        segfaultFile = None
    try:
        main(options=options)
    except Exception as e:
        print("Fail End Process: ", e)
        traceback.print_exc()
        if options.faultSave:
            faulthandler.dump_traceback(file=segfaultFile, all_threads=True)
    finally:
        if options.faultSave:
            faulthandler.disable()
            segfaultFile.close()
        print("exiting RAAD.")
    return


if __name__ == '__main__':
    """Performs execution delta of the process."""
    p = datetime.datetime.now()
    mainFaultContext()
    q = datetime.datetime.now()
    print("Execution time: " + str(q - p))
