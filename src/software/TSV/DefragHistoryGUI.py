# !/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Daniel Garces, Joseph Tarango
# *****************************************************************************/
"""

"""
# from __future__ import absolute_import, division, print_function, unicode_literals
# from __future__ import nested_scopes, generators, generator_stop, with_statement, annotations
import sys
import datetime
import traceback
from matplotlib import style
from enum import Enum
import DefragHistoryGrapher as DHG

if sys.version_info.major > 2:
    import tkinter as tk
    import tkinter.ttk as ttk
    import tkinter.filedialog as filedialog
else:
    import Tkinter as tk
    import ttk
    import tkFileDialog as filedialog


LARGE_FONT = {"Verdana", 12}
DRIVES = {"ADP", "CDR"}
OPTIONS = {"Yes", "No"}
CORES = {1, 2, 3, 4}
style.use("ggplot")


class DefragHistoryAppMainWindow(tk.Tk):
    """
    Initialization function that initializes the Tk framework

    Args:
        *args(list): The first parameter containing the variable list of arguments
        **kwargs(dict): The second parameter contained named variable arguments.
    """

    def __init__(self, *args, **kwargs):
        # create and init a window
        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.wm_title(self, "Defrag History Visualizer")
        # create and init frame
        container = self.init_frame()
        # populate frame with widgets for StartPage
        self.frame = StartPage(container, self)
        # place the frame in a grid and display the frame
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame()

    def show_frame(self):
        frame = self.frame
        frame.tkraise()

    def init_frame(self):
        container = tk.Frame(self)
        container.pack(side="bottom", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        return container


class Fields(Enum):
    SET_POINTS = 0
    TRACKING_VARS = 1
    SECONDARY_VARS = 2


class FieldsAttributes:
    FieldsLabels = dict()
    FieldsLabels[Fields.SET_POINTS] = "Select set points"
    FieldsLabels[Fields.TRACKING_VARS] = "Select tracking variables"
    FieldsLabels[Fields.SECONDARY_VARS] = "Select optional secondary variables"
    FieldsSelectionMode = dict()
    FieldsSelectionMode[Fields.SET_POINTS] = "multiple"
    FieldsSelectionMode[Fields.TRACKING_VARS] = "multiple"
    FieldsSelectionMode[Fields.SECONDARY_VARS] = "multiple"
    FieldsLegendLocation = dict()
    FieldsLegendLocation[Fields.SET_POINTS] = (0, 1.04)
    FieldsLegendLocation[Fields.TRACKING_VARS] = (0, 1.04)
    FieldsLegendLocation[Fields.SECONDARY_VARS] = (1, 1.04)


class StartPage(tk.Frame):
    listbox = None
    listBox2 = None
    dhFile = None
    dhg = None

    def __init__(self, parent, controller):
        self.window = controller
        tk.Frame.__init__(self, parent)
        # Page Header
        grid_row = 0
        grid_column = 1
        label = tk.Label(self, text="Defrag History Plot")
        label.grid(row=grid_row, column=grid_column)

        # interface for selecting a drive
        grid_row = 2
        grid_column = 1
        self.driveVar = tk.StringVar()
        self.driveVar.set("ADP")
        driveMenu = tk.OptionMenu(self, self.driveVar, *DRIVES)
        tk.Label(self, text="Choose a drive").grid(row=grid_row, column=grid_column, sticky="nsew")
        driveMenu.grid(row=grid_row+1, column=grid_column)

        # File browser and file path display
        grid_row = 4
        grid_column = 0
        dirPath = tk.StringVar()
        button = ttk.Button(self, text="Browse Configuration File", command=lambda: self.display_dir(dirPath))
        button.grid(row=grid_row, column=grid_column, sticky="nsew")
        ttk.Entry(self, textvariable=dirPath).grid(row=grid_row, column=grid_column+1, columnspan=2, sticky="nsew")

        # Display the DH column names
        self.field_labels = {}
        self.field_listboxes = {}
        grid_row = 6
        grid_column = 0
        for field in Fields:
            self.field_labels[field] = tk.Label(self, text=FieldsAttributes.FieldsLabels[field])
            self.field_labels[field].grid(row=grid_row, column=grid_column, sticky="nsew", padx=10)
            self.field_listboxes[field] = tk.Listbox(self, selectmode=FieldsAttributes.FieldsSelectionMode[field],
                                                     exportselection=0)
            self.field_listboxes[field].grid(row=grid_row + 1, column=grid_column, rowspan=1, sticky="nsew", padx=5)
            grid_column = grid_column + 1

        # interface for activating bandwidth
        grid_row = 8
        grid_column = 1
        self.optionVar = tk.StringVar()
        self.optionVar.set("Yes")
        optionsMenu = tk.OptionMenu(self, self.optionVar, *OPTIONS)
        tk.Label(self, text="Is the secondary axis bandwidth?").grid(row=grid_row, column=grid_column, sticky="nsew")
        optionsMenu.grid(row=grid_row + 1, column=grid_column)

        # interface for selecting the number of drives
        grid_row = 8
        grid_column = 2
        self.coreVar = tk.IntVar()
        self.coreVar.set(1)
        coreMenu = tk.OptionMenu(self, self.coreVar, *CORES)
        tk.Label(self, text="Select the number of cores").grid(row=grid_row, column=grid_column, sticky="nsew")
        coreMenu.grid(row=grid_row + 1, column=grid_column)

        # interface for plotting data
        grid_row = 9
        grid_column = 0
        button2 = ttk.Button(self, text="Plot Data", command=lambda: self.create_new_graph_window())
        button2.grid(row=grid_row, column=grid_column, padx=5, pady=5)
        self.graphWindows = []

    @staticmethod
    def validateEntryCallBack(P):
        if (P == ""):
            return True
        if (str.isdigit(P) and int(P) <= 100):
            return True
        else:
            return False

    def display_dir(self, dirPath):
        for field in Fields:
            self.field_listboxes[field].delete(0, tk.END)
        dirPath.set(filedialog.askopenfilename())
        if str(dirPath.get())[-4:].lower() != ".ini":
            dirPath.set("Input must be a configuration file")
        else:
            driveName = self.driveVar.get()
            mode = 0
            if driveName == "ADP":
                mode = 1
            elif driveName == "CDR":
                mode = 2
            self.dhFile = DefragConfig(str(dirPath.get()), mode)
            self.dhg = self.dhFile.readConfigContent()
            for key in self.dhFile.setPoints:
                self.field_listboxes[Fields.SET_POINTS].insert(tk.END, key)
            for key in self.dhFile.trackingVars:
                self.field_listboxes[Fields.TRACKING_VARS].insert(tk.END, key)
            for key in self.dhFile.secondaryVars:
                self.field_listboxes[Fields.SECONDARY_VARS].insert(tk.END, key)

    def is_data_selected_from_fields(self):
        return (len(self.field_listboxes[Fields.TRACKING_VARS].curselection()) > 0)

    @staticmethod
    def get_listbox_content(listbox):
        selectionList = []
        for index in listbox.curselection():
            selectionList.append(listbox.get(index))
        return selectionList

    def create_new_graph_window(self):
        if self.is_data_selected_from_fields():

            self.dhg.setSetPointNames(self.get_listbox_content(self.field_listboxes[Fields.SET_POINTS]))
            self.dhg.setTrackingNames(self.get_listbox_content(self.field_listboxes[Fields.TRACKING_VARS]))
            self.dhg.setSecondaryVars(self.get_listbox_content(self.field_listboxes[Fields.SECONDARY_VARS]))

            for field in Fields:
                self.field_listboxes[field].selection_clear(0, tk.END)

            dataDict = self.dhFile.vizDict
            object_t = "uid-41"
            numCores = self.coreVar.get()
            bandwidth = self.optionVar.get()
            bandwidthFlag = False
            if bandwidth == "Yes":
                bandwidthFlag = True
            elif bandwidth == "No":
                bandwidthFlag = False
            driveName = self.driveVar.get()
            if driveName == "ADP":
                self.dhg.generateTSVisualizationADP(object_t, dataDict, bandwidthFlag, numCores=numCores)
            elif driveName == "CDR":
                self.dhg.generateTSVisualizationCDR(object_t, dataDict, bandwidthFlag, numCores=numCores)


class DefragConfig():
    dhFilePath = None
    setPoints = []
    trackingVars = []
    secondaryVars = []

    def __init__(self, configFilePath, mode):
        self.dhFilePath = configFilePath
        self.mode = mode
        self.vizDict = None

    def readConfigContent(self, debug=False):
        dhg = DHG.DefragHistoryGrapher(mode=self.mode, debug=True)
        self.vizDict = dhg.generateDataDictFromConfig(self.dhFilePath)
        self.setPoints = dhg.getSetPointNames()
        object_t = "uid-41"
        try:
            subdict = self.vizDict[object_t]
        except Exception:
            print("DefragHistory object not found in the configuration file")
            return
        if debug is True:
            print("DefragHistory object found...")
        if self.mode == 1:
            logType = subdict["header"]["prevlogtype"][0]

            if str(logType) == "DEFRAG_HISTORY_ELEMENT_TYPE_EXTENDED":
                logName = "logextended[0]"
            else:
                logName = "lognormal[0]"
            logDict = subdict["__anuniontypedef115__"][logName]
            self.trackingVars = logDict.keys()
            self.secondaryVars = logDict.keys()
        elif self.mode == 2:
            logName = "log[0]"
            logDict = subdict[logName]
            self.trackingVars = logDict.keys()
            self.secondaryVars = logDict.keys()

        return dhg

    @staticmethod
    def get_data_listbox(dhDict, keylist, startpercent, endpercent):
        datalist = []

        for key in keylist:
            startIndex = int(len(dhDict[key]) * (startpercent / 100))
            endIndex = int(len(dhDict[key]) * (endpercent / 100))
            datalist.append(dhDict[key][startIndex:endIndex])
        return datalist


if __name__ == '__main__':
    """Performs execution delta of the process."""
    pStart = datetime.datetime.now()
    try:
        app = DefragHistoryAppMainWindow()
        app.mainloop()
    except Exception as errorMain:
        print("Fail End Process: {0}".format(errorMain))
        traceback.print_exc()
    qStop = datetime.datetime.now()
    print("Execution time: " + str(qStop - pStart))
