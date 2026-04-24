function stableSerialize(value) {
  if (Array.isArray(value)) {
    return `[${value.map((item) => stableSerialize(item)).join(",")}]`;
  }

  if (value && typeof value === "object") {
    const entries = Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stableSerialize(value[key])}`);
    return `{${entries.join(",")}}`;
  }

  return JSON.stringify(value);
}

export function buildWaveOpticsSignature(payload) {
  return stableSerialize(payload);
}

export function createWaveOpticsState() {
  return {
    pending: false,
    result: null,
    signature: null,
    error: null,
  };
}

export function markWaveOpticsPending(state) {
  return {
    ...state,
    pending: true,
    error: null,
  };
}

export function storeWaveOpticsResult(state, signature, result) {
  return {
    ...state,
    pending: false,
    result,
    signature,
    error: null,
  };
}

export function storeWaveOpticsError(state, error) {
  return {
    ...state,
    pending: false,
    error,
  };
}

export function isWaveOpticsFresh(state, currentSignature) {
  return Boolean(state.result && state.signature === currentSignature && !state.error);
}

export function isWaveOpticsStale(state, currentSignature) {
  return Boolean(state.result && state.signature !== currentSignature);
}
