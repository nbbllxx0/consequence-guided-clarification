"""A17: default-design release controls, from the stored E03 tables (no new optimization).

The round-3 reviewers asked whether the question saving needs CGC's candidate pool and minimax rule,
or whether checking the default design alone gives the same saving. Policies (zero allowance):
  N_ask_all    release the default design (mandatory answers applied) if its loss is <= tau at every
               open reading; otherwise ask every remaining varying slot and release the identified
               reading's reference.
  N_fixed      the same check, repeated after each answer with the answered default design; questions
               follow the declared slot order; budget as CGC.
  N_minimax    the same check; the question is the slot whose worst answer leaves the smallest worst-case
               loss of the answered default design.
  N_fixed_S    N_fixed under CGC-S's ledger: seed library, lower-bound test before requesting the open
               readings' bundles, local check (the cheapest nominal-only variant).
  feas_screen  no references: release the default design if it is feasible at every open reading,
               otherwise ask every remaining varying slot (the reference-free screen of domain #2).
Bundles: a loss check of the default design needs the reference of every open reading, so N_* request
the bundles of every reading left open after the mandatory answers (lazy count) and are also reported
with the full-table count |Theta| used for CGC. feas_screen requests the nominal bundle and, when it
asks, the identified reading's bundle.
Scoring is strict (no allowance): pool-unsafe if the released design exceeds tau at any open reading,
truth exceedance if it exceeds tau at the hidden reading, both against the full best-known table.
Usage: python experiments/a17_nominal_controls.py [consensus|union]
Output: results/a17/<variant>.json
"""
import json
import os
import sys

import numpy as np

VARIANT = sys.argv[1] if len(sys.argv) > 1 else "consensus"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["LT_VARIANT"] = VARIANT
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import e03_literature_tasks as e03  # noqa: E402
import littasks as lt  # noqa: E402
import policies as pl  # noqa: E402

TAUS = (0.01, 0.02, 0.05, 0.10, 0.20)
OUT = os.path.join(ROOT, "results", "a17")


def load_task(tid):
    orc0, out = e03.oracle_from_file(tid)
    zero = pl.Oracle(ref=orc0.ref, C=orc0.C, noise={k: 0.0 for k in orc0.noise})
    return lt.TASKS[tid]["task"], zero


def varying(task, S, asked):
    return [s for s in task.slots if s not in asked and len({t[s] for t in S}) > 1]


def nominal_check(task, orc, truth, tau, rule, budget=3):
    interps = task.interpretations()
    keys = {pl.ikey(t) for t in interps}
    answers = {s: truth[s] for s in task.mandatory}
    asked = list(task.mandatory)
    lim = budget + len(task.mandatory)
    S0 = pl._surviving(interps, answers)

    def cur():
        return pl.ikey(dict(task.nominal, **answers))

    def worst(d, S):
        return max(orc.loss(d, pl.ikey(t)) for t in S) if d in keys else np.inf

    commit, released = None, False
    while True:
        S = pl._surviving(interps, answers)
        d = cur()
        if worst(d, S) <= tau:
            commit, released = d, True
            break
        open_slots = varying(task, S, asked)
        if not open_slots:
            commit = pl.ikey(truth) if len(S) == 1 else d
            released = worst(commit, S) <= tau
            break
        if rule == "ask_all":
            for s in open_slots:
                answers[s] = truth[s]
                asked.append(s)
            continue
        if len(asked) >= lim:
            commit = d
            break
        if rule == "fixed":
            q = open_slots[0]
        else:
            def wc(s):
                vals = sorted({t[s] for t in S}, key=str)
                out = []
                for v in vals:
                    a2 = dict(answers, **{s: v})
                    out.append(worst(pl.ikey(dict(task.nominal, **a2)), [t for t in S if t[s] == v]))
                return max(out)
            q = min(sorted(open_slots), key=wc)
        answers[q] = truth[q]
        asked.append(q)
    return asked, commit, released, len(S0), len(interps)


def nominal_check_s(task, orc, truth, tau, budget=3):
    """N_fixed under CGC-S's ledger: the same seed library; ask (declared order) while the lower bound
    of the answered default design exceeds tau; otherwise request every open reading's bundle and release
    the default design if it passes the local check, else ask the next slot."""
    interps = task.interpretations()
    keys = {pl.ikey(t) for t in interps}
    answers = {s: truth[s] for s in task.mandatory}
    asked = list(task.mandatory)
    lim = budget + len(task.mandatory)
    nom = dict(task.nominal, **answers)
    seed = [nom] + [dict(nom, **{s: v}) for s, vals in sorted(task.slots.items())
                    if len(vals) > 1 and s not in answers for v in (vals[0], vals[-1])]
    K = {pl.ikey(t) for t in seed if pl.ikey(t) in keys}

    def worst_local(d, S):
        if d not in keys:
            return np.inf
        out = []
        for t in S:
            c = orc.C[(d, pl.ikey(t))]
            out.append(c / min(orc.C[(e, pl.ikey(t))] for e in K) - 1.0 if np.isfinite(c) else np.inf)
        return max(out)

    commit, released = None, False
    while True:
        S = pl._surviving(interps, answers)
        d = pl.ikey(dict(task.nominal, **answers))
        if worst_local(d, S) <= tau:
            K |= {pl.ikey(t) for t in S}
            if worst_local(d, S) <= tau:
                commit, released = d, True
                break
        open_slots = varying(task, S, asked)
        if not open_slots or len(asked) >= lim:
            commit = d
            break
        q = open_slots[0]
        answers[q] = truth[q]
        asked.append(q)
        cur = pl.ikey(dict(task.nominal, **answers))
        if cur in keys:
            K.add(cur)
    return asked, commit, released, len(K), len(K)


def feas_screen(task, orc, truth, tau):
    interps = task.interpretations()
    answers = {s: truth[s] for s in task.mandatory}
    asked = list(task.mandatory)
    S0 = pl._surviving(interps, answers)
    d = pl.ikey(dict(task.nominal, **answers))
    if all(np.isfinite(orc.C[(d, pl.ikey(t))]) for t in S0):
        return asked, d, True, 1, 1
    for s in varying(task, S0, asked):
        answers[s] = truth[s]
        asked.append(s)
    tk = pl.ikey(truth)
    return asked, tk, True, 1 + (tk != d), 1 + (tk != d)


def row(task, orc, truth, asked, commit, released, b_lazy, b_full, *, tau):
    interps = task.interpretations()
    surv = [pl.ikey(t) for t in interps if all(t[s] == truth[s] for s in asked)]
    w = max(orc.loss(commit, k) for k in surv) if commit else np.inf
    tl = orc.loss(commit, pl.ikey(truth)) if commit else np.inf
    return dict(truth=pl.ikey(truth), asked=list(asked), q=len([s for s in asked if s not in task.mandatory]),
                q_all=len(asked), released=bool(released), unsafe=bool(released and w > tau),
                exceed=bool(released and tl > tau), bundles_lazy=int(b_lazy), bundles_full=int(b_full),
                commit=commit, worst=float(w))


def totals(rows):
    keys = ("q", "q_all", "released", "unsafe", "exceed", "bundles_lazy", "bundles_full")
    t = {k: int(sum(r[k] for r in rows)) for k in keys}
    t["cases"] = len(rows)
    return t


def run(tids, tau):
    res, per = {}, {}
    for tid in tids:
        task, orc = load_task(tid)
        interps = task.interpretations()
        rows = {}
        for name, rule in (("N_ask_all", "ask_all"), ("N_fixed", "fixed"), ("N_minimax", "minimax")):
            rows[name] = [row(task, orc, t, *nominal_check(task, orc, t, tau, rule), tau=tau) for t in interps]
        rows["N_fixed_S"] = [row(task, orc, t, *nominal_check_s(task, orc, t, tau), tau=tau) for t in interps]
        rows["feas_screen"] =[row(task, orc, t, *feas_screen(task, orc, t, tau), tau=tau) for t in interps]
        for name, fn in (("CGC", pl.cgc), ("CGC_S", pl.cgc_s), ("ask_all", pl.ask_all)):
            rr = []
            for t in interps:
                o = fn(task, orc, t, tau)
                rr.append(row(task, orc, t, o.asked, o.commit, o.released, o.optimizations, o.optimizations, tau=tau))
            rows[name] = rr
        per[tid] = {k: totals(v) for k, v in rows.items()}
        per[tid]["cases_where_N_fixed_asks_more_than_CGC"] = sum(
            a["q"] > b["q"] for a, b in zip(rows["N_fixed"], rows["CGC"]))
        per[tid]["cases_where_CGC_asks_more_than_N_fixed"] = sum(
            a["q"] < b["q"] for a, b in zip(rows["N_fixed"], rows["CGC"]))
        for k, v in rows.items():
            a = res.setdefault(k, {kk: 0 for kk in totals(v)})
            for kk, vv in totals(v).items():
                a[kk] += vv
    return res, per


def unresolved(tids, tau=0.05):
    """Releases decided within the measured two-start spread. A zero-allowance release is flagged
    unresolved when the released design's loss plus the reading's two-start spread exceeds tau at some
    open reading. The conservative replay requires loss + spread <= tau (allowance = -spread for computed
    readings) and so asks or abstains instead of making a flagged release."""
    acc = {}
    flagged = []
    for tid in tids:
        orc0, _ = e03.oracle_from_file(tid)
        task = lt.TASKS[tid]["task"]
        zero = pl.Oracle(ref=orc0.ref, C=orc0.C, noise={k: 0.0 for k in orc0.noise})
        cons = pl.Oracle(ref=orc0.ref, C=orc0.C, noise={k: -max(v, 0.0) for k, v in orc0.noise.items()})
        interps = task.interpretations()
        for name, fn in (("CGC", pl.cgc), ("CGC_S", pl.cgc_s)):
            for t in interps:
                o = fn(task, zero, t, tau)
                surv = [pl.ikey(x) for x in interps if all(x[s] == t[s] for s in o.asked)]
                if o.released and max(zero.loss(o.commit, k) + max(orc0.noise[k], 0.0) for k in surv) > tau:
                    flagged.append(dict(policy=name, task=tid, truth=pl.ikey(t), commit=o.commit,
                                        max_loss=max(zero.loss(o.commit, k) for k in surv)))
                oc = fn(task, cons, t, tau)
                r = row(task, zero, t, oc.asked, oc.commit, oc.released, oc.optimizations, oc.optimizations,
                        tau=tau)
                a = acc.setdefault(name + "_conservative", {k: 0 for k in totals([r])})
                for kk, vv in totals([r]).items():
                    a[kk] += vv
    by = {}
    for f in flagged:
        by.setdefault(f["policy"], {}).setdefault(f["task"], 0)
        by[f["policy"]][f["task"]] += 1
    return dict(conservative=acc, flagged_counts={p: sum(v.values()) for p, v in by.items()},
                flagged_by_task=by, flagged=flagged)


def main():
    tids = list(lt.TASKS)
    out = dict(variant=VARIANT, tasks=len(tids), tau_sweep={}, per_task={})
    out["unresolved"] = unresolved(tids)
    for tau in TAUS:
        tot, per = run(tids, tau)
        out["tau_sweep"][f"{tau:g}"] = tot
        if tau == 0.05:
            out["per_task"] = per
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"{VARIANT}.json"), "w") as fh:
        json.dump(out, fh, indent=1, default=float)
    print(json.dumps(out["tau_sweep"]["0.05"], indent=1))
    diff = {t: (v["cases_where_N_fixed_asks_more_than_CGC"], v["cases_where_CGC_asks_more_than_N_fixed"],
                v["N_fixed"]["q"], v["CGC"]["q"]) for t, v in out["per_task"].items()
            if v["N_fixed"]["q"] != v["CGC"]["q"]}
    print("tasks where N_fixed and CGC differ (N>CGC cases, CGC>N cases, N q, CGC q):", diff)


if __name__ == "__main__":
    main()
