const chart = document.querySelector("#snow-chart");
const select = document.querySelector("#season-select");
const tooltip = document.querySelector("#chart-tooltip");
let payload;

const formatDate = (value) => new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "short" }).format(new Date(`${value}T12:00:00`));

function getAxisLabelIndexes(length, maxLabels = 6) {
  if (length <= maxLabels) return Array.from({ length }, (_, index) => index);

  const indexes = [];
  const interval = (length - 1) / (maxLabels - 1);
  for (let label = 0; label < maxLabels; label += 1) {
    indexes.push(Math.round(label * interval));
  }
  return [...new Set(indexes)];
}

function renderChart(season) {
  const data = payload.seasons[season];
  const historical = Object.entries(payload.seasons)
    .filter(([name]) => name !== season)
    .map(([, rows]) => rows);
  const width = 800, height = 330, left = 44, top = 20, right = 18, bottom = 38;
  const historicalStats = Array.from({ length: Math.max(...historical.map((rows) => rows.length), data.length) }, (_, index) => {
    const values = historical.map((rows) => rows[index]?.depth_cm).filter((value) => value !== undefined);
    if (!values.length) return null;
    return { min: Math.min(...values), max: Math.max(...values), mean: values.reduce((sum, value) => sum + value, 0) / values.length };
  });
  const max = Math.ceil(Math.max(
    ...data.map(({ depth_cm }) => depth_cm),
    ...historicalStats.filter(Boolean).map(({ max: value }) => value),
  ) / 50) * 50;
  const x = (i) => left + (i / (data.length - 1)) * (width - left - right);
  const y = (value) => top + (1 - value / max) * (height - top - bottom);
  const points = data.map((row, i) => `${x(i).toFixed(1)},${y(row.depth_cm).toFixed(1)}`);
  const line = `M ${points.join(" L ")}`;
  const area = `${line} L ${x(data.length - 1)},${height - bottom} L ${x(0)},${height - bottom} Z`;
  const stats = historicalStats.slice(0, data.length);
  const upper = stats.map((stat, index) => `${x(index).toFixed(1)},${y(stat?.max ?? 0).toFixed(1)}`);
  const lower = stats.map((stat, index) => `${x(index).toFixed(1)},${y(stat?.min ?? 0).toFixed(1)}`).reverse();
  const band = `M ${[...upper, ...lower].join(" L ")} Z`;
  const mean = `M ${stats.map((stat, index) => `${x(index).toFixed(1)},${y(stat?.mean ?? 0).toFixed(1)}`).join(" L ")}`;

  chart.querySelector("#historical-band").setAttribute("d", band);
  chart.querySelector("#historical-mean").setAttribute("d", mean);
  chart.querySelector("#area-path").setAttribute("d", area);
  chart.querySelector("#line-path").setAttribute("d", line);
  chart.querySelector(".grid-lines").innerHTML = [0, .25, .5, .75, 1].map((step) => {
    const value = Math.round(max * step), lineY = y(value);
    return `<line class="grid-line" x1="${left}" y1="${lineY}" x2="${width - right}" y2="${lineY}" /><text class="axis-label" x="0" y="${lineY + 4}">${value}</text>`;
  }).join("");
  chart.querySelector("#points").innerHTML = data.map((row, index) => `<circle class="data-point" cx="${x(index)}" cy="${y(row.depth_cm)}" r="4" tabindex="0" data-date="${formatDate(row.date)}" data-depth="${row.depth_cm}"><title>${formatDate(row.date)} : ${row.depth_cm} cm</title></circle>`).join("");
  chart.querySelector("#axis-labels").innerHTML = getAxisLabelIndexes(data.length).map((index) => {
    const row = data[index];
    return `<text class="axis-label" text-anchor="middle" x="${x(index)}" y="${height - 10}">${formatDate(row.date)}</text>`;
  }).join("");

  const peak = data.reduce((best, row) => row.depth_cm > best.depth_cm ? row : best);
  document.querySelector("#peak-depth").textContent = peak.depth_cm;
  document.querySelector("#season-title").textContent = `Saison ${season}`;
  document.querySelector("#season-summary").textContent = `Le maximum de cette courbe de démonstration est atteint le ${formatDate(peak.date)}.`;
  document.querySelector("#start-depth").textContent = `${data[0].depth_cm} cm`;
  document.querySelector("#peak-date").textContent = formatDate(peak.date);
  document.querySelector("#point-count").textContent = data.length;
  bindTooltip();
}

function showTooltip(point) {
  const chartBox = chart.getBoundingClientRect();
  const pointBox = point.getBoundingClientRect();
  tooltip.textContent = `${point.dataset.date} · ${point.dataset.depth} cm`;
  tooltip.style.left = `${pointBox.left - chartBox.left + pointBox.width / 2}px`;
  tooltip.style.top = `${pointBox.top - chartBox.top}px`;
  tooltip.hidden = false;
}

function bindTooltip() {
  chart.querySelectorAll(".data-point").forEach((point) => {
    point.addEventListener("mouseenter", () => showTooltip(point));
    point.addEventListener("focus", () => showTooltip(point));
    point.addEventListener("mouseleave", () => { tooltip.hidden = true; });
    point.addEventListener("blur", () => { tooltip.hidden = true; });
  });
}

async function loadData() {
  const response = await fetch("/api/snow-depth");
  if (!response.ok) throw new Error("Impossible de charger les données.");
  payload = await response.json();
  const seasons = Object.keys(payload.seasons).sort().reverse();
  select.innerHTML = seasons.map((season) => `<option value="${season}">Saison ${season}</option>`).join("");
  select.disabled = false;
  chart.insertAdjacentHTML("afterbegin", '<defs><linearGradient id="snow-gradient" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stop-color="#dd2222" stop-opacity=".24"/><stop offset="100%" stop-color="#dd2222" stop-opacity="0"/></linearGradient></defs>');
  document.querySelector("#source-line").textContent = payload.source;
  document.querySelector("#data-status").textContent = payload.is_demo ? "Prototype · données simulées" : "Données Open-Meteo · locales";
  renderChart(seasons[0]);
}

select.addEventListener("change", () => renderChart(select.value));
loadData().catch((error) => { document.querySelector("#source-line").textContent = error.message; });
