"""3-D verification of src/simp.py.

1. H8 element matrix equals AutoSiMP's KE_UNIT_3D / 2 (AutoSiMP used a cube of side 2).
2. Analytic bar: uniaxial tension of a prism with symmetry (roller) supports gives
   C = F^2 L / (E A) exactly for trilinear elements (uniform stress state).
3. One-step parity vs AutoSiMP's exact 3-D path: compliance ratio 1/2, identical OC update.
4. Linear backends agree (SuperLU, Pardiso general, Pardiso SPD).
5. Pardiso SPD factorization time vs mesh size (results/timing_3d_<date>.json).
"""
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(1, os.environ.get("AUTOSIMP_DIR", os.path.join(os.path.dirname(ROOT), "AutoSiMP_full_implementation")))
import simp  # noqa: E402
import pub_simp_solver as old  # noqa: E402

ok = True
out = {}


def check(name, cond, detail):
    global ok
    ok &= bool(cond)
    print(f"[{'PASS' if cond else 'FAIL'}] {name}: {detail}")


# 1. element matrix
KE = simp.ke_h8(0.3)
err = np.max(np.abs(KE - old.KE_UNIT_3D / 2)) / np.max(np.abs(KE))
check("H8 KE = AutoSiMP KE/2", err < 1e-12, f"max rel diff {err:.1e}; symmetric={np.allclose(KE, KE.T)}")
ev = np.linalg.eigvalsh(KE)
check("H8 KE has 6 rigid modes", np.sum(np.abs(ev) < 1e-10) == 6, f"{np.sum(np.abs(ev) < 1e-10)} zero eigenvalues")


# 2. analytic bar: L along x, cross-section ny x nz; x=0 face u_x=0, plus symmetry planes y=0 (u_y=0), z=0 (u_z=0)
def bar(nelx, nely, nelz, F=1.0, nu=0.3):
    p = simp.Problem(nelx, nely, np.array([], int), [], nelz=nelz, nu=nu)
    nid = lambda ix, iy, iz: simp.node_id(nely, ix, iy, iz, nelz)  # noqa: E731
    iy, iz = np.meshgrid(np.arange(nely + 1), np.arange(nelz + 1), indexing="ij")
    fixed = list(3 * nid(0, iy, iz).ravel())                          # u_x = 0 on x=0
    ix, iz2 = np.meshgrid(np.arange(nelx + 1), np.arange(nelz + 1), indexing="ij")
    fixed += list(3 * nid(ix, 0, iz2).ravel() + 1)                   # u_y = 0 on y=0
    ix, iy2 = np.meshgrid(np.arange(nelx + 1), np.arange(nely + 1), indexing="ij")
    fixed += list(3 * nid(ix, iy2, 0).ravel() + 2)                   # u_z = 0 on z=0
    f = np.zeros(p.ndof)
    # consistent nodal loads of a uniform traction on x = L face (bilinear quads)
    w = np.zeros((nely + 1, nelz + 1))
    for a in range(nely):
        for b in range(nelz):
            w[a:a + 2, b:b + 2] += 0.25
    f[3 * nid(nelx, iy, iz).ravel()] = (F / (nely * nelz)) * w.ravel()
    p.fixed_dofs = np.unique(fixed)
    p.loads = [simp.LoadCase(f)]
    S = simp.SIMP(p, simp.Settings(linear="superlu"))
    c, _ = S.evaluate(np.ones(S.act.size), p.loads)
    return c, F ** 2 * nelx / (nely * nelz)


for dims in [(8, 2, 3), (12, 4, 4)]:
    c, ca = bar(*dims)
    check(f"analytic bar {dims}", abs(c - ca) / ca < 1e-10, f"C={c:.12f} exact={ca:.12f}")

# 3. one-step parity with AutoSiMP 3-D exact path (cantilever preset)
nx, ny, nz = 16, 8, 8
fixed_o, free_o, F_o = old._bc_cantilever_3d(nx, ny, nz)
H_old = old._build_density_filter(nx, ny, 1.5, nz)
edof_o = old._edof_table_3d(nx, ny, nz)
ri, ci = old._build_sparse_indices(edof_o)
rng = np.random.default_rng(7)
x0 = np.clip(0.4 + 0.2 * rng.standard_normal(nx * ny * nz), 1e-3, 1)
c_o, xn_o, _, xp_o = old._fea_and_sensitivity(
    x0.copy(), 3.0, 1.5, 0.2, 2.0, 0.5, True, H_old, KE_UNIT=old.KE_UNIT_3D, ke_size=24, volfrac=0.4,
    n_elem=nx * ny * nz, ndof=3 * (nx + 1) * (ny + 1) * (nz + 1), edof=edof_o, free=free_o, F=F_o,
    row_idx=ri, col_idx=ci, E0=1.0, Emin=1e-9, amg_solver=None)
p = simp.Problem(nx, ny, fixed_o, [simp.LoadCase(F_o.astype(float))], volfrac=0.4, nelz=nz)
S = simp.SIMP(p, simp.Settings(Emin=1e-9, xmin=1e-3, move=0.2, rmin=1.5, oc_tol=1e-12, linear="superlu"))
c_n, dc, dv, xp_n, _ = S.gradient(x0.copy(), 2.0)
xn_n, _ = S._oc(x0.copy(), dc, dv, 2.0)
check("3-D compliance = 2 x AutoSiMP (unit vs side-2 cube)", abs(c_n / c_o - 2) < 1e-9, f"ratio={c_n / c_o:.12f}")
check("3-D physical density identical", np.max(np.abs(xp_n - xp_o)) < 1e-12, f"{np.max(np.abs(xp_n - xp_o)):.1e}")
check("3-D OC update identical", np.max(np.abs(xn_n - xn_o)) < 1e-8, f"{np.max(np.abs(xn_n - xn_o)):.1e}")

# 4. backends agree
nx, ny, nz = 24, 12, 12
fixed, _, F = old._bc_cantilever_3d(nx, ny, nz)
xr = np.clip(rng.random(nx * ny * nz), 0, 1)
sols = {}
for lin in ("superlu", "pardiso", "pardiso_spd"):
    S = simp.SIMP(simp.Problem(nx, ny, fixed, [simp.LoadCase(F.astype(float))], nelz=nz), simp.Settings(linear=lin))
    c, U = S.evaluate(xr, S.p.loads)
    sols[lin] = (c, U[:, 0], S.residual(xr, U, S.p.loads))
ref = sols["superlu"][1]
for lin, (c, u, res) in sols.items():
    d = np.linalg.norm(u - ref) / np.linalg.norm(ref)
    check(f"backend {lin}", d < 1e-8 and res < 1e-8, f"C={c:.10f} |du|/|u|={d:.1e} residual={res:.1e}")

# 5. Pardiso SPD factorization timing
timing = {}
for (nx, ny, nz) in [(32, 16, 16), (48, 24, 24), (64, 32, 32), (80, 40, 40), (96, 48, 48)]:
    fixed, _, F = old._bc_cantilever_3d(nx, ny, nz)
    S = simp.SIMP(simp.Problem(nx, ny, fixed, [simp.LoadCase(F.astype(float))], nelz=nz),
                  simp.Settings(linear="pardiso_spd"))
    xr = np.clip(np.random.default_rng(1).random(S.act.size), 0, 1)
    ts = []
    for _ in range(3):
        t = time.perf_counter()
        lu = S.factor(xr)
        ts.append(time.perf_counter() - t)
        t2 = time.perf_counter()
        U = S.solve(lu, S.p.loads)
        tsolve = time.perf_counter() - t2
        del lu
    t = time.perf_counter()
    S.gradient(xr, 4.0)
    tgrad = time.perf_counter() - t
    timing[f"{nx}x{ny}x{nz}"] = dict(nel=S.act.size, ndof_free=int(S.free.size), factor_s=float(np.median(ts)),
                                     solve_s=tsolve, gradient_s=tgrad)
    print(f"  {nx}x{ny}x{nz}: nel={S.act.size:7d} dof={S.free.size:8d} factor={np.median(ts):6.2f}s "
          f"solve={tsolve:5.2f}s full-gradient={tgrad:6.2f}s")
out["timing"] = timing
with open(os.path.join(ROOT, "results", "timing_3d_20261022.json"), "w") as fh:
    json.dump(out, fh, indent=1)
print("ALL PASS" if ok else "SOME FAILED")
