"""Command-line interface for the gamma-spectroscopy toolkit.

The whole workflow is reachable without writing a line of Python::

    # 1. create an example spectrum to play with
    gamma-toolkit generate --output examples/example_spectrum.csv

    # 2. analyse it according to a configuration file
    gamma-toolkit analyze --config config/example_config.toml --plot plots/

Two subcommands are provided: ``generate`` (write a reproducible synthetic
spectrum) and ``analyze`` (run the detection/fitting/calibration pipeline and
print a report).  Both take explicit parameters -- there are no hidden scripts
to run in a particular order.
"""

from __future__ import annotations

import argparse
from pathlib import Path

# The CLI only ever *saves* figures, so a non-interactive backend is selected
# before anything pulls in pyplot.  This lets the command run on headless
# machines and continuous-integration servers.
import matplotlib

matplotlib.use("Agg")

from . import io, plotting, synthetic  # noqa: E402  (after backend selection)
from .config import load_config  # noqa: E402
from .pipeline import AnalysisResult, analyse_spectrum  # noqa: E402

# A ready-made Cs-137 / Co-60-like source used by the ``generate`` command.
# The three photopeaks are placed so that a straight-line calibration through
# them recovers energies close to the real 661.66 / 1173.23 / 1332.49 keV lines.
_DEMO_PEAKS = [
    synthetic.SyntheticPeak(center=970.0, area=90000.0, sigma=8.0),
    synthetic.SyntheticPeak(center=1722.0, area=45000.0, sigma=10.0),
    synthetic.SyntheticPeak(center=1957.0, area=40000.0, sigma=11.0),
]


def _cmd_generate(args: argparse.Namespace) -> None:
    """Write a reproducible synthetic spectrum to disk."""
    spectrum = synthetic.make_spectrum(
        _DEMO_PEAKS,
        n_channels=args.n_channels,
        seed=args.seed,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    io.save_spectrum(spectrum, output)
    print(f"wrote synthetic spectrum with {len(spectrum)} channels to {output}")


def _report(result: AnalysisResult) -> str:
    """Format the analysis result as a plain-text table (no side effects)."""
    lines = [f"detected and fitted {len(result.peak_fits)} peak(s):", ""]

    calibrated = result.calibration_model is not None
    header = f"{'centroid (ch)':>14} {'sigma (ch)':>11}"
    if calibrated:
        header += f" {'energy (keV)':>13} {'resolution (%)':>15}"
    lines.append(header)

    for i, fit in enumerate(result.peak_fits):
        row = f"{fit.center:>14.2f} {fit.sigma:>11.2f}"
        if calibrated:
            row += (
                f" {result.peak_energies[i]:>13.2f}"
                f" {result.resolutions[i] * 100:>15.2f}"
            )
        lines.append(row)

    if calibrated:
        coeffs = result.calibration_model.coefficients
        terms = " + ".join(f"{c:.5g}*ch^{p}" for p, c in enumerate(coeffs))
        lines += ["", f"calibration: energy = {terms}"]

    return "\n".join(lines)


def _cmd_analyze(args: argparse.Namespace) -> None:
    """Run the full pipeline described by a config file and print a report."""
    config = load_config(args.config)
    spectrum = io.load_spectrum(config.spectrum_file)
    result = analyse_spectrum(spectrum, config)

    print(_report(result))

    if args.plot is not None:
        _save_plots(spectrum, result, Path(args.plot))


def _save_plots(spectrum, result: AnalysisResult, out_dir: Path) -> None:
    """Save the spectrum, per-peak fit and calibration figures under ``out_dir``."""
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)

    ax = plotting.plot_spectrum(spectrum)
    ax.figure.savefig(out_dir / "spectrum.png", dpi=150, bbox_inches="tight")
    plt.close(ax.figure)

    for i, fit in enumerate(result.peak_fits):
        ax = plotting.plot_peak_fit(spectrum, fit)
        ax.figure.savefig(out_dir / f"peak_{i}.png", dpi=150, bbox_inches="tight")
        plt.close(ax.figure)

    if result.calibration_model is not None:
        centroids = [fit.center for fit in result.peak_fits]
        ax = plotting.plot_calibration(
            result.calibration_model, centroids, result.peak_energies
        )
        ax.figure.savefig(out_dir / "calibration.png", dpi=150, bbox_inches="tight")
        plt.close(ax.figure)

    print(f"saved plots to {out_dir}")


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level argument parser (exposed for testing)."""
    parser = argparse.ArgumentParser(
        prog="gamma-toolkit",
        description="Gamma-spectroscopy peak analysis and energy calibration.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="write a reproducible synthetic spectrum")
    gen.add_argument("--output", required=True, help="destination file")
    gen.add_argument("--seed", type=int, default=0, help="RNG seed (default 0)")
    gen.add_argument(
        "--n-channels", type=int, default=2048, help="number of channels (default 2048)"
    )
    gen.set_defaults(func=_cmd_generate)

    ana = sub.add_parser("analyze", help="run the analysis pipeline from a config file")
    ana.add_argument("--config", required=True, help="path to a TOML config file")
    ana.add_argument(
        "--plot",
        nargs="?",
        const="plots",
        default=None,
        help="save figures to this directory (default 'plots' when given no value)",
    )
    ana.set_defaults(func=_cmd_analyze)

    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point used by the ``gamma-toolkit`` console script."""
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main()
