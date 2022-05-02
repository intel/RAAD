#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Daniel Garces, Tyler Woods
# *****************************************************************************/
# @package gui
import optparse, datetime, traceback, unittest

from src.software.guiDeveloper import GUIDeveloper
# from software.guiOneShot import GUIOneShot


class TableRegressionTests(unittest.TestCase):
    """
    Regression testing for functions creating the telemetry data table
    """

    def assertGetDataAsArray(self, testInput, expectedResults, chosenKey="all", oneShot=False):
        """
        Assert checking for outputs that are received from the getDataAsArray function
        Args:
            testInput: input DataDict that will be passed to getDataAsArray
            *expectedResults: Resulting array that is formed
            chosenKey:
            oneShot:
        Returns:
        """
        testResults = GUIDeveloper.getDataAsArray(testInput, chosenKey=chosenKey, oneShot=oneShot)
        print("test results: ", testResults)
        return self.assertEqual(testResults, expectedResults)

    def testNilContainer(self):
        testInput = {}
        Expected = [
            ["Telemetry Object", "Telemetry Feature"],
        ]
        return self.assertGetDataAsArray(testInput, Expected)

    def testSimpleContainer(self):
        testInput = {
            "First Object": {
                "name": "First Object",
                "First feature": [1]
            }
        }
        Expected = [
            ["Telemetry Object", "Telemetry Feature", "t_0"],
            ["First Object", "First feature", 1]
        ]
        return self.assertGetDataAsArray(testInput, Expected)

    def testSpecificContainer(self):
        testInput = {
            "First Object": {
                "name": "First Object",
                "First feature": [1],
                "Second feature": [2]
            },
            "Second Object": {
                "name": "Second Object",
                "First feature": [1],
                "Second feature": [2]
            }
        }
        Expected = [
            ["Telemetry Object", "Telemetry Feature", "t_0"],
            ["First Object", "First feature", 1],
            ["First Object", "Second feature", 2]
        ]
        return self.assertGetDataAsArray(testInput, Expected, chosenKey="First Object")

    def testGetDataDict(self):
        return self.assertIsInstance(GUIDeveloper.getDataDic(self.config_file), dict)

    def testPopupTable(self):
        testInput = [
            ["Telemetry Object", "Telemetry Feature", "t_0"],
            ["First Object", "First feature", 1],
            ["First Object", "Second feature", 2]
        ]
        return self.assertNotEqual(GUIDeveloper().popupTable(dataArray=testInput, programLabel="testWindow", returnLayout=True), None)

    def testOneShotContainer(self):
        testInput = {
            "uid-1": {
                "name": "First Object",
                "First feature": [1],
                "Second feature": [2]
            },
            "uid-2": {
                "name": "Second Object",
                "First feature": [1],
                "Second feature": [2]
            }
        }
        Expected = {
            "First Object": [
                ["Telemetry Object", "Telemetry Feature", "t_0"],
                ["First Object", "First feature", 1],
                ["First Object", "Second feature", 2]
            ],
            "Second Object": [
                ["Telemetry Object", "Telemetry Feature", "t_0"],
                ["Second Object", "First feature", 1],
                ["Second Object", "Second feature", 2]
            ]
        }
        return self.assertGetDataAsArray(testInput, Expected, oneShot=True)

    def setUp(self):
        """
        Function Type: Helper
        """
        self.filename = self.__class__.__name__ + '.db'
        self.config_file = "/home/lab/tests/test8/time-series2020-09-02-21-35-08-930263.ini"

    def tearDown(self):
        """
        Function Type: Helper
        """
        return


class AxonRegressionTests(unittest.TestCase):
    """
    Regression testing for functions uploading and downloading data to and from AXON
    """

    def testEmptyUpload(self):
        """
        Sends empty file to upload
        Returns:
            Success: Whether test had the expected output
        """
        return self.assertEqual(GUIDeveloper().GUIUpload(""), (False, 0))

    def testUploadFail(self):
        """
        Sends bad file to upload
        Returns:
            Success: Whether test had the expected output
        """
        return self.assertEqual(GUIDeveloper().GUIUpload(""), (False, 0))

    def testUploadSuccess(self):
        """
        Sends expected file to upload
        Returns:
            Success: Whether test had the expected output
        """
        print("Content file in test is: ", self.content_file)
        return self.assertEqual(GUIDeveloper().GUIUpload(self.content_file)[0], True)

    def testUploadSuccessDev(self):
        """
        Sends expected file to upload in the development space
        Returns:
            Success: Whether test had the expected output
        """
        return self.assertEqual(GUIDeveloper().GUIUpload(self.content_file, mode="development")[0], True)

    def testCorrectUploadID(self):
        """
        Sends expected file to upload and checks the ID received
        Returns:
            Success: Whether test had the expected output
        """
        return self.assertIsInstance(GUIDeveloper().GUIUpload(self.content_file)[1], str)

    def testDownloadBadID(self):
        """
        Prompts AXON to download an ID that does not exist
        Returns:
            Success: Whether test had the expected output
        """
        return self.assertEqual(GUIDeveloper().GUIDownload("0", self.test_directory)["success"], False)

    def testDownloadSuccess(self):
        """
        Prompts AXON to download an ID that does exist
        Returns:
            Success: Whether test had the expected output
        """
        return self.assertEqual(GUIDeveloper.GUIDownload(self.expected_id, self.test_directory)["success"], True)

    def setUp(self):
        """
        Function Type: Helper
        """
        self.filename = self.__class__.__name__ + '.db'
        self.content_file = "/home/lab/5f62d5440aa99f000c332488/intel-driveinfo-zip-v1.zip"
        self.expected_id = "5f6845cc49da2d0015f2b005"
        self.test_directory = "/home/lab/5f62d5440aa99f000c332488/"

    def tearDown(self):
        """
        Function Type: Helper
        """
        # self.env.close()
        # self.env = None
        # test_support.rmtree(self.homeDir)
        return


def suite():
    from sys import modules
    loader = unittest.TestLoader()
    suites = loader.loadTestsFromModule(modules[__name__])
    return suites


def API(options=None):
    """
    API for the default application in the graphical interface.
    Args:
        options: Commandline inputs.
    Returns:
    """
    if options.debug:
        print("Options are:\n{0}\n".format(options))
    ###############################################################################
    # Graphical User Interface (GUI) Configuration
    ###############################################################################
    print("options: ", str(options.mode))

    if options.mode == "Test":
        unittest.main(defaultTest='suite')
    else:
        print("Error in Selection")


def main():
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--example", action='store_true', dest='example', default=False,
                      help='Show command execution example.')
    parser.add_option("--debug", action='store_true', dest='debug', default=True, help='Debug mode.')
    parser.add_option("--more", dest='more', default=False, help="Displays more options.")
    parser.add_option("--mode", dest='mode', default="Test", help="Mode of Operation.")
    (options, args) = parser.parse_args()

    ##############################################
    # Main
    ##############################################
    API(options)
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
    print("Execution time: " + str(q - p))
