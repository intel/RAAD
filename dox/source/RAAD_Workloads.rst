RAAD Extended Workloads
#######################
Several of RAAD's capabilities require time for training machine learning models. Learn how to setup a process to run RAAD overnight with the Linux screen command.

It is ideally best if you run RAAD on the high performance Linux server. Python Libraries (i.e., PyLaTeX) may or may not work properly on Windows. This tutorial is meant for running RAAD on the Linux server.

Server.rst

Step-by-step guide
******************
# RAAD may still be ran on Windows, though the following steps are no longer applicable. If it is your first time using RAAD and you plan on using Windows, please perform steps of the Information for Developers of RAAD section in Getting Started with RAAD Tools wiki to download RAAD and setup necessary Python environments.
    - Please perform this step instead of step 7 in the Getting Started with RAAD Tools wiki mentioned above. After the creation of the environment finishes, you need to clone the RAAD repository by using git. If you do not have git please install it then open a terminal and execute the following command:

    .. code-block::

        git clone --recursive https://github.com/Intel/RAAD.git

# If it is your first time using RAAD on the a server:
    - Begin by ensuring the grant of access to the server and to the necessary RAAD repositories.
    - Use a terminal to execute the ssh command to log into your profile on the RAAD server.
    - I.E. `ssh yourRADServerUserName@ServerName`
    - Users may have to use Git Bash to login through ssh if you are remotely accessing the server from a Windows machine.
    - Once you have accessed the server and logged into your profile, execute the following command to download all necessary repositories (shown below):

    .. code-block::

        git clone --recursive https://github.com/Intel/RAAD.git

# Create the file credentials.conf under the directory path RAAD_Sandbox/RAAD/.raadProfile/
    - Once this file has been created, use a text editor to add two lines: add your username to the first line of the file, followed by your password on the second line of the file. This file becomes a hidden credentials file used to access the Debug Handbook Wiki as well as the JIRA database. See the "fakecredentials.conf" file for an example.
# If you have your own set/time-series of telemetry binaries you would like to process, do so by:
    - First, renaming the original inputSeries/ directory within RAAD_Sandbox/RAAD/data/ to some other name, add your set of telemetry binaries into a new directory named inputSeries, and move that directory into the same data directory as the original inputSeries/ (i.e., move into RAAD_Sandbox/RAAD/data/)
# After setting up the server and obtaining the RAAD repository:
    - Connect to the server and log into your profile
    - Enter the command:  screen into the terminal to start a new screen session, then hit Enter again (shown below).

    - Assuming you cloned the repository into your home directory on your RAAD server profile, enter the following command to change the correct directory for execution (shown below):

    .. code-block::

        cd ~/RAAD/src

    - The RAAD server should contain Python environments necessary for running RAAD. To activate, enter: conda activate RAAD
    - Enter the command: `python main.py` to execute RAAD through one simple API (i.e., autoModuleAPI). Once RAAD begins to run, press "ctrl + a" on your keyboard, release, then press "d" once to detach from the screen session.
    - At this point, the execution will continue to run even after you log out of the server. You may now logout by entering exit.
    - At a later time, you can check the progress of the execution and/or observe the results and output after execution. Connect to the server once again and log into your profile (step 2 above). Then, to resume the previous screen session, enter screen -r (shown below).
    - Once you are finished with the session, you may enter the command: exit to terminate the screen session, and enter exit again to log out of the RAAD server.
# By using screen, you may set up workloads to be run remotely in the background on the RAAD Server, and may resume the process which was used to execute RAAD at a later time.
