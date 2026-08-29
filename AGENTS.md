# Herriott Cell Configurator: Agent Guide

This file is the first stop for any coding agent or maintainer working in this repository. Read it before changing code, then follow the links under **Detailed documentation** for the part of the system you are modifying.

## Project in one paragraph

The project is a browser UI backed by FastAPI. The fast path calculates MPC geometry, exact spherical-mirror ray tracing, Gaussian/q-parameter propagation, a practical three-lens input telescope, and an output free-space section. The explicit wave-optics path builds a complex field at an upstream collimated input/phase-plate plane, propagates it through the telescope, then through every traced intracell leg on adaptive transverse grids. Plotly renders the results. The root `index.html` is only a placeholder; the real UI is `frontend/index.html` and requires the Python backend.

## Read these next

- [Architecture and data flow](docs/ARCHITECTURE.md)
- [Physics and numerical conventions](docs/PHYSICS.md)
- [Extension and verification guide](docs/EXTENDING.md)
- [User-facing overview and deployment](README.md)

If documentation and code disagree, use this priority order and update the stale documentation in the same change:

1. Pydantic contracts in `backend/app/schemas/simulation.py`
2. Backend calculation code under `backend/app/core/`
3. Frontend request construction in `frontend/js/form-state.js`
4. Renderers and prose documentation

## Non-negotiable invariants

Preserve these unless a feature explicitly changes the underlying physical model and the tests/documentation are updated with it.

- `total_passes` means round trips and spots per mirror. A nominal configuration has `2 * total_passes` mirror-to-mirror legs.
- Lengths and beam radii are millimetres. Vacuum wavelength is entered in nanometres and converted to millimetres.
- Intracell diffraction uses `lambda_medium = lambda_vacuum / refractive_index`; external telescope propagation uses the vacuum wavelength.
- At the planar air/cell boundary, the physical transverse field is continuous and `q_cell = n * q_air` for the q convention used here.
- Mirror 1 is the entrance mirror. `cav-cav` radii are positive. In `cav-vex`, R1 is positive and R2 is negative.
- Beam radius `w` is the 1/e field-amplitude, 1/e^2 intensity radius. Wave frames report the equivalent radius `2 * sqrt(<x^2>)` or `2 * sqrt(<y^2>)`.
- A telescope mismatch must remain visible. Launch the cell with the achieved telescope q, never silently replace it with the ideal target q.
- Ray tracing uses exact sphere intersections. Do not insert the external telescope into the 3D cavity ray path or mirror-spot plots unless the product requirement explicitly changes.
- The Gaussian-beam/unfolded-path plot may show external sections: green upstream mode matching and orange downstream out-coupling.
- Explicit wave optics is available only when the main analytic mode is TEM00. The independent wave launch profile may still be Gaussian, super-Gaussian, round super-Gaussian, or LG.
- A phase-only spiral plate is `exp(i*l*phi)` and has no independent radial phase index. In this app, phase-plate `p=0` is phase-only; `p>0` additionally applies `(sqrt(2)*r/w)^p` as an amplitude mask and therefore represents a complex pupil shaper.
- LG `p` is a radial-node index. Pupil-shaper `p` is a non-negative radial amplitude exponent. They are not interchangeable.
- Never reduce wave-optics grids or suppress diagnostics merely to make a request finish. Sampling failures must be explicit.
- The hard wave-grid cap is 2048 samples per axis. Grids through 640 use dense Collins transforms; larger grids use the scaled-FFT/Bluestein path.
- `simulation-reference.js` is a legacy JavaScript reference and analytic display helper. Production physics comes from the backend.

## Repository map

```text
backend/app/main.py                       FastAPI app, static mount, error envelopes
backend/app/api/routes/simulation.py      HTTP endpoints
backend/app/services/simulation_service.py Fast and queued wave-optics orchestration
backend/app/schemas/simulation.py         Request/response contracts and validation
backend/app/core/simulation.py            Top-level fast simulation pipeline
backend/app/core/mode_matching.py         q optics and three-lens design
backend/app/core/ray_tracing.py           Exact spherical ray tracing
backend/app/core/optics.py                Intracell ABCD sampling
backend/app/core/modes.py                 TEM/HG/LG/custom M2 metadata and normalization
backend/app/core/wave_optics.py           Complex-field generation, grids, propagation

frontend/index.html                       Actual application markup
frontend/js/form-state.js                 DOM-field registry, requests, save/load, UI modes
frontend/js/main.js                       Live simulation and wave-job lifecycle
frontend/js/api-client.js                 Fetch/error handling
frontend/js/wave-optics-state.js          Fresh/stale wave-result signatures
frontend/js/renderers.js                  Plotly plots and profile overlays
frontend/js/digit-stepper.js              Digit-at-caret keyboard/wheel control
frontend/js/simulation-reference.js       Legacy reference/display math, not backend source

tests/fixtures/configs/                   Reusable request fixtures
tests/reference/run_js_simulation.mjs     Legacy parity runner
tests/test_simulation_core.py              Fast physics and mode-matching regression tests
tests/test_wave_optics.py                  Numerical propagation and sampling tests
tests/test_api.py                          API/error/job tests
tests/test_frontend_wave_optics_state.py   Frontend contracts executed with Node
tests/test_digit_stepper.py                Caret-place stepping tests
```

## Safe change workflow

1. Inspect `git status --short`. Preserve unrelated user changes.
2. Read the applicable detailed document and the complete source functions you will modify.
3. Treat `SimulationRequest`, `WaveOpticsSettings`, and response models as the API source of truth.
4. Make backend physics changes before renderer changes. Do not reproduce backend calculations in the browser.
5. If a request field changes, update every layer listed in [EXTENDING.md](docs/EXTENDING.md#adding-or-changing-a-request-field).
6. Add focused numerical tests, including a failure/limit case when relevant.
7. Run the complete verification commands below.
8. Update README/user prose when behavior changes and these maintainer documents when an invariant or extension path changes.

## Required verification

From the repository root with the development environment installed:

```bash
.venv/bin/python -m compileall -q backend
for file in frontend/js/*.js; do node --check "$file"; done
.venv/bin/pytest -q
git diff --check
```

For UI changes, also start the app and exercise the affected controls in a real browser when browser automation or manual access is available:

```bash
.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

At minimum, a live smoke check should cover `GET /health`, `POST /api/simulate`, and one short `POST /api/simulate-wave-optics` request.

## Cross-layer traps

- Adding markup alone does not send a value. Register main numeric fields in `NUMERIC_FIELDS`, toggles/selects in `LEGACY_TOGGLE_FIELDS`, and wave settings in `WAVE_OPTICS_FIELDS`.
- Every numeric input is converted to a text spinbutton by `digit-stepper.js`. Preserve its `min`, `max`, and initial decimal spelling; those determine caret stepping and ARIA bounds.
- `applyModeMatchingResult()` writes calculated lenses/distances back into the DOM. Auto/fixed modes therefore expose the actual resolved design to save/load and subsequent mode changes.
- Fast inputs invalidate a prior wave result through the serialized request signature. Power and pulse energy are intentionally excluded because they scale display readouts without changing propagation.
- Wave jobs are in-memory, single-worker, and non-persistent. A server restart loses them. This is suitable for the current single-user tool, not a distributed deployment.
- The wave solver follows the number of successfully traced ray legs, not blindly `2N`. The output Gaussian section starts at the actual traced exit leg.
- The mode-matching optimizer is deterministic and cached. Do not introduce uncontrolled randomness into results.
- Automatic telescope selection uses the positive standard focal-length catalog in `mode_matching.py`. Fixed/manual modes accept any non-zero focal length, including negative values.
- Legacy saved configuration keys are migrated in `form-state.js` and the schema validator. The hidden direct-at-M1 waist controls are accepted for compatibility, but the current launch is produced by the telescope.
- Validation uses `extra="forbid"`. A field mismatch between frontend and schema produces HTTP 422. Add a readable field label in `api-client.js` for new user-facing inputs.

## Deployment reality

- Local/Docker production path: FastAPI serves `frontend/index.html` and `/static/*`, and the UI calls `/api/*` on the same origin.
- Docker maps host port 3001 to container port 8000.
- GitHub Pages cannot run the FastAPI or NumPy wave solver. The branch `index.html-only-with-wave-propagation-(slow)` is a separate legacy static implementation and is not synchronized with `main`.
- Do not claim that the Pages version contains a feature implemented only on `main`.

## When work is complete

Report:

- the behavior implemented or diagnosed;
- the physics convention chosen when multiple conventions exist;
- verification commands and numerical cases run;
- any sampling warnings or performance limits encountered;
- whether browser UI testing was actually performed;
- whether changes are merely local, committed, pushed, or deployed.
