"""Tests for the :class:`~gammalib.spectrum.Spectrum` container.

The container is the vocabulary of the whole library, so we check both that it
accepts well-formed data and that it rejects the malformed inputs that would
otherwise surface as confusing errors much later in the pipeline.
"""

import numpy as np
import pytest

from gammalib.spectrum import Spectrum


def test_spectrum_stores_channels_and_counts():
    """A valid spectrum should expose exactly the arrays it was built from."""
    spectrum = Spectrum(channels=[0, 1, 2], counts=[5, 9, 4])
    assert np.array_equal(spectrum.channels, [0, 1, 2])
    assert np.array_equal(spectrum.counts, [5, 9, 4])


def test_spectrum_length_equals_number_of_channels():
    """len() is used elsewhere as the channel count; pin that meaning down."""
    spectrum = Spectrum(channels=range(10), counts=range(10))
    assert len(spectrum) == 10


def test_spectrum_rejects_mismatched_lengths():
    """Mismatched arrays are a common data-entry error and must fail loudly."""
    with pytest.raises(ValueError):
        Spectrum(channels=[0, 1, 2], counts=[5, 9])


def test_spectrum_rejects_empty_input():
    """An empty spectrum has no meaning and would break peak search downstream."""
    with pytest.raises(ValueError):
        Spectrum(channels=[], counts=[])


def test_spectrum_rejects_two_dimensional_input():
    """Only 1-D histograms are supported; a 2-D array is a caller mistake."""
    with pytest.raises(ValueError):
        Spectrum(channels=[[0, 1]], counts=[[1, 2]])


def test_slice_is_inclusive_on_both_bounds():
    """slice() defines the fitting window, so both endpoints must be kept."""
    spectrum = Spectrum(channels=range(10), counts=range(10))
    window = spectrum.slice(3, 6)
    assert np.array_equal(window.channels, [3, 4, 5, 6])


def test_slice_rejects_window_outside_the_spectrum():
    """A window that overlaps nothing signals a configuration error, not empty data."""
    spectrum = Spectrum(channels=range(10), counts=range(10))
    with pytest.raises(ValueError):
        spectrum.slice(100, 200)


def test_slice_rejects_inverted_bounds():
    """A window whose upper bound is below its lower bound is a caller mistake."""
    spectrum = Spectrum(channels=range(10), counts=range(10))
    with pytest.raises(ValueError):
        spectrum.slice(6, 3)
