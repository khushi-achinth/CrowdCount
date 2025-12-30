const lineCtx = document.getElementById("lineChart").getContext("2d");
const barCtx = document.getElementById("barChart").getContext("2d");

let lineChart = null;
let barChart = null;

/* ---------- GUARANTEED UNIQUE & STABLE COLORS ---------- */
const COLOR_PALETTE = [
  "#00E5FF", "#FF6F00", "#66BB6A", "#AB47BC",
  "#FF5252", "#FFD740", "#29B6F6", "#EC407A",
  "#7E57C2", "#26A69A"
];

const zoneColors = {};

function getColor(zone, index) {
  if (!zoneColors[zone]) {
    zoneColors[zone] = COLOR_PALETTE[index % COLOR_PALETTE.length];
  }
  return zoneColors[zone];
}

/* ---------- INITIALIZE CHARTS ---------- */
function initCharts(zones) {

  /* ---- LINE GRAPH (unchanged) ---- */
  const lineDatasets = zones.map((z, i) => ({
    label: z,
    data: [],
    borderColor: getColor(z, i),
    fill: false,
    tension: 0.3
  }));

  lineChart = new Chart(lineCtx, {
    type: "line",
    data: {
      labels: [],
      datasets: lineDatasets
    },
    options: {
      responsive: true,
      animation: false,
      scales: {
        y: { beginAtZero: true }
      }
    }
  });

  /* ---- BAR GRAPH (ZONE SNAPSHOT, NO LEGEND) ---- */
  barChart = new Chart(barCtx, {
    type: "bar",
    data: {
      labels: zones,
      datasets: [{
        data: zones.map(() => 0),
        backgroundColor: zones.map((z, i) => getColor(z, i))
      }]
    },
    options: {
      responsive: true,
      animation: false,
      plugins: {
        legend: {
          display: false   // 🔥 LEGEND REMOVED
        }
      },
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
}

/* ---------- UPDATE DASHBOARD ---------- */
async function updateDashboard() {
  const res = await fetch("http://127.0.0.1:5000/dashboard_data");
  const payload = await res.json();

  const zones = Object.keys(payload.zones);
  if (!lineChart) initCharts(zones);

  const timestamp = payload.time[payload.time.length - 1];

  /* ---- LINE GRAPH ---- */
  lineChart.data.labels.push(timestamp);
  zones.forEach((z, i) => {
    lineChart.data.datasets[i].data.push(payload.zones[z].count);
  });
  lineChart.update();

  /* ---- BAR GRAPH (LIVE COUNTS) ---- */
  barChart.data.datasets[0].data = zones.map(
    z => payload.zones[z].count
  );
  barChart.update();

  /* ---- ZONE COUNTS + ALERTS ---- */
  const container = document.getElementById("zonesContainer");
  container.innerHTML = "";

  zones.forEach(z => {
    const zoneData = payload.zones[z];

    const zoneDiv = document.createElement("div");
    zoneDiv.className = "zone";
    zoneDiv.innerHTML = `${z} <span>${zoneData.count}</span>`;

    const alertDiv = document.createElement("div");
    alertDiv.className = "alert";
    alertDiv.innerText = zoneData.alert || "";
    alertDiv.style.display = zoneData.alert ? "block" : "none";

    zoneDiv.appendChild(alertDiv);
    container.appendChild(zoneDiv);
  });
}

setInterval(updateDashboard, 1000);
