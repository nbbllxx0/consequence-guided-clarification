"""A15: replays requested by the round-3 reviewers, from the stored E03/E08 tables (no new optimization).

Sections (all at zero allowance, the primary setting, unless stated):
  tau_sweep      questions, releases, pool-unsafe releases and bundles of every policy for tau in TAUS
  robust         robust-first CGC and CGC with the robust design as an extra candidate (23 applicable tasks)
  robust_alone   the no-question robust baseline at zero allowance
  cgcs_gap       per CGC-S release: local-reference gaps U_t/V_t - 1 and margins tau - max loss
  frozen         E08 tasks: the base-table releases re-scored, unchanged, against six-start references
  band           releases and questions decided within the measured two-start spread of tau
  attribution    silent-default failures by cause (infeasible: which constraint; finite: load on void)
  order_null     question counts over all slot orders, with the full-table check and the local check
  expected_rule  question chosen by the expected (uniform prior) instead of the worst answer
  wall_clock     measured wall-clock per bundle and per case
Usage: python experiments/a15_reviewer_replays.py [consensus|union]
Output: results/a15/<variant>.json
"""
import itertools
import json
import os
import statistics
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
import runner  # noqa: E402
import simp  # noqa: E402
import taskspec  # noqa: E402

TAU = e03.TAU
TAUS = (0.01, 0.02, 0.05, 0.10, 0.20)
OUT = os.path.join(ROOT, "results", "a15")


# ------------------------------------------------------------------ shared helpers
def load_task(tid):
    orc0, out = e03.oracle_from_file(tid)
    zero = pl.Oracle(ref=orc0.ref, C=orc0.C, noise={k: 0.0 for k in orc0.noise})
    return lt.TASKS[tid]["task"], zero, orc0, out


def survivors(interps, truth, asked):
    ans = {s: truth[s] for s in asked}
    return [pl.ikey(t) for t in interps if all(t[s] == v for s, v in ans.items())]


def score(task, orc, interps, outcomes, tau, loss=None):
    """Per-case rows for a list of (truth, Outcome); loss(c, t) defaults to the oracle loss."""
    loss = loss or orc.loss
    rows = []
    for truth, o in outcomes:
        surv = survivors(interps, truth, o.asked)
        worst = max(loss(o.commit, k) for k in surv) if o.commit else np.inf
        rows.append(dict(truth=pl.ikey(truth), asked=list(o.asked),
                         q=len([s for s in o.asked if s not in task.mandatory]), q_all=len(o.asked),
                         released=bool(o.released), unsafe=bool(o.released and worst > tau),
                         exceed=bool(o.released and loss(o.commit, pl.ikey(truth)) > tau),
                         bundles=int(o.optimizations), commit=o.commit, worst=float(worst), extra=o.extra))
    return rows


def totals(rows):
    return dict(cases=len(rows), questions=sum(r["q"] for r in rows), questions_incl_mandatory=sum(r["q_all"] for r in rows),
                released=sum(r["released"] for r in rows), unsafe=sum(r["unsafe"] for r in rows),
                exceed=sum(r["exceed"] for r in rows), bundles=sum(r["bundles"] for r in rows))


def add(acc, name, tot):
    a = acc.setdefault(name, {k: 0 for k in tot})
    for k, v in tot.items():
        a[k] += v


def robust_loss(tid, orc):
    """Robust design losses per reading (file ratio), or None when not applicable / stale."""
    if e03.robust_applicable(tid):
        return None
    p = os.path.join(e03.OUT, f"robust_{tid}.json")
    if not os.path.exists(p):
        return None
    with open(p) as fh:
        rob = json.load(fh)
    T = lt.TASKS[tid]
    if rob.get("spec_hashes") != [taskspec.spec_hash(T["build"](t)) for t in lt.interpretations(tid)]:
        raise RuntimeError(f"robust design for {tid} is stale")
    return {k: r - 1.0 for k, r in zip(rob["keys"], rob["ratio"])}


# ------------------------------------------------------------------ policy variants used only here
def cgc_candidates(task, orc, truth, tau, extra_loss, budget=3, rule="worst"):
    """CGC (full table) with optional extra candidate designs {name: {t_key: loss}} and a choice of
    question rule: 'worst' (the paper's minimax: worst answer) or 'expected' (answers weighted by the
    number of surviving readings, i.e. a uniform prior over readings)."""
    interps = task.interpretations()
    keys = sorted(pl.ikey(t) for t in interps)
    cands = keys + sorted(extra_loss)

    def loss(c, t):
        return extra_loss[c][t] if c in extra_loss else orc.loss(c, t)

    def best(S):
        ks = [pl.ikey(t) for t in S]
        w = {c: max(loss(c, k) for k in ks) for c in cands}
        c = min(sorted(w), key=lambda c: w[c])
        return c, w[c]

    answers = {s: truth[s] for s in task.mandatory}
    asked = list(task.mandatory)
    lim = budget + len(task.mandatory)
    while True:
        S = pl._surviving(interps, answers)
        commit, B = best(S)
        if B <= tau or len(asked) >= lim:
            break
        pick = None
        for s in sorted(task.slots):
            vals = sorted({t[s] for t in S}, key=str)
            if s in asked or len(vals) < 2:
                continue
            parts = [[t for t in S if t[s] == v] for v in vals]
            if rule == "worst":
                sc = max(best(P)[1] for P in parts)
            else:
                sc = sum(len(P) * best(P)[1] for P in parts) / len(S)
            if pick is None or sc < pick[1]:
                pick = (s, sc)
        if pick is None:
            break
        answers[pick[0]] = truth[pick[0]]
        asked.append(pick[0])
    tk = pl.ikey(truth)
    rel = B <= tau
    return pl.Outcome("CGC_var", asked, commit, rel, len(interps) + len(extra_loss), 0, loss(commit, tk),
                      rel and loss(commit, tk) > tau, dict(B=B))


def cgc_s_order(task, orc, truth, tau, order, budget=3):
    """CGC-S (local check, library screening) with questions in a fixed slot order instead of the minimax
    choice: whenever the policy would ask, it asks the first open slot of `order` that still varies."""
    interps = task.interpretations()
    keys = {pl.ikey(t) for t in interps}
    answers = {s: truth[s] for s in task.mandatory}
    asked = list(task.mandatory)
    lim = budget + len(task.mandatory)
    nom = dict(task.nominal, **answers)
    seed = [nom] + [dict(nom, **{s: v}) for s, vals in sorted(task.slots.items())
                    if len(vals) > 1 and s not in answers for v in (vals[0], vals[-1])]
    K = {pl.ikey(t) for t in seed if pl.ikey(t) in keys}

    def loss_k(d, t):
        c = orc.C[(d, t)]
        if not np.isfinite(c):
            return np.inf
        return c / min(orc.C[(e, t)] for e in K) - 1.0

    def nxt(S):
        for s in order:
            if s not in asked and len({t[s] for t in S}) > 1:
                return s
        return None

    released, commit = False, None
    while True:
        S = pl._surviving(interps, answers)
        q, commit, B = pl._plan(task, S, sorted(K), loss_k, lambda t: 0.0, tau, asked, lim)
        if q is not None:
            q = nxt(S) or q
            answers[q] = truth[q]
            asked.append(q)
            cur = pl.ikey(dict(nom, **answers))
            if cur in keys:
                K.add(cur)
            continue
        K |= {pl.ikey(t) for t in S}
        q2, commit, B = pl._plan(task, S, sorted(K), loss_k, lambda t: 0.0, tau, asked, lim)
        if B <= tau:
            released = True
            break
        if q2 is None:
            break
        q2 = nxt(S) or q2
        answers[q2] = truth[q2]
        asked.append(q2)
    tk = pl.ikey(truth)
    L = orc.loss(commit, tk)
    return pl.Outcome("CGC_S_order", asked, commit, released, len(K), 0, L, released and L > tau, dict(K=sorted(K)))


def cgc_s_with_k(task, orc, truth, tau):
    """pl.cgc_s, plus the final library K rebuilt by replaying its steps (same decisions)."""
    o = pl.cgc_s(task, orc, truth, tau)
    o2 = cgc_s_order(task, orc, truth, tau, order=[])      # empty order: falls back to the minimax choice
    if o2.asked != o.asked or o2.commit != o.commit or o2.released != o.released or o2.optimizations != o.optimizations:
        raise RuntimeError(f"CGC-S re-implementation diverged for {task.name} {pl.ikey(truth)}")
    o.extra["K"] = o2.extra["K"]
    return o


# ------------------------------------------------------------------ sections
def tau_sweep(tids):
    acc = {}
    for tau in TAUS:
        a = {}
        for tid in tids:
            task, orc, _, _ = load_task(tid)
            interps = task.interpretations()
            rl = robust_loss(tid, orc)
            for name, fn in (("no_ask", pl.no_ask), ("ask_all", pl.ask_all), ("CGC", pl.cgc), ("CGC_S", pl.cgc_s)):
                add(a, name, totals(score(task, orc, interps, [(t, fn(task, orc, t, tau)) for t in interps], tau)))
            add(a, "robust_first", totals(robust_first_rows(task, orc, interps, rl, tau)))
            ext = {"robust": rl} if rl else {}
            add(a, "CGC_robust_candidate", totals(score(
                task, orc, interps, [(t, cgc_candidates(task, orc, t, tau, ext)) for t in interps], tau,
                loss=lambda c, k: rl[k] if c == "robust" else orc.loss(c, k))))
        acc[f"{tau:g}"] = a
    return acc


def robust_first_rows(task, orc, interps, rl, tau):
    """Release the robust design when its worst loss over every reading is within tau (zero allowance);
    otherwise CGC on the full table. The robust run needs every reference, so it costs |Theta| + 1."""
    n = len(interps)
    if rl is not None and max(rl.values()) <= tau:
        return [dict(truth=pl.ikey(t), asked=list(task.mandatory), q=0, q_all=len(task.mandatory), released=True,
                     unsafe=False, exceed=bool(rl[pl.ikey(t)] > tau), bundles=n + 1, commit="robust",
                     worst=max(rl.values()), extra={}) for t in interps]
    rows = score(task, orc, interps, [(t, pl.cgc(task, orc, t, tau)) for t in interps], tau)
    if rl is not None:
        for r in rows:
            r["bundles"] += 1
    return rows


def robust_section(tids):
    res = dict(applicable=[], covers_at_tau=[], per_task={})
    for tid in tids:
        task, orc, orc_noise, _ = load_task(tid)
        rl = robust_loss(tid, orc)
        if rl is None:
            continue
        res["applicable"].append(tid)
        worst = max(rl.values())
        # spread-allowance check, to reproduce the paper's robust row (worst ratio - 1 - noise)
        worst_spread = max(rl[k] - orc_noise.noise.get(k, 0.0) for k in rl)
        if worst <= TAU:
            res["covers_at_tau"].append(tid)
        res["per_task"][tid] = dict(n=len(rl), worst=worst, worst_spread_allowance=worst_spread)
    res["covers_spread_allowance"] = sum(v["worst_spread_allowance"] <= TAU for v in res["per_task"].values())
    return res


def robust_alone(tids):
    """The no-question robust baseline at zero allowance: release the robust design in every case of an
    applicable task. Bundles per case are |Theta| + 1 (every reference plus the robust optimization)."""
    acc = dict(tasks=0, cases=0, released=0, unsafe=0, exceed=0, bundles=0)
    for tid in tids:
        _, orc, _, _ = load_task(tid)
        rl = robust_loss(tid, orc)
        if rl is None:
            continue
        n = len(rl)
        acc["tasks"] += 1
        acc["cases"] += n
        acc["released"] += n
        acc["unsafe"] += n if max(rl.values()) > TAU else 0
        acc["exceed"] += sum(v > TAU for v in rl.values())
        acc["bundles"] += n * (n + 1)
    return acc


def cgcs_gap(tids):
    rows = []
    for tid in tids:
        task, orc, _, _ = load_task(tid)
        interps = task.interpretations()
        for truth in interps:
            o = cgc_s_with_k(task, orc, truth, TAU)
            if not o.released:
                continue
            K = o.extra["K"]
            surv = survivors(interps, truth, o.asked)
            gaps, llo, lfull = [], [], []
            for t in surv:
                U = min(orc.C[(e, t)] for e in K)
                V = orc.ref[t]
                c = orc.C[(o.commit, t)]
                gaps.append(U / V - 1.0)
                llo.append(c / U - 1.0)
                lfull.append(c / V - 1.0)
            rows.append(dict(task=tid, truth=pl.ikey(truth), n_surv=len(surv), K=len(K),
                             max_gap=max(gaps), n_gap=sum(g > 1e-9 for g in gaps),
                             max_local=max(llo), max_full=max(lfull),
                             margin_local=TAU - max(llo), margin_full=TAU - max(lfull)))
    g = [r["max_gap"] for r in rows]
    return dict(releases=len(rows), releases_with_gap=sum(r["n_gap"] > 0 for r in rows),
                survivors_with_gap=sum(r["n_gap"] for r in rows), survivors=sum(r["n_surv"] for r in rows),
                tasks_with_gap=sorted({r["task"] for r in rows if r["n_gap"] > 0}),
                max_gap=max(g) if g else 0.0,
                min_margin_full=min(r["margin_full"] for r in rows),
                releases_margin_full_below_0p01=sum(r["margin_full"] < 0.01 for r in rows),
                releases_margin_full_below_0p02=sum(r["margin_full"] < 0.02 for r in rows),
                median_margin_full=statistics.median(r["margin_full"] for r in rows),
                gap_exceeds_margin=sum(r["max_gap"] > r["margin_local"] for r in rows if r["n_gap"]),
                rows=rows)


def frozen(tids=("L18", "L24", "L37", "L16")):
    res = {}
    for tid in tids:
        with open(os.path.join(ROOT, "results", "e08", f"{tid}.json")) as fh:
            e08 = json.load(fh)
        task = lt.TASKS[tid]["task"]
        interps = task.interpretations()
        tabs = {}
        for var in ("base", "polished", "refined_x2"):
            v = e08[var]
            keys = v["keys"]
            tabs[var] = dict(keys=keys, ref=v["ref"],
                             C={(d, t): float(v["C"][i][j]) for i, d in enumerate(keys) for j, t in enumerate(keys)})
        base = pl.Oracle(ref=tabs["base"]["ref"], C=tabs["base"]["C"], noise={k: 0.0 for k in tabs["base"]["keys"]})
        e03_ref = load_task(tid)[1].ref
        same_base = all(abs(base.ref[k] / e03_ref[k] - 1) < 1e-9 for k in e03_ref) and set(e03_ref) == set(base.ref)
        out = dict(base_matches_e03=same_base)
        for name, fn in (("CGC", pl.cgc), ("CGC_S", pl.cgc_s)):
            worst_pol, worst_ref, n_rel, over_pol, over_ref = [], [], 0, 0, 0
            for truth in interps:
                o = fn(task, base, truth, TAU)
                if not o.released:
                    continue
                n_rel += 1
                surv = survivors(interps, truth, o.asked)
                pr = {t: min(tabs["polished"]["ref"][t], base.ref[t]) for t in surv}
                wp = max(base.C[(o.commit, t)] / pr[t] - 1 for t in surv)      # same design, stronger reference
                wr = max(tabs["refined_x2"]["C"][(o.commit, t)] / tabs["refined_x2"]["ref"][t] - 1 for t in surv)
                worst_pol.append(wp)
                worst_ref.append(wr)
                over_pol += wp > TAU
                over_ref += wr > TAU
            out[name] = dict(releases=n_rel, max_frozen_six_start=max(worst_pol), over_tau_six_start=over_pol,
                             max_same_reading_refined=max(worst_ref), over_tau_refined=over_ref)
        res[tid] = out
    return res


def band(tids):
    """Decisions within the measured two-start spread of tau (full-table CGC, zero allowance)."""
    rel_band, ask_band, tasks = 0, 0, set()
    n_rel, n_ask = 0, 0
    for tid in tids:
        task, orc, orc_noise, _ = load_task(tid)
        interps = task.interpretations()
        keys = sorted(pl.ikey(t) for t in interps)
        for truth in interps:
            o = pl.cgc(task, orc, truth, TAU)
            prefix = list(task.mandatory)
            steps = [list(prefix)]
            for s in o.asked[len(task.mandatory):]:
                prefix = prefix + [s]
                steps.append(list(prefix))
            for i, asked in enumerate(steps):
                surv = survivors(interps, truth, asked)
                B = min(max(orc.loss(c, k) for k in surv) for c in keys)
                spread = max(orc_noise.noise.get(k, 0.0) for k in surv)
                last = i == len(steps) - 1
                if last and o.released:
                    n_rel += 1
                    if B > TAU - spread:
                        rel_band += 1
                        tasks.add(tid)
                elif not last:
                    n_ask += 1
                    if B <= TAU + spread:
                        ask_band += 1
                        tasks.add(tid)
    return dict(releases=n_rel, releases_within_spread=rel_band, questions=n_ask, questions_within_spread=ask_band,
                tasks=sorted(tasks))


def attribution(tids):
    """Silent-default failures: for each task with a pool-unsafe nominal commitment, classify the
    violating readings. Infeasible: which feasibility rule fails. Finite: share of the applied load on
    nodes whose adjacent elements are all void (rho < 0.5) in the default design."""
    res = {}
    for tid in tids:
        task, orc, _, out = load_task(tid)
        nom = pl.ikey(task.nominal)
        T = lt.TASKS[tid]
        specs = {pl.ikey(t): T["build"](t) for t in lt.interpretations(tid)}
        bad = [k for k in out["keys"] if orc.loss(nom, k) > TAU]
        if not bad:
            continue
        st = e03.settings_for(T["dim"])
        recs = [runner.load(runner.job_key(specs[nom], i, st)) for i in e03.INITS]
        if any(r is None for r in recs):
            raise RuntimeError(f"default design of {tid} is not cached; refusing to optimize")
        rbest = min(recs, key=lambda r: r["compliance"])
        xp, act = runner.load_design(rbest["key"])
        Pn = taskspec.build(specs[nom])
        full = np.zeros(Pn.nel)
        full[np.asarray(act)] = xp
        cls = []
        for k in bad:
            c = orc.C[(nom, k)]
            sn, sk = specs[nom], specs[k]
            if not np.isfinite(c):
                why = []
                if json.dumps(sn.get("domain"), sort_keys=True) != json.dumps(sk.get("domain"), sort_keys=True):
                    why.append("domain")
                if sn.get("rmin", st["rmin"]) < sk.get("rmin", st["rmin"]) - 1e-12:
                    why.append("filter radius")
                if json.dumps(sn.get("solid"), sort_keys=True) != json.dumps(sk.get("solid"), sort_keys=True):
                    why.append("passive region")
                if sn.get("volfrac") != sk.get("volfrac"):
                    why.append("volume bound")
                cls.append(dict(reading=k, kind="infeasible", why=why or ["other"]))
                continue
            P = taskspec.build(sk)
            nd = 3 if getattr(P, "nelz", 0) else 2
            edof = simp.edof_3d(P.nelx, P.nely, P.nelz) if nd == 3 else simp.edof_2d(P.nelx, P.nely)
            enodes = edof[:, ::nd] // nd
            nnode = int(enodes.max()) + 1
            nmax = np.zeros(nnode)
            np.maximum.at(nmax, enodes.ravel(), np.repeat(full, enodes.shape[1]))
            f = np.zeros(nnode)
            for lc in P.loads:
                fv = np.abs(np.asarray(lc.f)).reshape(-1, nd).sum(1)
                f[:fv.size] += fv
            void_share = float(f[nmax < 0.5].sum() / f.sum())
            cls.append(dict(reading=k, kind="finite", loss=float(orc.loss(nom, k)), load_on_void_share=void_share))
        fin = [c for c in cls if c["kind"] == "finite"]
        res[tid] = dict(dim=T["dim"], n_bad=len(bad), readings=cls,
                        task_class=("infeasible" if any(c["kind"] == "infeasible" for c in cls)
                                    else "large_loss" if max(c["loss"] for c in fin) > 10 else "consequential"),
                        load_on_void=bool(fin) and max(c["load_on_void_share"] for c in fin) > 0.5)
    summ = {}
    for v in res.values():
        key = f"{v['dim']}D_{v['task_class']}"
        summ[key] = summ.get(key, 0) + 1
    lv = [t for t, v in res.items() if v["task_class"] != "infeasible" and v["load_on_void"]]
    causes = {}
    for v in res.values():
        for c in v["readings"]:
            if c["kind"] == "infeasible":
                for w in c["why"]:
                    causes[w] = causes.get(w, 0) + 1
    return dict(tasks=len(res), classes=summ, finite_tasks_with_load_on_void=lv,
                finite_tasks=[t for t, v in res.items() if v["task_class"] != "infeasible"],
                infeasible_causes_by_reading=causes, per_task=res)


def order_null(tids):
    acc = {}
    per_task = {}
    for tid in tids:
        task, orc, _, _ = load_task(tid)
        interps = task.interpretations()
        free = [s for s in task.slots if s not in task.mandatory and len(task.slots[s]) > 1]
        perms = list(itertools.permutations(free)) or [()]
        full = [totals(score(task, orc, interps, [(t, pl.cgc_fixed(task, orc, t, TAU, order=list(p))) for t in interps], TAU))
                for p in perms]
        loc = [totals(score(task, orc, interps, [(t, cgc_s_order(task, orc, t, TAU, list(p))) for t in interps], TAU))
               for p in perms]
        for name, lst in (("full_random_mean", full), ("local_random_mean", loc)):
            add(acc, name, {k: float(np.mean([x[k] for x in lst])) for k in ("questions", "released", "unsafe", "bundles")})
        add(acc, "local_declared", {k: loc[0][k] for k in ("questions", "released", "unsafe", "bundles")})
        add(acc, "local_reverse", {k: loc[-1][k] for k in ("questions", "released", "unsafe", "bundles")})
        per_task[tid] = dict(free=len(free), full_q=[x["questions"] for x in full], local_q=[x["questions"] for x in loc])
    acc["tasks_with_2plus_free"] = sum(v["free"] >= 2 for v in per_task.values())
    return dict(totals=acc, per_task=per_task)


def expected_rule(tids):
    acc = {}
    for tid in tids:
        task, orc, _, _ = load_task(tid)
        interps = task.interpretations()
        for name, rule in (("worst_answer", "worst"), ("expected_answer", "expected")):
            add(acc, name, totals(score(task, orc, interps,
                                        [(t, cgc_candidates(task, orc, t, TAU, {}, rule=rule)) for t in interps], TAU)))
        add(acc, "CGC_reference", totals(score(task, orc, interps, [(t, pl.cgc(task, orc, t, TAU)) for t in interps], TAU)))
    return acc


def wall_clock(tids):
    per_dim = {2: [], 3: []}
    case = dict(CGC_S=[], ask_all=[], CGC=[], saved_q=[], tid=[])
    for tid in tids:
        task, orc, _, out = load_task(tid)
        interps = task.interpretations()
        w = {k: out["meta"][k]["wall_s"] for k in out["keys"]}
        per_dim[out["dim"]].extend(w.values())
        for truth in interps:
            o = cgc_s_with_k(task, orc, truth, TAU)
            a = pl.ask_all(task, orc, truth, TAU)
            case["CGC_S"].append(sum(w[k] for k in o.extra["K"]))
            case["ask_all"].append(w[pl.ikey(truth)])
            case["CGC"].append(sum(w.values()))
            case["saved_q"].append(len(a.asked) - len(o.asked))
            case["tid"].append(tid)

    def q(x):
        return dict(n=len(x), median=float(np.median(x)), p25=float(np.percentile(x, 25)), p75=float(np.percentile(x, 75)),
                    max=float(np.max(x)))
    extra_s = np.array(case["CGC_S"]) - np.array(case["ask_all"])
    saved = np.array(case["saved_q"])
    by_dim = {}
    for dim in (2, 3):
        m = np.array([lt.TASKS[t]["dim"] == dim for t in case["tid"]])
        if m.any():
            by_dim[f"{dim}D"] = dict(cases=int(m.sum()), extra_s_total=float(extra_s[m].sum()),
                                     saved_q_total=int(saved[m].sum()),
                                     extra_s_per_saved_q=float(extra_s[m].sum() / max(saved[m].sum(), 1)))
    return dict(bundle_wall_s={f"{d}D": q(v) for d, v in per_dim.items() if v},
                case_wall_s={k: q(case[k]) for k in ("CGC_S", "ask_all", "CGC")}, break_even=by_dim,
                note="wall_s = sum of the two starts of one reading, measured in batch runs (2-D: 19 single-thread "
                     "workers; 3-D: 4 workers x 4 MKL threads), so it includes contention")


def main():
    tids = list(lt.TASKS)
    res = dict(variant=VARIANT, tau=TAU)
    for name, fn in (("tau_sweep", tau_sweep), ("robust", robust_section), ("robust_alone", robust_alone),
                     ("cgcs_gap", cgcs_gap),
                     ("band", band), ("order_null", order_null), ("expected_rule", expected_rule),
                     ("wall_clock", wall_clock), ("attribution", attribution)):
        res[name] = fn(tids)
        print(name, "done", flush=True)
    if VARIANT == "consensus":
        res["frozen"] = frozen()
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"{VARIANT}.json"), "w") as fh:
        json.dump(res, fh, indent=1, default=float)
    brief = {k: v for k, v in res.items() if k not in ("cgcs_gap", "attribution", "order_null")}
    brief["cgcs_gap"] = {k: v for k, v in res["cgcs_gap"].items() if k != "rows"}
    brief["attribution"] = {k: v for k, v in res["attribution"].items() if k != "per_task"}
    brief["order_null"] = res["order_null"]["totals"]
    print(json.dumps(brief, indent=1, default=float))


if __name__ == "__main__":
    main()
