"""Matplotlib styling and figure builders.

All figures are saved at 300 dpi to ``results/`` and the underlying numbers to
``results/data/`` as CSV, so every plot in the report is fully reproducible.
"""
import os
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from . import config as cfg

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, "results")
DATA = os.path.join(RESULTS, "data")
os.makedirs(DATA, exist_ok=True)

plt.rcParams.update({
    "figure.figsize": (7.0, 4.6),
    "font.size": 11,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "lines.linewidth": 2.0,
    "lines.markersize": 5,
})

C = {"air": "#1f77b4", "egr": "#d62728", "oxy": "#2ca02c",
     "N2": "#1f77b4", "CO2": "#d62728", "H2O": "#2ca02c"}


def save_csv(name, columns):
    """columns: dict of header -> 1D array (equal length)."""
    keys = list(columns)
    rows = zip(*[np.asarray(columns[k]) for k in keys])
    with open(os.path.join(DATA, name), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(keys)
        w.writerows(rows)


def _fig(path):
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS, path), dpi=cfg.DPI, bbox_inches="tight")
    plt.close()
    print("  wrote results/%s" % path)
