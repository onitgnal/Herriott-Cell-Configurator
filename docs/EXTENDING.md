# Extension and Verification Guide

Use this guide when implementing a feature. It enumerates the cross-layer work that is easy to miss in this repository.

## Before editing

1. Read [AGENTS.md](../AGENTS.md), [ARCHITECTURE.md](ARCHITECTURE.md), and the applicable section of [PHYSICS.md](PHYSICS.md).
2. Run `git status --short` and preserve unrelated work.
3. Identify whether the request changes:
   - a fast simulation input/result;
   - a wave-only setting/result;
   - saved configuration compatibility;
   - plots only;
   - deployment/runtime behavior.
4. Read the complete functions around the change. `wave_optics.py` has tightly coupled planning, propagation, and diagnostics; changing one in isolation is risky.
5. Define the physical convention explicitly before coding when literature uses overloaded symbols such as `p`, `l`, pass, waist, or radius.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Node is used only for frontend syntax/contract tests. The production frontend has no npm build.

Run the app with:

```bash
.venv/bin/uvicorn backend.app.main:app --reload
```

Open `http://127.0.0.1:8000/`. Tailwind and Plotly currently load from public CDNs, so a completely offline browser will not render the normal styled plots unless those dependencies are already cached or vendored in a future change.

## Adding or changing a request field

### Fast simulation field

Update all applicable locations:

1. `SimulationRequest` in `backend/app/schemas/simulation.py`
   - choose the exact type, default, bounds, and literal values;
   - extend `validate_optical_geometry()` for coupled constraints;
   - decide whether old saved files need a `mode="before"` migration.
2. The backend consumer, normally `backend/app/core/simulation.py` or `mode_matching.py`.
3. A response model if the resolved or calculated value must return to the UI.
4. `frontend/index.html`
   - paired numeric controls use `num-<domId>` and `param-<domId>`;
   - retain meaningful `min`, `max`, `step`, and decimal spelling;
   - give the user units and a concise physical explanation.
5. `NUMERIC_FIELDS` or `LEGACY_TOGGLE_FIELDS` in `frontend/js/form-state.js`.
6. UI visibility/disabled-state functions if the field is conditional.
7. `applyResolvedInputs()` if the backend overwrites an automatic value.
8. `frontend/js/api-client.js` field labels so 422 errors name the control.
9. Save/load behavior. Registry fields are saved automatically; renamed fields may need a legacy key.
10. Tests:
    - schema/API validation;
    - a physics result assertion;
    - a frontend markup/request-capture assertion.
11. Documentation if the field changes a convention, workflow, limit, or deployment contract.

Do not add a browser-side default that disagrees with Pydantic. A minimal API request may use the schema default even when no browser is involved.

### Wave-only setting

Update:

1. `WaveOpticsSettings` bounds/defaults.
2. `WaveOpticsResult` if the selected value is returned explicitly.
3. `WAVE_OPTICS_FIELDS` in `form-state.js`.
4. HTML control and conditional UI logic in `updateWaveOpticsUI()`.
5. Field generation, grid planning, propagation, and/or output assembly in `wave_optics.py`.
6. Sampling/memory behavior for minimum, ordinary, and maximum values.
7. `api-client.js` validation label.
8. `tests/test_wave_optics.py`, `tests/test_api.py`, and the Node frontend contract tests.

Wave settings are automatically included in the stale-result signature. If a new setting is display-only, explicitly exclude it in `buildWaveOpticsSignature()` and test that decision.

## Adding a launch profile

This is a full-stack and numerical change. Complete every step:

1. Add the literal to both `WaveOpticsSettings.profile_type` and `WaveOpticsResult.profile_type`.
2. Add the dropdown option and any conditional controls to `frontend/index.html`.
3. Register new settings and update `updateWaveOpticsUI()`.
4. Implement the normalized complex field in `AdaptiveWaveOpticsSolver.build_launch_field()`.
5. Define its radius convention in `PHYSICS.md` and UI prose.
6. Update `_launch_profile_grid_factors()` and `_input_pupil_window_factor()` using the actual radial tail and smallest feature scale. A correct field on an undersized grid is still an incorrect simulation.
7. Decide whether it uses explicit angular-spectrum telescope propagation or has a mathematically exact first-order transform like ideal LG.
8. Include profile metadata in the result.
9. Confirm renderer behavior. The display map path is generic, but labels/status and control visibility may not be.
10. Test:
    - input-plane amplitude and phase separately;
    - signed azimuthal phase if relevant;
    - power normalization;
    - propagation through the telescope;
    - expected symmetry/central null/radius;
    - maximum supported indices and sampling-limit errors;
    - a non-default refractive index if wavelength handling matters.

Never infer a high-order grid margin only from M². Ring modes and phase-only vortices with the same second moment can have very different tail and spectral requirements.

## Changing mode matching

`mode_matching.py` is intentionally independent from the ray tracer and FFT solver. Preserve this separation.

When changing the telescope:

- use complex q and the vacuum wavelength externally;
- preserve the planar `q_cell=n*q_air` conversion;
- calculate both x/y axes even when the ordinary case is symmetric;
- keep optimization deterministic and bounded;
- report the achieved solution and error;
- launch analytic and explicit wave paths with the same achieved q;
- update external plot samples and lens positions;
- test auto, fixed-lens, manual, unequal M², negative manual focal length, and `n != 1` cases.

If adding thick lenses or media between lenses, the current `thin_lens_q` and common-air assumptions must be replaced by an explicit ABCD element sequence. Do not hide a thick-lens correction inside an effective distance without documenting it.

## Changing cell geometry or ray tracing

1. Extend schema literals and validate radius signs/singularities.
2. Resolve new geometry in `simulation.py` before stability/cavity calculations.
3. Update `HerriottCell` intersections and surface normals.
4. Preserve local basis transport and hole coordinates.
5. Confirm the ray response still contains all geometry required by wave frames.
6. Revisit cavity formulas; do not reuse two-spherical-mirror expressions for an unsupported geometry.
7. Update 3D/mirror renderers only after the backend geometry is correct.
8. Add a fixture and test exact hit count, exit status, centers, normals, and known symmetric limits.

`max_trace_passes = max(150, 4*total_passes)` is a safety cap, not the requested optical length. Do not use it as a nominal round-trip count.

## Changing adaptive wave propagation

Changes here must preserve four separate concerns:

1. q-based plane prediction;
2. window size/tail containment;
3. real-space, curvature, and kernel sampling;
4. memory-safe execution backend.

For each change, test both dense and scaled-FFT propagation. The existing equivalence test should remain near numerical precision for a grid that both algorithms can evaluate.

Do not:

- raise the 2048 hard cap without measuring actual workspace memory and runtime;
- treat `max_grid_points` as a request to reset or coarsen the physics;
- catch `WaveOpticsSamplingError` and return an analytic result as if it were explicit propagation;
- remove edge/spectral warnings to make a test green;
- use a display-grid map for subsequent propagation;
- apply a mirror phase at the initial M1 launch or after the final exiting leg.

High-order maximum-index regression tests should use a short, stable cell when the purpose is to verify field generation/planner support. Full default-cell propagation is a separate performance test and can require large memory and tens of seconds.

## Changing plots or UI state

Keep the rendering responsibilities distinct:

- external telescope/output traces belong only in the Gaussian/unfolded plot;
- exact ray data drives 3D and spot locations;
- fresh wave frames replace analytic profile images, not ray positions;
- stale wave frames must fall back visibly to analytic profiles;
- power/energy edits may reuse propagation but must refresh quantitative readouts.

For a new numeric input, test digit-at-caret behavior indirectly by preserving the number/range registry pattern and directly when adding special formatting. The digit stepper changes `type=number` to `type=text` at runtime, so code must not depend on native number-input APIs after initialization.

If adding Plotly interactions, ensure input wheel handlers only capture wheel events while a numeric spinbutton is focused. Plot wheel/zoom interactions must remain available.

## Adding an API endpoint or background operation

Keep route handlers thin. Put orchestration in `services/` and calculations in `core/`.

For a job endpoint, define:

- request/response schemas;
- stable status and error codes;
- progress meaning and terminal states;
- memory/concurrency policy;
- cleanup/retention;
- restart behavior;
- frontend abort/poll behavior;
- API tests for success, failure, missing ID, and validation.

The current wave-job manager is single-process and single-worker. Do not present it as durable queue infrastructure.

## Saved configuration compatibility

Configuration downloads use current snake_case request fields plus `wave_optics`. Older browser files may contain camelCase keys.

When renaming/removing a field:

1. Decide whether old files should preserve behavior or only remain loadable.
2. Add migration in `applyLegacyConfig()` and, for API clients, a Pydantic `mode="before"` validator.
3. Keep schema `extra="forbid"`; explicit migration is safer than silently ignoring typos.
4. Add a fixture or direct migration test.
5. Document any behavior that cannot be preserved, such as legacy direct-at-M1 launch values superseded by the telescope.

## Test map

| Change | Minimum relevant tests |
| --- | --- |
| schema/default/validation | `tests/test_api.py`, direct Pydantic test |
| cavity/radius/ray physics | `tests/test_simulation_core.py`, fixture parity if applicable |
| mode matching/q boundary | `tests/test_simulation_core.py` with auto/fixed/manual and index case |
| wave field/profile | `tests/test_wave_optics.py` field-level and propagated case |
| grid/backend | dense/scaled equivalence, high-order planner, limit and memory error |
| frontend control/request | `tests/test_frontend_wave_optics_state.py` Node script/markup contract |
| digit stepping | `tests/test_digit_stepper.py` |
| endpoint/job/error | `tests/test_api.py` |
| deployment/static path | live Uvicorn smoke test |

Reference fixtures live under `tests/fixtures/configs/`. Prefer a focused new test over changing an existing fixture unless the fixture itself represents a newly corrected convention.

## Required full verification

```bash
.venv/bin/python -m compileall -q backend
for file in frontend/js/*.js; do node --check "$file"; done
.venv/bin/pytest -q
git diff --check
```

Count collection when reporting a result:

```bash
.venv/bin/pytest --collect-only | tail -1
```

Profile the fast backend when touching optimizer or live-simulation code:

```bash
.venv/bin/python scripts/profile_backend.py --iterations 100
```

## Live smoke tests

Start the server, then from another shell:

```bash
curl -fsS http://127.0.0.1:8000/health
curl -fsS -H 'Content-Type: application/json' -d '{}' http://127.0.0.1:8000/api/simulate
```

A short vortex calculation that exercises the telescope without a long default-cell run:

```bash
curl -fsS \
  -H 'Content-Type: application/json' \
  -d '{
    "total_passes": 4,
    "revolutions": 1,
    "wave_optics": {
      "profile_type": "gaussian",
      "phase_plate_enabled": true,
      "phase_plate_radial_p": 2,
      "phase_plate_l": 3,
      "max_grid_points": 1024,
      "max_memory_mb": 512,
      "display_grid_points": 48
    }
  }' \
  http://127.0.0.1:8000/api/simulate-wave-optics
```

For UI work, verify at least:

- auto/fixed/manual telescope control enablement;
- calculated lens/distance values written back to the form;
- validation error names the affected input;
- wave status transitions pending → running → fresh;
- an optical edit makes the result stale;
- Gaussian plot external colors/markers;
- no telescope geometry appears in the 3D or mirror-spot plots;
- caret stepping by arrow and focused wheel at integer and decimal places;
- save/load retains all new settings.

## Debugging common failures

### HTTP 422 “Request validation failed”

Inspect `details[0].loc` and `details[0].message`. Common causes are a frontend/schema field mismatch, an exceeded bound, non-coprime N/k with automatic injection, a singular automatic radius, or a zero/invalid-sign focal/radius value.

If the UI shows only the generic message, add the field to the label map in `api-client.js` and ensure the backend returns the standard validation envelope.

### HTTP 400 wave sampling error

The request is physically planned but exceeds configured or hard sampling/memory limits. Read the required point count and whether the failure is the configured cap, 2048 hard cap, or memory budget. Adjust window/samples only when the new values remain physically justified.

### Wave result says stale

Compare the current `buildWaveOpticsRequest()` payload with the stored signature. New propagation inputs are normally included automatically. Do not force the state fresh.

### Telescope says closest fit

Inspect `relative_q_error`, target q, achieved x/y q, lens catalog, and distance limits. Unequal M² is expected to prevent an exact shared spherical-lens match. The cell must still use achieved q.

### Analytic and wave radii disagree at M1

Check, in order:

1. telescope field sampling and guard-band warnings;
2. lens phase sign and angular-spectrum sign;
3. vacuum versus medium wavelength;
4. planar q scaling;
5. whether exact achieved q is used in both paths;
6. profile equivalent-radius convention (high-order fields need not equal the base Gaussian radius).

## Completion checklist

- [ ] Schema, backend, frontend registry, UI, save/load, and error labels agree.
- [ ] Physical convention and units are documented.
- [ ] Fast and wave paths share the correct resolved geometry/q.
- [ ] Sampling and memory failure modes remain explicit.
- [ ] Focused tests cover normal, edge, and invalid cases.
- [ ] Full Python, Node, pytest, and diff checks pass.
- [ ] Live API smoke test passes.
- [ ] Browser behavior was checked, or inability to do so is reported.
- [ ] README and maintainer documents remain accurate.
- [ ] Final handoff distinguishes local, committed, pushed, and deployed state.
