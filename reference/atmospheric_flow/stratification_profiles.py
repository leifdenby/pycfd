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
        p = np.array(pos)
        if len(p.shape) > 1:
            z = p[-1]
        else:
            z = p
        return self.T0 + self.dTdz*z

    def rho(self, pos):
        p = np.array(pos)
        if len(p.shape) > 1:
            z = p[-1]
        else:
            z = p

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

class PseudoHydrostaticallyBalancedMoistAtmosphere(HydrostaticallyBalancedAtmosphere):
    """
    Given an atmosphere with non-zero specific concentration of water vapour
    and a fixed lapse rate it is not strictly guaranteed that the atmosphere
    will be stable, and so the hydrostatic assumption is not strictly valid.
    """
    def __init__(self, rho0, p0, dTdz, RH0, dRHdz, gas_properties, g=None):
        super(PseudoHydrostaticallyBalancedMoistAtmosphere, self).__init__(rho0=rho0, p0=p0, dTdz=dTdz, gas_properties=gas_properties, g=g)

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


class LayeredAtmosphere(object):
    def _get_values_from_layer(self, variable, pos):

        if type(pos) in [float, np.float, np.float64 ]:
            z = pos

            for (z_min, z_max), layer in self.layer_instances.items():
                if z_min <= z and z <= z_max:
                    f = getattr(layer, variable)
                    return f([z - z_min])

        else:
            pos = np.array(pos)
            if len(pos.shape) > 1:
                z = pos[-1]
            else:
                z = pos

            values = np.zeros(z.shape)

            for (z_min, z_max), layer in self.layer_instances.items():
                idx_in_layer = np.logical_and(z_min <= z, z < z_max)
                f = getattr(layer, variable)
                values[idx_in_layer] = f([z[idx_in_layer] - z_min])

            return values

class LayeredDryAtmosphere(LayeredAtmosphere):
    def __init__(self, layers, rho0=None, p0=None):
        self.layers = layers
        self.gas_properties = ref_gas_properties.AtmosphericAir()

        # create an instance of HydroststaticallyBalancedAtmosphere for
        # each layer
        self.layer_instances = {}

        # ground state
        z_min = 0.0
        if rho0 is None:
            rho0 = 1.205
        if p0 is None:
            p0 = 101325.0
        for layer in self.layers:
            z_max = layer['z_max']
            z = (z_min, z_max)
            layer_instance = HydrostaticallyBalancedAtmosphere(rho0=rho0,
                                                               p0=p0,
                                                               dTdz=layer['dTdz'],
                                                               gas_properties=self.gas_properties,
                                                               )
            self.layer_instances[z] = layer_instance

            # calculate the start values of the next layer, remember that this
            # layer is offset.
            z_offset = z_max - z_min
            z_min = z_max
            rho0 = layer_instance.rho([z_offset])
            p0 = layer_instance.p([z_offset])

    def temp(self, pos):
        return self._get_values_from_layer('temp', pos)

    def p(self, pos):
        return self._get_values_from_layer('p', pos)

    def rho(self, pos):
        return self._get_values_from_layer('rho', pos)

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
    def __init__(self, layers, RH0, RH_min=None, rho0=None, p0=None):
        self.layers = layers
        self.RH_min = RH_min
        self.RH0 = RH0
        self.gas_properties = ref_gas_properties.AtmosphericAir()

        # create an instance of HydrostHydrostaticallyBalancedAtmosphere for
        # each layer
        self.layer_instances = {}

        # ground state
        z_min = 0.0
        if rho0 is None:
            rho0 = 1.205
        if p0 is None:
            p0 = 101325.0
        RH0 = self.RH0
        for layer in self.layers:
            z_max = layer['z_max']
            z = (z_min, z_max)
            layer_instance = PseudoHydrostaticallyBalancedMoistAtmosphere(rho0=rho0,
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

    def p(self, pos):
        return self._get_values_from_layer('p', pos)

    def rho(self, pos):
        return self._get_values_from_layer('rho', pos)

    def _get_values_from_layer(self, variable, pos):

        if len(np.array(pos).shape) > 1:
            z = pos[-1]
        else:
            z = pos

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

class Soong1973(LayeredMoistAtmosphere):
    def __init__(self, cloud_base_height=None):
        self.cloud_base_height = cloud_base_height

        layers = []
        dTdz_dry = -10.0e-3  # K/m
        dTdz_moist = -6.0e-3  # K/m

        RH0 = 0.70

        if self.cloud_base_height is not None:
            layer_thickness_0 = self.cloud_base_height # m
            # TODO: This is completely arbitrary, the RH needs lowering that's
            # for sure, not sure how much at this point
            if cloud_base_height == 1600.:
                RH0 = 0.50
            elif cloud_base_height == 1100.:
                RH0 = 0.59
            else:
                raise NotImplementedError
        else:
            layer_thickness_0 = 800.0 # m

        RH_LCL = 0.90

        dRHdz_0 = (RH_LCL - RH0)/layer_thickness_0  # %/m
        dRHdz_1 = -0.075e-3 # %/m

        layers.append({'z_max': layer_thickness_0, 'dTdz': dTdz_dry, 'dRHdz': dRHdz_0})
        layers.append({'z_max': 12800., 'dTdz': dTdz_moist, 'dRHdz': dRHdz_1})
        layers.append({'z_max': np.finfo('f').max, 'dTdz': 0.0, 'dRHdz': 0.0})

        T0 = 25.0 + 273.15 #  [K], from Soong 1973 paper
        p0 = 101325.0 #  [Pa], default value used, Soong 1973 doesn't give a value

        gas_properties = ref_gas_properties.AtmosphericAir()
        rho0 = p0/T0*1.0/gas_properties.R()

        super(Soong1973, self).__init__(layers=layers, RH0=RH0, RH_min=0.3, rho0=rho0, p0=p0)

    def __str__(self):
        if self.cloud_base_height is None:
            return "Soong 1973 layered moist atmosphere"
        else:
            return "Soong 1973 layered moist atmosphere (with modified cloud base at %s)" % self.cloud_base_height

class Soong1973Dry(LayeredDryAtmosphere):
    def __init__(self):
        layers = []
        dTdz_dry = -10.0e-3  # K/m
        dTdz_moist = -6.0e-3  # K/m

        self.g = 10.0

        layer_thickness_0 = 800.0 # m

        layers.append({'z_max': 800.0, 'dTdz': dTdz_dry, })
        layers.append({'z_max': 12800., 'dTdz': dTdz_moist, })
        layers.append({'z_max': np.finfo('f').max, 'dTdz': 0.0, })

        super(Soong1973Dry, self).__init__(layers=layers, )

    def __str__(self):
        return "Soong 1973 layered dry atmosphere"

class SimpleMoistStable(LayeredMoistAtmosphere):
    def __init__(self, cloud_base_height=None, dRHdz=None, RH_LCL=None):
        self.cloud_base_height = cloud_base_height

        layers = []
        dTdz_dry = -8.0e-3  # K/m
        dTdz_moist = -6.0e-3  # K/m

        if self.cloud_base_height is not None:
            layer_thickness_0 = self.cloud_base_height # m
        else:
            layer_thickness_0 = 800.0 # m

        if dRHdz is None:
            dRHdz = -0.2e-3 # %/m

        self.dRHdz = dRHdz

        RH0 = 0.70
        if RH_LCL is None:
            RH_LCL = 0.90

        dRHdz_0 = (RH_LCL - RH0)/layer_thickness_0  # %/m
        dRHdz_1 = self.dRHdz # %/m

        layers.append({'z_max': layer_thickness_0, 'dTdz': dTdz_dry, 'dRHdz': dRHdz_0})
        layers.append({'z_max': 12800., 'dTdz': dTdz_moist, 'dRHdz': dRHdz_1})
        layers.append({'z_max': np.finfo('f').max, 'dTdz': 0.0, 'dRHdz': 0.0})

        super(SimpleMoistStable, self).__init__(layers=layers, RH0=RH0, RH_min=0.2)

    def __str__(self):
        return "Simple stable moist atmosphere based on Soong1973 (dRHdz=%g%%/km)" % (self.dRHdz*1.e3)

if __name__ == "__main__":
    from matplotlib import pyplot as plot

    atmosphere = Soong1973()
    atmosphere = Soong1973()

    plot.ion()
    z = np.linspace(0.0, 20000.0, 100)
    temp = atmosphere.temp([z])

    plot.subplot(131)
    plot.plot(atmosphere.temp([z]), z)
    #plot.plot(atmosphere.dew_point([z]), z)
    plot.xlabel("Temperature [K]")
    plot.ylabel("Height [m]")
    plot.grid(True)

    plot.subplot(132)
    plot.plot(atmosphere.rel_humidity([z]), z)
    plot.xlabel("Relative humidity [%]")
    plot.ylabel("Height [m]")
    plot.xlim(0.0, 1.0)
    plot.grid(True)

    plot.subplot(133)
    plot.plot(atmosphere.p([z]), z)
    plot.xlabel("Pressure [Pa]")
    plot.ylabel("Height [m]")
    plot.xlim(0.0, None)
    plot.grid(True)

    plot.suptitle("Atmospheric stratification profile from Soong 1973")

    plot.draw()
    raw_input()
