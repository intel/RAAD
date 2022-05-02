#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors:Joseph Tarango
# *****************************************************************************/
pcie = {
       0:"UNUSED_CHECKPOINT",              #Unused entry
       1:"BIS_INIT",                       #BIS structure Init (very beginning of bootloader starts) (obsolete).
       2:"PSS_RESET",                      #PSS Hardware placed in reset PERST assert ISR.
       3:"PSS_DMA_RESET_START",            #PSS DMA Engine reset start.
       4:"PSS_INIT",                       #PSS Hardware Init always the first thing called in the BL and MFW.
       5:"PSS_WARMBOOT",                   #PSS Warm boot Init.
       6:"PSS_RESET_DEASSERT",             #PSS Hardware reset deassert ISR.
       7:"PCIE_PLL_LOCK_GAIN",             #PCIe PLL Lock Gained ISR.
       8:"PCIE_LINK_TRAIN_INIT",           #PCIe Link Train Init called from PLL lock gained ISR.
       9:"PCIE_LINK_UP",                   #PCIe Link Up called from error ISR.
       10:"PCIE_PLL_LOCK_LOSS",             #PCIe PLL Lock Lost ISR.
       11:"PCIE_LINK_DOWN",                 #PCIe Link down called from error ISR.
       12:"KRNL_STRTS",                     #Kernel Starts.
       13:"DISCOVERY_STARTS",               #NAND Discovery starts (obsolete).
       14:"PMIC_SXP_OK",                    #PMIC SXP OK asserts.
       15:"DISCOVERY_SUCCESS",              #NAND Discovery successfully done.
       16:"PCI_CFG_RDY_RELEASE",            #Firmware releases PCI CFG READY.
       17:"PCI_ENABLE_OROM",                #Option ROM enabled.
       18:"PSS_INTERRUPT_VERIFICATION_WAIT",#Debug interrupt memory verification wait loop exit
       19:"PCIE_PLL_LOCK_GAIN_NOLOCK",      #Debug of PLL lock interrupt state
       20:"PSS_TIMEOVERFLOW",               #Timer overflow upper bits
       21:"PSS_RESET_REASSERT",             #PSS Hardware reset asserted again (coldBootPolled).
       22:"PSS_RESET_REASSERT1",            #PSS Hardware reset asserted again (validatePcieState).
       23:"PSS_RECOVERY_RESET",             #PSS reset recovery.
       24:"PSS_PLL_LOCK_TIMEOUT",           #PSS PLL lock timeout.
       25:"PSS_WAIT_LINK_TIMEOUT",          #PSS Wait for link timeout.
       26:"NVME_CSTS_READY",                #NVME CSTS.RDY change.
       27:"NVME_CC_ENABLE",                 #NVME CC.EN enable.
       28:"PSS_KILL_LINK",                  #PSS link kill due to PLI.
       29:"PSS_RESET_DEASSERT1",            #PSS PERST deassert called from validatePcieState routine.
       30:"PSS_WARMBOOT1",                  #PSS Warm boot path post PERST handling.
       31:"PCI_CFG_RDY_DISABLE",            #PCI configuration ready disable.
       32:"PSS_PWRON_INIT",                 #PSS NPL power on initialization function called.
       33:"PSS_ENABLE_INTERRUPT",           #PSS Enable interrupts called.
       34:"PSS_DISABLE_INTERRUPT",          #PSS Disable interrupts called.
       35:"PCI_DISABLE_OROM",               #PSS Disable OROM called.
       36:"NVME_CC_DISABLE",                #NVME CC.EN disable.
       37:"NPL_INIT",                       #NPL Iniialization called
       38:"SYSTEM_WARM_RESET_START",        #Warm Reset start of SystemHal_CpuWarmReset() routine.
       39:"SYSTEM_WARM_RESET_END",          #Warm Reset HalCpu_WarmReset() after setting input warm reset signature
       40:"PSS_NPL_NOTIFY_ACTIVE",          #NPL active notify in PSS
       41:"PSS_NPL_NOTIFY_SHUTDOWN",        #NPL shutdown notify in PSS
       42:"PSS_NPL_NOTIFY_RESET_PERST",     #NPL notify warm reset pending due to PERST in PSS
       43:"PSS_NPL_NOTIFY_RESET_LINKDOWN",  #NPL notify warm reset pending due to link down in PSS
       44:"PSS_NPL_NOTIFY_RESET_NVME",      #NPL notify warm reset pending due to NVME reset call to warm reset in PSS
       45:"PSS_NPL_NOTIFY_INIT",            #NPL notify init in PSS
       46:"SYSTEM_BL_START_COMPLETE",       #Bootloader complete
       47:"COMPRESSED_ENTRY",               #Compress entry representing link up cfg ready link down
       48:"PSS_CFG_RDY_MULTI_WR",           #Multiple writes of config ready enable bit required
       49:"PCI_FLR",                        #PCI Function level reset
       50:"PSS_TRACK_MAIN_FW_BASE",         #Must be last ENUM
}

nvmeAdminCommands = {       
     0:               "AC_DELETE_SQ",               
     1:               "AC_CREATE_SQ",               
     2:               "AC_GET_LOG_PAGE",            
     4:               "AC_DELETE_CQ",               
     5:               "AC_CREATE_CQ",               
     6:               "AC_IDENTIFY",                
     8:               "AC_ABORT",                   
     9:               "AC_SET_FEATURES",            
     10:               "AC_GET_FEATURES",            
     12:               "AC_ASYNCH_EVENT",            
     13:               "AC_NAMESPACE_MANAGEMENT",    
     16:               "AC_FW_COMMIT",               
     17:               "AC_FW_DOWNLOAD",             
     18:               "AC_CREATE_NAMESPACE",        
     19:               "AC_DELETE_NAMESPACE",        
     20:               "AC_DEVICE_SELF_TEST",        
     21:               "AC_NAMESPACE_ATTACH",        
     201:               "AC_DIRECTIVE_SEND",          
     202:               "AC_DIRECTIVE_RECEIVE",       
     129:               "AC_SECURITY_SEND",          
     128:               "AC_FORMAT",                  
     130:               "AC_SECURITY_RECEIVE",        
     194:               "AC_MCTP_GET_LOG_PAGE",       
     196:               "AC_PERFORM_SELF_TEST",       
     197:              "AC_VNDRSPECIFIC_IDENTIFY",    
     209:              "AC_VNDRSPECIFIC_NEGREAD",     
     208:              "AC_VNDRSPECIFIC_NEGWRITE",    
     210:              "AC_VNDRSPECIFIC_GETINTELLOG",   
     212:              "AC_INTEL_DRIVE_RECOVERY",     
     225:              "AC_VNDRSPECIFIC_TCWRITE",     
     226:              "AC_VNDRSPECIFIC_TCREAD",      
     227:              "AC_VNDRSPECIFIC_CLR_NS",      
     229:              "AC_DELL_GETDEVICEPCIERERGISTERS", 
     231:              "AC_DELL_GETMONITOREDATTRIBBVALUE",
     233:              "AC_DELL_SETVENDORSIMULATIONDATA", 
     232:              "AC_DELL_GETDEVICEHEALTHPOLLCHANGEDATTRIB",
     235:              "AC_DELL_GETDEVICELOGPAGE"        
}

transInitState_e = {
  0: 'SLOW_CTX_LOAD',        
  1: 'DISABLE_LOGICAL_FORCED',        
  2: 'DISABLE_LOGICAL_NO_SC',         
  3: 'FAST_CTX_LOAD',                 
  4: 'SEC_INIT_START',                
  5: 'DISABLE_LOGICAL_SEC_INIT_FAIL', 
  6: 'DISABLE_LOGICAL_NO_FC',         
  7: 'FAST_CTX_BLOB_LOAD',            
  8: 'ENABLE_LOGICAL',                 
}

transError_e = {
                                               
   0:      "enErrNone - No error encountered.",                                                                      
   1:      "enErrUndefined - The error is not yet defined, set when a function starts",
   2:      "enErrNullPointer - A valid pointer was expected",                                                               
   3:      "enErrInvalidArg - Function input argument is invalid",                                                        
   4:      "enErrNotImplemented - No interface for the protocol",                                                              
   5:      "enErrCmdIDConflict - The command ID had issues???",                                                               
   6:      "enErrHostToDmaTransfer - DMA transfer error.",                                                                        
   7:      "enErrDmaToHostTransfer - DMA transfer error.",                                                                        
   8:      "enErrRangeError",                                                                                                             
   9:      "enErrLbaCategorize",                                                                                                           
   10:     "enErrLocked - Drive is locked for the command requested.",                                                 
   11:     "enErrInvalidBuffer - Internal buffer was not available or not aligned properly.",                                 
   12:     "enErrHostTableInconsistant - Data from host and data in table are inconsistent.",                                         
   13:     "enErrInvalidHostArg - Data from host is invalid.",                                                                 
   14:     "enErrAsyncCmdLimit - Too many Async commands outstanding.",                                                       
   15:     "enErrCmdNotSent - Problem with sending the command.",                                                          
   16:     "enErrDisableLogical - Command not supported in disable logical state.",                                            
   17:     "enErrInvalidFWSlot - Invalid fw slot specified in FW activate.",                                                  
   18:     "enErrAbortCmdExceeded - Too many Abort commands received.",                                                          
   19:     "enErrAbortTimeout - Abort the command due to timeout value.",                                                    
   20:     "enErrSQDeleted - Command aborted due to submission queue deletion.",                                          
   21:     "enErrFuseFailed - Fused command failed.",                                                                      
   22:     "enErrFusedMissing - Fused command was missing something???",                                                     
   23:     "enErrInvalidNamespace - Namespace specified does not exist or not valid for this command.",                          
   24:     "enErrNamespaceIdExceeded - The number of namespaces supported has been exceeded",                                       
   25:     "enErrNamspaceNotReady - The specified namespace was not ready to accept the command.",                               
   26:     "enErrNamespaceSizeInsufficient - Exceed capacity",                                                                            
   27:     "enErrCapacityOverrun - The drive capacity was exceeded by the command.",                                            
   28:     "enErrInvalidSetting - Invalid setting for this command.",                                                          
   29:     "enErrPowerLoss - Power loss event triggered an abort.",                                                       
   30:     "enErrToSmall - LBA range too small for the Namespace.",                                                     
   31:     "enErrOverrun - LBA range too large for the Namespace.",                                                     
   32:     "enErrMaxCapOverrun - Command specific LBA range beyond max capacity.",                                            
   33:     "enErrInvalidQueueID - Invalid queue identifier specified.",                                                        
   34:     "enErrInvalidQueueSize - Queue size requested was too large.",                                                        
   35:     "enErrInvalidFormat - Format command specified an invalid format.",                                                
   36:     "enErrInvalidVector - Invalid Interrupt vector for command.",                                                      
   37:     "enErrCQInvalid - The completion queue specified for the command is invalid.",                                 
   38:     "enErrInvalidDelete - The requested queue does not exist.",                                                        
   39:     "enErrInvalidLogPage - The Log Page requested does not exist.",                                                     
   40:     "enErrAsyncLimit - Too many Asynchronous error commands were sent.",                                            
   41:     "enAbortCmdExceeded - Not enough room on the abort command queue.",                                                
   42:     "enErrInvalidFW - firmware update specified an invalid image.",                                                
   43:     "enErrTcmdLocked - Drive is locked for the test command requested.",                                            
   44:     "enErrInvalidCmdInHandler - Data Command Handler was called with an unsupported command.",                               
   45:     "enErrFWApplicationReqReset - Activate Action Completed Successfully but requires conventional reset.",                    
   46:     "enErrMctpInvalidRequest - Mctp argument is invalid.",                                                                  
   47:     "enErrMctpAttrNotConfig - Mctp poll attribute is not configured.",                                                     
   48:     "enErrAccessDenied - Access denied (TCG's SIIS specification), data protection error.",                           
   49:     "enErrCmdSeqError - synchronous protocol violation (TCG SIIS specification), command sequence error.",           
   50:     "enErrInvalidFieldinCmd - invalid field in command (invalid SP ID param, invalid Transfer Len, other invalid command)",
   51:     "enErrNamespaceAlreadyAttached - Namespace to attach has already been attached.",                                             
   52:     "enErrNamespaceNotAttached - Namespace to detach has not been attached.",                                                 
   53:     "enErrNamespaceReadOnly - Namespace is read only",                                                                     
   54:     "enErrInvalidControllerList - Controller List Invalid",                                                                    
   55:     "enErrCmdFetch - Command Fetch Error.",                                                                       
   56:     "enErrPrpFetch - PRP Fetch Error.",                                                                           
   57:     "enErrThinProvisioningNotSupported - Thin Provisioning is not supported.",                                                        
   58:     "enErrInvalidThreshold - Invalid Threshold selection",                                                                
   59:     "enErrInvalidSensor - Invalid Sensor selection",                                                                   
   60:     "enErrAborted - DMA is aborted. Host aborted all outstanding commands.",                                     
   61:     "enErrInvalidPRPOffset - PRP Entry with a non-zero offset used in Create I/O Completion/Submission Queue command",    
   62:     "enErrInvalidDirectiveType - Invalid Directive Type",                                                                     
   63:     "enErrInvalidDirectiveOperation - Invalid Directive OPeration",                                                                
   64:     "enErrFeatureIdentifierNotSaveable - Feature IdentifierNotSaveable",                                                              
   65:     "enErrFeatureNotChangeable - Feature not changeable",                                                                     
   66:     "enErrFeatureNotNamespaceSpecific - Feature not namespace specific",                                                             
   67:     "enErrOverlappingRange - Overlapping ranges",                                                                         
   68:     "enErrInvalidFWSecurityRevision - Security down revision prohibited.",                                                         
   69:     "enErrInvalidProtectionInformation - The Protection Information settings specified in the command are invalid",                   
   70:     "enErrWriteWhileReadOnly - A drive write command (WRITE_UNC, WRITE_ZEROES, WRITE_DM, WRITE) while drive is read only",  
   71:     "enErrFwActivationRequiresReset - Firmware Activation Requires Reset.",                                                        
   72:     "enErrFirmwareDisableLockBit - SMBUS Firmware Lock Bit Set to Prohibit Updates"                                            
}

pssState_e = {
   0 : "PSS_STATE_NONE",
   1 : "PSS_STATE_PERST_ASSERT_ENTER",       
   2 : "PSS_STATE_PERST_ASSERT_EXIT",       
   3 : "PSS_STATE_PERST_DEASSERT_ENTER",     
   4 : "PSS_STATE_PERST_DEASSERT_EXIT",      
   5 : "PSS_STATE_PLL_LOCK_GAINED_ENTER",    
   6 : "PSS_STATE_PLL_LOCK_GAINED_EXIT",     
   7 : "PSS_STATE_LINK_UP",                  
   8 : "PSS_STATE_LINK_DOWN_ENTER",          
   9: "PSS_STATE_LINK_DOWN_EXIT",           
   10: "PSS_STATE_PLL_LOCK_LOST_ENTER",      
   11: "PSS_STATE_PLL_LOCK_LOST_EXIT"       
} ;


specialEvents = ['MB_Trans_PCIErrorHandler', 'CSTS.RDY', 'CC.EN']
 
 
def enumParser(format, params):
    '''
    Add your nlog format to be parsed below. Make sure that when you add the
    enum-dict translation above, you create a the key as a decimal integer, and the value as a string.
    If you don't you'll get type errors
    '''
    
   
    if "PssDebugTrace" in format and len(params) != 0:
        x = pcie[params[0]]
        s = format.replace('"', '') #removes the quotes
        s = s.replace('(%d)', x) #removes params
        s = s.replace('"', '')
    elif "Npl_AdminCmdHandler: Received" in format and "AC_IDENTIFY" not in format and len(params) != 0:
        x = nvmeAdminCommands[params[0]]
        s = format.replace('"', '') #removes the quotes
        s = s.replace('0x%x', x) #removes params 
        #s =  % params #put the params in
    elif "init state is: (%d)" in format:
        x = transInitState_e[params[0]] 
        s = format.replace('"', '')
        s = s.replace('(%d)', x)
        s = s.replace('"', '')
    elif "Bis_SetTransportSubSystemState(): Changing PSS State" in format:
        x = pssState_e[params[0]]
        y = pssState_e[params[1]]
        s = format.replace('"', '')
        s = s.replace('(%d)', x)
        s = s.replace('%d', y)
        s = s.replace('"', '')
    else:
        s = format % params #put the params in
    return s
    


def enhancedPrint(firstTag, i): #attention getting format is nice to have for quick debugging.
    printPretty = False
    for x in specialEvents:
        if x in firstTag+i:
            printPretty = True
                
        
    if printPretty == True:
        print ('====================================================ATTENTION==========================================================================================================================')
        
    print (firstTag+i)
        
    if printPretty == True:
        print ('=====================================================~~~~~~~~==========================================================================================================================')





