#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
# @package reportGenerator
from __future__ import annotations
import optparse, datetime, traceback, pprint, os, pylatex, numpy, random, difflib, copy, tempfile, sys, re, typing, \
    platform, subprocess
from collections import OrderedDict
import pylatex
from pylatex import escape_latex, NoEscape, NewLine, NewPage, Document, Section, Subsection, Tabular, Math, TikZ, Axis, \
    Plot, Figure, Matrix, Alignat
from pylatex.utils import italic
import ast

from software.utilsCommon import tryFile, tryFolder, DictionaryFlatten
from software.debug import whoami


class ReportGenerator():
    """
    Report generation in LaTeX to PDF.
    """
    # @todo add description for each section
    debug = True
    geometry_options = None
    pendingDocument = None
    customerPage = None
    codeBranchPage = None

    timeToken = None
    outPath = None
    savePath = None
    fileName = None
    logoImage = None
    firstPage = None
    titleInfo = None
    teamName = None
    authorName = None
    specificationName = None
    specificationVersion = None
    supportedProductList = None
    reportVersion = None
    customerName = None
    userName = None
    productName = None
    modelName = None
    productStatus = None
    productSerial = None
    firmwareName = None
    collectionTypes = None

    def __init__(self,
                 outPath=None,
                 fileName=None,
                 logoImage=None,
                 debug: bool = True):
        """
        Setup of report generation.
        Args:
            outPath: Path to create/save.
            fileName: Desired file name.
            logoImage: Desired logo to be added to the report.
            debug: Developer debug flag.
        """
        self.setDebug(status=debug)
        self.setInitialize(outPath=outPath,
                           fileName=fileName,
                           logoImage=logoImage)
        return

    def setDebug(self, status: bool = True):
        """
        Set debug status of class.
        Args:
            status: flag to enable and disable debug status.

        Returns: Void

        """
        self.debug = status
        return

    def setInitialize(self,
                      outPath=None,
                      fileName=None,
                      logoImage=None):
        """
        Setup of the class configuration basis.
        Args:
            outPath: Path to create/save.
            fileName: Desired file name.
            logoImage: Desired logo to be added to the report.

        Returns: Void

        """

        if outPath is None:
            self.outPath = '.'
        else:
            self.outPath = outPath

        if fileName is None:
            self.fileName = 'report',
        else:
            self.fileName = fileName

        if logoImage is None:
            self.logoImage = 'Intel_IntelligentSystems.png'
        else:
            self.logoImage = logoImage

        self.setGeometry()

        # Modify document
        self.pendingDocument = pylatex.Document(geometry_options=self.geometry_options)
        return

    def setGeometry(self, head=None, margin=None, bottom=None, includeheadfoot=None):
        """
        Set the page layout to target for PDF/printing.
        Args:
            head: Header of file setup.
            margin: Page margin.
            bottom: Page bottom margin.
            includeheadfoot: Add header/footer.

        Returns: Void

        """
        if head is None:
            head = "140pt"
        if margin is None:
            margin = "0.5in"
        if bottom is None:
            bottom = "0.6in"
        if includeheadfoot is None:
            includeheadfoot = True
        self.geometry_options = {
            "head": head,
            "margin": margin,
            "bottom": bottom,
            "includeheadfoot": includeheadfoot
        }
        return

    @staticmethod
    def getLiteral(varObj):
        varName = [k for k, v in locals().items() if v == varObj][0]
        return varName

    def _dict2BulletList(self,
                         elements=None,
                         level: int = 1,
                         indent_size: int = 4,
                         spaceOrTab: bool = True,
                         addNewLine: bool = True,
                         retSpaceValue: bool = True):
        """
        Recursive basis method to traverse a dictionary, list, set, basic type to create a tab based index and individual item list.
        Args:
            elements: traversing dictionary
            level: level variable for recursive indentition
            indent_size: size of indent in spaces
            spaceOrTab: Flag to use spaces or tabs.
            addNewLine: Add new line to delimited item.
            retSpaceValue: Flag to return space values.

        Returns: Formatted tupple with tab/spaces indicated.
        """
        if elements is None:
            return elements

        if spaceOrTab is True:
            spacesValue = (indent_size * level)
            spaceToken = ' ' * (indent_size * level)
        else:
            spacesValue = level
            spaceToken = '\t' * (level)

        if addNewLine is True:
            cNewLine = f'{os.linesep}'
        else:
            cNewLine = ''

        try:
            # Baseline types
            if isinstance(elements, (bool, int, float, complex, str)):
                elementName = self.getLiteral(elements)
                elementValue = str(elements)
                items = '='.join([elementName, elementValue])
            else:
                # Assumes is a dictionary or list
                items = elements.items()
        except AttributeError:
            for bullet_point in elements:
                if retSpaceValue:
                    yield f'{spaceToken} {bullet_point}{cNewLine}', spacesValue
                else:
                    yield f'{spaceToken} {bullet_point}{cNewLine}'
        else:
            if isinstance(elements, (bool, int, float, complex, str)):
                if retSpaceValue:
                    yield f'{spaceToken} {items}', spacesValue
                else:
                    yield f'{spaceToken} {items}'
            else:
                for bullet_point, sub_points in items:
                    if isinstance(sub_points, (list, set, dict, OrderedDict)):
                        if retSpaceValue:
                            yield f'{spaceToken} {bullet_point} {cNewLine}', spacesValue
                        else:
                            yield f'{spaceToken} {bullet_point} {cNewLine}'
                        yield from self._dict2BulletList(elements=sub_points,
                                                         level=(level + 1),
                                                         indent_size=indent_size,
                                                         spaceOrTab=spaceOrTab,
                                                         addNewLine=addNewLine,
                                                         retSpaceValue=retSpaceValue)
                    else:
                        if retSpaceValue:
                            yield f'{spaceToken} {bullet_point} := {str(sub_points)}{cNewLine}', spacesValue
                        else:
                            yield f'{spaceToken} {bullet_point} := {str(sub_points)}{cNewLine}'
        return

    def dict2BulletList(self,
                        elements=None,
                        level: int = 1,
                        indent_size: int = 4,
                        spaceOrTab: bool = True,
                        addNewLine: bool = True,
                        retSpaceValue: bool = True):
        """
        Recursive method to traverse a dictionary, list, set, basic type to create a tab based index and individual item list.
        Args:
            elements: traversing dictionary
            level: level variable for recursive indentition
            indent_size: size of indent in spaces
            spaceOrTab: Flag to use spaces or tabs.
            addNewLine: Add new line to delimited item.
            retSpaceValue: Flag to return space values.

        Returns: Formatted tupple with tab/spaces indicated.
        """
        if elements is None:
            return elements

        blItems = list()
        fItems = self._dict2BulletList(elements=elements,
                                       level=level,
                                       indent_size=indent_size,
                                       spaceOrTab=spaceOrTab,
                                       addNewLine=addNewLine,
                                       retSpaceValue=retSpaceValue)
        for line in fItems:
            # if self.debug:
            #    print(line)
            blItems.append(line)
        return blItems

    def extractFiles(self, inTokens, fileType: str = '.pdf'):
        """
        Function to traverse a dictionary and capture the key and values related to PDF or a given file type.
        Args:
            inTokens: dictionary, list, set, or string
            fileType: File extension to detect.

        Returns: dictionary of found items with file type.
        """
        dictTokens = dict()
        pdfList = list()
        if isinstance(inTokens, dict) or isinstance(inTokens, OrderedDict):
            for keyST, valueST in inTokens.items():
                pdfList = self.extractFiles(inTokens=valueST)
                if pdfList is not None and pdfList != list():
                    dictTokens[keyST] = pdfList
            if dictTokens is not None and dictTokens != dict():
                pdfList = dictTokens
            else:
                pdfList = None
        elif isinstance(inTokens, list) or isinstance(inTokens, set):
            for valueST in inTokens:
                if isinstance(valueST, str) and valueST.endswith(fileType) and os.path.exists(valueST):
                    pdfList.append(valueST)
            if pdfList == list():
                pdfList = None
        elif isinstance(inTokens, str):
            if isinstance(inTokens, str) and inTokens.endswith(fileType) and os.path.exists(inTokens):
                pdfList.append(inTokens)
            if pdfList == list():
                pdfList = None
        else:
            pdfList = None
        return pdfList

    def addCustomCommandText(self, candidateString: str):
        if candidateString is None:
            candidateString = r"\noindent\rule{\textwidth}{1pt}"
        self.pendingDocument.append(NoEscape(candidateString))
        return

    def addCustomlineText(self, candidateString: str):
        stringModification = rf'\\hspace{{1mm}} {candidateString} \\'
        self.addCustomCommandText(candidateString=stringModification)
        return

    def createDocumentRAAD(self, systemInfo=None):
        """
        Documentation creation module to streamline all components.
        Returns:Void
        """
        # @todo Please note order is important. Only step 4 can be re-arranged.
        # Step 0: Pop the jiraMining section from systemInfo for later processing
        if 'Machine Learning Expert Analysis' in systemInfo:
            if 'Jira Similarity Analysis and Clustering' in systemInfo['Machine Learning Expert Analysis']:
                jiraMeta = systemInfo['Machine Learning Expert Analysis'][
                    'Jira Similarity Analysis and Clustering'].pop('Data-mining for Jiras')
            else:
                jiraMeta = None

            if 'NLOG Event Summary' in systemInfo['Machine Learning Expert Analysis']:
                nlogMeta = systemInfo['Machine Learning Expert Analysis']['NLOG Event Summary'].pop('Nlog Table')
            else:
                nlogMeta = None
        else:
            jiraMeta = None
            nlogMeta = None

        # Step 1: Prepare
        self.updateTimeStamp()
        self.setGeometry()
        self.pendingDocument = pylatex.Document(geometry_options=self.geometry_options)
        self.pendingDocument.packages.append(pylatex.package.Package('hyperref'))
        ####################################################################################
        # Step 2: Cover information, Generating first page style
        self.updateCover()
        ####################################################################################
        # Step 3: Customer information and Basic data
        status = None
        if 'Time Series' in systemInfo:
            if 'Device Signature' in systemInfo['Time Series']:
                if 'failureModeString' in systemInfo['Time Series']['Device Signature']:
                    status = systemInfo['Time Series']['Device Signature']['failureModeString']
                    self.productStatus = status
        self.updateCustomerInformation(productStatus=status)
        ####################################################################################
        # Step 4a: Add sections list
        tableOfContentsString = '\\tableofcontents'
        self.pendingDocument.append(pylatex.utils.NoEscape(tableOfContentsString))

        self.pendingDocument.append(pylatex.section.Chapter('Extracted Data'))
        systemTokens = self.dict2BulletList(elements=systemInfo, level=0)
        PDFTrackingList = list()
        uidcnt = 0
        for lineItem, spacesValue in systemTokens:
            if spacesValue is not None:
                imageTokens = ('.pdf' in str(lineItem))
                if not imageTokens:
                    if PDFTrackingList != list():
                        if len(PDFTrackingList) > 1:
                            rowWidth = 2
                        else:
                            rowWidth = 1
                        figTableComplex, figRowsComplex, figHeaderStringComplex = self.addPDFImagesRows(
                            inFigureList=PDFTrackingList, rowWidth=rowWidth)
                        if figTableComplex is not None:
                            with self.pendingDocument.create(
                                    pylatex.LongTabu(figHeaderStringComplex)) as dataTableComplex:
                                for _, item in enumerate(figTableComplex):
                                    dataTableComplex.add_row(item)
                        PDFTrackingList = list()
                    hTxt = str(spacesValue) + "mm"
                    hsObj = pylatex.HorizontalSpace(hTxt)
                    self.pendingDocument.append(hsObj)

                    ignoreToken = (':=' not in str(lineItem))
                    if (spacesValue == 0) and ignoreToken:
                        safeLineItem = pylatex.utils.escape_latex(lineItem.strip())
                        self.pendingDocument.append(pylatex.section.Section(safeLineItem))
                    elif (spacesValue == 4) and ignoreToken:
                        safeLineItem = pylatex.utils.escape_latex(lineItem.strip())
                        self.pendingDocument.append(pylatex.section.Subsection(safeLineItem))
                    elif (spacesValue == 8) and ignoreToken:
                        safeLineItem = pylatex.utils.escape_latex(lineItem.strip())
                        self.pendingDocument.append(pylatex.section.Subsubsection(safeLineItem))
                    else:
                        safeLineItem = pylatex.utils.escape_latex(lineItem)
                        self.pendingDocument.append(safeLineItem)
                elif imageTokens:
                    cleanLineItem = lineItem.replace('\n', '')
                    PDFItem = cleanLineItem.replace(' ', '')
                    PDFTrackingList.append(PDFItem)
        self.pendingDocument.append(pylatex.NewPage())
        ####################################################################################
        # Step 4b: bAdd list
        # self.pendingDocument.append(pylatex.Section('Meta Data List(s)'))
        # systemTokens = self.dict2BulletList(elements=systemInfo,
        #                                    spaceOrTab=True,
        #                                    addNewLine=True,
        #                                    retSpaceValue=False)
        # enumListObj = self.addEnumerateList(enumStrList=systemTokens)
        # self.pendingDocument.append(enumListObj)
        # self.pendingDocument.append(pylatex.NewPage())
        ####################################################################################
        #  Generate Meta Images
        ####################################################################################
        # Step 4c: Add images
        # pdfList = self.extractFiles(inTokens=systemInfo, fileType='.pdf')
        # if isinstance(pdfList, dict):
        #    pdfList = DictionaryFlatten().getFlattenDictionary(dd=pdfList, separator=' - ', prefix='')
        # if pdfList is not None:
        #    for sKey, sValue in pdfList.items():
        #        figTableComplex, figRowsComplex, figHeaderStringComplex = self.addPDFImagesRows(inFigureList=sValue, rowWidth=2)
        #        if figTableComplex is not None:
        #            self.pendingDocument.append(' '.join(['Figure(s)', sKey]))
        #            self.pendingDocument.append(NewLine())
        #            with self.pendingDocument.create(pylatex.LongTabu(figHeaderStringComplex)) as dataTableComplex:
        #                for _, item in enumerate(figTableComplex):
        #                    dataTableComplex.add_row(item)
        ####################################################################################
        # Step 4d: Matrix mathematics, Generate Meta Data Tables
        # self.pendingDocument.append('Meta Matrix Data Table(s)')
        # mathObj = self.addMathMatrix(arrayMatrix=None, arrayMatrixLabel=None)
        # self.pendingDocument.append(mathObj)
        ####################################################################################
        # Step 4e: Populate Jira Tables and list of pdf figures
        if jiraMeta is not None:
            # find the index of the jira section, and insert data below
            match = pylatex.section.Subsection(pylatex.utils.NoEscape('Jira Similarity Analysis and Clustering'))
            size = len(self.pendingDocument.data)
            foundAt = size
            for i in range(size - 1, 0, -1):
                try:
                    if self.pendingDocument[i] == match:
                        if self.pendingDocument[i].title == match.title:
                            foundAt = i
                            break
                except Exception as e:
                    pass
            foundAt = foundAt + 3
            self.pendingDocument.insert(foundAt, '\n')
            foundAt += 1
            for k, v in jiraMeta['Nearest Neighbor Set Per Jira'].items():
                # todo @rmace001: need to have default org jira rootURL and add as input parameter
                # convert Jira IDs to hyperlinks
                for row in v:
                    for j in range(len(row) - 1):
                        row[j] = self.hyperlink(url='https://nsg-jira.intel.com/browse/' + row[j], text=row[j])

                tblName, tblObj = self.addMetaTable(
                    tableName=jiraMeta['Known Cause Table Titles'][k],
                    tableLayout="X[l] X[l] X[l] X[l] X[l]",
                    tableMeta=v,
                    tableHeader=["JIRA ID",
                                 "Nearest Neighbor 1",
                                 "Nearest Neighbor 2",
                                 "Nearest Neighbor 3",
                                 "Weighted Log Probability",
                                 ],
                    row_height=1.5
                )
                self.pendingDocument.insert(foundAt, tblName)
                foundAt += 1
                self.pendingDocument.insert(foundAt, tblObj)
                foundAt += 1
            jiraFigures = self.addImagesRows(inFigureList=jiraMeta['Jira Cluster Figures'],
                                             image_options=["width=270px"])
            self.pendingDocument.insert(foundAt, 'Jira Cluster Groupings')
            foundAt += 1
            self.pendingDocument.insert(foundAt, jiraFigures[0])

        ####################################################################################
        # Step 4f: Populate NLOG table
        if nlogMeta is not None:
            match = pylatex.section.Subsection(pylatex.utils.NoEscape('NLOG Event Summary'))
            size = len(self.pendingDocument.data)
            foundAt = size
            for i in range(size - 1, 0, -1):
                try:
                    if self.pendingDocument[i] == match:
                        if self.pendingDocument[i].title == match.title:
                            foundAt = i
                            break
                except Exception as e:
                    print(f"{e}{os.linesep}{pprint.pformat(whoami())}")
                    pass
            foundAt = foundAt + 3
            self.pendingDocument.insert(foundAt, '\n')
            foundAt += 1
            tblNameNlog, tblObjNlog = self.addMetaTable(
                tableName='Nlog output from telemetry_nlog parsing Version: 3.40',
                tableLayout="X[l] X[l] X[l] X[l] ",
                tableMeta=nlogMeta,
                tableHeader=["Time(H:M:S)",
                             "Core",
                             "(NLog)",
                             "Event"
                             ],
                row_height=1.5
            )
            self.pendingDocument.insert(foundAt, tblNameNlog)
            foundAt += 1
            self.pendingDocument.insert(foundAt, tblObjNlog)

        ####################################################################################
        # Step 5: Save data
        ####################################################################################
        self.outPath = tryFolder(self.outPath)
        self.createFilePath(self.outPath)
        savePath = os.path.join(self.outPath, self.fileName)
        self.savePath = savePath
        print(f"Report location: {str(self.savePath)} with *.tex or *.pdf")

        platformType = platform.system()
        architectureType = ('64' in platform.machine())
        if platformType.upper() == 'Linux':
            compilerLocation = '/usr/bin/pdflatex'
        elif platformType == 'Windows':
            if architectureType is True:
                compilerLocation = os.path.abspath(r'C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe')
            else:
                compilerLocation = os.path.abspath(r'C:\Program Files\MiKTeX\miktex\bin\pdflatex.exe')
            AssertionError((os.path.exists(compilerLocation)), f"Error non-supported OS {compilerLocation} {whoami()}")
        else:
            compilerLocation = 'pdflatex'
            AssertionError((platformType not in ['Windows', 'Linux']),
                           f"Error non-supported OS {compilerLocation}, {whoami()}")
        if platformType.upper() == 'Linux':
            self.pendingDocument.generate_tex(filepath=savePath)
            command = [compilerLocation] + ['--interaction=nonstopmode'] + \
                      ['-output-directory=' + self.outPath] + [savePath + '.tex']

            for i in range(2):
                try:
                    subprocess.run(command, timeout=5, capture_output=True)
                except:
                    print("Compilation command not executed properly")
                    continue

        else:
            self.pendingDocument.generate_tex(filepath=savePath)
            command = [compilerLocation] + ['--interaction=nonstopmode'] + \
                      ['-output-directory=' + self.outPath] + [savePath + '.tex']

            for i in range(2):
                try:
                    subprocess.run(command, timeout=5, capture_output=True)
                except:
                    print("Compilation command not executed properly")
                    continue

        if not os.path.exists(savePath + '.pdf'):
            command = [compilerLocation] + [savePath + '.tex']
            for i in range(2):
                try:
                    subprocess.check_output(command, timeout=5)
                except:
                    continue
        return

    def createDocumentRAAD_Backup(self, systemInfo=None):
        """
        Documentation creation module to streamline all components.
        Returns:Void
        """
        # @todo Please note order is important. Only step 4 can be re-arranged.
        # Step 1: Prepare
        self.updateTimeStamp()
        self.setGeometry()
        self.pendingDocument = pylatex.Document(geometry_options=self.geometry_options)
        ####################################################################################
        # Step 2: Cover information, Generating first page style
        self.updateCover()
        ####################################################################################
        # Step 3: Customer information and Basic data
        self.updateCustomerInformation()
        ####################################################################################
        # Step 4a: Add section list
        self.pendingDocument.append(pylatex.section.Chapter('Dictionary Data(s)'))
        systemTokens = self.dict2BulletList(elements=systemInfo)
        # self.pendingDocument.create(pylatex.MediumText())
        for lineItem, spacesValue in systemTokens:
            if spacesValue is not None:
                hTxt = str(spacesValue) + "mm"
                hsObj = pylatex.HorizontalSpace(hTxt)
                self.pendingDocument.append(hsObj)
            safeLineItem = pylatex.utils.escape_latex(lineItem)
            self.pendingDocument.append(safeLineItem)
        self.pendingDocument.append(pylatex.NewPage())
        ####################################################################################
        # Step 4b: bAdd list
        # self.pendingDocument.append(pylatex.Section('Meta Data List(s)'))
        # systemTokens = self.dict2BulletList(elements=systemInfo,
        #                                    spaceOrTab=True,
        #                                    addNewLine=True,
        #                                    retSpaceValue=False)
        # enumListObj = self.addEnumerateList(enumStrList=systemTokens)
        # self.pendingDocument.append(enumListObj)
        # self.pendingDocument.append(pylatex.NewPage())
        ####################################################################################
        #  Generate Meta Images
        ####################################################################################
        # Step 4c: Add images
        # self.pendingDocument.append('Figure(s)')
        # self.addPDFImages(inFigureList=None)
        # self.addPDFImagesRows(inFigureList=None, rowWidth=1)
        ####################################################################################
        # Step 4d: Matrix mathematics, Generate Meta Data Tables
        # self.pendingDocument.append('Meta Matrix Data Table(s)')
        # mathObj = self.addMathMatrix(arrayMatrix=None, arrayMatrixLabel=None)
        # self.pendingDocument.append(mathObj)
        ####################################################################################
        # Step 5: Save data
        ####################################################################################
        self.outPath = tryFolder(self.outPath)
        self.createFilePath(self.outPath)
        savePath = os.path.join(self.outPath, self.fileName)
        self.savePath = savePath
        print(f"Report location: {str(self.savePath)}")
        self.pendingDocument.generate_pdf(filepath=savePath, clean=False, clean_tex=False, silent=False,
                                          compiler='latexmk', compiler_args=['--v'])
        # self.pendingDocument.generate_pdf(filepath=savePath, clean=False, clean_tex=False, silent=False, compiler_args=["--f", "--v"])
        # self.pendingDocument.generate_pdf(filepath=savePath, clean_tex=False, clean=True, compiler_args=["--f", "--v"])

        return

    def createDocument(self):
        """
        Documentation creation module to streamline all components.
        Returns:Void
        """
        self.setGeometry()
        self.pendingDocument = pylatex.Document(geometry_options=self.geometry_options)
        self.updateTimeStamp()
        ####################################################################################
        # Cover information
        self.updateCover()
        ####################################################################################
        # Customer information and Basic data
        self.updateCustomerInformation()
        ####################################################################################
        # Add list
        self.pendingDocument.append('Meta Data List(s)')
        self.addEnumerateList(enumStrList=None)
        self.pendingDocument.append(pylatex.NewPage())
        ####################################################################################
        #  Generate Meta Images
        ####################################################################################
        # Add images
        self.pendingDocument.append('Figure(s)')
        self.addPDFImages(inFigureList=None)
        self.addPDFImagesRows(inFigureList=None, rowWidth=1)
        ####################################################################################
        # Matrix mathematics, Generate Meta Data Tables
        self.pendingDocument.append('Meta Matrix Data Table(s)')
        mathObj = self.addMathMatrix(arrayMatrix=None, arrayMatrixLabel=None)
        self.pendingDocument.append(mathObj)
        ####################################################################################
        # Save data
        ####################################################################################
        self.createFilePath(self.outPath)
        savePath = os.path.join(self.outPath, self.fileName)
        self.savePath = savePath
        self.pendingDocument.generate_pdf(filepath=savePath, clean_tex=False)
        return

    def updateTimeStamp(self, inTime=None):
        """
        Time stamp update or set for document.
        Args:
            inTime: date time desired to be set.

        Returns: Void

        """
        if inTime is None:
            self.timeToken = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f")
        else:
            self.timeToken = inTime
        return

    def updateCover(self,
                    titleInfo=None,
                    teamName=None,
                    authorName=None,
                    specificationName=None,
                    specificationVersion=None,
                    supportedProductList=None,
                    reportVersion=None):

        """
        Cover template for the report.
        Args:
            titleInfo: Title to be presented.
            teamName: Team name used in the gather process.
            authorName: Author of report generation.
            specificationName: System specification and name.
            specificationVersion: Verion number of specification.
            supportedProductList: Product list within report or supported.
            reportVersion: Report module version.

        Returns: Void

        """

        # Data token updates
        if (titleInfo is None) or (self.titleInfo is None):
            self.titleInfo = "Rapid Automated-Analysis for Developers (RAAD) - Report"
        else:
            self.titleInfo = titleInfo

        if (teamName is None) or self.teamName is None:
            self.teamName = (f"Team: " + "RAMP")
        else:
            self.teamName = teamName

        if (authorName is None) or self.authorName is None:
            self.authorName = (f"PI: " + "Joseph Tarango")
        else:
            self.authorName = authorName

        if (specificationName is None) or self.specificationName is None:
            self.specificationName = (f"Specification: " + "Telemetry")
        else:
            self.specificationName = specificationName

        if (specificationVersion is None) or self.specificationVersion is None:
            self.specificationVersion = (f"Version: " + "2.0")
        else:
            self.specificationVersion = specificationVersion

        if (supportedProductList is None) or self.supportedProductList is None:
            self.supportedProductList = (f"HR, ADP, YVR")
        else:
            self.supportedProductList = supportedProductList

        if (reportVersion is None) or (self.reportVersion is None):
            self.reportVersion = (f"Version: " + "Alpha" + "1.0")
        else:
            self.reportVersion = reportVersion

        # Create first page object
        self.firstPage = pylatex.PageStyle("firstPage")

        # Header image
        with self.firstPage.create(pylatex.Head("L")) as header_left:
            with header_left.create(pylatex.MiniPage(pos='c')) as logo_wrapper:
                logo_file = self.logoImage
                logo_file = os.path.abspath(logo_file)
                logo_wrapper.append(pylatex.StandAloneGraphic(image_options="width=60px", filename=logo_file))

        # Add document title
        with self.firstPage.create(pylatex.Head("R")) as right_header:
            with right_header.create(pylatex.MiniPage(pos='c', align='r')) as title_wrapper:
                title_wrapper.append(pylatex.LargeText(pylatex.utils.bold(self.titleInfo)))
                title_wrapper.append(pylatex.LineBreak())
                title_wrapper.append(pylatex.MediumText(pylatex.utils.bold(self.timeToken)))

        # Add footer
        with self.firstPage.create(pylatex.Foot("C")) as footer:
            message = "Technical Message"
            with footer.create(pylatex.Tabularx("X X X X")) as footer_table:
                footer_table.add_row([pylatex.MultiColumn(4, align='l', data=pylatex.TextColor("blue", message))])
                footer_table.add_hline(color="blue")
                footer_table.add_empty_row()

                teamInfo = pylatex.MiniPage(pos='t')
                teamInfo.append(self.teamName)  # Rapid Automated Machine Programming
                teamInfo.append("\n")
                teamInfo.append(self.authorName)  # Principal Investigator

                internalSpec = pylatex.MiniPage(pos='t')
                internalSpec.append(self.specificationName)
                internalSpec.append("\n")
                internalSpec.append(self.specificationVersion)

                internalProducts = pylatex.MiniPage(pos='t')
                internalProducts.append("Supported Products: ")
                internalProducts.append("\n")
                internalProducts.append(self.supportedProductList)

                document_details = pylatex.MiniPage(pos='t')
                document_details.append("Version: Alpha 1.0")
                document_details.append(pylatex.LineBreak())
                document_details.append(pylatex.simple_page_number())

                footer_table.add_row([teamInfo, internalSpec, internalProducts, document_details])
        # Add cover to document
        self.pendingDocument.preamble.append(self.firstPage)
        return

    def updateCustomerInformation(self,
                                  customerName=None,
                                  userName=None,
                                  productName=None,
                                  modelName=None,
                                  productStatus=None,
                                  productSerial=None,
                                  firmwareName=None,
                                  collectionTypes=None):
        """
        Customer template information setup.
        Args:
            customerName: Customer name
            userName: Interface user name.
            productName: Product name used.
            modelName: Product model used.
            productStatus: Product status.
            productSerial: Identifier of the product.
            firmwareName: Firmware used in extraction.
            collectionTypes: Collection set to be used for analysis, regression, and forcasting.

        Returns: Void.

        """

        if (customerName is None) or (self.customerName is None):
            self.customerName = (f"Customer: Internal Research")
        else:
            self.customerName = customerName

        if (userName is None) or (self.userName is None):
            self.userName = (f"User: Tester")
        else:
            self.userName = userName

        if (productName is None) or (self.productName is None):
            self.productName = (f"Product: ADP")
        else:
            self.productName = productName

        if (modelName is None) or (self.modelName is None):
            self.modelName = (f"Model: A-2")
        else:
            self.modelName = modelName

        if (productStatus is None) or (self.productStatus is None):
            self.productStatus = (f"Status: HEALTHY")
        else:
            self.productStatus = f"Status: {productStatus}"

        if (productSerial is None) or (self.productSerial is None):
            self.productSerial = (f"Serial: PHAB8506001G3P8AGN")
        else:
            self.productSerial = None

        if (firmwareName is None) or (self.firmwareName is None):
            self.firmwareName = (f"Firmware: 2CV1ZRAD-002")
        else:
            self.firmwareName = firmwareName

        if (collectionTypes is None) or (self.collectionTypes is None):
            self.collectionTypes = (f"Type: Data Collection, Fault Analysis, Prediction")
        else:
            self.collectionTypes = collectionTypes

        customerPage = pylatex.MiniPage(pos='h')
        customerPage.append(self.customerName)
        customerPage.append("\n")
        customerPage.append(self.userName)
        customerPage.append("\n")
        customerPage.append(self.productName)
        customerPage.append("\n")
        customerPage.append(self.modelName)
        customerPage.append("\n")
        customerPage.append(self.productStatus)
        self.customerPage = customerPage

        # Add device information
        codeBranchPage = pylatex.MiniPage(pos='t!', align='r')
        codeBranchPage.append(self.productSerial)
        codeBranchPage.append(pylatex.LineBreak())
        codeBranchPage.append(pylatex.utils.bold(self.firmwareName))
        codeBranchPage.append(pylatex.LineBreak())
        codeBranchPage.append(pylatex.utils.bold(self.collectionTypes))
        self.codeBranchPage = codeBranchPage

        with self.pendingDocument.create(pylatex.Tabu("X[l] X[r]")) as first_page_table:
            first_page_table.add_row([self.customerPage, self.codeBranchPage])
            first_page_table.add_empty_row()

        # Add customer information to page.
        self.pendingDocument.change_document_style("firstPage")
        self.pendingDocument.add_color(name="lightgray", model="gray", description="0.80")
        return

    @staticmethod
    def hyperlink(url: str = None, text: str = None):
        if url is not None and text is not None:
            text = pylatex.utils.escape_latex(text)
            return pylatex.utils.NoEscape(r'\href{' + url + '}{' + text + '}')
        else:
            url = 'defaultURL'
            text = '_defaultText'
            print(f'Invalid url or text parameters passed to reportGenerator hyperlink() method')
            return url + text

    @staticmethod
    def generateString(characterSet=None, fileStringNameSize=None):
        """
        Generate random string set when not set by user.
        Args:
            characterSet: Character set to be used.
            fileStringNameSize: File string name size maxima.

        Returns: Token generated.

        """
        if characterSet is None:
            characterSet = 'abcdef0123456789'

        if fileStringNameSize is None:
            fileStringNameSize = 16

        random.seed(1)
        generatedToken = ''.join(random.choice(characterSet) for _ in range(fileStringNameSize))
        return generatedToken

    @staticmethod
    def getTempPathName(genPath=True):
        if genPath is True:
            generatedPath = tempfile.gettempdir()
        else:
            generatedPath = ""
        return generatedPath

    @staticmethod
    def getTempFileName(genFile=True):
        """
        Generate file name.
        Args:
            genFile: proceed flag with generation.

        Returns: file name token string.

        """
        utc_datetime = datetime.datetime.utcnow()
        utc_name = utc_datetime.strftime("%Y-%m-%d-%H%M")
        if genFile is True:
            pseudo = "".join([utc_name, "_"])
            fileConstruct = tempfile.mkstemp(suffix="", prefix=pseudo, dir=None)
        else:
            fileConstruct = ""
        return fileConstruct

    def getTempPathAndFileName(self, extensionName=None, genPath=True, genFile=True):
        """
        Generate path and file name.
        Args:
            extensionName:Extension name desired.
            genPath: proceed flag with generation.
            genFile: proceed flag with generation.

        Returns: token generation of path and file name token string.

        """
        if extensionName is None:
            extensionName = "_debug.tex"
        outfileRef = "".join(
            [self.getTempPathName(genPath=genPath), "/", self.getTempFileName(genFile=genFile), extensionName])
        return outfileRef

    @staticmethod
    def createFilePath(requestPath):
        """
        Generate file path with existance okay.
        Args:
            requestPath: path to request creation.

        Returns: Void

        """
        os.makedirs(requestPath, exist_ok=True)
        return

    def addMetaTable(self,
                     tableName: str = None,
                     tableLayout: str = None,
                     tableHeader: typing.List[str] = None,
                     tableMeta: list = None,
                     alternateColoring: int = 2,
                     color: str = "lightgray",
                     mapper=pylatex.utils.bold,
                     row_height: float = 1.5):
        """
        Meta data table constructor.
        Args:
            tableName: Name of table.
            tableLayout: Format of table.
            tableHeader: Header of table
            tableMeta: Table meta data.
            alternateColoring: Coloring for human friendlyness.
            color: Color setting.
            mapper: mapper for rows.
            row_height: row customization height.

        Returns: Tablename and table object pair.

        """
        # Generate Meta Data Tables
        if tableName is None:
            tableName = self.generateString()

        if tableLayout is None:
            tableLayout = "X[l] X[2l] X[r] X[r] X[r]"

        if tableHeader is None:
            tableHeader = ["date", "description", "Col_3", "Col_4", "Col_5"]

        if tableMeta is not None and isinstance(tableMeta, list):
            dataValid = True
        else:
            dataValid = False

        if ((alternateColoring < 2) or ((dataValid is True) and (alternateColoring > len(tableMeta)))):
            alternateColoring = 2

        dataTableObj = pylatex.LongTabu(tableLayout, row_height=row_height)
        dataTableObj.add_row(tableHeader,
                             mapper=mapper,
                             color=color)
        dataTableObj.add_empty_row()
        dataTableObj.add_hline()
        if dataValid is False:
            startRange = 2
            endRange = 8
            tableRows = random.randint(startRange, 8)
            for i in range(tableRows):
                randomRow = ["2020-DEC-31",
                             "Testing",
                             str(random.randint(startRange, endRange)),
                             str(random.randint(startRange, endRange)),
                             str(random.randint(startRange, endRange))]
                if (i % alternateColoring) == 0:
                    dataTableObj.add_row(randomRow, color=color)
                else:
                    dataTableObj.add_row(randomRow)
        else:
            for i, listRow in enumerate(tableMeta):
                if (i % alternateColoring) == 0:
                    dataTableObj.add_row(listRow, color=color)
                else:
                    dataTableObj.add_row(listRow)
        tableObject = copy.deepcopy(dataTableObj)

        if self.debug is True:
            debugFile = self.getTempPathAndFileName(extensionName="_debug.tex", genPath=True, genFile=True)
            debugFile = os.path.abspath(debugFile)
            self.createFilePath(requestPath=debugFile)  # @todo: verify file creation sets
            tableObject.generate_tex(debugFile)
            print(f"{whoami()} debug table filename is {debugFile}")

        return tableName, tableObject

    @staticmethod
    def addPDFImages(inFigureList: typing.List[str] = None):
        """
        Add PDF images to report in a simple two column format.
        Args:
            inFigureList: Figure string list of paths to add.

        Returns: Figure table object and total rows in existance.

        """
        if inFigureList is None:
            return (None, 0)
        # Add images
        validFigureList = []
        for i, figureItem in enumerate(inFigureList):
            figExists = os.path.exists(figureItem)
            if figExists:
                validFigureList.append(figureItem)

        figureList = []
        figTable = pylatex.LongTabu("X[c] X[c]")
        for _, itemFigure in enumerate(validFigureList):
            figGen = pylatex.StandAloneGraphic(itemFigure, image_options="width=200px")
            figureList.append(figGen)

        # Prepare grid of 2 by N figures
        if len(figureList) > 0:
            (figureRows, figureLeftOver) = divmod(len(figureList), 2)
            figureTotalRows = figureRows + figureLeftOver
            for i in range(figureRows):
                if i >= figureTotalRows:
                    figTable.add_row([figureList[(i * 2)], figureList[i * 2 + 1]])
            if figureLeftOver >= 1:
                figTable.add_row([figureList[figureTotalRows - 1], figureList[figureTotalRows - 1]])
        else:
            figTable = None
            (figureTotalRows) = 0

        return (figTable, figureTotalRows)

    @staticmethod
    def addPDFImagesRows(inFigureList: list = None, rowWidth: int = 1):
        """
        Add PDF images to report in a simple n by m column format.
        Args:
            inFigureList: Figure string list of paths to add.
            rowWidth:

        RReturns: Figure table object and total rows in existance.

        """
        if inFigureList is None:
            return (None, 0)
        AssertionError(0 < rowWidth < len(inFigureList), f"Error in width... {os.linesep} {whoami()}")
        # Add images in existance
        figureList = list()
        for _, itemFigure in enumerate(inFigureList):
            figExists = os.path.exists(itemFigure)
            if figExists:
                figGen = pylatex.StandAloneGraphic(itemFigure, image_options="width=200px")
                figureList.append(figGen)

        # Prepare grid of rowWidth by len(figureList)/rowWidth figures
        if len(figureList) > 0 and rowWidth > 0:
            (figureRows, figureLeftOver) = divmod(len(figureList), rowWidth)
            figureTotalRows = figureRows
            if figureLeftOver > 0:
                figureTotalRows += 1
            rowItems = 0  # Items collected into a single row.
            rowCount = 0  # Count of all rows accumulated.
            rowList = None  # Row container for items collected.
            matrixList = list()  # Matrix grid arrangement of figures.
            for _, figureContent in enumerate(figureList):
                if rowCount < figureRows:
                    if (rowItems == 0):
                        # Non-remainder, Start a new row.
                        rowList = list()
                        rowList.append(figureContent)
                        rowItems += 1
                    elif (0 < rowItems < rowWidth):
                        # Non-remainder, Within a row bounds appending.
                        rowList.append(figureContent)
                        rowItems += 1
                    else:
                        # The conditions above are turing complete; if we enter there there is a logical or data fault.
                        print(whoami())
                        raise (TypeError)

                    if (rowItems == rowWidth):
                        # Non-remainder, At row boundary so append row and prepare for new row.
                        rowItems = 0
                        rowCount += 1
                        matrixList.append(rowList)

                elif (rowCount >= figureRows) and (figureLeftOver > 0):
                    if (rowItems == 0):
                        # Remainder, start a new row only if the remaining items is > known left over.
                        rowList = list()
                        rowList.append(figureContent)
                        rowItems += 1
                    elif (0 < rowItems < rowWidth):
                        # Remainder, we have entered a partial row so append items that can fit.
                        rowList.append(figureContent)
                        rowItems += 1
                    else:
                        # The conditions above are turing complete; if we enter there there is a logical or data fault.
                        print(whoami())
                        raise (TypeError)
                    # (i % rowWidth) == figureLeftOver)
                    if (rowItems == figureLeftOver) and (rowItems <= rowWidth):
                        # Remainder, we no longer have any more content so duplicate the last item until we are at row width.
                        while (rowItems < rowWidth):
                            rowList.append(figureContent)
                            rowItems += 1
                        rowCount += 1
                        matrixList.append(rowList)
                    else:
                        # The conditions above are turing complete; if we enter there there is a logical or data fault.
                        print(whoami())
                        raise (TypeError)
                else:
                    # The conditions above are turing complete; if we enter there there is a logical or data fault.
                    print(whoami())
                    raise (TypeError)

            rowConfigurationString = ""
            for i in range(rowWidth):
                if 0 < i < rowWidth:
                    rowConfigurationString += " "
                rowConfigurationString += "X[c]"
            figTable = matrixList
        else:
            figTable = None
            figureTotalRows = 0
            rowConfigurationString = ""

        return (figTable, figureTotalRows, rowConfigurationString)

    @staticmethod
    def addImagesRows(inFigureList: list = None, rowWidth: int = 1, image_options: list = None):
        """
        Add PDF images to report in a simple n by m column format.
        Args:
            inFigureList: Figure string list of paths to add.
            rowWidth: width of row of images
            image_options: string list – Specifies the options for the image (ie. height, width)

        Returns: Figure table object and total rows in existence.

        """
        if image_options is None:
            image_options = ["width=200px"]
        if inFigureList is None:
            return (None, 0)
        AssertionError(0 < rowWidth < len(inFigureList), f"Error in width... {os.linesep} {whoami()}")
        # Add images in existence
        figureList = list()
        for _, itemFigure in enumerate(inFigureList):
            figExists = os.path.exists(itemFigure)
            if figExists:
                figGen = pylatex.StandAloneGraphic(itemFigure, image_options=image_options)
                figureList.append(figGen)

        # Prepare grid of rowWidth by len(figureList)/rowWidth figures
        if len(figureList) > 0 and rowWidth > 0:
            (figureRows, figureLeftOver) = divmod(len(figureList), rowWidth)
            figureTotalRows = figureRows
            if figureLeftOver > 0:
                figureTotalRows += 1
            rowItems = 0  # Items collected into a single row.
            rowCount = 0  # Count of all rows accumulated.
            rowList = None  # Row container for items collected.
            matrixList = list()  # Matrix grid arrangement of figures.
            for _, figureContent in enumerate(figureList):
                if rowCount <= figureRows:
                    if (rowItems == 0):
                        # Non-remainder, Start a new row.
                        rowList = list()
                        rowList.append(figureContent)
                        rowItems += 1
                    elif (0 < rowItems < rowWidth):
                        # Non-remainder, Within a row bounds appending.
                        rowList.append(figureContent)
                        rowItems += 1
                    else:
                        # The conditions above are turing complete; if we enter there there is a logical or data fault.
                        print(whoami())
                        raise (TypeError)

                    if (rowItems == rowWidth):
                        # Non-remainder, At row boundary so append row and prepare for new row.
                        rowItems = 0
                        rowCount += 1
                        matrixList.append(rowList)

                elif rowCount > figureRows and figureLeftOver > 0:
                    if (rowItems == 0):
                        # Remainder, start a new row only if the remaining items is > known left over.
                        rowList = list()
                        rowList.append(figureContent)
                        rowItems += 1
                    elif (0 < rowItems < rowWidth):
                        # Remainder, we have entered a partial row so append items that can fit.
                        rowList.append(figureContent)
                        rowItems += 1
                    else:
                        # The conditions above are turing complete; if we enter there there is a logical or data fault.
                        print(whoami())
                        raise (TypeError)

                    if ((rowItems % rowWidth) == figureLeftOver) and rowItems <= rowWidth:
                        # Remainder, we no longer have any more content so duplicate the last item until we are at row width.
                        while (rowItems <= rowWidth):
                            rowList.append(figureContent)
                            rowItems += 1
                        rowCount += 1
                        matrixList.append(rowList)
                    else:
                        # The conditions above are turing complete; if we enter there there is a logical or data fault.
                        print(whoami())
                        raise (TypeError)
                else:
                    # The conditions above are turing complete; if we enter there there is a logical or data fault.
                    print(whoami())
                    raise (TypeError)

            rowConfigurationString = ""
            for i in range(rowWidth):
                rowConfigurationString += "X[c]"
                if 0 < i < rowWidth:
                    rowConfigurationString += " "

            figTable = pylatex.LongTabu(rowConfigurationString)
            for _, item in enumerate(matrixList):
                figTable.add_row(item)
        else:
            figTable = None
            figureTotalRows = 0

        return (figTable, figureTotalRows)

    @staticmethod
    def addMathMatrix(arrayMatrix: list = None, arrayMatrixLabel: str = None):
        """
        Add a matrix table in mathematical form.
        Args:
            arrayMatrix: Array to add into document.
            arrayMatrixLabel: Array label to be on the left hand side of the equal operator.

        Returns: mathematics object for report.

        """
        if arrayMatrix is None:
            arrayMatrix = [[2, 3, 4],
                           [0, 0, 1],
                           [0, 0, 2]]
        if arrayMatrixLabel is None:
            arrayMatrixLabel = 'M='
        else:
            arrayMatrixLabel = f"{arrayMatrixLabel}="

        M = numpy.array(arrayMatrix)
        matrixObj = pylatex.Matrix(M, mtype='b')
        mathObj = pylatex.Math(data=[arrayMatrixLabel, matrixObj])
        return mathObj

    @staticmethod
    def addEnumerateList(enumStrList: list = None):
        if enumStrList is None:
            return None
        enumListObj = pylatex.Enumerate(enumeration_symbol=r"\alph*)", options={'start': 20})
        for _, selectItem in enumerate(enumStrList):
            enumListObj.add_item(selectItem)
        return enumListObj


class RegressionUnitTestsCases():
    """
    Self regression testing class for report generator. The following is a test set to ensure minimum functionality.
    """
    filename = None
    reportGenObj = None
    homeDir = None
    status = "Pass"
    debug = True

    def __init__(self,
                 outDir: str = None,
                 referenceDir: str = None,
                 debug: bool = True):
        """
        Setup and constants of unit test.
        Args:
            outDir: Output directory of unit test.
            referenceDir: Reference meta data for congruence.
            debug: Developer debug flag.
        """

        if outDir is None:
            curPath = os.getcwd()
            outDir = os.path.join(curPath, "../../../data/output")
            outDir = os.path.abspath(outDir)
        else:
            tmpFilePath, file_extension = os.path.splitext(f"{__file__}")
            tmpFilePath = f"{tmpFilePath}_unitTestDir"
            outDir = os.path.abspath(tmpFilePath)

        if referenceDir is None:
            referenceDir = os.path.abspath("../../../data/reportGenerator_unitTestDir")
            self.referenceDir = referenceDir
        else:
            self.referenceDir = os.path.abspath(referenceDir)

        self.debug = debug
        self.homeDir = outDir
        self.filename = "produced"
        self.reportGenObj = ReportGenerator(outPath=self.homeDir,
                                            fileName=self.filename,
                                            logoImage="../Intel_IntelligentSystems.png",
                                            debug=self.debug)
        return

    def test_createDocument(self):
        """
        Create a document and compare it to reference. Create a custom diff tool for comparing .tex files.
        Returns: Status of test.
        """
        self.reportGenObj.createDocument()

        referPath = os.path.abspath(self.referenceDir)
        fileContext = os.path.join(referPath, "reference.tex")
        unitTestReferece = os.path.abspath(fileContext)

        fileContext = os.path.join(self.homeDir, "produced.tex")
        unitTestProduced = os.path.abspath(fileContext)

        refExists = os.path.exists(unitTestReferece)
        proExists = os.path.exists(unitTestProduced)

        # I.E. Date timestamp is not a valid test line. \textbf{2021{-}03{-}02{-}23{-}28{-}53{-}740847}%
        # Matcher using escape char. re.compile(".{0,1}\\\\textbf\\{(\\d{1,}\\{\\-\\}){1,}\\d{1,}\\}%.{0,1}")
        excludeRegex = re.compile(pattern="((.)+)?(textbf)\x7B(\d+\x7B\x2D\x7D)+\d+\x7D\x25((.)+)?")
        excludedLines = [98]
        lineDiffListSource = []
        lineDiffListDestination = []

        if refExists is False and proExists is False:
            testStatus = "Fail"
        else:
            testStatus = "Pass"
            refDoc = open(unitTestReferece).readlines()
            pDoc = open(unitTestProduced).readlines()
            if self.debug:
                for line in difflib.unified_diff(refDoc, pDoc):
                    print(f"{whoami()} {os.linesep} Diff-Context: {pprint.pformat(line)}")

            refDoc = open(unitTestReferece).readlines()
            pDoc = open(unitTestProduced).readlines()
            diffs = difflib.Differ().compare(refDoc, pDoc)
            lineNum = 0
            for line in diffs:
                # Split off the code
                code = line[:2]
                # If the  line is in both files or just pDoc, increment the line number.
                if code in ("  ", "+ "):
                    lineNum += 1
                # If this line is only in pDoc, print the line number and the text on the line
                if code == "+ ":
                    candidateString = line[2:].strip()
                    isRegexExcluded = excludeRegex.findall(string=candidateString) is not None
                    lineOffset = (lineNum - 1)
                    isLineExcluded = lineOffset in excludedLines
                    excludeFailCase = (isRegexExcluded or isLineExcluded)
                    if excludeFailCase is False and self.debug:
                        print(f"Source:      {lineNum}, {refDoc[lineOffset]}")
                        print(f"Destination: {lineNum}, {line[2:].strip()}")
                    if excludeFailCase is False and testStatus == "Pass":
                        testStatus = "Fail"
                        lineDiffListSource.append([lineNum, refDoc[lineOffset]])
                        lineDiffListDestination.append([lineNum, line[2:].strip()])
            self.status = testStatus
        return testStatus

    def test_updateCover(self):
        """
        Template cover testing.
        Returns: None.
        """
        # Data token update
        titleInfo = "Rapid Automated-Analysis for Developers (RAAD) - Report"
        teamName = (f"Team: " + "RAMP")
        authorName = (f"PI: " + "Joseph Tarango")
        specificationName = (f"Specification: " + "Telemetry")
        specificationVersion = (f"Version: " + "2.0")
        supportedProductList = (f"HR, ADP, YVR")
        reportVersion = (f"Version: " + "Alpha" + "1.0")
        self.reportGenObj.updateCover(titleInfo=titleInfo,
                                      teamName=teamName,
                                      authorName=authorName,
                                      specificationName=specificationName,
                                      specificationVersion=specificationVersion,
                                      supportedProductList=supportedProductList,
                                      reportVersion=reportVersion)
        return

    def test_updateCustomerInformation(self):
        """
        Template customer testing.
        Returns: None.
        """
        customerName = (f"Customer: Internal Research")
        userName = (f"User: Tester")
        productName = (f"Product: ADP")
        modelName = (f"Model: A-2")
        productStatus = (f"Status: HEALTHY")
        productSerial = (f"Serial: PHAB8506001G3P8AGN")
        firmwareName = (f"Firmware: 2CV1ZRAD-002")
        collectionTypes = (f"Type: Data Collection, Fault Analysis, Prediction")
        self.reportGenObj.updateCustomerInformation(customerName=customerName,
                                                    userName=userName,
                                                    productName=productName,
                                                    modelName=modelName,
                                                    productStatus=productStatus,
                                                    productSerial=productSerial,
                                                    firmwareName=firmwareName,
                                                    collectionTypes=collectionTypes)
        return

    def test_addMetaTable(self):
        """
        Template meta table testing.
        Returns: None.
        """
        tableName = self.reportGenObj.generateString()
        tableLayout = "X[l] X[2l] X[r] X[r] X[r]"
        tableHeader = ["date", "description", "Col_3", "Col_4", "Col_5"]
        tableMeta = []
        alternateColoring = 2
        color = "lightgray"
        mapper = pylatex.utils.bold
        row_height = 1.5
        startRange = 2
        endRange = 7
        for _ in range(random.randint(startRange, 8)):
            tableRows = random.randint(startRange, 8)
            for i in range(tableRows):
                randomRow = ["2020-DEC-31",
                             "Testing",
                             str(random.randint(startRange, endRange)),
                             str(random.randint(startRange, endRange)),
                             str(random.randint(startRange, endRange))]
                tableMeta.append(randomRow)
            tableName, tableObject = self.reportGenObj.addMetaTable(tableName=tableName, tableLayout=tableLayout,
                                                                    tableHeader=tableHeader,
                                                                    tableMeta=tableMeta,
                                                                    alternateColoring=alternateColoring,
                                                                    color=color, mapper=mapper, row_height=row_height)
            print(f"{whoami()} with generated file name {tableName} {os.linesep} {pprint.pformat(tableObject)}")
        return

    def test_addPDFImages(self):
        """
        Template PDF addition testing.
        Returns: None or error string.
        """
        testFigurePDFs = [('../../../data/sampleRAD/ARMA_Model_2020-10-05-09-04-12-924760.pdf'),
                          ('../../../data/sampleRAD/Defrag_History_Graph_2020-10-05-06-47-47-036468_uid-41.pdf'),
                          ('../../../data/sampleRAD/RNN_Prediction_2020-10-07-23-40-07-523165.pdf'),
                          ('../../../data/sampleRAD/ARMA_Model_2020-10-05-11-06-52-418751.pdf')]
        for figureItem in testFigurePDFs:
            figExists = os.path.exists(figureItem)
            assert figExists is True, f"File does not exist {figureItem}."
        testList_0 = list()
        testList_1 = list(testFigurePDFs[:1])
        testList_2 = list(testFigurePDFs[:2])
        testList_3 = list(testFigurePDFs[:3])
        testList_4 = list(testFigurePDFs)
        figureInfo = [self.reportGenObj.addPDFImages(inFigureList=list(testList_0)),
                      self.reportGenObj.addPDFImages(inFigureList=testList_1),
                      self.reportGenObj.addPDFImages(inFigureList=testList_2),
                      self.reportGenObj.addPDFImages(inFigureList=testList_3),
                      self.reportGenObj.addPDFImages(inFigureList=testList_4)]

        knownResult = [r"Index 0 (None, 0)",

                       r"Index 1 (LongTabu(NoEscape(X[c] X[c]), "
                       r"[NoEscape(\includegraphics[width=200px]"
                       r"{../../../data/sampleRAD/ARMA_Model_2020-10-05-09-04-12-924760.pdf}"
                       r"&\includegraphics[width=200px]"
                       r"{../../../data/sampleRAD/ARMA_Model_2020-10-05-09-04-12-924760.pdf}\\)], "
                       r"None, [NoEscape(\includegraphics[width=200px]"
                       r"{../../../data/sampleRAD/ARMA_Model_2020-10-05-09-04-12-924760.pdf}"
                       r"&\includegraphics[width=200px]"
                       r"{../../../data/sampleRAD/ARMA_Model_2020-10-05-09-04-12-924760.pdf}\\)]),"
                       f"\n 1)",

                       r"Index 2 (LongTabu(NoEscape(X[c] X[c]), [], None, []), 1)",

                       r"Index 3 (LongTabu(NoEscape(X[c] X[c]), [NoEscape(\includegraphics[width=200px]"
                       r"{../../../data/sampleRAD/Defrag_History_Graph_2020-10-05-06-47-47-036468_uid-41.pdf}"
                       r"&\includegraphics[width=200px]"
                       r"{../../../data/sampleRAD/Defrag_History_Graph_2020-10-05-06-47-47-036468_uid-41.pdf}\\)],"
                       r" None, [NoEscape(\includegraphics[width=200px]"
                       r"{../../../data/sampleRAD/Defrag_History_Graph_2020-10-05-06-47-47-036468_uid-41.pdf}"
                       r"&\includegraphics[width=200px]"
                       r"{../../../data/sampleRAD/Defrag_History_Graph_2020-10-05-06-47-47-036468_uid-41.pdf}\\)]),"
                       f"\n 2)",

                       r"Index 4 (LongTabu(NoEscape(X[c] X[c]), [], None, []), 2)"]

        for i, figRow in enumerate(figureInfo):
            resultMetaMade = str(f"Index {i} {pprint.pformat(figRow)}")
            resultExpected = str(knownResult[i])
            errorInfo = str(" ".join(list(whoami())))
            errorMessage = rf"{errorInfo} {os.linesep} Result: {resultMetaMade} {os.linesep} Expected: {resultExpected}"
            if (resultMetaMade != resultExpected):
                return errorMessage
        return None

    def test_addMathMatrix(self):
        """
        Template mathematics matrix testing.
        Returns: Mathematics object.
        """
        arrayMatrix = [[2, 3, 4],
                       [0, 0, 1],
                       [0, 0, 2]]
        arrayMatrixLabel = 'M='

        mathObj = self.reportGenObj.addMathMatrix(arrayMatrix=arrayMatrix, arrayMatrixLabel=arrayMatrixLabel)
        return mathObj

    def setUp(self):
        """
        Function Type: Helper
        # Method called to prepare the test fixture.  This is called immediately
        #    before calling the test method; any exception raised by this method will
        #    be considered an error rather than a test failure. The default
        #    implementation does nothing.
        """
        self.filename = self.__class__.__name__ + '.db'
        # self.homeDir = get_new_environment_path()
        # self.env = db.DBEnv()
        # self.env.open(self.homeDir, db.DB_CREATE | db.DB_INIT_MPOOL)

    def tearDown(self):
        """
        Function Type: Helper

         Method called immediately after the test method has been called and the
            result recorded.  This is called even if the test method raised an
            exception, so the implementation in subclasses may need to be particularly
            careful about checking internal state.  Any exception raised by this
            method will be considered an error rather than a test failure.  This
            method will only be called if the :meth:`setUp` succeeds, regardless of
            the outcome of the test method. The default implementation does nothing.
        """
        # self.env.close()
        # self.env = None
        # test_support.rmtree(self.homeDir)
        return

    def getTestFunctionList(self):
        return [self.test_updateCover,
                self.test_updateCustomerInformation,
                self.test_addMetaTable,
                self.test_addMathMatrix,
                self.test_addPDFImages,
                self.test_createDocument]

    def suite(self):
        """
         Method called to prepare the test fixture.  This is called immediately
            before calling the test method; any exception raised by this method will
            be considered an error rather than a test failure. The default
            implementation does nothing.
        """
        tests = self.getTestFunctionList()
        # testingSuite = unittest.TestSuite()
        testResult = None
        for i, testFunction in enumerate(tests):
            try:
                result = testFunction()
                stringCleaner = str(testFunction.__name__)
                stringCleaner = stringCleaner.replace('\\', '')
                testFunctionName = stringCleaner.replace("'", "")
                resultVector = (i, testFunctionName, [result])
                if i <= 0:
                    testResult = [[resultVector]]
                else:
                    testResult.append([resultVector])
            except BaseException as ErrorContext:
                print("Error encountered in Unit Test Execution.")
                whoami()
                pprint.pprint(ErrorContext)
                pass
        return tests

    def run(self):
        """
        Function Type: Method
         Run the test, collecting the result into the test result object passed as
          *result*.  If *result* is omitted or ``None``, a temporary result
          object is created (by calling the :meth:`defaultTestResult` method) and
          used. The result object is not returned to :meth:`run`'s caller.

          The same effect may be had by simply calling the :class:`TestCase`
          instance.
        """
        # loader = unittest.TestLoader()
        testingSuite = self.suite()
        if self.debug:
            print(f"Testing Suite info {os.linesep} {pprint.pformat(testingSuite)}")
        self.tearDown()
        return


def testSuite(debug: bool = False):
    """
    Function Type: Method
    Run all test for the class.
    """
    testObj = RegressionUnitTestsCases(debug=debug)
    testObj.run()
    return True


def API(options=None):
    """ API for the default application in the graphical interface.
    Args:
        options: Commandline inputs.
    Returns:
    """
    if options.debug:
        print("Options are:\n{0}\n".format(options))
    ###############################################################################
    # Graphical User Interface (GUI) Configuration
    ###############################################################################
    testSuite(debug=options.debug)
    return


def main():
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--debug", action='store_true', dest='debug', default=True, help='Debug mode.')
    (options, args) = parser.parse_args()

    ##############################################
    # Main
    ##############################################
    API(options)
    return 0


if __name__ == '__main__':
    """Performs execution delta of the process."""
    p = datetime.datetime.now()
    try:
        main()
    except Exception as e:
        print("Fail End Process: ", e)
        traceback.print_exc()
    q = datetime.datetime.now()
    print("Execution time: " + str(q - p))
