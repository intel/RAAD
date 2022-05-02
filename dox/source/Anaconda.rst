Anaconda & Jetbrains Environment
##################################
    - References
        - https://docs.anaconda.com/anaconda/install/silent-mode/
        - https://www.jetbrains.com/help/pycharm/installation-guide.html#silent
    - Download binary for your operating system (Choose Anaconda3-2020+)
        - https://repo.anaconda.com/archive/

Linux Ubuntu Mate x64
*********************

Anaconda Installation
============

1. Download file

    .. code-block::

        wget https://repo.anaconda.com/archive/Anaconda3-2020.07-Linux-x86_64.sh
        chmod 755 Anaconda3-2020.07-Linux-x86_64.sh
        ./Anaconda3-2020.07-Linux-x86_64.sh -b -p $HOME/anaconda3

#. Open Anaconda
#. Change to repository directory
#. Recreate and update the base environment with the best known method.
    - Please note environment_ubuntu-x86_64.yml should be `environment_{operating system}.yml`

    .. code-block::

        conda update --force conda -y
        conda update anaconda -y
        conda update --all
        conda update anaconda-navigator
        conda update python
        conda env create --file environment_ubuntu-x86_64.yml

#. To update use
    .. code-block::

        conda env update -f environment_ubuntu-x86_64.yml

Jet Brains PyCharm Debugger
=============================
- https://www.jetbrains.com/pycharm/
    .. code-block::

        sudo snap install pycharm-community --classic

Windows 10 x64
********************
Installation
============
- Open command prompt
    .. code-block::

        set url=https://repo.anaconda.com/archive/Anaconda3-2020.07-Windows-x86_64.exe
        set file=Anaconda3-2020.07-Windows-x86_64.exe
        certutil -urlcache -split -f %url% %file%
        start /wait "" Anaconda3-2020.07-Windows-x86_64.exe /InstallationType=JustMe /RegisterPython=0 /S /D=%UserProfile%\anaconda3
        start /wait "" %UserProfile%\anaconda3\Scripts\activate.bat

- Anaconda should be open or open Anaconda manually
- Change to repository directory
- Recreate and update the base environment with the best known method.
    - Please note environment_windows-x86_64.yml should be `environment_{operating system}.yml`

      .. code-block::

        conda update --force conda -y
        conda update anaconda -y
        conda update --all
        conda update anaconda-navigator
        conda update python
        conda env create --file environment_win-x86_64.yml

- To update use:
    .. code-block::

        conda env update -f environment_win-x86_64.yml

Pycharm Debugger
================
Client Config via Command Line
-------------------------------
- Create file: silent.config using create config file via command line

    .. code-block::

        echo. > "silent.config"
        echo mode=user >> "silent.config"
        echo launcher32=0 >> "silent.config"
        echo launcher64=1 >> "silent.config"
        echo updatePATH=0 >> "silent.config"
        echo jre32=1 >> "silent.config"
        echo updateContextMenu=1 >> "silent.config"
        echo python2=0 >> "silent.config"
        echo python3=0 >> "silent.config"
        echo regenerationSharedArchive=1 >> "silent.config"
        echo .py=0 >> "silent.config"

- Optionally, edit config file manually:

    .. code-block::

        ; Installation mode. It can be user or admin.
        ; NOTE: for admin mode please use "Run as Administrator" for command prompt to avoid UAC dialog or user 'admin'.
        mode=user

        ; Desktop shortcut for launchers
        launcher32=0
        launcher64=1

        ; Add launchers path to PATH env variable
        updatePATH=0

        ; Download and install jre32. This may take a few minutes.
        jre32=1

        ; Add "Open Folder as Project" to context menu
        updateContextMenu=1


        ; Download and install python. This may take a few minutes.
        python2=0
        python3=0

        ; Regenerating the Shared Archive
        ; https://docs.oracle.com/en/java/javase/11/vm/class-data-sharing.html
        regenerationSharedArchive=1

        ; List of associations. To create an association change value to 1.
        .py=0

Commandline Install
-------------------
- Installing in command line

    .. code-block::

        set url=https://download.jetbrains.com/python/pycharm-community-2021.2.2.exe
        set file=pycharm-community-2021.2.2.exe
        certutil -urlcache -split -f %url% %file%
        start /wait "" pycharm-community-2021.2.2.exe /S /CONFIG=.\silent.config /LOG=C:\JetBrains\PyCharmEdu\install.log /D=C:\JetBrains\Edu\PyCharm_2020
