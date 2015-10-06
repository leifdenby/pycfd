import numpy as np
import scipy.spatial

def plot_3d_single_isosurface(x, y, z, data, isosurface_value):
    import mpl_toolkits.mplot3d as a3
    import matplotlib.pyplot as plot
    """
    Plot a single contour of a 3D dataset, uses scipy's convex hull to compute
    just a single isosurface, so if the topology has internal "holes" they
    won't be plotted.
    """
    idx_inside = data > isosurface_value

    x_inside = x[idx_inside]
    y_inside = y[idx_inside]
    z_inside = z[idx_inside]

    X_inside = np.array([x_inside.ravel(), y_inside.ravel(), z_inside.ravel()]).T

    phi_inside = scipy.spatial.ConvexHull(X_inside)

    fig = plot.figure()
    ax = fig.gca(projection='3d')
    n_simplices, n_simplice_pts = phi_inside.simplices.shape


    for i in range(n_simplices):
        s = phi_inside.simplices[i]
        pts = phi_inside.points[s,:]
        collection = a3.art3d.Poly3DCollection([pts], alpha=0.7, linewidth=0.1)
        # have to set facecolor, otherwise alpha is not respected
        # http://stackoverflow.com/questions/18897786/transparency-for-poly3dcollection-plot-in-matplotlib
        face_color = [0.5, 0.5, 1]
        collection.set_facecolor(face_color)
        ax.add_collection3d(collection)

    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(y.min(), y.max())
    ax.set_zlim(z.min(), z.max())

    plot.draw()
    plot.show()


if __name__ == "__main__":
    x_ = np.linspace(-1., 1., 60)
    x, y, z = np.meshgrid(x_, x_, x_, indexing='ij')

    phi = np.sqrt(x**2. + y**2. + z**2.)

    plot_3d_single_isosurface(x, y, z, data=phi, isosurface_value=0.5)
