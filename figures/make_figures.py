"""Publication figures for the CMAME paper (all data read from results/ and tasks/; no hand-entered values
except the census labels, which are parsed from tasks/literature_screen_v3.md and asserted).

Usage: python figures/make_figures.py [fig names]      (default: all available)
Output: figures/out/<name>.pdf and .png (300 dpi); figures/out/manifest.json (source files per figure)
Print sizes (Elsevier): single column 90 mm, 1.5 column 140 mm, double column 190 mm. Text 7 pt Arial.
"""
import glob
import json
import os
import re
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import FancyBboxPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import littasks as lt  # noqa: E402
import policies as pl  # noqa: E402

OUT = os.path.join(ROOT, "figures", "out")
R = os.path.join(ROOT, "results")
MM = 1 / 25.4
W1, W15, W2 = 90 * MM, 140 * MM, 190 * MM
TAU = 0.05

# validated categorical order (dataviz reference palette, light surface; labels always carry identity)
C = dict(blue="#2a78d6", orange="#eb6834", aqua="#1baf7a", yellow="#eda100", magenta="#e87ba4", violet="#6250d6",
         red="#e34948", green="#008300")
INK, INK2, MUTED, GRID, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUES = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

mpl.rcParams.update({
    "font.family": "Arial", "font.size": 7, "axes.titlesize": 7, "axes.labelsize": 7, "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5, "legend.fontsize": 6.5, "axes.edgecolor": BASE, "axes.labelcolor": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.linewidth": 0.6, "xtick.major.width": 0.6,
    "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": False, "grid.color": GRID, "grid.linewidth": 0.4,
    "lines.linewidth": 1.2, "lines.markersize": 3.5, "legend.frameon": False, "pdf.fonttype": 42,
    "ps.fonttype": 42, "savefig.dpi": 300, "figure.dpi": 150, "axes.titleweight": "bold",
    "axes.titlelocation": "left"})

MANIFEST = {}


def save(fig, name, sources):
    os.makedirs(OUT, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    MANIFEST[name] = sorted(os.path.relpath(s, ROOT).replace("\\", "/") for s in sources)


def load(path):
    with open(path) as fh:
        return json.load(fh)


def panel_label(ax, s):
    ax.set_title(s, loc="left", fontsize=7, fontweight="bold", color=INK, pad=3)


def tau_line(ax, horizontal=True):
    (ax.axhline if horizontal else ax.axvline)(TAU, color=C["red"], lw=0.8, ls=(0, (3, 2)), zorder=1)


# --------------------------------------------------------------------------- Fig. census
def fig_census():
    md = open(os.path.join(ROOT, "tasks", "literature_screen_v3.md"), encoding="utf-8").read()
    comb = md.split("## Combined counts")[1].split("\n## ")[0]
    frame = int(re.search(r"Eligible: \*\*(\d+) / (\d+)\*\*", comb).group(2))
    elig = int(re.search(r"Eligible: \*\*(\d+) /", comb).group(1))
    insc = int(re.search(r"In scope for a structured-grid compliance solver: \*\*(\d+) /", comb).group(1))
    amb = int(re.search(r"In scope and ambiguous: \*\*(\d+)\*\*", comb).group(1))
    amb3 = int(re.search(r"In scope and ambiguous: \*\*\d+\*\* \(2-D \d+, 3-D (\d+)\)", comb).group(1))
    kept = len(lt.TASKS)
    kept3 = sum(T["dim"] == 3 for T in lt.TASKS.values())
    enc = kept + len(lt.RESOLVED)
    enc3 = kept3 + sum(T["dim"] == 3 for T in lt.RESOLVED.values())
    assert enc + len(lt.NOT_ENCODED) == amb, (enc, len(lt.NOT_ENCODED), amb)
    from a05_score_llm import annot
    names = {"load_position": "Load position", "load_extent_distribution": "Load extent / distribution",
             "load_direction": "Load direction", "support_location_extent": "Support location / extent",
             "support_type": "Support type", "domain_extent": "Domain extent / aspect",
             "passive_region": "Passive region", "volume_fraction": "Volume fraction (unstated)",
             "filter_or_solver_setting": "Filter radius (conflicting)"}
    cnt2, cnt3 = {}, {}
    for tid in lt.TASKS:
        for s, cats in annot(tid).items():
            d = cnt3 if lt.TASKS[tid]["dim"] == 3 else cnt2
            d[cats[0]] = d.get(cats[0], 0) + 1
    fig, (a, b) = plt.subplots(1, 2, figsize=(W2, 52 * MM), gridspec_kw=dict(width_ratios=[1.05, 1], wspace=0.55))
    stages = [("arXiv frame", frame, None), ("Eligible compliance examples", elig, None),
              ("In scope (structured grid)", insc, None), ("Ambiguous and in scope", amb, amb3),
              ("Encoded tasks", enc, enc3), ("Open after adjudication", kept, kept3)]
    y = np.arange(len(stages))[::-1]
    for yi, (lab, n, n3) in zip(y, stages):
        a.barh(yi, n, color=BLUES[3], height=0.62)
        if n3:
            a.barh(yi, n3, color=BLUES[5], height=0.62)
        a.text(n + 4, yi, f"{n}" + (f"  (3-D: {n3})" if n3 else ""), va="center", color=INK, fontsize=6.5)
    a.set_yticks(y, [s[0] for s in stages])
    a.set_xlim(0, frame * 1.25)
    a.set_xlabel("Papers / examples")
    a.spines["left"].set_visible(False)
    a.tick_params(axis="y", length=0)
    panel_label(a, "(a) Frozen literature screen")
    order = sorted([k for k in names if cnt2.get(k, 0) + cnt3.get(k, 0)], key=lambda k: cnt2.get(k, 0) + cnt3.get(k, 0))
    yy = np.arange(len(order))
    v2 = [cnt2.get(k, 0) for k in order]
    v3 = [cnt3.get(k, 0) for k in order]
    b.barh(yy, v2, color=BLUES[3], height=0.62, label="2-D")
    b.barh(yy, v3, left=v2, color=BLUES[5], height=0.62, label="3-D")
    for yi, p, q in zip(yy, v2, v3):
        b.text(p + q + 0.3, yi, str(p + q), va="center", fontsize=6.5, color=INK)
    b.set_yticks(yy, [names[k] for k in order])
    b.set_xlabel(f"Ambiguity slots in the {kept} adjudicated tasks")
    b.spines["left"].set_visible(False)
    b.tick_params(axis="y", length=0)
    b.legend(loc="lower right")
    panel_label(b, "(b) What is left open")
    save(fig, "fig_census", [os.path.join(ROOT, "tasks", "literature_screen_v3.md"),
                             os.path.join(ROOT, "src", "littasks.py"),
                             os.path.join(ROOT, "experiments", "a05_score_llm.py")])


# --------------------------------------------------------------------------- Fig. controlled 2-D
def fig_controlled_2d():
    geoms = [("cantilever", "Cantilever", C["blue"], "o"), ("mbb_full", "Full MBB beam", C["orange"], "s"),
             ("l_domain", "L-bracket", C["aqua"], "^"), ("plate_hole", "Plate with hole", C["violet"], "D")]
    tracks = [("center", "(a) Load centre", "Load centre (fraction of edge)"),
              ("width", "(b) Load patch width", "Patch width (relative)"),
              ("split", "(c) Load split", "Split ratio (relative)")]
    fig, axs = plt.subplots(1, 3, figsize=(W2, 50 * MM), sharey=True, gridspec_kw=dict(wspace=0.12))
    srcs = []
    for ax, (tr, title, xl) in zip(axs, tracks):
        for g, lab, col, mk in geoms:
            p = os.path.join(R, "e01", f"{g}_{tr}.json")
            srcs.append(p)
            d = load(p)
            L = np.array(d["L_best"])
            mid = len(d["vals"]) // 2
            x = np.array(d["vals"]) if tr == "center" else np.linspace(0, 1, len(d["vals"]))
            yv = np.maximum(L[mid], 1e-5)
            ax.plot(x, yv, color=col, marker=mk, ms=2.8, lw=1.0, label=lab)
        tau_line(ax)
        ax.set_yscale("log")
        ax.set_ylim(1e-5, 1e4)
        ax.set_xlabel(xl)
        panel_label(ax, title)
        ax.grid(True, axis="y", which="major")
    axs[0].set_ylabel("Loss of the mid-value design")
    axs[1].text(0.02, TAU * 1.4, "τ = 5%", color=C["red"], fontsize=6)
    axs[2].legend(loc="upper left", bbox_to_anchor=(0.0, 1.0))
    save(fig, "fig_controlled_2d", srcs)


# --------------------------------------------------------------------------- Fig. controlled 3-D
def _logy(ax, lo=1e-4, hi=1e5):
    ax.set_yscale("log")
    ax.set_ylim(lo, hi)
    ax.yaxis.set_minor_locator(mpl.ticker.NullLocator())
    ax.yaxis.set_major_locator(mpl.ticker.LogLocator(numticks=10))
    ax.grid(True, axis="y")


def fig_controlled_3d():
    fig, axs = plt.subplots(1, 4, figsize=(W2, 50 * MM), gridspec_kw=dict(wspace=0.42))
    srcs = []
    ax = axs[0]
    for f, lab, col, mk in (("cant_z_off", "Cantilever", C["blue"], "o"), ("deck_off", "Deck", C["orange"], "s")):
        p = os.path.join(R, "e02b", f"{f}.json")
        srcs.append(p)
        d = load(p)
        L = np.array(d["L"])
        ax.plot(d["vals"], np.maximum(L[0], 1e-4), color=col, marker=mk, ms=3, label=lab)
    tau_line(ax)
    _logy(ax)
    ax.set_xlabel("Load offset (elements)")
    ax.set_ylabel("Loss of the nominal design")
    ax.legend(loc="upper left")
    panel_label(ax, "(a) Lateral load offset")
    ax = axs[1]
    p = os.path.join(R, "e02b", "lbr_pos.json")
    srcs.append(p)
    d = load(p)
    L = np.array(d["L"])
    mid = len(d["vals"]) // 2
    ax.plot(d["vals"], np.maximum(L[mid], 1e-4), color=C["aqua"], marker="^", ms=3)
    ax.axvline(d["vals"][mid], color=MUTED, lw=0.6, ls=":")
    tau_line(ax)
    _logy(ax)
    ax.set_xlabel("Load height y (elements)")
    panel_label(ax, "(b) L-bracket load height")
    ax = axs[2]
    p = os.path.join(R, "e02b", "deck_width.json")
    srcs.append(p)
    d2 = load(p)
    L2 = np.array(d2["L"])
    ax.plot(d2["vals"], np.maximum(L2[0], 1e-4), color=C["violet"], marker="D", ms=3)
    tau_line(ax)
    _logy(ax)
    ax.set_xlabel("Patch width across deck (elements)")
    panel_label(ax, "(c) Deck load width")
    ax = axs[3]
    rows = []
    for f, lab in (("cant_z", "Cantilever z"), ("cant_y", "Cantilever y"), ("deck_lane", "Deck lane"),
                   ("cant_z_off", "Cant. z offset"), ("deck_off", "Deck offset"), ("lbr_pos", "L-bracket"),
                   ("deck_width", "Deck width")):
        p = os.path.join(R, "e02b", f"emin_{f}.json")
        if not os.path.exists(p):
            continue
        srcs.append(p)
        e = load(p)
        L6, L9 = np.array(e["L_emin6"]), np.array(e["L_emin9"])
        m = L6 > 1
        rows.append((lab, L6[m], L9[m]))
    cols = [C["blue"], C["orange"], C["aqua"], C["violet"], C["magenta"], C["green"], C["yellow"]]
    for i, (lab, a6, a9) in enumerate(rows):
        ax.scatter(a6, a9 / a6, s=6, color=cols[i % 7], label=lab, lw=0)
    ax.axhline(1, color=MUTED, lw=0.6)
    ax.axhline(1e3, color=MUTED, lw=0.6, ls=(0, (2, 2)))
    ax.text(1.3, 1.3e3, "x1000 = Emin ratio", fontsize=6, color=INK2, va="bottom")
    ax.text(1.3, 1.25, "no change", fontsize=6, color=INK2, va="bottom")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1, 1e6)
    ax.set_ylim(0.5, 1e4)
    ax.xaxis.set_minor_locator(mpl.ticker.NullLocator())
    ax.yaxis.set_minor_locator(mpl.ticker.NullLocator())
    ax.set_xlabel("Loss with Emin = 1e-6")
    ax.set_ylabel("Loss ratio, Emin 1e-9 / 1e-6")
    ax.legend(loc="lower right", bbox_to_anchor=(1.0, 0.09), fontsize=5.5, handletextpad=0.1, borderaxespad=0.1,
              labelspacing=0.2)
    panel_label(ax, "(d) Void-stiffness test")
    save(fig, "fig_controlled_3d", srcs)


# --------------------------------------------------------------------------- Fig. literature loss tables
def _loss_table(tid):
    o = load(os.path.join(R, "e03", f"{tid}.json"))
    keys = o["keys"]
    Cm = np.array(o["C"], float)
    ref = np.array([o["ref"][k] for k in keys])
    return keys, Cm / ref[None, :] - 1, o


BINS = [-1e9, 0.05, 0.2, 1.0, 10.0, 1e30]
BIN_LAB = ["≤ 0.05", "0.05–0.2", "0.2–1", "1–10", "> 10 (large)"]
BIN_COL = [BLUES[0], BLUES[2], BLUES[3], BLUES[5], BLUES[6]]


def _heat(ax, tid, title, short):
    keys, L, o = _loss_table(tid)
    n = len(keys)
    Lc = np.where(np.isfinite(L), np.maximum(L, -1), np.nan)
    cmap = ListedColormap(BIN_COL)
    cmap.set_bad("#ffffff")
    ax.imshow(np.ma.masked_invalid(Lc), cmap=cmap, norm=BoundaryNorm(BINS, len(BIN_COL)), aspect="equal")
    for i in range(n):
        for j in range(n):
            if not np.isfinite(L[i, j]):
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, hatch="////", ec=MUTED, lw=0))
    ax.set_xticks(range(n), short, rotation=90)
    ax.set_yticks(range(n), short)
    ax.set_xlabel("Hidden reading t")
    ax.set_ylabel("Design for reading d")
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    panel_label(ax, title)
    return os.path.join(R, "e03", f"{tid}.json")


def _short(tid):
    T = lt.TASKS[tid]["task"]
    var = [s for s in T.slots if len(T.slots[s]) > 1]
    return [",".join(str(t[s]) for s in var) for t in T.interpretations()]


def fig_lit_tables():
    picks = [("L04", "(a) L04 (2-D)"), ("L16", "(b) L16 (2-D)"), ("L06", "(c) L06 (3-D)"), ("L24", "(d) L24 (3-D)")]
    fig, axs = plt.subplots(1, 4, figsize=(W2, 62 * MM), gridspec_kw=dict(wspace=0.75))
    srcs = [_heat(ax, t, ti, _short(t)) for ax, (t, ti) in zip(axs, picks)]
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in BIN_COL] + \
              [plt.Rectangle((0, 0), 1, 1, fill=False, hatch="////", ec=MUTED)]
    fig.legend(handles, BIN_LAB + ["infeasible"], loc="lower center", ncol=6, bbox_to_anchor=(0.5, -0.06),
               title="Loss of design d under reading t (relative to the best design for t)", title_fontsize=6.5)
    save(fig, "fig_lit_tables", srcs)


# --------------------------------------------------------------------------- Fig. policies
POL = [("no_ask_a0", "Silent default (no question)"), ("ask_all_a0", "Ask every open slot"),
       ("robust", "Robust design, no question*"), ("CGC_a0", "CGC, full table"),
       ("CGC_S_a0", "CGC-S, screening + lazy references"), ("robust_then_H", "Robust if it covers, else CGC*")]


def fig_policies():
    s = load(os.path.join(R, "e03", "summary.json"))["policies"]
    fig, axs = plt.subplots(1, 3, figsize=(W2, 48 * MM), sharey=True, gridspec_kw=dict(wspace=0.15))
    y = np.arange(len(POL))[::-1]
    labels = [f"{lab}" + (f"  [{s[k]['tasks']} tasks]" if s[k]["tasks"] != len(lt.TASKS) else "") for k, lab in POL]
    metrics = [("mean_extra_questions", "(a) Non-mandatory questions", "Mean per case", "{:.2f}"),
               ("false_releases", "(b) Pool-unsafe releases",
                f"Cases (of {s['CGC_a0']['cases']}; robust: {s['robust']['cases']})", "{:d}"),
               ("mean_optimizations", "(c) Reference bundles", "Mean per case", "{:.1f}")]
    for ax, (m, title, xl, fmt) in zip(axs, metrics):
        v = [s[k][m] for k, _ in POL]
        cols = [C["red"] if (m == "false_releases" and x > 0) else BLUES[4] for x in v]
        ax.barh(y, v, color=cols, height=0.6)
        for yi, x in zip(y, v):
            ax.text(x + max(v) * 0.02, yi, fmt.format(x), va="center", fontsize=6.5, color=INK)
        ax.set_xlim(0, max(v) * 1.22 if max(v) > 0 else 1)
        ax.set_xlabel(xl)
        panel_label(ax, title)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
    axs[0].set_yticks(y, labels)
    save(fig, "fig_policies", [os.path.join(R, "e03", "summary.json"), os.path.join(R, "e03", "replay.json")])


# --------------------------------------------------------------------------- Fig. cost
def fig_cost():
    rp = load(os.path.join(R, "e03", "replay.json"))
    rows = []
    for tid in rp:
        if tid.startswith("_") or tid not in lt.TASKS:
            continue
        n = len(lt.interpretations(tid))
        rows.append((tid, n, rp[tid]["CGC_a0"]["mean_optimizations"], rp[tid]["CGC_S_a0"]["mean_optimizations"],
                     rp[tid]["ask_all_a0"]["mean_questions"] - len(lt.TASKS[tid]["task"].mandatory),
                     rp[tid]["CGC_a0"]["mean_questions"] - len(lt.TASKS[tid]["task"].mandatory),
                     lt.TASKS[tid]["dim"]))
    fig, (a, b) = plt.subplots(1, 2, figsize=(W15, 55 * MM), gridspec_kw=dict(wspace=0.35))
    for r in rows:
        mk = "^" if r[6] == 3 else "o"
        a.scatter(r[2], r[3], marker=mk, s=14, color=C["violet"] if r[6] == 3 else C["blue"], lw=0, alpha=0.85)
    lim = [0, max(r[2] for r in rows) + 1]
    a.plot(lim, lim, color=MUTED, lw=0.6)
    a.set_xlabel("Reference bundles, CGC (= number of readings)")
    a.set_ylabel("Reference bundles, CGC-S")
    for r in rows:
        if r[2] >= 9:
            a.annotate(r[0], (r[2], r[3]), xytext=(3, -2), textcoords="offset points", fontsize=6, color=INK2)
    a.scatter([], [], marker="o", color=C["blue"], label="2-D task")
    a.scatter([], [], marker="^", color=C["violet"], label="3-D task")
    a.legend(loc="upper left")
    panel_label(a, "(a) Reference bundles per case")
    M = np.zeros((3, 3), int)                     # per case: (ask_all, consequence-guided) non-mandatory questions
    for tid in rp:
        if tid.startswith("_") or tid not in lt.TASKS:
            continue
        mand = set(lt.TASKS[tid]["task"].mandatory)
        for ra, rh in zip(rp[tid]["_rows"]["ask_all_a0"], rp[tid]["_rows"]["CGC_a0"]):
            assert ra["truth"] == rh["truth"]
            M[len([q for q in rh["asked"] if q not in mand]), len([q for q in ra["asked"] if q not in mand])] += 1
    b.imshow(np.where(M > 0, np.log1p(M), np.nan), cmap=ListedColormap(BLUES[1:6]), origin="lower")
    for i in range(3):
        for j in range(3):
            if M[i, j]:
                b.text(j, i, str(M[i, j]), ha="center", va="center", fontsize=6.5,
                       color="white" if np.log1p(M[i, j]) > 0.6 * np.log1p(M.max()) else INK)
    b.plot([-0.5, 2.5], [-0.5, 2.5], color=MUTED, lw=0.6)
    b.set_xticks(range(3))
    b.set_yticks(range(3))
    b.set_xlabel("Questions, ask every open slot")
    b.set_ylabel("Questions, CGC")
    for sp in b.spines.values():
        sp.set_visible(False)
    b.tick_params(length=0)
    panel_label(b, f"(b) Non-mandatory questions ({M.sum()} cases)")
    save(fig, "fig_cost", [os.path.join(R, "e03", "replay.json")])


# --------------------------------------------------------------------------- Fig. verification
def fig_verification():
    v = load(os.path.join(R, "e04", "verification.json"))
    fig, axs = plt.subplots(1, 2, figsize=(W15, 48 * MM), gridspec_kw=dict(wspace=0.4))
    ax = axs[0]
    c3 = v["C3_two_springs"]
    th = np.linspace(0.2, 0.8, 61)
    reg = (th ** 4 / 0.5 ** 3 + (1 - th) ** 4 / 0.5 ** 3) - 1
    ax.plot(c3["theta"], c3["V_numeric"], color=C["blue"], marker="o", ms=3, label="Optimal value V(θ)")
    ax.plot(th, 1 + reg, color=C["orange"], label="Compliance of x(0.5) at θ")
    ax.set_xlabel("θ (load split)")
    ax.set_ylabel("Compliance")
    ax.annotate(f"regret {100 * c3['regret_commit_0p5_at_0p2_numeric']:.2f}% at θ = 0.2", xy=(0.2, 3.29),
                xytext=(0.27, 2.75), fontsize=6, color=INK2, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
    ax.text(0.52, 1.1, "optimal value V(θ) = 1", fontsize=6, color=INK2)
    ax.text(0.665, 2.25, "committed design\nx(0.5) evaluated at θ", fontsize=6, color=INK2, ha="right")
    panel_label(ax, "(a) Two springs: flat V(θ), large regret")
    ax = axs[1]
    d = v["V1_derivatives"]
    labs = list(d)
    ax.bar(range(len(labs)), [d[k]["max_err_dc_over_max_dc"] for k in labs], color=BLUES[4], width=0.6)
    ax.set_yscale("log")
    ax.set_ylim(1e-10, 1e-5)
    ax.yaxis.set_minor_locator(mpl.ticker.NullLocator())
    ax.set_xticks(range(len(labs)), [k.replace("_cantilever_", " ").replace("_beta", "\nβ=") for k in labs],
                  fontsize=6)
    ax.set_ylabel("max |FD − adjoint| / max |dc/dx|")
    panel_label(ax, "(b) Sensitivity check")
    save(fig, "fig_verification", [os.path.join(R, "e04", "verification.json")])


# --------------------------------------------------------------------------- method schematic
def _box(ax, x, y, w, h, text, fc="#ffffff", ec=BASE, bold=False, fs=6.5):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.008,rounding_size=0.012",
                                fc=fc, ec=ec, lw=0.8))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=INK, fontweight="bold" if bold else "normal",
            linespacing=1.25)


def _arrow(ax, p, q, text=None, off=(0, 0.018), color=INK2):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>", color=color, lw=0.8, shrinkA=0, shrinkB=0,
                                                    mutation_scale=7))
    if text:
        ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], text, ha="center", va="bottom",
                fontsize=6, color=INK2)


def fig_method():
    fig, ax = plt.subplots(figsize=(W2, 70 * MM))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    w, h = 0.2, 0.2
    X = [0.11, 0.37, 0.63, 0.89]
    y1, y2, y3 = 0.8, 0.45, 0.12
    _box(ax, X[0], y1, w, h, "Ambiguous request\n(text, figure or\nliterature example)", fc=BLUES[0])
    _box(ax, X[1], y1, w, h, "Admissible readings Θ\nslots × values: load position,\nsupport extent, domain, ...")
    _box(ax, X[2], y1, w, h, "Mandatory questions\nload sign, unstated volume\nfraction (compliance cannot\n"
                             "distinguish them)")
    _box(ax, X[3], y1, w, h, "Design library L\nnominal + slot extremes;\none factorization per design,\n"
                             "one solve per reading")
    _box(ax, X[3], y2, w, h, "Certified lower bound\n" + r"$\ell_{lo}(d,t)=C_t(d)\,/\,\hat V_t-1$" + "\n"
         + r"$\hat V_t=\mathrm{min}_{e\in L}\,C_t(e)$", fs=6.5)
    ax.text(X[3], y2 - h / 2 - 0.02, "no reference optimization needed", fontsize=6, color=INK2, ha="center",
            va="top")
    _box(ax, X[2], y2, w, h, "Consequential?\n" + r"$\mathrm{min}_d\,\mathrm{max}_t\, \ell_{lo}(d,t) > \tau$ + noise", fc="#fdf3e6",
         ec=C["yellow"])
    _box(ax, X[1], y2, w, h, "Ask the minimax question\n(slot whose worst answer\nleaves the smallest loss)", fc="#eef5fd")
    _box(ax, X[2], y3, w, h, "Certify: references for the\nsurviving readings only;\n"
                             + r"$\mathrm{max}_t$ loss$(d^*,t) \leq \tau$ + noise?")
    _box(ax, X[3], y3, w, h, "Release d*\n(certified for every\nsurviving reading)", fc="#eaf6ef", ec=C["aqua"])
    e = w / 2
    for i in range(3):
        _arrow(ax, (X[i] + e, y1), (X[i + 1] - e, y1))
    _arrow(ax, (X[3], y1 - h / 2), (X[3], y2 + h / 2))
    _arrow(ax, (X[3] - e, y2), (X[2] + e, y2))
    _arrow(ax, (X[2] - e, y2), (X[1] + e, y2), "yes", off=(0, 0.012))
    _arrow(ax, (X[2], y2 - h / 2), (X[2], y3 + h / 2), "no", off=(0.015, -0.01))
    _arrow(ax, (X[2] + e, y3), (X[3] - e, y3), "pass", off=(0, 0.012))
    _arrow(ax, (X[1], y2 + h / 2), (X[1], y1 - h / 2), "answer shrinks Θ", off=(-0.075, -0.01))
    ax.annotate("", xy=(X[1], y2 - h / 2), xytext=(X[2] - e, y3),
                arrowprops=dict(arrowstyle="-|>", color=INK2, lw=0.8, connectionstyle="angle,angleA=180,angleB=90",
                                mutation_scale=7))
    ax.text(X[1] - 0.012, (y2 - h / 2 + y3) / 2, "fail: survivor\ndesigns join L", fontsize=6, color=INK2,
            ha="right", va="center")
    ax.text(0.01, 0.0, "τ = 5% loss tolerance; noise = multi-start spread of each reference design", fontsize=6,
            color=INK2, ha="left", va="bottom")
    save(fig, "fig_method", [os.path.join(ROOT, "src", "policies.py"), os.path.join(ROOT, "src", "consequence.py")])


# --------------------------------------------------------------------------- design galleries
def _best_designs(tid):
    """Best-of-starts optimized design per interpretation (as in the E03 oracle), plus the run keys."""
    import e03_literature_tasks as e03
    import runner
    specs, st, jobs = e03.jobs_for(tid)
    out = {}
    for n, k in enumerate(specs):
        recs = [runner.load(runner.job_key(*j)) for j in jobs[2 * n:2 * n + 2]]
        b = min(recs, key=lambda r: r["compliance"])
        xp, act = runner.load_design(b["key"])
        out[k] = (xp, act, specs[k], b["key"])
    return out


def _dens2(xp, act, spec):
    nx, ny = spec["nelx"] * spec.get("scale", 1), spec["nely"] * spec.get("scale", 1)
    full = np.full(nx * ny, np.nan)
    full[np.asarray(act)] = xp
    return full.reshape(nx, ny).T


def fig_gallery_2d():
    tid = "L04"
    D = _best_designs(tid)
    keys, L, _ = _loss_table(tid)
    rb = load(os.path.join(R, "e03", f"robust_{tid}.json"))
    with np.load(os.path.join(R, "e03", f"robust_{tid}.npz")) as z:
        xr, ar = z["xphys"], z["act"]
    show = [k for k in keys if k.split("=")[1] in ("0.4", "0.5", "0.6")]
    fig, axs = plt.subplots(1, len(show) + 1, figsize=(W2, 36 * MM), gridspec_kw=dict(wspace=0.08))
    for ax, k in zip(axs, show):
        xp, act, spec, _ = D[k]
        ax.imshow(1 - _dens2(xp, act, spec), cmap="gray", vmin=0, vmax=1, origin="lower", interpolation="nearest")
        i = keys.index(k)
        worst = np.max(L[i])
        ax.set_title(f"design for c = {k.split('=')[1]}\nworst loss {worst:.3g}", fontsize=6.5,
                     fontweight="normal", loc="center")
        ax.axis("off")
    spec0 = D[show[0]][2]
    axs[-1].imshow(1 - _dens2(xr, ar, spec0), cmap="gray", vmin=0, vmax=1, origin="lower", interpolation="nearest")
    axs[-1].set_title(f"robust design (no question)\nworst loss {max(rb['ratio']) - 1:.3f}",
                      fontsize=6.5, fontweight="normal", loc="center")
    axs[-1].axis("off")
    save(fig, "fig_gallery_2d", [os.path.join(R, "e03", f"{tid}.json"), os.path.join(R, "e03", f"robust_{tid}.json"),
                                 os.path.join(R, "e03", f"robust_{tid}.npz"), os.path.join(R, "runs")])


def _render3(xp, act, spec, path, size=(700, 420)):
    import pyvista as pv
    nx, ny, nz = spec["nelx"], spec["nely"], spec["nelz"]
    full = np.zeros(nx * ny * nz)
    full[np.asarray(act)] = xp
    arr = np.pad(full.reshape(nx, ny, nz), 1)          # a void layer closes surfaces cut by the box faces
    g = pv.ImageData(dimensions=(nx + 3, ny + 3, nz + 3), origin=(-1, -1, -1))
    g.cell_data["d"] = arr.ravel(order="F")
    surf = g.cell_data_to_point_data().contour([0.5], scalars="d").smooth(n_iter=30)
    g = pv.ImageData(dimensions=(nx + 1, ny + 1, nz + 1))
    p = pv.Plotter(off_screen=True, window_size=size)
    p.set_background("white")
    p.add_mesh(surf, color="#9ec5f4", smooth_shading=True, specular=0.2)
    p.add_mesh(g.outline(), color="#898781", line_width=1)
    c = np.array([nx, ny, nz], float) / 2
    L = float(max(nx, ny, nz))
    p.camera_position = [tuple(c + L * np.array([0.9, 0.75, 1.5])), tuple(c), (0, 1, 0)]   # y is vertical
    p.reset_camera()
    p.camera.zoom(1.1)
    p.screenshot(path)
    p.close()


def fig_gallery_3d():
    import tempfile
    picks = [("L24", ["load=line|sup=1", "load=strip|sup=4"]), ("L06", ["h=0.4|width=line", "h=0.6|width=line"])]
    fig, axs = plt.subplots(1, 4, figsize=(W2, 40 * MM), gridspec_kw=dict(wspace=0.04))
    srcs = []
    with tempfile.TemporaryDirectory() as td:
        i = 0
        for tid, ks in picks:
            D = _best_designs(tid)
            keys, L, _ = _loss_table(tid)
            srcs.append(os.path.join(R, "e03", f"{tid}.json"))
            for k in ks:
                xp, act, spec, _ = D[k]
                png = os.path.join(td, f"{tid}_{i}.png")
                _render3(xp, act, spec, png)
                axs[i].imshow(plt.imread(png))
                worst = np.max(L[keys.index(k)])
                axs[i].set_title(f"{tid}: {k.replace('|', ', ')}\nworst loss {worst:.3g}", fontsize=6.5,
                                 fontweight="normal", loc="center")
                axs[i].axis("off")
                i += 1
    save(fig, "fig_gallery_3d", srcs + [os.path.join(R, "runs")])


def fig_screening():
    d = load(os.path.join(R, "a07", "screening.json"))
    fig, ax = plt.subplots(figsize=(W1, 62 * MM))
    floor = 1e-4

    def tr(x):
        return min(max(x, floor), 1e5) if np.isfinite(x) else 1e5
    for r in d["rows"]:
        ax.scatter(tr(r["B"]), tr(r["B_lo"]), s=14, lw=0, marker="^" if r["dim"] == 3 else "o",
                   color=C["violet"] if r["dim"] == 3 else C["blue"], alpha=0.85)
    ax.axhline(TAU, color=C["red"], lw=0.8, ls=(0, (3, 2)))
    ax.axvline(TAU, color=C["red"], lw=0.8, ls=(0, (3, 2)))
    ax.plot([floor, 1e5], [floor, 1e5], color=MUTED, lw=0.6)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(floor * 0.7, 2e5)
    ax.set_ylim(floor * 0.7, 2e5)
    ax.xaxis.set_minor_locator(mpl.ticker.NullLocator())
    ax.yaxis.set_minor_locator(mpl.ticker.NullLocator())
    ax.set_xlabel("Minimax loss, full table")
    ax.set_ylabel("Screening statistic, library only")
    ax.text(0.97, 0.36, f"flagged & consequential: {d['tp']}\nneither: {d['tn']}\nfalse flags: {d['fp']}, "
            f"misses: {d['fn']}\noptimizations: {d['library_optimizations']} vs {d['full_table_optimizations']}",
            transform=ax.transAxes, va="bottom", ha="right", fontsize=6, color=INK2)
    ax.scatter([], [], marker="o", color=C["blue"], label="2-D task")
    ax.scatter([], [], marker="^", color=C["violet"], label="3-D task")
    ax.legend(loc="lower right")
    panel_label(ax, "Library screening vs full table")
    save(fig, "fig_screening", [os.path.join(R, "a07", "screening.json")])


def fig_llm():
    sc = load(os.path.join(R, "e05", "scores.json"))
    models = [m for m in ("codex", "claude") if m in sc]
    label = {"codex": "gpt-6.1-sol (Codex CLI)", "claude": "claude-opus-5-5 (Claude CLI)"}
    fig, axs = plt.subplots(1, 2, figsize=(W15, 50 * MM), gridspec_kw=dict(wspace=0.55))
    ax = axs[0]
    mets = [("recall_layout", "Layout-slot recall"), ("recall_mandatory", "Mandatory-slot recall"),
            ("layout_precision", "Layout items in annotated categories")]
    y = np.arange(len(mets))[::-1]
    h = 0.36
    for i, m in enumerate(models):
        v = [sc[m][k] for k, _ in mets]
        ax.barh(y + (0.5 - i) * h, v, height=h, color=[C["blue"], C["orange"]][i], label=label[m])
        for yi, x in zip(y + (0.5 - i) * h, v):
            ax.text(x + 0.02, yi, f"{x:.2f}", va="center", fontsize=6, color=INK)
    ax.set_yticks(y, [lab for _, lab in mets])
    ax.set_xlim(0, 1.2)
    ax.set_xlabel("Fraction")
    ax.legend(loc="upper center", bbox_to_anchor=(0.35, -0.28), ncol=2, fontsize=6)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    panel_label(ax, "(a) Category detection (text only)")
    ax = axs[1]
    v = [sc[m]["mean_layout_items"] for m in models]
    ax.bar(range(len(models)), v, color=[C["blue"], C["orange"]][:len(models)], width=0.55)
    for i, x in enumerate(v):
        ax.text(i, x + 0.3, f"{x:.1f}", ha="center", fontsize=6.5, color=INK)
    ann = np.mean([len([s for s in lt.TASKS[t]["task"].slots if s not in lt.TASKS[t]["task"].mandatory])
                   for t in lt.TASKS])
    ax.axhline(ann, color=C["red"], lw=0.8, ls=(0, (3, 2)))
    ax.set_xlim(-0.6, 2.3)
    ax.text(2.25, ann + 0.4, f"annotated slots\nper task: {ann:.1f}", fontsize=6, color=INK2, ha="right",
            va="bottom")
    ax.set_xticks(range(len(models)), [label[m].split(" ")[0] for m in models])
    ax.set_ylabel("Layout items listed per task")
    panel_label(ax, "(b) Items an LLM would ask about")
    save(fig, "fig_llm", [os.path.join(R, "e05", "scores.json")])


FIGS = dict(method=fig_method, screening=fig_screening, llm=fig_llm, census=fig_census, gallery_2d=fig_gallery_2d, gallery_3d=fig_gallery_3d, controlled_2d=fig_controlled_2d, controlled_3d=fig_controlled_3d,
            lit_tables=fig_lit_tables, policies=fig_policies, cost=fig_cost, verification=fig_verification)


def main():
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        FIGS[n]()
        print("ok", n)
    mp = os.path.join(OUT, "manifest.json")
    old = load(mp) if os.path.exists(mp) else {}
    old.update(MANIFEST)
    with open(mp, "w") as fh:
        json.dump(old, fh, indent=1)


if __name__ == "__main__":
    main()
