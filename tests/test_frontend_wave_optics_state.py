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
