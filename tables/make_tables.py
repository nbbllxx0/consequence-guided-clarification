"""Tables for the CMAME paper, generated from results/ and src/ (no hand-entered numbers).

Usage: python tables/make_tables.py
Output: tables/out/<name>.csv and <name>.tex (booktabs), tables/out/manifest.json
"""
import csv
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import littasks as lt  # noqa: E402

OUT = os.path.join(ROOT, "tables", "out")
R = os.path.join(ROOT, "results")
MANIFEST = {}


def load(p):
    with open(p) as fh:
        return json.load(fh)


def tex_escape(s):
    return (str(s).replace("\\", r"\textbackslash{}").replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")
            .replace("#", r"\#").replace("×", r"$\times$").replace("τ", r"$\tau$").replace("≤", r"$\le$")
            .replace("^", r"\textasciicircum{}").replace("~", r"\textasciitilde{}").replace("|", r"\textbar{}")
            .replace(">", r"\textgreater{}").replace("<", r"\textless{}"))


def write(name, header, rows, sources, caption, colspec=None):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"{name}.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    colspec = colspec or "l" * len(header)
    lines = [r"\begin{table}[t]", r"\centering\small", f"\\caption{{{tex_escape(caption)}}}", f"\\label{{tab:{name}}}",
             f"\\begin{{tabular}}{{{colspec}}}", r"\toprule", " & ".join(tex_escape(h) for h in header) + r" \\",
             r"\midrule"]
    lines += [" & ".join(tex_escape(c) for c in r) + r" \\" for r in rows]
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    with open(os.path.join(OUT, f"{name}.tex"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    MANIFEST[name] = sorted(os.path.relpath(s, ROOT).replace("\\", "/") for s in sources)


def fmt_loss(x):
    if not np.isfinite(x):
        return "infeasible"
    return f"{x:.3f}" if x < 10 else f"{x:.2g}"


def t_tasks():
    summ = load(os.path.join(R, "e03", "summary.json"))["per_task"]
    rows = []
    for tid, T in lt.TASKS.items():
        task = T["task"]
        slots = "; ".join(f"{s}: {', '.join(map(str, v))}" + (" (mandatory)" if s in task.mandatory else "")
                          for s, v in task.slots.items())
        c = summ[tid]
        rows.append([tid, T["source"]["arxiv"], T["source"]["position"], f"{T['dim']}-D", slots,
                     len(lt.interpretations(tid)), c["cls"], fmt_loss(c["nominal_worst"])])
    write("tab_tasks", ["Task", "arXiv", "Frame pos.", "Dim.", "Slots and admissible values", "Readings",
                        "Default-design class", "Default-design worst loss"], rows,
          [os.path.join(ROOT, "src", "littasks.py"), os.path.join(R, "e03", "summary.json")],
          "Literature-derived tasks: ambiguity slots, admissible readings and the consequence of the nominal "
          "(silent-default) design under the exhaustive table.", "lllllrll")


def t_not_encoded():
    rows = [[a, why] for a, why in lt.NOT_ENCODED.items()]
    write("tab_not_encoded", ["arXiv", "Reason not encoded"], rows, [os.path.join(ROOT, "src", "littasks.py")],
          "In-scope ambiguous examples of the frozen screen that are not encoded, with the reason.", "lp{11cm}")


def t_policies():
    s = load(os.path.join(R, "e03", "summary.json"))["policies"]
    names = {"no_ask_a0": "Silent default", "ask_all_a0": "Ask every open slot", "CGC_a0": "CGC (full table)",
             "CGC_S_a0": "CGC-S (screening, lazy references)", "CGC": "CGC, measured-spread allowance",
             "CGC_S": "CGC-S, measured-spread allowance", "robust": "Robust design, no question (allowance)",
             "robust_then_H": "Robust if it covers, else CGC (allowance)"}
    rows = [[names[k], s[k]["tasks"], s[k]["cases"], s[k]["total_extra_questions"], s[k]["releases"],
             s[k]["false_releases"], s[k]["truth_exceedances"], s[k]["tasks_with_false_release"],
             f"{s[k]['mean_optimizations']:.2f}", f"{s[k]['mean_optimizations_task_weighted']:.2f}"]
            for k in names if k in s]
    write("tab_policies", ["Policy", "Tasks", "Cases", "Non-mandatory questions", "Releases", "Pool-unsafe releases",
                           "Selected-truth exceedances", "Tasks with a pool-unsafe release",
                           "Reference bundles per case", "Per case, task-weighted"], rows,
          [os.path.join(R, "e03", "summary.json")],
          "Policy outcomes over the literature tasks (each admissible reading in turn is the hidden truth; tau = 5%; "
          "zero allowance unless stated).", "lrrrrrrrrr")


def t_controlled():
    rows = []
    e01 = load(os.path.join(R, "e01", "summary.json"))
    for k, v in e01.items():
        g, tr = k.split("/")
        rows.append(["2-D", g, tr, 9, fmt_loss(v["mid_row_max_loss"]), fmt_loss(v["max_loss"]),
                     f"{v['noise_max']:.2g}", v["accepted"]])
    for d, f in (("e02", "cant_z"), ("e02", "cant_y"), ("e02", "deck_lane"), ("e02b", "cant_z_off"),
                 ("e02b", "deck_off"), ("e02b", "lbr_pos"), ("e02b", "deck_width")):
        x = load(os.path.join(R, d, f"{f}.json"))
        L = np.array(x["L"])
        nom = 0 if f in ("cant_z_off", "deck_off", "deck_width") else len(x["vals"]) // 2
        rows.append(["3-D", f, "position" if "width" not in f else "width", len(x["vals"]), fmt_loss(L[nom].max()),
                     fmt_loss(L.max()), f"{np.nanmax(x['noise']):.2g}", f"{sum(x['accepted'])}/{len(x['accepted'])}"])
    write("tab_controlled", ["Dim.", "Geometry / track", "Ambiguity", "Values", "Default-design worst loss", "Max loss",
                             "Max noise", "Accepted"], rows,
          [os.path.join(R, "e01", "summary.json")] + [os.path.join(R, d, f"{f}.json") for d, f in
                                                       (("e02", "cant_z"), ("e02", "cant_y"), ("e02", "deck_lane"),
                                                        ("e02b", "cant_z_off"), ("e02b", "deck_off"),
                                                        ("e02b", "lbr_pos"), ("e02b", "deck_width"))],
          "Controlled sweeps: loss of the default design and the worst entry of each cross table.", "lllrrrrl")


def t_verification():
    v = load(os.path.join(R, "e04", "verification.json"))
    rows = []
    for k, d in v["V1_derivatives"].items():
        rows.append(["V1 sensitivities", k, f"max |FD-adjoint|/max|dc| = {d['max_err_dc_over_max_dc']:.1e}; "
                     f"max rel. = {d['max_rel_err_dc']:.1e} (h = {d['h']:g})"])
    for k in ("C1_scale_3F", "C2_sign_minusF"):
        d = v[k]
        rows.append([k.split("_")[0], k, f"compliance ratio {d['ratio']:.6f} (expected {d['expected_ratio']:g}); "
                     f"max design difference {d['max_design_diff']:.1e}"])
    c3 = v["C3_two_springs"]
    rows.append(["C3", "two springs", f"V(theta) in [{min(c3['V_numeric']):.6f}, {max(c3['V_numeric']):.6f}]; "
                 f"regret of x(0.5) at theta = 0.2: {100 * c3['regret_commit_0p5_at_0p2_numeric']:.2f}%"])
    for k, d in v["omitted_intent"].items():
        rows.append(["C4/C5 omitted intent", k, f"robust worst loss in pool {d['robust_worst_in_pool']:.3f}; "
                     f"loss at intended c = {d['intended']}: {d['robust_loss_at_intended']:.3g}"])
    fe = v["failed_equilibrium"]
    for k in ("C6_L41_x_rollers", "C7_L24_vertical_only_strips"):
        rows.append([k.split("_")[0], k, f"free rigid modes {fe[k]['free_rigid_modes']} "
                     f"(annotated reading: {fe[k]['annotated_reading_free_modes']})"])
    rows.append(["C6/C7", f"all {fe['annotated_readings']} annotated readings",
                 f"free rigid modes {fe['all_annotated_readings_free_modes']}"])
    write("tab_verification", ["Check", "Case", "Result"], rows, [os.path.join(R, "e04", "verification.json")],
          "Verification and diagnostic controls.", "llp{9cm}")


def t_adjudication():
    a = load(os.path.join(R, "a10", "adjudication.json"))
    rows = [[tid, r["source"]["arxiv"], f"{r['dim']}-D", "; ".join(f"{k}: {', '.join(map(str, v))}"
                                                              for k, v in r["pre_slots"].items()), r["reason"]]
            for tid, r in lt.RESOLVED.items()]
    write("tab_resolved", ["Task", "arXiv", "Dim.", "Slots before adjudication", "Reading kept and reason"], rows,
          [os.path.join(ROOT, "src", "littasks.py"), os.path.join(ROOT, "tasks", "adjudication", "A_shaoliang.txt"),
           os.path.join(ROOT, "tasks", "adjudication", "B_jun_wang.txt")],
          f"Encoded tasks whose only open slot the adjudication resolves from the source text (consensus encoding). "
          f"Adjudicator agreement over {a['units']} candidate slots: raw {a['raw_agreement']:.2f}; open for both "
          f"{a['both_open']}, for A {a['A_open']}, for B {a['B_open']}.", "lllp{4cm}p{6cm}")


def t_si_encodings():
    """SI table: every slot of every adjudicated task with its values, reason and reconstruction notes."""
    pv = load(os.path.join(ROOT, "tasks", "published_versions_20261023.json"))["papers"]
    rows = []
    for tid, T in lt.TASKS.items():
        task, a = T["task"], T["source"]["arxiv"]
        rec = pv.get(a, {})
        pub = rec.get("doi") or (rec.get("versions") or [{}])[-1].get("doi", "") if rec.get("status") == "published" else ""
        for s, v in task.slots.items():
            rows.append([tid, a, pub, s + (" (mandatory)" if s in task.mandatory else ""), ", ".join(map(str, v)),
                         str(task.nominal[s]), T["reasons"].get(s, "")])
        rows.append([tid, a, pub, "set-up", "", "", "; ".join(T["recon"])])
    header = ["Task", "arXiv (encoded version)", "Published version DOI", "Slot", "Admissible values", "Default",
              "Reason / evidence"]
    with open(os.path.join(OUT, "tab_si_encodings.csv"), "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows([header] + rows)
    # LaTeX version without the DOI column (sources are cited by their bib keys src_<Task>); needs array, longtable,
    # booktabs
    col = r">{\raggedright\arraybackslash}p"
    lines = [r"{\small\setlength{\tabcolsep}{3pt}",
             r"\begin{longtable}{" + "".join(f"{col}{{{w}}}" for w in ("0.8cm", "1.85cm", "1.5cm", "2.2cm", "1.7cm",
                                                                       "4.35cm")) + "}",
             r"\caption{Encodings of the adjudicated literature tasks (consensus encoding): slots, admissible values, "
             r"default value, and the reason each slot is open; reconstruction choices per task.}\label{tab:si_encodings}\\",
             r"\toprule", " & ".join(tex_escape(h) for i, h in enumerate(header) if i != 2) + r" \\", r"\midrule\endhead"]
    lines += [" & ".join(tex_escape(c) for i, c in enumerate(r) if i != 2) + r" \\" for r in rows]
    lines += [r"\bottomrule", r"\end{longtable}}"]
    with open(os.path.join(OUT, "tab_si_encodings.tex"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    MANIFEST["tab_si_encodings"] = ["src/littasks.py", "tasks/published_versions_20261023.json"]


def t_union():
    path = os.path.join(R, "e03_union", "summary.json")
    if not os.path.exists(path):
        print("   union summary missing: tab_union skipped")
        return
    rows = []
    for var, sp in (("consensus", os.path.join(R, "e03", "summary.json")), ("union", path)):
        s = load(sp)
        for k, name in (("no_ask_a0", "Silent default"), ("ask_all_a0", "Ask every open slot"),
                        ("CGC_a0", "CGC"), ("CGC_S_a0", "CGC-S")):
            v = s["policies"][k]
            rows.append([var, name, s["n_tasks"], v["cases"], v["total_extra_questions"], v["releases"], v["false_releases"],
                         v["truth_exceedances"], v["tasks_with_false_release"], f"{v['mean_optimizations']:.2f}",
                         f"{v['mean_optimizations_task_weighted']:.2f}"])
    write("tab_union", ["Encoding", "Policy", "Tasks", "Cases", "Non-mandatory questions", "Releases", "Pool-unsafe releases",
                        "Selected-truth exceedances", "Tasks with a pool-unsafe release", "Bundles per case",
                        "Per case, task-weighted"], rows,
          [os.path.join(R, "e03", "summary.json"), path],
          "Sensitivity to the adjudication: consensus encoding (readings both adjudicators accept) and union encoding "
          "(readings either accepts); zero allowance; question budget 3 (unreleased cases are abstentions).", "llrrrrrrrrr")


def t_key_numbers():
    """Headline numbers for the writing guide, each with its source file."""
    k = {}
    s = load(os.path.join(R, "e03", "summary.json"))
    k["e03_tasks"] = (s["n_tasks"], "results/e03/summary.json")
    k["e03_cases"] = (s["n_cases"], "results/e03/summary.json")
    k["e03_classes"] = (s["classes"], "results/e03/summary.json")
    for p, v in s["policies"].items():
        k[f"e03_{p}"] = ({kk: v[kk] for kk in ("tasks", "cases", "mean_questions", "mean_extra_questions",
                                                "false_releases", "tasks_with_false_release", "mean_optimizations")},
                         "results/e03/summary.json")
    rp = load(os.path.join(R, "e03", "replay.json"))
    cov = [t for t in rp if "robust" in rp[t] and rp[t]["robust"].get("covers")]
    app = [t for t in rp if "robust" in rp[t]]
    k["robust_covers"] = (f"{len(cov)}/{len(app)}", "results/e03/replay.json")
    e01 = load(os.path.join(R, "e01", "summary.json"))
    k["e01_max_loss"] = ({kk: round(v["max_loss"], 4) for kk, v in e01.items()}, "results/e01/summary.json")
    k["e01_noise_max"] = (round(max(v["noise_max"] for v in e01.values()), 4), "results/e01/summary.json")
    for f in ("cant_z_off", "deck_off", "lbr_pos", "deck_width"):
        x = load(os.path.join(R, "e02b", f"{f}.json"))
        L = np.array(x["L"])
        nom = len(x["vals"]) // 2 if f == "lbr_pos" else 0
        k[f"e02b_{f}_nominal_row"] = ([round(float(v), 4) for v in L[nom]], f"results/e02b/{f}.json (vals {x['vals']})")
    for f in ("cant_z", "cant_y", "deck_lane", "cant_z_off", "deck_off", "lbr_pos", "deck_width"):
        p = os.path.join(R, "e02b", f"emin_{f}.json")
        if os.path.exists(p):
            e = load(p)
            L6, L9 = np.array(e["L_emin6"]), np.array(e["L_emin9"])
            m = L6 > 1
            k[f"emin_{f}_median_ratio"] = (round(float(np.median(L9[m] / L6[m])), 1), p.replace(ROOT, "").lstrip("\\/"))
    v = load(os.path.join(R, "e04", "verification.json"))
    k["derivatives_max_err_over_max_dc"] = (max(d["max_err_dc_over_max_dc"] for d in v["V1_derivatives"].values()),
                                            "results/e04/verification.json")
    k["two_springs_regret"] = (v["C3_two_springs"]["regret_commit_0p5_at_0p2_numeric"], "results/e04/verification.json")
    k["omitted_intent"] = ({kk: round(d["robust_loss_at_intended"], 1) for kk, d in v["omitted_intent"].items()},
                           "results/e04/verification.json")
    a7 = load(os.path.join(R, "a07", "screening.json"))
    k["screening_confusion"] = ({kk: a7[kk] for kk in ("tasks", "tp", "fp", "fn", "tn")}, "results/a07/screening.json")
    k["screening_optimizations"] = (f"{a7['library_optimizations']} vs {a7['full_table_optimizations']}",
                                    "results/a07/screening.json")
    k["e03_hindsight"] = (s["hindsight"], "results/e03/summary.json")
    k["e03_slots_per_task"] = (s["slots_per_task"], "results/e03/summary.json")
    for p in ("CGC_a0", "CGC_S_a0"):
        rows = [r for t in rp for r in rp[t]["_rows"][p]]
        k[f"e03_{p}_totals"] = (dict(bundles=int(sum(r["optimizations"] for r in rows)),
                                     bundles_without_L22=int(sum(r["optimizations"] for t in rp if t != "L22"
                                                                 for r in rp[t]["_rows"][p])),
                                     cross_evals=int(sum(r["cross_evals"] for r in rows))), "results/e03/replay.json")
    # a full table for a task with n readings costs n x n cross-evaluations; summed over its n cases
    k["e03_full_table_cross_evals_over_cases"] = (int(sum(len(rp[t]["_rows"]["CGC_a0"]) ** 3 for t in rp)),
                                                  "results/e03/replay.json")
    k["e03_kkt_selected"] = (s["kkt_selected"], "results/e03/summary.json")
    a10 = load(os.path.join(R, "a10", "adjudication.json"))
    k["adjudication"] = ({kk: a10[kk] for kk in ("units", "encoded_units", "proposed_units", "A_open", "B_open",
                                                  "both_open", "raw_agreement", "kappa", "both_open_same_values")},
                         "results/a10/adjudication.json")
    for var, f in (("consensus", "agreement.json"), ("union", os.path.join("agreement_union", "agreement.json")),
                   ("pre", os.path.join("agreement_pre", "agreement.json"))):
        p6 = os.path.join(R, "e06", f)
        if os.path.exists(p6):
            g = load(p6)
            k[f"e06_{var}"] = ({kk: g[kk] for kk in ("tasks", "units", "kappa", "raw_agreement", "disagreements",
                                                       "outside_convention_items")}, os.path.relpath(p6, ROOT))
    pu = os.path.join(R, "e03_union", "summary.json")
    if os.path.exists(pu):
        su = load(pu)
        k["union_e03"] = (dict(tasks=su["n_tasks"], cases=su["n_cases"], classes=su["classes"],
                               **{p: {kk: su["policies"][p][kk] for kk in ("total_extra_questions", "false_releases",
                                                                         "truth_exceedances", "tasks_with_false_release",
                                                                         "mean_optimizations")}
                                  for p in ("no_ask_a0", "ask_all_a0", "CGC_a0", "CGC_S_a0")}),
                          "results/e03_union/summary.json")
    k["census_resolved_by_adjudication"] = (sorted(lt.RESOLVED), "src/littasks.py (ADJUDICATION)")
    k["census_encoded"] = (len(lt.TASKS), "src/littasks.py")
    k["census_not_encoded"] = (len(lt.NOT_ENCODED), "src/littasks.py")
    k["census_3d_encoded"] = (sum(T["dim"] == 3 for T in lt.TASKS.values()), "src/littasks.py")
    k["readings_total"] = (sum(len(lt.interpretations(t)) for t in lt.TASKS), "src/littasks.py")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "key_numbers.json"), "w") as fh:
        json.dump({kk: dict(value=vv[0], source=vv[1]) for kk, vv in k.items()}, fh, indent=1)


def t_near_threshold():
    s = load(os.path.join(R, "e08", "summary.json"))
    rows = []
    for tid, v in s.items():
        rows.append([tid, f"{lt.TASKS[tid]['dim']}-D", len(lt.interpretations(tid))]
                    + [f"{v[k]['B']:.4f}" for k in ("base", "polished", "refined_x2")]
                    + ["yes" if v["polished"]["stable_CGC"] and v["polished"]["stable_CGC_S"] else "no",
                       "yes" if v["refined_x2"]["stable_CGC"] and v["refined_x2"]["stable_CGC_S"] else "no"])
    write("tab_near_threshold", ["Task", "Dim.", "Readings", "Minimax loss (2 starts)", "Minimax loss (6 starts)",
                                 "Minimax loss (x2 mesh)", "Decisions stable, 6 starts", "Decisions stable, x2 mesh"],
          rows, [os.path.join(R, "e08", "summary.json")],
          "Near-threshold tasks: full-table minimax loss and stability of CGC and CGC-S decisions under additional "
          "starts and mesh refinement (tau = 5%).", "llrrrrll")


def t_matched():
    m = load(os.path.join(R, "e09", "matched.json"))
    names = {"2D_vf015_nostrip": ("2-D", "0.15", "none"), "2D_vf040_nostrip": ("2-D", "0.40", "none"),
             "2D_vf040_strip": ("2-D", "0.40", "2-element strip"), "3D_cant_y_vf015_nostrip": ("3-D", "0.15", "none")}
    rows = []
    for k, (d, vf, strip) in names.items():
        row = m[k]["nominal_row"]
        rows.append([d, vf, strip, fmt_loss(row[1]), fmt_loss(row[0]), fmt_loss(m[k]["max_loss"])])
    write("tab_matched", ["Dim.", "Volume fraction", "Passive load region", "Loss, load at 0.35 H",
                          "Loss, load at 0.2 H", "Max loss"], rows,
          [os.path.join(R, "e09", "matched.json"), os.path.join(R, "e02", "cant_y.json")],
          "Matched cantilever controls: loss of the mid-height design when the load moves along the loaded edge.",
          "lllrrr")


def main():
    for f in (t_tasks, t_not_encoded, t_policies, t_controlled, t_verification, t_near_threshold, t_matched,
              t_adjudication, t_union, t_si_encodings, t_key_numbers):
        f()
        print("ok", f.__name__)
    with open(os.path.join(OUT, "manifest.json"), "w") as fh:
        json.dump(MANIFEST, fh, indent=1)


if __name__ == "__main__":
    main()
