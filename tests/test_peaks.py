"""Tests for peak detection.

We drive the detector with noiseless synthetic spectra where the true peak
positions are known exactly, so any deviation is unambiguous.  We also verify
the contract that channel *numbers* (not array indices) are returned, which
matters for cropped spectra.
"""

import numpy as np
import pytest

from gammalib.peaks import find_peak_channels
from gammalib.spectrum import Spectrum
from gammalib.synthetic import SyntheticPeak, make_spectrum


def test_finds_all_injected_peaks():
    """Three well-separated peaks should yield exactly three detections."""
    peaks = [
        SyntheticPeak(center=300.0, area=60000.0, sigma=6.0),
        SyntheticPeak(center=800.0, area=60000.0, sigma=6.0),
        SyntheticPeak(center=1400.0, area=60000.0, sigma=6.0),
    ]
    spectrum = make_spectrum(peaks, n_channels=2048, add_noise=False)
    found = find_peak_channels(spectrum, min_prominence=100.0, min_distance=20)
    assert list(found) == [300, 800, 1400]


def test_returns_channel_numbers_not_array_indices():
    """For a spectrum that does not start at channel 0, the offset must be kept."""
    channels = np.arange(500, 700)
    # A single triangular bump centred at channel 600.
    counts = 100.0 - np.abs(channels - 600)
    spectrum = Spectrum(channels=channels, counts=counts)

    found = find_peak_channels(spectrum, min_prominence=10.0)

    assert found.tolist() == [600]


def test_high_prominence_threshold_rejects_small_ripples():
    """Raising the prominence above the peak height must return nothing."""
    peaks = [SyntheticPeak(center=500.0, area=5000.0, sigma=6.0)]
    spectrum = make_spectrum(peaks, n_channels=1024, add_noise=False)
    found = find_peak_channels(spectrum, min_prominence=1e6)
    assert found.size == 0


def test_non_positive_prominence_is_rejected():
    """A non-positive prominence is meaningless and must raise."""
    spectrum = make_spectrum(
        [SyntheticPeak(center=500.0, area=5000.0, sigma=6.0)],
        n_channels=1024,
        add_noise=False,
    )
    with pytest.raises(ValueError):
        find_peak_channels(spectrum, min_prominence=0.0)


def test_zero_distance_is_rejected():
    """A minimum distance below one channel is meaningless and must raise."""
    spectrum = make_spectrum(
        [SyntheticPeak(center=500.0, area=5000.0, sigma=6.0)],
        n_channels=1024,
        add_noise=False,
    )
    with pytest.raises(ValueError):
        find_peak_channels(spectrum, min_prominence=10.0, min_distance=0)
