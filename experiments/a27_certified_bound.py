"""A27: certified lower bound on each reading's optimal compliance (reviewer request, loop v5 round 1).

For rho in [0, 1], Emin + (E0 - Emin) rho^3 <= Emin + (E0 - Emin) rho, so a stiffer linear interpolation
gives a compliance no larger than SIMP's at every physical density field. The physical densities of the
SIMP problem (filtered and projected) lie in F = {0 <= rho <= 1, passive solid = 1, passive void = 0,
sum rho <= V}, the box-plus-volume set on which the volume constraint is imposed. Hence the optimum of the
convex variable-thickness problem min_{rho in F} c_lin(rho) bounds the SIMP optimum from below.
Convexity gives a certificate at any iterate rho_k (Frank-Wolfe gap):
    c_lin* >= c_lin(rho_k) + min_{rho in F} g_k . (rho - rho_k),   g_k = dc_lin/drho at rho_k,
where the minimum over F is a fractional knapsack. The bound L_t is the largest certificate over the
iterations of an optimality-criteria solve of the convex problem (no filter, no projection).
Reported per reading: L_t, the gap R_t / L_t - 1 of the computed reference R_t, and per CGC / CGC-S release
the certified upper bound max_t C_t(d) / L_t - 1 on its loss against the true optimum.
Usage: python experiments/a27_certified_bound.py [2|3] [task ...]
Output: results/a27/<tid>.json, results/a27/summary_<dim>d.json
"""
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["LT_VARIANT"] = "consensus"
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import e03_literature_tasks as e03  # noqa: E402
import littasks as lt  # noqa: E402
import policies as pl  # noqa: E402

OUT = os.path.join(ROOT, "results", "a27")
TAU = e03.TAU
MAX_IT = 400
GAP_TOL = 1e-3


def bound_job(spec, linear, threads):
    os.environ["OMP_NUM_THREADS"] = os.environ["MKL_NUM_THREADS"] = str(threads)
    import simp
    import taskspec
    prob = taskspec.build(spec)
    st = simp.Settings(penal=1.0, project=False, rmin=1.0, move=0.2, linear=linear)
    S = simp.SIMP(prob, st)
    t0 = time.perf_counter()
    n = S.act.size
    solid, void = S.solid[S.act], S.void[S.act]
    free = ~(solid | void)
    budget = prob.volfrac * n - solid.sum()
    x = np.full(n, prob.volfrac)
    x[solid], x[void] = 1.0, 0.0
    best_lb, c_min, hist = -np.inf, np.inf, []
    S._lam_prev = None
    S._move = st.move
    for it in range(1, MAX_IT + 1):
        c, dc, dv, xp, _ = S.gradient(x, 0.0)
        g = dc[free]
        order = np.argsort(g)                      # most negative first (dc <= 0)
        k = int(np.floor(budget))
        rho = np.zeros(g.size)
        rho[order[:k]] = 1.0
        if k < g.size:
            rho[order[k]] = budget - k
        lb = c + float(g @ (rho - xp[free]))
        best_lb, c_min = max(best_lb, lb), min(c_min, c)
        hist.append((c, lb))
        if (c_min - best_lb) / c_min < GAP_TOL:
            break
        x, _ = S._oc(x, dc, dv, 0.0)
    return dict(L=float(best_lb), c_lin=float(c_min), rel_gap=float((c_min - best_lb) / c_min), n_iter=it,
                wall_s=time.perf_counter() - t0, n_active=int(n))


def run_task(tid, workers):
    T = lt.TASKS[tid]
    dim = T["dim"]
    specs, _, _ = e03.jobs_for(tid)
    linear = "superlu" if dim == 2 else "cudss"
    threads = 1 if dim == 2 else 4
    with ProcessPoolExecutor(max_workers=min(workers, len(specs))) as ex:
        futs = {k: ex.submit(bound_job, s, linear, threads) for k, s in specs.items()}
        res = {k: f.result() for k, f in futs.items()}
    orc0, _ = e03.oracle_from_file(tid)
    zero = pl.Oracle(ref=orc0.ref, C=orc0.C, noise={k: 0.0 for k in orc0.noise})
    task = T["task"]
    interps = task.interpretations()
    gaps = {k: orc0.ref[k] / res[k]["L"] - 1 for k in specs}
    rel = {}
    for name, fn in (("CGC", pl.cgc), ("CGC_S", pl.cgc_s)):
        ub = []
        for t in interps:
            o = fn(task, zero, t, TAU)
            if not o.released:
                continue
            surv = [pl.ikey(x) for x in interps if all(x[s] == t[s] for s in o.asked)]
            ub.append(max(zero.C[(o.commit, k)] / res[k]["L"] - 1 for k in surv))
        rel[name] = dict(releases=len(ub), certified_within_tau=int(sum(u <= TAU for u in ub)),
                         min_certified_ub=min(ub) if ub else None, max_certified_ub=max(ub) if ub else None)
    return dict(task=tid, dim=dim, bound=res, reference_gap=gaps, releases=rel)


def main():
    dim = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    tids = sys.argv[2:] or [t for t in lt.TASKS if lt.TASKS[t]["dim"] == dim]
    workers = 16 if dim == 2 else 1
    os.makedirs(OUT, exist_ok=True)
    allg, summ = [], {}
    for tid in tids:
        r = run_task(tid, workers)
        with open(os.path.join(OUT, f"{tid}.json"), "w") as fh:
            json.dump(r, fh, indent=1, default=float)
        g = list(r["reference_gap"].values())
        allg += g
        summ[tid] = dict(min_gap=min(g), median_gap=float(np.median(g)), max_gap=max(g),
                         max_rel_gap_lin=max(b["rel_gap"] for b in r["bound"].values()), releases=r["releases"])
        print(tid, json.dumps(summ[tid], default=float), flush=True)
    tot = dict(readings=len(allg), min_gap=min(allg), median_gap=float(np.median(allg)), max_gap=max(allg),
               readings_gap_le_tau=int(sum(x <= TAU for x in allg)),
               releases={p: dict(releases=sum(s["releases"][p]["releases"] for s in summ.values()),
                                 certified_within_tau=sum(s["releases"][p]["certified_within_tau"]
                                                          for s in summ.values())) for p in ("CGC", "CGC_S")})
    with open(os.path.join(OUT, f"summary_{dim}d.json"), "w") as fh:
        json.dump(dict(total=tot, per_task=summ), fh, indent=1, default=float)
    print(json.dumps(tot, indent=1, default=float))


if __name__ == "__main__":
    main()
