"""No-question robust baseline: one design for all admissible interpretations.

Minimize the p-norm of reference-normalized compliances
    J(x) = ( sum_t (C_t(x) / V_t)^p )^(1/p),  p = 16 (smooth approximation of the max),
over interpretations that share the design domain (same active set). Interpretations are
grouped by support signature: one factorization per group per iteration, one
back-substitution per interpretation. Same filter, projection, schedule and OC update as
simp.SIMP; dJ/dx is a positive combination of compliance sensitivities, so OC applies.
Volume constraint: the smallest volume fraction among the interpretations (feasible for all).
"""
from __future__ import annotations

import time

import numpy as np

import simp
import taskspec


class RobustSIMP:
    def __init__(self, specs, refs, settings: dict, p=16.0):
        self.specs = list(specs)
        self.V = np.asarray(refs, float)
        self.p = p
        self.groups = {}
        for i, s in enumerate(self.specs):
            self.groups.setdefault(taskspec.support_signature(s), []).append(i)
        self.solvers = {}
        for sig, idx in self.groups.items():
            prob = taskspec.build(self.specs[idx[0]])
            self.solvers[sig] = simp.SIMP(prob, simp.Settings(**settings))
        acts = [S.act for S in self.solvers.values()]
        if any(not np.array_equal(a, acts[0]) for a in acts):
            raise ValueError("robust baseline requires a common active set")
        self.S0 = next(iter(self.solvers.values()))
        self.S0.p.volfrac = min(s["volfrac"] for s in self.specs)
        self.loads = [taskspec.build(s).loads for s in self.specs]

    def objective(self, x, beta):
        S0, s = self.S0, self.S0.s
        xf, xp = S0.physical(x, beta)
        Cs = np.zeros(len(self.specs))
        ces = []
        for sig, idx in self.groups.items():
            S = self.solvers[sig]
            lu = S.factor(xp)
            for i in idx:
                U = S.solve(lu, self.loads[i])
                c, ce = S.compliance_and_ce(U, self.loads[i])
                Cs[i] = c
                ces.append((i, ce))
        r = Cs / self.V
        J = float(np.sum(r ** self.p) ** (1 / self.p))
        w = (r / J) ** (self.p - 1) / self.V            # dJ/dC_t
        ce_tot = np.zeros(S0.act.size)
        for i, ce in ces:
            ce_tot += w[i] * ce
        dE = -s.penal * (s.E0 - s.Emin) * xp ** (s.penal - 1)
        dh = simp.heaviside_deriv(xf, beta, s.eta) if s.project else np.ones_like(xf)
        dh = np.where(S0.fixmask, 0.0, dh)
        return J, Cs, S0.HT @ (dE * ce_tot * dh), S0.HT @ dh, xp

    def optimize(self, x0=None):
        S0, s = self.S0, self.S0.s
        t0 = time.perf_counter()
        S0._lam_prev = None
        x = np.full(S0.act.size, S0.p.volfrac) if x0 is None else np.asarray(x0, float).copy()
        phases = list(s.schedule) + [(s.final_beta, s.final_max_iter)]
        hist, it, conv = [], 0, False
        for ip, (beta, n) in enumerate(phases):
            last = ip == len(phases) - 1
            S0._move = s.final_move if last else s.move
            for _ in range(n):
                it += 1
                J, Cs, dJ, dv, xp = self.objective(x, beta)
                hist.append(J)
                x, _ = S0._oc(x, dJ, dv, beta)
                if last and len(hist) > s.conv_window:
                    w = np.array(hist[-s.conv_window:])
                    if (w.max() - w.min()) / abs(w.mean()) < s.conv_tol:
                        conv = True
                        break
            if conv:
                break
        J, Cs, _, _, xp = self.objective(x, beta)
        return dict(xphys=xp, J=J, C=Cs, ratio=Cs / self.V, n_iter=it, converged=conv,
                    wall_s=time.perf_counter() - t0, act=S0.act)
