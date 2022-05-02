#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
import sys, os, re, copy, argparse, shutil, platform, traceback

#import wrapper, assumes ssddev directory structure
repoRoot = os.path.join(os.path.realpath(__file__),'..')
repoRoot = os.path.join(os.path.realpath(repoRoot),'..')
repoRoot = os.path.dirname(os.path.realpath(repoRoot))
buildgenToolsDir = os.path.realpath(os.path.join(repoRoot, r'/toolslib/bg3'))
datacontrolDir = os.path.abspath(os.path.join(repoRoot + r'/tools/lib/datacontrol'))
sys.path.append(buildgenToolsDir)
sys.path.append(datacontrolDir)

from dataControlGenMain import dataControlGenWrapper, matchSequence
from validation.dataControlValidation import withoutBoundingChars, validateString, validateEditString, validateVersion 

#local variables
repodir = os.path.dirname(os.path.realpath(__file__))

# @todo: Insert restricted Paths functionality?

def dataControlGen(output=sys.stdout, to_create = None, to_deprecate=None, to_edit=None, implement=False, repodir=None, repoRoot= None, file=None, debug_mode=False, update_h=False, update_dict=False):
  
        
    numberOfErrors = dataControlGenWrapper(output, to_create, to_deprecate, to_edit, implement,  repodir, repoRoot, file, debug=debug_mode, update_h=False)
    
    return numberOfErrors


def main():
    description = 'Datacontrol code management tool to reserve, implement and retire structure uids.\n'\
                  'Documented at https://nsg-wiki.intel.com/display/FW/datacrontrolGen.py\n'
    parser = argparse.ArgumentParser(prog='dataControlGen.py', 
                                     description=description)
    parser.add_argument('--create',                    dest = "to_create"  ,                                default = None,
                                                       metavar = ('<tempUID> (<editString>)'))
    parser.add_argument('--edit',                      dest='to_edit',                                      default=None,
                                                       metavar=('<uidNum> <version> (<editString>)'))
    parser.add_argument('--deprecate',                 dest='to_deprecate',                                 default=None,
                                                       metavar=('<uidNum> <version>'))
    parser.add_argument('--implement',                 action = 'store_true',                               default= False)
    parser.add_argument('--h',                         dest='update_h',         action ='store_true',       default = False) # @todo: change to specify build
    parser.add_argument('--dict',                      dest='update_dict',      action ='store_true',       default = False)
                                                   
    parser.add_argument('--debug',                     action='store_true', dest='debug',              default=False)
    parser.add_argument('--file',                      dest= 'structuresFile',                              default= None,    help = "Use to specify structures_meta, NAME ONLY. Should be in same directory.")
    args = parser.parse_args()
        

    to_deprecate = None
    to_edit = None
    to_create = None
    if args.to_create:
        to_create = []
        print("<temp-uid>,<structName>,<dataArea>,<dataGroup>,<product>,(<editString>)\n")
        # get rid of brackets
        args.to_create = withoutBoundingChars(args.to_create, "[", "]")
            
        for uidInfo in args.to_create.split(';'): #separate into uids
            print(uidInfo)
            if matchSequence[6].match(uidInfo):
                m = matchSequence[6].match(uidInfo)
                tempUid     = validateString(m.group(1))
                structName  = validateString(m.group(2))
                dataArea    = validateString(m.group(3))
                dataGroup   = validateString(m.group(4))
                product     = validateString(m.group(5))
                editString  = validateEditString(m.group(6))
                argList     = [tempUid, structName, dataArea, dataGroup, product, editString]
                if args.debug: 
                    print("tempUid: ", tempUid, ",structName: ", structName, ",dataArea: ", dataArea, ",dataGroup: ", ",product: ", product, ",editString: ", editString)
                to_create.append(tuple(a for a in argList)) #store in tuple
            else:
                print ("Create takes six (6) arguments, please specify '--create [<temp-uid>,<structName>,<dataArea>,<dataGroup>,<product>,(<editString>)]'.\n NO SPACES. Multiple instances: separated by ';'.")
                quit(0)
    if args.to_deprecate:
        to_deprecate = []
        print("<uidNum> <version>\n")
        args.to_deprecate = withoutBoundingChars(args.to_deprecate, "[", "]")
        for uidInfo in args.to_deprecate.split(';'): #separate into uids
            print(uidInfo)
            uidInfo = uidInfo.split(',') #separate info
            uidNum = validateString(uidInfo[0])
            version = validateVersion(uidInfo[1])
            if len(uidInfo) != 2:
                print ("Deprecate takes two (2) arguments, please specify '--deprecate [<uidNum><version>]'.\n NO SPACES. Multiple instances: separated by ';'.")
                quit(0)
            to_deprecate.append(tuple(a for a in uidInfo)) #store in tuple
    if args.to_edit:
        to_create = []
        print("<temp-uid>,<version>,(<editString>)\n")
        # get rid of brackets
        args.to_edit = withoutBoundingChars(args.to_edit, "[", "]")
            
        for uidInfo in args.to_edit.split(';'): #separate into uids
            print(uidInfo)
            if matchSequence[6].match(uidInfo):
                m = matchSequence[6].match(uidInfo)
                uidNum     = validateString(m.group(1))
                version     = validateVersion(m.group(2))
                editString  = validateEditString(m.group(3))
                argList     = [tempUid, version, editString]
                if args.debug: 
                    print("uidNum: ", uidNum, ",version: ", version, ",editString: ", editString)
                to_edit.append(tuple(a for a in argList)) # store in tuple
            else:
                print ("Create takes three (3) arguments, please specify '--create [<temp-uid>,<version>,(<editString>)]'.\n NO SPACES. Multiple instances: separated by ';'.")
                quit(0)

    #repoRoot init

    numberOfErrors = dataControlGenWrapper(to_create= to_create, to_deprecate= to_deprecate, to_edit=to_edit, implement= args.implement, repodir= repodir, repoRoot= repoRoot, file= args.structuresFile, debug= args.debug, update_h= args.update_h, update_dict = args.update_dict)

    if numberOfErrors > 0:
        sys.stdout.write(str(numberOfErrors) + " error(s) found, see output\n")
    else:
        sys.stdout.write(str(numberOfErrors) + " error(s) found\n")




if __name__ == '__main__':
    main()
