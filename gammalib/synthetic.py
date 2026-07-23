"""Generation of synthetic spectra.

Real detector data cannot be shipped with the repository (both because of size
and because measured data usually belongs to a collaboration).  Instead the
toolkit can *generate* a realistic-looking spectrum on demand, which is used
for the tutorial, for the runnable examples, and for the test suite.

Every source of randomness goes through a NumPy :class:`~numpy.random.Generator`
that is seeded explicitly, so a given seed always produces exactly the same
spectrum.  This is what makes the tests reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .spectrum import Spectrum


@dataclass(frozen=True)
class SyntheticPeak:
    """One Gaussian photopeak to place in a synthetic spectrum.

    Parameters
    ----------
    center:
        Channel at which the peak is centred.
    area:
        Total number of net counts in the peak (its integral).
    sigma:
        Gaussian standard deviation, in channels.  The FWHM is
        ``2.3548 * sigma``.
    """

    center: float
    area: float
    sigma: float


def gaussian_counts(channels: np.ndarray, peak: SyntheticPeak) -> np.ndarray:
    """Expected counts of a single Gaussian photopeak, without noise.

    The amplitude is derived from the requested *area* so that the integral of
    the returned curve equals ``peak.area`` (a Gaussian of area ``S`` and width
    ``sigma`` has amplitude ``S / (sigma * sqrt(2*pi))``).
    """
    amplitude = peak.area / (peak.sigma * np.sqrt(2.0 * np.pi))
    return amplitude * np.exp(-0.5 * ((channels - peak.center) / peak.sigma) ** 2)


def make_spectrum(
    peaks: list[SyntheticPeak],
    n_channels: int = 2048,
    background_level: float = 20.0,
    background_slope: float = -0.005,
    seed: int = 0,
    add_noise: bool = True,
) -> Spectrum:
    """Build a synthetic spectrum from a list of peaks on a linear continuum.

    Parameters
    ----------
    peaks:
        Photopeaks to add.
    n_channels:
        Number of channels in the analyser (default ``2048``).
    background_level, background_slope:
        Intercept and slope of the linear Compton-like continuum, in counts.
        The continuum is clipped at zero so it never goes negative.
    seed:
        Seed for the Poisson noise generator.  The same seed reproduces the
        same spectrum exactly (default ``0``).
    add_noise:
        If ``True`` (default) the ideal counts are replaced by a Poisson draw,
        mimicking real counting statistics.  Set to ``False`` to obtain the
        noiseless expectation, which is convenient for testing the fitters.

    Returns
    -------
    Spectrum
    """
    if n_channels <= 0:
        raise ValueError(f"n_channels must be positive, got {n_channels}")

    channels = np.arange(n_channels)

    continuum = np.clip(background_level + background_slope * channels, 0.0, None)
    expected = continuum.astype(float)
    for peak in peaks:
        expected = expected + gaussian_counts(channels, peak)

    if not add_noise:
        return Spectrum(channels=channels, counts=expected)

    # A dedicated Generator keeps this call free of any global RNG state, so
    # tests that run in parallel cannot interfere with each other.
    rng = np.random.default_rng(seed)
    noisy = rng.poisson(expected).astype(float)
    return Spectrum(channels=channels, counts=noisy)
