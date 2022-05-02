#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
# Purpose       : Validation and Error Functions for dataControlGen suite

import sys, os, re, copy, argparse, shutil, platform, traceback 

##########Global Variables######################
HARDFAIL_FLAG = True
ENFORCEFORMAT_FLAG = False

TELEMETRY_VERSION_1         = "1.0"
TELEMETRY_VERSION_2         = "2.0"
TELEMETRY_LATEST_VERSION    = "2.0"

 # Sequences used in matching. Use precompiled version to accelerate code.
matchSequenceValidation     =  [None] * 12 # Assign size  to the array
matchSequenceValidation[1]  = re.compile("(.+?)='(.+?)'|(?:,)(.+?)='(.+?)'")
matchSequenceValidation[2] = re.compile("[a-zA-Z0-9,\.\_\- ]*\Z")
###########Validation Handling#######################
def validateLength(arg):
    if not ENFORCEFORMAT_FLAG:
        return arg
    try:
        arg = str(arg) #always keep as string
        if len(arg) > 256:
            failString = "Failed Input Length Test. Enforced 256 char maximum: %s"% arg
            throwFormatError(failString)
        return arg #as string
    except Exception as e:
        throwTraceback(e)
    
def validateString(arg):
    if not ENFORCEFORMAT_FLAG:
        return arg
    try:
        arg = validateLength(arg)
        arg = arg.strip() #get rid of leading and trailing spaces
        if matchSequenceValidation[2].match(arg):
            return arg
        else:
            failString = "Failed enforced Alphanumeric, space, and .,_- Chars Test: %s"% arg
            throwFormatError(failString)
    except Exception as e:
        throwTraceback(e)
        
#def validateStringList(string):
    
        
def validateEditString(arg):
    if not ENFORCEFORMAT_FLAG:
        return arg
    try:
        #get rid of parenthesis
        arg = withoutBoundingChars(arg, '(', ')')
            
        if len(arg) != 0:
            filteredEditString = ""
            if matchSequenceValidation[1].match(arg): #find atleast 1
                for keyValue in matchSequenceValidation[1].finditer(arg):
                    key = validateString(keyValue.group(1))
                    value = validateString(keyValue.group(2))
                    filteredEditString += keyValue
                arg = filteredEditString
            else:
                failString = "Failed Enforced editString format Test: (key='stringValue',key ='stringValue'...). SINGLE QUOTES REQUIRED: %s" %arg
                throwFormatError(failString)
        return arg
    except Exception as e:
        throwTraceback(e)
        
def validateVersion(version):
    try:
        version = validateString(version)
        if version in ["1", TELEMETRY_VERSION_1, "ONE"]:
            version = TELEMETRY_VERSION_1
        elif version in ["2", TELEMETRY_VERSION_2, "TWO"]:
            version = TELEMETRY_VERSION_2
        else:
            throwVersionError(version)
        return version
    except Exception as e:
        throwTraceback(e)
        
def withoutBoundingChars(arg, startChar, endChar):
    if arg[0] == startChar:
        arg = arg[1:]
    if arg[-1] == endChar:
        arg = arg[:-1]
    return arg


###########Error Handling#######################
    
def throwTraceback(exception):
    print("ERROR: An exception occurred: {0}".format(exception))
    if HARDFAIL_FLAG:
        traceback.print_exc()
        quit(1)
    
def throwIOError(fileName):
    print("File Attempted Location: %s \nNot Found, Quitting...\n" % fileName)
    if HARDFAIL_FLAG:
        traceback.print_exc()
        quit(2)

def throwVersionError(version):
    print("Encountered unexpected version: %s . Quitting without changes...\n" % version)
    if HARDFAIL_FLAG:
        traceback.print_stack()
        quit (4)

def throwUidError(uidNum):
    print("Tried to perform invalid uid operation on: %s. Quitting without changes...\n" % uidNum)
    if HARDFAIL_FLAG:
        traceback.print_stack()
        quit(5)
    
def throwClassificationError(uidNum):
    print("Encountered unexpected Classification: %s. Quitting without changes...\n" % uidNum)
    if HARDFAIL_FLAG:
        traceback.print_stack()
        quit(6)

def throwFormatError(failString):
    print(failString)
    if ENFORCEFORMAT_FLAG:
        traceback.print_stack()
        quit(7)
