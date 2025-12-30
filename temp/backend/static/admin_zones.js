const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

let points = [];
let drawing = false;

/* 🔥 FORCE canvas sizing AFTER video actually starts */
video.addEventListener("loadeddata", () => {
  canvas.width = video.clientWidth;
  canvas.height = video.clientHeight;
  console.log("Canvas size:", canvas.width, canvas.height);
});

/* Start drawing */
function startDraw() {
  points = [];
  drawing = true;
  canvas.style.cursor = "crosshair";
}


/* Draw polygon */
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (points.length < 2) return;

  ctx.beginPath();
  points.forEach((p, i) => {
    if (i === 0) ctx.moveTo(p[0], p[1]);
    else ctx.lineTo(p[0], p[1]);
  });
  ctx.closePath();
  ctx.strokeStyle = "yellow";
  ctx.lineWidth = 2;
  ctx.stroke();
}

/* CLICK HANDLER — THIS WILL NOW WORK */
canvas.addEventListener("click", (e) => {
  if (!drawing) return;

  const rect = canvas.getBoundingClientRect();
  const x = Math.round(e.clientX - rect.left);
  const y = Math.round(e.clientY - rect.top);

  console.log("Canvas click:", x, y);

  points.push([x, y]);
  draw();
});

/* Save zone */
function saveZone() {
  canvas.style.cursor = "default";

  if (points.length < 3) {
    alert("Draw at least 3 points");
    return;
  }

  const id = parseInt(prompt("Zone ID"));
  const name = prompt("Zone name");
  const threshold = parseInt(prompt("Threshold"));

  fetch("/admin/zones", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + localStorage.getItem("token")
    },
    body: JSON.stringify({
      id,
      name,
      threshold,
      points: points.flat()
    })
  })
  .then(res => {
    if (!res.ok) throw new Error("Save failed");
    alert("Zone saved successfully");
    drawing = false;
  })
  .catch(err => alert(err.message));
}
