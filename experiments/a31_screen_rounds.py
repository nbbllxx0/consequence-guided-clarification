"""A31: reference-free compliance-jump screen and interaction rounds (reviewer requests, loop v5 round 2).

From the stored E03 tables (no new optimization), at zero allowance and tau = 0.05.
  jump_screen(J)  release the default design (mandatory answers applied) if it is feasible at every open
                  reading and its compliance there is at most J times its compliance at its own reading;
                  otherwise ask every remaining varying slot in one batch and release the identified
                  reading's reference. It needs no reference of any other reading: one bundle, plus one
                  when it asks. Scored strictly against the full best-known table.
  rounds          interaction rounds per case: mandatory questions form one round; ask-all sends every
                  question in that round; CGC and CGC-S send each further question in its own round; the
                  default check (N_ask_all) sends its remaining questions in one further round.
Usage: python experiments/a31_screen_rounds.py
Output: results/a31/consensus.json
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["LT_VARIANT"] = "consensus"
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import a17_nominal_controls as a17  # noqa: E402
import e03_literature_tasks as e03  # noqa: E402
import littasks as lt  # noqa: E402
import policies as pl  # noqa: E402

TAU = e03.TAU
JS = (1.1, 1.25, 1.5, 2.0, 5.0, 10.0)
OUT = os.path.join(ROOT, "results", "a31")


def jump_screen(task, orc, truth, J):
    interps = task.interpretations()
    keys = {pl.ikey(t) for t in interps}
    answers = {s: truth[s] for s in task.mandatory}
    S = pl._surviving(interps, answers)
    d = pl.ikey(dict(task.nominal, **answers))
    ok = d in keys
    if ok:
        own = orc.C[(d, d)]
        ok = all(np.isfinite(orc.C[(d, pl.ikey(t))]) and orc.C[(d, pl.ikey(t))] <= J * own for t in S)
    if ok:
        return 0, d, S, 1
    rest = a17.varying(task, S, list(task.mandatory))
    return len(rest), pl.ikey(truth), S, 2


def main():
    tids = list(lt.TASKS)
    screen = {f"{J:g}": dict(q=0, unsafe=0, exceed=0, bundles=0, cases=0) for J in JS}
    rounds = {p: dict(rounds=0, cases_with_question=0, max_rounds=0) for p in ("ask_all", "CGC", "CGC_S", "N_ask_all")}
    for tid in tids:
        task, orc = a17.load_task(tid)
        interps = task.interpretations()
        m = len(task.mandatory)
        for t in interps:
            tk = pl.ikey(t)
            for J in JS:
                q, d, S, b = jump_screen(task, orc, t, J)
                a = screen[f"{J:g}"]
                a["q"] += q
                a["bundles"] += b
                a["cases"] += 1
                if q == 0:
                    w = max(orc.loss(d, pl.ikey(x)) for x in S)
                    a["unsafe"] += bool(w > TAU)
                    a["exceed"] += bool(orc.loss(d, tk) > TAU)
            o_all = pl.ask_all(task, orc, t, TAU)
            o_cgc = pl.cgc(task, orc, t, TAU)
            o_s = pl.cgc_s(task, orc, t, TAU)
            asked_n, _, _, _, _ = a17.nominal_check(task, orc, t, TAU, "ask_all")
            per = {
                "ask_all": 1 if o_all.asked else 0,
                "CGC": (1 if m else 0) + len([s for s in o_cgc.asked if s not in task.mandatory]),
                "CGC_S": (1 if m else 0) + len([s for s in o_s.asked if s not in task.mandatory]),
                "N_ask_all": (1 if m else 0) + (1 if len(asked_n) > m else 0),
            }
            for p, r in per.items():
                rounds[p]["rounds"] += r
                rounds[p]["cases_with_question"] += r > 0
                rounds[p]["max_rounds"] = max(rounds[p]["max_rounds"], r)
    out = dict(tau=TAU, tasks=len(tids), jump_screen=screen, rounds=rounds)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "consensus.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
