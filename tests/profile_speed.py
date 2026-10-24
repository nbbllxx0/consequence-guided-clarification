"""Time one production run (pilot settings) and split the cost by stage."""
import cProfile
import os
import pstats
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import simp2d as s2  # noqa: E402

nelx, nely = 120, 60
ndof = 2 * (nelx + 1) * (nely + 1)
j = np.arange(nely + 1)
fixed = np.concatenate([2 * j, 2 * j + 1])          # left edge clamped
f = np.zeros(ndof)
f[2 * s2.node_id(nely, nelx, nely // 2) + 1] = -1.0
prob = s2.Problem2D(nelx, nely, fixed, [s2.LoadCase(f)], volfrac=0.4)
S = s2.SIMP2D(prob, s2.Settings(rmin=0.04 * nely))
pr = cProfile.Profile()
pr.enable()
r = S.optimize()
pr.disable()
print(f"iters={r['n_iter']} converged={r['converged']} C={r['compliance']:.4f} gray={r['grayness']:.4f} "
      f"wall={r['wall_s']:.1f}s  per-iter={1000 * r['wall_s'] / r['n_iter']:.1f} ms")
pstats.Stats(pr).sort_stats("cumulative").print_stats(14)
