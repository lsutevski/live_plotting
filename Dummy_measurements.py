

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.axes import Axes


class Ramsey:
    def __init__(self):
        self.w = 2*np.pi/2
        self.k = 0.2
        self.t_max = 10
        self.n_points = 100

        self.nx = 50
        self.ny = 100
        
        self.n_iterations = 1_000
        self.iter = 0
        self.flag = True
        
        self.x = np.linspace(0, self.t_max, self.n_points)
        self.ps = (1-np.exp(-self.k*self.x)*np.sin(self.w*self.x))/2

        self.xs = np.linspace(0, 5, self.nx)
        self.ys = np.linspace(0, 10, self.ny)
        
        self.y = np.zeros(self.n_points)
        
        x, y = np.meshgrid(self.xs, self.ys)
        k_x = 1.5
        k_y = 4
        self.ps_z = np.exp(-((x-2.5)/k_x)**2 - ((y-5)/k_y)**2)
        self.z = np.zeros((self.ny, self.nx))
        
        self.rng = np.random.default_rng()

    def math_func(self):
        return np.array(self.rng.uniform(0,1, size = self.n_points) < self.ps, dtype = float)

    def map_func(self):
        return np.array(np.reshape(self.rng.uniform(0,1, size = (self.ny, self.nx)), (self.ny, self.nx)) > self.ps_z, dtype = float)
        
    def get_data(self):
        while self.iter < (self.n_iterations - 1) and self.flag:
            self.iter += 1
            self.y = self.y + self.math_func()
            self.z = self.z + self.map_func()
            yield self.y/self.iter, self.z/self.iter

    def execute_meas(self):
        self.data = self.get_data()
        return self.data
        
    def analysis(self, data):
        y, z = next(self.data)
        signal = {
            'line' : y,
            'map' : z
        }
        fit = {
            'line' : self.ps,
        }

        return (signal, fit)
    
    def plot(self, signal, fit, live = False, save = False):
        if not live:
            self.fig, self.axs = plt.subplots(1, 2, figsize = (10,5))
        else:
            for ax in self.axs:
                ax.clear()
        
        y = signal['line']
        z = signal['map']

        y_fit = fit['line']
        
        
        self.axs[0].scatter(self.x, y)
        self.axs[0].plot(self.x, y_fit)
        
        self.axs[1].pcolorfast(self.xs, self.ys, z)

        self.fig.canvas.draw()
        self.hdisplay.update(obj = self.fig)
        if save:
            print('Saved')
        else:
            pass
    def getData(self):
        data = self.data

        data_pack = {
            "iter" : self.iter,
            "name" : "Ramsey",
            "n_iterations" : self.n_iterations,
            }

        data_pack["layout"] = {
                "line" : {
                    'types' : ['Scatter', 'Line'],
                    'lines' : ['signal', 'fit'],
                    'x_label' : "t [ms]",
                    'y_label' : r'$p_e$',
                    'loc' : [0, 0, 1, 1]
                },

                "map" : {
                    'type' : 'Map',
                    'loc' : [0, 1, 1, 1]
                },
            }

        signal, fit = self.analysis(data)


        data_pack["data"] = {
            'line_signal' : {
                'x' : self.x,
                'y' : signal['line'],
            },
            'line_fit': {
                'x' : self.x,
                'y' : fit['line'],
            },
            'map' : {
                'x' : self.xs,
                'y' : self.ys,
                'z' : signal['map']
            },
        }
        return data_pack


class RO:
    def __init__(self):
        self.nx = 51
        self.ny = 51
        
        self.n_iterations = 1_000_000
        self.iter = 0

        self.xs = np.linspace(-10, 10, self.nx)
        self.ys = np.linspace(-10, 10, self.ny)
        
        x, y = np.meshgrid(self.xs, self.ys)

        self.flag = True
        
        k_x = 1.5
        k_y = 1.5

        x_0, y_0 = 3, 3
        
        self.ps_z = np.exp(-((x-x_0)/k_x)**2 - ((y-y_0)/k_y)**2) + np.exp(-((x+x_0)/k_x)**2 - ((y+y_0)/k_y)**2)
        self.ps_z = self.ps_z / np.max(self.ps_z)
        self.z = np.zeros((self.ny, self.nx))
        self.rng = np.random.default_rng()

    def map_func(self):
        return np.array(np.reshape(self.rng.uniform(0,1, size = (self.ny, self.nx)), (self.ny, self.nx)) > self.ps_z, dtype = float)
        
    def get_data(self):
        while self.iter < (self.n_iterations - 1) and self.flag:
            self.iter += 1
            self.z = self.z + self.map_func()
            z = self.z/self.iter
            
            yield z

    def execute_meas(self):
        self.data = self.get_data()
        return self.data
        
    def analysis(self, data):
        z = next(self.data)
        signal = {
            'map' : z,
        }
        return (signal,)
    
    def plot(self, signal, live = False, save = False):
        if not live:
            self.fig, self.axs = plt.subplots(1, 1, figsize = (10,5))
        else:
            self.axs.clear()
    
        z = signal['map']
        
        self.axs.pcolorfast(self.xs, self.ys, z)

        self.fig.canvas.draw()
        if save:
            print('Saved')
        else:
            pass
    

    def getData(self):
        data = self.data

        data_pack = {
            "iter" : self.iter,
            "name" : "RO",
            "n_iterations" : self.n_iterations,
            }

        data_pack["layout"] = {
                "IQ" : {
                    'type' : 'Map',
                    'x_label' : "I [V]",
                    'y_label' : "Q [V]",
                    'loc' : [0, 0, 1, 1]
                },
            }

        signal, = self.analysis(data)
        


        data_pack["data"] = {
            'IQ' : {
                'x' : self.xs,
                'y' : self.ys,
                'z' : signal['map'],
            },
        }
        return data_pack