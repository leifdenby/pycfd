"""
Initial smoothed Gresho vortex

Based on document by Matthias Waidmann.
"""

import numpy as np

x0 = 0.0
y0 = 0.0
u_c = 0.0
v_c = 0.0
rho_c = 1.0
w_ref = 1.0

phi = 4*1024

R = 0.4

a = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, #  0-9
     0.0, 0.0, 1./12., -12./13., 9./2., -184./15., 609./32., -222./17., -38./9., 54./19.,  # 10-19
     783./20., -558./7., 1053./22., 1014./23., -1473./16., 204./5., 510./13., -1564./27., 153./8., 450./29.,  # 20-29
     -269./15., 174./31., 57./32., -74./33., 15./17., -6./35., 1./72.  # 30-36
     ]

def x_c(t):
    return x0+t*u_c

def y_c(t):
    return y0+t*v_c

def r_(x, y, t):
    return np.sqrt((x-x_c(t))**2.0 + (y-y_c(t))**2.0)/R

def rho(x, y, t):
    r = r_(x, y, t)
    return rho_c*(1.0 + (r < 1.0)*(1-r**2.0)**6.0)

def theta_(x, y, t):
    return np.arctan((y-y_c(t))/(x-x_c(t)))

def x_velocity(x, y, t):
    theta = theta_(x, y, t)
    delta = (x-x_c(t))/np.abs(x-x_c(t))
    r = r_(x, y, t)
    return u_c - (r<1.0)*phi*w_ref*delta*np.sin(theta)*(1-r)**6.0*r**6.0

def y_velocity(x, y, t):
    theta = theta_(x, y, t)
    delta = (x-x_c(t))/np.abs(x-x_c(t))
    r = r_(x, y, t)
    return v_c + (r<1.0)*phi*w_ref*delta*np.cos(theta)*(1-r)**6.0*r**6.0

def p_scaled(r):
    s = sum([a[k]*r**k for k in range(12,37)])
    return (r<=1.0)*phi**2.0*rho_c*2.0*s

def p(x, y, t):
    r = r_(x, y, t)
    return (r<1.0)*w_ref**2.0*(p_scaled(r) - p_scaled(1.0))
