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
