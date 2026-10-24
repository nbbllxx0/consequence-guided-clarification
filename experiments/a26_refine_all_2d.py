"""A26: 2x mesh refinement of every two-dimensional task not refined in E08 (reviewer request, loop v5 round 1).

E08 refined nine tasks chosen near the tolerance. Here every remaining 2-D task is rebuilt at scale 2
(filter radius and patch sizes scaled, as in E08), optimized from the two primary starts, and cross-
evaluated. Reported per task: the base and refined full-table minimax loss B and default-design worst loss,
whether the CGC / CGC-S question counts and release flags of the base replay are unchanged, and the base
releases re-scored on the refined table (the refined design of the released reading against the refined
references of its open readings).
Usage: python experiments/a26_refine_all_2d.py [task ...]
Output: results/a26/<tid>.json, results/a26/summary.json
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["LT_VARIANT"] = "consensus"
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import e03_literature_tasks as e03  # noqa: E402
import e08_near_threshold as e08  # noqa: E402
import littasks as lt  # noqa: E402
import policies as pl  # noqa: E402

OUT = os.path.join(ROOT, "results", "a26")
DONE_E08 = {"L11", "L16", "L18", "L20", "L21", "L24", "L25", "L36", "L37"}
TAU = e03.TAU


def rescore(tid, base, ref):
    task = lt.TASKS[tid]["task"]
    interps = task.interpretations()
    out = {}
    for name, fn in (("CGC", pl.cgc), ("CGC_S", pl.cgc_s)):
        worst, n_rel, over = [], 0, 0
        for t in interps:
            o = fn(task, base, t, TAU)
            if not o.released:
                continue
            n_rel += 1
            surv = [pl.ikey(x) for x in interps if all(x[s] == t[s] for s in o.asked)]
            w = max(ref.C[(o.commit, k)] / ref.ref[k] - 1 for k in surv)
            worst.append(w)
            over += w > TAU
        out[name] = dict(releases=n_rel, over_tau_refined=over, max_refined=max(worst) if worst else None)
    return out


def main():
    tids = sys.argv[1:] or [t for t in lt.TASKS if lt.TASKS[t]["dim"] == 2 and t not in DONE_E08]
    sp = os.path.join(OUT, "summary.json")
    summ = json.load(open(sp)) if os.path.exists(sp) else {}
    os.makedirs(OUT, exist_ok=True)
    for tid in tids:
        st = e03.settings_for(2)
        orc_b, info_b = e08.table(tid, e08.specs_for(tid, 1), e03.INITS, st)
        orc0, _ = e03.oracle_from_file(tid)
        base_match = all(abs(orc_b.ref[k] / orc0.ref[k] - 1) < 1e-9 for k in orc0.ref)
        orc_r, info_r = e08.table(tid, e08.specs_for(tid, 2), e03.INITS, e08.settings(2, True))
        zb = pl.Oracle(ref=orc_b.ref, C=orc_b.C, noise={k: 0.0 for k in orc_b.ref})
        zr = pl.Oracle(ref=orc_r.ref, C=orc_r.C, noise={k: 0.0 for k in orc_r.ref})
        rb, rr = e08.replay(tid, zb), e08.replay(tid, zr)
        stable = {p: all(x["n_asked"] == y["n_asked"] and x["released"] == y["released"]
                         for x, y in zip(rb[p], rr[p])) for p in ("CGC", "CGC_S")}
        res = dict(base=dict(info_b, replay=rb), refined_x2=dict(info_r, replay=rr), base_matches_e03=base_match,
                   stable=stable, rescored=rescore(tid, zb, zr))
        with open(os.path.join(OUT, f"{tid}.json"), "w") as fh:
            json.dump(res, fh, indent=1)
        summ[tid] = dict(B=info_b["B"], B_refined=info_r["B"], B_nominal=info_b["B_nominal"],
                         B_nominal_refined=info_r["B_nominal"], accepted_refined=all(info_r["accepted"].values()),
                         base_matches_e03=base_match, stable=stable, rescored=res["rescored"])
        print(tid, json.dumps(summ[tid]), flush=True)
        with open(sp, "w") as fh:
            json.dump(summ, fh, indent=1)


if __name__ == "__main__":
    main()
