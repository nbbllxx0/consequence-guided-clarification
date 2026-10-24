"""A21: the two-dimensional large-loss tasks re-encoded with a shared load-introduction region.

Section 6.2 attributes most two-dimensional large losses to loads acting on void material. This replay
adds, to every reading of each such task, the same passive solid region: every element within `DEPTH`
elements of a node that carries load in any reading of the task (nodes below 1e-3 of the largest nodal
load are ignored). Because the region is shared, every design stays feasible at every reading. All
readings are re-optimized (two starts, the primary settings), and the silent default, ask-all, CGC and
CGC-S are replayed at zero allowance.
Usage: python experiments/a21_pad_replay.py [task ...]
Output: results/a21/pad.json
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["LT_VARIANT"] = "consensus"
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import e03_literature_tasks as e03  # noqa: E402
import e08_near_threshold as e08  # noqa: E402
import littasks as lt  # noqa: E402
import policies as pl  # noqa: E402
import taskspec  # noqa: E402

OUT = os.path.join(ROOT, "results", "a21")
TASKS = ["L01", "L04", "L09", "L11", "L13", "L14", "L15", "L22", "L25", "L38", "L41", "L44"]
DEPTH = 2
TAU = e03.TAU


def pad_boxes(specs):
    """Solid boxes (element coordinates) around every loaded node of any reading."""
    boxes = set()
    for sp in specs.values():
        P = taskspec.build(sp)
        f = np.zeros((P.nelx + 1) * (P.nely + 1))
        for lc in P.loads:
            f += np.abs(np.asarray(lc.f)).reshape(-1, 2).sum(1)
        for n in np.flatnonzero(f > 1e-3 * f.max()):
            ix, iy = divmod(int(n), P.nely + 1)
            boxes.add((ix - DEPTH, iy - DEPTH, ix + DEPTH, iy + DEPTH))
    return [list(b) for b in sorted(boxes)]


def run_task(tid):
    T = lt.TASKS[tid]
    task = T["task"]
    st = e03.settings_for(T["dim"])
    base = {pl.ikey(t): T["build"](t) for t in task.interpretations()}
    pad = pad_boxes(base)
    specs = {k: dict(s, solid=(s.get("solid") or []) + pad) for k, s in base.items()}
    orc, info = e08.table(tid, specs, e03.INITS, st)
    zero = pl.Oracle(ref=orc.ref, C=orc.C, noise={k: 0.0 for k in orc.noise})
    interps = task.interpretations()
    nom = pl.ikey(task.nominal)
    res = dict(pad_boxes=len(pad), keys=info["keys"], accepted=all(info["accepted"].values()),
               nominal_max_loss=float(max(zero.loss(nom, k) for k in info["keys"])))
    for name, fn in (("no_ask", pl.no_ask), ("ask_all", pl.ask_all), ("CGC", pl.cgc), ("CGC_S", pl.cgc_s)):
        q = rel = unsafe = bundles = 0
        for t in interps:
            o = fn(task, zero, t, TAU)
            surv = [pl.ikey(x) for x in interps if all(x[s] == t[s] for s in o.asked)]
            w = max(zero.loss(o.commit, k) for k in surv)
            q += len([s for s in o.asked if s not in task.mandatory])
            rel += o.released
            unsafe += bool(o.released and w > TAU)
            bundles += o.optimizations
        res[name] = dict(cases=len(interps), questions=q, released=rel, unsafe=unsafe, bundles=bundles)
    res["silent_default_pool_unsafe"] = res["nominal_max_loss"] > TAU
    res["C"] = info["C"]
    res["ref"] = info["ref"]
    return res


def main():
    tids = sys.argv[1:] or TASKS
    path = os.path.join(OUT, "pad.json")
    res = json.load(open(path)) if os.path.exists(path) else {}
    for tid in tids:
        res[tid] = run_task(tid)
        r = res[tid]
        print(tid, "nominal max loss", round(r["nominal_max_loss"], 4), "CGC q", r["CGC"]["questions"],
              "ask-all q", r["ask_all"]["questions"], flush=True)
        os.makedirs(OUT, exist_ok=True)
        with open(path, "w") as fh:
            json.dump(res, fh, indent=1, default=float)
    summ = dict(tasks=len(res), still_pool_unsafe=[t for t, r in res.items() if r["silent_default_pool_unsafe"]],
                nominal_max_loss={t: r["nominal_max_loss"] for t, r in res.items()},
                questions={p: sum(r[p]["questions"] for r in res.values()) for p in ("ask_all", "CGC", "CGC_S")})
    print(json.dumps(summ, indent=1, default=float))


if __name__ == "__main__":
    main()
