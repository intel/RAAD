Access Telemetry using Ubuntu (Linux) NVMe-CLI
=====================================
When wanting to access Telemetry packet in an open-source format as a single Application Programming Interface (API).

Summary
*******
"binaryInterface.py" is a script that extracts uid-specific data from drive or binary, and returns it dynamically. It's a wrapper for other scripts such as "getTelemetry.py" and "parseTelemetry.py", but also implements nvme-cli library for Telemetry use in a Python format. Additional documentation on NVMe-CLI can be found in this Github below.

Environment
***********
    - You need to clone NVMe-CLI library
        - https://github.com/linux-nvme/nvme-cli
    - This script needs to be run on a hardware-enabled environment. This meaning, most likely you want to run this code on a Test Machine. The test machine needs to be connected to the appropriate SSD drive you want to extract telemetry from.
    - Note: device 0 is attached to NVME INTEL SSDDQXXX38T9 with name /dev/nvme0n1.
    - These same numbers apply when telling the script which device to extract telemetry from, so take note.

Warning
"""""""
Make sure you know the number of the device you are trying to access. Accessing device /dev/sg0, for example will fail as this is your local drive, and may sometimes have unforeseen consequences if written out to.

Step-by-step guide
******************

Import tool code by cloning Github:
    1. Import Open Source code by cloning Github Repo:
        - https://github.com/linux-nvme/nvme-cli

    #. Create Directory
        - `mkdir ~/RAAD_Sandbox`
        - `cd ~/RAAD_Sandbox`
    #. Clone
        - `git clone https://github.com/Intel/RAAD.git`
    #. Navigate (cd) into script location
        - `cd ~/RAAD_Sandbox/RAAD/src/software/parse`
    #. Import NVMe-CLI into same repo
        - `git clone https://github.com/linux-nvme/nvme-cli`
    #. Run Script
        - Run script (nvme-cli -> parseTelemetryBin)

            .. code-block:: python

                python
                >> from binaryInterface import *
                >> binCache, payload = hybridBinParse("5", "/dev/nvme0n1")
                >> payload = hybridChachedBinParse(binCache, "6")

        - OR (getTelemetry -> parseTelemetryBin process, normal)

            .. code-block:: python

                python
                >> from binaryInterface import *
                >> binaryCache, payload = binParse("5")
                >> payload = cachedBinParse(binaryCache, "6")

        - OR (getTelemetry -> parseTelemetryBin process, when you already have a binary file. NOTE: this version can be used without Test Machine)
            .. code-block:: python

                python
                >> from binaryInterface import *
                >> binaryCache, payload = binParse("5", "<NameOfSampleBinHere>")
                >> payload = hybridChachedBinParse(binCache, "6")

    # To run a sample of tests demoing how to use this library

        .. code-block:: python

            python binaryInterface.py

        NOTE: see warning in Troubleshooting, scripts will need to be tweaked to be CL-usable.

Output
=======
You can expect the following output:

        .. code-block::

            Phase 1 Extract
            Data area 1 validity check pass!!!
            Phase 2 Parse
            Passed!!!
            File Format: <Serial Number> <Core (Optional)> (eUID> <Major> <Minor> <Known Firmware Name> <Byte Size>
            Read Data Area 1 at Byte 512 of size 91136
            Read Data Area 2 at Byte 512 of size 995840
            Read Data Area 3 at Byte 1087488 of size  680960
            uidInfoDict Contains the following UIDs:
            ['1', '2', ..., '5']
            Printing Payload UID 5: dataOffset 24252, dataSize: 1024
            Storing Payload in: PHA...5.1.0.bis.1024.1.0.bin ...
            ===objectId= 5, maj= 1, min= 0===
            offset=24542
            size=1024
            name=bis
            dataArea=1
            rawData: BIS .......

    Note: Printing of the binary data of the requested UID at the bottom.

Troubleshooting
===============
    NOTE: that this script still requires Command Line Inputs to be implemented, and the current version is hard-coded to produce some results for testing and learning purposes. This is because this library is made to be called in-code not used in CL, but can be tweaked to do so.
