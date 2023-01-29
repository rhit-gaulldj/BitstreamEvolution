import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import configparser
import re
from Config import Config
import math

"""
Static parameters can be found and changed in the config.ini file in the root project folder
DO NOT CHANGE THEM HERE
"""

def animate_generation(i):
    avg_fitness = []
    graph_data = open('workspace/alllivedata.log','r').read()
    lines = graph_data.split('\n')
    xs = []
    ys = []
    
    # There used to be a bug where the program always believed it was in sim mode, but once that was fixed, the code below
    # broke the chart on non-simulation mode. As such, the target frequency is just always set to 1728, which worked fine before
    #if not config.get_simulation_mode() == "FULLY_INTRINSIC":
        #target_freq = 1728
        # Based on my calculations for the maximum number of bits we can 
        # modify with our given search space constraints
    #else:
        #target_freq = [config.get_desired_frequency()]*(config.get_population_size+2)
    target_freq = 1728
    
    base = [config.get_desired_frequency()]*0
    for line in lines:
        if len(line) > 1:
            x, y = line.split(',')
            if x == "../hardware": x = "hardware0";
            match = re.match(r"([a-z]+)([0-9]+)", x, re.I)
            if match:
                items = match.groups()
                xs.append(int(items[1]))
            ys.append(float(y))
    avg = 0.0
    if sum(ys) > 0:
        avg = sum(ys)/len(ys)
    else:
        avg_fitness.append(avg)
    ax1.clear()
    # ax1.plot(xs, ys)
    ax1.set_xlim([0, config.get_population_size()+1])
    ax1.plot(target_freq, "r--")
    ax1.plot(base, "w-")
    ax1.plot(avg_fitness, color="violet")
    '''if not config.get_simulation_mode() == "FULLY_INTRINSIC":
        ax1.set_yscale('symlog')
        ax1.set_ylim([0, 1000000])'''
    # ax1.plot.stem(xs,ys,  color="green", use_line_collection=True)
    ax1.scatter(xs, ys)
    # plt.stem(xs, ys, markerfmt="bo", linefmt="b-", use_line_collection=True)
    # plt.plot(xs, ys, color="blue")
    ax1.set(xlabel='Circuit Number', ylabel='Fitness', title='Circuit Fitness this Generation')

# fig2 = plt.figure()
def animate_epoch(i):
    graph_data = open('workspace/bestlivedata.log','r').read()
    lines = graph_data.split('\n')
    xs = []
    ys = []
    zs = []
    ws = []
    ts = []
    ds = []
    for line in lines:
        if len(line) > 1:
            x, y, z, w, t, d = line.split(',')
            xs.append(int(x))
            ys.append(float(y))
            zs.append(float(z))
            ws.append(float(w))
            ts.append(float(t))
            ds.append(float(d))
    ax2.clear()
    # ax2.set_yscale('symlog')
    # Plot the overall best before the gen best so the gen best line appears on top
    ax2.plot(xs, ts, color="#00b87d") # Ovr best Fitness
    ax2.plot(xs, ys, color="green") # Generation/Epoch Best Fitness
    ax2.plot(xs, zs, color="red") # Generation Worst Fitness
    ax2.plot(xs, ws, color="yellow") # Generation Average Fitness
    ax2.tick_params(axis='y', labelcolor='white')
    
    ax3.clear()
    ax3.plot(xs, ds, color="#5a70ed") # Generation diversity measure
    ax3.tick_params(axis='y', labelcolor='#5a70ed')
    ax3.set_ylabel('Diversity', color='#5a70ed')
    
    ax2.set(xlabel='Generation', ylabel='Fitness', title='Best Circuit Fitness per Generation')


def animate_waveform(i):    
    graph_data = open('workspace/waveformlivedata.log','r').read()
    lines = graph_data.split('\n')
    pulse_trigger = [341]*500
    xs = []
    ys = []
    for line in lines:
        if len(line) > 1:
            x, y = line.split(',')
            xs.append(int(x))
            ys.append(float(y))
    ax4.clear()
    ax4.set_ylim([0, 1000])
    ax4.plot(pulse_trigger, "r--")
    ax4.plot(xs, ys, color="blue")
    ax4.set(xlabel='Time (50 mS Total)', ylabel='Voltage (normalized)', title='Current Hardware Waveform')

def animate_map(i):
    graph_data = open('workspace/maplivedata.log','r').read()
    lines = graph_data.split('\n')
    scale_factor = int(lines[0])
    lines.pop(0) # Remove scale factor from the lines set
    xs = []
    ys = []
    sizes = []
    
    for line in lines:
        vals = line.split(' ')
        if (len(vals) > 2 and len(vals[2]) > 0):
            row = int(vals[0])
            col = int(vals[1])
            fit = float(vals[2])
            sizes.append(fit)
            xs.append((col + 0.5) * scale_factor)
            ys.append((row + 0.5) * scale_factor)

    ax5.clear()
    ax5.scatter(xs, ys, s=sizes)
    ax5.set_xlim(0, 1024)
    ax5.set_ylim(0, 1024)
    ax5.set(xlabel='Max Voltage (norm)', ylabel='Min Voltage (norm)', title='Elite Map')

config_parser = configparser.ConfigParser()
config_parser.read("data/config.ini")
config = Config(config_parser)

style.use('dark_background')

rows = 2
cols = 1
has_wf_plot = False
if config.get_simulation_mode() == 'FULLY_INTRINSIC' or config.get_simulation_mode() == 'FULLY_SIM':
    rows = rows + 1
    has_wf_plot = True

has_map_plot = False
if config.get_selection_type() == 'MAP_ELITES':
    # Replace the fitness plot with the map plot
    has_map_plot = True

fig = plt.figure()

ax2 = fig.add_subplot(rows, cols, 1)
ax3 = ax2.twinx()
if has_wf_plot:
    ax4 = fig.add_subplot(rows, cols, 3)

if has_map_plot:
    ax5 = fig.add_subplot(rows, cols, 2)
else:
    ax1 = fig.add_subplot(rows, cols, 2)
    ax1.set_xticks(range(1, config.get_population_size(), 1))

if has_wf_plot:
    ani3 = animation.FuncAnimation(fig, animate_waveform)#, interval=200)

if has_map_plot:
    ani4 = animation.FuncAnimation(fig, animate_map)
else:
    ani = animation.FuncAnimation(fig, animate_generation)

ani2 = animation.FuncAnimation(fig, animate_epoch)

plt.subplots_adjust(hspace=0.50)
plt.show()