# Reference protocol

Annotate from original video, time-aligned supporting tracks, or both. Record
each source and the view used. Inspect a predeclared sequence of timestamps,
including visible zero counts, and retain unknown reference rows with a reason.
Never use the evaluated detector to propose a reference count.

Count a vehicle if it is in the approach lane upstream of its stop line and is
stopped or slowly moving as part of a close, connected line of vehicles waiting
for the intersection. The pilot queue state machine starts with 1 m/s, one
second of dwell, and a maximum gap of eight metres. Document any changes based
on development examples. Treat vehicles that move away on green as discharged
when they leave the stopped queue, even if still inside the lane. Track lane
changes from the earliest interval in which the new lane can be resolved.
Continue recording a residual queue through a phase boundary.

Use clear, partial or heavy occlusion based on loss of vehicle visibility in the
input view. Apply a separate flag when the queue tail might extend beyond the
view. Mark a count unknown when an alternate view or trustworthy aligned track
cannot establish it. Retain phase as unknown when there is no verified record.
Do not infer a phase change solely from movement.

Each reference row includes the physical intersection, recording, lane,
time in seconds, split, verified cycle identifier when available, phase,
occlusion category and integer reference count or null. Save timestamps for
cross-view checks and the evidence behind corrections. If cycles are scored,
use complete audited intervals and define the sampling cadence in the manifest.

For cycle peak scoring, attach the same integer `cycle_start_ms`, exclusive
`cycle_end_ms`, and positive `cycle_step_ms` to every row in a lane cycle.
Two or more expected sample timestamps must all be present exactly once, with
a reference count and an estimate at each timestamp. Derive the bounds from
independently verified phase transitions.
