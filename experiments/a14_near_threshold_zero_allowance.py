"""A14: E08 near-threshold checks re-scored at zero allowance (the primary setting).

Tasks: the four original E08 tasks and the five further low-margin tasks (L25, L11, L20, L21, L36).

E08 reports the minimax loss B and replays CGC / CGC_S with the two-start spread subtracted (allowance). This
script reuses the saved E08 tables (results/e08/<tid>.json: C, ref, noise per variant), so no finite element
work is repeated, and recomputes B, the default-design worst loss and both replays with zero allowance. A decision is
stable if every case keeps its question count and release flag relative to the base variant.
Output: results/a14/near_threshold_a0.json
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import littasks as lt  # noqa: E402
import policies as pl  # noqa: E402

TAU = 0.05
OUT = os.path.join(ROOT, "results", "a14")


def main():
    res = {}
    for tid in ("L18", "L24", "L37", "L16", "L25", "L11", "L20", "L21", "L36"):
        with open(os.path.join(ROOT, "results", "e08", f"{tid}.json")) as fh:
            e08 = json.load(fh)
        task = lt.TASKS[tid]["task"]
        nom = pl.ikey(task.nominal)
        rows = {}
        for var in ("base", "polished", "refined_x2"):
            v = e08[var]
            keys = v["keys"]
            C = np.array(v["C"], float)
            ref = np.array([v["ref"][k] for k in keys])
            L = C / ref[None, :] - 1
            orc = pl.Oracle(ref=v["ref"], C={(d, t): float(C[i, j]) for i, d in enumerate(keys)
                                             for j, t in enumerate(keys)}, noise={k: 0.0 for k in keys})
            rep = {}
            for name, fn in (("CGC", pl.cgc), ("CGC_S", pl.cgc_s)):
                rep[name] = [dict(truth=pl.ikey(t), n_asked=len(o.asked), released=o.released)
                             for t in task.interpretations() for o in [fn(task, orc, t, TAU)]]
            rows[var] = dict(B=float(np.min(np.max(L, 1))), B_nominal=float(np.max(L[keys.index(nom)])),
                             B_spread=v["B"], replay=rep)
        for var in ("polished", "refined_x2"):
            for p in ("CGC", "CGC_S"):
                a, b = rows["base"]["replay"][p], rows[var]["replay"][p]
                rows[var][f"stable_{p}"] = all(x["n_asked"] == y["n_asked"] and x["released"] == y["released"]
                                               for x, y in zip(a, b))
        res[tid] = rows
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "near_threshold_a0.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    for tid, rows in res.items():
        print(tid, {v: dict(B=round(r["B"], 4), B_spread=round(r["B_spread"], 4),
                            **{k: r[k] for k in r if k.startswith("stable")}) for v, r in rows.items()})


if __name__ == "__main__":
    main()
