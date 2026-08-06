const form = document.querySelector("#simulation-form");
const statusLine = document.querySelector("#status");
const button = form.querySelector("button");
let animationFrame = null;

const format = (value, digits = 3) => new Intl.NumberFormat("cs-CZ", {
  maximumFractionDigits: digits,
}).format(value);

function drawChart(canvas, points, series, includeZero = false) {
  const ratio = window.devicePixelRatio || 1;
  const width = canvas.clientWidth;
  const height = Number(canvas.getAttribute("height"));
  canvas.width = width * ratio;
  canvas.height = height * ratio;
  const ctx = canvas.getContext("2d");
  ctx.scale(ratio, ratio);

  const pad = { left: 48, right: 14, top: 28, bottom: 30 };
  const values = series.flatMap((item) => points.map(item.value));
  let minY = Math.min(...values);
  let maxY = Math.max(...values);
  if (includeZero) {
    minY = Math.min(0, minY);
    maxY = Math.max(0, maxY);
  }
  const margin = Math.max((maxY - minY) * 0.08, 0.0001);
  minY -= margin;
  maxY += margin;
  const maxX = points.at(-1).time_s || 1;
  const x = (value) => pad.left + value / maxX * (width - pad.left - pad.right);
  const y = (value) => pad.top + (maxY - value) / (maxY - minY) * (height - pad.top - pad.bottom);

  ctx.strokeStyle = "#d7ddd7";
  ctx.fillStyle = "#687b77";
  ctx.font = "10px monospace";
  ctx.lineWidth = 1;
  for (let index = 0; index <= 4; index += 1) {
    const value = minY + (maxY - minY) * index / 4;
    const gy = y(value);
    ctx.beginPath();
    ctx.moveTo(pad.left, gy);
    ctx.lineTo(width - pad.right, gy);
    ctx.stroke();
    ctx.fillText(format(value, 2), 2, gy + 3);
  }

  series.forEach((item, seriesIndex) => {
    ctx.strokeStyle = item.color;
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    points.forEach((point, index) => {
      const px = x(point.time_s);
      const py = y(item.value(point));
      if (index === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.stroke();
    ctx.fillStyle = item.color;
    ctx.fillRect(pad.left + seriesIndex * 112, 4, 13, 3);
    ctx.fillText(item.label, pad.left + 18 + seriesIndex * 112, 9);
  });

  ctx.fillStyle = "#687b77";
  ctx.fillText("0 s", pad.left - 5, height - 7);
  ctx.fillText(`${format(maxX, 0)} s`, width - pad.right - 45, height - 7);
}

function setTankLevels(point, maximumLevel) {
  const level1 = Math.max(4, Math.min(88, point.tank1_level_m / maximumLevel * 82));
  const level2 = Math.max(4, Math.min(88, point.tank2_level_m / maximumLevel * 82));
  document.querySelector(".upper-tank .tank-water").style.height = `${level1}%`;
  document.querySelector(".lower-tank .tank-water").style.height = `${level2}%`;
  document.querySelector("#level-1-label").textContent = `${format(point.tank1_level_m)} m`;
  document.querySelector("#level-2-label").textContent = `${format(point.tank2_level_m)} m`;
}

function playSimulation(points) {
  if (animationFrame) cancelAnimationFrame(animationFrame);
  const visual = document.querySelector("#flow-visual");
  const maximumLevel = Math.max(...points.flatMap((point) => [point.tank1_level_m, point.tank2_level_m])) * 1.05;
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
    const interpolated = {
      tank1_level_m: current.tank1_level_m + (next.tank1_level_m - current.tank1_level_m) * fraction,
      tank2_level_m: current.tank2_level_m + (next.tank2_level_m - current.tank2_level_m) * fraction,
    };
    setTankLevels(interpolated, maximumLevel);
    visual.classList.toggle("reverse", current.volume_flow_m3_h < 0);
    if (progress < 1) animationFrame = requestAnimationFrame(frame);
    else {
      visual.classList.remove("playing", "reverse");
      animationFrame = null;
    }
  }
  animationFrame = requestAnimationFrame(frame);
}

function showResults(data) {
  document.querySelector("#placeholder").hidden = true;
  document.querySelector("#results").hidden = false;
  document.querySelector("#flow").textContent = format(data.maximum_flow_m3_h);
  document.querySelector("#final-level-1").textContent = format(data.final_tank1_level_m);
  document.querySelector("#final-level-2").textContent = format(data.final_tank2_level_m);
  document.querySelector("#equilibrium").textContent = format(data.equilibrium_level_m);
  document.querySelector("#settling-time").textContent = data.settling_time_s === null ? "mimo interval" : format(data.settling_time_s, 1);

  drawChart(document.querySelector("#levels-chart"), data.points, [
    { label: "Nádoba 1", color: "#102a2a", value: (point) => point.tank1_level_m },
    { label: "Nádoba 2", color: "#16a6a0", value: (point) => point.tank2_level_m },
  ]);
  drawChart(document.querySelector("#flow-chart"), data.points, [
    { label: "Průtok", color: "#16a6a0", value: (point) => point.volume_flow_m3_h },
  ], true);
  playSimulation(data.points);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  button.disabled = true;
  statusLine.className = "status";
  statusLine.textContent = "OpenModelica počítá časový průběh…";
  const payload = Object.fromEntries([...new FormData(form)].map(([key, value]) => [key, Number(value)]));
  try {
    const response = await fetch("/api/simulations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Simulace selhala.");
    showResults(data);
    statusLine.textContent = "Výpočet byl úspěšně dokončen";
  } catch (error) {
    statusLine.className = "status error";
    statusLine.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});
