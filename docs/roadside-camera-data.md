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
frame timestamps and scenario tracks. Its decoded groups held steady throughout the run.
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

## Local decode check

Visual Camera 6 in Run 1003 decoded all 1,937 frames without a decoder
warning. The encoded playback lasts 64.567 seconds, while the publisher's
per-frame capture clock spans 73.093 seconds. Use the capture timestamps
when joining to reference tracks. Frame index divided by nominal playback
FPS would use the wrong timebase. The inspected view shows a crosswalk,
stop-line markings and signal hardware. The view of the upstream approach
is limited, so it is useful as a camera-view check. It does not establish
eligibility for a complete queue benchmark.

Run 1023 shows the same view at night. It decoded all 1,669 frames without
decoder warnings. Encoded playback lasts 55.633 seconds across a capture
clock span of 61.513 seconds. Under the same Eastern time assumption, 614
of 636 scenario reference timestamps overlap the camera capture range.
The decoded SPaT capture contains no observed movement-state changes.
See the [clock overlap report](../results/roadside-clock-overlap.json).

## Run clock-aware inference

The example layout below is for software validation. Its ground dimensions
are approximate, and the view has limited upstream coverage.

```sh
mkdir -p runs
.venv/bin/python scripts/calibrate.py configs/isc-camera6-clock-pilot.json runs/isc-camera.json
.venv/bin/python scripts/infer.py data/local/roadside/VisualCamera6_Run_1023.mp4 \
  runs/isc-camera.json runs/isc-predictions.json --recording isc-run-1023-visual-camera-6 \
  --weights data/local/yolo11n.pt \
  --capture-clock data/local/roadside/VisualCamera6_Run_1023_frame-timing.csv \
  --capture-timezone America/New_York
```

The output records `frame_index`, playback-relative `time` in seconds, and
`capture_time_us` as integer Unix epoch microseconds. Vehicle speed and dwell
use elapsed capture time. The browser still seeks on playback time.
To evaluate verified references using `--join-clock capture`, attach the
exact associated capture timestamp to every reference row. Missing matches
stay uncertain. For cycle peak calculations, provide `time` and the cycle
bounds on a common reference clock. Associate phases and tracks with frames
before scoring them. The provided raw files do not establish that association
on their own.

## Decoded controller data

Using the publisher-recommended J2735 2016 schema, the decoder read **1,455
SPaT messages** across Runs 1023, 108 and 1290. Runs 1023 and 1290 reported
constant states. Run 108 recorded **12 movement-state changes across four
groups**. Its initial and final states do not establish successive onset
boundaries for a complete cycle. See the [raw phase audit](../results/roadside-spat-audit.json).

The [publisher metadata bundle](https://data.transportation.gov/api/views/j58q-ymi4/files/3ccc6fbc-1d9a-4922-8bff-51971c87962b?download=true)
(section 4.7.3, Table 21) maps vehicle signal groups 2, 5, 8 and 11 to
eastbound, northbound, westbound and southbound directions respectively.
The [approach phase export](../results/roadside-108-approach-phases.json)
uses that official mapping. Camera lanes still need to be independently
matched to those directions before supplying the export to inference.

Install the SAE schema wheel and pinned `pycrate==0.7.11` from the
[USDOT decoder repository](https://github.com/usdot-fhwa-stol/j2735decoder/tree/98a13583ebdebe3c6861236ac851b3377d33df22).
The raw PCAP archives remain local.

```sh
.venv/bin/python scripts/decode_roadside_spat.py data/local/roadside/V2XHubSPaT_Run_108.pcap \
  > runs/run-108-spat.json
python3 scripts/map_roadside_phases.py runs/run-108-spat.json \
  data/isc-west-approach-signal-groups.json > runs/run-108-approaches.json
```

A lane's verified phase timeline can set `clock` to `capture` and use
`capture_time_us` for each event instead of playback-relative `time`.
Use exact event times from an independently mapped controller log.

Run 108 Visual Camera 3 decoded all **1,531 frames** without warnings.
The publisher frame clock spans **50.420 seconds**, with 503 of 516
scenario reference rows in range. The reviewed 30-second image has
severe glare and obscured lane detail. The reference table contains a
single passenger-vehicle track plus scripted vulnerable road users.
This run supplies genuine phase transitions for integration tests.
Exact queue counts and a complete cycle benchmark still require
separate footage and reference coverage.

Download only the Run 108 files using
`python3 scripts/download_roadside.py data/local/roadside-108 --run 108`.
