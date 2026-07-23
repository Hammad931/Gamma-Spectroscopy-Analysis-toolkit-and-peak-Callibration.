# API reference

Every public function and its parameters. Defaults are shown in the signatures.
The modules are organised by responsibility; nothing here depends on being
called in a particular order.

The full docstrings live in the source and are the authoritative version; this
page is a map.

## `gammalib.spectrum`

### `Spectrum(channels, counts)`
Immutable container for an MCA histogram. Validates that the two arrays are
1-D and equal in length. Methods:

- `len(spectrum)` — number of channels.
- `spectrum.slice(low, high)` — sub-spectrum with channel numbers in the
  inclusive range `[low, high]`.

## `gammalib.io`

### `load_spectrum(path, delimiter=None)`
Read a spectrum from a text/CSV file. One column → counts only (channels become
`0..N-1`); two columns → `channel, counts`. Lines starting with `#` are
comments. Raises `FileNotFoundError` if the path does not exist.

### `save_spectrum(spectrum, path)`
Write a spectrum as a two-column text file, round-trip compatible with
`load_spectrum`.

## `gammalib.synthetic`

### `SyntheticPeak(center, area, sigma)`
Description of one Gaussian photopeak: its centre channel, total net area, and
width.

### `make_spectrum(peaks, n_channels=2048, background_level=20.0, background_slope=-0.005, seed=0, add_noise=True)`
Build a synthetic spectrum from a list of peaks on a clipped linear continuum.
With `add_noise=True` the counts are a Poisson draw seeded by `seed` (so a seed
fully determines the spectrum); with `add_noise=False` you get the noiseless
expectation.

### `gaussian_counts(channels, peak)`
The noiseless counts of a single peak, normalised so its integral equals
`peak.area`.

## `gammalib.peaks`

### `find_peak_channels(spectrum, min_prominence, min_distance=1)`
Return the **channel numbers** (not array indices) of detected peaks, sorted
ascending. `min_prominence` (required) is how far, in counts, a maximum must
stand out; `min_distance` is the minimum gap between peaks in channels.

## `gammalib.fitting`

### `gaussian(x, amplitude, center, sigma)`
A bare Gaussian.

### `gaussian_plus_linear(x, amplitude, center, sigma, slope, intercept)`
A Gaussian added to a linear background — the peak model.

### `fit_peak(spectrum, approx_center, window_half_width)`
Fit `gaussian_plus_linear` in the window
`[approx_center ± window_half_width]`. Returns a `PeakFit` with the best-fit
parameters, the centroid and sigma uncertainties, and the window used. Raises
`RuntimeError` if the optimiser does not converge.

### `PeakFit`
Result object: `amplitude, center, sigma, slope, intercept, center_error,
sigma_error, window`.

## `gammalib.calibration`

### `fit_calibration(channels, energies, degree=1)`
Fit a polynomial mapping peak channels to known energies. Returns a
`CalibrationModel`. Raises `ValueError` on length mismatch or too few points for
the requested degree.

### `apply_calibration(model, channels)`
Convert channels to energies with a fitted model.

### `calibration_residuals(model, channels, energies)`
`predicted − known` energy for each reference point; a quick calibration sanity
check.

### `CalibrationModel`
`coefficients` (increasing-power order) and `degree`.

## `gammalib.analysis`

### `fwhm_from_sigma(sigma)`
Gaussian FWHM = `2·√(2 ln 2)·sigma`.

### `gaussian_area(amplitude, sigma)`
Net area of a Gaussian = `amplitude·sigma·√(2π)`.

### `energy_resolution(fwhm_energy, centroid_energy)`
Relative resolution `FWHM / energy` (a fraction; ×100 for a percentage).

## `gammalib.pipeline`

### `analyse_spectrum(spectrum, config)`
Run detection → fitting → optional calibration → resolution. Returns an
`AnalysisResult`. Raises `ValueError` if the number of reference energies does
not match the number of detected peaks.

### `AnalysisResult`
`peak_fits`, `calibration_model` (or `None`), `peak_energies`, `resolutions`.

## `gammalib.config`

### `load_config(path)`
Read and validate a TOML config file into a `Config`. Relative spectrum paths
are anchored to the config file's directory.

### `Config`
`spectrum_file, min_prominence, min_distance, window_half_width,
reference_energies, calibration_degree`.

## `gammalib.plotting`

`plot_spectrum`, `plot_peak_fit`, `plot_calibration` — draw already-computed
data onto a Matplotlib `Axes` (created if not given) and return it. These do no
processing and are, by design, not unit-tested.
