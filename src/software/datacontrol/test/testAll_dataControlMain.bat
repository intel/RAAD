@echo off

CLS
echo ======================
echo Clear Screen
echo Datacontrol Gen Main Testing
set "LOG_FILE=test/testAll_dataControlMain_log.txt"
set "PY_FILE_READ_TEST=test/testRead_dataControlMain.py"
set "PY_FILE=dataControlGenMain.py"
set "UID_STRUCTURES_FILE=structures.csv"
echo Go One Directory Up
cd ..

echo Log File: %LOG_FILE%
echo Python File: %PY_FILE%
echo Read Test File: %PY_FILE_READ_TEST%
echo uid Structures File: %UID_STRUCTURES_FILE%

echo Clear File > %LOG_FILE%
echo ======================
echo Creating brand new structures_test.csv Test File. Vital for successful run. 
echo ==TESTING META FILE READ...
python %PY_FILE_READ_TEST% >> %LOG_FILE% 2>&1
if ERRORLEVEL 1 (
        goto :EXIT
)
echo done!


echo ==TESTING CREATE metaUID: AUTO
echo ==TESTING CREATE metaUID: AUTO >> %LOG_FILE% 
python %PY_FILE% --create [AUTO,testStructName1,6,Transport_PART,ADP,()] --debug --file %UID_STRUCTURES_FILE% >> %LOG_FILE% --debug 2>&1
if ERRORLEVEL 1 (
        goto :EXIT
)
echo done!

echo ==TESTING CREATE metaUID: SINGLE COMMAND LINE GIVEN UID
echo ==TESTING CREATE metaUID: SINGLE COMMAND LINE GIVEN UID >> %LOG_FILE% 
python %PY_FILE% --create [temp_it2,testStructName2,6,Transport_PART,ADP,()] --debug --file %UID_STRUCTURES_FILE% >> %LOG_FILE% 2>&1
if ERRORLEVEL 1 (
        goto :EXIT
)
echo done!

echo ==TESTING CREATE metaUID: MULTPLE COMMAND LINE GIVEN UIDs
echo ==TESTING CREATE metaUID: MULTPLE COMMAND LINE GIVEN UIDs >> %LOG_FILE%
python %PY_FILE% --create [AUTO,testStructName3,6,Transport_PART,ADP,();temp_4,testStructName4,6,Transport_PART,CDR,();temp_5,testStructName5,6,Transport_PART,CDR,();temp_6,testStructName6,6,Transport_PART,CDR,();temp_7,testStructName7,6,Transport_PART,CDR,();temp_8,testStructName8,6,Transport_PART,CDR,()] --file %UID_STRUCTURES_FILE% >> %LOG_FILE% 2>&1
if ERRORLEVEL 1 (
        goto :EXIT
)
echo done!

echo ==TESTING CREATE metaUID: ALREADY USED UID 
echo ==TESTING CREATE metaUID: ALREADY USED UID>> %LOG_FILE% 
python %PY_FILE% --create [0,testStructName0,6,Transport_PART,ADP,()] --debug --file %UID_STRUCTURES_FILE% >> %LOG_FILE% 2>&1
if ERRORLEVEL 1 (
        echo CORRECTLY FAULTED
        echo CORRECTLY FAULTED >> %LOG_FILE% 2>&1
)
echo Should have faulted!

echo ==TESTING DEPRECATE metaUID: SINGLE TEMP UID
echo ==TESTING DEPRECATE metaUID: SINGLE TEMP UID >> %LOG_FILE% 
python %PY_FILE% --deprecate [temp_it2,TWO] --debug --file %UID_STRUCTURES_FILE% >> %LOG_FILE% 2>&1
if ERRORLEVEL 1 (
        goto :EXIT
)
echo done!

echo ==TESTING DEPRECATE metaUID: MULTIPLE TEMP UIDs
echo ==TESTING DEPRECATE metaUID: MULTIPLE TEMP UIDs >> %LOG_FILE% 
python %PY_FILE% --deprecate [temp_0,TWO;temp_4,TWO] --debug --file %UID_STRUCTURES_FILE% >> %LOG_FILE% 2>&1
if ERRORLEVEL 1 (
        goto :EXIT
)
echo done!


echo ==TESTING DEPRECATE metaUID: SINGLE PERMANENT UID
echo ==TESTING DEPRECATE metaUID: SINGLE PERMANENT UID >> %LOG_FILE% 
python %PY_FILE% --deprecate [1,TWO] --debug --file %UID_STRUCTURES_FILE% >> %LOG_FILE% 2>&1
if ERRORLEVEL 1 (
        goto :EXIT
)
echo done!

echo ==TESTING DEPRECATE metaUID: MULTIPLE PERMANENT UIDs
echo ==TESTING DEPRECATE metaUID: MULTIPLE PERMANENT UIDs >> %LOG_FILE% 
python %PY_FILE% --deprecate [2,TWO;3,TWO] --debug --file %UID_STRUCTURES_FILE% >> %LOG_FILE% 2>&1
if ERRORLEVEL 1 (
        goto :EXIT
)
echo done!

echo ==TESTING DEPRECATE metaUID: MEDLEY UIDs
echo ==TESTING DEPRECATE metaUID: MEDLEY UIDs >> %LOG_FILE% 
python %PY_FILE% --deprecate [temp_8,TWO;1,ONE] --debug --file %UID_STRUCTURES_FILE% >> %LOG_FILE% 2>&1
if ERRORLEVEL 1 (
        goto :EXIT
)
echo done!

echo ==TESTING EDIT metaUID: SINGLE TEMP UID
echo ==TESTING EDIT metaUID: SINGLE TEMP UID >> %LOG_FILE% 
python %PY_FILE% --edit [temp_1,TWO,(owner='single_temp_edit',size='0x30')] --debug --file %UID_STRUCTURES_FILE% >> %LOG_FILE% 2>&1
if ERRORLEVEL 1 (
        goto :EXIT
)
echo done!


echo ==TESTING EDIT metaUID: MULTIPLE TEMP UIDs
echo ==TESTING EDIT metaUID: MULTIPLE TEMP UIDs >> %LOG_FILE% 
python %PY_FILE% --edit [temp_4,TWO,(owner='multiple_temp_edit',size='0x30');temp_6,TWO,(owner='multiple_temp_edit',autoparsability='WHOO')] --debug --file %UID_STRUCTURES_FILE% >> %LOG_FILE% 2>&1
if ERRORLEVEL 1 (
        goto :EXIT
)
echo done!


echo ==TESTING EDIT metaUID: MULTIPLE PERMANENT UIDs
echo ==TESTING EDIT metaUID: MULTIPLE PERMANENT UIDs >> %LOG_FILE% 
python %PY_FILE% --edit [4,TWO,(owner='multiple_perm_edit',size='0x30');5,TWO,(owner='multiple_perm_edit',size='0x30')] --debug --file %UID_STRUCTURES_FILE% >> %LOG_FILE% 2>&1
if ERRORLEVEL 1 (
        goto :EXIT
)
echo done!

echo ==TESTING EDIT metaUID: MEDLEY UIDs
echo ==TESTING EDIT metaUID: MEDLEY UIDs >> %LOG_FILE% 
python %PY_FILE% --edit [temp_7,TWO,(owner='Andrea_test',size='0x30');0,ONE,(owner='Andrea_test',autoparsability='WHOO')] --debug --file %UID_STRUCTURES_FILE% >> %LOG_FILE% 2>&1
if ERRORLEVEL 1 (
        goto :EXIT
)
echo done!

echo ==TESTING H metaUID: SINGLE CALL
echo ==TESTING H metaUID: SINGLE CALL >> %LOG_FILE% 
python %PY_FILE% --h --debug --file %UID_STRUCTURES_FILE% >> %LOG_FILE% 2>&1
if ERRORLEVEL 1 (
        goto :EXIT
)
echo done!



::echo ==TESTING IMPLEMENT metaUID: WITH NO TEMP UIDs AVAILABLE
::echo ==TESTING IMPLEMENT metaUID: WITH NO TEMP UIDs AVAILABLE >> %LOG_FILE% 
::python %PY_FILE% --implement --debug --file %UID_STRUCTURES_FILE% >> %LOG_FILE% 2>&1
::if ERRORLEVEL 1 (
::        echo CORRECTLY FAULTED
::        echo CORRECTLY FAULTED >> %LOG_FILE% 2>&1
::)
::echo Should have faulted!

echo ==TESTING IMPLEMENT metaUID: CHANGES, TEST H FILE UPDATED AS WELL
echo ==TESTING IMPLEMENT metaUID: CHANGES, TEST H FILE UPDATED AS WELL >> %LOG_FILE% 
python %PY_FILE% --implement --debug --file %UID_STRUCTURES_FILE% >> %LOG_FILE% 2>&1
if ERRORLEVEL 1 (
        goto :EXIT
)
echo done!

goto :RESET

:EXIT
echo ======================
echo ERROR, EXITED. SEE LOG FILE FOR ERRORS
echo ======================
goto :RESET

:RESET
REM Returning to Original Directory
cd test
echo CHECK LOG AND CSV FILE TO MAKE SURE EXPECTED OUTPUT MATCHES
goto :EOF
