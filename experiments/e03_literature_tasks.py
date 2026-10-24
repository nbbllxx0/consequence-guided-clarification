"""E03: literature-derived tasks -> exhaustive oracle tables -> policy replay.

For each task in src/littasks.py:
  1. optimize every interpretation from two starts (uniform, sin5); reference = best;
     noise = relative spread of the two starts;
  2. full cross table C[d, t] with designs mapped onto each interpretation's domain;
     references updated to the best known (signed gaps recorded);
  3. replay policies with each admissible interpretation as the hidden truth;
     truth-agnostic check: a release is false if ANY surviving admissible interpretation
     has loss > tau + noise.
Outputs: results/e03/<task>.json and results/e03/replay.json
"""
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import consequence as cq  # noqa: E402
import littasks as lt  # noqa: E402
import policies as pl  # noqa: E402
import runner  # noqa: E402
import taskspec  # noqa: E402

OUT = os.path.join(ROOT, "results", "e03" + lt.RESULTS_SUFFIX)   # LT_VARIANT selects the encoding
INITS = ("uniform", "sin5")
TAU = 0.05


def settings_for(dim):
    return runner.settings_dict(rmin=1.5, linear="superlu" if dim == 2 else "pardiso_spd")


def jobs_for(tid):
    T = lt.TASKS[tid]
    specs = {pl.ikey(t): T["build"](t) for t in lt.interpretations(tid)}
    st = settings_for(T["dim"])
    return specs, st, [(specs[k], i, st) for k in specs for i in INITS]


def prefetch(tids):
    """Run every missing optimization in two pooled batches (2-D, 3-D); results land in the cache."""
    for dim, workers, threads in ((2, 19, 1), (3, 4, 4)):
        jobs = [j for tid in tids if lt.TASKS[tid]["dim"] == dim for j in jobs_for(tid)[2]]
        if jobs:
            print(f"prefetch dim={dim}: {len(jobs)} jobs", flush=True)
            runner.run_many(jobs, workers=workers, threads=threads)


def oracle_for(tid):
    T = lt.TASKS[tid]
    specs, st, jobs = jobs_for(tid)
    threads = 1 if T["dim"] == 2 else 4
    recs = runner.run_many(jobs, workers=19 if T["dim"] == 2 else 4, threads=threads, verbose=False)
    lib = cq.Library(st)
    ref, noise, meta = {}, {}, {}
    for n, k in enumerate(specs):
        rr = recs[2 * n:2 * n + 2]
        cs = [r["compliance"] for r in rr]
        b = int(np.argmin(cs))
        xp, act = runner.load_design(rr[b]["key"])
        P = taskspec.build(specs[k])
        lib.add(k, xp, k, act=act, nel=P.nel)
        ref[k] = cs[b]
        noise[k] = (max(cs) - min(cs)) / min(cs)
        meta[k] = dict(accepted=all(r["accepted"] for r in rr), kkt=max(r["kkt"] for r in rr),
                       wall_s=sum(r["wall_s"] for r in rr), n_iter=[r["n_iter"] for r in rr])
    keys = list(specs)
    C = lib.evaluate(keys, specs)
    feas = np.array([[lib.feasible(d, specs[t]) for t in keys] for d in keys])
    # a filter radius read as a minimum length scale: a design made with a smaller radius violates
    # the length scale of an interpretation with a larger one
    rm = {k: specs[k].get("rmin", st["rmin"]) for k in keys}
    feas &= np.array([[rm[d] >= rm[t] - 1e-12 for t in keys] for d in keys])
    Cf = np.where(feas, C, np.inf)
    best_known = np.minimum(np.array([ref[k] for k in keys]), np.min(np.where(feas, C, np.inf), 0))
    gaps = {k: float(ref[k] / best_known[j] - 1) for j, k in enumerate(keys)}
    refb = {k: float(best_known[j]) for j, k in enumerate(keys)}
    Cd = {(d, t): float(Cf[i, j]) for i, d in enumerate(keys) for j, t in enumerate(keys)}
    out = dict(task=tid, source=T["source"], dim=T["dim"], slots=T["task"].slots, nominal=T["task"].nominal,
               mandatory=list(T["task"].mandatory), reasons=T["reasons"], recon=T["recon"], keys=keys,
               C=[[Cd[(d, t)] for t in keys] for d in keys], ref=refb, ref_gap_beaten=gaps, noise=noise,
               meta=meta, counter=lib.counter.as_dict())
    with open(os.path.join(OUT, f"{tid}.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    return pl.Oracle(ref=refb, C=Cd, noise=noise), out


def robust_applicable(tid):
    T = lt.TASKS[tid]
    specs = [T["build"](t) for t in lt.interpretations(tid)]
    if len(specs) < 2:
        return "single interpretation"
    if len({json.dumps(s.get("domain"), sort_keys=True) for s in specs}) > 1:
        return "interpretations differ in the design domain"
    if len({s.get("rmin") for s in specs}) > 1:
        return "filter radius is itself ambiguous"
    if len({json.dumps(s.get("solid"), sort_keys=True) for s in specs}) > 1:
        return "interpretations differ in passive regions"
    return None


def _robust_job(tid, refs, threads):
    os.environ["OMP_NUM_THREADS"] = os.environ["MKL_NUM_THREADS"] = str(threads)
    import robust
    T = lt.TASKS[tid]
    interps = lt.interpretations(tid)
    specs = [T["build"](t) for t in interps]
    st = dict(settings_for(T["dim"]), **{k: specs[0][k] for k in ("rmin", "final_move") if k in specs[0]})
    if T["dim"] == 3:
        st["linear"] = "cudss"                     # robust design is not a cached oracle job: use the GPU
    st["schedule"] = [tuple(x) for x in st["schedule"]]
    R = robust.RobustSIMP(specs, [refs[pl.ikey(t)] for t in interps], st)
    r = R.optimize()
    np.savez_compressed(os.path.join(OUT, f"robust_{tid}.npz"), xphys=r["xphys"], act=r["act"])
    out = dict(task=tid, spec_hashes=[taskspec.spec_hash(sp) for sp in specs], linear=st["linear"],
               keys=[pl.ikey(t) for t in interps], C=r["C"].tolist(), ratio=r["ratio"].tolist(),
               J=r["J"], n_iter=r["n_iter"], converged=r["converged"], wall_s=r["wall_s"],
               n_groups=len(R.groups), volfrac=R.S0.p.volfrac, p=R.p)
    with open(os.path.join(OUT, f"robust_{tid}.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    return out


def robust_all(tids, refs_by_task):
    """No-question robust baseline per task (p-norm of reference-normalized compliances)."""
    res, todo = {}, []
    for tid in tids:
        why = robust_applicable(tid)
        p = os.path.join(OUT, f"robust_{tid}.json")
        if why:
            res[tid] = dict(applicable=False, reason=why)
        else:
            cached = None
            if os.path.exists(p):
                with open(p) as fh:
                    cached = json.load(fh)
                T = lt.TASKS[tid]
                if cached.get("spec_hashes") != [taskspec.spec_hash(T["build"](t)) for t in lt.interpretations(tid)]:
                    cached = None                      # task definition changed since the cached run
            if cached is not None:
                res[tid] = dict(cached, applicable=True)
            else:
                todo.append(tid)
    for dim, workers, threads in ((2, 12, 1), (3, 4, 4)):
        batch = [t for t in todo if lt.TASKS[t]["dim"] == dim]
        if not batch:
            continue
        print(f"robust dim={dim}: {len(batch)} tasks", flush=True)
        with ProcessPoolExecutor(max_workers=min(workers, len(batch))) as ex:
            futs = {t: ex.submit(_robust_job, t, refs_by_task[t], threads) for t in batch}
            for t, f in futs.items():
                res[t] = dict(f.result(), applicable=True)
    return res


def robust_rows(tid, oracle, rob, tau=TAU):
    task = lt.TASKS[tid]["task"]
    ratio = dict(zip(rob["keys"], rob["ratio"]))
    worst = max(ratio[k] - 1 - oracle.noise.get(k, 0) for k in ratio)
    rows = []
    for truth in task.interpretations():
        tk = pl.ikey(truth)
        rows.append(dict(truth=tk, asked=list(task.mandatory), n_asked=len(task.mandatory), commit="robust",
                         true_loss=ratio[tk] - 1, worst_surviving_loss=worst, false_release_any=bool(worst > tau),
                         truth_exceed=bool(ratio[tk] - 1 > tau + oracle.noise.get(tk, 0)),
                         released=True, optimizations=len(ratio) + 1, cross_evals=0))
    # cost: the normalized p-norm objective needs every reference (|Theta| optimizations) plus the robust run
    return dict(rows=rows, mean_questions=float(np.mean([r["n_asked"] for r in rows])),
                max_true_loss=float(np.max([r["true_loss"] for r in rows])),
                false_release_any=int(sum(r["false_release_any"] for r in rows)),
                mean_optimizations=float(len(ratio) + 1), covers=bool(worst <= tau), worst=float(worst),
                robust_wall_s=rob["wall_s"], robust_groups=rob["n_groups"])


def robust_then_h(rp, n_interp):
    """Release the robust design when it covers every admissible reading within tau (+ noise);
    otherwise fall back to consequence-guided clarification (CGC, full table). The references are shared;
    the robust run costs one extra optimization whenever it is attempted."""
    rb = rp.get("robust")
    if rb is not None and rb["covers"]:
        rows = rb["rows"]
    else:
        extra = 1 if rb is not None else 0
        rows = [dict(r, optimizations=r["optimizations"] + extra) for r in rp["CGC"]["rows"]]
    return dict(rows=rows, mean_questions=float(np.mean([r["n_asked"] for r in rows])),
                max_true_loss=float(np.max([r["true_loss"] for r in rows])),
                false_release_any=int(sum(r["false_release_any"] for r in rows)),
                mean_optimizations=float(np.mean([r["optimizations"] for r in rows])))


def replay(tid, oracle, tau=TAU):
    task = lt.TASKS[tid]["task"]
    interps = task.interpretations()
    res = {}
    # zero-allowance variants (primary setting): decision and evaluation both without the noise term
    zero = pl.Oracle(ref=oracle.ref, C=oracle.C, noise={k: 0.0 for k in oracle.noise})
    runs = [(n, f, oracle) for n, f in pl.POLICIES.items()] + \
           [("CGC_a0", pl.cgc, zero), ("CGC_S_a0", pl.cgc_s, zero), ("no_ask_a0", pl.no_ask, zero),
            ("ask_all_a0", pl.ask_all, zero), ("oracle_a0", pl.oracle_lookahead, zero)]
    for name, fn, oracle in runs:
        rows = []
        for truth in interps:
            o = fn(task, oracle, truth, tau)
            ans = {s: truth[s] for s in o.asked}
            surv = [pl.ikey(t) for t in interps if all(t[s] == v for s, v in ans.items())]
            worst = max(oracle.loss(o.commit, t) - oracle.noise.get(t, 0) for t in surv) if o.commit else np.inf
            rows.append(dict(truth=pl.ikey(truth), asked=o.asked, n_asked=len(o.asked), commit=o.commit,
                             true_loss=o.true_loss, worst_surviving_loss=worst,
                             false_release_any=bool(o.released and worst > tau),
                             truth_exceed=bool(o.released and o.true_loss > tau + oracle.noise.get(pl.ikey(truth), 0)),
                             released=o.released, optimizations=o.optimizations, cross_evals=o.cross_evals))
        res[name] = dict(rows=rows,
                         mean_questions=float(np.mean([r["n_asked"] for r in rows])),
                         max_true_loss=float(np.max([r["true_loss"] for r in rows])),
                         false_release_any=int(sum(r["false_release_any"] for r in rows)),
                         mean_optimizations=float(np.mean([r["optimizations"] for r in rows])))
    return res


def oracle_from_file(tid):
    """Rebuild the oracle from a saved per-task table (no FE work)."""
    with open(os.path.join(OUT, f"{tid}.json")) as fh:
        out = json.load(fh)
    keys = out["keys"]
    Cd = {(d, t): float(out["C"][i][j]) for i, d in enumerate(keys) for j, t in enumerate(keys)}
    return pl.Oracle(ref=out["ref"], C=Cd, noise=out["noise"]), out


def main():
    os.makedirs(OUT, exist_ok=True)
    args = sys.argv[1:]
    replay_only = "--replay-only" in args
    tids = [a for a in args if not a.startswith("--")] or list(lt.TASKS)
    if replay_only:
        oracles = {tid: oracle_from_file(tid) for tid in tids}
    else:
        prefetch(tids)
        oracles = {tid: oracle_for(tid) for tid in tids}
    rob = robust_all(tids, {tid: oracles[tid][1]["ref"] for tid in tids})
    all_replay = {}
    for tid in tids:
        oracle, out = oracles[tid]
        L = np.array(out["C"]) / np.array([out["ref"][k] for k in out["keys"]])[None, :] - 1
        rp = replay(tid, oracle)
        if rob[tid]["applicable"]:
            rp["robust"] = robust_rows(tid, oracle, rob[tid])
        else:
            print(f"   robust n/a for {tid}: {rob[tid]['reason']}")
        rp["robust_then_H"] = robust_then_h(rp, len(out["keys"]))
        all_replay[tid] = {k: {kk: vv for kk, vv in v.items() if kk != "rows"} for k, v in rp.items()}
        all_replay[tid]["_rows"] = {k: v["rows"] for k, v in rp.items()}
        line = "  ".join(f"{k}:q={v['mean_questions']:.1f}/maxL={v['max_true_loss']:.3f}/FR={v['false_release_any']}/opt={v['mean_optimizations']:.1f}"
                         for k, v in rp.items())
        print(f"{tid} dim={out['dim']} n={len(out['keys'])} maxL={np.max(L[np.isfinite(L)]):.3f} "
              f"noise<={max(out['noise'].values()):.1e}\n   {line}", flush=True)
    path = os.path.join(OUT, "replay.json")
    merged = {}
    if os.path.exists(path):                       # a partial run updates only its own tasks
        with open(path) as fh:
            merged = json.load(fh)
    merged.update(all_replay)
    with open(path, "w") as fh:
        json.dump(merged, fh, indent=1)


if __name__ == "__main__":
    main()
