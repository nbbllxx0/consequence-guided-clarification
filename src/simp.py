"""Vectorized three-field SIMP for 2-D (Q4, plane stress) and 3-D (H8) linear elasticity.

Infrastructure for the consequence-guided clarification study:

* genuine irregular domains: elements outside ``active`` are removed (no stiffness, no
  volume, excluded from the filter); nodes used only by removed elements carry no DOFs;
* independent load cases: compliance = sum_k w_k f_k^T u_k with separate states;
* one factorization per stiffness matrix, reused for every right-hand side, so a design
  can be cross-evaluated under alternative load models at back-substitution cost;
* explicit continuation schedule, convergence test and acceptance diagnostics.

Numbering follows the AutoSiMP solver. 2-D: e = ex*nely + ey, node n = ix*(nely+1)+iy.
3-D: e = (ex*nely + ey)*nelz + ez, node n = (ix*(nely+1) + iy)*(nelz+1) + iz.
Unit cubic/square elements; physical lengths are in element widths.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
from scipy.sparse import csc_matrix, csr_matrix, triu
from scipy.sparse.linalg import splu
from scipy.spatial import cKDTree

try:
    from pypardiso import PyPardisoSolver
    HAVE_PARDISO = True
except ImportError:  # pragma: no cover
    HAVE_PARDISO = False


# ---------------------------------------------------------------- element matrices
def ke_q4(nu=0.3):
    gp = 1.0 / np.sqrt(3.0)
    D = 1.0 / (1 - nu ** 2) * np.array([[1, nu, 0], [nu, 1, 0], [0, 0, (1 - nu) / 2]])
    xn = np.array([-1, 1, 1, -1], float)
    yn = np.array([-1, -1, 1, 1], float)
    KE = np.zeros((8, 8))
    for xi, et in [(-gp, -gp), (gp, -gp), (gp, gp), (-gp, gp)]:
        dNdxi = 0.25 * np.array([-(1 - et), (1 - et), (1 + et), -(1 + et)])
        dNdeta = 0.25 * np.array([-(1 - xi), -(1 + xi), (1 + xi), (1 - xi)])
        J = np.array([[dNdxi @ xn, dNdxi @ yn], [dNdeta @ xn, dNdeta @ yn]])
        Ji = np.linalg.inv(J)
        dNdx = Ji[0, 0] * dNdxi + Ji[0, 1] * dNdeta
        dNdy = Ji[1, 0] * dNdxi + Ji[1, 1] * dNdeta
        B = np.zeros((3, 8))
        B[0, 0::2] = dNdx
        B[1, 1::2] = dNdy
        B[2, 0::2] = dNdy
        B[2, 1::2] = dNdx
        KE += B.T @ D @ B * np.linalg.det(J)
    return KE


def ke_h8(nu=0.3):
    """Unit-cube trilinear hexahedron (2x2x2 Gauss), node order as AutoSiMP."""
    gp = 1.0 / np.sqrt(3.0)
    nc = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
                   [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], float)
    lam = nu / ((1 + nu) * (1 - 2 * nu))
    mu = 1 / (2 * (1 + nu))
    D = np.zeros((6, 6))
    D[:3, :3] = lam
    D[[0, 1, 2], [0, 1, 2]] = lam + 2 * mu
    D[[3, 4, 5], [3, 4, 5]] = mu
    xyz = nc * 0.5                                    # physical unit cube
    KE = np.zeros((24, 24))
    for r, s, t in nc * gp:
        dN = 0.125 * np.stack([nc[:, 0] * (1 + nc[:, 1] * s) * (1 + nc[:, 2] * t),
                               nc[:, 1] * (1 + nc[:, 0] * r) * (1 + nc[:, 2] * t),
                               nc[:, 2] * (1 + nc[:, 0] * r) * (1 + nc[:, 1] * s)], 1)
        J = dN.T @ xyz
        G = dN @ np.linalg.inv(J).T
        B = np.zeros((6, 24))
        B[0, 0::3] = G[:, 0]
        B[1, 1::3] = G[:, 1]
        B[2, 2::3] = G[:, 2]
        B[3, 0::3] = G[:, 1]
        B[3, 1::3] = G[:, 0]
        B[4, 1::3] = G[:, 2]
        B[4, 2::3] = G[:, 1]
        B[5, 0::3] = G[:, 2]
        B[5, 2::3] = G[:, 0]
        KE += B.T @ D @ B * np.linalg.det(J)
    return KE


def edof_2d(nelx, nely):
    ex = np.repeat(np.arange(nelx), nely)
    ey = np.tile(np.arange(nely), nelx)
    bl = ex * (nely + 1) + ey
    br = (ex + 1) * (nely + 1) + ey
    return np.stack([2 * bl, 2 * bl + 1, 2 * br, 2 * br + 1,
                     2 * br + 2, 2 * br + 3, 2 * bl + 2, 2 * bl + 3], 1).astype(np.int64)


def edof_3d(nelx, nely, nelz):
    nny, nnz = nely + 1, nelz + 1
    ex, ey, ez = (a.ravel() for a in np.meshgrid(np.arange(nelx), np.arange(nely), np.arange(nelz), indexing="ij"))

    def nid(ix, iy, iz):
        return (ix * nny + iy) * nnz + iz
    nodes = np.stack([nid(ex, ey, ez), nid(ex + 1, ey, ez), nid(ex + 1, ey + 1, ez), nid(ex, ey + 1, ez),
                      nid(ex, ey, ez + 1), nid(ex + 1, ey, ez + 1), nid(ex + 1, ey + 1, ez + 1),
                      nid(ex, ey + 1, ez + 1)], 1)
    return (3 * nodes[:, :, None] + np.arange(3)[None, None, :]).reshape(len(ex), 24).astype(np.int64)


def node_id(nely, ix, iy, iz=None, nelz=None):
    if iz is None:
        return ix * (nely + 1) + iy
    return (ix * (nely + 1) + iy) * (nelz + 1) + iz


def heaviside(x, beta, eta):
    if beta <= 0:
        return x.copy()
    return (np.tanh(beta * eta) + np.tanh(beta * (x - eta))) / (np.tanh(beta * eta) + np.tanh(beta * (1 - eta)))


def heaviside_deriv(x, beta, eta):
    if beta <= 0:
        return np.ones_like(x)
    return beta * (1 - np.tanh(beta * (x - eta)) ** 2) / (np.tanh(beta * eta) + np.tanh(beta * (1 - eta)))


# ---------------------------------------------------------------- problem definition
@dataclass
class LoadCase:
    f: np.ndarray
    weight: float = 1.0


@dataclass
class Problem:
    nelx: int
    nely: int
    fixed_dofs: np.ndarray
    loads: list
    volfrac: float = 0.4
    nelz: int = 0
    active: np.ndarray | None = None
    solid: np.ndarray | None = None
    void: np.ndarray | None = None
    nu: float = 0.3

    @property
    def dim(self):
        return 3 if self.nelz else 2

    @property
    def nel(self):
        return self.nelx * self.nely * (self.nelz or 1)

    @property
    def ndof(self):
        if self.nelz:
            return 3 * (self.nelx + 1) * (self.nely + 1) * (self.nelz + 1)
        return 2 * (self.nelx + 1) * (self.nely + 1)


@dataclass
class Settings:
    penal: float = 3.0
    E0: float = 1.0
    Emin: float = 1e-6
    rmin: float = 1.5
    eta: float = 0.5
    move: float = 0.1
    schedule: tuple = ((1.0, 50), (2.0, 50), (4.0, 50), (8.0, 50))
    final_beta: float = 8.0
    final_max_iter: int = 200
    final_move: float = 0.02          # move limit in the final (polishing) phase
    conv_window: int = 20
    conv_tol: float = 1e-3            # (max-min)/mean over the window; drift enters the allowance
    xmin: float = 0.0
    oc_tol: float = 1e-7
    dc_floor: float = 1e-12
    project: bool = True
    linear: str = "auto"              # "superlu" | "pardiso" | "pardiso_spd" | "cudss" | "auto"


# ---------------------------------------------------------------- linear solvers
class _SuperLU:
    def __init__(self, K):
        # K is SPD: no pivoting (diag_pivot_thresh=0, symmetric mode); same accuracy, less fill
        self.lu = splu(K, permc_spec="MMD_AT_PLUS_A", diag_pivot_thresh=0.0, options=dict(SymmetricMode=True))

    def solve(self, B):
        return self.lu.solve(B)


class _Pardiso:
    def __init__(self, K, spd):
        self.spd = spd
        self.ps = PyPardisoSolver(mtype=2 if spd else 11)
        self.ps.set_statistical_info_off()
        self.A = triu(K, format="csr") if spd else K.tocsr()
        self.A.sort_indices()
        self.ps.factorize(self.A)

    def solve(self, B):
        X = self.ps.solve(self.A, np.asarray(B, float))
        return X.reshape(B.shape)

    def __del__(self):
        try:
            self.ps.free_memory(everything=True)
        except Exception:
            pass


_ROWSUM_SRC = r"""
extern "C" __global__ void rowsum(const long long* ptr, const int* idx, const double* val,
                                  const double* x, double* out, long long n) {
    long long k = (long long)blockIdx.x * blockDim.x + threadIdx.x;
    if (k < n) {
        double s = 0.0;
        for (long long j = ptr[k]; j < ptr[k + 1]; j++) s += val[j] * x[idx[j]];
        out[k] = s;
    }
}
"""


class _CuDSS:
    """GPU sparse direct solver (NVIDIA cuDSS via nvmath-python), SPD, upper triangle.

    The sparsity pattern is fixed per SIMP instance, so reordering and symbolic analysis
    (plan) run once; each factor() uploads new values and refactorizes numerically. Only the
    most recent factorization is valid: solve() on an older handle raises."""

    def __init__(self, S):
        import cupy as cp
        import cupyx.scipy.sparse as cpsp
        import nvmath.sparse.advanced as nsa
        self.cp, self.nsa = cp, nsa
        n, nnz = S.free.size, S._nnz
        # upper-triangle CSR pattern; CSC data position -> upper CSR position (-1: lower triangle)
        pos = csc_matrix((np.arange(1, nnz + 1, dtype=float), S._indices, S._indptr), shape=(n, n))
        up = triu(pos.tocsr(), format="csr")
        up.sort_indices()
        up_of_csc = np.full(nnz, -1, np.int64)
        up_of_csc[up.data.astype(np.int64) - 1] = np.arange(up.nnz)
        csc_of_acc = np.empty(nnz, np.int64)
        csc_of_acc[S._csc_order] = np.arange(nnz)
        target = up_of_csc[csc_of_acc[S._inv]]           # per element-matrix entry
        keep = target >= 0
        # assembly on the GPU as data_up = M @ E with M[k, e] = summed element-matrix entries;
        # one thread per row sums in a fixed order, so the assembly is bitwise reproducible
        M = csr_matrix((S._ke_flat[keep], (target[keep], S._elem_of_entry[keep])), shape=(up.nnz, S.act.size))
        M.sum_duplicates()
        M.sort_indices()
        self.M_ptr, self.M_idx = cp.asarray(M.indptr.astype(np.int64)), cp.asarray(M.indices.astype(np.int32))
        self.M_val = cp.asarray(M.data)
        self.kern = cp.RawKernel(_ROWSUM_SRC, "rowsum")
        self.nup = up.nnz
        self.K = cpsp.csr_matrix((cp.zeros(up.nnz), cp.asarray(up.indices), cp.asarray(up.indptr)), shape=(n, n))
        self.n, self.solver, self.version = n, None, 0

    def factor(self, E_act):
        cp = self.cp
        E = cp.asarray(np.ascontiguousarray(E_act, dtype=float))
        threads = 256
        self.kern(((self.nup + threads - 1) // threads,), (threads,),
                  (self.M_ptr, self.M_idx, self.M_val, E, self.K.data, np.int64(self.nup)))
        if self.solver is None:
            opts = self.nsa.DirectSolverOptions(sparse_system_type=self.nsa.DirectSolverMatrixType.SPD,
                                                sparse_system_view=self.nsa.DirectSolverMatrixViewType.UPPER)
            self.solver = self.nsa.DirectSolver(self.K, cp.zeros(self.n), options=opts, execution="cuda")
            self.solver.plan()
        self.solver.factorize()
        self.version += 1
        return _CuDSSHandle(self, self.version)

    def solve(self, B, version):
        if version != self.version:
            raise RuntimeError("cuDSS handle is stale: a newer factorization replaced it")
        cp = self.cp
        B = np.asarray(B, float)
        one = B.ndim == 1
        B2 = B.reshape(self.n, -1)
        X = np.empty_like(B2)
        for j in range(B2.shape[1]):          # the RHS shape is fixed at creation: one column at a time
            self.solver.reset_operands(b=cp.asarray(B2[:, j]))
            X[:, j] = cp.asnumpy(self.solver.solve())
        return X[:, 0] if one else X

    def __del__(self):
        try:
            if self.solver is not None:
                self.solver.free()
        except Exception:
            pass


class _CuDSSHandle:
    def __init__(self, owner, version):
        self.owner, self.version = owner, version

    def solve(self, B):
        return self.owner.solve(B, self.version)


# ---------------------------------------------------------------- solver
class SIMP:
    def __init__(self, prob: Problem, st: Settings | None = None):
        self.p = prob
        self.s = st or Settings()
        nel = prob.nel
        self.active = np.ones(nel, bool) if prob.active is None else np.asarray(prob.active, bool).copy()
        self.solid = np.zeros(nel, bool) if prob.solid is None else (np.asarray(prob.solid, bool) & self.active)
        self.void = np.zeros(nel, bool) if prob.void is None else (np.asarray(prob.void, bool) & self.active)
        self.act = np.flatnonzero(self.active)
        self.fixmask = (self.solid | self.void)[self.act]
        if prob.dim == 2:
            self.KE = ke_q4(prob.nu)
            self.edof = edof_2d(prob.nelx, prob.nely)[self.act]
        else:
            self.KE = ke_h8(prob.nu)
            self.edof = edof_3d(prob.nelx, prob.nely, prob.nelz)[self.act]
        used = np.zeros(prob.ndof, bool)
        used[self.edof.ravel()] = True
        fixed = np.zeros(prob.ndof, bool)
        fixed[np.asarray(prob.fixed_dofs, int)] = True
        self.free = np.flatnonzero(used & ~fixed)
        for lc in prob.loads:
            if np.any(lc.f[~used] != 0):
                raise ValueError("load applied to a node outside the active domain")
        lin = self.s.linear
        if lin == "auto":
            lin = "pardiso_spd" if (HAVE_PARDISO and (prob.dim == 3 or self.free.size > 30000)) else "superlu"
        self.linear = lin
        self._move = self.s.move
        self._build_assembly()
        self._build_filter()

    def _build_assembly(self):
        nd, k = self.p.ndof, self.KE.shape[0]
        g2f = -np.ones(nd, np.int64)
        g2f[self.free] = np.arange(self.free.size)
        fr = g2f[np.repeat(self.edof, k, axis=1)]
        fc = g2f[np.tile(self.edof, (1, k))]
        keep = (fr >= 0) & (fc >= 0)
        nf = self.free.size
        key = fr[keep] * nf + fc[keep]
        ukey, inv = np.unique(key, return_inverse=True)
        self._inv, self._nnz = inv, ukey.size
        rows, cols = ukey // nf, ukey % nf
        order = np.lexsort((rows, cols))
        self._csc_order = order
        self._indices = rows[order].astype(np.int32)
        self._indptr = np.concatenate([[0], np.cumsum(np.bincount(cols, minlength=nf))]).astype(np.int32)
        self._ke_flat = np.broadcast_to(self.KE.ravel(), keep.shape)[keep]
        self._elem_of_entry = np.broadcast_to(np.arange(self.edof.shape[0])[:, None], keep.shape)[keep]

    def stiffness(self, E_act):
        vals = E_act[self._elem_of_entry] * self._ke_flat
        data = np.bincount(self._inv, weights=vals, minlength=self._nnz)[self._csc_order]
        nf = self.free.size
        return csc_matrix((data, self._indices, self._indptr), shape=(nf, nf))

    def centers(self):
        p = self.p
        if p.dim == 2:
            return np.stack([self.act // p.nely, self.act % p.nely], 1).astype(float) + 0.5
        ez = self.act % p.nelz
        ey = (self.act // p.nelz) % p.nely
        ex = self.act // (p.nelz * p.nely)
        return np.stack([ex, ey, ez], 1).astype(float) + 0.5

    def _build_filter(self):
        xy = self.centers()
        R = self.s.rmin
        pairs = cKDTree(xy).query_pairs(R - 1e-10, output_type="ndarray")
        n = self.act.size
        if len(pairs):
            w = R - np.linalg.norm(xy[pairs[:, 0]] - xy[pairs[:, 1]], axis=1)
            rows = np.concatenate([pairs[:, 0], pairs[:, 1], np.arange(n)])
            cols = np.concatenate([pairs[:, 1], pairs[:, 0], np.arange(n)])
            vals = np.concatenate([w, w, np.full(n, R)])
        else:
            rows = cols = np.arange(n)
            vals = np.full(n, R)
        Hs = np.bincount(rows, weights=vals, minlength=n)
        self.H = csr_matrix((vals / Hs[rows], (rows, cols)), shape=(n, n))
        self.HT = self.H.T.tocsr()

    # ------------------------------------------------------------ physics
    def physical(self, x, beta):
        xf = self.H @ x
        xp = heaviside(xf, beta, self.s.eta) if self.s.project else xf.copy()
        xp[self.solid[self.act]] = 1.0
        xp[self.void[self.act]] = 0.0
        return xf, xp

    def young(self, xp):
        s = self.s
        return s.Emin + (s.E0 - s.Emin) * xp ** s.penal

    def factor(self, xp):
        if self.linear == "cudss":
            if getattr(self, "_gpu", None) is None:
                self._gpu = _CuDSS(self)
            return self._gpu.factor(self.young(xp))
        K = self.stiffness(self.young(xp))
        if self.linear == "superlu":
            return _SuperLU(K)
        return _Pardiso(K, spd=(self.linear == "pardiso_spd"))

    def solve(self, lu, loads):
        F = np.stack([lc.f[self.free] for lc in loads], 1)
        U = np.zeros((self.p.ndof, len(loads)))
        U[self.free] = lu.solve(F)
        return U

    def compliance_and_ce(self, U, loads):
        c = 0.0
        ce = np.zeros(self.act.size)
        for k, lc in enumerate(loads):
            u = U[:, k]
            c += lc.weight * float(lc.f @ u)
            ue = u[self.edof]
            ce += lc.weight * np.einsum("ei,ei->e", ue @ self.KE, ue)
        return c, ce

    def evaluate(self, xp, loads, lu=None):
        if lu is None:
            lu = self.factor(xp)
        U = self.solve(lu, loads)
        return self.compliance_and_ce(U, loads)[0], U

    def residual(self, xp, U, loads):
        """True relative equilibrium residual max_k ||K u_k - f_k|| / ||f_k|| on free DOFs."""
        K = self.stiffness(self.young(xp))
        r = 0.0
        for k, lc in enumerate(loads):
            fk = lc.f[self.free]
            r = max(r, float(np.linalg.norm(K @ U[self.free, k] - fk) / max(np.linalg.norm(fk), 1e-300)))
        return r

    # ------------------------------------------------------------ optimization
    def _oc(self, x, dc, dv, beta):
        s = self.s
        dc = np.minimum(dc, -s.dc_floor)
        dv = np.maximum(dv, s.dc_floor)
        vol_target = self.p.volfrac * self.act.size
        mv = self._move
        lo_b = np.maximum(s.xmin, x - mv)
        hi_b = np.minimum(1.0, x + mv)
        # bracket the multiplier around the previous value (warm start), expanding if needed
        lp = getattr(self, "_lam_prev", None)
        if lp is not None and np.isfinite(lp) and lp > 0:
            l1, l2 = lp / 4, lp * 4

            def vol(lm):
                xn = np.where(self.fixmask, x, np.clip(x * np.sqrt(-dc / (lm * dv)), lo_b, hi_b))
                return self.physical(xn, beta)[1].sum()
            while l1 > 1e-300 and vol(l1) <= vol_target:
                l1 /= 4
            while l2 < 1e300 and vol(l2) > vol_target:
                l2 *= 4
        else:
            l1, l2 = 0.0, 1e9
        xnew = x
        while (l2 - l1) / (l1 + l2 + 1e-300) > s.oc_tol:
            lm = 0.5 * (l1 + l2)
            xn = np.clip(x * np.sqrt(-dc / (lm * dv)), lo_b, hi_b)
            xnew = np.where(self.fixmask, x, xn)
            if self.physical(xnew, beta)[1].sum() > vol_target:
                l1 = lm
            else:
                l2 = lm
        self._lam_prev = 0.5 * (l1 + l2)
        return xnew, 0.5 * (l1 + l2)

    def gradient(self, x, beta, lu=None):
        """Compliance, design gradient dc/dx, volume gradient dv/dx, physical density."""
        s, p = self.s, self.p
        xf, xp = self.physical(x, beta)
        if lu is None:
            lu = self.factor(xp)
        U = self.solve(lu, p.loads)
        c, ce = self.compliance_and_ce(U, p.loads)
        dE = -s.penal * (s.E0 - s.Emin) * xp ** (s.penal - 1)
        dh = heaviside_deriv(xf, beta, s.eta) if s.project else np.ones_like(xf)
        dh = np.where(self.fixmask, 0.0, dh)
        return c, self.HT @ (dE * ce * dh), self.HT @ dh, xp, U

    def kkt_residual(self, x, beta, lam=None):
        """Projected-gradient stationarity of min c s.t. mean(xp) <= vf, 0 <= x <= 1.

        g = dc + lam*dv with lam from the OC update (or least squares on clearly interior
        variables); r = max_i |x_i - clip(x_i - g_i/s, 0, 1)| over free variables, with
        s = max|dc| (dimensionless; 0 at a KKT point).
        """
        c, dc, dv, xp, _ = self.gradient(x, beta)
        free = ~self.fixmask
        if lam is None:
            interior = free & (x > 0.05) & (x < 0.95)
            lam = -float(dc[interior] @ dv[interior] / max(dv[interior] @ dv[interior], 1e-300)) if interior.any() else 0.0
        g = dc + lam * dv
        sc = max(np.max(np.abs(dc[free])), 1e-300)
        r = np.abs(x - np.clip(x - g / sc, 0.0, 1.0))
        return float(np.max(r[free])), lam

    def optimize(self, x0=None, record=False):
        s, p = self.s, self.p
        t0 = time.perf_counter()
        self._lam_prev = None
        x = np.full(self.act.size, p.volfrac) if x0 is None else np.asarray(x0, float).copy()
        x[self.solid[self.act]] = 1.0
        x[self.void[self.act]] = 0.0
        phases = list(s.schedule) + [(s.final_beta, s.final_max_iter)]
        hist, betas = [], []
        converged = False
        lam = np.nan
        it = 0
        for ip, (beta, n_it) in enumerate(phases):
            last = ip == len(phases) - 1
            self._move = s.final_move if last else s.move
            for _ in range(n_it):
                it += 1
                c, dc, dv, xp, _ = self.gradient(x, beta)
                hist.append(c)
                betas.append(beta)
                x, lam = self._oc(x, dc, dv, beta)
                if last and len(hist) >= s.conv_window + 1:
                    w = np.array(hist[-s.conv_window:])
                    if (w.max() - w.min()) / abs(w.mean()) < s.conv_tol:
                        converged = True
                        break
            if converged:
                break
        beta = betas[-1]
        xf, xp = self.physical(x, beta)
        lu = self.factor(xp)
        U = self.solve(lu, p.loads)
        c, _ = self.compliance_and_ce(U, p.loads)
        out = dict(x=x, xphys=xp, compliance=c, history=np.array(hist), betas=np.array(betas),
                   n_iter=it, converged=converged, oc_multiplier=lam, beta=beta,
                   volfrac=float(xp.sum() / self.act.size), wall_s=time.perf_counter() - t0,
                   grayness=float(4 * np.mean(xp * (1 - xp))), linear=self.linear,
                   residual=self.residual(xp, U, p.loads))
        if record:
            out["U"] = U
            out["lu"] = lu
        return out
