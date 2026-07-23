"""The end-to-end analysis pipeline.

This module wires the single-purpose steps together into the workflow a user
usually wants: load a spectrum, find the peaks, fit each of them, and -- if
reference energies are supplied -- build an energy calibration and report the
resolution at every line.

It is kept free of any input/output side effects: it takes data and a
:class:`~gammalib.config.Config`, and returns a plain :class:`AnalysisResult`.
Reading files, printing and plotting live elsewhere (in the CLI and the
plotting module), so the pipeline itself is easy to call from a notebook and
easy to test.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import analysis, calibration, peaks
from .calibration import CalibrationModel
from .config import Config
from .fitting import PeakFit, fit_peak
from .spectrum import Spectrum


@dataclass(frozen=True)
class AnalysisResult:
    """Everything the pipeline computed for one spectrum.

    Attributes
    ----------
    peak_fits:
        One :class:`~gammalib.fitting.PeakFit` per detected peak, ordered by
        channel.
    calibration_model:
        The fitted ``channel -> energy`` model, or ``None`` if no reference
        energies were provided.
    peak_energies:
        Calibrated energy of each peak centroid (empty if uncalibrated).
    resolutions:
        Relative energy resolution (FWHM/energy) at each peak (empty if
        uncalibrated).
    """

    peak_fits: list[PeakFit]
    calibration_model: CalibrationModel | None
    peak_energies: np.ndarray
    resolutions: np.ndarray


def analyse_spectrum(spectrum: Spectrum, config: Config) -> AnalysisResult:
    """Run detection, fitting and (optional) calibration on a spectrum.

    Parameters
    ----------
    spectrum:
        The spectrum to analyse.
    config:
        Parameters controlling every step.

    Returns
    -------
    AnalysisResult

    Raises
    ------
    ValueError
        If reference energies are given but their count does not match the
        number of detected peaks.  Peaks and reference energies are paired in
        ascending-channel / ascending-energy order, so the two lists must line
        up one-to-one for the calibration to be meaningful.
    """
    peak_channels = peaks.find_peak_channels(
        spectrum,
        min_prominence=config.min_prominence,
        min_distance=config.min_distance,
    )

    peak_fits = [
        fit_peak(spectrum, int(channel), config.window_half_width)
        for channel in peak_channels
    ]

    references = config.reference_energies
    if not references:
        return AnalysisResult(
            peak_fits=peak_fits,
            calibration_model=None,
            peak_energies=np.array([]),
            resolutions=np.array([]),
        )

    if len(references) != len(peak_fits):
        raise ValueError(
            f"{len(references)} reference energies were given but "
            f"{len(peak_fits)} peaks were detected; adjust min_prominence or "
            "the reference_energies list so the two match"
        )

    # Peaks come out of detection already sorted by channel; reference energies
    # are sorted here so the user need not worry about ordering in the config.
    centroids = np.array([fit.center for fit in peak_fits])
    sorted_energies = np.sort(references)

    model = calibration.fit_calibration(
        centroids, sorted_energies, degree=config.calibration_degree
    )
    peak_energies = calibration.apply_calibration(model, centroids)

    resolutions = np.array(
        [
            analysis.energy_resolution(
                analysis.fwhm_from_sigma(fit.sigma)
                * _kev_per_channel(model, fit.center),
                energy,
            )
            for fit, energy in zip(peak_fits, peak_energies)
        ]
    )

    return AnalysisResult(
        peak_fits=peak_fits,
        calibration_model=model,
        peak_energies=peak_energies,
        resolutions=resolutions,
    )


def _kev_per_channel(model: CalibrationModel, channel: float) -> float:
    """Local energy-per-channel gain, used to turn a channel width into keV.

    The width of a peak is measured in channels; to express the resolution in
    energy we multiply it by the derivative of the calibration curve at the
    peak's position.  For a linear calibration this is simply the slope.
    """
    # Derivative of c0 + c1*x + c2*x^2 + ... evaluated at ``channel``.
    coeffs = model.coefficients
    powers = np.arange(1, coeffs.size)
    return float(np.sum(coeffs[1:] * powers * channel ** (powers - 1)))
