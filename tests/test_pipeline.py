"""Integration tests for the end-to-end pipeline.

Unlike the unit tests, these exercise the whole chain (detect -> fit ->
calibrate -> resolution) on one synthetic spectrum, checking that the pieces
fit together and that the guard against a peak/reference count mismatch fires.
"""

from pathlib import Path

import pytest

from gammalib.config import Config
from gammalib.pipeline import analyse_spectrum
from gammalib.synthetic import SyntheticPeak, make_spectrum

# Three peaks placed on a known linear energy scale (energy = 5 + 0.6*channel).
_TRUE_INTERCEPT = 5.0
_TRUE_SLOPE = 0.6
_PEAKS = [
    SyntheticPeak(center=400.0, area=90000.0, sigma=7.0),
    SyntheticPeak(center=1000.0, area=70000.0, sigma=8.0),
    SyntheticPeak(center=1600.0, area=60000.0, sigma=9.0),
]
_REFERENCE_ENERGIES = [_TRUE_INTERCEPT + _TRUE_SLOPE * p.center for p in _PEAKS]


def _config(reference_energies):
    """Build a Config in memory (the spectrum is passed directly, not read)."""
    return Config(
        spectrum_file=Path("unused.dat"),
        min_prominence=200.0,
        min_distance=20,
        window_half_width=30,
        reference_energies=reference_energies,
        calibration_degree=1,
    )


def test_pipeline_detects_every_peak():
    """The three injected peaks must all come through to the result."""
    spectrum = make_spectrum(_PEAKS, n_channels=2048, seed=7)
    result = analyse_spectrum(spectrum, _config(_REFERENCE_ENERGIES))
    assert len(result.peak_fits) == 3


def test_pipeline_recovers_the_true_energy_scale():
    """The calibrated peak energies must match the injected reference lines."""
    spectrum = make_spectrum(_PEAKS, n_channels=2048, seed=7)
    result = analyse_spectrum(spectrum, _config(_REFERENCE_ENERGIES))
    # 1 keV tolerance comfortably covers the Poisson noise in the centroids.
    assert result.peak_energies == pytest.approx(sorted(_REFERENCE_ENERGIES), abs=1.0)


def test_pipeline_reports_positive_resolutions():
    """Every calibrated peak must have a physical (positive) resolution."""
    spectrum = make_spectrum(_PEAKS, n_channels=2048, seed=7)
    result = analyse_spectrum(spectrum, _config(_REFERENCE_ENERGIES))
    assert all(r > 0 for r in result.resolutions)


def test_mismatched_reference_count_raises():
    """Fewer reference energies than detected peaks must be an error."""
    spectrum = make_spectrum(_PEAKS, n_channels=2048, seed=7)
    with pytest.raises(ValueError):
        analyse_spectrum(spectrum, _config(_REFERENCE_ENERGIES[:2]))


def test_pipeline_runs_without_calibration():
    """With no reference energies the pipeline still fits peaks, sans calibration."""
    spectrum = make_spectrum(_PEAKS, n_channels=2048, seed=7)
    result = analyse_spectrum(spectrum, _config([]))
    assert result.calibration_model is None
    assert len(result.peak_fits) == 3
