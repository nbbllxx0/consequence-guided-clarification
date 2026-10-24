"""A35: stored-table analyses requested by the loop v5 round-3 reviewers (no new optimization).

Sections:
  sheet_tasks   primary totals without L37-L45, the tasks adjudicator A judged from sheet evidence only
  tracks        zero-allowance policy replay on the 19 controlled tracks (A08's replay, without its spread
                allowance): cases, questions, releases without a question, pool-unsafe releases, bundles per case
  envelope      cost = bundles + c x non-mandatory questions for every evaluated policy that releases in all
                134 primary cases without a pool-unsafe release; the cheapest policy as a function of c and
                the crossing points (cross-evaluations excluded, as in the paper)
Usage: python experiments/a35_review_tables.py
Output: results/a35/summary.json
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["LT_VARIANT"] = "consensus"
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import a24_category_pool_controls as a24  # noqa: E402
import littasks as lt  # noqa: E402

R = os.path.join(ROOT, "results")
OUT = os.path.join(R, "a35")
SHEET = [f"L{i}" for i in range(37, 46)]


def sheet_tasks():
    tids = list(lt.TASKS)
    keep = [t for t in tids if t not in SHEET]
    return dict(excluded=[t for t in SHEET if t in tids], tasks=len(keep), without=a24.policy_totals(keep))


def track_replay():
    """Zero-allowance replay of every controlled track (A08 replays them with the spread as allowance)."""
    import glob
    import a08_scaling_controlled as a08
    out = {}
    for p in sorted(glob.glob(os.path.join(R, "e01", "*_*.json"))):
        if p.endswith("summary.json"):
            continue
        d = json.load(open(p))
        out[f"2D/{os.path.basename(p)[:-5]}"] = a08.run("t", d["C"], d["best_known"], [0.0] * len(d["vals"]),
                                                       len(d["vals"]) // 2)
    for sub, f, nom in (("e02", "cant_z", None), ("e02", "cant_y", None), ("e02", "deck_lane", None),
                        ("e02b", "cant_z_off", 0), ("e02b", "deck_off", 0), ("e02b", "lbr_pos", None),
                        ("e02b", "deck_width", 0)):
        d = json.load(open(os.path.join(R, sub, f"{f}.json")))
        n = len(d["vals"])
        out[f"3D/{f}"] = a08.run("t", d["C"], d["ref"], [0.0] * n, n // 2 if nom is None else nom)
    return out


def tracks(d):
    acc = dict(tracks=0, cases=0, ask_all_q=0, CGC_q=0, CGC_S_q=0, released_unasked_cases=0, harmless_tracks=0,
               CGC_unsafe=0, CGC_S_unsafe=0, silent_unsafe=0, CGC_bundles=0.0, CGC_S_bundles=0.0,
               max_nominal_worst_harmless=0.0, min_nominal_worst_consequential=float("inf"))
    for name, v in d.items():
        n = v["n"]
        acc["tracks"] += 1
        acc["cases"] += n
        acc["ask_all_q"] += n
        acc["CGC_q"] += round(v["CGC"]["questions"] * n)
        acc["CGC_S_q"] += round(v["CGC_S"]["questions"] * n)
        acc["CGC_unsafe"] += v["CGC"]["unsafe"]
        acc["CGC_S_unsafe"] += v["CGC_S"]["unsafe"]
        acc["silent_unsafe"] += v["no_ask"]["unsafe"]
        acc["CGC_bundles"] += v["CGC"]["bundles"] * n
        acc["CGC_S_bundles"] += v["CGC_S"]["bundles"] * n
        if v["CGC"]["questions"] == 0:
            acc["harmless_tracks"] += 1
            acc["released_unasked_cases"] += n
            acc["max_nominal_worst_harmless"] = max(acc["max_nominal_worst_harmless"], v["nominal_worst"])
        else:
            acc["min_nominal_worst_consequential"] = min(acc["min_nominal_worst_consequential"], v["nominal_worst"])
    return acc


NAMES = {"cantilever": "Cantilever", "l_domain": "L-domain", "mbb_full": "Full MBB beam", "plate_hole": "Perforated plate",
         "center": "load center", "split": "load split", "width": "patch width", "cant_z": "Cantilever, load height",
         "cant_y": "Cantilever, transverse load position", "deck_lane": "Deck, lane position",
         "cant_z_off": "Cantilever, load offset", "deck_off": "Deck, load offset", "lbr_pos": "L-bracket, load height",
         "deck_width": "Deck, patch width"}


def fmt(x):
    if x < 1e-3:
        return "$<0.001$"
    if x < 1:
        return f"{x:.3f}"
    return f"{x:,.0f}" if x >= 10 else f"{x:.2f}"


def tracks_table(d):
    """Supplementary table of the zero-allowance controlled-track replay."""
    rows = []
    for name, v in d.items():
        dim, tr = name.split("/")
        if dim == "2D":
            g, slot = tr.rsplit("_", 1)
            label = f"{NAMES[g]}, {NAMES[slot]}"
        else:
            label = NAMES[tr]
        rows.append(f"{label} & {dim[0]} & {v['n']} & {fmt(v['nominal_worst'])} & {v['CGC']['questions']:.0f} & "
                    f"{v['CGC']['unsafe']} & {v['CGC_S']['bundles']:.2f} & {v['CGC_S']['unsafe']} & {v['no_ask']['unsafe']} \\\\")
    tex = ("\\begin{table}[pos=tbp]\\centering\\small\n"
           "\\caption{Policy replay on the controlled tracks at zero allowance, $\\tau=0.05$. Each track is one slot "
           "with every value in turn as the intended one; the default value is the middle one, except in the "
           "three-dimensional offset and width tracks, where it is the first. Default loss: largest loss of the default "
           "design over the track. Questions: CGC questions per case (ask-all asks one). CGC-S asks the same "
           "questions.}\\label{tab:si_tracks}\n"
           "\\begin{tabularx}{\\linewidth}{Yrrrrrrrr}\n\\toprule\n"
           "Track & Dim. & Values & \\shortstack{Default\\\\loss} & \\shortstack{CGC\\\\questions} & "
           "\\shortstack{CGC\\\\pool-unsafe} & \\shortstack{CGC-S\\\\bundles} & \\shortstack{CGC-S\\\\pool-unsafe} & "
           "\\shortstack{Silent default\\\\pool-unsafe} \\\\\n\\midrule\n" + "\n".join(rows) +
           "\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n")
    with open(os.path.join(ROOT, "v4", "tables", "si_tracks.tex"), "w", encoding="utf-8") as fh:
        fh.write(tex)


def minmax_table():
    """Supplementary table of the robust designs of the six uncovered tasks (A20 p-norms, A33 min-max)."""
    a20 = json.load(open(os.path.join(R, "a20", "summary.json")))
    a33 = json.load(open(os.path.join(R, "a33", "summary.json")))["per_task"]
    rows = []
    for tid in sorted(a33):
        n = len(json.load(open(os.path.join(R, "e03", f"{tid}.json")))["keys"])
        v, ps = a33[tid], a33[tid]["per_start"]

        def f4(x, conv=True):
            return (f"{x:.4f}" if x < 1 else f"{x:,.0f}") + ("" if conv else "$^*$")
        pn = [f4(a20[tid]["p16"])]
        for p in (64, 256):
            r = json.load(open(os.path.join(R, "a20", f"robust_p{p}_{tid}.json")))
            pn.append(f4(r["worst"], r["converged"]))
        mm = " & ".join(f4(ps[s]["worst"], ps[s]["converged"]) + ("$^\\dagger$" if ps[s]["volume_excess"] > 1e-6 else "")
                        for s in ("uniform", "sin5", "p16"))
        rows.append(f"{tid} & {n} & {' & '.join(pn)} & {mm} & {'yes' if v['covers'] else 'no'} \\\\")
    tex = ("\\begin{table}[pos=tbp]\\centering\\small\n"
           "\\caption{Worst pool loss of the robust designs in the six applicable tasks that the $p=16$ design does not "
           "cover. $p$-norm designs start from the uniform field; bound-form min--max designs (Eq.~(12) of the main "
           "paper, method of moving asymptotes) start from the uniform field, the 5\\% sinusoidal perturbation, and "
           "the $p=16$ design. $^*$: stopped at the iteration limit without meeting the convergence test. $^\\dagger$: "
           "exceeds the volume bound by more than the relative feasibility tolerance $10^{-6}$, so infeasible and "
           "excluded. Covers: the best feasible design has worst loss at most $\\tau=0.05$.}\\label{tab:si_minmax}\n"
           "\\begin{tabular}{lrrrrrrrl}\n\\toprule\n"
           " & & \\multicolumn{3}{c}{$p$-norm} & \\multicolumn{3}{c}{Min--max, start} & \\\\\n"
           "\\cmidrule(lr){3-5}\\cmidrule(lr){6-8}\n"
           "Task & Readings & 16 & 64 & 256 & Uniform & Sinusoidal & $p=16$ & Covers \\\\\n\\midrule\n" + "\n".join(rows) +
           "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n")
    with open(os.path.join(ROOT, "v4", "tables", "si_minmax.tex"), "w", encoding="utf-8") as fh:
        fh.write(tex)


def envelope():
    a15 = json.load(open(os.path.join(R, "a15", "consensus.json")))["tau_sweep"]["0.05"]
    a17 = json.load(open(os.path.join(R, "a17", "consensus.json")))["tau_sweep"]["0.05"]
    a31 = json.load(open(os.path.join(R, "a31", "consensus.json")))["jump_screen"]["1.1"]
    pols = {"ask-all": (a15["ask_all"]["bundles"], a15["ask_all"]["questions"]),
            "reference-free screen, J=1.1": (a31["bundles"], a31["q"]),
            "default check, ledger": (a17["N_fixed_S"]["bundles_lazy"], a17["N_fixed_S"]["q"]),
            "CGC-S": (a15["CGC_S"]["bundles"], a15["CGC_S"]["questions"]),
            "CGC": (a15["CGC"]["bundles"], a15["CGC"]["questions"]),
            "robust-first CGC, p=16": (a15["robust_first"]["bundles"], a15["robust_first"]["questions"])}
    checks = {"ask-all": a15["ask_all"], "CGC-S": a15["CGC_S"], "CGC": a15["CGC"],
              "robust-first CGC, p=16": a15["robust_first"]}
    for k, v in checks.items():
        assert v["unsafe"] == 0 and v["released"] == v["cases"] == 134, k
    assert a31["unsafe"] == 0 and a17["N_fixed_S"]["unsafe"] == 0
    p33 = os.path.join(R, "a33", "summary.json")
    if os.path.exists(p33):
        t = json.load(open(p33))["totals"]["robust_first_best"]
        assert t["unsafe"] == 0 and t["released"] == t["cases"] == 134
        pols["robust-first CGC, best robust design"] = (t["bundles"], t["questions"])
    cs = [i / 100 for i in range(0, 5001)]
    best = [min(pols, key=lambda p: pols[p][0] + c * pols[p][1]) for c in cs]
    segments, start = [], 0
    for i in range(1, len(cs) + 1):
        if i == len(cs) or best[i] != best[start]:
            segments.append(dict(policy=best[start], from_c=cs[start], to_c=cs[i - 1]))
            start = i
    cross = []
    for a, b in zip(segments, segments[1:]):
        (ba, qa), (bb, qb) = pols[a["policy"]], pols[b["policy"]]
        cross.append(dict(between=[a["policy"], b["policy"]], c=(bb - ba) / (qa - qb)))
    pair = (pols["CGC-S"][0] - pols["ask-all"][0]) / (pols["ask-all"][1] - pols["CGC-S"][1])
    return dict(policies={k: dict(bundles=v[0], questions=v[1]) for k, v in pols.items()}, segments=segments,
                crossings=cross, pairwise_cgcs_vs_ask_all=pair)


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(ROOT, "v4", "tables"), exist_ok=True)
    tr = track_replay()
    res = dict(sheet_tasks=sheet_tasks(), tracks=tracks(tr), track_rows=tr, envelope=envelope())
    tracks_table(tr)
    minmax_table()
    with open(os.path.join(OUT, "summary.json"), "w") as fh:
        json.dump(res, fh, indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
