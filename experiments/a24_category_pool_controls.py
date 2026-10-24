"""A24: controls requested by the loop-v5 round-1 reviewers, from the stored E03/E08 tables (no new optimization).

Sections (zero allowance, tau = 0.05 unless stated):
  category     zero-optimization category rules. Each non-mandatory slot is labelled by what it describes
               (CATEGORY below, from the slot's encoding reason). A rule asks every mandatory slot and every
               slot whose label is in its ask set (declared order, only slots still varying), sets every other
               slot to its default value, and releases the reference of the resulting reading. Cost: that one
               bundle per case. Rules: entity (ask position, domain, passive region, support, direction;
               default load extent), attribute (also default support extent), position_only (ask position,
               domain and direction; default every extent and passive region).
  own_paper    the primary totals without the authors' own sources (L11, L15, L44)
  common_pool  CGC and CGC-S releases re-scored, unchanged, with each reading's reference replaced by the best
               compliance of any computed design at that reading: the table designs, the robust design
               (23 tasks), and the six-start references of the E08 tasks
Scoring is strict: pool-unsafe if the released design exceeds tau at any open reading, truth exceedance if it
exceeds tau at the hidden reading, against the full table.
Usage: python experiments/a24_category_pool_controls.py [consensus|union]
Output: results/a24/<variant>.json
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

TAU = 0.05
TAUS = (0.01, 0.02, 0.05, 0.10, 0.20)
OUT = os.path.join(ROOT, "results", "a24")
OWN = ("L11", "L15", "L44")

# What each non-mandatory slot describes (from its encoding reason in littasks).
CATEGORY = {
    ("L01", "arm"): "domain", ("L01", "load"): "position",
    ("L02", "strip"): "load_extent", ("L02", "vf"): "volfrac",
    ("L04", "c"): "position", ("L04", "pad"): "passive", ("L04", "sup"): "support",
    ("L05", "rmin"): "setting",
    ("L06", "h"): "position", ("L06", "width"): "load_extent",
    ("L07", "clamp"): "support",
    ("L08", "ar"): "domain",
    ("L09", "load"): "position",
    ("L11", "voids"): "domain", ("L11", "r"): "domain",
    ("L12", "sup"): "support", ("L12", "load"): "load_extent", ("L12", "shell"): "passive",
    ("L13", "load"): "position",
    ("L14", "c"): "position",
    ("L15", "pos"): "position",
    ("L16", "sup"): "support_extent", ("L16", "load"): "load_extent",
    ("L17", "len"): "load_extent", ("L17", "pos"): "position",
    ("L18", "patch"): "load_extent",
    ("L19", "extent"): "domain",
    ("L20", "sup"): "support_extent", ("L20", "extent"): "domain", ("L20", "supcomp"): "support",
    ("L21", "load"): "position",
    ("L22", "pos"): "position",
    ("L23", "solid"): "passive",
    ("L24", "sup"): "support_extent", ("L24", "load"): "load_extent",
    ("L25", "sup"): "support_extent", ("L25", "load"): "load_extent",
    ("L27", "ar"): "domain",
    ("L28", "ar"): "domain",
    ("L29", "strip"): "passive",
    ("L31", "sup"): "support",
    ("L33", "load"): "load_extent", ("L33", "sup"): "support_extent",
    ("L34", "load"): "load_extent",
    ("L35", "load"): "load_extent",
    ("L36", "roller"): "support_extent", ("L36", "load"): "position",
    ("L37", "strip"): "passive", ("L37", "patch"): "load_extent", ("L37", "pad"): "passive",
    ("L38", "orient"): "domain", ("L38", "load"): "position", ("L38", "dir"): "direction",
    ("L38", "sup"): "support",
    ("L39", "ar"): "domain",
    ("L40", "ar"): "domain", ("L40", "rmin"): "setting",
    ("L41", "load"): "position",
    ("L42", "ar"): "domain", ("L42", "sup"): "support",
    ("L43", "pos"): "position", ("L43", "angle"): "direction",
    ("L44", "pos"): "position",
    ("L45", "pos"): "position", ("L45", "b"): "passive", ("L45", "dir"): "direction",
    ("L45", "rmin"): "setting",
}
RULES = {
    "entity": {"position", "domain", "passive", "support", "support_extent", "direction", "volfrac"},
    "attribute": {"position", "domain", "passive", "support", "direction", "volfrac"},
    "position_only": {"position", "domain", "direction", "volfrac"},
}


def load_task(tid):
    orc0, out = e03.oracle_from_file(tid)
    zero = pl.Oracle(ref=orc0.ref, C=orc0.C, noise={k: 0.0 for k in orc0.noise})
    return lt.TASKS[tid]["task"], zero, orc0


def survivors(interps, truth, asked):
    return [pl.ikey(t) for t in interps if all(t[s] == truth[s] for s in asked)]


def category_rule(task, orc, truth, ask_set, tid):
    interps = task.interpretations()
    answers = {s: truth[s] for s in task.mandatory}
    asked = list(task.mandatory)
    for s in task.slots:
        if s in task.mandatory:
            continue
        S = pl._surviving(interps, answers)
        if len({t[s] for t in S}) < 2:
            continue
        if CATEGORY[(tid, s)] in ask_set:
            answers[s] = truth[s]
            asked.append(s)
    commit = pl.ikey(dict(task.nominal, **answers))
    if commit not in {pl.ikey(t) for t in interps}:   # default values inadmissible with the answers: ask the rest
        for s in task.slots:
            if s not in asked and len({t[s] for t in pl._surviving(interps, answers)}) > 1:
                answers[s] = truth[s]
                asked.append(s)
        commit = pl.ikey(truth)
    return asked, commit


def score(task, orc, truth, asked, commit, tau):
    interps = task.interpretations()
    surv = survivors(interps, truth, asked)
    w = max(orc.loss(commit, k) for k in surv)
    tl = orc.loss(commit, pl.ikey(truth))
    return dict(q=len([s for s in asked if s not in task.mandatory]), unsafe=bool(w > tau), exceed=bool(tl > tau))


def category(tids):
    labelled = {(tid, s) for tid in tids for s in lt.TASKS[tid]["task"].slots
                if s not in lt.TASKS[tid]["task"].mandatory and len(lt.TASKS[tid]["task"].slots[s]) > 1}
    missing = sorted(labelled - set(CATEGORY))
    assert not missing, f"slots without a category: {missing}"
    res = {}
    for tau in TAUS:
        for rule, ask_set in RULES.items():
            tot = dict(q=0, unsafe=0, exceed=0, cases=0, bundles=0, unsafe_tasks=set())
            for tid in tids:
                task, orc, _ = load_task(tid)
                for t in task.interpretations():
                    asked, commit = category_rule(task, orc, t, ask_set, tid)
                    r = score(task, orc, t, asked, commit, tau)
                    tot["q"] += r["q"]
                    tot["unsafe"] += r["unsafe"]
                    tot["exceed"] += r["exceed"]
                    tot["cases"] += 1
                    tot["bundles"] += 1
                    if r["unsafe"]:
                        tot["unsafe_tasks"].add(tid)
            tot["unsafe_tasks"] = sorted(tot["unsafe_tasks"])
            res.setdefault(f"{tau:g}", {})[rule] = tot
    counts = {}
    for (tid, s), c in CATEGORY.items():
        if (tid, s) in labelled:
            counts[c] = counts.get(c, 0) + 1
    return dict(rules={k: sorted(v) for k, v in RULES.items()}, slot_counts=counts, by_tau=res)


def policy_totals(tids, tau=TAU):
    tot = {}
    for tid in tids:
        task, orc, _ = load_task(tid)
        interps = task.interpretations()
        for name, fn in (("CGC", pl.cgc), ("CGC_S", pl.cgc_s), ("ask_all", pl.ask_all)):
            a = tot.setdefault(name, dict(q=0, unsafe=0, bundles=0, cases=0))
            for t in interps:
                o = fn(task, orc, t, tau)
                surv = survivors(interps, t, o.asked)
                a["q"] += len([s for s in o.asked if s not in task.mandatory])
                a["unsafe"] += bool(o.released and max(orc.loss(o.commit, k) for k in surv) > tau)
                a["bundles"] += o.optimizations
                a["cases"] += 1
        nom = pl.ikey(task.nominal)
        a = tot.setdefault("silent_default", dict(unsafe_cases=0, unsafe_tasks=0, cases=0))
        n = 0
        for t in interps:
            mand = pl.ikey(dict(task.nominal, **{s: t[s] for s in task.mandatory}))
            surv = survivors(interps, t, list(task.mandatory))
            n += max(orc.loss(mand, k) for k in surv) > tau
        a["unsafe_cases"] += n
        a["unsafe_tasks"] += n > 0
        a["cases"] += len(interps)
        del nom
    return tot


def own_paper(tids):
    keep = [t for t in tids if t not in OWN]
    return dict(excluded=list(OWN), tasks=len(keep), all_tasks=policy_totals(tids), without_own=policy_totals(keep))


def pool_refs(tid, orc):
    ref = dict(orc.ref)
    src = {k: "table" for k in ref}
    for k in ref:                                   # best table design at each reading
        m = min(orc.C[(d, k)] for d in ref)
        if m < ref[k]:
            ref[k], src[k] = m, "table"
    p = os.path.join(ROOT, "results", "e03", f"robust_{tid}.json")
    if os.path.exists(p):
        with open(p) as fh:
            rob = json.load(fh)
        for k, c in zip(rob["keys"], rob["C"]):
            if k in ref and c < ref[k]:
                ref[k], src[k] = c, "robust"
    p = os.path.join(ROOT, "results", "e08", f"{tid}.json")
    if os.path.exists(p):
        with open(p) as fh:
            pol = json.load(fh)["polished"]["ref"]
        for k, c in pol.items():
            if k in ref and c < ref[k]:
                ref[k], src[k] = c, "six_start"
    return ref, src


def common_pool(tids, tau=TAU):
    out = {}
    for name, fn in (("CGC", pl.cgc), ("CGC_S", pl.cgc_s)):
        rel, over, worst_all, by_task, lowered = 0, 0, [], {}, {}
        for tid in tids:
            task, orc, _ = load_task(tid)
            ref, src = pool_refs(tid, orc)
            lowered[tid] = {k: [src[k], orc.ref[k] / ref[k] - 1] for k in ref if ref[k] < orc.ref[k] * (1 - 1e-12)}
            interps = task.interpretations()
            for t in interps:
                o = fn(task, orc, t, tau)
                if not o.released:
                    continue
                rel += 1
                surv = survivors(interps, t, o.asked)
                w = max(orc.C[(o.commit, k)] / ref[k] - 1 for k in surv)
                worst_all.append(w)
                if w > tau:
                    over += 1
                    by_task[tid] = by_task.get(tid, 0) + 1
        out[name] = dict(releases=rel, over_tau=over, over_by_task=by_task, max_worst=float(max(worst_all)),
                         margins_below_001=int(sum(tau - w < 0.01 for w in worst_all)))
    out["lowered_references"] = {t: v for t, v in lowered.items() if v}
    return out


def main():
    tids = list(lt.TASKS)
    out = dict(variant=VARIANT, tasks=len(tids), category=category(tids), own_paper=own_paper(tids),
               common_pool=common_pool(tids))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"{VARIANT}.json"), "w") as fh:
        json.dump(out, fh, indent=1, default=float)
    print(json.dumps(dict(category_005=out["category"]["by_tau"]["0.05"], slot_counts=out["category"]["slot_counts"],
                          own_paper=out["own_paper"], common_pool={k: v for k, v in out["common_pool"].items()
                                                                   if k != "lowered_references"}), indent=1))


if __name__ == "__main__":
    main()
