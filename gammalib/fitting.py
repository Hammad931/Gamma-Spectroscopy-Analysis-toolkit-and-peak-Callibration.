"""Fitting a Gaussian photopeak on top of a linear continuum.

Peak search gives an approximate position; fitting turns it into a precise
centroid, a width (and therefore an energy resolution), and a net area.  The
model is the classic one for a photopeak sitting on the Compton continuum::

    f(x) = A * exp(-(x - mu)^2 / (2 * sigma^2)) + slope * x + intercept

The two model functions (:func:`gaussian` and :func:`gaussian_plus_linear`) are
kept separate and pure so they can be reused for plotting and tested on their
own, independently of the fitting machinery.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import curve_fit

from .spectrum import Spectrum


def gaussian(x: np.ndarray, amplitude: float, center: float, sigma: float) -> np.ndarray:
    """A bare Gaussian ``amplitude * exp(-(x - center)^2 / (2 sigma^2))``."""
    return amplitude * np.exp(-0.5 * ((x - center) / sigma) ** 2)


def gaussian_plus_linear(
    x: np.ndarray,
    amplitude: float,
    center: float,
    sigma: float,
    slope: float,
    intercept: float,
) -> np.ndarray:
    """A Gaussian photopeak added to a linear background."""
    return gaussian(x, amplitude, center, sigma) + slope * x + intercept


@dataclass(frozen=True)
class PeakFit:
    """Result of fitting one photopeak.

    Attributes
    ----------
    amplitude, center, sigma, slope, intercept:
        Best-fit values of the five model parameters.  ``sigma`` is always
        returned as a positive number.
    center_error, sigma_error:
        One-standard-deviation uncertainties on the centroid and the width,
        taken from the diagonal of the covariance matrix.  These are the two
        that downstream analysis (calibration, resolution) actually needs.
    window:
        The ``(low, high)`` inclusive channel range the fit was performed on.
        Recorded so the fit can be reproduced and plotted.
    """

    amplitude: float
    center: float
    sigma: float
    slope: float
    intercept: float
    center_error: float
    sigma_error: float
    window: tuple[int, int]


def _initial_guess(channels: np.ndarray, counts: np.ndarray) -> list[float]:
    """Build a starting point for the optimiser from the windowed data.

    A good initial guess is what keeps ``curve_fit`` from wandering off.  We
    estimate the background from the two window edges, the amplitude from the
    peak height above that background, and the width from the number of
    channels standing clearly above the background.
    """
    intercept_guess = float(counts[0])
    slope_guess = float((counts[-1] - counts[0]) / (channels[-1] - channels[0]))
    baseline = slope_guess * channels + intercept_guess

    above = counts - baseline
    amplitude_guess = float(above.max())
    center_guess = float(channels[np.argmax(above)])

    # Rough width: how many channels sit above half of the peak height.
    half = amplitude_guess / 2.0
    width_channels = max(int(np.count_nonzero(above > half)), 1)
    sigma_guess = width_channels / 2.3548  # FWHM -> sigma

    return [amplitude_guess, center_guess, sigma_guess, slope_guess, intercept_guess]


def fit_peak(spectrum: Spectrum, approx_center: int, window_half_width: int) -> PeakFit:
    """Fit a single Gaussian-plus-linear peak around ``approx_center``.

    Parameters
    ----------
    spectrum:
        The full spectrum; only the window around the peak is used.
    approx_center:
        Approximate peak channel, e.g. one value returned by
        :func:`gammalib.peaks.find_peak_channels`.
    window_half_width:
        Half-width of the fitting window, in channels.  The fit uses the range
        ``[approx_center - window_half_width, approx_center + window_half_width]``.
        It should be a few times the expected peak width so that enough
        continuum is visible on either side.

    Returns
    -------
    PeakFit

    Raises
    ------
    RuntimeError
        If the optimiser fails to converge.  The original message from SciPy is
        preserved so the user can see why.
    """
    if window_half_width < 2:
        raise ValueError(
            f"window_half_width must be at least 2, got {window_half_width}"
        )

    low = approx_center - window_half_width
    high = approx_center + window_half_width
    region = spectrum.slice(low, high)

    x = region.channels.astype(float)
    y = region.counts

    guess = _initial_guess(x, y)

    try:
        popt, pcov = curve_fit(gaussian_plus_linear, x, y, p0=guess, maxfev=10000)
    except RuntimeError as exc:
        raise RuntimeError(
            f"peak fit near channel {approx_center} did not converge: {exc}"
        ) from exc

    amplitude, center, sigma, slope, intercept = popt
    errors = np.sqrt(np.diag(pcov))

    result = PeakFit(
        amplitude=float(amplitude),
        center=float(center),
        # sigma enters the model squared, so its sign is arbitrary; report |sigma|.
        sigma=float(abs(sigma)),
        slope=float(slope),
        intercept=float(intercept),
        center_error=float(errors[1]),
        sigma_error=float(errors[2]),
        window=(int(region.channels[0]), int(region.channels[-1])),
    )

    # Invariant made explicit for the reader: the returned window is ordered.
    assert result.window[0] <= result.window[1]
    return result
