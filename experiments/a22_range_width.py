"""A22: sensitivity of the replay to the width of the vague-position ranges (halved ranges).

For the load-position tasks with an author-chosen convention range, each sampled offset from the nominal
value is halved (the default value is kept), new readings are optimized (two starts, the primary
settings), and the silent default, ask-all, CGC and CGC-S are replayed at zero allowance on the halved
encoding and, for comparison, on the original encoding.
Usage: python experiments/a22_range_width.py [task ...]
Output: results/a22/range_width.json
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

OUT = os.path.join(ROOT, "results", "a22")
SLOTS = {"L04": "c", "L14": "c", "L36": "load", "L41": "load", "L43": "pos"}
TAU = e03.TAU


def halved_task(tid):
    task = lt.TASKS[tid]["task"]
    s = SLOTS[tid]
    nom = task.nominal[s]
    vals = sorted({round(nom + (v - nom) / 2, 6) for v in task.slots[s]})
    slots = dict(task.slots, **{s: vals})
    return pl.Task(tid + "_half", slots, dict(task.nominal), tuple(task.mandatory)), vals


def replay(task, orc):
    zero = pl.Oracle(ref=orc.ref, C=orc.C, noise={k: 0.0 for k in orc.noise})
    interps = task.interpretations()
    nom = pl.ikey(task.nominal)
    out = dict(nominal_max_loss=float(max(zero.loss(nom, pl.ikey(t)) for t in interps)))
    for name, fn in (("no_ask", pl.no_ask), ("ask_all", pl.ask_all), ("CGC", pl.cgc), ("CGC_S", pl.cgc_s)):
        q = rel = unsafe = bundles = 0
        for t in interps:
            o = fn(task, zero, t, TAU)
            surv = [pl.ikey(x) for x in interps if all(x[s] == t[s] for s in o.asked)]
            q += len([s for s in o.asked if s not in task.mandatory])
            rel += o.released
            unsafe += bool(o.released and max(zero.loss(o.commit, k) for k in surv) > TAU)
            bundles += o.optimizations
        out[name] = dict(cases=len(interps), questions=q, released=rel, unsafe=unsafe, bundles=bundles)
    return out


def main():
    tids = sys.argv[1:] or list(SLOTS)
    res = {}
    for tid in tids:
        T = lt.TASKS[tid]
        st = e03.settings_for(T["dim"])
        task, vals = halved_task(tid)
        specs = {pl.ikey(t): T["build"](t) for t in task.interpretations()}
        orc, info = e08.table(tid, specs, e03.INITS, st, nominal=pl.ikey(task.nominal))
        orig, _ = e03.oracle_from_file(tid)
        res[tid] = dict(slot=SLOTS[tid], original=T["task"].slots[SLOTS[tid]], halved=vals,
                        accepted=all(info["accepted"].values()),
                        halved_replay=replay(task, orc), original_replay=replay(T["task"], orig))
        h, o = res[tid]["halved_replay"], res[tid]["original_replay"]
        print(tid, "nominal max loss", round(o["nominal_max_loss"], 4), "->", round(h["nominal_max_loss"], 4),
              "CGC q", o["CGC"]["questions"], "->", h["CGC"]["questions"],
              "ask-all q", o["ask_all"]["questions"], "->", h["ask_all"]["questions"], flush=True)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "range_width.json"), "w") as fh:
        json.dump(res, fh, indent=1, default=float)


if __name__ == "__main__":
    main()
