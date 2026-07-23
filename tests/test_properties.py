"""Property-based tests with Hypothesis.

These complement -- they do not replace -- the concrete unit tests: once the
behaviour is pinned down by examples, Hypothesis searches for inputs that break
general properties we expect to hold for *any* valid values.
"""

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from gammalib.analysis import fwhm_from_sigma
from gammalib.calibration import apply_calibration, fit_calibration

# Finite, sensibly bounded reals avoid exercising floating-point overflow, which
# is not what these properties are about.
_reals = st.floats(min_value=-1e3, max_value=1e3, allow_nan=False, allow_infinity=False)
_positive = st.floats(min_value=1e-3, max_value=1e3, allow_nan=False,
                      allow_infinity=False)


@given(sigma_a=_positive, sigma_b=_positive)
def test_fwhm_is_monotonic_in_sigma(sigma_a, sigma_b):
    """A wider Gaussian must never have a smaller FWHM."""
    if sigma_a <= sigma_b:
        assert fwhm_from_sigma(sigma_a) <= fwhm_from_sigma(sigma_b)
    else:
        assert fwhm_from_sigma(sigma_a) >= fwhm_from_sigma(sigma_b)


@settings(max_examples=50)
@given(intercept=_reals, slope=_reals)
def test_linear_calibration_round_trips_for_any_line(intercept, slope):
    """For any straight line, fitting its points must reproduce that line."""
    channels = np.array([0.0, 250.0, 500.0, 750.0, 1000.0])
    energies = intercept + slope * channels

    model = fit_calibration(channels, energies, degree=1)
    recovered = apply_calibration(model, channels)

    # An absolute tolerance scaled by the data range absorbs conditioning noise.
    tolerance = 1e-6 * (1.0 + abs(intercept) + abs(slope) * channels.max())
    assert np.allclose(recovered, energies, atol=tolerance)
