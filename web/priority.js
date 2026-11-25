"use strict";

function planIntersection(approaches, crossings, threshold) {
  const hasDemand = approaches.some(item => item.minimum >= threshold);
  const order = approaches.map((item, index) => ({...item, index}));
  if (hasDemand) {
    order.sort((a, b) => Number(b.minimum >= threshold) - Number(a.minimum >= threshold)
      || (a.minimum >= threshold ? b.minimum - a.minimum : 0) || a.index - b.index);
  }

  const timeline = [];
  let elapsed = 0;
  function add(label, seconds, reason) {
    timeline.push({label, seconds, reason, start: elapsed});
    elapsed += seconds;
  }

  // Exclusive pedestrian service avoids mixing crossing phases with vehicle turns.
  for (const crossing of crossings) {
    add(crossing.name, crossing.walk, "Walk");
    add(crossing.name, crossing.clearance, "Pedestrian clearance");
    add("All red", 2, "Separation");
  }
  for (const approach of order) {
    const priority = approach.minimum >= threshold;
    add(approach.name, priority ? Math.min(35, 12 + approach.minimum) : 12,
        priority ? "Queue threshold reached" : "Regular service");
    add(approach.name, 3, "Amber");
    add("All red", 2, "Separation");
  }
  return timeline;
}

if (typeof module !== "undefined") module.exports = {planIntersection};
