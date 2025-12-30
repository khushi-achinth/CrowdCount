const API_BASE = "http://127.0.0.1:5000";
const token = localStorage.getItem("token");
const role = localStorage.getItem("role");

if (!token) {
  alert("Session expired. Please login again.");
  window.location.replace("login.html");
}

/* ---------- LOGOUT ---------- */
function logout() {
  localStorage.clear();
  window.location.replace("login.html");
}

/* ---------- AUTH FETCH ---------- */
function authFetch(url, options = {}) {
  return fetch(url, {
    ...options,
    headers: {
      "Authorization": "Bearer " + token,
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });
}

/* ---------- ROLE-BASED UI ---------- */
/* ---------- ROLE-BASED UI ---------- */
if (role !== "admin") {
  const exportSection = document.getElementById("exportSection");
  const exportHeading = document.getElementById("exportHeading");
  const zoneMgmtHeading = document.getElementById("zoneMgmtHeading");
  const zonePanel = document.getElementById("zoneManagementPanel");

  if (exportSection) exportSection.style.display = "none";
  if (exportHeading) exportHeading.style.display = "none";
  if (zoneMgmtHeading) zoneMgmtHeading.style.display = "none";
  if (zonePanel) zonePanel.style.display = "none";

} else {
  const zonePanel = document.getElementById("zoneManagementPanel");
  if (zonePanel) zonePanel.style.display = "block";
}



/* ---------- CHART SETUP ---------- */
const lineCtx = document.getElementById("lineChart").getContext("2d");
const barCtx = document.getElementById("barChart").getContext("2d");

let lineChart = null;
let barChart = null;
let zoneNames = null;

const COLORS = [
  "#00E5FF", "#FF6F00", "#66BB6A", "#AB47BC",
  "#FF5252", "#FFD740", "#29B6F6", "#EC407A"
];

function initCharts(zones) {
  zoneNames = zones.slice();

  lineChart = new Chart(lineCtx, {
    type: "line",
    data: {
      labels: [],
      datasets: zoneNames.map((z, i) => ({
        label: z,
        data: [],
        borderColor: COLORS[i % COLORS.length],
        fill: false
      }))
    },
    options: { animation: false }
  });

  barChart = new Chart(barCtx, {
    type: "bar",
    data: {
      labels: zoneNames,
      datasets: [{
        data: zoneNames.map(() => 0),
        backgroundColor: zoneNames.map((_, i) => COLORS[i % COLORS.length])
      }]
    },
    options: {
      animation: false,
      plugins: { legend: { display: false } }
    }
  });
}

/* ---------- DASHBOARD UPDATE ---------- */
async function updateDashboard() {
  const res = await authFetch(`${API_BASE}/dashboard_data`);
  const data = await res.json();

  const zones = Object.keys(data.zones);
  if (!zoneNames && zones.length > 0) initCharts(zones);
  if (!zoneNames) return;

  const t = data.time[data.time.length - 1];
  lineChart.data.labels.push(t);
  zoneNames.forEach((z, i) => {
    lineChart.data.datasets[i].data.push(data.zones[z].count);
  });
  lineChart.update("none");

  barChart.data.datasets[0].data =
    zoneNames.map(z => data.zones[z].count);
  barChart.update("none");

  /* ZONE OCCUPANCY */
  const zoneDiv = document.getElementById("zonesContainer");
  zoneDiv.innerHTML = "";
  zoneNames.forEach(z => {
    const zd = data.zones[z];
    const el = document.createElement("div");
    el.className = "zone";
    el.innerHTML = `${z} <span>${zd.count}</span>`;
    if (zd.alert) {
      const a = document.createElement("div");
      a.className = "alert";
      a.innerText = zd.alert;
      a.style.display = "block";
      el.appendChild(a);
    }
    zoneDiv.appendChild(el);
  });

  /* ANALYTICS */
  const analyticsDiv = document.getElementById("analyticsContainer");
  analyticsDiv.innerHTML = "";

  zoneNames.forEach(z => {
    const zd = data.zones[z];
    const status = !zd.alert
      ? { text: "Safe", color: "#4CAF50" }
      : zd.alert.toLowerCase().includes("approaching")
        ? { text: "Approaching limit", color: "#FF9800" }
        : { text: "Overcrowded", color: "#F44336" };

    const box = document.createElement("div");
    box.style.padding = "10px";
    box.style.margin = "6px 0";
    box.style.borderLeft = `6px solid ${status.color}`;
    box.style.background = "#f9f9f9";
    box.style.color = "#000";

    box.innerHTML = `
      <b>${z}</b><br>
      Current Count: <b>${zd.count}</b><br>
      Threshold: <b>${zd.threshold}</b><br>
      Status: <span style="color:${status.color};font-weight:bold">${status.text}</span>
    `;
    analyticsDiv.appendChild(box);
  });
}

/* ---------- EXPORTS ---------- */
function downloadCSV() {
  window.open(`${API_BASE}/export/csv`, "_blank");
}
function downloadPDF() {
  window.open(`${API_BASE}/export/pdf`, "_blank");
}

setInterval(updateDashboard, 1000);

/* ============================================================
   =============== PHASE 4A + 4B — ZONE DRAWING ===============
   ============================================================ */

if (role === "admin") {
  initZoneDrawing();
}

function initZoneDrawing() {
  const panel = document.getElementById("zoneManagementPanel");

  const frame = panel.querySelector("div[style*='height']");
  const controls = panel.querySelectorAll("div")[1];
  const buttons = controls.querySelectorAll("button");

  const drawBtn = buttons[0];
  const saveBtn = buttons[1];
  const cancelBtn = buttons[2];

  // ✅ ENABLE DRAW BUTTON
  drawBtn.disabled = false;
  saveBtn.disabled = true;
  cancelBtn.disabled = false;

  /* Canvas overlay */
  const canvas = document.createElement("canvas");
  canvas.width = frame.clientWidth;
  canvas.height = frame.clientHeight;
  canvas.style.position = "absolute";
  canvas.style.top = "0";
  canvas.style.left = "0";
  canvas.style.cursor = "crosshair";

  frame.style.position = "relative";
  frame.appendChild(canvas);

  const ctx = canvas.getContext("2d");

  let drawing = false;
  let points = [];

  drawBtn.onclick = () => {
    points = [];
    drawing = true;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    saveBtn.disabled = true;
  };

  cancelBtn.onclick = () => {
    drawing = false;
    points = [];
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    saveBtn.disabled = true;
  };

  canvas.addEventListener("click", (e) => {
    if (!drawing) return;
    const r = canvas.getBoundingClientRect();
    points.push({ x: e.clientX - r.left, y: e.clientY - r.top });
    redraw();
  });

  canvas.addEventListener("dblclick", () => {
    if (points.length < 3) return;
    drawing = false;
    redraw(true);
    saveBtn.disabled = false;
  });

  saveBtn.onclick = async () => {
    const name = prompt("Enter zone name:");
    if (!name) return;

    const threshold = prompt("Enter threshold:");
    if (!threshold) return;

    const flatPoints = points.flatMap(p => [
      Math.round(p.x),
      Math.round(p.y)
    ]);

    const res = await authFetch(`${API_BASE}/zones/add`, {
      method: "POST",
      body: JSON.stringify({
        name,
        threshold,
        points: flatPoints
      })
    });

    const result = await res.json();
    alert(result.message || "Zone saved. Restart system to apply.");

    saveBtn.disabled = true;
    loadZoneList();

  };

  function redraw(close = false) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = "#00E5FF";
    ctx.lineWidth = 2;

    if (points.length) {
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      points.slice(1).forEach(p => ctx.lineTo(p.x, p.y));
      if (close) ctx.lineTo(points[0].x, points[0].y);
      ctx.stroke();
    }

    ctx.fillStyle = "#FF5252";
    points.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
      ctx.fill();
    });
  }
}

/* ================= EXISTING ZONES LIST ================= */

async function loadZoneList() {
  if (role !== "admin") return;

  const res = await authFetch(`${API_BASE}/zones`);
  const zones = await res.json();

  const list = document.getElementById("zoneList");
  list.innerHTML = "";

  zones.forEach(z => {
    const row = document.createElement("div");
    row.style.borderBottom = "1px solid #ccc";
    row.style.padding = "8px";

    const renameBtn = document.createElement("button");
    renameBtn.innerText = "Rename";
    renameBtn.onclick = async () => {
      const newName = prompt("New zone name:", z.name);
      if (!newName) return;

      await authFetch(`${API_BASE}/zones/update`, {
        method: "PUT",
        body: JSON.stringify({ id: z.id, name: newName })
      });

      loadZoneList();
      alert("Renamed. Restart system to apply.");
    };

    const thresholdBtn = document.createElement("button");
    thresholdBtn.innerText = "Edit Threshold";
    thresholdBtn.onclick = async () => {
      const t = prompt("New threshold:", z.threshold);
      if (!t) return;

      await authFetch(`${API_BASE}/zones/update`, {
        method: "PUT",
        body: JSON.stringify({ id: z.id, threshold: t })
      });

      loadZoneList();
      alert("Threshold updated. Restart system to apply.");
    };

    const deleteBtn = document.createElement("button");
    deleteBtn.innerText = "Delete";
    deleteBtn.onclick = async () => {
      if (!confirm(`Delete zone "${z.name}"?`)) return;

      await authFetch(`${API_BASE}/zones/delete/${z.id}`, {
        method: "DELETE"
      });

      loadZoneList();
      alert("Zone deleted. Restart system to apply.");
    };

    row.innerHTML = `<b>${z.name}</b><br>Threshold: ${z.threshold}<br>`;
    row.append(renameBtn, thresholdBtn, deleteBtn);
    list.appendChild(row);
  });
}

/* call once on load */
if (role === "admin") {
  loadZoneList();
}

