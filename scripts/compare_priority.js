"use strict";

// Run identical arrival streams through both replay policies in a simple queue simulation.
const {planIntersection} = require("../web/priority");
const names = ["North", "East", "South", "West"];

function arrivals(rates, seconds, seed) {
  let state = seed >>> 0;
  function draw() {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 4294967296;
  }
  return Array.from({length: seconds}, (_, time) => ({
    vehicles: rates.map(rate => Number(draw() < rate)),
    pedestrians: time % 47 === 12 ? 1 : 0,
  }));
}

function run(input, threshold) {
  const queues = names.map(() => []);
  const pedestrians = [];
  let phase = null, remaining = 0, phases = [];
  let vehicleWait = 0, pedestrianWait = 0, maxPedestrianWait = 0, departed = 0, pedestriansServed = 0, peakQueue = 0;
  for (const [time, events] of input.entries()) {
    events.vehicles.forEach((num, i) => {
      for (let j = 0; j < num; j++) queues[i].push(time);
    });
    for (let j = 0; j < events.pedestrians; j++) pedestrians.push(time);
    if (remaining === 0) {
      if (phases.length === 0) {
        phases = planIntersection(names.map((name, i) => ({name, minimum: queues[i].length})),
          pedestrians.length ? [{name: "Crosswalk", walk: 7, clearance: 14}] : [], threshold);
      }
      phase = phases.shift();
      remaining = phase.seconds;
    }
    if (phase.reason === "Walk") {
      while (pedestrians.length) {
        maxPedestrianWait = Math.max(maxPedestrianWait, time - pedestrians.shift());
        pedestriansServed++;
      }
    }
    if ((phase.reason === "Queue threshold reached" || phase.reason === "Regular service")
        && (phase.seconds - remaining) % 2 === 1) {
      const queue = queues[names.indexOf(phase.label)];
      if (queue.length) {
        queue.shift();
        departed++;
      }
    }
    const queued = queues.reduce((total, queue) => total + queue.length, 0);
    peakQueue = Math.max(peakQueue, queued);
    vehicleWait += queued;
    pedestrianWait += pedestrians.length;
    remaining--;
  }
  for (const arrival of pedestrians) maxPedestrianWait = Math.max(maxPedestrianWait, input.length - arrival);
  return {vehicleQueueSeconds: vehicleWait, pedestrianQueueSeconds: pedestrianWait,
    maxObservedPedestrianWait: maxPedestrianWait, peakTotalQueue: peakQueue,
    vehiclesDeparted: departed, pedestriansServed, pedestrianBacklog: pedestrians.length,
    vehicleBacklog: queues.reduce((total, queue) => total + queue.length, 0)};
}

const outputs = {};
for (const [name, rates] of Object.entries({balanced: [.08, .08, .08, .08], asymmetric: [.06, .22, .05, .08]})) {
  const input = arrivals(rates, 900, 419);
  outputs[name] = {fixed: run(input, Infinity), adaptive: run(input, 10)};
}
process.stdout.write(JSON.stringify({durationSeconds: 900, seed: 419, scenarios: outputs}, null, 2) + "\n");
