# coding: utf-8
import numpy as np
from scipy.constants import pi

def x_velocity(pos, t):
    x, y = pos
    return np.cos(2*pi*x)*np.sin(2*pi*y)

def y_velocity(pos, t):
    x, y = pos
    return np.sin(-2*pi*x)*np.cos(2*pi*y)

def dudx(pos, t):
    x, y = pos
    return -2*pi*np.sin(2*pi*x)*np.sin(2*pi*y)

def dvdy(pos, t):
    x, y = pos
    return -2*pi*np.sin(-2*pi*x)*np.sin(2*pi*y)

def rho(pos, t):
    x, y = pos
    r = np.sqrt(x*x+y*y)
    return 1.0 + (r < 0.5)*np.cos(2*pi*(r-0.25))**2.0

