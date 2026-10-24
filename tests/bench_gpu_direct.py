"""GPU direct sparse solve (cuDSS via nvmath-python) vs CPU Pardiso-SPD on 3-D cantilever
stiffness matrices of a realistic graded design. Reports per-iteration costs (numeric
factorization + one solve; the symbolic plan is reused because the pattern is fixed),
the relative residual, and the difference from the Pardiso solution.

Usage: python tests/bench_gpu_direct.py [nelx ...]   (box nelx x nelx/2 x nelx/2)
Output: results/bench_gpu_direct_<date>.json
"""
import json
import os
import sys
import time

import cupy as cp
import cupyx.scipy.sparse as cpsp
import numpy as np
import nvmath.sparse.advanced as nsa
from scipy.sparse import triu

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import simp  # noqa: E402
import taskspec  # noqa: E402


def problem(nx):
    ny = nz = nx // 2
    spec = dict(dim=3, nelx=nx, nely=ny, nelz=nz, volfrac=0.3, domain={"type": "rect"},
                supports=[{"face": "x0", "comp": "xyz"}],
                load_cases=[{"patches": [{"face": "x1", "center": [ny / 2, nz / 2], "size": [ny / 4, nz / 4],
                                          "dir": [0, -1, 0]}]}])
    return taskspec.build(spec)


def design(S, seed=0):
    """Smooth graded density in [0.001, 1] (contrast up to 1e9 in stiffness after penalization)."""
    c = S.centers()
    rng = np.random.default_rng(seed)
    k = rng.uniform(0.5, 3.0, (3, 3))
    z = sum(np.sin(k[i, 0] * c[:, 0] / 10 + k[i, 1] * c[:, 1] / 10 + k[i, 2] * c[:, 2] / 10 + i) for i in range(3))
    return np.clip(0.5 + 0.5 * z / 3, 1e-3, 1.0)


def bench(nx, reps=3):
    P = problem(nx)
    S = simp.SIMP(P, simp.Settings(linear="pardiso_spd"))
    xp = design(S)
    K = S.stiffness(S.young(xp)).tocsr()
    K.sort_indices()
    f = P.loads[0].f[S.free]
    n = K.shape[0]
    out = dict(nelx=nx, nel=int(S.act.size), ndof_free=int(n), nnz=int(K.nnz))

    # CPU Pardiso-SPD (upper triangle), numeric factorization + solve
    tf = []
    for _ in range(reps):
        t = time.perf_counter()
        lu = simp._Pardiso(K, spd=True)
        u_cpu = lu.solve(f[:, None])[:, 0]
        tf.append(time.perf_counter() - t)
        del lu
    out["cpu_pardiso_s"] = min(tf)
    out["cpu_rel_residual"] = float(np.linalg.norm(K @ u_cpu - f) / np.linalg.norm(f))

    # GPU cuDSS: SPD, upper view; plan once, then (reset values, factorize, solve) per iteration
    Ku = triu(K, format="csr")
    Ku.sort_indices()
    Kg = cpsp.csr_matrix(Ku)
    fg = cp.asarray(f)
    opts = nsa.DirectSolverOptions(sparse_system_type=nsa.DirectSolverMatrixType.SPD,
                                   sparse_system_view=nsa.DirectSolverMatrixViewType.UPPER)
    cp.cuda.Device().synchronize()
    t = time.perf_counter()
    solver = nsa.DirectSolver(Kg, fg, options=opts, execution="cuda")
    solver.plan()
    cp.cuda.Device().synchronize()
    out["gpu_plan_s"] = time.perf_counter() - t
    tg = []
    for r in range(reps):
        Kg2 = cpsp.csr_matrix(Ku)          # fresh values each iteration (host->device copy included)
        cp.cuda.Device().synchronize()
        t = time.perf_counter()
        Kg.data[:] = Kg2.data              # in-place value update of the GPU operand; plan stays valid
        solver.factorize()
        ug = solver.solve()
        cp.cuda.Device().synchronize()
        tg.append(time.perf_counter() - t)
    u_gpu = cp.asnumpy(ug).ravel()
    # value-update check: a different design on the same pattern must be solved exactly
    K2 = S.stiffness(S.young(design(S, seed=1))).tocsr()
    K2.sort_indices()
    K2u = triu(K2, format="csr")
    K2u.sort_indices()
    assert np.array_equal(K2u.indices, Ku.indices) and np.array_equal(K2u.indptr, Ku.indptr)
    Kg.data[:] = cp.asarray(K2u.data)
    solver.factorize()
    u2 = cp.asnumpy(solver.solve()).ravel()
    out["gpu_update_rel_residual"] = float(np.linalg.norm(K2 @ u2 - f) / np.linalg.norm(f))
    out["gpu_update_vs_old_rel_diff"] = float(np.linalg.norm(u2 - u_gpu) / np.linalg.norm(u_gpu))
    solver.free()
    out["gpu_factor_solve_s"] = min(tg)
    out["gpu_rel_residual"] = float(np.linalg.norm(K @ u_gpu - f) / np.linalg.norm(f))
    out["gpu_vs_cpu_rel_diff"] = float(np.linalg.norm(u_gpu - u_cpu) / np.linalg.norm(u_cpu))
    out["compliance_rel_diff"] = float(abs(f @ u_gpu - f @ u_cpu) / abs(f @ u_cpu))
    out["gpu_mem_peak_GB"] = cp.get_default_memory_pool().total_bytes() / 1e9
    print(json.dumps(out), flush=True)
    return out


def main():
    sizes = [int(a) for a in sys.argv[1:]] or [40, 60, 80, 100]
    res = [bench(nx) for nx in sizes]
    with open(os.path.join(ROOT, "results", f"bench_gpu_direct_{time.strftime('%Y%m%d')}.json"), "w") as fh:
        json.dump(dict(note="CPU timings taken while other CPU jobs may run; see cpu_busy", results=res,
                       cpu_busy=os.environ.get("CPU_BUSY", "unknown")), fh, indent=1)


if __name__ == "__main__":
    main()
