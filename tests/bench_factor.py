"""Compare sparse factorization options for the SPD 2-D stiffness (120x60)."""
import os
import sys
import time

import numpy as np
from scipy.sparse.linalg import splu

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import simp2d as s2  # noqa: E402

nelx, nely = 120, 60
ndof = 2 * (nelx + 1) * (nely + 1)
j = np.arange(nely + 1)
f = np.zeros(ndof)
f[2 * s2.node_id(nely, nelx, nely // 2) + 1] = -1.0
S = s2.SIMP2D(s2.Problem2D(nelx, nely, np.concatenate([2 * j, 2 * j + 1]), [s2.LoadCase(f)]))
rng = np.random.default_rng(0)
xp = np.clip(rng.random(S.act.size), 0, 1)
K = S.stiffness(S.young(xp))
b = f[S.free]
ref = splu(K).solve(b)
cfgs = {
    "default": {},
    "MMD_AT_PLUS_A": dict(permc_spec="MMD_AT_PLUS_A"),
    "MMD_AT_PLUS_A+sym+nopivot": dict(permc_spec="MMD_AT_PLUS_A", diag_pivot_thresh=0.0,
                                      options=dict(SymmetricMode=True)),
    "COLAMD+sym+nopivot": dict(permc_spec="COLAMD", diag_pivot_thresh=0.0, options=dict(SymmetricMode=True)),
}
for name, kw in cfgs.items():
    ts = []
    for _ in range(5):
        t = time.perf_counter()
        lu = splu(K, **kw)
        ts.append(time.perf_counter() - t)
    x = lu.solve(b)
    err = np.linalg.norm(x - ref) / np.linalg.norm(ref)
    print(f"{name:28s} factor {1000 * np.median(ts):6.1f} ms  nnz(L+U)={lu.L.nnz + lu.U.nnz:9d}  rel.err={err:.1e}")
print("cpu cores:", os.cpu_count())
