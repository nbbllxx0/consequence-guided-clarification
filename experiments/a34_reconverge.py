"""A34: re-convergence of the references whose projected-gradient residual exceeds 0.1 (reviewer request,
loop v5 round 3), then the primary replay on the re-converged tables.

For each of the 64 primary readings whose selected start has residual r > 0.1 (Section 4.2), the selected
design is optimized further at the final projection sharpness (beta = 8), with the same filter, projection
and volume bound, by the method of moving asymptotes (src/mma.py; move limit 0.05). The run stops when the
projected-gradient residual, with the MMA volume multiplier, is at most R_TOL = 0.01, or after MAX_IT
iterations. The residual is checked every CHECK iterations.

Each task with a re-converged reading then gets a new table: the design of a reading is the re-converged
design when its compliance is lower, otherwise the original one; the cross table is re-evaluated, and the
best-known reference is the minimum of the old reference, the new own compliance and the new feasible
column minimum. The replay (zero allowance, tau = 0.05) repeats CGC, CGC-S, ask-all and the silent default,
and compares per case with the primary replay. The primary releases are also re-scored, unchanged,
against the new references.
Usage: python experiments/a34_reconverge.py [run [task ...] | replay]
Output: results/a34/<task>__<reading-hash>.json(+.npz), results/a34/<task>_table.json, results/a34/summary.json
"""
import hashlib
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
import runner  # noqa: E402

OUT = os.path.join(ROOT, "results", "a34")
TAU = e03.TAU
R_FLAG, R_TOL, MAX_IT, CHECK, MOVE = 0.1, 0.01, 1000, 10, 0.05


def tag(k):
    return hashlib.sha1(k.encode()).hexdigest()[:10]


def flagged():
    out = []
    for tid in sorted(lt.TASKS):
        specs, st, _ = e03.jobs_for(tid)
        for k, sp in specs.items():
            rr = [runner.load(runner.job_key(sp, i, st)) for i in e03.INITS]
            r = min(rr, key=lambda r: r["compliance"])
            if r["kkt"] > R_FLAG:
                out.append((tid, k, r["key"]))
    return out


def reconverge_job(tid, k, run_key, threads):
    os.environ["OMP_NUM_THREADS"] = os.environ["MKL_NUM_THREADS"] = str(threads)
    import mma
    import simp
    import taskspec
    rec = runner.load(run_key)
    spec = rec["spec"]
    prob = taskspec.build(spec)
    st = dict(rec["settings"], **{q: spec[q] for q in ("rmin", "final_move") if q in spec})
    st["schedule"] = [tuple(x) for x in st["schedule"]]
    if lt.TASKS[tid]["dim"] == 3:
        st["linear"] = "cudss"
    S = simp.SIMP(prob, simp.Settings(**st))
    with np.load(os.path.join(runner.RUNS, run_key + ".npz")) as d:
        x = np.asarray(d["x"], float).copy()
    beta = float(rec["beta"])
    free = ~S.fixmask
    nf, nact, vf = int(free.sum()), S.act.size, prob.volfrac
    r0_ls, _ = S.kkt_residual(x, beta)
    t0 = time.perf_counter()
    c0 = None
    xv = x[free].copy()
    x1, x2, low, upp = xv.copy(), xv.copy(), np.zeros(nf), np.ones(nf)
    hist, res_hist, it, lam_u, r_mma = [], [], 0, np.nan, np.inf
    while it < MAX_IT:
        it += 1
        c, dc, dv, xp, _ = S.gradient(x, beta)
        if c0 is None:
            c0 = c
        hist.append(c)
        fv = np.array([xp.sum() / (vf * nact) - 1.0])
        sol, low, upp = mma.mmasub(1, nf, it, xv, np.zeros(nf), np.ones(nf), x1, x2, dc[free] / c0, fv,
                                   (dv[free] / (vf * nact))[None, :], low, upp, 1.0, np.zeros(1),
                                   np.full(1, 1000.0), np.ones(1), move=MOVE)
        lam_u = float(sol["lam"][0]) * c0 / (vf * nact)
        if it % CHECK == 0:
            r_mma, _ = S.kkt_residual(x, beta, lam=lam_u)
            res_hist.append((it, float(r_mma)))
            if r_mma <= R_TOL:
                break
        x2, x1, xv = x1, xv, np.clip(sol["x"], 0.0, 1.0)
        x[free] = xv
    xf, xp = S.physical(x, beta)
    lu = S.factor(xp)
    U = S.solve(lu, prob.loads)
    c_new, _ = S.compliance_and_ce(U, prob.loads)
    r_ls, _ = S.kkt_residual(x, beta)
    out = dict(task=tid, reading=k, run_key=run_key, c_old=rec["compliance"], c_new=float(c_new),
               rel_change=float(c_new / rec["compliance"] - 1.0), kkt_old_oc=rec["kkt"], kkt_old_ls=float(r0_ls),
               kkt_new_mma=float(r_mma), kkt_new_ls=float(r_ls), reached=bool(r_mma <= R_TOL), n_iter=it,
               volfrac=float(xp.sum() / nact), volfrac_target=vf, residual=float(S.residual(xp, U, prob.loads)),
               res_hist=res_hist, wall_s=time.perf_counter() - t0, linear=st["linear"])
    os.makedirs(OUT, exist_ok=True)
    base = os.path.join(OUT, f"{tid}__{tag(k)}")
    np.savez_compressed(base + ".npz", xphys=xp, act=S.act)
    with open(base + ".json", "w") as fh:
        json.dump(out, fh, indent=1)
    return out


def run(tids):
    jobs = [j for j in flagged() if (not tids or j[0] in tids)
            and not os.path.exists(os.path.join(OUT, f"{j[0]}__{tag(j[1])}.json"))]
    two = [j for j in jobs if lt.TASKS[j[0]]["dim"] == 2]
    three = [j for j in jobs if lt.TASKS[j[0]]["dim"] == 3]
    print(f"{len(two)} 2-D and {len(three)} 3-D readings", flush=True)
    for batch, workers, threads in ((two, 14, 1), (three, 3, 2)):
        if not batch:
            continue
        with ProcessPoolExecutor(max_workers=min(workers, len(batch))) as ex:
            futs = {j: ex.submit(reconverge_job, *j, threads) for j in batch}
            for j, f in futs.items():
                o = f.result()
                print(j[0], j[1][:40], f"dC={o['rel_change']:+.4f} r {o['kkt_old_oc']:.2f}->{o['kkt_new_mma']:.3f}"
                      f" it={o['n_iter']} {o['wall_s']:.0f}s", flush=True)


def table(tid, recon):
    """New cross table for one task with the re-converged designs (when better) in place of the originals."""
    import consequence as cq
    import taskspec
    T = lt.TASKS[tid]
    specs, st, _ = e03.jobs_for(tid)
    _, old = e03.oracle_from_file(tid)
    lib = cq.Library(st)
    own = {}
    for k, sp in specs.items():
        rr = [runner.load(runner.job_key(sp, i, st)) for i in e03.INITS]
        b = min(rr, key=lambda r: r["compliance"])
        P = taskspec.build(sp)
        xp, act = runner.load_design(b["key"])
        own[k], src = b["compliance"], "original"
        if k in recon and recon[k]["c_new"] < b["compliance"]:
            with np.load(os.path.join(OUT, f"{tid}__{tag(k)}.npz")) as d:
                xp, act = d["xphys"], d["act"]
            own[k], src = recon[k]["c_new"], "reconverged"
        lib.add(k, xp, src, act=act, nel=P.nel)
    keys = list(specs)
    C = lib.evaluate(keys, specs)
    feas = np.array([[lib.feasible(d, specs[t]) for t in keys] for d in keys])
    rm = {k: specs[k].get("rmin", st["rmin"]) for k in keys}
    feas &= np.array([[rm[d] >= rm[t] - 1e-12 for t in keys] for d in keys])
    Cf = np.where(feas, C, np.inf)
    Vold = np.array([old["ref"][k] for k in keys])
    Vnew = np.minimum.reduce([Vold, np.array([own[k] for k in keys]), Cf.min(0)])
    out = dict(task=tid, keys=keys, C=Cf.tolist(), ref_old=dict(zip(keys, Vold.tolist())),
               ref=dict(zip(keys, Vnew.tolist())), source={k: lib.origin[k] for k in keys}, dim=T["dim"])
    with open(os.path.join(OUT, f"{tid}_table.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    return out


def replay():
    recs = {}
    for f in os.listdir(OUT):
        if "__" in f and f.endswith(".json"):
            o = json.load(open(os.path.join(OUT, f)))
            recs.setdefault(o["task"], {})[o["reading"]] = o
    pols = (("CGC", pl.cgc), ("CGC_S", pl.cgc_s), ("ask_all", pl.ask_all), ("no_ask", pl.no_ask))
    per_task, tot = {}, {}
    vchange = []
    for tid in sorted(lt.TASKS):
        task = lt.TASKS[tid]["task"]
        interps = task.interpretations()
        orc0, old = e03.oracle_from_file(tid)
        z0 = pl.Oracle(ref=orc0.ref, C=orc0.C, noise={k: 0.0 for k in orc0.ref})
        if tid in recs:
            new = table(tid, recs[tid])
            keys = new["keys"]
            Cd = {(d, t): float(new["C"][i][j]) for i, d in enumerate(keys) for j, t in enumerate(keys)}
            z1 = pl.Oracle(ref=new["ref"], C=Cd, noise={k: 0.0 for k in keys})
            vchange += [new["ref"][k] / new["ref_old"][k] - 1.0 for k in keys]
        else:
            z1 = z0
            vchange += [0.0] * len(interps)
        row = {}
        for name, fn in pols:
            a = dict(cases=0, q0=0, q1=0, rel0=0, rel1=0, unsafe1=0, changed=0, old_release_over_new_ref=0)
            for t in interps:
                o0, o1 = fn(task, z0, t, TAU), fn(task, z1, t, TAU)
                surv0 = [pl.ikey(x) for x in interps if all(x[s] == t[s] for s in o0.asked)]
                surv1 = [pl.ikey(x) for x in interps if all(x[s] == t[s] for s in o1.asked)]
                nq = lambda o: len([s for s in o.asked if s not in task.mandatory])  # noqa: E731
                a["cases"] += 1
                a["q0"] += nq(o0)
                a["q1"] += nq(o1)
                a["rel0"] += o0.released
                a["rel1"] += o1.released
                a["changed"] += (nq(o0) != nq(o1)) or (o0.released != o1.released)
                if o1.released and o1.commit and max(z1.loss(o1.commit, k) for k in surv1) > TAU:
                    a["unsafe1"] += 1
                # the primary release, design unchanged (old table row), against the new references
                if o0.released and o0.commit:
                    w = max(z0.C[(o0.commit, k)] / z1.ref[k] - 1.0 for k in surv0)
                    a["old_release_over_new_ref"] += w > TAU
            row[name] = a
            acc = tot.setdefault(name, {q: 0 for q in a})
            for q, v in a.items():
                acc[q] += v
        per_task[tid] = row
    rr = [o for v in recs.values() for o in v.values()]
    res = dict(readings=len(rr), reached=sum(o["reached"] for o in rr),
               improved=sum(o["rel_change"] < 0 for o in rr),
               rel_change_min=min(o["rel_change"] for o in rr), rel_change_median=float(np.median([o["rel_change"] for o in rr])),
               kkt_new_max=max(o["kkt_new_mma"] for o in rr), kkt_new_median=float(np.median([o["kkt_new_mma"] for o in rr])),
               V_lowered_gt_1pct=int(sum(v < -0.01 for v in vchange)), V_lowered_any=int(sum(v < -1e-9 for v in vchange)),
               V_change_min=float(min(vchange)), totals=tot, per_task=per_task,
               settings=dict(r_flag=R_FLAG, r_tol=R_TOL, max_it=MAX_IT, check=CHECK, move=MOVE))
    with open(os.path.join(OUT, "summary.json"), "w") as fh:
        json.dump(res, fh, indent=1, default=float)
    print(json.dumps({k: v for k, v in res.items() if k != "per_task"}, indent=1, default=float))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    if mode == "run":
        run(sys.argv[2:])
    else:
        replay()
