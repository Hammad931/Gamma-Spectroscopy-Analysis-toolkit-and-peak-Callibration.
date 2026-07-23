"""Tests for configuration loading.

We write small TOML files to a temporary directory and check that the values
land in the right fields, that defaults fill in the optional keys, and that a
missing required key and a missing file both raise clearly.
"""

import pytest

from gammalib.config import load_config

_FULL_CONFIG = """
[input]
spectrum_file = "data/spectrum.dat"

[peak_detection]
min_prominence = 120.0
min_distance = 15

[fitting]
window_half_width = 25

[calibration]
degree = 2
reference_energies = [661.66, 1173.23, 1332.49]
"""


def test_all_fields_are_read(tmp_path):
    """Every explicitly-set key must appear in the parsed Config."""
    path = tmp_path / "config.toml"
    path.write_text(_FULL_CONFIG)

    config = load_config(path)

    assert config.min_prominence == 120.0
    assert config.min_distance == 15
    assert config.window_half_width == 25
    assert config.calibration_degree == 2
    assert config.reference_energies == [661.66, 1173.23, 1332.49]


def test_relative_spectrum_path_is_anchored_to_the_config(tmp_path):
    """A relative spectrum path must resolve next to the config file itself."""
    path = tmp_path / "config.toml"
    path.write_text(_FULL_CONFIG)

    config = load_config(path)

    assert config.spectrum_file == (tmp_path / "data/spectrum.dat").resolve()


def test_optional_sections_fall_back_to_defaults(tmp_path):
    """A minimal config (only the required key) must still load with defaults."""
    path = tmp_path / "minimal.toml"
    path.write_text('[input]\nspectrum_file = "s.dat"\n')

    config = load_config(path)

    assert config.calibration_degree == 1
    assert config.reference_energies == []


def test_missing_required_key_raises(tmp_path):
    """Leaving out [input].spectrum_file must raise a descriptive KeyError."""
    path = tmp_path / "broken.toml"
    path.write_text("[peak_detection]\nmin_prominence = 10.0\n")

    with pytest.raises(KeyError):
        load_config(path)


def test_missing_file_raises(tmp_path):
    """Pointing at a non-existent config file must raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nope.toml")


def test_absolute_spectrum_path_is_left_untouched(tmp_path):
    """An absolute spectrum path must be used verbatim, not re-anchored."""
    absolute = (tmp_path / "elsewhere" / "s.dat").resolve()
    path = tmp_path / "abs.toml"
    path.write_text(f'[input]\nspectrum_file = "{absolute}"\n')

    config = load_config(path)

    assert config.spectrum_file == absolute
