"""Verification of irregular domains, traction patches and load-case handling.

1. Removed elements vs soft elements: an L-domain with removed elements must equal the
   limit of the full rectangle with the removed block at stiffness eps -> 0.
2. Hole volume accounting: the volume fraction is relative to the active domain only.
3. Patch traction: resultant equals the requested force; a centred patch on a symmetric
   problem gives a symmetric response; width -> small approaches the point-load response.
4. Independent load cases: c = c1 + c2, not (f1+f2)^T u.
5. Cross-evaluation: evaluate() under alternative loads equals a fresh solve.
"""
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import domains as dm  # noqa: E402
import simp2d as s2  # noqa: E402

ok = True


def check(name, cond, detail):
    global ok
    ok &= bool(cond)
    print(f"[{'PASS' if cond else 'FAIL'}] {name}: {detail}")


nelx, nely = 60, 60
nodes_l, s_l = dm.edge_nodes(nelx, nely, "left")
fix = dm.fixed_dofs(nodes_l)

# 1. L-domain: removed elements vs eps-stiffness block
act = dm.mask_l_domain(nelx, nely, 30, 30)
nodes_r, s_r = dm.segment_nodes(nelx, nely, 60, 0, 60, 30)          # right edge of the lower arm
f = dm.patch_traction(nelx, nely, nodes_r, s_r, center=15, width=10, direction=(0, -1))
xp_full = np.where(act, 1.0, 0.0)
SL = s2.SIMP2D(s2.Problem2D(nelx, nely, fix, [s2.LoadCase(f)], active=act))
cL, _ = SL.evaluate(np.ones(SL.act.size), SL.p.loads)
prev = None
for eps in (1e-4, 1e-6, 1e-8):
    SR = s2.SIMP2D(s2.Problem2D(nelx, nely, fix, [s2.LoadCase(f)]), s2.Settings(Emin=eps))
    cR, _ = SR.evaluate(xp_full, SR.p.loads)
    rel = abs(cR - cL) / cL
    check(f"L-domain removed vs Emin={eps:g}", rel < 50 * eps + 1e-9, f"cL={cL:.6f} cR={cR:.6f} rel={rel:.1e}")

# 2. hole volume accounting
act_h = dm.mask_holes(nelx, nely, [(30, 30, 10)])
SH = s2.SIMP2D(s2.Problem2D(nelx, nely, fix, [s2.LoadCase(dm.patch_traction(
    nelx, nely, *dm.edge_nodes(nelx, nely, "right"), center=30, width=10, direction=(0, -1)))],
    active=act_h, volfrac=0.4), s2.Settings(rmin=2.4))
r = SH.optimize()
check("hole volume fraction", abs(r["volfrac"] - 0.4) < 1e-3, f"active vf={r['volfrac']:.5f}; n_active={SH.act.size} of {nelx * nely}")
check("hole run converged", r["converged"], f"iters={r['n_iter']} C={r['compliance']:.4f} gray={r['grayness']:.3f}")

# 3. patch traction properties
nodes_rr, s_rr = dm.edge_nodes(nelx, nely, "right")
fp = dm.patch_traction(nelx, nely, nodes_rr, s_rr, center=30, width=8, direction=(0, -1), resultant=2.5)
check("patch resultant", abs(fp[1::2].sum() + 2.5) < 1e-12 and abs(fp[0::2].sum()) < 1e-12, f"sum fy={fp[1::2].sum():.12f}")
ny = nely + 1
prof = fp[2 * nodes_rr + 1]
check("centred patch symmetric", np.allclose(prof, prof[::-1], atol=1e-12), "nodal profile mirror-symmetric")
Sfull = s2.SIMP2D(s2.Problem2D(nelx, nely, fix, [s2.LoadCase(fp)]))
xp1 = np.ones(Sfull.act.size)
fpt = np.zeros_like(fp)
fpt[2 * s2.node_id(nely, nelx, 30) + 1] = -2.5
cs = []
for w in (8, 4, 2):
    fw = dm.patch_traction(nelx, nely, nodes_rr, s_rr, center=30, width=w, direction=(0, -1), resultant=2.5)
    cs.append(Sfull.evaluate(xp1, [s2.LoadCase(fw)])[0])
cpt = Sfull.evaluate(xp1, [s2.LoadCase(fpt)])[0]
check("narrowing patch approaches point load", abs(cs[2] - cpt) < abs(cs[0] - cpt),
      f"C(w=8,4,2)={np.round(cs, 6)} C(point)={cpt:.6f}")

# 4. independent load cases
f1 = dm.patch_traction(nelx, nely, nodes_rr, s_rr, center=15, width=8, direction=(0, -1))
f2 = dm.patch_traction(nelx, nely, nodes_rr, s_rr, center=45, width=8, direction=(0, 1))
lu = Sfull.factor(xp1)
c1 = Sfull.evaluate(xp1, [s2.LoadCase(f1)], lu)[0]
c2 = Sfull.evaluate(xp1, [s2.LoadCase(f2)], lu)[0]
c12 = Sfull.evaluate(xp1, [s2.LoadCase(f1), s2.LoadCase(f2)], lu)[0]
csum = Sfull.evaluate(xp1, [s2.LoadCase(f1 + f2)], lu)[0]
check("independent cases add", abs(c12 - (c1 + c2)) < 1e-10 * c12, f"c1+c2={c1 + c2:.6f} c12={c12:.6f} summed-vector={csum:.6f}")

# 5. cross-evaluation equals a fresh solve
xp_rand = np.clip(np.random.default_rng(3).random(Sfull.act.size), 0, 1)
lu_r = Sfull.factor(xp_rand)
c_cross = Sfull.evaluate(xp_rand, [s2.LoadCase(f2)], lu_r)[0]
S2 = s2.SIMP2D(s2.Problem2D(nelx, nely, fix, [s2.LoadCase(f2)]))
c_fresh = S2.evaluate(xp_rand, S2.p.loads)[0]
check("cross-evaluation = fresh solve", abs(c_cross - c_fresh) < 1e-10 * c_fresh, f"{c_cross:.10f} vs {c_fresh:.10f}")

print("ALL PASS" if ok else "SOME FAILED")
