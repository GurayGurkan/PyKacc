# PyKACC: Developed as a Wireless Accelerometer Monitor
# GUI version 2.1
# Author: Guray GURKAN, Twitter: @guraygurkan
# 
# Last Revision: 18.02.2016

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import numpy as np
from bluetooth import *
import TEST_GUI_ver4
import time
import glob
import datetime
import pyqtgraph
from datetime import datetime as dt


class MainDialog(QMainWindow,TEST_GUI_ver4.Ui_MainWindow):
    fheader="Recorded by PyKACC v4.0"
    init=0
    elapsed=0
    frame=0
    Ndev=''
    fname=[]
    FileObj=''
    devices=[]
    devlist=[{'Device name':'KACC 1','MAC':'20:13:02:19:11:05'},\
          {'Device name':'KACC 2','MAC':'20:13:06:21:12:73'},\
           {'Device name':'KACC 3','MAC':'20:13:06:21:15:47'},\
            {'Device name':'KACC 4','MAC':'20:13:06:21:15:34'},\
             {'Device name':'KACC 5','MAC':'20:13:06:21:12:68'}]
    x_curves=['','','','','']
    y_curves=['','','','','']
    z_curves=['','','','','']   
    colors=['b','r','g','y','m']
    sockets=[]
    
    time_sync = True
    amplitude_sync = True
    
    RECVBUFFER=500 #Initial Receive buffer
    BUFFERSIZE=(RECVBUFFER)/23;  #Buffer length in samples: 23 for KACCver1 format
    DELAY_MS=250
    FSAMP=100    # Acquisition Frequency of DATA
    BUFFER_DURATION=8 #Length in seconds
    PLOT_DURATION=16
    BUFFER=BUFFER_DURATION*FSAMP # LOG matrix memory pre-allocated size, samples are written when full
    PLOT_BUFFER = []
       
    ACC=np.zeros((0,3))
    PLOT_BUFFER =''
    LOG=''
    length_LOG=0
    length_overall=0
    frame =0;
    endbuffer=['','','','','']
    xlabel = np.linspace(0,PLOT_DURATION,PLOT_DURATION*FSAMP)
    folder=''
    numTabs=0
    tlabel=''
    
    
    def __init__(self,parent=None): #******************************************
        super(MainDialog,self).__init__(parent)
        self.timer = QTimer()
        self.timer2 = QTimer() 
        
        QObject.connect(self.timer, SIGNAL("timeout()"), self.update_plot)
     
        self.setupUi(self)
        self.pushButton.clicked.connect(self.SET)
        self.pushButton_2.clicked.connect(self.START)
        self.pushButton_3.clicked.connect(self.STOP)
        self.pushButton_4.clicked.connect(self.SelectFolder)
        self.pushButton_Analyze.clicked.connect(self.createAnalysisTab)   

        
        
        #Sensor Isimlerinin Atanmasi:
        self.dev1.setText(self.devlist[0].values()[1])
        self.dev2.setText(self.devlist[1].values()[1])
        self.dev3.setText(self.devlist[2].values()[1])
        self.dev4.setText(self.devlist[3].values()[1])
        self.dev5.setText(self.devlist[4].values()[1])
        
        #Eksen bilgileri x="", y="_2", z="_3"
        self.legendX=self.graphicsView.addLegend(size=(5,10),offset=(-5,5));
        self.legendY=self.graphicsView_2.addLegend(size=(5,10),offset=(-5,5))
        self.legendZ=self.graphicsView_3.addLegend(size=(5,10),offset=(-5,-5))
        self.legendXa=self.graphicsView_x.addLegend(size=(5,10),offset=(-5,-5))
        self.legendYa=self.graphicsView_y.addLegend(size=(5,10),offset=(-5,-5))
        self.legendZa=self.graphicsView_z.addLegend(size=(5,10),offset=(-5,-5))
      
        self.prepareView(self.graphicsView,"X-axis",[-2,2],[0 ,self.PLOT_DURATION])
        self.prepareView(self.graphicsView_2,"Y-axis",[-2,2],[0 ,self.PLOT_DURATION])
        self.prepareView(self.graphicsView_3,"Z-axis",[-2,2],[0 ,self.PLOT_DURATION])
        
        self.graphicsView.plotItem.sigRangeChanged.connect(self.syncLiveLimits)
        #self.graphicsView_2.plotItem.sigRangeChanged.connect(self.syncLiveLimits)
        #self.graphicsView_3.plotItem.sigRangeChanged.connect(self.syncLiveLimits)
        
        self.prepareView(self.graphicsView_x,"X-axis",[-2,2],[0 ,60])
        self.prepareView(self.graphicsView_y,"Y-axis",[-2,2],[0 ,60])
        self.prepareView(self.graphicsView_z,"Z-axis",[-2,2],[0 ,60])
        
        
     
        self.graphicsView_x.plotItem.sigRangeChanged.connect(self.syncAnalysisLimits)
        #self.graphicsView_y.plotItem.sigRangeChanged.connect(self.syncAnalysisLimits)
        #self.graphicsView_z.plotItem.sigRangeChanged.connect(self.syncAnalysisLimits)
    
   
        
        # Buton Durumlari
        self.pushButton_3.setEnabled(False)
        self.pushButton_2.setEnabled(False)
        
        self.pushButton_Opendata.clicked.connect(self.OpenData)
        
    def OpenData(self):
        self.validfile=False
        while not self.validfile:
            self.file2Open = QFileDialog.getOpenFileNameAndFilter(None, 'Select a file:', 'C:\\')        
            self.AnalysisData = np.loadtxt(self.file2Open[0],delimiter=' ',dtype=float,skiprows=14)
            if len(self.AnalysisData)==size(self.AnalysisData,0):
                self.AnalysisRange=[]
                self.graphicsView_x.clear()
                self.graphicsView_y.clear()
                self.graphicsView_z.clear()
           
                self.AnalysisNumDevices = size(self.AnalysisData,1)/3
                self.validfile = True
                self.AnalysisSamples = len(self.AnalysisData)

                #self.tlabel = np.linspace(0,(self.AnalysisSamples-1)/100.,self.AnalysisSamples)
                self.tlabel = np.arange(0,(self.AnalysisSamples)/100.,float(1/100.))
                self.RangeSelectorX=pyqtgraph.LinearRegionItem(values=[0,self.tlabel[-1]/2])
                self.RangeSelectorY=pyqtgraph.LinearRegionItem(values=[0,self.tlabel[-1]/2])
                self.RangeSelectorZ=pyqtgraph.LinearRegionItem(values=[0,self.tlabel[-1]/2])
                
                self.graphicsView_x.addItem(self.RangeSelectorX)
                self.graphicsView_y.addItem(self.RangeSelectorY)
                self.graphicsView_z.addItem(self.RangeSelectorZ)
        
                self.RangeSelectorX.sigRegionChanged.connect(self.updateAnalysis)
                self.RangeSelectorY.sigRegionChanged.connect(self.updateAnalysis)
                self.RangeSelectorZ.sigRegionChanged.connect(self.updateAnalysis)
                
                self.AnalysisXcurves = []
                self.AnalysisYcurves = []
                self.AnalysisZcurves = []
                
                for c in range(self.AnalysisNumDevices):
                    self.AnalysisXcurves.append(self.graphicsView_x.plot(pen=self.colors[c]))
                    self.AnalysisYcurves.append(self.graphicsView_y.plot(pen=self.colors[c]))
                    self.AnalysisZcurves.append(self.graphicsView_z.plot(pen=self.colors[c]))
                    self.AnalysisXcurves[c].setData(self.tlabel,self.AnalysisData[:,3*c])
                    self.AnalysisYcurves[c].setData(self.tlabel,self.AnalysisData[:,3*c+1])
                    self.AnalysisZcurves[c].setData(self.tlabel,self.AnalysisData[:,3*c+2])
                    
                self.graphicsView_x.plotItem.vb.setRange(xRange=[-10,self.tlabel[-1]+10])
            else:
                QMessageBox("Reselect..")
        pass
    
    def prepareHistogramView(self,plotItemObj,channel_str):
        plotItemObj.setLabel('left',"Counts", units='samples')
        plotItemObj.setBackground(background='w')
        plotItemObj.setLabel('bottom',"values",units='g')
        plotItemObj.showGrid(x=True, y=True, alpha=0.5)
        plotItemObj.setTitle("Histogram of " + channel_str)
        
    def prepareFFTView(self,plotItemObj,channel_str):
        plotItemObj.setLabel('left',"Magnitude", units='g')
        plotItemObj.setBackground(background='w')
        plotItemObj.setLabel('bottom',"Frequency",units='Hz')
        plotItemObj.showGrid(x=True, y=True, alpha=0.5)
        plotItemObj.setTitle("FFT of " + channel_str)
        
    def Time2Samples(self):
        
        s1 = np.flatnonzero(self.tlabel==self.AnalysisRange[0])[0]
        s2 = np.flatnonzero(self.tlabel==self.AnalysisRange[1])[0]
        return s1,s2
        
    
    def createAnalysisTab(self):
        self.numTabs+=1
        analysisWidget = QWidget()
        histog_x = pyqtgraph.PlotWidget(parent=analysisWidget)
        fft_x = pyqtgraph.PlotWidget(parent=analysisWidget)
        histog_y = pyqtgraph.PlotWidget(parent=analysisWidget)
        fft_y = pyqtgraph.PlotWidget(parent=analysisWidget)
        histog_z = pyqtgraph.PlotWidget(parent=analysisWidget)
        fft_z = pyqtgraph.PlotWidget(parent=analysisWidget)
        #pix = QPixmap('Logo.png')
        #pix = pix.scaled(40,40,Qt.KeepAspectRatio)
        #Logo = QLabel(parent = analysisWidget)
        #Logo.setPixmap(pix)
        #Logo.move(2,570)
        #Logo.resize(40,40)
        
        
        
        closeButton =QPushButton('X',parent=analysisWidget)
        closeButton.resize(25,25)
        closeButton.move(800,10)
        closeButton.clicked.connect(self.closeAnalysisTab)
        #X
        histog_x.move(10,10)
        histog_x.resize(QSize(400,200))
        self.prepareHistogramView(histog_x,"X-channels") 
        
        fft_x.move(420,10)
        fft_x.resize(QSize(400,200))
        self.prepareFFTView(fft_x,"X-channels")
        #Y
        histog_y.move(10,210)
        histog_y.resize(QSize(400,200))
        self.prepareHistogramView(histog_y,"Y-channels") 
        
        fft_y.move(420,210)
        fft_y.resize(QSize(400,200))
        self.prepareFFTView(fft_y,"Y-channels")
        
        #Z
        histog_z.move(10,410)
        histog_z.resize(QSize(400,200))
        self.prepareHistogramView(histog_z,"Z-channels") 
        
        fft_z.move(420,410)
        fft_z.resize(QSize(400,200))
        self.prepareFFTView(fft_z,"Z-channels")
  
        self.tabWidget.addTab(analysisWidget,'Sub-analysis ' + str(self.numTabs))
        
        self.AnalysisSamples = self.Time2Samples()
        n1=self.AnalysisSamples[0]
        n2=self.AnalysisSamples[1]
        hist_curvesX=[]
        fft_curvesX=[]
        hist_curvesY=[]
        fft_curvesY=[]
        hist_curvesZ=[]
        fft_curvesZ=[]
        for c in range(self.AnalysisNumDevices):
            hist_curvesX.append(histog_x.plot(pen=self.colors[c],name=str(c)))
            fft_curvesX.append(fft_x.plot(pen=self.colors[c],name='1'))
            
            hist_curvesY.append(histog_y.plot(pen=self.colors[c],name=str(c)))
            fft_curvesY.append(fft_y.plot(pen=self.colors[c],name=str(c)))
            
            hist_curvesZ.append(histog_z.plot(pen=self.colors[c],name=str(c)))
            fft_curvesZ.append(fft_z.plot(pen=self.colors[c],name=str(c)))

            freqs, fftX = self.FFTanalysis(self.AnalysisData[n1:n2,3*c],100)
            freqs, fftY = self.FFTanalysis(self.AnalysisData[n1:n2,3*c+1],100)
            freqs, fftZ = self.FFTanalysis(self.AnalysisData[n1:n2,3*c+2],100)
 
            fft_curvesX[c].setData(freqs,fftX)
            fft_curvesY[c].setData(freqs,fftY)
            fft_curvesZ[c].setData(freqs,fftZ)
            
            fft_x.setRange(xRange=(0,50))
            fft_y.setRange(xRange=(0,50))
            fft_z.setRange(xRange=(0,50))
            
            histX, binX = self.HISTanalysis(self.AnalysisData[n1:n2,3*c])
            histY, binY = self.HISTanalysis(self.AnalysisData[n1:n2,3*c+1])
            histZ, binZ = self.HISTanalysis(self.AnalysisData[n1:n2,3*c+2])
            
            hist_curvesX[c].setData(binX,histX)
            hist_curvesY[c].setData(binY,histY)
            hist_curvesZ[c].setData(binZ,histZ)
            
    def FFTanalysis(self,array,fsamp):
        N= len(array)
        absfft = np.abs(np.fft.fft(array-np.mean(array)))
        absfft = absfft/float(N)
        freqs = np.array(range(N))*fsamp/float(N)
        return freqs[:round(N/2.)], absfft[:round(N/2.)]
        
    def HISTanalysis(self,array):
        
        hist, edges = np.histogram(array,bins=len(array)/10)
        return hist, edges[:-1]
        
    def closeAnalysisTab(self,ind):
         self.tabWidget.removeTab(self.tabWidget.currentIndex())
                
    def syncLiveLimits(self):
        [rangex, rangey] = self.sender().vb.viewRange()
        self.graphicsView_2.plotItem.vb.setRange(xRange=rangex)
        self.graphicsView_3.plotItem.vb.setRange(xRange=rangex)
        self.graphicsView_2.plotItem.vb.setRange(yRange=rangey)
        self.graphicsView_3.plotItem.vb.setRange(yRange=rangey)
        
    def syncAnalysisLimits(self):
        [rangex, rangey] = self.sender().vb.viewRange()
        
        if self.syncAnalysisCheck_X.isChecked():
            self.graphicsView_y.plotItem.vb.setRange(xRange=rangex)
            self.graphicsView_z.plotItem.vb.setRange(xRange=rangex)
        if self.syncAnalysisCheck_Y.isChecked():
            self.graphicsView_y.plotItem.vb.setRange(yRange=rangey)
            self.graphicsView_z.plotItem.vb.setRange(yRange=rangey)
        
 
    def updateAnalysis(self):
        x1,x2 =self.sender().getRegion()
        self.RangeSelectorX.setRegion([x1, x2])
        self.RangeSelectorY.setRegion([x1, x2])
        self.RangeSelectorZ.setRegion([x1, x2])
        self.AnalysisRange = [int(100.*x1)/100.,int(100.*x2)/100.]
  
    def SelectFolder(self):
        self.folder = QFileDialog.getExistingDirectory(None, 'Select a folder:', 'C:\\', QFileDialog.ShowDirsOnly)        
        
        glob.os.chdir(str(self.folder))
        self.lineEdit_Path.setText(str(self.folder))
        
        
    def START(self): #***********************START*****************************
        #print "START Pressed"
        
        
        #pasted 
        self.pushButton_2.setEnabled(False)
        self.pushButton_3.setEnabled(True)
        self.init = time.time()
        pctime=time.localtime()

# DOSYA ADI
        self.fheader=['***************************\n\r',\
            '\n\r',\
            self.fheader + '\n\r',\
            'Acquisition started at {} {} {} {} {} {} \n\r'.format(pctime[0],pctime[1],pctime[2],pctime[3],pctime[4],pctime[5]),\
            '\n\r',\
            '***************************\n\r','\n\r']
        self.FileObj.writelines(self.fheader)
#        for c in range(self.Ndev):
#            self.sockets[c].send("START")
            
        self.init=time.time()        
        self.timer.start(self.DELAY_MS)

#***********************STOP******************************
    def STOP(self): 
        #print "STOP Pressed"
        self.timer.stop()
        
        self.FileObj.close()
        
        for c in range(len(self.sockets)):
            self.sockets[c].send("END")
            self.sockets[c].close()
        #print "All devices disconnected..."
        #self.pushButton_2.setEnabled(True)
        self.pushButton_3.setEnabled(False)
        self.pushButton_2.setEnabled(False)
        self.pushButton.setEnabled(True)
        self.groupBox.setEnabled(True)
        self.statusbar.showMessage('All devices disconnected...')
        time.sleep(4)
        self.statusbar.showMessage('Ready for new SET...')
        
        for c in range(self.Ndev):
            self.legendX.removeItem(self.devlist[self.devices[c]-1].values()[1])
            self.legendY.removeItem(self.devlist[self.devices[c]-1].values()[1])
            self.legendZ.removeItem(self.devlist[self.devices[c]-1].values()[1])
        
        # Reset to Initial Conditions...
        self.sockets=[]
        self.init=0
        self.elapsed=0
        self.frame=0
        self.Ndev=''
        self.fname=[]
        self.FileObj=''
        self.devices=[]
        self.ACC=np.zeros((0,3))
        self.PLOT_BUFFER =''
        self.LOG=''
        self.length_LOG=0
        self.length_overall=0
        self.frame =0;
        self.endbuffer=['','','','','']
        self.fname=''
        self.lineEdit.setText("")
        self.fheader="Recorded by PyKACC v4.0"
        self.graphicsView_2.clear()
        self.graphicsView_3.clear()    
        self.graphicsView.clear()
        
        
#************************SET******************************  
    def SET(self):   
        if len(self.lineEdit.text())>0:
            self.fname=self.lineEdit.text() + ".txt"
            self.devices=[]
            if self.dev1.isChecked():
                self.devices.append(1)
            if self.dev2.isChecked():
                self.devices.append(2)
            if self.dev3.isChecked():
                self.devices.append(3)
            if self.dev4.isChecked():
                self.devices.append(4)
            if self.dev5.isChecked():
                self.devices.append(5)
                
            self.Ndev=len(self.devices)
            self.sockets=list(range(self.Ndev));
            self.PLOT_BUFFER = [np.zeros((self.PLOT_DURATION*self.FSAMP,3)) for t in range(self.Ndev)]
            self.statusbar.showMessage('Plot Buffer Created')
            time.sleep(0.2)
            self.LOG=np.zeros((self.BUFFER,3*self.Ndev),dtype=float)
            
            self.statusbar.showMessage('Data Buffer Created')
            time.sleep(0.2)
            self.length_LOG=np.zeros((self.Ndev),dtype=int) # initial new data length is null
            
            for c in range(self.Ndev):
                self.x_curves[c]=self.graphicsView.plot(pen=self.colors[c],name=self.devlist[self.devices[c]-1].values()[1])
                self.y_curves[c]=self.graphicsView_2.plot(pen=self.colors[c],name=self.devlist[self.devices[c]-1].values()[1])
                self.z_curves[c]=self.graphicsView_3.plot(pen=self.colors[c],name=self.devlist[self.devices[c]-1].values()[1])
            self.groupBox.setEnabled(False)
            self.pushButton_2.setEnabled(True)
            self.statusbar.showMessage('Ready for START...')
            
            # PASTED FROM START----
            self.statusbar.showMessage('Establishing Bluetooth connections...')
            self.FileObj=open(self.fname,'w')
            
            
            
            for c in range(self.Ndev):
                self.sockets[c]=BluetoothSocket(RFCOMM)
                time.sleep(.2)
            
            
            for c in range(self.Ndev):
                self.sockets[c].connect((self.devlist[self.devices[c]-1].values()[0],1))
                time.sleep(.5)

            self.statusbar.showMessage('Bluetooth connections established...')
            return True
        else:
            QMessageBox.critical(self,"File Name Error","Please Enter a Valid File Name!")
            
            
            

#************************ update plot ******************************
    def update_plot(self):
        
        
        for ch in range(self.Ndev):
            data=self.getdata(self.sockets[ch],self.endbuffer[ch],self.RECVBUFFER)
            self.endbuffer[ch]=data[1]       #new residue is the 2nd output
             # ---- ************************   SYNC PART   ************************
            if (self.frame<40):
                if data[2]>self.RECVBUFFER-100:
                    self.RECVBUFFER +=50
                    #print "Adapting buffer length to: ", self.RECVBUFFER
                    #self.setWindowTitle('PyKACC - Adapting Buffer Length: {}'.format(self.frame))
                    self.statusbar.showMessage('Adapting Buffer Length @Frame: {}'.format(self.frame))
                else:
                    #self.setWindowTitle('PyKACC - Synchronizing...: {}'.format(self.frame))
                    self.statusbar.showMessage('Synchronizing @Frame: {}'.format(self.frame))
                
                    
                
            else:
                
                self.statusbar.showMessage('Acquiring...Number of devices: {}'.format(self.Ndev))               
                ACC_NEW=np.zeros((0,3)) # Reset Frame Buffer for current channel
                
                self.label_6.setText(str(self.length_overall))
                
                
                # ---- ************************   ACQUISITION PART   ************************   
                
                aa=map(self.extractdata,data[0])
               
                for item in aa:
                    ACC_NEW=np.row_stack((ACC_NEW,np.array(item)))

                self.PLOT_BUFFER[ch]=np.row_stack((self.PLOT_BUFFER[ch],ACC_NEW));
                self.PLOT_BUFFER[ch]=np.delete(self.PLOT_BUFFER[ch],np.arange(len(ACC_NEW)),axis=0);
                self.LOG[self.length_LOG[ch]:self.length_LOG[ch] + ACC_NEW.shape[0],3*ch:3*(ch+1)]=ACC_NEW
                self.length_LOG[ch]+=ACC_NEW.shape[0]
            
                
                self.x_curves[ch].setData(self.xlabel,self.PLOT_BUFFER[ch][:,0])
                self.y_curves[ch].setData(self.xlabel,self.PLOT_BUFFER[ch][:,1])
                self.z_curves[ch].setData(self.xlabel,self.PLOT_BUFFER[ch][:,2])

                if self.frame==41:
                    self.init=time.time() #Keep acquisition initiation time updated...
                self.elapsed=time.time()-self.init
                
                self.label_5.setText(str(dt.strftime( dt(1900,1,1,0,0,0) + datetime.timedelta(seconds = round(self.elapsed)),"%H:%M:%S")))
                
        # Write to file if BUFFER is almost full and empty the BUFFER
        if max(self.length_LOG)>self.BUFFER-50:
            np.savetxt(self.FileObj,self.LOG[:min(self.length_LOG),:],delimiter=' ',fmt='%.3f')
            self.LOG=np.delete(self.LOG,np.arange(min(self.length_LOG)),axis=0)
            #print "LOG shape after delete: ", LOG.shape
        
            self.LOG=np.row_stack((self.LOG,np.zeros((min(self.length_LOG),3*(self.Ndev)))))
            #print "LOG shape after row_stack():", LOG.shape
        
            self.length_overall=self.length_overall + max(self.length_LOG)
            self.length_LOG=self.length_LOG-min(self.length_LOG)
        #print "LOG LENGTH after loop: ", length_LOG
        self.frame=self.frame+1
        
#************************ extract data ******************************        
    def extractdata(self,line_input):
        
        xval2=0.0;
        yval2=0.0;
        zval2=0.0;
        if len(line_input)==21:
            Xind=line_input.index("X")
            xval=line_input[Xind+1:Xind+5]
            xval2=comp2dec(xval);
            Yind=line_input.index("Y")
            yval=line_input[Yind+1:Yind+5]
            yval2 = comp2dec(yval)
            Zind=line_input.index("Z")
            zval=line_input[Zind+1:Zind+5]
            zval2=comp2dec(zval)
        xval2=xval2/16383;
        yval2=yval2/16383;
        zval2=zval2/16383;
        return [xval2, yval2, zval2]
    
    def getdata(self,BTSocket, residue,recvbuffer):
        newbytes=BTSocket.recv(recvbuffer)
        checksum = len(newbytes)
        BTstream=residue + newbytes  # READLINE . . . . .
        time.sleep(recvbuffer*10/57600)
        offset_init = BTstream.find("X")
    
        if (BTstream.endswith("\r") | BTstream.endswith("\n") ):
            BTstream = BTstream[offset_init:]
            newresidue=''
        else:
            offset_end = BTstream.rfind("X")
            newresidue=BTstream[offset_end:]
            BTstream = BTstream[offset_init:offset_end]
        a=BTstream.splitlines() #split("\r\n")
        return a, newresidue, checksum
    
    def HourMinSec(self,time_lag):
        hour = int(time_lag/3600)
        minute=int((time_lag - hour*3600))/60
        sec = int((time_lag-hour*3600-minute*60))
        return hour,minute,sec 
        
        
    def prepareView(self,obj,title,ylim,xlim):
        obj.setLabel('left',"Acceleration", units='g')
        obj.setBackground(background='w')
        obj.setLabel('bottom',"time",units='seconds')
        obj.showGrid(x=True, y=True, alpha=0.5)
        obj.setTitle(title)
        obj.setRange(yRange=(ylim[0],ylim[1]),xRange=(xlim[0],xlim[1]))
    
    
     
def comp2dec(dword):
    dig1=float(int(dword[0],16))
    outp = 0.000
    if dig1>7:
        outp=float(-(65535-int(dword,16)+1))
    else:
        
        outp=float(int(dword,16))
    return outp


    
              
# MAIN BURADA
              
app=QApplication(sys.argv)
form=MainDialog()
form.show()
app.exec_()

    

