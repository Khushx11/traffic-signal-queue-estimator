# Fixed traffic-signal camera data

A roadside input camera should show the stop line and the upstream approach
from a fixed mount. Assess full queue visibility separately for each lane.
Keep aerial and roadside scores separate.

## US DOT roadside camera pilot

The [Intersection Safety Challenge Stage 1B validation sample](https://data.transportation.gov/Roadways-and-Bridges/Intersection-Safety-Challenge-Stage-1B-Validation-/j58q-ymi4)
contains RGB footage at a controlled signalised intersection in McLean,
Virginia. The [collection overview](https://data.transportation.gov/stories/s/U-S-DOT-Intersection-Safety-Challenge-Stage-1B-Sys/smqb-i5sx/)
describes the controlled scenarios, sensor calibration and missing controller
data for some runs.

```sh
python3 scripts/download_roadside.py data/local/roadside
python3 scripts/audit_roadside_clock.py \
  data/local/roadside/VisualCamera6_Run_1003_frame-timing.csv \
  data/local/roadside/Run_1003_GT.csv --timezone America/New_York
```

Run 1003 includes a sensor recording log, frame timestamps and scenario
ground-truth tracks. The sensor log does not contain phase transitions.
Using the local Eastern time assumption for the camera CSV, 730 of 758
ground-truth timestamps fall within the camera timestamp span. This is a
clock overlap check. It does not verify frame-to-event alignment or identify
a full light cycle. The ground truth covers the scripted actors. It does not
provide lane-by-lane natural traffic queue counts.

Run 1023 has an explicit V2XHub SPaT packet capture, in addition to video,
frame timestamps and scenario tracks. Decoding the phase messages, mapping
signal groups to lanes and checking usable cycles are separate steps.
Treat the two runs as scenarios at a single physical test site.

## Other sources

- [Aalborg University's MTID](https://vap.aau.dk/mtid/) synchronises
  a pole camera with a drone reference at one operating intersection.
  The publisher-linked Kaggle archive request returned HTTP 404 in this pilot.
- [TUMTraf Intersection](https://innovation-mobility.com/en/project-providentia/a9-dataset/)
  provides gantry-mounted RGB views and synchronised LiDAR. Publisher
  registration is required. It is a candidate for roadside occlusion tests.

The repository stores the source registry and audit code. Use the publisher
downloads for media and sensor files.
