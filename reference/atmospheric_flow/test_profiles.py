import numpy as np

import stratification_profiles

def test_RICO():
    profile = stratification_profiles.RICO()

    assert profile.temp(0.0) == 299.2
    assert profile.q_t(0.0) == 0.016
    assert profile.temp(0.0) > profile.temp(1000.)
