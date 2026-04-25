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
