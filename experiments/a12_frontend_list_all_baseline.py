"""Reference for the E05 front-end scores: a non-model detector that lists one layout item in every category.

Scored with the same rules as experiments/a05_score_llm.py (category recall, share of listed layout items in an
encoded category, downstream CGC restricted to detected slots). It needs no paper text, so any front-end score
that it matches does not show text understanding.
Output: results/e05/list_all_baseline.json
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import littasks as lt  # noqa: E402
import policies as pl  # noqa: E402
from a05_score_llm import E03, OUT05, TAU, annot, oracle, restricted_full_h  # noqa: E402

with open(os.path.join(ROOT, "v4", "prompts", "output_schema.json"), encoding="utf-8") as fh:
    CATS = json.load(fh)["properties"]["items"]["items"]["properties"]["category"]["enum"]


def main():
    rec = dict(found_layout=0, total_layout=0, found_mand=0, total_mand=0, layout_items=0, matched_layout_items=0,
               fr=0, fr_noask=0, cases=0, tasks=0)
    for tid in lt.TASKS:
        task = lt.TASKS[tid]["task"]
        A = annot(tid)
        found = {s for s, acc in A.items() if set(CATS) & set(acc)}
        mand = set(task.mandatory)
        lay = [s for s in A if s not in mand]
        rec["tasks"] += 1
        rec["found_layout"] += len([s for s in lay if s in found])
        rec["total_layout"] += len(lay)
        rec["found_mand"] += len([s for s in mand if s in found])
        rec["total_mand"] += len(mand)
        used = {c for s in found for c in A[s]}
        rec["layout_items"] += len(CATS)
        rec["matched_layout_items"] += len([c for c in CATS if c in used])
        if os.path.exists(os.path.join(E03, f"{tid}.json")):
            orc = oracle(tid)
            for truth in task.interpretations():
                fr, _, _ = restricted_full_h(task, orc, truth, found)
                rec["fr"] += int(fr)
                rec["cases"] += 1
                o = pl.no_ask(task, orc, truth, TAU)
                rec["fr_noask"] += int(o.released and orc.loss(o.commit, pl.ikey(truth)) > TAU)
    rec["recall_layout"] = rec["found_layout"] / max(rec["total_layout"], 1)
    rec["recall_mandatory"] = rec["found_mand"] / max(rec["total_mand"], 1)
    rec["layout_precision"] = rec["matched_layout_items"] / max(rec["layout_items"], 1)
    rec["layout_items_per_task"] = rec["layout_items"] / max(rec["tasks"], 1)
    os.makedirs(OUT05, exist_ok=True)
    with open(os.path.join(OUT05, "list_all_baseline.json"), "w") as fh:
        json.dump(rec, fh, indent=1)
    print(json.dumps(rec, indent=1))


if __name__ == "__main__":
    main()
