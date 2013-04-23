# coding: utf-8
import pysolver.grids.grid2d
import pysolver.plotting
import numpy as np
from scipy.constants import pi

N = 30
domain_spec = pysolver.grids.grid2d.DomainSpec((N, N), (-0.5, 0.5), (-0.5, 0.5))
grid = pysolver.grids.grid2d.FV(domain_spec, num_ghost_cells=2)
x, y = grid.getCellCenterPositions()
r = np.sqrt(x*x+y*y)

ph = pysolver.plotting.PlottingHelper()
plot = ph.getPlotter()

u = np.cos(2*pi*x)*np.sin(2*pi*y)
v = np.sin(-2*pi*x)*np.cos(2*pi*y)

ph.quiver(x, y, u, v)
rho = 1.0 + (r < 0.5)*np.cos(2*pi*(r-0.25))**2.0
plot.imshow(np.rot90(rho), interpolation='none', extent=grid.getExtent())
plot.colorbar()
plot.savefig('ic.png')
