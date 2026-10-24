"""Per-iteration cost breakdown of the 3-D SIMP loop with the cuDSS backend.

Usage: python tests/profile_gpu_iter.py [nelx]   (box nelx x nelx/2 x nelx/2, 10 iterations)
"""
import os
import sys
import time

import cupy as cp
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tests"))
import bench_gpu_direct as bg  # noqa: E402
import simp  # noqa: E402


def main():
    nx = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    P = bg.problem(nx)
    S = simp.SIMP(P, simp.Settings(linear="cudss"))
    x = np.full(S.act.size, P.volfrac)
    S._lam_prev = None
    S._move = S.s.move
    T = {"assembly+factor_gpu": 0.0}; T.update(physical=0.0, solve=0.0, sens=0.0, filter_T=0.0, oc=0.0)
    s = S.s
    S.factor(S.physical(x, 1.0)[1])          # plan outside the timing
    for it in range(10):
        t = time.perf_counter(); xf, xp = S.physical(x, 1.0); T["physical"] += time.perf_counter() - t
        t = time.perf_counter(); h = S.factor(xp); cp.cuda.Device().synchronize(); T["assembly+factor_gpu"] += time.perf_counter() - t
        t = time.perf_counter(); U = S.solve(h, P.loads); T["solve"] += time.perf_counter() - t
        t = time.perf_counter(); c, ce = S.compliance_and_ce(U, P.loads); T["sens"] += time.perf_counter() - t
        t = time.perf_counter()
        dE = -s.penal * (s.E0 - s.Emin) * xp ** (s.penal - 1)
        dh = simp.heaviside_deriv(xf, 1.0, s.eta)
        dc, dv = S.HT @ (dE * ce * dh), S.HT @ dh
        T["filter_T"] += time.perf_counter() - t
        t = time.perf_counter(); x, _ = S._oc(x, dc, dv, 1.0); T["oc"] += time.perf_counter() - t
    tot = sum(T.values())
    print(f"nel={S.act.size} per-iteration total {tot / 10:.3f} s")
    for k, v in T.items():
        print(f"  {k:10s} {v / 10:.4f} s  ({100 * v / tot:.0f}%)")


if __name__ == "__main__":
    main()
