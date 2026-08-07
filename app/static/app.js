const tabs = [...document.querySelectorAll(".model-tab")];
const panels = [...document.querySelectorAll(".model-panel")];
const twoTanksPanel = document.querySelector('[data-model-panel="two-tanks"]');
const waterPipePanel = document.querySelector('[data-model-panel="water-pipe"]');
const irrigationPanel = document.querySelector('[data-model-panel="garden-irrigation"]');
const state = { twoTanks: null, waterPipe: null, irrigation: null };
let tankAnimationFrame = null;

const format = (value, digits = 3) => new Intl.NumberFormat("cs-CZ", {
  maximumFractionDigits: digits,
}).format(value);

function activateModel(model) {
  tabs.forEach((tab) => {
    const active = tab.dataset.model === model;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
  });
  panels.forEach((panel) => {
    const active = panel.dataset.modelPanel === model;
    panel.classList.toggle("active", active);
    panel.hidden = !active;
  });
  window.history.replaceState(null, "", `#${model}`);
  window.requestAnimationFrame(() => {
    if (model === "two-tanks" && state.twoTanks) drawTwoTanksCharts(state.twoTanks);
    if (model === "water-pipe" && state.waterPipe) drawWaterPipeChart(state.waterPipe);
    if (model === "garden-irrigation" && state.irrigation) {
      drawIrrigationChart(state.irrigation);
    }
  });
}

tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => activateModel(tab.dataset.model));
  tab.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    let nextIndex = index;
    if (event.key === "ArrowLeft") nextIndex = (index - 1 + tabs.length) % tabs.length;
    if (event.key === "ArrowRight") nextIndex = (index + 1) % tabs.length;
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = tabs.length - 1;
    tabs[nextIndex].focus();
    activateModel(tabs[nextIndex].dataset.model);
  });
});

function drawChart(canvas, points, series, options) {
  const width = canvas.clientWidth;
  if (!width || !points.length) return;
  const ratio = window.devicePixelRatio || 1;
  const height = Number(canvas.getAttribute("height"));
  canvas.width = width * ratio;
  canvas.height = height * ratio;
  const context = canvas.getContext("2d");
  context.scale(ratio, ratio);

  const pad = { left: 48, right: 14, top: 28, bottom: 30 };
  const values = series.flatMap((item) => points.map(item.value));
  let minY = Math.min(...values);
  let maxY = Math.max(...values);
  if (options.includeZero) {
    minY = Math.min(0, minY);
    maxY = Math.max(0, maxY);
  }
  const margin = Math.max((maxY - minY) * 0.08, 0.0001);
  minY -= margin;
  maxY += margin;
  const firstX = options.xValue(points[0]);
  const lastX = options.xValue(points.at(-1));
  const xRange = lastX - firstX || 1;
  const x = (value) => pad.left + (value - firstX) / xRange * (width - pad.left - pad.right);
  const y = (value) => pad.top + (maxY - value) / (maxY - minY) * (height - pad.top - pad.bottom);

  context.strokeStyle = "#d7ddd7";
  context.fillStyle = "#687b77";
  context.font = "10px monospace";
  context.lineWidth = 1;
  for (let index = 0; index <= 4; index += 1) {
    const value = minY + (maxY - minY) * index / 4;
    const gridY = y(value);
    context.beginPath();
    context.moveTo(pad.left, gridY);
    context.lineTo(width - pad.right, gridY);
    context.stroke();
    context.fillText(format(value, 2), 2, gridY + 3);
  }

  series.forEach((item, seriesIndex) => {
    context.strokeStyle = item.color;
    context.lineWidth = 2.5;
    context.beginPath();
    points.forEach((point, index) => {
      const pointX = x(options.xValue(point));
      const pointY = y(item.value(point));
      if (index === 0) context.moveTo(pointX, pointY);
      else context.lineTo(pointX, pointY);
    });
    context.stroke();
    context.fillStyle = item.color;
    context.fillRect(pad.left + seriesIndex * 112, 4, 13, 3);
    context.fillText(item.label, pad.left + 18 + seriesIndex * 112, 9);
  });

  context.fillStyle = "#687b77";
  const startLabel = options.xStartLabel ?? `${format(firstX, 0)} ${options.xUnit}`;
  const endLabel = options.xEndLabel ?? `${format(lastX, 0)} ${options.xUnit}`;
  context.fillText(startLabel, pad.left - 5, height - 7);
  context.fillText(endLabel, width - pad.right - 55, height - 7);
}

function payloadFrom(form) {
  return Object.fromEntries(
    [...new FormData(form)].map(([key, value]) => [key, Number(value)]),
  );
}

async function requestSimulation(endpoint, payload) {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail.map((item) => item.msg).join("; ")
      : data.detail;
    throw new Error(detail || "Simulace selhala.");
  }
  return data;
}

function setTankLevels(point, maximumLevel) {
  const level1 = Math.max(4, Math.min(88, point.tank1_level_m / maximumLevel * 82));
  const level2 = Math.max(4, Math.min(88, point.tank2_level_m / maximumLevel * 82));
  twoTanksPanel.querySelector(".tank-one .tank-water").style.height = `${level1}%`;
  twoTanksPanel.querySelector(".tank-two .tank-water").style.height = `${level2}%`;
  twoTanksPanel.querySelector(".level-1-label").textContent = `${format(point.tank1_level_m)} m`;
  twoTanksPanel.querySelector(".level-2-label").textContent = `${format(point.tank2_level_m)} m`;
}

function playTankSimulation(points) {
  if (tankAnimationFrame) cancelAnimationFrame(tankAnimationFrame);
  const visual = twoTanksPanel.querySelector(".flow-visual");
  const maximumLevel = Math.max(
    ...points.flatMap((point) => [point.tank1_level_m, point.tank2_level_m]),
  ) * 1.05;
  const simulatedDuration = points.at(-1).time_s || 1;
  const playbackDuration = 10000;
  let pointIndex = 0;
  let startTime = null;
  visual.classList.add("playing");

  function frame(now) {
    if (startTime === null) startTime = now;
    const progress = Math.min(1, (now - startTime) / playbackDuration);
    const targetTime = progress * simulatedDuration;
    while (pointIndex < points.length - 2 && points[pointIndex + 1].time_s <= targetTime) {
      pointIndex += 1;
    }
    const current = points[pointIndex];
    const next = points[Math.min(pointIndex + 1, points.length - 1)];
    const interval = next.time_s - current.time_s;
    const fraction = interval > 0 ? Math.min(1, (targetTime - current.time_s) / interval) : 0;
    setTankLevels({
      tank1_level_m: current.tank1_level_m + (next.tank1_level_m - current.tank1_level_m) * fraction,
      tank2_level_m: current.tank2_level_m + (next.tank2_level_m - current.tank2_level_m) * fraction,
    }, maximumLevel);
    visual.classList.toggle("reverse", current.volume_flow_m3_h < 0);
    if (progress < 1) tankAnimationFrame = requestAnimationFrame(frame);
    else {
      visual.classList.remove("playing", "reverse");
      tankAnimationFrame = null;
    }
  }
  tankAnimationFrame = requestAnimationFrame(frame);
}

function drawTwoTanksCharts(data) {
  drawChart(twoTanksPanel.querySelector(".levels-chart"), data.points, [
    { label: "Nádoba 1", color: "#102a2a", value: (point) => point.tank1_level_m },
    { label: "Nádoba 2", color: "#16a6a0", value: (point) => point.tank2_level_m },
  ], { xValue: (point) => point.time_s, xUnit: "s", includeZero: false });
  drawChart(twoTanksPanel.querySelector(".flow-chart"), data.points, [
    { label: "Průtok", color: "#16a6a0", value: (point) => point.volume_flow_m3_h },
  ], { xValue: (point) => point.time_s, xUnit: "s", includeZero: true });
}

function showTwoTanksResults(data) {
  state.twoTanks = data;
  twoTanksPanel.querySelector(".placeholder").hidden = true;
  twoTanksPanel.querySelector(".results").hidden = false;
  twoTanksPanel.querySelector(".maximum-flow").textContent = format(data.maximum_flow_m3_h);
  twoTanksPanel.querySelector(".final-level-1").textContent = format(data.final_tank1_level_m);
  twoTanksPanel.querySelector(".final-level-2").textContent = format(data.final_tank2_level_m);
  twoTanksPanel.querySelector(".equilibrium").textContent = format(data.equilibrium_level_m);
  twoTanksPanel.querySelector(".settling-time").textContent = data.settling_time_s === null
    ? "mimo interval"
    : format(data.settling_time_s, 1);
  drawTwoTanksCharts(data);
  playTankSimulation(data.points);
}

function drawWaterPipeChart(data) {
  drawChart(waterPipePanel.querySelector(".pressure-chart"), data.pressure_profile, [
    { label: "Tlaková ztráta", color: "#16a6a0", value: (point) => point.pressure_drop_bar },
  ], { xValue: (point) => point.distance_m, xUnit: "m", includeZero: true });
}

function showWaterPipeResults(data) {
  state.waterPipe = data;
  waterPipePanel.querySelector(".placeholder").hidden = true;
  waterPipePanel.querySelector(".results").hidden = false;
  waterPipePanel.querySelector(".pipe-volume-flow").textContent = format(data.volume_flow_m3_h);
  waterPipePanel.querySelector(".pipe-velocity").textContent = format(data.velocity_m_s);
  waterPipePanel.querySelector(".pipe-mass-flow").textContent = format(data.mass_flow_kg_s);
  waterPipePanel.querySelector(".pipe-reynolds").textContent = format(data.reynolds_number, 0);
  waterPipePanel.querySelector(".pipe-regime").textContent = data.flow_regime;
  waterPipePanel.querySelector(".pipe-friction").textContent = format(data.friction_factor, 5);
  waterPipePanel.querySelector(".single-pipe-visual").classList.add("playing");
  drawWaterPipeChart(data);
}

function drawIrrigationChart(data) {
  const points = data.beds.map((bed, index) => ({ ...bed, chartIndex: index }));
  drawChart(irrigationPanel.querySelector(".irrigation-flow-chart"), points, [
    { label: "Průtok záhonu", color: "#16a6a0", value: (bed) => bed.bed_flow_l_min },
  ], {
    xValue: (bed) => bed.chartIndex,
    xUnit: "",
    xStartLabel: "A",
    xEndLabel: "J",
    includeZero: true,
  });
}

function showIrrigationResults(data) {
  state.irrigation = data;
  irrigationPanel.querySelector(".placeholder").hidden = true;
  irrigationPanel.querySelector(".results").hidden = false;
  irrigationPanel.querySelector(".irrigation-total-flow").textContent = format(data.total_flow_l_min);
  irrigationPanel.querySelector(".irrigation-filter-pressure").textContent = format(data.pressure_after_filter_bar);
  irrigationPanel.querySelector(".irrigation-water").textContent = format(data.total_water_l, 1);
  irrigationPanel.querySelector(".irrigation-end-level").textContent = format(data.tank_level_end_estimated_m);
  irrigationPanel.querySelector(".irrigation-uniformity").textContent = data.emitter_uniformity_percent === null
    ? "—"
    : format(data.emitter_uniformity_percent, 1);

  irrigationPanel.querySelector(".result-warnings").innerHTML = data.warnings
    .map((warning) => `<li>${warning}</li>`)
    .join("");
  irrigationPanel.querySelector(".beds-table-body").innerHTML = data.beds
    .map((bed) => {
      const balanceClass = bed.relative_delivery_percent < 85 || bed.relative_delivery_percent > 115
        ? "outside-target"
        : "inside-target";
      return `<tr>
        <th>${bed.id}<small>zóna ${bed.zone} · ${bed.row_count} řádků</small></th>
        <td>${format(bed.valve_opening, 2)}</td>
        <td>${format(bed.inlet_pressure_bar)} bar</td>
        <td>${format(bed.bed_flow_l_min)} l/min</td>
        <td>${format(bed.water_delivered_l, 1)} l</td>
        <td class="${balanceClass}">${format(bed.relative_delivery_percent, 0)} %</td>
      </tr>`;
    })
    .join("");
  irrigationPanel.querySelector(".rows-table-body").innerHTML = data.rows
    .map((row) => `<tr>
      <th>${row.bed_id}${row.row_number}</th>
      <td>${row.emitter_count}</td>
      <td>${format(row.flow_l_h, 1)} l/h</td>
      <td>${format(row.start_pressure_bar)} bar</td>
      <td>${format(row.end_pressure_bar)} bar</td>
    </tr>`)
    .join("");

  irrigationPanel.querySelectorAll(".zone-network i").forEach((bedNode) => {
    const bed = data.beds.find((item) => item.id === bedNode.textContent);
    bedNode.classList.toggle("active", Boolean(bed && bed.bed_flow_l_min > 0.001));
  });
  irrigationPanel.querySelector(".irrigation-visual").classList.add("playing");
  drawIrrigationChart(data);
}

const irrigationPresets = {
  all: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
  one: [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  balanced: [0.21, 0.42, 0.18, 0.25, 0.14, 0.14, 0.1, 0.17, 0.1, 0.11],
};

irrigationPanel.querySelectorAll(".preset-button").forEach((presetButton) => {
  presetButton.addEventListener("click", () => {
    const openings = irrigationPresets[presetButton.dataset.irrigationPreset];
    openings.forEach((opening, index) => {
      const bedId = String.fromCharCode(97 + index);
      irrigationPanel.querySelector(`[name="opening_${bedId}"]`).value = opening;
    });
    irrigationPanel.querySelectorAll(".preset-button").forEach((button) => {
      button.classList.toggle("active", button === presetButton);
    });
  });
});

function connectForm({ selector, endpoint, pending, onSuccess }) {
  const form = document.querySelector(selector);
  const button = form.querySelector(".submit-button");
  const statusLine = form.querySelector(".status");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    button.disabled = true;
    statusLine.className = "status";
    statusLine.textContent = pending;
    try {
      const data = await requestSimulation(endpoint, payloadFrom(form));
      onSuccess(data);
      statusLine.textContent = "Výpočet byl úspěšně dokončen";
    } catch (error) {
      statusLine.className = "status error";
      statusLine.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
}

connectForm({
  selector: "#two-tanks-form",
  endpoint: "/api/models/two-tanks/simulations",
  pending: "OpenModelica počítá časový průběh…",
  onSuccess: showTwoTanksResults,
});

connectForm({
  selector: "#water-pipe-form",
  endpoint: "/api/models/water-pipe/simulations",
  pending: "OpenModelica počítá ustálený průtok…",
  onSuccess: showWaterPipeResults,
});

connectForm({
  selector: "#garden-irrigation-form",
  endpoint: "/api/models/garden-irrigation/simulations",
  pending: "OpenModelica vyvažuje průtoky deseti záhonů…",
  onSuccess: showIrrigationResults,
});

const initialModel = window.location.hash.slice(1);
if (["two-tanks", "water-pipe", "garden-irrigation"].includes(initialModel)) {
  activateModel(initialModel);
}

let resizeTimer = null;
window.addEventListener("resize", () => {
  window.clearTimeout(resizeTimer);
  resizeTimer = window.setTimeout(() => {
    const activeModel = document.querySelector(".model-tab.active").dataset.model;
    if (activeModel === "two-tanks" && state.twoTanks) drawTwoTanksCharts(state.twoTanks);
    if (activeModel === "water-pipe" && state.waterPipe) drawWaterPipeChart(state.waterPipe);
    if (activeModel === "garden-irrigation" && state.irrigation) {
      drawIrrigationChart(state.irrigation);
    }
  }, 120);
});
