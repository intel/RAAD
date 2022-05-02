#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
# @package triage
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
"""
Process Developed by Joseph Tarango
Triage
-> Rationality:
We do triage work to ensure that: 
    The process of reporting test failures is quick.
    Assess and classify new JIRA sightings as FW, hardware, drive, test/test environment, or ‘other’ failures.
    Coordinate "treatment" of these failures with the appropriate teams/individuals.
    Work with the Program Manager & SI to prioritize new JIRA.
    Ensure new JIRA sighting resolutions start off in the right direction.

-> Suggested Workflow:
I. BVT Status Check:
    Go to https://nsg-bamb.intel.com/browse/GEN3-G3TCI.
    Check if the last BVT tests done are successful.
    Indicate it in the ‘BVT Notes/Summary’ section in the NIT report (see section Report Outline below).
. Main Triage:

    Create a working directory in ‘Y:/Users’ to save your repo clone + debug artifacts (logs, asserts, etc).
    Go to the Conval analysis page of PDR from <http://tidbits.lm.intel.com/contvaldashboard/detail.php?program=cd> and select the graph corresponding to ‘15-xx-x'. You’ll see all the machines that were tested and test results for that day.
    Update your local repository to the firmware version used by Conval.
    Create a folder in Outlook specifically for Conval reports and create a ‘rule’ that will ensure that all the NIT email reports are saved in this folder. (This makes it really simple to search if the current failure string that you’re observing has been previously reported, or not).
    Go to <http://tidbits.lm.intel.com/tidbits/waitQueueManager.php?tidbit=cd> and clear all the queued tests.
    First Pass:
        Fill out an excel page with basic details like name of machine, test name, basic comment that you feel should be made, etc.
        Remote login to the machine. Look for the details in the FAST interface. Note down pertinent details in your excel sheet.
        Open Twidl and see the drive status. This is being done because it has been observed that the status reported on TIDBITS and the actual drive status can be sometimes different. Note this down in your excel sheet as well. Look for the FW version of the drive, also look at the maxLBA field. All this will indicate whether the drive is truly healthy.
        Write notes like information regarding this drive’s history. Example scenario, a drive has been failing the basic precommit test and you know that this particular drive hasn’t had a good defect map loaded……
        Why excel sheet? Note that you don’t have to write something redundant that is already present in FAST. The reason for having these excel notes is so you can write, based on your experience, what might be the issue or what needs to be looked at by the developer who will be assigned the issue. Also, you will have proper documentation of what you actually did to a certain drive on a certain day after it encountered a certain failure. Remember, the goal is to have fast triaging work, not slow it down by writing redundant info. You can replace this excel with your own Onenote/notebook/sticky notes, etc.
        Use VNC for logging in, this will ensure that you’re not blocking someone from looking into the machine at the same time.
    Check the drives physically:
        As the drives are local, you should go to the lab and physically check if any of them has something like an assert (indicated by a red solid/blinking LED). Why do this? TIDBITS reporting anomaly, as explained above.
        Do miscellaneous checks, like whether the drive is properly mounted (look out for quarch and L06x drives especially).
    Final pass:
        Now you have a comprehensive overview of the actual state of the drive. So you should get more details now.
        Retrieve and inspect test logs (to understand what the failure looks like from a host’s perspective), and if appropriate, do the test implementation to understand the stimulus it provides to the drive. Also, note that the availability of logs depends on the test environment and the test failure.
    Scenarios: (Most scenarios can be found in this page if you scroll up, assert response is given here just as an example). If the drive status shows:
        ASSERT:
            The assert is usually of the form: ASSERT_X (where X is the address).
            Open the file AssertTable-<firmware_version>.csv, located at: Y://fast-data//Releases//Nightly//PDRShortBranch//2015WWXX.X//PleasantdaleRefresh//
            Do a quick search for the assert address. You will get a corresponding assert name. Note it down
            Open TWIDL and type in the following commands:      unlock()      setTestCommandRouting(1)      rdump(“<Path-to-your-repo>/ ASSERT_<assert_name>_<firmware_version>_<machine#>_CORE_0.bin”)      unlock()      setTestCommandRouting(2)      rdump(“<Path-to-your-repo>/ ASSERT_<assert_name>_<firmware_version>_<machine#>_CORE_1.bin”)
        XASSERT:
            DO NOT powercycle the drive. A developer can look into the live assert, if you’re not doing it already.
            Ensure the drive is preserved. Do not allow the drive to be LLF'd.
        De-enum without ASSERT: Recover using the tool ‘RecoverDrive’ (shortcut on Desktop) and hitting RTC Powercycle
        ASSERT dump unavailable:
            You can get the ASSERT table by using the 'makeasserttable' flag with buildgen.
            Command: #To select the appropriate target: buildgen3.py --listtargets #To create the assert table buildgen3.py --target <selected target> --makeasserttable
        BAD CONTEXT
        If you observe a BAD_CONTEXT or INITIALIZED0 or any such string in the 'drive status' field after starting twidl and suspect an assert, then it is advisable to do a PLI sidetrace process to capture the assert.
        Note that this is important to understand and debug ASSERTS that neither show up in the 'Drive Status' field, nor do they result in the red LED blinking.
        To perform this, enter the following (DO NOT use the edump() command):
        
        mkdir C://plisidetrace
        cd /d C://plisidetrace
        mkdir "core 0" "core 1" "sidetrace"
        cd "core 0"
        C://fast-tools//TwidlTVE//applications//parsePliDump.py --core 0 -d 1
        cd ..
        cd "core 1"
        C://fast-tools//TwidlTVE//applications//parsePliDump.py --core 1 -d 1
        cd ..
        cd "sidetrace"
        C://fast-tools//TwidlTVE//applications//parseSideTrace.py -d 1 --details

        mkdir C://plisidetrace cd /d C://plisidetrace mkdir "core 0" "core 1" "sidetrace" cd "core 0" C://fast-tools//TwidlTVE//applications//parsePliDump.py --core 0 -d 1 cd .. cd "core 1" C:\fast-tools\TwidlTVE\applications\parsePliDump.py --core 1 -d 1 cd .. cd "sidetrace" C:\fast-tools\TwidlTVE\applications\parseSideTrace.py -d 1 --details
    
        Report a JIRA issue:
            Search for the corresponding failure string in the previous NIT reports folder in your email. If you can find it, then simply copy the same in your report and follow the steps from (d)
            If you weren’t able to find the issue on your previous NIT reports, then, do the following:
                Determine the team (FWOPS, SWT, NSGSE, etc.) that the failure corresponds to.
                Go to the page (https://nsg-jira.intel.com), select the appropriate dashboard and look at the active/open JIRAs.
                If you still can’t find it, then use the search box at the top right of the page.
                If you are able to find the issue, then follow the steps from (d). 
                Quick tip: If you see an issue that is exactly what you’ve seen but it has been closed recently, then contact the assigned developer before reporting; it could be that this current failure might have occurred under different circumstances. If the issue you found is exactly the same & has been fixed (but is quite older) then it is better to just create a new JIRA sighting.
        If you’ve not been able to find the corresponding JIRA in the above steps, then you must create one. To do this:
            Go to the page (https://nsg-jira.intel.com/secure/CreateIssue!default.jspa) to create a sighting.
            The various fields to be filled up are:
                Summary: Short brief description of the failure. Avoid writing the exact NIT Work Week number.
                Priority: Select ‘P2 High’. If the assigned developer then thinks it needs to be changed, he can do it.
                Exposure: ‘Low’ is okay as a default value if you’re not sure.
                Components: Not mandatory to be filled out.
                Security Level: NSG SE
                Program:
                PDR - if the issue was found on a PDR mule / PDR drive
                Note: When a developer investigates the issue and sees that this also affects another product like DV, then that product must be added to the list of Affected Products.
                Affects Version/s: ‘NIT Branch Build’. It can be updated later if need be.
                Submitter Org: ‘Intel – FW Development’
                Suspected Problem Area: Select according to the failure observed.
                Issue Characteristic: According to the failure observed.
                Scrum Team: PCIe Team
                Description: This field has to be filled carefully and given verbose information regarding the failure, including the NIT work week, machine number, firmware build in use, test name, test category, etc. 
                If you think that the nature of the failure can be described in a few lines of the logs, then just copy paste from the log file directly instead of attaching the entire log file as an attachment. 
                If the issue is an assert, then just paste the small code snippet in the description with the {no format} tags starting and ending it.
                Labels: This is completely based on the specific failure in question. However, the common ones are:
                PDR_NIT: For all NIT failures
                100sPhase2b: For failures observed on PDR mules.
                100sPhase3a: For failures observed on the L06A drives.
                100sPhase3b: For failures observed on the L06B drives.
                Mailing List: Add the names of developers whom you know have good knowledge of this particular issue or have worked on it recently. Adding the manager’s name if you’re not sure isn’t a bad practice.
        
        If the issue isn’t a new one just created, then you should comment on the JIRA. Click on the ‘Comment’ link at the bottom of the JIRA page that the recent NIT failure corresponds to.
        The information you provide should include:
             - Machine number
             - NIT work week
             - Firmware build
             - Test name
             - Test category
             - If the drive is quarch, L06A, L06B, SS, etc.
             - TIDBITS URL for the PDRNITWWxx.
        Attach the corresponding files like the assert dumps, logs, etc. to the JIRA issue (More>Attach Files)
    Post-triage:

        FA Summary:
            Go to the NIT analysis page of PDR from <http://tidbits.lm.intel.com/tidbits> & select the graph corresponding to ‘PDRNIT2015WWxx.x'.
            If a drive hasn’t passed a test, you will be able to click on the ‘Fail’ link (in red) against the name of the machine that ran the test on the drive.
            Now, fill out the text-box below the ‘ADD TO FA LOG’ section on the page with an appropriate/more specific description than the one already present there (note that you don’t have to write the JIRA# here).
            Select the ‘Set as FA Summary’ tick-box.
            Hit ‘Post’.
        Triage Mode:
            Go to the NIT analysis page of PDR from <http://tidbits.lm.intel.com/tidbits> & select the graph corresponding to ‘PDRNIT2015WWxx.x'.
            On the right sidebar, select ‘TRIAGE MODE’.
            Now fill in the JIRA# across the names of the machines that failed the test in question.
            NIT report Outline:

-> NIT report Outline:
<Product Family> Continous Validation NVMe 201X WWXX.X
What’s new in Conval?
--- Enter important information regarding the NIT run that includes:
        New Bootloader version
        New Lightswitch version
        Drive population info (adding new set of drives)
        Drive location change (new rack used)…. and so on  

 Conval Triage schedule:
    Primary owners -> The main guys responsible for triaging
    Secondary -> New guys (if at all) who are being brought up to speed to take over triage work in the near future 

NVME Notes/Summary:
       NVME Failures:
        Enter the failures encountered in the N.I.Testing. The format agreed upon is:
        <number of failures>x <Brief Failure Description> (JIRA hyperlink) <NEW failure?> <Developer assigned?>

For example:
4x De-enum failure (NSGSE-30160)
1x Drive de-enumerated during ASSERTTest (NSGSE-31528) NEW UNASSIGNED

BVT Notes/Summary: 
1. BVT machines are <all healthy/ready> or <not healthy>
2. BVT builds are <passing> or <not passing>
Test Info:
TIDBITS:                               <TIDBITS URL for current NIT>
TWIDL:                                 <version#>
Light-switch Revision :  <LS files’ location in the Y drive>
Drive Population:            <Total drives tested> (X L06A, X L06B, X Mules)

Firmware Details:
FW Tag:              <Tag as seen in Mercurial> 
Binary:                <Binary files’ location in the Y drive> 
Changeset:
<Changes in the latest firmware of last night using which NIT was done. It can be found in the Mercurial. Note that changes related to the associated JIRAs need to be mentioned, other ones like merge tags needn’t be. No entry should take more than a line>

Comments:
    <Mention appropriate comments like if you need to specify if a particular machine failed due to a prep issue; so that the other engineers know the reason why the number of failures on the TIDBITS page and in this report do not match (assumption is, obviously, that one wouldn’t report a prep error under the ‘NVME failures’ section)>
    <Report if any of the triage owners aren’t available, etc.>
    <Write ‘Please email if you have any suggestions regarding NIT improvements>

Thanks <if you want to>, 
Owners’ names    
"""
if __name__ == '__main__':
    """Performs execution delta of the process."""
    import datetime, traceback
    p = datetime.datetime.now()
    try:
        print("")
    except Exception as e:
        print("Fail End Process: ", e)
        traceback.print_exc()
    q = datetime.datetime.now()
    print("Execution time: " + str(q - p))
