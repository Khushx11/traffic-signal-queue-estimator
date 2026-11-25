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

## Results and model choice

Fine-tuning used 240 images across eight training videos and 28 validation
images across seven different videos. The TrafficCAM test contains 204
images across 51 other videos, including one byte-identical pair inside the
test split. No exact images were shared across any splits. Training ran for
five epochs on the Apple M4 CPU.

- **TrafficCAM original**. Recall improved from 22.6% to 46.3%, small-object
  recall from 15.4% to 41.1%, and count MAE from 17.24 to 9.91 vehicles per
  frame. Precision fell from 76.6% to 45.7%. The fine-tuned model also
  improved recall and count MAE under all four simulated degradations.
- **MIO-TCD original**. Recall rose from 49.4% to 58.9%, while precision fell
  from 79.7% to 41.6% and count MAE rose from 1.30 to 2.20. Across simulated
  degradations the fine-tuned model improved recall in every tested case,
  while count MAE worsened in three of four cases.
- **Peachtree transfer diagnostic**. On the same 120 cropped frames, the
  baseline had tracked vehicles in 176 of 240 lane-timestamps and abstained
  on all 240. Fine-tuning produced tracks in all 240 and returned six count
  estimates, 82 lower bounds and 152 uncertain outputs. This clip still
  lacks an independent lane-queue reference.

Keep the pretrained checkpoint as the general default. The fine-tuned model
is available locally as `runs/trafficcam-final/weights/best.pt` and can be
passed explicitly to the CLI for diagnostics. It has a single vehicle class,
so class-dependent heavy-vehicle handling is unavailable with that checkpoint.

- [Raw aggregate test metrics](../results/detector-robustness.json)
- [Training and validation history](../results/detector-training.json)
- [Peachtree transfer diagnostics](../results/peachtree-detector-transfer.json)
