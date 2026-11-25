# Vehicle detector robustness

The original Peachtree pilot struggled to detect enough stopped vehicles to
establish a continuous queue. This experiment tests whether supervised
fine-tuning improves the detection stage.

## Sources and split

- [TrafficCAM publisher download and official splits](https://github.com/Math-ML-X/TrafficCAM/blob/main/TrafficCAM-download.md).
  Fully labelled Indian fixed-camera videos. Build bounding boxes from vehicle
  polygons. Use the officially assigned video IDs, sample 30 available
  annotated images per training video and four per validation/test video.
  The converter rejects video ID overlap. These identifiers do not establish
  that all physical cameras and intersections are distinct.
- [MIO-TCD publisher data and terms](https://tcd.miovision.com/challenge/dataset.html).
  An independent 80-image audit from publisher-labelled localization training
  frames in archive order. The experiment uses these images solely for
  testing. The publisher's challenge test is a separate split. The dataset
  is CC BY-NC-SA 4.0.
- [UA-DETRAC benchmark](https://sites.google.com/view/daweidu/projects/ua-detrac)
  and [TRANCOS](https://gram.web.uah.es/data/datasets/trancos/index.html)
  were reviewed as candidates. UA-DETRAC's old download host did not provide a
  verified archive during this run. TRANCOS's publisher link redirected to
  Microsoft sign-in. Neither contributed to training or evaluation.

Images and fitted checkpoints are local experiment artifacts. Use the source
links to review dataset terms and retrieve the archives.

## Reproduction

Save the publisher's TrafficCAM fully annotated and official split archives
as `data/local/trafficcam.zip` and `data/local/trafficcam-splits.zip`.
Save the first 100 MiB of MIO-TCD's localization TAR and the full localization
toolkit as shown. Install the pinned video dependencies first.

```sh
curl -fL --range 0-104857599 --max-filesize 105000000 \
  https://tcd.miovision.com/static/dataset/MIO-TCD-Localization.tar \
  -o data/local/mio-head.tar
curl -fL https://tcd.miovision.com/static/dataset/MIO-TCD-Localization-Code.tar \
  -o data/local/mio-code.tar

.venv/bin/python scripts/prepare_detection.py data/local/robustness-final \
  --trafficcam data/local/trafficcam.zip data/local/trafficcam-splits.zip \
  --mio data/local/mio-head.tar data/local/mio-code.tar --train-per-video 30
.venv/bin/python scripts/finetune_detector.py data/local/yolo11n.pt \
  data/local/robustness-final/dataset.yaml runs/trafficcam-final --epochs 5
.venv/bin/python scripts/compare_detectors.py data/local/robustness-final \
  runs/detector-comparison-final.json data/local/yolo11n.pt \
  runs/trafficcam-final/weights/best.pt
```

Inference uses 480-pixel sizing and a fixed 0.25 confidence cutoff for both
checkpoints. Boxes are matched greedily by confidence using IoU ≥ 0.5. Small
objects have a box area below 32² pixels after scaling the longer image edge
to 480 pixels. Compare precision, recall, small-object recall and per-frame
vehicle-count MAE on original images and in separate synthetic conditions.
The corruptions are Gaussian blur, darkening to 35% intensity, 3× linear
resolution degradation and a solid occlusion strip. They do not establish
performance in natural night scenes, rain, glare or real occlusion.
These are frame-level vehicle detections. Queue membership and signal timing
require their own independent reference labels.
