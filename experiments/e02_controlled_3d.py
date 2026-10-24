"""E02: controlled 3-D tracks (Pardiso SPD), mirroring E01.

Tracks (each 5 values x 2 inits, best-of-2 reference, 5x5 cross table):
  cant_z     : cantilever box 40x20x20 (x0 face clamped); end-face patch centre moves
               across the width (z) at mid-height -- a purely 3-D ambiguity.
  cant_y     : same box; patch centre moves along the height (y) at mid-width.
  deck_lane  : bridge deck 48x12x24 (corner bearings on the bottom face); top-face patch
               moves across the deck width (lane offset).
Refinement: cant_z repeated at 2x mesh (80x40x40) with identical physical lengths.
Outputs: results/e02/<track>.json, results/e02/summary.json.
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import consequence as cq  # noqa: E402
import runner  # noqa: E402

OUT = os.path.join(ROOT, "results", "e02")
INITS = ("uniform", "sin5")
NV = 5
SET = runner.settings_dict(rmin=1.5, linear="pardiso_spd")


def cant(scale=1):
    return dict(dim=3, nelx=40, nely=20, nelz=20, volfrac=0.15, scale=scale, domain={"type": "rect"},
                supports=[{"face": "x0", "comp": "xyz"}])


def deck(scale=1):
    return dict(dim=3, nelx=48, nely=12, nelz=24, volfrac=0.15, scale=scale, domain={"type": "rect"},
                supports=[{"face": "y0", "rect": [0, 4, 0, 24], "comp": "xyz"},
                          {"face": "y0", "rect": [44, 48, 0, 24], "comp": "y"}])


def tracks(scale=1):
    vals = np.linspace(0.2, 0.8, NV)
    T = {}
    s = cant(scale)
    T["cant_z"] = (vals, [dict(s, load_cases=[{"patches": [{"face": "x1", "center": [10.0, float(v * 20)],
                                                             "size": [6.0, 6.0], "dir": [0, -1, 0]}]}]) for v in vals])
    T["cant_y"] = (vals, [dict(s, load_cases=[{"patches": [{"face": "x1", "center": [float(v * 20), 10.0],
                                                             "size": [6.0, 6.0], "dir": [0, -1, 0]}]}]) for v in vals])
    d = deck(scale)
    T["deck_lane"] = (vals, [dict(d, load_cases=[{"patches": [{"face": "y1", "center": [24.0, float(v * 24)],
                                                                "size": [12.0, 6.0], "dir": [0, -1, 0]}]}]) for v in vals])
    return T


def run_track(name, vals, specs, threads):
    jobs = [(s, i, SET) for s in specs for i in INITS]
    recs = runner.run_many(jobs, workers=max(1, 19 // threads), threads=threads)
    per = [recs[2 * k:2 * k + 2] for k in range(len(specs))]
    lib = cq.Library(SET)
    refs, noise = [], []
    for k, rr in enumerate(per):
        cs = [r["compliance"] for r in rr]
        b = int(np.argmin(cs))
        xp, _ = runner.load_design(rr[b]["key"])
        lib.add(f"d{k}", xp, k)
        refs.append(cs[b])
        noise.append((max(cs) - min(cs)) / min(cs))
    interps = {f"t{k}": s for k, s in enumerate(specs)}
    C = lib.evaluate([f"d{k}" for k in range(len(specs))], interps)
    ref = np.minimum(np.array(refs), C.min(0))
    L = C / ref[None, :] - 1
    tab = dict(vals=list(map(float, vals)), C=C.tolist(), ref=ref.tolist(), L=L.tolist(), noise=noise,
               accepted=[all(r["accepted"] for r in rr) for rr in per],
               kkt_max=[max(r["kkt"] for r in rr) for rr in per],
               wall_s=[sum(r["wall_s"] for r in rr) for rr in per], counter=lib.counter.as_dict())
    with open(os.path.join(OUT, f"{name}.json"), "w") as fh:
        json.dump(tab, fh, indent=1)
    print(f"{name:14s} max L={L.max():.3f} nominal-row max L={L[NV // 2].max():.3f} noise max={max(noise):.2e} "
          f"accepted {sum(tab['accepted'])}/{len(per)} wall/run~{np.mean(tab['wall_s']) / 2:.0f}s", flush=True)
    return tab


def main():
    os.makedirs(OUT, exist_ok=True)
    summary = {}
    for name, (vals, specs) in tracks(1).items():
        summary[name] = run_track(name, vals, specs, threads=4)
    vals, specs = tracks(2)["cant_z"]
    summary["cant_z_fine"] = run_track("cant_z_fine", vals, specs, threads=10)
    with open(os.path.join(OUT, "summary.json"), "w") as fh:
        json.dump({k: dict(maxL=float(np.max(v["L"])), noise=float(max(v["noise"]))) for k, v in summary.items()}, fh, indent=1)


if __name__ == "__main__":
    main()
