export class ApiError extends Error {
  constructor(message, status, details = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

function getErrorMessage(body, fallbackMessage) {
  if (body?.error?.message) {
    return body.error.message;
  }

  if (Array.isArray(body?.details) && body.details.length > 0) {
    return body.details[0].message || fallbackMessage;
  }

  return fallbackMessage;
}

export async function simulateConfiguration(payload, { signal } = {}) {
  return postJson("/api/simulate", payload, { signal });
}

export async function simulateWaveOptics(payload, { signal } = {}) {
  return postJson("/api/simulate-wave-optics", payload, { signal });
}

async function postJson(url, payload, { signal } = {}) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    signal,
  });

  let body = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }

  if (!response.ok) {
    throw new ApiError(
      getErrorMessage(body, `Backend request failed with status ${response.status}.`),
      response.status,
      body?.details ?? null,
    );
  }

  return body;
}
