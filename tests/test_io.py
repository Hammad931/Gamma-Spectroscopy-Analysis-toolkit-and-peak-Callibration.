"""Tests for reading and writing spectra.

The key promise of the I/O layer is that saving then loading a spectrum returns
the same data, so a user can trust intermediate files.  We also check the two
convenience behaviours (single-column files and comment lines) and the error
raised for a missing file.
"""

import numpy as np
import pytest

from gammalib.io import load_spectrum, save_spectrum
from gammalib.spectrum import Spectrum


def test_save_then_load_round_trips_the_data(tmp_path):
    """Writing and reading back must preserve channels and counts."""
    original = Spectrum(channels=[0, 1, 2, 3], counts=[10, 42, 7, 3])
    path = tmp_path / "spectrum.dat"

    save_spectrum(original, path)
    restored = load_spectrum(path)

    assert np.array_equal(restored.channels, original.channels)
    assert np.allclose(restored.counts, original.counts)


def test_single_column_file_gets_sequential_channels(tmp_path):
    """A counts-only file must be interpreted with channels 0, 1, 2, ..."""
    path = tmp_path / "counts_only.dat"
    path.write_text("5\n9\n4\n")

    spectrum = load_spectrum(path)

    assert np.array_equal(spectrum.channels, [0, 1, 2])
    assert np.allclose(spectrum.counts, [5, 9, 4])


def test_comment_lines_are_ignored(tmp_path):
    """A header comment must not be parsed as data."""
    path = tmp_path / "with_header.dat"
    path.write_text("# channel counts\n0 5\n1 8\n")

    spectrum = load_spectrum(path)

    assert len(spectrum) == 2


def test_loading_a_missing_file_raises(tmp_path):
    """A clear FileNotFoundError is friendlier than NumPy's internal error."""
    with pytest.raises(FileNotFoundError):
        load_spectrum(tmp_path / "does_not_exist.dat")
