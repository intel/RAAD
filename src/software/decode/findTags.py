#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
# Human made config search to generate.
##############################################
import os, re, sys, pyparsing, dataclasses, pprint
import software.decode.baseTags as baseTags
import software.decode.autoParser_v3 as autoParser_v3
##############################################
# .exe extension patch for the compiled version of this script
##############################################
if not re.search('\.PY$|\.PYC$|\.EXE$', os.path.split(sys.argv[0])[1].upper()):  # @todo Ignore.
    sys.argv[0] = os.path.join(os.path.split(sys.argv[0])[0] , os.path.split(sys.argv[0])[1]+'.exe')
##############################################
# Python version info.
##############################################
print(" ")
if (sys.version_info > (3, 0)):
    # Python 3 code in this block
    print("Welcome to the future, Python 3 and beyond!.")
else:
    # Python 2 code in this block
    print("You shall not pass!")
    print(" Python 2 no longer has security updates so stop using it.")
    print(" Try the automated 2to3 converter. https://docs.python.org/2/library/2to3.html")
    print(" I.E. 2to3 -w example.py")
    quit(2)

class autoParseList(object):
    class structureItem(object):
        def __init__(self, structureElement=None):
            if structureElement is None:
                self.structureElement = None
                self.label = None
                self.fillCount = None
            else:
                self._setAll(structureElement=structureElement)
            return

        def _setAll(self, structureElement=None):
            if structureElement is not None:
                self.structureList = structureElement
                self.label = structureElement[0]
                fillCount = 0
                for index_Row, item_Row in enumerate(structureElement):
                    if item_Row is not None:
                        fillCount += 1
                self.fillCount = fillCount
            return

        def setAll(self, structureElement=None):
            self.setAll(structureElement=structureElement)
            return

        def getFillCount(self):
            return self.fillCount

        def getLabel(self):
            return self.label

        def getStructureElement(self):
            return self.structureElement

    def __init__(self, structureListOfLists=None, debug=False):
        self.structureListOfLists = structureListOfLists
        self.simpleList = None
        self.debug = debug
        if structureListOfLists is not None:
            self.simpleList = self.getProcessedList(autoParserDataObjectList=structureListOfLists)

    def getProcessedList(self, autoParserDataObjectList=None):
        """

        Args:
            autoParserDataObjectList (list):
        """
        if autoParserDataObjectList is None:
            return None

        # Sort by unique name, type name, then pack value max to min. We want these in alphabetical order and highest number first
        sortedObjectList = sorted(autoParserDataObjectList, key=lambda x: (x[0].lower(), x[1].lower(), x[4], x[2], x[3], x[5].lower(), x[6].lower(), x[7], x[8]))

        if self.debug:
            pprint.pprint(sortedObjectList)

        # Prepare to remove duplicate entries. We want to keep the sets of {unque name per, unique type, with maximum pack value}
        objList = []
        previousName = ''
        previousType = ''
        for indexArray, rowSet in enumerate(sortedObjectList):
            if rowSet[0] != previousName and rowSet[1] != previousType:  # Do not add seen values.
                objC = self.structureItem()
                objC.setAll(structureElement=rowSet)
                objList.append(objC)
                previousName = rowSet[0]
                previousType = rowSet[1]
            elif rowSet[0] == previousName and rowSet[1] != previousType:  # Do not add seen values.
                objC = self.structureItem()
                objC.setAll(structureElement=rowSet)
                objList.append(objC)
                previousName = rowSet[0]
                previousType = rowSet[1]

        # Sort list by total filled sets.
        objList = sorted(objList, key=lambda x: (x.getLabel().lower(), x.getFillCount()), reverse=True)
        if self.debug:
            pprint.pprint(objList)

        # Recreate simple input list
        simpleList = []
        for indexArray, rowSet in enumerate(objList):
            simpleList.append(rowSet.getStructureElement())
        if self.debug:
            pprint.pprint(simpleList)

        return simpleList


class autoParseObject(object):
    try:
        autoObjects = baseTags.AUTOPARSER_DATA_OBJECT_LIST
    except ImportError:
        print("Error with: AUTOPARSER_DATA_OBJECT_LIST")
    itemOfInterestIndex = None
    itemOfInterestLoaded = False
    simularityScore = 0.0
    simularityScoreList = []

    @dataclasses.dataclass
    class sortFrameFields(object):
        def __init__(self, field_sScore=None, field_Index=None, field_instanceName=None, field_typedef=None,
                     field_vMajor_macro=None, field_vMinor_macro=None, field_pack=None, field_vMajorName=None,
                     field_vMinorName=None, field_RNLBA=None, field_WNLBA=None):
            self.field_sScore = field_sScore
            self.field_Index = field_Index
            self.field_instanceName = field_instanceName
            self.field_typedef = field_typedef
            self.field_vMajor_macro = field_vMajor_macro
            self.field_vMinor_macro = field_vMinor_macro
            self.field_pack = field_pack
            self.field_vMajorName = field_vMajorName
            self.field_vMinorName = field_vMinorName
            self.field_RNLBA = field_RNLBA
            self.field_WNLBA = field_WNLBA

    def __init__(self, itemOfInterest=None):
        self.field_instanceName = None
        self.field_typedef = None
        self.field_vMajor_macro =  None
        self.field_vMinor_macro = None
        self.field_pack = None
        self.field_vMajorName = None
        self.field_vMinorName = None
        self.field_RNLBA = None
        self.field_WNLBA = None
        if isinstance(itemOfInterest, str):
            self._loadItem(itemOfInterest=itemOfInterest)

    def getItemList(self):
        return (self.field_instanceName, self.field_typedef, self.field_vMajor_macro, self.field_vMinor_macro, self.field_pack, self.field_vMajorName, self.field_vMinorName, self.field_RNLBA, self.field_WNLBA)

    def isItemLoaded(self):
        return self.itemOfInterestLoaded

    def findSimilar(self, itemOfInterest=None, mode=1, scoreThreshold=0.95):
        # Mode 1: Use field_instanceName
        # Mode 2: Use field_typedef
        itemBase = itemOfInterest
        itemLower = itemBase.lower()
        itemUpper = itemBase.upper()
        itemFound = False
        simularList = []
        for field_Index, field_row in enumerate(self.autoObjects):
            field_instanceName, field_typedef, field_vMajor_macro, field_vMinor_macro, field_pack, field_vMajorName, field_vMinorName, field_RNLBA, field_WNLBA = field_row
            if mode is 1:
                selectedSearchItem = field_instanceName
            elif (mode is 2):  # @todo should be 80% or above
                selectedSearchItem = field_typedef
            elif (mode is 3):  # @todo
                selectedSearchItem = field_instanceName
            else:  # @todo should be 80% or above
                selectedSearchItem = field_typedef
            # Debug code for known usage case.
            # if selectedSearchItem.lower() == 'defraghistory' and itemLower == 'defraghistory':
            #    print("STOP")
            sMatchBase, sScoreBase = self.isSimilar(field_instanceName=selectedSearchItem, itemOfInterest=itemBase, scoreThreshold=scoreThreshold)
            sMatchLower, sScoreLower = self.isSimilar(field_instanceName=selectedSearchItem, itemOfInterest=itemLower, scoreThreshold=scoreThreshold)
            sMatchUpper, sScoreUpper = self.isSimilar(field_instanceName=selectedSearchItem, itemOfInterest=itemUpper, scoreThreshold=scoreThreshold)
            if sMatchBase:
                itemFound = True
                baseObj = self.sortFrameFields(field_sScore=sScoreBase, field_Index=field_Index,
                                               field_instanceName=field_instanceName, field_typedef=field_typedef,
                                               field_vMajor_macro=field_vMajor_macro, field_vMinor_macro=field_vMinor_macro,
                                               field_pack=field_pack,
                                               field_vMajorName=field_vMajorName, field_vMinorName=field_vMinorName,
                                               field_RNLBA=field_RNLBA, field_WNLBA=field_WNLBA)
                simularList.append(baseObj)
            if sMatchLower:
                itemFound = True
                baseObj = self.sortFrameFields(field_sScore=sScoreLower, field_Index=field_Index,
                                               field_instanceName=field_instanceName, field_typedef=field_typedef,
                                               field_vMajor_macro=field_vMajor_macro, field_vMinor_macro=field_vMinor_macro,
                                               field_pack=field_pack,
                                               field_vMajorName=field_vMajorName, field_vMinorName=field_vMinorName,
                                               field_RNLBA=field_RNLBA, field_WNLBA=field_WNLBA)
                simularList.append(baseObj)
            if sMatchUpper:
                itemFound = True
                baseObj = self.sortFrameFields(field_sScore=sScoreUpper, field_Index=field_Index,
                                               field_instanceName=field_instanceName, field_typedef=field_typedef,
                                               field_vMajor_macro=field_vMajor_macro, field_vMinor_macro=field_vMinor_macro,
                                               field_pack=field_pack,
                                               field_vMajorName=field_vMajorName, field_vMinorName=field_vMinorName,
                                               field_RNLBA=field_RNLBA, field_WNLBA=field_WNLBA)
                simularList.append(baseObj)
        if itemFound is True:
            simularList.sort(key=lambda sList: sList.field_sScore, reverse=True)  # Decending order according to simularity score.
            self._setItem(field_instanceName=simularList[0].field_instanceName, field_typedef=simularList[0].field_typedef,
                     field_vMajor_macro=simularList[0].field_vMajor_macro, field_vMinor_macro=simularList[0].field_vMinor_macro,
                     field_pack=simularList[0].field_pack,
                     field_vMajorName=simularList[0].field_vMajorName, field_vMinorName=simularList[0].field_vMinorName,
                     field_RNLBA=simularList[0].field_RNLBA, field_WNLBA=simularList[0].field_WNLBA)
            self.itemOfInterestIndex = simularList[0].field_Index
            self.itemOfInterestLoaded = True
        return itemFound

    def getSScore(self):
        return self.simularityScore

    def getSScoreList(self):
        return self.simularityScoreList

    def _getSimularityScore(self, field_instanceName='', itemOfInterest=''):
        import difflib
        if (isinstance(field_instanceName, str) is False) or ((isinstance(itemOfInterest, str) is False)):
            simularityScore = 0.0
        else:
            simularityScore = difflib.SequenceMatcher(None, field_instanceName, itemOfInterest).ratio()
        self.simularityScoreList.append([field_instanceName, itemOfInterest, simularityScore])
        return simularityScore

    def isSimilar(self, field_instanceName='', itemOfInterest='', scoreThreshold=0.95):
        if (0.0 >= scoreThreshold <= 1.0):
            matchFound = False
            simularityScore = 0.0
        else:
            simularityScore = self._getSimularityScore(field_instanceName=field_instanceName, itemOfInterest=itemOfInterest)
            if simularityScore >= scoreThreshold:
                matchFound = True
            else:
                matchFound = False
        return (matchFound, simularityScore)

    def getPragmaPack(self):
        if self.field_pack is not None:
            return self.field_pack
        else:
            return 4  # Default pack for compilation.

    def _loadItem(self, itemOfInterest=None):
        baseItem = itemOfInterest
        lowerItem = baseItem.lower()
        upperItem = baseItem.upper()
        itemFound = False
        itemIndex = 0
        for field_Index, field_row in enumerate(self.autoObjects):
            field_instanceName, field_typedef, field_vMajor_macro, field_vMinor_macro, field_pack, field_vMajorName, field_vMinorName, field_RNLBA, field_WNLBA = field_row
            if field_instanceName is baseItem:
                itemFound = True
                itemIndex = field_Index
            elif field_instanceName is lowerItem:
                itemFound = True
                itemIndex = field_Index
            elif field_instanceName is upperItem:
                itemFound = True
                itemIndex = field_Index

            if itemFound is True:
                self._setItem(field_instanceName=field_instanceName, field_typedef=field_typedef, field_vMajor_macro=field_vMajor_macro, field_vMinor_macro=field_vMinor_macro, field_pack=field_pack, field_vMajorName=field_vMajorName, field_vMinorName=field_vMinorName, field_RNLBA=field_RNLBA, field_WNLBA=field_WNLBA)
                self.itemOfInterestIndex = itemIndex
                self.itemOfInterestLoaded = True
                return
        return (self.itemOfInterestLoaded, self.itemOfInterestIndex)

    def _setItem(self, field_instanceName=None, field_typedef=None, field_vMajor_macro=None, field_vMinor_macro=None, field_pack=None, field_vMajorName=None, field_vMinorName=None, field_RNLBA=None, field_WNLBA=None):
        setCount = 0
        allCount = 0

        allCount = allCount + 1
        if field_instanceName is not None:
            self.field_instanceName = field_instanceName
            setCount = setCount + 1

        allCount = allCount + 1
        if field_typedef is not None:
            self.field_typedef = field_typedef
            setCount = setCount + 1

        allCount = allCount + 1
        if field_vMajor_macro is not None:
            self.field_vMajor_macro = field_vMajor_macro
            setCount = setCount + 1
        allCount = allCount + 1
        if field_vMinor_macro is not None:
            self.field_vMinor_macro = field_vMinor_macro
            setCount = setCount + 1

        allCount = allCount + 1
        if field_pack is not None:
            self.field_pack = field_pack
            setCount = setCount + 1

        allCount = allCount + 1
        if field_vMajorName is not None:
            self.field_vMajorName = field_vMajorName
            setCount = setCount + 1

        allCount = allCount + 1
        if field_vMinorName is not None:
            self.field_vMinorName = field_vMinorName
            setCount = setCount + 1

        allCount = allCount + 1
        if field_RNLBA is not None:
            self.field_RNLBA = field_RNLBA
            setCount = setCount + 1

        allCount = allCount + 1
        if field_WNLBA is not None:
            self.field_WNLBA = field_WNLBA
            setCount = setCount + 1

        setAllItems = (setCount == allCount)
        return (setAllItems, setCount)

#####################################################################
class uniqueIdentifierTypes_e(object):
    try:
        eUniqueIdentifier_t = baseTags.eUniqueIdentifier_t
        eUniqueIdentifier_t_lower = dict((str(k).lower(), v.lower()) for k, v in eUniqueIdentifier_t.items())
        reverse_eUniqueIdentifier_t = {v: k for k, v in eUniqueIdentifier_t.items()}
        reverse_eUniqueIdentifier_t_lower = dict((k.lower(), str(v).lower()) for k, v in reverse_eUniqueIdentifier_t.items())
    except ImportError:
        print("Error with: eUniqueIdentifier_t")

    eUID_prefix = "uid_"
    eUID_suffix = "_e"

    def __init__(self):
        self.name = None
        self.uid = None
        self.shortName = None
        self.fileTupple = None

    def getForwardDictionary(self):
        return self.eUniqueIdentifier_t

    def getReverseDictionary(self):
        return self.reverse_eUniqueIdentifier_t

    @staticmethod
    def _strip_end(stringInput='', suffix=''):
        try:
            partitionedString = stringInput.removesuffix(suffix)
        except:
            if not stringInput.endswith(suffix):
                partitionedString = stringInput
            else:
                partitionedString = stringInput[:len(stringInput) - len(suffix)]
        return partitionedString

    @staticmethod
    def _strip_start(stringInput='', prefix=''):
        try:
            partitionedString = stringInput.removeprefix(prefix)
        except:
            if not stringInput.startswith(prefix):
                partitionedString = stringInput
            else:
                partitionedString = stringInput[len(prefix):len(stringInput)]
        return partitionedString

    def _strip_StartEnd(self, stringInput='', prefix='', suffix=''):
        cleanedStr = stringInput
        cleanedStr = self._strip_start(stringInput=cleanedStr, prefix=prefix)
        cleanedStr = self._strip_end(stringInput=cleanedStr, suffix=suffix)
        return cleanedStr

    def getAll(self, shortName=None):
        if shortName is not None:
            self.getKeyShort(otype=shortName)
        else:
            # Return last index of value and key from dictionaries
            return ((list(self.reverse_eUniqueIdentifier_t.keys())[-1]), (list(self.eUniqueIdentifier_t.keys())[-1]))

    def _checkInput(self, otype=None):
        if otype is None:
            return (list(self.eUniqueIdentifier_t.keys())[-1])

    def getUnknownKey(self):
        return (list(self.reverse_eUniqueIdentifier_t.keys())[-1])

    def getUnknownValue(self):
        return (list(self.eUniqueIdentifier_t.keys())[-1])

    def getKey(self, otype=None):
        if otype is None:
            return (list(self.reverse_eUniqueIdentifier_t.keys())[-1])
        elif isinstance(otype, int) and otype in self.reverse_eUniqueIdentifier_t:
            return self.reverse_eUniqueIdentifier_t[otype]
        else:
            return (list(self.reverse_eUniqueIdentifier_t.keys())[-1])

    def getKeyShort(self, otype=None):
        theKey = self.getKey(otype=otype)
        if theKey is not None:
            # Remove prefix and suffix from key.
            theKey = self._strip_StartEnd(stringInput=theKey, prefix=self.eUID_prefix, suffix=self.eUID_suffix)
        return theKey

    def getValueShort(self, otype=None):
        otype_mod = None
        if otype in self.eUniqueIdentifier_t:
            otype_mod = "uid_{}_e".format(self.eUID_prefix, otype, self.eUID_suffix)
        elif otype not in self.eUniqueIdentifier_t:
            lowerReverse_eUID_t = dict((k.lower, v.lower()) for k, v in self.eUniqueIdentifier_t.items())
            if otype in lowerReverse_eUID_t:
                otype_mod_lower = "uid_{}_e".format(self.eUID_prefix, otype, self.eUID_suffix)
            else:
                otype_mod_lower = None
            otype_mod = otype_mod_lower
        return otype_mod

    def getValue(self, otype=None):
        foundValue = None
        if otype is None:
            foundValue = (list(self.eUniqueIdentifier_t.keys())[-1])
        elif (isinstance(otype, str)) and (otype in self.eUniqueIdentifier_t):
            foundValue = self.eUniqueIdentifier_t[otype]
        else:
            foundValue = (list(self.eUniqueIdentifier_t.keys())[-1])
        return foundValue

    def getKeyOrValue(self, otype=None):
        """
        unique identifier lookup function
        Args:
            otype: str, int

        Returns: if is int then return string; otherwise, if the type is string return int

        """
        foundValue = None
        if otype is None:
            foundValue = (list(self.eUniqueIdentifier_t.keys())[-1])
        elif isinstance(otype, int) and otype in self.eUniqueIdentifier_t:
            foundValue = self.eUniqueIdentifier_t[otype]
        elif isinstance(otype, str) and otype in self.reverse_eUniqueIdentifier_t:
            foundValue = self.reverse_eUniqueIdentifier_t[otype]
        else:
            foundValue = (list(self.eUniqueIdentifier_t.keys())[-1])
        return foundValue

    def parseFileName(self, fileNameInput='4294967294-unknownUniqueIdentifier_0_0.py'):
        if isinstance(fileNameInput, str):
            fieldCount = 1
            uid = ''
            uid_name = ''
            major = ''
            minor = ''
            for index, letter in enumerate(fileNameInput, 0):
                if letter.isdigit() and fieldCount is 1:  # First Field, uid
                    uid = "{}{}".format(uid, letter)
                    fieldCount = 1
                elif letter is '-':  # Dash not a field and starts field 2.
                    fieldCount = 2
                elif ((letter is '_') or (letter.isalpha() is True)) and fieldCount is 2:  # Second Field, uid name
                    uid_name = "{}{}".format(uid_name, letter)
                elif letter.isdigit() and fieldCount is 2:  # Third field, major
                    major = "{}{}".format(major, letter)
                    fieldCount = 3
                elif letter.isdigit() and fieldCount is 3:  # Third field, major
                    major = "{}{}".format(major, letter)
                    fieldCount = 3
                elif (letter is '_') and fieldCount is 3:  # Underscore before field to minor
                    fieldCount = 4
                elif letter.isdigit() and fieldCount is 4:  # Third field, minor
                    minor = "{}{}".format(minor, letter)
                elif letter is '.' and fieldCount is 4:  # We only have '.py' left unless something is wrong.
                    fieldCount = 5
                elif letter.isalpha() and fieldCount >= 5:  # We only have 'py' left unless something is wrong.
                    fieldCount = fieldCount + 1
            foundTupple = (uid, uid_name, major, minor)
        else:
            foundTupple = ("4294967294", "unknownUniqueIdentifier", "0", "0")
        self.fileTupple = foundTupple
        return foundTupple

    def getUIDSimularitySearch(self, searchName=None, sScoreThreshold=0.95, debug=False):
        itemFound = None
        sSCore = 0.0
        if searchName is not None:
            # dict = {field_instanceName: field_UID)}
            import difflib
            # @todo otherOptions: max_search = max(self.eUniqueIdentifier_t.items(), key=lambda i: difflib.SequenceMatcher(None, i.key(), searchName).ratio())
            searchNameLower = str(searchName).lower()
            foundTuppleList = []
            for dKey, dValue in self.reverse_eUniqueIdentifier_t.items():
                dKeyClean = str(dKey)
                dKeyClean = self._strip_StartEnd(stringInput=dKeyClean, prefix=self.eUID_prefix, suffix=self.eUID_suffix)
                sScoreDefault = difflib.SequenceMatcher(None, dKeyClean, searchName).ratio()

                dKeyLowerClean = str(dKey).lower()
                dKeyLowerClean = self._strip_StartEnd(stringInput=dKeyLowerClean, prefix=self.eUID_prefix, suffix=self.eUID_suffix)
                sScoreLower = difflib.SequenceMatcher(None, dKeyLowerClean, searchName).ratio()

                if sScoreDefault >= sScoreThreshold:
                    tuppleItem = [sScoreDefault, dKey, dValue]
                    foundTuppleList.append(tuppleItem)
                elif sScoreLower >= sScoreThreshold:
                    tuppleItem = [sScoreLower, dKey, dValue]
                    foundTuppleList.append(tuppleItem)
                else:
                    tuppleItem = None
                if debug:
                    print("Found Tupple:")
                    pprint.pprint(tuppleItem)
            if len(foundTuppleList) > 0:
                foundTuppleList_Sorted = sorted(foundTuppleList, key=lambda x: (x[0]))
                itemFound = foundTuppleList_Sorted[0][2]
                sScore = foundTuppleList_Sorted[0][0]
            else:
                itemFound = (list(self.eUniqueIdentifier_t.keys())[-1])
                sScore = 0.0
        else:
            itemFound = (list(self.eUniqueIdentifier_t.keys())[-1])
            sScore = 0.0
        return itemFound, sScore

##############################################
# Class based on the layout of autoParser expectations.
##############################################
class dataStructureItem(object):
    def __init__(self,
                eUIDName=None,
                instanceName=None,
                typeDef=None,
                majorMacro=None,
                minorMacro=None,
                packMode=None,
                versionMajorName=None,
                versionMinorName=None,
                RNLBA=None,
                WNLBA=None,
                uid=None,
                debug=False):

        # Instance Name
        self.instanceName = instanceName
        if instanceName is not None:
            self.eUIDName = "uid_{}_e".format(instanceName)
        else:
            self.eUIDName = None
        # Typedef
        self.typeDef = typeDef
        # VERSION MAJOR macro
        self.majorMacro = majorMacro
        # VERSION MINOR macro
        self.minorMacro = minorMacro
        # Pack
        self.packMode = packMode
        # versionMajorName
        self.versionMajorName = versionMajorName
        # versionMinorName
        self.versionMinorName = versionMinorName
        # RNLBA
        self.RNLBA = RNLBA
        # WNLBA
        self.WNLBA = WNLBA
        # unique identifier value
        self.uid = uid
        self.uidSScore = 0.0
        # debug info
        self.debug = debug

    def __eq__(self, other):
        if self.get_all() == other.get_all():
            return True
        return False

    def __lt__(self, other):
        if self.get_verify() < other.get_verify():
            return True
        return False

    def __gt__(self, other):
        if self.get_verify() > other.get_verify():
            return True
        return False

    def get_all(self):
        return (self.instanceName, self.typeDef, self.majorMacro, self.minorMacro, self.packMode, self.versionMajorName, self.versionMinorName, self.RNLBA, self.WNLBA)

    def get_all_min(self):
        return (self.instanceName, self.typeDef, None, None, self.packMode, None, None, None, None)

    def get_all_extra(self):
        return (self.instanceName, self.typeDef, self.majorMacro, self.minorMacro, self.packMode, self.versionMajorName, self.versionMinorName, self.RNLBA, self.WNLBA, self.uid)

    def set_all(self,
                instanceName=None,
                typeDef=None,
                majorMacro=None,
                minorMacro=None,
                packMode=None,
                versionMajorName=None,
                versionMinorName=None,
                RNLBA=None,
                WNLBA=None,
                uid=None):
        changeCount = 0

        if (instanceName is not None):
            self.instanceName = instanceName
            self.eUIDName = "uid_{}_e".format(instanceName)
            changeCount += 1
        if (typeDef is not None):
            self.typeDef = typeDef
            changeCount += 1
        if (majorMacro is not None):
            self.majorMacro = majorMacro
            changeCount += 1
        if (minorMacro is not None):
            self.minorMacro = minorMacro
            changeCount += 1
        if (packMode is not None):
            self.packMode = packMode
            changeCount += 1
        if (versionMajorName is not None):
            self.versionMajorName = versionMajorName
            changeCount += 1
        if (versionMinorName is not None):
            self.versionMinorName = versionMinorName
            changeCount += 1
        if (RNLBA is not None):
            self.RNLBA = RNLBA
            changeCount += 1
        if (WNLBA is not None):
            self.WNLBA = WNLBA
            changeCount += 1
        if (uid is not None):
            self.uid = uid
            changeCount += 1
        return changeCount

    def get_uidSScore(self):
        return self.uidSScore

    def tryFillEmpty(self, sScoreThreshold=0.95):
        changeCount = 0
        if (self.uid is None):
            searchUID  = uniqueIdentifierTypes_e()
            uidFound, self.uidSScore = searchUID.getUIDSimularitySearch(searchName=self.instanceName, sScoreThreshold=sScoreThreshold, debug=self.debug)
            if uidFound == searchUID.getUnknownValue():
                if self.debug:
                    print("ERROR...UID needs to be populated get_verify() for name={} type={}".format(self.instanceName, self.typeDef))
            else:
                if self.debug:
                    print("# UID found {} Simularity Score: {}".format(uidFound, self.uidSScore))
                self.set_uid(uidFound)
        else:
            self.uidSScore = 2.0

        if (self.packMode is None):
            parseObj = autoParseObject(self.instanceName)
            if parseObj.isItemLoaded():
                changeCount += 1
                if self.debug:
                    print("= Found exact pragma pack:")
                    print("  Name={} Type={} Version={}.{} PragmaPack={}".format(self.instanceName, self.typeDef, self.majorMacro,
                                                                  self.minorMacro, parseObj.getPragmaPack()))
                self.packMode = parseObj.getPragmaPack()
            else:
                if parseObj.findSimilar(itemOfInterest=self.instanceName, mode=1, scoreThreshold=sScoreThreshold) is True:
                    changeCount += 1
                    if self.debug:
                        print("~ Found similar pragma pack:")
                        print("  Name={} Type={} Version={}.{} PragmaPack={}".format(self.instanceName, self.typeDef,
                                                                                    self.majorMacro,
                                                                                    self.minorMacro,
                                                                                    parseObj.getPragmaPack()))
                    self.packMode = parseObj.getPragmaPack()
                else:
                    if parseObj.findSimilar(itemOfInterest=self.typeDef, mode=2, scoreThreshold=sScoreThreshold) is True:
                        changeCount += 1
                        if self.debug:
                            print("* Found similar pragma pack:")
                            print("  Name={} Type={} Version={}.{} PragmaPack={}".format(self.instanceName, self.typeDef,
                                                                                        self.majorMacro,
                                                                                        self.minorMacro,
                                                                                        parseObj.getPragmaPack()))
                        self.packMode = parseObj.getPragmaPack()
                    else:
                        if self.debug:
                            # @todo Add the UID value.
                            print("!! Error in trying to find pragma pack:")
                            print(" Name={} Type={} Version {}.{} SimularityScore={}".format(self.instanceName, self.typeDef, self.majorMacro, self.minorMacro, parseObj.getSScore()))
                        # print out the simularity score lists.
                        # if self.debug:
                        #    import pprint
                        #    pprint.pprint(parseObj.getSScoreList())
        return changeCount

    def get_verify(self):
        changeCount = 0
        requiredCount = 0
        totalItemsCorrect = False

        if (self.instanceName is not None):
            changeCount += 1
            requiredCount += 1
        if (self.typeDef is not None):
            changeCount += 1
            requiredCount += 1
        if (self.packMode is not None):
            changeCount += 1
            requiredCount += 1
        if (self.majorMacro is not None):
            changeCount += 1
        if (self.minorMacro is not None):
            changeCount += 1
        if (self.uid is not None):
            changeCount += 1
        """
        if (self.versionMajorName is not None):
            changeCount += 1
        if (self.versionMinorName is not None):
            changeCount += 1
        if (self.RNLBA is not None):
            changeCount += 1
        if (self.WNLBA is not None):
            changeCount += 1
        """
        # Verification Count
        if ((requiredCount >= 3) and (changeCount >= 5)):
            totalItemsCorrect = True
        return totalItemsCorrect

    def get_instanceNameFull(self):
        return "uid_{}_name_{}".format(self.uid, self.instanceName)

    def get_instanceName(self):
        return self.instanceName

    def get_uid(self):
        return self.uid

    def set_eUID(self, eUIDName=None):
        changeCount = 0
        if (eUIDName is not None):
            self.eUIDName = eUIDName
            changeCount += 1
        return changeCount

    def set_instanceName(self, instanceName=None):
        changeCount = 0
        if (instanceName is not None):
            self.instanceName = instanceName
            self.eUIDName = "uid_{}_e".format(self.instanceName)
            searchUID = uniqueIdentifierTypes_e()
            uidValue = searchUID.getKeyOrValue(otype=self.eUIDName)
            if (uidValue != searchUID.getUnknownValue()) and (uidValue != searchUID.getUnknownKey()):
                self.uid = uidValue
                self.uidSScore = 1.0
            else:
                self.uid = None
                self.uidSScore = 0.0
            changeCount += 1
        return changeCount

    def set_typeDef(self, typeDef=None):
        changeCount = 0
        if (typeDef is not None):
            self.typeDef = typeDef
            changeCount += 1
        return changeCount

    def set_majorMacro(self, majorMacro=None):
        changeCount = 0
        if (majorMacro is not None):
            self.majorMacro = majorMacro
            changeCount += 1
        return changeCount

    def set_minorMacro(self, minorMacro=None):
        changeCount = 0
        if (minorMacro is not None):
            self.minorMacro = minorMacro
            changeCount += 1
        return changeCount

    def set_uid(self, uid=None):
        changeCount = 0
        if (uid is not None):
            self.uid = uid
            changeCount += 1
        return changeCount

class dataStructureList(object):
    def __init__(self, dataSList=None, debug=False):
        if dataSList is not None:
            self.dataSList = dataSList
        else:
            self.dataSList = None
        self.debug = debug
        return

    def getProcessedList(self, autoParserDataObjectList: list = None, mode=1):
        """

        Args:
            autoParserDataObjectList (dataStructureItem(list)):
        """
        if autoParserDataObjectList is None:
            return None

        sortedObjectList = self.getSortedList(autoParserDataObjectList, mode=mode)

        # Prepare to remove duplicate entries. We want to keep the sets of {unque name per, unique type, with maximum pack value}
        objList = []
        previousName = ''
        previousType = ''
        for indexArray, rowSet in enumerate(sortedObjectList):
            if rowSet.instanceName != previousName and rowSet.typeDef != previousType:  # Do not add seen values.
                objList.append(rowSet)
                previousName = rowSet.instanceName
                previousType = rowSet.typeDef
            elif rowSet.instanceName == previousName and rowSet.typeDef != previousType:  # Do not add seen values.
                objList.append(rowSet)
                previousName = rowSet.instanceName
                previousType = rowSet.typeDef
        # Sort list by total filled sets.
        # objList = sorted(objList, key=lambda x: (x.instanceName , x.typeDef), reverse=True)
        # if self.debug:
        #    pprint.pprint(objList)

        return objList

    @staticmethod
    def _getDuplicatesWithCount(listOfClassItems=[]):
        # Get frequency count of duplicate elements in the given list
        dictOfElems = dict()
        # Iterate over each element in list
        for elem in listOfClassItems:
            currentUID = elem.uid
            # If element exists in dict then increment its value else add it in dict
            if currentUID in dictOfElems:
                dictOfElems[currentUID] += 1
            else:
                dictOfElems[currentUID] = 1

        # Filter key-value pairs in dictionary. Keep pairs whose value is greater than 1 i.e. only duplicate elements from list.
        duplicateElements = {}
        duplicatesExist = False
        for key, value in dictOfElems.items():
            if key is not None and value > 1:
                duplicateElements[key] = value
                duplicatesExist = True

        # Returns a dict of duplicate elements and their frequency count, and if duplciates exist.
        return duplicateElements, duplicatesExist

    def getOneUIDList(self, autoParserDataObjectList: list = None):
        """

        Args:
            autoParserDataObjectList (dataStructureItem(list)):
        """
        if autoParserDataObjectList is None:
            return None

        class reversor:
            def __init__(self, obj):
                self.obj = obj

            def __eq__(self, other):
                return other.obj == self.obj

            def __lt__(self, other):
                return other.obj < self.obj

        sortedObjectList = autoParserDataObjectList
        duplicatesExist = True
        loopCount = 0
        searchList = sortedObjectList
        while(duplicatesExist is True and loopCount < 8):
            sortedObjectList = self.getProcessedList(autoParserDataObjectList=sortedObjectList, mode=2)
            sortedObjectList = sorted(sortedObjectList, key=lambda x: (4294967295 if x.uid is None else x.uid, reversor(x.uidSScore), x.instanceName.lower(), x.typeDef.lower(), x.packMode))
            duplicatesList, duplicatesExist = self._getDuplicatesWithCount(listOfClassItems=sortedObjectList)
            # Prepare to remove duplicate entries. We want to keep the sets of {unque name per, unique type, with maximum pack value}
            objList = []
            previousUID = None
            previous_uidSScore = 0.0
            for indexArray, rowSet in enumerate(searchList):
                # if (rowSet.uid != previousUID and self.debug):
                #     print("Previous Current")
                #     print("UID  :  {} ~ {}".format(previousUID, rowSet.uid))
                #     print("Score:  {} ~ {}".format(previous_uidSScore, rowSet.uidSScore))
                if (rowSet.uid is None) and (previousUID is None):
                    objList.append(rowSet)
                elif (rowSet.uid is None):
                    objList.append(rowSet)
                elif isinstance(rowSet.uid, int) and (previousUID is None):
                    objList.append(rowSet)
                elif (rowSet.uid != previousUID and isinstance(rowSet.uid, int) and isinstance(previousUID, int)):
                    objList.append(rowSet)
                elif (rowSet.uid == previousUID) and (rowSet.uidSScore <= previous_uidSScore) and isinstance(rowSet.uid, int) and isinstance(previousUID, int):
                    modifySet = rowSet
                    modifySet.uid = None
                    modifySet.uidSScore = 0.0
                    objList.append(modifySet)
                elif (rowSet == objList[len(objList)-1]):
                    if self.debug:
                        print("Duplicate getOneUIDList().")
                        print("Loop {}: Previous ~ Current".format(loopCount))
                        print(" UID  :  {} ~ {}".format(previousUID, rowSet.uid))
                        print(" Score:  {} ~ {}".format(previous_uidSScore, rowSet.uidSScore))
                    if rowSet.uidSScore >= previous_uidSScore:
                        removeValue = objList.pop()
                        if self.debug:
                            print(" Removing")
                            pprint.pprint(removeValue.get_all())
                            print(" Adding")
                            pprint.pprint(rowSet.get_all())
                        objList.append(rowSet)
                    else:
                        print(" Error getOneUIDList().")
                else:
                    if self.debug:
                        print("Warning getOneUIDList() possible previous simularity is less than current.")
                        print("Loop {}: Previous ~ Current".format(loopCount))
                        print(" UID  :  {} ~ {}".format(previousUID, rowSet.uid))
                        print(" Score:  {} ~ {}".format(previous_uidSScore, rowSet.uidSScore))
                    # Remove clean and replace
                    removeValue = objList.pop()
                    if self.debug:
                        print(" Removing...")
                        pprint.pprint(removeValue.get_all())
                    removeValue.uid = None
                    removeValue.uidSScore = 0.0
                    objList.append(removeValue)
                    if self.debug:
                        print(" Modifying...")
                        pprint.pprint(removeValue.get_all())
                        # Add better candidate.
                        print(" Adding...")
                        pprint.pprint(rowSet.get_all())
                    objList.append(rowSet)
                previousUID = rowSet.uid
                previous_uidSScore = rowSet.uidSScore
            loopCount += 1
            searchList = objList
        if self.debug:
            pprint.pprint(objList)
        objList = sorted(objList, key=lambda x: (4294967295 if x.uid is None else x.uid, reversor(x.uidSScore), x.instanceName.lower(), x.typeDef.lower(), x.packMode))

        if self.debug:
            pprint.pprint(objList)

        return objList

    def getSortedList(self, autoParserDataObjectList: list = None, mode=1):
        """
        Args:
            mode: Mode for sorting One is default, mode 2 is for sorting by UID.
            autoParserDataObjectList (dataStructureItem(list)):
        """
        if autoParserDataObjectList is None:
            return None
        if mode is 1:
            # Sort by unique name, type name, then pack value max to min. We want these in alphabetical order and highest number first
            sortedObjectList = sorted(autoParserDataObjectList, key=lambda x: (x.instanceName.lower(), x.typeDef.lower(), x.packMode))
        else:
            sortedObjectList = sorted(autoParserDataObjectList, key=lambda x: (4294967295 if x.uid is None else x.uid,
                                                                               x.instanceName.lower(),
                                                                               x.typeDef.lower(),
                                                                               x.packMode,
                                                                               str(x.majorMacro), str(x.minorMacro),
                                                                               str(x.versionMajorName), str(x.versionMinorName),
                                                                               str(x.RNLBA), str(x.WNLBA)))
        if self.debug:
            pprint.pprint(sortedObjectList)
        return sortedObjectList

##############################################
# Main Functions
##############################################
def hammerTime(dataObjectList=None, textInsert="All I know is that I know nothing...", debug=False):
    # Debug printer
    if ((dataObjectList is not None) and (debug is True)):
        for dataIter, dataItem in enumerate(dataObjectList):
            strList = (dataObjectList[dataIter]).get_all()
            if (debug is True):
                print(textInsert)
            for (strIter, strItem) in enumerate(strList):
                if (debug is True):
                    print(' L: ', int(strIter), ',V: ', strItem)
    return None

def configurationFileCreator(fileName="autoParser.cfg", dataObjectList=None, debug=False, mode=1):
    # File creator based on found tags.
    fileString = []
    fileString.append("#! /usr/bin/python")
    fileString.append("# -*- coding: utf-8 -*-")
    fileString.append("# Author(s): Joseph Tarango")
    fileString.append("# Skynet Machine Programming Config Generator...")
    fileString.append("AUTOPARSER_DATA_OBJECT_LIST = [")
    fileString.append("    # InstanceName, Typedef, VersionMajorMacro, VersopmMinorMacro, PragmaPack, VersionMajorName, VersionMinorName, RNLBA, WNLBA, eUID_Telemetry")
    if dataObjectList is not None:
        for (dataIter, dataItem) in enumerate(dataObjectList):
            if mode is 1:
                strList = (dataObjectList[dataIter]).get_all()
            elif mode is 2:
                strList = (dataObjectList[dataIter]).get_all_extra()
            elif mode is 3:
                strList = (dataObjectList[dataIter]).get_all_min()
            else:
                strList = (dataObjectList[dataIter]).get_all()
            strSlam = "    ["
            for (strIter, strItem) in enumerate(strList):
                if (strItem is not None and strIter != 4 and strIter != 7 and strIter != 8 and strIter != 9):
                    strSlam = str(strSlam) + (str('\'') + str(strItem)) + str('\'')
                else:
                    strSlam = (str(strSlam) + str(strItem))
                if (strIter < (len(strList)-1)):
                    strSlam = str(strSlam) + str(', ')
            strSlam = str(strSlam) + str('],')
            fileString.append(strSlam)
    fileString.append("]")
    print("Configuration Filename: ", fileName)
    if (debug is True): print("===========Testing File 1, 2, 3...===========\n")
    # Create the file from the string array.
    fileOpen = open(fileName, "w", encoding='utf-8')
    for (strLine, stringItem) in enumerate(fileString):
        if (debug is True): print(fileString[strLine])
        fileOpen.write(fileString[strLine])
        fileOpen.write("\n")
    fileOpen.close()
    return None

def uidFileCreator(fileName="telemetryObjects_eUID.py", debug=False):
    # File creator based on found tags.
    fileString = []
    fileString.append("#! /usr/bin/python")
    fileString.append("# -*- coding: utf-8 -*-")
    fileString.append("# Author(s): Joseph Tarango")
    fileString.append("# Skynet Machine Programming Config Generator...")
    fileString.append("TELEMETRYLIST = [")
    fileString.append("    # Id, Instance, Class Type, major, minor, byte size.")
    uidAccess = uniqueIdentifierTypes_e()
    uidDictionary = uidAccess.getForwardDictionary()
    if uidDictionary is not None:
        for (dataKey, dataValue) in uidDictionary.items():
            dataValueClean = uidAccess._strip_StartEnd(stringInput=dataValue, prefix='uid_', suffix='_e')
            strSlam = f'                ({dataKey}, "{dataValueClean}", 0, 0, 0),'
            fileString.append(strSlam)
    fileString.append("]")
    print("Configuration Filename: ", fileName)
    # Create the file from the string array.
    fileOpen = open(fileName, "w", encoding='utf-8')
    for (strLine, stringItem) in enumerate(fileString):
        if (debug is True): print(fileString[strLine])
        fileOpen.write(fileString[strLine])
        fileOpen.write("\n")
    fileOpen.close()
    return None

def whereIsWaldo(line="", strFront='uniqueIdentifier = uid_', strBack='_e;', strIDName='MATCH = ', debug=False):
    # Uses the search criteria to find the content we are looking for after we found the header.
    match = None
    rule = pyparsing.nestedExpr(strFront, strBack)  # Pulls the middle instance name.
    for match in rule.searchString(line):
        match = str(match).strip('[ ],\'')  # cleanup, similarly for other items below.
        if (debug is True): print(strIDName, match)
    return match

def reduced_dataStructureItem(dataObjectList=None):
    seenList = []
    reducedDataList = []
    if dataObjectList is not None:
        for (dataIter, dataItem) in enumerate(dataObjectList):
            strItem = (dataObjectList[dataIter]).get_instanceName()
            if strItem not in seenList:
                seenList.append(strItem)
                reducedDataList.append(dataObjectList[dataIter])
    return reducedDataList

def sorter_dataStructureItem(dataObjectList=None):
    sortedObjectList = sorted(dataObjectList, key=lambda x: x.get_instanceName().lower())
    return sortedObjectList

class FindProgressBar():
    def __init__(self, itemList=None, debug=False):
        self.total = 0
        self.point = 0
        self.increment = 0
        self.cPos = 0
        self.failSetup = False
        self.debug = debug
        self._setup(itemList=itemList)
        return

    def _setup(self, itemList=None):
        if itemList is None:
            self.failSetup = True
            return
        # Progress Bar Vars
        self.total = len(itemList)
        self.point = self.total / 100
        self.increment = self.total / 20
        self.cPos = 1
        self.failSetup = False
        return

    def updateTick(self, debug=False):
        if self.failSetup is True:
            return
        # Progress Bar...
        if debug is not True:
            if ((self.cPos > 0) and (self.cPos <= self.total)):
                if (self.cPos % (5 * self.point) == 0):
                    sys.stdout.write('\r')
                    strFillBar = "#" * (self.cPos / self.increment)
                    strBlankBar = " " * ((self.total - self.cPos) / self.increment)
                    strPercentBar = str(self.cPos / self.point)
                    progressBarPut = ("[{}{}] {}%".format(strFillBar, strBlankBar, strPercentBar))
                    sys.stdout.write(progressBarPut)
                    sys.stdout.flush()
            self.cPos = self.cPos + 1
        return

def main():
    ##############################################
    # Parse options.
    ##############################################
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--example", action='store_true', dest='example', default=False, help='Show command execution example.')
    parser.add_option("--sourceCode", action='store_true', dest='sourceCode', default=None, help='C and C++ code top directory')
    parser.add_option("--configFile", action='store_true', dest='configFile', default=None, help='Configuration file name to generate.')
    parser.add_option("--mergePreviousConfig", action='store_true', dest='mergePreviousConfig', default=True, help='Enable previous configuration list to merge with in the generation.')
    parser.add_option("--simularityScore", action='store_true', dest='simularityScore', default=0.95, help='Simularity metric between [0.0,1.0] for matching with known unique names.')
    parser.add_option("--debug", action='store_true', dest='debug', default=False, help='Debug mode.')
    parser.add_option("--verbose", action='store_true', dest='verbose', default=False, help='Verbose printing for debug use.')
    (options, args) = parser.parse_args()

    ##############################################
    # Message
    ##############################################
    print('##############################################')
    print('Average Joe\'s Configuration Generator')
    print(' Execution is expected to be less than 1 minute,')
    print('  if not then the machine maybe using old or slow hardware.')
    print('Starting... Skynet artificial neural network conscious mind.')
    print('##############################################')
    ##############################################
    # OPTIONS
    ##############################################
    print("Options List")
    print("Input...")
    print(" Example Flag: ", options.example)
    print(" Source Code Path: ", options.sourceCode)
    print(" Configuration File Name: ", options.configFile)
    print(" Debug Flag: ", options.debug)
    print(" Verbose Flag: ", options.verbose)
    print(" Merge Flag: ", options.mergePreviousConfig)
    print(" Simularity Score Value:", options.simularityScore)

    if (options.example):
        print('\nCommand-line execution example:')
        print('%s' % r"autoParser.py --sourceCode .\code\ssddev\gen3\nand\src --configFile autoParser.cfg --debug True --verbose True")
        quit(1)
    if (options.sourceCode and os.path.exists(os.path.abspath(options.sourceCode))):
        pathToSearch = options.sourceCode
    else:
        # "/home/lab/raad/ADP" "A:/Source/raad/ADP"
        pathToSearch = "../../ADP"
        if not os.path.exists(os.path.abspath(pathToSearch)):
            print("Source code path does not exist")
            quit(2)

    if (options.configFile is not None):
        pathToSearch = options.sourceCode
        print("Location exists?", os.path.exists(os.path.abspath(options.configFile)))
    else:
        options.configFile = "nu_autoParser.cfg"
        print("Warning Location exists?", os.path.exists(os.path.abspath(options.configFile)))

    if ((options.simularityScore < 0.0) or (options.simularityScore > 1.0) or (not isinstance(options.simularityScore, float))):
        options.simularityScore = 0.95

    debug = options.debug  # Replace the debug flag
    print("Using...")
    print(" Source Code Path: ", pathToSearch)
    print(" Configuration File Name: ", options.configFile)
    print('##############################################')
    ##############################################
    # Hard Coded Values, necessary for now...
    ##############################################
    # The following is the excepted format of the firmware code.
    searchListNAND = [
        "///< Data Control Tracking information for Telemetry.",
        "///< uniqueIdentifier =",
        "///< major =",
        "///< minor = ",
        "///< size = ",
    ]

    lineSearchListCount = len(searchListNAND)  # Number of lines to search from the first tag.
    """ Example search set.
    searchKnownTags = \
    [ # FORMAT:
      # [Front_Tag, Back_Tag, String_Print_Name],
      # Unique Identifier
      ['uniqueIdentifier = uid_','_e;', ' instance ='],
      # Major Identifier
      ['major = ',               ';',   '  major ='], 
      # Minor Identifier
      ['minor = ',               ';',   '  minor ='],
      # Type Identifier from the sizeof tag.
      ['size = sizeof(',         ');',  '  type ='],
    ]
    """
    # File Types we are looking for in the path.
    extensionListCode = [".h", ".c", ".hpp", ".cpp"]
    ##############################################
    # Main, Extract Configuration File from source code.
    #############################################
    # The first tag of the block, we use this to check subsequent lines.
    #  Algorithm uses this for the found line then search next set.
    #  Summary: Found tag the check this line and the next lines.
    #   The code tags can be all in one line or multible lines with no new
    #   lines in between.
    search_str = searchListNAND[0]  # Main TAG for search.

    # Create an empty list for tracking data
    dataObjectList = []
    rootdir = pathToSearch

    # Progress Bar Vars
    unoNada, dosNada, tfiles = next(os.walk(rootdir))
    progressBar = FindProgressBar(itemList=tfiles, debug=options.debug)

    for (folder, dirs, files) in os.walk(rootdir):
        for file in files:
            # Progress Bar...
            progressBar.updateTick(options.debug)
            # Work, Work, Work...
            for (indexExtension, itemExtension) in enumerate(extensionListCode):
                if (debug is True): print("Extension, Index: ", indexExtension, "Postfix", itemExtension)
                if (file.endswith(itemExtension)):
                    fullpath = os.path.join(folder, file)
                    if (debug is True): print("File: ", file)
                    with open(fullpath, 'r', encoding="utf8", errors='ignore') as openFile:
                        foundLine = False
                        count = 0
                        dataSRow = dataStructureItem()
                        for (lineNo, line) in enumerate(openFile):
                            if ((search_str in line) or ((foundLine is True) and (count <= lineSearchListCount)) ):
                                foundLine = True
                                count += 1
                                if (debug is True):
                                    print('Line Number = ', lineNo, ':: Count =', count, ' :: Line = ', line)
                                    print('MATCH')
                                # Unique Identifier
                                match = whereIsWaldo(line=line, strFront='uniqueIdentifier = uid_', strBack='_e;', strIDName=' instance =', debug=debug)
                                dataSRow.set_instanceName(match)
                                # Major Identifier
                                match = whereIsWaldo(line=line, strFront='major = ', strBack=';', strIDName='  major =', debug=debug)
                                dataSRow.set_majorMacro(match)
                                # Minor Identifier
                                match = whereIsWaldo(line=line, strFront='minor = ', strBack=';', strIDName='  minor =', debug=debug)
                                dataSRow.set_minorMacro(match)
                                # Type Identifier from the sizeof tag.
                                match = whereIsWaldo(line=line, strFront='size = sizeof(', strBack=');', strIDName='  type =', debug=debug)
                                dataSRow.set_typeDef(match)
                                if (count >= lineSearchListCount):
                                    foundLine = False
                                    count = 0
                                    dataObjectList.append(dataSRow)
                                    # if options.debug: dataSRow = None  # @todo Force item reset for debug
                                    dataSRow = dataStructureItem()
    ##############################################
    # Add existing list items.
    ##############################################
    if options.mergePreviousConfig is True:
        try:
            import source.baseTags
            autoObjects = source.baseTags.AUTOPARSER_DATA_OBJECT_LIST
            for field_Index, field_row in enumerate(autoObjects):
                field_instanceName, field_typedef, field_vMajor_macro, field_vMinor_macro, field_pack, field_vMajorName, field_vMinorName, field_RNLBA, field_WNLBA = field_row
                oldRow = dataStructureItem()
                oldRow.set_all(instanceName=field_instanceName, typeDef=field_typedef,
                               majorMacro=field_vMajor_macro, minorMacro=field_vMinor_macro,
                               packMode=field_pack,
                               versionMajorName=field_vMajorName, versionMinorName=field_vMinorName,
                               RNLBA=field_RNLBA, WNLBA=field_WNLBA, uid=None)
                dataObjectList.append(oldRow)  # Adding to list
        except ImportError:
            print("Error with: AUTOPARSER_DATA_OBJECT_LIST")

    ##############################################
    # Attempt to fill in Missing content.
    ##############################################
    for (dataIter, dataItem) in enumerate(dataObjectList):
        (dataObjectList[dataIter]).tryFillEmpty(sScoreThreshold=0.95)
    cleanSL = dataStructureList()
    dataObjectListAfter = cleanSL.getOneUIDList(autoParserDataObjectList=dataObjectList)
    dataObjectList = dataObjectListAfter

    ##############################################
    # Sort through the found objects.
    ##############################################
    validObjectsCount = 0
    goodList = []
    badList = []
    for (dataIter, dataItem) in enumerate(dataObjectList):
        valid = (dataObjectList[dataIter]).get_verify()
        if (valid is True):
            validObjectsCount += 1
            strList = (dataObjectList[dataIter]).get_all()
            goodList.append(dataObjectList[dataIter])
            if (debug is True): print("=VALID=============================")
            for strIter, strItem in enumerate(strList):
                if (debug is True): print('Line: ', int(strIter), ',Value: ', strItem)
        else:
            strList = (dataObjectList[dataIter]).get_all()
            badList.append(dataObjectList[dataIter])
            if (debug is True): print("===========================INVALID=")
            for (strIter, strItem) in enumerate(strList):
                if (debug is True): print('Line: ', int(strIter), ',Value: ', strItem)
    ##############################################
    # Verify lists
    ##############################################
    if (debug is True):
        print("Objects Valid ", validObjectsCount, ",Objects Invalid Math ", (len(dataObjectList) - validObjectsCount), ",Objects Found ", len(dataObjectList))
    print("The Good: ", len(goodList), "... The Bad:", len(badList), "... and The Ulgy Truth:", len(dataObjectList), "...")
    hammerTime(dataObjectList=goodList, textInsert="Good very good...", debug=debug)
    hammerTime(dataObjectList=badList, textInsert="Anger is the path to the dark side...", debug=options.verbose)
    ##############################################
    # Create the file...
    ##############################################
    # Cleanup good and bad list and keep the main ulgy list the same just sort.
    gsl = dataStructureList()
    goodList = gsl.getProcessedList(autoParserDataObjectList=goodList)
    bsl = dataStructureList()
    badList = bsl.getProcessedList(autoParserDataObjectList=badList)
    usl = dataStructureList()
    # dataObjectList = usl.getSortedList(autoParserDataObjectList=dataObjectList)
    dataObjectList = bsl.getProcessedList(autoParserDataObjectList=dataObjectList)
    dataObjectList = usl.getSortedList(autoParserDataObjectList=dataObjectList, mode=2)
    # Write out the file.
    # Mode 1 Default auto parser.
    configurationFileCreator(fileName=options.configFile, dataObjectList=goodList, debug=debug, mode=1)
    configurationFileCreator(fileName=str('bad_' + options.configFile), dataObjectList=badList, debug=debug, mode=1)
    configurationFileCreator(fileName=str('ulgy_' + options.configFile), dataObjectList=dataObjectList, debug=debug, mode=1)
    # Mode 2 Auto decoder for RAAD.
    configurationFileCreator(fileName=str('extra_' + options.configFile), dataObjectList=goodList, debug=debug, mode=2)
    configurationFileCreator(fileName=str('extra_bad_' + options.configFile), dataObjectList=badList, debug=debug, mode=2)
    configurationFileCreator(fileName=str('extra_ulgy_' + options.configFile), dataObjectList=dataObjectList, debug=debug, mode=2)
    # Mode 3 Auto decoder for RAAD.
    configurationFileCreator(fileName=str('min_' + options.configFile), dataObjectList=goodList, debug=debug, mode=3)
    configurationFileCreator(fileName=str('min_bad_' + options.configFile), dataObjectList=badList, debug=debug, mode=3)
    configurationFileCreator(fileName=str('min_ulgy_' + options.configFile), dataObjectList=dataObjectList, debug=debug, mode=3)
    # Update object list for RAAD.
    uidFileCreator(fileName=f"telemetryObjects_eUID_{options.configFile}.py", debug=False)
    print('##############################################')

    autoParserOptions = None
    # options.fwBuildOutputDir
    #         self.options = options
    #         self.verbose = options.verbose
    # parser.add_option("--cfg", dest='inputCfg', metavar='<CFG>', default=None, help='CFG file with specified FW structs to direct parser generation (default=None)')
    # parser.add_option("--compiler", dest='ghsCompilerVersion', metavar='<COMPVER>', default=GHS_COMPILER_VERSION, help='GHS compiler version (default=comp_201754)')
    # parser.add_option("--debug", action='store_true', dest='debug', default=False, help='Debug mode.')
    # parser.add_option("--example", action='store_true', dest='example', default=False, help='Show command execution example.')
    # parser.add_option("--fwbuilddir", dest='fwBuildOutputDir', metavar='<DIR>', help='FW build directory (ex: projects/objs/alderstream_02)')
    # parser.add_option("--project", dest='projectName', metavar='<PROJ>', help='Project name (ex: alderstream_02)')
    # parser.add_option("--verbose", action='store_true', dest='verbose', default=False, help='Verbose printing for debug use.')
    # cag = source.autoParser_v3.AutoParser(options)
    # cag.autoGenerateCtypes()

    return 0


if __name__ == '__main__':
    """Performs execution delta of the process."""
    from datetime import datetime
    p = datetime.now()
    print("Time started: ", str(p))
    # try:
    main()
    # except:
    #    print(" Rico: Bugs!!!!")
    #    print(" Uncomment main try block and start debugging.")
    q = datetime.now()
    print("Execution time: ", str(q-p), " Tempus fugit!")
    print("Time completed: ", str(q))
    quit(0)
