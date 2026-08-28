from __future__ import annotations

import json
import subprocess

from tests.helpers import ROOT_DIR


def run_digit_stepper_cases() -> dict:
    script = """
import { caretPlaceExponent, stepNumericText } from "./frontend/js/digit-stepper.js";

const step = (value, start, direction, options = {}) =>
  stepNumericText(value, start, start, direction, options);

const zeroAtThousands = step("1000", 0, -1);
console.log(JSON.stringify({
  exponents: {
    hundreds: caretPlaceExponent("123.45", 0),
    units: caretPlaceExponent("123.45", 2),
    unitsAtDecimal: caretPlaceExponent("123.45", 3),
    tenths: caretPlaceExponent("123.45", 4),
    hundredths: caretPlaceExponent("123.45", 5),
  },
  hundredsUp: step("123.45", 0, 1),
  unitsDown: step("123.45", 2, -1),
  tenthsUp: step("123.45", 4, 1),
  hundredthsUp: step("123.45", 5, 1),
  naturalCarry: step("9.99", 3, 1),
  naturalBorrow: step("0.00", 3, -1),
  negativeIncrease: step("-12.3", 1, 1),
  clampedMinimum: step("0.0001", 5, -1, { min: "0.0001" }),
  clampedMaximum: step("2048", 0, 1, { max: "2048" }),
  zeroAtThousands,
  retainedThousands: stepNumericText(
    zeroAtThousands.value,
    zeroAtThousands.selectionStart,
    zeroAtThousands.selectionEnd,
    -1,
    { exponent: zeroAtThousands.exponent },
  ),
}));
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=ROOT_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_caret_place_exponents_and_decimal_stepping() -> None:
    result = run_digit_stepper_cases()

    assert result["exponents"] == {
        "hundreds": 2,
        "units": 0,
        "unitsAtDecimal": 0,
        "tenths": -1,
        "hundredths": -2,
    }
    assert result["hundredsUp"]["value"] == "223.45"
    assert result["unitsDown"]["value"] == "122.45"
    assert result["tenthsUp"]["value"] == "123.55"
    assert result["hundredthsUp"]["value"] == "123.46"


def test_digit_stepper_handles_carry_borrow_bounds_and_negative_values() -> None:
    result = run_digit_stepper_cases()

    assert result["naturalCarry"]["value"] == "10.00"
    assert result["naturalBorrow"]["value"] == "-0.01"
    assert result["negativeIncrease"]["value"] == "-2.3"
    assert result["clampedMinimum"]["value"] == "0.0001"
    assert result["clampedMaximum"]["value"] == "2048"
    assert result["zeroAtThousands"]["value"] == "0"
    assert result["retainedThousands"]["value"] == "-1000"


def test_every_numeric_input_is_bound_through_the_shared_controller() -> None:
    index_html = (ROOT_DIR / "frontend" / "index.html").read_text(encoding="utf-8")
    main_js = (ROOT_DIR / "frontend" / "js" / "main.js").read_text(encoding="utf-8")
    controller_js = (ROOT_DIR / "frontend" / "js" / "digit-stepper.js").read_text(encoding="utf-8")

    assert index_html.count('type="number"') >= 40
    assert 'bindDigitAtCaretControls();' in main_js
    assert 'querySelectorAll(\'input[type="number"]\')' in controller_js
    assert 'event.key !== "ArrowUp" && event.key !== "ArrowDown"' in controller_js
    assert 'input.addEventListener("wheel"' in controller_js
