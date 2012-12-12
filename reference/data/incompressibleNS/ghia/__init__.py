import numpy as np
import os

def load(Re):
    """
    Load and return experimental data for a given Reynolds number Re.
    """
    
    Re_s = [100, 400, 1000, 320, 5000, 7500, 10000]

    if int(Re) in Re_s:
        datadir = os.path.dirname(os.path.abspath(__file__))
        
        dtype = [('grid_point','i'), ('y','f')]
        for Re in Re_s:
            dtype.append(('Re_%i' % Re, 'f'))
        raw_data_u = np.loadtxt(os.path.join(datadir, 'u_vel.dat'), dtype=dtype)
        
        dtype = [('grid_point','i'), ('x','f')]
        for Re in Re_s:
            dtype.append(('Re_%i' % Re, 'f'))
        raw_data_v = np.loadtxt(os.path.join(datadir, 'v_vel.dat'), dtype=dtype)

        data = {
                'u_vel' : { 'y' : raw_data_u['y'], 'u' : raw_data_u['Re_%i' % Re]},
                'v_vel' : { 'x' : raw_data_v['x'], 'v' : raw_data_v['Re_%i' % Re]},
                'source' : 'Ghia et al. 1982',
                }

        return data
    else:
        return None


