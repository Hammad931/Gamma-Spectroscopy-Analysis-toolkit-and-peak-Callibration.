"""Physical quantities derived from a peak fit.

Once a peak has been fitted (:mod:`gammalib.fitting`) and the detector has been
calibrated (:mod:`gammalib.calibration`), a handful of standard numbers follow
directly: the peak's full width at half maximum, its net area, and the
detector's energy resolution.  These are pure algebraic conversions with no
state, which makes them trivial to test exhaustively.
"""

from __future__ import annotations

import numpy as np

# FWHM = 2 * sqrt(2 * ln 2) * sigma for a Gaussian.  Named for readability.
FWHM_PER_SIGMA = 2.0 * np.sqrt(2.0 * np.log(2.0))


def fwhm_from_sigma(sigma: float) -> float:
    """Full width at half maximum of a Gaussian of standard deviation ``sigma``."""
    if sigma < 0:
        raise ValueError(f"sigma must be non-negative, got {sigma}")
    return FWHM_PER_SIGMA * sigma


def gaussian_area(amplitude: float, sigma: float) -> float:
    """Net area (integral) of a Gaussian of the given amplitude and width.

    A Gaussian ``A * exp(-(x-mu)^2 / (2 sigma^2))`` integrates to
    ``A * sigma * sqrt(2*pi)``.  For a photopeak this is the number of net
    counts, i.e. the counts once the continuum has been removed.
    """
    if sigma < 0:
        raise ValueError(f"sigma must be non-negative, got {sigma}")
    return amplitude * sigma * np.sqrt(2.0 * np.pi)


def energy_resolution(fwhm_energy: float, centroid_energy: float) -> float:
    """Relative energy resolution ``FWHM / centroid`` (a dimensionless fraction).

    Multiply by 100 to express it as the usual percentage.  Both arguments must
    be in the same energy unit; the result does not depend on which unit that is.
    """
    if centroid_energy <= 0:
        raise ValueError(
            f"centroid_energy must be positive, got {centroid_energy}"
        )
    return fwhm_energy / centroid_energy
