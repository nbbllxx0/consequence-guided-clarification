"""A19: release decisions on sub-sampled controlled tracks, scored at the held-out values (no new run).

Each two-dimensional controlled track (E01) holds nine values of one slot with a complete design x
reading table. For a window of sampled values, spaced every `step` values, the release check uses only
the designs and references of the sampled readings: it releases the design with the smallest worst loss
over the sampled readings when that worst loss is <= tau. The released design is then scored, against the
best-known reference of each reading, at the held-out readings inside the window. A release whose loss
exceeds tau at a held-out reading is a between-sample failure.
Windows: three sampled values with step 1 (no held-out value, a control), step 2 (two held-out values)
and step 4 (six held-out values, the window 0-8), plus five values with step 2 (four held-out values).
Usage: python experiments/a19_subsample_tracks.py
Output: results/a19/subsample.json
"""
import glob
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "a19")
TAU = 0.05
DESIGNS = (("3 values, step 1", 3, 1), ("3 values, step 2", 3, 2), ("3 values, step 4", 3, 4),
           ("5 values, step 2", 5, 2))


def track_loss(d):
    """L[i, j]: loss of the design optimized for value i, evaluated at value j, against the best known."""
    C = np.array(d["C"], float)
    best = np.array(d["best_known"], float)
    return C / best[None, :] - 1.0


def windows(n, k, step):
    span = (k - 1) * step
    return [list(range(a, a + span + 1, step)) for a in range(0, n - span)]


def main():
    res = {}
    agg = {name: dict(windows=0, releases=0, held_out_checked=0, fails=0, max_held_out_loss=0.0)
           for name, _, _ in DESIGNS}
    for f in sorted(glob.glob(os.path.join(ROOT, "results", "e01", "*_*.json"))):
        track = os.path.basename(f)[:-5]
        with open(f) as fh:
            d = json.load(fh)
        L = track_loss(d)
        n = L.shape[0]
        per = {}
        for name, k, step in DESIGNS:
            rows = []
            for w in windows(n, k, step):
                held = [j for j in range(w[0], w[-1] + 1) if j not in w]
                worst = {i: max(L[i, j] for j in w) for i in w}
                c = min(worst, key=lambda i: (worst[i], i))
                rel = bool(worst[c] <= TAU)
                hl = [float(L[c, j]) for j in held]
                rows.append(dict(window=w, commit=c, worst_sampled=float(worst[c]), released=rel,
                                 held_out=held, held_out_loss=hl,
                                 fail=bool(rel and hl and max(hl) > TAU)))
                a = agg[name]
                a["windows"] += 1
                if rel:
                    a["releases"] += 1
                    a["held_out_checked"] += len(held)
                    a["fails"] += int(bool(hl) and max(hl) > TAU)
                    if hl:
                        a["max_held_out_loss"] = max(a["max_held_out_loss"], max(hl))
            per[name] = rows
        res[track] = per
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "subsample.json"), "w") as fh:
        json.dump(dict(tau=TAU, summary=agg, per_track=res), fh, indent=1)
    print(json.dumps(agg, indent=1))
    for track, per in res.items():
        for name, rows in per.items():
            bad = [(r["window"], round(max(r["held_out_loss"]), 3)) for r in rows if r["fail"]]
            if bad:
                print(track, name, bad)


if __name__ == "__main__":
    main()
