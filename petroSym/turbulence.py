# -*- coding: utf-8 -*-
"""
Created on Fri May 13 17:19:55 2016

@author: santiago
"""

from PyQt4 import QtCore,QtGui
from turbulence_ui import Ui_turbulence
from utils import * #Para currentFields
from mesh import *
from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile
from PyFoam.RunDictionary.BoundaryDict import BoundaryDict

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

class turbulenceUI(QtGui.QScrollArea, Ui_turbulence):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QScrollArea.__init__(self, parent)

        self.setupUi(self)
        
RASModels = ['kEpsilon','kOmega','kOmegaSST']
LESModels = ['Smagorinsky']

class turbulence(turbulenceUI):
    
    def __init__(self, currentFolder, currentSolver):
        turbulenceUI.__init__(self)
        self.currentFolder = currentFolder
        self.currentSolver = currentSolver
        #self.radioTurb1.setChecked(True)
        self.loadData()
        self.apply_button.setEnabled(False)
        return
        
    def loadData(self):
        filename = '%s/constant/turbulenceProperties'%self.currentFolder
        tprop = ParsedParameterFile(filename,createZipped=False)
        symType = tprop['simulationType']
        if (symType=='laminar'):
            self.radioTurb1.setChecked(True)
        elif (symType=='RASModel'):
            self.radioTurb2.setChecked(True)
            filename = '%s/constant/RASProperties'%self.currentFolder
            Rprop = ParsedParameterFile(filename,createZipped=False)
            RASModelName = Rprop['RASModel']
            self.comboBoxTurb.setCurrentIndex(self.comboBoxTurb.findText(RASModelName))
        elif (symType=='LESModel'):
            self.radioTurb3.setChecked(True)
            filename = '%s/constant/LESProperties'%self.currentFolder
            Lprop = ParsedParameterFile(filename,createZipped=False)
            LESodelName = Lprop['LESModel']
            self.comboBoxTurb.setCurrentIndex(self.comboBoxTurb.findText(LESodelName))
        
        return
        
    def aplicar(self):
        if not(self.radioTurb1.isChecked()) and not(self.radioTurb2.isChecked()) and not(self.radioTurb3.isChecked()):
            w=QtGui.QMessageBox(QtGui.QMessageBox.Information, "ERROR", "You MUST select a Turbulence Model!")
            w.exec_()
            return
            
        [self.timedir, self.fields, currtime] = currentFields(self.currentFolder,nproc=self.window().nproc)
        
        filename = '%s/constant/turbulenceProperties'%self.currentFolder
        tprop = ParsedParameterFile(filename,createZipped=False)
        
        fields = []
        if self.radioTurb2.isChecked():
            RASModelName = str(self.comboBoxTurb.currentText())
            filename = '%s/constant/RASProperties'%self.currentFolder
            print self.currentFolder
            if not os.path.isfile(filename):
                command = 'cp %s/templates/template_pimpleFoam/constant/RASProperties %s/constant/.' % (os.path.dirname(os.path.realpath(__file__)),self.currentFolder)
                os.system(command)
                
            Rprop = ParsedParameterFile(filename,createZipped=False)
            Rprop['RASModel'] = RASModelName
            Rprop.writeFile()
            tprop['simulationType'] = 'RASModel'
            
            typ = self.comboBoxTurb.currentText()
            if (typ == 'kEpsilon'):
                exists = os.path.isfile(self.timedir+'/'+'k')
                if not exists:
                    #command = 'cp %s/0/k %s' % (self.currentFolder,self.timedir)
                    command = 'cp %s/templates/template_pimpleFoam/0/k %s' % (os.path.dirname(os.path.realpath(__file__)),self.timedir)
                    os.system(command)
                exists = os.path.isfile(self.timedir+'/'+'epsilon')
                if not exists:
                    #command = 'cp %s/0/epsilon %s' % (self.currentFolder,self.timedir)
                    command = 'cp %s/templates/template_pimpleFoam/0/epsilon %s' % (os.path.dirname(os.path.realpath(__file__)),self.timedir)
                    os.system(command)
                fields = ['k','epsilon']
            else: #komega o komegasst
                exists = os.path.isfile(self.timedir+'/'+'k')
                if not exists:
                    #command = 'cp %s/0/k %s' % (self.currentFolder,self.timedir)
                    command = 'cp %s/templates/template_pimpleFoam/0/k %s' % (os.path.dirname(os.path.realpath(__file__)),self.timedir)
                    os.system(command)
                exists = os.path.isfile(self.timedir+'/'+'omega')
                if not exists:
                    #command = 'cp %s/0/omega %s' % (self.currentFolder,self.timedir)
                    command = 'cp %s/templates/template_pimpleFoam/0/omega %s' % (os.path.dirname(os.path.realpath(__file__)),self.timedir)
                    os.system(command)
                fields = ['k','omega']                    
                
        elif self.radioTurb3.isChecked():
            LESModelName = str(self.comboBoxTurb.currentText())
            filename = '%s/constant/LESProperties'%self.currentFolder
            
            print self.currentFolder
            if not os.path.isfile(filename):
                command = 'cp %s/templates/template_pimpleFoam/constant/LESProperties %s/constant/.' % (os.path.dirname(os.path.realpath(__file__)),self.currentFolder)
                os.system(command)            
            
            Lprop = ParsedParameterFile(filename,createZipped=False)
            Lprop['LESModel'] = LESModelName
            Lprop.writeFile()
            tprop['simulationType'] = 'LESModel'
            
            exists = os.path.isfile(self.timedir+'/'+'nuSgs')
            if not exists:
                #command = 'cp %s/0/nuSgs %s' % (self.currentFolder,self.timedir)
                command = 'cp %s/templates/template_pimpleFoam/0/nuSgs %s' % (os.path.dirname(os.path.realpath(__file__)),self.timedir)
                os.system(command)
            fields = ['nuSgs']
        else:
            fields = ['p','U']
            tprop['simulationType'] = 'laminar'
            
        tprop.writeFile()
        self.updateFieldFiles(self.timedir, fields, currtime)
        
        self.apply_button.setEnabled(False)
        return
        
    def updateFieldFiles(self,timedir,fields,currtime):
        #tengo que releer cada uno de los campos en el directorio actual,
        #pisar los boundaries por los que aparece en constant/polyMesh/boundary
        #imponerles alguna CB por defecto dependiendo del tipo de patch
        boundaries = BoundaryDict(self.currentFolder)
        filename2 = '%s/system/changeDictionaryPetroSym'%self.currentFolder
        fieldData2 = []
        if os.path.isfile(filename2):
            fieldData2 = ParsedParameterFile(filename2,createZipped=False)

        for ifield in fields:
            filename = '%s/%s'%(timedir,ifield)
            fieldData = ParsedParameterFile(filename,createZipped=False)

            fieldData['boundaryField'] = {}
            for ipatch in boundaries.getValueDict():
                if ipatch not in fieldData['boundaryField']:
                    if boundaries[ipatch]['nFaces']==0:
                        continue
                    patchDict={}
                    if ifield in unknowns:
                        if boundaries[ipatch]['type']=='empty':
                            patchDict['type'] = 'empty'
                        else:
                            patchDict['type'] = 'zeroGradient'
                    else:
                        patchDict['type'] = 'calculated'
                    
                    if fieldData2==[]:
                        fieldData['boundaryField'][ipatch] = patchDict
                    else:
                        fieldData2['dictionaryReplacement'][ifield]['boundaryField'][ipatch] = patchDict
            
            # poner el campo interno uniforme en cero
            if types[ifield] == 'scalar':
                if fieldData2==[]:
                    fieldData['internalField'] = 'uniform 0'
                else:
                    fieldData2['dictionaryReplacement'][ifield]['internalField'] = 'uniform 0'
            elif types[ifield] == 'vector':
                if fieldData2==[]:
                    fieldData['internalField'] = 'uniform (0 0 0)'
                else:
                    fieldData2['dictionaryReplacement'][ifield]['internalField'] = 'uniform (0 0 0)'

            fieldData.writeFile()
        
        if fieldData2!=[]:
            fieldData2.writeFile()

        return
        
    def changeComboBox(self):
        self.apply_button.setEnabled(True)
        
    def changeTurbList(self):
        self.apply_button.setEnabled(True)
        self.comboBoxTurb.clear()
        if self.radioTurb1.isChecked():
            self.comboBoxTurb.addItems([])
        if self.radioTurb2.isChecked():
            self.comboBoxTurb.addItems(RASModels)
        if self.radioTurb3.isChecked():
            self.comboBoxTurb.addItems(LESModels)