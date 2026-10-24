"""A29: Supplementary tables for the loop-v5 controls (A24 type rules, A26/E08 refinement, A27 bound).

Reads stored results only.
  tables/si_typerule.tex  slot-type rules (A24) at five tolerances, beside CGC-S (A15)
  tables/si_refcheck.tex  per task: certified reference gap (A27), CGC-S releases certified within tau,
                          and the 2x-mesh full-table minimax loss with decision stability (A26; A14 for
                          the nine near-tolerance tasks)
Usage: python experiments/a29_si_tables_v5.py
"""
import io
import json
import os
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "v4", "tables")
TAUS = ("0.01", "0.02", "0.05", "0.1", "0.2")


def jload(*p):
    with open(os.path.join(RES, *p), encoding="utf-8") as fh:
        return json.load(fh)


def fnum(x):
    if x == float("inf"):
        return "Inf."
    if x < 1e-3:
        return "$<0.001$"
    if x < 10:
        return f"{x:.4f}" if x < 1 else f"{x:.3g}"
    return f"{x:,.0f}"


def typerule_table():
    a24 = jload("a24", "consensus.json")["category"]["by_tau"]
    a15 = jload("a15", "consensus.json")["tau_sweep"]
    rows = []
    for t in TAUS:
        r = a24[t]
        cs = a15[t]["CGC_S_a0"] if "CGC_S_a0" in a15[t] else a15[t]["CGC_S"]
        cells = [t if t not in ("0.1", "0.2") else t + "0"]
        for k in ("entity", "attribute", "position_only"):
            cells += [str(r[k]["q"]), str(r[k]["unsafe"]), str(r[k]["exceed"])]
        cells += [str(cs["questions"]), str(cs.get("pool_unsafe", cs.get("unsafe")))]
        rows.append(" & ".join(cells) + r" \\")
    head = [
        r"\begin{table}[pos=tbp]\centering\small",
        r"\caption{Slot-type rules on the primary benchmark (134 cases) at five tolerances, zero allowance. Each rule asks every varying slot of the listed types, defaults the others to their default values, and releases the reference of the resulting reading. Q: non-mandatory questions; U: pool-unsafe releases; E: selected-truth exceedances.}\label{tab:si_typerule}",
        r"\begin{tabular}{lrrrrrrrrrrr}",
        r"\toprule",
        r" & \multicolumn{3}{c}{Load extent defaulted} & \multicolumn{3}{c}{All extents defaulted} & \multicolumn{3}{c}{Position only} & \multicolumn{2}{c}{CGC-S} \\",
        r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}\cmidrule(lr){8-10}\cmidrule(lr){11-12}",
        r"$\tau$ & Q & U & E & Q & U & E & Q & U & E & Q & U \\",
        r"\midrule",
    ]
    tail = [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(head + rows + tail)


def stable_a14(d):
    """Decisions unchanged on the refined mesh: same questions and release flag in every case, both policies."""
    for pol in ("CGC", "CGC_S"):
        b = {r["truth"]: (r["n_asked"], r["released"]) for r in d["base"]["replay"][pol]}
        f = {r["truth"]: (r["n_asked"], r["released"]) for r in d["refined_x2"]["replay"][pol]}
        if b != f:
            return False
    return True


def refcheck_table():
    a14 = jload("a14", "near_threshold_a0.json")
    tids = sorted(f[:3] for f in os.listdir(os.path.join(RES, "a27")) if f.startswith("L") and f.endswith(".json"))
    rows = []
    for tid in tids:
        b = jload("a27", tid + ".json")
        gaps = list(b["reference_gap"].values())
        rel = b["releases"]["CGC_S"]
        mesh = "--"
        p26 = os.path.join(RES, "a26", tid + ".json")
        if tid in a14:
            d = a14[tid]
            mesh = f"{fnum(d['base']['B'])} & {fnum(d['refined_x2']['B'])} & {'yes' if stable_a14(d) else 'no'}"
        elif os.path.exists(p26):
            d = jload("a26", tid + ".json")
            ok = d["stable"]["CGC"] and d["stable"]["CGC_S"]
            mesh = f"{fnum(d['base']['B'])} & {fnum(d['refined_x2']['B'])} & {'yes' if ok else 'no'}"
        if mesh == "--":
            mesh = "-- & -- & --"
        rows.append(f"{tid} & {b['dim']} & {len(gaps)} & {statistics.median(gaps):.3f} & {max(gaps):.3f} & "
                    f"{rel['certified_within_tau']}/{rel['releases']} & {mesh} \\\\")
    head = [
        r"\begin{table}[pos=tbp]\centering\small",
        r"\caption{Reference checks per task. Gap: the computed reference divided by the certified lower bound on the optimal compliance, minus one, median and maximum over the task's readings. Certified: CGC-S releases whose loss against that bound is at most $\tau=0.05$ at every open reading. Mesh: full-table minimax loss on the reconstruction mesh and on a mesh refined by two in each direction, and whether every CGC and CGC-S question count and release flag is unchanged. Three-dimensional tasks other than L24 were not refined.}\label{tab:si_refcheck}",
        r"\begin{tabular}{lrrrrrrrl}",
        r"\toprule",
        r" & & & \multicolumn{2}{c}{Gap} & & \multicolumn{3}{c}{Mesh} \\",
        r"\cmidrule(lr){4-5}\cmidrule(lr){7-9}",
        r"Task & Dim. & Readings & Median & Max. & Certified & Base & Refined & Unchanged \\",
        r"\midrule",
    ]
    tail = [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(head + rows + tail)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, txt in (("si_typerule.tex", typerule_table()), ("si_refcheck.tex", refcheck_table())):
        with io.open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            fh.write(txt)
        print("wrote", name)


if __name__ == "__main__":
    main()
