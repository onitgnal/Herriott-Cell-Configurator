from __future__ import annotations

import json
import subprocess

from tests.helpers import ROOT_DIR


def test_wave_optics_state_marks_results_stale_when_signature_changes() -> None:
    script = """
import {
  buildWaveOpticsSignature,
  createWaveOpticsState,
  isWaveOpticsFresh,
  isWaveOpticsStale,
  markWaveOpticsPending,
  storeWaveOpticsResult,
} from "./frontend/js/wave-optics-state.js";

const payloadA = {
  mirror_distance_mm: 1132,
  total_passes: 14,
  wave_optics: {
    profile_type: "gaussian",
    max_grid_points: 160,
  },
};
const payloadB = {
  wave_optics: {
    max_grid_points: 160,
    profile_type: "gaussian",
  },
  total_passes: 14,
  mirror_distance_mm: 1200,
};
const payloadPowerOnly = {
  ...payloadA,
  peak_power_gw: 25,
  pulse_energy_mj: 5,
};

let state = createWaveOpticsState();
state = markWaveOpticsPending(state);
state = storeWaveOpticsResult(state, buildWaveOpticsSignature(payloadA), { wave_optics: { warnings: [] } });

console.log(JSON.stringify({
  freshSamePayload: isWaveOpticsFresh(state, buildWaveOpticsSignature(payloadA)),
  sameSignatureDespiteKeyOrder: buildWaveOpticsSignature(payloadA) === buildWaveOpticsSignature({
    total_passes: 14,
    mirror_distance_mm: 1132,
    wave_optics: { max_grid_points: 160, profile_type: "gaussian" },
  }),
  staleAfterOpticalChange: isWaveOpticsStale(state, buildWaveOpticsSignature(payloadB)),
  freshAfterDisplayOnlyChange: isWaveOpticsFresh(state, buildWaveOpticsSignature(payloadPowerOnly)),
}));
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=ROOT_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["freshSamePayload"] is True
    assert payload["sameSignatureDespiteKeyOrder"] is True
    assert payload["staleAfterOpticalChange"] is True
    assert payload["freshAfterDisplayOnlyChange"] is True


def test_renderer_peak_density_uses_base_mode_waists_and_remaining_wave_power() -> None:
    script = """
globalThis.window = { Plotly: {} };
const {
  analyticPeakDensityPerMm2,
  wavePeakDensityPerMm2,
} = await import("./frontend/js/renderers.js");

console.log(JSON.stringify({
  analytic: analyticPeakDensityPerMm2(Math.sqrt(5), Math.sqrt(3), {
    type: "hg",
    M2x: 5,
    M2y: 3,
    peak_factor: 0.25,
  }),
  wave: wavePeakDensityPerMm2({
    peak_density_per_mm2: 2.0,
    power_fraction: 0.8,
  }),
}));
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=ROOT_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["analytic"] == 0.25
    assert payload["wave"] == 1.6


def test_wave_optics_progress_bar_markup_exists() -> None:
    index_html = (ROOT_DIR / "frontend" / "index.html").read_text(encoding="utf-8")
    styles = (ROOT_DIR / "frontend" / "styles.css").read_text(encoding="utf-8")

    assert 'id="wave-optics-progress"' in index_html
    assert 'id="wave-optics-progress-bar"' in index_html
    assert 'id="wave-optics-progress-text"' in index_html
    assert 'id="wave-optics-progress-eta"' in index_html
    assert 'id="calculate-wave-optics-bar"' in index_html
    assert 'id="wave-optics-status-card"' in index_html
    assert 'id="calculate-wave-optics-label"' in index_html
    assert 'data-running="false"' in index_html
    assert ".wave-optics-run-button" in styles
    assert "@keyframes wave-optics-button-progress" in styles
    assert ".wave-optics-progress-track" in styles
    assert "@keyframes wave-optics-progress-slide" in styles


def test_laguerre_gaussian_launch_controls_capture_indices_and_toggle_visibility() -> None:
    index_html = (ROOT_DIR / "frontend" / "index.html").read_text(encoding="utf-8")
    assert '<option value="laguerre_gaussian">Laguerre–Gaussian (LG)</option>' in index_html
    assert 'id="wave-lg-indices-group"' in index_html
    assert 'id="wave-lg-p"' in index_html
    assert 'id="wave-lg-l"' in index_html
    assert 'id="wave-max-grid" value="2048" step="64" min="32" max="2048"' in index_html
    assert 'id="wave-max-memory" value="1024" step="64" min="16" max="4096"' in index_html
    assert "large grids use scaled FFT" in index_html

    script = """
const classes = () => ({
  values: new Set(["hidden"]),
  toggle(name, force) {
    if (force) this.values.add(name);
    else this.values.delete(name);
  },
  contains(name) { return this.values.has(name); },
});
const elements = {
  "wave-profile-type": { value: "laguerre_gaussian" },
  "wave-super-order": { value: "4" },
  "wave-lg-p": { value: "3" },
  "wave-lg-l": { value: "-2" },
  "wave-window-safety": { value: "4" },
  "wave-samples-per-radius": { value: "14" },
  "wave-max-grid": { value: "2048" },
  "wave-max-memory": { value: "1024" },
  "wave-super-order-group": { classList: classes() },
  "wave-lg-indices-group": { classList: classes() },
};
globalThis.document = { getElementById: (id) => elements[id] ?? null };
const { captureWaveOpticsSettings, updateWaveOpticsUI } = await import("./frontend/js/form-state.js");
updateWaveOpticsUI();
const settings = captureWaveOpticsSettings();
console.log(JSON.stringify({
  settings,
  lgHidden: elements["wave-lg-indices-group"].classList.contains("hidden"),
  superHidden: elements["wave-super-order-group"].classList.contains("hidden"),
}));
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=ROOT_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["settings"]["profile_type"] == "laguerre_gaussian"
    assert payload["settings"]["laguerre_p"] == 3
    assert payload["settings"]["laguerre_l"] == -2
    assert payload["lgHidden"] is False
    assert payload["superHidden"] is True


def test_second_beam_controls_exist() -> None:
    index_html = (ROOT_DIR / "frontend" / "index.html").read_text(encoding="utf-8")

    assert 'id="second-beam-enabled"' in index_html
    assert 'id="group-second-beam"' in index_html
    assert 'id="num-second-x"' in index_html
    assert 'id="num-second-y"' in index_html
    assert 'id="num-second-thx"' in index_html
    assert 'id="num-second-thy"' in index_html
    assert 'id="num-second-polang"' in index_html


def test_refractive_index_control_and_round_trip_explanation_exist() -> None:
    index_html = (ROOT_DIR / "frontend" / "index.html").read_text(encoding="utf-8")

    assert 'id="num-refr_index"' in index_html
    assert 'id="param-refr_index"' in index_html
    assert "Vacuum Wavelength" in index_html
    assert "Round Trips / Spots per Mirror" in index_html
    assert "two mirror-to-mirror legs" in index_html


def test_concave_convex_radius_mode_selector_exists() -> None:
    index_html = (ROOT_DIR / "frontend" / "index.html").read_text(encoding="utf-8")

    assert 'id="radius-mode-vex"' in index_html
    assert '<option value="auto_equal">Auto: |R1| = |R2|</option>' in index_html
    assert '<option value="auto_r2">Set R1, auto-calculate R2</option>' in index_html
    assert '<option value="manual">Set R1 and R2</option>' in index_html
    assert 'id="group-R1-vex"' in index_html
    assert 'id="group-R2-vex"' in index_html
    assert 'id="auto-R-vex"' not in index_html


def test_api_client_prefers_specific_validation_detail() -> None:
    script = """
import { getErrorMessage } from "./frontend/js/api-client.js";
console.log(JSON.stringify({
  specific: getErrorMessage({
    error: { message: "Request validation failed." },
    details: [{ message: "R1 is outside the valid range." }],
  }, "Fallback"),
  namedGrid: getErrorMessage({
    error: { message: "Request validation failed." },
    details: [{ loc: ["body", "wave_optics", "max_grid_points"], message: "Input should be less than or equal to 2048" }],
  }, "Fallback"),
}));
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=ROOT_DIR,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["specific"] == "R1 is outside the valid range."
    assert payload["namedGrid"] == "Max Grid: Input should be less than or equal to 2048"


def test_mode_matching_telescope_controls_and_external_plot_contract_exist() -> None:
    index_html = (ROOT_DIR / "frontend" / "index.html").read_text(encoding="utf-8")
    renderers = (ROOT_DIR / "frontend" / "js" / "renderers.js").read_text(encoding="utf-8")

    assert "Input Beam Mode-Matching" in index_html
    assert 'id="mode-matching-mode"' in index_html
    assert '<option value="auto">Auto-select practical lenses and distances</option>' in index_html
    assert '<option value="fixed_lenses">Use selected lenses; auto-fit distances</option>' in index_html
    assert '<option value="manual">Manual lenses and distances</option>' in index_html
    for control in (
        "num-input_beam_radius",
        "num-mm_f1",
        "num-mm_f2",
        "num-mm_f3",
        "num-mm_d0",
        "num-mm_d12",
        "num-mm_d23",
        "num-mm_d3m",
        "num-output_propagation",
        "mode-matching-status",
    ):
        assert f'id="{control}"' in index_html
    assert "external_beam_propagation: external" in renderers
    assert 'addExternalSection(external?.input_section, "Mode matching"' in renderers
    assert 'addExternalSection(external?.output_section, "Out coupling"' in renderers


def test_phase_plate_controls_capture_hygg_and_vortex_indices() -> None:
    index_html = (ROOT_DIR / "frontend" / "index.html").read_text(encoding="utf-8")
    assert 'id="wave-phase-plate-enabled"' in index_html
    assert 'id="wave-phase-p"' in index_html
    assert 'id="wave-phase-l"' in index_html
    assert "p=0 is a phase-only spiral plate" in index_html

    script = """
const classes = () => ({
  values: new Set(["hidden"]),
  toggle(name, force) { if (force) this.values.add(name); else this.values.delete(name); },
  contains(name) { return this.values.has(name); },
});
const elements = {
  "wave-profile-type": { value: "gaussian" },
  "wave-super-order": { value: "4" },
  "wave-lg-p": { value: "0" },
  "wave-lg-l": { value: "1" },
  "wave-phase-plate-enabled": { checked: true },
  "wave-phase-p": { value: "2" },
  "wave-phase-l": { value: "-3" },
  "wave-window-safety": { value: "4" },
  "wave-samples-per-radius": { value: "14" },
  "wave-max-grid": { value: "2048" },
  "wave-max-memory": { value: "1024" },
  "wave-super-order-group": { classList: classes() },
  "wave-lg-indices-group": { classList: classes() },
  "wave-phase-plate-group": { classList: classes() },
  "wave-phase-indices-group": { classList: classes() },
};
globalThis.document = { getElementById: (id) => elements[id] ?? null };
const { captureWaveOpticsSettings, updateWaveOpticsUI } = await import("./frontend/js/form-state.js");
updateWaveOpticsUI();
console.log(JSON.stringify({
  settings: captureWaveOpticsSettings(),
  phaseHidden: elements["wave-phase-indices-group"].classList.contains("hidden"),
}));
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=ROOT_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["settings"]["phase_plate_enabled"] is True
    assert payload["settings"]["phase_plate_radial_p"] == 2
    assert payload["settings"]["phase_plate_l"] == -3
    assert payload["phaseHidden"] is False
