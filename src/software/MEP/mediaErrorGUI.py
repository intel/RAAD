# !/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Daniel Garces, Joseph Tarango
# *****************************************************************************/
"""mediaErrorGUI.py

this module contains the basic function for generating a window-based GUI for mediaErrorPredictor

Example:
    Default Usage:
        $ python mediaErrorGUI.py

"""
# from __future__ import absolute_import, division, print_function, unicode_literals
# from __future__ import nested_scopes, generators, generator_stop, with_statement, annotations
import sys
import datetime
import traceback
from matplotlib import style
from enum import Enum
import mediaErrorPredictor as MEP

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
        tk.Tk.wm_title(self, "Media Error Visualizer")
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


class FieldsAttributes:
    FieldsLabels = {}
    FieldsLabels[Fields.TRACKING_VARS] = "Select tracking variable"
    FieldsSelectionMode = {}
    FieldsSelectionMode[Fields.TRACKING_VARS] = "single"
    FieldsLegendLocation = {}
    FieldsLegendLocation[Fields.TRACKING_VARS] = (0, 1.04)


class StartPage(tk.Frame):
    listbox = None
    listBox2 = None

    def __init__(self, parent, controller):
        self.window = controller
        tk.Frame.__init__(self, parent)
        # Page Header
        grid_row = 0
        grid_column = 0
        label = tk.Label(self, text="Media Error Prediction Plot")
        label.grid(row=grid_row, column=grid_column, columnspan=2)

        # File browser and file path display
        grid_row = 2
        grid_column = 0
        dirPath = tk.StringVar()
        button = ttk.Button(self, text="Browse Configuration File", command=lambda: self.populate_object(dirPath))
        button.grid(row=grid_row, column=grid_column + 1, sticky="nsew")
        ttk.Entry(self, textvariable=dirPath).grid(row=grid_row, column=grid_column, columnspan=1, sticky="nsew")

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
            self.field_labels[field].grid(row=grid_row, column=grid_column, sticky="nsew", padx=10, columnspan=2)
            self.field_listboxes[field] = tk.Listbox(self, selectmode=FieldsAttributes.FieldsSelectionMode[field],
                                                     exportselection=0)
            self.field_listboxes[field].grid(row=grid_row + 1, column=grid_column, rowspan=1, sticky="nsew", padx=5,
                                             columnspan=2)
            grid_column = grid_column + 1

        # interface for activating Matrix Profile
        grid_row = 8
        grid_column = 0
        self.optionVar = tk.StringVar()
        self.optionVar.set("Yes")
        optionsMenu = tk.OptionMenu(self, self.optionVar, *OPTIONS)
        self.slider = tk.Scale(self, from_=0, to=200, orient=tk.HORIZONTAL)
        tk.Label(self, text="Would you like to use the matrix profile of the data?").grid(row=grid_row,
                                                                                          column=grid_column,
                                                                                          sticky="nsew",
                                                                                          columnspan=2)
        tk.Label(self, text="Input window length for matrix profile").grid(row=grid_row + 2, column=grid_column,
                                                                           sticky="nsew", columnspan=2)

        self.slider.grid(row=grid_row + 3, column=grid_column, columnspan=2)
        optionsMenu.grid(row=grid_row + 1, column=grid_column, columnspan=2)

        # interface for plotting data
        grid_row = 12
        grid_column = 0
        button2 = ttk.Button(self, text="Plot Data", command=lambda: self.create_new_graph_window())
        button2.grid(row=grid_row, column=grid_column, padx=5, pady=5, columnspan=2)
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
            self.mep = self.objectFile.readConfigContent()
            currentOptions = ["None"] + self.objectFile.dataDict.keys()
            self._update_drop_down_menu(currentOptions, 0)

    def display_dir(self):
        currentName = self.objectVar.get()
        self.currentObject = currentName
        for field in Fields:
            self.field_listboxes[field].delete(0, tk.END)
        for key in sorted(self.objectFile.dataDict[currentName].keys()):
            self.field_listboxes[Fields.TRACKING_VARS].insert(tk.END, key)

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

            subSeqLen = int(self.slider.get())

            self.mep.setMatrixProfileFlag(matrixProfileFlag, subSeqLen=subSeqLen)

            for field in primaryFields:
                self.mep.ARMAModel(self.currentObject, field)


class ObjectConfig:
    objectFilePath = None
    objectIDs = []
    trackingVars = []

    def __init__(self, configFilePath):
        self.objectFilePath = configFilePath

    def readConfigContent(self, debug=False):
        mep = MEP.MediaErrorPredictor(self.objectFilePath, debug=debug)
        self.dataDict = mep.dataDict
        self.objectIDs = self.dataDict.keys()

        return mep


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
