#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
"""
Brief:
    pssDebugTraceTriage.py - Parse the pssdebug trace list to look for state sequence errors

Description:
    PSS Debug state change triage analysis object

Classes:
    pssDebugTraceTriage.
"""

from src.software.parse.nlogParser.nlog_triage.nlogTriageBase import nlogTriageBase

# Version Table
# Version 0.7 : Framework implemented, Alpha level state checking in place for CDR
TOOL_VERSION = 0.7

"""
State lists define the enumeration value associated with the state, the previous
allowed states and the name of the state
"""

# PCIE state list
PCIE_STATE_INIT            = 0                # Default initial state
PCIE_STATE_PERST_ASSERT    = 1                # PERST asserted state
PCIE_STATE_PERST_DEASSERT  = 2                # PERST deasserted state, no PLL lock
PCIE_STATE_PLL_LOCK        = 3                # PLL lock, training initialization
PCIE_STATE_PLL_LOCK_LOSS   = 4                # PLL lock lost
PCIE_STATE_LINK_UP         = 5                # Link training complete, config space not ready
PCIE_STATE_LINK_DOWN       = 6                # Link down/hot reset state

pcieStateTransitionTable = { PCIE_STATE_INIT:           {'allowed': None,                                                                                 'name': 'PCIE Initial state'             },
                             PCIE_STATE_PERST_ASSERT:   {'allowed': None,                                                                                 'name': 'PCIE PERST Assertion'           },
                             PCIE_STATE_PERST_DEASSERT: {'allowed': [PCIE_STATE_INIT, PCIE_STATE_PERST_ASSERT],                                           'name': 'PCIE PERST Deassertion'         },
                             PCIE_STATE_PLL_LOCK:       {'allowed': [PCIE_STATE_INIT, PCIE_STATE_PERST_DEASSERT, PCIE_STATE_PLL_LOCK],                    'name': 'PCIE PLL lock, train begining'  },
                             PCIE_STATE_PLL_LOCK_LOSS:  {'allowed': [PCIE_STATE_INIT, PCIE_STATE_PLL_LOCK, PCIE_STATE_LINK_UP, PCIE_STATE_LINK_DOWN],     'name': 'PCIE PLL lock lost'             },
                             PCIE_STATE_LINK_UP:        {'allowed': [PCIE_STATE_INIT, PCIE_STATE_PLL_LOCK, PCIE_STATE_LINK_DOWN],                         'name': 'PCIE Link training complete'    },
                             PCIE_STATE_LINK_DOWN:      {'allowed': [PCIE_STATE_INIT, PCIE_STATE_LINK_UP, PCIE_STATE_PERST_ASSERT, PCIE_STATE_LINK_DOWN], 'name': 'PCIE Link down complete'        }
                           }

# PCI state list
PCI_CONFIG_NOT_READY       = 0                # Default initial state
PCI_CONFIG_READY           = 1                # PCI config space and NPL initialization complete
PCI_FLR                    = 2                # PCI config space and NPL reset

pciConfigTransitionTable = { PCI_CONFIG_NOT_READY:     {'allowed': None,                                                   'name': 'PCIE not link up'                  },
                             PCI_CONFIG_READY:         {'allowed': [PCI_CONFIG_READY, PCI_FLR],                            'name': 'PCI configuration space enabled'   },
                             PCI_FLR:                  {'allowed': [PCI_CONFIG_NOT_READY, PCI_CONFIG_READY],               'name': 'PCI FLR processing'                },
                           }

# NVME state list
NVME_STATE_DEFAULT         = 0                # Default initial state
NVME_STATE_INIT            = 1                # NPL initialization complete, CC.EN = 0, CSTS.RDY = 0
NVME_STATE_ENABLED         = 2                # CC.EN = 1, CSTS.RDY = 0
NVME_STATE_READY           = 3                # CC.EN = 1, CSTS.RDY = 1
NVME_STATE_RESET           = 4                # CC.EN = 1->0, CSTS.RDY = 1
NVME_STATE_SSRESET         = 5                # NSSR write, CC.EN = 0, CSTS.RDY = 1
NVME_STATE_SAFE_SHUTDOWN   = 6                # Safe shutdown
NVME_STATE_ABRT_SHUTDOWN   = 7                # Abrupt shutdown
NVME_STATE_SHUTDOWN_PROCESSING = 8            # Waiting to complete the shutdown

nvmeStateTransitionTable = { NVME_STATE_DEFAULT:       {'allowed': None,                                                                                              'name': 'NVME Initial state, power on or bus reset'                    },
                             NVME_STATE_INIT:          {'allowed': [NVME_STATE_DEFAULT, NVME_STATE_RESET, NVME_STATE_SSRESET, NVME_STATE_ENABLED],                    'name': 'NVME NPL initialization complete'      },
                             NVME_STATE_ENABLED:       {'allowed': [NVME_STATE_DEFAULT, NVME_STATE_READY],                                                            'name': 'NVME enabled, not ready'               },
                             NVME_STATE_READY:         {'allowed': [NVME_STATE_DEFAULT, NVME_STATE_RESET, NVME_STATE_SSRESET, NVME_STATE_SAFE_SHUTDOWN, NVME_STATE_ABRT_SHUTDOWN], 'name': 'NVME ready'                            },
                             NVME_STATE_RESET:         {'allowed': [NVME_STATE_DEFAULT, NVME_STATE_ENABLED, NVME_STATE_SSRESET, NVME_STATE_DEFAULT, NVME_STATE_INIT], 'name': 'NVME controller reset processing'      },
                             NVME_STATE_SSRESET:       {'allowed': [NVME_STATE_DEFAULT, NVME_STATE_ENABLED, NVME_STATE_RESET, NVME_STATE_INIT],                       'name': 'NVME subsystem reset processing'       },
                             NVME_STATE_SAFE_SHUTDOWN: {'allowed': [NVME_STATE_DEFAULT, NVME_STATE_SHUTDOWN_PROCESSING, NVME_STATE_RESET, NVME_STATE_INIT],           'name': 'NVME safe shutdown processing'         },
                             NVME_STATE_ABRT_SHUTDOWN: {'allowed': [NVME_STATE_DEFAULT, NVME_STATE_SHUTDOWN_PROCESSING, NVME_STATE_RESET, NVME_STATE_INIT],           'name': 'NVME abrupt shutdown processing'       },
                             NVME_STATE_SHUTDOWN_PROCESSING: {'allowed': [NVME_STATE_RESET, NVME_STATE_DEFAULT, NVME_STATE_INIT, NVME_STATE_ENABLED],                 'name': 'NVME abrupt shutdown processing'       },
                           }


# Define the event numbers
INIT                            = 0                    # 0-Unused entry
BIS_INIT                        = 1                    # 1-BIS structure Init (very beginning of bootloader starts) (obsolete).
PSS_RESET                       = 2                    # 2-PSS Hardware placed in reset PERST assert ISR.
PSS_DMA_RESET_START             = 3                    # 3-PSS DMA Engine reset start.
PSS_INIT                        = 4                    # 4-PSS Hardware Init always the first thing called in the BL and MFW.
PSS_WARMBOOT                    = 5                    # 5-PSS Warm boot Init.
PSS_RESET_DEASSERT              = 6                    # 6-PSS Hardware reset deassert ISR.
PCIE_PLL_LOCK_GAIN              = 7                    # 7-PCIe PLL Lock Gained ISR.
PCIE_LINK_TRAIN_INIT            = 8                    # 8-PCIe Link Train Init called from PLL lock gained ISR.
PCIE_LINK_UP                    = 9                    # 9-PCIe Link Up called from error ISR.
PCIE_PLL_LOCK_LOSS              = 10                   # 10-PCIe PLL Lock Lost ISR.
PCIE_LINK_DOWN                  = 11                   # 11-PCIe Link down called from error ISR.
KRNL_STRTS                      = 12                   # 12-Kernel Starts.
DISCOVERY_STARTS                = 13                   # 13-NAND Discovery starts (obsolete).
PMIC_SXP_OK                     = 14                   # 14-PMIC SXP OK asserts.
DISCOVERY_SUCCESS               = 15                   # 15-NAND Discovery successfully done.
PCI_CFG_RDY_RELEASE             = 16                   # 16-Firmware releases PCI CFG READY.
PCI_ENABLE_OROM                 = 17                   # 17-Option ROM enabled.
PSS_INTERRUPT_VERIFICATION_WAIT = 18                   # 18-Debug interrupt memory verification wait loop exit
PCIE_PLL_LOCK_GAIN_NOLOCK       = 19                   # 19-Debug of PLL lock interrupt state
PSS_TIMEOVERFLOW                = 20                   # 20-Timer overflow upper bits
PSS_RESET_REASSERT              = 21                   # 21-PSS Hardware reset asserted again (coldBootPolled).
PSS_RESET_REASSERT1             = 22                   # 22-PSS Hardware reset asserted again (validatePcieState).
PSS_RECOVERY_RESET              = 23                   # 23-PSS reset recovery.
PSS_PLL_LOCK_TIMEOUT            = 24                   # 24-PSS PLL lock timeout.
PSS_WAIT_LINK_TIMEOUT           = 25                   # 25-PSS Wait for link timeout.
NVME_CSTS_READY                 = 26                   # 26-NVME CSTS.RDY change.
NVME_CC_ENABLE                  = 27                   # 27-NVME CC.EN enable.
PSS_KILL_LINK                   = 28                   # 28-PSS link kill due to PLI.
PSS_RESET_DEASSERT1             = 29                   # 29-PSS PERST deassert called from validatePcieState routine.
PSS_WARMBOOT1                   = 30                   # 30-PSS Warm boot path post PERST handling.
PCI_CFG_RDY_DISABLE             = 31                   # 31-PCI configuration ready disable.
PSS_PWRON_INIT                  = 32                   # 32-PSS NPL power on initialization function called.
PSS_ENABLE_INTERRUPT            = 33                   # 33-PSS Enable interrupts called.
PSS_DISABLE_INTERRUPT           = 34                   # 34-PSS Disable interrupts called.
PCI_DISABLE_OROM                = 35                   # 35-PSS Disable OROM called.
NVME_CC_DISABLE                 = 36                   # 36-NVME CC.EN disable.
NPL_INIT                        = 37                   # 37-NPL Iniialization called
SYSTEM_WARM_RESET_START         = 38                   # 38-Warm Reset, start of SystemHal_CpuWarmReset() routine.
SYSTEM_WARM_RESET_END           = 39                   # 39-Warm Reset, HalCpu_WarmReset() after setting input warm reset signature
PSS_NPL_NOTIFY_ACTIVE           = 40                   # 40-NPL active notify in PSS
PSS_NPL_NOTIFY_SHUTDOWN         = 41                   # 41-NPL shutdown notify in PSS
PSS_NPL_NOTIFY_RESET_PERST      = 42                   # 42-NPL notify warm reset pending due to PERST in PSS
PSS_NPL_NOTIFY_RESET_LINKDOWN   = 43                   # 43-NPL notify warm reset pending due to link down in PSS
PSS_NPL_NOTIFY_RESET_NVME       = 44                   # 44-NPL notify warm reset pending due to NVME reset call to warm reset in PSS
PSS_NPL_NOTIFY_INIT             = 45                   # 45-NPL notify init in PSS
SYSTEM_BL_START_COMPLETE        = 46                   # 46-Bootloader complete
COMPRESSED_ENTRY                = 47                   # 47-Compress entry representing link up, cfg ready, link down
PSS_CFG_RDY_MULTI_WR            = 48                   # 48-Multiple writes of config ready enable bit required
PCI_FLR                         = 49                   # 49-PCI Function level reset
PSS_ASSERT_RECOVERY_ENTERED     = 50                   # 50-Assert recovery entered
PSS_TRACK_MAIN_FW_BASE          = 51                   # Boundary marker
SAFE_SHUTDOWN                   = 100
ABRUPT_SHUTDOWN                 = 101

"""
The event transition map defines the PCIE, PCICFG and NVME state transitions associated 
with the event in the FW
"""
# Define the event action map
pssTransitionMap_CDR = {INIT:                          {'pcieState': PCIE_STATE_INIT, 'pciCfgState': PCI_CONFIG_NOT_READY, 'nvmeState': NVME_STATE_DEFAULT},
                        BIS_INIT:                      {},
                        PSS_RESET:                     {'pcieState': PCIE_STATE_PERST_ASSERT, 'pciCfgState': PCI_CONFIG_NOT_READY, 'nvmeState': NVME_STATE_DEFAULT},
                        PSS_DMA_RESET_START:           {},
                        PSS_INIT:                      {},
                        PSS_WARMBOOT:                  {},
                        PSS_RESET_DEASSERT:            {'pcieState': PCIE_STATE_PERST_DEASSERT},
                        PCIE_PLL_LOCK_GAIN:            {'pcieState': PCIE_STATE_PLL_LOCK},
                        PCIE_LINK_TRAIN_INIT:          {'pcieState': PCIE_STATE_PLL_LOCK},
                        PCIE_LINK_UP:                  {'pcieState': PCIE_STATE_LINK_UP },
                        PCIE_PLL_LOCK_LOSS:            {'pcieState': PCIE_STATE_PLL_LOCK_LOSS, 'pciCfgState': PCI_CONFIG_NOT_READY, 'nvmeState': NVME_STATE_DEFAULT},
                        PCIE_LINK_DOWN:                {'pcieState': PCIE_STATE_LINK_DOWN,     'pciCfgState': PCI_CONFIG_NOT_READY, 'nvmeState': NVME_STATE_DEFAULT},
                        KRNL_STRTS:                    {},
                        DISCOVERY_STARTS:              {},
                        PMIC_SXP_OK:                   {},
                        DISCOVERY_SUCCESS:             {},
                        PCI_CFG_RDY_RELEASE:           {'pciCfgState': PCI_CONFIG_READY},
                        PCI_ENABLE_OROM:               {},
                        PSS_INTERRUPT_VERIFICATION_WAIT: {},
                        PCIE_PLL_LOCK_GAIN_NOLOCK:     {'pcieState': PCIE_STATE_PLL_LOCK},
                        PSS_TIMEOVERFLOW:              {},
                        PSS_RESET_REASSERT:            {'pcieState': PCIE_STATE_PERST_ASSERT, 'pciCfgState': PCI_CONFIG_NOT_READY, 'nvmeState': NVME_STATE_DEFAULT},
                        PSS_RESET_REASSERT1:           {'pcieState': PCIE_STATE_PERST_ASSERT, 'pciCfgState': PCI_CONFIG_NOT_READY, 'nvmeState': NVME_STATE_DEFAULT},
                        PSS_RECOVERY_RESET:            {},
                        PSS_PLL_LOCK_TIMEOUT:          {'warning': 'PLL Lock timeout detected'},
                        PSS_WAIT_LINK_TIMEOUT:         {'warning': 'PCIE link wait timeout detected'},
                        NVME_CSTS_READY:               {'nvmeState': NVME_STATE_READY},
                        NVME_CC_ENABLE:                {'nvmeState': NVME_STATE_ENABLED},
                        PSS_KILL_LINK:                 {'pcieState': PCIE_STATE_PERST_ASSERT, 'pciCfgState': PCI_CONFIG_NOT_READY, 'nvmeState': NVME_STATE_DEFAULT},
                        PSS_RESET_DEASSERT1:           {'pcieState': PCIE_STATE_PERST_DEASSERT},
                        PSS_WARMBOOT1:                 {},
                        PCI_CFG_RDY_DISABLE:           {'pciCfgState': PCI_CONFIG_NOT_READY},
                        PSS_PWRON_INIT:                {'nvmeState': NVME_STATE_INIT},
                        PSS_ENABLE_INTERRUPT:          {'pssInterrupt': 1},
                        PSS_DISABLE_INTERRUPT:         {'pssInterrupt': 0},
                        PCI_DISABLE_OROM:              {},
                        NVME_CC_DISABLE:               {'nvmeState': NVME_STATE_RESET},
                        NPL_INIT:                      {'nvmeState': NVME_STATE_INIT},
                        SYSTEM_WARM_RESET_START:       {},
                        SYSTEM_WARM_RESET_END:         {},
                        PSS_NPL_NOTIFY_ACTIVE:         {},
                        PSS_NPL_NOTIFY_SHUTDOWN:       {},
                        PSS_NPL_NOTIFY_RESET_PERST:    {},
                        PSS_NPL_NOTIFY_RESET_LINKDOWN: {},
                        PSS_NPL_NOTIFY_RESET_NVME:     {},
                        PSS_NPL_NOTIFY_INIT:           {},
                        SYSTEM_BL_START_COMPLETE:      {},
                        COMPRESSED_ENTRY:              {},
                        PSS_CFG_RDY_MULTI_WR:          {},
                        PCI_FLR:                       {'pciCfgState': PCI_FLR, 'nvmeState': NVME_STATE_DEFAULT},
                        PSS_ASSERT_RECOVERY_ENTERED:   {},
                        SAFE_SHUTDOWN:                 {'nvmeState': NVME_STATE_SAFE_SHUTDOWN},
                        ABRUPT_SHUTDOWN:               {'nvmeState': NVME_STATE_ABRT_SHUTDOWN},
                        }

class pssDebugTraceTriage(nlogTriageBase):
    """
    Process the input Debug state and look for unexpected or illegal transitions
    """
    errorLevel = 0
    warningLevel = 1
    eventList = []

    def __resetTimeStamps(self):
        self.startTime = None
        self.perstDeassertTime = None
        self.linkTrainStartTime = None
        self.linkUpTime = None
        self.pcicfgReadyTime = None
        self.flrTime = None
        self.cstsReadyTime = None
        self.flrRecoveryTime = None
        self.lastAdjustTime = 0
        self.previousTs = 0

    def __adjustTimeStamps(self, adjustTime):
        if (self.startTime is not None): self.startTime += adjustTime
        if (self.perstDeassertTime is not None): self.perstDeassertTime += adjustTime
        if (self.linkTrainStartTime is not None): self.linkTrainStartTime += adjustTime
        if (self.linkUpTime is not None): self.linkUpTime += adjustTime
        if (self.pcicfgReadyTime is not None): self.pcicfgReadyTime += adjustTime
        if (self.flrTime is not None): self.flrTime += adjustTime
        if (self.cstsReadyTime is not None): self.cstsReadyTime += adjustTime
        if (self.flrRecoveryTime is not None): self.flrRecoveryTime += adjustTime

    def __resetState(self):
        self.pcieState = PCIE_STATE_INIT
        self.pciCfgState = PCI_CONFIG_NOT_READY
        self.nvmeState = NVME_STATE_DEFAULT
        self.__resetTimeStamps()

    def __init__(self, family = "CDR"):
        self.__resetState()

        if (family == "CD"): self.transitionMap = pssTransitionMap_CDR
        elif (family == "CDR"): self.transitionMap = pssTransitionMap_CDR
        elif (family == "ADP"): self.transitionMap = pssTransitionMap_CDR
        else: self.transitionMap = pssTransitionMap_CDR

        super(pssDebugTraceTriage, self).__init__(family+'_pssdebug', TOOL_VERSION)


    def __updatePcieState(self, newStateNumber, time, stateEvent):
        # lookup the entry
        currentState = pcieStateTransitionTable[self.pcieState]

        # Check if the transition is valid
        if (currentState['allowed'] is not None):
            if (newStateNumber not in currentState['allowed']):
                self._message(nlogTriageBase.warningLevel, "%s: Illegal PCIE state transition from %s to %s", (self._timestamp(time), pcieStateTransitionTable[self.pcieState]['name'], pcieStateTransitionTable[newStateNumber]['name']))

        # Set new state
        self.pcieState = newStateNumber

        # Check for time markers
        if (newStateNumber == PCIE_STATE_PERST_DEASSERT): 
            self.perstDeassertTime = time
        if (newStateNumber == PCIE_STATE_PLL_LOCK): 
            self.linkTrainStartTime = time
            if (self.perstDeassertTime is not None):
                linkTrainTimeCheck = (self.linkTrainStartTime - self.perstDeassertTime) * 1000
                if (linkTrainTimeCheck > 20):
                    self._message(nlogTriageBase.warningLevel, "PCIE link training start time %6.3fms exceeded 20ms timeout from PERST deassert", (linkTrainTimeCheck))

        if (newStateNumber == PCIE_STATE_LINK_UP):
            self.linkUpTime  = time
            if (self.linkTrainStartTime is not None): 
                linkTrainingTime = (self.linkUpTime - self.linkTrainStartTime) * 1000
                self._message(nlogTriageBase.information, "PCIE link training time %6.3fms", (linkTrainingTime))

        # Reset the markers on PERST assert
        if (newStateNumber == PCIE_STATE_PERST_ASSERT): self.__resetTimeStamps() 

        # Reset link up time on link down
        if (newStateNumber == PCIE_STATE_LINK_DOWN): self.__resetTimeStamps()
        self.previousPcieUpdateEvent = stateEvent

    def __updatePciCfgState(self, newStateNumber, time, stateEvent):
        # lookup the entry
        currentState = pciConfigTransitionTable[self.pciCfgState]

        # Check if the transition is valid
        if (currentState['allowed'] is not None):
            if (newStateNumber not in currentState['allowed']):
                self._message(nlogTriageBase.warningLevel, "%s: Illegal PCI Config state transition from %s to %s", (self._timestamp(time), pciConfigTransitionTable[self.pciCfgState]['name'], pciConfigTransitionTable[newStateNumber]['name']))

        if ((self.pciCfgState == PCI_FLR) and (newStateNumber == PCI_CONFIG_READY) and (self.flrTime is not None)):
            self.flrRecoveryTime = time
            if (self.flrTime is not None):
                flrRecoveryTime = (self.flrRecoveryTime - self.flrTime) * 1000
                if (flrRecoveryTime > 100):
                    self._message(nlogTriageBase.warningLevel, "PCI FLR recovery time %6.3fms exceeded 100ms timeout from FLR assertion", flrRecoveryTime)

        # Set new state
        self.pciCfgState = newStateNumber

        # Check for time markers
        if (newStateNumber == PCI_CONFIG_READY): 
            self.pcicfgReadyTime = time
            if (self.perstDeassertTime is not None):
                configReadyTime = self.pcicfgReadyTime - self.perstDeassertTime
                if (configReadyTime > 1):
                    self._message(nlogTriageBase.warningLevel, "PCI config space enable time %6.3fms exceeded 1s timeout from PERST deassert", (configReadyTime))

        if (newStateNumber == PCI_FLR): 
            self.flrTime = time
            self.startTime = time  # reset the start time marker

        self.previousPciCfgUpdateEvent = stateEvent


    def __updateNvmeState(self, newStateNumber, time, stateEvent):
        # Expected, ignore it and stay in shutdown mode
        if (((self.nvmeState == NVME_STATE_SAFE_SHUTDOWN) or (self.nvmeState == NVME_STATE_ABRT_SHUTDOWN)) and (newStateNumber == NVME_STATE_ENABLED)):
            newStateNumber = NVME_STATE_SHUTDOWN_PROCESSING

        # lookup the entry
        currentState = nvmeStateTransitionTable[self.nvmeState]

        # Check if the transition is valid, transition to same state is always valid
        if (self.nvmeState != newStateNumber) and (currentState['allowed'] is not None):
            if (newStateNumber not in currentState['allowed']):
                self._message(nlogTriageBase.warningLevel, "%s: Illegal NVME state transition from %s to %s", (self._timestamp(time), nvmeStateTransitionTable[self.nvmeState]['name'], nvmeStateTransitionTable[newStateNumber]['name']))

        # Set new state
        self.nvmeState = newStateNumber

        # Check for time markers
        if (newStateNumber == NVME_STATE_READY): 
            self.cstsReadyTime = time
            if (self.startTime is not None):
                ttr = self.cstsReadyTime - self.startTime
                self._message(nlogTriageBase.information, "Time to ready %6.3fs", (ttr))

        self.previousNvmeUpdateEvent = stateEvent
        self.previousNvmeUpdateTime = time

    def __updateStateItem(self, machine, newstate, time, stateEvent):
        if (machine == 'pcieState'):   self.__updatePcieState(newstate, time, stateEvent)
        if (machine == 'pciCfgState'): self.__updatePciCfgState(newstate, time, stateEvent)
        if (machine == 'nvmeState'):   self.__updateNvmeState(newstate, time, stateEvent)
        if (machine == 'warning'):     self._message(nlogTriageBase.warningLevel, "%s: %s", (self._timestamp(time), newstate))
        if (machine == 'error'):       self._message(nlogTriageBase.errorLevel, "%s: %s", (self._timestamp(time), newstate))

    def __updateStateData(self, stateEvent, time):
        # Start the start time
        if(self.startTime is None): self.startTime = time

        # Get the transition entry
        transition = self.transitionMap[stateEvent]
        for machine in transition:
            self.__updateStateItem(machine, transition[machine], time, stateEvent)

    def __safeShutdown(self, seconds):
        self.eventList.append( {'state': SAFE_SHUTDOWN, 'time': seconds} )
        self.__updateStateData(SAFE_SHUTDOWN, seconds)

    def __abruptShutdown(self, seconds):
        self.eventList.append( {'state': ABRUPT_SHUTDOWN, 'time': seconds} )
        self.__updateStateData(ABRUPT_SHUTDOWN, seconds)

    def checkEvents(self):
        """
        Check the nlog tuple list for illegal PSS state transitions

        @return list of strings for issues found
        """
        # Process the list, and sort the list
        self.__resetState()
        self.eventList.sort(key = lambda x:  x['time'])

        # Clean any old messages
        self._resetMesageLog()

        for eventDict in self.eventList:
            self.__updateStateData(eventDict['state'], eventDict['time'])

        return self.messageLog

    def updateTime(self, seconds):
        if (seconds > self.lastAdjustTime): 
            adjustTime = seconds - self.lastAdjustTime
            self.lastAdjustTime = seconds
            self.__adjustTimeStamps(adjustTime)

    def addNlogEvent(self, formatStr, params, tsSeconds, coreId):
        """
        Determine if this a pss debug trace nlog entry and record the state transition 
        in the list if it is

        @param formatStr - nlog format string
        @param params - nlog associated parameter tuple
        @param tsSeconds - nlog timestamp in seconds (floating point value)
        @param coreId - Core number for the NLOG
        """
        self.hostMessage = None

        # Check for correct core and time sequence
        if ((coreId == 0) and (self.previousTs <= tsSeconds)):
            if (("PssDebugTrace" in formatStr) and (len(params) != 0)):
                self.eventList.append( {'state':params[0], 'time': tsSeconds} )
                self.__updateStateData(params[0], tsSeconds)
            elif ("Initiating safe shutdown" in formatStr):
                self.__safeShutdown(tsSeconds)
            elif ("Initiating abrupt shutdown" in formatStr):
                self.__abruptShutdown(tsSeconds)

            self.previousTs = tsSeconds

        # Return any messages generated by this event
        return self.hostMessage

