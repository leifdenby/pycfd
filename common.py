import numpy as np
import os

basedir = os.path.dirname(os.path.abspath(__file__))

def print_grid(u, num_format="%.3e"):
    (i_max, j_max) = u.shape
    print u.shape
    for i in range(i_max):
        for j in range(j_max):
            if "e" in num_format and u[i,j] == 0.0:  # introduced because -0.0 is a number, and it would print wrong
                print "  0.0    ",
            else:
                if "e" in num_format and u[i,j] > 0.0:
                    print " ",
                else:
                    print "",
                print num_format % u[i,j],
        print


class Domain2D:
    def __init__(self, limits, Ns):
        ((self.xmin, self.xmax), (self.ymin, self.ymax)) = limits
        self.Nx, self.Ny = Ns

    def meshgrid(self):
        return np.meshgrid(np.linspace(self.xmin, self.xmax, self.Nx), np.linspace(self.ymin, self.ymax, self.Ny))

    def dx(self):
        return ( (self.xmax-self.xmin)/self.Nx, (self.ymax-self.ymin)/self.Ny)


def meshgrid(x, y):
    xx, yy = np.meshgrid(x, y)
    return np.array([xx.T, yy.T])

# http://www.mail-archive.com/numpy-discussion@scipy.org/msg36672.html
# create a slice along a specific axis, using aslice(axis, start, end)
aslice = lambda axis, s, e: (slice(None),) * axis + (slice(s, e),)

aindex = lambda axis, s: (slice(None),) * axis + (s,)

cvmgt = lambda bools, if_true, if_false: (if_true.T*bools.T + np.logical_not(bools).T*if_false.T).T

def cond_eval(cond, f_true, f_false):
    results = np.empty(cond.shape)
    condinv = np.invert(cond)
    def f_(*args):
        results[cond] = f_true(*[arg[cond] for arg in args])
        results[condinv] = f_false(*[arg[condinv] for arg in args])
        return results

    return f_

def cond_map(q, cond, f):
    def f_(**args):
        #q[cond] = f(*[arg[cond] for arg in args])
        q[cond] = f(**{k:v[cond] for k,v in args.items()})
        return q

    return f_
