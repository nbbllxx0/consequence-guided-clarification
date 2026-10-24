"""Agreement between the first annotation (src/littasks.py in the active LT_VARIANT, categories from a05_score_llm.annot) and the blind
Codex re-annotation (results/e06/raw). Unit: (task, group) presence over coarse boundary-value groups (GROUP), applied symmetrically;
that the annotation convention covers; Cohen's kappa and raw agreement. Items tagged scale_only and the
categories outside the convention (material, mesh, filter_or_solver_setting unless a task annotates it,
other) are listed separately. Disagreements are written for adjudication.
Output: results/e06/agreement.json, results/e06/disagreements.md
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
from a05_score_llm import annot, lt  # noqa: E402

E06 = os.path.join(ROOT, "results", "e06")
OUT06 = os.path.join(E06, "agreement" + lt.RESULTS_SUFFIX) if lt.RESULTS_SUFFIX else E06
COVERED = ["domain_extent", "support_location_extent", "support_type", "load_position",
           "load_extent_distribution", "load_direction", "volume_fraction", "passive_region"]
# coarse groups used symmetrically for both annotations (position vs extent of a load, and location vs
# type of a support, are not separated reliably by either annotator)
GROUP = {"domain_extent": "domain", "support_location_extent": "support", "support_type": "support",
         "load_position": "load_pos_ext", "load_extent_distribution": "load_pos_ext", "load_direction": "load_dir",
         "volume_fraction": "volume_fraction", "passive_region": "passive"}
GROUPS = ["domain", "support", "load_pos_ext", "load_dir", "volume_fraction", "passive"]


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0, po


def main():
    os.makedirs(OUT06, exist_ok=True)
    recs = {}
    for p in glob.glob(os.path.join(E06, "raw", "*.json")):
        with open(p) as fh:
            r = json.load(fh)
        if r.get("parsed") and r["task"] in lt.TASKS:
            recs[r["task"]] = r
    A, B, dis, outside = [], [], [], []
    for tid in sorted(recs):
        # symmetric unit: (task, group); both annotations are mapped to the same coarse groups
        A_ = annot(tid)
        first = {GROUP[A_[s][0]] for s in A_ if A_[s][0] in GROUP}
        first_any = {c for s in A_ for c in A_[s]}
        items = [it for it in recs[tid]["parsed"]["items"] if it["effect"] != "scale_only"]
        second = {GROUP[it["category"]] for it in items if it["category"] in GROUP}
        for c in GROUPS:
            a = c in first
            b = c in second
            A.append(int(a))
            B.append(int(b))
            if a != b:
                ex = [it for it in items if GROUP.get(it["category"]) == c] if b else []
                dis.append(dict(task=tid, category=c, first=a, second=b,
                                second_items=[dict(entity=i["entity"], readings=i["readings"][:4],
                                                   evidence=i.get("evidence", "")) for i in ex]))
        for it in items:
            if it["category"] not in COVERED and it["category"] not in first_any:
                outside.append(dict(task=tid, category=it["category"], entity=it["entity"]))
    k, po = kappa(A, B)
    out = dict(tasks=len(recs), units=len(A), kappa=k, raw_agreement=po, first_positive=sum(A),
               second_positive=sum(B), both_positive=sum(a and b for a, b in zip(A, B)),
               disagreements=len(dis), outside_convention_items=len(outside),
               outside_by_category={c: sum(o["category"] == c for o in outside) for c in {o["category"] for o in outside}},
               runs_with_commands=sum(r.get("executed_command_events", 0) > 0 for r in recs.values()))
    with open(os.path.join(OUT06, "agreement.json"), "w") as fh:
        json.dump(dict(out, disagreement_list=dis, outside=outside), fh, indent=1)
    with open(os.path.join(OUT06, "disagreements.md"), "w", encoding="utf-8") as fh:
        fh.write(f"# First annotation vs blind Codex re-annotation\n\nkappa = {k:.3f}, raw agreement = {po:.3f} "
                 f"over {len(A)} (task, group) units; {len(dis)} disagreements.\n\n")
        for d in dis:
            fh.write(f"- {d['task']} [{d['category']}] first={d['first']} second={d['second']}\n")
            for i in d["second_items"]:
                fh.write(f"    - {i['entity']}: {'; '.join(i['readings'])[:300]} ({i['evidence'][:150]})\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
