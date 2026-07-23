"""Tests for energy calibration.

We fabricate reference points that lie *exactly* on a known polynomial, so the
recovered coefficients and the residuals have unambiguous expected values.  The
error paths (length mismatch, too few points) are checked as well.
"""

import numpy as np
import pytest

from gammalib.calibration import (
    apply_calibration,
    calibration_residuals,
    fit_calibration,
)


def test_linear_fit_recovers_known_coefficients():
    """Points on energy = 3 + 0.5*channel must yield those two coefficients."""
    channels = np.array([100.0, 500.0, 900.0])
    energies = 3.0 + 0.5 * channels
    model = fit_calibration(channels, energies, degree=1)
    assert model.coefficients == pytest.approx([3.0, 0.5])


def test_apply_calibration_matches_the_generating_line():
    """Applying the fitted model must reproduce the energies it was fit to."""
    channels = np.array([100.0, 500.0, 900.0])
    energies = 3.0 + 0.5 * channels
    model = fit_calibration(channels, energies, degree=1)
    assert apply_calibration(model, channels) == pytest.approx(energies)


def test_residuals_are_zero_for_exact_data():
    """Perfect reference data must leave (near) zero residuals."""
    channels = np.array([100.0, 500.0, 900.0])
    energies = 3.0 + 0.5 * channels
    model = fit_calibration(channels, energies, degree=1)
    residuals = calibration_residuals(model, channels, energies)
    assert residuals == pytest.approx(np.zeros(3), abs=1e-9)


def test_quadratic_fit_recovers_curvature():
    """A genuinely quadratic dataset must be recovered by a degree-2 fit."""
    channels = np.array([0.0, 250.0, 500.0, 750.0, 1000.0])
    energies = 1.0 + 0.4 * channels + 1e-4 * channels ** 2
    model = fit_calibration(channels, energies, degree=2)
    assert model.coefficients == pytest.approx([1.0, 0.4, 1e-4])


def test_mismatched_input_lengths_are_rejected():
    """Channels and energies must correspond one-to-one."""
    with pytest.raises(ValueError):
        fit_calibration(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0]))


def test_too_few_points_for_degree_is_rejected():
    """A straight line needs at least two points; one must raise."""
    with pytest.raises(ValueError):
        fit_calibration(np.array([100.0]), np.array([50.0]), degree=1)
