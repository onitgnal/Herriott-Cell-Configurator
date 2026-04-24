import { ApiError, simulateConfiguration } from "./api-client.js";
import {
  applyResolvedInputs,
  bindNumericFields,
  buildSimulationRequest,
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
} from "./form-state.js";
import { renderErrorPlots, renderSimulationPlots, renderUnstablePlots, resizePlots } from "./renderers.js";

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

let simulationTimer = null;
let activeController = null;

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

function handleSimulationError(error) {
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

    applyResolvedInputs(result.resolved_inputs);
    applyReadouts(result);

    if (result.stable && result.ray_trace && result.beam_propagation) {
      renderSimulationPlots(result, config.show_beam_profiles);
    } else {
      renderUnstablePlots(result.status_message);
    }
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

function scheduleSimulation() {
  window.clearTimeout(simulationTimer);
  simulationTimer = window.setTimeout(() => {
    void runSimulation();
  }, 40);
}

function bindUiEvents() {
  openSidebarButton.addEventListener("click", () => toggleSidebar(true));
  closeSidebarButton.addEventListener("click", () => toggleSidebar(false));
  backdrop.addEventListener("click", () => toggleSidebar(false));

  document.getElementById("cell-type").addEventListener("change", () => {
    updateCellTypeUI();
    scheduleSimulation();
  });

  ["auto-R", "auto-R-vex", "auto-out-hole", "auto-mode-match", "auto-injection"].forEach((id) => {
    document.getElementById(id).addEventListener("change", () => {
      updateToggleGroups();
      scheduleSimulation();
    });
  });

  document.getElementById("out-mirror").addEventListener("change", scheduleSimulation);
  document.getElementById("mode-type").addEventListener("change", () => {
    updateModeUI();
    scheduleSimulation();
  });
  document.getElementById("show-beam-profiles").addEventListener("change", scheduleSimulation);

  bindNumericFields(scheduleSimulation);

  setStandardButton.addEventListener("click", () => {
    setStandardConfig();
    flashStandardSaved();
  });

  resetButton.addEventListener("click", () => {
    resetToStandardConfig();
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
  updateToggleGroups();
  initializeStandardConfig();
  bindUiEvents();
  void runSimulation();
  window.addEventListener("resize", resizePlots);
}

initialize();
