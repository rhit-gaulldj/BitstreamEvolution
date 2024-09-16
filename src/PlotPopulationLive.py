import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from matplotlib import colormaps
import configparser
import re
from Config import Config
import math 
import numpy as np
import sys
from utilities import determine_color
from os.path import exists
from os import mkdir

FRAME_INTERVAL = 10000
config = Config("workspace/builtconfig.ini")

plots_dir = config.get_plots_directory()
plot = lambda fig, ax, function : animation.FuncAnimation(fig, function, interval=FRAME_INTERVAL, cache_frame_data=False, fargs=(fig,ax))

def plot_population_time_dynamics(i, fig, time_ax):
    data = open('workspace/bitstream_avg.log','r').read()
    lines = data.split('\n')

    num_rows = 3
    if(config.get_routing_type == "NEWSE"):
        num_rows = 2
    num_cols = len(config.get_accessed_columns())

    gens = []
    image = []
    for line in lines:
        if len(line) > 1:
            index = line.find(":")
            t = int(line[0:index])
            gens.append(t)
            d=line[index+1:]
            l = []
            for i in range(96): #iterate through logic tiles
                cur_sum = 0.0
                for j in range(num_cols*num_rows): #iterate through bits in logic tile
                    cur_sum += ord(d[num_cols*num_rows*i + j]) - 32
                l.append(cur_sum / (num_cols*num_rows*config.get_population_size()))
            image.append(l)

    print(image)
    image = np.array(image)
    print(image)
    time_ax.clear()                         
    image_ax = time_ax.imshow(image, cmap="Purples", vmin=0, vmax=1)
    time_ax.set_yticks(np.arange(len(gens)), labels=gens)
    labels = time_ax.yaxis.get_ticklabels()
    for i in range(len(labels)):
        if i % 10 != 0:
            labels[i].set_visible(False)
    time_ax.set(ylabel='Generation', xlabel='Logic Tile', title='Percentage of 1\'s in Logic Tiles across the Population')
    plt.colorbar(mappable=image_ax, ax=time_ax, orientation='horizontal')

    if(config.get_save_plots()):
        fig.savefig(plots_dir.joinpath("avg_bitstream_over_time.png"))
    
                               
def plot_population_space_dynamics(i, fig, space_ax):
    pass

def run():
    fig = plt.figure()
    time_ax = fig.add_subplot(1,1,1)
    ani = plot(fig, time_ax, plot_population_time_dynamics)

    plt.show()

if (__name__ == "__main__"):
    run()