"""Locate where the bridge trajectories of old and new solvers diverge, and test whether
the OC bisection tolerance (old: absolute 1e-9 on lambda) explains it."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import test_parity as tp  # noqa: E402

spec, bc = tp.old_problem("bridge_120x30")
H_old = tp.old._build_density_filter(spec.nelx, spec.nely, tp.RMIN)


def run_old():
    x = np.full(spec.nelx * spec.nely, spec.volfrac)
    hist = []
    for beta, n in tp.SCHED:
        for _ in range(n):
            c, x, _, _ = tp.old_step(spec, bc, x, beta, H_old)
            hist.append(c)
    return np.array(hist)


def run_new(absolute):
    S = tp.new_solver(spec, bc)
    if absolute:
        orig = S._oc

        def oc_abs(x, dc, dv, beta, S=S):
            s = S.s
            fd = np.isin(S.act, S.free_design, assume_unique=True)
            dc = np.minimum(dc, -1e-12)
            dv = np.maximum(dv, 1e-12)
            l1, l2 = 0.0, 1e9
            xnew = x
            for _ in range(100):
                lm = 0.5 * (l1 + l2)
                xn = np.clip(x * np.sqrt(-dc / (lm * dv)), np.maximum(s.xmin, x - s.move), np.minimum(1, x + s.move))
                xnew = np.where(fd, xn, x)
                if S.physical(xnew, beta)[1].sum() / S.act.size > S.p.volfrac:
                    l1 = lm
                else:
                    l2 = lm
                if l2 - l1 < 1e-9:
                    break
            return xnew, lm
        S._oc = oc_abs
    return S.optimize()["history"], S


ho = run_old()
for absolute in (False, True):
    hn, S = run_new(absolute)
    rel = np.abs(hn - ho) / np.abs(ho)
    first = int(np.argmax(rel > 1e-6)) if np.any(rel > 1e-6) else None
    print(f"absolute_oc={absolute}: first iter rel>1e-6 = {first}, max rel = {rel.max():.2e}, "
          f"final old {ho[-1]:.4f} new {hn[-1]:.4f}")
# lambda scale at the start
xf, xp = S.physical(np.full(S.act.size, spec.volfrac), 1.0)
print("load norm", np.linalg.norm(bc.F), " compliance at start", ho[0])
