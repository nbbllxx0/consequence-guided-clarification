"""A28: silent-default infeasibility repaired (reviewer request, loop v5 round 1).

In L23, L29, L37 and L45 the default design is infeasible at some reading because that reading's passive
solid elements are not solid in it. Here the missing elements are set solid in the default design (the
volume then exceeds the bound by the added elements, reported), and the repaired design is evaluated at
that reading against the reading's reference. A repaired loss within tau means the failure is the
mapping convention; a loss above tau means the mechanics also fails.
Usage: python experiments/a28_passive_repair.py
Output: results/a28/passive_repair.json
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["LT_VARIANT"] = "consensus"
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import a18_midpoint_check as a18  # noqa: E402
import e03_literature_tasks as e03  # noqa: E402
import policies as pl  # noqa: E402
import simp  # noqa: E402
import taskspec  # noqa: E402

TASKS = ("L23", "L29", "L37", "L45")
OUT = os.path.join(ROOT, "results", "a28")


def main():
    res = {}
    for tid in TASKS:
        T, specs, st, lib = a18.library(tid)
        task = T["task"]
        orc0, _ = e03.oracle_from_file(tid)
        rows = []
        for t in task.interpretations():
            mand = pl.ikey(dict(task.nominal, **{s: t[s] for s in task.mandatory}))
            tk = pl.ikey(t)
            if np.isfinite(orc0.C[(mand, tk)]):
                continue
            sp = specs[tk]
            S = simp.SIMP(taskspec.build(sp), simp.Settings(**dict(st, **{k: sp[k] for k in ("rmin",) if k in sp})))
            x = lib._on(mand, S)
            solid = S.solid[S.act]
            added = int(np.sum(solid & (x < 0.99)))
            x = np.where(solid, 1.0, x)
            c, _ = S.evaluate(x, S.p.loads)
            rows.append(dict(nominal=mand, reading=tk, added_solid=added, n_active=int(S.act.size),
                             volume_excess=float(x.mean() / sp["volfrac"] - 1),
                             repaired_loss=float(c / orc0.ref[tk] - 1)))
        res[tid] = rows
        print(tid, json.dumps(rows), flush=True)
    res["adjusted_count"] = adjusted_count(res)
    print(json.dumps(res["adjusted_count"], indent=1))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "passive_repair.json"), "w") as fh:
        json.dump(res, fh, indent=1)


SINGLE_NODE = {"L25": ("sup", "node"), "L33": ("load", "node"), "L34": ("load", "node")}


def nominal_worst(tid, drop=None):
    """Worst loss of the mandatory-answered default design over each case's open readings (silent default)."""
    import littasks as lt
    task = lt.TASKS[tid]["task"]
    orc0, _ = e03.oracle_from_file(tid)
    interps = [t for t in task.interpretations() if not (drop and t[drop[0]] == drop[1])]
    nominal = dict(task.nominal)
    if drop and nominal[drop[0]] == drop[1]:             # the default reading itself is dropped
        nominal[drop[0]] = next(v for v in task.slots[drop[0]] if v != drop[1])
    w = 0.0
    for t in interps:
        mand = pl.ikey(dict(nominal, **{s: t[s] for s in task.mandatory}))
        surv = [pl.ikey(x) for x in interps if all(x[s] == t[s] for s in task.mandatory)]
        w = max(w, max(orc0.C[(mand, k)] / orc0.ref[k] - 1 for k in surv))
    return w


def adjusted_count(rep):
    """Silent-default failures after three reconstruction adjustments: a solid region at each load (A21,
    2-D large-loss tasks), single-node readings dropped, and missing passive elements filled (this run)."""
    import littasks as lt
    tau = e03.TAU
    fail = sorted(t for t in lt.TASKS if nominal_worst(t) > tau)
    with open(os.path.join(ROOT, "results", "a21", "pad.json")) as fh:
        pad = json.load(fh)
    fixed_pad = sorted(t for t, v in pad.items() if v["nominal_max_loss"] <= tau)
    fixed_node = sorted(t for t, d in SINGLE_NODE.items() if nominal_worst(t, d) <= tau)
    fixed_passive = []
    for tid in TASKS:
        task = lt.TASKS[tid]["task"]
        orc0, _ = e03.oracle_from_file(tid)
        finite_ok = True
        for t in task.interpretations():
            mand = pl.ikey(dict(task.nominal, **{s: t[s] for s in task.mandatory}))
            surv = [pl.ikey(x) for x in task.interpretations() if all(x[s] == t[s] for s in task.mandatory)]
            for k in surv:
                c = orc0.C[(mand, k)]
                if np.isfinite(c) and c / orc0.ref[k] - 1 > tau:
                    finite_ok = False
        if finite_ok and all(r["repaired_loss"] <= tau for r in rep[tid]):
            fixed_passive.append(tid)
    remaining = [t for t in fail if t not in set(fixed_pad) | set(fixed_node) | set(fixed_passive)]
    return dict(failing_as_encoded=fail, n_failing=len(fail), fixed_by_pad=fixed_pad, fixed_by_dropping_single_node=fixed_node,
                fixed_by_passive_repair=fixed_passive, remaining=remaining, n_remaining=len(remaining))


if __name__ == "__main__":
    main()
