# Traffic Signal Queue Estimator

This project investigates whether lane geometry and temporal tracking improve
fixed-camera queue counts at unseen signalised intersections, especially under
occlusion.

## Current evidence

The FHWA data pilot is in progress. The project currently includes a download
manifest, archive checks, lane geometry, and evaluation foundations.
See the [data audit](docs/data-pilot.md) for verified archive contents and open
alignment checks. There are no real-world benchmark scores yet.

## Reproduce the current checks

```sh
python3 scripts/audit_sources.py --download > pilot-inventory.json
python3 -m unittest discover -s tests -v
```

The archive command stores downloads under `data/local/` by default and emits
SHA-256 hashes and member lists. Python 3.9 or later is sufficient for these checks.

## Review workspace

Run `python3 -m http.server --bind 127.0.0.1 --directory web 8000` and open
`http://127.0.0.1:8000`. The workspace starts with an illustrative count
timeline. Load a browser-playable local video, then the matching prediction
JSON. Use the chart or keyboard-accessible range control to seek and export
the imported rows in CSV or JSON.

## Local detector prototype

Install OpenCV and Ultralytics in a virtual environment. Supply a compatible
pretrained detection checkpoint under its own usage terms. The inference CLI
runs separately from the review workspace.

```sh
python3 scripts/infer.py recording.mp4 camera.json predictions.json \
  --recording collection-camera-window --weights local-model.pt --method temporal
python3 scripts/evaluate.py audited-reference.json predictions.json --split test
```

The camera configuration requires a pixel-to-ground homography and one
polygon, stop point, upstream vector and visible distance per lane. Include
the corresponding pixel-space lane fields for the tracking baseline. The
temporal occlusion indicator currently uses a heavy-vehicle heuristic and
the confidence values are provisional. Benchmark joins expect explicit
recording IDs, lane IDs, common timestamps, and independently audited labels.
