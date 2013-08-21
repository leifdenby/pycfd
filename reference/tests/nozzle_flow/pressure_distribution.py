"""
Exact solution for pressure and velocity for incompressible flow through a
nozzle. Based on Bernoulli's equation.
"""

import pysolver.plotting
import reference.atmospheric_flow.atmospheres

import numpy as np

xl = 1.0
N = 100

x = np.linspace(0., xl, N)

# inflow parameters
atmos_profile = reference.atmospheric_flow.atmospheres.StandardEarthAtmosphere()
rho0 = atmos_profile.rho
p0 = atmos_profile.p
u0 = 1.0
Al = 1.0

# output parameters
Ar = 2.0

# area function
A = lambda x: Al - x*(Al-Ar)/xl
# pressure along center of nozzle
p = lambda x: p0 + .5*rho0*u0**2.*(1-Al**2./(A(x)**2.))
# velocity along center of nozzle
u = lambda x: u0*Al/A(x)

if False:
    # pressure & velocity plot
    import matplotlib as mpl
    mpl.rcParams['text.usetex']=True
    plotter = pysolver.plotting.PlottingHelper()
    plot = plotter.getPlotter()
    plot.subplot(121)
    plot.plot(x, u(x))
    plot.grid(True)
    plot.xlim(0., xl)
    plot.legend()
    plot.xlabel("length along nozzle/m")
    plot.ylabel("velocity/(m/s)")
    plot.subplot(122)
    plot.plot(x, p(x))
    plot.grid(True)
    plot.xlim(0., xl)
    plot.ylabel("Pressure/Pa")
    plot.xlabel("length along nozzle/m")
    plot.legend()
    plot.suptitle(r"Incompressible nozzle flow\\$A_l=%g$, $A_r=%g$, $\rho_0=%g$, $p_0=%g$, $u_0=%g$, $x_l=%g$" % (Al, Ar, rho0, p0, u0, xl))
    plot.draw()
    raw_input()


if True:
    w = (1-Ar/Al)/xl
    dpdx = lambda x: -rho0*u0**2.*w/((1-w*x)**3.)

    x_i = .5*(x[1:] + x[:-1])

    dpdx_num = (p(x)[1:] - p(x)[:-1])/(x[1]-x[0])

    plotter = pysolver.plotting.PlottingHelper()
    plot = plotter.getPlotter()
    plot.plot(x_i, dpdx(x_i), label='dpdx (exact)')
    plot.plot(x_i, dpdx_num, label='dpdx (num)')
    plot.grid(True)
    plot.xlim(0., xl)
    plot.legend()
    plot.xlabel("length along nozzle/m")
    plot.ylabel(r"$\frac{\partial p}{\partial x}$")
    raw_input()
