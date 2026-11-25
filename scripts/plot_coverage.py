"""Plot the count error versus estimate coverage for comparable benchmark runs."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("inputs", type=Path, nargs="+")
    args = parser.parse_args()
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
    for path in args.inputs:
        source = json.loads(path.read_text())
        methods = {
            name: result["coverage_curve"]
            for name, result in source.get("methods", {}).items()
        } or {path.stem: source["error_vs_coverage"]}
        for name, points in methods.items():
            eligible = sorted({(point["coverage"], point["mae"]) for point in points
                               if point["coverage"] is not None and point["mae"] is not None})
            if eligible:
                ax.plot(*zip(*eligible), marker="o", label=name.replace("_", " "))
    ax.set(xlabel="Eligible timestamps receiving a count estimate",
           ylabel="Mean absolute error (vehicles per lane)", xlim=(0, 1.04))
    ax.set_title("Queue count error versus coverage")
    ax.grid(alpha=0.25)
    if ax.lines:
        ax.legend()
    fig.savefig(args.output, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
