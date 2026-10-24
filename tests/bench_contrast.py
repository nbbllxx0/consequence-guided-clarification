"""SuperLU cost on a real high-contrast optimized design vs a random field;
default pivoting vs SPD mode (diag_pivot_thresh=0, SymmetricMode)."""
import glob, json, os, sys, time
os.environ["OMP_NUM_THREADS"] = os.environ["MKL_NUM_THREADS"] = "1"
import numpy as np
from scipy.sparse.linalg import splu
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src")); sys.path.insert(0, os.path.join(ROOT, "experiments"))
import e01_controlled_sweeps as e, simp, taskspec, runner
spec = e.track_specs("mbb_full")["center"][1][4]
recs = [json.load(open(f)) for f in glob.glob(os.path.join(ROOT, "results/runs/*.json"))]
rec = [r for r in recs if r["spec"] == spec][0]
xp_opt, _ = runner.load_design(rec["key"])
S = simp.SIMP(taskspec.build(spec), simp.Settings(rmin=2.4))
xp_rand = np.clip(np.random.default_rng(0).random(S.act.size), 0, 1)
b = S.p.loads[0].f[S.free]
for name, xp in (("random", xp_rand), ("optimized", xp_opt)):
    K = S.stiffness(S.young(xp))
    for mode, kw in (("default-pivot", dict(permc_spec="MMD_AT_PLUS_A")),
                     ("spd-nopivot", dict(permc_spec="MMD_AT_PLUS_A", diag_pivot_thresh=0.0, options=dict(SymmetricMode=True)))):
        ts = []
        for _ in range(3):
            t = time.perf_counter(); lu = splu(K, **kw); ts.append(time.perf_counter() - t)
        x = lu.solve(b); res = np.linalg.norm(K @ x - b) / np.linalg.norm(b)
        print(f"{name:9s} {mode:14s} factor {1000*np.median(ts):7.1f} ms  nnz(LU)={lu.L.nnz+lu.U.nnz:8d}  residual={res:.1e}")
