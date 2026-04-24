const EPSILON = 1e-9;

export function vAdd(a, b) {
  return [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
}

export function vSub(a, b) {
  return [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
}

export function vDot(a, b) {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

export function vNorm(a) {
  return Math.sqrt(vDot(a, a));
}

export function vScale(a, scalar) {
  return [a[0] * scalar, a[1] * scalar, a[2] * scalar];
}

export function vNormalize(a) {
  return vScale(a, 1 / vNorm(a));
}

export function vCross(a, b) {
  return [
    a[1] * b[2] - a[2] * b[1],
    a[2] * b[0] - a[0] * b[2],
    a[0] * b[1] - a[1] * b[0],
  ];
}

export function clamp(value, lower, upper) {
  return Math.max(lower, Math.min(upper, value));
}

function finiteOrNull(value) {
  return Number.isFinite(value) ? value : null;
}

export function hermite(n, x) {
  if (n === 0) {
    return 1;
  }
  if (n === 1) {
    return 2 * x;
  }

  let h0 = 1;
  let h1 = 2 * x;
  let hn = h1;

  for (let i = 1; i < n; i += 1) {
    hn = 2 * x * h1 - 2 * i * h0;
    h0 = h1;
    h1 = hn;
  }

  return hn;
}

export function laguerre(p, l, x) {
  if (p === 0) {
    return 1;
  }
  if (p === 1) {
    return 1 + l - x;
  }

  let l0 = 1;
  let l1 = 1 + l - x;
  let lp = l1;

  for (let i = 1; i < p; i += 1) {
    lp = ((2 * i + 1 + l - x) * l1 - (i + l) * l0) / (i + 1);
    l0 = l1;
    l1 = lp;
  }

  return lp;
}

export function computeModeNorm(mode) {
  let maxIntensity = 0;
  let sumIntensity = 0;
  const ds = 0.1;

  for (let sx = -4; sx <= 4; sx += ds) {
    for (let sy = -4; sy <= 4; sy += ds) {
      let intensity = 0;
      const expTerm = Math.exp(-0.5 * (sx * sx + sy * sy));

      if (mode.type === "hg") {
        const hx = hermite(mode.n, sx);
        const hy = hermite(mode.m, sy);
        const field = hx * hy * expTerm;
        intensity = field * field;
      } else if (mode.type === "lg") {
        const r2 = sx * sx + sy * sy;
        const laguerreValue = laguerre(mode.p, mode.l, r2);
        const field = Math.pow(r2, Math.abs(mode.l) / 2) * laguerreValue * expTerm;
        intensity = field * field;
      } else {
        intensity = expTerm * expTerm;
      }

      if (intensity > maxIntensity) {
        maxIntensity = intensity;
      }
      sumIntensity += intensity;
    }
  }

  sumIntensity *= ds * ds;

  return {
    norm: maxIntensity > 0 ? 1 / maxIntensity : 1,
    peak_factor: maxIntensity > 0 ? (2 * maxIntensity) / sumIntensity : 2 / Math.PI,
  };
}

export function evaluateModeIntensity(localX, localY, waistX, waistY, mode) {
  let baseWaistX = waistX;
  let baseWaistY = waistY;

  if (mode.type === "hg" || mode.type === "lg") {
    baseWaistX = waistX / Math.sqrt(mode.M2x || 1);
    baseWaistY = waistY / Math.sqrt(mode.M2y || 1);
  }

  const scaledX = Math.SQRT2 * localX / baseWaistX;
  const scaledY = Math.SQRT2 * localY / baseWaistY;
  const expTerm = Math.exp(
    -(localX * localX) / (baseWaistX * baseWaistX) -
      (localY * localY) / (baseWaistY * baseWaistY),
  );

  if (mode.type === "tem00" || mode.type === "custom") {
    return expTerm * expTerm;
  }

  if (mode.type === "hg") {
    const hx = hermite(mode.n, scaledX);
    const hy = hermite(mode.m, scaledY);
    const field = hx * hy * expTerm;
    return field * field * mode.norm;
  }

  if (mode.type === "lg") {
    const symmetricWaist = (baseWaistX + baseWaistY) / 2;
    const r2Symmetric = (2 * (localX * localX + localY * localY)) / (symmetricWaist * symmetricWaist);
    const laguerreValue = laguerre(mode.p, mode.l, r2Symmetric);
    const field =
      Math.pow(r2Symmetric, Math.abs(mode.l) / 2) *
      laguerreValue *
      Math.exp(-(localX * localX + localY * localY) / (symmetricWaist * symmetricWaist));
    return field * field * mode.norm;
  }

  return 0;
}

export function propagateQ(q, a, b, c, d) {
  const numeratorReal = a * q.r + b;
  const numeratorImag = a * q.i;
  const denominatorReal = c * q.r + d;
  const denominatorImag = c * q.i;
  const denominatorMagnitudeSquared =
    denominatorReal * denominatorReal + denominatorImag * denominatorImag;

  return {
    r:
      (numeratorReal * denominatorReal + numeratorImag * denominatorImag) /
      denominatorMagnitudeSquared,
    i:
      (numeratorImag * denominatorReal - numeratorReal * denominatorImag) /
      denominatorMagnitudeSquared,
  };
}

export function getWaist(q, wavelengthMm, m2) {
  const magnitudeSquared = q.r * q.r + q.i * q.i;
  const inverseQImaginary = -q.i / magnitudeSquared;
  return Math.sqrt((m2 * wavelengthMm) / (Math.PI * -inverseQImaginary));
}

export function computeABCDAxis(
  mirrorDistanceMm,
  mirror1RadiusMm,
  mirror2RadiusMm,
  wavelengthMm,
  inputWaistMm,
  inputWaistPositionMm,
  maxPasses,
  m2,
) {
  const rayleighRange = (Math.PI * inputWaistMm * inputWaistMm) / (m2 * wavelengthMm);
  let q = { r: -inputWaistPositionMm, i: rayleighRange };

  const zVals = [];
  const wVals = [];
  const mirrorWaists = [];
  const centerWaists = [];
  const stepsPerPass = 20;
  let totalZ = 0;

  for (let pass = 0; pass < maxPasses; pass += 1) {
    for (let step = 0; step <= stepsPerPass; step += 1) {
      const distance = (step / stepsPerPass) * mirrorDistanceMm;
      const propagated = { r: q.r + distance, i: q.i };
      const waist = getWaist(propagated, wavelengthMm, m2);

      zVals.push(totalZ + distance);
      wVals.push(waist);

      if (step === 0) {
        mirrorWaists.push(waist);
      }
      if (step === stepsPerPass / 2) {
        centerWaists.push(waist);
      }
    }

    totalZ += mirrorDistanceMm;
    const qEnd = { r: q.r + mirrorDistanceMm, i: q.i };
    const currentRadius = pass % 2 === 0 ? mirror2RadiusMm : mirror1RadiusMm;
    q = propagateQ(qEnd, 1, 0, -2 / currentRadius, 1);
  }

  mirrorWaists.push(getWaist(q, wavelengthMm, m2));

  return {
    z_vals: zVals,
    w_vals: wVals,
    w_mirrors_w: mirrorWaists,
    w_center_w: centerWaists,
  };
}

function reflectVector(vector, normal) {
  return vSub(vector, vScale(normal, 2 * vDot(vector, normal)));
}

export class HerriottCell {
  constructor(
    mirrorDistanceMm,
    mirror1RadiusMm,
    mirror2RadiusMm,
    inputHole,
    outputHole,
    outputMirror,
    holeRadiusMm,
    mirror1Tilt,
    mirror2Tilt,
  ) {
    this.L = mirrorDistanceMm;
    this.R1 = mirror1RadiusMm;
    this.R2 = mirror2RadiusMm;
    this.in_hole = inputHole;
    this.out_hole = outputHole;
    this.out_mirror = outputMirror;
    this.hole_radius = holeRadiusMm;

    const tilt1X = mirror1Tilt[0] * Math.abs(mirror1RadiusMm);
    const tilt1Y = mirror1Tilt[1] * Math.abs(mirror1RadiusMm);
    const tilt1Magnitude = Math.sqrt(tilt1X * tilt1X + tilt1Y * tilt1Y) / Math.abs(mirror1RadiusMm);
    this.C1 = [
      tilt1Magnitude > EPSILON
        ? Math.abs(mirror1RadiusMm) * Math.sin(tilt1Magnitude) * (tilt1X / (tilt1Magnitude * Math.abs(mirror1RadiusMm)))
        : 0,
      tilt1Magnitude > EPSILON
        ? Math.abs(mirror1RadiusMm) * Math.sin(tilt1Magnitude) * (tilt1Y / (tilt1Magnitude * Math.abs(mirror1RadiusMm)))
        : 0,
      mirror1RadiusMm * Math.cos(tilt1Magnitude),
    ];

    const tilt2X = mirror2Tilt[0] * Math.abs(mirror2RadiusMm);
    const tilt2Y = mirror2Tilt[1] * Math.abs(mirror2RadiusMm);
    const tilt2Magnitude = Math.sqrt(tilt2X * tilt2X + tilt2Y * tilt2Y) / Math.abs(mirror2RadiusMm);
    this.C2 = [
      tilt2Magnitude > EPSILON
        ? Math.abs(mirror2RadiusMm) * Math.sin(tilt2Magnitude) * (tilt2X / (tilt2Magnitude * Math.abs(mirror2RadiusMm)))
        : 0,
      tilt2Magnitude > EPSILON
        ? Math.abs(mirror2RadiusMm) * Math.sin(tilt2Magnitude) * (tilt2Y / (tilt2Magnitude * Math.abs(mirror2RadiusMm)))
        : 0,
      mirrorDistanceMm - mirror2RadiusMm * Math.cos(tilt2Magnitude),
    ];
  }

  intersectMirror(point, direction, mirrorNumber) {
    const center = mirrorNumber === 1 ? this.C1 : this.C2;
    const radius = mirrorNumber === 1 ? this.R1 : this.R2;

    const delta = vSub(point, center);
    const b = vDot(direction, delta);
    const c = vDot(delta, delta) - radius * radius;
    const discriminant = b * b - c;

    if (discriminant < 0) {
      return { P_int: null, normal: null };
    }

    const t1 = -b - Math.sqrt(discriminant);
    const t2 = -b + Math.sqrt(discriminant);
    const validTs = [t1, t2].filter((value) => value > EPSILON);

    if (validTs.length === 0) {
      return { P_int: null, normal: null };
    }

    const t = Math.min(...validTs);
    const intersection = vAdd(point, vScale(direction, t));
    const normal = vScale(vSub(center, intersection), 1 / radius);
    return { P_int: intersection, normal };
  }

  traceRays(point0, direction0, basisU1, basisU2, maxPasses = 150) {
    const points = [point0];
    const mirrorHits = { 1: [] };
    const centerHits = [];
    const mirror2Hits = [];

    let point = point0;
    let direction = vNormalize(direction0);
    let u1 = vNormalize(basisU1);
    let u2 = vNormalize(basisU2);
    let targetMirror = 2;
    let exitStatus = "Trapped (Max Passes)";
    let bounce = 0;

    for (bounce = 0; bounce < maxPasses; bounce += 1) {
      const { P_int: intersection, normal } = this.intersectMirror(point, direction, targetMirror);

      const tCenter = (this.L / 2 - point[2]) / direction[2];
      const tMirror = intersection ? vNorm(vSub(intersection, point)) : Number.POSITIVE_INFINITY;

      if (tCenter > 0 && tCenter < tMirror) {
        const centerPoint = vAdd(point, vScale(direction, tCenter));
        centerHits.push({ P: centerPoint, u1: [...u1], u2: [...u2] });
      }

      if (!intersection) {
        exitStatus = `Escaped cell at pass ${bounce}`;
        break;
      }

      points.push(intersection);

      let escaped = false;
      const reflectedDirection = vNormalize(reflectVector(direction, normal));
      const reflectedU1 = vNormalize(reflectVector(u1, normal));
      const reflectedU2 = vNormalize(reflectVector(u2, normal));
      const hitRecord = {
        P: [...intersection],
        u1: [...u1],
        u2: [...u2],
        v_in: [...direction],
        v_out: [...reflectedDirection],
        normal: [...normal],
      };

      if (targetMirror === 1) {
        mirrorHits[1].push(hitRecord);

        if (this.out_mirror === 1) {
          const outputDistance = Math.sqrt(
            (intersection[0] - this.out_hole[0]) ** 2 + (intersection[1] - this.out_hole[1]) ** 2,
          );

          if (outputDistance <= this.hole_radius) {
            exitStatus = `Exited cleanly pass ${bounce + 1} (Out Hole)`;
            hitRecord.v_out = null;
            escaped = true;
          }
        }

        if (!escaped && bounce > 0) {
          const inputDistance = Math.sqrt(
            (intersection[0] - this.in_hole[0]) ** 2 + (intersection[1] - this.in_hole[1]) ** 2,
          );

          if (inputDistance <= this.hole_radius) {
            exitStatus = `Escaped pass ${bounce + 1} (In Hole)`;
            hitRecord.v_out = null;
            escaped = true;
          }
        }
      } else {
        mirror2Hits.push(hitRecord);

        if (this.out_mirror === 2) {
          const outputDistance = Math.sqrt(
            (intersection[0] - this.out_hole[0]) ** 2 + (intersection[1] - this.out_hole[1]) ** 2,
          );

          if (outputDistance <= this.hole_radius) {
            exitStatus = `Exited cleanly pass ${bounce + 1} (Out Hole)`;
            hitRecord.v_out = null;
            escaped = true;
          }
        }
      }

      if (escaped) {
        break;
      }

      direction = reflectedDirection;
      u1 = reflectedU1;
      u2 = reflectedU2;
      point = intersection;
      targetMirror = targetMirror === 1 ? 2 : 1;
    }

    mirrorHits[2] = mirror2Hits;

    return {
      points,
      mirror_hits: mirrorHits,
      center_hits: centerHits,
      exit_status: exitStatus,
      total_bounces: bounce,
    };
  }
}

export function resolveModeConfig(config) {
  const modeType = config.mode_type;
  const modeConfig = { type: modeType };
  let m2x = 1;
  let m2y = 1;
  let title = "Fundamental TEM00";

  if (modeType === "hg") {
    modeConfig.n = config.hermite_n;
    modeConfig.m = config.hermite_m;
    m2x = 2 * modeConfig.n + 1;
    m2y = 2 * modeConfig.m + 1;
    title = `HG<sub>${modeConfig.n},${modeConfig.m}</sub>`;
  } else if (modeType === "lg") {
    modeConfig.p = config.laguerre_p;
    modeConfig.l = config.laguerre_l;
    m2x = 2 * modeConfig.p + Math.abs(modeConfig.l) + 1;
    m2y = m2x;
    title = `LG<sub>${modeConfig.p},${modeConfig.l}</sub>`;
  } else if (modeType === "custom") {
    m2x = config.custom_m2;
    m2y = config.custom_m2;
    title = `Custom M²=${m2x.toFixed(2)}`;
  }

  const normData = computeModeNorm({ ...modeConfig, M2x: m2x, M2y: m2y });

  return {
    ...modeConfig,
    M2x: m2x,
    M2y: m2y,
    title,
    norm: normData.norm,
    peak_factor: normData.peak_factor,
  };
}

export function simulateConfiguration(config) {
  const mirrorDistanceMm = config.mirror_distance_mm;
  const totalPasses = config.total_passes;
  const revolutions = config.revolutions;
  const spotPatternRadiusMm = config.spot_pattern_radius_mm;
  const wavelengthMm = config.wavelength_nm * 1e-6;
  const holeRadiusMm = config.hole_radius_mm;
  const peakPowerGw = config.peak_power_gw;
  const pulseEnergyMj = config.pulse_energy_mj;
  const thetaRt = (2 * Math.PI * revolutions) / totalPasses;

  let mirror1RadiusMm;
  let mirror2RadiusMm;

  if (config.cell_type === "cav-cav") {
    if (config.auto_symmetric_radius) {
      const cActual = 1 - Math.cos(thetaRt / 2);
      mirror1RadiusMm = mirrorDistanceMm / cActual;
      mirror2RadiusMm = mirror1RadiusMm;
    } else {
      mirror1RadiusMm = config.symmetric_radius_mm;
      mirror2RadiusMm = config.symmetric_radius_mm;
    }
  } else if (config.auto_opposite_radii) {
    mirror1RadiusMm = mirrorDistanceMm / Math.sin(thetaRt / 2);
    mirror2RadiusMm = -mirrorDistanceMm / Math.sin(thetaRt / 2);
  } else {
    mirror1RadiusMm = config.mirror1_radius_mm;
    mirror2RadiusMm = config.mirror2_radius_mm;
  }

  const g1 = 1 - mirrorDistanceMm / mirror1RadiusMm;
  const g2 = 1 - mirrorDistanceMm / mirror2RadiusMm;
  const stabilityProduct = g1 * g2;
  const mode = resolveModeConfig(config);

  const response = {
    stable: Number.isFinite(stabilityProduct) && stabilityProduct > 0 && stabilityProduct < 1,
    status_message: "Stability Error (g1g2 bounds)",
    resolved_inputs: {
      mirror_distance_mm: mirrorDistanceMm,
      total_passes: totalPasses,
      revolutions,
      spot_pattern_radius_mm: spotPatternRadiusMm,
      wavelength_nm: config.wavelength_nm,
      wavelength_mm: wavelengthMm,
      hole_radius_mm: holeRadiusMm,
      peak_power_gw: peakPowerGw,
      pulse_energy_mj: pulseEnergyMj,
      mirror1_radius_mm: finiteOrNull(mirror1RadiusMm),
      mirror2_radius_mm: finiteOrNull(mirror2RadiusMm),
      input_waist_x_mm: finiteOrNull(config.input_waist_x_mm),
      input_waist_y_mm: finiteOrNull(config.input_waist_y_mm),
      input_waist_z_mm: finiteOrNull(config.input_waist_z_mm),
      input_x_mm: finiteOrNull(config.input_x_mm),
      input_y_mm: finiteOrNull(config.input_y_mm),
      input_theta_x_mrad: finiteOrNull(config.input_theta_x_mrad),
      input_theta_y_mrad: finiteOrNull(config.input_theta_y_mrad),
      input_hole_x_mm: finiteOrNull(config.input_x_mm),
      input_hole_y_mm: finiteOrNull(config.input_y_mm),
      output_hole_x_mm: finiteOrNull(config.output_hole_x_mm),
      output_hole_y_mm: finiteOrNull(config.output_hole_y_mm),
      output_mirror: config.output_mirror,
      polarization_angle_deg: config.polarization_angle_deg,
      mirror1_tilt_x_mrad: config.mirror1_tilt_x_mrad,
      mirror1_tilt_y_mrad: config.mirror1_tilt_y_mrad,
      mirror2_tilt_x_mrad: config.mirror2_tilt_x_mrad,
      mirror2_tilt_y_mrad: config.mirror2_tilt_y_mrad,
    },
    stability: {
      g1: finiteOrNull(g1),
      g2: finiteOrNull(g2),
      product: finiteOrNull(stabilityProduct),
    },
    mode,
    cavity: null,
    ray_trace: null,
    beam_propagation: null,
  };

  if (!response.stable) {
    return response;
  }

  let gSum = g1 + g2 - 2 * g1 * g2;
  if (gSum === 0) {
    gSum = EPSILON;
  }

  const cavityRayleighRangeMm = Math.sqrt(
    Math.abs(
      ((mirrorDistanceMm * mirrorDistanceMm) * g1 * g2 * (1 - g1 * g2)) / (gSum * gSum),
    ),
  );
  const cavityWaistPositionMm = (mirrorDistanceMm * g2 * (1 - g1)) / gSum;
  const idealWaistMm = Math.sqrt((wavelengthMm * cavityRayleighRangeMm) / Math.PI);
  const mirror1BeamMm = Math.sqrt(
    Math.abs(
      ((wavelengthMm * mirrorDistanceMm) / Math.PI) *
        Math.sqrt(g2 / (g1 * (1 - g1 * g2))),
    ),
  );
  const mirror2BeamMm = Math.sqrt(
    Math.abs(
      ((wavelengthMm * mirrorDistanceMm) / Math.PI) *
        Math.sqrt(g1 / (g2 * (1 - g1 * g2))),
    ),
  );

  let inputWaistXMm = config.input_waist_x_mm;
  let inputWaistYMm = config.input_waist_y_mm;
  let inputWaistZMm = config.input_waist_z_mm;

  if (config.auto_mode_match) {
    inputWaistXMm = idealWaistMm * Math.sqrt(mode.M2x);
    inputWaistYMm = idealWaistMm * Math.sqrt(mode.M2y);
    inputWaistZMm = cavityWaistPositionMm;
  }

  let inputXMm;
  let inputYMm;
  let inputThetaXMrad;
  let inputThetaYMrad;

  if (config.auto_injection) {
    inputXMm = spotPatternRadiusMm;
    inputYMm = 0;

    const mArrive00 = 1 - (2 * mirrorDistanceMm) / mirror2RadiusMm;
    const mArrive01 = 2 * mirrorDistanceMm * g2;

    inputThetaXMrad =
      ((spotPatternRadiusMm * (Math.cos(thetaRt) - mArrive00)) / mArrive01) * 1000;
    inputThetaYMrad = ((spotPatternRadiusMm * Math.sin(thetaRt)) / mArrive01) * 1000;
  } else {
    inputXMm = config.input_x_mm;
    inputYMm = config.input_y_mm;
    inputThetaXMrad = config.input_theta_x_mrad;
    inputThetaYMrad = config.input_theta_y_mrad;
  }

  let outputHoleXMm;
  let outputHoleYMm;
  let outputMirror;

  if (config.auto_output_hole) {
    outputHoleXMm = inputXMm;
    outputHoleYMm = inputYMm;
    outputMirror = 1;
  } else {
    outputHoleXMm = config.output_hole_x_mm;
    outputHoleYMm = config.output_hole_y_mm;
    outputMirror = config.output_mirror;
  }

  response.cavity = {
    rayleigh_range_mm: cavityRayleighRangeMm,
    waist_position_mm: cavityWaistPositionMm,
    ideal_waist_mm: idealWaistMm,
    cavity_waist_x_mm: idealWaistMm * Math.sqrt(mode.M2x),
    cavity_waist_y_mm: idealWaistMm * Math.sqrt(mode.M2y),
    mirror1_beam_mm: mirror1BeamMm,
    mirror2_beam_mm: mirror2BeamMm,
    mirror_beam_x_mm:
      Math.abs(mirror1BeamMm - mirror2BeamMm) < 1e-3 ? mirror1BeamMm * Math.sqrt(mode.M2x) : null,
    mirror_beam_y_mm:
      Math.abs(mirror1BeamMm - mirror2BeamMm) < 1e-3 ? mirror1BeamMm * Math.sqrt(mode.M2y) : null,
    mirror1_display_beam_mm:
      Math.abs(mirror1BeamMm - mirror2BeamMm) < 1e-3 ? null : mirror1BeamMm * Math.sqrt(mode.M2x),
    mirror2_display_beam_mm:
      Math.abs(mirror1BeamMm - mirror2BeamMm) < 1e-3 ? null : mirror2BeamMm * Math.sqrt(mode.M2x),
  };

  response.resolved_inputs = {
    ...response.resolved_inputs,
    input_waist_x_mm: inputWaistXMm,
    input_waist_y_mm: inputWaistYMm,
    input_waist_z_mm: inputWaistZMm,
    input_x_mm: inputXMm,
    input_y_mm: inputYMm,
    input_theta_x_mrad: inputThetaXMrad,
    input_theta_y_mrad: inputThetaYMrad,
    input_hole_x_mm: inputXMm,
    input_hole_y_mm: inputYMm,
    output_hole_x_mm: outputHoleXMm,
    output_hole_y_mm: outputHoleYMm,
    output_mirror: outputMirror,
  };

  const inputHole = [inputXMm, inputYMm];
  const outputHole = [outputHoleXMm, outputHoleYMm];
  const mirror1Tilt = [config.mirror1_tilt_x_mrad * 1e-3, config.mirror1_tilt_y_mrad * 1e-3];
  const mirror2Tilt = [config.mirror2_tilt_x_mrad * 1e-3, config.mirror2_tilt_y_mrad * 1e-3];

  const cell = new HerriottCell(
    mirrorDistanceMm,
    mirror1RadiusMm,
    mirror2RadiusMm,
    inputHole,
    outputHole,
    outputMirror,
    holeRadiusMm,
    mirror1Tilt,
    mirror2Tilt,
  );

  const pointX = inputXMm;
  const pointY = inputYMm;
  const discriminant =
    cell.R1 * cell.R1 - (pointX - cell.C1[0]) ** 2 - (pointY - cell.C1[1]) ** 2;
  const initialZ =
    discriminant >= 0 ? cell.C1[2] - Math.sign(cell.R1) * Math.sqrt(discriminant) : 0;
  const initialPoint = [pointX, pointY, initialZ];

  const initialDirection = vNormalize([inputThetaXMrad * 1e-3, inputThetaYMrad * 1e-3, 1]);
  const referenceX = [1, 0, 0];
  const referenceU1 = vNormalize(vSub(referenceX, vScale(initialDirection, vDot(referenceX, initialDirection))));
  const referenceU2 = vNormalize(vCross(initialDirection, referenceU1));
  const polarizationAngleRad = (config.polarization_angle_deg * Math.PI) / 180;
  const basisU1 = vAdd(
    vScale(referenceU1, Math.cos(polarizationAngleRad)),
    vScale(referenceU2, Math.sin(polarizationAngleRad)),
  );
  const basisU2 = vAdd(
    vScale(referenceU1, -Math.sin(polarizationAngleRad)),
    vScale(referenceU2, Math.cos(polarizationAngleRad)),
  );

  const maxTracePasses = Math.max(150, 4 * totalPasses);
  const rayTrace = cell.traceRays(initialPoint, initialDirection, basisU1, basisU2, maxTracePasses);
  const abcdPasses = Math.max(totalPasses, rayTrace.total_bounces + 1);
  const abcdX = computeABCDAxis(
    mirrorDistanceMm,
    mirror1RadiusMm,
    mirror2RadiusMm,
    wavelengthMm,
    inputWaistXMm,
    inputWaistZMm,
    abcdPasses,
    mode.M2x,
  );
  const abcdY = computeABCDAxis(
    mirrorDistanceMm,
    mirror1RadiusMm,
    mirror2RadiusMm,
    wavelengthMm,
    inputWaistYMm,
    inputWaistZMm,
    abcdPasses,
    mode.M2y,
  );

  response.status_message = rayTrace.exit_status;
  response.ray_trace = {
    ...rayTrace,
    input_basis: {
      u1: basisU1,
      u2: basisU2,
    },
    input_point: initialPoint,
    cell_centers: {
      mirror1: cell.C1,
      mirror2: cell.C2,
    },
  };
  response.beam_propagation = {
    x: abcdX,
    y: abcdY,
  };

  return response;
}
