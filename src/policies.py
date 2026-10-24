"""Clarification policies replayed against a hidden intended interpretation.

Task model: slots s with finite admissible node values; an interpretation is one value per
slot (restricted to `admissible` combinations). Mandatory slots must be asked. A question
asks one slot and returns its true value (exact-answer replay; no human-time claim).

Each policy returns: asked slots, committed design name, number of optimizations it
requested (charged), factorizations/back-substitutions it caused, and the outcome loss
under the hidden interpretation, computed by the offline evaluator from an exhaustive
reference table that the policy never sees.

Oracle cost model (`Oracle`): optimizations are precomputed offline (runner cache) but a
policy is charged once per interpretation whose reference it requests.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Task:
    name: str
    slots: dict                      # slot -> list of values
    nominal: dict                    # slot -> nominal value (what a silent default would pick)
    mandatory: tuple = ()            # slots that must be asked regardless of consequence
    admissible: list | None = None   # optional explicit list of interpretations (dicts)

    def interpretations(self):
        if self.admissible is not None:
            return [dict(a) for a in self.admissible]
        names = list(self.slots)
        return [dict(zip(names, v)) for v in itertools.product(*[self.slots[n] for n in names])]


def ikey(interp):
    return "|".join(f"{k}={interp[k]}" for k in sorted(interp))


@dataclass
class Oracle:
    """Offline exhaustive data: reference compliance per interpretation and the full
    cross table C[d_key][t_key] (design optimized for d, evaluated under t)."""
    ref: dict                        # t_key -> reference compliance (best known)
    C: dict                          # (d_key, t_key) -> compliance
    noise: dict                      # t_key -> multi-start relative spread

    def loss(self, d_key, t_key):
        return self.C[(d_key, t_key)] / self.ref[t_key] - 1.0


@dataclass
class Outcome:
    policy: str
    asked: list
    commit: str | None
    released: bool
    optimizations: int
    cross_evals: int
    true_loss: float
    false_release: bool
    extra: dict = field(default_factory=dict)


def _surviving(interps, answers):
    return [t for t in interps if all(t[k] == v for k, v in answers.items())]


def allowance(oracle, keys, tau):
    return {k: max(oracle.noise.get(k, 0.0), 0.0) for k in keys}


# ------------------------------------------------------------------ baselines
def no_ask(task, oracle, truth, tau):
    nom = ikey(task.nominal)
    tk = ikey(truth)
    L = oracle.loss(nom, tk)
    return Outcome("no_ask", [], nom, True, 1, 0, L, L > tau + oracle.noise.get(tk, 0))


def ask_all(task, oracle, truth, tau):
    ambiguous = list(task.mandatory) + [s for s, v in task.slots.items() if len(v) > 1 and s not in task.mandatory]
    tk = ikey(truth)
    return Outcome("ask_all", ambiguous, tk, True, 1, 0, oracle.loss(tk, tk), False)


def ask_mandatory_then_nominal(task, oracle, truth, tau):
    """Mandatory questions, then commit to the nominal value of every other slot."""
    ans = {s: truth[s] for s in task.mandatory}
    commit = dict(task.nominal, **ans)
    ck, tk = ikey(commit), ikey(truth)
    L = oracle.loss(ck, tk)
    return Outcome("mandatory_only", list(task.mandatory), ck, True, 1, 0, L, L > tau + oracle.noise.get(tk, 0))


# ------------------------------------------------------------------ consequence policies
def _minimax_plan(task, keys_of, S, lossf, tau, allow, budget, asked):
    """Greedy worst-case question choice: ask the slot whose worst answer leaves the
    smallest best-commitment worst-case loss. Returns (slot or None, commit key, B)."""
    def best_commit(Ssub):
        cands = [ikey(t) for t in Ssub]
        worst = {c: max(lossf(c, ikey(t)) - allow.get(ikey(t), 0) for t in Ssub) for c in cands}
        c = min(worst, key=worst.get)
        return c, worst[c]
    c0, B0 = best_commit(S)
    if B0 <= tau or len(asked) >= budget:
        return None, c0, B0
    best = None
    for s in task.slots:
        if s in asked or len({t[s] for t in S}) < 2:
            continue
        wc = max(best_commit([t for t in S if t[s] == v])[1] for v in {t[s] for t in S})
        if best is None or wc < best[1]:
            best = (s, wc)
    if best is None:
        return None, c0, B0
    return best[0], c0, B0


def full_h(task, oracle, truth, tau, budget=3):
    """Consequence-guided clarification with the exact table: every interpretation's
    reference is computed up front (|Theta| optimizations)."""
    interps = task.interpretations()
    answers = {s: truth[s] for s in task.mandatory}
    asked = list(task.mandatory)
    allow = {ikey(t): oracle.noise.get(ikey(t), 0) for t in interps}
    while True:
        S = _surviving(interps, answers)
        q, commit, B = _minimax_plan(task, None, S, oracle.loss, tau, allow, budget + len(task.mandatory), asked)
        if q is None:
            break
        answers[q] = truth[q]
        asked.append(q)
    tk = ikey(truth)
    L = oracle.loss(commit, tk)
    released = B <= tau
    n_opt = len(interps)
    n_cross = len(interps) ** 2
    return Outcome("full_H", asked, commit, released, n_opt, n_cross, L,
                   released and L > tau + oracle.noise.get(tk, 0), dict(B=B))


def h_lazy(task, oracle, truth, tau, budget=3, seed_extremes=True):
    """Ours: certified screening with a small library; references only for survivors.

    Library seed = nominal + per-slot extreme interpretations (others at nominal).
    Certified lower bound l_lo(d,t) = C_t(d)/min_{e in lib} C_t(e) - 1 decides asks
    without computing references; release requires exact references for every surviving
    interpretation (computed lazily, charged).
    """
    interps = task.interpretations()
    keys = [ikey(t) for t in interps]
    answers = {s: truth[s] for s in task.mandatory}
    asked = list(task.mandatory)
    lib = {ikey(task.nominal)}
    if seed_extremes:
        for s, vals in task.slots.items():
            if len(vals) > 1:
                for v in (vals[0], vals[-1]):
                    t = dict(task.nominal, **{s: v})
                    if ikey(t) in keys:
                        lib.add(ikey(t))
    computed_refs = set()
    evals = set()

    def C(d, t):
        evals.add((d, t))
        return oracle.C[(d, t)]

    while True:
        S = _surviving(interps, answers)
        Sk = [ikey(t) for t in S]
        # certified lower bounds with the current library
        U = {t: min(C(e, t) for e in lib) for t in Sk}
        llo = {(d, t): C(d, t) / U[t] - 1 for d in lib for t in Sk}
        dstar = min(lib, key=lambda d: max(llo[(d, t)] for t in Sk))
        worst_lo = max(llo[(dstar, t)] - oracle.noise.get(t, 0) for t in Sk)
        if worst_lo > tau and len(asked) < budget + len(task.mandatory):
            # certified consequential: choose question by the lower-bound minimax plan
            q, _, _ = _minimax_plan(task, None, S, lambda d, t: C(d, t) / U[t] - 1 if d in lib else np.inf,
                                    tau, {}, budget + len(task.mandatory), asked)
            if q is None:
                break
            answers[q] = truth[q]
            asked.append(q)
            # an answered slot fixes interpretations; add the now-nominal design for survivors
            S2 = _surviving(interps, answers)
            cand = dict({s: truth[s] for s in answers}, **{s: task.nominal[s] for s in task.slots if s not in answers})
            if ikey(cand) in [ikey(t) for t in S2]:
                lib.add(ikey(cand))
            continue
        # verification: compute references for survivors not yet computed, check release
        for t in Sk:
            computed_refs.add(t)
        lib |= set(Sk)                    # their optimized designs join the library
        L_exact = {t: C(dstar, t) / oracle.ref[t] - 1 for t in Sk}
        dbest = min(lib, key=lambda d: max(C(d, t) / oracle.ref[t] - 1 - oracle.noise.get(t, 0) for t in Sk))
        B = max(C(dbest, t) / oracle.ref[t] - 1 - oracle.noise.get(t, 0) for t in Sk)
        if B <= tau or len(asked) >= budget + len(task.mandatory):
            dstar = dbest
            break
        q, _, _ = _minimax_plan(task, None, S, oracle.loss, tau, {k: oracle.noise.get(k, 0) for k in Sk},
                                budget + len(task.mandatory), asked)
        if q is None:
            dstar = dbest
            break
        answers[q] = truth[q]
        asked.append(q)
    tk = ikey(truth)
    L = oracle.loss(dstar, tk)
    Sk = [ikey(t) for t in _surviving(interps, answers)]
    B = max(oracle.loss(dstar, t) - oracle.noise.get(t, 0) for t in Sk)
    released = B <= tau
    n_opt = len(lib | computed_refs)
    return Outcome("H_lazy", asked, dstar, released, n_opt, len(evals), L,
                   released and L > tau + oracle.noise.get(tk, 0), dict(B=B, library=len(lib)))


def oracle_lookahead(task, oracle, truth, tau, budget=3):
    """Information limit: fewest questions such that the best commitment over the surviving
    set satisfies B <= tau, searching all question orders (exact table)."""
    interps = task.interpretations()
    slots = [s for s in task.slots if len(task.slots[s]) > 1 and s not in task.mandatory]
    best = None
    for k in range(0, min(budget, len(slots)) + 1):
        for subset in itertools.combinations(slots, k):
            ans = {s: truth[s] for s in list(task.mandatory) + list(subset)}
            S = _surviving(interps, ans)
            cands = [ikey(t) for t in S]
            worst = {c: max(oracle.loss(c, ikey(t)) - oracle.noise.get(ikey(t), 0) for t in S) for c in cands}
            c = min(worst, key=worst.get)
            if worst[c] <= tau:
                best = (list(task.mandatory) + list(subset), c, worst[c])
                break
        if best:
            break
    if best is None:
        tk = ikey(truth)
        return Outcome("oracle", slots, tk, True, len(interps), 0, oracle.loss(tk, tk), False)
    asked, c, B = best
    tk = ikey(truth)
    L = oracle.loss(c, tk)
    return Outcome("oracle", asked, c, True, len(interps), 0, L, L > tau + oracle.noise.get(tk, 0), dict(B=B))


# ------------------------------------------------------------------ ledgered policies (round-3 audit)
# A policy may use only what it has computed. A "reference bundle" is the two-start optimization of one
# reading; it yields that reading's design, its compliance and its two-start spread (noise). Cross
# evaluations of computed designs under any reading need no optimization (one factorization per design
# and support group). References are local: ref_K(t) = min over computed designs feasible for t. The
# final judgement (false release) always uses the global best-known references of the offline table.

def _plan(task, S, cands, loss, allow, tau, asked, budget):
    """Adjusted minimax over commitment candidates `cands`; deterministic ties.
    Returns (slot or None, commit, B) with B = min_c max_{t in S} [loss(c, t) - allow(t)]."""
    def best(Ssub):
        ks = [ikey(t) for t in Ssub]
        w = {c: max(loss(c, k) - allow(k) for k in ks) for c in cands}
        c = min(sorted(w), key=lambda c: w[c])
        return c, w[c]
    c0, B0 = best(S)
    if B0 <= tau or len(asked) >= budget:
        return None, c0, B0
    pick = None
    for s in sorted(task.slots):
        vals = sorted({t[s] for t in S}, key=str)
        if s in asked or len(vals) < 2:
            continue
        wc = max(best([t for t in S if t[s] == v])[1] for v in vals)
        if pick is None or wc < pick[1]:
            pick = (s, wc)
    return (pick[0] if pick else None), c0, B0


def cgc(task, oracle, truth, tau, budget=3):
    """Consequence-guided clarification with the full table (every reading optimized up front).
    Candidates: all computed designs."""
    interps = task.interpretations()
    keys = sorted(ikey(t) for t in interps)
    answers = {s: truth[s] for s in task.mandatory}
    asked = list(task.mandatory)
    lim = budget + len(task.mandatory)
    while True:
        S = _surviving(interps, answers)
        q, commit, B = _plan(task, S, keys, oracle.loss, lambda k: oracle.noise.get(k, 0.0), tau, asked, lim)
        if q is None:
            break
        answers[q] = truth[q]
        asked.append(q)
    tk = ikey(truth)
    L = oracle.loss(commit, tk)
    rel = B <= tau
    return Outcome("CGC", asked, commit, rel, len(interps), 0, L, rel and L > tau + oracle.noise.get(tk, 0),
                   dict(B=B, bundles=len(interps)))


def cgc_s(task, oracle, truth, tau, budget=3, a0=0.0):
    """CGC with certified screening and lazy references, under an information ledger.

    K = readings whose reference bundle has been computed (library). Lower bound for any reading t:
    l_lo(d, t) = C_t(d) / ref_K(t) - 1 with ref_K(t) = min_{e in K} C_t(e) (feasible e); allowance =
    measured spread for t in K, a0 otherwise. Ask while no library design is within tau on the
    survivors; otherwise compute references for all survivors and release only if the best computed
    design is within tau (+ measured spread) of the local references for every survivor."""
    interps = task.interpretations()
    keys = {ikey(t) for t in interps}
    answers = {s: truth[s] for s in task.mandatory}
    asked = list(task.mandatory)
    lim = budget + len(task.mandatory)
    K = set()
    nom = dict(task.nominal, **answers)
    seed = [nom] + [dict(nom, **{s: v}) for s, vals in sorted(task.slots.items())
                    if len(vals) > 1 and s not in answers for v in (vals[0], vals[-1])]
    K |= {ikey(t) for t in seed if ikey(t) in keys}

    def ref_k(t):
        pairs.update((d, t) for d in K)
        return min(oracle.C[(d, t)] for d in K)

    pairs = set()                       # (design, reading) cross evaluations used (one solve each)

    def loss_k(d, t):
        pairs.add((d, t))
        c = oracle.C[(d, t)]
        if not np.isfinite(c):
            return np.inf
        return c / ref_k(t) - 1.0

    def allow(t):
        return oracle.noise.get(t, 0.0) if t in K else a0

    released, commit, B = False, None, np.inf
    while True:
        S = _surviving(interps, answers)
        q, commit, B = _plan(task, S, sorted(K), loss_k, allow, tau, asked, lim)
        if q is not None:
            answers[q] = truth[q]
            asked.append(q)
            cur = ikey(dict(nom, **answers))
            if cur in keys:
                K.add(cur)
            continue
        # verification: references for every survivor, then the exact local check
        K |= {ikey(t) for t in S}
        q2, commit, B = _plan(task, S, sorted(K), loss_k, allow, tau, asked, lim)
        if B <= tau:
            released = True
            break
        if q2 is None:
            break                       # budget exhausted or nothing left to ask: abstain
        answers[q2] = truth[q2]
        asked.append(q2)
    tk = ikey(truth)
    L = oracle.loss(commit, tk)
    return Outcome("CGC_S", asked, commit, released, len(K), len(pairs), L,
                   released and L > tau + oracle.noise.get(tk, 0), dict(B_local=B, bundles=len(K)))


def cgc_fixed(task, oracle, truth, tau, budget=3, order=None):
    """Baseline: same release check as CGC (full table), but questions in a fixed slot order (declared order
    unless `order` is given) instead of the minimax choice."""
    interps = task.interpretations()
    keys = sorted(ikey(t) for t in interps)
    answers = {s: truth[s] for s in task.mandatory}
    asked = list(task.mandatory)
    lim = budget + len(task.mandatory)
    seq = [s for s in (order or list(task.slots)) if s not in task.mandatory]
    while True:
        S = _surviving(interps, answers)
        _, commit, B = _plan(task, S, keys, oracle.loss, lambda k: oracle.noise.get(k, 0.0), tau, asked, lim)
        if B <= tau or len(asked) >= lim:
            break
        nxt = [s for s in seq if s not in asked and len({t[s] for t in S}) > 1]
        if not nxt:
            break
        answers[nxt[0]] = truth[nxt[0]]
        asked.append(nxt[0])
    tk = ikey(truth)
    L = oracle.loss(commit, tk)
    rel = B <= tau
    return Outcome("CGC_fixed", asked, commit, rel, len(interps), 0, L, rel and L > tau + oracle.noise.get(tk, 0),
                   dict(B=B))


POLICIES = dict(no_ask=no_ask, mandatory_only=ask_mandatory_then_nominal, ask_all=ask_all,
                full_H=full_h, H_lazy=h_lazy, oracle=oracle_lookahead, CGC=cgc, CGC_S=cgc_s)
