"""
Initial smoothed Gresho vortex

Based on document by Matthias Waidmann.
"""

import numpy as np

x0 = 0.0
y0 = 0.0
u_c = 1.0
v_c = 1.0
rho_c = 0.0
w_ref = 0.0

phi = 4*1024

R = 0.4

def x_c(t):
    return x0+t*u_c

def y_c(t):
    return y0+t*v_c

def r(x, y, t):
    return np.sqrt((x-x_c(t))**2.0 + (y-y_c(t))**2.0)/R

def rho(x, y, t):
    r_ = r(x, y, t)
    return rho_c*(1.0 + (r_ < 1.0)*(1-r_**2.0)**6.0)

def theta(x, y, t):
    return np.atan((y-y_c(t))/(x-x_c(t)))

def x_velocity(x, y, t):
    theta_ = theta(x, y, t)
    delta = (x-x_c(t))/np.abs(x-x_c(t))
    r_ = r(x, y, t)
    return u_c*(1.0 - (r_ < 1.0)*phi*w_ref*delta*np.sin(theta_)*(1-r_)**6.0*r_**6.0)

def y_velocity(x, y, t):
    theta_ = theta(x, y, t)
    delta = (x-x_c(t))/np.abs(x-x_c(t))
    r_ = r(x, y, t)
    return u_c*(1.0 + (r_ < 1.0)*phi*w_ref*delta*np.cos(theta_)*(1-r_)**6.0*r_**6.0)
