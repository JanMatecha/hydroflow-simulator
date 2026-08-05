const form = document.querySelector("#simulation-form");
const statusLine = document.querySelector("#status");
const button = form.querySelector("button");

const format = (value, digits = 3) => new Intl.NumberFormat("cs-CZ", {
  maximumFractionDigits: digits,
}).format(value);

function drawChart(points) {
  const canvas = document.querySelector("#pressure-chart");
  const ratio = window.devicePixelRatio || 1;
  const width = canvas.clientWidth;
  const height = 220;
  canvas.width = width * ratio;
  canvas.height = height * ratio;
  const ctx = canvas.getContext("2d");
  ctx.scale(ratio, ratio);
  const pad = { left: 42, right: 12, top: 14, bottom: 28 };
  const maxX = points.at(-1).distance_m;
  const maxY = points.at(-1).pressure_drop_bar;
  const x = (value) => pad.left + value / maxX * (width - pad.left - pad.right);
  const y = (value) => height - pad.bottom - value / maxY * (height - pad.top - pad.bottom);
  ctx.strokeStyle = "#d7ddd7"; ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i += 1) {
    const gy = pad.top + i * (height - pad.top - pad.bottom) / 4;
    ctx.beginPath(); ctx.moveTo(pad.left, gy); ctx.lineTo(width - pad.right, gy); ctx.stroke();
  }
  ctx.strokeStyle = "#16a6a0"; ctx.lineWidth = 3; ctx.beginPath();
  points.forEach((point, index) => index ? ctx.lineTo(x(point.distance_m), y(point.pressure_drop_bar)) : ctx.moveTo(x(point.distance_m), y(point.pressure_drop_bar)));
  ctx.stroke();
  ctx.fillStyle = "#687b77"; ctx.font = "11px monospace";
  ctx.fillText("0", pad.left - 4, height - 8);
  ctx.fillText(`${format(maxX, 1)} m`, width - pad.right - 46, height - 8);
  ctx.fillText(`${format(maxY, 2)}`, 3, pad.top + 4);
}

function showResults(data) {
  const visual = document.querySelector("#flow-visual");
  const duration = Math.max(2.8, Math.min(8, 8 - Math.log10(Math.max(data.volume_flow_m3_h, 0.01)) * 1.5));
  visual.classList.remove("running");
  void visual.offsetWidth;
  visual.style.setProperty("--flow-duration", `${duration}s`);
  visual.classList.add("running");
  document.querySelector("#placeholder").hidden = true;
  document.querySelector("#results").hidden = false;
  document.querySelector("#flow").textContent = format(data.volume_flow_m3_h);
  document.querySelector("#velocity").textContent = format(data.velocity_m_s);
  document.querySelector("#reynolds").textContent = format(data.reynolds_number, 0);
  document.querySelector("#regime").textContent = data.flow_regime;
  document.querySelector("#mass-flow").textContent = format(data.mass_flow_kg_s);
  document.querySelector("#friction").textContent = format(data.friction_factor, 5);
  drawChart(data.pressure_profile);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  button.disabled = true;
  statusLine.className = "status";
  statusLine.textContent = "OpenModelica počítá…";
  const payload = Object.fromEntries([...new FormData(form)].map(([key, value]) => [key, Number(value)]));
  try {
    const response = await fetch("/api/simulations", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
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
