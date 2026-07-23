"""Tests for the command-line interface.

The CLI is a user-facing entry point, so it is tested like any other exposed
function: we drive ``main`` with argument lists and assert on the files it
produces and the report it formats, rather than on anything it prints.
"""

import numpy as np
import pytest

from gammalib import cli
from gammalib.io import load_spectrum
from gammalib.pipeline import AnalysisResult
from gammalib.fitting import PeakFit


def test_parser_requires_a_subcommand():
    """Running with no subcommand must fail rather than silently do nothing."""
    parser = cli.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_generate_writes_a_reproducible_spectrum(tmp_path):
    """`generate` must create a loadable spectrum, and the seed must fix it."""
    out = tmp_path / "spec.csv"
    cli.main(["generate", "--output", str(out), "--seed", "5", "--n-channels", "512"])

    spectrum = load_spectrum(out)
    assert len(spectrum) == 512


def test_generate_is_deterministic_for_a_seed(tmp_path):
    """Two runs with the same seed must produce identical files."""
    first = tmp_path / "a.csv"
    second = tmp_path / "b.csv"
    cli.main(["generate", "--output", str(first), "--seed", "9"])
    cli.main(["generate", "--output", str(second), "--seed", "9"])

    assert first.read_text() == second.read_text()


def test_analyze_runs_end_to_end(tmp_path):
    """A generated spectrum plus a matching config must analyse without error."""
    spectrum_path = tmp_path / "spec.csv"
    cli.main(["generate", "--output", str(spectrum_path), "--seed", "3"])

    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f'[input]\nspectrum_file = "{spectrum_path}"\n'
        "[peak_detection]\nmin_prominence = 200.0\nmin_distance = 20\n"
        "[fitting]\nwindow_half_width = 30\n"
        "[calibration]\nreference_energies = [661.66, 1173.23, 1332.49]\n"
    )

    plots = tmp_path / "plots"
    # Should complete and create the requested figures.
    cli.main(["analyze", "--config", str(config_path), "--plot", str(plots)])
    assert (plots / "spectrum.png").exists()
    assert (plots / "calibration.png").exists()


def _dummy_fit(center):
    return PeakFit(
        amplitude=1.0, center=center, sigma=5.0, slope=0.0, intercept=0.0,
        center_error=0.1, sigma_error=0.1, window=(int(center) - 10, int(center) + 10),
    )


def test_report_omits_energy_columns_when_uncalibrated():
    """Without a calibration the report must not invent energy/resolution columns."""
    result = AnalysisResult(
        peak_fits=[_dummy_fit(500.0)],
        calibration_model=None,
        peak_energies=np.array([]),
        resolutions=np.array([]),
    )
    text = cli._report(result)
    assert "energy (keV)" not in text
    assert "centroid (ch)" in text
