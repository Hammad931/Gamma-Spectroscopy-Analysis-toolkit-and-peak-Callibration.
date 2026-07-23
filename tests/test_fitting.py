"""Tests for the Gaussian model and the peak fitter.

The model functions are checked against their closed-form values.  The fitter is
driven with noiseless data built from known parameters, so we can assert that it
recovers those parameters to tight tolerances -- with room left for the residual
error introduced by the linear-background approximation.
"""

import numpy as np
import pytest

from gammalib.fitting import fit_peak, gaussian, gaussian_plus_linear
from gammalib.synthetic import SyntheticPeak, make_spectrum


def test_gaussian_equals_amplitude_at_its_center():
    """At x = center the exponential is 1, so the value must be the amplitude."""
    assert gaussian(np.array([5.0]), amplitude=3.0, center=5.0, sigma=2.0)[0] == \
        pytest.approx(3.0)


def test_gaussian_is_symmetric_about_the_center():
    """Points equidistant from the centre must have equal value."""
    left = gaussian(np.array([3.0]), amplitude=1.0, center=5.0, sigma=2.0)[0]
    right = gaussian(np.array([7.0]), amplitude=1.0, center=5.0, sigma=2.0)[0]
    assert left == pytest.approx(right)


def test_linear_term_adds_a_constant_offset():
    """With a flat (slope 0) background the model equals Gaussian + intercept."""
    x = np.array([5.0])
    bare = gaussian(x, 1.0, 5.0, 2.0)[0]
    with_bg = gaussian_plus_linear(x, 1.0, 5.0, 2.0, slope=0.0, intercept=4.0)[0]
    assert with_bg - bare == pytest.approx(4.0)


def test_fit_recovers_known_center():
    """On noiseless data the fitted centroid must match the injected one."""
    peak = SyntheticPeak(center=512.3, area=80000.0, sigma=7.0)
    spectrum = make_spectrum([peak], n_channels=1024, add_noise=False)
    fit = fit_peak(spectrum, approx_center=512, window_half_width=30)
    assert fit.center == pytest.approx(512.3, abs=0.05)


def test_fit_recovers_known_width():
    """The fitted sigma must match the injected width on noiseless data."""
    peak = SyntheticPeak(center=512.0, area=80000.0, sigma=7.0)
    spectrum = make_spectrum([peak], n_channels=1024, add_noise=False)
    fit = fit_peak(spectrum, approx_center=512, window_half_width=30)
    assert fit.sigma == pytest.approx(7.0, rel=0.02)


def test_fit_reports_the_window_it_used():
    """The recorded window must match the requested half-width around the centre."""
    peak = SyntheticPeak(center=512.0, area=80000.0, sigma=7.0)
    spectrum = make_spectrum([peak], n_channels=1024, add_noise=False)
    fit = fit_peak(spectrum, approx_center=512, window_half_width=30)
    assert fit.window == (482, 542)


def test_fit_rejects_a_degenerate_window():
    """Too narrow a window cannot constrain five parameters and must raise."""
    peak = SyntheticPeak(center=512.0, area=80000.0, sigma=7.0)
    spectrum = make_spectrum([peak], n_channels=1024, add_noise=False)
    with pytest.raises(ValueError):
        fit_peak(spectrum, approx_center=512, window_half_width=1)
