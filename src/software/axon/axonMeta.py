#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
# @package axonMeta
from __future__ import absolute_import, division, print_function, \
    unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations

import os, ctypes, datetime, json, sys, traceback, tempfile, hashlib, math, hmac, hashlib, binascii
from uuid import UUID
from typing import List

"""
Brief:

Description:

    Layout axon_meta.py
        <Text Template>
        <import items>
        myNameIdentify = templateUtility()
        myNameIdentify.execute()
        <Other Code>

        Wiki
            https://wiki.ith.intel.com/display/Axon/Content+Type+Metadata
    """


class AXON_Meta(object):
    _pack_ = 1
    _fields_ = [
        ("uID-API", ctypes.c_uint32, ctypes.sizeof(ctypes.c_uint32)),  # API Identifier
        ("major", ctypes.c_uint16, ctypes.sizeof(ctypes.c_uint16)),  # Major version number of the file.
        ("minor", ctypes.c_uint16, ctypes.sizeof(ctypes.c_uint16)),  # Minor version number of the file.
    ]

    def __init__(self,
                 uid=(-1),
                 major=(-1),
                 minor=(1),
                 time=datetime.datetime.now(),
                 user="DarthVader",
                 debug=True):
        """
        Initalizes an object.  The parameters have default values to ensure all fields have a setting. The setting of variable  by the user will allow for customization on tracking of meta data.
        Args:
            uid:
            major: The major field is used for detection of structural ordering.
            minor: The minor field is used for detection of extensions.
            time: Creation time.
            user: The organization user information.
            debug: Developer debug flag.
        """
        if (debug is True):
            print('AxonInterface init called')
        (head, tail) = os.path.split(os.path.dirname(os.path.abspath(__file__)))
        __origin__ = 'axonInterface.py :Joseph Tarango :05-12-2020 11:58:00'
        self.uid = uid
        self.major = major
        self.minor = minor
        self.data = None
        # Meta tracking data
        self.time = time
        self.user = user
        self.absPath = os.path.dirname(os.path.abspath(__file__))
        self.path = head
        self.filename = tail
        self.debug = debug

        importPath = os.path.abspath(head)
        print("Importing Paths: ", str(importPath))
        sys.path.insert(1, importPath)

        if (self.debug is True):
            print("__origin__", ":", __origin__)

            print("self.uid", ":", self.uid)
            print("self.major", ":", self.major)
            print("self.minor", ":", self.minor)
            print("self.data", ":", self.data)

            print("self.time", ":", self.time)
            print("self.user", ":", self.user)
            print("self.absPath", ":", self.absPath)
            print("self.path", ":", self.path)
            print("self.filename", ":", self.filename)
            print("self.debug", ":", self.debug)
            # print("self.URL",                          ":", self.URL                         )

            # Initiate version tracking
            # self.versioning = software.container.basicTypes.UID_Application(uid=self.uid, major=self.major, minor=self.minor)
        return

    def GetVersion(self):
        return self.versioning

    def __roundEpochTime(self, dt=None, roundTo=100):
        """
        Round a datetime object to any time lapse in seconds
        Args:
            @dt : datetime.datetime object, default now.
            @roundTo : Closest number of seconds to round to, default 1 second.
        Return:
            Epoch time in seconds.
        """
        if dt is None:
            dt = self.convertTime()
        seconds = math.floor(dt // roundTo)
        return int(seconds)

    def convertTime(self, year=1970, month=1, day=1, hour=0, minute=0, second=0, microsecond=0):
        """
        Function to calculate the time from epoch or a given signature.
        Args:
            @year: Year of epoch 1970.
            @month: Month of epoch January.
            @day: Day of epoch 1.
            @hour: Hour of epoch 0.
            @minute: Minute of epoch 0.
            @second: Second of epoch 0.
            @microsecond: Microsecond of epoch 0.
        Return:
            UTC time in seconds from epoch.
        """
        # Unix Epoch is the default
        timeUTC = datetime.datetime(year=year,
                                    month=month,
                                    day=day,
                                    hour=hour,
                                    minute=minute,
                                    second=second,
                                    microsecond=microsecond)
        timeUTC = (datetime.datetime.utcnow() - timeUTC).total_seconds()  # Epoch in seconds
        return timeUTC

    def __createHMACSignature(self,
                              timeUTC=None,
                              hostName=None,
                              serial=None,
                              firmware=None,
                              method="simple"):
        """
        Record meta creator for the overall instance.
        Args:
            @timeUTC: Time in seconds from epoch.
            @hostName: Name of the host machine.
            @serial: Operating system identification.
            @firmware: Firmware identifier serial number
            @method: Unique identifier generator for queries.

        Returns:
            Signature of the event.
        """
        if timeUTC is None:
            timeUTC = self.__roundEpochTime()
        if hostName is None:
            hostName = "skynetT2020"
        if serial is None:
            serial = "PHAB00000000960DGN"
        if firmware is None:
            firmware = "2DAAZ000"

        key = str(self.__roundEpochTime())
        message = "{0}-{1}-{2}-{3}".format(timeUTC, hostName, serial, firmware)
        byteKey = binascii.unhexlify(key)

        if method != "simple":
            message = message.encode()
            signature = hmac.new(byteKey, message, hashlib.sha256).hexdigest().hex
        else:
            hashSig = hashlib.new("MD5", message.encode("utf-8"))  # md5 -> new since it is more secure.
            signature = UUID(hashSig.hexdigest()).hex
        return signature

    #############################
    #######JSON META TOOLS#######
    #############################
    def failure(self,
                hostName=os.getenv('HOSTNAME'),
                pool="RAD_Dev_PF",
                version=1,
                osInfo=str(sys.platform),
                axonCLIVersion="",
                uuid=None):
        return self.record(hostName=hostName, pool=pool, version=version, osInfo=osInfo, axonCLIVersion=axonCLIVersion,
                           uuid=uuid)

    def record(self,
               hostName="skynetT2020",
               pool="RAD_Dev_PF",
               version=1,
               osInfo=None,
               axonCLIVersion="1.0.17-e48ba68",
               uuid=None):
        """
        Record meta creator for the overall instance.
        Args:
            @hostName: Name of the host machine.
            @pool: Name of the machine pool.
            @version: Version of the record creation.
            @osInfo: Operating system identification.
            @axonCLIVersion: Version identifer
            @uuid: Unique identifier generator for queries.

        Returns:
            String array of the record for file writing.
        """
        if uuid is None:
            timeUTC = self.__roundEpochTime()  # Epoch in seconds
            print("record() timeUTC {}".format(timeUTC))
            hostName = "skynetT2020"
            serial = "PHAB00000000960DGN"
            firmware = "2DAAZ000"
            uuid = self.__createHMACSignature(timeUTC, hostName, serial, firmware)
        else:
            print("UUID", uuid)
        stringRecord = []  # type: List[str]
        stringRecord.append("{")
        stringRecord.append("  \"system\": {")
        stringRecord.append("   \"hostname\": \"{0}\",".format(hostName))
        stringRecord.append("   \"pool\": \"{0}\",".format(pool))
        stringRecord.append("   \"version\": {0}".format(version))
        stringRecord.append("   },")
        stringRecord.append("     \"software\": {")
        stringRecord.append("     \"os\": {")
        stringRecord.append("     \"name\": \"{}\",".format(osInfo))
        stringRecord.append("     \"version\": 1")
        stringRecord.append("    },")
        stringRecord.append("    \"version\": 1")
        stringRecord.append("  },")
        stringRecord.append("     \"axoncli\": \"{0}\",".format(axonCLIVersion))
        stringRecord.append("     \"uuid\": \"{}\"".format(uuid))
        # stringRecord.append("     \"uuid\": \"{}\",".format(uuid))
        # stringRecord.append("     \"ts\": \"{}\"".format(timeUTC))
        stringRecord.append("}")
        return stringRecord

    def contents(self,
                 product="Arbordale Plus",
                 sha="b91c544280d55d9e3e2139d7337bd94733442f82f727e0a79ec3295ea2a67f78",
                 timeStamp="2020-04-01T15:24:01.339000",
                 uuidRandom="326e95920ffa4ff98ee6c8b48ff9d0a3",
                 infoSource="Telemetry",
                 collectorTimeStamp="2020-04-01T21:24:20",
                 fileName="drive_info.zip",
                 phase="WORKLOAD",
                 host="lm-310-19-h1",
                 testName="StressERDTTest_logs",
                 bus="NVMe",
                 numberOfSectors=33230736,
                 driveStatus="Healthy",
                 serial="PHAB00000000960CGN",
                 wwid=00000000,
                 BlockDataSize=512,
                 MaximumTransferSize=131072,
                 model="INTEL SSDPF2KX960G9SSME2",
                 firmware="2DAAZ000",
                 testTag="ADP-XFT-QUALITYANDRELIABILITY-2020WW13.7_101345",
                 testRunID="test_run_id",
                 pool="RAD_Dev_PF"):
        """
        Creation of the meta data for a zip file to be uploaded.
        Args:
            product (str): Product identifier.
            sha (str): SHA signature generated from file.
            timeStamp (str): Time stamp of event.
            uuidRandom (str): unique signature generator.
            infoSource (str): Source of the information.
            collectorTimeStamp (str): Collection from the time stamp.
            fileName (str): File name to upload.
            phase (str): Phase of the workload generated.
            host (str): Host name of the system.
            testName (str): Test execution name.
            bus (str): Type of interface used.
            numberOfSectors (str): Total sectors of the device
            driveStatus (str): Drive state.
            serial (str): serial of the device.
            wwid (str): World wide identifier of creator.
            BlockDataSize (str): Block size used in the device.
            MaximumTransferSize (str): Maximum transfer size supported by the device.
            model (str): Model of the device.
            firmware (str): Firmware on the device.
            testTag (str): Execution generated tag of the device.
            testRunID (str): The run identifier of the execution.
            pool (str): System pool associated.

        Returns:
            List[str]: Construction of the string to be uploaded in describing the contents.
        """
        return self.driveInfoZip(product=product,
                                 sha=sha,
                                 timeStamp=timeStamp,
                                 uuidRandom=uuidRandom,
                                 infoSource=infoSource,
                                 collectorTimeStamp=collectorTimeStamp,
                                 fileName=fileName,
                                 phase=phase,
                                 host=host,
                                 testName=testName,
                                 bus=bus,
                                 numberOfSectors=numberOfSectors,
                                 driveStatus=driveStatus,
                                 serial=serial,
                                 wwid=wwid,
                                 BlockDataSize=BlockDataSize,
                                 MaximumTransferSize=MaximumTransferSize,
                                 model=model,
                                 firmware=firmware,
                                 testTag=testTag,
                                 testRunID=testRunID,
                                 pool=pool)

    def driveInfoZip(self,
                     product="Arbordale Plus",
                     sha="b91c544280d55d9e3e2139d7337bd94733442f82f727e0a79ec3295ea2a67f78",
                     timeStamp="2020-04-01T15:24:01.339000",
                     uuidRandom="326e95920ffa4ff98ee6c8b48ff9d0a3",
                     infoSource="Telemetry",
                     collectorTimeStamp="2020-04-01T21:24:20",
                     fileName="drive_info.zip",
                     phase="WORKLOAD",
                     host="lm-310-19-h1",
                     testName="StressERDTTest_logs",
                     bus="NVMe",
                     numberOfSectors=33230736,
                     driveStatus="Healthy",
                     serial="PHAB00000000960CGN",
                     wwid=00000000,
                     BlockDataSize=512,
                     MaximumTransferSize=131072,
                     model="INTEL SSDPF2KX960G9SSME2",
                     firmware="2DAAZ000",
                     testTag="ADP-XFT-QUALITYANDRELIABILITY-2020WW13.7_101345",
                     testRunID="test_run_id",
                     pool="RAD_Dev_PF"):
        """
        Creation of the meta data for a zip file to be uploaded.
        Args:
            product (str): Product identifier.
            sha (str): SHA signature generated from file.
            timeStamp (str): Time stamp of event.
            uuidRandom (str): unique signature generator.
            infoSource (str): Source of the information.
            collectorTimeStamp (str): Collection from the time stamp.
            fileName (str): File name to upload.
            phase (str): Phase of the workload generated.
            host (str): Host name of the system.
            testName (str): Test execution name.
            bus (str): Type of interface used.
            numberOfSectors (str): Total sectors of the device
            driveStatus (str): Drive state.
            serial (str): serial of the device.
            wwid (str): World wide identifier of creator.
            BlockDataSize (str): Block size used in the device.
            MaximumTransferSize (str): Maximum transfer size supported by the device.
            model (str): Model of the device.
            firmware (str): Firmware on the device.
            testTag (str): Execution generated tag of the device.
            testRunID (str): The run identifier of the execution.
            pool (str): System pool associated.

        Returns:
            List[str]: Construction of the string to be uploaded in describing the contents.
        """
        diz = []
        diz.append("{")
        diz.append("  \"product\": \"{0}\",".format(product))
        diz.append("   \"sha256\": \"{0}\",".format(sha))
        diz.append("   \"dut_capture_timestamp\": \"{0}\",".format(timeStamp))
        diz.append("   \"uuid_random\": \"{0}\",".format(uuidRandom))
        diz.append("   \"source\": {")
        diz.append("    \"nsg_drive_info_tools_collector\": {")
        diz.append("       \"deps\": {")
        diz.append("         \"RAAD\": \"RAAD Trunk 1.00.00 [20WW1]\"")
        diz.append("       },")
        diz.append("       \"error\": null,")
        diz.append("       \"type\": \"collector\",")
        diz.append("       \"version\": \"development\"")
        diz.append("     },")
        diz.append("     \"nsg_drive_info_tools_decoder\": null,")
        diz.append("     \"version\": 1")
        diz.append("   },")
        diz.append("   \"version\": 1,")
        diz.append("   \"info_source\": \"{0}\",".format(infoSource))
        diz.append("   \"collector_timestamp\": \"{0}\",".format(collectorTimeStamp))
        diz.append("   \"filename\": \"{0}\",".format(fileName))
        diz.append("   \"CTF\": {")
        diz.append("     \"phase\": \"{0}\",".format(phase))
        diz.append("     \"host\": \"{0}\",".format(host))
        diz.append("     \"test_name\": \"{0}\"".format(testName))
        diz.append("   },")
        diz.append("   \"size\": 361126,")
        diz.append("   \"id_block\": {")
        diz.append("     \"Bus\": \"{0}\",".format(bus))
        diz.append("     \"MediaSerialNumber\": null,")
        diz.append("     \"NumberOfSectors\": {0},".format(numberOfSectors))
        diz.append("     \"DriveStatus\": \"{0}\",".format(driveStatus))
        diz.append("     \"Vendor\": \"0x8086:0x8086\",")
        diz.append("     \"Serial\": \"{0}\",".format(serial))
        diz.append("     \"WWID\": \"{0}\",".format(wwid))
        diz.append("     \"SouthFirmware\": null,")
        diz.append("     \"BlockDataSize\": {0},".format(BlockDataSize))
        diz.append("     \"MaximumTransferSize\": {0},".format(MaximumTransferSize))
        diz.append("     \"Model\": \"{0}\",")
        diz.append("     \"Firmware\": \"{0}\",".format(firmware))
        diz.append("     \"isTPer\": true,")
        diz.append("     \"BlockSize\": {0}".format(BlockDataSize))
        diz.append("   },")
        diz.append("   \"options_list\": [")
        diz.append("     \"TELEMETRY,\"")
        diz.append("   ],")
        diz.append("   \"content-type\": \"application/zip\",")
        diz.append("   \"ConVal\": {")
        diz.append("     \"execution_identifier\": \"{0}\",".format(testTag))
        diz.append("     \"test_run_id\": \"{0}\",".format(testRunID))
        diz.append("     \"pool\": \"{0}\"".format(pool))
        diz.append("   }")
        diz.append(" }")
        return diz

    def RADString(self,
                  idName="RAD_PF",
                  idVersion="1",
                  pythonVersion="3",
                  appType="collector",
                  modeVersion="development"):
        """
        Application content creator for Rapid Automation-Analysis for Developers.

        Args:
            idName (str): Application identification name.
            idVersion (str): Application identification version.
            pythonVersion (str): Python version.
            appType (str): Application mode type.
            modeVersion (str): Mode version.

        Returns:
            List[str]: Construction of the string to be uploaded in describing the contents.
        """
        lines = []
        lines.append("{")
        lines.append("    \"signature\": {},")
        lines.append("    \"_metadataOnly\": \"false\",")
        lines.append("    \"content-type\": \"application/zip\",")
        lines.append("    \"source\": {")
        lines.append("        \"{0}\": {".format(idName))
        lines.append("            \"deps\": {")
        lines.append("                \"python\": \"{0}\"".format(pythonVersion))
        lines.append("            },")
        lines.append("            \"type\": \"{0}\",".format(appType))
        lines.append("            \"error\": \"\",")
        lines.append("            \"version\": \"{0}\"".format(modeVersion))
        lines.append("        }")
        lines.append("    },")
        lines.append("    \"version\": {}".format(idVersion))
        lines.append("}")
        return lines

    def contentString(self,
                      content_version="1",
                      fileListName=None,
                      source_version="1",
                      collection_type="collector",
                      name_version="1.0",
                      python_version="3",
                      error_encountered=""):
        """
        Content description package.
        Args:
            content_version (str): Version of the content
            fileListName (List[str]): File list of the content
            source_version (str): Version of the content
            collection_type (str): Type either collection or decoder.
            name_version (str): Name of the content.
            python_version (str): Python dependency version.
            error_encountered (str): Errors encountered.

        Returns:
            List[str]: Construction of the string to be uploaded in describing the contents.
        """
        if fileListName is None:
            fileListName = [""]
        lines = []
        lines.append("{")
        lines.append("    \"contents\": {")
        lines.append("        \"type\": {")
        lines.append("            \"version\": 1,".format(content_version))
        lines.append("            \"content-type\": \"application/zip\",")
        lines.append("            \"content-encoding\": \"zlib\",")
        for fileItemName in enumerate(fileListName):
            lines.append("            \"filename\": {},".format(fileItemName))
        lines.append("            \"source\" : {")
        lines.append("                \"version\": \"{}\",".format(source_version))
        lines.append("                \"name\" : {")
        lines.append("                    \"type\": \"{0}\",".format(collection_type))  # collector | decoder
        lines.append("                    \"version\": \"1.0\",".format(name_version))
        lines.append("                    \"deps\": {")
        lines.append("                        \"python\": \"{}\",".format(python_version))
        lines.append("                    },")
        lines.append("                    \"error\": \"\"".format(error_encountered))
        lines.append("                }")
        lines.append("          }")
        lines.append("        }")
        lines.append("    }")
        lines.append("}")
        return lines

    def ticketString(self,
                     hsdes_id=0,
                     hsdes_link="http://link_to_hsd",
                     cirs_id="CI1927-3292",
                     cirs_link="http://link_to_speed_cirs_facr_ticket",
                     cirs_type="FACR",
                     jira_id=0,
                     jira_link="http://link_to_jira",
                     jira_info="world"):
        """
        JIRA bug tracking content.
        Args:
            hsdes_id (int): Identification number.
            hsdes_link (): Web hyperlink to content.
            cirs_id (): Identification number.
            cirs_link (): Web hyperlink to content.
            cirs_type (str): Description type.
            jira_id (str): JIRA identification.
            jira_link (str): Web hyperlink to content.
            jira_info (str): Description information.

        Returns:
            List[str]: Construction of the string to be uploaded in describing the contents.
        """
        lines = []
        lines.append("{")
        lines.append("    \"tickets\": {")
        lines.append("        \"version\": 1,")
        lines.append("        \"hsdes\": [")
        lines.append("            {")
        lines.append("                \"id\": \"{0}\",".format(hsdes_id))  # 0
        lines.append("                \"link\": \"{0}\"".format(hsdes_link))  # http://link_to_hsd
        lines.append("            }")
        lines.append("        ],")
        lines.append("        \"cirs\": [")
        lines.append("            {")
        lines.append("                \"id\": \"{0}\",".format(cirs_id))  # CI1927-3292
        lines.append("                \"link\": \"{0}\",".format(cirs_link))  # http://link_to_speed_cirs_facr_ticket
        lines.append("                \"type\": \"{0}\"".format(cirs_type))  # FACR
        lines.append("            }")
        lines.append("        ],")
        lines.append("        \"jira\": [")
        lines.append("            {")
        lines.append("                \"id\": \"{0}\",".format(jira_id))  # 0
        lines.append("                \"link\": \"{0}\",".format(jira_link))  # http://link_to_jira
        lines.append("                \"hello\": \"{0}\"".format(jira_info))  # world
        lines.append("            }")
        lines.append("        ]")
        lines.append("    }")
        lines.append("}")
        return lines

    @staticmethod
    def RAAD(self):
        template = {
            "signature": {},
            # "_metadataOnly": "false",
            "content-type": "application/zip",
            "source": {
                "RAD_PF": {
                    "deps": {
                        "python": "3"
                    },
                    "type": "collector",
                    "error": "",
                    "version": "development"
                }
            },
            # "_uploadStatus": "DONE",
            "version": 1
        }
        return template  # "intel-raad-v1"

    @staticmethod
    def meta(self):
        template = {
            "uuid": None,
            "source": {
                "version": 1
            },
            "drive_info_metadata": {},
            "system": {
                "version": 1,
                "hostname": None,
                "pool": None,
                "purpose": None,
                "id": {
                    "version": 1,
                    "source": None,
                    "uuid": None,
                    "rawid": None,
                },
                "location": {
                    "rack": None,
                    "system": None
                }
            },
            "software": {
                "version": 1,
                "os": {
                    "version": None,
                    "name": None
                }
            },
            "platform": {
                "version": 1,
                "tla": None,
                "name": None,
                "config": None,
                "stepping": None
            },
            "host": {
                "version": 1,
                "hostname": None
            }
        }
        return template

    @staticmethod
    def content(self, fileName=""):
        template = {
            "contents": {
                "type": {
                    "version": 1,
                    "content-type": "application/zip",
                    "content-encoding": "zlib",
                    "filename": fileName,
                    "source": {
                        "version": 1,
                        "name": {
                            "type": "collector | decoder",
                            "version": "1.0",
                            "deps": {
                                "python": "3",
                            },
                            "error": ""  #
                        }
                    }
                }
            }
        }
        return template

    @staticmethod
    def source(self):
        template = {
            "source": {
                "version": 1,
                "RADc": {
                    "type": "collector",
                    "version": "1.0",
                    "deps": {
                        # library:version dependencies
                        "python": "3",
                    },
                    "error": ""
                }
            }
        }

        return template

    @staticmethod
    def platform(self):
        template = {
            "platform": {
                "version": 1,
                # "tla": "ICL",
                # "name": "Ice Lake",
                # "config": "ICL-U42",
                # "stepping": "B0"
            }
        }
        return template

    @staticmethod
    def system(self):
        template = {
            "system": {
                "version": 1,
                "hostname": "",  # sut-icl-01
                "pool": "",  # siv.icl.sxcycling
                "purpose": "",  # automation
                "id": {
                    "uuid": "",  # 1d2c2c83-6d10-237b-5182-3010d6139520
                    "rawid": "",  # FZTL9230007D
                    "source": ""  # smbios
                }
            }
        }
        return template

    @staticmethod
    def host(self):
        template = {
            "host": {
                "version": 1,
                "hostname": ""  # PG02WVAW0461
            }
        }
        return template

    @staticmethod
    def ticket(self):
        template = {
            "tickets": {
                "version": 1,
                "hsdes": [
                    {
                        "id": "0",  # 0
                        "link": ""  # http://link_to_hsd
                    }
                ],
                "cirs": [
                    {
                        "id": "",  # CI1927-3292
                        "link": "",  # http://link_to_speed_cirs_facr_ticket
                        "type": ""  # FACR
                    }
                ],
                "jira": [
                    {
                        "id": "",  # 0
                        "link": "",  # http://link_to_jira
                        "hello": ""  # world
                    }
                ]
            }
        }
        return template

    def saveJSON(self, saveFile=None, objectJSON=None):

        if saveFile is None:
            temporaryFolder, saveFile = tempfile.mkstemp()

        if objectJSON is None:
            objectJSON = self.RAAD()

        with open(saveFile, 'w') as fileJSON:
            json.dump(objectJSON, fileJSON)

        return (objectJSON, fileJSON)

    def loadJSON(self, inJSONFile=None):
        metadata = json.loads(inJSONFile)
        metadataString = json.dumps(metadata)
        return metadataString


def setup(debug=True):
    state = None
    '''
    try:
        import setuptools, traceback
        state = setuptools.setup(
                      name='AXON Data Stream',
                      version='1.0',
                      author='Joseph Tarango',
                      author_email='no-reply@intel.com',
                      description='AXON Data Stream for Intel telemetry.',
                      url='http://github.com/StorageRelationalLibrary/src/software/axon/axonInterface.py',
                      packages=setuptools.find_packages(),
                      # classifiers
                      install_requires=[
                                        'keras',
                                        'numpy',
                                        'pandas',
                                        'matplotlib',
                                        'tensorflow',
                                       ],
                      classifiers=[
                                   # Optional
                                   # How mature is this project? Common values are
                                   #   3 - Alpha
                                   #   4 - Beta
                                   #   5 - Production/Stable
                                   'Development Status :: 3 - Alpha',
                                   # Indicate who your project is intended for
                                   'Intended Audience :: Developers',
                                   'Topic :: Software Development :: Build Tools',
                                   # Specify the Python versions you support here. In particular, ensure
                                   # that you indicate whether you support Python 2, Python 3 or both.
                                   # These classifiers are *not* checked by 'pip install'. See instead
                                   # 'python_requires' below.
                                   'Programming Language :: Python :: 3.7.7',
                                  ],
                      data_files=[
                                  ('my_data', ['trainingData/indata_file.dat'])
                                 ],  # Optional, In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
                     )
        if(debug is True):
                print("Setup State ", state)
    except:
        print("Exception within Install path.")
        print("The execution of the file requires setup tools. The command is pip install setup findpackages")
        print("Setup State ", state)
        traceback.print_exc()
    '''
    return state


def hollowShell(options=None):
    print("Running hollow AXON instance")
    # referenceTest = AxonInterface()
    # (exitCode, cmdOutput, cmdError, dataOutput) = referenceTest.sendCmd()
    # print("Exit Code:", exitCode)
    # print("Command line output:", cmdOutput)
    # print("Command Error", cmdError)
    # print("Data Transaction Output:", dataOutput)
    return


def main():
    ##############################################
    # Main function, Options
    ##############################################
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("--example", action='store_true', dest='example', default=False,
                      help='Show command execution example.')
    parser.add_option("--debug", action='store_true', dest='debug', default=False, help='Debug mode.')
    parser.add_option("--verbose", action='store_true', dest='verbose', default=False,
                      help='Verbose printing for debug use.')
    (options, args) = parser.parse_args()

    ##############################################
    # Main
    ##############################################
    setup()
    hollowShell(options)
    return 0


if __name__ == '__main__':
    """Performs execution delta of the process."""
    p = datetime.datetime.now()
    try:
        main()
    except Exception as e:
        print("Fail End Process: ", e)
        traceback.print_exc()
    q = datetime.datetime.now()
    print("\nExecution time: " + str(q - p))
