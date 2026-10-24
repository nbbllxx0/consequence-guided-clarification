"""A20: sharper robust designs for the applicable tasks that the p = 16 design does not cover.

The primary robust baseline minimizes the p-norm (p = 16) of the reference-normalized compliances. For
n readings, the p-norm overestimates the largest ratio by at most a factor n^(1/p); p = 256 bounds this
factor by 1.009 for n <= 9 (1.012 for the 18 readings of L22). This run repeats the robust optimization
with p = 64 and p = 256 (one start from the uniform density, the primary filter, projection, continuation
and optimality-criteria settings, as in E03), and reports the worst loss over every reading. It is a
sharper approximation of the minimax-ratio design, not a bound (epigraph) formulation.
Usage: python experiments/a20_robust_pnorm.py [task ...]
Output: results/a20/robust_p<p>_<task>.json, results/a20/summary.json
"""
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["LT_VARIANT"] = "consensus"
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import e03_literature_tasks as e03  # noqa: E402
import littasks as lt  # noqa: E402
import policies as pl  # noqa: E402

OUT = os.path.join(ROOT, "results", "a20")
TASKS = ["L09", "L12", "L13", "L15", "L22", "L25"]
PS = (64.0, 256.0)
TAU = e03.TAU


def job(tid, p, threads):
    os.environ["OMP_NUM_THREADS"] = os.environ["MKL_NUM_THREADS"] = str(threads)
    import robust
    T = lt.TASKS[tid]
    interps = lt.interpretations(tid)
    specs = [T["build"](t) for t in interps]
    orc, _ = e03.oracle_from_file(tid)
    st = dict(e03.settings_for(T["dim"]), **{k: specs[0][k] for k in ("rmin", "final_move") if k in specs[0]})
    if T["dim"] == 3:
        st["linear"] = "cudss"
    st["schedule"] = [tuple(x) for x in st["schedule"]]
    keys = [pl.ikey(t) for t in interps]
    R = robust.RobustSIMP(specs, [orc.ref[k] for k in keys], st, p=p)
    r = R.optimize()
    loss = {k: float(c - 1.0) for k, c in zip(keys, r["ratio"])}
    out = dict(task=tid, p=p, keys=keys, loss=loss, worst=max(loss.values()), J=r["J"], n_iter=r["n_iter"],
               converged=r["converged"], wall_s=r["wall_s"], volfrac=R.S0.p.volfrac)
    with open(os.path.join(OUT, f"robust_p{int(p)}_{tid}.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    return out


def main():
    tids = sys.argv[1:] or TASKS
    os.makedirs(OUT, exist_ok=True)
    runs = [(t, p) for t in tids for p in PS]
    res = {}
    with ProcessPoolExecutor(max_workers=6) as ex:
        futs = {(t, p): ex.submit(job, t, p, 4 if lt.TASKS[t]["dim"] == 3 else 1) for t, p in runs}
        for (t, p), f in futs.items():
            res.setdefault(t, {})[f"p{int(p)}"] = f.result()["worst"]
            print(t, p, round(res[t][f"p{int(p)}"], 4), flush=True)
    with open(os.path.join(ROOT, "results", "a15", "consensus.json")) as fh:
        base = json.load(fh)["robust"]["per_task"]
    summ = {t: dict(p16=base[t]["worst"], **v, covers=any(x <= TAU for x in [base[t]["worst"], *v.values()]))
            for t, v in res.items()}
    with open(os.path.join(OUT, "summary.json"), "w") as fh:
        json.dump(summ, fh, indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
