"""A13: does the minimax question choice matter once the release check is fixed?

CGC (greedy minimax question) against CGC_fixed (same full-table release check, same budget and candidates,
questions in a fixed slot order) on every task of the chosen encoding, zero allowance, exhaustive E03 tables.
Fixed orders: the declared slot order, its reverse, and, per task, the best and the worst of all slot
permutations (chosen in hindsight, so not deployable).
Usage: python experiments/a13_fixed_order_control.py [consensus|union]
Output: results/a13/fixed_order_<variant>.json
"""
import itertools
import json
import os
import sys

VARIANT = sys.argv[1] if len(sys.argv) > 1 else "consensus"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["LT_VARIANT"] = VARIANT
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import e03_literature_tasks as e03  # noqa: E402
import littasks as lt  # noqa: E402
import policies as pl  # noqa: E402

OUT = os.path.join(ROOT, "results", "a13")


def run(fn, task, orc, interps):
    tot = dict(cases=0, released=0, unsafe=0, exceed=0, questions=0)
    for truth in interps:
        o = fn(truth)
        ans = {s: truth[s] for s in o.asked}
        surv = [pl.ikey(t) for t in interps if all(t[s] == v for s, v in ans.items())]
        worst = max(orc.loss(o.commit, k) for k in surv)
        tot["cases"] += 1
        tot["released"] += int(o.released)
        tot["unsafe"] += int(o.released and worst > e03.TAU)
        tot["exceed"] += int(o.released and orc.loss(o.commit, pl.ikey(truth)) > e03.TAU)
        tot["questions"] += len([s for s in o.asked if s not in task.mandatory])
    return tot


def add(acc, name, tot):
    a = acc.setdefault(name, dict(cases=0, released=0, unsafe=0, exceed=0, questions=0))
    for k, v in tot.items():
        a[k] += v


def main():
    acc, per_task = {}, {}
    for tid in lt.TASKS:
        orc0, _ = e03.oracle_from_file(tid)
        orc = pl.Oracle(ref=orc0.ref, C=orc0.C, noise={k: 0.0 for k in orc0.noise})
        task = lt.TASKS[tid]["task"]
        interps = task.interpretations()
        free = [s for s in task.slots if s not in task.mandatory and len(task.slots[s]) > 1]
        cgc = run(lambda t: pl.cgc(task, orc, t, e03.TAU), task, orc, interps)
        perms = {p: run(lambda t, p=p: pl.cgc_fixed(task, orc, t, e03.TAU, order=list(p)), task, orc, interps)
                 for p in itertools.permutations(free)} or {(): cgc}
        declared = perms[tuple(free)]
        reverse = perms[tuple(reversed(free))]

        def rank(r):
            return (-r["released"], r["unsafe"], r["questions"])
        best = min(perms.values(), key=rank)
        worst = max(perms.values(), key=rank)
        for name, tot in (("CGC", cgc), ("fixed_declared", declared), ("fixed_reverse", reverse),
                          ("fixed_best_hindsight", best), ("fixed_worst_hindsight", worst)):
            add(acc, name, tot)
        per_task[tid] = dict(free_slots=len(free), CGC=cgc["questions"], declared=declared["questions"],
                             reverse=reverse["questions"], best=best["questions"], worst=worst["questions"],
                             released=dict(CGC=cgc["released"], declared=declared["released"],
                                           reverse=reverse["released"], worst=worst["released"]))
    acc["tasks_by_free_slots"] = {n: sum(v["free_slots"] == n for v in per_task.values())
                                  for n in sorted({v["free_slots"] for v in per_task.values()})}
    res = dict(variant=VARIANT, totals=acc, per_task=per_task)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"fixed_order_{VARIANT}.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(acc, indent=1))


if __name__ == "__main__":
    main()
