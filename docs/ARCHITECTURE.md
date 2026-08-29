# Architecture and Data Flow

This document explains how the running application is assembled and where state and calculations live. For equations and sign conventions, see [PHYSICS.md](PHYSICS.md). For change checklists, see [EXTENDING.md](EXTENDING.md).

## Runtime overview

```text
Browser DOM
  │
  ├─ fast input change ──> form-state.js ──> POST /api/simulate
  │                                             │
  │                                             └─ simulation.py
  │                                                ├─ geometry/stability
  │                                                ├─ mode matching
  │                                                ├─ exact ray tracing
  │                                                └─ ABCD/external traces
  │
  └─ explicit wave button ─> POST /api/simulate-wave-optics/jobs
                                 │
                                 └─ single background worker
                                    ├─ reruns the fast simulation
                                    └─ wave_optics.py
                                       ├─ input pupil
                                       ├─ three-lens telescope
                                       └─ adaptive intracell propagation

API response ──> main.js state/readouts ──> renderers.js ──> Plotly
```

The fast result is always authoritative for geometry, ray hits, resolved inputs, and analytic beam envelopes. A completed wave result is an additional payload tied to the exact optical request signature that generated it.

## Backend layers

### Application and routes

`backend/app/main.py`:

- constructs the FastAPI app;
- mounts the `frontend/` directory at `/static`;
- serves `frontend/index.html` at `/`;
- translates Pydantic validation, sampling, and unexpected errors into JSON envelopes;
- provides `/health`.

`backend/app/api/routes/simulation.py` deliberately contains no physics. It validates requests through Pydantic and calls the service layer.

### Contracts and validation

`backend/app/schemas/simulation.py` is the external API contract. It defines:

- `SimulationRequest`: all fast-path geometry, mode, telescope, ray, power, and plotting inputs;
- `WaveOpticsSettings`: the explicit field profile and sampling limits;
- `WaveOpticsSimulationRequest`: `SimulationRequest` plus `wave_optics`;
- all nested response models;
- validation and legacy migration for the concave-convex radius selector.

The models use `extra="forbid"` and reject NaN/infinity. Bounds here are authoritative even if HTML controls use different slider ranges.

Important validation performed after field parsing includes:

- singular automatic-radius combinations;
- valid signs for manual concave-convex radii;
- valid calculated R2 for fixed-R1 mode;
- coprime N/k for nonzero automatic injection patterns;
- nonzero telescope focal lengths.

### Fast simulation service

`run_simulation()` calls `simulate_configuration()` and validates the result back through `SimulationResponse`. The round-trip validation is intentional: backend dictionaries cannot silently drift away from the public response schema.

`simulate_configuration()` runs in this order:

1. Resolve mirror radii from cell type and radius mode.
2. Calculate g factors and reject unstable cells early.
3. Construct mode metadata (`M2x`, `M2y`, normalization, peak factor).
4. Calculate the cavity eigenmode and target q at M1.
5. Resolve the three-lens telescope.
6. Use the telescope's achieved x/y q at M1 to derive the live analytic launch.
7. Resolve automatic or manual injection/output holes.
8. Trace the primary ray and optional second ray through exact mirror surfaces.
9. Propagate q through the actual traced number of legs.
10. Build the upstream telescope and downstream free-space sections.
11. Return the complete response dictionary for Pydantic validation.

An unstable response intentionally has `cavity`, ray, beam, matching, and external sections set to `None`.

### Core module ownership

| Module | Owns | Does not own |
| --- | --- | --- |
| `simulation.py` | pipeline, resolved geometry, cavity formulas, response assembly | detailed telescope optimization or FFT propagation |
| `mode_matching.py` | q transforms, practical three-lens optimization, external sampling | ray geometry |
| `ray_tracing.py` | exact sphere intersections, reflection, holes, local bases | Gaussian diffraction |
| `optics.py` | sampled intracell ABCD/q envelope | high-order complex fields |
| `modes.py` | analytic mode M2, normalization, peak-density factors | explicit 2D wave propagation |
| `wave_optics.py` | field generation, telescope FFT, adaptive cell grids, diagnostics | HTTP/job management |
| `math_utils.py` | dependency-free 3D vector helpers | optical policy |

## Mode-matching architecture

The mode-matching plane is a collimated input plane upstream of three thin lenses:

```text
input / phase plate --d0--> L1 --d12--> L2 --d23--> L3 --d3m--> M1 | cell
```

The three modes are:

| Mode | User controls | Optimizer controls |
| --- | --- | --- |
| `auto` | collimated input radius | catalog f1/f2/f3 and d12/d23/d3m; d0 is the practical fixed plate distance |
| `fixed_lenses` | input radius and f1/f2/f3 | d12/d23/d3m; d0 remains the requested value |
| `manual` | all focal lengths and distances | nothing |

The automatic catalog and search bounds are constants in `mode_matching.py`. Optimization is deterministic, cached by optical target, and reports a normalized q error. A mismatch is not fatal: `success` and `message` tell the UI whether it is a match or closest fit, while all propagation uses the achieved q.

The public response removes internal complex objects but reports target and achieved air-q real/imaginary components for diagnostics.

## Wave-optics job architecture

There are synchronous and queued endpoints:

| Endpoint | Use |
| --- | --- |
| `POST /api/simulate-wave-optics` | tests, scripts, direct synchronous clients |
| `POST /api/simulate-wave-optics/jobs` | browser UI; returns a job immediately |
| `GET /api/simulate-wave-optics/jobs/{id}` | polling progress/result |

The job manager in `simulation_service.py` has one worker thread so simultaneous large NumPy calculations do not multiply memory demand. Jobs are stored in process memory. It retains at most 24 terminal jobs and has no persistence, cancellation endpoint, authentication, or cross-process coordination.

The progress callback is emitted by the actual wave loop. `main.js` polls every 180 ms and displays completed steps, percent, current segment, elapsed time, and an estimated remaining time.

## Wave result structure

`WaveOpticsResult` contains:

- `input_profile`: complex-field summary at the collimated pupil/plate plane;
- `launch_profile`: summary at M1 before the first cell leg;
- mirror, center, and optional focus frames;
- per-segment grid/radius/warning diagnostics;
- union of propagation backends actually used;
- deduplicated real-space and spectral guard-band warnings;
- the effective settings used.

Frames carry geometry (`position`, `u1`, `u2`) from the exact ray trace so 2D local profiles can be placed correctly on the 3D/mirror plots.

`intensity_map` is a normalized, downsampled display image. Quantitative power and peak-density data are separate fields; never infer absolute power from pixels.

## Frontend architecture

The frontend is native ES modules plus Plotly and Tailwind loaded by `frontend/index.html`. There is no bundler.

### Field registry and configuration

`form-state.js` is the bridge between DOM controls and API snake_case fields:

- `NUMERIC_FIELDS` maps paired range/number inputs;
- `LEGACY_TOGGLE_FIELDS` maps checkboxes/selects and old config keys;
- `WAVE_OPTICS_FIELDS` maps the explicit wave settings;
- `captureConfig()` builds the fast form state;
- `buildSimulationRequest()` removes display-only fields;
- `buildWaveOpticsRequest()` attaches the wave settings;
- `applyConfig()` and `applyLegacyConfig()` load JSON;
- `applyResolvedInputs()` and `applyModeMatchingResult()` put auto-calculated values back into visible controls.

The “Set Standard” button changes an in-memory reset point only. “Save Config” downloads a JSON file. There is no database or browser-storage persistence.

### Main state machine

`main.js` maintains two independent request paths:

- Fast simulations are debounced by 40 ms. A new request aborts the previous fetch.
- Wave optics runs only on button press. The current job is polled until completed or failed.

`wave-optics-state.js` stores the result with a stable serialization of the propagation request. Any optical input change marks it stale. `peak_power_gw` and `pulse_energy_mj` are excluded from the signature because they only scale intensity/fluence readouts.

When a result is stale, failed, missing, or unsupported, plots fall back to analytic profiles. Stale wave data must never be presented as current.

### Rendering boundaries

`renderers.js` owns all Plotly conversion and display-only mode evaluation:

- Gaussian/unfolded plot: intracell ABCD envelope plus external telescope/output sections and element markers;
- 3D ray plot: cell ray points only;
- mirror and center plots: ray locations with analytic or fresh wave profiles;
- hover readouts: beam radius, polarization, incidence data, intensity/fluence, and wave sampling diagnostics.

The renderer uses `simulation-reference.js` for analytic HG/LG display functions and small vector helpers. It must not become a second implementation of the backend simulation.

### Digit-at-caret behavior

`digit-stepper.js` converts every `input[type=number]` into a text-based ARIA spinbutton after page initialization. Arrow keys, focused wheel events, and hardware knobs that emit those events increment the caret-selected decimal place. Arithmetic uses `BigInt` scaled integers to avoid binary floating-point stepping errors and naturally carries/borrows between digits.

## API errors

Errors have an `error` object with a stable code/message. Validation errors additionally contain `details` with a Pydantic location, message, and type. `api-client.js` maps important field names to readable labels and prefers the specific first detail over the generic “Request validation failed” summary.

Wave sampling errors use HTTP 400. Schema validation uses HTTP 422. Unexpected exceptions use HTTP 500.

## Legacy compatibility

- Older camelCase configuration files are recognized in `applyLegacyConfig()`.
- Missing refractive index defaults to 1.0 when loading browser JSON.
- `auto_opposite_radii` is migrated to the three-state `opposite_radius_mode` by the Pydantic validator.
- Legacy direct-at-M1 waist/injection fields remain accepted so saved files are not rejected. The telescope is now the source of the launch q.
- `tests/reference/run_js_simulation.mjs` runs the old JavaScript simulator to protect unaffected geometry/ray behavior. Tests deliberately exclude fields superseded by the telescope where parity is no longer meaningful.

## Deployment

FastAPI serves both the API and assets from one origin. This is assumed by relative URLs in `api-client.js`.

- Local: Uvicorn on port 8000.
- Docker: container port 8000, host port 3001 in `docker-compose.yml`.
- Root `index.html`: explanatory placeholder only.
- GitHub Pages static branch: unrelated legacy app; no FastAPI and no automatic feature parity.

For multi-user or public deployment, the first architectural pressure points are the in-memory job manager, lack of job cancellation/quotas, 1 GiB default wave memory allowance, absence of authentication, and single-process state.
