#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2015 Eric Prestat
#
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# <http://www.gnu.org/licenses/>.-
"""
TODO:
- read gas?
- select a time zone using a combobox?

- display loaded file
- export button

improvement of the layout:
- add color to the label of the QCheckBox?
- standardise the color of the plot

There are a few bug:
- a factor (1x+09) is displayed with date and time on the x-axis... wait for a
better date implementation in pyqtgraph?!
- a supplementary axis is displayed on the plot (top left) using date axis
"""
# Use PyQt QPI #2 with python 2.x
import sip
sip.setapi('QString', 2)

from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import pytz, datetime
# Try relative import, if not global import
try:
    from DateTimeAxisItem import DateTimeAxisItem
except ImportError:
    from atmosphere_data_log_plotter.DateTimeAxisItem import DateTimeAxisItem

def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt.replace(tzinfo=None) - epoch
    return delta.total_seconds()

def read_date_time_csv_atmosphere(fname):
    """
    Return "naive" time read from the log file (depending on daylight saving
    time and zone time)
    """
    f = open(fname, 'r')
    f.readline()
    line1 = f.readline()
    date = line1.split('Date (yyyy.mm.dd) = ')[1].split(',')[0].split('.')
    line2 = f.readline()
    time = line2.split('Time (hh:mm:ss.ms) = ')[1].split(',')[0].split(':')  
    f.close()
    dt = datetime.datetime(int(date[0]), int(date[1]), int(date[2]),
                           int(time[0]), int(time[1]), int(time[2].split('.')[0]))
    return dt

def convert_datetime_to_utc(dt, timezone='Europe/London'):
    """
    Convert datetime to UTC considering daylight saving time and zone time
    """
    bst = pytz.timezone(timezone)
    return bst.localize(dt).astimezone(pytz.utc)

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.view = data_plotter_layout(parent=self)
        self.setCentralWidget(self.view)

class data_plotter_layout(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None):
        pg.GraphicsLayoutWidget.__init__(self, parent=parent)
        self.setBackground(None)
        self._add_checkBox()
        self._load_data()
        self._setup_plot()

    def _setup_plot(self):
        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)
        # Initialise the two plots
        self.axis_p1 = DateTimeAxisItem(orientation='bottom')
        self.p1 = self.addPlot(title="Region Selection", enableMouse=False,
                               axisItems={'bottom': self.axis_p1})
        self.p1.setLabels(left='Pressure (mbarr)')
#        self.p1.setLabels(bottom='Time (min)')
        self.nextRow()        
        self.axis_p2 = DateTimeAxisItem(orientation='bottom')
        self.p2 = self.addPlot(title="Zoom on selected region",
                               axisItems={'bottom': self.axis_p2})
        self.p2.setLabels(left='Pressure (mbarr)')
        self.p2.setLabels(bottom='Time (min)')
        self._add_second_right_axis_p1()
        self._add_second_right_axis_p2()
        self.p1.vb.sigResized.connect(self._updateViewsp1)
        self.p2.vb.sigResized.connect(self._updateViewsp2)
        time_zoom = [self.time.max()*1.0/3, self.time.max()*2.0/3]
        self.zoom = [(time + self.starting_time_unix) for time in time_zoom]
        
        self._update_plots()

    def _load_data(self):
        # Open data
        self.fname = QtGui.QFileDialog.getOpenFileName(
                     filter = self.tr(' Log File *.csv ;; *.*'))
       
        # TODO
        # read comments that contains description
        # time is in millisecond, notes a str
        self.time0, self.holder_t, self.holder_p, self.tank1_p, self.tank2_p,\
                        self.vacuum_tank_p = np.loadtxt(self.fname,
                                                        delimiter=',',
                                                        skiprows=10,
                                                        unpack=True,
                                                        usecols=(0,2,3,4,5,6))
        print("Data loaded")
        self.time = self.time0/1000
        starting_time_utc = convert_datetime_to_utc(read_date_time_csv_atmosphere(self.fname))
        self.starting_time_unix = unix_time(starting_time_utc)
        self.actual_time = self.time0/1000 + self.starting_time_unix
        if hasattr(self, 'p1'):
            self._update_plots()
        
    def _add_checkBox(self):
        self.ButtonLoadLogfile = QtGui.QPushButton()
        self.ButtonLoadLogfile.setText('Load log file')
        self.holder_t_checkBox = QtGui.QCheckBox('Holder Temperature')
        self.holder_t_checkBox.setChecked(True)
        self.holder_p_checkBox = QtGui.QCheckBox('Holder Pressure')
        self.holder_p_checkBox.setChecked(True)
        self.tank1_p_checkBox = QtGui.QCheckBox('Tank1 Pressure')
        self.tank2_p_checkBox = QtGui.QCheckBox('Tank2 Pressure')
        self.vacuum_tank_p_checkBox = QtGui.QCheckBox('Vacuum tank Pressure')

        self.layout = QtGui.QHBoxLayout()
        self.layout.addWidget(self.ButtonLoadLogfile)
        self.layout.addWidget(self.holder_t_checkBox)
        self.layout.addWidget(self.holder_p_checkBox)
        self.layout.addWidget(self.tank1_p_checkBox)
        self.layout.addWidget(self.tank2_p_checkBox)
        self.layout.addWidget(self.vacuum_tank_p_checkBox)
        self.setLayout(self.layout)        

        self.ButtonLoadLogfile.clicked.connect(self._load_data)        
        self.holder_t_checkBox.stateChanged.connect(self._update_plots)
        self.holder_p_checkBox.stateChanged.connect(self._update_plots)
        self.tank1_p_checkBox.stateChanged.connect(self._update_plots)
        self.tank2_p_checkBox.stateChanged.connect(self._update_plots)
        self.vacuum_tank_p_checkBox.stateChanged.connect(self._update_plots)

    def _update_plots(self):
        self.p1.clear()
        if hasattr(self, 'p1_right'):
            self.p1_right.clear()
            self.p2_right.clear()
        self.p2.clear()    
        if self.holder_t_checkBox.isChecked():
            self.p1_right = pg.PlotCurveItem(self.actual_time, self.holder_t, pen='b',
                                             viewBox=self.viewBox_right_p1)
            self.viewBox_right_p1.addItem(self.p1_right)
            self.p2_right = pg.PlotCurveItem(self.actual_time, self.holder_t, pen='b', viewBox=self.viewBox_right_p2)
            self.viewBox_right_p2.addItem(self.p2_right)
        if self.holder_p_checkBox.isChecked():
            self.p1.plot(self.actual_time, self.holder_p, pen=(255,0,0), name='Holder pressure')
            self.p2.plot(self.actual_time, self.holder_p, pen=(255,0,0), name='Holder pressure')
        if self.tank1_p_checkBox.isChecked():
            self.p1.plot(self.actual_time, self.tank1_p, pen=(0,255,0), name='Tank1 pressure')
            self.p2.plot(self.actual_time, self.tank1_p, pen=(0,255,0), name='Tank1 pressure')
        if self.tank2_p_checkBox.isChecked():
            self.p1.plot(self.actual_time, self.tank2_p, pen=(0,0,255), name='Tank2 pressure')
            self.p2.plot(self.actual_time, self.tank2_p, pen=(0,0,255), name='Tank2 pressure')
        if self.vacuum_tank_p_checkBox.isChecked():
            self.p1.plot(self.actual_time, self.vacuum_tank_p, pen=(255,255,255),name='Vacuum tank pressure')
            self.p2.plot(self.actual_time, self.vacuum_tank_p, pen=(255,255,255), name='Vacuum tank pressure')
#        self.p1.addLegend()
#        self.p2.addLegend()
        self._link_two_plots()

    def _add_second_right_axis_p1(self):
        self.viewBox_right_p1 = pg.ViewBox(enableMouse=False)
        self.p1.showAxis('right')
        self.p1.scene().addItem(self.viewBox_right_p1)
        self.p1.getAxis('right').linkToView(self.viewBox_right_p1)
        self.viewBox_right_p1.setXLink(self.p1)
        self.p1.getAxis('right').setLabel('Temperature (°C)', color='#0000ff')        

    def _add_second_right_axis_p2(self):
        self.viewBox_right_p2 = pg.ViewBox()
        self.p2.showAxis('right')
        self.p2.scene().addItem(self.viewBox_right_p2)
        self.p2.getAxis('right').linkToView(self.viewBox_right_p2)
        self.viewBox_right_p2.setXLink(self.p2)
        self.p2.getAxis('right').setLabel('Temperature (°C)', color='#0000ff') 
        
    def _updateViewsp1(self):
        ## view has resized; update auxiliary views to match
        self.viewBox_right_p1.setGeometry(self.p1.vb.sceneBoundingRect())            
        ## need to re-update linked axes since this was called
        ## incorrectly while views had different shapes.
        ## (probably this should be handled in ViewBox.resizeEvent)
        self.viewBox_right_p1.linkedViewChanged(self.p1.vb, self.viewBox_right_p1.XAxis)

    def _updateViewsp2(self):
        ## view has resized; update auxiliary views to match
        self.viewBox_right_p2.setGeometry(self.p2.vb.sceneBoundingRect())            
        ## need to re-update linked axes since this was called
        ## incorrectly while views had different shapes.
        ## (probably this should be handled in ViewBox.resizeEvent)
        self.viewBox_right_p2.linkedViewChanged(self.p2.vb, self.viewBox_right_p2.XAxis)

    def _link_two_plots(self):
        lr = pg.LinearRegionItem(self.zoom)
        lr.setZValue(-10)
        self.p1.addItem(lr)
        
        def updatePlot():
            self.p2.setXRange(*lr.getRegion(), padding=0)
        def updateRegion():
            lr.setRegion(self.p2.getViewBox().viewRange()[0])
            self.zoom = lr.getRegion()
        lr.sigRegionChanged.connect(updatePlot)
        self.p2.sigXRangeChanged.connect(updateRegion)
        updatePlot()

if __name__ == '__main__':  
    app = QtGui.QApplication([])
    win = MainWindow()
    win.resize(1200,800)
    win.show()
    app.exec_()