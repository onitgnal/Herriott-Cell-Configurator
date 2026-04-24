import {
  clamp,
  evaluateModeIntensity,
  vDot,
  vNormalize,
} from "./simulation-reference.js";

const Plotly = window.Plotly;

function turboColor(value) {
  const normalized = clamp(value, 0, 1);
  const r =
    34.61 +
    normalized *
      (1172.33 + normalized * (-10793.56 + normalized * (33300.12 + normalized * (-38394.49 + normalized * 14825.05))));
  const g =
    23.31 +
    normalized *
      (557.33 + normalized * (1225.33 + normalized * (-3574.96 + normalized * (1073.77 + normalized * 707.56))));
  const b =
    27.2 +
    normalized *
      (3211.1 + normalized * (-15327.97 + normalized * (27814 + normalized * (-22569.18 + normalized * 6838.66))));
  return [
    Math.round(clamp(r, 0, 255)),
    Math.round(clamp(g, 0, 255)),
    Math.round(clamp(b, 0, 255)),
  ];
}

function generateSpotDataUrl(waistX, waistY, u1, u2, mode, sizePx = 60) {
  const canvas = document.createElement("canvas");
  canvas.width = sizePx;
  canvas.height = sizePx;
  const context = canvas.getContext("2d");
  const imageData = context.createImageData(sizePx, sizePx);
  const data = imageData.data;
  const boxSize = 4 * Math.max(waistX, waistY);

  let index = 0;
  for (let pixelY = 0; pixelY < sizePx; pixelY += 1) {
    const deltaY = (0.5 - pixelY / (sizePx - 1)) * boxSize;
    for (let pixelX = 0; pixelX < sizePx; pixelX += 1) {
      const deltaX = (pixelX / (sizePx - 1) - 0.5) * boxSize;
      const localX = deltaX * u1[0] + deltaY * u1[1];
      const localY = deltaX * u2[0] + deltaY * u2[1];
      const intensity = clamp(evaluateModeIntensity(localX, localY, waistX, waistY, mode), 0, 1);
      const alpha = intensity < 0.01 ? 0 : 255;
      const [r, g, b] = turboColor(intensity);

      data[index] = r;
      data[index + 1] = g;
      data[index + 2] = b;
      data[index + 3] = alpha;
      index += 4;
    }
  }

  context.putImageData(imageData, 0, 0);
  return { url: canvas.toDataURL(), box_size: boxSize };
}

function renderPlaceholderPlot(divId, title, message) {
  Plotly.react(
    divId,
    [],
    {
      title: {
        text: title,
        font: { size: 13, color: "#334155" },
      },
      margin: { l: 20, r: 20, b: 20, t: 40 },
      xaxis: { visible: false },
      yaxis: { visible: false },
      annotations: message
        ? [
            {
              text: message,
              xref: "paper",
              yref: "paper",
              x: 0.5,
              y: 0.5,
              showarrow: false,
              font: { size: 14, color: "#64748b" },
            },
          ]
        : [],
    },
    { responsive: true },
  );
}

function renderWaistPlot(beamPropagation, totalPasses, mirrorDistanceMm, modeTitle) {
  const maxIndex = totalPasses * 20 + 1;
  const zPlot = beamPropagation.x.z_vals.slice(0, maxIndex);
  const wxPlot = beamPropagation.x.w_vals.slice(0, maxIndex);
  const wyPlot = beamPropagation.y.w_vals.slice(0, maxIndex);
  const maxWaist = Math.max(...wxPlot, ...wyPlot);

  const traces = [
    {
      x: zPlot.concat(zPlot.slice().reverse()),
      y: wxPlot.concat(wxPlot.map((waist) => -waist).reverse()),
      fill: "toself",
      fillcolor: "rgba(217, 70, 239, 0.15)",
      line: { color: "transparent" },
      hoverinfo: "none",
      name: "Profile X",
    },
    {
      x: zPlot.concat(zPlot.slice().reverse()),
      y: wyPlot.concat(wyPlot.map((waist) => -waist).reverse()),
      fill: "toself",
      fillcolor: "rgba(14, 165, 233, 0.15)",
      line: { color: "transparent" },
      hoverinfo: "none",
      name: "Profile Y",
    },
    { x: zPlot, y: wxPlot, mode: "lines", line: { color: "#d946ef", width: 2 }, name: "+wx" },
    { x: zPlot, y: wxPlot.map((waist) => -waist), mode: "lines", line: { color: "#d946ef", width: 2 }, showlegend: false },
    { x: zPlot, y: wyPlot, mode: "lines", line: { color: "#0ea5e9", width: 2, dash: "dot" }, name: "+wy" },
    { x: zPlot, y: wyPlot.map((waist) => -waist), mode: "lines", line: { color: "#0ea5e9", width: 2, dash: "dot" }, showlegend: false },
  ];

  const mirrorShapes = beamPropagation.x.w_mirrors_w.slice(0, totalPasses + 1).map((_, index) => ({
    type: "line",
    x0: index * mirrorDistanceMm,
    x1: index * mirrorDistanceMm,
    y0: -maxWaist * 1.1,
    y1: maxWaist * 1.1,
    line: { color: "rgba(100, 116, 139, 0.4)", width: 1.5, dash: "dash" },
  }));

  Plotly.react(
    "plotWaist",
    traces,
    {
      title: { text: `Gaussian Beam (${modeTitle})`, font: { size: 13, color: "#334155" } },
      margin: { l: 45, r: 25, b: 40, t: 30 },
      xaxis: { title: "Unfolded Path Distance z [mm]", range: [0, totalPasses * mirrorDistanceMm], zeroline: false },
      yaxis: { title: "Beam Radius w [mm]", range: [-maxWaist * 1.15, maxWaist * 1.15] },
      showlegend: true,
      legend: { orientation: "h", y: 1.05, x: 1, xanchor: "right", yanchor: "bottom" },
      shapes: mirrorShapes,
      hovermode: "x unified",
    },
    { responsive: true },
  );
}

function renderRayPlots(result, showBeamProfiles) {
  const { ray_trace: rayTrace, beam_propagation: beamPropagation, resolved_inputs: inputs, mode } = result;
  const points = rayTrace.points;
  const hits = rayTrace.mirror_hits;
  const centerHits = rayTrace.center_hits;
  const inputBasis = rayTrace.input_basis;
  const inputPoint = rayTrace.input_point;

  const x3 = points.map((point) => point[2]);
  const y3 = points.map((point) => point[0]);
  const z3 = points.map((point) => point[1]);
  const colors = points.map((_, index) => index);

  const trace3d = {
    type: "scatter3d",
    mode: "lines",
    x: x3,
    y: y3,
    z: z3,
    line: { color: colors, colorscale: "Viridis", width: 3 },
  };
  const trace3dStart = {
    type: "scatter3d",
    mode: "markers",
    x: [x3[0]],
    y: [y3[0]],
    z: [z3[0]],
    marker: { color: "green", size: 6 },
  };
  const trace3dEnd = {
    type: "scatter3d",
    mode: "markers",
    x: [x3[x3.length - 1]],
    y: [y3[y3.length - 1]],
    z: [z3[z3.length - 1]],
    marker: { color: "red", size: 6 },
  };

  const limit = inputs.spot_pattern_radius_mm * 1.5;
  const plot3dDiv = document.getElementById("plot3d");
  const currentCamera = plot3dDiv?._fullLayout?.scene?.camera
    ? JSON.parse(JSON.stringify(plot3dDiv._fullLayout.scene.camera))
    : { eye: { x: 1.5, y: -1.5, z: 0.5 } };

  Plotly.react(
    "plot3d",
    [trace3d, trace3dStart, trace3dEnd],
    {
      title: { text: "3D Cavity Ray Path", font: { size: 13, color: "#334155" } },
      margin: { l: 0, r: 0, b: 0, t: 30 },
      showlegend: false,
      uirevision: "true",
      scene: {
        xaxis: { title: "Z Axis [mm]", range: [-10, inputs.mirror_distance_mm + 10] },
        yaxis: { title: "X [mm]", range: [-limit, limit] },
        zaxis: { title: "Y [mm]", range: [-limit, limit] },
        camera: currentCamera,
      },
    },
    { responsive: true },
  );

  const getRadialTextPosition = (x, y) => {
    let angle = (Math.atan2(y, x) * 180) / Math.PI;
    if (angle < 0) {
      angle += 360;
    }
    if (angle >= 337.5 || angle < 22.5) return "middle right";
    if (angle < 67.5) return "top right";
    if (angle < 112.5) return "top center";
    if (angle < 157.5) return "top left";
    if (angle < 202.5) return "middle left";
    if (angle < 247.5) return "bottom left";
    if (angle < 292.5) return "bottom center";
    return "bottom right";
  };

  const getRayAngleToNormalDeg = (ray, normal) => {
    if (!ray || !normal) {
      return null;
    }
    const cosTheta = clamp(Math.abs(vDot(vNormalize(ray), vNormalize(normal))), 0, 1);
    return (Math.acos(cosTheta) * 180) / Math.PI;
  };

  const getSteeringAnglesMrad = (ray) => {
    if (!ray || Math.abs(ray[2]) < 1e-12) {
      return null;
    }
    return {
      thx: (1000 * ray[0]) / ray[2],
      thy: (1000 * ray[1]) / ray[2],
    };
  };

  const formatSteeringAngles = (ray) => {
    const steering = getSteeringAnglesMrad(ray);
    if (!steering) {
      return "N/A";
    }
    return `(${steering.thx.toFixed(2)}, ${steering.thy.toFixed(2)}) mrad`;
  };

  const getMirrorRayInfoHtml = (hit) => {
    const incidenceAngle = getRayAngleToNormalDeg(hit.v_in, hit.normal);
    if (incidenceAngle == null) {
      return "";
    }
    const reflectedSteering = hit.v_out ? formatSteeringAngles(hit.v_out) : "N/A (hole exit)";
    return `<br>Incidence: ${incidenceAngle.toFixed(2)}°<br>Incoming (θx, θy): ${formatSteeringAngles(hit.v_in)}<br>Reflected (θx, θy): ${reflectedSteering}`;
  };

  const baseLayout = {
    margin: { l: 40, r: 40, b: 40, t: 60 },
    uirevision: "true",
    showlegend: false,
    xaxis: { title: "X [mm]", range: [-limit, limit], zeroline: false },
    yaxis: { title: "Y [mm]", range: [-limit, limit], zeroline: false, scaleanchor: "x", scaleratio: 1 },
  };

  const build2dPlot = (divId, title, hitsData, getWIndex, isCenter, mirrorNumber) => {
    const layout = JSON.parse(JSON.stringify(baseLayout));
    layout.shapes = [];
    layout.images = [];

    const px = [];
    const py = [];
    const text = [];
    const positions = [];
    const hover = [];
    const colorscale = [];
    const polX = [];
    const polY = [];

    const wxArray = isCenter ? beamPropagation.x.w_center_w : beamPropagation.x.w_mirrors_w;
    const wyArray = isCenter ? beamPropagation.y.w_center_w : beamPropagation.y.w_mirrors_w;
    let minIntensity = Number.POSITIVE_INFINITY;
    let maxIntensity = Number.NEGATIVE_INFINITY;
    let minFluence = Number.POSITIVE_INFINITY;
    let maxFluence = Number.NEGATIVE_INFINITY;

    const inputHole = [inputs.input_hole_x_mm, inputs.input_hole_y_mm];
    const outputHole = [inputs.output_hole_x_mm, inputs.output_hole_y_mm];

    if (mirrorNumber === 1) {
      layout.shapes.push({
        type: "circle",
        x0: inputHole[0] - inputs.hole_radius_mm,
        y0: inputHole[1] - inputs.hole_radius_mm,
        x1: inputHole[0] + inputs.hole_radius_mm,
        y1: inputHole[1] + inputs.hole_radius_mm,
        line: { color: "#16a34a", width: 2, dash: "dot" },
      });

      if (inputs.output_mirror === 1) {
        layout.shapes.push({
          type: "circle",
          x0: outputHole[0] - inputs.hole_radius_mm,
          y0: outputHole[1] - inputs.hole_radius_mm,
          x1: outputHole[0] + inputs.hole_radius_mm,
          y1: outputHole[1] + inputs.hole_radius_mm,
          line: { color: "#ef4444", width: 2 },
        });
      }
    } else if (mirrorNumber === 2 && inputs.output_mirror === 2) {
      layout.shapes.push({
        type: "circle",
        x0: outputHole[0] - inputs.hole_radius_mm,
        y0: outputHole[1] - inputs.hole_radius_mm,
        x1: outputHole[0] + inputs.hole_radius_mm,
        y1: outputHole[1] + inputs.hole_radius_mm,
        line: { color: "#ef4444", width: 2 },
      });
    }

    hitsData.forEach((hit, index) => {
      const waistIndex = getWIndex(index);
      const waistX = wxArray[waistIndex] ?? wxArray[wxArray.length - 1];
      const waistY = wyArray[waistIndex] ?? wyArray[wyArray.length - 1];
      const areaFactor = waistX * waistY;
      const intensity = (100 * (inputs.peak_power_gw * mode.peak_factor)) / areaFactor;
      const fluence = (100 * (inputs.pulse_energy_mj * mode.peak_factor)) / areaFactor;

      minIntensity = Math.min(minIntensity, intensity);
      maxIntensity = Math.max(maxIntensity, intensity);
      minFluence = Math.min(minFluence, fluence);
      maxFluence = Math.max(maxFluence, fluence);

      px.push(hit.P[0]);
      py.push(hit.P[1]);

      let label = isCenter ? String(index + 1) : String(waistIndex);
      if (
        !isCenter &&
        mirrorNumber === inputs.output_mirror &&
        hit === hitsData[hitsData.length - 1] &&
        result.status_message.includes("Out Hole")
      ) {
        label = "<b>Out</b>";
      }

      text.push(label);
      positions.push(getRadialTextPosition(hit.P[0], hit.P[1]));

      let hoverAngle = (Math.atan2(hit.u1[1], hit.u1[0]) * 180) / Math.PI;
      while (hoverAngle <= -90) {
        hoverAngle += 180;
      }
      while (hoverAngle > 90) {
        hoverAngle -= 180;
      }

      const rayAngleHtml = !isCenter && mirrorNumber !== 0 ? getMirrorRayInfoHtml(hit) : "";
      hover.push(
        `Hit: ${label}<br>X: ${hit.P[0].toFixed(2)}<br>Y: ${hit.P[1].toFixed(2)}<br>wx: ${waistX.toFixed(3)}<br>wy: ${waistY.toFixed(3)}<br>Pol: ${hoverAngle.toFixed(1)}°${rayAngleHtml}<br>Intensity: ${intensity.toFixed(2)} GW/cm²<br>Fluence: ${fluence.toFixed(2)} mJ/cm²`,
      );
      colorscale.push(waistIndex);

      const maxWaist = Math.max(waistX, waistY);
      if (showBeamProfiles) {
        const image = generateSpotDataUrl(waistX, waistY, hit.u1, hit.u2, mode, 60);
        layout.images.push({
          source: image.url,
          xref: "x",
          yref: "y",
          x: hit.P[0],
          y: hit.P[1],
          sizex: image.box_size,
          sizey: image.box_size,
          xanchor: "center",
          yanchor: "middle",
          layer: "below",
        });

        const vectorLength = maxWaist * 1.5;
        polX.push(hit.P[0] - vectorLength * hit.u1[0], hit.P[0] + vectorLength * hit.u1[0], null);
        polY.push(hit.P[1] - vectorLength * hit.u1[1], hit.P[1] + vectorLength * hit.u1[1], null);
      } else {
        layout.shapes.push({
          type: "circle",
          x0: hit.P[0] - maxWaist,
          y0: hit.P[1] - maxWaist,
          x1: hit.P[0] + maxWaist,
          y1: hit.P[1] + maxWaist,
          line: { color: "rgba(217, 70, 239, 0.6)", width: 1.5 },
          fillcolor: "rgba(217, 70, 239, 0.15)",
        });
      }
    });

    if (hitsData.length === 0) {
      minIntensity = 0;
      maxIntensity = 0;
      minFluence = 0;
      maxFluence = 0;
    }

    const statsHtml = `<br><span style="font-size:11px; color:#64748b; font-weight:normal;">Fluence: ${minFluence.toFixed(2)} - ${maxFluence.toFixed(2)} mJ/cm² | Intensity: ${minIntensity.toFixed(2)} - ${maxIntensity.toFixed(2)} GW/cm²</span>`;
    layout.title = { text: title + statsHtml, font: { size: 13, color: "#334155" }, y: 0.95 };

    if (isCenter && hitsData.length > 0) {
      const maxExtent = Math.max(...px.map(Math.abs), ...py.map(Math.abs)) * 1.2 + 2;
      layout.xaxis.range = [-maxExtent, maxExtent];
      layout.yaxis.range = [-maxExtent, maxExtent];
    }

    const traces = [
      {
        x: px,
        y: py,
        mode: "markers+text",
        type: "scatter",
        text,
        textposition: positions,
        hovertext: hover,
        hoverinfo: "text",
        textfont: { size: 10, color: "#475569" },
        marker: { color: colorscale, colorscale: "Viridis", size: 8, line: { color: "white", width: 1 } },
      },
    ];

    if (mirrorNumber === 1) {
      const waistX = wxArray[0];
      const waistY = wyArray[0];
      let hoverAngle = (Math.atan2(inputBasis.u1[1], inputBasis.u1[0]) * 180) / Math.PI;
      while (hoverAngle <= -90) {
        hoverAngle += 180;
      }
      while (hoverAngle > 90) {
        hoverAngle -= 180;
      }

      traces.push({
        x: [inputPoint[0]],
        y: [inputPoint[1]],
        mode: "markers+text",
        type: "scatter",
        text: ["<b>In</b>"],
        textposition: getRadialTextPosition(inputPoint[0], inputPoint[1]),
        hovertext: [`Start (0)<br>X: ${inputPoint[0].toFixed(2)}<br>Y: ${inputPoint[1].toFixed(2)}<br>Pol: ${hoverAngle.toFixed(1)}°`],
        hoverinfo: "text",
        textfont: { size: 11, color: "#16a34a" },
        marker: { color: "#16a34a", size: 8, symbol: "star" },
      });

      if (showBeamProfiles) {
        const image = generateSpotDataUrl(waistX, waistY, inputBasis.u1, inputBasis.u2, mode, 60);
        layout.images.push({
          source: image.url,
          xref: "x",
          yref: "y",
          x: inputPoint[0],
          y: inputPoint[1],
          sizex: image.box_size,
          sizey: image.box_size,
          xanchor: "center",
          yanchor: "middle",
          layer: "below",
        });

        const vectorLength = Math.max(waistX, waistY) * 1.5;
        polX.push(inputPoint[0] - vectorLength * inputBasis.u1[0], inputPoint[0] + vectorLength * inputBasis.u1[0], null);
        polY.push(inputPoint[1] - vectorLength * inputBasis.u1[1], inputPoint[1] + vectorLength * inputBasis.u1[1], null);
      }
    }

    if (showBeamProfiles && polX.length > 0) {
      traces.push({
        x: polX,
        y: polY,
        mode: "lines",
        line: { color: "#1e293b", width: 2 },
        hoverinfo: "none",
        name: "Polarization",
      });
    }

    Plotly.react(divId, traces, layout, { responsive: true });
  };

  build2dPlot("plotM1", "Mirror 1 Spots (z=0)", hits[1] || [], (index) => 2 * index + 2, false, 1);
  build2dPlot("plotCenter", "Center Spots (z=L/2)", centerHits, (index) => index, true, 0);
  build2dPlot("plotM2", "Mirror 2 Spots (z=L)", hits[2] || [], (index) => 2 * index + 1, false, 2);
}

export function renderSimulationPlots(result, showBeamProfiles) {
  renderWaistPlot(result.beam_propagation, result.resolved_inputs.total_passes, result.resolved_inputs.mirror_distance_mm, result.mode.title);
  renderRayPlots(result, showBeamProfiles);
}

export function renderUnstablePlots(statusMessage) {
  renderPlaceholderPlot("plotWaist", "Gaussian Beam (Unstable)", statusMessage);
  renderPlaceholderPlot("plot3d", "3D Cavity Ray Path", "No ray trace for unstable cavity.");
  renderPlaceholderPlot("plotM1", "Mirror 1 Spots (z=0)", "No spot data.");
  renderPlaceholderPlot("plotCenter", "Center Spots (z=L/2)", "No spot data.");
  renderPlaceholderPlot("plotM2", "Mirror 2 Spots (z=L)", "No spot data.");
}

export function renderErrorPlots(message) {
  renderPlaceholderPlot("plotWaist", "Gaussian Beam", message);
  renderPlaceholderPlot("plot3d", "3D Cavity Ray Path", message);
  renderPlaceholderPlot("plotM1", "Mirror 1 Spots (z=0)", message);
  renderPlaceholderPlot("plotCenter", "Center Spots (z=L/2)", message);
  renderPlaceholderPlot("plotM2", "Mirror 2 Spots (z=L)", message);
}

export function resizePlots() {
  Plotly.Plots.resize("plotWaist");
  Plotly.Plots.resize("plot3d");
  Plotly.Plots.resize("plotM1");
  Plotly.Plots.resize("plotCenter");
  Plotly.Plots.resize("plotM2");
}
