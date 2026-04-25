# Herriott Cell Configurator

Browser-based design and inspection tool for Herriott and multipass cells.
The app combines:

- 3D geometric ray tracing on spherical mirrors
- fast paraxial ABCD beam propagation for live interaction
- transverse-mode beam overlays and intensity / fluence estimates
- an explicit adaptive-grid 2D wave-optics solver for MPC mirror-to-focus-to-mirror propagation

The repository is split into a small frontend and a FastAPI backend. The fast
ABCD path updates continuously while you edit inputs. The more expensive 2D
wave-optics path runs only when you click the dedicated button, reports real
progress, and shows an ETA while the solver loop is running.

## What The App Does

- Designs concave-concave and concave-convex multipass cells
- Auto-computes mirror radii from mirror spacing, pass count, and revolution count
- Auto-computes a nominal injection ray for rotating dense spot patterns
- Traces the injected ray in 3D using exact sphere intersections and vector reflection
- Computes cavity stability, cavity waist, and mirror beam sizes
- Displays TEM00, HG, LG, and custom `M^2` analytic beam overlays
- Estimates peak intensity and fluence on mirror and center/focus plots
- Runs an adaptive-grid 2D scalar diffraction solver for selected MPC segments
- Supports `gaussian`, `super_gaussian`, and `round_super_gaussian` launch profiles
- Saves and loads JSON configurations

## Quick Start

### Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn backend.app.main:app --reload
```

Open `http://127.0.0.1:8000/`.

### Docker

```bash
docker compose up
```

Open `http://localhost:3003/`.

## Repository Layout

```text
backend/
  app/
    api/        FastAPI routes
    core/       optics, ray tracing, simulation, wave optics
    schemas/    Pydantic request/response models
    services/   simulation orchestration and wave-optics jobs
frontend/
  index.html    main UI shell
  styles.css    app styles
  js/
    api-client.js
    form-state.js
    main.js
    renderers.js
    simulation-reference.js
    wave-optics-state.js
tests/
  fixtures/
  ...
scripts/
  profile_backend.py
```

## Runtime Architecture

### Fast Path

The live UI uses `POST /api/simulate`.

That path is implemented mainly in:

- `backend/app/core/simulation.py`
- `backend/app/core/optics.py`
- `backend/app/core/ray_tracing.py`
- `backend/app/core/modes.py`

It is responsible for:

- geometry resolution
- cavity stability checks
- mode selection and `M^2` handling
- auto mode matching
- auto injection
- 3D ray tracing
- unfolded ABCD beam propagation

### Wave-Optics Path

The explicit 2D solver is implemented in:

- `backend/app/core/wave_optics.py`
- `backend/app/services/simulation_service.py`
- `backend/app/api/routes/simulation.py`

The UI integration is implemented in:

- `frontend/js/main.js`
- `frontend/js/wave-optics-state.js`
- `frontend/js/renderers.js`

This path:

- runs only when the user clicks **Calculate Wave-Optics Beam Profiles**
- starts a backend job instead of blocking the UI
- polls live backend progress
- shows actual loop progress and estimated remaining time
- marks the 2D result stale after relevant input changes
- renders wave-optics profiles on the MPC center plane and mirror planes when fresh
- falls back to the fast analytic overlays when the 2D result is stale or unavailable

## Wave-Optics Implementation

The optional wave-optics feature uses an adaptive-grid 2D Collins/Fresnel
scalar diffraction solver that follows the paraxial ABCD beam envelope. When a
segment has a real internal ABCD minimum, it uses:

`mirror n -> internal focus / waist plane -> mirror n+1`

For monotonic segments with no internal focus, such as the supported `cav-vex`
case, it uses direct scaled mirror-to-mirror propagation instead of fabricating
a focus plane near one mirror.

In both cases, the solver also samples the propagated field at the MPC center
plane halfway between the mirrors. The UI center panel displays these center
plane profiles, while real internal focus profiles remain available as
diagnostics for split-focus segments.

Key implementation points:

- The field is propagated as a full complex 2D field, not only as Gaussian beam parameters.
- Separate transverse windows are chosen for the start mirror, any real internal focus plane, and the end mirror.
- A separate transverse window is also chosen for the MPC center plane at `L/2`.
- ABCD-predicted beam size and curvature are used to plan those windows and sample spacings.
- The window shrinks near a real focus and expands again toward the next mirror; direct segments scale between the two mirror windows.
- Real-space sampling, curvature sampling, and kernel Nyquist limits are enforced explicitly.
- Configurations that exceed the configured grid or memory limits raise a clear error instead of silently aliasing.
- Mirror curvature is applied as thin-mirror phase.
- Mirror-hole clipping is applied where the current paraxial model already supports it.

Supported launch profiles:

- `gaussian`
- `super_gaussian`
- `round_super_gaussian`

Current limitations:

- The 2D solver is scalar and paraxial, not a full vector or non-paraxial field solver.
- Higher-order HG and LG modes remain part of the analytic overlay path rather than the explicit 2D launch-profile path.
- The internal adaptive focus plane is chosen from the shared minimum-area ABCD estimate when the x and y minima do not occur at the same longitudinal position. If that minimum lies on a mirror, the segment is treated as a no-focus direct propagation.

## API Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Serves the frontend |
| `GET` | `/health` | Simple health check |
| `POST` | `/api/simulate` | Fast live simulation |
| `POST` | `/api/simulate-wave-optics` | Synchronous wave-optics simulation |
| `POST` | `/api/simulate-wave-optics/jobs` | Starts a background wave-optics job |
| `GET` | `/api/simulate-wave-optics/jobs/{job_id}` | Polls wave-optics job progress, ETA, and final result |

The browser UI uses the job-based wave-optics API so it can show real progress.
The synchronous wave-optics endpoint remains available for direct API use and tests.

## Main Frontend Behavior

- Live input edits re-run only the fast analytic simulation.
- The wave-optics solver is never live-updated while parameters are still changing.
- When a fresh 2D result exists, the mirror/focus plots use the wave-optics profiles.
- When any relevant input changes, the 2D result becomes stale and the plots fall back to the analytic beam overlays.
- The wave-optics status card shows whether the 2D result is fresh, stale, failed, or currently running.

## Core Simulation Model

This repository currently models:

- spherical-mirror Herriott / MPC geometry
- exact 3D geometric ray tracing between the two mirrors
- cavity stability and eigenmode estimates
- unfolded Gaussian beam propagation with ABCD matrices
- optional adaptive-grid scalar diffraction between successive MPC mirror bounces

This repository does not currently model:

- nonlinear spectral broadening
- self-phase modulation
- material dispersion
- ionization or plasma effects
- thermal loading
- absorption spectroscopy response
- mirror coating damage models
- non-paraxial vector propagation

## Units And Conventions

- Distances, beam radii, and mirror radii are in `mm`.
- Wavelength is entered in `nm` and converted internally to `mm`.
- Ray and tilt angles are entered in `mrad` and converted internally to `rad`.
- Peak power is in `GW`.
- Pulse energy is in `mJ`.
- Intensity is reported in `GW/cm^2`.
- Fluence is reported in `mJ/cm^2`.

Radius-of-curvature convention used by the app:

- In `cav-cav`, both mirror radii are positive.
- In `cav-vex`, mirror 1 is positive concave and mirror 2 is negative convex.

Plotting convention:

- Internal Cartesian coordinates use `P = [x, y, z]`.
- Mirror 1 is near `z = 0`.
- Mirror 2 is near `z = L`.
- The 3D Plotly figure maps internal coordinates as `plot x = z`, `plot y = x`, `plot z = y`.

## Development

Run the test suite:

```bash
pytest
```

Profile the backend:

```bash
python scripts/profile_backend.py --iterations 100
```

Useful files when extending the app:

- `backend/app/core/simulation.py` for the fast optics path
- `backend/app/core/wave_optics.py` for adaptive 2D propagation
- `backend/app/schemas/simulation.py` for API contracts
- `frontend/js/main.js` for UI orchestration and wave-optics polling
- `frontend/js/renderers.js` for Plotly rendering
- `tests/test_api.py` for endpoint coverage
- `tests/test_wave_optics.py` for wave-optics numerical checks

## Validation Coverage

The test suite includes checks for:

- API parity with the simulation service
- invalid request handling
- wave-optics sampling-limit errors
- Gaussian wave-optics propagation against the existing ABCD reference
- mirror -> focus -> mirror propagation
- super-Gaussian and round super-Gaussian launch profiles
- adaptive window shrink / expand behavior
- frontend stale-state behavior
- frontend progress markup

## Literature Basis

The implementation is motivated by Herriott-style and MPC design literature,
including:

- Hariton et al., "Spectral broadening in convex-concave multipass cells," *Optics Express* 31, no. 12 (2023), DOI: [10.1364/OE.486797](https://doi.org/10.1364/OE.486797)
- Ma et al., "Design of multipass cell with dense spot patterns and its performance in a light-induced thermoelastic spectroscopy-based methane sensor," *Light: Advanced Manufacturing* 6, no. 1 (2025), DOI: [10.37188/lam.2025.001](https://doi.org/10.37188/lam.2025.001)
- Viotti et al., "Multi-pass cells for post-compression of ultrashort laser pulses," *Optica* 9, no. 2 (2022), DOI: [10.1364/OPTICA.449225](https://doi.org/10.1364/OPTICA.449225)

Those papers motivate the geometry and use cases. This repository implements a
practical design tool, not a full reproduction of every model in the cited work.
