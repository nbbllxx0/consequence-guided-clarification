"""A18: release check between sampled values (no new optimization).

For every zero-allowance release of CGC and CGC-S at tau = 0.05, and for every numeric slot that still
varies among the release's open readings, build the readings at the midpoints of adjacent sampled values
(integer midpoints for slots counted in elements). Every stored design of the task (the selected start
of each reading's bundle) is evaluated at each midpoint reading. With U_m = min over feasible library
designs of C_m, Eq. (7) gives the certified lower bound l_lo(d, m) = C_m(d) / U_m - 1 on the loss of
the released design d against the midpoint optimum, so l_lo > tau proves that the release fails at the
midpoint reading. Only finite-element solves are run.

Excluded slots: those that change the design domain (arm, ar), volume fraction (mandatory), and the
L22 element positions (adjacent integers, no midpoint).
Usage: python experiments/a18_midpoint_check.py [task ...]
Output: results/a18/midpoint.json
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["LT_VARIANT"] = "consensus"
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import consequence as cq  # noqa: E402
import e03_literature_tasks as e03  # noqa: E402
import littasks as lt  # noqa: E402
import policies as pl  # noqa: E402
import runner  # noqa: E402
import taskspec  # noqa: E402

TAU = e03.TAU
OUT = os.path.join(ROOT, "results", "a18")
SKIP_SLOTS = {"arm", "ar", "volfrac"}
SKIP_TASKS = {"L22"}


def numeric_slots(task):
    out = []
    for s, vals in task.slots.items():
        if s in SKIP_SLOTS or len(vals) < 2:
            continue
        if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals):
            out.append(s)
    return out


def midpoint(a, b):
    if isinstance(a, int) and isinstance(b, int):
        return (a + b) // 2 if abs(b - a) >= 2 else None
    return round((a + b) / 2, 6)


def library(tid):
    """Stored designs of every reading (selected start), loaded from the optimization cache."""
    T = lt.TASKS[tid]
    specs, st, _ = e03.jobs_for(tid)
    lib = cq.Library(st)
    for k, sp in specs.items():
        recs = [runner.load(runner.job_key(sp, i, st)) for i in e03.INITS]
        if any(r is None for r in recs):
            raise RuntimeError(f"{tid} {k}: design not cached; refusing to optimize")
        r = min(recs, key=lambda r: r["compliance"])
        xp, act = runner.load_design(r["key"])
        lib.add(k, xp, k, act=act, nel=taskspec.build(sp).nel)
    return T, specs, st, lib


def check_task(tid):
    T, specs, st, lib = library(tid)
    task = T["task"]
    orc0, _ = e03.oracle_from_file(tid)
    zero = pl.Oracle(ref=orc0.ref, C=orc0.C, noise={k: 0.0 for k in orc0.noise})
    interps = task.interpretations()
    nslots = numeric_slots(task)
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
                m = midpoint(a, b)
                if m is None:
                    continue
                for x in surv:
                    if x[s] != a:
                        continue
                    y = dict(x, **{s: m})
                    mids.setdefault(pl.ikey(y), y)
                    mine.add(pl.ikey(y))
    if not mids:
        return dict(task=tid, numeric_slots=nslots, midpoints=0, releases=[])
    mspecs = {k: T["build"](y) for k, y in mids.items()}
    names = list(specs)
    C = lib.evaluate(names, mspecs)
    feas = np.array([[lib.feasible(d, mspecs[m]) for m in mspecs] for d in names])
    rm = {d: specs[d].get("rmin", st["rmin"]) for d in names}
    feas &= np.array([[rm[d] >= mspecs[m].get("rmin", st["rmin"]) - 1e-12 for m in mspecs] for d in names])
    Cf = np.where(feas, C, np.inf)
    mkeys = list(mspecs)
    U = Cf.min(0)
    out = []
    for (commit, skeys), cases in releases.items():
        rel_m = [mkeys.index(mk) for mk in sorted(per_rel[(commit, skeys)])]
        i = names.index(commit)
        llo = {mkeys[j]: float(Cf[i, j] / U[j] - 1) if np.isfinite(U[j]) else None for j in rel_m}
        vals = [v for v in llo.values() if v is not None]
        out.append(dict(commit=commit, open=list(skeys), cases=cases, midpoints=llo,
                        max_lower_bound=max(vals) if vals else None,
                        proven_fail=bool(vals and max(vals) > TAU)))
    return dict(task=tid, numeric_slots=nslots, midpoints=len(mids), releases=out,
                counter=lib.counter.as_dict())


def main():
    tids = [a for a in sys.argv[1:]] or [t for t in lt.TASKS if t not in SKIP_TASKS
                                         and numeric_slots(lt.TASKS[t]["task"])]
    res = {}
    for tid in tids:
        res[tid] = check_task(tid)
        r = res[tid]
        nf = sum(x["proven_fail"] for x in r["releases"])
        print(tid, "midpoints", r["midpoints"], "releases", len(r["releases"]), "proven fail", nf, flush=True)
    summ = dict(tasks=len(res),
                release_sets=sum(len(r["releases"]) for r in res.values()),
                release_sets_checked=sum(1 for r in res.values() for x in r["releases"] if x["midpoints"]),
                proven_fail_sets=sum(x["proven_fail"] for r in res.values() for x in r["releases"]),
                cases={p: dict(checked=sum(1 for r in res.values() for x in r["releases"] if x["midpoints"]
                                           for c in x["cases"] if c["policy"] == p),
                               proven_fail=sum(1 for r in res.values() for x in r["releases"] if x["proven_fail"]
                                               for c in x["cases"] if c["policy"] == p))
                       for p in ("CGC", "CGC_S")},
                max_lower_bound={t: max([x["max_lower_bound"] for x in r["releases"]
                                         if x["max_lower_bound"] is not None], default=None)
                                 for t, r in res.items()})
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "midpoint.json"), "w") as fh:
        json.dump(dict(tau=TAU, summary=summ, per_task=res), fh, indent=1, default=float)
    print(json.dumps(summ, indent=1, default=float))


if __name__ == "__main__":
    main()
