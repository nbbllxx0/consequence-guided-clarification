"""A16: LaTeX tables from the A15 replays (results/a15/<variant>.json).

Writes into the package table directory given as the first argument:
  tau_sweep.tex       primary benchmark, every policy against the tolerance (main text)
  si_union_tau.tex    the same for the union encoding (Supplementary Information)
  si_attribution.tex  silent-default failures by cause, per task (Supplementary Information)
Usage: python experiments/a16_a15_tables.py <package>/tables
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1]


def load(variant):
    with open(os.path.join(ROOT, "results", "a15", f"{variant}.json")) as fh:
        return json.load(fh)


def tau_table(res, label, caption, n_cases, star):
    rows = []
    for tau, d in res["tau_sweep"].items():
        rows.append(" & ".join([
            f"{float(tau):.2f}",
            f"{d['no_ask']['unsafe']}",
            f"{d['ask_all']['questions']}", f"{d['ask_all']['unsafe']}",
            f"{d['CGC']['questions']}", f"{d['CGC']['released']}",
            f"{d['CGC_S']['questions']}", f"{d['CGC_S']['released']}", f"{d['CGC_S']['unsafe']}",
            f"{d['CGC_S']['bundles'] / n_cases:.2f}",
            f"{d['robust_first']['questions']}"]) + r" \\")
    head = (r"$\tau$ & \shortstack{Silent\\unsafe} & \shortstack{Ask-all\\questions} & \shortstack{Ask-all\\unsafe}"
            r" & \shortstack{CGC\\questions} & \shortstack{CGC\\releases} & \shortstack{CGC-S\\questions}"
            r" & \shortstack{CGC-S\\releases} & \shortstack{CGC-S\\unsafe} & \shortstack{CGC-S\\bundles}"
            r" & \shortstack{Robust-first\\questions} \\")
    return "\n".join([
        r"\begin{table}[pos=tbp]\centering\small",
        rf"\caption{{{caption}}}\label{{{label}}}",
        r"\setlength{\tabcolsep}{3.5pt}",
        r"\begin{tabular}{lrrrrrrrrrr}", r"\toprule", head, r"\midrule", *rows, r"\bottomrule", r"\end{tabular}",
        r"\par\smallskip\raggedright\footnotesize " + star, r"\end{table}", ""])


def fmt_loss(x):
    return f"{x:,.0f}" if x >= 1000 else f"{x:.1f}" if x >= 10 else f"{x:.3f}"


def attribution_table(res):
    rows = []
    for tid, v in sorted(res["attribution"]["per_task"].items(), key=lambda kv: (kv[1]["dim"], kv[0])):
        fin = [c for c in v["readings"] if c["kind"] == "finite"]
        inf = [c for c in v["readings"] if c["kind"] == "infeasible"]
        why = sorted({w for c in inf for w in c["why"]})
        loss = fmt_loss(max(c["loss"] for c in fin)) if fin else "--"
        share = f"{max(c['load_on_void_share'] for c in fin):.2f}" if fin else "--"
        cls = {"infeasible": "infeasible", "large_loss": "loss above 10", "consequential": "loss 0.05--10"}[v["task_class"]]
        rows.append(f"{tid} & {v['dim']} & {cls} & {v['n_bad']} & {loss} & {share} & {', '.join(why) or '--'} " + r"\\")
    return "\n".join([
        r"\begin{table}[pos=tbp]\centering\small",
        r"\caption{Silent-default failures by cause in the 26 pool-unsafe primary tasks. Violating readings are "
        r"those at which the default design's loss exceeds $\tau=0.05$. Void-load share is the largest fraction, "
        r"over finite violating readings, of the applied load acting on nodes whose adjacent elements all have "
        r"default-design density below 0.5. Infeasibility causes list the mapping rules that differ between the nominal "
        r"and the violating reading.}\label{tab:si_attribution}",
        r"\begin{tabularx}{\linewidth}{llYrrrY}", r"\toprule",
        r"Task & Dim. & Class & \shortstack{Violating\\readings} & \shortstack{Largest\\finite loss}"
        r" & \shortstack{Void-load\\share} & Infeasibility cause \\",
        r"\midrule", *rows, r"\bottomrule", r"\end{tabularx}", r"\end{table}", ""])


def check_footnote(res, n_cases, cgc, rf):
    """The footnotes state per-case bundles and released counts that do not vary with tau; check them."""
    for d in res["tau_sweep"].values():
        assert f"{d['CGC']['bundles'] / n_cases:.2f}" == cgc and f"{d['robust_first']['bundles'] / n_cases:.2f}" == rf
        assert d["robust_first"]["unsafe"] == 0
        assert d["ask_all"]["released"] == d["no_ask"]["released"] == n_cases


def main():
    con, uni = load("consensus"), load("union")
    check_footnote(con, 134, "6.10", "6.84")
    check_footnote(uni, 240, "11.19", "11.63")
    files = {
        "tau_sweep.tex": tau_table(
            con, "tab:tau", "Primary benchmark (134 cases) replayed at five tolerances, zero allowance.", 134,
            "Questions exclude mandatory slots; unsafe counts are pool-unsafe releases. Ask-all and the silent "
            "default release in every case, CGC requests 6.10 bundles per case at every tolerance, and "
            "robust-first CGC requests 6.84 and has no unsafe release."),
        "si_union_tau.tex": tau_table(
            uni, "tab:si_union_tau", "Union encoding (240 cases) replayed at five tolerances, zero allowance.", 240,
            "Questions exclude mandatory slots; unsafe counts are pool-unsafe releases. Ask-all and the silent "
            "default release in every case; CGC requests 11.19 bundles per case at every tolerance; robust-first "
            "CGC requests 11.63 and has no unsafe release."),
        "si_attribution.tex": attribution_table(con),
    }
    for name, text in files.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("wrote", name)


if __name__ == "__main__":
    main()
