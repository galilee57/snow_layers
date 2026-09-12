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
  const max = Math.max(50, Math.ceil(Math.max(
    ...data.map(({ depth_cm }) => depth_cm),
    ...historicalStats.filter(Boolean).map(({ max: value }) => value),
  ) / 50) * 50);
  const x = (i) => left + (i / Math.max(1, data.length - 1)) * (width - left - right);
  const y = (value) => top + (1 - value / max) * (height - top - bottom);
  const points = data.map((row, i) => `${x(i).toFixed(1)},${y(row.depth_cm).toFixed(1)}`);
  const line = `M ${points.join(" L ")}`;
  const area = `${line} L ${x(data.length - 1)},${height - bottom} L ${x(0)},${height - bottom} Z`;
  const stats = historicalStats.slice(0, data.length);
  const upper = stats.map((stat, index) => `${x(index).toFixed(1)},${y(stat?.max ?? 0).toFixed(1)}`);
  const lower = stats.map((stat, index) => `${x(index).toFixed(1)},${y(stat?.min ?? 0).toFixed(1)}`).reverse();
  const band = `M ${[...upper, ...lower].join(" L ")} Z`;
  const mean = `M ${stats.map((stat, index) => `${x(index).toFixed(1)},${y(stat?.mean ?? 0).toFixed(1)}`).join(" L ")}`;

  chart.querySelector("#historical-band").setAttribute("d", historical.length ? band : "");
  chart.querySelector("#historical-mean").setAttribute("d", historical.length ? mean : "");
  chart.querySelector("#area-path").setAttribute("d", area);
  chart.querySelector("#line-path").setAttribute("d", line);
  chart.querySelector(".grid-lines").innerHTML = [0, .25, .5, .75, 1].map((step) => {
    const value = Math.round(max * step), lineY = y(value);
    return `<line class="grid-line" x1="${left}" y1="${lineY}" x2="${width - right}" y2="${lineY}" /><text class="axis-label" x="0" y="${lineY + 4}">${value}</text>`;
  }).join("");
  chart.querySelector("#points").innerHTML = data.map((row, index) => `<circle class="data-point" cx="${x(index)}" cy="${y(row.depth_cm)}" r="3" tabindex="0" data-date="${formatDate(row.date)}" data-depth="${row.depth_cm}"><title>${formatDate(row.date)} : ${row.depth_cm} cm</title></circle>`).join("");
  chart.querySelector("#axis-labels").innerHTML = getAxisLabelIndexes(data.length).map((index) => {
    const row = data[index];
    return `<text class="axis-label" text-anchor="middle" x="${x(index)}" y="${height - 10}">${formatDate(row.date)}</text>`;
  }).join("");

  const peak = data.reduce((best, row) => row.depth_cm > best.depth_cm ? row : best);
  document.querySelector("#peak-depth").textContent = peak.depth_cm;
  document.querySelector("#season-title").textContent = `Saison ${season}`;
  document.querySelector("#season-summary").textContent = `Le maximum ${payload.is_demo ? "simulé" : "modélisé"} à ${payload.station} est atteint le ${formatDate(peak.date)}.`;
  document.querySelector("#start-depth").textContent = `${data[0].depth_cm} cm`;
  document.querySelector("#peak-date").textContent = formatDate(peak.date);
  document.querySelector("#point-count").textContent = data.length;
  const [startYear, endYear] = season.split("-").map(Number);
  const expectedDays = Math.round((Date.UTC(endYear, 3, 30) - Date.UTC(startYear, 11, 1)) / 86400000) + 1;
  const partial = !payload.is_demo && (data.length !== expectedDays || data[0].date !== `${startYear}-12-01` || data.at(-1).date !== `${endYear}-04-30`);
  document.querySelector("#source-line").textContent = `${payload.source} · cm · ≈ ${payload.location.elevation_m} m · ${data[0].date} → ${data.at(-1).date}${payload.collected_at ? " · Collecte : " + new Date(payload.collected_at).toLocaleDateString("fr-FR") : ""}${partial ? " · Données partielles" : ""}`;
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


const stationSelect = document.querySelector("#station-select");
const importButton = document.querySelector("#import-button");
let stations = [], selectedSlug = "meribel", requestVersion = 0;
let map;
const markers = new Map();

function clearChart(message, resetSelect = true) {
  tooltip.hidden = true;
  chart.querySelectorAll("path").forEach((path) => path.removeAttribute("d"));
  chart.querySelectorAll("g").forEach((group) => { group.innerHTML = ""; });
  ["peak-depth", "start-depth", "peak-date", "point-count", "season-title"].forEach((id) => { document.getElementById(id).textContent = "—"; });
  document.querySelector("#season-summary").textContent = message;
  if (resetSelect) {
    select.replaceChildren(new Option("Aucune saison disponible", ""));
    select.disabled = true;
  }
}

async function loadData(preferredSeason) {
  const version = ++requestVersion;
  const slug = selectedSlug;
  clearChart("Chargement des données de la station…");
  document.querySelector("#data-status").textContent = "Chargement…";
  document.querySelector("#source-line").textContent = "Chargement…";
  try {
    const response = await fetch(`/api/snow-depth?station=${encodeURIComponent(slug)}`);
    if (!response.ok) throw new Error("Impossible de charger les données de cette station.");
    const result = await response.json();
    if (version !== requestVersion) return;
    payload = result;
    const seasons = Object.keys(payload.seasons).sort().reverse();
    document.querySelector("#source-line").textContent = `${payload.source} · ${payload.location.elevation_m} m (altitude de référence approximative)${payload.collected_at ? " · Collecte : " + new Date(payload.collected_at).toLocaleDateString("fr-FR") : ""}`;
    document.querySelector("#data-status").textContent = payload.is_demo ? "Prototype · données simulées" : seasons.length ? "Réanalyse Open-Meteo · cache local" : "Aucune donnée locale";
    const choices = [...new Set([...seasons, ...JSON.parse(select.dataset.importSeasons)])].sort().reverse();
    select.replaceChildren(...choices.map((season) => new Option(`Saison ${season}${seasons.includes(season) ? "" : " · à charger"}`, season)));
    select.disabled = false;
    select.value = choices.includes(preferredSeason) ? preferredSeason : (seasons[0] || choices[0]);
    showSelectedSeason();
  } catch (error) {
    if (version !== requestVersion) return;
    clearChart(error.message);
    document.querySelector("#source-line").textContent = error.message;
    document.querySelector("#data-status").textContent = "Chargement impossible";
  }
}

function showSelectedSeason() {
  if (payload?.seasons?.[select.value]?.length) {
    renderChart(select.value);
  } else {
    clearChart("Cette saison n’est pas disponible localement. Chargez-la avec le bouton sous les informations de station (réanalyse Open-Meteo).", false);
  }
}

function pinIcon(selected, category = "") {
  return L.divIcon({ className: "", html: `<div class="station-pin category-${category}${selected ? " selected" : ""}"></div>`, iconSize: [16, 16], iconAnchor: [8, 8] });
}

function chooseStation(slug, moveMap = true) {
  const station = stations.find((item) => item.slug === slug);
  if (!station) return;
  selectedSlug = slug;
  stationSelect.value = slug;
  document.querySelector("#selected-station").textContent = station.name;
  document.querySelector("#station-details").textContent = `${station.massif} · ≈ ${station.elevation_m} m · ${station.latitude.toFixed(3)}° N, ${station.longitude.toFixed(3)}° E (approximatif)`;
  markers.forEach((marker, key) => {
    marker.setIcon(pinIcon(key === slug, markers.get(key).stationCategory));
    marker.setZIndexOffset(key === slug ? 1000 : 0);
  });
  if (map && moveMap) { map.setView([station.latitude, station.longitude], Math.max(map.getZoom(), 8)); markers.get(slug).openTooltip(); }
  const url = new URL(window.location.href);
  url.searchParams.set("station", slug);
  history.replaceState(null, "", url);
  loadData();
}

async function initializeStations() {
  try {
    const response = await fetch("/api/stations");
    if (!response.ok) throw new Error("Le catalogue des stations est indisponible. Rechargez la page.");
    const catalog = await response.json();
    stations = catalog.stations;
    stationSelect.replaceChildren(...[...stations].sort((a, b) => a.name.localeCompare(b.name, "fr")).map((station) => new Option(`${station.name} · ${station.massif}`, station.slug)));
    stationSelect.disabled = false;
    importButton.disabled = false;
    document.querySelector("#map-status").textContent = `${stations.length} stations · ${catalog.note}.`;
    if (window.L) {
      map = L.map("station-map", { scrollWheelZoom: false }).fitBounds([[41.3, -5.2], [51.1, 9.7]]);
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 16, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }).on("tileerror", () => { document.querySelector("#map-status").textContent = "Fond de carte indisponible. La liste des stations reste utilisable. " + catalog.note; }).addTo(map);
      stations.forEach((station) => {
        const label = document.createElement("span"); label.textContent = station.name;
        const marker = L.marker([station.latitude, station.longitude], {icon: pinIcon(false, station.altitude_category), title: station.name, alt: station.name, keyboard: true}).addTo(map).bindTooltip(label);
        marker.stationCategory = station.altitude_category;
        marker.on("click", () => chooseStation(station.slug));
        markers.set(station.slug, marker);
      });
    } else {
      document.querySelector("#station-map").hidden = true;
      document.querySelector("#map-status").textContent = "Carte indisponible hors connexion : utilisez la liste. " + catalog.note;
    }
    const requested = new URLSearchParams(location.search).get("station");
    chooseStation(stations.some((station) => station.slug === requested) ? requested : "meribel", false);
    initializeComparison();
  } catch (error) {
    document.querySelector("#map-status").textContent = error.message;
    clearChart(error.message);
    document.querySelector("#data-status").textContent = "Catalogue indisponible";
  }
}

chart.insertAdjacentHTML("afterbegin", '<defs><linearGradient id="snow-gradient" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stop-color="#dd2222" stop-opacity=".24"/><stop offset="100%" stop-color="#dd2222" stop-opacity="0"/></linearGradient></defs>');
stationSelect.addEventListener("change", () => chooseStation(stationSelect.value));
select.addEventListener("change", showSelectedSeason);
document.querySelector("#import-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const slug = selectedSlug, season = select.value;
  if (select.disabled || !season) return;
  importButton.disabled = true;
  document.querySelector("#request-status").textContent = "Chargement Open-Meteo en cours…";
  try {
    const response = await fetch("/api/snow-depth/import", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({station: slug, season}) });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "La requête a échoué.");
    if (selectedSlug === slug) {
      await loadData(season);
      document.querySelector("#request-status").textContent = `${result.count} jours · ${result.cached ? "lus dans le cache local" : "chargés et conservés localement"}${result.partial ? " · Données partielles" : ""}.`;
    }
  } catch (error) {
    if (selectedSlug === slug) document.querySelector("#request-status").textContent = error.message;
  } finally { importButton.disabled = false; }
});
initializeStations();

const compareA = document.querySelector("#compare-a");
const compareB = document.querySelector("#compare-b");
const comparisonSeries = document.querySelector("#comparison-series");
const comparisonState = new Map([
  ["basse-min", true], ["basse-max", true], ["basse-mean", true],
  ["moyenne-min", true], ["moyenne-max", true], ["moyenne-mean", true],
  ["haute-min", true], ["haute-max", true], ["haute-mean", true],
  ["station-a", true], ["station-b", true],
]);
let comparisonPayload;

function comparisonPath(values, x, y) {
  const points = values.map((value, index) => value == null ? null : `${x(index).toFixed(1)},${y(value).toFixed(1)}`).filter(Boolean);
  return points.length ? `M ${points.join(" L ")}` : "";
}

function drawComparison() {
  if (!comparisonPayload) return;
  const seasons = comparisonPayload.seasons;
  const width = 1000, height = 430, left = 54, right = 18, top = 22, bottom = 50;
  const values = [];
  Object.values(comparisonPayload.categories).forEach((rows) => Object.values(rows).forEach((row) => values.push(row.min, row.max)));
  Object.values(comparisonPayload.stations).forEach((station) => values.push(...Object.values(station.values)));
  const max = Math.max(50, Math.ceil(Math.max(...values, 0) / 50) * 50);
  const x = (index) => left + (index / Math.max(1, seasons.length - 1)) * (width - left - right);
  const y = (value) => top + (1 - value / max) * (height - top - bottom);
  document.querySelector("#comparison-grid").innerHTML = [0, .25, .5, .75, 1].map((step) => `<line class="comparison-grid-line" x1="${left}" y1="${y(max * step)}" x2="${width - right}" y2="${y(max * step)}"/><text class="comparison-axis-label" x="4" y="${y(max * step) + 4}">${Math.round(max * step)}</text>`).join("");
  const series = [];
  const categoryStyles = {basse: "low", moyenne: "mid", haute: "high"};
  Object.entries(comparisonPayload.categories).forEach(([category, rows]) => {
    ["min", "max", "mean"].forEach((stat) => {
      if (!comparisonState.get(`${category}-${stat}`)) return;
      series.push(`<path class="comparison-${categoryStyles[category]} comparison-${stat}" d="${comparisonPath(seasons.map((season) => rows[season]?.[stat]), x, y)}"><title>${category} montagne · ${stat}</title></path>`);
    });
  });
  [compareA.value, compareB.value].forEach((slug, index) => {
    if (!comparisonState.get(`station-${index === 0 ? "a" : "b"}`)) return;
    const station = comparisonPayload.stations[slug];
    if (station) series.push(`<path class="comparison-station station-${index === 0 ? "a" : "b"}" d="${comparisonPath(seasons.map((season) => station.values[season]), x, y)}"><title>${station.name}</title></path>`);
  });
  comparisonSeries.innerHTML = series.join("");
  document.querySelector("#comparison-axis").innerHTML = seasons.filter((_, index) => index % Math.ceil(seasons.length / 8) === 0 || index === seasons.length - 1).map((season) => `<text class="comparison-axis-label" text-anchor="middle" x="${x(seasons.indexOf(season))}" y="${height - 16}">${season}</text>`).join("");
  document.querySelector("#comparison-status").textContent = `${seasons.length} saisons comparées · moyenne de décembre à avril · hauteur modélisée en cm.`;
}

async function initializeComparison() {
  const options = [...stations].sort((a, b) => a.name.localeCompare(b.name, "fr")).map((station) => new Option(`${station.name} · ${station.altitude_category} montagne`, station.slug));
  compareA.replaceChildren(...options.map((option) => option.cloneNode(true)));
  compareB.replaceChildren(...options.map((option) => option.cloneNode(true)));
  compareA.value = selectedSlug;
  compareB.value = stations.find((station) => station.slug !== selectedSlug)?.slug || selectedSlug;
  async function refreshComparison() {
    if (compareA.value === compareB.value) {
      document.querySelector("#comparison-status").textContent = "Choisissez deux stations différentes pour comparer leur évolution.";
      return;
    }
    const response = await fetch(`/api/comparison?station=${encodeURIComponent(compareA.value)}&station=${encodeURIComponent(compareB.value)}`);
    comparisonPayload = response.ok ? await response.json() : null;
    if (comparisonPayload) drawComparison();
  }
  compareA.addEventListener("change", refreshComparison);
  compareB.addEventListener("change", refreshComparison);
  document.querySelectorAll(".stat-toggle").forEach((button) => button.addEventListener("click", () => {
    const key = button.dataset.stat;
    comparisonState.set(key, !comparisonState.get(key));
    button.classList.toggle("is-on", comparisonState.get(key));
    drawComparison();
  }));
  await refreshComparison();
}
