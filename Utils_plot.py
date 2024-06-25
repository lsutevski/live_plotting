import ipywidgets as widgets
from IPython.display import display as ipydisplay, clear_output

import numpy as np
import IPython.display as display


import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.axes import Axes

import time

import asyncio
import zmq
import threading



# Matplotlib widget
class LivePlot:
    '''
    This is a class which handles live plotting via matplotlib widget.
    '''
    def __init__(self, experiment, result_handles, name = None, refresh_time = 1):
        self.experiment = experiment
        self.is_running = False
        self.data = result_handles

        self.start_button = widgets.Button(description="Start", button_style='success')
        self.stop_button = widgets.Button(description="Stop", button_style='danger', disabled=True)
        self.save_button = widgets.Checkbox(value=False, description='save')

        self.progress_bar = widgets.FloatProgress(value=0.0, min=0.0, max=1.0, description='Iteration: 0', bar_style='info')

        self.output_area = widgets.Output()

        self.start_button.on_click(self.start)
        self.stop_button.on_click(self.stop)

        self.buttons = widgets.HBox([self.start_button, self.stop_button, self. save_button])
        self.layout = widgets.VBox([self.progress_bar, self.buttons, self.output_area])

        self.refresh_time = refresh_time

        clear_output(wait=True)

        ipydisplay(self.layout)


        with self.output_area:
            #self.experiment.plot(*self.experiment.analysis(self.data), save = False)
            self.experiment.plot(*self.experiment.analysis(self.data), save = False)


    def start(self, b):
        if not self.is_running:
            self.is_running = True
            self.stop_button.disabled = False
            self.start_button.disabled = True
        
            self.signal = self.experiment.analysis(self.data)
            self.task = asyncio.create_task(self.run_plotting())
            self.data_task = asyncio.create_task(self.get_data())

    async def run_plotting(self):
        while self.is_running and (self.experiment.iter + 1)< self.experiment.n_iterations:
            with self.output_area:
                self.experiment.plot(*self.signal, live = True, save = self.save_button.value)
                self.progress_bar.value = (self.experiment.iter + 1)/self.experiment.n_iterations
                self.progress_bar.description = 'Iteration: ' + str(self.experiment.iter+1)
            await asyncio.sleep(self.refresh_time)  # Update interval
        self.stop()  # Auto-stop when done

    async def get_data(self):
        while self.is_running and self.experiment.iter < self.experiment.n_iterations:
            self.signal = self.experiment.analysis(self.data)
            await asyncio.sleep(0.9*self.refresh_time)  # Update interval
        self.stop()  # Auto-stop when done

    def stop(self):
        if self.is_running:
            self.is_running = False
            self.stop_button.disabled = True
            self.start_button.disabled = False
            if self.task and not self.task.done():
                self.task.cancel()
                self.data_task.cancel()
            
            self.experiment.plot(*self.experiment.analysis(self.data), live = True, save = True)


    def __del__(self):
        self.stop()



##################### PyQtGraph #####################

DATA_PORT = 5555
CONTROL_PORT = 5556

class LivePlotting:
    def __init__(self):
        self.context = zmq.Context()

        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(f"tcp://*:{DATA_PORT}")
        self.socket.setsockopt(zmq.SNDHWM, 1)

        self.control_context = zmq.Context()
        self.control_socket = self.control_context.socket(zmq.REP)
        self.control_socket.bind(f"tcp://*:{CONTROL_PORT}")
        
        self._running = False
        self._save = False

        self._stop_event = threading.Event()
        self._thread = None
        self._lock = threading.RLock()  # Recursive lock to prevent deadlock within the same thread

    def _fetch_and_send_data(self, meas):
        while not self._stop_event.is_set():
            with self._lock:
                data = meas.getData()
                iter = self.meas.iter
                
            self.socket.send_pyobj(data)
            
                
            if iter == meas.n_iterations-1:
                self._stop_event.set()
                time.sleep(1)
                
                with self._lock:
                    data = meas.getData()
                self.socket.send_pyobj(data)
                    #self._stop_event.set()
                    #self._thread.join(0)

            time.sleep(1)  # Adjust the sleep time as needed

    def handle_control(self):
        poller = zmq.Poller()
        poller.register(self.control_socket, zmq.POLLIN)

        while not self._stop_event.is_set():
            socks = dict(poller.poll(100))  # Poll sockets with a 100-ms timeout
            if self.control_socket in socks and socks[self.control_socket] == zmq.POLLIN:
                try:
                    message = self.control_socket.recv_string(flags=zmq.NOBLOCK)
                    if message == "SAVE":
                        self.control_socket.send_string("OK")
                        save_thread = threading.Thread(target=self.meas.plot, args= self.signal,
                                                        kwargs= {'show_fig' : False,'save' : True})
                        save_thread.start()
                except zmq.ZMQError as e:
                    if e.errno == zmq.ETERM:
                        break

    def start_control_thread(self):
        self._control_thread = threading.Thread(target=self.handle_control)
        self._control_thread.start()

    def start(self, meas, refresh_rate = 1):
        '''
        Receives as an argument a measurement and a refresh rate in seconds.
        '''
        self.refresh_rate = refresh_rate
        self.stop()

        self.meas = meas
        self.running = True

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._fetch_and_send_data, args=(meas,))
        self._thread.start()

        self.start_control_thread()

    def stop(self):
        if self._thread is not None and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join()
            self._control_thread.join()
            self.running = False