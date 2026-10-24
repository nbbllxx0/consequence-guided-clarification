"""Consequence computation: design library, cross-evaluation, certified regret lower bounds.

Key fact (notes/method_v1.md): for every interpretation t and library D,
    V_t <= U_t = min_{e in D, feasible for t} C_t(e),
so  l(d, t) >= C_t(d)/U_t - 1 =: l_lo(d, t)  holds for any reference computed later.

Cost model: designs are evaluated per support/domain signature. One factorization of
K(d) serves every load-only interpretation with that signature (back-substitution only).
Every factorization and back-substitution is counted.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

import simp
import taskspec


@dataclass
class Counter:
    optimizations: int = 0
    factorizations: int = 0
    backsubs: int = 0
    opt_wall_s: float = 0.0

    def as_dict(self):
        return dict(optimizations=self.optimizations, factorizations=self.factorizations,
                    backsubs=self.backsubs, opt_wall_s=self.opt_wall_s)


@dataclass
class Library:
    """Designs (physical densities on the common active set) with provenance."""
    settings: dict
    designs: dict = field(default_factory=dict)      # name -> xphys (active elements)
    origin: dict = field(default_factory=dict)       # name -> interpretation id or tag
    counter: Counter = field(default_factory=Counter)
    _solvers: dict = field(default_factory=dict)     # support signature -> SIMP
    _cache: dict = field(default_factory=dict)       # (design, interp_key) -> compliance

    def solver_for(self, spec):
        sig = taskspec.support_signature(spec)
        if sig not in self._solvers:
            self._solvers[sig] = simp.SIMP(taskspec.build(spec), simp.Settings(**self.settings))
        return self._solvers[sig], sig

    def add(self, name, xphys, origin, act=None, nel=None):
        """Store a design on the full grid (NaN outside its own active set) so it can be
        evaluated under interpretations whose domain differs (removed/undefined -> void)."""
        xphys = np.asarray(xphys, float)
        if act is None:
            self.designs[name] = xphys
        else:
            full = np.full(nel, np.nan)
            full[np.asarray(act)] = xphys
            self.designs[name] = full
        self.origin[name] = origin

    def _on(self, name, S):
        """Design values on the active set of solver S (void where undefined)."""
        x = self.designs[name]
        if x.size == S.p.nel:                 # stored on the full grid (NaN outside its own domain)
            v = x[S.act]
        elif x.size == S.act.size:
            v = x
        else:
            raise ValueError("design grid does not match interpretation grid")
        return np.where(np.isnan(v), 0.0, v)

    def feasible(self, name, spec, tol=1e-6):
        """Feasibility of a design under an interpretation: volume over that domain, and the
        interpretation's passive solid elements present (density >= 0.99)."""
        S, _ = self.solver_for(spec)
        x = self._on(name, S)
        solid = S.solid[S.act]
        if solid.any() and x[solid].min() < 0.99:
            return False
        return x.mean() <= spec["volfrac"] * (1 + tol) + 1e-12

    def evaluate(self, names, interps):
        """Compliance matrix C[d, t] for designs `names` under interpretations {key: spec}.

        Groups interpretations by support signature; one factorization per (design, group).
        Cached; only new pairs are charged.
        """
        keys = list(interps)
        C = np.full((len(names), len(keys)), np.nan)
        groups = {}
        for j, k in enumerate(keys):
            groups.setdefault(taskspec.support_signature(interps[k]), []).append(j)
        for i, n in enumerate(names):
            for sig, js in groups.items():
                todo = [j for j in js if (n, keys[j]) not in self._cache]
                if todo:
                    S, _ = self.solver_for(interps[keys[todo[0]]])
                    xp = self._on(n, S)
                    lu = S.factor(xp)
                    self.counter.factorizations += 1
                    loads = []
                    owners = []
                    for j in todo:
                        P = taskspec.build(interps[keys[j]])
                        owners.append((j, len(loads), len(P.loads)))
                        loads.extend(P.loads)
                    U = S.solve(lu, loads)
                    self.counter.backsubs += len(loads)
                    for j, a, m in owners:
                        c = 0.0
                        for q in range(a, a + m):
                            c += loads[q].weight * float(loads[q].f @ U[:, q])
                        self._cache[(n, keys[j])] = c
                for j in js:
                    C[i, j] = self._cache[(n, keys[j])]
        return C


def lower_bound_loss(C, feasible=None):
    """l_lo[d, t] = C[d, t] / min_e C[e, t] - 1 over feasible library designs."""
    Cm = np.where(feasible, C, np.inf) if feasible is not None else C
    U = Cm.min(0)
    return C / U[None, :] - 1.0, U


def worst_case_commit(L):
    """Design minimizing the worst-case loss over interpretations: (index, value)."""
    w = np.nanmax(L, 1)
    i = int(np.nanargmin(w))
    return i, float(w[i])
