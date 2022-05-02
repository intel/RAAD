# !/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Daniel Garces, Joseph Tarango
# *****************************************************************************/
import datetime
import traceback
import PySimpleGUI
import condaEnvironment

CONDA_INSTALL_VARS = ['Install', 'Update']
OPTIONS = ['Yes', 'No']


def mainWindow():
    """
    Main window layout for graphical interface.

    Args:

    Returns:

    """
    layout = [
        [PySimpleGUI.Text('Welcome to the RAAD Anaconda Environment Wizard/Manager', size=(50, 2))],
        [PySimpleGUI.Text('Are you running this GUI from the distributed executable?', size=(50, 1))],
        [PySimpleGUI.Drop(values=OPTIONS, auto_size_text=True, size=(20, 1), key="main.mode",
                          enable_events=True, default_value=OPTIONS[0]),
         PySimpleGUI.Button('Select', size=(10, 1))]]
    window = PySimpleGUI.Window("RAAD Wizard", layout)
    while True:
        event, values = window.read()
        if event is None or event == 'Exit':
            break
        if event == "Select":
            if values['main.mode'] == 'Yes':
                installerExecAppWindow()
            else:
                installerDevAppWindow()

    window.close()
    return


def installerExecAppWindow(returnLayout=False):
    """
    Graphical install application window.
    Args:
        returnLayout: returns object with gui layout.
    Returns:
        Layout object.
    """
    class buttonFunctionality:
        condaEnvInstance = None

        def __init__(self, condaEnvInstance=None):
            """
            Anaconda environment object.
            Args:
                condaEnvInstance: Anaconda instance.
            Returns:
            """
            if condaEnvInstance is None:
                condaEnvInstance = condaEnvironment.condaEnvironment()
            self.condaEnvInstance = condaEnvInstance

        def execute_installation(self, inConfiguration):
            """
            Install instance  creation
            Args:
                inConfiguration: Configuration for mode of operation
            Returns:
            """
            installationMode = inConfiguration['install.mode']

            if installationMode == "Install":
                self.condaEnvInstance.installFresh()
            elif installationMode == "Update":
                self.condaEnvInstance.anacondaUpdate()
            else:
                print("Error with the installation mode, please try again")
            return

        def createCondaEnv(self, inConfiguration):
            """
            Anaconda environment setup parsing.
            Args:
                inConfiguration: Configuration for mode of operation
            Returns:
            """
            if str(inConfiguration['create.specificationFile'])[-4:].lower() == ".yml":
                self.condaEnvInstance.condaCreateEnv(specificationFile=str(inConfiguration['create.specificationFile']))
            elif str(inConfiguration['create.specificationFile'])[-4:].lower() == ".txt":
                self.condaEnvInstance.condaLoadEnv(outFile=str(inConfiguration['create.specificationFile']),
                                                   envName=str(inConfiguration['create.envName']))
            else:
                inConfiguration['create.specificationFile'].Update(
                    values="Input must be a specification file (either .txt or .yml)")

        def unpackCondaEnv(self, inConfiguration):
            self.condaEnvInstance.targetMachineUnPack(homeCondaPath=inConfiguration['unpack.condaPath'],
                                                      tarName=inConfiguration['unpack.tarName'],
                                                      path=inConfiguration['unpack.resultPack'])

    installingFrame = PySimpleGUI.Frame(layout=[
        [PySimpleGUI.Text('Would you like to install or update Anaconda?', size=(50, 1))],
        [PySimpleGUI.Drop(values=CONDA_INSTALL_VARS, auto_size_text=True, size=(20, 1), key="install.mode",
                          enable_events=True, default_value=CONDA_INSTALL_VARS[0]),
         PySimpleGUI.Button('Execute', size=(10, 1))],
    ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Install/Update Anaconda',
        tooltip='Choose whether to install Anaconda fresh or Update current distribution')

    creatingFrame = PySimpleGUI.Frame(layout=[
        [PySimpleGUI.Text('Name for new Environment to be created (only used if specification is .txt)', size=(75, 1))],
        [PySimpleGUI.In(key="create.envName", enable_events=True)],
        [PySimpleGUI.Text('Browse for file containing specification of the environment (either .txt or .yml)',
                          size=(75, 1))],
        [PySimpleGUI.In(key='create.specificationFile', enable_events=True),
         PySimpleGUI.FileBrowse(size=(10, 1), target='create.specificationFile')],
        [PySimpleGUI.Button('Create', size=(10, 1))]
    ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Anaconda Environment Creation',
        tooltip='Select the specification file to generate an environment')

    unpackingFrame = PySimpleGUI.Frame(layout=[
        [PySimpleGUI.Text('Name for tar file to be unpacked (must be in the same directory as this script)',
                          size=(75, 1))],
        [PySimpleGUI.In(key="unpack.tarName", enable_events=True)],
        [PySimpleGUI.Text('Browse for folder that contains Anaconda Home Location', size=(75, 1))],
        [PySimpleGUI.In(key='unpack.condaPath', enable_events=True),
         PySimpleGUI.FolderBrowse(size=(10, 1), target='unpack.condaPath')],
        [PySimpleGUI.Text('Browse for folder where uncompressed files will be stored', size=(75, 1))],
        [PySimpleGUI.In(key='unpack.resultPath', enable_events=True),
         PySimpleGUI.FolderBrowse(size=(10, 1), target='unpack.resultPath')],
        [PySimpleGUI.Button('Unpack', size=(10, 1))]
    ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Unpacking Anaconda Environment',
        tooltip='Type in the name of the the tar file to be unpacked and browse for the location of the anaconda home '
                'directory and the folder where the files will be extracted')
    installationTab = [[installingFrame]]
    creationTab = [
        [PySimpleGUI.Text('2.1 Create your environment based on specification file (.txt or .yml)', size=(88, 1)),
         PySimpleGUI.Text('2.2 Create your environment based on packed environment (.tar)', size=(85, 1))],
        [creatingFrame,
         PySimpleGUI.Text('or', size=(10, 1), justification='center'),
         unpackingFrame]]
    layout = [
        [PySimpleGUI.Text('Tabs for all the processes available in the manager', size=(75, 1))],
        [PySimpleGUI.TabGroup([[
            PySimpleGUI.Tab('1. Anaconda Installation Phase', installationTab),
            PySimpleGUI.Tab('2. Conda Environment Creation Phase', creationTab),
        ]])]
    ]

    if returnLayout is True:
        return layout
    window = PySimpleGUI.Window('RAAD Environment Manager', layout)
    buttons = buttonFunctionality()
    while True:
        event, values = window.read()
        if event is None or event == 'Exit':
            break
        elif event == 'Execute':
            buttons.execute_installation(inConfiguration=values)
        elif event == 'Create':
            buttons.createCondaEnv(inConfiguration=values)
        elif event == 'Unpack':
            buttons.unpackCondaEnv(inConfiguration=values)
    window.close()
    return


def installerDevAppWindow(returnLayout=False):
    """
    Anaconda environment setup for developers
    Args:
        returnLayout: Installer type object.
    Returns:
    """
    class buttonFunctionality:
        condaEnvInstance = None

        def __init__(self, condaEnvInstance=None):
            """
            Anaconda button environment object.
            Args:
                condaEnvInstance: Anaconda instance.
            Returns:
            """
            if condaEnvInstance is None:
                condaEnvInstance = condaEnvironment.condaEnvironment()
            self.condaEnvInstance = condaEnvInstance
            return

        def execute_installation(self, inConfiguration):
            """
            Anaconda environment object for updating or installing.
            Args:
                inConfiguration: configuration setup
            Returns:
            """
            installationMode = inConfiguration['install.mode']
            if installationMode == "Install":
                self.condaEnvInstance.installFresh()
            elif installationMode == "Update":
                self.condaEnvInstance.anacondaUpdate()
            else:
                print("Error with the installation mode, please try again")
            return

        def createCondaEnv(self, inConfiguration):
            """
            Anaconda environment object.
            Args:
                inConfiguration: configuration setup
            Returns:
            """
            if str(inConfiguration['create.specificationFile'])[-4:].lower() == ".yml":
                self.condaEnvInstance.condaCreateEnv(specificationFile=str(inConfiguration['create.specificationFile']))
            elif str(inConfiguration['create.specificationFile'])[-4:].lower() == ".txt":
                self.condaEnvInstance.condaLoadEnv(outFile=str(inConfiguration['create.specificationFile']),
                                                   envName=str(inConfiguration['create.envName']))
            else:
                inConfiguration['create.specificationFile'].Update(
                    values="Input must be a specification file (either .txt or .yml)")

        def updateCondaEnv(self, inConfiguration):
            """
            Anaconda environment object update.
            Args:
                inConfiguration: configuration setup
            Returns:
            """
            if str(inConfiguration['update.specificationFile'])[-4:].lower() == ".yml":
                self.condaEnvInstance.condaUpdateEnv(specificationFile=str(inConfiguration['update.specificationFile']))
            elif str(inConfiguration['update.specificationFile'])[-4:].lower() == ".txt":
                self.condaEnvInstance.condaInstallDependecies(outFile=str(inConfiguration['update.specificationFile']),
                                                              envName=str(inConfiguration['update.envName']))
            else:
                inConfiguration['update.specificationFile'].Update(
                    values="Input must be a specification file (either .txt or .yml)")

        def saveCondaEnv(self, inConfiguration):
            """
            Anaconda environment object save.
            Args:
                inConfiguration: configuration setup
            Returns:
            """
            if str(inConfiguration['save.specificationFile'])[-4:].lower() == ".yml":
                self.condaEnvInstance.condaExportEnv(outFile=str(inConfiguration['save.specificationFile']))
            elif str(inConfiguration['save.specificationFile'])[-4:].lower() == ".txt":
                self.condaEnvInstance.condaSaveEnv(outFile=str(inConfiguration['save.specificationFile']))
            else:
                inConfiguration['save.specificationFile'].Update(
                    values="Input must be a specification file (either .txt or .yml)")

        def deleteCondaEnv(self, inConfiguration):
            """
            Anaconda environment object setting delete.
            Args:
                inConfiguration: configuration setup
            Returns:
            """
            self.condaEnvInstance.condaDeleteEnv(str(inConfiguration['delete.envName']))
            return

        def cloneCondaEnv(self, inConfiguration):
            """
            Anaconda environment object clone setting delete.
            Args:
                inConfiguration: configuration setup
            Returns:
            """
            self.condaEnvInstance.condaCloneEnv(envName=str(inConfiguration['clone.envName']),
                                                newEnv=str(inConfiguration['clone.newEnv']))
            return

        def packCondaEnv(self, inConfiguration):
            """
            Anaconda environment object setting packer.
            Args:
                inConfiguration: configuration setup
            Returns:
            """
            self.condaEnvInstance.sourceMachinePack(tarName=str(inConfiguration['pack.tarName']),
                                                    envName=str(inConfiguration['pack.envName']))
            return

        def unpackCondaEnv(self, inConfiguration):
            """
            Anaconda environment object setting unpacker.
            Args:
                inConfiguration: configuration setup
            Returns:
            """
            self.condaEnvInstance.targetMachineUnPack(homeCondaPath=inConfiguration['unpack.condaPath'],
                                                      tarName=inConfiguration['unpack.tarName'],
                                                      path=inConfiguration['unpack.resultPack'])

    installingFrame = PySimpleGUI.Frame(layout=[
        [PySimpleGUI.Text('Would you like to install or update Anaconda?', size=(50, 1))],
        [PySimpleGUI.Drop(values=CONDA_INSTALL_VARS, auto_size_text=True, size=(20, 1), key="install.mode",
                          enable_events=True),
         PySimpleGUI.Button('Execute', size=(10, 1))],
    ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Install/Update Anaconda',
        tooltip='Choose whether to install Anaconda fresh or Update current distribution')

    creatingFrame = PySimpleGUI.Frame(layout=[
        [PySimpleGUI.Text('Name for new Environment to be created (only used if specification is .txt)', size=(75, 1))],
        [PySimpleGUI.In(key="create.envName", enable_events=True)],
        [PySimpleGUI.Text('Browse for file containing specification of the environment (either .txt or .yml)',
                          size=(75, 1))],
        [PySimpleGUI.In(key='create.specificationFile', enable_events=True),
         PySimpleGUI.FileBrowse(size=(10, 1), target='create.specificationFile')],
        [PySimpleGUI.Button('Create', size=(10, 1))]
    ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Anaconda Environment Creation',
        tooltip='Select the specification file to generate an environment')

    updatingFrame = PySimpleGUI.Frame(layout=[
        [PySimpleGUI.Text('Browse for file containing specification of the environment (either .txt or .yml)',
                          size=(75, 1))],
        [PySimpleGUI.In(key='update.specificationFile', enable_events=True),
         PySimpleGUI.FileBrowse(size=(10, 1), target='update.specificationFile')],
        [PySimpleGUI.Button('Update', size=(10, 1))]
    ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Anaconda Environment Update',
        tooltip='Select the specification file to update an existing environment')

    savingFrame = PySimpleGUI.Frame(layout=[
        [PySimpleGUI.Text(
            'Name of the file where the specification will be saved (.txt or .yml suffix must be included)',
            size=(75, 1))],
        [PySimpleGUI.In(key="save.specificationFile", enable_events=True)],
        [PySimpleGUI.Button('Save', size=(10, 1))]
    ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Saving Anaconda Environment',
        tooltip='Type in the name of the environment to be saved')

    deletingFrame = PySimpleGUI.Frame(layout=[
        [PySimpleGUI.Text('Name for new Environment to be deleted', size=(75, 1))],
        [PySimpleGUI.In(key="delete.envName", enable_events=True), PySimpleGUI.Button('Delete', size=(10, 1))],
    ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Deleting Anaconda Environment',
        tooltip='Type in the name of the environment to be deleted')

    cloningFrame = PySimpleGUI.Frame(layout=[
        [PySimpleGUI.Text('Name for Environment to be cloned', size=(75, 1))],
        [PySimpleGUI.In(key="clone.envName", enable_events=True)],
        [PySimpleGUI.Text('Name for target environment (new environment)', size=(75, 1))],
        [PySimpleGUI.In(key="clone.newEnv", enable_events=True)],
        [PySimpleGUI.Button('Clone', size=(10, 1))]
    ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Cloning Anaconda Environment',
        tooltip='Type in the name of the environment to be cloned as well as the target environment')

    packingFrame = PySimpleGUI.Frame(layout=[
        [PySimpleGUI.Text('Name for Environment to be packed', size=(75, 1))],
        [PySimpleGUI.In(key="pack.envName", enable_events=True)],
        [PySimpleGUI.Text('Name for tar file to be generated', size=(75, 1))],
        [PySimpleGUI.In(key="pack.tarName", enable_events=True)],
        [PySimpleGUI.Button('Pack', size=(10, 1))]
    ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Packing Anaconda Environment',
        tooltip='Type in the name of the environment to be packed as well as the name for the tar file to be generated')

    unpackingFrame = PySimpleGUI.Frame(layout=[
        [PySimpleGUI.Text('Name for tar file to be unpacked (must be in the same directory as this script)',
                          size=(75, 1))],
        [PySimpleGUI.In(key="unpack.tarName", enable_events=True)],
        [PySimpleGUI.Text('Browse for folder that contains Anaconda Home Location', size=(75, 1))],
        [PySimpleGUI.In(key='unpack.condaPath', enable_events=True),
         PySimpleGUI.FolderBrowse(size=(10, 1), target='unpack.condaPath')],
        [PySimpleGUI.Text('Browse for folder where uncompressed files will be stored', size=(75, 1))],
        [PySimpleGUI.In(key='unpack.resultPath', enable_events=True),
         PySimpleGUI.FolderBrowse(size=(10, 1), target='unpack.resultPath')],
        [PySimpleGUI.Button('Unpack', size=(10, 1))]
    ], relief=PySimpleGUI.RELIEF_SUNKEN, title='Unpacking Anaconda Environment',
        tooltip='Type in the name of the the tar file to be unpacked and browse for the location of the anaconda home '
                'directory and the folder where the files will be extracted')

    installationTab = [[installingFrame]]
    creationTab = [[creatingFrame, unpackingFrame]]
    savingTab = [[savingFrame, packingFrame]]
    miscTab = [[cloningFrame, deletingFrame], [updatingFrame]]
    layout = [
        [PySimpleGUI.Text('Tabs for all the processes available in the manager', size=(75, 1))],
        [PySimpleGUI.TabGroup([[
            PySimpleGUI.Tab('1. Anaconda Installation Phase', installationTab),
            PySimpleGUI.Tab('2. Conda Environment Creation Phase', creationTab),
            PySimpleGUI.Tab('3. Conda Environment Saving/Packing', savingTab),
            PySimpleGUI.Tab('4. Miscellaneous Functions', miscTab)
        ]])]
    ]

    if returnLayout is True:
        return layout
    window = PySimpleGUI.Window('RAAD Environment Manager', layout)
    buttons = buttonFunctionality()
    while True:
        event, values = window.read()
        if event is None or event == 'Exit':
            break
        elif event == 'Execute':
            buttons.execute_installation(inConfiguration=values)
        elif event == 'Create':
            buttons.createCondaEnv(inConfiguration=values)
        elif event == 'Update':
            buttons.updateCondaEnv(inConfiguration=values)
        elif event == 'Save':
            buttons.saveCondaEnv(inConfiguration=values)
        elif event == 'Delete':
            buttons.deleteCondaEnv(inConfiguration=values)
        elif event == 'Clone':
            buttons.cloneCondaEnv(inConfiguration=values)
        elif event == 'Pack':
            buttons.packCondaEnv(inConfiguration=values)
        elif event == 'Unpack':
            buttons.unpackCondaEnv(inConfiguration=values)
    window.close()
    return


if __name__ == '__main__':
    """Performs execution delta of the process."""
    pStart = datetime.datetime.now()
    try:
        mainWindow()
    except Exception as errorMain:
        print(f"Fail End Process: {errorMain}")
        traceback.print_exc()
    qStop = datetime.datetime.now()
    print(f"Execution time: {str(qStop - pStart)}")
