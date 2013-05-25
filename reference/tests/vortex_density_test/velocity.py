# coding: utf-8
import pysolver.grids.grid2d
import pysolver.plotting
import numpy as np
from scipy.constants import pi

N = 30
domain_spec = pysolver.grids.grid2d.DomainSpec((N, N), (-0.5, 0.5), (-0.5, 0.5))
grid = pysolver.grids.grid2d.FV(domain_spec, num_ghost_cells=2)
x, y = grid.getCellCenterPositions()
ph = pysolver.plotting.PlottingHelper()

u = np.cos(2*pi*x)*np.sin(2*pi*y)
v = np.sin(-2*pi*x)*np.cos(2*pi*y)

ph.quiver(x, y, u, v)

raw_input()

l = np.sqrt(u*u + v*v)
plot = ph.getPlotter()
plot.imshow(l, interpolation='non')
raw_input()
