"""2-D per-iteration cost on the full MBB (180x60): SuperLU vs single-thread Pardiso SPD,
and OC bisection tolerance 1e-9 vs 1e-6 (relative)."""
import os
import sys
import time

os.environ["OMP_NUM_THREADS"] = os.environ["MKL_NUM_THREADS"] = "1"
import numpy as np  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import e01_controlled_sweeps as e  # noqa: E402
import simp  # noqa: E402
import taskspec  # noqa: E402

spec = e.track_specs("mbb_full")["center"][1][4]
P = taskspec.build(spec)
rng = np.random.default_rng(0)
for lin in ("superlu", "pardiso_spd"):
    S = simp.SIMP(P, simp.Settings(rmin=2.4, linear=lin))
    x = np.clip(0.4 + 0.1 * rng.standard_normal(S.act.size), 0, 1)
    t = time.perf_counter()
    for _ in range(5):
        S.gradient(x, 4.0)
    tg = (time.perf_counter() - t) / 5
    c, dc, dv, xp, _ = S.gradient(x, 4.0)
    for tol in (1e-9, 1e-6):
        S.s.oc_tol = tol
        t = time.perf_counter()
        for _ in range(5):
            S._oc(x, dc, dv, 4.0)
        to = (time.perf_counter() - t) / 5
        print(f"{lin:12s} gradient(factor+solve+sens) {1000 * tg:6.1f} ms   OC(tol={tol:g}) {1000 * to:6.1f} ms")
