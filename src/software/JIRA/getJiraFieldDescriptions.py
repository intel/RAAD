#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Rogelio Macedo, Joseph Tarango
# *****************************************************************************/

import json, os, datetime
import traceback
from getpass import getpass
import requests
import urllib3


def readPasswordFile(defaultFile=".raadProfile/credentials.conf"):
    """

    Args:
        defaultFile: file containing newline separated credentials

    Returns:

    """
    defaultPasswordFile = os.path.abspath(os.path.join(os.getcwd(), defaultFile))
    if os.path.isfile(defaultPasswordFile):
        with open(defaultPasswordFile) as openFile:
            fileMeta = openFile.read()
            INFO = fileMeta.split('\n')  # Separator is \n
            t = [str(INFO[0])]
        pw: str = getpass("password: ")
        t.append(pw)
    return tuple(t)


def getJiraFields():
    basicAuth: tuple[str, str] = readPasswordFile()
    MAX_RESULTS = 50
    HOST_NAME: str = "https://nsg-jira.intel.com"
    jira_options: dict = {
        'verify': False,
        'server': f"{HOST_NAME}",  # format strings only work in Python 3
        'project': "NSGSE",
        'maxresults': MAX_RESULTS
    }
    # Create a Session to contain your basic AUTH, it will also persist your cookies
    USER_AGENT = \
        "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
    authed_session = requests.Session()
    authed_session.headers.update({'User-Agent': USER_AGENT})

    # WARNING: You should point this to your cert file for the server to actually
    # verify the host. Skips verification if set to false
    # With setup from above, things are okay if it's set to false
    CERT_FILE = False
    authed_session.verify = CERT_FILE  # Cert verification, will not verify on false
    returnData = None
    authed_session.auth = basicAuth  # (basicAuth[0], basicAuth[1])
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    returnData = authed_session.get(HOST_NAME + "/rest/api/2/field")
    writeFile(data=returnData)


def writeFile(data):
    finalFilename = "data/fieldsInfo.1.json"
    with open(finalFilename, "w") as outfile:
        outfile.write(json.dumps(data.json(), indent=4))
    return


if __name__ == '__main__':
    """Performs execution delta of the process."""
    pStart = datetime.datetime.now()
    try:
        getJiraFields()
    except Exception as errorMain:
        print("Fail End Process: {0}".format(errorMain))
        traceback.print_exc()
    qStop = datetime.datetime.now()
    print("Execution time: " + str(qStop - pStart))
