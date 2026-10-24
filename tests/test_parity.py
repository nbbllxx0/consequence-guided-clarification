"""Parity of the new vectorized solver (src/simp2d.py) with the AutoSiMP solver.

The old code is imported read-only. Both run with identical inputs, using the old
exact (spsolve) path, not its AMG-CG path:
  1. one-step parity: filter, projection, compliance, OC update from a random design;
  2. trajectory parity: a fixed schedule on all 17 benchmark boundary conditions.
Passive regions are not compared: the old code applied them by monkey-patching.
Writes results/parity_<date>.json.
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OLD = os.environ.get("AUTOSIMP_DIR", os.path.join(os.path.dirname(ROOT), "AutoSiMP_full_implementation"))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(1, OLD)

import simp2d as new  # noqa: E402
import pub_simp_solver as old  # noqa: E402
from bc_generator import generate_bc  # noqa: E402
from run_experiments import PROBLEM_SET  # noqa: E402

PENAL, RMIN, MOVE, ETA, VF_OVERRIDE = 3.0, 1.5, 0.2, 0.5, None
SCHED = ((1.0, 20), (2.0, 20), (4.0, 20), (8.0, 20))     # 80 iterations, no early stop


def old_problem(name):
    spec = PROBLEM_SET[name]
    bc = generate_bc(spec)
    return spec, bc


def new_solver(spec, bc):
    prob = new.Problem2D(nelx=spec.nelx, nely=spec.nely, fixed_dofs=np.asarray(bc.fixed_dofs),
                         loads=[new.LoadCase(np.asarray(bc.F, float))], volfrac=spec.volfrac)
    st = new.Settings(Emin=1e-9, xmin=1e-3, move=MOVE, rmin=RMIN, schedule=SCHED,
                      final_max_iter=0, oc_tol=1e-12)
    return new.SIMP2D(prob, st)


def old_step(spec, bc, rho, beta, H):
    nelx, nely = spec.nelx, spec.nely
    edof = old._edof_table_2d(nelx, nely)
    ri, ci = old._build_sparse_indices(edof)
    ndof = 2 * (nelx + 1) * (nely + 1)
    return old._fea_and_sensitivity(
        rho, PENAL, RMIN, MOVE, beta, ETA, True, H, KE_UNIT=old.KE_UNIT_2D, ke_size=8,
        volfrac=spec.volfrac, n_elem=nelx * nely, ndof=ndof, edof=edof,
        free=np.asarray(bc.free_dofs), F=np.asarray(bc.F, float), row_idx=ri, col_idx=ci,
        E0=1.0, Emin=1e-9, amg_solver=None)


def new_step(S, x, beta):
    xf, xp = S.physical(x, beta)
    lu = S.factor(xp)
    U = S.solve(lu, S.p.loads)
    c, ce = S.compliance_and_ce(U, S.p.loads)
    dE = -PENAL * (1 - 1e-9) * xp ** (PENAL - 1)
    dh = new.heaviside_deriv(xf, beta, ETA)
    xn, _ = S._oc(x, S.HT @ (dE * ce * dh), S.HT @ dh, beta)
    return c, xn, xp


def main():
    rng = np.random.default_rng(20261022)
    out = {"settings": dict(penal=PENAL, rmin=RMIN, move=MOVE, eta=ETA, schedule=SCHED,
                            note="old path = exact spsolve (amg_solver=None)"), "problems": {}}
    worst_c = worst_x = worst_traj = 0.0
    for name in PROBLEM_SET:
        if PROBLEM_SET[name].nelz:          # 2-D solver; 3-D cases are verified separately
            out["problems"][name] = "skipped: 3-D"
            continue
        spec, bc = old_problem(name)
        S = new_solver(spec, bc)
        H_old = old._build_density_filter(spec.nelx, spec.nely, RMIN)
        # 1) one-step parity from a random design
        x0 = np.clip(spec.volfrac + 0.2 * rng.standard_normal(spec.nelx * spec.nely), 1e-3, 1)
        c_o, xn_o, _, xp_o = old_step(spec, bc, x0.copy(), 2.0, H_old)
        c_n, xn_n, xp_n = new_step(S, x0.copy(), 2.0)
        dc = abs(c_n - c_o) / abs(c_o)
        dx = float(np.max(np.abs(xn_n - xn_o)))
        dp = float(np.max(np.abs(xp_n - xp_o)))
        # 2) trajectory parity with the same fixed schedule
        x_o = np.full(spec.nelx * spec.nely, spec.volfrac)
        hist_o, t0 = [], time.perf_counter()
        for beta, n in SCHED:
            for _ in range(n):
                c, x_o, _, _ = old_step(spec, bc, x_o, beta, H_old)
                hist_o.append(c)
        t_old = time.perf_counter() - t0
        r = S.optimize()
        hist_n = r["history"]
        traj = float(np.max(np.abs(hist_n - np.array(hist_o)) / np.abs(np.array(hist_o))))
        worst_c, worst_x, worst_traj = max(worst_c, dc), max(worst_x, dx), max(worst_traj, traj)
        out["problems"][name] = dict(nelx=spec.nelx, nely=spec.nely, step_rel_dc=dc, step_max_dx=dx,
                                     step_max_dxphys=dp, traj_max_rel_dc=traj,
                                     final_c_old=hist_o[-1], final_c_new=float(hist_n[-1]),
                                     t_old_s=t_old, t_new_s=r["wall_s"], n_iter=int(r["n_iter"]))
        print(f"{name:26s} step dc={dc:.1e} dx={dx:.1e}  traj={traj:.1e}  "
              f"c_old={hist_o[-1]:.4f} c_new={hist_n[-1]:.4f}  t_old={t_old:5.1f}s t_new={r['wall_s']:5.1f}s")
    out["worst"] = dict(step_rel_dc=worst_c, step_max_dx=worst_x, traj_max_rel_dc=worst_traj)
    print("WORST", out["worst"])
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    with open(os.path.join(ROOT, "results", "parity_20261022.json"), "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
