"""
Lid-driven cavity problem with fixed density.
"""

import pysolver.run_settings
import run_handling

import pysolver.models.soundproof.constant_density_ns
import pysolver.grids.grid2d
import pysolver.numMethods.soundproof.bcg
import pysolver.tests
import pysolver.tests.lid_driven_cavity


N = (100, 100)
x = (0.0, 1.0)
y = (0.0, 1.0)

base_state = {'x_vel': 0.0, 'y_vel': 0.0}
viscosity = 1.0
u_top = 1.0

ambient_state = pysolver.tests.ConstantState(base_state)
domain_spec = pysolver.grids.grid2d.DomainSpec(N=N, x=x, y=y)

model = pysolver.models.soundproof.constant_density_ns.ConstantDensityIncompressibleNS2D(viscosity=viscosity)
test = pysolver.tests.lid_driven_cavity.Test2D(domain_spec=domain_spec, u_top=u_top, ambient_state=ambient_state, viscosity=viscosity)

output_times = [60.0]

num_scheme = pysolver.numMethods.soundproof.bcg.BCG(model=model, boundary_conditions=test.boundary_conditions, domain_spec=domain_spec)

def plotting_routine(Q, grid, model, test, t, n_steps, num_scheme, save_fig = False):
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



    f = plot.figure(1)
    f.clf()
    f.text(0.5, 0.92, "%d t=%es\n%s\n%s" % (n_steps, t, model, test), horizontalalignment='center')

    s = plot.subplot(121)
    #if hasattr(model.state,'temp'):
        #plot.imshow(np.rot90(Q.view(model.state).temp[n:-n,n:-n]), norm=temp_norm, extent=extent, interpolation="nearest")
        #plot.colorbar()
    if hasattr(model.state,'rho'):
        plot.imshow(np.rot90(Q.view(model.state).rho[n:-n,n:-n]), extent=extent, interpolation="nearest")
        plot.colorbar()
    plot.grid(True)
    k = Nx/20 if Nx/20 > 0 else 1
    plottingHelper.quiver(x[::k,::k], y[::k,::k], u[::k,::k], v[::k,::k])

    #c_levels = np.linspace(1.08, 1.18, 10)
    #plot.contour(x, y, Q.view(model.state).rho[n:-n,n:-n], c_levels, colors="black")

    s = plot.subplot(122)
    s.set_xlabel('position (m)')
    s.set_ylabel('velocity (m/s)')
    plots = []
    #p1 = plot.plot(y[Nx/2,:], v[Nx/2,:], label="y-velocity along vertical center", marker="x")
    #plots.extend(p1)
    #p3 = plot.plot(y[Nx*0.1,:], v[Nx*0.1,:], label="y-velocity along left edge", marker="x")
    #plots.extend(p3)
    p1 = plot.plot(y[Nx/2,:], u[Nx/2,:], label="x-velocity along vertical center", marker="x")
    plots.extend(p1)
    if hasattr(model.state,'temp'):
        ax2 = s.twinx()
        ax2.set_ylabel('Temperature (K)')
        p2 = plot.plot(y[Nx/2,:], Q.view(model.state).temp[Nx/2,n:-n], label="temp along vertical center", color="red")
        plots.extend(p2)

    if hasattr(test, 'discrete_solution'):
        discrete_data_v = getattr(test, 'discrete_solution')['u_vel']
        source = getattr(test, 'discrete_solution')['source']
        (y_, u_) = (discrete_data_v['y'], discrete_data_v['u'])
        p = plot.plot(y_, u_, label=source, marker='x')
        plots.extend(p)
    if hasattr(model.state,'rho'):
        ax2 = s.twinx()
        ax2.set_ylabel('Density (kg/m3)')
        p2 = plot.plot(y[Nx*0.45,:], Q.view(model.state).rho[n:-n,n:-n][Nx*0.45,:], marker="x", label="density along vertical center", color="red")
        plots.extend(p2)

    plot.legend(plots, [p.get_label() for p in plots], loc=0)
    plot.grid(True)
    plot.draw()

    if save_fig:
        output_folder = '/Users/leifdenby/Desktop/PhD/output/%s' % repr(model)
        import os
        try:
            os.makedirs(output_folder)
        except:
            pass

        frame_counter = 0
        filename = '%s/frame_%d.png' % (output_folder, frame_counter)
        while os.path.exists('%s/frame_%d.png' % (output_folder, frame_counter)):
            frame_counter += 1
            filename = '%s/frame_%d.png' % (output_folder, frame_counter)
        plot.savefig(filename)
        np.savetxt("%s-rho.dat" % filename, Q.view(model.state).rho[n:-n,n:-n])

    #print "v_max= %e, u_max= %e" % (np.max(v), np.max(u))

interactive_settings = run_handling.InteractiveSettings(pause=True, output_every_n_steps=5, plotting_routine=plotting_routine)

settings = pysolver.Settings(num_scheme, model, test, output_times, interactive_settings)

settingsHelper = run_handling.SettingsGenerationHelper(__file__, settings=settings)

settingsHelper.run()
#settingsHelper.enqueue()
