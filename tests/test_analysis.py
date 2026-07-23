"""Tests for the derived-quantity helpers (FWHM, area, resolution).

These are pure algebraic conversions, so each is checked against its exact
closed-form value, and each guard clause is checked for the input it is meant to
reject.
"""

import numpy as np
import pytest

from gammalib.analysis import energy_resolution, fwhm_from_sigma, gaussian_area


def test_fwhm_of_unit_sigma_is_the_known_constant():
    """FWHM = 2*sqrt(2 ln2)*sigma, which is 2.35482... for sigma = 1."""
    assert fwhm_from_sigma(1.0) == pytest.approx(2.3548200450309493)


def test_area_of_unit_gaussian_is_sqrt_two_pi():
    """A unit-amplitude, unit-sigma Gaussian integrates to sqrt(2*pi)."""
    assert gaussian_area(amplitude=1.0, sigma=1.0) == pytest.approx(np.sqrt(2 * np.pi))


def test_resolution_is_the_ratio_of_fwhm_to_energy():
    """Resolution of a 50 keV-wide peak at 500 keV must be exactly 0.1."""
    assert energy_resolution(fwhm_energy=50.0, centroid_energy=500.0) == \
        pytest.approx(0.1)


def test_negative_sigma_is_rejected_by_fwhm():
    """A negative width is unphysical and must raise."""
    with pytest.raises(ValueError):
        fwhm_from_sigma(-1.0)


def test_non_positive_energy_is_rejected_by_resolution():
    """Dividing by a zero/negative energy is meaningless and must raise."""
    with pytest.raises(ValueError):
        energy_resolution(fwhm_energy=10.0, centroid_energy=0.0)


def test_negative_sigma_is_rejected_by_area():
    """A negative width has no area and must raise rather than return nonsense."""
    with pytest.raises(ValueError):
        gaussian_area(amplitude=1.0, sigma=-2.0)
