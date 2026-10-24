"""A11: question budget in the union encoding. CGC and CGC-S with budget 3 (as in E03) and 4 on the union
tasks where they withhold release (L38, L45; four open slots), zero allowance, exhaustive E03 tables.
Output: results/a11/budget.json
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["LT_VARIANT"] = "union"
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import e03_literature_tasks as e03  # noqa: E402
import littasks as lt  # noqa: E402
import policies as pl  # noqa: E402

OUT = os.path.join(ROOT, "results", "a11")


def main():
    res = {}
    for tid in ("L38", "L45"):
        orc, _ = e03.oracle_from_file(tid)
        zero = pl.Oracle(ref=orc.ref, C=orc.C, noise={k: 0.0 for k in orc.noise})
        task = lt.TASKS[tid]["task"]
        interps = task.interpretations()
        for name, fn in (("CGC", pl.cgc), ("CGC_S", pl.cgc_s)):
            for budget in (3, 4):
                rows = []
                for truth in interps:
                    o = fn(task, zero, truth, e03.TAU, budget=budget)
                    ans = {s: truth[s] for s in o.asked}
                    surv = [pl.ikey(t) for t in interps if all(t[s] == v for s, v in ans.items())]
                    worst = max(zero.loss(o.commit, k) for k in surv) if o.commit else float("inf")
                    rows.append(dict(released=o.released, unsafe=bool(o.released and worst > e03.TAU),
                                     questions=len([s for s in o.asked if s not in task.mandatory]),
                                     bundles=o.optimizations))
                res[f"{tid}_{name}_budget{budget}"] = dict(
                    cases=len(rows), released=sum(r["released"] for r in rows), unsafe=sum(r["unsafe"] for r in rows),
                    questions=sum(r["questions"] for r in rows), bundles=sum(r["bundles"] for r in rows))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "budget.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
