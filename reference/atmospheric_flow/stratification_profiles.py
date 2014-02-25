import numpy as np
import scipy.constants
from pycfd.reference.atmospheric_flow import gas_properties as ref_gas_properties

def getStandardIsothermalAtmosphere():
    gas_properties = ref_gas_properties.AtmosphericAir()
    rho0 = 1.205
    p0 = 101325.0
    dTdz = 0.0  # isothermal
    g = scipy.constants.g
    return HydrostaticallyBalancedAtmosphere(rho0=rho0, p0=p0, dTdz=dTdz, gas_properties=gas_properties, g=g)

def getStandardIsentropicAtmosphere():
    gas_properties = ref_gas_properties.AtmosphericAir()
    rho0 = 1.205
    p0 = 101325.0
    g = scipy.constants.g
    dTdz = -g/gas_properties.cp()
    return HydrostaticallyBalancedAtmosphere(rho0=rho0, p0=p0, dTdz=dTdz, gas_properties=gas_properties, g=g)

def getConstantDensityAtmosphere():
    gas_properties = ref_gas_properties.AtmosphericAir()
    rho0 = 1.205
    p0 = 101325.0
    g = scipy.constants.g
    dTdz = -g/gas_properties.R()
    return HydrostaticallyBalancedAtmosphere(rho0=rho0, p0=p0, dTdz=dTdz, gas_properties=gas_properties, g=g)

def getKleinIsentropicAtmosphere():
    gas_properties = ref_gas_properties.AtmosphericAir()
    rho0 = 1.0
    g = 10.0
    T0 = 300.0
    p0 = rho0*gas_properties.R()*T0
    dTdz = -g/gas_properties.cp()
    return HydrostaticallyBalancedAtmosphere(rho0=rho0, p0=p0, dTdz=dTdz, gas_properties=gas_properties, g=g)

def getIsentropicAtmosphere(theta0=300.0, g=9.81, p0=1.0e6):
    """
    Generate an isentropic atmopsheric profile.
    """
    gas_properties = ref_gas_properties.AtmosphericAir()
    T0 = theta0
    rho0 = p0/T0*1.0/gas_properties.R()
    dTdz = -g/gas_properties.cp()
    return HydrostaticallyBalancedAtmosphere(rho0=rho0, p0=p0, dTdz=dTdz, gas_properties=gas_properties, g=g)


class HydrostaticallyBalancedAtmosphere(object):
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
        self.pot_temperature0 = self.T0  # p=p0 at surface
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

    def pot_temperature(self, pos):
        """
        Calculate the potential temperature at pos.
        """
        return self.temp(pos)*np.power(self.p(pos)/self.p0, -self.gas_properties.kappa())

    def x_velocity(self, pos):
        return 0.0

    def y_velocity(self, pos):
        return 0.0

    def lapseRate(self):
        """
        Calculate lapse rate for using in the CNS-AMR compressible code
        """
        return self.dTdz*scipy.constants.R*1000.0/self.gas_properties.M

class HydrostaticallyBalancedMoistAtmosphere(HydrostaticallyBalancedAtmosphere):
    def __init__(self, rho0, p0, dTdz, RH0, dRHdz, gas_properties, g=None):
        super(HydrostaticallyBalancedMoistAtmosphere, self).__init__(rho0=rho0, p0=p0, dTdz=dTdz, gas_properties=gas_properties, g=g)

        self.dRHdz = dRHdz
        self.RH0 = RH0

    def rel_humidity(self, pos):
        z = pos[-1]
        return self.RH0 + self.dRHdz*z

a = 6.112
b = 12.62
c = 243.5
gamma = lambda T, RH : np.log(RH) + b*T/(c+T)
P_a = lambda T, RH: a*np.exp(gamma(T, RH))
T_dp = lambda T, RH: c*np.log(P_a(T, RH)/a)/(b-np.log(P_a(T, RH)/a))


class NearIsentropic(HydrostaticallyBalancedAtmosphere):
    """
    This profile is forced a little more stable that isentropic (neutral)
    stability, since ATHAM can't run with a profile that is rigth on neutral.
    """
    def __init__(self, dTdz_offset=1.0e-3):
        gas_properties = ref_gas_properties.AtmosphericAir()
        rho0 = 1.205
        p0 = 101325.0
        g = scipy.constants.g
        dTdz = -g/gas_properties.cp() + dTdz_offset
        super(NearIsentropic, self).__init__(rho0=rho0, p0=p0, dTdz=dTdz, gas_properties=gas_properties, g=g)

    def __str__(self):
        return "Near-isentropic (dry)"

class LayeredMoistAtmosphere(object):
    def __init__(self, layers, RH0, RH_min=None):
        self.layers = layers
        self.RH_min = RH_min
        self.RH0 = RH0
        self.gas_properties = ref_gas_properties.AtmosphericAir()

        # create an instance of HydrostHydrostaticallyBalancedAtmosphere for
        # each layer
        self.layer_instances = {}

        # ground state
        z_min = 0.0
        rho0 = 1.205
        p0 = 101325.0
        RH0 = self.RH0
        for layer in self.layers:
            z_max = layer['z_max']
            z = (z_min, z_max)
            layer_instance = HydrostaticallyBalancedMoistAtmosphere(rho0=rho0,
                                                                    p0=p0,
                                                                    dTdz=layer['dTdz'],
                                                                    dRHdz=layer['dRHdz'],
                                                                    RH0=RH0,
                                                                    gas_properties=self.gas_properties,
                                                                    )
            self.layer_instances[z] = layer_instance

            # calculate the start values of the next layer, remember that this
            # layer is offset.
            z_offset = z_max - z_min
            z_min = z_max
            rho0 = layer_instance.rho([z_offset])
            p0 = layer_instance.p([z_offset])
            RH0 = layer_instance.rel_humidity([z_offset])

    def temp(self, pos):
        return self._get_values_from_layer('temp', pos)

    def _get_values_from_layer(self, variable, pos):

        z = pos[-1]
        try:
            values = np.zeros(z.shape)

            for (z_min, z_max), layer in self.layer_instances.items():
                idx_in_layer = np.logical_and(z_min <= z, z < z_max)
                f = getattr(layer, variable)
                values[idx_in_layer] = f([z[idx_in_layer] - z_min])

            return values
        except AttributeError:
            for (z_min, z_max), layer in self.layer_instances.items():
                if z_min <= z and z <= z_max:
                    f = getattr(layer, variable)
                    return f([z - z_min])


    def rel_humidity(self, pos):
        rel_humidity = self._get_values_from_layer('rel_humidity', pos)
        try:
            rel_humidity[rel_humidity < self.RH_min] = self.RH_min
            return rel_humidity
        except TypeError:
            if rel_humidity < self.RH_min:
                return self.RH_min
            else:
                return rel_humidity

    def dew_point(self, pos):
        temp = self.temp(pos)
        rel_humidity = self.rel_humidity(pos)

        return T_dp(temp-273.15, rel_humidity) + 273.15


class Soong1972(LayeredMoistAtmosphere):
    def __init__(self):
        layers = []
        dTdz_dry = -10.0e-3  # K/m
        dTdz_moist = -6.0e-3  # K/m

        layer_thickness_0 = 800.0 # m
        RH0 = 0.70
        RH_LCL = 0.90

        dRHdz_0 = (RH_LCL - RH0)/layer_thickness_0  # %/m
        dRHdz_1 = -0.075e-3 # %/m

        layers.append({'z_max': 800.0, 'dTdz': dTdz_dry, 'dRHdz': dRHdz_0})
        layers.append({'z_max': 12800., 'dTdz': dTdz_moist, 'dRHdz': dRHdz_1})
        layers.append({'z_max': np.finfo('f').max, 'dTdz': 0.0, 'dRHdz': 0.0})

        super(Soong1972, self).__init__(layers=layers, RH0=RH0, RH_min=0.3)

    def __str__(self):
        return "Soong 1972 layered moist atmosphere"

if __name__ == "__main__":
    from matplotlib import pyplot as plot

    atmosphere = Soong1972()

    plot.ion()
    z = np.linspace(0.0, 20000.0, 100)
    temp = atmosphere.temp([z])

    plot.subplot(121)
    plot.plot(atmosphere.temp([z]), z)
    #plot.plot(atmosphere.dew_point([z]), z)
    plot.xlabel("Temperature [K]")
    plot.ylabel("Height [m]")
    plot.grid(True)

    plot.subplot(122)
    plot.plot(atmosphere.rel_humidity([z]), z)
    plot.xlabel("Relative humidity [%]")
    plot.ylabel("Height [m]")
    plot.xlim(0.0, 1.0)
    plot.grid(True)

    plot.suptitle("Atmospheric stratification profile from Soong 1972")

    plot.draw()
    raw_input()
