"""A25: optimized references at the midpoint readings of A18 (reviewer request, loop v5 round 1).

A18 evaluated the stored designs at readings between sampled values and could only bound the loss from
below. Here every midpoint reading is optimized with the primary settings (two starts, better start kept),
so the loss of each released design at a midpoint is measured against that reading's own computed
reference: l = C_m(d) / min(R_m, U_m) - 1, with R_m the midpoint reference and U_m the best stored design
at m. A release fails between samples if l > tau at any of its midpoint readings.
Usage: python experiments/a25_midpoint_references.py [task ...]
Output: results/a25/midpoint_refs.json
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
import littasks as lt  # noqa: E402
import policies as pl  # noqa: E402
import runner  # noqa: E402
import taskspec  # noqa: E402

TAU = e03.TAU
OUT = os.path.join(ROOT, "results", "a25")


def check_task(tid):
    T, specs, st, lib = a18.library(tid)
    task = T["task"]
    orc0, _ = e03.oracle_from_file(tid)
    zero = pl.Oracle(ref=orc0.ref, C=orc0.C, noise={k: 0.0 for k in orc0.noise})
    interps = task.interpretations()
    nslots = a18.numeric_slots(task)
    releases = {}
    for name, fn in (("CGC", pl.cgc), ("CGC_S", pl.cgc_s)):
        for t in interps:
            o = fn(task, zero, t, TAU)
            if not o.released:
                continue
            surv = [x for x in interps if all(x[s] == t[s] for s in o.asked)]
            releases.setdefault((o.commit, tuple(sorted(pl.ikey(x) for x in surv))), []).append(
                dict(policy=name, truth=pl.ikey(t)))
    mids, per_rel = {}, {}
    for (commit, skeys), cases in releases.items():
        surv = [x for x in interps if pl.ikey(x) in skeys]
        mine = per_rel.setdefault((commit, skeys), set())
        for s in nslots:
            vals = sorted({x[s] for x in surv})
            for a, b in zip(vals, vals[1:]):
                m = a18.midpoint(a, b)
                if m is None:
                    continue
                for x in surv:
                    if x[s] == a:
                        y = dict(x, **{s: m})
                        mids.setdefault(pl.ikey(y), y)
                        mine.add(pl.ikey(y))
    if not mids:
        return dict(task=tid, midpoints=0, releases=[])
    mspecs = {k: T["build"](y) for k, y in mids.items()}
    dim = T["dim"]
    recs = runner.run_many([(mspecs[k], i, st) for k in mspecs for i in e03.INITS],
                           workers=(16 if dim == 2 else 2), threads=(1 if dim == 2 else 4), verbose=False)
    mref, accepted, kkt = {}, {}, {}
    it = iter(recs)
    for k in mspecs:
        rr = [next(it) for _ in e03.INITS]
        b = min(rr, key=lambda r: r["compliance"])
        mref[k] = b["compliance"]
        accepted[k] = all(r["accepted"] for r in rr)
        kkt[k] = b["kkt"]
        xp, act = runner.load_design(b["key"])
        lib.add("mid:" + k, xp, k, act=act, nel=taskspec.build(mspecs[k]).nel)
    names = list(specs) + ["mid:" + k for k in mspecs]
    C = lib.evaluate(names, mspecs)
    feas = np.array([[lib.feasible(d, mspecs[m]) for m in mspecs] for d in names])
    rm = {d: (specs[d] if d in specs else mspecs[d[4:]]).get("rmin", st["rmin"]) for d in names}
    feas &= np.array([[rm[d] >= mspecs[m].get("rmin", st["rmin"]) - 1e-12 for m in mspecs] for d in names])
    Cf = np.where(feas, C, np.inf)
    mkeys = list(mspecs)
    best = np.minimum(np.array([mref[k] for k in mkeys]), Cf.min(0))
    out = []
    for (commit, skeys), cases in releases.items():
        rel_m = [mkeys.index(mk) for mk in sorted(per_rel[(commit, skeys)])]
        i = names.index(commit)
        loss = {mkeys[j]: float(Cf[i, j] / best[j] - 1) for j in rel_m}
        out.append(dict(commit=commit, open=list(skeys), cases=cases, midpoint_loss=loss,
                        max_loss=max(loss.values()) if loss else None,
                        fails=bool(loss and max(loss.values()) > TAU)))
    return dict(task=tid, midpoints=len(mids), midpoint_refs=mref, accepted=accepted, kkt=kkt,
                ref_beaten_by_stored={mkeys[j]: bool(best[j] < mref[mkeys[j]]) for j in range(len(mkeys))},
                releases=out)


def main():
    tids = sys.argv[1:] or [t for t in lt.TASKS if t not in a18.SKIP_TASKS and a18.numeric_slots(lt.TASKS[t]["task"])]
    res = {}
    for tid in tids:
        res[tid] = r = check_task(tid)
        print(tid, "midpoints", r["midpoints"], "release sets", len(r["releases"]),
              "fail", sum(x["fails"] for x in r["releases"]),
              "max", max([x["max_loss"] for x in r["releases"] if x["max_loss"] is not None], default=None), flush=True)
    summ = dict(tasks=len(res), midpoint_readings=sum(r["midpoints"] for r in res.values()),
                release_sets_checked=sum(1 for r in res.values() for x in r["releases"] if x["midpoint_loss"]),
                failing_sets=sum(x["fails"] for r in res.values() for x in r["releases"]),
                cases={p: dict(checked=sum(1 for r in res.values() for x in r["releases"] if x["midpoint_loss"]
                                           for c in x["cases"] if c["policy"] == p),
                               fail=sum(1 for r in res.values() for x in r["releases"] if x["fails"]
                                        for c in x["cases"] if c["policy"] == p)) for p in ("CGC", "CGC_S")},
                max_loss={t: max([x["max_loss"] for x in r["releases"] if x["max_loss"] is not None], default=None)
                          for t, r in res.items()},
                all_accepted=all(all(r.get("accepted", {}).values()) for r in res.values()))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "midpoint_refs.json"), "w") as fh:
        json.dump(dict(tau=TAU, summary=summ, per_task=res), fh, indent=1, default=float)
    print(json.dumps(summ, indent=1, default=float))


if __name__ == "__main__":
    main()
