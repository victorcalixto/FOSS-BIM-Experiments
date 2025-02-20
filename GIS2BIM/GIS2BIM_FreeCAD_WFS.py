# -*- coding: utf8 -*-
#***************************************************************************
#*   Copyright (c) 2021 Maarten Vroegindeweij <maarten@3bm.co.nl>          *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

"""This module provides tools to load GIS information into FreeCAD
"""

__title__= "GIS2BIM_FreeCAD_import_wfs"
__author__ = "Maarten Vroegindeweij"
__url__ = "https://github.com/DutchSailor/GIS2BIM"

# WFS Importer

from PySide2 import QtCore, QtWidgets
from PySide2.QtWidgets import *
from PySide2.QtWebEngineWidgets import QWebEngineView
from PySide2.QtWebEngineWidgets import QWebEnginePage 
from PySide2.QtCore import QUrl

import os
import FreeCAD

from PyPackages import GIS2BIM
from PyPackages import GIS2BIM_FreeCAD
from PyPackages import GIS2BIM_CRS 
from PyPackages import GIS2BIM_GUI

import importlib
#importlib.reload(GIS2BIM_GUI)
#importlib.reload(GIS2BIM_FreeCAD)

class GISWFS_Dialog(QtWidgets.QDialog):
	def __init__(self, parent=None):
		super(GISWFS_Dialog, self).__init__(parent)
		
		self.sitename = "GIS-Sitedata"
		
		dialog = QtWidgets.QMessageBox()
		dialog.setText(" Several limitations are 1) WFS 2.0.0 2) Server should support SRS 4326 3)For preview purposes server should support GeoJSON 4)Request for import works only with gml. Work in progress!")
		dialog.setWindowTitle("Warning: This is a Proof of Concept.")
		dialog.exec_() 

		#Get/set parameters for GIS
		self.tempFolderName = "GIStemp/"
		self.X = str(GIS2BIM_FreeCAD.ArchSiteCreateCheck(self.sitename).CRS_x)
		self.Y = str(GIS2BIM_FreeCAD.ArchSiteCreateCheck(self.sitename).CRS_y)	
		self.lat = str(GIS2BIM_FreeCAD.ArchSiteCreateCheck(self.sitename).WGS84_Latitude)
		self.lon = str(GIS2BIM_FreeCAD.ArchSiteCreateCheck(self.sitename).WGS84_Longitude)
		self.bboxWidthStart = str(GIS2BIM_FreeCAD.ArchSiteCreateCheck(self.sitename).BoundingboxWidth)
		self.bboxHeightStart = str(GIS2BIM_FreeCAD.ArchSiteCreateCheck(self.sitename).BoundingboxHeight)
		self.CRS = str(GIS2BIM_FreeCAD.ArchSiteCreateCheck(self.sitename).CRS_EPSG_SRID)
		self.CRSDescription = str(GIS2BIM_FreeCAD.ArchSiteCreateCheck(self.sitename).CRS_EPSG_Description)
		self.bboxString = GIS2BIM.CreateBoundingBox(float(GIS2BIM_FreeCAD.ArchSiteCreateCheck(self.sitename).CRS_x),float(GIS2BIM_FreeCAD.ArchSiteCreateCheck(self.sitename).CRS_y),float(self.bboxWidthStart),float(self.bboxHeightStart),0)

		#Set Style
		self.setStyleSheet("QWidget {background-color: rgb(68, 68, 68)} QPushButton { background-color: black } QGroupBox {border: 1px solid grey; }") #margin: 2px;
		
		#Download files
		self.URLUpdate = GIS2BIM.GetWebServerData("HTMLLocationDataJSmapbboxupdate", "Other", "URL")	#Javascript-URL for update boundingbox
		self.URLwfs = GIS2BIM.GetWebServerData("HTMLwfsJSwfsUpdate", "Other", "URL")	#Javascript-URL for update wfs
		self.URLmap = GIS2BIM.GetWebServerData("HTMLwfs", "Other", "URL")
		self.filepathJSUpdate = GIS2BIM.DownloadURL(GIS2BIM_FreeCAD.CreateTempFolder(self.tempFolderName),self.URLUpdate,"map_bboxupdate.js") #Javascript-file for update boundingbox
		self.filepathJSwfs = GIS2BIM.DownloadURL(GIS2BIM_FreeCAD.CreateTempFolder(self.tempFolderName),self.URLwfs,"map_wfsupdate.js") #Javascript-file for update wfs
		self.filepathBaseMap = GIS2BIM.DownloadURL(GIS2BIM_FreeCAD.CreateTempFolder(self.tempFolderName),self.URLmap,"basemapWFS.html") #Basemap from GIS2BIM Repository for preview
		self.filepathNewMap = GIS2BIM.DownloadURL(GIS2BIM_FreeCAD.CreateTempFolder(self.tempFolderName),self.URLmap,"mapWFS.html") #Edited Basemap with location and bbox
		#self.filepathBaseMap = "C:/Users/mikev/OneDrive/Bureaublad/TEMP/GIStemp/basemapWFS.html"	
		#self.filepathNewMap = "C:/Users/mikev/OneDrive/Bureaublad/TEMP/GIStemp/mapWFS.html"	
		self.tempFolderPath = GIS2BIM_FreeCAD.CreateTempFolder(self.tempFolderName)	

		os.remove(self.filepathNewMap)
		BaseMap = open(self.filepathBaseMap,"r")
		BaseMapstr = BaseMap.read()
		Newstr = BaseMapstr.replace("51LAT",str(self.lat))
		Newstr = Newstr.replace("4LONG", str(self.lon))
		Newstr = Newstr.replace("WBBOX",self.bboxWidthStart)
		Newstr = Newstr.replace("HBBOX",self.bboxHeightStart)
		open(self.filepathNewMap, "x")
		f1 = open(self.filepathNewMap, "w")
		f1.write(Newstr)
		f1.close()

		#Download list of predefined WFS Requests
		category = "webserverRequests"
		service = "WFS_curves"
		data = GIS2BIM.GetWebServerDataService(category,service)
		
		TitleList  = []
		for i in data:
			TitleList.append(i["title"])
		
		ServerRequestPrefix  = []
		for i in data:
			ServerRequestPrefix.append(i["serverrequestprefix"])
		yx = sorted(zip(TitleList,ServerRequestPrefix))
		self.TitleList = [x[0] for x in yx]
		self.ServerRequestPrefix = [x[1] for x in yx]
		
		#Widget Right Bottom Combined
		gridRB = QtWidgets.QGridLayout()
		gridRB.addWidget(self.webserverGroup(), 0, 0, QtCore.Qt.AlignTop)
		gridRB.addWidget(self.freeCADGroup(), 1, 0, QtCore.Qt.AlignTop)
		
		#Overall Grid
		grid = QtWidgets.QGridLayout()
		grid.addWidget(self.webViewGroup(), 0, 0, 1, 2)
		grid.addWidget(self.locationGroup(), 3, 0, QtCore.Qt.AlignTop)	
		grid.addLayout(gridRB, 3, 1)
		grid.addLayout(self.buttonGroup(),4,0,1,2)
		grid.setRowStretch(0,2)
		self.setLayout(grid)
		
		self.setWindowTitle("Load 2D Vector Data with WFS(Web Feature Server)")
		self.resize(920, 910)

	def webViewGroup(self):
		groupBoxx = GIS2BIM_GUI.webViewGroup(self)
		return groupBoxx

	def locationGroup(self):
		groupBoxx = GIS2BIM_GUI.locationGroup(self)
		return groupBoxx

	def webserverGroup(self):
		groupBox = QtWidgets.QGroupBox("Input Webserver / Request")

		cboDefWFSLab = QtWidgets.QLabel("Predifined WFS Requests", self)		
		self.cboDefWFS = QtWidgets.QComboBox(self)
		self.cboDefWFS.addItems(self.TitleList)
		self.cboDefWFS.currentIndexChanged.connect(self.selectionchange)

		requestLab = QtWidgets.QLabel("Webserver Address & Request", self)
		self.request= QtWidgets.QLineEdit(self)		
		self.request.setText(self.ServerRequestPrefix[self.cboDefWFS.currentIndex()])

		xPathStrLab = QtWidgets.QLabel("xPath String")
		self.xPathStr = QtWidgets.QLineEdit()
		self.xPathStr.setText("//{http://www.opengis.net/gml/3.2}posList")

		grid = QtWidgets.QGridLayout()
		grid.addWidget(cboDefWFSLab,0,0)
		grid.addWidget(self.cboDefWFS,0,1)
		grid.addWidget(requestLab,1,0)
		grid.addWidget(self.request,1,1)
		grid.setRowStretch(1,1)
		grid.addWidget(xPathStrLab,2,0)
		grid.addWidget(self.xPathStr,2,1)

		groupBox.setLayout(grid)
		
		return groupBox

	def freeCADGroup(self):
		groupBox = QtWidgets.QGroupBox("FreeCAD Import Settings")
		
		clsPolygonLab = QtWidgets.QLabel("Close Polygon")
		self.clsPolygon = QtWidgets.QCheckBox()
		self.clsPolygon.setChecked(1)

		clsCreateFaceLab = QtWidgets.QLabel("Create Face")
		self.clsCreateFace = QtWidgets.QCheckBox()
		self.clsCreateFace.setChecked(1)
		
		groupNameLab = QtWidgets.QLabel("Group Name")
		self.groupName = QtWidgets.QLineEdit()
		self.groupName.setText("GIS_WFS")

		lineColorLab = QtWidgets.QLabel("Line Color", self)	
		self.lineColor = QtWidgets.QComboBox(self)
		colorlst = ("red","black")		
		self.lineColor.addItems(colorlst)
		#lineColor = QtWidgets.QPushButton("Color")
		#lineColor = QtWidgets.QColorDialog()	

		linePatternLab = QtWidgets.QLabel("Draw Style", self)	
		self.linePattern = QtWidgets.QComboBox(self)
		patternlst = ("Solid","Dashed","Dotted","Dashdot")		
		self.linePattern.addItems(patternlst)

		grid = QtWidgets.QGridLayout()
		grid.addWidget(clsPolygonLab,0,0)
		grid.addWidget(self.clsPolygon,0,1)
		grid.addWidget(clsCreateFaceLab,0,2)
		grid.addWidget(self.clsCreateFace,0,3)
		grid.addWidget(lineColorLab,0,4)
		grid.addWidget(self.lineColor,0,5)
		grid.addWidget(linePatternLab,1,2)
		grid.addWidget(self.linePattern,1,3)
		grid.addWidget(groupNameLab,1,0)
		grid.addWidget(self.groupName,1,1)
	#	groupBox.setStyleSheet("QGroupBox {border: 1px solid grey; margin: 10px;}")
		groupBox.setLayout(grid)
		
		return groupBox

	def buttonGroup(self):
		hbox = GIS2BIM_GUI.buttonGroup(self)
		return hbox

	def onbboxWidth(self):
		JS2 = open(self.filepathJSUpdate,"r")
		JS2 = JS2.read()
		JS2 = JS2.replace("WBBOX", self.bboxWidth.text())
		JS2 = JS2.replace("HBBOX", self.bboxHeight.text())
		self.webPage.runJavaScript(JS2) # update bboxWidth in mapview
		self.onTest()

	def onbboxHeight(self):
		JS3 = open(self.filepathJSUpdate,"r")
		JS3 = JS3.read()
		JS3 = JS3.replace("WBBOX", self.bboxWidth.text())
		JS3 = JS3.replace("HBBOX", self.bboxHeight.text())
		self.webPage.runJavaScript(JS3) # update bboxHeight in mapview
		self.onTest()
	
	def selectionchange(self): 
		#Update serverRequest
		self.request.clear()		
		self.request.setText(self.ServerRequestPrefix[self.cboDefWFS.currentIndex()])
		self.onTest()

	def onTest(self):
		JS4 = open(self.filepathJSwfs,"r")
		JS4 = JS4.read()
		self.bboxString = GIS2BIM.CreateBoundingBox(float(GIS2BIM_FreeCAD.ArchSiteCreateCheck(self.sitename).CRS_x),float(GIS2BIM_FreeCAD.ArchSiteCreateCheck(self.sitename).CRS_y),float(self.bboxWidth.text()),float(self.bboxHeight.text()),0)
		url = self.request.text()
		urlreq = url + self.bboxString
		urlpreview = urlreq + "&outputFormat=json&srsName=EPSG:4326"
		JS4 = JS4.replace("URLpreview", urlpreview) 
		self.webPage.runJavaScript(JS4) # update wfs in mapview

	def onImport(self):
		self.bboxString = GIS2BIM.CreateBoundingBox(float(GIS2BIM_FreeCAD.ArchSiteCreateCheck(self.sitename).CRS_x),float(GIS2BIM_FreeCAD.ArchSiteCreateCheck(self.sitename).CRS_y),float(self.bboxWidth.text()),float(self.bboxHeight.text()),2)
		url = self.request.text()
		print(self.bboxString)
		print(url)

		xpathstr = self.xPathStr.text()
		closedValue = self.clsPolygon.isChecked()
		makeFaceValue = self.clsCreateFace.isChecked()
		drawStyle = str(self.linePattern.currentText())  
		Curves = GIS2BIM_FreeCAD.CurvesFromWFS(url,self.bboxString,xpathstr,-float(self.X),-float(self.Y),1000,3,closedValue,makeFaceValue,drawStyle,(0.7,0.0,0.0))
		GIS2BIM_FreeCAD.CreateLayer(self.groupName.text())
		FreeCAD.activeDocument().getObject(self.groupName.text()).addObjects(Curves)
		FreeCAD.ActiveDocument.recompute()
		self.close()

	def onCancel(self):
		self.close()

form = GISWFS_Dialog()
form.exec_()