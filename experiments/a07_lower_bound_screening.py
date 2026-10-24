"""A07: how well does the certified lower bound flag consequential tasks without optimizing the readings?

For each literature task (E03 exhaustive tables), library L0 = default design + slot-extreme designs (the
CGC-S seed). Screening statistic: B_lo = min_{d in L0} max_t [ C_t(d) / min_{e in L0} C_t(e) - 1 - noise_t ].
Truth: B = min over all reading-optimal designs d of max_t [ loss(d, t) - noise_t ] (minimax regret over the
full table), and B_nom = max_t loss(nominal, t) - noise_t.
Flag "consequential" when B_lo > tau. Reports the confusion matrix against B > tau and the optimizations the
screen needs (|L0|) vs the full table (|Theta|).
Output: results/a07/screening.json, results/a07/screening.md; with --zero-allowance (noise_t = 0, the primary
setting) results/a07/screening_a0.json and screening_a0.md
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import littasks as lt  # noqa: E402
import policies as pl  # noqa: E402

E03 = os.path.join(ROOT, "results", "e03" + lt.RESULTS_SUFFIX)
OUT = os.path.join(ROOT, "results", "a07")
TAU = 0.05
ZERO = "--zero-allowance" in sys.argv
SUFFIX = "_a0" if ZERO else ""


def library_seed(task, keys):
    lib = {pl.ikey(task.nominal)}
    for s, vals in task.slots.items():
        if len(vals) > 1:
            for v in (vals[0], vals[-1]):
                k = pl.ikey(dict(task.nominal, **{s: v}))
                if k in keys:
                    lib.add(k)
    return sorted(lib)


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for tid in lt.TASKS:
        p = os.path.join(E03, f"{tid}.json")
        if not os.path.exists(p):
            continue
        with open(p) as fh:
            o = json.load(fh)
        keys = o["keys"]
        if len(keys) < 2:
            continue
        C = np.array(o["C"], float)
        ref = np.array([o["ref"][k] for k in keys])
        noise = np.array([0.0 if ZERO else o["noise"][k] for k in keys])
        task = lt.TASKS[tid]["task"]
        L0 = library_seed(task, keys)
        idx = [keys.index(k) for k in L0]
        U = np.min(C[idx], axis=0)                       # min over library designs per reading (inf if infeasible)
        lo = C[idx] / U[None, :] - 1 - noise[None, :]
        B_lo = float(np.min(np.max(lo, axis=1)))
        L = C / ref[None, :] - 1 - noise[None, :]
        B = float(np.min(np.max(L, axis=1)))
        B_nom = float(np.max(L[keys.index(pl.ikey(task.nominal))]))
        rows.append(dict(task=tid, dim=lt.TASKS[tid]["dim"], readings=len(keys), library=len(L0), B_lo=B_lo, B=B,
                         B_nominal=B_nom, flagged=bool(B_lo > TAU), consequential=bool(B > TAU)))
    tp = sum(r["flagged"] and r["consequential"] for r in rows)
    fp = sum(r["flagged"] and not r["consequential"] for r in rows)
    fn = sum(not r["flagged"] and r["consequential"] for r in rows)
    tn = sum(not r["flagged"] and not r["consequential"] for r in rows)
    out = dict(tau=TAU, tasks=len(rows), tp=tp, fp=fp, fn=fn, tn=tn,
               library_optimizations=int(sum(r["library"] for r in rows)),
               full_table_optimizations=int(sum(r["readings"] for r in rows)), rows=rows)
    with open(os.path.join(OUT, f"screening{SUFFIX}.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    lines = [f"# Certified lower-bound screening (library = nominal + slot extremes), tau = {TAU}", "",
             f"Tasks with >= 2 readings: {len(rows)}. Flagged & consequential {tp}, flagged & not {fp}, "
             f"not flagged & consequential {fn}, neither {tn}.",
             f"Optimizations: library {out['library_optimizations']} vs full table {out['full_table_optimizations']}.",
             "", "| task | dim | readings | library | B_lo (screen) | B (minimax, full table) | B nominal | flagged | "
             "consequential |", "|---|---|---|---|---|---|---|---|---|"]
    f = lambda x: "inf" if not np.isfinite(x) else (f"{x:.3f}" if abs(x) < 10 else f"{x:.3g}")  # noqa: E731
    for r in rows:
        lines.append(f"| {r['task']} | {r['dim']} | {r['readings']} | {r['library']} | {f(r['B_lo'])} | {f(r['B'])} | "
                     f"{f(r['B_nominal'])} | {r['flagged']} | {r['consequential']} |")
    with open(os.path.join(OUT, f"screening{SUFFIX}.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines[:4]))


if __name__ == "__main__":
    main()
