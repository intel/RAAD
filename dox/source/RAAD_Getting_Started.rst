Getting Started with RAAD Tools
###############################
If it is your first time utilizing RAAD, please follow the instructions below to download and execute the required files to start developing or utilizing RAAD. There are two sections in this article:
    - one for developers.
    - one for users of RAAD.

The section for developers is directly below. The section for users can be found after the section for developers. Please note the tutorial is for Windows, the tutorial for Ubuntu/Linux will be uploaded at a later iteration of the project.

Information for Developers of RAAD:
    - As a developer you need to download the installation wizard found in the RAAD under "RAAD Executables": The wizard is named installer.exe. Once you have downloaded the file from teams, please follow the instructions below. @todo jdtarang

Instructions for the installation wizard:
*****************************************
After the download is done, run the executable. You may encounter a blue window telling you "Windows protected your PC".

.. figure:: images/GS001.png

Click on "More info" and then on the new button "Run Anyway".

.. figure:: images/GS002.png

Once the executable is running, you should see a background terminal window with all the warning and info statements for the wizard executable. If the executable runs correctly, a window like the one shown below should pop-up on top of the terminal window. Select "Yes" on the first drop down menu (as the wizard is being run directly from the executable), and continue with the other steps.

.. figure:: images/GS003.png

    Note: Make sure you click on "Select" so that the GUI registers the option chosen in the drop down menu.

After you have accessed the second screen, install Anaconda by choosing the "install" option from the drop down menu and clicking the "Execute" button shown below. The Anaconda executable will be downloaded and the installer will be launched. Accept the terms and conditions and don't change any of the options while installing anaconda (click on next until you reach the installation). Wait for the installation to finish and then return to RAAD installation Wizard

.. figure:: images/GS004.png

    Note: If for some reason you already had Anaconda installed in your device, you can update it to the latest version by choosing the "update" option in the drop down menu and clicking the "Execute" button shown below.

.. figure:: images/GS005.png

    Note: If the wizard starts crashing before Anaconda gets updated/installed, please check your connection to the internet and try again. If the problem persists, please manually download anaconda by going to https://www.anaconda.com/products/individual

Download the environment configuration file found here: environment_win-x86_64.yml

After the file has been download into your local machine, click on the tab titled "2. Conda Environment Creation Phase" to change to the next tab and start the environment creation process. The tab looks like the one displayed below

.. figure:: images/GS006.png

Once you are in the "Conda Environment Creation Phase" tab, use the "Anaconda Environment Creation" tool to create the environment using the .yml that you downloaded in step 3. To create the environment, you need to click on the "Browse" button, which will display a navigator window as shown below. Use this navigation window to locate your copy of "environment_win32.yml" and click the open button to insert the path in the input line.

.. figure:: images/GS007.png

.. figure:: images/GS008.png

Once the path is in the input line, click on the create button and wait for the process to finish. If the environment was created successfully, a success message like the one displayed below will be shown in the background terminal window.

.. figure:: images/GS009.png

    Note: The main wizard GUI will be frozen while this process executes. Look at the background terminal window to check for progress, but do not close the wizard window as this will terminate the process and might affect future installation attempts.

If you find a proxy error, please follow the following instructions, which are based on the initial solution proposed by Joe Tarango here:
- Look for env in your search bar near the lower left of your screen. Go to "Edit the System Environment Variables" as shown below.

.. figure:: images/GS010.png

- Once this configuration opens, click "Yes" on the pop-up window.

.. figure:: images/GS011.png

- Click on "Environment Variables" as shown below.

.. figure:: images/GS012.png

- Click on the "New..." button for System variables and then add the following 3 variables as shown in the pictures below. Please consider that the examples below are for configuring the proxy with the US network. Change your configuration accordingly to reflect the location of the proxy that you want to utilize. Please refer to the code below for the easy cut and paste variable values.

.. code-block:: bash

        HTTPS_PROXY
        https://proxy-chain.com:2
        NO_PROXY
        localhost,192.168.0.0/16,172.16.0.0/12,127.0.0.0/8,10.0.0.0/8
        HTTP_PROXY
        http://proxy-chain.com:1

.. figure:: images/GS013.png

.. figure:: images/GS014.png

.. figure:: images/GS015.png

- Open an Anaconda3 Prompt (it should have been installed during the Anaconda installation), and type: where .condarc.

.. figure:: images/GS016.png

        Note:  If there is no .condarc, please create this file inside C:\Users\<your-user>\, where <your-user> corresponds to the user name that you are utilizing on your local machine.

.. figure:: images/GS017.png

- Navigate to the file location and open the file with your editor of choice (emac, vim, notepad++, etc). Modify your file to resemble the file shown below.

.. code-block::

        channels:
          - conda-forge
          - defaults
          - intel
          - pytorch
          - anaconda
          - bioconda
          - mkl

        ssl_verify: true
        allow_other_channels: true

        # Proxy settings: http://[username]:[password]@[server]:[port]
        proxy_servers:
        http: http://proxy-chain.com:1
        https: https://proxy-chain.com:2

        # Implies always using the --yes option whenever asked to proceed
        always_yes: true

        # Auto updating of dependencies
        update_dependencies: true

        # Environment variables to add configuration to control the number of threads. Choose for you machine.
        default_threads: 4

        # Update conda automatically
        auto_update_conda: true

        # Enable certain features to be tracked by default.
        track_features:
        - mkl

        # pip_interop_enabled (bool)
        #   Allow the conda solver to interact with non-conda-installed python packages.
        pip_interop_enabled: true

        # Show channel URLs when displaying what is going to be downloaded.
        show_channel_urls: true

        #   Opt in, or opt out, of automatic error reporting to core maintainers.
        #   Error reports are anonymous, with only the error stack trace and information given by `conda info` being sent.
        report_errors: false


- If you don't have it installed, please install the C++ Redistributable included in the Visual Studio 2019, which can be found here: https://visualstudio.microsoft.com/downloads/. After the download and the installation. Close all the installers and restart your computer. After your computer reboots, open the RAAD installation wizard again and try the environment creation againy.

- If the issues persist, uninstall anaconda by following the instructions in https://docs.anaconda.com/anaconda/install/uninstall/, kill the RAAD installation Wizard and start again from step 1.

- If you face additional issues with anaconda not described in this tutorial, please use the following list to manually install the packages in the conda prompt. Navigate to Anaconda Prompt and execute each of the following commands independently. Wait for the command to complete its execution before running the next command

.. code-block::

    conda create --name RAAD2.0 python=3.7
    conda activate RAAD2.0
    conda uninstall pip
    conda install pip=20.2.4=py37_0
    conda install wgetter
    conda install pandas=1.0.5
    conda install -c conda-forge scikit-learn
    conda install statsmodels
    conda install -c anaconda psutil
    conda install -c conda-forge gputil
    conda install -c anaconda cryptography
    conda install -c anaconda pycrypto
    conda install -c anaconda urllib3
    conda install -c conda-forge atlassian-python-api
    conda install -c conda-forge jira
    conda install -c conda-forge pyinstaller
    pip install matplotlib==3.3.1
    pip install tensorflow==2.3.0
    pip install gnupg
    pip install PyLaTeX
    pip install tinyaes
    pip install PySimpleGUI
    pip install tornado
    pip install pycairo
    pip install unidecode
    pip install sentence-transformers

- After the creation of the environment finishes, you need to clone the RAAD repository by using git. If you do not have git, please go here to download it. Open a git terminal (as shown below), and execute the following command:

.. figure:: images/GS018.png

.. code-block::

        git clone https://github.com/Intel/RAAD.git

- After the repo has been cloned, close the installation wizard and the git bash terminal. Open an Anaconda3 Prompt (it should have been installed during the Anaconda installation) and activate the environment by executing conda activate RAAD2.0

.. figure:: images/GS020.png

.. figure:: images/GS021.png

- Use the anaconda prompt to navigate to the location of the recently cloned "RAAD" repo and start developing using emac, vim, or your IDE of choice (I personally recommend PyCharm, which has a ton of useful features for developing in Python). If you decide to use PyCharm, you might need to open the repo using their interface, so it is properly initialized as a PyCharm project and you can use the embedded terminal for git and executing your scripts.

- If you want to easily manage your environments, navigate inside the repo to src/ and then run the installer GUI by utilizing the following command once you are inside src:  python installer.py

    .. figure:: images/GS022.png

    - Select "No" in the first window for the installation wizard

    .. figure:: images/GS023.png

    - utilize the other miscellaneous functionalities that we have included to facilitate environment management for RAAD.

    .. figure:: images/GS024.png

Information for Users of RAAD
*****************************
As an user of RAAD, you need to access the GUI to run the functionality of our system,. There are two choices for running the GUI:

    - Follow the instructions for developers all the way to steps above. Once you have a copy of the repo in your machine, run the main.py script by executing the following command from Anaconda3 prompt (with the right environment activated), or from your IDE of choice (as long as you are using the right environment for the interpreter) - please remember that you need to navigate to src/ before running the command: python main.py --mode 1

        - After around 30 seconds of automatic set-up, the system will generate a window like the one displayed below. Follow the subsection "Instructions for the GUI" for more information on how to operate the GUI.

        .. figure:: images/GS025.png

    - Create or use the GUI executable. @todo jdtarang folder inside the RAAD teams channel:  The GUI is named gui.exe. Once you have the executable and its accompanying folder, make sure you save them both to the same location in your machine to allow the executable to operate correctly. The software file should contain a single file (the logo for the GUI), please make sure the logo is directly inside "software" and not nested inside other folders. To open and run the executable, just double-click on it.

        - You may encounter a blue window telling you "Windows protected your PC". Click on "More info" and then on the new button "Run Anyway"

        .. figure:: images/GS026.png


        - Follow the subsection "Instructions for the GUI" for more information on how to operate the GUI.

        .. figure:: images/GS027.png

            Note: Method 1 is preferable to guarantee that you get all the latest changes and recent code pushes that are constantly being added to the repo to improve the system functionality; however, method 2 provides a stable baseline with the basic functionality at the time of writing.

Instructions for the GUI:
==========================

The GUI has several sections at the time of writing, all of which will be covered below to help users more efficiently utilize RAAD. Remember that after running each section, the GUI will be frozen until the process finish running. To see the progress and potential warnings printed by each section, please refer to the background terminal window that pops up after the GUI executable is run. If when the GUI window launches, it does not display a sideways scrolling bar, please exit full-screen and re-enter it, so that the interface refreshes correctly and adjusts to your screen size and resolution.

Load and Probe Drive for Data Collection
-----------------------------------------

.. figure:: images/GS028.png

        Important note: To run this section successfully, you need to execute the gui.exe as admin, so that IOMeter can operate successfully

This section of the GUI helps the user utilize a workload to load the specified drive before collecting telemetry data. For convenience, an additional option for parsing the collected telemetry data is added, so that the user can obtain text files instead of binary files as the output of this section. The customizable inputs in this section are:

    #. Drive Workload Configuration: path to the input file where the workload configuration is stored
    #. SSD Number: Integer for the drive number from which to pull telemetry data
    #. SSD Name: String for name of device interface to get data from
    #. Telemetry Pull Identifier: String for the name of the data set that corresponds to the telemetry pull to be executed
    #. Output Directory: path to the output directory where the binaries from the telemetry pull will be stored
    #. Volume Label (Windows Specific): String for the label to be used on the disk volume
    #. Volume Allocation Unit (Windows Specific): String for the volume allocation unit size
    #. Volume File System (Windows Specific): String for the name of the file system to be used in the disk volume
    #. Volume Letter (Windows Specific): String for the letter to be assigned to the disk volume
    #. Partition Style (Windows Specific): String for the name of the partition style to be used in the specified disk
    #. Partition Drive (Windows Specific): Flag to indicate if the program should partition the drive using the given parameters
    #. Prep Drive (Linux Specific): Flag to indicate if the program should prep the drive before loading it
    #. Parse Binary Files: Flag to parse the telemetry binaries pulled from the drive

Data Collect or Parse
---------------------

.. figure:: images/GS029.png

This section of the GUI helps the user collect and parse binary files for telemetry. The resulting files after the parsing are text files containing all the information previously stored in the binary telemetry files. The customizable inputs in this section are:

    #. Usage Case for Intel: This dropdown menu specifies the mode to be utilized. "PARSE" is for parsing previously collected telemetry data. "CLI", "IMAS", and "TWIDL" are all for collecting telemetry data from a specified SSD device. While "CLI" is the most general method for collecting telemetry, "IMAS" is an Intel specific external tool and "TWIDL" is an Intel specific internal tool. Bear this in mind when selecting a collecting method.
    #. SSD Selection Name or Number: String specifying the name (path to the location) of the SSD device, or the number of the device on the TWIDL enabled memory list
    #. Input Directory: Only used when "PARSE" option is selected. This input field specifies the path to the directory where the previously collected binary telemetry files are located.
    #. Firmware Parsers directory: Input field specifying where the python parsing files for processing the binary files are located. This files are usually generated by Auto-Parse, so they are outside the current code repo. The code repo for Auto-parsers as well as an example telemetry binary can be found in Intel IMAS or NVMe-CLI releases
    #. Output Working Directory: Input field specifying where the resulting text files will be stored.
    #. Number of Queries: Number of telemetry pulls to be executed or parse depending on the option chosen for field 1
    #. Time Frame to collect: Only used when "PARSE" is not selected. It specifies for how long should the system collect telemetry data. It serves as a time-limit to the execution of a large number telemetry pulls.

Fault Analysis Handbook Webpage (FAH)
-------------------------------------

.. figure:: images/GS030.png

This sections of the GUI checks if the specified user has access to the Handbook to perform a crawl for information (to be utilized for failure prediction later). The customizable inputs in this section are:

    #. Username: String specifying the username to access the handbook.
    #. Password: String for the password associated with the username to access the handbook.
    #. Loaded AES-256 Password Hash Signature: Generated signature for the specified password.

Telemetry Data Table
--------------------

.. figure:: images/GS031.png

This section of the GUI generates a data table to display the information contained in the decoded configuration (.ini) file. You can display the fields for a single object or for all the objects. The customizable inputs in this section are:

    1. Decoded *.ini File: Input to specify the path for the decoded configuration (.ini) file that contains the information to be included in the table.
    #. Choose Object to decode or choose all: Drop-down menu containing all the object UIDs. To update the list of UIDs based on the specified *.ini file, you need to click on the "Refresh Object UIDs" button.


Telemetry Generic Object Time Series Graph
-------------------------------------------

.. figure:: images/GS032.png


This section of the GUI generates line graphs of the timeseries for different fields inside a single telemetry object. The customizable inputs in this section are:

    #. Select Configuration File:  Input to specify the path for the decoded configuration (.ini) file that contains the desired telemetry object to be graphed
    #. Browse Output Location: Input to specify the path to the directory where the resulting PDFs will be stored - if "Save Figures to PDF?" is set to Yes
    #. Object Name: String for the name of the object to be graphed
    #. Select Tracking Variables: Object's fields to be graphed on the main axis (the y-scale on the left side of the graph)
    #. Select Optional Secondary Variables: Object's fields to be graphed on the secondary axis (the y-scale on the right side of the graph)
    #. Start % of data: If set to a non-zero value, the first values of the time-series corresponding to the specified % are ignored when graphing all variables
    #. End % of data: If set to other value that is not 100, the last values of the time-series corresponding to (1- specified %) are ignored when graphing all variables
    #. Get the Matrix Profile for the Data?: Flag to indicate that the Matrix Profile of the data must be extracted before graphing it.  Please refer to https://www.cs.ucr.edu/~eamonn/MatrixProfile.html to understand what Matrix Profile is.
    #. Save Figures to PDF?: Flag to indicate whether the generated figures should be saved to PDFs or should be directly displayed to the screen for a single-use.

Telemetry Garbage (Defrag) Collection History
----------------------------------------------

.. figure:: images/GS033.png

.. figure:: images/GS034.png

Steps
    #. This section of the GUI generates all the relevant graphs for analyzing Defrag History. The customizable inputs in this section are:
    #. Drive Type: Drop down menu that allows the user to choose between two different drive types (CDR and ADP). Please select the drive from which the telemetry data values to be used were extracted.
    #. Browse Configuration File:  Input to specify the path for the decoded configuration (.ini) file that contains the desired telemetry data to be graphed. Please make sure this .ini file contains uid-41 as one of the objects.
    #. Browse Output Location: Input to specify the path to the directory where the resulting PDFs will be stored - if "Save Figures to PDF?" is set to Yes
    #. Select Set Points: Baseline reference lines used for evaluating whether HostWrites has fallen below each threshold. Each set-point represents a different threshold and associated drive state
    #. Select Tracking Variables: Variables to be graphed in the main axis. We recommend you choose HostWrites and NandWrites if you are using the set-points, as these two fields will provide the best insight.
    #. Select Optional Secondary Variables: Variables to be graphed in the secondary axis.
    #. Start % of data: If set to a non-zero value, the first values of the time-series corresponding to the specified % are ignored when graphing all variables
    #. End % of data: If set to other value that is not 100, the last values of the time-series corresponding to (1- specified %) are ignored when graphing all variables
    #. Is the Secondary Axis Bandwidth?: Flag to indicate if the secondary variables will be used to calculate Bandwidth before graphing the resulting values
    #. Select the Number of Cores: Select the number of cores in the Drive from which the telemetry data was extracted.
    #. Save Figures to PDF?: Flag to indicate whether the generated figures should be saved to PDFs or should be directly displayed to the screen for a single-use.

ARMA Prediction Plot
--------------------

.. figure:: images/GS035.png

This section of the GUI takes a single object and a single field inside that telemetry object and then uses the Auto-Regressive Moving Average (ARMA) algorithm to predict future behavior of the field's values. The customizable inputs in this section are:

    #. Browse Configuration File:  Input to specify the path for the decoded configuration (.ini) file that contains the desired telemetry data to be used for the predictions
    #. Object Name: Drop down menu listing all the objects contained in the configuration file. Choose the object that you want to use for the forecasting
    #. Select Tracking Axis Variable: Object's field to be used in the forecasting
    #. Length of Window to be Considered for Matrix Profile: Number of data values to be considered in a single window for Matrix Profile Extraction
    #. Get the Matrix Profile for the Data?: Flag to indicate that the Matrix Profile of the data must be extracted before graphing it.  Please refer to https://www.cs.ucr.edu/~eamonn/MatrixProfile.html to understand what Matrix Profile is.

RNN Prediction Plot
-------------------
.. figure:: images/GS036.png

.. figure:: images/GS037.png

This section uses RNNs models to forecast the timeseries values for different fields of a single telemetry object. The customizable inputs in this section are:

    #. Browse Configuration File:  Input to specify the path for the decoded configuration (.ini) file that contains the desired telemetry data to be used for the predictions
    #. Object Name: Drop down menu listing all the objects contained in the configuration file. Choose the object that you want to use for the forecasting
    #. Select Field Variables: Object's fields to be used as inputs into the neural network. We have limited the number of  fields to prevent users from generating bigger models that they would not be able to run locally.
    #. Select Plot Data: For simplicity, we can only display a single field at a time. Use the drop down menu to choose the field to be graphed. Remember that this field must also be part of the inputs to the neural network, or the GUI will not generate any graphs
    #. Input Width: How big should the input time-series window be for forecasting future values. Bigger values will generate bigger models that require more computational resources, but allow for more accurate forecasting and a longer forecast output (we are able to predict further in the future)
    #. Label Width: The number of time steps (data values) to be outputted by the neural network. This corresponds to the number of data values that will comprise the forecast.
    #. Shift: How many data values should be skipped when shifting the input window to generate a new set of inputs for the neural network
    #. Neurons Per Hidden Layer: How many units should be included in the LSTM and fully connected layers of the neural network
    #. Batch Size: Number of data values to be considered before triggering a weight update in the neural network
    #. Max Epochs: Number of iterations for training the neural network with the totality of the training set.
    #. Categorical Encoding of the Data?: Flag that indicates whether the input is categorical (non-numerical), and therefore needs to be turned into a numerical value to be processed by the neural network
    #. Embedded Encoding of the Data?: Flag that indicates whether the input should be encoded using complex embeddings. Usually recommended after generating a categorical encoding to uncover hidden relations between inputs
    #. Optimizer for Neural Network: name for the optimizer to be used in the model. To know more about optimizers, please refer to: https://towardsdatascience.com/overview-of-various-optimizers-in-neural-networks-17c1be2df6d5
    #. Activation for LSTM layers: name of the activation function to be used in LSTM layers. To know more about activation functions, please refer to: https://en.wikipedia.org/wiki/Activation_function
    #. Activation for Dense Layer: name of the activation function to be used in Dense layers. To know more about activation functions, please refer to: https://en.wikipedia.org/wiki/Activation_function
    #. Initializer for LSTM layer: name of the weight initializer function to be used in LSTM layers. To know more about initialization function, please refer to: https://machinelearningmastery.com/weight-initialization-for-deep-learning-neural-networks/
    #. Initializer for Dense Layer: name of the weight initializer function to be used in Dense layers. To know more about initialization function, please refer to: https://machinelearningmastery.com/weight-initialization-for-deep-learning-neural-networks/
    #. Apply Dropout Between Layers?: Flag to indicate whether dropout should be applied between layers.
    #. Get the Matrix Profile for the Data?: Flag to indicate that the Matrix Profile of the data must be extracted before graphing it.  Please refer to https://www.cs.ucr.edu/~eamonn/MatrixProfile.html to understand what Matrix Profile is.
    #. Length of Window to be Considered for Matrix Profile:  Number of data values to be considered in a single window for Matrix Profile Extraction
        - Note: The "Plot RNN Prediction" button will only generate a single graph at a time, so you might need to click it a total of 4 times to generate all graphs. Remember that you need to wait until the current graph is generated before you are able to click it again.

NLOG Predictor
--------------
.. figure:: images/GS038.png

.. figure:: images/GS039.png

This section uses RNNs models to predict future NLOG events. The customizable inputs in this section are:

    #. Browse NLOG folder: Path for the nlog Folder in which the nlog event files are contained
    #. Browse NLOG parser folder: Path for the folder in which the NLogFormats.py script is contained
    #. Number of Components: Integer for the number of dimensions to be used in the NLOG description embeddings
    #. Max Number of Parameters: Integer for the maximum number of parameters that can be contained in an NLOG description for the specified formats file
    #. Input Size: Integer for the number of NLOG events to be considered as the input for the predictive models
    #. Max Output Size: Integer for the maximum number of NLOG events to be predicted with the models
    #. Model Type for Width Predictor: name of the model type to be used in the linear regression model for determining the number of NLOG events to be predicted. Must be selected from the following: ['elastic', 'lasso', 'ridge', 'default']
    #. Neurons Per Hidden Layer for Time Predictor: Integer for the number of neurons contained in each hidden layer for the NLOG time stamp predictor model
    #. Neurons Per Hidden Layer for Event Predictor: Integer for the number of neurons contained in each hidden layer for the NLOG event predictor model
    #. Neurons Per Hidden Layer for Parameter Predictor: Integer for the number of neurons contained in each hidden layer for the NLOG parameter predictor model
    #. Max Epochs for Time Predictor: Integer for the maximum number of epochs to be considered when training the NLOG time stamp predictor model
    #. Max Epochs for Event Predictor: Integer for the maximum number of epochs to be considered when training the NLOG event predictor model
    #. Max Epochs for Parameter Predictor: Integer for the maximum number of epochs to be considered when training the NLOG parameter predictor model
    #. Optimizer for Time Predictor: name of the optimizer to be used in the NLOG time stamp predictor model. Must be selected from the following: ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']
    #. Optimizer for Event Predictor: name of the optimizer to be used in the NLOG event predictor model. Must be selected from the following: ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']
    #. Optimizer for Parameter Predictor: name of the optimizer to be used in the NLOG parameter predictor model. Must be selected from the following: ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax']
    #. Activation for LSTM Layers in Time Predictor: name of the activation function to be used in the LSTM layers of the NLOG time stamp predictor model. Must be selected from the following: ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
    #. Activation for LSTM Layers in Event Predictor: name of the activation function to be used in the LSTM layers of the NLOG event predictor model. Must be selected from the following: ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
    #. Activation for LSTM Layers in Parameter Predictor: name of the activation function to be used in the LSTM layers of the NLOG parameter predictor model. Must be selected from the following: ['relu', 'sigmoid', 'softmax', 'softplus', 'softsign', 'tanh', 'selu', 'elu', 'exponential']
    #. Initializer for LSTM Layers in Time Predictor: name of the weight initializer function to be used in the LSTM layers of the NLOG time stamp predictor model. Must be selected from the following: ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal', 'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
    #. Initializer for LSTM Layers in Event Predictor: name of the weight initializer function to be used in the LSTM layers of the NLOG event predictor model. Must be selected from the following: ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal', 'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
    #. Initializer for LSTM Layers in Parameter Predictor: name of the weight initializer function to be used in the LSTM layers of the NLOG parameter predictor model. Must be selected from the following: ['random_normal', 'random_uniform', 'truncated_normal', 'zeros', 'ones', 'glorot_normal', 'glorot_uniform', 'identity', 'orthogonal', 'constant', 'variance_scaling']
    #. Apply Dropout Between Layers in Time Predictor?: Boolean flag that indicates if dropout in between layers should be applied to the NLOG time stamp predictor model
    #. Apply Dropout Between Layers in Event Predictor?: Boolean flag that indicates if dropout in between layers should be applied to the NLOG event predictor model
    #. Apply Dropout Between Layers in Parameter Predictor?: Boolean flag that indicates if dropout in between layers should be applied to the NLOG parameter predictor model

User Report
-----------
.. figure:: images/GS040.png

This section will print the string representation of the User Report to be used for the first case in our Path Finding. Just hit Refresh Report to generate the report with the previously loaded data in section 1.

    - Important Note: before you run this section, please download and install the MikTex distribution for Windows, so your system can correctly parse the output into a PDF. The MikTex distribution can be found here: https://miktex.org/download. After the download finishes, please install the MikTex distribution using the wizard (please make sure you choose the option to install it for all users in the computer, so that the script runs successfully). Also download the necessary packages as suggested in the installation wizard. If the MikTex distribution is unable to download the packages (known bug), please utilize an online compiler like Overleaf: https://www.overleaf.com/ to compile the resulting .tex file.

Database Upload
--------------------
.. figure:: images/GS041.png

This section will upload the zip file of the binary telemetry pulls to the Database. The customizable inputs in this section are:

    - Please enter your upload Destination and the File to Upload: Drop down menu to specify the Axon location where the zip file should be uploaded
    - Content File: Path to the zip file containing all the binary files to be stored


AXON Database Download
----------------------
.. figure:: images/GS042.png

This section will download a zip file from the Axon Database containing the binary telemetry pulls. The customizable inputs in this section are:

    #. Choose Download Directory: Path to the directory where the downloaded zip file will be stored locally
    #. Axon IDs: Available objects to be downloaded. This are based on the User Profile specified in the next section


User Profile Information
------------------------
.. figure:: images/GS043.png

This section allows the user to update their profile information by specifying a few parameters. The customizable inputs in this section are:

    #. Enter Identity Number: Numerical value that identifies each user of RAAD
    #. Enter Username: Username used for RAAD, the handbook connection, and Axon
    #. Enter Mode: Mode of operation through which the user is accessing RAAD services
    #. Key Encrypt-Decrypt Location: Path to the encryption key if one is available
    #. Enable Encryption: Flag for encrypting communications and locally stored data
    #. Enter Working Directory: Root directory from which the GUI is being run

Application Information
-----------------------

.. figure:: images/GS044.png

This section allows the user to update the application information by specifying different parameters. The customizable inputs in this section are:
    #. Enter Identity Number: Numerical value that identifies each user of RAAD
    #. Enter Major Version Number: New major version number to be assigned to the application
    #. Enter Minor Version Number: New minor version number to be assigned to the application
    #. Enter Name: Name of the developer that wants to request the changes
    #. Execution Location: Path to the directory in which the root folder for StorageRelationalAnalysis is located
    #. Enter Mode: Mode of operation through which the user is accessing RAAD services
    #. Enter URL: URL for the web GUI
