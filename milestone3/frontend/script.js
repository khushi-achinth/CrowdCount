console.log("PAGE LOADED", new Date().toLocaleTimeString());

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
      y: { beginAtZero: true }
    }
  }
});


/* ---------------- LIVE DATA FETCH ---------------- */

const UPDATE_INTERVAL = 1000; // 🔥 1 second

setInterval(() => {
  fetch("http://127.0.0.1:5000/dashboard_data", { cache: "no-store" })
    .then(res => res.json())
    .then(data => {

      // COUNTS
      entrance.innerText = data.zones.entrance.count;
      retail.innerText = data.zones.retail.count;
      foodcourt.innerText = data.zones.foodcourt.count;

      // LINE GRAPH (SMOOTH, LIMITED HISTORY)
      lineChart.data.labels = data.time.slice(-20);
      lineChart.data.datasets[0].data = data.zones.entrance.history.slice(-20);
      lineChart.data.datasets[1].data = data.zones.retail.history.slice(-20);
      lineChart.data.datasets[2].data = data.zones.foodcourt.history.slice(-20);
      lineChart.update("none");

      // HEATMAP (UNCHANGED LOGIC)
      heatmapChart.data.datasets[0].data =
        data.zones.entrance.history.map((v,i)=>({x:i,y:v,r:Math.min(20,v)}));
      heatmapChart.data.datasets[1].data =
        data.zones.retail.history.map((v,i)=>({x:i,y:v,r:Math.min(20,v)}));
      heatmapChart.data.datasets[2].data =
        data.zones.foodcourt.history.map((v,i)=>({x:i,y:v,r:Math.min(20,v)}));
      heatmapChart.update("none");

      // ZONE ALERTS
      ["entrance","retail","foodcourt"].forEach(zone => {
        const box = document.getElementById(`${zone}-alert`);
        const msg = data.zones[zone].alert;

        if (msg) {
          box.innerText = "⚠ " + msg;
          box.style.display = "block";
        } else {
          box.style.display = "none";
        }
      });

    });
}, UPDATE_INTERVAL);
