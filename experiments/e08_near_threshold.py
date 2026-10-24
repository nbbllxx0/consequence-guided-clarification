"""E08: decision stability of near-threshold literature tasks (Codex round-3 blockers).

Tasks: L18, L24, L37 (full-table minimax loss within about 1% of tau = 5%), plus L16 as a harmless control.
  (a) reference polishing: four extra starts per reading (smooth random fields 'rnd10s1'..'rnd10s4');
      references = best of all six starts; cross table, CGC and CGC_S replayed on the enlarged pool.
  (b) mesh refinement: every reading at scale 2 (filter radius and patch sizes scaled; two starts),
      own cross table and replay.
Reported per task and variant: minimax loss B of the full table, nominal worst loss, and the CGC / CGC_S
questions and releases per hidden truth. A decision is stable if the question counts and release flags
match the base E03 replay.
Usage: python experiments/e08_near_threshold.py [task ...]   (default: the four tasks above; the summary is merged)
Output: results/e08/<tid>.json, results/e08/summary.json
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import consequence as cq  # noqa: E402
import e03_literature_tasks as e03  # noqa: E402
import littasks as lt  # noqa: E402
import policies as pl  # noqa: E402
import runner  # noqa: E402
import taskspec  # noqa: E402

OUT = os.path.join(ROOT, "results", "e08")
TASKS = ["L18", "L24", "L37", "L16"]
EXTRA = ("rnd10s1", "rnd10s2", "rnd10s3", "rnd10s4")


def settings(dim, refined):
    st = e03.settings_for(dim)
    if dim == 3:
        st = dict(st, linear="cudss")
    return st


def specs_for(tid, scale):
    T = lt.TASKS[tid]
    out = {}
    for t in lt.interpretations(tid):
        s = T["build"](t)
        if scale != 1:
            s = dict(s, scale=scale, rmin=s.get("rmin", 1.5) * scale)
        out[pl.ikey(t)] = s
    return out


def table(tid, specs, inits, st, nominal=None):
    jobs = [(specs[k], i, st) for k in specs for i in inits]
    dim = specs[next(iter(specs))].get("dim", 2)
    runner.run_many(jobs, workers=(16 if dim == 2 else 2), threads=(1 if dim == 2 else 4), verbose=False)
    lib = cq.Library(st)
    ref, noise, accepted = {}, {}, {}
    for k, s in specs.items():
        recs = [runner.load(runner.job_key(s, i, st)) for i in inits]
        cs = [r["compliance"] for r in recs]
        b = int(np.argmin(cs))
        xp, act = runner.load_design(recs[b]["key"])
        lib.add(k, xp, k, act=act, nel=taskspec.build(s).nel)
        ref[k], noise[k] = min(cs), (max(cs) - min(cs)) / min(cs)
        accepted[k] = all(r["accepted"] for r in recs)
    keys = list(specs)
    C = lib.evaluate(keys, specs)
    feas = np.array([[lib.feasible(d, specs[t]) for t in keys] for d in keys])
    rm = {k: specs[k].get("rmin", st["rmin"]) for k in keys}
    feas &= np.array([[rm[d] >= rm[t] - 1e-12 for t in keys] for d in keys])
    Cf = np.where(feas, C, np.inf)
    best = np.minimum(np.array([ref[k] for k in keys]), Cf.min(0))
    refb = {k: float(best[j]) for j, k in enumerate(keys)}
    Cd = {(d, t): float(Cf[i, j]) for i, d in enumerate(keys) for j, t in enumerate(keys)}
    orc = pl.Oracle(ref=refb, C=Cd, noise=noise)
    L = Cf / best[None, :] - 1 - np.array([noise[k] for k in keys])[None, :]
    nom = keys.index(nominal if nominal is not None else pl.ikey(lt.TASKS[tid]["task"].nominal))
    return orc, dict(keys=keys, ref=refb, noise=noise, accepted=accepted, B=float(np.min(np.max(L, 1))),
                     B_nominal=float(np.max(L[nom])), C=Cf.tolist())


def replay(tid, orc):
    task = lt.TASKS[tid]["task"]
    out = {}
    for name in ("CGC", "CGC_S"):
        fn = pl.POLICIES[name]
        rows = []
        for truth in task.interpretations():
            o = fn(task, orc, truth, e03.TAU)
            rows.append(dict(truth=pl.ikey(truth), n_asked=len(o.asked), released=o.released, commit=o.commit,
                             bundles=o.optimizations))
        out[name] = rows
    return out


def main():
    tids = sys.argv[1:] or TASKS
    sp = os.path.join(OUT, "summary.json")
    summ = json.load(open(sp)) if os.path.exists(sp) else {}
    for tid in tids:
        dim = lt.TASKS[tid]["dim"]
        st = e03.settings_for(dim)
        base_specs = specs_for(tid, 1)
        res = {}
        orc, info = table(tid, base_specs, e03.INITS, st)
        res["base"] = dict(info, replay=replay(tid, orc))
        orc, info = table(tid, base_specs, e03.INITS + EXTRA, st)
        res["polished"] = dict(info, replay=replay(tid, orc))
        orc, info = table(tid, specs_for(tid, 2), e03.INITS, settings(dim, True))
        res["refined_x2"] = dict(info, replay=replay(tid, orc))
        for v in ("polished", "refined_x2"):
            for p in ("CGC", "CGC_S"):
                a, b = res["base"]["replay"][p], res[v]["replay"][p]
                res[v][f"stable_{p}"] = all(x["n_asked"] == y["n_asked"] and x["released"] == y["released"]
                                            for x, y in zip(a, b))
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, f"{tid}.json"), "w") as fh:
            json.dump(res, fh, indent=1)
        summ[tid] = {v: dict(B=res[v]["B"], B_nominal=res[v]["B_nominal"],
                             accepted=all(res[v]["accepted"].values()),
                             **{k: res[v][k] for k in res[v] if k.startswith("stable_")}) for v in res}
        print(tid, json.dumps(summ[tid]), flush=True)
    with open(os.path.join(OUT, "summary.json"), "w") as fh:
        json.dump(summ, fh, indent=1)


if __name__ == "__main__":
    main()
