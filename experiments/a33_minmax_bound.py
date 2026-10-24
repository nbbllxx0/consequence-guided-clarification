"""A33: bound-form (epigraph) min-max robust designs, solved with MMA (reviewer request, loop v5 round 3).

The primary robust baseline minimizes the p-norm (p = 16) of the reference-normalized compliances with the
optimality-criteria update. Here the min-max problem itself is solved in its bound form,
    min z  s.t.  C_t(x) / V_t <= z  for every reading t,   mean(xp) <= f,   0 <= x <= 1,
with the method of moving asymptotes (src/mma.py; Svanberg's min-max form a0 = 1, a_t = 1). Filter,
projection, continuation (beta = 1, 2, 4, 8 for 50 iterations each, then up to 300 at beta = 8) and the
volume bound (the smallest fraction among the readings) are those of the primary robust baseline. Starts:
the uniform field, the 5% sinusoidal perturbation, and the p = 16 design. The run covers the six
applicable tasks whose p = 16 design leaves a loss above tau (the other 17 applicable tasks are covered
already, so a better robust design cannot change their counts). V_t are the stored best-known references.

The replay then repeats robust alone, robust-first CGC and CGC with the robust design as an extra
candidate, using for each task the robust design (p = 16 or min-max) with the smaller worst loss.
Usage: python experiments/a33_minmax_bound.py [run [task ...] | replay]
Output: results/a33/minmax_<task>_<start>.json, results/a33/summary.json
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

OUT = os.path.join(ROOT, "results", "a33")
TASKS = ["L09", "L12", "L13", "L15", "L22", "L25"]
STARTS = ("uniform", "sin5", "p16")
TAU = e03.TAU
FINAL_MAX, MOVE, FINAL_MOVE, WINDOW, CONV_TOL = 300, 0.1, 0.05, 20, 1e-4


def minmax_job(tid, start, threads):
    os.environ["OMP_NUM_THREADS"] = os.environ["MKL_NUM_THREADS"] = str(threads)
    import mma
    import robust
    import runner
    import simp
    T = lt.TASKS[tid]
    interps = lt.interpretations(tid)
    specs = [T["build"](t) for t in interps]
    orc, _ = e03.oracle_from_file(tid)
    keys = [pl.ikey(t) for t in interps]
    st = dict(e03.settings_for(T["dim"]), **{k: specs[0][k] for k in ("rmin", "final_move") if k in specs[0]})
    if T["dim"] == 3:
        st["linear"] = "cudss"
    st["schedule"] = [tuple(x) for x in st["schedule"]]
    R = robust.RobustSIMP(specs, [orc.ref[k] for k in keys], st, p=16.0)
    S0, s = R.S0, R.S0.s
    vf, nact = S0.p.volfrac, S0.act.size
    if start == "p16":
        with np.load(os.path.join(e03.OUT, f"robust_{tid}.npz")) as d:
            x = np.clip(np.asarray(d["xphys"], float), 0.0, 1.0)
    else:
        x = runner.initial_design(S0, start, vf)
    fix = S0.fixmask
    x[S0.solid[S0.act]] = 1.0
    x[S0.void[S0.act]] = 0.0
    free = ~fix
    nf, m = int(free.sum()), len(specs) + 1

    def responses(x, beta):
        xf, xp = S0.physical(x, beta)
        dE = -s.penal * (s.E0 - s.Emin) * xp ** (s.penal - 1)
        dh = simp.heaviside_deriv(xf, beta, s.eta) if s.project else np.ones_like(xf)
        dh = np.where(fix, 0.0, dh)
        Cs, G = np.zeros(len(specs)), np.zeros((len(specs), nact))
        for sig, idx in R.groups.items():
            S = R.solvers[sig]
            lu = S.factor(xp)
            for i in idx:
                U = S.solve(lu, R.loads[i])
                c, ce = S.compliance_and_ce(U, R.loads[i])
                Cs[i] = c
                G[i] = S0.HT @ (dE * ce * dh) / R.V[i]
        fv = xp.sum() / (vf * nact) - 1.0
        dv = (S0.HT @ dh) / (vf * nact)
        return Cs / R.V, G, fv, dv, xp

    t0 = time.perf_counter()
    phases = list(s.schedule) + [(s.final_beta, FINAL_MAX)]
    hist, it_total, conv = [], 0, False
    a0, a = 1.0, np.r_[np.ones(len(specs)), 0.0]
    c, d = np.full(m, 1000.0), np.ones(m)
    for ip, (beta, n_it) in enumerate(phases):
        last = ip == len(phases) - 1
        xv = x[free].copy()
        x1, x2, low, upp = xv.copy(), xv.copy(), np.zeros(nf), np.ones(nf)
        for k in range(1, n_it + 1):
            it_total += 1
            r, G, fv, dv, xp = responses(x, beta)
            hist.append(float(r.max()))
            if last and len(hist) > WINDOW:
                w = np.array(hist[-WINDOW:])
                if (w.max() - w.min()) / abs(w.mean()) < CONV_TOL:
                    conv = True
                    break
            fval = np.r_[r, fv]
            dfdx = np.vstack([G[:, free], dv[free][None, :]])
            sol, low, upp = mma.mmasub(m, nf, k, xv, np.zeros(nf), np.ones(nf), x1, x2, np.zeros(nf), fval, dfdx,
                                       low, upp, a0, a, c, d, move=FINAL_MOVE if last else MOVE)
            x2, x1, xv = x1, xv, np.clip(sol["x"], 0.0, 1.0)
            x[free] = xv
        if conv:
            break
    r, _, fv, _, xp = responses(x, beta)
    loss = {k: float(v - 1.0) for k, v in zip(keys, r)}
    out = dict(task=tid, start=start, keys=keys, loss=loss, worst=max(loss.values()), n_iter=it_total,
               converged=conv, volume_excess=float(fv), wall_s=time.perf_counter() - t0, volfrac=vf,
               linear=st["linear"], history_tail=hist[-25:])
    os.makedirs(OUT, exist_ok=True)
    np.savez_compressed(os.path.join(OUT, f"minmax_{tid}_{start}.npz"), xphys=xp, act=S0.act)
    with open(os.path.join(OUT, f"minmax_{tid}_{start}.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    return out


def run(tids):
    os.makedirs(OUT, exist_ok=True)
    jobs = [(t, s) for t in tids for s in STARTS if not os.path.exists(os.path.join(OUT, f"minmax_{t}_{s}.json"))]
    two = [j for j in jobs if lt.TASKS[j[0]]["dim"] == 2]
    three = [j for j in jobs if lt.TASKS[j[0]]["dim"] == 3]
    for batch, workers, threads in ((two, 12, 1), (three, 1, 4)):
        if not batch:
            continue
        with ProcessPoolExecutor(max_workers=min(workers, len(batch))) as ex:
            futs = {j: ex.submit(minmax_job, *j, threads) for j in batch}
            for j, f in futs.items():
                o = f.result()
                print(j, "worst", round(o["worst"], 5), "it", o["n_iter"], "conv", o["converged"],
                      "vol", f"{o['volume_excess']:.1e}", f"{o['wall_s']:.0f}s", flush=True)


def replay():
    import a15_reviewer_replays as a15
    best = {}
    for tid in TASKS:
        runs = [json.load(open(os.path.join(OUT, f"minmax_{tid}_{s}.json"))) for s in STARTS]
        feas = [r for r in runs if r["volume_excess"] <= 1e-6]  # the feasibility tolerance of Section 2.4
        b = min(feas, key=lambda r: r["worst"])
        best[tid] = dict(start=b["start"], worst=b["worst"], loss=b["loss"],
                         per_start={r["start"]: dict(worst=r["worst"], converged=r["converged"], n_iter=r["n_iter"],
                                                     volume_excess=r["volume_excess"]) for r in runs})
    acc = {}
    per_task = {}
    for tid in lt.TASKS:
        task, orc, _, _ = a15.load_task(tid)
        interps = task.interpretations()
        rl16 = a15.robust_loss(tid, orc)
        rl = rl16
        if tid in best and rl16 is not None:
            p16_worst = max(rl16.values())
            per_task[tid] = dict(p16_worst=p16_worst, minmax_worst=best[tid]["worst"], start=best[tid]["start"],
                                 covers=best[tid]["worst"] <= TAU, per_start=best[tid]["per_start"])
            if best[tid]["worst"] < p16_worst:
                rl = best[tid]["loss"]
        for name, r in (("p16", rl16), ("best", rl)):
            a15.add(acc, f"robust_first_{name}", a15.totals(a15.robust_first_rows(task, orc, interps, r, TAU)))
            ext = {"robust": r} if r else {}
            a15.add(acc, f"CGC_robust_candidate_{name}", a15.totals(a15.score(
                task, orc, interps, [(t, a15.cgc_candidates(task, orc, t, TAU, ext)) for t in interps], TAU,
                loss=lambda cc, k, r=r: r[k] if cc == "robust" else orc.loss(cc, k))))
            if r is not None:
                n = len(r)
                a = acc.setdefault(f"robust_alone_{name}", dict(tasks=0, cases=0, unsafe=0, exceed=0))
                a["tasks"] += 1
                a["cases"] += n
                a["unsafe"] += n if max(r.values()) > TAU else 0
                a["exceed"] += sum(v > TAU for v in r.values())
    res = dict(per_task=per_task, totals=acc, settings=dict(final_max=FINAL_MAX, move=MOVE, final_move=FINAL_MOVE,
                                                            window=WINDOW, conv_tol=CONV_TOL, starts=STARTS))
    with open(os.path.join(OUT, "summary.json"), "w") as fh:
        json.dump(res, fh, indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    if mode == "run":
        run(sys.argv[2:] or TASKS)
    else:
        replay()
