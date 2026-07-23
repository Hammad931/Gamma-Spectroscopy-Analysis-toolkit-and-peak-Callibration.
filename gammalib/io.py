"""Reading and writing spectra to disk.

The toolkit deliberately uses a simple, human-readable text format instead of
any of the many binary MCA formats: a two-column file of ``channel  counts``.
This keeps the example data inspectable and avoids depending on vendor-specific
parsers.  A one-column file (counts only) is also accepted, in which case the
channel numbers are taken to be ``0, 1, 2, ...``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .spectrum import Spectrum


def load_spectrum(path: str | Path, delimiter: str | None = None) -> Spectrum:
    """Load a spectrum from a text/CSV file.

    Parameters
    ----------
    path:
        Path to the file.  One or two columns are accepted:

        * one column  -> interpreted as counts, channels become ``0..N-1``;
        * two columns -> interpreted as ``channel, counts``.
    delimiter:
        Column separator.  ``None`` (the default) lets NumPy split on any run
        of whitespace, which also handles comma-separated files when combined
        with the ``,`` value.

    Returns
    -------
    Spectrum

    Notes
    -----
    Lines starting with ``#`` are treated as comments and ignored, so the file
    may carry a small header describing the measurement.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"spectrum file not found: {path}")

    data = np.loadtxt(path, delimiter=delimiter, comments="#", ndmin=2)

    if data.shape[1] == 1:
        counts = data[:, 0]
        channels = np.arange(counts.size)
    elif data.shape[1] >= 2:
        channels = data[:, 0].astype(int)
        counts = data[:, 1]
    else:  # pragma: no cover - np.loadtxt never returns zero columns
        raise ValueError(f"could not parse any column from {path}")

    return Spectrum(channels=channels, counts=counts)


def save_spectrum(spectrum: Spectrum, path: str | Path) -> None:
    """Write a spectrum to a two-column ``channel  counts`` text file.

    The output is round-trip compatible with :func:`load_spectrum`.  A short
    header line is written so the file is self-describing.
    """
    path = Path(path)
    table = np.column_stack([spectrum.channels, spectrum.counts])
    np.savetxt(
        path,
        table,
        header="channel counts",
        fmt=["%d", "%.6g"],
    )
