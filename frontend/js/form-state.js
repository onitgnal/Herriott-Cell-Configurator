const NUMERIC_FIELDS = [
  { key: "mirror_distance_mm", domId: "L", type: "float", legacyKey: "L" },
  { key: "total_passes", domId: "n", type: "int", legacyKey: "n" },
  { key: "revolutions", domId: "k", type: "int", legacyKey: "k" },
  { key: "symmetric_radius_mm", domId: "R", type: "float", legacyKey: "R" },
  { key: "mirror1_radius_mm", domId: "R1", type: "float", legacyKey: "R1" },
  { key: "mirror2_radius_mm", domId: "R2", type: "float", legacyKey: "R2" },
  { key: "spot_pattern_radius_mm", domId: "r0", type: "float", legacyKey: "r0" },
  { key: "hole_radius_mm", domId: "hole_r", type: "float", legacyKey: "hole_r" },
  { key: "output_hole_x_mm", domId: "out_hole_x", type: "float", legacyKey: "out_hole_x" },
  { key: "output_hole_y_mm", domId: "out_hole_y", type: "float", legacyKey: "out_hole_y" },
  { key: "wavelength_nm", domId: "lambda", type: "float", legacyKey: "lambda" },
  { key: "refractive_index", domId: "refr_index", type: "float", legacyKey: "refractive_index" },
  { key: "custom_m2", domId: "M2", type: "float", legacyKey: "M2" },
  { key: "input_beam_radius_mm", domId: "input_beam_radius", type: "float", legacyKey: "inputBeamRadius" },
  { key: "lens1_focal_length_mm", domId: "mm_f1", type: "float", legacyKey: "modeMatchF1" },
  { key: "lens2_focal_length_mm", domId: "mm_f2", type: "float", legacyKey: "modeMatchF2" },
  { key: "lens3_focal_length_mm", domId: "mm_f3", type: "float", legacyKey: "modeMatchF3" },
  { key: "phase_plate_to_lens1_mm", domId: "mm_d0", type: "float", legacyKey: "modeMatchD0" },
  { key: "lens1_to_lens2_mm", domId: "mm_d12", type: "float", legacyKey: "modeMatchD12" },
  { key: "lens2_to_lens3_mm", domId: "mm_d23", type: "float", legacyKey: "modeMatchD23" },
  { key: "lens3_to_mirror1_mm", domId: "mm_d3m", type: "float", legacyKey: "modeMatchD3M" },
  { key: "output_propagation_mm", domId: "output_propagation", type: "float", legacyKey: "outputPropagation" },
  { key: "peak_power_gw", domId: "peak_power", type: "float", legacyKey: "peak_power" },
  { key: "pulse_energy_mj", domId: "pulse_energy", type: "float", legacyKey: "pulse_energy" },
  { key: "hermite_n", domId: "hgn", type: "int", legacyKey: "hgn" },
  { key: "hermite_m", domId: "hgm", type: "int", legacyKey: "hgm" },
  { key: "laguerre_p", domId: "lgp", type: "int", legacyKey: "lgp" },
  { key: "laguerre_l", domId: "lgl", type: "int", legacyKey: "lgl" },
  { key: "input_waist_x_mm", domId: "winx", type: "float", legacyKey: "winx" },
  { key: "input_waist_y_mm", domId: "winy", type: "float", legacyKey: "winy" },
  { key: "input_waist_z_mm", domId: "zin", type: "float", legacyKey: "zin" },
  { key: "polarization_angle_deg", domId: "polang", type: "float", legacyKey: "polang" },
  { key: "input_x_mm", domId: "x", type: "float", legacyKey: "x" },
  { key: "input_y_mm", domId: "y", type: "float", legacyKey: "y" },
  { key: "input_theta_x_mrad", domId: "thx", type: "float", legacyKey: "thx" },
  { key: "input_theta_y_mrad", domId: "thy", type: "float", legacyKey: "thy" },
  { key: "second_input_x_mm", domId: "second-x", type: "float", legacyKey: "second_x" },
  { key: "second_input_y_mm", domId: "second-y", type: "float", legacyKey: "second_y" },
  { key: "second_input_theta_x_mrad", domId: "second-thx", type: "float", legacyKey: "second_thx" },
  { key: "second_input_theta_y_mrad", domId: "second-thy", type: "float", legacyKey: "second_thy" },
  { key: "second_polarization_angle_deg", domId: "second-polang", type: "float", legacyKey: "second_polang" },
  { key: "mirror1_tilt_x_mrad", domId: "m1tx", type: "float", legacyKey: "m1tx" },
  { key: "mirror1_tilt_y_mrad", domId: "m1ty", type: "float", legacyKey: "m1ty" },
  { key: "mirror2_tilt_x_mrad", domId: "m2tx", type: "float", legacyKey: "m2tx" },
  { key: "mirror2_tilt_y_mrad", domId: "m2ty", type: "float", legacyKey: "m2ty" },
];

const LEGACY_TOGGLE_FIELDS = [
  { key: "cell_type", elementId: "cell-type", legacyKey: "cellType", type: "select" },
  { key: "auto_symmetric_radius", elementId: "auto-R", legacyKey: "autoR", type: "checkbox" },
  { key: "opposite_radius_mode", elementId: "radius-mode-vex", legacyKey: "oppositeRadiusMode", type: "select" },
  { key: "auto_output_hole", elementId: "auto-out-hole", legacyKey: "autoOutHole", type: "checkbox" },
  { key: "output_mirror", elementId: "out-mirror", legacyKey: "outMirror", type: "select-int" },
  { key: "auto_mode_match", elementId: "auto-mode-match", legacyKey: "autoModeMatch", type: "checkbox" },
  { key: "auto_injection", elementId: "auto-injection", legacyKey: "autoInjection", type: "checkbox" },
  { key: "second_beam_enabled", elementId: "second-beam-enabled", legacyKey: "secondBeamEnabled", type: "checkbox" },
  { key: "mode_type", elementId: "mode-type", legacyKey: "modeType", type: "select" },
  { key: "show_beam_profiles", elementId: "show-beam-profiles", legacyKey: "showBeamProfiles", type: "checkbox" },
  { key: "mode_matching_mode", elementId: "mode-matching-mode", legacyKey: "modeMatchingMode", type: "select" },
];

const WAVE_OPTICS_FIELDS = [
  { key: "profile_type", elementId: "wave-profile-type", type: "select" },
  { key: "super_gaussian_order", elementId: "wave-super-order", type: "float" },
  { key: "laguerre_p", elementId: "wave-lg-p", type: "int" },
  { key: "laguerre_l", elementId: "wave-lg-l", type: "int" },
  { key: "phase_plate_enabled", elementId: "wave-phase-plate-enabled", type: "checkbox" },
  { key: "phase_plate_radial_p", elementId: "wave-phase-p", type: "int" },
  { key: "phase_plate_l", elementId: "wave-phase-l", type: "int" },
  { key: "window_safety_factor", elementId: "wave-window-safety", type: "float" },
  { key: "samples_per_radius", elementId: "wave-samples-per-radius", type: "int" },
  { key: "max_grid_points", elementId: "wave-max-grid", type: "int" },
  { key: "max_memory_mb", elementId: "wave-max-memory", type: "float" },
];

const AUTO_GROUPS = [
  { checkboxId: "auto-R", groupId: "group-R" },
  { checkboxId: "auto-out-hole", groupId: "group-out-hole" },
  { checkboxId: "auto-injection", groupId: "group-injection" },
];

const ENABLE_GROUPS = [
  { checkboxId: "second-beam-enabled", groupId: "group-second-beam" },
];

let standardConfig = {};

function getNumericFieldConfig(key) {
  return NUMERIC_FIELDS.find((field) => field.key === key);
}

function getNumericElementsByDomId(domId) {
  return {
    range: document.getElementById(`param-${domId}`),
    number: document.getElementById(`num-${domId}`),
  };
}

function updateNumberStep(numberInput, valueString, type) {
  if (type !== "float") {
    return;
  }

  if (valueString.includes(".")) {
    const decimals = valueString.split(".")[1].length;
    numberInput.step = decimals > 0 ? Math.pow(10, -decimals).toFixed(decimals) : "1";
    return;
  }

  numberInput.step = "1";
}

function setControlDisabledGroup(checkboxId, groupId) {
  const checkbox = document.getElementById(checkboxId);
  const group = document.getElementById(groupId);
  const disabled = checkbox.checked;
  group.classList.toggle("opacity-50", disabled);
  group.classList.toggle("pointer-events-none", disabled);
}

function setControlEnabledGroup(checkboxId, groupId) {
  const checkbox = document.getElementById(checkboxId);
  const group = document.getElementById(groupId);
  const disabled = !checkbox.checked;
  group.classList.toggle("opacity-50", disabled);
  group.classList.toggle("pointer-events-none", disabled);
}

function setGroupDisabled(groupId, disabled) {
  const group = document.getElementById(groupId);
  group.classList.toggle("opacity-50", disabled);
  group.classList.toggle("pointer-events-none", disabled);
}

function setNumericControlValue(domId, numericValue, displayValue = String(numericValue)) {
  const { range, number } = getNumericElementsByDomId(domId);
  if (!range || !number || numericValue == null || Number.isNaN(numericValue)) {
    return;
  }

  if (numericValue < Number(range.min)) {
    range.min = String(numericValue);
  }
  if (numericValue > Number(range.max)) {
    range.max = String(numericValue);
  }

  range.value = String(numericValue);
  number.value = displayValue;
  updateNumberStep(number, displayValue, NUMERIC_FIELDS.find((field) => field.domId === domId)?.type ?? "float");
}

function applyLegacyConfig(legacyConfig) {
  if (legacyConfig.cellType !== undefined) {
    document.getElementById("cell-type").value = legacyConfig.cellType;
  }

  LEGACY_TOGGLE_FIELDS.forEach((field) => {
    if (legacyConfig[field.legacyKey] === undefined) {
      return;
    }
    const element = document.getElementById(field.elementId);
    if (field.type === "checkbox") {
      element.checked = Boolean(legacyConfig[field.legacyKey]);
    } else {
      element.value = String(legacyConfig[field.legacyKey]);
    }
  });

  if (legacyConfig.oppositeRadiusMode === undefined && legacyConfig.autoRVex !== undefined) {
    document.getElementById("radius-mode-vex").value = legacyConfig.autoRVex ? "auto_equal" : "manual";
  }

  NUMERIC_FIELDS.forEach((field) => {
    if (legacyConfig[field.legacyKey] === undefined) {
      return;
    }

    const rawValue = String(legacyConfig[field.legacyKey]);
    const numericValue = field.type === "int" ? parseInt(rawValue, 10) : parseFloat(rawValue);
    setNumericControlValue(field.domId, numericValue, rawValue);
  });

  updateCellTypeUI();
  updateModeUI();
  updateToggleGroups();
}

function captureLegacyConfig() {
  const legacyConfig = {};

  NUMERIC_FIELDS.forEach((field) => {
    const number = document.getElementById(`num-${field.domId}`);
    legacyConfig[field.legacyKey] = number.value;
  });

  LEGACY_TOGGLE_FIELDS.forEach((field) => {
    const element = document.getElementById(field.elementId);
    if (field.type === "checkbox") {
      legacyConfig[field.legacyKey] = element.checked;
    } else {
      legacyConfig[field.legacyKey] = element.value;
    }
  });

  return legacyConfig;
}

export function updateModeUI() {
  const modeType = document.getElementById("mode-type").value;
  document.getElementById("group-hg").classList.toggle("hidden", modeType !== "hg");
  document.getElementById("group-lg").classList.toggle("hidden", modeType !== "lg");
  document.getElementById("group-custom").classList.toggle("hidden", modeType !== "custom");
}

export function updateWaveOpticsUI() {
  const profileType = document.getElementById("wave-profile-type")?.value;
  document.getElementById("wave-super-order-group")?.classList.toggle(
    "hidden",
    profileType !== "super_gaussian" && profileType !== "round_super_gaussian",
  );
  document.getElementById("wave-lg-indices-group")?.classList.toggle(
    "hidden",
    profileType !== "laguerre_gaussian",
  );
  const phasePlateSupported = profileType !== "laguerre_gaussian";
  const phasePlateEnabled = Boolean(document.getElementById("wave-phase-plate-enabled")?.checked);
  document.getElementById("wave-phase-plate-group")?.classList.toggle("hidden", !phasePlateSupported);
  document.getElementById("wave-phase-indices-group")?.classList.toggle(
    "hidden",
    !phasePlateSupported || !phasePlateEnabled,
  );
}

export function updateModeMatchingUI() {
  const mode = document.getElementById("mode-matching-mode")?.value ?? "auto";
  setGroupDisabled("group-mode-matching-lenses", mode === "auto");
  setGroupDisabled("group-mode-matching-distances", mode !== "manual");
}

export function updateCellTypeUI() {
  const cellType = document.getElementById("cell-type").value;
  document.getElementById("ui-cav-cav").classList.toggle("hidden", cellType !== "cav-cav");
  document.getElementById("ui-cav-vex").classList.toggle("hidden", cellType !== "cav-vex");
}

export function updateToggleGroups() {
  AUTO_GROUPS.forEach(({ checkboxId, groupId }) => setControlDisabledGroup(checkboxId, groupId));
  ENABLE_GROUPS.forEach(({ checkboxId, groupId }) => setControlEnabledGroup(checkboxId, groupId));
  const oppositeRadiusMode = document.getElementById("radius-mode-vex").value;
  setGroupDisabled("group-R1-vex", oppositeRadiusMode === "auto_equal");
  setGroupDisabled("group-R2-vex", oppositeRadiusMode !== "manual");
  updateModeMatchingUI();
}

export function captureConfig() {
  const config = {};

  NUMERIC_FIELDS.forEach((field) => {
    const number = document.getElementById(`num-${field.domId}`);
    config[field.key] = field.type === "int" ? parseInt(number.value, 10) : parseFloat(number.value);
  });

  LEGACY_TOGGLE_FIELDS.forEach((field) => {
    const element = document.getElementById(field.elementId);
    if (field.type === "checkbox") {
      config[field.key] = element.checked;
    } else if (field.type === "select-int") {
      config[field.key] = parseInt(element.value, 10);
    } else {
      config[field.key] = element.value;
    }
  });

  return config;
}

export function buildSimulationRequest(config = captureConfig()) {
  const { show_beam_profiles, ...request } = config;
  return request;
}

export function captureWaveOpticsSettings() {
  const settings = {};

  WAVE_OPTICS_FIELDS.forEach((field) => {
    const element = document.getElementById(field.elementId);
    if (!element) {
      return;
    }

    if (field.type === "select") {
      settings[field.key] = element.value;
    } else if (field.type === "checkbox") {
      settings[field.key] = element.checked;
    } else if (field.type === "int") {
      settings[field.key] = parseInt(element.value, 10);
    } else {
      settings[field.key] = parseFloat(element.value);
    }
  });

  return settings;
}

export function buildWaveOpticsRequest(config = captureConfig(), waveOptics = captureWaveOpticsSettings()) {
  return {
    ...buildSimulationRequest(config),
    wave_optics: waveOptics,
  };
}

export function applyConfig(config) {
  const normalizedConfig = {
    ...config,
    opposite_radius_mode:
      config.opposite_radius_mode ?? (config.auto_opposite_radii === false ? "manual" : "auto_equal"),
  };

  NUMERIC_FIELDS.forEach((field) => {
    if (normalizedConfig[field.key] === undefined || normalizedConfig[field.key] === null) {
      return;
    }

    const rawValue = String(normalizedConfig[field.key]);
    const numericValue = field.type === "int" ? parseInt(rawValue, 10) : parseFloat(rawValue);
    setNumericControlValue(field.domId, numericValue, rawValue);
  });

  LEGACY_TOGGLE_FIELDS.forEach((field) => {
    if (normalizedConfig[field.key] === undefined) {
      return;
    }
    const element = document.getElementById(field.elementId);
    if (field.type === "checkbox") {
      element.checked = Boolean(normalizedConfig[field.key]);
    } else {
      element.value = String(normalizedConfig[field.key]);
    }
  });

  if (config.wave_optics) {
    WAVE_OPTICS_FIELDS.forEach((field) => {
      if (config.wave_optics[field.key] === undefined) {
        return;
      }
      const element = document.getElementById(field.elementId);
      if (!element) {
        return;
      }
      if (field.type === "checkbox") {
        element.checked = Boolean(config.wave_optics[field.key]);
      } else {
        element.value = String(config.wave_optics[field.key]);
      }
    });
  }

  updateCellTypeUI();
  updateModeUI();
  updateWaveOpticsUI();
  updateToggleGroups();
}

export function applyResolvedInputs(resolvedInputs) {
  const currentConfig = captureConfig();

  if (
    currentConfig.cell_type === "cav-cav" &&
    currentConfig.auto_symmetric_radius &&
    resolvedInputs.mirror1_radius_mm != null
  ) {
    setNumericControlValue("R", resolvedInputs.mirror1_radius_mm, resolvedInputs.mirror1_radius_mm.toFixed(2));
  }

  if (
    currentConfig.cell_type === "cav-vex" &&
    resolvedInputs.mirror1_radius_mm != null &&
    resolvedInputs.mirror2_radius_mm != null
  ) {
    if (currentConfig.opposite_radius_mode === "auto_equal") {
      setNumericControlValue("R1", resolvedInputs.mirror1_radius_mm, resolvedInputs.mirror1_radius_mm.toFixed(2));
    }
    if (currentConfig.opposite_radius_mode !== "manual") {
      setNumericControlValue("R2", resolvedInputs.mirror2_radius_mm, resolvedInputs.mirror2_radius_mm.toFixed(2));
    }
  }

  if (currentConfig.auto_mode_match) {
    if (resolvedInputs.input_waist_x_mm != null) {
      setNumericControlValue("winx", resolvedInputs.input_waist_x_mm, resolvedInputs.input_waist_x_mm.toFixed(3));
    }
    if (resolvedInputs.input_waist_y_mm != null) {
      setNumericControlValue("winy", resolvedInputs.input_waist_y_mm, resolvedInputs.input_waist_y_mm.toFixed(3));
    }
    if (resolvedInputs.input_waist_z_mm != null) {
      setNumericControlValue("zin", resolvedInputs.input_waist_z_mm, resolvedInputs.input_waist_z_mm.toFixed(1));
    }
  }

  if (currentConfig.auto_injection) {
    if (resolvedInputs.input_x_mm != null) {
      setNumericControlValue("x", resolvedInputs.input_x_mm, resolvedInputs.input_x_mm.toFixed(2));
    }
    if (resolvedInputs.input_y_mm != null) {
      setNumericControlValue("y", resolvedInputs.input_y_mm, resolvedInputs.input_y_mm.toFixed(2));
    }
    if (resolvedInputs.input_theta_x_mrad != null) {
      setNumericControlValue("thx", resolvedInputs.input_theta_x_mrad, resolvedInputs.input_theta_x_mrad.toFixed(2));
    }
    if (resolvedInputs.input_theta_y_mrad != null) {
      setNumericControlValue("thy", resolvedInputs.input_theta_y_mrad, resolvedInputs.input_theta_y_mrad.toFixed(2));
    }
  }

  if (currentConfig.auto_output_hole) {
    if (resolvedInputs.output_hole_x_mm != null) {
      setNumericControlValue("out_hole_x", resolvedInputs.output_hole_x_mm, resolvedInputs.output_hole_x_mm.toFixed(2));
    }
    if (resolvedInputs.output_hole_y_mm != null) {
      setNumericControlValue("out_hole_y", resolvedInputs.output_hole_y_mm, resolvedInputs.output_hole_y_mm.toFixed(2));
    }
    document.getElementById("out-mirror").value = String(resolvedInputs.output_mirror);
  }
}

export function applyModeMatchingResult(modeMatching) {
  if (!modeMatching) {
    return;
  }
  const focalDomIds = ["mm_f1", "mm_f2", "mm_f3"];
  const distanceDomIds = ["mm_d0", "mm_d12", "mm_d23", "mm_d3m"];
  focalDomIds.forEach((domId, index) => {
    const value = modeMatching.focal_lengths_mm[index];
    setNumericControlValue(domId, value, Number(value).toFixed(1));
  });
  distanceDomIds.forEach((domId, index) => {
    const value = modeMatching.distances_mm[index];
    setNumericControlValue(domId, value, Number(value).toFixed(1));
  });
}

export function bindNumericFields(onChange) {
  NUMERIC_FIELDS.forEach((field) => {
    const { range, number } = getNumericElementsByDomId(field.domId);
    if (!range || !number) {
      return;
    }

    updateNumberStep(number, number.value, field.type);

    range.addEventListener("input", (event) => {
      number.value = event.target.value;
      updateNumberStep(number, number.value, field.type);
      onChange();
    });

    number.addEventListener("input", (event) => {
      updateNumberStep(number, event.target.value, field.type);
    });

    number.addEventListener("change", (event) => {
      const rawValue = event.target.value;
      const numericValue = field.type === "int" ? parseInt(rawValue, 10) : parseFloat(rawValue);

      if (Number.isNaN(numericValue)) {
        number.value = range.value;
        updateNumberStep(number, number.value, field.type);
        return;
      }

      if (numericValue < Number(range.min)) {
        range.min = String(numericValue);
      }
      if (numericValue > Number(range.max)) {
        range.max = String(numericValue);
      }

      range.value = String(numericValue);
      number.value = field.type === "int" ? String(numericValue) : rawValue.trim();
      updateNumberStep(number, number.value, field.type);
      onChange();
    });
  });
}

export function bindWaveOpticsFields(onChange) {
  WAVE_OPTICS_FIELDS.forEach((field) => {
    const element = document.getElementById(field.elementId);
    if (!element) {
      return;
    }
    element.addEventListener("input", onChange);
    element.addEventListener("change", onChange);
  });
}

export function initializeStandardConfig() {
  standardConfig = { ...captureConfig(), wave_optics: captureWaveOpticsSettings() };
}

export function setStandardConfig() {
  standardConfig = { ...captureConfig(), wave_optics: captureWaveOpticsSettings() };
}

export function resetToStandardConfig() {
  applyConfig(standardConfig);
}

export function flashStandardSaved() {
  const button = document.getElementById("set-standard");
  const originalText = button.innerText;
  button.innerText = "✓ Saved";
  window.setTimeout(() => {
    button.innerText = originalText;
  }, 1500);
}

export function saveConfigToFile() {
  const json = JSON.stringify({ ...captureConfig(), wave_optics: captureWaveOpticsSettings() }, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);

  const downloadNode = document.createElement("a");
  downloadNode.href = url;
  downloadNode.download = "herriott_config.json";
  document.body.appendChild(downloadNode);
  downloadNode.click();

  window.setTimeout(() => {
    document.body.removeChild(downloadNode);
    URL.revokeObjectURL(url);
  }, 100);
}

export async function loadConfigFromFile(file) {
  const rawConfig = JSON.parse(await file.text());
  const configWithDefaults = {
    refractive_index: 1.0,
    ...rawConfig,
  };

  if ("cellType" in rawConfig || "modeType" in rawConfig || "showBeamProfiles" in rawConfig) {
    applyLegacyConfig(configWithDefaults);
    return;
  }

  applyConfig(configWithDefaults);
}
