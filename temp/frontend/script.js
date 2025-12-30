console.log("Dashboard JS LOADED");

// ---------------- CONFIG ----------------
const FETCH_INTERVAL = 1000;
const MAX_POINTS = 30;

// ---------------- STATE ----------------
let zoneNames = null;          // loaded ONCE
const histories = {};
const colors = {};
const zoneContainer = document.getElementById("zoneContainer");

// Stable color per zone (Milestone-3 style)
function color(id) {
  if (!colors[id]) {
    colors[id] = `hsl(${(parseInt(id) * 60) % 360},70%,50%)`;
  }
  return colors[id];
}

// ---------------- CHARTS ----------------
const lineChart = new Chart(lineChart, {
  type: "line",
  data: { labels: [], datasets: [] },
  options: {
    animation: false,
    responsive: true,
    maintainAspectRatio: false,
    scales: { y: { beginAtZero: true } }
  }
});

const bubbleChart = new Chart(bubbleChart, {
  type: "bubble",
  data: { datasets: [] },
  options: {
    animation: false,
    responsive: true,
    maintainAspectRatio: false,
    scales: { y: { beginAtZero: true } }
  }
});

// ---------------- LOAD ZONE CONFIG FIRST ----------------
fetch("/zone_config", { cache: "no-store" })
  .then(r => r.json())
  .then(cfg => {
    zoneNames = cfg;

    Object.entries(cfg).forEach(([id, info]) => {
      histories[id] = [];

      lineChart.data.datasets.push({
        zoneId: id,
        label: info.name,
        borderColor: color(id),
        data: [],
        fill: false,
        tension: 0.3
      });

      bubbleChart.data.datasets.push({
        zoneId: id,
        label: info.name,
        backgroundColor: color(id),
        data: []
      });
    });
  });

// ---------------- LIVE UPDATE ----------------
setInterval(() => {

  // 🔒 HARD GUARD: do NOTHING until names are loaded
  if (!zoneNames) return;

  fetch("/dashboard_data", { cache: "no-store" })
    .then(r => r.json())
    .then(d => {

      const timestamp = new Date().toLocaleTimeString();
      lineChart.data.labels.push(timestamp);
      if (lineChart.data.labels.length > MAX_POINTS) {
        lineChart.data.labels.shift();
      }

      zoneContainer.innerHTML = "";

      Object.entries(d.zones).forEach(([id, z]) => {

        histories[id].push(z.count);
        if (histories[id].length > MAX_POINTS) {
          histories[id].shift();
        }

        const lineSet = lineChart.data.datasets.find(ds => ds.zoneId === id);
        lineSet.data = histories[id];

        const bubbleSet = bubbleChart.data.datasets.find(ds => ds.zoneId === id);
        bubbleSet.data = histories[id].map((v, i) => ({
          x: i, y: v, r: Math.min(20, v)
        }));

        // ---- ZONE UI ----
        const div = document.createElement("div");
        div.className = "zone";
        div.innerHTML = `
          ${zoneNames[id].name}
          <span>${z.count}</span>
          <div class="alert">${z.alert ? "⚠ " + z.alert : ""}</div>
        `;
        zoneContainer.appendChild(div);
      });

      lineChart.update("none");
      bubbleChart.update("none");
    });

}, FETCH_INTERVAL);
