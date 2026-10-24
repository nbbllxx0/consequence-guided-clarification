"""A10: agreement between the two author adjudications of the literature-task encodings.

Records: tasks/adjudication/A_shaoliang.txt (adjudicator A) and tasks/adjudication/B_jun_wang.txt
(adjudicator B). The decisions below are transcribed from those records; src/littasks.py
(ADJUDICATION) implements the resulting consensus and union encodings.
Unit: one candidate ambiguity slot = every non-mandatory slot of the pre-adjudication encoding plus
every slot an adjudicator proposed to add. A unit is "open" for an adjudicator who accepts at least
two readings of it. Mandatory slots are kept by rule by both and reported separately.
Output: results/a10/adjudication.json, results/a10/adjudication.md
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["LT_VARIANT"] = "pre"
sys.path.insert(0, os.path.join(ROOT, "src"))
import littasks as lt  # noqa: E402

OUT = os.path.join(ROOT, "results", "a10")

# encoded slots that adjudicator A resolves to one stated value (A's CHANGE boxes)
A_CLOSED = {("L05", "rmin"): "1.5", ("L07", "clamp"): "left_edge", ("L17", "len"): "full", ("L19", "extent"): "half",
            ("L20", "extent"): "half", ("L27", "ar"): "square", ("L40", "rmin"): "1.5", ("L42", "sup"): "pins"}
# encoded slots whose value set adjudicator B extends (B's CHANGE boxes)
B_EXTENDED = {("L02", "strip"): "full", ("L21", "load"): "0.75 H", ("L23", "solid"): "0.10", ("L36", "roller"): "nodes5"}
# slots proposed by an adjudicator; A addressed each (one reading kept), B opened each.
# L02 vf: both change the value (A: 1/6 only; B: 0.5 or 1/6). L04 len: not encoded (Fig. 9(a) labels the height L).
PROPOSED = [("L02", "vf"), ("L04", "len"), ("L04", "sup"), ("L04", "pad"), ("L11", "r"), ("L12", "shell"),
            ("L17", "pos"), ("L20", "supcomp"), ("L31", "sup"), ("L33", "sup"), ("L37", "pad"), ("L38", "sup"),
            ("L38", "dir"), ("L40", "ar"), ("L42", "ar"), ("L45", "dir"), ("L45", "rmin")]
NOMINAL_DIFF = {"L22": "A keeps 9, B proposes 6", "L39": "A reads 3.0, B keeps 3.46"}
EXCLUSIONS = dict(agree_exclude=15, differ=["2201.11513: A exclude; B encode only if a uniform-traction patch "
                                            "type is implemented, otherwise exclude (kept excluded)"])


def main():
    units, mand = [], []
    for tid, T in lt.TASKS.items():
        task = T["task"]
        for s in task.slots:
            if s in task.mandatory:
                mand.append((tid, s))
                continue
            a_open = (tid, s) not in A_CLOSED
            units.append(dict(task=tid, slot=s, kind="encoded", A_open=a_open, B_open=True,
                              same_values=a_open and (tid, s) not in B_EXTENDED,
                              A_note=A_CLOSED.get((tid, s)), B_note=B_EXTENDED.get((tid, s))))
    for tid, s in PROPOSED:
        units.append(dict(task=tid, slot=s, kind="proposed", A_open=False, B_open=True, same_values=False,
                          A_note=None, B_note=None))
    n = len(units)
    both = sum(u["A_open"] and u["B_open"] for u in units)
    neither = sum(not u["A_open"] and not u["B_open"] for u in units)
    pa = sum(u["A_open"] for u in units) / n
    pb = sum(u["B_open"] for u in units) / n
    po = (both + neither) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    out = dict(units=n, encoded_units=sum(u["kind"] == "encoded" for u in units),
               proposed_units=sum(u["kind"] == "proposed" for u in units), mandatory_slots_kept_by_both=len(mand),
               A_open=sum(u["A_open"] for u in units), B_open=sum(u["B_open"] for u in units), both_open=both,
               raw_agreement=po, kappa=(po - pe) / (1 - pe) if pe < 1 else None,
               kappa_note="B marks every unit open, so chance agreement equals observed agreement",
               both_open_same_values=sum(u["same_values"] for u in units), A_closed=sorted(f"{t}.{s}" for t, s in A_CLOSED),
               B_extended=sorted(f"{t}.{s}" for t, s in B_EXTENDED), nominal_differences=NOMINAL_DIFF,
               exclusions=EXCLUSIONS, unit_list=units)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "adjudication.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    lines = ["# Agreement between the two adjudications", "",
             f"- candidate slots: {n} ({out['encoded_units']} encoded non-mandatory, {out['proposed_units']} proposed); "
             f"{len(mand)} mandatory slots kept by both",
             f"- open for A: {out['A_open']}; open for B: {out['B_open']}; open for both: {both}",
             f"- raw agreement {po:.3f}; Cohen's kappa {out['kappa']:.3f} ({out['kappa_note']})",
             f"- open for both with identical admissible values: {out['both_open_same_values']} of {both}",
             f"- A resolves to one value: {', '.join(out['A_closed'])}",
             f"- B extends the value set: {', '.join(out['B_extended'])}",
             f"- nominal differences: {'; '.join(f'{k}: {v}' for k, v in NOMINAL_DIFF.items())}",
             f"- exclusions: {EXCLUSIONS['agree_exclude']} of 16 agreed; {EXCLUSIONS['differ'][0]}"]
    with open(os.path.join(OUT, "adjudication.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
