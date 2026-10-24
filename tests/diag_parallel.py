"""Diagnose (a) parallel slowdown and (b) MBB non-convergence.

(a) time one E01 job alone, then N identical jobs in a process pool, reporting per-iteration
    time and the worker's thread count.
(b) for the alone run, print the objective tail and the KKT residual distribution.
"""
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))


def job(spec, settings):
    import threading
    import simp
    import taskspec
    t0 = time.perf_counter()
    S = simp.SIMP(taskspec.build(spec), simp.Settings(**settings))
    r = S.optimize()
    try:
        import psutil
        nth = psutil.Process().num_threads()
    except Exception:
        nth = threading.active_count()
    kk, lam = S.kkt_residual(r["x"], r["beta"], lam=r["oc_multiplier"])
    return dict(wall=time.perf_counter() - t0, iters=r["n_iter"], conv=r["converged"], threads=nth,
                tail=r["history"][-30:].tolist(), kkt=kk, C=r["compliance"])


if __name__ == "__main__":
    import e01_controlled_sweeps as e
    import runner
    spec = e.track_specs("mbb_full")["center"][1][4]
    st = e.SET
    os.environ["OMP_NUM_THREADS"] = os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    with ProcessPoolExecutor(1) as ex:
        a = ex.submit(job, spec, st).result()
    print(f"alone: wall={a['wall']:.1f}s iters={a['iters']} per-iter={1000 * a['wall'] / a['iters']:.0f}ms "
          f"conv={a['conv']} threads={a['threads']} kkt={a['kkt']:.2e} C={a['C']:.4f}")
    t = np.array(a["tail"])
    print("tail rel range", (t.max() - t.min()) / t.mean(), " last values", np.round(t[-6:], 5))
    for n in (4, 10, 19):
        t0 = time.perf_counter()
        with ProcessPoolExecutor(n) as ex:
            rs = list(ex.map(job, [spec] * n, [st] * n))
        w = np.array([r["wall"] for r in rs])
        print(f"{n:2d} parallel: batch {time.perf_counter() - t0:.1f}s; per-job wall median {np.median(w):.1f}s "
              f"(slowdown x{np.median(w) / a['wall']:.1f}); threads/worker {rs[0]['threads']}")
