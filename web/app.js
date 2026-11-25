"use strict";

const element = (id) => document.getElementById(id);
const video = element("video");
const chart = element("chart");
const context = chart.getContext("2d");
const overlay = element("overlay");
const lane = element("lane");
const seek = element("seek");
let records = [];
let objectUrl;

function load(rows, label) {
  if (!Array.isArray(rows) || !rows.length || rows.some(row =>
    !row || !Number.isFinite(row.time) || row.time < 0 ||
    typeof row.lane !== "string" || !row.lane ||
    !["estimate", "lower_bound", "uncertain"].includes(row.state) ||
    (row.state === "uncertain" ? row.count !== null : !Number.isInteger(row.count) || row.count < 0) ||
    (row.reference != null && (!Number.isInteger(row.reference) || row.reference < 0))
  )) {
    throw new Error("Expected rows with time, lane, state and count.");
  }
  records = [...rows].sort((a, b) => a.time - b.time);
  lane.replaceChildren(...[...new Set(records.map(row => row.lane))].map(id => new Option(id, id)));
  seek.max = Math.max(1, records[records.length - 1].time);
  seek.value = 0;
  element("source").textContent = label;
  render();
}

function render() {
  const rows = records.filter(row => row.lane === lane.value);
  if (!rows.length) return;
  const maxTime = Number(seek.max);
  const now = Number(seek.value);
  const showReference = element("reference").checked;
  const ceiling = rows.reduce((max, row) => Math.max(max, row.count ?? 0, showReference ? row.reference ?? 0 : 0), 1);
  const x = (s) => 40 + s / maxTime * (chart.width - 58);
  const y = (n) => 225 - n / ceiling * 188;
  context.clearRect(0, 0, chart.width, chart.height);
  context.font = "12px system-ui";
  for (const [index, row] of rows.entries()) {
    if (!["red", "amber", "green"].includes(row.phase)) continue;
    context.fillStyle = {red: "#392c36", amber: "#423c2d", green: "#233d37"}[row.phase];
    const next = rows[index + 1]?.time ?? row.time;
    context.fillRect(x(row.time), 22, x(next) - x(row.time), 203);
  }
  for (let step = 0; step <= 4; step++) {
    const n = Math.round(ceiling * step / 4);
    context.fillStyle = "#a9bdcf";
    context.fillText(String(n), 8, y(n) + 4);
    context.fillRect(40, y(n), chart.width - 58, 0.5);
  }
  for (const [field, color] of (showReference ? [["reference", "#d7bdf5"], ["count", "#7eedcb"]] : [["count", "#7eedcb"]])) {
    context.fillStyle = color;
    for (const row of rows) {
      if (row[field] == null) continue;
      const lower = field === "count" && row.state === "lower_bound";
      context.fillRect(x(row.time) - 2, y(row[field]) - 2, lower ? 8 : 4, 4);
    }
  }
  context.fillStyle = "#f2f6f8";
  context.fillRect(x(now), 22, 1, 203);
  context.fillText("0 s", 40, 246);
  context.fillText(maxTime.toFixed(1) + " s", chart.width - 75, 246);
  const current = rows.reduce((nearest, row) => row.time <= now ? row : nearest, null);
  paintOverlay(current);
  const estimate = current?.count == null ? "Uncertain" : current.count + (current.state === "lower_bound" ? "+ vehicles" : " vehicles");
  element("readout").textContent = current
    ? now.toFixed(1) + " s · " + estimate + (showReference && current.reference != null ? " · reference " + current.reference : "")
    : "No estimate at this timestamp";
}

function paintOverlay(row) {
  overlay.width = overlay.clientWidth;
  overlay.height = overlay.clientHeight;
  if (!video.videoWidth || !row || !Array.isArray(row.tracks)) return;
  const ctx = overlay.getContext("2d");
  const ratio = Math.min(overlay.width / video.videoWidth, overlay.height / video.videoHeight);
  const x = (overlay.width - video.videoWidth * ratio) / 2;
  const y = (overlay.height - video.videoHeight * ratio) / 2;
  ctx.translate(x, y);
  ctx.scale(ratio, ratio);
  ctx.font = "12px system-ui";
  for (const track of row.tracks) {
    if (!Array.isArray(track.box) || track.box.length !== 4 || !track.box.every(Number.isFinite)) continue;
    const [x1, y1, x2, y2] = track.box;
    const queued = row.visible_ids?.includes(track.id);
    ctx.strokeStyle = ctx.fillStyle = queued ? "#7eedcb" : "#9ab2c9";
    ctx.lineWidth = 2 / ratio;
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
    ctx.fillText(String(track.id), x1, y1 - 4);
  }
}

function move(time) {
  seek.value = time;
  if (Number.isFinite(video.duration)) video.currentTime = Math.min(Number(seek.value), video.duration);
  render();
}

function exportRows(format) {
  const fields = ["time", "lane", "count", "state", "phase", "phase_source", "model", "reference"];
  const cell = value => {
    const text = String(value ?? "");
    const safe = typeof value === "string" && /^[\s]*[=+@-]/.test(text) ? "'" + text : text;
    return '"' + safe.replaceAll('"', '""') + '"';
  };
  const output = format === "csv"
    ? [fields.join(","), ...records.map(row => fields.map(key => cell(row[key])).join(","))].join("\n")
    : JSON.stringify(records, null, 2);
  const url = URL.createObjectURL(new Blob([output], {type: format === "csv" ? "text/csv" : "application/json"}));
  const link = document.createElement("a");
  link.href = url;
  link.download = "queue-counts." + format;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

element("recording-file").addEventListener("change", event => {
  const file = event.target.files[0];
  if (!file) return;
  if (objectUrl) URL.revokeObjectURL(objectUrl);
  objectUrl = URL.createObjectURL(file);
  video.src = objectUrl;
  element("placeholder").hidden = true;
  element("status").textContent = "Local video loaded. Import predictions for this recording to compare.";
  records = [];
  lane.replaceChildren();
  context.clearRect(0, 0, chart.width, chart.height);
  paintOverlay(null);
  element("readout").textContent = "";
  element("source").textContent = "Local recording · awaiting predictions";
});
video.addEventListener("error", () => { element("status").textContent = "This recording could not be played."; });
element("predictions").addEventListener("change", async event => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    load(JSON.parse(await file.text()), "Imported predictions · " + file.name);
    element("status").textContent = "Predictions loaded.";
  } catch (error) {
    element("status").textContent = error.message;
  }
});
video.addEventListener("timeupdate", () => { seek.value = video.currentTime; render(); });
seek.addEventListener("input", () => move(Number(seek.value)));
lane.addEventListener("change", render);
element("reference").addEventListener("change", render);
chart.addEventListener("click", event => {
  const pixel = event.offsetX / chart.clientWidth * chart.width;
  move(Math.max(0, (pixel - 40) / (chart.width - 58) * Number(seek.max)));
});
for (const format of ["csv", "json"]) {
  element(format).addEventListener("click", () => {
    if (records.length) exportRows(format);
    else element("status").textContent = "Import predictions before exporting.";
  });
}
async function loadSample() {
  try {
    const response = await fetch("illustrative-cycle.json");
    if (!response.ok) throw new Error("Sample unavailable");
    load(await response.json(), "Synthetic signal cycle · track-state fixture");
    video.src = "illustrative-cycle.mp4";
    element("placeholder").hidden = true;
  } catch (error) {
    element("status").textContent = error.message;
  }
}

loadSample();

element("analyze").addEventListener("click", async () => {
  const button = element("analyze");
  const videoFile = element("recording-file").files[0];
  const configFile = element("camera-config").files[0];
  const status = element("status");
  if (!videoFile || !configFile) {
    status.textContent = "Choose a local recording and its camera configuration.";
    return;
  }
  button.disabled = true;
  status.textContent = "Analysing the recording locally…";
  try {
    const camera = JSON.stringify(JSON.parse(await configFile.text()));
    const response = await fetch("/analyze", {method: "POST", headers: {"X-Camera-Config": encodeURIComponent(camera)}, body: videoFile});
    if (!response.ok) throw new Error("Analysis failed. Check the local server, video and camera configuration.");
    const rows = await response.json();
    if (videoFile === element("recording-file").files[0]) {
      load(rows, "Local inference · " + videoFile.name);
      status.textContent = "Analysis complete.";
    }
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});
