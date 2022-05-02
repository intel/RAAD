#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: David Escamilla, Joseph Tarango
# *****************************************************************************/
# , nested_scopes, generators, generator_stop, with_statement, annotations
"""
Handles all of the generations of the HTML files. (Tables, graphs, etc.)
"""


class htmlGen(object):
    """
    # Generates all of the html output
    # <p>
    """
    htmlOutputFileName = ""
    htmlOutput = None
    urlRoot = "http://nsg-jira.intel.com"  # Root url for Atlassian server

    def openHtmlOutput(self, filename):
        """
        # openHtmlOutput
        # Open a file for writing.  Delete the file if it exists
        #
        # @param filename        Filename to open
        #
        """
        self.htmlOutputFileName = filename
        self.htmlOutput = open(filename, 'w')

    def BeginHtlmOutput(self, title, heading1):
        """
        # Write everything found at the beginning of an HTML file up to the body section.
        #
        # @param title          Title to be displayed in the tab/window section
        # @param Heading1        First large heading in the HTML document
        #
        """
        self.htmlOutput.write(
            "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Transitional//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\">" + "\n")
        self.htmlOutput.write("<html xmlns=\"http://www.w3.org/1999/xhtml\">" + "\n")
        self.htmlOutput.write("<head>" + "\n")
        self.htmlOutput.write("<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\" />" + "\n")
        self.htmlOutput.write("<title>" + title + "</title>" + "\n")
        self.htmlOutput.write("</head>" + "\n")
        self.htmlOutput.write("" + "\n")
        self.htmlOutput.write("<body>" + "\n")
        self.htmlOutput.write("<h1>" + heading1 + "</h1>" + "\n")
        self.htmlOutput.write("<style type=\"text/css\">" + "\n")
        self.htmlOutput.write("  table{" + "\n")
        self.htmlOutput.write(" font-size:16px;" + "\n")
        self.htmlOutput.write(" width:75%;" + "\n")
        self.htmlOutput.write(" border-collapse: collapse;" + "\n")
        self.htmlOutput.write(" border: 1px solid black;" + "\n")
        self.htmlOutput.write(" margin-left:40px;" + "\n")
        self.htmlOutput.write("  }" + "\n")
        self.htmlOutput.write("  table td{" + "\n")
        self.htmlOutput.write(" font-size:16px;" + "\n")
        self.htmlOutput.write(" border: 1px solid black;" + "\n")
        self.htmlOutput.write("  }" + "\n")
        self.htmlOutput.write("  table th{" + "\n")
        self.htmlOutput.write(" font-size:16px;" + "\n")
        self.htmlOutput.write(" border: 2px solid black;" + "\n")
        self.htmlOutput.write(" background-color: LightGray;" + "\n")
        self.htmlOutput.write(" font-weight: bold;" + "\n")
        self.htmlOutput.write("  }" + "\n")
        self.htmlOutput.write("</style>" + "\n")

    def EndHtlmOutput(self):
        """
        # EndHtlmOutput
        # Close the body and html document
        """
        self.htmlOutput.write("</body>" + "\n")
        self.htmlOutput.write("</html>" + "\n")
        self.htmlOutput.flush()

    def RawHtlmOutput(self, rawHtml):
        """
        # Write raw information to the HTML file.  It puts into whatever string you send.
        #
        # @param rawHtml         String to place in the HTML file
        """
        self.htmlOutput.write(str(rawHtml) + "\n")

    """
    # 
    # Table Generation Section
    # 
    """

    def BeginTable(self):
        """
        # Tag to start HTML table
        """
        self.htmlOutput.write(" <table>" + "\n")

    def EndTable(self):
        """
        # Tag to end HTML table
        """
        self.htmlOutput.write(" </table>" + "\n")

    def TableHeader(self, theColumns, theWidths):
        """
        # TableHeader
        # Write a header row in a table.  Assumes table already started.
        #
        # @param theColumns      Text to display in each column (a list)
        # @param theWidths        The percentage of the width for the column (a list)
        """
        self.htmlOutput.write("   <tr>" + "\n")
        for index, column in enumerate(theColumns):
            self.htmlOutput.write("  <th width=" + str(theWidths[index]) + "%>" + str(column) + "</td>\n")
        self.htmlOutput.write("   </tr>" + "\n")

    def TableData(self, theIssue, theColumns, keyColmn, firstColumnColor, title):
        """
        # TableData
        # Write the information in each cell of the table.  This table only allows 1 color change
        #
        # @param theIssue        The issue or the list of information to display
        # @param theColumns      Which elements of the list to use
        # @param keyColmn        Which element has the issue key in it, so that a hyperlink can be provided to the issue
        # @param firstColumnColor        The color, if any, of the first column
        # @param title        HTML title attribute to mouse over inforamtion
        """
        self.htmlOutput.write("   <tr>" + "\n")
        tdOpening = "<td"

        self.htmlOutput.write("   <tr>" + "\n")
        for index, column in enumerate(theColumns):
            tdOpening = "<td"
            if (index == 0):
                tdOpening += " title= \"" + title + "\""
                if (firstColumnColor):
                    tdOpening += " bgcolor=" + firstColumnColor
            tdOpening += ">"
            #
            # keyColumn is the key, so we need to make a link
            #
            if (index == keyColmn):
                self.htmlOutput.write("  " + tdOpening + "<a href=\"" + self.urlRoot + "/browse/" + str(
                    theIssue[column]) + "\" target=\"_blank\">" + str(theIssue[column]) + "</a></td>\n")
            else:
                if (len(theIssue) <= index):
                    self.htmlOutput.write("  " + tdOpening + " </td>\n")
                else:
                    self.htmlOutput.write("  " + tdOpening + str(theIssue[column]) + "</td>\n")
        self.htmlOutput.write("   </tr>" + "\n")

    def TableDataColor(self, theRow):
        """
        # Write a row of the table.  Color can change per cell, all columns sent will be displayed, and there is a specific format per each
        #
        # @param theRow         A list of dictionary entries with the following information, "text", "key", "color", "title"
        """
        self.htmlOutput.write("   <tr>" + "\n")
        tdOpening = "<td"

        self.htmlOutput.write("   <tr>" + "\n")
        for aColumn in theRow:
            tdOpening = "<td"
            if (len(aColumn["title"]) > 0):
                tdOpening += " title= \"" + str(aColumn["title"]) + "\""
            # Note: We should be using it with # in front, but currently the regular one is not, so we need to match
            #            tdOpening += " bgcolor=#"+str(aColumn["color"])
            tdOpening += " bgcolor=" + str(aColumn["color"])
            tdOpening += ">"
            if (len(aColumn["key"]) > 0):
                self.htmlOutput.write("  " + tdOpening + "<a href=\"" + self.urlRoot + "/browse/" + str(
                    aColumn["key"]) + "\" target=\"_blank\">" + str(aColumn["text"]) + "</a></td>\n")
            else:
                self.htmlOutput.write("  " + tdOpening + str(aColumn["text"]) + "</td>\n")
        self.htmlOutput.write("   </tr>" + "\n")

    """
    # 
    # Graph Generation Section
    # 
    """

    def googlePieChart(self, title, idName, data):
        """
        # Generate a pie chart using the google graph API
        # Note: The input is different than the Groovy version, which uses lists instead of dictionaries
        #
        # @param title       The issue or the list of information to display
        # @param idName      The graph ID
        # @param data        Which element has the issue key in it, so that a hyperlink can be provided to the issue
        """
        dataCount = 0
        self.htmlOutput.write("<script type=\"text/javascript\" src=\"https://www.google.com/jsapi\"></script>" + "\n")
        self.htmlOutput.write(" <script type=\"text/javascript\">" + "\n")
        self.htmlOutput.write(" google.load(\"visualization\", \"1\", {packages:[\"corechart\"]});" + "\n")
        self.htmlOutput.write(" google.setOnLoadCallback(drawChart);" + "\n")
        self.htmlOutput.write(" function drawChart() {" + "\n")
        self.htmlOutput.write("   var data = google.visualization.arrayToDataTable([" + "\n")
        for key, value in data.items():
            if (dataCount == 0):
                dataCount += 1
                self.htmlOutput.write(" ['Org',  'Count'],\n")
            else:
                # Note: This is needed to place a comma at the end and \n
                self.htmlOutput.write(",\n")
            self.htmlOutput.write(" ['" + str(key) + "', " + str(value) + "]")
        self.htmlOutput.write("\n")
        self.htmlOutput.write("\n")

        self.htmlOutput.write("   ]);" + "\n")
        self.htmlOutput.write("   var options = {" + "\n")
        self.htmlOutput.write("  title: '" + str(title) + "'" + "\n")
        self.htmlOutput.write("   };" + "\n")
        self.htmlOutput.write(
            "   var chart = new google.visualization.PieChart(document.getElementById('" + str(idName) + "'));" + "\n")
        self.htmlOutput.write("   chart.draw(data, options);" + "\n")
        self.htmlOutput.write(" }" + "\n")
        self.htmlOutput.write(" </script>" + "\n")
        self.htmlOutput.write(" <div id=\"" + str(idName) + "\" style=\"width: 900px; height: 500px;\"></div>" + "\n")

    def googleStackedColumn(self, title, idName, headerList, dataList, columnColors):
        """
        # Generate a pie chart using the google graph API
        #
        # @param title          The issue or the list of information to display
        # @param idName         The graph ID
        # @param headerList     Label for each piece of the data to be displayed
        # @param dataList       List of the data to be displayed
        # @param columnColors   Colors of the columns
        """
        dataCount = 0
        self.htmlOutput.write("<script type=\"text/javascript\" src=\"https://www.google.com/jsapi\"></script>" + "\n")
        self.htmlOutput.write(" <script type=\"text/javascript\">" + "\n")
        self.htmlOutput.write(" google.load(\"visualization\", \"1\", {packages:[\"corechart\"]});" + "\n")
        self.htmlOutput.write(" google.setOnLoadCallback(drawChart);" + "\n")
        self.htmlOutput.write(" function drawChart() {" + "\n")
        self.htmlOutput.write("   var data = google.visualization.arrayToDataTable([" + "\n")
        #
        # dataList is a list of lists of column values.   When we are at element zero we insert the header before the data
        #
        for index, valueList in enumerate(dataList):
            if (index == 0):
                self.htmlOutput.write(" [")
                for colIndex, aColumn in enumerate(headerList):
                    if (colIndex > 0):
                        self.htmlOutput.write(",")
                    self.htmlOutput.write("'" + str(aColumn) + "'")
                self.htmlOutput.write(" ],\n")
            else:
                self.htmlOutput.write(",\n")
            self.htmlOutput.write(" [")
            for valIndex, aValue in enumerate(valueList):
                if (valIndex > 0):
                    self.htmlOutput.write(",")
                self.htmlOutput.write(str(aValue))
            self.htmlOutput.write(" ]")

        self.htmlOutput.write("\n")
        self.htmlOutput.write("   ]);" + "\n")
        #
        # Set the options / colors
        #
        self.htmlOutput.write("   var options = {" + "\n")
        self.htmlOutput.write("  title: '" + str(title) + "'" + ",\n")
        if (len(columnColors) == 0):
            columnColors = ["hotpink", "cyan", "lightgreen"]
        self.htmlOutput.write("  colors: [")
        for colorIndex, aColor in enumerate(columnColors):
            if (colorIndex > 0):
                self.htmlOutput.write(",")
            self.htmlOutput.write("\"" + str(aColor) + "\"")
        self.htmlOutput.write("]," + "\n")
        self.htmlOutput.write("  isStacked: true\n")
        self.htmlOutput.write("   };" + "\n")
        self.htmlOutput.write(
            "   var chart = new google.visualization.ColumnChart(document.getElementById('" + "$idName" + "'));" + "\n")
        self.htmlOutput.write("   chart.draw(data, options);" + "\n")
        self.htmlOutput.write(" }" + "\n")
        self.htmlOutput.write(" </script>" + "\n")
        self.htmlOutput.write(" <div id=\"" + "$idName" + "\" style=\"width: 900px; height: 500px;\"></div>" + "\n")

    def googleGauge(self, title, gaugeValue, gaugeMax, yellowFrom, yellowTo, redFrom, redTo):
        """
        # Generate a pie chart using the google graph API
        #
        # @param  title         Title to appear on gauge
        # @param  gaugeValue    Value that the pointer points to on the guage
        # @param  gaugeMax      Maximum number on gauge
        # @param  yellowFrom    Value where yellow starts
        # @param  yellowTo      Value where yellow ends
        # @param  redFrom       Value where red starts
        # @param  redTo         Value where red ends
        #
        """
        self.htmlOutput.write("  <script type='text/javascript' src='https://www.google.com/jsapi'></script>" + "\n")
        self.htmlOutput.write("  <script type='text/javascript'>" + "\n")
        self.htmlOutput.write("    google.load('visualization', '1', {packages:['gauge']});" + "\n")
        self.htmlOutput.write("    google.setOnLoadCallback(drawChart);" + "\n")
        self.htmlOutput.write("    function drawChart() {" + "\n")
        self.htmlOutput.write("      var data = google.visualization.arrayToDataTable([" + "\n")
        self.htmlOutput.write("     ['Label', 'Value']," + "\n")
        self.htmlOutput.write("     ['" + str(title) + "', " + str(gaugeValue) + "]" + "\n")
        self.htmlOutput.write("  ]);" + "\n")
        self.htmlOutput.write(" " + "\n")
        self.htmlOutput.write("       var options = {" + "\n")
        self.htmlOutput.write("         max: " + str(gaugeMax) + ", " + "\n")
        self.htmlOutput.write("         yellowFrom:" + str(yellowFrom) + ", yellowTo:" + str(yellowTo) + "," + "\n")
        self.htmlOutput.write("         redFrom:" + str(redFrom) + ", redTo: " + str(redTo) + "," + "\n")
        self.htmlOutput.write("         minorTicks: 3         " + "\n")
        self.htmlOutput.write("       };" + "\n")
        self.htmlOutput.write(" " + "\n")
        self.htmlOutput.write(
            "      var chart = new google.visualization.Gauge(document.getElementById('chart_div'));" + "\n")
        self.htmlOutput.write("      chart.draw(data, options);" + "\n")
        self.htmlOutput.write("    }" + "\n")
        self.htmlOutput.write("  </script>" + "\n")
        self.htmlOutput.write("  <div id='chart_div'></div>  " + "\n")
