import { ApiError, simulateConfiguration, simulateWaveOptics } from "./api-client.js";
import {
  applyResolvedInputs,
  bindNumericFields,
  bindWaveOpticsFields,
  buildSimulationRequest,
  buildWaveOpticsRequest,
  captureConfig,
  flashStandardSaved,
  initializeStandardConfig,
  loadConfigFromFile,
  resetToStandardConfig,
  saveConfigToFile,
  setStandardConfig,
  updateCellTypeUI,
  updateModeUI,
  updateToggleGroups,
  updateWaveOpticsUI,
} from "./form-state.js";
import { renderErrorPlots, renderSimulationPlots, renderUnstablePlots, resizePlots } from "./renderers.js";
import {
  buildWaveOpticsSignature,
  createWaveOpticsState,
  isWaveOpticsFresh,
  isWaveOpticsStale,
  markWaveOpticsPending,
  storeWaveOpticsError,
  storeWaveOpticsResult,
} from "./wave-optics-state.js";

const sidebar = document.getElementById("sidebar");
const backdrop = document.getElementById("sidebar-backdrop");
const openSidebarButton = document.getElementById("open-sidebar");
const closeSidebarButton = document.getElementById("close-sidebar");
const statusMessage = document.getElementById("status-msg");
const stabilityOutput = document.getElementById("calc-stab");
const cavityWaistOutput = document.getElementById("calc-w0");
const mirrorBeamOutput = document.getElementById("calc-wm");
const effectiveM2Output = document.getElementById("display-eff-m2");
const setStandardButton = document.getElementById("set-standard");
const resetButton = document.getElementById("reset-defaults");
const saveButton = document.getElementById("save-config");
const loadButton = document.getElementById("load-config-trigger");
const fileInput = document.getElementById("config-upload");
const waveOpticsButton = document.getElementById("calculate-wave-optics");
const waveOpticsStatus = document.getElementById("wave-optics-status");
const waveOpticsSummary = document.getElementById("wave-optics-summary");

let simulationTimer = null;
let activeController = null;
let activeWaveController = null;
let currentSimulationResult = null;
let waveOpticsState = createWaveOpticsState();

function toggleSidebar(show) {
  if (show) {
    sidebar.classList.remove("-translate-x-full");
    backdrop.classList.remove("hidden");
    void backdrop.offsetWidth;
    backdrop.classList.remove("opacity-0");
  } else {
    sidebar.classList.add("-translate-x-full");
    backdrop.classList.add("opacity-0");
    window.setTimeout(() => backdrop.classList.add("hidden"), 300);
  }

  window.setTimeout(() => {
    window.dispatchEvent(new Event("resize"));
  }, 350);
}

function setStatus(text, className) {
  statusMessage.textContent = text;
  statusMessage.className = className;
}

function setWaveOpticsStatus(text, className, summary = "") {
  waveOpticsStatus.textContent = text;
  waveOpticsStatus.className = className;
  waveOpticsSummary.textContent = summary;
  waveOpticsButton.disabled = Boolean(waveOpticsState.pending);
}

function setLoadingState() {
  setStatus("Calculating...", "font-semibold text-slate-500 text-xs text-right break-words max-w-[120px]");
}

function applyReadouts(result) {
  const stability = result.stability.product;
  stabilityOutput.textContent = stability != null ? stability.toFixed(4) : "--";
  effectiveM2Output.textContent = `${result.mode.M2x.toFixed(2)}, ${result.mode.M2y.toFixed(2)}`;

  if (!result.cavity) {
    cavityWaistOutput.textContent = "--";
    mirrorBeamOutput.textContent = "--";
    setStatus(
      result.status_message,
      "font-semibold text-red-600 text-xs text-right break-words max-w-[120px]",
    );
    return;
  }

  cavityWaistOutput.textContent = `x:${result.cavity.cavity_waist_x_mm.toFixed(2)} y:${result.cavity.cavity_waist_y_mm.toFixed(2)}`;

  if (result.cavity.mirror_beam_x_mm != null && result.cavity.mirror_beam_y_mm != null) {
    mirrorBeamOutput.textContent = `x:${result.cavity.mirror_beam_x_mm.toFixed(2)} y:${result.cavity.mirror_beam_y_mm.toFixed(2)}`;
  } else {
    mirrorBeamOutput.textContent = `M1:${result.cavity.mirror1_display_beam_mm.toFixed(2)} M2:${result.cavity.mirror2_display_beam_mm.toFixed(2)}`;
  }

  if (result.status_message.includes("Out Hole")) {
    setStatus(result.status_message, "font-semibold text-green-600 text-xs text-right break-words max-w-[120px]");
  } else if (result.status_message.includes("Escaped")) {
    setStatus(result.status_message, "font-semibold text-red-600 text-xs text-right break-words max-w-[120px]");
  } else {
    setStatus(result.status_message, "font-semibold text-amber-600 text-xs text-right break-words max-w-[120px]");
  }
}

function currentWaveOpticsPayload(config = captureConfig()) {
  return buildWaveOpticsRequest(config);
}

function currentWaveOpticsSignature(config = captureConfig()) {
  return buildWaveOpticsSignature(currentWaveOpticsPayload(config));
}

function getActiveWaveOptics(config = captureConfig()) {
  const signature = currentWaveOpticsSignature(config);
  if (!isWaveOpticsFresh(waveOpticsState, signature)) {
    return null;
  }
  return waveOpticsState.result?.wave_optics ?? null;
}

function renderCurrentPlots(config = captureConfig()) {
  if (!currentSimulationResult) {
    return;
  }

  const waveOptics = getActiveWaveOptics(config);
  if (currentSimulationResult.stable && currentSimulationResult.ray_trace && currentSimulationResult.beam_propagation) {
    renderSimulationPlots(currentSimulationResult, config.show_beam_profiles, waveOptics);
  } else {
    renderUnstablePlots(currentSimulationResult.status_message);
  }
}

function refreshWaveOpticsStatus(config = captureConfig()) {
  const signature = currentWaveOpticsSignature(config);
  const warningCount = waveOpticsState.result?.wave_optics?.warnings?.length ?? 0;

  if (waveOpticsState.pending) {
    setWaveOpticsStatus(
      "Calculating...",
      "text-xs font-semibold text-slate-600",
      "Adaptive 2D propagation is running on the current mirror-to-focus-to-mirror path.",
    );
    return;
  }

  if (!waveOpticsState.result && waveOpticsState.error) {
    setWaveOpticsStatus("Failed", "text-xs font-semibold text-red-600", waveOpticsState.error);
    return;
  }

  if (!waveOpticsState.result) {
    setWaveOpticsStatus(
      "Not Calculated",
      "text-xs font-semibold text-slate-500",
      "The fast ABCD/Gaussian beam overlays are active until you run the wave-optics solver.",
    );
    return;
  }

  if (isWaveOpticsFresh(waveOpticsState, signature)) {
    const summary = warningCount > 0
      ? `${warningCount} sampling warning${warningCount === 1 ? "" : "s"} reported.`
      : "Fresh wave-optics profiles are active on the mirror/focus plots.";
    setWaveOpticsStatus(
      warningCount > 0 ? "Fresh With Warnings" : "Fresh",
      warningCount > 0 ? "text-xs font-semibold text-amber-600" : "text-xs font-semibold text-emerald-600",
      summary,
    );
    return;
  }

  const staleSummary = waveOpticsState.error
    ? `${waveOpticsState.error} The UI is showing the fast analytic fallback.`
    : "Inputs changed after the last 2D run. The UI has fallen back to the fast analytic overlays.";
  if (isWaveOpticsStale(waveOpticsState, signature)) {
    setWaveOpticsStatus("Stale", "text-xs font-semibold text-amber-600", staleSummary);
    return;
  }

  setWaveOpticsStatus("Unavailable", "text-xs font-semibold text-slate-500", "Wave-optics data is not available.");
}

function handleSimulationError(error) {
  currentSimulationResult = null;
  stabilityOutput.textContent = "--";
  cavityWaistOutput.textContent = "--";
  mirrorBeamOutput.textContent = "--";

  const message =
    error instanceof ApiError
      ? error.message
      : error instanceof Error
        ? error.message
        : "Backend request failed.";

  setStatus(message, "font-semibold text-red-600 text-xs text-right break-words max-w-[120px]");
  renderErrorPlots(message);
  refreshWaveOpticsStatus();
  console.error(error);
}

async function runSimulation() {
  const config = captureConfig();
  const request = buildSimulationRequest(config);

  if (activeController) {
    activeController.abort();
  }

  const controller = new AbortController();
  activeController = controller;
  setLoadingState();

  try {
    const result = await simulateConfiguration(request, { signal: controller.signal });
    if (activeController !== controller) {
      return;
    }

    currentSimulationResult = result;
    applyResolvedInputs(result.resolved_inputs);
    applyReadouts(result);
    renderCurrentPlots(captureConfig());
    refreshWaveOpticsStatus(captureConfig());
  } catch (error) {
    if (error?.name === "AbortError") {
      return;
    }

    if (activeController !== controller) {
      return;
    }

    handleSimulationError(error);
  } finally {
    if (activeController === controller) {
      activeController = null;
    }
  }
}

async function runWaveOptics() {
  const config = captureConfig();
  const payload = currentWaveOpticsPayload(config);
  const signature = buildWaveOpticsSignature(payload);

  if (activeWaveController) {
    activeWaveController.abort();
  }

  const controller = new AbortController();
  activeWaveController = controller;
  waveOpticsState = markWaveOpticsPending(waveOpticsState);
  refreshWaveOpticsStatus(config);

  try {
    const result = await simulateWaveOptics(payload, { signal: controller.signal });
    if (activeWaveController !== controller) {
      return;
    }

    waveOpticsState = storeWaveOpticsResult(waveOpticsState, signature, result);
    refreshWaveOpticsStatus(captureConfig());
    renderCurrentPlots(captureConfig());
  } catch (error) {
    if (error?.name === "AbortError") {
      return;
    }

    if (activeWaveController !== controller) {
      return;
    }

    const message =
      error instanceof ApiError
        ? error.message
        : error instanceof Error
          ? error.message
          : "Wave-optics request failed.";
    waveOpticsState = storeWaveOpticsError(waveOpticsState, message);
    refreshWaveOpticsStatus(captureConfig());
    renderCurrentPlots(captureConfig());
    console.error(error);
  } finally {
    if (activeWaveController === controller) {
      activeWaveController = null;
    }
    refreshWaveOpticsStatus(captureConfig());
  }
}

function scheduleSimulation() {
  window.clearTimeout(simulationTimer);
  simulationTimer = window.setTimeout(() => {
    void runSimulation();
  }, 40);
}

function handleFastInputChange() {
  refreshWaveOpticsStatus(captureConfig());
  scheduleSimulation();
}

function handleWaveOpticsInputChange() {
  updateWaveOpticsUI();
  refreshWaveOpticsStatus(captureConfig());
  renderCurrentPlots(captureConfig());
}

function bindUiEvents() {
  openSidebarButton.addEventListener("click", () => toggleSidebar(true));
  closeSidebarButton.addEventListener("click", () => toggleSidebar(false));
  backdrop.addEventListener("click", () => toggleSidebar(false));

  document.getElementById("cell-type").addEventListener("change", () => {
    updateCellTypeUI();
    handleFastInputChange();
  });

  ["auto-R", "auto-R-vex", "auto-out-hole", "auto-mode-match", "auto-injection"].forEach((id) => {
    document.getElementById(id).addEventListener("change", () => {
      updateToggleGroups();
      handleFastInputChange();
    });
  });

  document.getElementById("out-mirror").addEventListener("change", handleFastInputChange);
  document.getElementById("mode-type").addEventListener("change", () => {
    updateModeUI();
    handleFastInputChange();
  });
  document.getElementById("show-beam-profiles").addEventListener("change", () => {
    renderCurrentPlots(captureConfig());
  });

  bindNumericFields(handleFastInputChange);
  bindWaveOpticsFields(handleWaveOpticsInputChange);
  waveOpticsButton.addEventListener("click", () => {
    void runWaveOptics();
  });

  setStandardButton.addEventListener("click", () => {
    setStandardConfig();
    flashStandardSaved();
  });

  resetButton.addEventListener("click", () => {
    resetToStandardConfig();
    updateWaveOpticsUI();
    refreshWaveOpticsStatus(captureConfig());
    void runSimulation();
  });

  saveButton.addEventListener("click", saveConfigToFile);
  loadButton.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", async (event) => {
    const [file] = event.target.files ?? [];
    if (!file) {
      return;
    }

    try {
      await loadConfigFromFile(file);
      updateWaveOpticsUI();
      refreshWaveOpticsStatus(captureConfig());
      void runSimulation();
    } catch (error) {
      handleSimulationError(error instanceof Error ? error : new Error("Error parsing config file."));
    } finally {
      event.target.value = "";
    }
  });
}

function initialize() {
  updateCellTypeUI();
  updateModeUI();
  updateWaveOpticsUI();
  updateToggleGroups();
  initializeStandardConfig();
  bindUiEvents();
  refreshWaveOpticsStatus(captureConfig());
  void runSimulation();
  window.addEventListener("resize", resizePlots);
}

initialize();
