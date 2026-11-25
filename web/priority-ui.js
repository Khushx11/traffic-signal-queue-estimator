"use strict";

function renderPriority() {
  const threshold = Number(element("priority-threshold").value);
  const length = Number(element("crossing-length").value);
  if (!Number.isInteger(threshold) || threshold < 1 || !Number.isFinite(length) || length < 1 || length > 100) {
    element("priority-summary").textContent = "Enter a positive queue threshold and a crossing length of 1–100 m.";
    element("priority-order").replaceChildren();
    return;
  }
  const demo = element("priority-demo").checked;
  const groups = new Map();
  if (demo) {
    for (const [name, count] of [["North", 4], ["East", 14], ["South", 7], ["West", 2]]) {
      groups.set(name, {name, minimum: count, incomplete: false});
    }
  } else {
    const assignments = new Map();
    for (const line of element("approach-map").value.split("\n")) {
      const [laneId, name, extra] = line.split("=").map(value => value.trim());
      if (!laneId && !name) continue;
      if (!laneId || !name || extra !== undefined || assignments.has(laneId)) {
        element("priority-summary").textContent = "Use one unique lane=approach assignment on each line.";
        element("priority-order").replaceChildren();
        return;
      }
      assignments.set(laneId, name);
    }
    const position = Number(seek.value);
    const latest = new Map();
    for (const row of records) {
      if (row.time <= position && position - row.time <= 0.5) latest.set(row.lane, row);
    }
    const laneIds = new Set([...records.map(row => row.lane), ...assignments.keys()]);
    for (const laneId of laneIds) {
      const name = assignments.get(laneId) || laneId;
      const group = groups.get(name) || {name, minimum: 0, incomplete: false};
      const row = latest.get(laneId);
      group.minimum += row?.count ?? 0;
      group.incomplete ||= row?.state !== "estimate";
      groups.set(name, group);
    }
  }
  const approaches = [...groups.values()];
  const crossingInputs = element("crossing-calls").value.split("\n").map(line => line.trim()).filter(Boolean);
  const crossings = [];
  const names = new Set();
  for (const input of crossingInputs) {
    const [name, distance, extra] = input.split("=").map(value => value.trim());
    const metres = Number(distance);
    if (!name || names.has(name) || extra !== undefined || !Number.isFinite(metres) || metres < 1 || metres > 100) {
      element("priority-summary").textContent = "Give each pending crossing a unique name and length, such as North crosswalk=14.";
      element("priority-order").replaceChildren();
      return;
    }
    names.add(name);
    crossings.push({name, walk: 7, clearance: Math.ceil(metres)});
  }
  if (!crossings.length && element("pedestrian-call").checked) {
    crossings.push({name: "Pedestrian crossing", walk: 7, clearance: Math.ceil(length)});
  }
  const timeline = planIntersection(approaches, crossings, threshold);
  const busiest = approaches.reduce((best, item) => !best || item.minimum > best.minimum ? item : best, null);
  const coverageNote = approaches.some(item => item.incomplete) ? " · Some approaches have incomplete counts." : "";
  element("priority-summary").textContent = approaches.length
    ? approaches.map(item => item.name + " " + (item.incomplete
      ? item.minimum ? item.minimum + "+" : "unknown" : item.minimum)).join(" · ") + (busiest.minimum > 0 ? " · Highest reported demand: " + busiest.name + "." : "") + coverageNote
    : "Load queue rows or use the four-approach example.";
  const items = timeline.map(item => {
    const li = document.createElement("li");
    li.textContent = item.start + " s · " + item.label + " · " + item.reason + " (" + item.seconds + " s)";
    return li;
  });
  element("priority-order").replaceChildren(...items);
}

element("plan-priority").addEventListener("click", renderPriority);
renderPriority();
