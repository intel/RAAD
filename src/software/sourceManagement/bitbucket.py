#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
# @package bitbucket
import optparse, datetime, traceback, requests, pprint, getpass
from requests.auth import HTTPBasicAuth
from cryptography.fernet import Fernet
from src.software.utilsCommon import getTempPathAndFileName
from src.software.debug import whoami


class BitBucket():
    """
    Class to pull code repos for a base address used with Bitbucket/Github.
    """
    debug = False

    # BitBucket URL
    baseUrlAddress = 'https://nsg-bit.intel.com'

    # BitBucket API version
    baseVersion = 1.0  # 'BitBucket REST API version

    # HTTP connect/read Timeout
    timeout = "30"  # 'Connect/read timeout in seconds

    username = None
    password = None
    keyRuntime = None  # Runtime generated key.
    keyTokenUserName = None    # Runtime token for Username.
    keyTokenPassword = None  # Runtime token for password.
    keyStatus = "Hidden"

    def __init__(self,
                 # Login
                 username: str = None,
                 password: str = None,
                 debug: bool = False,
                 baseUrlAddress: str = None,
                 baseVersion: str = None,
                 timeout: int = None):
        # Login
        if username is not None and isinstance(username, str):
            self.keyRuntime, self.keyTokenUserName = self.encryptCredentials(inputMsg=username)
        if password is not None and isinstance(password, str):
            self.key, self.keyTokenUserName = self.encryptCredentials(inputMsg=username, key=self.keyRuntime)
        del username, password
        self.hideCredentialsInfo()
        self.debug = debug

        # BitBucket URL
        if baseUrlAddress is not None:
            self.baseUrlAddress = baseUrlAddress

        # BitBucket API version
        if baseUrlAddress is not None:
            self.baseVersion = baseVersion

        # HTTP connect/read Timeout
        if timeout is not None:
            self.timeout = timeout  # 'Connect/read timeout in seconds
        return

    @staticmethod
    def getCredentials():
        username = getpass.getpass('Username:')
        password = getpass.getpass('Password:')
        return username, password

    def hideCredentialsInfo(self):
        username = "President Skroob"
        self.username = username

        # Password for matched luggage
        password = "123456"
        self.password = password
        self.keyStatus = "Hidden Text"
        return

    def unhideCredentialsInfo(self):
        username = self.decryptCredentials(self.keyRuntime, self.keyTokenUserName)
        self.username = username

        # Password for matched luggage
        password = self.decryptCredentials(self.keyRuntime, self.keyTokenPassword)
        self.password = password
        self.keyStatus = "Plain Text"
        return

    def verifyCredentialsExist(self):
        if self.keyRuntime is not None and \
           self.keyTokenUserName is not None and \
           self.keyTokenPassword is not None and \
           self.keyStatus is "Hidden":
            return True
        return False

    def verifyCresentialsAssert(self):
        assert self.verifyCredentialsExist() is True, "User Credentials do not exist. Please add them."

    def encryptCredentials(self, inputMsg: str = None, key=None):
        if key is None:
            key = Fernet.generate_key()
        cipher = Fernet(key)
        encodedInput = inputMsg.encode('utf-8')
        keyToken = cipher.encrypt(encodedInput)
        del inputMsg
        if self.debug:
            print(key)
            print(keyToken)
        return key, keyToken

    def decryptCredentials(self, key, tokenInput):
        # Create a cipher and decrypt when you need your password or senstive information.
        cipher = Fernet(key)
        secretText = cipher.decrypt(tokenInput).decode('utf-8')
        if self.debug:
            print(secretText)
        return secretText

    @staticmethod
    def getHelpURL():
        return "https://docs.atlassian.com/bitbucket-server/rest/5.16.0/bitbucket-rest.html"

    @staticmethod
    def getBaseURL(baseAddr: str = None):
        if baseAddr is None:
            baseAddr = "nsg-bit.intel.com"
        req_url = f"https://{baseAddr}"
        return req_url

    def getRestVersionURL(self, baseAddr: str = None, ver: str = None):
        if ver is None:
            ver = "1.0"
        req_url = f"{self.getBaseURL(baseAddr=baseAddr)}/rest/api/{ver}"
        return req_url

    def getProjectsURL(self, baseAddr: str = None, ver: str = None):
        req_url = f"{self.getRestVersionURL(baseAddr=baseAddr, ver=ver)}/projects"
        return req_url

    def getProjectReposURL(self, baseAddr: str = None, ver: str = None, project: str = None):
        req_url = f"{self.getProjectsURL(baseAddr=baseAddr, ver=ver)}/{project}/repos"
        return req_url

    def getRepoURL(self, baseAddr: str = None, ver: str = None, project: str = None, repo: str = None):
        req_url = f"{self.getProjectReposURL(baseAddr=baseAddr, ver=ver, project=project)}/repos/{repo}"
        return req_url

    def getRepoCommitsURL(self, baseAddr: str = None, ver: str = None, project: str = None, repo: str = None):
        req_url = f"{self.getRepoURL(baseAddr=baseAddr, ver=ver, project=project, repo=repo)}/commits"
        return req_url

    def getProjectsAndRepos(self, baseAddr: str = None, ver: str = None):
        self.verifyCresentialsAssert()
        projectList = list()
        pairProjectRepoList = list()
        headers = {'Content-Type': 'application/json'}

        # Pull all projects
        # Note: Request 100 repositories per page (and only their slugs), and the next page URL
        # Sample I.E. https://nsg-bit.intel.com/rest/api/1.0/projects/
        # ndict = {"size": 5,
        #          "limit": 25,
        #          "isLastPage": true,
        #          "values": [{"key":
        #                          "ARC",
        #                      "id": 2962,
        #                      "name": "ARCHIVED",
        #                      "description": "ARCHIVED Repos",
        #                      "public": false,
        #                      "type": "NORMAL",
        #                      "links": {"self": [{"href": "https://nsg-bit.intel.com/projects/ARC"}]}},
        #                     {"key": "FSEDEV",
        #                      "id": 1507,
        #                      "name": "FSE-DEV",
        #                      "public": false,
        #                      "type": "NORMAL",
        #                      "links": {"self": [{"href": "https://nsg-bit.intel.com/projects/FSEDEV"}]}},
        #                     ..., ],
        #          "start": 0}
        # Keep fetching pages while there's a page to fetch
        isLastPage = False
        nextStart = 0
        while isLastPage is False:
            next_page_url = f"{self.getProjectsURL(baseAddr=baseAddr, ver=ver)}?start={str(nextStart)}"
            self.unhideCredentialsInfo()
            response = requests.get(url=next_page_url,
                                    auth=HTTPBasicAuth(username=self.username, password=self.password),
                                    headers=headers,
                                    timeout=self.timeout)
            self.hideCredentialsInfo()
            page_json = response.json()
            try:
                nextStart = int(page_json['nextPageStart'])
                if page_json["isLastPage"] is 'false' or page_json["isLastPage"] is False:
                    isLastPage = False
                else:
                    isLastPage = True
                for projectObj in page_json['values']:
                    projectItem = projectObj['key']
                    projectList.append(projectItem)
                # Get the next page URL, if present
                # It will include same query parameters, so no need to append them again
            except BaseException as ErrorContext:
                print(f"{whoami()} {ErrorContext} {response.status_code} {response.text} {response.content}")

        # Collect repos
        # Note: Request 100 repositories per page (and only their slugs), and the next page URL
        # Sample I.E. https://nsg-bit.intel.com/rest/api/1.0/projects/ISE/repos/3dxp-trunk
        # dict = {"size":25,"limit":25,"isLastPage":false,
        #         "values":[
        #             {"slug":"3dxp-trunk",
        #              "id":133,
        #              "name":"3dxp-trunk",
        #              "hierarchyId":"5b71d05c041612345df3",
        #              "scmId":"git",
        #              "state":"AVAILABLE",
        #              "statusMessage":"Available",
        #              "forkable":false,
        #              "project":{"key":"ISE",
        #                         "id":22,
        #                         "name":"ISE",
        #                         "public":false,
        #                         "type":"NORMAL",
        #                         "links":{"self":[{"href":"https://nsg-bit.intel.com/projects/ISE"}]}},
        #                                           "public":false,
        #                                           "links":{"clone":[{"href":"https://nsg-bit.intel.com/scm/ise/3dxp-trunk.git",
        #                                                               "name":"http"},
        #                                                             {"href":"ssh://git@nsg-bit.intel.com:7999/ise/3dxp-trunk.git",
        #                                                              "name":"ssh"}],
        #                                                    "self":[{"href":"https://nsg-bit.intel.com/projects/ISE/repos/3dxp-trunk/browse"}]
        #                                                    },
        #                                            },
        #                                  },
        #                        },
        #              },
        #              ...
        #         ],
        #        }
        for repo in projectList:
            repoList = list()
            isLastPage = False
            nextStart = 0
            while isLastPage is False:
                next_page_url = f"{self.getRepoURL(baseAddr=baseAddr, ver=ver, project=repo)}?start={str(nextStart)}"
                self.unhideCredentialsInfo()
                response = requests.get(url=next_page_url,
                                        auth=HTTPBasicAuth(username=self.username, password=self.password),
                                        headers=headers,
                                        timeout=self.timeout)
                self.hideCredentialsInfo()
                page_json = response.json()
                try:
                    nextStart = int(page_json['nextPageStart'])
                    if page_json["isLastPage"] is 'false' or page_json["isLastPage"] is False:
                        isLastPage = False
                    else:
                        isLastPage = True
                    for repoObj in page_json['values']:
                        repoItem = repoObj['slug']
                        repoList.append(repoItem)
                    # Get the next page URL, if present
                    # It will include same query parameters, so no need to append them again
                except BaseException as ErrorContext:
                    print(f"{whoami()} {ErrorContext} {response.status_code} {response.text} {response.content}")
            pairProjectRepoList.append([repo, repoList])

        return (pairProjectRepoList)

    def getRepoCommits(self, baseAddr: str = None, ver: str = None, project: str = None, repo: str = None):
        self.verifyCresentialsAssert()
        headers = {'Content-Type': 'application/json'}

        # Pull all project commits
        # Note: Request 100 repositories per page and the next page URL
        # Sample I.E. https://nsg-bit.intel.com/rest/api/1.0/projects/ISE/repos/3dxp-trunk/commits
        # ndict = {"values": [{"id": "1606a7267b0524f7a84c9dfe8197872fb1c68daa",
        #                      "displayId": "1606a7267b0",
        #                      "author": {"name": "sys_nsg_qb_ci",
        #                                 "emailAddress": "sys_nsg_qb_ci@intel.com",
        #                                 "id": 29105,
        #                                 "displayName": "NSG Quickbuild CI",
        #                                 "active": true,
        #                                 "slug": "sys_nsg_qb_ci",
        #                                 "type": "NORMAL",
        #                                 "links": {"self": [{"href": "https://nsg-bit.intel.com/users/sys_nsg_qb_ci"}]}
        #                                 },
        #                      "authorTimestamp": 1547240258000,
        #                      "committer": {"name": "sys_nsg_qb_ci",
        #                                    "emailAddress": "sys_nsg_qb_ci@intel.com",
        #                                    "id": 29105,
        #                                    "displayName": "NSG Quickbuild CI",
        #                                    "active": true,
        #                                    "slug": "sys_nsg_qb_ci",
        #                                    "type": "NORMAL",
        #                                    "links": {"self": [{"href": "https://nsg-bit.intel.com/users/sys_nsg_qb_ci"}]}},
        #                      "committerTimestamp": 1547240258000,
        #                      "message": "Merge branch bugfix/MBE-26888-remove-media-clock-gating into integration using Build, Test and Promote by idewji for commit: 416e06095ea58be7b6f872fe28d763469091cf3c",
        #                      "parents": [{"id": "048ebe3ce5118660d3f0f0b74746f87c9e6d3e57",
        #                                   "displayId": "048ebe3ce51"},
        #                                  {"id": "416e06095ea58be7b6f872fe28d763469091cf3c",
        #                                   "displayId": "416e06095ea"}],
        #                      "properties": {"jira-key": ["MBE-26888"]}
        #                      },
        #                     ...,
        #                     ]}
        # Keep fetching pages while there's a page to fetch
        repoMessageList = list()
        isLastPage = False
        nextStart = 0
        while isLastPage is False:
            next_page_url = f"{self.getRepoCommitsURL(baseAddr=baseAddr, ver=ver, project=project, repo=repo)}?start={str(nextStart)}"
            self.unhideCredentialsInfo()
            response = requests.get(url=next_page_url,
                                    auth=HTTPBasicAuth(username=self.username, password=self.password),
                                    headers=headers,
                                    timeout=self.timeout)
            self.hideCredentialsInfo()
            page_json = response.json()
            try:
                nextStart = int(page_json['nextPageStart'])
                if page_json["isLastPage"] is 'false' or page_json["isLastPage"] is False:
                    isLastPage = False
                else:
                    isLastPage = True
                for repoObj in page_json['values']:
                    repoItem = repoObj['message']
                    repoMessageList.append(repoItem)
                # Get the next page URL, if present
                # It will include same query parameters, so no need to append them again
            except BaseException as ErrorContext:
                print(f"{whoami()} {ErrorContext} {response.status_code} {response.text} {response.content}")
        return repoMessageList

    def getExploreAllRepoCommentMeta(self, baseAddr: str = None, ver: str = None):
        self.verifyCresentialsAssert()
        setList = list()
        # Error handling.
        if baseAddr is not None and self.baseUrlAddress is None:
            baseAddr = baseAddr
        elif baseAddr is None and self.baseUrlAddress is not None:
            baseAddr = self.baseUrlAddress
        else:
            return setList

        if ver is not None and self.baseUrlAddress is None:
            ver = ver
        elif ver is None and self.baseUrlAddress is not None:
            ver = self.baseVersion
        else:
            return setList

        if ver is None and self.baseVersion is None:
            return setList
        (pairProjectRepoList) = self.getProjectsAndRepos(baseAddr=baseAddr, ver=ver)
        for _, project, repoList in enumerate(pairProjectRepoList):
            for _, repo in enumerate(repoList):
                comments = self.getRepoCommits(baseAddr=baseAddr, ver=ver, project=project, repo=repo)
                setList.append([project, repo, comments])
        return setList


def API(options=None):
    """ API for the default application in the graphical interface.
    Args:
        options: Commandline inputs.
    Returns:
    """
    if options.debug:
        print("Options are:\n{0}\n".format(options))
    ###############################################################################
    sourceObj = BitBucket(debug=options.debug)
    sourceObj.getCredentials()
    commitMessages = sourceObj.getExploreAllRepoCommentMeta()
    if options.debug:
        pprint.pprint(commitMessages)  # Please note this is alot of data...
        outfileRef = getTempPathAndFileName(extensionName="_debug.txt", genPath=True, genFile=True)
        with open(outfileRef, 'w') as fileSaver:
            for cLine in commitMessages:
                fileSaver.writelines(cLine)
    return


def main():
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--debug", action='store_true', dest='debug', default=True, help='Debug mode.')
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
