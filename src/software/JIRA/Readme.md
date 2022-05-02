----------------------------
I. File list
----------------------------

commit_PROA.txt         Tab delimited team commits, sprint date, and asks.
commit_PROA_end.txt     A copy (done manually) of the previous sprint's team commits.
commit_PROD.txt         Tab delimited team commits, sprint date, and asks.
commit_PROD_end.txt     A copy (done manually) of the previous sprint's team commits.
milestones.txt          Tab delimited program milestones, tags, target date, and color to use for milestones
classCommonReports.py   Class used to gather data for commonly run reports
classGetJiraIssues.py   Class used to access and retrieve Jira information from the server using the REST interface
classHtmlGen.py         Class used to make outputting in HTML format easier.  Provided functions for tables, and graphs as well.
classJiraIssues.py      Class used to format the JSON formatted Jira issue into a dictionary format.  Note: Only fields of interest are placed in the dictionary
classJiraIssuesList.py  Class used to hold a list of dictionaries of each issue.  also some functions that deal the filtering and gathering information from those lists.
classSupportFiles.py    Class used to access and format the support tab delimited files (commits, milestones)
review_retro_plan.py    Produces a HTML template for the end of sprint Review, Retrospective, and plan for next sprint. Note: Uses JiraSnapshot_eos.json, which is a snapshot of the end of the sprint.
sprint_graph.py         Produces a HTML report showing the planned work sprint by sprint with milestone indications 
team_progress.py        Produces the DSU html report
updateSnapshot.py       Updates the local Jira Snapshot (JiraSnapshot.json) with Jira issues that have changes since the last check.  Existing snapshot is renamed
wsr.py                  Produces the Weekly Status Report (WSR) information, to help identify things that need to be reported in that report.
commits.json            Temporary file, can be deleted
JiraSnapshot.json       A snapshot of the Jira database in the format of one issue per line in JSON format.  JSON is the format returned by rest calls to the Jira server
JiraSnapshot_eos.json   A copy of the JiraSnapshot.json made (manually) at the end of the sprint and used by the review_retro_plan.py script


Script are designed to function using Python 2.7.2

----------------------------
II. Quick Start
----------------------------
Before performing any of the quick start instructions you need to do five things:
1) Install Python 2.7.2 on your system (http://www.python.org/download/releases/2.7.2/)
2) Make a directory and get the latest scripts from the sandbox
3) Un-archive all .zipX files (this will un-archive to a snapshot (JiraSnapshot.json))
4) Open a terminal/command/DOS window and change directories to where you put the scripts

    ----------------------------------------------------
    A. Produce DSU html files
    ----------------------------------------------------
    1) Run the updateSnapshot.py script.  Use your normal Jira login information when prompted.  This will update the local snapshot with the current information.
    2) Run team_progress.py script.  This will produce two files for each team:
        a) XXXX_dsu.html (where XXXX is the first 4 letters of the team name) - the HTML file to display during DSU
        b) XXXX_onenote.html (where XXXX is the first 4 letters of the team name) - A outline format of the issue by developer section to aid in taking notes.

    ----------------------------------------------------
    B. Produce WSR html file
    ----------------------------------------------------
    1) Run the updateSnapshot.py script.  Use your normal Jira login information when prompted.  This will update the local snapshot with the current information.
    2) Run wsr.py script.  This will produce one file:
        a) WSR_WWXX_onenote.html (where XX is the work week) - the HTML file with notes about what was completed and in progress for a specific week

    ----------------------------------------------------
    C. Produce Review, Retro, and Plan Report html file
    ----------------------------------------------------
    1) Run the updateSnapshot.py script at the end of the sprint.  Use your normal Jira login information when prompted.  This will update the local snapshot with the current information.
    2) Copy the JiraSnapshot.json file and replace the JiraSnapshot_eos.json with it.  The JiraSnapshot_eos.json is the snapshot at the end of the sprint.  Archive it and commit it in mercurial
    3) Copy the commit files (commit_PROA.txt & commit_PROD.txt) over the previous print commit files (commit_PROA_end.txt & commit_PROA_end.txt)
    4) Update the current commit files (commit_PROA.txt & commit_PROD.txt) with the new end of sprint date.
    5) Run review_retro_plan.py script.  This will produce one file for each team:
        a) eos_rrp_wwYY_XXXX.html (where XXXX is the first 4 letters of the team name, and YY is the work week of the planned sprint) - The review, retrospective, and Plan template

    ----------------------------------------------------
    D. Produce a Sprint map / graph file
    ----------------------------------------------------
    1) Run the updateSnapshot.py script.  Use your normal Jira login information when prompted.  This will update the local snapshot with the current information.
    2) Run sprint_graph.py script.  This will produce one files for each team:
        a) XXXX_graph.html (where XXXX is the first 4 letters of the team name) - the HTML file to display a sprint by sprint plan with milestone color coding



----------------------------
III. Questions And Answers
----------------------------

Q:  When I run updateSnapshot, it fails quickly and displays a huge error message with error code 400 like this:
    Retrieving issue list:
    The server couldn't fulfill the request.
    Error code:  400
    URL: P:\nsg-jira.intel.com\rest\api\2\search?jql=((updated >= "2013-07-31") and
    (project = NSGSE) and issuetype in (Story, "Development Task", Sighting, HGST_Sighting) ) or issuekey=NSGSE-1135 or issuekey=NSGSE-10864 or issuekey=NSGSE-9873
    or issuekey=NSGSE-7285 or issuekey=NSGSE-12442 or issuekey=NSGSE-8942 or issuekey=NSGSE-8930 or issuekey=NSGSE-871 or issuekey=NSGSE-7944 or issuekey=NSGSE-10580 
    or issuekey=NSGSE-8928 or issuekey=NSGSE-1150 or issuekey=NSGSE-11977 or issuekey=NSGSE-8945 or issuekey=NSGSE-12577 or issuekey=NSGSE-9812 or issuekey=NSGSE-9055 
    or issuekey=NSGSE-6477 or issuekey=NSGSE-12814 or issuekey=NSGSE-12433 or issuekey=NSGSE-12824 or issuekey=NSGSE-11601 or issuekey=NSGSE-12932 or issuekey=NSGSE-3379 
    or issuekey=NSGSE-12551 or issuekey=NSGSE-12471 or issuekey=NSSE-9364 or issuekey=NSGSE-9358 or issuekey=NSGSE-11676 or issuekey=NSGSE-9368 or issuekey=NSGSE-12234 
    or issuekey=NSGSE-11948 or issuekey=NSGSE-12651 or issuekey=NSGSE-11933 or issuekey=NSGSE-11971 or issuekey=NSGSE-1108 or issuekey=NSGSE-960 or issuekey=NSGSE-12630 
    or issuekey=NSGSE-11705 or issuekey=NSGSE-12596 or issuekey=NSGSE-12593 or issuekey=NSGSE-11853 or issuekey=NSGSE-9367 or issuekey=NSGSE-12654 or issuekey=NSGSE-12713&fields=changelog,updated&expand=changelog&startAt=0&maxResults=40

A:  There is something wrong in your commits file (either a commit or stretch goal is messed up).  In the above error, cut and paste everything past the "jql=" into a Jira search.  It will point out the problem error if you don't see it in the commit file by inspection.  In the above error message, this is the actual problem.
    If you cut and paste into a search in Jira you will see that it can't find the NSSE-9364 issue, since the G was accidentally left out.

Q:  When I run updateSnapshot, it fails slower and displays a huge error message with error code 401 like this (but with the stuff past the error code omitted):
    Retrieving issue list:
    The server couldn't fulfill the request.
    Error code:  401
A:  There are two main causes of this.  
    1)  You typed your username or password wrong.  So try again.  
    2)  You typed your username or password wrong 3 times in the past and now Jira wants you to do a Captcha image to show that you are a real person.  
        With a browser surf to the Jira site.  Log out and log back in.  Do tha Captcha image check if prompted.

Q:  When I run a updateSnapshot or another script, it fails slower and displays a error message about decoding... Like this:
    Traceback (most recent call last):
      File "team_progress.py", line 464, in <module>
        aJiraIssue.parseJson(aLine.decode('latin1').encode('utf8'))
      File "C:\Users\daescamx\Documents\Jira_Rest_Scripts\classJiraIssues.py", line
    69, in parseJson
        self.issueDictionary["priority"] = jLine["fields"]["priority"]["name"]
    KeyError: 'name'

A:  Someone entered a Jira and did not complete all of the fields expected.  You need to change and check in the python code to handle this situation that I did not encounter.
    Note:  And error like the above was recently hit when a person entered a sighting without a priority.  I did not know that could be done since it had not been done before.
