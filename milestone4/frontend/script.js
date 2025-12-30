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
if (role !== "admin") {
  ["exportSection", "exportHeading", "zoneMgmtHeading", "zoneManagementPanel"]
    .forEach(id => {
      const el = document.getElementById(id);
      if (el) el.style.display = "none";
    });
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

setInterval(updateDashboard, 1000);

/* ============================================================
   =============== ZONE DRAWING ===============================
   ============================================================ */

if (role === "admin") {
  initZoneDrawing();
  loadZoneList();
}

function initZoneDrawing() {
  const panel = document.getElementById("zoneManagementPanel");
  if (!panel) return;

  const frame = panel.querySelector(".zone-frame");
  if (!frame) return;

  const buttons = panel.querySelectorAll("button");
  const drawBtn = buttons[0];
  const saveBtn = buttons[1];
  const cancelBtn = buttons[2];

  drawBtn.disabled = false;
  saveBtn.disabled = true;
  cancelBtn.disabled = false;

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

  canvas.addEventListener("click", e => {
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
    const threshold = prompt("Enter threshold:");
    if (!name || !threshold) return;

    const flatPoints = points.flatMap(p => [
      Math.round(p.x),
      Math.round(p.y)
    ]);

    await authFetch(`${API_BASE}/zones/add`, {
      method: "POST",
      body: JSON.stringify({ name, threshold, points: flatPoints })
    });

    alert("Zone saved. Restart system to apply.");
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

    row.innerHTML = `<b>${z.name}</b><br>Threshold: ${z.threshold}<br>`;

    const renameBtn = document.createElement("button");
    renameBtn.innerText = "Rename";
    renameBtn.style.marginRight = "12px";   // ✅ spacing
    renameBtn.onclick = async () => {
      const newName = prompt("New zone name:", z.name);
      if (!newName) return;
      await authFetch(`${API_BASE}/zones/update`, {
        method: "PUT",
        body: JSON.stringify({ id: z.id, name: newName })
      });
      loadZoneList();
    };

    const thresholdBtn = document.createElement("button");
    thresholdBtn.innerText = "Edit Threshold";
    thresholdBtn.style.marginRight = "12px"; // ✅ spacing
    thresholdBtn.onclick = async () => {
      const t = prompt("New threshold:", z.threshold);
      if (!t) return;
      await authFetch(`${API_BASE}/zones/update`, {
        method: "PUT",
        body: JSON.stringify({ id: z.id, threshold: t })
      });
      loadZoneList();
    };

    const deleteBtn = document.createElement("button");
    deleteBtn.innerText = "Delete";
    // ❌ no margin on last button (clean edge)
    deleteBtn.onclick = async () => {
      if (!confirm(`Delete ${z.name}?`)) return;
      await authFetch(`${API_BASE}/zones/delete/${z.id}`, {
        method: "DELETE"
      });
      loadZoneList();
    };

    row.append(renameBtn, thresholdBtn, deleteBtn);
    list.appendChild(row);
  });
}
/************************************************************
 * ADDITIVE PATCH — ZONE COORDINATE NORMALIZATION
 * (Does NOT modify any existing feature)
 ************************************************************/

/**
 * Convert raw pixel points (drawn on frame.jpg)
 * into normalized [0–1] coordinates
 */
function normalizeZonePoints(rawPoints) {
  const img = document.querySelector(".zone-frame img");
  if (!img) return rawPoints; // safety fallback

  const w = img.clientWidth;
  const h = img.clientHeight;

  return rawPoints.map((v, i) =>
    i % 2 === 0
      ? +(v / w).toFixed(6)   // x
      : +(v / h).toFixed(6)   // y
  );
}

/**
 * Wrapper to be used ONLY when saving a zone
 * Existing draw logic remains untouched
 */
function saveZoneWithNormalization(zonePayload) {
  return {
    ...zonePayload,
    points: normalizeZonePoints(zonePayload.points)
  };
}

function downloadCSV() {
  fetch("http://127.0.0.1:5000/export/csv", {
    headers: {
      "Authorization": "Bearer " + localStorage.getItem("token")
    }
  })
  .then(res => {
    if (!res.ok) throw new Error("Download failed");
    return res.blob();
  })
  .then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "crowd_data.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  })
  .catch(err => alert(err.message));
}

function downloadPDF() {
  fetch("http://127.0.0.1:5000/export/pdf", {
    headers: {
      "Authorization": "Bearer " + localStorage.getItem("token")
    }
  })
  .then(res => {
    if (!res.ok) throw new Error("Download failed");
    return res.blob();
  })
  .then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "crowd_report.pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  })
  .catch(err => alert(err.message));
}
