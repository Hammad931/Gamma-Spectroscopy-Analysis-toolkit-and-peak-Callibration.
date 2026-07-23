"""Locating candidate peaks in a spectrum.

This step gives *approximate* peak positions (to the nearest channel).  The
precise sub-channel centroids come later, from the Gaussian fit in
:mod:`gammalib.fitting`.  Keeping detection and fitting separate means the two
can be tested and reused independently.

Detection is a thin, well-documented wrapper around
:func:`scipy.signal.find_peaks`.  We expose the two parameters that matter most
for gamma spectra -- *prominence* (how far a peak stands out above the local
continuum) and *minimum distance* between peaks -- and hide the rest.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks

from .spectrum import Spectrum


def find_peak_channels(
    spectrum: Spectrum,
    min_prominence: float,
    min_distance: int = 1,
) -> np.ndarray:
    """Return the channel numbers of candidate peaks, sorted ascending.

    Parameters
    ----------
    spectrum:
        The spectrum to search.
    min_prominence:
        Minimum prominence a maximum must have, in counts, to be reported.
        This is the single most useful knob for rejecting statistical ripples
        on the continuum.  It has no default on purpose: a sensible value
        depends on the count level of the data and the user should choose it.
    min_distance:
        Minimum separation between two reported peaks, in channels
        (default ``1``).  Use it to avoid splitting a single broad peak into
        several detections.

    Returns
    -------
    numpy.ndarray
        The channel numbers (not the array indices) of the detected peaks.
        The array is empty if nothing is found.

    Notes
    -----
    ``scipy.signal.find_peaks`` returns *indices* into the counts array; we map
    them back to the spectrum's own channel numbering before returning, so the
    result stays meaningful even for cropped spectra.
    """
    if min_prominence <= 0:
        raise ValueError(f"min_prominence must be positive, got {min_prominence}")
    if min_distance < 1:
        raise ValueError(f"min_distance must be at least 1, got {min_distance}")

    indices, _properties = find_peaks(
        spectrum.counts,
        prominence=min_prominence,
        distance=min_distance,
    )
    return spectrum.channels[indices]
