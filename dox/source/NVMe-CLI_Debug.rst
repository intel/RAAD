NVMe CLI Usage Commands on Linux Debug
######################################
Generic Commands
*****************
Example nvme command
    .. code-block::

        sudo ./nvme -version
Get the identification
    .. code-block::

        sudo ./nvme nvme intel id-ctrl /dev/nvme0
Extract Telemetry Payload
    .. code-block::

        sudo ./nvme telemetry-log /dev/nvme0 -o telemetryPayload.bin -g 1
Clear APL max lifetime Temperature: A drive power-cycle or pci rescan may be needed.
    .. code-block::

        sudo ./nvme admin-passthru /dev/nvme0 -o 0xF5 --cdw=x018
        sudo ./nvme subsystem-reset /dev/nvme0
Firmware Update
    .. code-block::

        sudo ./nvme fw-download /dev/nvme0 -f firmware_file.bin
        sudo ./nvme fw-activate /dev/nvme0 -s 0 -a 1
Format 4K
    .. code-block::

        sudo ./nvme format /dev/nvme0n1 -b 4k
Format 512B
    .. code-block::

        sudo ./nvme format /dev/nvme0n1 -b 512
RAW Input-Output
================
To read the first LBA of a 4k formatted drive:
    .. code-block::

        sudo ./nvme read /dev/nvme0n1 -s 0 -z 4096
It is recommended to pipe the output to another program to avoid raw binary output to the console (this example will print a hexdump of the block)
    .. code-block::

        sudo ./nvme read /dev/nvme0n1 -s 0 -z 4096 | hexdump -C

To write to the first LBA of a 4k formatted drive. This assumes there is a file '4k.bin' available, this can be easily created using dd.
    .. code-block::

        sudo ./nvme write /dev/nvme0n1 -s 0 -z 4096 -d 4k.bin

For random data:
    .. code-block::

        dd if=/dev/urandom of=4k.bin bs=4096 count=1

For nonrandom data
    .. code-block::

        dd if=/dev/zero of=4k.bin bs=4096 count=1'

Intel Specific
**************
smart-log-add: Parses the Intel vendor unique SMART log page (0xCA)
    .. code-block::

        sudo ./nvme intel smart-log-add /dev/nvmeX
market-name: Returns the marketing name for the drive, e.g. "Intel(R) SSD DC P4501 Series". (Log page 0xDD)
    .. code-block::

        sudo ./nvme intel market-name /dev/nvmeX
temp-stats: Returns the temperature statistics for the drive. (Log page 0xC5)
    .. code-block::

        sudo ./nvme intel temp-stats /dev/nvmeX
lat-stats: Returns IO latency statistics (Log pages 0xC1 for writes and 0xC2 for reads ).  Note this must be first be enabled with Set/Get feature 0xE2, e.g. 'nvme set-feature /dev/nvme0 -f 0xe2 -v 1'
    .. code-block::

        sudo ./nvme intel lat-stats /dev/nvmeX
internal-log: Returns one of the event logs for the drive, (Example gathers the nLog)
    .. code-block::

        sudo ./nvme intel internal-log /dev/nvmeX --namespace-id=1 --log 0
Clear Assert (Opcode 0xD4): (NB) This will only work on specific firmware builds where the NCAT functionality is enabled (Usually Pre-PRQ, Amazon and Dell/EMC firmware), and only while the firmware is asserted. After this step a full reset of the drive is required (usually warmReset() ) 'nvme reset /dev/nvmeX' is not sufficient. If in doubt do a full platform reboot.
    .. code-block::

        sudo ./nvme admin-passthru /dev/nvmeX --p[cpde=0xD4 --cdw10=0x00 -w
Low Level Format (Opcode 0xD4): (NB) This will only work on specific firmware builds where the NCAT functionality is enabled (Usually Pre-PRQ, Amazon and Dell/EMC firmware), and only while the firmware is in a Bad Context state. After this step an 'nvme reset /dev/nvmeX' is usually sufficient to return the drive to a Healthy state.
    .. code-block::

        sudo ./nvme admin-passthru /dev/nvmeX --p[cpde=0xD4 --cdw10=0x04 -w

Useful Linux Commands
======================
Check for PCIe devices (PCIe Link) from both controller ID 0 and 1
    .. code-block::

        lspci | grep Non
Check for NVMe devices (NVMe Driver Loaded) and namespaces within those devices
    .. code-block::

        ls –al /dev/nvm* or lsblk
NVMe subsystem reset device and Rescan or Reboot Host: Prior to 4.4 kernel
        - reboot Host Platform (Linux: 4.4+ kernel)
            .. code-block::

                modprobe –r nvme, echo 1 > /sys/bus/pci/rescan, modprobe nvme

Example Bash Script accessTelemetry.sh
======================
.. code-block::

    HAMMERTIME=$(date +%Y.%m.%d.%H.%M.%S)
    FILENAME=CDDP_$HAMMERTIME.bin
    DIRECTORY=Telemetry_Logs
    LOCATION=$DIRECTORY/$FILENAME
    NVMTARGET=/dev/nvme0
    CLIPATH=~/git/nvme-cli/
    PWD=$(pwd)
    cd $CLIPATH
    echo ++++++++++++++++++++++++++++++++++++++++++++
    echo Checking All NVMe Devices...
    echo ++++++++++++++++++++++++++++++++++++++++++++
    ls /dev/nvme*
    echo ++++++++++++++++++++++++++++++++++++++++++++
    echo Checking All PCIe NVMe...
    echo ++++++++++++++++++++++++++++++++++++++++++++
    sudo lspci | grep Non-Volatile
    echo ++++++++++++++++++++++++++++++++++++++++++++
    echo Identify NVMe SSD at Index $NVMTARGET...
    echo ++++++++++++++++++++++++++++++++++++++++++++
    sudo ./nvme id-ctrl $NVMTARGET
    echo ++++++++++++++++++++++++++++++++++++++++++++
    echo Telemetry Get Host Log at Index $NVMTARGET...
    echo ++++++++++++++++++++++++++++++++++++++++++++
    sudo ./nvme telemetry-log $NVMTARGET -o "$FILENAME" -g 1
    chmod 777 "$FILENAME"

    if [ -d "$DIRECTORY" ]; then
      # Control will enter here if $DIRECTORY exists.
      mv "$FILENAME" "$LOCATION"
    else
      mkdir "$DIRECTORY"
      chmod -R 777 "$DIRECTORY"
    fi
    echo File at $LOCATION
    ls -la $LOCATION
    echo ++++++++++++++++++++++++++++++++++++++++++++
    cd $PWD

Usage Example to Log content
============================
    .. code-block::

        jtarango@Telemetry-Bench-0:~/git/nvme-cli$ sudo ./accessTelemetry.sh
        ++++++++++++++++++++++++++++++++++++++++++++
        Checking All NVMe Devices...
        ++++++++++++++++++++++++++++++++++++++++++++
        /dev/nvme0
        ++++++++++++++++++++++++++++++++++++++++++++
        Checking All PCIe NVMe...
        ++++++++++++++++++++++++++++++++++++++++++++
        02:00.0 Non-Volatile memory controller: Intel Corporation Device 0d54
        ++++++++++++++++++++++++++++++++++++++++++++
        Identify NVMe SSD at Index /dev/nvme0...
        ++++++++++++++++++++++++++++++++++++++++++++
        NVME Identify Controller:
        vid       : 0x8086
        ssvid     : 0x8086
        sn        : BTLP82300JUP15PDGN
        mn        : INTEL SSDPD2KS150T8
        fr        : VDAAD453
        rab       : 4
        ieee      : 5cd2e4
        cmic      : 0x3
        mdts      : 5
        cntlid    : 0x1
        ver       : 0x10200
        rtd3r     : 0x989680
        rtd3e     : 0xe4e1c0
        oaes      : 0x100
        ctratt    : 0
        rrls      : 0
        cntrltype : 0
        fguid     :
        crdt1     : 0
        crdt2     : 0
        crdt3     : 0
        oacs      : 0x1f
        acl       : 127
        aerl      : 7
        frmw      : 0x2
        lpa       : 0xc
        elpe      : 127
        npss      : 0
        avscc     : 0
        apsta     : 0
        wctemp    : 343
        cctemp    : 353
        mtfa      : 0
        hmpre     : 0
        hmmin     : 0
        tnvmcap   : 0
        unvmcap   : 0
        rpmbs     : 0
        edstt     : 0
        dsto      : 0
        fwug      : 0
        kas       : 0
        hctma     : 0
        mntmt     : 0
        mxtmt     : 0
        sanicap   : 0x3
        hmminds   : 0
        hmmaxd    : 0
        nsetidmax : 0
        endgidmax : 0
        anatt     : 0
        anacap    : 0
        anagrpmax : 0
        nanagrpid : 0
        pels      : 0
        sqes      : 0x66
        cqes      : 0x44
        maxcmd    : 0
        nn        : 0
        oncs      : 0x6e
        fuses     : 0
        fna       : 0x6
        vwc       : 0
        awun      : 0
        awupf     : 0
        nvscc     : 0
        nwpc      : 0
        acwu      : 0
        sgls      : 0x70001
        mnan      : 0
        subnqn    :
        ioccsz    : 0
        iorcsz    : 0
        icdoff    : 0
        ctrattr   : 0
        msdbd     : 0
        ps    0 : mp:25.00W operational enlat:0 exlat:0 rrt:0 rrl:0
                  rwt:0 rwl:0 idle_power:- active_power:-
        ++++++++++++++++++++++++++++++++++++++++++++
        Telemetry Get Host Log at Index /dev/nvme0...
        ++++++++++++++++++++++++++++++++++++++++++++
        File at Telemetry_Logs/CDDP_2020.01.17.19.33.35.bin
        -rwxrwxrwx 1 root root 1208320 Jan 17 19:33 Telemetry_Logs/CDDP_2020.01.17.19.33.35.bin
        ++++++++++++++++++++++++++++++++++++++++++++

References
***********
1. https://nvmexpress.org/
#. https://www.mankier.com/1/nvme
#. https://github.com/nvmecompliance/dnvme
#. https://github.com/nvmecompliance/tnvme
#. https://github.com/linux-nvme/nvme-cli
#. https://github.com/clearlinux/telemetrics-backend
