# Herriott Cell Configurator

Browser-based Herriott/multipass-cell design tool for exploring dense spot
patterns, mirror geometry, paraxial beam evolution, transverse modes, and
mirror/center-plane fluence and intensity estimates.

The application is contained in `index.html`. It has no backend and performs
all calculations in JavaScript in the browser.

## Quick Start

### Open directly

Because the app is a static HTML file, you can open `index.html` directly in a
browser. An internet connection is needed for the CDN versions of Tailwind CSS
and Plotly.

### Run with Docker

```bash
docker compose up
```

Then open:

```text
http://localhost:3001
```

## What The Web App Can Do

The configurator can:

- Design a two-spherical-mirror Herriott-style multipass cell.
- Switch between concave-concave and concave-convex mirror geometries.
- Auto-calculate radii of curvature for a desired pass count and pattern
  revolution number.
- Auto-calculate an ideal paraxial injection ray that generates a rotating
  dense spot pattern.
- Trace the injected ray in 3D using exact intersections with spherical mirror
  surfaces and vector reflection.
- Show the spots on mirror 1, the cavity center plane, and mirror 2.
- Place input and output holes and detect whether the traced ray exits through
  the selected output aperture or escapes through the input aperture.
- Propagate a Gaussian beam envelope with ABCD matrices over the unfolded path.
- Estimate cavity eigenmode waist and mirror beam radii.
- Display TEM00, Hermite-Gaussian, Laguerre-Gaussian, or custom `M^2` beam
  overlays.
- Estimate peak intensity in `GW/cm^2` and peak fluence in `mJ/cm^2` at the
  plotted spots.
- Save and load configurations as JSON files.

The app is a geometry and paraxial beam-design tool. It does not simulate
nonlinear spectral broadening, material dispersion, self-phase modulation,
B-integral, gas ionization, thermal effects, absorption spectroscopy, or LITES
sensor response.

## Literature Basis

The code and interface are motivated by Herriott-type multipass-cell design
work for post-compression, convex/concave multipass-cell layouts, and dense spot
patterns:

- Victor Hariton, Kilian Fritsch, Kevin Schwarz, Nazar Kovalenko, Goncalo
  Figueira, Gunnar Arisholm, and Oleg Pronin, "Spectral broadening in
  convex-concave multipass cells," *Optics Express* 31, no. 12 (2023):
  19554-19568. DOI: [10.1364/OE.486797](https://doi.org/10.1364/OE.486797).
- Yufei Ma, Yahui Liu, Ying He, Shunda Qiao, and Haiyue Sun, "Design of
  multipass cell with dense spot patterns and its performance in a
  light-induced thermoelastic spectroscopy-based methane sensor," *Light:
  Advanced Manufacturing* 6, no. 1 (2025): 5-13. DOI:
  [10.37188/lam.2025.001](https://doi.org/10.37188/lam.2025.001).
- Anne-Lise Viotti, Marcus Seidel, Esmerando Escoto, Supriya Rajhans, Wim P.
  Leemans, Ingmar Hartl, and Christoph M. Heyl, "Multi-pass cells for
  post-compression of ultrashort laser pulses," *Optica* 9, no. 2 (2022):
  197-216. DOI:
  [10.1364/OPTICA.449225](https://doi.org/10.1364/OPTICA.449225).

Relationship to the cited papers:

- Ma et al. motivate the dense-spot-pattern ray-tracing workflow and the use of
  vector reflection to design multipass-cell geometries.
- Hariton et al. motivate the concave-convex multipass-cell use case and the
  practical readouts of mirror radii, cell length, eigenmode beam sizes, peak
  intensity, and fluence.
- Viotti et al. provide the broader post-compression context for Herriott-type
  multipass cells with ultrashort laser pulses.

The JavaScript implementation is intentionally narrower than those papers: it
implements geometric ray tracing, Gaussian/ABCD propagation, transverse-mode
visualization, and peak intensity/fluence estimates only.

## Coordinate System, Units, And Sign Conventions

The JavaScript uses the internal Cartesian point format:

```text
P = [x, y, z]
```

where:

- `z = 0` is the entrance mirror, mirror 1.
- `z = L` is the back mirror, mirror 2.
- `x` and `y` are transverse coordinates in millimeters.
- Plotly's 3D plot maps internal coordinates as `plot x = z`,
  `plot y = x`, and `plot z = y`.

Primary units:

| Quantity | UI unit | Internal unit |
| --- | --- | --- |
| Distances, beam radii, mirror ROC | mm | mm |
| Wavelength | nm | mm, using `lambda_mm = lambda_nm * 1e-6` |
| Input/output ray angles | mrad | rad, using `angle_rad = angle_mrad * 1e-3` |
| Mirror tilts | mrad | rad |
| Peak power | GW | GW |
| Pulse energy | mJ | mJ |
| Intensity | GW/cm^2 | GW/cm^2 |
| Fluence | mJ/cm^2 | mJ/cm^2 |

Radius-of-curvature sign convention:

- In the concave-concave mode, both radii are positive in the app.
- In the concave-convex mode, mirror 1 is positive concave and mirror 2 is
  negative convex.
- The code's sign convention may differ from individual papers or optical
  design programs. Use the app's labels and readouts as the source of truth
  for this implementation.

## How To Use The App

1. Choose the basic cell geometry in **Cell Design**.
2. Set **Mirror Distance (L)**, **Total Passes (N)**, and **Revolutions (k)**.
3. Leave **Auto-calc Mirror ROC** enabled for a first design pass, or disable it
   to enter radii manually.
4. Leave **Auto Ideal Injection** enabled to generate the nominal rotating spot
   pattern, or disable it to manually steer the input ray.
5. Inspect **Ray Trace Status**. A useful closed configuration usually exits
   through the selected output hole rather than escaping through the input hole
   or remaining trapped until the trace limit.
6. Inspect the spot plots. Look for spot overlap, hole clipping, and whether the
   output spot reaches the chosen output aperture.
7. Open **Transversal Mode & Beam** to change the beam mode and mode-matching
   assumptions.
8. Use **Peak Power**, **Pulse Energy**, and the beam settings to inspect
   estimated intensity and fluence ranges on each plotted surface.
9. Use **Set Standard** to make the current values the in-session reset point,
   **Reset** to return to that point, **Save File** to export JSON, and
   **Load File** to restore JSON later.

For dense closed patterns, choose `N` and `k` so that they are relatively prime.
If they share a common divisor, the pattern can repeat early and use fewer
distinct spot positions.

## Input Parameters

### Cell Design

| Control | Meaning |
| --- | --- |
| `Mirror Distance (L)` | Separation between mirror vertices, in mm. One pass in the unfolded Gaussian plot has length `L`. |
| `Total Passes (N)` | Target number of mirror-to-mirror passes used for auto geometry and the plotted unfolded path range. The 3D trace may stop earlier if the ray exits or escapes. |
| `Revolutions (k)` | Number of full spot-pattern revolutions over `N` passes. The target angular advance is `theta_rt = 2*pi*k/N`. |
| `Cavity Geometry` | Selects concave-concave (`cav-cav`) or concave-convex (`cav-vex`) geometry. |
| `Auto-calc Mirror ROC (R)` | For concave-concave cells, computes one shared positive radius from `L`, `N`, and `k`. |
| `Mirror Radius (R)` | Manual concave-concave radius when auto ROC is disabled. |
| `Auto-calc Ideal |R1|=|R2|` | For concave-convex cells, computes equal-magnitude opposite-sign radii from `L`, `N`, and `k`. |
| `M1 Concave (R1)` | Manual mirror-1 radius in mm when concave-convex auto ROC is disabled. Positive values are concave in the app convention. |
| `M2 Convex (R2)` | Manual mirror-2 radius in mm when concave-convex auto ROC is disabled. Negative values are convex in the app convention. |
| `Spot Pattern (r0)` | Initial input-hole radial position and nominal pattern radius in mm. It also sets the default transverse viewing range. |
| `Output Hole / Auto` | When enabled, places the output hole at the input-hole coordinates on mirror 1. |
| `Output Hole / Mirror` | Manual output-hole mirror: mirror 1 or mirror 2. |
| `Output Hole / X, Y` | Manual output-hole center coordinates in mm. |
| `Hole Aperture (r_h)` | Radius of input/output apertures in mm. The ray exits when the hit point is inside the selected output hole. |
| `Peak Power (P)` | Peak pulse power used for spot intensity estimates, in GW. |
| `Pulse Energy (E)` | Pulse energy used for spot fluence estimates, in mJ. |
| `Wavelength (lambda)` | Optical wavelength in nm. Internally converted to mm for Gaussian beam equations. |

### Transversal Mode & Beam

| Control | Meaning |
| --- | --- |
| `Render Beam Profile Overlays` | Shows generated intensity images under each spot and projected polarization/profile-axis lines. When disabled, spots use simple radius circles. |
| `Transversal Mode` | Selects TEM00, Hermite-Gaussian, Laguerre-Gaussian, or custom `M^2`. |
| `HG Index n` | Horizontal Hermite-Gaussian order. The app uses `M_x^2 = 2n + 1`. |
| `HG Index m` | Vertical Hermite-Gaussian order. The app uses `M_y^2 = 2m + 1`. |
| `LG Index p` | Radial Laguerre-Gaussian order. |
| `LG Index l` | Azimuthal Laguerre-Gaussian order. The app uses `M_x^2 = M_y^2 = 2p + |l| + 1`. |
| `Custom M^2 Factor` | User-defined equal beam-quality factor for `x` and `y`. |
| `Effective M^2 (x, y)` | Readout of the active `M_x^2` and `M_y^2`. |
| `Auto Mode-Matched Input` | Sets the input waist radii and waist position from the cavity eigenmode equations. |
| `Waist X (w0x)` | Manual input waist radius in the x plane, in mm, when auto mode matching is disabled. |
| `Waist Y (w0y)` | Manual input waist radius in the y plane, in mm, when auto mode matching is disabled. |
| `Waist Pos (z0)` | Distance from mirror 1 to the beam waist, in mm. Positive values place the waist inside the cell. |
| `Pol. Angle (theta_p)` | Rotation angle of the initial transverse profile/polarization axes in degrees. This affects the overlay orientation and the projected polarization lines. |

### Input Ray Steering

| Control | Meaning |
| --- | --- |
| `Auto Ideal Injection` | Computes input ray position and slopes that produce the nominal rotating paraxial spot pattern. |
| `X, Y` | Manual input-hole and initial ray coordinates on mirror 1, in mm. |
| `theta_x, theta_y` | Manual input ray slopes in mrad. Internally converted to radians and normalized into a 3D direction vector. |

### Mirror Pointing

| Control | Meaning |
| --- | --- |
| `Mirror 1 Tilt X, Y` | Tilts mirror 1 by shifting the spherical center according to the entered mrad pointing angles. |
| `Mirror 2 Tilt X, Y` | Tilts mirror 2 by shifting the spherical center according to the entered mrad pointing angles. |

The ray trace uses tilted spherical surfaces. The Gaussian ABCD beam propagation
does not include the mirror tilts; it remains a paraxial unfolded-axis estimate.

### Buttons

| Button | Meaning |
| --- | --- |
| `Set Standard` | Stores the current values as the in-memory reset target for this page session. |
| `Reset` | Restores the current in-memory standard configuration. |
| `Save File` | Downloads the current configuration as `herriott_config.json`. |
| `Load File` | Loads a previously saved JSON configuration. |

## Readouts And Plots

### Calculated Properties

| Readout | Meaning |
| --- | --- |
| `Stability (g1g2)` | Product of the two cavity stability parameters. The app requires `0 < g1*g2 < 1`. |
| `Cavity Waist (w0)` | Mode-matched waist radius readout in mm. For non-TEM00 modes, the displayed x/y values are scaled by `sqrt(M_x^2)` and `sqrt(M_y^2)`. |
| `Mirror Beams (w1, w2)` | Eigenmode beam radii on the mirrors. For symmetric mirror beams it reports x/y values; for unequal mirror beams it reports M1/M2 using the x-axis `M^2` scaling. |
| `Ray Trace Status` | Reports whether the ray exited through the output hole, escaped through the input hole, left the spherical mirror geometry, hit a stability error, or remained trapped until the trace limit. |

### Gaussian Beam Evolution Plot

This plot shows the paraxial beam radius along the unfolded path.

- Horizontal axis: unfolded path distance `z` in mm.
- Vertical axis: beam radius `w` in mm.
- Magenta solid envelope: `+/- w_x`.
- Cyan dotted envelope: `+/- w_y`.
- Shaded regions: filled beam-radius envelopes.
- Vertical dashed lines: mirror encounters at multiples of `L`.

The Gaussian plot uses ABCD propagation and the entered or mode-matched beam
parameters. It is not the same as the exact 3D geometric ray path; it is a
paraxial beam-size estimate along the unfolded path.

### 3D Cavity Ray Path

This plot shows the geometric ray traced between the spherical mirrors.

- Green marker: starting point on mirror 1.
- Red marker: final traced point.
- Colored line: ray path, colored by point order.
- Axes: longitudinal `Z Axis [mm]` plus transverse `X [mm]` and `Y [mm]`.

The 3D path uses exact sphere intersections and vector reflection. It does not
draw mirror surfaces or mirror apertures.

### Mirror 1 Spots

This plot shows spot coordinates on mirror 1 near `z = 0`.

- Green dotted circle: input hole.
- Red circle: output hole if the selected output mirror is mirror 1.
- `In` marker: initial injected spot.
- Numbered markers: mirror-1 return hits. The numbering matches the pass index
  used by the unfolded path.
- `Out` label: clean output-hole exit, when detected on the final plotted hit.
- Beam image overlays: normalized transverse intensity profiles, if enabled.
- Black line overlay: projected profile/polarization axis.

Hover text includes spot number, `X`, `Y`, `w_x`, `w_y`, profile/polarization
angle, the incidence angle relative to the local mirror normal, incoming and
reflected steering angles in the `theta_x/theta_y` frame, peak intensity, and
peak fluence.

### Center Spots

This plot shows where each traced segment crosses the center plane `z = L/2`.
It is useful for checking focusing or crossing behavior inside the cell.

- Markers are numbered by center-plane crossing order.
- The plot auto-scales to the center-hit extent.
- Hover text reports the same beam and intensity/fluence quantities as the
  mirror plots, excluding the mirror-only incidence and steering-angle fields.

### Mirror 2 Spots

This plot shows spot coordinates on mirror 2 near `z = L`.

- Red circle: output hole if the selected output mirror is mirror 2.
- Numbered markers: mirror-2 hits. The numbering matches the unfolded pass
  index, so the first mirror-2 hit is pass 1.
- Beam overlays and hover text follow the same conventions as mirror 1.

### Intensity And Fluence In Plot Titles

Each 2D spot plot title includes the minimum and maximum peak fluence and peak
intensity among the hits shown in that plot:

```text
Fluence: min - max mJ/cm^2 | Intensity: min - max GW/cm^2
```

These are peak values estimated from the local beam radii and selected
transverse mode. They do not include losses, nonlinear propagation, pulse-front
effects, temporal profile changes, aperture diffraction, or mirror damage
models.

## Physics And Equations Implemented In JavaScript

This section documents the equations currently implemented in `index.html`. The
formulas are written in plain ASCII inside code blocks so they render reliably
on GitHub without relying on LaTeX support.

### Basic Vector Operations

The ray tracer uses standard 3D vector algebra. For vectors
`a = (a_x, a_y, a_z)` and `b = (b_x, b_y, b_z)`:

```text
a + b = (a_x + b_x, a_y + b_y, a_z + b_z)
```

```text
a - b = (a_x - b_x, a_y - b_y, a_z - b_z)
```

```text
a . b = a_x*b_x + a_y*b_y + a_z*b_z
```

```text
||a|| = sqrt(a . a)
```

```text
normalize(a) = a / ||a||
```

```text
a x b = (
  a_y*b_z - a_z*b_y,
  a_z*b_x - a_x*b_z,
  a_x*b_y - a_y*b_x
)
```

### Target Pattern Angle

The desired angular advance for the pass pattern is:

```text
theta_rt = 2*pi*k/N
```

where `N` is the target total pass count and `k` is the number of revolutions
over those passes.

### Auto Mirror Radius: Concave-Concave

For a concave-concave cell with equal mirror radii, the app computes:

```text
C_actual = 1 - cos(theta_rt/2)
R1 = R2 = L/C_actual
```

This is the equal-radius paraxial design used by the auto-ROC control.

### Auto Mirror Radius: Concave-Convex

For the concave-convex mode, the app computes equal-magnitude opposite-sign
radii:

```text
R1 =  L/sin(theta_rt/2)
R2 = -L/sin(theta_rt/2)
```

In the app convention, `R1 > 0` is the concave entrance mirror and `R2 < 0` is
the convex back mirror.

### Stability Parameters

The cavity stability parameters are:

```text
g1 = 1 - L/R1
g2 = 1 - L/R2
```

The stability readout is:

```text
S = g1*g2
```

The app proceeds only when:

```text
0 < g1*g2 < 1
```

### Cavity Eigenmode

The helper term used by the cavity-mode equations is:

```text
G = g1 + g2 - 2*g1*g2
```

If `G` is exactly zero, the JavaScript replaces it with `1e-9` before
evaluating the following expressions.

The cavity Rayleigh range is:

```text
zR_cavity = sqrt(abs((L^2*g1*g2*(1 - g1*g2)) / G^2))
```

The waist position from mirror 1 is:

```text
z0_cavity = L*g2*(1 - g1)/G
```

The fundamental mode waist radius is:

```text
w0_ideal = sqrt(lambda*zR_cavity/pi)
```

The fundamental eigenmode radii on mirror 1 and mirror 2 are:

```text
wm1_ideal = sqrt(abs((lambda*L/pi) * sqrt(g2/(g1*(1 - g1*g2)))))
wm2_ideal = sqrt(abs((lambda*L/pi) * sqrt(g1/(g2*(1 - g1*g2)))))
```

For non-fundamental or custom-`M^2` modes, displayed beam radii are scaled as:

```text
w_x = w*sqrt(M2x)
w_y = w*sqrt(M2y)
```

When **Auto Mode-Matched Input** is enabled, the app sets:

```text
w_in_x = w0_ideal*sqrt(M2x)
w_in_y = w0_ideal*sqrt(M2y)
z_in   = z0_cavity
```

### Gaussian Beam ABCD Propagation

For each transverse axis, the input Rayleigh range is:

```text
z_R = pi*w_in^2/(M2*lambda)
```

The initial complex beam parameter at mirror 1 is:

```text
q0 = -z_in + i*z_R
```

Free-space propagation by distance `d` is:

```text
q(d) = q + d
```

Reflection by a spherical mirror is represented by the ABCD matrix:

```text
[ A  B ]   [ 1    0 ]
[ C  D ] = [ -2/R 1 ]
```

The ABCD transform is:

```text
q' = (A*q + B)/(C*q + D)
```

The code evaluates this complex division explicitly. For `q = q_r + i*q_i`:

```text
num_r = A*q_r + B
num_i = A*q_i

den_r = C*q_r + D
den_i = C*q_i

den_mag2 = den_r^2 + den_i^2

q'_r = (num_r*den_r + num_i*den_i)/den_mag2
q'_i = (num_i*den_r - num_r*den_i)/den_mag2
```

The beam radius is recovered from `1/q = U + i*V`. The code uses:

```text
V = -q_i/(q_r^2 + q_i^2)
w(q) = sqrt((M2*lambda)/(pi*(-V)))
```

The beam is sampled with 20 substeps per pass for plotting. Mirror beam values
are sampled at pass endpoints, and center-plane values at `L/2`.

The ABCD reflection radius alternates by pass:

```text
if pass is even: current_R = R2
if pass is odd:  current_R = R1
```

### Auto Ideal Injection

When auto injection is enabled, the initial position is:

```text
x_in = r0
y_in = 0
```

The code uses these paraxial round-trip matrix elements:

```text
M_arrive_00 = 1 - 2*L/R2
M_arrive_01 = 2*L*g2
```

It then chooses slopes so the phase-space vector advances by the target pattern
angle:

```text
theta_x = r0*(cos(theta_rt) - M_arrive_00)/M_arrive_01
theta_y = r0*sin(theta_rt)/M_arrive_01
```

The UI displays these slopes in mrad:

```text
theta_mrad = 1000*theta_rad
```

### Mirror Surfaces And Tilts

Mirror tilts are entered as small angles:

```text
tau_x = 1e-3*tilt_x_mrad
tau_y = 1e-3*tilt_y_mrad
```

The total tilt magnitude is:

```text
tau = sqrt(tau_x^2 + tau_y^2)
```

For mirror 1, the spherical center is:

```text
C1 = (
  abs(R1)*sin(tau)*(tau_x/tau),
  abs(R1)*sin(tau)*(tau_y/tau),
  R1*cos(tau)
)
```

For mirror 2, the spherical center is:

```text
C2 = (
  abs(R2)*sin(tau)*(tau_x/tau),
  abs(R2)*sin(tau)*(tau_y/tau),
  L - R2*cos(tau)
)
```

When `tau` is zero, the transverse center offsets are set to zero to avoid
division by zero.

Each mirror surface satisfies:

```text
||P - C||^2 = R^2
```

### Initial Ray Point And Direction

The initial point lies on mirror 1 at the selected transverse input position.
Given:

```text
x0 = x_in
y0 = y_in
```

the discriminant used to find the spherical surface point is:

```text
disc_p0 = R1^2 - (x0 - C1_x)^2 - (y0 - C1_y)^2
```

If `disc_p0 >= 0`, the code uses:

```text
z0_init = C1_z - sign(R1)*sqrt(disc_p0)
```

If `disc_p0 < 0`, it falls back to:

```text
z0_init = 0
```

The initial point is:

```text
P0 = (x0, y0, z0_init)
```

The input ray direction is:

```text
v0 = normalize((theta_x, theta_y, 1))
```

where `theta_x` and `theta_y` are in radians.

### Profile And Polarization Axes

The code constructs two transverse unit vectors perpendicular to the ray. First,
it projects the lab x-axis perpendicular to the ray:

```text
u1_ref = normalize(e_x - v0*(e_x . v0))
```

Then:

```text
u2_ref = normalize(v0 x u1_ref)
```

The entered profile/polarization angle `theta_p` rotates these axes:

```text
u1 =  u1_ref*cos(theta_p) + u2_ref*sin(theta_p)
u2 = -u1_ref*sin(theta_p) + u2_ref*cos(theta_p)
```

The ray direction and both transverse axes are reflected at each mirror.

### Ray-Sphere Intersection

For a ray:

```text
P(t) = P + t*v
```

and a spherical mirror center `C`, the code sets:

```text
Delta = P - C
b = v . Delta
c = Delta . Delta - R^2
discriminant = b^2 - c
```

If `discriminant < 0`, there is no mirror intersection. Otherwise:

```text
t1 = -b - sqrt(discriminant)
t2 = -b + sqrt(discriminant)
```

The code chooses the smallest positive `t > 1e-9`. The hit point is:

```text
P_hit = P + t*v
```

The signed surface normal used by the app is:

```text
normal = (C - P_hit)/R
```

### Vector Reflection

The same reflection equation is applied to the ray direction and to the two
profile/polarization axes:

```text
a_reflected = a - 2*(a . normal)*normal
```

The reflected vector is normalized after reflection.

### Center-Plane Crossings

For each segment, before the next mirror hit, the center-plane intersection is
tested at:

```text
t_center = (L/2 - P_z)/v_z
```

The center point is recorded only when:

```text
0 < t_center < t_mirror
```

where:

```text
t_mirror = ||P_hit - P||
```

### Hole Exit Tests

Input and output holes are circular in the local mirror `x-y` plane. The input
hole is always tied to the current injection coordinates:

```text
h_in = (x_in, y_in)
```

When automatic output-hole placement is enabled, the output hole is on mirror 1
at:

```text
h_out = (x_in, y_in)
```

For a hit point `(x, y)` and hole center `(x_h, y_h)`, the distance is:

```text
d_h = sqrt((x - x_h)^2 + (y - y_h)^2)
```

A hit is inside the hole when:

```text
d_h <= r_h
```

Rules implemented by the trace:

- On mirror 1, the selected output hole is checked if `out_mirror = 1`.
- On mirror 1, the input hole is checked after the first bounce; entering it is
  reported as an input-hole escape.
- On mirror 2, the selected output hole is checked if `out_mirror = 2`.
- The trace stops at the first detected clean exit or escape.

The maximum trace length is:

```text
N_trace_max = max(150, 4*N)
```

### Hermite-Gaussian Mode Equations

The Hermite polynomial recurrence is:

```text
H_0(x) = 1
H_1(x) = 2*x
H_{i+1}(x) = 2*x*H_i(x) - 2*i*H_{i-1}(x)
```

For the HG mode selected by indices `n` and `m`, the effective beam quality
factors are:

```text
M2x = 2*n + 1
M2y = 2*m + 1
```

For a spot with local coordinates `(l_x, l_y)`, the effective fundamental radii
used by the field calculation are:

```text
w0x = W_x/sqrt(M2x)
w0y = W_y/sqrt(M2y)
```

The scaled coordinates are:

```text
s_x = sqrt(2)*l_x/w0x
s_y = sqrt(2)*l_y/w0y
```

The common envelope is:

```text
E_env = exp(-(l_x^2)/(w0x^2) - (l_y^2)/(w0y^2))
```

The implemented HG field amplitude is:

```text
E_HG = H_n(s_x)*H_m(s_y)*E_env
```

and the plotted normalized intensity is:

```text
I_HG_plot = E_HG^2*norm
```

### Laguerre-Gaussian Mode Equations

The associated Laguerre recurrence implemented in the code is:

```text
L_0^l(x) = 1
L_1^l(x) = 1 + l - x
L_{i+1}^l(x) = ((2*i + 1 + l - x)*L_i^l(x) - (i + l)*L_{i-1}^l(x))/(i + 1)
```

For the LG mode selected by indices `p` and `l`, the effective beam quality
factors are:

```text
M2x = M2y = 2*p + abs(l) + 1
```

The display calculation uses:

```text
w0 = (w0x + w0y)/2
r2_sym = 2*(l_x^2 + l_y^2)/(w0^2)
```

The implemented LG amplitude is:

```text
E_LG = (r2_sym)^(abs(l)/2) * L_p^l(r2_sym) * exp(-(l_x^2 + l_y^2)/(w0^2))
```

and the plotted normalized intensity is:

```text
I_LG_plot = E_LG^2*norm
```

Implementation note: the JavaScript passes the signed `l` value into
`L_p^l(...)` but uses `abs(l)` in the radial power and `M^2` expression. Many
textbook LG conventions use `abs(l)` in the associated Laguerre order. This
README documents the implemented code exactly.

### TEM00 And Custom-M2 Intensity Overlay

For TEM00 and custom `M^2`, the plotted intensity is:

```text
I_plot = exp(-2*((l_x^2)/(w0x^2) + (l_y^2)/(w0y^2)))
```

Custom `M^2` uses:

```text
M2x = M2y = M2_custom
```

### Mode Normalization And Peak Factor

The app samples a square normalized-coordinate grid:

```text
s_x, s_y in [-4, 4]
ds = 0.1
```

On this normalization grid, the TEM00 intensity is:

```text
I_TEM00_norm = exp(-(s_x^2 + s_y^2))
```

The HG normalization-grid field and intensity are:

```text
E_HG_norm = H_n(s_x)*H_m(s_y)*exp(-0.5*(s_x^2 + s_y^2))
I_HG_norm = E_HG_norm^2
```

The LG normalization-grid radius, field, and intensity are:

```text
r2 = s_x^2 + s_y^2
E_LG_norm = (r2)^(abs(l)/2)*L_p^l(r2)*exp(-0.5*(s_x^2 + s_y^2))
I_LG_norm = E_LG_norm^2
```

For the selected mode, the code then computes:

```text
I_max = max(I)
I_sum = sum(I(s_x, s_y))*ds^2
```

The image-overlay normalization is:

```text
norm = 1/I_max
```

If `I_max` is not positive, the JavaScript uses:

```text
norm = 1
```

The peak factor used for intensity and fluence estimates is:

```text
f_peak = 2*I_max/I_sum
```

If the maximum cannot be computed, the fallback value is:

```text
f_peak = 2/pi
```

For a TEM00 Gaussian, this approaches the familiar peak factor `2/pi`.

### Spot Overlay Coordinates

The generated beam image uses a square of side:

```text
B = 4*max(W_x, W_y)
```

For image-pixel coordinates `p_x, p_y` in an image with `S` pixels per side:

```text
dX = (p_x/(S - 1) - 0.5)*B
dY = (0.5 - p_y/(S - 1))*B
```

The local transverse coordinates used by the intensity function are:

```text
l_x = dX*u1_x + dY*u1_y
l_y = dX*u2_x + dY*u2_y
```

The image alpha is:

```text
alpha = min(255, floor(255*I_plot))
```

The overlay is therefore a visualization aid, not a diffraction calculation.

### Plot Indexing And Display Formulas

The Gaussian beam plot samples 20 points per pass and displays the first:

```text
N_plot = 20*N + 1
```

samples. The unfolded path range is:

```text
0 <= z <= N*L
```

The ray trace may run longer than the requested plot range when needed for exit
detection. The ABCD propagation pass count is:

```text
N_ABCD = max(N, N_bounces + 1)
```

The default transverse plot half-width for the 3D and mirror plots is:

```text
x_lim = y_lim = 1.5*r0
```

For the center-plane plot, the app auto-scales to:

```text
x_lim = y_lim = 1.2*max(abs(x_i), abs(y_i)) + 2
```

where the maximum is taken over center-plane hits.

Spot labels are placed radially using:

```text
phi = atan2(y, x)*180/pi
```

If `phi < 0`, the app adds `360` degrees, then assigns text positions by
45-degree sectors.

The profile/polarization angle shown in hover text is:

```text
phi_pol = atan2(u1_y, u1_x)*180/pi
```

The displayed value is folded into:

```text
-90 deg < phi_pol <= 90 deg
```

by adding or subtracting `180` degrees as needed.

For mirror hits, the incidence angle shown in hover text is measured relative to
the local surface normal:

```text
theta_inc = acos(abs(v_in . normal))*180/pi
```

The incoming/reflected steering values shown in hover text use the same
parameterization as the input-ray steering controls:

```text
theta_x = 1000*v_x/v_z   [mrad]
theta_y = 1000*v_y/v_z   [mrad]
```

When a plotted hit exits through an input or output hole, the reflected
steering angle pair is reported as unavailable because no reflected cavity
segment exists after that point.

Mirror-plot labels use these pass-index formulas:

```text
j_M1     = 2*i + 2
j_M2     = 2*i + 1
j_center = i + 1
```

where `i` is the zero-based hit index in that plotted list.

When image overlays are disabled, each spot is drawn as a circle with radius:

```text
w_max = max(W_x, W_y)
```

When image overlays are enabled, the plotted profile/polarization line length
is:

```text
ell_pol = 1.5*w_max
```

### Peak Intensity And Fluence Estimates

For each plotted spot, the area factor is:

```text
A_factor = W_x*W_y
```

where `W_x` and `W_y` are in `mm`.

The peak intensity displayed in hover text and plot titles is:

```text
I_peak = 100*(P_GW*f_peak)/(W_x*W_y)   [GW/cm^2]
```

The factor `100` converts from per `mm^2` to per `cm^2`.

The peak fluence displayed in hover text and plot titles is:

```text
F_peak = 100*(E_mJ*f_peak)/(W_x*W_y)   [mJ/cm^2]
```

Losses, mirror reflectivity, aperture diffraction, material nonlinearities, and
temporal pulse shape are not included.

## Configuration Files

`Save File` writes a JSON object containing numeric controls and UI toggles. The
saved keys include:

```text
L, n, k, R, R1, R2, r0, hole_r, out_hole_x, out_hole_y,
lambda, M2, peak_power, pulse_energy,
hgn, hgm, lgp, lgl,
winx, winy, zin, polang,
x, y, thx, thy,
m1tx, m1ty, m2tx, m2ty,
cellType, autoR, autoRVex, autoOutHole, outMirror,
autoModeMatch, autoInjection, modeType, showBeamProfiles
```

`Load File` applies any matching keys from a saved configuration and then reruns
the simulation.

## Modeling Assumptions And Limitations

- Mirrors are ideal spherical surfaces.
- Mirror finite clear aperture is not modeled.
- Input and output holes are circular tests in the mirror `x-y` plane.
- Ray intersections use exact 3D sphere geometry, but Gaussian propagation is a
  paraxial ABCD model along an unfolded axis.
- Mirror tilts affect ray tracing but not the ABCD beam envelope.
- Beam overlays are normalized transverse intensity drawings, not propagated
  field solutions.
- HG and LG modes are represented for visualization and `M^2` scaling; no
  phase, Gouy phase, interference, or mode beating is simulated.
- Peak intensity and fluence use local beam radii and selected transverse-mode
  peak factors only.
- Nonlinear pulse propagation, spectral broadening, dispersion compensation,
  B-integral, self-focusing, gas/material ionization, thermal lensing,
  absorption spectroscopy, and LITES sensor response are outside the current
  model.
