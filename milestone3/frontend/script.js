/* ---------------- LINE GRAPH ---------------- */

const lineCtx = document.getElementById("lineChart").getContext("2d");

const lineChart = new Chart(lineCtx, {
  type: "line",
  data: {
    labels: [],
    datasets: [
      { label: "Entrance", borderColor: "cyan", data: [], fill: false },
      { label: "Retail", borderColor: "green", data: [], fill: false },
      { label: "Food Court", borderColor: "orange", data: [], fill: false }
    ]
  },
  options: {
    responsive: true,
    animation: false,
    scales: {
      y: { beginAtZero: true }
    }
  }
});


/* ---------------- ACTIVITY HEATMAP ---------------- */

const heatmapCtx = document.getElementById("heatmapChart").getContext("2d");

const heatmapChart = new Chart(heatmapCtx, {
  type: "bubble",
  data: {
    datasets: [
      { label: "Entrance", backgroundColor: "rgba(0,255,255,0.6)", data: [] },
      { label: "Retail", backgroundColor: "rgba(0,255,0,0.6)", data: [] },
      { label: "Food Court", backgroundColor: "rgba(255,165,0,0.6)", data: [] }
    ]
  },
  options: {
    responsive: true,
    animation: false,
    scales: {
      x: { title: { display: true, text: "Time" } },
      y: { title: { display: true, text: "Activity Level" }, beginAtZero: true }
    }
  }
});


/* ---------------- LIVE DATA FETCH ---------------- */

setInterval(() => {
  fetch("http://127.0.0.1:5000/dashboard_data", { cache: "no-store" })
    .then(res => res.json())
    .then(data => {

      /* COUNTS */
      document.getElementById("entrance").innerText = data.zones.entrance.count;
      document.getElementById("retail").innerText = data.zones.retail.count;
      document.getElementById("foodcourt").innerText = data.zones.foodcourt.count;

      /* LINE GRAPH (BACKEND DRIVEN) */
      lineChart.data.labels = data.time;
      lineChart.data.datasets[0].data = data.zones.entrance.history;
      lineChart.data.datasets[1].data = data.zones.retail.history;
      lineChart.data.datasets[2].data = data.zones.foodcourt.history;
      lineChart.update();

      /* HEATMAP (DERIVED FROM BACKEND HISTORY — KEY FIX) */
      heatmapChart.data.datasets[0].data =
        data.zones.entrance.history.map((v, i) => ({
          x: i,
          y: v,
          r: Math.min(20, v)
        }));

      heatmapChart.data.datasets[1].data =
        data.zones.retail.history.map((v, i) => ({
          x: i,
          y: v,
          r: Math.min(20, v)
        }));

      heatmapChart.data.datasets[2].data =
        data.zones.foodcourt.history.map((v, i) => ({
          x: i,
          y: v,
          r: Math.min(20, v)
        }));

      heatmapChart.update();

      /* ALERT */
      document.getElementById("alert").style.display =
        data.zones.foodcourt.alert ? "block" : "none";
    });
}, 3000);
