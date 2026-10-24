"""Summarize E03 (results/e03/replay.json + per-task oracle tables) across tasks.

Per policy: tasks, mean questions beyond the mandatory ones, total false releases (truth-agnostic,
counted per hidden truth), tasks with any false release, mean optimizations, and max true loss.
Per task: consequence class from the exhaustive table (worst loss of the default design over the
admissible readings): harmless (<= tau + noise), consequential (> tau), unsupported (> 10, where the
value scales with Emin because a load meets near-void material), infeasible (the default design
violates another reading's volume, passive region or length scale).
"Extra questions" = questions about non-mandatory slots.
Output: results/e03/summary.json and results/e03/summary.md
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import e03_literature_tasks as e03  # noqa: E402
import littasks as lt  # noqa: E402
import runner  # noqa: E402
import policies as pl  # noqa: E402

E03 = os.path.join(ROOT, "results", "e03" + lt.RESULTS_SUFFIX)
TAU = 0.05
UNSUPPORTED = 10.0


def task_class(tid):
    with open(os.path.join(E03, f"{tid}.json")) as fh:
        o = json.load(fh)
    keys = o["keys"]
    C = np.array(o["C"], float)
    ref = np.array([o["ref"][k] for k in keys])
    noise = np.array([o["noise"][k] for k in keys])
    nom = pl.ikey(lt.TASKS[tid]["task"].nominal)
    i = keys.index(nom)
    L = C[i] / ref - 1 - noise
    worst = float(np.max(L))
    if not np.isfinite(worst):
        cls = "infeasible"            # default design violates another reading's volume, passive or length scale
    else:
        cls = "harmless" if worst <= TAU else ("large_loss" if worst > UNSUPPORTED else "consequential")
    return dict(n=len(keys), nominal_worst=worst, cls=cls, dim=o["dim"],
                ref_gap_max=float(max(o["ref_gap_beaten"].values())), noise_max=float(noise.max()))


def kkt_selected(tids):
    """Projected-gradient residual of the selected (lower-compliance) start of every reference bundle."""
    ks = []
    for tid in tids:
        specs, st, _ = e03.jobs_for(tid)
        for sp in specs.values():
            rr = [runner.load(runner.job_key(sp, i, st)) for i in e03.INITS]
            ks.append(min(rr, key=lambda r: r["compliance"])["kkt"])
    return dict(references=len(ks), gt_0p1=int(sum(x > 0.1 for x in ks)), gt_0p5=int(sum(x > 0.5 for x in ks)))


def slots_hist(tids):
    """Number of tasks by count of varying non-mandatory slots."""
    h = {}
    for t in tids:
        task = lt.TASKS[t]["task"]
        n = len([s for s, v in task.slots.items() if len(v) > 1 and s not in task.mandatory])
        h[n] = h.get(n, 0) + 1
    return {str(k): h[k] for k in sorted(h)}


def main():
    with open(os.path.join(E03, "replay.json")) as fh:
        rp = json.load(fh)
    tids = [t for t in rp if t in lt.TASKS]
    classes = {t: task_class(t) for t in tids}
    pols = sorted({p for t in tids for p in rp[t] if not p.startswith("_")})
    summ = {}
    for p in pols:
        have = [t for t in tids if p in rp[t]]
        rows = [r for t in have for r in rp[t]["_rows"][p]]
        mand = {t: set(lt.TASKS[t]["task"].mandatory) for t in have}
        extra_q = [len([s for s in r["asked"] if s not in mand[t]]) for t in have for r in rp[t]["_rows"][p]]
        summ[p] = dict(tasks=len(have), cases=len(rows), mean_questions=float(np.mean([r["n_asked"] for r in rows])),
                       mean_extra_questions=float(np.mean(extra_q)),
                       false_releases=int(sum(r["false_release_any"] for r in rows)),
                       truth_exceedances=int(sum(r.get("truth_exceed", False) for r in rows)),
                       releases=int(sum(r["released"] for r in rows)),
                       total_extra_questions=int(sum(extra_q)),
                       mean_optimizations_task_weighted=float(np.mean([np.mean([r["optimizations"] for r in
                                                                                rp[t]["_rows"][p]]) for t in have])),
                       tasks_with_false_release=int(sum(rp[t][p]["false_release_any"] > 0 for t in have)),
                       mean_optimizations=float(np.mean([r["optimizations"] for r in rows])),
                       max_true_loss=float(np.max([r["true_loss"] for r in rows])))
    # hindsight check: CGC question count vs the fewest questions over all question subsets (exact table)
    hind = {}
    for p, o in (("CGC", "oracle"), ("CGC_a0", "oracle_a0")):
        pairs = [(a, b) for t in tids if p in rp[t]["_rows"] and o in rp[t]["_rows"]
                 for a, b in zip(rp[t]["_rows"][p], rp[t]["_rows"][o])]
        hind[f"{p}_vs_{o}"] = dict(cases=len(pairs), equal_count=sum(a["n_asked"] == b["n_asked"] for a, b in pairs),
                                   more_than_hindsight=sum(a["n_asked"] > b["n_asked"] for a, b in pairs),
                                   different_questions=sum(a["asked"] != b["asked"] for a, b in pairs))
    cls_counts = {}
    for t, c in classes.items():
        cls_counts.setdefault(f"{c['dim']}D", {}).setdefault(c["cls"], 0)
        cls_counts[f"{c['dim']}D"][c["cls"]] += 1
    out = dict(tau=TAU, n_tasks=len(tids), n_cases=sum(c["n"] for c in classes.values()), classes=cls_counts,
               per_task=classes, policies=summ, hindsight=hind,
               slots_per_task=slots_hist(tids), kkt_selected=kkt_selected(tids))
    with open(os.path.join(E03, "summary.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    lines = [f"# E03 summary ({len(tids)} tasks, {out['n_cases']} hidden-truth cases, tau = {TAU})", "",
             "Default-design consequence class per dimension: " + json.dumps(cls_counts), "",
             "| policy | tasks | mean questions | non-mandatory questions (total) | releases | pool-unsafe releases "
             "(cases) | selected-truth exceedances | tasks with a pool-unsafe release | reference bundles per case "
             "(case-weighted / task-weighted) |", "|---|---|---|---|---|---|---|---|---|"]
    for p, v in summ.items():
        lines.append(f"| {p} | {v['tasks']} | {v['mean_questions']:.2f} | {v['total_extra_questions']} | "
                     f"{v['releases']} | {v['false_releases']} | {v['truth_exceedances']} | "
                     f"{v['tasks_with_false_release']} | {v['mean_optimizations']:.2f} / {v['mean_optimizations_task_weighted']:.2f} |")
    lines += ["", "| task | dim | readings | class | default-design worst loss | max ref gap | max noise |",
              "|---|---|---|---|---|---|---|"]
    for t, c in classes.items():
        lines.append(f"| {t} | {c['dim']} | {c['n']} | {c['cls']} | {c['nominal_worst']:.3g} | "
                     f"{c['ref_gap_max']:.3g} | {c['noise_max']:.2g} |")
    with open(os.path.join(E03, "summary.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines[:12 + len(summ)]))


if __name__ == "__main__":
    main()
