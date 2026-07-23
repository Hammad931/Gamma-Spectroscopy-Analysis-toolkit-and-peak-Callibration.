"""gammalib -- a small toolkit for gamma-ray spectrum analysis.

The public API is organised around a few single-purpose modules:

* :mod:`gammalib.spectrum`    -- the :class:`~gammalib.spectrum.Spectrum` container
* :mod:`gammalib.io`          -- reading and writing spectra
* :mod:`gammalib.synthetic`   -- generating reproducible test spectra
* :mod:`gammalib.peaks`       -- locating candidate peaks
* :mod:`gammalib.fitting`     -- fitting Gaussian photopeaks
* :mod:`gammalib.calibration` -- channel-to-energy calibration
* :mod:`gammalib.analysis`    -- derived quantities (FWHM, area, resolution)
* :mod:`gammalib.pipeline`    -- the end-to-end workflow
* :mod:`gammalib.plotting`    -- visualisation helpers

The most useful names are re-exported here for convenience.
"""

from __future__ import annotations

from .analysis import energy_resolution, fwhm_from_sigma, gaussian_area
from .calibration import CalibrationModel, apply_calibration, fit_calibration
from .config import Config, load_config
from .fitting import PeakFit, fit_peak, gaussian, gaussian_plus_linear
from .io import load_spectrum, save_spectrum
from .peaks import find_peak_channels
from .pipeline import AnalysisResult, analyse_spectrum
from .spectrum import Spectrum
from .synthetic import SyntheticPeak, make_spectrum

__version__ = "0.1.0"

__all__ = [
    "Spectrum",
    "load_spectrum",
    "save_spectrum",
    "SyntheticPeak",
    "make_spectrum",
    "find_peak_channels",
    "PeakFit",
    "fit_peak",
    "gaussian",
    "gaussian_plus_linear",
    "CalibrationModel",
    "fit_calibration",
    "apply_calibration",
    "fwhm_from_sigma",
    "gaussian_area",
    "energy_resolution",
    "Config",
    "load_config",
    "AnalysisResult",
    "analyse_spectrum",
    "__version__",
]
