# coding: utf-8

from matplotlib._png import read_png
import os

def add_data(plot, mach=0.4):
    path = os.path.dirname(os.path.abspath(__file__))
    data = read_png(os.path.join(path, 'amick_flat_M%1.2f.png' % mach))
    plot.imshow(data, extent=[0.0, 1.0, .2, -1.])
    return plot


if __name__ == "__main__":
    import matplotlib.pyplot as plot
    plot.ion()
    add_data(plot)
    plot.axes().set_aspect(0.5)
    plot.draw()
    raw_input()
