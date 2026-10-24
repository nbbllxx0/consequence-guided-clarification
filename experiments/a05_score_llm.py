"""Score E05: LLM-enumerated readings vs the annotated ambiguity slots, and the downstream effect.

Recall: an annotated slot counts as found in a run if the model returned at least one item whose
category is in the slot's accepted category set (ANNOT). Mandatory slots (direction sign, unstated
volume fraction) are scored separately.
Downstream: consequence-guided clarification (full_H) restricted to the slots the model found; a
missed slot is believed to take its default value. With the hidden truth ranging over all annotated
readings, a selected-truth exceedance is a release whose loss at the hidden reading exceeds tau (zero
allowance, the primary setting; exhaustive E03 tables). Compared with no_ask.
Outputs: results/e05/scores.json, results/e05/scores.md, results/e05/unmatched_items.md
"""
import glob
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import littasks as lt  # noqa: E402
import policies as pl  # noqa: E402

E05 = os.path.join(ROOT, "results", "e05")
OUT05 = os.path.join(E05, "scores" + lt.RESULTS_SUFFIX) if lt.RESULTS_SUFFIX else E05
E03 = os.path.join(ROOT, "results", "e03" + lt.RESULTS_SUFFIX)
TAU = 0.05

LP, LE, LD = "load_position", "load_extent_distribution", "load_direction"
SL, ST, DE = "support_location_extent", "support_type", "domain_extent"
PR, VF, FS = "passive_region", "volume_fraction", "filter_or_solver_setting"
# task -> slot -> accepted categories (first = primary)
ANNOT = {
    "L01": {"arm": [DE], "load": [LP], "volfrac": [VF]}, "L02": {"strip": [LE]}, "L04": {"c": [LP]},
    "L05": {"dir": [LD], "rmin": [FS]}, "L06": {"h": [LP], "width": [LE]}, "L07": {"clamp": [SL], "volfrac": [VF]},
    "L08": {"ar": [DE]}, "L09": {"sup": [SL], "load": [LP], "volfrac": [VF]},
    "L11": {"voids": [PR, DE], "dir": [LD]}, "L12": {"sup": [SL, ST], "load": [LE]}, "L13": {"load": [LP], "volfrac": [VF]},
    "L14": {"c": [LP]}, "L15": {"pos": [LP], "dir": [LD]}, "L16": {"sup": [SL], "load": [LE, LP]},
    "L17": {"len": [LE]}, "L18": {"patch": [LE]}, "L19": {"extent": [DE]}, "L20": {"extent": [DE], "sup": [SL, ST]},
    "L21": {"load": [LP], "volfrac": [VF]}, "L22": {"pos": [LP]}, "L23": {"solid": [PR]},
    "L24": {"sup": [SL], "load": [LE]}, "L25": {"sup": [SL], "load": [LE, LP]}, "L27": {"ar": [DE]},
    "L28": {"ar": [DE], "volfrac": [VF]}, "L29": {"strip": [PR]}, "L30": {"volfrac": [VF]},
    "L31": {"dir": [LD], "volfrac": [VF]}, "L33": {"load": [LE]}, "L34": {"load": [LE], "volfrac": [VF]},
    "L35": {"load": [LE], "volfrac": [VF]}, "L36": {"roller": [SL, ST], "load": [LP]},
    "L37": {"strip": [PR], "patch": [LE, PR], "volfrac": [VF]}, "L38": {"orient": [DE], "load": [LP]},
    "L39": {"ar": [DE]}, "L40": {"rmin": [FS]}, "L41": {"load": [LP]}, "L42": {"sup": [ST, SL]},
    "L43": {"pos": [LP], "angle": [LD]}, "L44": {"pos": [LP], "volfrac": [VF]},
    "L45": {"pos": [LP], "b": [PR, LE], "volfrac": [VF]},
}
# slots added by the adjudication (union variant)
ADDED = {"L02": {"vf": [VF]}, "L04": {"sup": [SL, ST], "pad": [PR]}, "L11": {"r": [PR, DE]}, "L12": {"shell": [PR]},
         "L17": {"pos": [LP]}, "L20": {"supcomp": [ST, SL]}, "L31": {"sup": [SL, ST]}, "L33": {"sup": [SL]},
         "L37": {"pad": [PR]}, "L38": {"sup": [SL, ST], "dir": [LD]}, "L40": {"ar": [DE]}, "L42": {"ar": [DE]},
         "L45": {"dir": [LD], "rmin": [FS]}}


def annot(tid):
    """Accepted categories of the slots of task `tid` in the active encoding (littasks.VARIANT)."""
    slots = lt.TASKS[tid]["task"].slots
    return {s: c for s, c in {**ANNOT[tid], **ADDED.get(tid, {})}.items() if s in slots}


def oracle(tid):
    with open(os.path.join(E03, f"{tid}.json")) as fh:
        o = json.load(fh)
    keys = o["keys"]
    C = {(d, t): o["C"][i][j] for i, d in enumerate(keys) for j, t in enumerate(keys)}
    return pl.Oracle(ref=o["ref"], C=C, noise={k: 0.0 for k in o["noise"]})     # zero allowance


def restricted_full_h(task, orc, truth, visible):
    """full_H when only `visible` slots are known to be ambiguous; others are believed nominal."""
    believed = [t for t in task.interpretations()
                if all(t[s] == task.nominal[s] for s in task.slots if s not in visible)]
    sub = pl.Task(task.name, {s: (v if s in visible else [task.nominal[s]]) for s, v in task.slots.items()},
                  task.nominal, tuple(m for m in task.mandatory if m in visible), [dict(b) for b in believed])
    fake_truth = {s: (truth[s] if s in visible else task.nominal[s]) for s in task.slots}
    o = pl.full_h(sub, orc, fake_truth, TAU)
    tk = pl.ikey(truth)
    L = orc.loss(o.commit, tk)
    return o.released and L > TAU, len(o.asked), L


def main():
    runs = {}
    for p in glob.glob(os.path.join(E05, "raw", "*", "*.json")):
        with open(p) as fh:
            r = json.load(fh)
        if r.get("parsed") and r["task"] in lt.TASKS:
            runs.setdefault(r["model"], []).append(r)
    os.makedirs(OUT05, exist_ok=True)
    res, unmatched = {}, []
    for model, rr in sorted(runs.items()):
        rec = dict(found_layout=0, total_layout=0, found_mand=0, total_mand=0, items=0, fr=0, cases=0,
                   fr_noask=0, extra_q=0.0, per_task={}, cmd_runs=sum(r.get("executed_command_events", 0) > 0 for r in rr))
        for r in rr:
            tid = r["task"]
            task = lt.TASKS[tid]["task"]
            A = annot(tid)
            cats = {it["category"] for it in r["parsed"]["items"]}
            rec["items"] += len(r["parsed"]["items"])
            found = {s for s, acc in A.items() if cats & set(acc)}
            mand = set(task.mandatory)
            lay = [s for s in A if s not in mand]
            rec["found_layout"] += len([s for s in lay if s in found])
            rec["total_layout"] += len(lay)
            rec["found_mand"] += len([s for s in mand if s in found])
            rec["total_mand"] += len(mand)
            used = {c for s in found for c in A[s]}
            for it in r["parsed"]["items"]:
                if it["effect"] == "layout":
                    rec["layout_items"] = rec.get("layout_items", 0) + 1
                    if it["category"] in used:
                        rec["matched_layout_items"] = rec.get("matched_layout_items", 0) + 1
                if it["category"] not in used and it["effect"] == "layout":
                    unmatched.append((model, tid, r["rep"], it))
            if os.path.exists(os.path.join(E03, f"{tid}.json")):
                orc = oracle(tid)
                for truth in task.interpretations():
                    fr, nq, _ = restricted_full_h(task, orc, truth, found)
                    rec["fr"] += int(fr)
                    rec["cases"] += 1
                    o = pl.no_ask(task, orc, truth, TAU)
                    rec["fr_noask"] += int(o.released and orc.loss(o.commit, pl.ikey(truth)) > TAU)
            pt = rec["per_task"].setdefault(tid, [])
            pt.append(sorted(found))
        rec["recall_layout"] = rec["found_layout"] / max(rec["total_layout"], 1)
        rec["recall_mandatory"] = rec["found_mand"] / max(rec["total_mand"], 1)
        rec["runs"] = len(rr)
        rec["mean_items"] = rec["items"] / max(len(rr), 1)
        rec["mean_layout_items"] = rec.get("layout_items", 0) / max(len(rr), 1)
        # share of the model's layout items that fall in an annotated slot category (precision proxy)
        rec["layout_precision"] = rec.get("matched_layout_items", 0) / max(rec.get("layout_items", 0), 1)
        res[model] = rec
    with open(os.path.join(OUT05, "scores.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    lines = ["| model | runs | layout-slot recall | mandatory-slot recall | items per run | layout items per run "
             "| layout items in annotated categories | selected-truth exceedances (LLM slots) | selected-truth exceedances (no_ask) | cases "
             "| runs that executed commands |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for m, v in res.items():
        lines.append(f"| {m} | {v['runs']} | {v['recall_layout']:.2f} ({v['found_layout']}/{v['total_layout']}) | "
                     f"{v['recall_mandatory']:.2f} ({v['found_mand']}/{v['total_mand']}) | {v['mean_items']:.1f} | "
                     f"{v['mean_layout_items']:.1f} | {v['layout_precision']:.2f} | "
                     f"{v['fr']} | {v['fr_noask']} | {v['cases']} | {v['cmd_runs']} |")
    with open(os.path.join(OUT05, "scores.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(os.path.join(OUT05, "unmatched_items.md"), "w", encoding="utf-8") as fh:
        fh.write("# LLM 'layout' items whose category matched no annotated slot (candidates for annotation review)\n\n")
        for m, tid, rep, it in unmatched:
            fh.write(f"- {m} {tid} r{rep} [{it['category']}] {it['entity']}: {it['description'][:300]} "
                     f"| readings: {'; '.join(it['readings'][:4])[:300]}\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
