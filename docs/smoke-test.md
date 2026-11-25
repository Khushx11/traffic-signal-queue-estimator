# Real-video smoke test

The first 120 frames from raw Peachtree camera 1 during the 16:00–16:15
collection ran through YOLO11n, ByteTrack, two image-marked approach lanes
and the temporal queue estimator. The raw input is 640 × 480 at 10 fps.
The detector processed the 120 frames in 8.62 seconds on the local Mac CPU,
including model inference, tracking, and in-memory result creation. Script
startup and writing the output file are outside that time.

This run uses approximate ground reference dimensions, with no audited labels
used for the run. It establishes pipeline execution and gives an indicative
throughput of 13.9 frames per second for this short preview. It does not
establish count accuracy, occlusion robustness or reliable queue tail metres.

The occupancy extraction also ran on 10 raw frames and wrote 20
lane/timestamp observations. Conversion to counts requires a labelled
development calibration file.

See [the video pilot dependency versions](../requirements-video-pilot.txt) and
[the camera setup](../configs/peachtree-camera1-pilot.json).

A second completed run on the first 900 decoded frames of the complete
Peachtree archive member took 59.15 seconds on the same CPU, or 15.2 frames
per second. It produced 1,800 lane-timestamp rows across two lanes. The
prototype issued an estimate for 1,758 rows and marked 42 uncertain. These
are counts of output states before any accuracy audit. In particular, the
high estimate coverage does not validate the confidence heuristic.

## Audit follow-up

Reviewing the saved outputs showed that every issued estimate in the original
900-frame run was zero. The decoded approach contains stopped vehicles.
That run remains useful for timing only.

The revised estimator abstains when there is no evidence for a zero. A causal
longitudinal speed estimate smooths short-term detector jitter. On 120
Peachtree frames, full-frame inference produced tracks on 143 of 240
lane-timestamps. Approach cropping produced tracks on 176. Both variants
abstained on all 240. Longer diagnostic traces include stable slow vehicles
roughly 29–34 nominal metres upstream and intermittent tracks near the stop
line. The estimator cannot establish a continuous queue from those tracks.
Ground dimensions are approximate. These diagnostic frames should be
excluded from any future frozen test split if they guide tuning.
