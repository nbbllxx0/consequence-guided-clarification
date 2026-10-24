"""A30: replay with the certified loss (reviewer request, loop v5 round 2; no new optimization).

The A27 bound L_t is a certified lower bound on the optimal compliance of reading t, so
C_t(d) / L_t - 1 is a certified upper bound on the loss of design d against the true optimum.
Replacing the best-known reference V_t by L_t in the release check gives a conservative rule: every
release it makes is within tau of the optimum at every open reading. This script replays full CGC
(question budget unlimited, so that a withheld release means no computed design can be certified even
after all answers) and ask-all with that loss, at several tolerances, and reports questions, releases
and the number of cases in which even the fully answered reference cannot be certified.
Usage: python experiments/a30_certified_replay.py
Output: results/a30/consensus.json
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["LT_VARIANT"] = "consensus"
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import e03_literature_tasks as e03  # noqa: E402
import littasks as lt  # noqa: E402
import policies as pl  # noqa: E402

OUT = os.path.join(ROOT, "results", "a30")
TAUS = (0.05, 0.10, 0.15, 0.20, 0.30, 0.50)
BUDGET = 99


def bounds(tid):
    with open(os.path.join(ROOT, "results", "a27", f"{tid}.json")) as fh:
        return {k: v["L"] for k, v in json.load(fh)["bound"].items()}


def main():
    tids = list(lt.TASKS)
    res = {}
    for tau in TAUS:
        acc = dict(cases=0, cgc_q=0, cgc_released=0, ask_all_q=0, ask_all_certified=0,
                   reference_uncertified=0, tasks_all_released=0, cgc_q_released=0, ask_all_q_released=0)
        for tid in tids:
            task = lt.TASKS[tid]["task"]
            orc0, _ = e03.oracle_from_file(tid)
            L = bounds(tid)
            cert = pl.Oracle(ref=L, C=orc0.C, noise={k: 0.0 for k in L})
            n_rel = 0
            interps = task.interpretations()
            for t in interps:
                tk = pl.ikey(t)
                o = pl.cgc(task, cert, t, tau, budget=BUDGET)
                a = pl.ask_all(task, cert, t, tau)
                acc["cases"] += 1
                acc["cgc_q"] += len([s for s in o.asked if s not in task.mandatory])
                acc["cgc_released"] += bool(o.released)
                n_rel += bool(o.released)
                acc["ask_all_q"] += len([s for s in a.asked if s not in task.mandatory])
                ok = cert.loss(tk, tk) <= tau
                if o.released:
                    acc["cgc_q_released"] += len([s for s in o.asked if s not in task.mandatory])
                if ok:
                    acc["ask_all_q_released"] += len([s for s in a.asked if s not in task.mandatory])
                acc["ask_all_certified"] += ok
                acc["reference_uncertified"] += not ok
            acc["tasks_all_released"] += n_rel == len(interps)
        res[f"{tau:.2f}"] = acc
        print(f"tau={tau:.2f}", acc, flush=True)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "consensus.json"), "w") as fh:
        json.dump(dict(tasks=len(tids), budget=BUDGET, by_tau=res), fh, indent=1)


if __name__ == "__main__":
    main()
