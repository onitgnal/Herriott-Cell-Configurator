# Physics and Numerical Conventions

This is the authoritative human-readable description of the implemented model. It is meant to prevent plausible-looking changes that use a different sign, radius, pass-count, or phase convention. The code and Pydantic schemas remain the executable source of truth.

## Units and coordinate conventions

| Quantity | Unit/convention |
| --- | --- |
| mirror distances, radii, holes, beam radii, focal lengths | mm |
| wavelength input | vacuum nm; converted using `1 nm = 1e-6 mm` |
| external diffraction wavelength | vacuum wavelength |
| intracell diffraction wavelength | `lambda_vacuum / n` |
| ray slopes and mirror tilts | mrad in requests, rad internally |
| peak power | GW |
| pulse energy | mJ |
| displayed peak intensity | GW/cm² |
| displayed fluence | mJ/cm² |

The cell optical axis is global `z`. Mirror 1 is near `z=0`; mirror 2 is near `z=L`. Ray points are stored as `(x, y, z)`. The 3D renderer deliberately maps the optical axis onto its plotted x-axis.

`w` always denotes the 1/e complex-field amplitude radius, equivalently the 1/e² intensity radius. This is not an FWHM or hard-aperture radius.

## Pass and pattern convention

The request names retain the historical `total_passes`, but the UI labels it **Round Trips / Spots per Mirror (N)**.

- One round trip contains two mirror-to-mirror legs.
- A nominal N-round-trip configuration contains `2N` legs.
- A well-formed rotating pattern with revolution number `k` uses

  `theta_rt = 2*pi*k/N`.

- Automatic nonzero injection requires `gcd(N, k) = 1`, otherwise the ray revisits an earlier spot before making N distinct spots per mirror.

The exact ray trace may terminate earlier at a hole or by missing a mirror. ABCD and wave results follow the successfully traced leg count where physical output placement depends on the actual exit.

## Mirror radius signs and stability

The code uses

`g1 = 1 - L/R1`

`g2 = 1 - L/R2`.

A cell is considered stable only for the strict condition

`0 < g1*g2 < 1`.

Radius signs:

- concave-concave (`cav-cav`): `R1 > 0`, `R2 > 0`;
- concave-convex (`cav-vex`): `R1 > 0`, `R2 < 0`.

### Automatic concave-concave radius

For a symmetric cell, both radii are

`R = L / (1 - cos(pi*k/N))`.

The schema rejects the singular denominator before simulation.

### Concave-convex radius modes

`auto_equal` chooses equal magnitude and opposite sign:

`R1 = L / abs(sin(pi*k/N))`, `R2 = -R1`.

`auto_r2` keeps the requested positive R1 and preserves the desired round-trip phase:

`target = cos(pi*k/N)^2`

`g1 = 1 - L/R1`

`g2 = target/g1`

`R2 = L/(1 - g2)`.

The validator rejects `g1=0`, infinite R2, or any R1 that produces a non-convex R2.

`manual` requires an explicitly positive R1 and negative R2.

## Cavity eigenmode

Define

`g_sum = g1 + g2 - 2*g1*g2`.

The implemented Rayleigh range and waist position measured from M1 toward M2 are

`z_R = sqrt(abs(L^2*g1*g2*(1-g1*g2) / g_sum^2))`

`z_waist = L*g2*(1-g1) / g_sum`.

The fundamental waist radius is

`w0 = sqrt(lambda_medium*z_R/pi)`.

The target q at the M1 plane is therefore

`q_target_cell = -z_waist + i*z_R`.

The fundamental mirror radii used by the app are

`w1 = sqrt(abs((lambda_medium*L/pi) * sqrt(g2/(g1*(1-g1*g2)))))`

`w2 = sqrt(abs((lambda_medium*L/pi) * sqrt(g1/(g2*(1-g1*g2)))))`.

Higher-order analytic display radii multiply these base radii by `sqrt(M2x)` or `sqrt(M2y)`.

## Gaussian q convention

For either transverse axis,

`1/q = 1/R_wavefront - i*M2*lambda/(pi*w^2)`.

At a waist,

`q = i*z_R`, where `z_R = pi*w0^2/(M2*lambda)`.

The basic transforms are:

- free space `d`: `q_out = q_in + d`;
- thin lens `f`: `1/q_out = 1/q_in - 1/f`, implemented as `q/(1-q/f)`;
- spherical mirror `R`: the reflected paraxial matrix has `C=-2/R`, equivalent to a thin lens `f=R/2` for q propagation.

`compute_abcd_axis()` accepts the exact achieved complex q. Do not reconstruct both axes from one averaged waist position when their achieved q values differ.

### Planar refractive-index boundary

With the q definition above and a planar boundary from index `n1` to `n2`, continuity of transverse phase and radius gives

`q2 = (n2/n1)*q1`.

The current external medium is air (`n1=1`) and the uniform cell medium has the requested `n`, so

`q_target_air = q_target_cell/n`

and the achieved telescope output is converted by

`q_cell = n*q_air`.

The external propagation uses `lambda_vacuum`; cell propagation uses `lambda_vacuum/n`.

## Analytic transverse modes

The main mode selector changes the fast analytic envelope and display profile:

- TEM00: `M2x=M2y=1`;
- HG(n,m): `M2x=2n+1`, `M2y=2m+1`;
- LG(p,l): `M2x=M2y=2p+abs(l)+1`;
- custom: requested shared `M2 >= 1`.

`modes.py` evaluates Hermite and associated-Laguerre polynomials and computes a normalized peak factor. The renderer divides modal envelope radii by `sqrt(M2)` before applying that factor, avoiding double-counting the high-order width in peak intensity.

Explicit 2D wave optics is intentionally restricted to a main TEM00 q envelope. An LG complex launch is selected independently in the wave-optics profile control.

## Three-lens mode matching

The input beam is collimated at the phase-plate plane. For a requested radius `w_in`, each axis starts with

`q_in = i*pi*w_in^2/(M2*lambda_vacuum)`.

The telescope sequence is

`input --d0-- L1 --d12-- L2 --d23-- L3 --d3m-- M1`.

All lenses are spherical, so x and y see the same focal lengths. A single system generally cannot match unequal x/y M² values exactly; the optimizer minimizes the maximum normalized x/y q error and the UI reports the closest fit.

The normalized matching error is

`max(abs(qx-qtarget), abs(qy-qtarget)) / max(abs(qtarget), 1 mm)`.

The automatic modes add a very small total-length penalty to favor practical compact solutions. Search characteristics:

- deterministic seeded candidate generation;
- standard positive focal-length catalog from 50 to 2500 mm;
- automatic inter-element distances bounded from 20 to 3000 mm;
- bounded Nelder-Mead refinement;
- cached automatic designs.

Match thresholds are 0.2% for equal x/y M² and 2% for unequal x/y M². These thresholds affect only status text. The achieved q is always used, even when status is “closest fit.”

The external Gaussian trace is sampled through every free-space section before each lens. The downstream trace propagates the actual q at the last traced cell plane into air without applying a fictitious final mirror reflection.

## Exact geometric ray model

`ray_tracing.py` intersects each ray with the appropriate spherical mirror using the quadratic line/sphere equation. It chooses the nearest positive intersection parameter and reflects vectors by

`v_reflected = v - 2*(v dot normal)*normal`.

The two local transverse basis vectors are reflected with the ray. They carry polarization/profile orientation to subsequent hit records and wave frames.

Mirror tilts move the corresponding sphere center according to the requested angular displacement. Injection directions use normalized `(theta_x, theta_y, 1)` with milliradians converted to radians.

The automatic injection is derived from the round-trip matrix at the requested spot radius. With

`M00_arrive = 1 - 2L/R2`

`M01_arrive = 2L*g2`,

the initial slopes are

`theta_x = r0*(cos(theta_rt)-M00_arrive)/M01_arrive`

`theta_y = r0*sin(theta_rt)/M01_arrive`

in radians, returned to the API/UI in milliradians.

The ray terminates on an input/output hole, a missed mirror, or the safety leg limit. The first point is the nominal launch point at M1 (or its plane for an invalid off-surface launch); `total_bounces = len(points)-1`.

## Explicit wave input fields

Fields are normalized to unit numerical power at the input plane before propagation. The following formulas omit normalization constants.

### Gaussian

`U(x,y) = exp(-(x/wx)^2 - (y/wy)^2)`.

### Separable super-Gaussian

For order `s`:

`U(x,y) = exp(-abs(x/wx)^(2s)) * exp(-abs(y/wy)^(2s))`.

### Round super-Gaussian

With `w_round = sqrt(wx*wy)`:

`U(r) = exp(-(r/w_round)^(2s))`.

### Laguerre-Gaussian

For the circular case, the implemented field is proportional to

`(sqrt(2)*r/w)^abs(l) * L_p^abs(l)(2r^2/w^2) * exp(-r^2/w^2) * exp(i*l*phi)`.

For unequal x/y radii, normalized elliptical coordinates preserve the corresponding Gaussian envelope. Signed `l` changes helical phase handedness; intensity depends on `abs(l)`.

### Vortex plate and radial pupil shaper

For Gaussian and both super-Gaussian profiles, enabling the plate applies

`exp(i*l*phi)`.

With radial pupil `p=0`, intensity at the plate is unchanged. A Gaussian with this phase produces the familiar Kummer/HyGG-type vortex after propagation; a super-Gaussian becomes a super-Gaussian optical vortex.

For `p>0`, the app additionally applies

`(sqrt(2)*r/w_round)^p`.

That factor changes amplitude and power distribution. It represents a complex pupil shaper such as a suitable SLM/hologram, not a second degree of freedom of a passive phase-only spiral plate. This `p` is not the LG node index and is not asserted to equal every literature HyGG parameterization.

## Telescope wave propagation

Gaussian, super-Gaussian, and vortex fields use a common transverse grid through the telescope. Free space uses the paraxial angular-spectrum transfer function

`H(fx,fy) = exp(-i*pi*lambda*d*(fx^2+fy^2))`.

Each thin lens applies

`exp(-i*k*(x^2+y^2)/(2f))`.

The grid is sized to hold the widest q-predicted beam and resolve the smallest beam/largest quadratic phase across all telescope planes. Common-grid propagation avoids interpolation at the lenses.

An ideal LG mode through a rotationally symmetric first-order telescope remains the same `(p,l)` mode with transformed q. For that profile only, the implementation uses the exact closed-form ABCD mapping at M1 instead of four very large telescope FFTs. Intracell propagation remains explicit.

The transverse field is unchanged at the planar air/cell boundary; only the propagation wavelength/q interpretation changes.

## Intracell wave propagation

The solver follows each successfully traced ray leg. q states predict radii and curvatures at:

- the start mirror;
- the geometric center plane `L/2`;
- an internal minimum-area plane when one exists away from a boundary;
- the end mirror.

The minimum-area location is found from 513 samples of `wx(z)*wy(z)`. If the minimum is effectively on a mirror, the leg uses direct mirror-to-mirror propagation. Otherwise it uses a split path through the internal focus. Center profiles are always calculated separately for display.

Propagation between different grids evaluates the scalar Collins/Fresnel integral:

- up to 640 points on both relevant axes: dense separable matrices;
- above 640: an equivalent scaled FFT/Bluestein transform with lower asymptotic memory.

Between continuing legs, the end mirror applies:

`exp(-i*k*(x^2+y^2)/R_mirror)`

plus local hole masks. No initial mirror phase is applied at launch, and no fictitious final reflection is applied after the last traced leg.

The model uses scalar paraxial diffraction with an `exp(-i*omega*t)` convention. A sign change in one kernel/lens/mirror term without changing the full convention will produce incorrect focusing.

## Adaptive sampling policy

Each plane plan contains a half-width, sample count, pitch, predicted radii, and diagnostic metadata. The pitch must satisfy all applicable constraints:

- requested samples per predicted beam radius;
- quadratic curvature-phase Nyquist limit;
- Collins-kernel Nyquist limit relative to the opposite plane.

Window sizing:

- Gaussian/super-Gaussian: configured safety factor;
- LG: integrated radial power tail for the exact `(p,l)` intensity, including the guard-band core;
- phase-only Kummer/HyGG-type vortices: extra window margin for their broader diffracted tails;
- positive radial pupil exponent: an input-pupil factor based on the broadened amplitude.

The planner chooses an efficient size up to 2048. At the hard 2048 cap only, a required count up to 2% above the cap may clamp to 2048 to absorb independent safety-margin/rounding overlap. Larger requirements fail explicitly. Configured caps below 2048 are strict.

Before propagation, estimated retained fields, kernels, FFT workspaces, and diagnostics are checked against `max_memory_mb`. A failure raises `WaveOpticsSamplingError`; it must not silently fall back to an undersampled grid.

## Frame diagnostics and quantitative power

The normalized input has unit numerical power. After propagation and mirror-hole clipping:

- `power_fraction` is the remaining numerical power;
- `peak_density_per_mm2` is `max(|U|^2)/integral(|U|^2)` on that frame;
- equivalent radii are `2*sqrt(<x^2>)` and `2*sqrt(<y^2>)`;
- `edge_power_fraction` measures power in the configured real-space border;
- `spectral_edge_fraction` measures spectrum in the Fourier-grid border.

Warnings are emitted when either edge fraction exceeds 0.5%. The display map is interpolated and normalized to a peak of one, so it is visual data only.

The renderer converts peak density from per-mm² to per-cm² with a factor of 100 before multiplying by GW or mJ.

## Known model boundaries

The app does not model:

- nonlinear spectral broadening or self-phase modulation;
- dispersion, absorption, ionization, plasma, or thermal loading;
- mirror coating damage or wavelength-dependent reflectivity;
- vector polarization evolution beyond transporting the transverse basis;
- non-paraxial/vector diffraction;
- aspheric lenses, measured aberrations, lens thickness, or telescope apertures;
- index gradients or nonlinear/complex refractive index;
- coherent interaction between the optional two geometric rays;
- downstream out-coupling lenses (the output section is free space).

The main analytic HG/LG/custom modes use M² envelope propagation. They are not explicit coherent wave fields unless an allowed wave launch profile is calculated.

## Literature used for the vortex conventions

- Karimi et al., “Hypergeometric-Gaussian modes,” *Optics Letters* 32, 3053–3055 (2007), [DOI 10.1364/OL.32.003053](https://doi.org/10.1364/OL.32.003053).
- Augustyniak et al., “Off-axis vortex beam propagation through classical optical system in terms of Kummer confluent hypergeometric function,” [arXiv:2005.05136](https://arxiv.org/abs/2005.05136).
- Liu et al., “Propagation characteristics of super-Gaussian beams with vortex wave-front,” *High Power Laser and Particle Beams* 26 (2014), [DOI 10.11884/HPLPB201426.121015](https://doi.org/10.11884/HPLPB201426.121015).

These references motivate the model; the app's radial pupil exponent is documented explicitly rather than being presented as a universal HyGG index convention.
