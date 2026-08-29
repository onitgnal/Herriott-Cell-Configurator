from __future__ import annotations

import re
from pathlib import Path

from backend.app.core.wave_optics import DENSE_COLLINS_MAX_POINTS
from backend.app.schemas.simulation import WAVE_OPTICS_MAX_GRID_POINTS

from tests.helpers import ROOT_DIR


DOCUMENTS = [
    ROOT_DIR / "README.md",
    ROOT_DIR / "AGENTS.md",
    ROOT_DIR / "docs" / "ARCHITECTURE.md",
    ROOT_DIR / "docs" / "PHYSICS.md",
    ROOT_DIR / "docs" / "EXTENDING.md",
]


def test_maintainer_documents_have_no_broken_local_links() -> None:
    markdown_link = re.compile(r"\[[^]]+]\(([^)]+)\)")

    for document in DOCUMENTS:
        assert document.is_file(), f"Missing maintainer document: {document.relative_to(ROOT_DIR)}"
        for target in markdown_link.findall(document.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://")):
                continue
            relative_target = target.split("#", 1)[0]
            if not relative_target:
                continue
            resolved = (document.parent / relative_target).resolve()
            assert resolved.exists(), (
                f"Broken documentation link in {document.relative_to(ROOT_DIR)}: {target}"
            )


def test_agent_handoff_tracks_critical_runtime_invariants() -> None:
    agent_guide = (ROOT_DIR / "AGENTS.md").read_text(encoding="utf-8")
    architecture = (ROOT_DIR / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
    physics = (ROOT_DIR / "docs" / "PHYSICS.md").read_text(encoding="utf-8")

    assert f"hard wave-grid cap is {WAVE_OPTICS_MAX_GRID_POINTS}" in agent_guide
    assert f"Grids through {DENSE_COLLINS_MAX_POINTS}" in agent_guide
    assert "q_cell = n * q_air" in agent_guide
    assert "LG `p` is a radial-node index" in agent_guide
    assert "The root `index.html` is only a placeholder" in agent_guide

    for endpoint in (
        "POST /api/simulate",
        "POST /api/simulate-wave-optics",
        "POST /api/simulate-wave-optics/jobs",
        "GET /api/simulate-wave-optics/jobs/{id}",
    ):
        assert endpoint in architecture

    assert "q2 = (n2/n1)*q1" in physics
    assert "exp(i*l*phi)" in physics
    assert "No initial mirror phase is applied" in physics
