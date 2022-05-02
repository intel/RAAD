#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
from dataclasses import dataclass
import re, sys, os, datetime, traceback, optparse, pprint, faulthandler
import numpy, pandas

##############################################
# Python generic info
##############################################
"""
Requires
"""
# .exe extension patch for the compiled version of this script
if not re.search(pattern='\.PY$|\.PYC$|\.EXE$', string=os.path.split(sys.argv[0])[1].upper()):
    sys.argv[0] = os.path.join(os.path.split(sys.argv[0])[0], os.path.split(sys.argv[0])[1] + '.exe')


@dataclass
class NPSG_ProgramData():
    def __init__(self,
                 programName: str,
                 faultCount: int,
                 discoverTime: int,
                 rootCauseTime: int,
                 solutionTime: int,
                 verificationTime: int):
        self.programName = None
        self.faultCount = None
        self.discoverTime = None
        self.rootCauseTime = None
        self.solutionTime = None
        self.verificationTime = None
        self.setAll(programName=programName,
                    faultCount=faultCount,
                    discoverTime=discoverTime,
                    rootCauseTime=rootCauseTime,
                    solutionTime=solutionTime,
                    verificationTime=verificationTime)
        return

    def setAll(self,
               programName: str = None,
               faultCount: int = None,
               discoverTime: int = None,
               rootCauseTime: int = None,
               solutionTime: int = None,
               verificationTime: int = None):

        if programName is not None:
            self.programName = programName
        if faultCount is not None:
            self.faultCount = faultCount
        if discoverTime is not None:
            self.discoverTime = discoverTime
        if rootCauseTime is not None:
            self.rootCauseTime = rootCauseTime
        if solutionTime is not None:
            self.solutionTime = solutionTime
        if verificationTime is not None:
            self.verificationTime = verificationTime
        return


class NPSG_Data():

    def __init__(self):
        # Template: NPSG_ProgramData(programName="Unknown", faultCount=0, discoverTime=0, rootCauseTime=0, solutionTime=0, verificationTime=0)
        # WorkFlow
        # Discovery: Create -> Open -> Pending
        # Root Cause: Create | Open | Pending -> In Progress
        # Root Cause/Solution: In Progress -> Implemented
        # Solution/Verified: Implemented to Close
        programs = list()
        programs.append(NPSG_ProgramData(programName="TV", faultCount=1001, discoverTime=0, rootCauseTime=0, solutionTime=2, verificationTime=15325))
        programs.append(NPSG_ProgramData(programName="FD", faultCount=0, discoverTime=0, rootCauseTime=0, solutionTime=0, verificationTime=0))
        programs.append(NPSG_ProgramData(programName="PDR", faultCount=0, discoverTime=0, rootCauseTime=0, solutionTime=0, verificationTime=0))
        programs.append(NPSG_ProgramData(programName="DV", faultCount=0, discoverTime=0, rootCauseTime=0, solutionTime=0, verificationTime=0))
        programs.append(NPSG_ProgramData(programName="CD", faultCount=0, discoverTime=0, rootCauseTime=0, solutionTime=0, verificationTime=0))
        programs.append(NPSG_ProgramData(programName="YV", faultCount=0, discoverTime=0, rootCauseTime=0, solutionTime=0, verificationTime=0))
        programs.append(NPSG_ProgramData(programName="CDR", faultCount=0, discoverTime=0, rootCauseTime=0, solutionTime=0, verificationTime=0))
        programs.append(NPSG_ProgramData(programName="GD", faultCount=0, discoverTime=0, rootCauseTime=0, solutionTime=0, verificationTime=0))
        programs.append(NPSG_ProgramData(programName="ADP", faultCount=0, discoverTime=0, rootCauseTime=0, solutionTime=0, verificationTime=0))
        programs.append(NPSG_ProgramData(programName="YVR", faultCount=0, discoverTime=0, rootCauseTime=0, solutionTime=0, verificationTime=0))
        return


@dataclass
class NASA_Data:
    def __init__(self):
        # Average Cost and Deviations Per Life Cycle
        self.decoder_LCCPS_Column = ["Average Cost", "Standard Deviation (STD)", "One Sigma (1-STD)", "Two Sigma (2-STD)"]
        self.decoder_LCCPS_Row = ["Requirements", "Design", "Build", "Test", "Operation"]

        # Life Cycle Cost Per Stage (LCCPS)
        self.dataLCCPS = [[22632.00, 31510.00, 54142.00, 85652.00],
                          [87832.00, 70191.00, 158023.00, 228214.00],
                          [354808.00, 381953.00, 736761.00, 1118714.00],
                          [1370888.00, 2638785.00, 4009673.00, 6648458.00],
                          [3558215.00, 6207917.00, 9766127.00, 15974039.00]]
        self.NASA_LifeCycleCostPerStage = numpy.array(self.dataLCCPS,
                                                      dtype=numpy.float64)
        self.NASA_LifeCycleCostPerStageDF = pandas.DataFrame(self.dataLCCPS,
                                                             index=self.decoder_LCCPS_Row,
                                                             columns=self.decoder_LCCPS_Column)

        # Life Cycle Flaws Per Stage (LCFPS)
        self.decoder_LCFPS_Column = ["All Errors", "All Errors Range Tails +/-", "STD-1", "STD-2"]
        self.dataLCFPS = [[66, 66, 57, 61],
                          [61, 61, 49, 55],
                          [41, 41, 35, 35],
                          [21, 21, 19, 20],
                          [42, 42, 36, 39]]
        self.NASA_LifeCycleFlawsPerStage = numpy.array(self.dataLCFPS,
                                                       dtype=numpy.float64)
        self.NASA_LifeCycleFlawsPerStageDF = pandas.DataFrame(self.dataLCFPS,
                                                              index=self.decoder_LCCPS_Row,
                                                              columns=self.decoder_LCFPS_Column)

        self.reference = "Haskins, Bill & Stecklein, Jonette & Dick, Brandon & Moroney, Gregory & Lovell, Randy & Dabney, James. (2004). 8.4.2 Error Cost Escalation Through the Project Life Cycle. INCOSE International Symposium. 14. 1723-1737. 10.1002/j.2334-5837.2004.tb00608.x. URL: https://ntrs.nasa.gov/api/citations/20100036670/downloads/20100036670.pdf."
        return

    def getDecoderRow(self):
        return self.decoder_LCCPS_Row

    def getDecoderCol(self):
        return self.decoder_LCCPS_Column

    def getLCCPS(self):
        return self.NASA_LifeCycleCostPerStage

    def getLCFPS(self):
        return self.NASA_LifeCycleFlawsPerStage


class FaultCostModelForReturnOnInvestment(object):

    def __init__(self):
        # Average Cost and Deviations Per Life Cycle
        self.Decoder_ROW = NASA_Data().getDecoderRow()
        self.Decoder_COL = NASA_Data().getDecoderCol()
        # Life Cycle Cost Per Stage (LCCPS)
        self.LifeCycleCostPerStage = NASA_Data().getLCCPS()
        # Life Cycle Flaws Per Stage (LCFPS)
        self.LifeCycleFlawsPerStage = NASA_Data().getLCFPS()
        return

    def LCCPS_CostTotal(self):
        LCPFS_Column_Sum = self.LifeCycleCostPerStage.sum(axis=0)
        return LCPFS_Column_Sum

    def LCCPS_CostMean(self, phaseOrClassOrModel: str = "estimationClass"):
        if phaseOrClassOrModel in ["productPhase", "estimationClass"] is False:
            return None

        if phaseOrClassOrModel == "estimationClass":
            # Column means
            LCPFS_Mean = self.LifeCycleCostPerStage.mean(axis=0)
        else:
            # Row Mean
            LCPFS_Mean = self.LifeCycleCostPerStage.mean(axis=1)

        return LCPFS_Mean

    def LCFPS_Percentage(self):
        # Column Sum
        LCPFS_Column_Sum = self.LifeCycleFlawsPerStage.sum(axis=0)
        LCFPS_Percentage = self.LifeCycleFlawsPerStage / LCPFS_Column_Sum
        return LCFPS_Percentage

    def Cost_Estimation_Model_Normalized(self, totalFaultCount):
        modelPercentages = self.LCFPS_Percentage()
        matrixRows, matrixCols = self.LifeCycleCostPerStage.shape
        matrixROI = numpy.full(shape=(matrixRows, matrixCols), fill_value=0.0, dtype=numpy.float64)
        for idxRows in range(matrixRows):
            for idxCols in range(matrixCols):
                percentageElement = modelPercentages[idxRows][idxCols]
                avgItem = percentageElement * totalFaultCount
                LCCPSItem = self.LifeCycleCostPerStage[idxRows][idxCols]
                matrixROI[idxRows][idxCols] = avgItem * LCCPSItem
        return matrixROI

    @staticmethod
    def getMinMaxInColOrRow(inputMatrix=None, colOrRow: str = "row", minOrMax: str = "max"):
        findResults = None
        findLocations = None

        # Error in usage of API
        if (inputMatrix is None) or \
                (isinstance(inputMatrix, numpy.ndarray) is False) or \
                ((colOrRow in ["col", "row"]) is False) or \
                ((minOrMax in ["max", "min"]) is False):
            return (findResults, findLocations)

        # Select columns or rows
        if colOrRow == "col":
            findAxis = 0
        else:
            findAxis = 1

        # Select min or max
        if minOrMax == "min":
            findFunction = numpy.amin
        else:
            findFunction = numpy.amax

        # Find min or max in column or row
        findResults = findFunction(inputMatrix, axis=findAxis)

        #  Get the indices of element in numpy array
        findLocations = numpy.where(inputMatrix == findResults)

        return (findResults, findLocations)

    def Cost_Estimation_Model_Bounds(self, totalFaultCount: int, boundType: str = "upper", phaseOrClassOrModel: str = "estimationClass"):

        """

        Defintions:
            upper is the computer science usage or Big-Oh 'O' or upper bound or worst case.
            normal is the computer science usage of Theta 'θ' of the average case, which is not defined in this usage.
            lower is the computer science usage or Omega 'Ω' or lower bound or best case.
            product phase is the stage in the product life cycle as defined in NASA_Decoder_COL.
            estimation class is the average, or standard deviation selected in NASA_Decoder_ROW.

        Args:
            totalFaultCount:
            boundType:
            phaseOrClassOrModel:

        Returns:

        """

        totalCost = None

        # Error in usage of API
        if ((boundType in ["lower", "upper"]) is False) or ((phaseOrClassOrModel in ["productPhase", "estimationClass", "normalModel"]) is False):
            return totalCost

        if boundType == "lower":
            minOrMax = "min"
        else:  # upper
            minOrMax = "max"

        if phaseOrClassOrModel == "productPhase":
            colOrRow = "row"
        else:  # estimationClass
            colOrRow = "col"

        if phaseOrClassOrModel == "normalModel":
            totalMatrixFound = self.LCCPS_CostMean()
        else:
            totalMatrixFound = self.getMinMaxInColOrRow(inputMatrix=self.LifeCycleCostPerStage, colOrRow=colOrRow, minOrMax=minOrMax)

        totalCost = totalMatrixFound * totalFaultCount
        return totalCost


def main_estimator(options, args):
    if options.debug:
        print("Options:")
        pprint.pprint(options)
        print("Args:")
        pprint.pprint(args)

    totalFaultCount = 102
    boundTypeList = ["upper", "normalModel", "lower"]
    phaseOrClassOrModelList = ["productPhase", "estimationClass", "normalModel"]
    NSGModel = FaultCostModelForReturnOnInvestment()

    resultants = list()
    for idxBTL, itemBTL in enumerate(boundTypeList):
        for idxPML, itemPML in enumerate(phaseOrClassOrModelList):
            cName = f"{str(itemBTL)}-{str(itemPML)}"
            cResult = NSGModel.Cost_Estimation_Model_Bounds(totalFaultCount=totalFaultCount, boundType=itemBTL, phaseOrClassOrModel=itemPML)
            resultants.append([cName, cResult])

    cName = f"model-normalized"
    cResult = NSGModel.Cost_Estimation_Model_Normalized(totalFaultCount)
    resultants.append([cName, cResult])
    if options.debug:
        print(f"{pprint.pformat(resultants)}")
    return


##############################################
# Libraries
##############################################

def main():
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--example", action='store_true', dest='example', default=False,
                      help='Show command execution example.')
    parser.add_option("--debug", action='store_true', dest='debug', default=False, help='Debug mode.')
    parser.add_option("--more", dest='more', default=False, help="Displays more options.")
    parser.add_option("--verbose", action='store_true', dest='verbose', default=False, help='Verbose printing for debug use.')
    parser.add_option("--faultSave", dest='faultSave', default=False, help="Enable fault context save for debug.")
    (options, args) = parser.parse_args()

    if options.faultSave:
        faultFolder = "../data/output/faultContext"
        os.makedirs(faultFolder, mode=0o777, exist_ok=True)
        faultFolder = os.path.abspath(faultFolder)
        faultFile = "fault.dump"
        faultLocation = os.path.abspath(os.path.join(faultFolder, faultFile))
        segfaultFile = open(faultLocation, 'w+')
        faulthandler.enable(file=segfaultFile, all_threads=True)
    else:
        segfaultFile = None
    try:
        main_estimator(options=options, args=args)
    except Exception as e:
        print("Fail End Process: ", e)
        traceback.print_exc()
        if options.faultSave:
            faulthandler.dump_traceback(file=segfaultFile, all_threads=True)
    finally:
        if options.faultSave:
            faulthandler.disable()
            segfaultFile.close()
        print("exiting RAAD.")

    return 0


# Main Execute
if __name__ == '__main__':
    p = datetime.datetime.now()
    main()
    q = datetime.datetime.now()
    print("Execution time: " + str(q - p))
