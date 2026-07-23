"""The :class:`Spectrum` container used across the whole toolkit.

A gamma-ray spectrum coming out of a multichannel analyser (MCA) is, at its
core, a histogram: for every channel of the analyser we store how many events
were recorded in it.  Every function in this library speaks in terms of this
small, immutable container so that the different steps (peak search, fitting,
calibration, plotting) never have to agree on a fixed calling order: each of
them simply takes a ``Spectrum`` and returns plain arrays or numbers.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Spectrum:
    """An MCA spectrum: counts recorded in a set of (integer) channels.

    Parameters
    ----------
    channels:
        1-D array of channel numbers.  Usually ``0, 1, ..., N-1`` but the
        container does not force this so that already-cropped spectra can be
        represented as well.
    counts:
        1-D array with the number of events recorded in each channel.  It must
        have the same length as ``channels``.

    Notes
    -----
    The object is frozen (immutable): analysis steps return *new* data instead
    of mutating the spectrum in place.  This keeps the functions decorrelated
    and avoids the whole class of bugs that come from shared mutable state.
    """

    channels: np.ndarray
    counts: np.ndarray

    def __post_init__(self) -> None:
        # We convert on the way in so callers may pass plain Python lists.
        # ``object.__setattr__`` is the documented way to assign fields on a
        # frozen dataclass from within ``__post_init__``.
        object.__setattr__(self, "channels", np.asarray(self.channels))
        object.__setattr__(self, "counts", np.asarray(self.counts, dtype=float))

        if self.channels.ndim != 1 or self.counts.ndim != 1:
            raise ValueError("channels and counts must both be one-dimensional")

        if self.channels.shape != self.counts.shape:
            raise ValueError(
                "channels and counts must have the same length "
                f"(got {self.channels.shape[0]} and {self.counts.shape[0]})"
            )

        if self.channels.size == 0:
            raise ValueError("a spectrum must contain at least one channel")

    def __len__(self) -> int:
        return int(self.channels.size)

    def slice(self, low: int, high: int) -> "Spectrum":
        """Return the sub-spectrum with channel numbers in ``[low, high]``.

        Both bounds are inclusive.  This is used to isolate the region around a
        peak before fitting it, and is intentionally the only "windowing"
        primitive in the library so that every consumer crops data the same way.
        """
        if high < low:
            raise ValueError(f"empty window requested: high ({high}) < low ({low})")

        mask = (self.channels >= low) & (self.channels <= high)
        selected = self.channels[mask]
        if selected.size == 0:
            raise ValueError(
                f"window [{low}, {high}] does not overlap the spectrum "
                f"[{self.channels.min()}, {self.channels.max()}]"
            )
        return Spectrum(channels=selected, counts=self.counts[mask])
