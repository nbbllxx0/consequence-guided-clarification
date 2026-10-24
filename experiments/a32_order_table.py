"""A32: per-task question order table for the tasks with two or more varying slots (reviewer request,
loop v5 round 2), from the A15 order-null replay and the stored E03 tables (no new optimization).

For each primary task with at least two varying non-mandatory slots, the table lists the questions asked
over the task's cases under each fixed slot order (full-table check, zero allowance, tau = 0.05) and under
CGC's minimax rule.
Usage: python experiments/a32_order_table.py
Output: results/a32/consensus.json, v4/tables/si_order.tex
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["LT_VARIANT"] = "consensus"
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import a17_nominal_controls as a17  # noqa: E402
import e03_literature_tasks as e03  # noqa: E402
import policies as pl  # noqa: E402

TAU = e03.TAU


def main():
    with open(os.path.join(ROOT, "results", "a15", "consensus.json")) as fh:
        per = json.load(fh)["order_null"]["per_task"]
    rows = []
    for tid, r in per.items():
        if r["free"] < 2:
            continue
        task, orc = a17.load_task(tid)
        interps = task.interpretations()
        q = sum(len([s for s in pl.cgc(task, orc, t, TAU).asked if s not in task.mandatory]) for t in interps)
        rows.append(dict(task=tid, free=r["free"], cases=len(interps), orders=r["full_q"], cgc=q))
    rows.sort(key=lambda x: int(x["task"][1:]))
    os.makedirs(os.path.join(ROOT, "results", "a32"), exist_ok=True)
    with open(os.path.join(ROOT, "results", "a32", "consensus.json"), "w") as fh:
        json.dump(rows, fh, indent=1)
    lines = [r"\begin{table}[pos=tbp]\centering\small",
             r"\caption{Questions by slot order in the 11 primary tasks with two or more varying slots"
             r" (full-table check, zero allowance, $\tau=0.05$). Each fixed order asks the slots in one"
             r" sequence in every case; CGC chooses each question by the minimax rule.}\label{tab:si_order}",
             r"\begin{tabular}{lrrrrr}", r"\toprule",
             r"Task & Varying slots & Cases & Fixed orders & Mean of fixed orders & CGC \\", r"\midrule"]
    for r in rows:
        mean = sum(r["orders"]) / len(r["orders"])
        lines.append(f"{r['task']} & {r['free']} & {r['cases']} & {', '.join(map(str, r['orders']))} & "
                     f"{mean:.0f} & {r['cgc']} \\\\")
    tot_mean = sum(sum(r["orders"]) / len(r["orders"]) for r in rows)
    lines += [r"\midrule",
              f"Total & & {sum(r['cases'] for r in rows)} & & {tot_mean:.0f} & {sum(r['cgc'] for r in rows)} \\\\",
              r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    os.makedirs(os.path.join(ROOT, "v4", "tables"), exist_ok=True)
    with open(os.path.join(ROOT, "v4", "tables", "si_order.tex"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
