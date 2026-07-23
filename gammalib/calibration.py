"""Energy calibration: turning channel numbers into energies.

A multichannel analyser records events by channel, not by energy.  To read a
spectrum in physical units we measure the centroids of a few peaks whose
energies are known (from calibration sources such as :sup:`137`\\ Cs or
:sup:`60`\\ Co) and fit a smooth mapping ``channel -> energy`` through them.

For most detectors a straight line is enough; a quadratic term captures mild
non-linearity of the electronics.  The model is stored in a small
:class:`CalibrationModel` value object so it can be passed around and applied
without re-fitting.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CalibrationModel:
    """A fitted ``channel -> energy`` polynomial.

    Attributes
    ----------
    coefficients:
        Polynomial coefficients in *increasing* power order, i.e.
        ``energy = c[0] + c[1]*channel + c[2]*channel^2 + ...``.
    degree:
        Degree of the polynomial (1 for linear, 2 for quadratic, ...).
    """

    coefficients: np.ndarray
    degree: int


def fit_calibration(
    channels: np.ndarray,
    energies: np.ndarray,
    degree: int = 1,
) -> CalibrationModel:
    """Fit a polynomial mapping from peak channels to known energies.

    Parameters
    ----------
    channels:
        Measured peak centroids (in channels).
    energies:
        Known energies of those peaks, in the same order.
    degree:
        Degree of the polynomial to fit (default ``1``, a straight line).

    Returns
    -------
    CalibrationModel

    Raises
    ------
    ValueError
        If the two inputs differ in length, or if there are not enough points
        to constrain a polynomial of the requested degree (a degree-``d`` fit
        needs at least ``d + 1`` points).
    """
    channels = np.asarray(channels, dtype=float)
    energies = np.asarray(energies, dtype=float)

    if channels.shape != energies.shape:
        raise ValueError(
            "channels and energies must have the same length "
            f"(got {channels.size} and {energies.size})"
        )
    if channels.size < degree + 1:
        raise ValueError(
            f"a degree-{degree} calibration needs at least {degree + 1} "
            f"reference points, got {channels.size}"
        )

    # numpy.polynomial fits in increasing-power order and is numerically better
    # behaved than the legacy np.polyfit for higher degrees.
    coefficients = np.polynomial.polynomial.polyfit(channels, energies, degree)
    return CalibrationModel(coefficients=coefficients, degree=degree)


def apply_calibration(model: CalibrationModel, channels: np.ndarray) -> np.ndarray:
    """Convert channel numbers to energies using a fitted model."""
    channels = np.asarray(channels, dtype=float)
    return np.polynomial.polynomial.polyval(channels, model.coefficients)


def calibration_residuals(
    model: CalibrationModel,
    channels: np.ndarray,
    energies: np.ndarray,
) -> np.ndarray:
    """Return ``predicted_energy - known_energy`` for each reference point.

    Small residuals (relative to the detector resolution) are the quickest
    sanity check that the calibration is trustworthy.
    """
    predicted = apply_calibration(model, channels)
    return predicted - np.asarray(energies, dtype=float)
