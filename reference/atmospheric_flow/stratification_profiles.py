import numpy as np
import scipy.constants
import reference.atmospheric_flow.gas_properties

def getStandardIsothermalAtmosphere():
    gas_properties = reference.atmospheric_flow.gas_properties.AtmosphericAir()
    rho0 = 1.205
    p0 = 101325.0
    dTdz = 0.0  # isothermal
    g = scipy.constants.g
    return HydrostaticallyBalancedAtmosphere(rho0=rho0, p0=p0, dTdz=dTdz, gas_properties=gas_properties, g=g)


def getStandardIsentropicAtmosphere():
    gas_properties = reference.atmospheric_flow.gas_properties.AtmosphericAir()
    rho0 = 1.205
    p0 = 101325.0
    g = scipy.constants.g
    dTdz = -g/gas_properties.cp()
    return HydrostaticallyBalancedAtmosphere(rho0=rho0, p0=p0, dTdz=dTdz, gas_properties=gas_properties, g=g)


class HydrostaticallyBalancedAtmosphere:
    """
    Class for setting a hydrostatically balanced atmosphere with
    an ideal gas and constant lapse rate given as dT/dz.

    p = rho*R/M*T

    R: Unified gas constant
    """
    def __init__(self, rho0, p0, dTdz, gas_properties, g = None):
        self.rho0 = rho0
        self.p0 = p0
        self.dTdz = dTdz
        self.gas_properties = gas_properties
        self.T0 = p0*gas_properties.M/(rho0*scipy.constants.R*1000.0)
        self.theta0 = self.T0  # p=p0 at surface
        if g is None:
            self.g = scipy.constants.g
        else:
            self.g = g

    def __str__(self):
        return "HydrostaticallyBalancedAtmosphere (rho0=%f, p0=%f, dTdz=%f) with %s" % (self.rho0, self.p0, self.dTdz, str(self.gas_properties))

    def temp(self, pos):
        z = pos[-1]
        return self.T0 + self.dTdz*z

    def rho(self, pos):
        z = pos[-1]
        if self.dTdz == 0.0:
            return self.rho0*np.exp(-z*self.g*self.gas_properties.M/(scipy.constants.R*1000.0*self.T0))
        else:
            alpha = self.g*self.gas_properties.M/(self.dTdz*scipy.constants.R*1000.0)
            return self.rho0*np.power(self.T0, alpha+1.0 )*np.power(self.temp(pos), -alpha - 1.0)

    def drho_dz(self, pos):
        if self.dTdz == 0.0:
            return -self.g*self.gas_properties.M/(scipy.constants.R*1000.0*self.T0)*self.rho(pos)
        else:
            alpha = self.g*self.gas_properties.M/(self.dTdz*scipy.constants.R*1000.0)
            return (-alpha-1.0)*np.power(self.temp(pos), -alpha - 2.0)*self.dTdz

    def p(self, pos):
        return self.rho(pos)*scipy.constants.R*1000.0/self.gas_properties.M*self.temp(pos)

    def theta(self, pos):
        """
        Calculate the potential temperature at pos.
        """
        return self.temp(pos)*np.power(self.p(pos)/self.p0, -self.gas_properties.kappa())

    def x_vel(self, pos):
        return 0.0

    def y_vel(self, pos):
        return 0.0

    def lapseRate(self):
        """
        Calculate lapse rate for using in the CNS-AMR compressible code
        """
        return self.dTdz*scipy.constants.R*1000.0/self.gas_properties.M
