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
angle, peak intensity, and peak fluence.

### Center Spots

This plot shows where each traced segment crosses the center plane `z = L/2`.
It is useful for checking focusing or crossing behavior inside the cell.

- Markers are numbered by center-plane crossing order.
- The plot auto-scales to the center-hit extent.
- Hover text reports the same beam and intensity/fluence quantities as the
  mirror plots.

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

This section documents the equations currently implemented in `index.html`.

### Basic Vector Operations

The ray tracer uses standard 3D vector algebra:

$$
\mathbf{a}+\mathbf{b}
=
(a_x+b_x,\ a_y+b_y,\ a_z+b_z)
$$

$$
\mathbf{a}-\mathbf{b}
=
(a_x-b_x,\ a_y-b_y,\ a_z-b_z)
$$

$$
\mathbf{a}\cdot\mathbf{b}
=
a_x b_x + a_y b_y + a_z b_z
$$

$$
\|\mathbf{a}\|=\sqrt{\mathbf{a}\cdot\mathbf{a}}
$$

$$
\hat{\mathbf{a}}={\mathbf{a}\over\|\mathbf{a}\|}
$$

$$
\mathbf{a}\times\mathbf{b}
=
(a_yb_z-a_zb_y,\ a_zb_x-a_xb_z,\ a_xb_y-a_yb_x)
$$

### Target Pattern Angle

The desired angular advance for the pass pattern is:

$$
\theta_{\mathrm{rt}}={2\pi k\over N}
$$

where:

- `N` is the target total pass count.
- `k` is the number of revolutions over those passes.

### Auto Mirror Radius: Concave-Concave

For a concave-concave cell with equal mirror radii, the app computes:

$$
C_{\mathrm{actual}} = 1-\cos\left({\theta_{\mathrm{rt}}\over 2}\right)
$$

$$
R_1=R_2={L\over C_{\mathrm{actual}}}
$$

This is the equal-radius paraxial design used by the auto-ROC control.

### Auto Mirror Radius: Concave-Convex

For the concave-convex mode, the app computes equal-magnitude opposite-sign
radii:

$$
R_1={L\over \sin(\theta_{\mathrm{rt}}/2)}
$$

$$
R_2=-{L\over \sin(\theta_{\mathrm{rt}}/2)}
$$

In the app convention, `R1 > 0` is the concave entrance mirror and `R2 < 0` is
the convex back mirror.

### Stability Parameters

The cavity stability parameters are:

$$
g_1 = 1-{L\over R_1}
$$

$$
g_2 = 1-{L\over R_2}
$$

The stability readout is:

$$
S = g_1 g_2
$$

The app proceeds only when:

$$
0 < g_1 g_2 < 1
$$

### Cavity Eigenmode

The helper term used by the cavity-mode equations is:

$$
G = g_1 + g_2 - 2g_1g_2
$$

If `G` is exactly zero, the JavaScript replaces it with `1e-9` before
evaluating the following expressions.

The cavity Rayleigh range is:

$$
z_R =
\sqrt{
\left|
{L^2 g_1 g_2 (1-g_1g_2)\over G^2}
\right|
}
$$

The waist position from mirror 1 is:

$$
z_0 = {L g_2(1-g_1)\over G}
$$

The fundamental mode waist radius is:

$$
w_0 = \sqrt{{\lambda z_R\over \pi}}
$$

The fundamental eigenmode radii on mirror 1 and mirror 2 are:

$$
w_{m1} =
\sqrt{
\left|
{\lambda L\over\pi}
\sqrt{
{g_2\over g_1(1-g_1g_2)}
}
\right|
}
$$

$$
w_{m2} =
\sqrt{
\left|
{\lambda L\over\pi}
\sqrt{
{g_1\over g_2(1-g_1g_2)}
}
\right|
}
$$

For non-fundamental or custom-`M^2` modes, displayed beam radii are scaled as:

$$
w_x = w \sqrt{M_x^2}
$$

$$
w_y = w \sqrt{M_y^2}
$$

When **Auto Mode-Matched Input** is enabled, the app sets:

$$
w_{0x,\mathrm{in}} = w_0\sqrt{M_x^2}
$$

$$
w_{0y,\mathrm{in}} = w_0\sqrt{M_y^2}
$$

$$
z_{\mathrm{in}} = z_0
$$

### Gaussian Beam ABCD Propagation

For each transverse axis, the input Rayleigh range is:

$$
z_R = {\pi w_{\mathrm{in}}^2\over M^2\lambda}
$$

The initial complex beam parameter at mirror 1 is:

$$
q_0 = -z_{\mathrm{in}} + i z_R
$$

Free-space propagation by distance `d` is:

$$
q(d) = q + d
$$

Reflection by a spherical mirror is represented with:

$$
\begin{bmatrix}
A & B \\
C & D
\end{bmatrix}
=
\begin{bmatrix}
1 & 0 \\
-2/R & 1
\end{bmatrix}
$$

and the ABCD transform is:

$$
q' = {Aq+B\over Cq+D}
$$

The code evaluates this complex division explicitly. For
`q = q_r + i q_i`, it computes:

$$
\mathrm{num}_r = Aq_r + B,\quad \mathrm{num}_i = Aq_i
$$

$$
\mathrm{den}_r = Cq_r + D,\quad \mathrm{den}_i = Cq_i
$$

$$
|\mathrm{den}|^2 = \mathrm{den}_r^2 + \mathrm{den}_i^2
$$

$$
q'_r =
{\mathrm{num}_r\mathrm{den}_r+\mathrm{num}_i\mathrm{den}_i
\over |\mathrm{den}|^2}
$$

$$
q'_i =
{\mathrm{num}_i\mathrm{den}_r-\mathrm{num}_r\mathrm{den}_i
\over |\mathrm{den}|^2}
$$

The beam radius is recovered from:

$$
{1\over q}=U+iV
$$

The code uses:

$$
V = {-q_i\over q_r^2+q_i^2}
$$

and:

$$
w(q) =
\sqrt{
{M^2\lambda\over \pi(-V)}
}
$$

The beam is sampled with 20 substeps per pass for plotting. Mirror beam values
are sampled at pass endpoints, and center-plane values at `L/2`.

The ABCD reflection radius alternates by pass:

$$
R_{\mathrm{pass}} =
\begin{cases}
R_2, & \mathrm{pass}\ \mathrm{even} \\
R_1, & \mathrm{pass}\ \mathrm{odd}
\end{cases}
$$

### Auto Ideal Injection

When auto injection is enabled, the initial position is:

$$
x_{\mathrm{in}} = r_0
$$

$$
y_{\mathrm{in}} = 0
$$

The code uses the following paraxial round-trip matrix elements:

$$
M_{00} = 1-{2L\over R_2}
$$

$$
M_{01} = 2L g_2
$$

It then chooses slopes so the phase-space vector advances by the target pattern
angle:

$$
\theta_x =
{r_0\left[\cos(\theta_{\mathrm{rt}})-M_{00}\right]\over M_{01}}
$$

$$
\theta_y =
{r_0\sin(\theta_{\mathrm{rt}})\over M_{01}}
$$

The UI displays these slopes in mrad:

$$
\theta_{\mathrm{mrad}} = 1000\,\theta_{\mathrm{rad}}
$$

### Mirror Surfaces And Tilts

Mirror tilts are entered as small angles:

$$
\tau_x = 10^{-3}\tau_{x,\mathrm{mrad}}
$$

$$
\tau_y = 10^{-3}\tau_{y,\mathrm{mrad}}
$$

The total tilt magnitude is:

$$
\tau = \sqrt{\tau_x^2+\tau_y^2}
$$

For mirror 1, the spherical center is:

$$
\mathbf{C}_1 =
\left(
|R_1|\sin\tau\,{\tau_x\over\tau},\
|R_1|\sin\tau\,{\tau_y\over\tau},\
R_1\cos\tau
\right)
$$

For mirror 2, the spherical center is:

$$
\mathbf{C}_2 =
\left(
|R_2|\sin\tau\,{\tau_x\over\tau},\
|R_2|\sin\tau\,{\tau_y\over\tau},\
L-R_2\cos\tau
\right)
$$

When `tau` is zero, the transverse center offsets are set to zero to avoid
division by zero.

Each mirror surface satisfies:

$$
\|\mathbf{P}-\mathbf{C}\|^2 = R^2
$$

### Initial Ray Point And Direction

The initial point lies on mirror 1 at the selected transverse input position.
Given:

$$
x_0=x_{\mathrm{in}},\quad y_0=y_{\mathrm{in}}
$$

the discriminant used to find the spherical surface point is:

$$
D_0 = R_1^2-(x_0-C_{1x})^2-(y_0-C_{1y})^2
$$

If `D0 >= 0`, the code uses:

$$
z_0 = C_{1z}-\mathrm{sign}(R_1)\sqrt{D_0}
$$

If `D0 < 0`, it falls back to:

$$
z_0 = 0
$$

The initial point is:

$$
\mathbf{P}_0=(x_0,y_0,z_0)
$$

The input ray direction is:

$$
\mathbf{v}_0 =
{\left(\theta_x,\theta_y,1\right)
\over
\left\|\left(\theta_x,\theta_y,1\right)\right\|}
$$

where `theta_x` and `theta_y` are in radians.

### Profile And Polarization Axes

The code constructs two transverse unit vectors perpendicular to the ray. First,
it projects the lab x-axis perpendicular to the ray:

$$
\mathbf{u}_{1,\mathrm{ref}} =
{\mathbf{e}_x-\mathbf{v}_0(\mathbf{e}_x\cdot\mathbf{v}_0)
\over
\left\|
\mathbf{e}_x-\mathbf{v}_0(\mathbf{e}_x\cdot\mathbf{v}_0)
\right\|}
$$

Then:

$$
\mathbf{u}_{2,\mathrm{ref}} =
{\mathbf{v}_0\times\mathbf{u}_{1,\mathrm{ref}}
\over
\left\|
\mathbf{v}_0\times\mathbf{u}_{1,\mathrm{ref}}
\right\|}
$$

The entered profile/polarization angle `theta_p` rotates these axes:

$$
\mathbf{u}_1 =
\mathbf{u}_{1,\mathrm{ref}}\cos\theta_p
+
\mathbf{u}_{2,\mathrm{ref}}\sin\theta_p
$$

$$
\mathbf{u}_2 =
-\mathbf{u}_{1,\mathrm{ref}}\sin\theta_p
+
\mathbf{u}_{2,\mathrm{ref}}\cos\theta_p
$$

The ray direction and both transverse axes are reflected at each mirror.

### Ray-Sphere Intersection

For a ray:

$$
\mathbf{P}(t)=\mathbf{P}+t\mathbf{v}
$$

and a spherical mirror center `C`, the code sets:

$$
\Delta = \mathbf{P}-\mathbf{C}
$$

$$
b = \mathbf{v}\cdot\Delta
$$

$$
c = \Delta\cdot\Delta - R^2
$$

$$
\Delta_q = b^2-c
$$

If `Delta_q < 0`, there is no mirror intersection. Otherwise:

$$
t_1 = -b-\sqrt{\Delta_q}
$$

$$
t_2 = -b+\sqrt{\Delta_q}
$$

The code chooses the smallest positive `t > 1e-9`. The hit point is:

$$
\mathbf{P}_{\mathrm{hit}}=\mathbf{P}+t\mathbf{v}
$$

The signed surface normal used by the app is:

$$
\mathbf{n}={\mathbf{C}-\mathbf{P}_{\mathrm{hit}}\over R}
$$

### Vector Reflection

The same reflection equation is applied to the ray direction and to the two
profile/polarization axes:

$$
\mathbf{a}' =
\mathbf{a} - 2(\mathbf{a}\cdot\mathbf{n})\mathbf{n}
$$

The reflected vector is normalized after reflection.

### Center-Plane Crossings

For each segment, before the next mirror hit, the center-plane intersection is
tested at:

$$
t_{\mathrm{center}} =
{L/2-P_z\over v_z}
$$

The center point is recorded only when:

$$
0 < t_{\mathrm{center}} < t_{\mathrm{mirror}}
$$

where:

$$
t_{\mathrm{mirror}} =
\|\mathbf{P}_{\mathrm{hit}}-\mathbf{P}\|
$$

### Hole Exit Tests

Input and output holes are circular in the local mirror `x-y` plane.

The input hole is always tied to the current injection coordinates:

$$
\mathbf{h}_{\mathrm{in}}=(x_{\mathrm{in}},y_{\mathrm{in}})
$$

When automatic output-hole placement is enabled, the output hole is:

$$
\mathbf{h}_{\mathrm{out}}=(x_{\mathrm{in}},y_{\mathrm{in}})
$$

on mirror 1.

For a hit point `(x, y)` and hole center `(x_h, y_h)`, the distance is:

$$
d_h = \sqrt{(x-x_h)^2+(y-y_h)^2}
$$

A hit is inside the hole when:

$$
d_h \le r_h
$$

Rules implemented by the trace:

- On mirror 1, the selected output hole is checked if `out_mirror = 1`.
- On mirror 1, the input hole is checked after the first bounce; entering it is
  reported as an input-hole escape.
- On mirror 2, the selected output hole is checked if `out_mirror = 2`.
- The trace stops at the first detected clean exit or escape.

The maximum trace length is:

$$
N_{\mathrm{trace,max}} = \max(150,\ 4N)
$$

### Hermite-Gaussian Mode Equations

The Hermite polynomial recurrence is:

$$
H_0(x)=1
$$

$$
H_1(x)=2x
$$

$$
H_{i+1}(x)=2xH_i(x)-2iH_{i-1}(x)
$$

For the HG mode selected by indices `n` and `m`, the effective beam quality
factors are:

$$
M_x^2 = 2n+1
$$

$$
M_y^2 = 2m+1
$$

For a spot with local coordinates `(l_x, l_y)`, the effective fundamental
radii used by the field calculation are:

$$
w_{0x}={W_x\over\sqrt{M_x^2}}
$$

$$
w_{0y}={W_y\over\sqrt{M_y^2}}
$$

The scaled coordinates are:

$$
s_x={\sqrt{2}l_x\over w_{0x}}
$$

$$
s_y={\sqrt{2}l_y\over w_{0y}}
$$

The common envelope is:

$$
E_{\mathrm{env}} =
\exp\left(
-{l_x^2\over w_{0x}^2}
-{l_y^2\over w_{0y}^2}
\right)
$$

The implemented HG field amplitude is:

$$
E_{\mathrm{HG}} =
H_n(s_x)H_m(s_y)E_{\mathrm{env}}
$$

and the plotted normalized intensity is:

$$
I_{\mathrm{HG,plot}} =
E_{\mathrm{HG}}^2 \cdot \mathrm{norm}
$$

### Laguerre-Gaussian Mode Equations

The associated Laguerre recurrence implemented in the code is:

$$
L_0^l(x)=1
$$

$$
L_1^l(x)=1+l-x
$$

$$
L_{i+1}^l(x)=
{(2i+1+l-x)L_i^l(x)-(i+l)L_{i-1}^l(x)\over i+1}
$$

For the LG mode selected by indices `p` and `l`, the effective beam quality
factors are:

$$
M_x^2 = M_y^2 = 2p+|l|+1
$$

The display calculation uses:

$$
w_0={w_{0x}+w_{0y}\over 2}
$$

$$
r_{\mathrm{sym}}^2 =
{2(l_x^2+l_y^2)\over w_0^2}
$$

The implemented LG amplitude is:

$$
E_{\mathrm{LG}} =
\left(r_{\mathrm{sym}}^2\right)^{|l|/2}
L_p^l\left(r_{\mathrm{sym}}^2\right)
\exp\left(-{l_x^2+l_y^2\over w_0^2}\right)
$$

and the plotted normalized intensity is:

$$
I_{\mathrm{LG,plot}} =
E_{\mathrm{LG}}^2 \cdot \mathrm{norm}
$$

Implementation note: the JavaScript passes the signed `l` value into
`L_p^l(...)` but uses `|l|` in the radial power and `M^2` expression. Many
textbook LG conventions use `|l|` in the associated Laguerre order. This README
documents the implemented code exactly.

### TEM00 And Custom-M2 Intensity Overlay

For TEM00 and custom `M^2`, the plotted intensity is:

$$
I_{\mathrm{plot}} =
\exp\left[
-2\left(
{l_x^2\over w_{0x}^2}
+
{l_y^2\over w_{0y}^2}
\right)
\right]
$$

Custom `M^2` uses:

$$
M_x^2=M_y^2=M_{\mathrm{custom}}^2
$$

### Mode Normalization And Peak Factor

The app samples a square normalized-coordinate grid:

$$
s_x,s_y \in [-4,4]
$$

with step:

$$
\Delta s = 0.1
$$

On this normalization grid, the TEM00 intensity is:

$$
I_{\mathrm{TEM00,norm}} =
\exp[-(s_x^2+s_y^2)]
$$

The HG normalization-grid field and intensity are:

$$
E_{\mathrm{HG,norm}} =
H_n(s_x)H_m(s_y)
\exp\left[-{1\over2}(s_x^2+s_y^2)\right]
$$

$$
I_{\mathrm{HG,norm}} = E_{\mathrm{HG,norm}}^2
$$

The LG normalization-grid radius, field, and intensity are:

$$
r_s^2=s_x^2+s_y^2
$$

$$
E_{\mathrm{LG,norm}} =
(r_s^2)^{|l|/2}L_p^l(r_s^2)
\exp\left[-{1\over2}(s_x^2+s_y^2)\right]
$$

$$
I_{\mathrm{LG,norm}} = E_{\mathrm{LG,norm}}^2
$$

For the selected mode, the code then computes:

$$
I_{\max} = \max(I)
$$

and an approximate integral:

$$
I_{\Sigma} \approx
\sum I(s_x,s_y)(\Delta s)^2
$$

The image-overlay normalization is:

$$
\mathrm{norm} = {1\over I_{\max}}
$$

If `I_max` is not positive, the JavaScript uses:

$$
\mathrm{norm}=1
$$

The peak factor used for intensity and fluence estimates is:

$$
f_{\mathrm{peak}} =
{2I_{\max}\over I_{\Sigma}}
$$

If the maximum cannot be computed, the fallback value is:

$$
f_{\mathrm{peak}} = {2\over\pi}
$$

For a TEM00 Gaussian, this approaches the familiar peak factor
`2/pi`.

### Spot Overlay Coordinates

The generated beam image uses a square of side:

$$
B = 4\max(W_x,W_y)
$$

For image-pixel coordinates `p_x, p_y` in an image with `S` pixels per side:

$$
dX = \left({p_x\over S-1}-{1\over2}\right)B
$$

$$
dY = \left({1\over2}-{p_y\over S-1}\right)B
$$

The local transverse coordinates used by the intensity function are:

$$
l_x = dX\,u_{1x}+dY\,u_{1y}
$$

$$
l_y = dX\,u_{2x}+dY\,u_{2y}
$$

The image alpha is:

$$
\alpha = \min(255,\ \lfloor 255 I_{\mathrm{plot}}\rfloor)
$$

The overlay is therefore a visualization aid, not a diffraction calculation.

### Plot Indexing And Display Formulas

The Gaussian beam plot samples 20 points per pass and displays the first:

$$
N_{\mathrm{plot}} = 20N + 1
$$

samples. The unfolded path range is:

$$
0 \le z \le NL
$$

The ray trace may run longer than the requested plot range when needed for exit
detection. The ABCD propagation pass count is:

$$
N_{\mathrm{ABCD}} =
\max(N,\ N_{\mathrm{bounces}}+1)
$$

The default transverse plot half-width for the 3D and mirror plots is:

$$
x_{\mathrm{lim}}=y_{\mathrm{lim}}=1.5r_0
$$

For the center-plane plot, the app auto-scales to:

$$
x_{\mathrm{lim}}=y_{\mathrm{lim}}=
1.2\max(|x_i|,|y_i|)+2
$$

where the maximum is taken over center-plane hits.

Spot labels are placed radially using:

$$
\phi = \mathrm{atan2}(y,x){180\over\pi}
$$

If `phi < 0`, the app adds `360` degrees, then assigns text positions by
45-degree sectors.

The profile/polarization angle shown in hover text is:

$$
\phi_{\mathrm{pol}} =
\mathrm{atan2}(u_{1y},u_{1x}){180\over\pi}
$$

The displayed value is folded into:

$$
-90^\circ < \phi_{\mathrm{pol}} \le 90^\circ
$$

by adding or subtracting `180` degrees as needed.

Mirror-plot labels use these pass-index formulas:

$$
j_{\mathrm{M1}} = 2i+2
$$

$$
j_{\mathrm{M2}} = 2i+1
$$

$$
j_{\mathrm{center}} = i+1
$$

where `i` is the zero-based hit index in that plotted list.

When image overlays are disabled, each spot is drawn as a circle with radius:

$$
w_{\max}=\max(W_x,W_y)
$$

When image overlays are enabled, the plotted profile/polarization line length
is:

$$
\ell_{\mathrm{pol}}=1.5w_{\max}
$$

### Peak Intensity And Fluence Estimates

For each plotted spot, the area factor is:

$$
A_{\mathrm{factor}} = W_x W_y
$$

where `W_x` and `W_y` are in `mm`.

The peak intensity displayed in hover text and plot titles is:

$$
I_{\mathrm{peak}} =
100\,{P_{\mathrm{GW}} f_{\mathrm{peak}}\over W_xW_y}
\quad [\mathrm{GW/cm^2}]
$$

The factor `100` converts from per `mm^2` to per `cm^2`.

The peak fluence displayed in hover text and plot titles is:

$$
F_{\mathrm{peak}} =
100\,{E_{\mathrm{mJ}} f_{\mathrm{peak}}\over W_xW_y}
\quad [\mathrm{mJ/cm^2}]
$$

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
