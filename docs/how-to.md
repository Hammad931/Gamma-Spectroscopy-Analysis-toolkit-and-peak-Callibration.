# How-to guides

Short, task-focused recipes. Each assumes you have installed the toolkit
(`pip install -e .`). For a gentle first run, start with the
[tutorial](tutorial.md) instead.

## Analyse your own spectrum

1. Export your spectrum as a two-column text file, `channel counts`, one row
   per channel. Lines beginning with `#` are ignored, so a header is fine. A
   single column (counts only) also works — channels are then assumed to be
   `0, 1, 2, ...`.
2. Copy `config/example_config.toml` and point `spectrum_file` at your file.
   A relative path is resolved next to the config file, so keep them together.
3. Set the reference energies of the calibration lines you used, in keV, and
   make sure `min_prominence` is high enough that exactly those peaks are
   detected.
4. Run:

   ```bash
   gamma-toolkit analyze --config my_config.toml --plot my_plots/
   ```

## Tune peak detection

If **too many** peaks are found (noise mistaken for peaks), raise
`min_prominence`. If **too few** are found, lower it. Use `min_distance` to stop
a single broad peak being reported as several. You can check what is detected
without committing to a calibration by leaving `reference_energies` empty — the
report then just lists the fitted peaks.

## Fit without calibrating

Omit `reference_energies` (or set it to `[]`) in the config. The pipeline still
detects and fits every peak and reports centroids and widths in channels; it
simply skips the energy columns.

## Use a quadratic calibration

If your electronics are slightly non-linear, set `degree = 2` in the
`[calibration]` section and provide at least three reference energies. Check the
calibration figure and the residuals to confirm the extra term is warranted —
do not add curvature the data does not ask for.

## Call the library from Python

The CLI is only a thin wrapper; every step is available directly. This is handy
inside a Jupyter notebook (put your analysis code in a notebook, but import the
functions from `gammalib` rather than redefining them there):

```python
from gammalib import (
    load_spectrum, find_peak_channels, fit_peak,
    fit_calibration, apply_calibration,
    fwhm_from_sigma, energy_resolution,
)

spectrum = load_spectrum("examples/example_spectrum.csv")

channels = find_peak_channels(spectrum, min_prominence=200.0, min_distance=20)
fits = [fit_peak(spectrum, int(c), window_half_width=30) for c in channels]

centroids = [f.center for f in fits]
energies  = [661.66, 1173.23, 1332.49]
model = fit_calibration(centroids, energies, degree=1)

for f, e in zip(fits, apply_calibration(model, centroids)):
    fwhm_keV = fwhm_from_sigma(f.sigma) * model.coefficients[1]  # slope = keV/ch
    print(f"{e:8.2f} keV   resolution {energy_resolution(fwhm_keV, e)*100:.2f} %")
```

## Generate a custom synthetic spectrum

For teaching or testing you can build a spectrum with any peaks you like:

```python
from gammalib import make_spectrum, SyntheticPeak, save_spectrum

peaks = [
    SyntheticPeak(center=300.0, area=50000.0, sigma=6.0),
    SyntheticPeak(center=900.0, area=30000.0, sigma=8.0),
]
spectrum = make_spectrum(peaks, n_channels=2048, seed=1)
save_spectrum(spectrum, "my_spectrum.csv")
```

Pass `add_noise=False` to get the noiseless expectation, which is what the test
suite uses to check the fitters against known inputs.

## Reproduce the tests and coverage

```bash
pip install -e ".[test]"
coverage run -m pytest
coverage report -m
```
