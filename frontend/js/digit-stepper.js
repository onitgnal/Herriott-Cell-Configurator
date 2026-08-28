function expandScientificNotation(rawValue) {
  const value = String(rawValue).trim();
  const match = value.match(/^([+-]?)(\d*)(?:\.(\d*))?[eE]([+-]?\d+)$/);
  if (!match) {
    return value;
  }

  const [, sign, integerPart = "", fractionalPart = "", exponentText] = match;
  const digits = `${integerPart || "0"}${fractionalPart}`;
  const decimalPosition = (integerPart || "0").length + Number(exponentText);
  let expanded;

  if (decimalPosition <= 0) {
    expanded = `0.${"0".repeat(-decimalPosition)}${digits}`;
  } else if (decimalPosition >= digits.length) {
    expanded = `${digits}${"0".repeat(decimalPosition - digits.length)}`;
  } else {
    expanded = `${digits.slice(0, decimalPosition)}.${digits.slice(decimalPosition)}`;
  }

  return `${sign === "-" ? "-" : ""}${expanded}`;
}

function decimalPlaces(value) {
  const expanded = expandScientificNotation(value);
  const decimalIndex = expanded.indexOf(".");
  return decimalIndex === -1 ? 0 : expanded.length - decimalIndex - 1;
}

function scaledInteger(value, scale) {
  const expanded = expandScientificNotation(value);
  const match = expanded.match(/^([+-]?)(\d*)(?:\.(\d*))?$/);
  if (!match) {
    return null;
  }

  const [, sign, integerPart = "", fractionalPart = ""] = match;
  if (!integerPart && !fractionalPart) {
    return null;
  }

  const paddedFraction = fractionalPart.padEnd(scale, "0").slice(0, scale);
  const digits = `${integerPart || "0"}${paddedFraction}`.replace(/^0+(?=\d)/, "") || "0";
  const magnitude = BigInt(digits);
  return sign === "-" ? -magnitude : magnitude;
}

function formatScaledInteger(value, scale) {
  const isNegative = value < 0n;
  const absoluteDigits = (isNegative ? -value : value).toString().padStart(scale + 1, "0");
  const integerPart = scale === 0 ? absoluteDigits : absoluteDigits.slice(0, -scale);
  const fractionalPart = scale === 0 ? "" : absoluteDigits.slice(-scale);
  return `${isNegative ? "-" : ""}${integerPart}${scale === 0 ? "" : `.${fractionalPart}`}`;
}

function digitIndices(value) {
  const indices = [];
  for (let index = 0; index < value.length; index += 1) {
    if (/\d/.test(value[index])) {
      indices.push(index);
    }
  }
  return indices;
}

function targetDigitIndex(value, selectionStart, selectionEnd) {
  const indices = digitIndices(value);
  if (indices.length === 0) {
    return null;
  }

  const start = Math.max(0, Math.min(selectionStart ?? value.length, value.length));
  const end = Math.max(start, Math.min(selectionEnd ?? start, value.length));
  if (end > start) {
    const selectedDigit = indices.find((index) => index >= start && index < end);
    if (selectedDigit != null) {
      return selectedDigit;
    }
  }

  if (/\d/.test(value[start] ?? "")) {
    return start;
  }

  if (value[start] === ".") {
    const digitToLeft = indices.filter((index) => index < start).at(-1);
    if (digitToLeft != null) {
      return digitToLeft;
    }
  }

  const digitToRight = indices.find((index) => index > start);
  if (digitToRight != null) {
    return digitToRight;
  }

  return indices.filter((index) => index < start).at(-1) ?? indices[0];
}

export function caretPlaceExponent(value, selectionStart, selectionEnd = selectionStart) {
  const expanded = expandScientificNotation(value);
  const digitIndex = targetDigitIndex(expanded, selectionStart, selectionEnd);
  if (digitIndex == null) {
    return 0;
  }

  const decimalIndex = expanded.indexOf(".") === -1 ? expanded.length : expanded.indexOf(".");
  return digitIndex < decimalIndex
    ? decimalIndex - digitIndex - 1
    : decimalIndex - digitIndex;
}

function caretForExponent(value, exponent) {
  const decimalIndex = value.indexOf(".") === -1 ? value.length : value.indexOf(".");
  const requestedIndex = exponent >= 0
    ? decimalIndex - exponent - 1
    : decimalIndex - exponent;
  const indices = digitIndices(value);
  if (indices.includes(requestedIndex)) {
    return requestedIndex;
  }
  return exponent >= 0 ? (indices[0] ?? 0) : (indices.at(-1) ?? value.length);
}

export function stepNumericText(
  rawValue,
  selectionStart,
  selectionEnd,
  direction,
  { min = null, max = null, exponent = null } = {},
) {
  const value = expandScientificNotation(rawValue);
  const placeExponent = exponent ?? caretPlaceExponent(value, selectionStart, selectionEnd);
  const optionValues = [min, max].filter((item) => item != null && item !== "");
  const scale = Math.max(
    decimalPlaces(value),
    Math.max(0, -placeExponent),
    ...optionValues.map(decimalPlaces),
  );
  const currentScaled = scaledInteger(value, scale) ?? 0n;
  const stepPower = scale + placeExponent;
  const stepScaled = 10n ** BigInt(Math.max(0, stepPower));
  let nextScaled = currentScaled + (direction >= 0 ? stepScaled : -stepScaled);

  const minScaled = min == null || min === "" ? null : scaledInteger(min, scale);
  const maxScaled = max == null || max === "" ? null : scaledInteger(max, scale);
  if (minScaled != null && nextScaled < minScaled) {
    nextScaled = minScaled;
  }
  if (maxScaled != null && nextScaled > maxScaled) {
    nextScaled = maxScaled;
  }

  const nextValue = formatScaledInteger(nextScaled, scale);
  const nextCaret = caretForExponent(nextValue, placeExponent);
  return {
    value: nextValue,
    selectionStart: nextCaret,
    selectionEnd: Math.min(nextCaret + 1, nextValue.length),
    exponent: placeExponent,
  };
}

function updateAriaValue(input) {
  const numericValue = Number(input.value);
  if (Number.isFinite(numericValue)) {
    input.setAttribute("aria-valuenow", String(numericValue));
  } else {
    input.removeAttribute("aria-valuenow");
  }
}

function isPotentialNumericText(value) {
  return /^[+-]?(?:\d+\.?\d*|\.\d*)?(?:[eE][+-]?\d*)?$/.test(value);
}

function bindDigitStepper(input) {
  input.type = "text";
  input.inputMode = "decimal";
  input.setAttribute("role", "spinbutton");
  input.setAttribute("aria-keyshortcuts", "ArrowUp ArrowDown");
  const interactionHint = "Place the caret on a digit, then use Arrow Up/Down or the mouse wheel to change that place value.";
  input.title = input.title ? `${input.title} ${interactionHint}` : interactionHint;
  if (input.min !== "") {
    input.setAttribute("aria-valuemin", input.min);
  }
  if (input.max !== "") {
    input.setAttribute("aria-valuemax", input.max);
  }
  input.dataset.digitStepper = "true";
  updateAriaValue(input);

  let retainedPlace = null;
  let lastEditableValue = input.value;
  let lastCommittedValue = input.value;
  const clearRetainedPlace = () => {
    retainedPlace = null;
  };

  const applyStep = (direction) => {
    const selectionStart = input.selectionStart ?? input.value.length;
    const selectionEnd = input.selectionEnd ?? selectionStart;
    const canReuseRetainedPlace = retainedPlace
      && retainedPlace.value === input.value
      && retainedPlace.selectionStart === selectionStart
      && retainedPlace.selectionEnd === selectionEnd;
    const result = stepNumericText(
      input.value,
      selectionStart,
      selectionEnd,
      direction,
      {
        min: input.getAttribute("min"),
        max: input.getAttribute("max"),
        exponent: canReuseRetainedPlace ? retainedPlace.exponent : null,
      },
    );

    input.value = result.value;
    input.dispatchEvent(new Event("change", { bubbles: true }));
    const finalCaret = caretForExponent(input.value, result.exponent);
    input.setSelectionRange(finalCaret, Math.min(finalCaret + 1, input.value.length));
    retainedPlace = {
      value: input.value,
      selectionStart: input.selectionStart,
      selectionEnd: input.selectionEnd,
      exponent: result.exponent,
    };
    updateAriaValue(input);
  };

  input.addEventListener("keydown", (event) => {
    if (event.key !== "ArrowUp" && event.key !== "ArrowDown") {
      clearRetainedPlace();
      return;
    }
    if (event.altKey || event.ctrlKey || event.metaKey) {
      return;
    }
    event.preventDefault();
    applyStep(event.key === "ArrowUp" ? 1 : -1);
  });

  input.addEventListener("wheel", (event) => {
    if (document.activeElement !== input || event.ctrlKey || event.metaKey) {
      return;
    }
    const wheelDelta = event.deltaY !== 0 ? event.deltaY : event.deltaX;
    if (wheelDelta === 0) {
      return;
    }
    event.preventDefault();
    applyStep(wheelDelta < 0 ? 1 : -1);
  }, { passive: false });

  input.addEventListener("input", () => {
    if (!isPotentialNumericText(input.value)) {
      input.value = lastEditableValue;
      input.setSelectionRange(input.value.length, input.value.length);
    } else {
      lastEditableValue = input.value;
    }
    clearRetainedPlace();
    updateAriaValue(input);
  });
  input.addEventListener("change", () => {
    if (!Number.isFinite(Number(input.value)) || input.value.trim() === "") {
      input.value = lastCommittedValue;
    }
  }, { capture: true });
  input.addEventListener("change", () => {
    lastCommittedValue = input.value;
    lastEditableValue = input.value;
    updateAriaValue(input);
  });
  input.addEventListener("pointerdown", clearRetainedPlace);
  input.addEventListener("focus", clearRetainedPlace);
}

export function bindDigitAtCaretControls(root = document) {
  root.querySelectorAll('input[type="number"]').forEach((input) => bindDigitStepper(input));
}
