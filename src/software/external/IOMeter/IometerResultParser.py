#!/usr/bin/python
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Jordan Howes, Joseph Tarango
# *****************************************************************************/
# IometerResultParse.py
# IOMeter Gen3 Launcher and Parser
# Supporting IOMeter w/ QoS and Randomization

import sys
import os
import csv
import operator
import zipfile
import time
import string

import win32com.client # conda install -c anaconda pywin32

class IometerResult:
	"""Holds IOMeter Test Info and Result Data"""
	def __init__(self, pRand, pRead, requestSize, qd, spanSize, time, avgRng, target, resultFilename, qosTime, qosTarget):
		self.pRand = pRand
		self.pRead = pRead
		self.requestSize = requestSize
		self.qd = qd
		self.spanSize = spanSize
		self.time = time
		self.avgRng = avgRng
		self.target = target
		self.resultFilename = resultFilename
		self.qosTime = qosTime
		self.qosTarget = qosTarget
		self.numWorkers = 0

		#Scores
		self.iops = None
		self.mbps = None
		self.iopsMin = None
		self.iopsMax = None
		self.qosTotals = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
		self.qosSum = 0
		self.instResults = [] # [[Iops, Average Lat, Max Lat],...] 
		self.qosResults = [] # [[Bin1,Bin2,Bin3,...],...]
		self.qosCompressedResults = [] # Same format as Results, but summed over windows of qosTime entries (presumably seconds)
		
		#Qos Merit
		self.qosMerit = []
		self.qosMeritTotals = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
		self.qosMeritSum = -1
		
		# Qos fail flag for coloring
		self.qosFailFlag = 0
		
		self.getScore()
		
		# qosMeritTotals will be a list of bins for the merit period (avgRng)
		# qosMeritSum will be the sum of them.

		# If I wanted to switch to the compressed data, this is going in the right direction.
		#meritStripCount = time/qosTime - avgRng/qosTime
		#self.qosMerit = self.qosCompressedResults[meritStripCount:]

		self.qosMerit = self.qosResults[(len(self.qosResults)-self.avgRng):]

		for item in self.qosMerit:
			self.qosMeritTotals = [sum(pair) for pair in zip(item, self.qosMeritTotals)]
		self.qosMeritSum = sum(self.qosMeritTotals)
		
		
		# Output each result line item to the CSV file as they are parsed. 
		# Not sure if this the best place for it, but it does have access to all of the required data.
		outFile = open("parsedResults.csv", "a")
		sys.stdout = outFile
		#For reference
		#print "HEADER,pRand,pRead,accSize,qDepth,spanSize,runTime,measureTime,targetIops,iops,mbps,totalCommands,<50 uS,<100 uS,<200 uS,<500 uS,<1 mS,<2 mS,<5 mS,<10 mS,<15 mS,<20 mS,<30 mS,<50 mS,<100 mS,<200 mS,<500 mS,<1 S,<2 S,<4.7 S,<5 S,<10 S,> 10 S"
		print("RESULT,%d,%d,%d,%d,%d,%d,%d,%d,%f,%f,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d"%( self.pRand, self.pRead, self.requestSize, self.qd, self.spanSize, self.time, self.avgRng, self.target, self.iops, self.mbps,
		self.qosSum, self.qosTotals[0], self.qosTotals[1], self.qosTotals[2], self.qosTotals[3], self.qosTotals[4], self.qosTotals[5], self.qosTotals[6], self.qosTotals[7], self.qosTotals[8], self.qosTotals[9], 
		self.qosTotals[10], self.qosTotals[11], self.qosTotals[12], self.qosTotals[13], self.qosTotals[14], self.qosTotals[15], self.qosTotals[16], self.qosTotals[17], self.qosTotals[18], self.qosTotals[19], self.qosTotals[20] ))
		sys.stdout = sys.__stdout__
		outFile.close()	
		
	def getScore(self):
		try:
			resultFile = open(self.resultFilename)
		except IOError:
			print("ERROR - Couldn't find file ", self.resultFilename)
			self.iops = -1
			self.mbps = -1
			return
		
		resultCsv = csv.reader(resultFile)
		qosCount = 0

		for row in resultCsv:
			if(len(row) >= 65): # No out of range errors...change from 21 to 65 for QOS
				if(row[1] == "WORKER"): # Only valid data.
					worker, workerCount = map(int,string.split(row[2], "of"))  # New code for multiworker
					self.numWorkers = workerCount
					if( worker == 1):  # if we are on the first worker do stuff...
						#First we need to correct for other workers!  This is all preloaded so the rest of the code just works.
						toUpdate = [7,15,20,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77] #Every row item we will touch...
						if(workerCount > 1): # if more than one worker
							for workerIdx in range(1,workerCount): # loop on each worker
								nextRow = resultCsv.next()
								for updateIdx in toUpdate: # add the worker to the base row value for toUpdate item)
									if(updateIdx == 7): # if it is the iops
										row[updateIdx] = float(row[updateIdx]) + float(nextRow[updateIdx])
									elif(updateIdx == 15): # if it is the average latency
										row[updateIdx] = float(row[updateIdx]) + float(nextRow[updateIdx])
										if(workerIdx == (workerCount - 1)): #if we have added all the workers divide it out by num for average.
											row[updateIdx] = row[updateIdx]/workerCount
									elif(updateIdx == 20): #if it is the max latency
										row[updateIdx] = max(float(row[updateIdx]), float(nextRow[updateIdx]))
									else:
										row[updateIdx] = int(row[updateIdx]) + int(nextRow[updateIdx])
									
						# continue with work, now the row values should contain every workers values.  Map it to real numbers just in case
						self.instResults.append(map(float,[row[7], row[15], row[20]])) # [Iops, Average Lat, Max Lat]
						self.qosResults.append(map(int,[row[57], row[58], row[59], row[60], row[61], row[62], row[63],
							row[64], row[65], row[66], row[67], row[68], row[69], row[70], row[71], row[72],
							row[73], row[74], row[75], row[76], row[77]]))
						
						self.qosTotals = [sum(pair) for pair in zip(self.qosTotals, self.qosResults[len(self.qosResults)-1])] # Sum the totals and the last inserted
						
						#  If at the top of a count, set the qoscurrent equal to the current qos event
						if(qosCount == 0):
							qosCurrent = self.qosResults[len(self.qosResults)-1]
						#  Else add the last read qos to the current sum
						else:
							qosCurrent = [sum(pair) for pair in zip(qosCurrent, self.qosResults[len(self.qosResults)-1])] # Sum the current and the last inserted
						
						qosCount += 1 # Increment the count
						# If qosCount equals qosTime dump the data to the compressed result and reset count
						if(qosCount == self.qosTime):
							self.qosCompressedResults.append(qosCurrent)
							qosCount = 0

		#update the QD to correct for multiwoker
		self.qd = self.qd * workerCount
		
		average = 0
		
		if(len(self.instResults)-self.avgRng < 0):
			print("ERROR - Trying to average over a range greater than collected data. Averaging over the entire range.")
			self.avgRng = len(self.instResults)
		for i in range(len(self.instResults)-self.avgRng,len(self.instResults)):
			average = average + self.instResults[i][0]
			#If first pass set min and max to current.
			if( self.iopsMin == None ):
				self.iopsMin = self.instResults[i][0]
				self.iopsMax = self.instResults[i][0]
			#IF lower than current min make new min.
			if( self.instResults[i][0] < self.iopsMin ):
				self.iopsMin = self.instResults[i][0]
			#If higher than current max make new max.
			if( self.instResults[i][0] > self.iopsMax ):
				self.iopsMax = self.instResults[i][0]

		average = average / self.avgRng

		self.iops = average
		self.mbps = (average * self.requestSize / 1048576)  # Was 4096, I assume a bug..fixed now.
		
		self.qosSum = sum(self.qosTotals)

		resultFile.close()
		
		
	#	6/14/10 - Result Archiving Moved to csvZipper.py
	
	#	resArchive = zipfile.ZipFile("resultArchive.zip", 'a')
	#	resArchive.write(self.resultFilename)
	#	resArchive.write(self.resultFilename[4:])
	#	resArchive.close()
		

class IometerResultParser:
	"""Holds IOMeter Test Info"""
	def __init__(self, filename, outFilename):
		self.outFilename = outFilename
		self.resultList = [] # List of all results from outfile, should be empty after organize data is called.  CANDIDATE FOR PUSH TO FUNCTION CALL
		self.outputArray = [] # 2D array of orgnaized results, it will contain the result list after organize data is called
		self.xHeaders1 = [] # Headers for the x axis of the output array.
		self.xHeaders2 = []
		self.yHeaders1 = [] # Headers for the y axis of the output array.
		self.yHeaders2 = []
		
		# Create the CSV output file and heads
		# The rest of the ouput code for the CSV lives inside the Result object, not very clean but it was the easiest place to sneak in the output.
		outFile = open("parsedResults.csv", "w")
		sys.stdout = outFile
		print("HEADER,pRand,pRead,accSize,qDepth,spanSize,runTime,measureTime,targetIops,iops,mbps,totalCommands,<50 uS,<100 uS,<200 uS,<500 uS,<1 mS,<2 mS,<5 mS,<10 mS,<15 mS,<20 mS,<30 mS,<50 mS,<100 mS,<200 mS,<500 mS,<1 S,<2 S,<4.7 S,<5 S,<10 S,> 10 S")
		sys.stdout = sys.__stdout__
		outFile.close()
		
		resultCsv = csv.reader(open(filename))
		
		for row in resultCsv:
			if(row[0] == "RESULT"):
#				print row
				self.resultList.append(IometerResult(int(row[1]),int(row[2]),int(row[3]),int(row[4]),int(row[5]),int(row[6]),int(row[7]),int(row[8]),row[9],int(row[10]),
				[float(row[11]),float(row[12]),float(row[13]),float(row[14]),float(row[15]),float(row[16]),float(row[17]),float(row[18]),float(row[19]),float(row[20]),
				float(row[21]),float(row[22]),float(row[23]),float(row[24]),float(row[25]),float(row[26]),float(row[27]),float(row[28]),float(row[29]),float(row[30]),
				float(row[31])]))
		
		# Count the data points
		self.dataCount = len(self.resultList)
		
		self.organizeData()
		self.outputData()
	
	def organizeData(self):
		pRand = []
		u_pRand = []
		
		pRead = []
		u_pRead = []
		
		requestSize = []
		u_requestSize = []
		
		qd = []
		u_qd = []
	
		# Build lists of each setting
		for i in range(len(self.resultList)):
			pRand.append(self.resultList[i].pRand)
			pRead.append(self.resultList[i].pRead)
			requestSize.append(self.resultList[i].requestSize)
			qd.append(self.resultList[i].qd)
		
#		# Build unique lists of each setting
		k_pRand = {} 
		for i in pRand: 
			k_pRand[i] = 1 
		u_pRand = k_pRand.keys()

		k_pRead = {} 
		for i in pRead: 
			k_pRead[i] = 1 
		u_pRead = k_pRead.keys()

		k_requestSize = {} 
		for i in requestSize: 
			k_requestSize[i] = 1 
		u_requestSize = k_requestSize.keys()
		
		k_qd = {} 
		for i in qd: 
			k_qd[i] = 1 
		u_qd = k_qd.keys()
		
		u_pRand.sort()
		u_pRead.sort()
		u_requestSize.sort()
		u_qd.sort()
				

		self.xHeaders1.append("")
		self.xHeaders1.append("")
		self.xHeaders2.append("")
		self.xHeaders2.append("")
		self.yHeaders1.append("")
		self.yHeaders1.append("")
		self.yHeaders2.append("")
		self.yHeaders2.append("")
		
		xSpaceFlag = 0
		ySpaceFlag = 0
		xHeaderFlag = 1
		#move left to right then down
		for i_pRead in u_pRead:
			self.yHeaders1.append("%i%% Read"%i_pRead)
			ySpaceFlag = 0
			for i_requestSize in u_requestSize:
				lineArray = []
				self.yHeaders2.append("%i"%i_requestSize)
				if(ySpaceFlag): self.yHeaders1.append("")
				ySpaceFlag = 1
				for i_pRand in u_pRand:
					if(xHeaderFlag): 
						self.xHeaders1.append("%i%% Random"%i_pRand)
						xSpaceFlag = 0
					for i_qd in u_qd:
						if(xHeaderFlag):
							self.xHeaders2.append("QD %i"%i_qd)
							if(xSpaceFlag): self.xHeaders1.append("")
							xSpaceFlag = 1
						flag = 1
						for ioResult in self.resultList:
							if( (ioResult.pRead == i_pRead) and (ioResult.pRand == i_pRand) and (ioResult.requestSize == i_requestSize) and (ioResult.qd == i_qd) ):
								lineArray.append(ioResult)  # Previously appended ioResult.iops..now appending the entire result structure.
								flag = 0
								self.resultList.remove(ioResult) # Remove it from result list to save space and shorten this loop next time.
						if flag: lineArray.append("") # Append a blank space if there is no data.
				self.outputArray.append(lineArray)
				xHeaderFlag = 0

		#  Transpose Y1
		transY1 = []
		for x in self.yHeaders1:
			transY1.append([x])
		self.yHeaders1 = transY1
		
		#  Transpose Y2
		transY2 = []
		for x in self.yHeaders2:
			transY2.append([x])
		self.yHeaders2 = transY2
		
	
	def outputData(self):
		#Index into excel alpha.  Note the double A at the start, this is so that the index can match the Y axis that also starts on 1, not 0.
		alphaIndex = ["A", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", 
			"AA", "AB", "AC", "AD", "AE", "AF", "AG", "AH", "AI", "AJ", "AK", "AL"]

		#xlApp = win32com.client.Dispatch( "Excel.Application" )
		xlApp = win32com.client.gencache.EnsureDispatch("Excel.Application") # Fix for makepy dependancy.
		filename = os.getcwd()+"\\"+self.outFilename
		
		xlApp.Visible = False
		xlApp.DisplayAlerts = False
		xlApp.SheetsInNewWorkbook = (self.dataCount + 1)
		
		if os.path.exists(filename):
			xlBook = xlApp.Workbooks.Open(filename)
#			print "Opened existing workbook"
		else:
			xlBook = xlApp.Workbooks.Add()
#			print "Added new workbook"

		xlSheet = xlBook.Worksheets(1)
		xlSheet.Name = "Results"
		
		#  Print the first xHeader line
		#  Calc the range based on the length of the line coverted to excel letters.
		xlRng = xlSheet.Range("A1:%s1" %(alphaIndex[len(self.xHeaders1)]) )
		xlRng.Value = self.xHeaders1
		xlRng.Font.Size = 12
		xlRng.Font.Bold = "True"
		xlRng.Interior.ColorIndex = 41
		xlRng.Font.ColorIndex = 2
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignRight
		
		#  Print the first xHeader line for MB/s
		#  Calc the range based on the length of the line coverted to excel letters.
		xlRng = xlSheet.Range("A%d:%s%d" %(len(self.outputArray) + 4, alphaIndex[len(self.xHeaders1)], len(self.outputArray) + 4 ) )
		xlRng.Value = self.xHeaders1
		xlRng.Font.Size = 12
		xlRng.Font.Bold = "True"
		xlRng.Interior.ColorIndex = 41
		xlRng.Font.ColorIndex = 2
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignRight
		
		#  Print the first xHeader line for Iops stability
		#  Calc the range based on the length of the line coverted to excel letters.
		xlRng = xlSheet.Range("A%d:%s%d" %((len(self.outputArray)*2) + 7, alphaIndex[len(self.xHeaders1)], (len(self.outputArray)*2) + 7 ) )
		xlRng.Value = self.xHeaders1
		xlRng.Font.Size = 12
		xlRng.Font.Bold = "True"
		xlRng.Interior.ColorIndex = 41
		xlRng.Font.ColorIndex = 2
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignRight
		
		#  Print the second xHeader line
		xlRng = xlSheet.Range("A2:%s2" %(alphaIndex[len(self.xHeaders1)]) )
		xlRng.Value = self.xHeaders2
		xlRng.Font.Size = 12
		xlRng.Font.Bold = "True"
		xlRng.Interior.ColorIndex = 41
		xlRng.Font.ColorIndex = 2
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignRight
		
		#  Print the second xHeader line for MB/s
		xlRng = xlSheet.Range("A%d:%s%d" %(len(self.outputArray) + 5,alphaIndex[len(self.xHeaders1)],len(self.outputArray) + 5 ) )
		xlRng.Value = self.xHeaders2
		xlRng.Font.Size = 12
		xlRng.Font.Bold = "True"
		xlRng.Interior.ColorIndex = 41
		xlRng.Font.ColorIndex = 2
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignRight
		
		#  Print the second xHeader line for iops stability
		xlRng = xlSheet.Range("A%d:%s%d" %((len(self.outputArray)*2) + 8,alphaIndex[len(self.xHeaders1)],(len(self.outputArray)*2) + 8 ) )
		xlRng.Value = self.xHeaders2
		xlRng.Font.Size = 12
		xlRng.Font.Bold = "True"
		xlRng.Interior.ColorIndex = 41
		xlRng.Font.ColorIndex = 2
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignRight
		
		#  Print the first yHeader line
		xlRng = xlSheet.Range("A1:A%d" %(len(self.yHeaders1)) )
		xlRng.Value = self.yHeaders1
		xlRng.Font.Size = 12
		xlRng.Font.Bold = "True"
		xlRng.Interior.ColorIndex = 41
		xlRng.Font.ColorIndex = 2
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignRight
		
		#  Print the first yHeader line for MB/s
		xlRng = xlSheet.Range("A%d:A%d" %(len(self.outputArray)+4,len(self.yHeaders1)+len(self.outputArray)+3) )
		xlRng.Value = self.yHeaders1
		xlRng.Font.Size = 12
		xlRng.Font.Bold = "True"
		xlRng.Interior.ColorIndex = 41
		xlRng.Font.ColorIndex = 2
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignRight
		
		#  Print the first yHeader line for iops stability
		xlRng = xlSheet.Range("A%d:A%d" %((len(self.outputArray)*2)+7,len(self.yHeaders1)+(len(self.outputArray)*2)+6) )
		xlRng.Value = self.yHeaders1
		xlRng.Font.Size = 12
		xlRng.Font.Bold = "True"
		xlRng.Interior.ColorIndex = 41
		xlRng.Font.ColorIndex = 2
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignRight
		
		#  Print the second yHeader line
		xlRng = xlSheet.Range("B1:B%d" %(len(self.yHeaders2)) )
		xlRng.Value = self.yHeaders2
		xlRng.Font.Size = 12
		xlRng.Font.Bold = "True"
		xlRng.Interior.ColorIndex = 41
		xlRng.Font.ColorIndex = 2
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignRight
		
		#  Print the second yHeader line for MB/s
		xlRng = xlSheet.Range("B%d:B%d" %(len(self.outputArray)+4,len(self.yHeaders2)+len(self.outputArray)+3) )
		xlRng.Value = self.yHeaders2
		xlRng.Font.Size = 12
		xlRng.Font.Bold = "True"
		xlRng.Interior.ColorIndex = 41
		xlRng.Font.ColorIndex = 2
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignRight
		
		#  Print the second yHeader line for iops stability
		xlRng = xlSheet.Range("B%d:B%d" %((len(self.outputArray)*2)+7,len(self.yHeaders2)+(len(self.outputArray)*2)+6) )
		xlRng.Value = self.yHeaders2
		xlRng.Font.Size = 12
		xlRng.Font.Bold = "True"
		xlRng.Interior.ColorIndex = 41
		xlRng.Font.ColorIndex = 2
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignRight

		# Labels
		xlRng =  xlSheet.Range("A1")
		xlRng.Value = "Iops"
		xlRng = xlSheet.Range("A%d" % (len(self.outputArray) + 4))
		xlRng.Value = "MiBps"
		xlRng = xlSheet.Range("A%d" % (len(self.outputArray)*2 + 7))
		xlRng.Value = "Iops Stability"


		## Print IOPS & Create the detail sheet
		xIndex = 3  # Needs to be referenced to a letter combo
		yIndex = 3  # Exact reference to a line number
		sheetIndex = 2  # Only here because ordering sheets in excel is hard.  Optimal solution is to create sheet on demand.
		for row in self.outputArray:
			for item in row:
				if(item != ""):
					xlRng = xlSheet.Range("%s%d" %( alphaIndex[xIndex], yIndex))#xlRng = xlBook.ActiveSheet.Range("%s%d" %( alphaIndex[xIndex], yIndex))
					xlRng.Value = item.iops
					
					# Create detail sheet
					self.addDetailSheet(xlBook.Worksheets(sheetIndex), item)
					
					# Create Link
					xlSheet.Hyperlinks.Add(
						Anchor=xlRng, 
						Address="", 
						SubAddress="'Rnd=%d_Rd=%d_QD=%d_%dk'!A1" %(item.pRand, item.pRead, item.qd, (float(item.requestSize)/1024))
						)
					
					sheetIndex += 1  # Again, only here because ordering sheets in excel is hard.
					
					# Set style formatting
					
					if( item.target == 0 ):
						xlRng.Style = "Normal"
					elif( item.iops > 0 ):
						if( item.iops < item.target ):
							# If less than the target make it red.
							xlRng.Style = "Bad"
						elif( item.iops < (item.target * 1.05) ):
							# If not better than 5% above the target it is yellow.
							xlRng.Style = "Neutral"
						else:
							# If better than 5% above the target it is green.
							xlRng.Style = "Good"
					
					xlRng.Font.Bold = True
					
					if( item.qosFailFlag == 0):
						xlRng.Font.ThemeColor = win32com.client.constants.xlThemeColorLight1
					elif( item.qosFailFlag == 1):
						xlRng.Font.Color = -16776961
					elif( item.qosFailFlag == -1):
						xlRng.Font.Color = -11489280
						
					xlRng.NumberFormat = 0
					
				xIndex += 1
			yIndex += 1
			xIndex = 3  # Match above initial conditions.
		
		
		##  Print MB/s
		xIndex = 3   # Needs to be referenced to a letter combo
		yIndex = 6 + len(self.outputArray)   # Exact reference to a line number
		for row in self.outputArray:
			for item in row:
				if(item != ""):
					xlRng = xlSheet.Range("%s%d" %( alphaIndex[xIndex], yIndex))#xlRng = xlBook.ActiveSheet.Range("%s%d" %( alphaIndex[xIndex], yIndex))
					xlRng.Value = item.mbps
					
										
					# Create Link
					xlSheet.Hyperlinks.Add(
						Anchor=xlRng, 
						Address="", 
						SubAddress="'Rnd=%d_Rd=%d_QD=%d_%dk'!A1" %(item.pRand, item.pRead, item.qd, (float(item.requestSize)/1024))
						)
					
					# Set style formatting
					if( item.target == 0 ):
						xlRng.Style = "Normal"
					elif( item.iops > 0 ):
						if( item.iops < item.target ):
							# If less than the target make it red.
							xlRng.Style = "Bad"
						elif( item.iops < (item.target * 1.05) ):
							# If not better than 5% above the target it is yellow.
							xlRng.Style = "Neutral"
						else:
							# If better than 5% above the target it is green.
							xlRng.Style = "Good"
					
					xlRng.Font.Bold = True
					
					if( item.qosFailFlag == 0):
						xlRng.Font.ThemeColor = win32com.client.constants.xlThemeColorLight1
					elif( item.qosFailFlag == 1):
						xlRng.Font.Color = -16776961
					elif( item.qosFailFlag == -1):
						xlRng.Font.Color = -11489280
						
					xlRng.NumberFormat = "0.00"
					
				xIndex += 1
			yIndex += 1
			xIndex = 3  # Match above initial conditions.
			
			
		##  Print Iops Stability
		xIndex = 3   # Needs to be referenced to a letter combo
		yIndex = 9 + 2*len(self.outputArray)   # Exact reference to a line number
		for row in self.outputArray:
			for item in row:
				if(item != ""):
					xlRng = xlSheet.Range("%s%d" %( alphaIndex[xIndex], yIndex))#xlRng = xlBook.ActiveSheet.Range("%s%d" %( alphaIndex[xIndex], yIndex))
					xlRng.Value = item.iopsMin/item.iops
					
										
					# Create Link
					xlSheet.Hyperlinks.Add(
						Anchor=xlRng, 
						Address="", 
						SubAddress="'Rnd=%d_Rd=%d_QD=%d_%dk'!A1" %(item.pRand, item.pRead, item.qd, (float(item.requestSize)/1024))
						)
					
					# Set style formatting, green for 10%, yellow for 20%, red for >20%
					if(item.iopsMin/item.iops >= 0.9):
						xlRng.Style = "Good"
					elif(item.iopsMin/item.iops >= 0.8):
						xlRng.Style = "Neutral"
					else:
						xlRng.Style = "Bad"

					
					xlRng.Font.Bold = True
					
					#if( item.qosFailFlag == 0):
					#	xlRng.Font.ThemeColor = win32com.client.constants.xlThemeColorLight1
					#elif( item.qosFailFlag == 1):
					#	xlRng.Font.Color = -16776961
					#elif( item.qosFailFlag == -1):
					#	xlRng.Font.Color = -11489280
						
					xlRng.NumberFormat = "0.00"
					
				xIndex += 1
			yIndex += 1
			xIndex = 3  # Match above initial conditions.
		
		# Autofit all of the rows/cols
		xlSheet.Cells.Select()
		xlSheet.Cells.EntireColumn.AutoFit()
		xlSheet.Range("A1").Select()
		
		# More consistant column size in the data area.
		xlSheet.Columns("C:%s"%(alphaIndex[len(self.outputArray)+2])).ColumnWidth = 14.29

		
		xlBook.SaveAs(filename)
		xlBook.Close(0)
		xlApp.Quit()
		
	def addDetailSheet(self, xlSheet, ioResult):
		#  Sheet Title
		xlSheet.Name = 	"Rnd=%d_Rd=%d_QD=%d_%dk" %(ioResult.pRand, ioResult.pRead, ioResult.qd, (float(ioResult.requestSize)/1024))
		
		#  Create the back button and link it to the main page.
		xlRng = xlSheet.Range("A1")
		xlSheet.Hyperlinks.Add(
			Anchor=xlRng, 
			Address="", 
			TextToDisplay="BACK", 
			SubAddress="'Results'!A1"
			)
		xlRng.Font.Bold = 1
		xlRng.Font.Color = -16776961
		xlRng.Font.Size = 18
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignCenter
				
		#  Title
		xlRng = xlSheet.Range("A2:D2")
		xlRng.Value = xlSheet.Name
		xlRng.Merge()
		xlRng.Font.Bold = 1
		
		#  Datablock
		xlRng = xlSheet.Range("A3:B3")
		xlRng.Value = "Percent Random"
		xlRng.Merge()
		xlRng.Font.Bold = 1
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		xlRng = xlSheet.Range("A4:B4")
		xlRng.Value = str(ioResult.pRand) + "%"
		xlRng.Merge()
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		
		xlRng = xlSheet.Range("C3:D3")
		xlRng.Value = "Percent Read"
		xlRng.Merge()
		xlRng.Font.Bold = 1
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		xlRng = xlSheet.Range("C4:D4")
		xlRng.Value = str(ioResult.pRead) + "%"
		xlRng.Merge()
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		
		xlRng = xlSheet.Range("A5:B5")
		xlRng.Value = "Request Size"
		xlRng.Merge()
		xlRng.Font.Bold = 1
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		xlRng = xlSheet.Range("A6:B6")
		xlRng.Value = str(float(ioResult.requestSize)/1024) + " KB"
		xlRng.Merge()
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		
		xlRng = xlSheet.Range("C5:D5")
		xlRng.Value = "Queue Depth"
		xlRng.Merge()
		xlRng.Font.Bold = 1
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		xlRng = xlSheet.Range("C6:D6")
		xlRng.Value = ioResult.qd
		xlRng.Merge()
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		
		xlRng = xlSheet.Range("A7:B7")
		xlRng.Value = "Span Size"
		xlRng.Merge()
		xlRng.Font.Bold = 1
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		xlRng = xlSheet.Range("A8:B8")
		xlRng.Value = str(ioResult.spanSize) + " LBA"
		xlRng.Merge()
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		
		xlRng = xlSheet.Range("C7:D7")
		xlRng.Value = "Performance Target"
		xlRng.Merge()
		xlRng.Font.Bold = 1
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		xlRng = xlSheet.Range("C8:D8")
		xlRng.Value = str(ioResult.target) + " Iops"
		xlRng.Merge()
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		
		xlRng = xlSheet.Range("A9:B9")
		xlRng.Value = "Run Time"
		xlRng.Merge()
		xlRng.Font.Bold = 1
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		xlRng = xlSheet.Range("A10:B10")
		xlRng.Value = str(ioResult.time) + " s"
		xlRng.Merge()
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		
		xlRng = xlSheet.Range("C9:D9")
		xlRng.Value = "Average Window"
		xlRng.Merge()
		xlRng.Font.Bold = 1
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		xlRng = xlSheet.Range("C10:D10")
		xlRng.Value = str(ioResult.avgRng) + " s"
		xlRng.Merge()
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		
		xlRng = xlSheet.Range("A11:D11")
		xlRng.Value = "Result Filename"
		xlRng.Merge()
		xlRng.Font.Bold = 1
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		xlRng = xlSheet.Range("A12:D12")
		xlRng.Value = ioResult.resultFilename
		xlRng.Merge()
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft


		#  Measured Data
		xlRng = xlSheet.Range("A13:B13")
		xlRng.Value = "Measured Iops"
		xlRng.Merge()
		xlRng.Font.Bold = 1
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		xlRng = xlSheet.Range("A14:B14")
		xlRng.Value = str(ioResult.iops)
		xlRng.Merge()
		xlRng.NumberFormat = "0.00"
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		
		xlRng = xlSheet.Range("C13:D13")
		xlRng.Value = "Measured MB/s"
		xlRng.Merge()
		xlRng.Font.Bold = 1
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		xlRng = xlSheet.Range("C14:D14")
		xlRng.Value = str(ioResult.mbps)
		xlRng.Merge()
		xlRng.NumberFormat = "0.00"
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		
		#IOps Stability
		xlRng = xlSheet.Range("A15:B15")
		xlRng.Value = "Iops Stability"
		xlRng.Merge()
		xlRng.Font.Bold = 1
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		xlRng = xlSheet.Range("C15:D15")
		xlRng.Value = str(ioResult.iopsMin/ioResult.iops)
		if(ioResult.iopsMin/ioResult.iops >= 0.9):
			xlRng.Style = "Good"
		elif(ioResult.iopsMin/ioResult.iops >= 0.8):
			xlRng.Style = "Neutral"
		else:
			xlRng.Style = "Bad"
		xlRng.Merge()
		xlRng.NumberFormat = "0.00"
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignLeft
		
		#  Percent from target, calculated and colored only if there is a target.
		xlRng = xlSheet.Range("A16:D16")
		xlRng.Value = "Percent from Target"
		xlRng.Merge()
		xlRng.Font.Bold = 1
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignCenter
		xlRng = xlSheet.Range("A17:D17")
		xlRng.Merge()
		xlRng.Font.Bold = 1
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignCenter
		if( ioResult.target > 0 ):
			xlRng.Value = float((ioResult.iops/ioResult.target) - 1)
			xlRng.Style
			xlRng.NumberFormat = "0.00%"
			if( ioResult.iops < ioResult.target ):
				# If less than the target make it red.
				xlRng.Style = "Bad"
			elif( ioResult.iops < (ioResult.target * 1.05) ):
				# If not better than 5% above the target it is yellow.
				xlRng.Style = "Neutral"
			else:
				# If better than 5% above the target it is green.
				xlRng.Style = "Good"
		else:
			xlRng.Value = "N/A"
			
		#  Header for QoS
		xlRng = xlSheet.Range("B19:C19")
		xlRng.Value = ["% Target", "% Measured"]
		xlRng.Font.Bold = 1
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignCenter
		xlRng = xlSheet.Range("D19:C19")
		xlRng.Merge()
		xlRng = xlSheet.Range("A18:D18")
		xlRng.Value = "Full Run QoS"
		xlRng.Font.Bold = 1
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignCenter
		xlRng.Merge()
		
		
		#  Header for Merit QoS
		xlRng = xlSheet.Range("B42:C42")
		xlRng.Value = ["% Target", "% Measured"]
		xlRng.Font.Bold = 1
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignCenter
		xlRng = xlSheet.Range("D42:C42")
		xlRng.Merge()
		xlRng = xlSheet.Range("A41:D41")
		xlRng.Value = "Average Range QoS"
		xlRng.Font.Bold = 1
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignCenter
		xlRng.Merge()
		
		#  QoS Bins
		xlRng = xlSheet.Range("A20:A40")
		xlRng.Value = [["<50 uS"],["<100 uS"],["<200 uS"],["<500 uS"],["<1 mS"],["<2 mS"],["<5 mS"],["<10 mS"],["<15 mS"],["<20 mS"],["<30 mS"],["<50 mS"],
						["<100 mS"],["<200 mS"],["<500 mS"],["<1 S"],["<2 S"],["<4.7 S"],["<5 S"],["<10 S"],["> 10 S"]]
		xlRng.Font.Bold = 1
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignRight
		
		#  Merit QoS Bins
		xlRng = xlSheet.Range("A43:A63")
		xlRng.Value = [["<50 uS"],["<100 uS"],["<200 uS"],["<500 uS"],["<1 mS"],["<2 mS"],["<5 mS"],["<10 mS"],["<15 mS"],["<20 mS"],["<30 mS"],["<50 mS"],
						["<100 mS"],["<200 mS"],["<500 mS"],["<1 S"],["<2 S"],["<4.7 S"],["<5 S"],["<10 S"],["> 10 S"]]
		xlRng.Font.Bold = 1
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignRight
		
		#  Qos Targets
		transQosTarget = []
		for x in ioResult.qosTarget:
			transQosTarget.append([x])
		xlRng = xlSheet.Range("B20:B40")
		xlRng.Value = transQosTarget
		xlRng.NumberFormat = "0.0000"
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignCenter
		
		#  Merit Qos Targets
		transQosTarget = []
		for x in ioResult.qosTarget:
			transQosTarget.append([x])
		xlRng = xlSheet.Range("B43:B63")
		xlRng.Value = transQosTarget
		xlRng.NumberFormat = "0.0000"
		xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignCenter
		
		#  Qos Totals
		count = 0
		lastPercent = 0.0
		qosResults = [] # For the CSV output.... What does this guy do?  Only referenced when items are added.
		for sum in ioResult.qosTotals:
			xlRng = xlSheet.Range("C%d:D%d"%(20+count, 20+count))
			# Add the current percent to this items percent
			lastPercent += (float(sum)/float(ioResult.qosSum)) * 100
			
			# For the csv output.
			qosResults.append(lastPercent)
			
			xlRng.Value = lastPercent		
			xlRng.NumberFormat = "0.0000"
			xlRng.Merge()
			xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignCenter
			
			#  Having all kinds of issues with this one, it is gonna look ugly but work.
			#  The idea is, if the % Measured is 100, or the target is zero it will be green.
			if(ioResult.qosTarget[count] == 0):
				xlRng.Style = "Good"
				ioResult.qosFailFlag = -1 # Push back the lack of a QoS Target.
			elif(lastPercent >= 99.99995):
				xlRng.Style = "Good"
			elif(ioResult.qosTarget[count] == 0):
				xlRng.Style = "Good"
				ioResult.qosFailFlag = -1 # Push back the lack of a QoS Target.
			elif(lastPercent < ioResult.qosTarget[count]):
				xlRng.Style = "Bad"
				ioResult.qosFailFlag = 1 # Push this failure back to the color on the chart.
			elif(lastPercent <= (ioResult.qosTarget[count] + 0.05)):
				xlRng.Style = "Neutral"
			else:
				xlRng.Style = "Good"
			count += 1
			
		#  Merit Qos Totals
		count = 0
		lastPercent = 0.0
#		qosResults = [] # For the CSV output.
		for sum in ioResult.qosMeritTotals:
			xlRng = xlSheet.Range("C%d:D%d"%(43+count, 43+count))
			# Add the current percent to this items percent
			lastPercent += (float(sum)/float(ioResult.qosMeritSum)) * 100
			
			xlRng.Value = lastPercent		
			xlRng.NumberFormat = "0.0000"
			xlRng.Merge()
			xlRng.HorizontalAlignment = win32com.client.constants.xlHAlignCenter
			
			#  Having all kinds of issues with this one, it is gonna look ugly but work.
			#  The idea is, if the % Measured is 100, or the target is zero it will be green.
			if(ioResult.qosTarget[count] == 0):
				xlRng.Style = "Good"
#				ioResult.qosFailFlag = -1 # Push back the lack of a QoS Target.
			elif(lastPercent >= 99.99995):
				xlRng.Style = "Good"
			elif(ioResult.qosTarget[count] == 0):
				xlRng.Style = "Good"
#				ioResult.qosFailFlag = -1 # Push back the lack of a QoS Target.
			elif(lastPercent < ioResult.qosTarget[count]):
				xlRng.Style = "Bad"
#				ioResult.qosFailFlag = 1 # Push this failure back to the color on the chart.
			elif(lastPercent <= (ioResult.qosTarget[count] + 0.05)):
				xlRng.Style = "Neutral"
			else:
				xlRng.Style = "Good"
			count += 1
			
			
		#  Paste the second by second data.
		xlRng = xlSheet.Range("BA1:BC1")
		xlRng.Value = ["Iops", "Average Latency", "Max Latency"]
		xlRng.Font.Bold = 1
		xlRng = xlSheet.Range("BA2:BC%d" %(len(ioResult.instResults)+1)) # +1 because we start at 2.
		xlRng.Value = ioResult.instResults
		xlRng.NumberFormat = "0.000" # Round to the microsecond.
		xlRng = xlSheet.Range("BA2:BA%d" %(len(ioResult.instResults)+1)) # +1 because we start at 2.
		xlRng.NumberFormat = "0" # Round off iops.
		
		#  Past Qos Compressed Data
		xlRng = xlSheet.Range("BM1:CG1")
		xlRng.Value = ["<50 uS","<100 uS","<200 uS","<500 uS","<1 mS","<2 mS","<5 mS","<10 mS","<15 mS","<20 mS","<30 mS","<50 mS",
						"<100 mS","<200 mS","<500 mS","<1 S","<2 S","<4.7 S","<5 S","<10 S","> 10 S"]
		xlRng.Font.Bold = 1
		xlRng = xlSheet.Range("BM2:CG%d" %(len(ioResult.qosCompressedResults)+1))
		xlRng.Value = ioResult.qosCompressedResults
		xlRng.NumberFormat = "0"
		
		
		#  Sort Iops
		time.sleep(1)
		xlSheet.Range("BA:BA").Copy()
		time.sleep(2)
		xlSheet.Range("BD:BD").Insert()
		xlSheet.Range("BD1").Value = "Iops Sorted"
		xlSheet.Range("BD:BD").Sort(
			Key1 = xlSheet.Range("BD1"),
			Order1 = win32com.client.constants.xlAscending,
			Header = win32com.client.constants.xlYes,
			Orientation = win32com.client.constants.xlTopToBottom
			)
			
		#  Sort Avg Lat
		time.sleep(1)
		xlSheet.Range("BB:BB").Copy()
		time.sleep(2)
		xlSheet.Range("BE:BE").Insert()
		xlSheet.Range("BE1").Value = "Average Latency Sorted"
		xlSheet.Range("BE:BE").Sort(
			Key1 = xlSheet.Range("BE1"),
			Order1 = win32com.client.constants.xlAscending,
			Header = win32com.client.constants.xlYes,
			Orientation = win32com.client.constants.xlTopToBottom
			)
		
		#  Sort Max Lat
		time.sleep(1)
		xlSheet.Range("BC:BC").Copy()
		time.sleep(2)
		xlSheet.Range("BF:BF").Insert()
		xlSheet.Range("BF1").Value = "Max Latency Sorted"
		xlSheet.Range("BF:BF").Sort(
			Key1 = xlSheet.Range("BF1"),
			Order1 = win32com.client.constants.xlAscending,
			Header = win32com.client.constants.xlYes,
			Orientation = win32com.client.constants.xlTopToBottom
			)
		
		# Plot Iops
		xlChart = (xlSheet.ChartObjects()).Add(192, 0, 410, 240).Chart
		xlChart.SetSourceData(
			Source = xlSheet.Range("BA:BA"),
			PlotBy = win32com.client.constants.xlColumns
			)
		xlChart.ChartType = win32com.client.constants.xlXYScatter
		xlChart.HasTitle = 1
		xlChart.HasLegend = 0
		xlChart.Axes(win32com.client.constants.xlValue).MinimumScaleIsAuto = 0
		xlChart.Axes(win32com.client.constants.xlValue).MinimumScale = 0.0
		xlChart.Axes(win32com.client.constants.xlCategory).MaximumScaleIsAuto = 0
		xlChart.Axes(win32com.client.constants.xlCategory).MaximumScale = (len(ioResult.instResults)+1)
		xlChart.Axes(win32com.client.constants.xlCategory).MinimumScale = 0
		xlChart.SeriesCollection(1).MarkerStyle = 9
		xlChart.SeriesCollection(1).MarkerSize = 2


# Trendlines WIP
#		xlChart.SeriesCollection(1).Trendlines.Add()
#		xlChart.SeriesCollection(1).Trendlines(1).Type = win32com.client.constants.xlMovingAvg
#		xlChart.SeriesCollection(1).Trendlines(1).Period = 100
#		xlChart.SeriesCollection(1).Trendlines(1).Format.Line.Visible = win32com.client.constants.msoTrue
#		xlChart.SeriesCollection(1).Trendlines(1).Format.Line.ObjectThemeColor = win32com.client.constants.msoThemeColorAccent1
#		xlChart.SeriesCollection(1).Trendlines(1).Format.Line.TintAndShade = 0
#		xlChart.SeriesCollection(1).Trendlines(1).Format.Line.Brightness = 0
#		xlChart.SeriesCollection(1).Trendlines(1).Format.Line.RGB = win32com.client.constants.RGB(255,0,0)


		#xlChart.Location(2, xlSheet.Name)
		
		# Plot Avg Lat
		xlChart = (xlSheet.ChartObjects()).Add(192, 240, 410, 240).Chart
		xlChart.SetSourceData(
			Source = xlSheet.Range("BB:BB"),
			PlotBy = win32com.client.constants.xlColumns
			)
		xlChart.ChartType = win32com.client.constants.xlXYScatter
		xlChart.HasTitle = 1
		xlChart.HasLegend = 0
		xlChart.Axes(win32com.client.constants.xlValue).MinimumScaleIsAuto = 0
		xlChart.Axes(win32com.client.constants.xlValue).MinimumScale = 0.0
		xlChart.Axes(win32com.client.constants.xlCategory).MaximumScaleIsAuto = 0
		xlChart.Axes(win32com.client.constants.xlCategory).MaximumScale = (len(ioResult.instResults)+1)
		xlChart.Axes(win32com.client.constants.xlCategory).MinimumScale = 0
		xlChart.SeriesCollection(1).MarkerStyle = 9
		xlChart.SeriesCollection(1).MarkerSize = 2
		
		# Plot Max Lat
		xlChart = (xlSheet.ChartObjects()).Add(192, 480, 410, 240).Chart
		xlChart.SetSourceData(
			Source = xlSheet.Range("BC:BC"),
			PlotBy = win32com.client.constants.xlColumns
			)
		xlChart.ChartType = win32com.client.constants.xlXYScatter
		xlChart.HasTitle = 1
		xlChart.HasLegend = 0
		xlChart.Axes(win32com.client.constants.xlValue).MinimumScaleIsAuto = 0
		xlChart.Axes(win32com.client.constants.xlValue).MinimumScale = 0.0
		xlChart.Axes(win32com.client.constants.xlCategory).MaximumScaleIsAuto = 0
		xlChart.Axes(win32com.client.constants.xlCategory).MaximumScale = (len(ioResult.instResults)+1)
		xlChart.Axes(win32com.client.constants.xlCategory).MinimumScale = 0
		xlChart.SeriesCollection(1).MarkerStyle = 9
		xlChart.SeriesCollection(1).MarkerSize = 2
		
		# Plot SORTED Iops
		xlChart = (xlSheet.ChartObjects()).Add(602, 0, 410, 240).Chart
		xlChart.SetSourceData(
			Source = xlSheet.Range("BD1:BD%d"%(len(ioResult.instResults)+1)),
			PlotBy = win32com.client.constants.xlColumns
			)
		xlChart.ChartType = win32com.client.constants.xlLine
		xlChart.HasTitle = 1
		xlChart.HasLegend = 0
		xlChart.Axes(win32com.client.constants.xlValue).MinimumScaleIsAuto = 0
		xlChart.Axes(win32com.client.constants.xlValue).MinimumScale = 0.0
		xlChart.SeriesCollection(1).MarkerStyle = 9
		xlChart.SeriesCollection(1).MarkerSize = 2
		
		# Plot SORTED Avg Lat
		xlChart = (xlSheet.ChartObjects()).Add(602, 240, 410, 240).Chart
		xlChart.SetSourceData(
			Source = xlSheet.Range("BE1:BE%d"%(len(ioResult.instResults)+1)),
			PlotBy = win32com.client.constants.xlColumns
			)
		xlChart.ChartType = win32com.client.constants.xlLine
		xlChart.HasTitle = 1
		xlChart.HasLegend = 0
		xlChart.Axes(win32com.client.constants.xlValue).MinimumScaleIsAuto = 0
		xlChart.Axes(win32com.client.constants.xlValue).MinimumScale = 0.0
		xlChart.SeriesCollection(1).MarkerStyle = 9
		xlChart.SeriesCollection(1).MarkerSize = 2
		
		# Plot SORTED Max Lat
		xlChart = (xlSheet.ChartObjects()).Add(602, 480, 410, 240).Chart
		xlChart.SetSourceData(
			Source = xlSheet.Range("BF1:BF%d"%(len(ioResult.instResults)+1)),
			PlotBy = win32com.client.constants.xlColumns
			)
		xlChart.ChartType = win32com.client.constants.xlLine
		xlChart.HasTitle = 1
		xlChart.HasLegend = 0
		xlChart.Axes(win32com.client.constants.xlValue).MinimumScaleIsAuto = 0
		xlChart.Axes(win32com.client.constants.xlValue).MinimumScale = 0.0
		xlChart.SeriesCollection(1).MarkerStyle = 9
		xlChart.SeriesCollection(1).MarkerSize = 2
