# Explanation: the physics and the design

This page is for understanding rather than doing. It explains what the toolkit
is modelling and why the code is shaped the way it is. For step-by-step
instructions, see the [tutorial](tutorial.md) and [how-to guides](how-to.md).

## The problem

A gamma-ray detector feeding a multichannel analyser (MCA) produces a
**histogram**: for each of its channels it counts how many photons deposited an
energy falling in that channel's range. A monoenergetic gamma line shows up not
as a spike but as a roughly Gaussian **photopeak**, broadened by the finite
resolution of the detector, and sitting on a sloping **continuum** from Compton
scattering.

Two things a physicist wants from such a spectrum:

1. **Energy calibration** — the MCA counts in channels, not keV. To read the
   spectrum physically we need a mapping channel → energy.
2. **Resolution** — how sharply the detector separates nearby energies,
   quantified by a peak's full width at half maximum relative to its energy.

Both start from the same measurement: the precise position and width of a few
peaks.

## The peak model

Each photopeak is modelled as a Gaussian on a straight-line background:

```
f(x) = A · exp( −(x − μ)² / (2σ²) )  +  m·x + b
```

- `μ` (the centroid) is the peak's position — what the calibration needs.
- `σ` sets the width; the FWHM is `2·√(2 ln 2)·σ ≈ 2.355·σ`.
- `A` is the height above background; the net peak area is `A·σ·√(2π)`.
- `m·x + b` approximates the continuum **locally**, across the fitting window.

The straight-line background is the key simplifying assumption. The real Compton
continuum is not linear over a whole spectrum, but across the narrow window
around a single peak it is close enough, which is why the fit is done
window-by-window rather than globally. Choosing the window a few times wider
than the peak gives the linear term enough clean continuum on both sides to
latch onto.

## Why detection and fitting are separate

Peak *detection* only needs to be approximately right — it hands the fitter a
starting channel. Peak *fitting* is where precision comes from. Keeping them in
separate functions means each can be tested on its own (detection against known
injected positions; fitting against known injected shapes) and each can be
swapped out — a different detector, a different peak shape — without disturbing
the other.

## The calibration

With centroids `μᵢ` measured for peaks of known energy `Eᵢ`, the calibration is
a least-squares polynomial fit `E(channel)`. A straight line suffices for most
detectors; a quadratic term captures mild electronic non-linearity. More degrees
than the data supports would just fit noise, so the degree is an explicit,
conservative choice left to the user.

**The matching assumption.** The toolkit pairs the detected peaks with the
reference energies by *sorting both and matching in order* — the lowest-channel
peak to the lowest energy, and so on. This is simple and predictable, and it is
correct whenever the calibration is monotonic (higher energy → higher channel),
which is essentially always true. The cost is that the number of detected peaks
must equal the number of reference energies; if they differ, the pipeline stops
and says so rather than guessing a wrong pairing.

## Turning a channel width into an energy resolution

A fit gives the width in *channels*. To express resolution in energy we multiply
that width by how many keV a channel is worth **at that peak** — the local slope
(derivative) of the calibration curve. For a linear calibration this is just the
constant slope; the code computes the derivative generally so a quadratic
calibration also works.

## Design choices worth knowing

- **A frozen `Spectrum` value object.** Every step takes a `Spectrum` and
  returns new numbers or arrays; nothing mutates shared state. This is what lets
  the functions be called in any order without hidden coupling.
- **No global state, no hidden files.** Parameters come from an explicit config
  object or function arguments, never from module-level globals or hard-coded
  paths, so the same code runs identically on another machine.
- **Reproducible randomness.** The only randomness is the synthetic-spectrum
  noise, and it goes through a seeded `numpy` generator. A given seed always
  yields the same spectrum, which is what makes the tests deterministic.
- **Plotting is processing-free.** Visualisation functions only draw what they
  are given. Because they contain no logic to get wrong, they are — following
  the course guidelines — deliberately left out of the test suite.

## Limitations

- Overlapping or multiplet peaks are not deconvolved; each detected maximum is
  fitted as a single Gaussian.
- The background is linear within a window, so very curved continua under a
  broad peak will bias the area slightly.
- Peak areas are reported from the fit but the toolkit does not currently
  propagate them into activity or efficiency calculations — a natural next
  extension.
