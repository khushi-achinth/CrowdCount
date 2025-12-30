console.log("Dashboard Loaded");

// ---------------- CONFIG ----------------
const FETCH_INTERVAL = 1000; // 1 second
const MAX_POINTS = 30;       // last 30 seconds
// --------------------------------------

// ---------------- LINE GRAPH ----------------
const lineCtx = document.getElementById("lineChart").getContext("2d");

const lineChart = new Chart(lineCtx, {
  type: "line",
  data: {
    labels: [],
    datasets: [
      { label: "Entrance", borderColor: "cyan", data: [], fill: false },
      { label: "Walk Path", borderColor: "green", data: [], fill: false },
      { label: "Exit", borderColor: "orange", data: [], fill: false }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    scales: {
      x: {
        ticks: { maxTicksLimit: 10 }
      },
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 2   // 2 people interval
        }
      }
    }
  }
});

// ---------------- BUBBLE GRAPH ----------------
const bubbleCtx = document.getElementById("bubbleChart").getContext("2d");

const bubbleChart = new Chart(bubbleCtx, {
  type: "bubble",
  data: {
    datasets: [
      { label: "Entrance", backgroundColor: "rgba(0,255,255,0.6)", data: [] },
      { label: "Walk Path", backgroundColor: "rgba(0,255,0,0.6)", data: [] },
      { label: "Exit", backgroundColor: "rgba(255,165,0,0.6)", data: [] }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    scales: {
      x: { title: { display: true, text: "Time (seconds)" } },
      y: { beginAtZero: true }
    }
  }
});

// ---------------- LIVE FETCH (1 SECOND) ----------------
setInterval(() => {
  fetch("http://127.0.0.1:5000/dashboard_data", { cache: "no-store" })
    .then(res => res.json())
    .then(data => {

      // Live counts
      entrance.innerText = data.zones.entrance.count;
      walkpath.innerText = data.zones.walkpath.count;
      exit.innerText = data.zones.exit.count;

      // ---- LINE GRAPH ----
      lineChart.data.labels = data.time.slice(-MAX_POINTS);
      lineChart.data.datasets[0].data =
        data.zones.entrance.history.slice(-MAX_POINTS);
      lineChart.data.datasets[1].data =
        data.zones.walkpath.history.slice(-MAX_POINTS);
      lineChart.data.datasets[2].data =
        data.zones.exit.history.slice(-MAX_POINTS);

      lineChart.update("none");

      // ---- BUBBLE GRAPH ----
      bubbleChart.data.datasets[0].data =
        data.zones.entrance.history.slice(-MAX_POINTS)
          .map((v, i) => ({ x: i, y: v, r: Math.min(20, v) }));

      bubbleChart.data.datasets[1].data =
        data.zones.walkpath.history.slice(-MAX_POINTS)
          .map((v, i) => ({ x: i, y: v, r: Math.min(20, v) }));

      bubbleChart.data.datasets[2].data =
        data.zones.exit.history.slice(-MAX_POINTS)
          .map((v, i) => ({ x: i, y: v, r: Math.min(20, v) }));

      bubbleChart.update("none");

      // ---- ALERTS ----
      ["entrance","walkpath","exit"].forEach(zone => {
        const box = document.getElementById(`${zone}-alert`);
        const msg = data.zones[zone].alert;

        if (msg) {
          box.innerText = "⚠ " + msg;
          box.style.display = "block";
        } else {
          box.style.display = "none";
        }
      });

    })
    .catch(err => console.error("Fetch error:", err));
}, FETCH_INTERVAL);