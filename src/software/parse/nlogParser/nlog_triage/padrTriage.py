#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors:Joseph Tarango, Randal Eike
# *****************************************************************************/
"""
Brief:
    padrTriage.py - Parse the PADR nlog message

Description:
    Triage the PADR messages and look for errors

Classes:
    padrTriage.
"""

from src.software.parse.nlogParser.nlog_triage.nlogTriageBase import nlogTriageBase

# Version Table
# Version 0.2 : Framework implemented and passes crash test, no state checking done
TOOL_VERSION = 0.2

MAX_PORT =  2
MAX_FID  =  64

class padrTriage(nlogTriageBase):
    transitionMarker = " -> goto "
    transitionMarkerLen = len(transitionMarker)
    padrMarker = "PADR_"
    padrMarkerLen = len(padrMarker)
    padrStateEndMarker = "_"
    padrActionStartMarker = "__"
    padrActionStartMarkerLen = len(padrActionStartMarker)

    def __init__(self):
        self.currentIntfState = {}
        for logicalIntf in range (0, MAX_PORT * MAX_FID):
            self.currentIntfState[logicalIntf] = 0

        super(padrTriage, self).__init__("PADR",TOOL_VERSION)

    def __updateState(self, padrState, padrAction, newPadrState, newPadrAction, port, fid):
        # @todo implement triage code to help diagnose PADR state errors
        self.currentIntfState[port*fid] = newPadrState
        pass

    def addNlogEvent(self, format, params, tsSeconds, coreId):
        """
        Determine if this a pss debug trace nlog entry and record the state transition 
        in the list if it is

        @param format - nlog format string
        @param params - nlog associated parameter tuple
        @param tsSeconds - nlog timestamp in seconds (floating point value)
        @param coreId - Core number for the NLOG
        """
        self.hostMessage = None

        if (padrTriage.padrMarker in format):
            # Get FID and port from the parameters if possible
            if (len(params) > 1): fid = params[1]
            else: fid = 0
            if (len(params) > 0): port = params[0]
            else: port = 0

            # look for transition
            padrTransition = format.find(padrTriage.transitionMarker)
            if (-1 == padrTransition): 
                newPadrState = ""
                newPadrAction = ""
                padrStateString = format[format.find(padrTriage.padrMarker) + padrTriage.padrMarkerLen:]
            else: 
                # Parse out the new state and action data
                newPadrStateString = format[padrTransition+padrTriage.transitionMarkerLen:]
                newPadrState = newPadrStateString[:newPadrStateString.find(padrTriage.padrStateEndMarker)]
                newPadrAction = newPadrStateString[newPadrStateString.rfind(padrTriage.padrActionStartMarker) + padrTriage.padrActionStartMarkerLen:newPadrStateString.rfind(" ")]

                padrStateString = format[format.find(padrTriage.padrMarker) + padrTriage.padrMarkerLen:padrTransition]

            # Parse out the state and action data
            padrState = padrStateString[:padrStateString.find(padrTriage.padrStateEndMarker)]
            padrAction = padrStateString[padrStateString.rfind(padrTriage.padrActionStartMarker) + padrTriage.padrActionStartMarkerLen:]

            # Determine if it's all ok
            self.__updateState(padrState, padrAction, newPadrState, newPadrAction, port, fid)

        return self.hostMessage

