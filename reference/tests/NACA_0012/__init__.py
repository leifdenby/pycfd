# coding: utf-8

from matplotlib._png import read_png
import matplotlib.pyplot as plot

data = read_png('amick_flat_M0.70.png')
plot.imshow(data, extent=[0.0, 1.0, .2, -1.])
plot.axes().set_aspect(0.5)

#plot.gca().invert_yaxis()

plot.show()
