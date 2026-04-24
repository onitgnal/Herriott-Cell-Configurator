from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT_DIR / "tests" / "fixtures" / "configs"


def load_fixture(name: str) -> dict[str, Any]:
    with (CONFIG_DIR / name).open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def run_js_reference(config_name: str) -> dict[str, Any]:
    result = subprocess.run(
        ["node", "tests/reference/run_js_simulation.mjs", f"tests/fixtures/configs/{config_name}"],
        cwd=ROOT_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def strip_none(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: strip_none(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [strip_none(item) for item in value]
    if isinstance(value, tuple):
        return tuple(strip_none(item) for item in value)
    return value


def assert_nested_close(actual: Any, expected: Any, *, rel_tol: float = 1e-6, abs_tol: float = 1e-8, path: str = "root") -> None:
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        if math.isfinite(actual) and math.isfinite(expected):
            assert math.isclose(actual, expected, rel_tol=rel_tol, abs_tol=abs_tol), f"Mismatch at {path}: {actual} != {expected}"
            return
        assert actual == expected, f"Mismatch at {path}: {actual} != {expected}"
        return

    if actual is None or expected is None:
        assert actual is expected, f"Mismatch at {path}: {actual} != {expected}"
        return

    if isinstance(actual, dict) and isinstance(expected, dict):
        assert actual.keys() == expected.keys(), f"Key mismatch at {path}: {actual.keys()} != {expected.keys()}"
        for key in actual:
            assert_nested_close(actual[key], expected[key], rel_tol=rel_tol, abs_tol=abs_tol, path=f"{path}.{key}")
        return

    if isinstance(actual, (list, tuple)) and isinstance(expected, (list, tuple)):
        assert len(actual) == len(expected), f"Length mismatch at {path}: {len(actual)} != {len(expected)}"
        for index, (actual_item, expected_item) in enumerate(zip(actual, expected, strict=True)):
            assert_nested_close(
                actual_item,
                expected_item,
                rel_tol=rel_tol,
                abs_tol=abs_tol,
                path=f"{path}[{index}]",
            )
        return

    assert actual == expected, f"Mismatch at {path}: {actual} != {expected}"
