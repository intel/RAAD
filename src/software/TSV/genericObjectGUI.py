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
import visualizeTS as VTS

if sys.version_info.major > 2:
    import tkinter as tk
    import tkinter.ttk as ttk
    import tkinter.filedialog as filedialog
else:
    import Tkinter as tk
    import ttk
    import tkFileDialog as filedialog


LARGE_FONT = {"Verdana", 12}
OPTIONS = {"Yes", "No"}
OBJECTS = {"None"}
style.use("ggplot")


class GenericObjectAppMainWindow(tk.Tk):
    """
    Initialization function that initializes the Tk framework

    Args:
        *args(list): The first parameter containing the variable list of arguments
        **kwargs(dict): The second parameter contained named variable arguments.
    """

    def __init__(self, *args, **kwargs):
        # create and init a window
        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.wm_title(self, "Generic Object Visualizer")
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
    TRACKING_VARS = 0
    SECONDARY_VARS = 1


class FieldsAttributes:
    FieldsLabels = {}
    FieldsLabels[Fields.TRACKING_VARS] = "Select tracking variables"
    FieldsLabels[Fields.SECONDARY_VARS] = "Select optional secondary variables"
    FieldsSelectionMode = {}
    FieldsSelectionMode[Fields.TRACKING_VARS] = "multiple"
    FieldsSelectionMode[Fields.SECONDARY_VARS] = "multiple"
    FieldsLegendLocation = {}
    FieldsLegendLocation[Fields.TRACKING_VARS] = (0, 1.04)
    FieldsLegendLocation[Fields.SECONDARY_VARS] = (1, 1.04)


class StartPage(tk.Frame):
    listbox = None
    listBox2 = None

    def __init__(self, parent, controller):
        self.window = controller
        tk.Frame.__init__(self, parent)
        # Page Header
        grid_row = 0
        grid_column = 1
        label = tk.Label(self, text="Generic Object Plot")
        label.grid(row=grid_row, column=grid_column)

        # File browser and file path display
        grid_row = 2
        grid_column = 0
        dirPath = tk.StringVar()
        button = ttk.Button(self, text="Browse Configuration File", command=lambda: self.populate_object(dirPath))
        button.grid(row=grid_row, column=grid_column+2, sticky="nsew")
        ttk.Entry(self, textvariable=dirPath).grid(row=grid_row, column=grid_column, columnspan=2, sticky="nsew")

        # interface for selecting object
        grid_row = 4
        grid_column = 0
        self.objectVar = tk.StringVar()
        self.objectVar.set("None")
        self.objectMenu = tk.OptionMenu(self, self.objectVar, *OBJECTS)
        tk.Label(self, text="Select the object to be graphed").grid(row=grid_row, column=grid_column, sticky="nsew")
        self.objectMenu.grid(row=grid_row + 1, column=grid_column)
        populateButton = ttk.Button(self, text="Select Object", command=lambda: self.display_dir())
        populateButton.grid(row=grid_row + 1, column=grid_column + 1, sticky="nsew")

        # Display the object column names
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

        # interface for activating Matrix Profile
        grid_row = 8
        grid_column = 1
        self.optionVar = tk.StringVar()
        self.optionVar.set("Yes")
        optionsMenu = tk.OptionMenu(self, self.optionVar, *OPTIONS)
        tk.Label(self, text="Would you like to use the matrix profile of the data?").grid(row=grid_row,
                                                                                          column=grid_column,
                                                                                          sticky="nsew")
        optionsMenu.grid(row=grid_row + 1, column=grid_column)

        # interface for plotting data
        grid_row = 9
        grid_column = 0
        button2 = ttk.Button(self, text="Plot Data", command=lambda: self.create_new_graph_window())
        button2.grid(row=grid_row, column=grid_column, padx=5, pady=5)
        self.graphWindows = []

    def _update_drop_down_menu(self, options, index=None):
        menu = self.objectMenu["menu"]
        menu.delete(0, "end")
        for string in options:
            menu.add_command(label=string,
                             command=lambda value=string:
                             self.objectVar.set(value))
        if index is not None:
            self.objectVar.set(options[index])

    def populate_object(self, dirPath):
        dirPath.set(filedialog.askopenfilename())
        if str(dirPath.get())[-4:].lower() != ".ini":
            dirPath.set("Input must be a configuration file")
        else:
            self.objectFile = ObjectConfig(str(dirPath.get()))
            self.vts = self.objectFile.readConfigContent()
            self.objectNamesDict = {}
            for key in self.objectFile.objectIDs:
                currentObject = "uid-" + key
                currentName = self.objectFile.vizDict[currentObject]["name"]
                self.objectNamesDict[currentName] = key
            currentOptions = ["None"] + list(self.objectNamesDict.keys())
            self._update_drop_down_menu(currentOptions, 0)

    def display_dir(self):
        currentName = self.objectVar.get()
        self.currentObject = self.objectNamesDict[currentName]
        currentObject = "uid-" + self.currentObject
        for field in Fields:
            self.field_listboxes[field].delete(0, tk.END)
        for key in self.objectFile.vizDict[currentObject].keys():
            self.field_listboxes[Fields.TRACKING_VARS].insert(tk.END, key)
            self.field_listboxes[Fields.SECONDARY_VARS].insert(tk.END, key)

    def is_data_selected_from_fields(self):
        return (len(self.field_listboxes[Fields.TRACKING_VARS].curselection()) > 0)

    def get_listbox_content(self, listbox):
        selectionList = []
        for index in listbox.curselection():
            selectionList.append(listbox.get(index))
        return selectionList

    def create_new_graph_window(self):
        if self.is_data_selected_from_fields():
            primaryFields = self.get_listbox_content(self.field_listboxes[Fields.TRACKING_VARS])
            secondaryFields = self.get_listbox_content(self.field_listboxes[Fields.SECONDARY_VARS])
            unionFields = primaryFields + secondaryFields
            currentObjects = []
            currentObjects.append(self.currentObject)

            for field in Fields:
                self.field_listboxes[field].selection_clear(0, tk.END)

            matrixProfile = self.optionVar.get()
            matrixProfileFlag = False
            if matrixProfile == "Yes":
                matrixProfileFlag = True
            elif matrixProfile == "No":
                matrixProfileFlag = False

            if matrixProfileFlag:
                self.objectFile.vizDict = self.vts.generateMP(self.objectFile.vizDict, obj=currentObjects,
                                                              fields=unionFields, subSeqLen=20, visualizeAllObj=False,
                                                              visualizeAllFields=False)
            objectName = "uid-" + self.currentObject
            self.vts.generateTSVisualizationGUI(objectName, self.objectFile.vizDict[objectName], primaryFields,
                                                secondaryFields)


class ObjectConfig:
    objectFilePath = None
    objectIDs = []
    trackingVars = []

    def __init__(self, configFilePath):
        self.objectFilePath = configFilePath

    def readConfigContent(self, debug=False):
        vts = VTS.visualizeTS(debug)
        self.vizDict = vts.generateDataDictFromConfig(self.objectFilePath)
        self.objectIDs = list(map(lambda x: x.strip("uid-"), self.vizDict.keys()))

        return vts


if __name__ == '__main__':
    """Performs execution delta of the process."""
    pStart = datetime.datetime.now()
    try:
        app = GenericObjectAppMainWindow()
        app.mainloop()
    except Exception as errorMain:
        print("Fail End Process: {0}".format(errorMain))
        traceback.print_exc()
    qStop = datetime.datetime.now()
    print("Execution time: " + str(qStop - pStart))
