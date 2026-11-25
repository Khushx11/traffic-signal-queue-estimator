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
