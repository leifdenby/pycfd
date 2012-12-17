"""
Lid-driven cavity problem with fixed density.
"""

import pysolver.run_settings
import run_handling

import pysolver.models.soundproof.variable_density_ns
import pysolver.grids.grid2d
import pysolver.numMethods.soundproof.bcg
import pysolver.numMethods.soundproof.mac
import pysolver.tests
import pysolver.tests.lid_driven_cavity

import reference.atmospheric_flow.stratification_profiles

N = (100, 100)
x = (0.0, 1000.0)
y = (0.0, 1000.0)

domain_spec = pysolver.grids.grid2d.DomainSpec(N=N, x=x, y=y)

base_state = {'x_vel': 0.0, 'y_vel': 0.0, 'rho': 1.0}
ambient_state = pysolver.tests.ConstantState(base_state)
viscosity = 0.0

model = pysolver.models.soundproof.variable_density_ns.VariableDensityIncompressibleNS2D(viscosity=viscosity, diffusion_coefficient=0.0, g=1.0)
test = pysolver.tests.RigidBox2D(ambient_state=ambient_state)

import pysolver.grids.boundary_conditions as BCs
test.boundary_conditions[2] = tuple([BCs.DensityAtWall() for i in range(4)])

output_times = [1000.0]

num_scheme = pysolver.numMethods.soundproof.bcg.BCG(model=model, boundary_conditions=test.boundary_conditions, domain_spec=domain_spec)
#num_scheme = pysolver.numMethods.soundproof.mac.MAC(model=model, boundary_conditions=test.boundary_conditions, domain_spec=domain_spec)

def plotting_routine(Q, grid, model, test, t, n_steps, num_scheme, save_fig = False):
    from pysolver.plotting import PlottingHelper
    import matplotlib.colors
    import numpy as np
    plottingHelper = PlottingHelper(for_print=save_fig)
    plot = plottingHelper.getPlotter()
    n = grid.num_ghost_cells
    (x, y) = grid.getCellCenterPositions(0)
    (u, v) = (Q.view(model.state).x_velocity[n:-n,n:-n], Q.view(model.state).y_velocity[n:-n,n:-n])
    if hasattr(model.state,'temp'):
        if hasattr(test,"temp_range"):
            (temp_min, temp_max) = getattr(test, "temp_range")
            temp_norm = matplotlib.colors.Normalize(vmin = temp_min, vmax = temp_max, clip = True)
        else:
            temp_norm = None
    extent = grid.getExtent(0)
    (Nx, Ny) = grid.getNumCells()

    f = plot.figure(0)
    f.clf()
    f.text(0.5, 0.92, "%d t=%es\n%s\n%s\n%s\n%s" % (n_steps, t, model, grid, test, num_scheme), horizontalalignment='center')

    s = plot.subplot(121)
    #if hasattr(model.state,'temp'):
        #plot.imshow(np.rot90(Q.view(model.state).temp[n:-n,n:-n]), norm=temp_norm, extent=extent, interpolation="nearest")
        #plot.colorbar()
    if hasattr(model.state,'rho'):
        plot.imshow(np.rot90(Q.view(model.state).rho[n:-n,n:-n]), extent=extent, interpolation="nearest")
        plot.colorbar()
    plot.grid(True)
    k = Nx/20 if Nx/20 > 0 else 1
    q = plottingHelper.quiver(x[::k,::k], y[::k,::k], u[::k,::k], v[::k,::k])
    vel_max = np.max(np.sqrt(u*u + v*v))
    qk = plot.quiverkey(q, 0.5, 0.3, vel_max, r'$%.4f \frac{m}{s}$' % vel_max, labelpos='W',
                           fontproperties={'weight': 'bold'})

    #c_levels = np.linspace(1.08, 1.18, 10)
    #plot.contour(x, y, Q.view(model.state).rho[n:-n,n:-n], c_levels, colors="black")

    s = plot.subplot(122)
    s.set_xlabel('position (m)')
    s.set_ylabel('velocity (m/s)')
    plots = []
    #p1 = plot.plot(y[Nx/2,:], u[Nx/2,:], label="y-velocity along vertical center", marker="x")
    #plots.extend(p1)
    #p3 = plot.plot(y[Nx*0.1,:], v[Nx*0.1,:], label="y-velocity along left edge", marker="x")
    #plots.extend(p3)
    p1 = plot.plot(x[:,Nx/2], v[:,Nx/2], label="y-velocity along horizontal center", marker="x")
    plots.extend(p1)
    if hasattr(model.state,'temp'):
        ax2 = s.twinx()
        ax2.set_ylabel('Temperature (K)')
        p2 = plot.plot(y[Nx/2,:], Q.view(model.state).temp[Nx/2,n:-n], label="temp along vertical center", color="red")
        plots.extend(p2)

    if hasattr(test, 'discrete_solution'):
        discrete_data_v = getattr(test, 'discrete_solution')['v_vel']
        source = getattr(test, 'discrete_solution')['source']
        (x_, v_) = (discrete_data_v['x'], discrete_data_v['v'])
        p = plot.plot(x_, v_, label=source, marker='o', linestyle='')
        plots.extend(p)
    if hasattr(model.state,'rho'):
        ax2 = s.twinx()
        ax2.set_ylabel('Density (kg/m3)')
        p2 = plot.plot(y[Nx*0.45,:], Q.view(model.state).rho[n:-n,n:-n][Nx*0.45,:], marker="x", label="density along vertical center", color="red")
        plots.extend(p2)

    plot.legend(plots, [p.get_label() for p in plots], loc=0)
    plot.grid(True)
    plot.draw()

    print "v_max= %e, u_max= %e" % (np.max(v), np.max(u))

interactive_settings = run_handling.InteractiveSettings(pause=False, output_every_n_steps=1, plotting_routine=plotting_routine)

settings = pysolver.Settings(num_scheme, model, test, output_times, interactive_settings)

settingsHelper = run_handling.SettingsGenerationHelper(__file__, settings=settings)

settingsHelper.run()
#settingsHelper.enqueue()
