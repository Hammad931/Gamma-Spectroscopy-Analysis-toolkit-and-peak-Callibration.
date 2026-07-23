"""Visualisation helpers.

Following the course guidelines, these functions do **no** data processing: they
receive quantities that were already computed elsewhere (the spectrum, a fit,
a calibration model) and only draw them.  Because all the logic lives upstream,
these functions are intentionally left untested -- there is nothing to assert
about a picture that would be worth the brittleness of the test.

Every function draws onto a Matplotlib ``Axes`` (created if not supplied) and
returns it, so plots can be composed by the caller.
"""

from __future__ import annotations

import numpy as np

import matplotlib.pyplot as plt

from .calibration import CalibrationModel, apply_calibration
from .fitting import PeakFit, gaussian_plus_linear
from .spectrum import Spectrum


def plot_spectrum(spectrum: Spectrum, ax=None):
    """Draw the raw spectrum as a step plot of counts versus channel."""
    if ax is None:
        _, ax = plt.subplots()
    ax.step(spectrum.channels, spectrum.counts, where="mid", linewidth=0.8)
    ax.set_xlabel("channel")
    ax.set_ylabel("counts")
    ax.set_title("Gamma-ray spectrum")
    return ax


def plot_peak_fit(spectrum: Spectrum, fit: PeakFit, ax=None):
    """Overlay a fitted Gaussian-plus-linear model on its data window."""
    if ax is None:
        _, ax = plt.subplots()

    region = spectrum.slice(*fit.window)
    dense_x = np.linspace(fit.window[0], fit.window[1], 400)
    model_y = gaussian_plus_linear(
        dense_x, fit.amplitude, fit.center, fit.sigma, fit.slope, fit.intercept
    )

    ax.step(region.channels, region.counts, where="mid", label="data", linewidth=0.8)
    ax.plot(dense_x, model_y, label="fit")
    ax.axvline(fit.center, linestyle="--", linewidth=0.8, label="centroid")
    ax.set_xlabel("channel")
    ax.set_ylabel("counts")
    ax.legend()
    return ax


def plot_calibration(
    model: CalibrationModel,
    channels: np.ndarray,
    energies: np.ndarray,
    ax=None,
):
    """Plot the calibration points together with the fitted curve."""
    if ax is None:
        _, ax = plt.subplots()

    channels = np.asarray(channels, dtype=float)
    dense_channels = np.linspace(channels.min(), channels.max(), 200)

    ax.scatter(channels, energies, label="reference peaks")
    ax.plot(dense_channels, apply_calibration(model, dense_channels), label="fit")
    ax.set_xlabel("channel")
    ax.set_ylabel("energy (keV)")
    ax.set_title("Energy calibration")
    ax.legend()
    return ax
