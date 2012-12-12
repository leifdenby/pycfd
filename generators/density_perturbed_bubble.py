
import pysolver.run_settings
import run_handling

import pysolver.models.soundproof.variable_density_ns
import pysolver.grids.grid2d
import pysolver.numMethods.soundproof.bcg
import pysolver.tests.VariableDensityIncompressibleNS2D as tests

import reference.atmospheric_flow.stratification_profiles

N = (100, 100)
x = (0.0, 1000.0)
y = (0.0, 1000.0)

surface_density = 1.205
surface_pressure = 101325.0
dTdz = 0.0
d_rho = -0.1
viscosity = 0.0

ambient_state = reference.atmospheric_flow.stratification_profiles.getStandardIsothermalAtmosphere()
domain_spec = pysolver.grids.grid2d.DomainSpec(N=N, x=x, y=y)

model = pysolver.models.soundproof.variable_density_ns.VariableDensityIncompressibleNS2D(viscosity=viscosity, diffusion_coefficient=0.0)
test = tests.SmoothBuoyantBubble(domain_spec, model, ambient_state, d_rho = d_rho, center=(500.0, 300.0), radius=100.0)

output_times = [60.0]
interactive_settings = None

num_scheme = pysolver.numMethods.soundproof.bcg.BCG(model=model, boundary_conditions=test.boundary_conditions, domain_spec=domain_spec)

settings = pysolver.Settings(num_scheme, model, test, output_times, interactive_settings)

settingsHelper = run_handling.SettingsGenerationHelper(__file__, settings=settings)

settingsHelper.run()
#settingsHelper.enqueue()
