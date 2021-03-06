# -*- coding: utf-8 -*-
"""
Created on Tue Aug 25 13:08:19 2015

@author: jgimenez
"""
from PyQt4 import QtGui, QtCore
from figureTracers_ui import figureTracersUI
from myNavigationToolbar import *

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas


from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile

from utils import *

import numpy
from collections import OrderedDict
import pylab
import warnings
warnings.filterwarnings("ignore")

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

#residuals
#  {
#    type residuals;
#    functionObjectLibs
#      (
#        "libutilityFunctionObjects.so"
#      );
#    outputControl timeStep;
#    outputInterval 20;
#    fields
#      (
#        U
#        p
#      );
#  }
#
dicc = {}
dicc['type'] = 'faceSource'
dicc['functionObjectLibs'] =  ['"libfieldFunctionObjects.so"']
dicc['outputControl']  = 'timeStep'
dicc['log'] = 'true'
dicc['valueOutput'] = 'false'
dicc['source'] = 'patch'
dicc['sourceName'] = 'outlet'
dicc['operation'] = 'areaAverage'
dicc['fields'] = []

class figureTracers(figureTracersUI):

    def __init__(self, currentFolder):
        import matplotlib
        matplotlib.use('GTKAgg')
        figureTracersUI.__init__(self)
        self.currentFolder = currentFolder
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
        
        filename = '%s/system/controlDict'%self.currentFolder
        self.parsedData = ParsedParameterFile(filename,createZipped=False)
        
        self.tracersData = []
        if 'functions' in self.parsedData.getValueDict().keys():
            for key in self.parsedData['functions'].keys():
                if self.parsedData['functions'][key]['type'] == 'scalarTransport':
                    tracer = {}
                    tracer['name'] = key
                    tracer['patchName'] = self.parsedData['functions'][key]['patchName']
                    tracer['startTime'] = self.parsedData['functions'][key]['fvOptions']['S']['timeStart']
                    self.tracersData.append(tracer)

        for tracer in self.tracersData:
            item = QtGui.QListWidgetItem()
            item.setCheckState(QtCore.Qt.Unchecked)
            item.setText(tracer['name'])
            self.listWidget.addItem(item)
            
        from PyFoam.RunDictionary.BoundaryDict import BoundaryDict
        boundaries = BoundaryDict(str(self.currentFolder))
        for ipatch in boundaries.getValueDict():
            if boundaries[ipatch]['type']  != 'empty':
                self.comboBox.addItem(ipatch)
        
    def getData(self):
        data = {}
        data['name'] = str(self.name.text())
        data['nsteps'] = self.spinBox.value()        
        data['fields'] = []
        for i in range(self.listWidget.count()):
            if self.listWidget.item(i).checkState() == QtCore.Qt.Checked:
                data['fields'].append(self.listWidget.item(i).text())
        
        return data
        
    def setData(self, data):
        #buscar en el controlDict el function object 'name'
        filename = '%s/system/controlDict'%(self.currentFolder)
        parsedData = ParsedParameterFile(filename,createZipped=False)
        if 'functions' in parsedData.getValueDict().keys():
            if data['name'] in parsedData['functions'].keys():
                dicc = parsedData['functions'][data['name']]
                if dicc['type']=='faceSource':
                    self.name.setText(data['name'])
                    self.spinBox.setValue(dicc['outputInterval'])
                    for i in range(self.listWidget.count()):
                        if self.listWidget.item(i) in dicc['fields']:
                            self.listWidget.item(i).setCheckState(QtCore.Qt.Checked)
                        else:
                            self.listWidget.item(i).setCheckState(QtCore.Qt.Unchecked)
        
    def ckeckAccept(self, evnt):

        allow = False
        for i in range(self.listWidget.count()):
            if self.listWidget.item(i).checkState() == QtCore.Qt.Checked:
                allow = True
                break
        if allow:
            self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
            
    def accept(self):
        filename = '%s/system/controlDict'%(self.currentFolder)
        parsedData = ParsedParameterFile(filename,createZipped=False)
        
        if 'functions' not in parsedData.getValueDict().keys():
            parsedData['functions'] = {}
        
        #Logica para evitar nombres repetidos
        for key in self.parsedData['functions'].keys():
            if key == str(self.name.text()):
                w = QtGui.QMessageBox(QtGui.QMessageBox.Information, "Error", "The name of the new figure and the name of the tracer must be different. Please select another name")
                w.exec_()
                return
        
        dicc['outputInterval'] = self.spinBox.value()
        fields = []
        for i in range(self.listWidget.count()):
            if self.listWidget.item(i).checkState() == QtCore.Qt.Checked:
                fields.append(str(self.listWidget.item(i).text()))
        dicc['fields'] = fields
        dicc['sourceName'] = str(self.comboBox.currentText())        
        parsedData['functions'][str(self.name.text())] = dicc
        parsedData.writeFile()
        
        self.done(self.Accepted)
            
            
class figureTracersWidget(QtGui.QWidget):

    def __init__(self, scrollAreaWidgetContents, name):         
        QtGui.QWidget.__init__(self)
        self.setParent(scrollAreaWidgetContents)
        fig = Figure((3.0, 2.0), dpi=100)
        canvas = FigureCanvas(fig)
        canvas.setParent(self)
        toolbar = myNavigationToolbar(canvas, self)
        axes = fig.add_subplot(111)
        axes.autoscale(True)
        axes.set_title(name)
        axes.set_xlabel('Time [s]')
        axes.set_ylabel('T')

         # place plot components in a layout
        plotLayout = QtGui.QVBoxLayout()
        plotLayout.addWidget(canvas,1)
        plotLayout.addWidget(toolbar,0,QtCore.Qt.AlignCenter)
        self.setLayout(plotLayout)
        
        self.dataPlot = []
        #self.dataPlot = OrderedDict()
        self.dirList = []
        self.currentime = 0
        self.dirType = 'Tracers'
        self.lastPos = -1
        self.name = name
        self.colors = ['r', 'b', 'k', 'g', 'y', 'c']
        
        # prevent the canvas to shrink beyond a point
        #original size looks like a good minimum size
        canvas.setMinimumSize(canvas.size())
        
    
    def unique2d(self,a):
        x, y = a.T
        b = x + y*1.0j 
        idx = numpy.unique(b,return_index=True)[1]
        return a[idx] 

    def plot(self,path):
        
        canvas = self.findChild(FigureCanvas)
        axes = canvas.figure.gca()
        N = self.lastPos
        #print N
        data = pylab.loadtxt(path,skiprows=N)
                
        with open(path, 'r') as archi:
            #archi.seek(1)
            archi.readline()
            archi.readline()
            archi.readline()
            headers = archi.readline()
            headers = headers.split('\t')
            headers = headers[1:]                    
            for i in range(len(headers)):
                headers[i].replace(' ','')
            archi.close()

        if len(data)>0:
            
            if self.dataPlot == []:
                self.dataPlot = data
            else:
                self.dataPlot = numpy.vstack((self.dataPlot,data))
                
            if len(self.dataPlot)>2:
                self.dataPlot = self.unique2d(self.dataPlot)

            if data.ndim==1:
                self.lastPos = N + 1
            else:
                self.lastPos = N + data.shape[0]

            #Esta logica es agregada ya que para valores muy chicos en el rango 
            #de la variable dependiente, matplot tira errores de overflow cuando
            #trata de graficar, por lo que si el valor que tengo es menor a una
            #tolerancia determinada, la seteo a cero                
            if len(self.dataPlot)>0:
                if self.dataPlot.ndim==2:
                    for i in range(len(self.dataPlot)):
                        if self.dataPlot[i][1] < 1e-80:
                            self.dataPlot[i][1] = 0
                else:
                    for i in range(len(self.dataPlot)-1):
                        if self.dataPlot[1] < 1e-80:
                            self.dataPlot[1] = 0

            if(self.dataPlot.ndim>1):
                #self.dataPlot = self.dataPlot[-250:,:]
                axes.clear()
                for i in range(len(headers)):
                    line = axes.plot(self.dataPlot[:,0],self.dataPlot[:,i+1],self.colors[i%6], label=headers[i])
                axes.autoscale(True)
                axes.set_title(self.name)
                axes.set_xlabel('Time [s]')
                axes.set_ylabel('T')

#                canvas.draw()
                
    def resetFigure(self):
        self.dataPlot = []
        self.dirList = []
        self.dirType = 'Tracers'
        self.lastPos = -1
        self.colors = ['r', 'b', 'k', 'g', 'y', 'c']
        
        canvas = self.findChild(FigureCanvas)
        canvas.figure.gca().cla()
        #Seteo de nuevo esto porque lo de arriba me lo borra
        axes = canvas.figure.gca()
        axes.set_title(self.name)
        axes.set_xlabel('Time [s]')
        axes.set_ylabel('T')
        self.currentime = 0
        axes.autoscale(True)
        canvas.draw()