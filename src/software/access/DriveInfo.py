#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Tyler Woods
# *****************************************************************************/
"""
Brief:
A script that extracts identification info from drive

Description:
    Uses NVMe-cli to gather information for drive.
    Returns telemetry data.
"""
# from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations

import os, subprocess, re
import src.software.parse.parseTelemetryBin
from collections import defaultdict

# Regular Expression to split output from id-ctrl
SPLIT_EXPRESSION = " +: +|[\\n]"
SPLIT_ENTRIES_EXPRESSION = " +: +"
SPLIT_GROUP_EXPRESSION = "[\\n]"

# Dictionary to translate fields from nvme-cli to correlated fields in AXON Metadata
CORRELLARY_FIELDS_ID_CTRL = {"sn": "serial", "mn": "model", "fr": "firmware", "ieee": "product"}
CORRELLARY_FIELDS_Intel_MAS = {"DeviceStatus": "DeviceStatus", "SectorSize": "BlockDataSize",
                               "MaximumLBA": "numberOfSectors"}

PRODUCTS = defaultdict(lambda: "Not Present")

PRODUCTS["0"] = "Hobbs Ravine"
PRODUCTS["1"] = "Alder Stream"
PRODUCTS["2"] = "Arbordale Plus"
PRODUCTS["3"] = "Cliffdale Refresh QLC"
PRODUCTS["4"] = "Cold Stream Refresh"
PRODUCTS["5"] = "BearCove Plus (2017)"
PRODUCTS["6"] = "Available"
PRODUCTS["7"] = "Youngsville Refresh Refresh"
PRODUCTS["8"] = "Cliffdale Refresh QLC 16K IU"
PRODUCTS["9"] = "Available"
PRODUCTS["A"] = "Arbordale Plus Refresh VE acronym ADPRVE"
PRODUCTS["B"] = "Cliffdale Refresh Refresh"
PRODUCTS["C"] = "Lakestream"
PRODUCTS["D"] = "BearCove Quantum"
PRODUCTS["E"] = "Cold Stream"
PRODUCTS["F"] = "Arbordale Plus DP"
PRODUCTS["G"] = "Haleyville"
PRODUCTS["H"] = "MammothGlacier"
PRODUCTS["I"] = "illegal"
PRODUCTS["J"] = "Arbordale Plus Refresh SE"
PRODUCTS["K"] = "Teton Glacier"
PRODUCTS["L"] = "Alderstream Single-Port on MRDP ASIC"
PRODUCTS["M"] = "Simulator"
PRODUCTS["N"] = "ArbordalePlus RR SE/ME (TLC)"
PRODUCTS["O"] = "illegal"
PRODUCTS["P"] = "Alderstream Dual-Port on MRDP ASIC"
PRODUCTS["Q"] = "Next available"
PRODUCTS["R"] = "Sunset Bay"
PRODUCTS["S"] = "Youngsville"
PRODUCTS["T"] = "ArbordalePlus RR VE/EE"
PRODUCTS["U"] = "CarsonBeach"
PRODUCTS["V"] = "Cliffdale Refresh"
PRODUCTS["W"] = "Intel Internal Product"
PRODUCTS["X"] = "Youngsville Refresh"
PRODUCTS["Y"] = "Prairieville"
PRODUCTS["Z"] = "Illegal"


class DriveInfo(object):
    """
    Object that holds information pertaining to the NVMe drive as reported by the nvme-cli subcommand id-ctrl.
    The aim of this information is to be attached to the meta data in a telemetry upload to the AXON database.
    """

    def __init__(self, debug=False, desired_fields_id_ctrl=None, desiredFields_intel_mas=None):
        """
        Instantiates pertinent data to be recovered from id-ctrl
        """
        if desired_fields_id_ctrl is None:
            desired_fields_id_ctrl = CORRELLARY_FIELDS_ID_CTRL
        if desiredFields_intel_mas is None:
            desiredFields_intel_mas = CORRELLARY_FIELDS_Intel_MAS
        self.debug = debug

        self.product = None
        self.serial = None
        self.model = None
        self.firmware = None

        self.desiredFields_id_ctrl = desired_fields_id_ctrl
        self.desiredFields_intel_mas = desiredFields_intel_mas
        self.IntelMASCommandLoc = ""

    def SetProduct(self, product):
        """
        Set function for product field
        Args:
            product: String identifying the internal name for the NVMe drive

        Returns: NULL

        """
        self.product = product

    def SetSerial(self, serial):
        """
        Set function for serial field
        Args:
            serial: Number in string form denoting the serial number of that particular drive

        Returns: NULL

        """
        self.serial = serial

    def SetModel(self, model):
        """
        Set function for model field
        Args:
            model: Model number of the NVMe drive

        Returns: NULL

        """
        self.model = model

    def SetFirmware(self, firmware):
        """
        Set function for firmware field
        Args:
            firmware: Firmware revision number for the firmware changeset currently loaded on the drive

        Returns: NULL

        """
        self.firmware = firmware

    def GetProduct(self, product):
        """
        Get function for product field
        Args:
            product: String identifying the internal name for the NVMe drive

        Returns: str

        """
        return self.product

    def GetSerial(self, serial):
        """
        Get function for serial field
        Args:
            serial: Number in string form denoting the serial number of that particular drive

        Returns: str

        """
        return self.serial

    def GetModel(self, model):
        """
        Get function for model field
        Args:
            model: Model number of the NVMe drive

        Returns: str

        """
        return self.model

    def GetFirmware(self, firmware):
        """
        Get function for firmware field
        Args:
            firmware: Firmware revision number for the firmware changeset currently loaded on the drive

        Returns: str

        """
        return self.firmware

    def SplitLines(self, lines):
        """
        Splits individual lines by the output delimiter and then uses those splits to populate a dictionary
        Args:
            lines: line-by-line output of the nvme-id-ctrl command

        Returns: parsed python dictionary

        """

        self.nvmeOutput = dict()

        for line in lines:
            if re.search(SPLIT_ENTRIES_EXPRESSION, line):
                matches = re.split(SPLIT_ENTRIES_EXPRESSION, line)
                if len(matches) == 2:
                    self.nvmeOutput[matches[0].strip()] = matches[1].strip()
        return self.nvmeOutput

    def GatherDesiredFields(self, fields, desiredFields):
        """
        Gathers fields from the set of possible fields that will be sent to the AXON database
        Args:
            fields: possible data fields that were found from nvme-id-ctrl
            desiredFields: selected fields
        Returns: data fields that will go to the AXON database
        """
        has_items = bool(fields)
        try:
            return {value: fields[key] for key, value in desiredFields.items()}
        except:
            if self.debug:
                import pprint
                print("GatherDesiredFields: fields, desiredFields")
                pprint.pprint(fields)
                pprint.pprint(desiredFields)
            return {}

    def ParseOutput(self, output, desiredFields=None):
        """
        Parses output from id-ctrl, splits output using a regular expression, then populates information into a dictionary
        Args:
            desiredFields:
            output: raw output from the id-ctrl

        Returns: dict(str=str)

        """
        if output == "":
            return {}

        if desiredFields is None:
            desiredFields = self.desiredFields_id_ctrl

        # Split output of nvme-id-ctrl into a dictionary
        allFields = self.SplitLines(re.split(SPLIT_GROUP_EXPRESSION, output))
        if self.debug:
            print("Split Output: ", allFields)

        # Gather only desired fields
        return self.GatherDesiredFields(allFields, desiredFields)

    def RunIdCtrlCommand(self, device):
        """
        Runs command for nvme id-ctrl and decodes the output
        Args:
            device: device to run the command on

        Returns:
            stdout[str]: Standard output of the id-ctrl command in utf-8 string form
        """

        # Assemble id-ctrl command
        command = ["sudo",
                   "nvme",
                   "id-ctrl",
                   str(device)]

        # Execute command and store that output in the object
        self.outputObject = subprocess.Popen(command,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT)

        stdout, stderr = self.outputObject.communicate()

        self.stdout = stdout.decode("utf-8")
        self.stderr = str(stderr)

        if self.debug: print("stdout", self.stdout)

        # return output to caller
        return self.stdout

    def RunIntelMASCommand(self, device):
        """
        Runs command for IntelMAS and decodes the output
        Args:
            device: device to run the command on

        Returns:
            stdout[str]: Standard output of the IntelMAS command in utf-8 string form
        """

        # Verify Intel Command is correctly configured
        if not os.path.exists(self.IntelMASCommandLoc):
            return ""

        # Assemble id-ctrl command
        command = ["sudo",
                   self.IntelMASCommandLoc,
                   "show",
                   "-a",
                   "-intelssd " + str(device)]

        # Execute command and store that output in the object
        self.outputObject = subprocess.Popen(command,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT)

        stdout, stderr = self.outputObject.communicate()

        # self.stdout = str(stdout)
        self.stdout = stdout.decode("utf-8")
        self.stderr = str(stderr)

        if self.debug: print("stdout", self.stdout)

        # return output to caller
        return self.stdout

    def DriveInfoAPI(self, device="/dev/nvme0n1", mode=1, dataDict=None):
        """
        Runs Identifying commands for nvme drive and parses their output
        Args:
            dataDict:
            device: device to query information
            mode: Mode to determine commands used to identify drive
                "1,4": Run both commands(nvme id-ctrl and IntelMAS) and parses their output
                "2": Run just nvme id-ctrl
                "3": Run parse
                "5": Run just IntelMAS

        Returns:
            MetaData[dict]: Dictionary containing info about the drive and the tags for each information
        """
        parseOutput = None
        if mode == 1 or mode == 4:
            # Run command and get the output
            IdCtrloutput = self.RunIdCtrlCommand(device)
            # Parse command output
            parseOutput = self.ParseOutput(IdCtrloutput, self.desiredFields_id_ctrl)
            # Run command and get the output
            IntelMASoutput = self.RunIntelMASCommand(device)
            # Parse command output
            parseOutput.update(self.ParseOutput(IntelMASoutput, self.desiredFields_intel_mas))
        elif mode == 2:
            # Run command and get the output
            IdCtrloutput = self.RunIdCtrlCommand(device)
            # Parse command output
            ParseOutput = self.ParseOutput(IdCtrloutput, self.desiredFields_id_ctrl)
        elif mode == 3:
            try:
                parseOutput = {}
                telemetryHeader = dataDict['uid-240']
                # factoryConfig = dataDict['uid-58']
                parseOutput["serial"] = telemetryHeader['reasonid.serialnumber'][
                    len(telemetryHeader['reasonid.serialnumber']) - 1]
                modelStr = ""
                # for charIndex in range(0, 40):
                # modelStr += format("%c", factoryConfig['modelnumber[%i]' % charIndex])
                parseOutput["model"] = modelStr
                parseOutput["firmware"] = telemetryHeader['reasonid.fwrevision'][
                    len(telemetryHeader['reasonid.fwrevision']) - 1]
                print(parseOutput)
                currentProduct = parseOutput["firmware"][0]
                parseOutput["product"] = PRODUCTS[str(currentProduct)]
                parseOutput["DeviceStatus"] = telemetryHeader['reasonid.failuremodestring'][
                    len(telemetryHeader['reasonid.failuremodestring']) - 1]
                # parseOutput["blockDataSize"] = factoryConfig['hostsectorsize'][len(factoryConfig['hostsectorsize'])]
                # parseOutput["numberOfSectors"] = factoryConfig['factorymaxsectors'][len(factoryConfig['factorymaxsectors'])]
            except:
                print("Failed to extract telemetry header. The config file did not have it")
                parseOutput = None

        elif mode == 5:
            # Run command and get the output
            IntelMASoutput = self.RunIntelMASCommand(device)
            # Parse command output
            parseOutput = self.ParseOutput(IntelMASoutput, self.desiredFields_intel_mas)
        else:
            print("Unknown mode entered")
            parseOutput = None

        if self.debug and parseOutput is not None:
            print("Fully parsed output: ", parseOutput)

        # Return organized fields back to calling function
        return parseOutput


def ExampleUsage():
    Info = DriveInfo(debug=True)

    Info.DriveInfoAPI(device="/dev/nvme0n1")


def main():
    ExampleUsage()


if __name__ == "__main__":
    main()
