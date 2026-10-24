"""E10: a controlled three-slot task (Codex round-3 'should': cases with at least three varying slots).

Cantilever 120x60 (E01 geometry: clamped left edge, passive solid strip at the loaded right edge, vf 0.4,
rmin 2.4). Slots: load centre c in {0.35, 0.5, 0.65} of the edge, patch width w in {4, 8, 12} elements,
load angle a in {-90, -70} degrees from the x axis. 18 readings x 2 starts; full table; replay with
zero allowance of silent default, ask-all, CGC (minimax order), CGC-S, and the fixed-order baseline in
two orders (declared order c, w, a and the adverse order w, a, c).
Output: results/e10/three_slot.json
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import e03_literature_tasks as e03  # noqa: E402
import e08_near_threshold as e08  # noqa: E402
import littasks as lt  # noqa: E402
import policies as pl  # noqa: E402

OUT = os.path.join(ROOT, "results", "e10")
TAU = 0.05


def spec(t):
    a = np.deg2rad(t["a"])
    s = lt._cant2(120, 60, 0.4, t["c"] * 60, float(t["w"]), direction=(float(np.cos(a)), float(np.sin(a))))
    s["solid"] = [[118, 0, 120, 60]]
    s["rmin"] = 2.4
    return s


def main():
    task = pl.Task("E10", {"c": [0.35, 0.5, 0.65], "w": [4, 8, 12], "a": [-90, -70]}, {"c": 0.5, "w": 8, "a": -90})
    specs = {pl.ikey(t): spec(t) for t in task.interpretations()}
    orc, info = e08.table(None, specs, e03.INITS, e03.settings_for(2), nominal=pl.ikey(task.nominal))
    zero = pl.Oracle(ref=orc.ref, C=orc.C, noise={k: 0.0 for k in orc.noise})
    pols = {"no_ask": pl.no_ask, "ask_all": pl.ask_all, "CGC": pl.cgc, "CGC_S": pl.cgc_s,
            "fixed_c_w_a": lambda T, o, t, tau: pl.cgc_fixed(T, o, t, tau, order=["c", "w", "a"]),
            "fixed_w_a_c": lambda T, o, t, tau: pl.cgc_fixed(T, o, t, tau, order=["w", "a", "c"])}
    interps = task.interpretations()
    res = {}
    for name, fn in pols.items():
        rows = []
        for truth in interps:
            o = fn(task, zero, truth, TAU)
            ans = {s: truth[s] for s in o.asked}
            surv = [pl.ikey(t) for t in interps if all(t[s] == v for s, v in ans.items())]
            worst = max(zero.loss(o.commit, k) for k in surv)
            rows.append(dict(truth=pl.ikey(truth), asked=o.asked, released=o.released,
                             unsafe=bool(o.released and worst > TAU), bundles=o.optimizations))
        res[name] = dict(questions=float(np.mean([len(r["asked"]) for r in rows])),
                         releases=int(sum(r["released"] for r in rows)), unsafe=int(sum(r["unsafe"] for r in rows)),
                         bundles=float(np.mean([r["bundles"] for r in rows])),
                         asked_slots={s: int(sum(s in r["asked"] for r in rows)) for s in task.slots})
    L = np.array(info["C"]) / np.array([info["ref"][k] for k in info["keys"]])[None, :] - 1
    out = dict(readings=len(interps), B=info["B"], B_nominal=info["B_nominal"], accepted=all(info["accepted"].values()),
               noise_max=float(max(info["noise"].values())), max_loss=float(np.nanmax(L[np.isfinite(L)])),
               policies=res)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "three_slot.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
