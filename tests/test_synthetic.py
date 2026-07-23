"""Tests for the synthetic-spectrum generator.

Reproducibility is the whole point of this module -- the example data and the
test suite both depend on a given seed always producing the same spectrum -- so
that is what we check most carefully, together with the area convention.
"""

import numpy as np
import pytest

from gammalib.synthetic import SyntheticPeak, gaussian_counts, make_spectrum

# A single, well-separated peak reused by several tests.
_ONE_PEAK = [SyntheticPeak(center=500.0, area=50000.0, sigma=6.0)]


def test_same_seed_reproduces_identical_spectrum():
    """The seed must fully determine the noisy spectrum for reproducibility."""
    first = make_spectrum(_ONE_PEAK, n_channels=1024, seed=123)
    second = make_spectrum(_ONE_PEAK, n_channels=1024, seed=123)
    assert np.array_equal(first.counts, second.counts)


def test_different_seeds_give_different_noise():
    """Two seeds should not, in practice, produce byte-identical spectra."""
    first = make_spectrum(_ONE_PEAK, n_channels=1024, seed=1)
    second = make_spectrum(_ONE_PEAK, n_channels=1024, seed=2)
    assert not np.array_equal(first.counts, second.counts)


def test_noiseless_peak_area_matches_requested_area():
    """The amplitude convention must make the peak integrate to its 'area'."""
    peak = SyntheticPeak(center=500.0, area=50000.0, sigma=6.0)
    spectrum = make_spectrum([peak], n_channels=1024, add_noise=False,
                             background_level=0.0, background_slope=0.0)
    integrated = spectrum.counts.sum()
    # A few-permille shortfall is expected from the Gaussian's clipped tails.
    assert integrated == pytest.approx(peak.area, rel=1e-3)


def test_gaussian_counts_peaks_at_the_center():
    """The maximum of a single Gaussian must sit at its declared centre."""
    channels = np.arange(1024)
    peak = SyntheticPeak(center=500.0, area=50000.0, sigma=6.0)
    values = gaussian_counts(channels, peak)
    assert np.argmax(values) == 500


def test_non_positive_channel_count_is_rejected():
    """A zero/negative channel count is a caller error and must raise."""
    with pytest.raises(ValueError):
        make_spectrum(_ONE_PEAK, n_channels=0)
