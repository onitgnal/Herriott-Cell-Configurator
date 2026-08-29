export class ApiError extends Error {
  constructor(message, status, details = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export function getErrorMessage(body, fallbackMessage) {
  if (Array.isArray(body?.details) && body.details.length > 0) {
    const detail = body.details[0];
    if (!detail.message) {
      return fallbackMessage;
    }
    const fieldName = Array.isArray(detail.loc) ? detail.loc.at(-1) : null;
    const fieldLabels = {
      max_grid_points: "Max Grid",
      max_memory_mb: "Max Memory",
      laguerre_p: "LG radial p",
      laguerre_l: "LG azimuthal l",
      phase_plate_radial_p: "Radial pupil p",
      phase_plate_l: "Vortex charge l",
      input_beam_radius_mm: "Input beam radius",
      lens1_focal_length_mm: "Lens 1 focal length",
      lens2_focal_length_mm: "Lens 2 focal length",
      lens3_focal_length_mm: "Lens 3 focal length",
      phase_plate_to_lens1_mm: "Plate to Lens 1 distance",
      lens1_to_lens2_mm: "Lens 1 to Lens 2 distance",
      lens2_to_lens3_mm: "Lens 2 to Lens 3 distance",
      lens3_to_mirror1_mm: "Lens 3 to Mirror 1 distance",
      output_propagation_mm: "Out-coupling distance",
      samples_per_radius: "Samples / Radius",
      window_safety_factor: "Window Margin",
    };
    if (fieldName && fieldLabels[fieldName]) {
      return `${fieldLabels[fieldName]}: ${detail.message}`;
    }
    return detail.message;
  }

  if (body?.error?.message) {
    return body.error.message;
  }

  return fallbackMessage;
}

export async function simulateConfiguration(payload, { signal } = {}) {
  return postJson("/api/simulate", payload, { signal });
}

export async function simulateWaveOptics(payload, { signal } = {}) {
  return postJson("/api/simulate-wave-optics", payload, { signal });
}

export async function startWaveOpticsJob(payload, { signal } = {}) {
  return postJson("/api/simulate-wave-optics/jobs", payload, { signal });
}

export async function getWaveOpticsJob(jobId, { signal } = {}) {
  return getJson(`/api/simulate-wave-optics/jobs/${encodeURIComponent(jobId)}`, { signal });
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

async function getJson(url, { signal } = {}) {
  const response = await fetch(url, { signal });

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
