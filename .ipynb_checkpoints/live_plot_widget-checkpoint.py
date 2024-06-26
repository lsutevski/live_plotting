import sys
import zmq
import ipywidgets as widgets
from IPython.display import display
from matplotlib import pyplot as plt
from random import randrange
from threading import Thread
import time
from tqdm.notebook import tqdm
from quantrol.utilities.Utils_plot import *

import pyqtgraph as pg
#from ..global_variables import START_EVENT, STOP_EVENT

from random import randint
import sys
#%gui qt6
import pyqtgraph as pg
from PyQt6 import QtCore, QtWidgets, QtGui
from PyQt6.QtCore import QObject, QThread, pyqtSignal as Signal, pyqtSlot as Slot, QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QStyle, QGridLayout, QProgressBar, QDockWidget
from time import sleep
from threading import Thread
import numpy as np

DATA_PORT = 5555
CONTROL_PORT = 5556

pg.setConfigOption('background', 0.9)
pg.setConfigOption('foreground', 'k')

left  = 0.125  # the left side of the subplots of the figure
right = 0.9    # the right side of the subplots of the figure
bottom = 0.1   # the bottom of the subplots of the figure
top = 0.9      # the top of the subplots of the figure
wspace = 0.2   # the amount of width reserved for blank space between subplots
hspace = 0.2   # the amount of height reserved for white space between subplots



class MainWindow(QMainWindow):

    colors = []
    cmap = pg.colormap.get('CET-D1A')
    #colormap = pg.colormap.get('viridis', source='matplotlib')  # Use any colormap you like
    for i in range(4):
        color = cmap.map(i/4, 'qcolor')
        colors.append(color)

    penRotation = [pg.mkPen(color = c, width = 3) for c in colors]

    currentPens = {}

    cmap = pg.colormap.get('CET-D1A')

    def __init__(self, zmq_socket):
        super().__init__()

        self.thread = QThread()

        self.timer = QTimer()
        self.timer.timeout.connect(self.updatePlots)

        self.layout = None

        self.zmq_socket = zmq_socket

        self.poller = zmq.Poller()
        self.poller.register(self.zmq_socket, zmq.POLLIN)
        #self._createLayout(self.layout)

    def _createLayout(self, layout):
        self.layout = layout

        plotLayout = QGridLayout()
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.plotWidgets = {}

        verticalLayout = QVBoxLayout()
        horizontalLayout = QHBoxLayout()

        self.startButton = QPushButton("Start")
        self.startButton.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, "SP_MediaPlay")))
        self.startButton.clicked.connect(self._start)

        self.stopButton = QPushButton("Stop")
        self.stopButton.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, "SP_MediaPause")))
        self.stopButton.clicked.connect(self._stop)
        self.stopButton.setEnabled(False)

        self.saveButton = QPushButton("Save")
        self.saveButton.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, "SP_DialogSaveButton")))
        self.saveButton.clicked.connect(self._save)

        self.redockButton = QPushButton("Redock")
        self.redockButton.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, "SP_TitleBarNormalButton")))
        self.redockButton.clicked.connect(self._redockAll)

        self.stopDataButton = QPushButton("Stop Data")
        self.stopDataButton.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, "SP_MessageBoxCritical")))
        self.stopDataButton.clicked.connect(self._stopData)



        #self._stopData()

        horizontalLayout.addWidget(self.startButton)
        horizontalLayout.addWidget(self.stopButton)
        horizontalLayout.addWidget(self.saveButton)
        horizontalLayout.addWidget(self.redockButton)
        horizontalLayout.addWidget(self.stopDataButton)
        horizontalWidget = QWidget()
        horizontalWidget.setLayout(horizontalLayout)

        self.plotItems = {}

        for key, value in self.layout.items():
            dockWidget = QDockWidget()
            dockWidget.setAllowedAreas
            #dockWidget.setFeatures(QDockWidget.AllDockWidgetFeatures)
            dockWidget.setFloating(True)
            dockWidget.setAllowedAreas(QtCore.Qt.DockWidgetArea.AllDockWidgetAreas)

            if value.get('lines', None):
                current_pens = {}

                widget = pg.PlotWidget()
                self.plotWidgets[key] = widget
                widget.showGrid(x=True, y=True)

                for i, name in enumerate(value.get('lines', None)):
                    self.plotWidgets[key] = widget
                    widget.legend = widget.addLegend()
                    plot_type = value.get('types', ['Line' for i in range(i+1)])[i]

                    if plot_type == 'Line':
                        self.plotItems[key+'_'+name] = widget.plot(pen = self.penRotation[i%len(self.penRotation)],
                                                                    symbol = value.get("markers", ["o", None])[i],
                                                                    name = key+'_'+name)
                    if plot_type == 'Scatter':
                        self.plotItems[key+'_'+name] = pg.ScatterPlotItem(pen = self.penRotation[i%len(self.penRotation)],
                                                                            symbol = "o",
                                                                            name = key+'_'+name)


                        widget.addItem(self.plotItems[key+'_'+name])

            else:
                if value['type'] == 'Line':
                    widget = pg.PlotWidget()
                    self.plotWidgets[key] = widget
                    widget.showGrid(x=True, y=True)

                    self.plotItems[key] = self.plotWidgets[key].plot(pen = self.penRotation[0], symbol = "o")

                    self.plotWidgets[key].setLabel(axis = 'left', text = value.get('y_label', 'y'))
                    self.plotWidgets[key].setLabel(axis = 'bottom', text = value.get('x_label', 'x'))
                    self.plotWidgets[key].setTitle(value.get('title', key))

                    self.plotWidgets[key].setAspectLocked(False)
                    #self.plotWidgets[key].setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)


                if value['type'] == 'Map':
                    # plot = pg.PlotItem()
                    # plot.setAspectLocked(False)
                    # plot.setLabel(axis='left', text = value.get('y_label', 'y'))
                    # plot.setLabel(axis='bottom',text = value.get('x_label', 'x'))
                    # plot.setTitle(value.get('title', key))

                    # self.plotWidgets[key] = pg.ImageView(view = plot)
                    # self.plotItems[key] = self.plotWidgets[key]
                    # self.plotItems[key].setImage(np.zeros((1,1)))
                    # self.plotItems[key].setColorMap(self.cmap)
                    # self.plotWidgets[key].setHistogramLabel(text = value.get('histogram_label', 'signal'))
                    self.plotWidgets[key] = pg.GraphicsLayoutWidget()


                    self.plotItems[key + '_parent'] = self.plotWidgets[key].addPlot(row = 0, col = 0)
                    self.plotItems[key] = pg.ImageItem()
                    self.plotItems[key + '_parent'].addItem(self.plotItems[key])
                    self.plotItems[key + '_parent'].setLabel('left', value.get('y_label', 'y'))
                    self.plotItems[key + '_parent'].setLabel('bottom', value.get('x_label', 'x'))

                    self.plotItems[key].setImage(np.zeros((1,1)))

                    self.plotWidgets[key+'_histo'] = pg.HistogramLUTItem()
                    self.plotWidgets[key+'_histo'].setImageItem(self.plotItems[key])
                    self.plotWidgets[key+'_histo'].gradient.setColorMap(self.cmap)
                    self.plotWidgets[key].addItem(self.plotWidgets[key+'_histo'])


                    # # button_histogram_widget = pg.LayoutWidget()
                    # # button_histogram_widget.addWidget(self.plotWidgets[key+'_histoAutoScale'], row=0, col=0)
                    # # button_histogram_widget.addItem(self.plotWidgets[key+'_histo'], row=1, col=0)

                    # #self.plotWidgets[key].addItem(button_histogram_widget)

                    # #self.plotWidgets[key].addItem(button_widget, row = 1, col = 0)
                    # self.plotWidgets[key].addItem(self.plotWidgets[key+'_histo'], row = 0, col = 1)
                    # #self.plotWidgets[key].setHistogramLabel(text = value.get('histogram_label', 'signal'))




                    #self.plotWidgets[key].setAspectLocked()
                    #self.plotWidgets[key].setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

                if value['type'] == 'Scatter':
                    widget = pg.PlotWidget()
                    self.plotWidgets[key] = widget
                    widget.showGrid(x=True, y=True)

                    self.plotItems[key] = pg.ScatterPlotItem(symbol = "o")#pen = self.penRotation[0], symbol = "o")
                    widget.addItem(self.plotItems[key])

                    self.plotWidgets[key].setLabel(axis = 'left', text = value.get('y_label', 'y'))
                    self.plotWidgets[key].setLabel(axis = 'bottom', text = value.get('x_label', 'x'))
                    self.plotWidgets[key].setTitle(value.get('title', key))

                if value['type'] == 'Counts':
                    widget = pg.PlotWidget()
                    self.plotWidgets[key] = widget
                    widget.showGrid(x=True, y=True)

                    self.plotItems[key] = []

                    self.plotWidgets[key].setLabel(axis = 'left', text = value.get('y_label', 'clicks'))
                    self.plotWidgets[key].setLabel(axis = 'bottom', text = value.get('x_label', 'x'))
                    self.plotWidgets[key].setTitle(value.get('title', key))
                    self.plotWidgets[key].setLimits(yMin=0, yMax=1, minYRange = 1)
                    self.plotWidgets[key].showGrid(x = False, y = False)
                    self.plotWidgets[key].hideAxis('left')

                #self.plotWidgets[key].setAspectLocked(False)
                #self.plotWidgets[key].setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

            dockWidget.setWidget(self.plotWidgets[key])


            plotLayout.addWidget(dockWidget, #self.plotWidgets[key],#dockWidget,
                                 self.layout[key]['loc'][0],
                                 self.layout[key]['loc'][1],
                                 self.layout[key]['loc'][2],
                                 self.layout[key]['loc'][3])


        plotWidget = QWidget()
        plotWidget.setLayout(plotLayout)

        self.progressBar = QProgressBar(self)
        self.progressBar.setValue(0)

        self.progressBar.setMaximum(self.layout.get("n_iterations", 1_000_000))
        self.progressBar.setFormat("{}/{}".format(0,self.layout.get("n_iterations", 1_000_000)))

        verticalLayout.addWidget(self.progressBar)
        verticalLayout.addWidget(horizontalWidget)
        verticalLayout.addWidget(plotWidget)


        self.main_widget.setLayout(verticalLayout)

        try:
            self._stop()
        except:
            pass

        try:
            self._start()
        except:
            pass

    def _redockAll(self):
        self.main_widget.setParent(None)
        self._createLayout(self.layout)
        self._start()

    def updateProgress(self, v):
        self.progressBar.setValue(v)

    def _start(self):
        self.timer.start(500)
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)

    def _stop(self):
        self.timer.stop()
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)

    def _stopData(self):
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(False)
        self.stopDataButton.setEnabled(False)

    def _save(self):
        # Start a new thread for the save operation
        save_thread = Thread(target=self.send_save_command)
        save_thread.start()

    def send_save_command(self):
        # Create a new context and socket for this thread
        thread_context = zmq.Context()
        thread_socket = thread_context.socket(zmq.REQ)
        thread_socket.connect(f"tcp://localhost:{CONTROL_PORT}")

        # Send save command to the measurement without waiting for a response
        thread_socket.send_string("SAVE")
        try:
            thread_socket.recv_string(flags=zmq.NOBLOCK)
        except zmq.Again:
            pass
        finally:
            thread_socket.close()
            thread_context.term()




    def updatePlots(self):
        events = dict(self.poller.poll(100))  # Poll sockets with a 100-ms timeout
        if self.zmq_socket in events:
            try:
                data = self.zmq_socket.recv_pyobj(flags=zmq.NOBLOCK)
            except zmq.Again as e:
                return None  # No data received

        else:
            return None

        if self.layout == None:
            try:
                self.layout = data["layout"]
            except:
                return None

            self._createLayout(self.layout)

        elif self.layout != data["layout"]:
            self.main_widget.setParent(None)
            self.layout = data["layout"]
            self._createLayout(self.layout)


        self.progressBar.setValue(data.get("iter", 0))
        self.progressBar.setFormat("{}/{}".format(data.get("iter", 0),
                                                  self.layout.get("n_iterations", 1_000_000)))

        for key, value in self.layout.items():
            if value.get('lines', None):
                for i, name in enumerate(value.get('lines', None)):
                    plot_type = value.get('types', ['Line' for i in range(i+1)])[i]
                    if plot_type == 'Line':
                        self.plotItems[key+'_'+name].setData(data["data"].get(key+'_'+name,{}).get('x', []),
                                                             data["data"].get(key+'_'+name,{}).get('y', []))
                        try:
                            self.plotWidgets[key].legend.removeItem(self.plotItems[key+'_'+name])
                            self.plotWidgets[key].legend.addItem(self.plotItems[key+'_'+name],
                                                                 data["data"].get(key+'_'+name,{}).get('legend', key+'_'+name))
                        except:
                            pass
                    if plot_type == 'Scatter':
                        self.plotItems[key+'_'+name].clear()
                        self.plotItems[key+'_'+name].setData(data["data"].get(key+'_'+name,{}).get('x', []),
                                                             data["data"].get(key+'_'+name,{}).get('y', []))
                        try:
                            self.plotWidgets[key].legend.removeItem(self.plotItems[key+'_'+name])
                            self.plotWidgets[key].legend.addItem(self.plotItems[key+'_'+name],
                                                                 data["data"].get(key+'_'+name,{}).get('legend', key+'_'+name))
                        except:
                            pass


            else:
                if value['type'] == 'Line':
                    self.plotItems[key].setData(data["data"].get(key,{}).get('x', []),
                                                data["data"].get(key,{}).get('y', []))

                if value['type'] == 'Map':


                    self.plotItems[key].setImage(data["data"].get(key,{}).get('z',np.zeros((1,1))), autoLevels = False)

                    x_values = data["data"].get(key,{}).get('x', None)
                    y_values = data["data"].get(key,{}).get('y', None)
                    z_values = data["data"].get(key,{}).get('z', None)

                    try:
                        scale_x = (x_values[-1] - x_values[0]) / z_values.shape[1]
                        scale_y = (y_values[-1] - y_values[0]) / z_values.shape[0]
                        translate_x = x_values[0]
                        translate_y = y_values[0]

                    except:
                        return None

                    transform = QtGui.QTransform()
                    transform.translate(translate_x, translate_y)
                    transform.scale(scale_x, scale_y)
                    self.plotItems[key].setTransform(transform)


                if value['type'] == 'Scatter':
                    self.plotItems[key].clear()
                    self.plotItems[key].setData(data["data"].get(key,{}).get('x', []),
                                                data["data"].get(key,{}).get('y', []))

                if value['type'] == 'Counts':
                    self.plotWidgets[key].clear()
                    if data["data"].get('title', None):
                        self.plotWidgets[key].setTitle(data["data"]['title'])
                    for t in data["data"].get(key, []):
                        l = self.plotWidgets[key].addLine(x = t, y = None, pen=pg.mkPen('orange', width=3))
                        #self.plotItems[key].append(l)
                    #self.parent.plot_data[key] = []

def main():
    zmq_context = zmq.Context()
    zmq_socket = zmq_context.socket(zmq.SUB)
    zmq_socket.connect(f"tcp://localhost:{DATA_PORT}")
    zmq_socket.setsockopt_string(zmq.SUBSCRIBE, '')  # Subscribe to all topics
    zmq_socket.setsockopt(zmq.RCVHWM, 1)  # Set high-water mark to 1


    app = QApplication(sys.argv)

    main_window = MainWindow(zmq_socket)
    main_window.show()
    main_window.timer.start(500)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
