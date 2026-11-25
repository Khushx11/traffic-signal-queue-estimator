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
