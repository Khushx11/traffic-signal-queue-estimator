# Real-world validation and dataset selection

Use the app for offline intersection review and testing proposed policies.
Leave actuation to the road authority's controller. For policy evaluation,
compare fixed-time, vehicle-actuated and adaptive policies on identical
vehicle and pedestrian arrivals. Measure per-approach queue length, stops,
vehicle delay, pedestrian delay and the worst wait as well as averages.
Test detector outages and use site-approved clearance and signal plans.

- [FHWA adaptive signal validation guidance](https://ops.fhwa.dot.gov/publications/fhwahop13031/appe.htm)
- [South Australian traffic signal design specification](https://dit.sa.gov.au/__data/assets/pdf_file/0007/1423483/RD-EL-D2-TRAFFIC-SIGNAL-DESIGN.pdf)
- [SUMO vehicle and pedestrian controller example](https://sumo.dlr.de/daily/userdoc/Tutorials/TraCIPedCrossing.html)

## Model roles

The default COCO detector and ByteTrack form the general baseline.
The TrafficCAM and mixed TrafficCAM plus MIO-TCD checkpoints specialise in
fixed-camera vehicle detection. The DOTA-pretrained oriented detector is a
candidate for elevated views. Simultaneous runs retain each checkpoint's
evidence and report uncertainty when queue votes disagree. Agreement does
not calibrate confidence or account for correlated misses. Pedestrian calls
in the priority replay remain manually supplied.

## Dataset inventory

- [TrafficCAM](https://math-ml-x.github.io/TrafficCAM/) supplies labelled
  frames from fixed intersection videos. The project trains and tests on
  separate video IDs.
- [MIO-TCD](https://tcd.miovision.com/challenge/dataset.html) adds labelled
  North American traffic-camera images. The mixed experiment reserves the
  original 80-image test slice and adds distinct images to training. Camera
  identities are unavailable for this split. The publisher lists CC BY-NC-SA 4.0.
- [US DOT Intersection Safety Challenge](https://data.transportation.gov/Roadways-and-Bridges/Intersection-Safety-Challenge-Stage-1B-Validation-/j58q-ymi4)
  supplies actual signal-camera recordings, scripted tracks and SPaT. Used
  for integration diagnostics. It does not supply a complete queue benchmark.
- [FHWA NGSIM](https://data.transportation.gov/Automobiles/Next-Generation-Simulation-NGSIM-Vehicle-Trajector/8ect-6jqj)
  supplies footage and trajectories used for Peachtree diagnostics.
- [TUMTraf Intersection](https://innovation-mobility.com/en/project-providentia/a9-dataset/)
  is a candidate for calibrated gantry imagery and LiDAR-based occlusion labels.
  Access requires publisher registration.
- [CityFlowV2](https://www.aicitychallenge.org/2022-data-and-evaluation/)
  is a candidate for multi-camera tracking and transfer. Check current
  availability and release-specific terms before use.
- [UA-DETRAC](https://sites.google.com/view/daweidu/projects/ua-detrac)
  is a candidate for fixed-camera vehicle tracking under night, rain and
  occlusion. The original archive was unavailable in the earlier pilot.
- [Aalborg MTID](https://vap.aau.dk/mtid/) is a candidate for pole-view and
  synchronised overhead checks. The publisher-linked Kaggle download
  returned HTTP 404 in the earlier pilot.
- [TRANCOS](https://gram.web.uah.es/data/datasets/trancos/index.html)
  is a candidate for crowded vehicle counting. The publisher download led to
  sign-in in the earlier pilot.
- [BDD100K](https://openaccess.thecvf.com/content_CVPR_2020/papers/Yu_BDD100K_A_Diverse_Driving_Dataset_for_Heterogeneous_Multitask_Learning_CVPR_2020_paper.pdf)
  has moving-camera pedestrian and vehicle annotations. It can support a
  separate transfer study. The perspective differs from fixed signal cameras.

Only the first four sources were used locally in this project. The others
are documented leads. Their images and labels were not included in this run.

## Policy stress test

Reproduce with `node scripts/compare_priority.js`. This 900-second seeded
queue simulation uses identical arrivals for both policies. It models
exclusive phases, one vehicle departing per two seconds of green and
calls queued until a walk interval. The fixed baseline retains fixed
vehicle order and timing while still serving pending pedestrian calls.

On the asymmetric scenario, adaptive service reduced vehicle queue-seconds
from 80,296 to 56,575. Pedestrian queue-seconds rose from 680 to 1,134,
and the worst observed pedestrian wait rose from 82 to 133 seconds. The
balanced case also increased pedestrian delay. This exposes a fairness
trade-off in the current policy. There is no calibrated network, turning
conflict matrix or field operational claim. Compare against a calibrated
SUMO model before drawing practical timing conclusions.

- [Seeded policy results](../results/priority-policy-simulation.json)

A third simulated variant prioritises waiting pedestrians once a
45-second trigger is reached and the current vehicle phase has finished
its all-red separation. The trigger does not interrupt an active phase.
This variant is evaluated in the seeded comparison script. It is separate
from the browser's one-snapshot priority preview.
