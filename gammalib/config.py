"""Loading the analysis configuration from a TOML file.

All the knobs of the pipeline (which file to analyse, how prominent a peak must
be, the fitting window, the reference energies, ...) live in a single TOML
file supplied by the user, never hard-coded in the source.  This module reads
that file into a plain, validated :class:`Config` object.

TOML is parsed with the standard-library :mod:`tomllib`, so no third-party
dependency is needed on Python 3.11 or newer.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Config:
    """All parameters needed to run the analysis pipeline.

    Attributes
    ----------
    spectrum_file:
        Path to the spectrum to analyse.  Interpreted relative to the config
        file's own directory when not absolute, so a config file is portable.
    min_prominence, min_distance:
        Peak-detection parameters (see :func:`gammalib.peaks.find_peak_channels`).
    window_half_width:
        Half-width of the fitting window in channels
        (see :func:`gammalib.fitting.fit_peak`).
    reference_energies:
        Known energies, in keV, of the calibration peaks.  They are matched to
        the detected peaks sorted by channel (see the documentation for this
        assumption).
    calibration_degree:
        Degree of the calibration polynomial.
    """

    spectrum_file: Path
    min_prominence: float
    min_distance: int
    window_half_width: int
    reference_energies: list[float] = field(default_factory=list)
    calibration_degree: int = 1


def load_config(path: str | Path) -> Config:
    """Read and validate a TOML configuration file.

    Missing optional keys fall back to the defaults documented on
    :class:`Config`; a missing required section raises a clear error rather
    than a bare :class:`KeyError`.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"configuration file not found: {path}")

    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    try:
        spectrum_file = Path(raw["input"]["spectrum_file"])
    except KeyError as exc:
        raise KeyError(
            "configuration must define [input].spectrum_file"
        ) from exc

    # Relative spectrum paths are resolved against the config file location, so
    # the same config works regardless of the current working directory.
    if not spectrum_file.is_absolute():
        spectrum_file = (path.parent / spectrum_file).resolve()

    detection = raw.get("peak_detection", {})
    fitting = raw.get("fitting", {})
    calibration = raw.get("calibration", {})

    return Config(
        spectrum_file=spectrum_file,
        min_prominence=float(detection.get("min_prominence", 50.0)),
        min_distance=int(detection.get("min_distance", 1)),
        window_half_width=int(fitting.get("window_half_width", 15)),
        reference_energies=[float(e) for e in calibration.get("reference_energies", [])],
        calibration_degree=int(calibration.get("degree", 1)),
    )
