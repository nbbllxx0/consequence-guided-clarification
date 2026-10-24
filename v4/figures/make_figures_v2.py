"""V2 figures for the CMAME paper: the data of figures/make_figures.py, redesigned presentation.

Usage: python v2/figures/make_figures_v2.py [names]      (default: all)
Output: v2/figures/<name>.pdf and .png (300 dpi); v2/figures/manifest.json (source files per figure)

Every plotted value is read from results/ and tasks/ through figures/make_figures.py (imported as `base`);
the worked example in fig_method is recomputed from results/e03/L06.json and asserted against policies.cgc_s.
Print widths: 90 mm and 140 mm (Elsevier), full width 164 mm (the preprint text block); Arial, 7 pt text,
6.5 pt ticks, nothing below 6 pt. Categorical palette #2a78d6 / #e0632b / #12966a / #8a5cc2 (dataviz palette
validator, light surface, all checks pass, 2026-10-23); orange also marks "exceeds tau" in the method schematic,
so result figures that colour by tau use it only for that meaning.
"""
import json
import os
import sys

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "figures"))
import make_figures as base  # noqa: E402  (data access: littasks, policies, loss tables, design loaders)

lt, pl = base.lt, base.pl
R, TAU, MM = base.R, base.TAU, base.MM
W1, W15 = base.W1, base.W15
W2 = 164 * MM      # full width of the reviewed preprint (166 mm text block); figures are included at natural size

INK, INK2, MUTED, GRID, EDGE, FILL = "#1a1a19", "#4a4945", "#7d7b74", "#e4e2dc", "#c9c7bd", "#f4f3ef"
BLUE, ORANGE, GREEN, VIOLET = "#2a78d6", "#e0632b", "#12966a", "#8a5cc2"
BLUES = base.BLUES
OVER = "#fcefe7"                     # light orange tint: loss above tau
OK_FILL, BAD_FILL = "#e3f3ec", "#fbe6dc"

mpl.rcParams.update({
    "font.family": "Arial", "font.size": 7, "axes.titlesize": 7, "axes.labelsize": 7, "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5, "legend.fontsize": 6.5, "legend.frameon": False, "axes.linewidth": 0.5,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "xtick.major.width": 0.5, "ytick.major.width": 0.5, "xtick.major.size": 2, "ytick.major.size": 2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False, "grid.color": GRID,
    "grid.linewidth": 0.4, "lines.linewidth": 1.0, "lines.markersize": 3.2, "pdf.fonttype": 42, "ps.fonttype": 42,
    "savefig.dpi": 300, "figure.dpi": 150, "mathtext.fontset": "custom", "mathtext.rm": "Arial",
    "mathtext.it": "Arial:italic", "mathtext.bf": "Arial:bold", "mathtext.cal": "cmsy10", "axes.unicode_minus": False})

MANIFEST = {}


def save(fig, name, sources, tight=True):
    if tight:                     # cropped output keeps the design width: rescale the canvas until the tight box fits it
        target = fig.get_figwidth()
        for _ in range(6):
            fig.canvas.draw()
            bb = fig.get_tightbbox(fig.canvas.get_renderer())
            width = bb.width + 0.04
            if abs(width - target) < 0.004:
                break
            fig.set_figwidth(fig.get_figwidth() * target / width)
    for ext in ("pdf", "png"):
        kw = dict(bbox_inches="tight", pad_inches=0.02) if tight else {}
        fig.savefig(os.path.join(HERE, f"{name}.{ext}"), facecolor="white", **kw)
    plt.close(fig)
    MANIFEST[name] = sorted(os.path.relpath(s, ROOT).replace("\\", "/") for s in sources)


def head(ax, letter, title="", dx=0.0, y=1.0, pad=4):
    """Bold panel letter and a plain header, left-aligned at the axes edge shifted by dx points."""
    ax.annotate(letter, (0, y), xycoords="axes fraction", xytext=(dx, pad), textcoords="offset points",
                fontsize=8, fontweight="bold", color=INK, ha="left", va="bottom", annotation_clip=False)
    if title:
        ax.annotate(title, (0, y), xycoords="axes fraction", xytext=(dx + 11, pad), textcoords="offset points",
                    fontsize=7, color=INK, ha="left", va="bottom", annotation_clip=False)


def tau_band(ax, top, label=None, xy=None):
    ax.axhspan(TAU, top, color=OVER, lw=0, zorder=0)
    ax.axhline(TAU, color=ORANGE, lw=0.7, ls=(0, (3, 2)), zorder=1)
    if label:
        ax.text(*xy, label, color=ORANGE, fontsize=6.2, ha="left", va="bottom", transform=ax.get_yaxis_transform())


def logy(ax, lo, hi):
    ax.set_yscale("log")
    ax.set_ylim(lo, hi)
    ax.yaxis.set_minor_locator(mpl.ticker.NullLocator())
    ax.yaxis.set_major_locator(mpl.ticker.LogLocator(numticks=12))
    ax.grid(True, axis="y", which="major")
    ax.set_axisbelow(True)


def hbar_axes(ax):
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(True, axis="x")
    ax.set_axisbelow(True)


# =========================================================================== Fig. 1: method schematic
def _l06_trace():
    """CGC-S on L06 with hidden reading h = 0.4, line: seed library, library cross-evaluation, question choice and
    verification, recomputed from results/e03/L06.json with zero allowance and asserted against policies.cgc_s."""
    tid = "L06"
    path = os.path.join(R, "e03", f"{tid}.json")
    o = base.load(path)
    keys = o["keys"]
    C = {(d, t): float(o["C"][i][j]) for i, d in enumerate(keys) for j, t in enumerate(keys)}
    orc = pl.Oracle(ref=o["ref"], C=C, noise={k: 0.0 for k in keys})
    task = lt.TASKS[tid]["task"]
    assert not task.mandatory
    truth = {"h": 0.4, "width": "line"}
    out = pl.cgc_s(task, orc, truth, TAU, a0=0.0)
    interps = task.interpretations()
    nom = dict(task.nominal)
    seed = [nom] + [dict(nom, **{s: v}) for s, vals in sorted(task.slots.items()) if len(vals) > 1
                    for v in (vals[0], vals[-1])]
    K = []
    for t in seed:
        if pl.ikey(t) in keys and pl.ikey(t) not in K:
            K.append(pl.ikey(t))

    def lo(d, t, lib):
        return C[(d, t)] / min(C[(e, t)] for e in lib) - 1.0

    def best(S, lib):
        w = {d: max(lo(d, pl.ikey(t), lib) for t in S) for d in lib}
        d = min(sorted(w), key=lambda c: w[c])
        return d, w[d]

    L0 = np.array([[lo(d, t, K) for t in keys] for d in K])
    d0, B0 = best(interps, K)
    worst = {s: max(best([t for t in interps if t[s] == v], K)[1] for v in task.slots[s]) for s in task.slots}
    q = min(sorted(worst), key=lambda s: worst[s])
    S1 = [t for t in interps if t[q] == truth[q]]
    K1 = list(K) + [k for k in [pl.ikey(dict(nom, **{q: truth[q]}))] if k not in K]
    _, B1 = best(S1, K1)
    K2 = K1 + [pl.ikey(t) for t in S1 if pl.ikey(t) not in K1]
    d2, B2 = best(S1, K2)
    assert B0 > TAU and B1 <= TAU and B2 <= TAU
    assert out.asked == [q] and out.commit == d2 and out.optimizations == len(K2) and out.released
    assert abs(out.extra["B_local"] - B2) < 1e-12
    return dict(keys=keys, K=K, L0=L0, d0=d0, B0=B0, worst=worst, q=q, S1=[pl.ikey(t) for t in S1], K2=K2,
                commit=d2, B2=B2, true_loss=out.true_loss, cross=out.cross_evals, path=path)


def _short_key(k):
    d = dict(p.split("=") for p in k.split("|"))
    return f"{d['h']} {d['width'][0].upper()}"


def fig_method():
    tr = _l06_trace()
    nread = [len(lt.interpretations(t)) for t in lt.TASKS]
    s = base.load(os.path.join(R, "e03", "summary.json"))["policies"]["CGC_S_a0"]
    assert s["cases"] == sum(nread)
    fig = plt.figure(figsize=(W2, 134 * MM * W2 / (190 * MM)))   # layout drawn in 190 x 134 units
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 190)
    ax.set_ylim(0, 134)
    ax.axis("off")

    def card(x, y, w, h, title=None, fc=FILL, ec=EDGE, lw=0.6, ls="-", r=1.6, z=1):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw,
                                    ls=ls, zorder=z))
        if title:
            ax.text(x + 2.2, y + h - 2.0, title, fontsize=7, fontweight="bold", color=INK, va="top", ha="left",
                    zorder=5)

    def txt(x, y, s, size=6.7, color=INK, ha="left", va="top", **kw):
        return ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va, linespacing=1.3, zorder=5, **kw)

    def arrow(x0, y0, x1, y1, color=INK2, lw=0.8, ls="-"):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), zorder=6, annotation_clip=False,
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, ls=ls, shrinkA=0, shrinkB=0,
                                    mutation_scale=6))

    def path(pts, color=INK2, lw=0.8, ls="-"):
        ax.plot([p[0] for p in pts[:-1]], [p[1] for p in pts[:-1]], color=color, lw=lw, ls=ls, zorder=6,
                solid_capstyle="butt")
        arrow(*pts[-2], *pts[-1], color=color, lw=lw, ls=ls)

    def chip(x, y, s, fc="white", ec=EDGE, color=INK, w=None, h=3.6, size=6.7, bold=False):
        w = w or 1.2 + 1.25 * len(s)
        ax.add_patch(FancyBboxPatch((x, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=0.9", fc=fc, ec=ec,
                                    lw=0.6, zorder=4))
        ax.text(x + w / 2, y, s, fontsize=size, color=color, ha="center", va="center", zorder=5,
                fontweight="bold" if bold else "normal")
        return x + w

    def row(y, letter, title):
        ax.text(1.0, y, letter, fontsize=8, fontweight="bold", color=INK, va="center", ha="left")
        ax.text(7.2, y, title, fontsize=7.5, color=INK, va="center", ha="left")

    # ---------------------------------------------------------------- row a: specification
    ya, ha_ = 94.0, 33.0
    row(131.0, "(a)", "Specify: admissible readings and the release rule")
    card(1, ya, 42, ha_, "Source specification")
    s_, x0, y0 = 12.0, 8.0, ya + 9.5                      # L06 cube in oblique view: left face fixed, load on right face
    dx, dy = 0.45 * s_, 0.32 * s_
    ax.add_patch(Polygon([[x0, y0], [x0 + s_, y0], [x0 + s_, y0 + s_], [x0, y0 + s_]], fc="white", ec=INK2, lw=0.6,
                         zorder=3))
    ax.add_patch(Polygon([[x0, y0 + s_], [x0 + s_, y0 + s_], [x0 + s_ + dx, y0 + s_ + dy], [x0 + dx, y0 + s_ + dy]],
                         fc="#ebeae4", ec=INK2, lw=0.6, zorder=3))
    ax.add_patch(Polygon([[x0 + s_, y0], [x0 + s_ + dx, y0 + dy], [x0 + s_ + dx, y0 + s_ + dy], [x0 + s_, y0 + s_]],
                         fc="#dcdad2", ec=INK2, lw=0.6, zorder=3))
    for yy in np.linspace(y0 + 0.6, y0 + s_ - 0.6, 7):    # fixed face (x = 0): wall hatching
        ax.plot([x0 - 1.4, x0], [yy - 1.0, yy], color=INK2, lw=0.45, zorder=3)
    ax.plot([x0, x0], [y0, y0 + s_], color=INK, lw=1.2, zorder=4)
    hb = 0.2 * s_
    for hv in task_h(tr):
        yl = y0 + hv * s_
        nominal = abs(hv - 0.5) < 1e-9
        if nominal:
            ax.add_patch(Polygon([[x0 + s_, yl - hb / 2], [x0 + s_ + dx, yl - hb / 2 + dy],
                                  [x0 + s_ + dx, yl + hb / 2 + dy], [x0 + s_, yl + hb / 2]],
                                 fc=ORANGE, alpha=0.22, ec="none", zorder=4))
        ax.plot([x0 + s_, x0 + s_ + dx], [yl, yl + dy], color=ORANGE, lw=1.1 if nominal else 0.6,
                ls="-" if nominal else (0, (2, 1.5)), zorder=5)
    for f in (0.2, 0.55, 0.9):                           # downward load arrows along the nominal line
        xa, yl = x0 + s_ + f * dx, y0 + 0.5 * s_ + f * dy
        arrow(xa, yl + 3.4, xa, yl + 0.2, color=ORANGE, lw=0.6)
    txt(x0 + s_ + dx + 1.6, y0 + 0.55 * s_ + dy, "height h?", size=6.7, color=ORANGE, va="center")
    txt(x0 + s_ + dx + 1.6, y0 + 0.55 * s_ + dy - 4.2, "line or strip?", size=6.7, color=ORANGE, va="center")
    txt(x0 - 2.4, y0 + 0.5 * s_, "fixed", size=6.5, color=INK2, ha="right", va="center", rotation=90)
    txt(3.2, ya + 6.2, "L06: load line drawn at about\nmid-height on the opposite face", size=6.6, color=INK2)

    card(47, ya, 50, ha_, "Admissible readings Θ")
    task = lt.TASKS["L06"]["task"]
    yy = ya + 23.5
    for slot, lab in (("h", "load height h"), ("width", "load width")):
        txt(49.5, yy, lab, size=6.7, color=INK2, va="center")
        xx = 69.0
        for v in task.slots[slot]:
            nominal = v == task.nominal[slot]
            xx = chip(xx, yy, str(v), ec=BLUE if nominal else EDGE, bold=nominal) + 1.2
        yy -= 5.6
    n6 = len(task.interpretations())
    txt(49.5, ya + 10.5, f"Θ = 3 × 2 = {n6} readings; bold = default\n(the silent default)", size=6.6,
        color=INK2)
    txt(49.5, ya + 3.6, f"Benchmark: {len(nread)} tasks, {min(nread)}–{max(nread)} readings",
        size=6.6, color=INK2)

    card(101, ya, 42, ha_, "Mandatory slots")
    txt(103.2, ya + 25.0, "asked first by every policy:", size=6.7, color=INK2)
    for i, it in enumerate(("load direction or sign", "unstated volume fraction")):
        chip(103.2, ya + 19.0 - 5.0 * i, it, w=36)
    txt(103.2, ya + 9.5, "sign: no compliance effect;\nvolume: sets the design set;\nL06 has neither", size=6.6,
        color=INK2)

    card(147, ya, 42, ha_, "Release rule", fc="white", ec=BLUE, lw=0.9)
    txt(149.2, ya + 25.0, "choose one design d; release it\nonly if, for every open " + r"$t\in\mathcal{S}$,",
        size=6.7)
    txt(168.0, ya + 13.5, r"$\ell(d,t)=\dfrac{C_t(d)}{V_t}-1\leq\tau$", size=7.0, ha="center", va="center")
    txt(149.2, ya + 8.0, f"τ = {TAU:g}, zero allowance\n$V_t$: best-known compliance", size=6.6, color=INK2)
    for xa in (43.0, 97.0, 143.0):
        arrow(xa + 0.4, ya + ha_ / 2, xa + 3.6, ya + ha_ / 2)

    # ---------------------------------------------------------------- row b: screening loop
    yb, hb_ = 52.0, 36.0
    row(90.5, "(b)", "Screen with computed designs; ask when no computed design passes "
                   "(CGC-S; worked example L06, hidden reading h = 0.4, line)")
    card(1, yb, 42, hb_, r"Seed library $\mathcal{K}$")
    txt(3.2, yb + 28.0, "default + extreme of each slot:", size=6.7, color=INK2)
    for i, k in enumerate(tr["K"]):
        chip(3.2 + (i % 2) * 19.0, yb + 21.5 - 5.0 * (i // 2), _short_key(k), w=17.5)
    txt(3.2, yb + 10.5, "bundle = two-start optimization:\ndesign, compliance, start spread",
        size=6.6, color=INK2)

    card(47, yb, 50, hb_, r"Cross-evaluate $\mathcal{K}$")
    L0 = tr["L0"]
    nr, nc = L0.shape
    cw, chh = 4.6, 3.3
    gx, gy = 63.0, yb + 24.5
    cols = ListedColormap(base.BIN_COL)
    norm = BoundaryNorm(base.BINS, len(base.BIN_COL))
    for i in range(nr):
        for j in range(nc):
            ax.add_patch(Rectangle((gx + j * cw, gy - (i + 1) * chh), cw, chh, fc=cols(norm(L0[i, j])), ec="white",
                                   lw=0.6, zorder=4))
        txt(gx - 1.0, gy - (i + 0.5) * chh, _short_key(tr["K"][i]), size=6.5, ha="right", va="center")
        txt(gx + nc * cw + 1.0, gy - (i + 0.5) * chh, f"{L0[i].max():.3g}", size=6.5, color=INK2, va="center")
    i0 = tr["K"].index(tr["d0"])
    ax.add_patch(Rectangle((gx, gy - (i0 + 1) * chh), nc * cw, chh, fill=False, ec=INK, lw=0.9, zorder=5))
    for j, k in enumerate(tr["keys"]):
        txt(gx + (j + 0.5) * cw, gy + 0.5, _short_key(k).replace(" ", "\n"), size=6.5, ha="center", va="bottom")
    txt(gx + nc * cw + 1.0, gy + 0.5, "max\n" + r"$\ell_{\mathrm{lo}}$", size=6.5, color=INK2, va="bottom")
    txt(51.0, gy - nr * chh / 2, "design", size=6.5, color=INK2, ha="center", va="center", rotation=90)
    lx, ly = gx + 9.0, gy - nr * chh - 2.6               # loss-bin key under the matrix (bins of the loss-table figure)
    txt(lx - 1.0, ly, r"$\ell_{\mathrm{lo}}\leq\tau$", size=6.5, color=INK2, ha="right", va="center")
    for b_, c_ in enumerate(base.BIN_COL):
        ax.add_patch(Rectangle((lx + b_ * 3.0, ly - 1.0), 3.0, 2.0, fc=c_, ec="white", lw=0.5, zorder=4))
    txt(lx + 15.8, ly, "> 10", size=6.5, color=INK2, va="center")
    txt(49.2, yb + 6.3, r"$\ell_{\mathrm{lo}}(d,t)=C_t(d)\,/\,U_t(\mathcal{K})-1\;\leq\;\ell(d,t)$", size=6.9)
    txt(49.2, yb + 2.6, "one factorization per design", size=6.5, color=INK2)

    card(101, yb, 42, hb_, "Choose the question", fc="white", ec=ORANGE, lw=0.9)
    txt(103.2, yb + 28.0, r"$B_{\mathcal{K}}(\mathcal{S})=\min_d\,\max_{t\in\mathcal{S}}\,\ell_{\mathrm{lo}}=$" + f" {tr['B0']:.3g}", size=6.9)
    txt(103.2, yb + 23.2, r"$>\tau$: no library design covers $\mathcal{S}$", size=6.6, color=ORANGE)
    txt(103.2, yb + 17.5, "worst B after the answer:", size=6.7, color=INK2)
    for i, (sl, lab) in enumerate((("h", "ask h"), ("width", "ask width"))):
        pick = sl == tr["q"]
        chip(103.2, yb + 12.5 - 4.8 * i, lab, w=16, ec=ORANGE if pick else EDGE, bold=pick)
        txt(121.0, yb + 12.5 - 4.8 * i, f"{tr['worst'][sl]:.3g}", size=6.7, va="center",
            color=INK if pick else INK2, fontweight="bold" if pick else "normal")
    txt(103.2, yb + 3.8, "minimax slot s* = h", size=6.6, color=INK2)

    card(147, yb, 42, hb_, r"Answer prunes $\mathcal{S}$")
    txt(149.2, yb + 28.0, "the engineer answers h = 0.4:", size=6.7, color=INK2)
    xx = 149.2
    for k in tr["S1"]:
        xx = chip(xx, yb + 21.5, _short_key(k), w=13) + 1.2
    txt(149.2, yb + 16.5, r"$\mathcal{S}$: " + f"{n6} → {len(tr['S1'])} readings; answered\ndefault reading joins " + r"$\mathcal{K}$",
        size=6.6, color=INK2)
    txt(149.2, yb + 7.0, "repeat while " + r"$B_{\mathcal{K}}>\tau$" + " and a\nquestion remains (budget 3)", size=6.6,
        color=INK2)
    for xa in (43.0, 97.0, 143.0):
        arrow(xa + 0.4, yb + hb_ / 2, xa + 3.6, yb + hb_ / 2)
    yl = yb - 2.4                                         # loop back: answer -> re-screen (bridge over the exit)
    ax.plot([168.0, 168.0, 123.2], [yb, yl, yl], color=INK2, lw=0.7, zorder=6)
    path([(120.8, yl), (72.0, yl), (72.0, yb + 0.1)], color=INK2, lw=0.7)
    txt(104.0, yl - 0.6, r"re-screen the smaller $\mathcal{S}$", size=6.5, color=INK2, ha="center")

    # ---------------------------------------------------------------- row c: verification
    yc, hc = 3.0, 32.0
    row(42.2, "(c)", "Verify against local references, then release or withhold")
    card(1, yc, 60, hc, "Bundles for every open reading")
    txt(3.2, yc + 24.0, f"request each missing bundle;\nL06: {len(tr['K2'])} bundles in total "
                        f"(CGC: all {n6})", size=6.6, color=INK2)
    txt(3.2, yc + 13.0, r"$U_t(\mathcal{K})=\min_{e\in\mathcal{K}}C_t(e)\;\geq\;V_t$", size=7.0)
    txt(3.2, yc + 6.4, "local references only; unrequested values\nstay hidden from the policy", size=6.6,
        color=INK2)
    path([(122.0, yb), (122.0, yc + hc + 4.0), (31.0, yc + hc + 4.0), (31.0, yc + hc + 0.1)], color=INK2,
         lw=0.7)
    txt(123.4, yc + hc + 8.0, r"$B_{\mathcal{K}}\leq\tau$" + ", or no question left", size=6.5, color=INK2, va="center")
    card(65, yc, 45, hc, "Local check", fc="white", ec=BLUE, lw=0.9)
    txt(67.2, yc + 23.5, r"$\max_{t\in\mathcal{S}}\,\ell_{\mathrm{lo}}(d^*,t;\mathcal{K})\leq\tau\;?$", size=7.0)
    txt(67.2, yc + 15.0, f"L06: d* = {_short_key(tr['commit'])} design,\nmax local loss {tr['B2']:.2g}",
        size=6.6, color=INK2)
    txt(67.2, yc + 6.4, "fails with a question left:\nask the local minimax slot", size=6.6, color=INK2)
    arrow(61.4, yc + hc / 2, 64.6, yc + hc / 2)
    ax.add_patch(FancyBboxPatch((115, yc + 18.5), 30, 9.5, boxstyle="round,pad=0,rounding_size=1.2", fc=OK_FILL,
                                ec=GREEN, lw=0.9, zorder=3))
    txt(130.0, yc + 23.2, "Release d*", size=7, color=GREEN, ha="center", va="center", fontweight="bold")
    ax.add_patch(FancyBboxPatch((115, yc + 4.0), 30, 9.5, boxstyle="round,pad=0,rounding_size=1.2", fc=BAD_FILL,
                                ec=ORANGE, lw=0.9, zorder=3))
    txt(130.0, yc + 10.4, "Withhold release", size=7, color=ORANGE, ha="center", va="center",
        fontweight="bold")
    txt(130.0, yc + 6.6, "no question left", size=6.5, color=INK2, ha="center", va="center")
    path([(110.4, yc + 23.2), (114.6, yc + 23.2)], color=INK2)
    txt(112.5, yc + 24.4, "yes", size=6.5, color=INK2, ha="center", va="bottom")
    path([(110.4, yc + 8.8), (114.6, yc + 8.8)], color=INK2)
    txt(112.5, yc + 10.0, "no", size=6.5, color=INK2, ha="center", va="bottom")
    card(149, yc, 40, hc, "Offline audit", fc="white", ec=MUTED, lw=0.7, ls=(0, (3, 2)))
    txt(151.2, yc + 24.0, "independent of the policy:\nthe released design against\nthe full best-known table\n"
                          "(every reading, every pair)", size=6.6, color=INK2)
    txt(151.2, yc + 10.0, f"L06: true loss {tr['true_loss']:.2g}\npool-unsafe if ℓ > τ for any\nopen reading",
        size=6.6, color=INK2)
    arrow(145.4, yc + 23.2, 148.6, yc + 23.2, color=MUTED, ls=(0, (2, 1.5)))
    save(fig, "fig_method", [tr["path"], os.path.join(ROOT, "src", "policies.py"),
                             os.path.join(ROOT, "src", "littasks.py"), os.path.join(R, "e03", "summary.json")],
         tight=False)


def task_h(tr):
    return sorted({float(dict(p.split("=") for p in k.split("|"))["h"]) for k in tr["keys"]})


# =========================================================================== census
def fig_census():
    import re
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
    assert enc + len(lt.NOT_ENCODED) == amb
    from a05_score_llm import annot
    names = {"load_position": "Load position", "load_extent_distribution": "Load extent / distribution",
             "load_direction": "Load direction", "support_location_extent": "Support location / extent",
             "support_type": "Support type", "domain_extent": "Domain extent / aspect",
             "passive_region": "Passive region", "volume_fraction": "Volume fraction (unstated)",
             "filter_or_solver_setting": "Filter radius (conflicting)"}
    cnt2, cnt3 = {}, {}
    for tid in lt.TASKS:
        for _, cats in annot(tid).items():
            d = cnt3 if lt.TASKS[tid]["dim"] == 3 else cnt2
            d[cats[0]] = d.get(cats[0], 0) + 1
    fig, (a, b) = plt.subplots(1, 2, figsize=(W2, 56 * MM), gridspec_kw=dict(width_ratios=[1.1, 1], wspace=0.62))
    stages = [("arXiv frame", frame, None, None), ("Eligible compliance examples", elig, None, None),
              ("In scope (structured grid)", insc, None, None), ("Ambiguous and in scope", amb, amb3, None),
              ("Encoded tasks", enc, enc3, f"{len(lt.NOT_ENCODED)} not encodable"),
              ("Open after adjudication", kept, kept3, f"{len(lt.RESOLVED)} resolved")]
    y = np.arange(len(stages))[::-1]
    for i, (yi, (lab, n, n3, why)) in enumerate(zip(y, stages)):
        last = i == len(stages) - 1
        c2, c3 = (BLUE, BLUES[5]) if last else (BLUES[2], BLUES[4])
        n2 = n - (n3 or 0)
        a.barh(yi, n2, color=c2, height=0.62, lw=0)
        if n3:
            a.barh(yi, n3, left=n2, color=c3, height=0.62, lw=0)
            a.plot([n2, n2], [yi - 0.31, yi + 0.31], color="white", lw=0.8, solid_capstyle="butt")
        a.text(n + 5, yi, f"{n}" + (f"   2-D {n2} · 3-D {n3}" if n3 else ""), va="center", color=INK,
               fontsize=6.5, fontweight="bold" if last else "normal")
        if i:
            drop = stages[i - 1][1] - n
            a.text(frame * 1.33, yi + 0.5, f"−{drop}" + (f" {why.split(' ', 1)[1]}" if why else ""), va="center", ha="right",
                   fontsize=6.0, color=MUTED)
    a.set_yticks(y, [s[0] for s in stages])
    a.set_xlim(0, frame * 1.33)
    a.set_xlabel("Papers or examples")
    hbar_axes(a)
    head(a, "(a)", "Frozen literature screen", dx=-118)
    order = sorted([k for k in names if cnt2.get(k, 0) + cnt3.get(k, 0)],
                   key=lambda k: cnt2.get(k, 0) + cnt3.get(k, 0))
    yy = np.arange(len(order))
    v2 = np.array([cnt2.get(k, 0) for k in order])
    v3 = np.array([cnt3.get(k, 0) for k in order])
    b.barh(yy, v2, color=BLUES[3], height=0.62, lw=0)
    b.barh(yy, v3, left=v2, color=BLUES[5], height=0.62, lw=0)
    for yi, p, q in zip(yy, v2, v3):
        if p and q:
            b.plot([p, p], [yi - 0.31, yi + 0.31], color="white", lw=0.8, solid_capstyle="butt")
    for yi, p, q in zip(yy, v2, v3):
        b.text(p + q + 0.25, yi, str(p + q), va="center", fontsize=6.5, color=INK)
    b.set_yticks(yy, [names[k] for k in order])
    b.set_xlabel(f"Open slots in the {kept} adjudicated tasks")
    hbar_axes(b)
    b.set_xlim(0, (v2 + v3).max() * 1.15)
    top = len(order) - 1
    b.text(v2[top] / 2, top + 0.62, "2-D", ha="center", va="bottom", fontsize=6.2, color=INK2)
    b.text(v2[top] + v3[top] / 2, top + 0.62, "3-D", ha="center", va="bottom", fontsize=6.2, color=INK2)
    head(b, "(b)", "What the source leaves open", dx=-104)
    save(fig, "fig_census", [os.path.join(ROOT, "tasks", "literature_screen_v3.md"),
                             os.path.join(ROOT, "src", "littasks.py"),
                             os.path.join(ROOT, "experiments", "a05_score_llm.py")])


# =========================================================================== controlled 2-D
GEOMS = [("cantilever", "Cantilever", BLUE, "o"), ("mbb_full", "Full MBB beam", ORANGE, "s"),
         ("l_domain", "L-domain", GREEN, "^"), ("plate_hole", "Perforated plate", VIOLET, "D")]


def fig_controlled_2d():
    tracks = [("center", "(a)", "Load center", "Load center (fraction of edge)"),
              ("width", "(b)", "Load patch width", "Patch width (fraction of edge)"),
              ("split", "(c)", "Load split between two patches", "Load fraction on one patch")]
    fig, axs = plt.subplots(1, 3, figsize=(W2, 54 * MM), sharey=True, gridspec_kw=dict(wspace=0.1))
    srcs = []
    for ax, (tk, let, title, xl) in zip(axs, tracks):
        for g, lab, col, mk in GEOMS:
            p = os.path.join(R, "e01", f"{g}_{tk}.json")
            srcs.append(p)
            d = base.load(p)
            L = np.array(d["L_best"])
            mid = len(d["vals"]) // 2
            x = np.array(d["vals"])
            ax.plot(x, np.maximum(L[mid], 1e-5), color=col, marker=mk, ms=2.6, lw=0.9, mec="white", mew=0.3,
                    label=lab, zorder=3)
        logy(ax, 1e-5, 1e4)
        tau_band(ax, 1e4)
        ax.set_xlabel(xl)
        head(ax, let, title, dx=-26 if ax is axs[0] else -4)
    axs[0].set_ylabel("Loss of the default design")
    axs[1].text(0.03, TAU * 1.5, "τ = 0.05", color=ORANGE, fontsize=6.2, transform=axs[1].get_yaxis_transform())
    axs[1].text(0.03, 2e3, "loss > τ: the silent default fails", color=ORANGE, fontsize=6.2,
                transform=axs[1].get_yaxis_transform(), va="center")
    h, lab = axs[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.1), handlelength=1.8, columnspacing=1.6)
    save(fig, "fig_controlled_2d", srcs)


# =========================================================================== controlled 3-D
def fig_controlled_3d():
    fig, axs = plt.subplots(1, 4, figsize=(W2, 54 * MM), gridspec_kw=dict(wspace=0.42))
    srcs = []
    ax = axs[0]
    for f, lab, col, mk in (("cant_z_off", "Cantilever", BLUE, "o"), ("deck_off", "Deck", ORANGE, "s")):
        p = os.path.join(R, "e02b", f"{f}.json")
        srcs.append(p)
        d = base.load(p)
        ax.plot(d["vals"], np.maximum(np.array(d["L"])[0], 1e-4), color=col, marker=mk, ms=3, mec="white",
                mew=0.3, label=lab, zorder=3)
        ax.text(d["vals"][-1] + 0.15, max(np.array(d["L"])[0][-1], 1e-4), lab, color=col, fontsize=6.2,
                va="center")
    logy(ax, 1e-4, 1e5)
    tau_band(ax, 1e5)
    ax.set_xlim(right=d["vals"][-1] + 1.6)
    ax.set_xlabel("Load offset (elements)")
    ax.set_ylabel("Loss of the default design")
    head(ax, "(a)", "Lateral load offset", dx=-26)
    ax = axs[1]
    p = os.path.join(R, "e02b", "lbr_pos.json")
    srcs.append(p)
    d = base.load(p)
    mid = len(d["vals"]) // 2
    ax.plot(d["vals"], np.maximum(np.array(d["L"])[mid], 1e-4), color=GREEN, marker="^", ms=3, mec="white",
            mew=0.3, zorder=3)
    ax.axvline(d["vals"][mid], color=MUTED, lw=0.6, ls=":")
    ax.text(d["vals"][mid] + 0.3, 3e4, "default", fontsize=6.0, color=INK2)
    logy(ax, 1e-4, 1e5)
    tau_band(ax, 1e5)
    ax.set_xlabel("Load height y (elements)")
    head(ax, "(b)", "L-bracket load height", dx=-4)
    ax = axs[2]
    p = os.path.join(R, "e02b", "deck_width.json")
    srcs.append(p)
    d2 = base.load(p)
    ax.plot(d2["vals"], np.maximum(np.array(d2["L"])[0], 1e-4), color=VIOLET, marker="D", ms=2.8, mec="white",
            mew=0.3, zorder=3)
    logy(ax, 1e-4, 1e5)
    tau_band(ax, 1e5)
    ax.set_xlabel("Patch width across deck (elements)")
    head(ax, "(c)", "Deck load width", dx=-4)
    ax = axs[3]
    fam = {"cant": ("Cantilever", "o"), "deck": ("Deck", "s"), "lbr": ("L-bracket", "^")}
    seen = set()
    for f in ("cant_z", "cant_y", "deck_lane", "cant_z_off", "deck_off", "lbr_pos", "deck_width"):
        p = os.path.join(R, "e02b", f"emin_{f}.json")
        if not os.path.exists(p):
            continue
        srcs.append(p)
        e = base.load(p)
        L6, L9 = np.array(e["L_emin6"]), np.array(e["L_emin9"])
        m = L6 > 1
        lab, mk = fam[f.split("_")[0]]
        ax.scatter(L6[m], L9[m] / L6[m], s=7, marker=mk, color=BLUE, alpha=0.75, lw=0,
                   label=lab if lab not in seen else None, zorder=3)
        seen.add(lab)
    ax.axhline(1, color=MUTED, lw=0.6)
    ax.axhline(1e3, color=MUTED, lw=0.6, ls=(0, (2, 2)))
    ax.text(1.3, 1.35e3, "×1000: loss scales with void stiffness", fontsize=6.5, color=INK2, va="bottom")
    ax.text(1.3, 1.3, "×1: loss independent of void stiffness", fontsize=6.5, color=INK2, va="bottom")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1, 1e6)
    ax.set_ylim(0.5, 1e4)
    ax.xaxis.set_minor_locator(mpl.ticker.NullLocator())
    ax.yaxis.set_minor_locator(mpl.ticker.NullLocator())
    ax.set_xlabel(r"Loss with $E_{\min}/E_0=10^{-6}$")
    ax.set_ylabel(r"Loss at $10^{-9}$ / loss at $10^{-6}$")
    ax.legend(loc="lower right", bbox_to_anchor=(1.0, 0.13), handletextpad=0.1, borderaxespad=0.1, labelspacing=0.25)
    head(ax, "(d)", "Large losses track void stiffness", dx=-26)
    save(fig, "fig_controlled_3d", srcs)


# =========================================================================== cross-evaluation tables
def _fmt(x):
    return f"{x:,.0f}" if x >= 100 else f"{x:.2g}"


def _heat(ax, tid, letter, short, slots):
    keys, L, _ = base._loss_table(tid)
    n = len(keys)
    cmap = ListedColormap(base.BIN_COL)
    cmap.set_bad("#ffffff")
    Lc = np.where(np.isfinite(L), np.maximum(L, -1), np.nan)
    ax.imshow(np.ma.masked_invalid(Lc), cmap=cmap, norm=BoundaryNorm(base.BINS, len(base.BIN_COL)), aspect="equal")
    for i in range(n + 1):
        ax.axhline(i - 0.5, color="white", lw=0.6)
        ax.axvline(i - 0.5, color="white", lw=0.6)
    for i in range(n):
        for j in range(n):
            if not np.isfinite(L[i, j]):
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, hatch="////", ec=MUTED, lw=0))
    worst = np.where(np.isfinite(L), L, np.inf).max(1)
    i0 = int(np.argmin(worst))
    ax.add_patch(Rectangle((-0.5, i0 - 0.5), n, 1, fill=False, ec=INK, lw=1.0, zorder=5))
    ax.set_xticks(range(n), short, rotation=90)
    ax.set_yticks(range(n), short)
    ax.set_xlabel("Hidden reading t")
    ax.set_ylabel("Design from reading d")
    ax.tick_params(length=0, pad=1.5)
    for s in ax.spines.values():
        s.set_visible(False)
    T = lt.TASKS[tid]
    head(ax, letter, f"{tid} ({T['dim']}-D; {slots})", dx=-22, pad=12)
    ax.annotate(f"minimax loss {_fmt(worst[i0])}", (0, 1), xycoords="axes fraction", xytext=(-11, 3),
                textcoords="offset points", fontsize=6.2, color=INK2, ha="left", va="bottom")
    return os.path.join(R, "e03", f"{tid}.json")


SLOT_NAMES = {"c": "load center", "sup": "support", "load": "load", "h": "height", "width": "width"}


def fig_lit_tables():
    picks = [("L04", "(a)"), ("L16", "(b)"), ("L06", "(c)"), ("L24", "(d)")]
    fig, axs = plt.subplots(1, 4, figsize=(W2, 66 * MM), gridspec_kw=dict(wspace=0.95))
    srcs = []
    for ax, (t, let) in zip(axs, picks):
        T = lt.TASKS[t]["task"]
        var = [s for s in T.slots if len(T.slots[s]) > 1]
        short = base._short(t)
        if t == "L16":                      # support and load lengths in percent of L
            short = [",".join(str(round(100 * float(x))) for x in k.split(",")) for k in short]
        srcs.append(_heat(ax, t, let, short, ", ".join(SLOT_NAMES.get(v, v) for v in var)))
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in base.BIN_COL] + \
              [plt.Rectangle((0, 0), 1, 1, fill=False, hatch="////", ec=MUTED),
               plt.Rectangle((0, 0), 1, 1, fill=False, ec=INK, lw=1.0)]
    fig.legend(handles, base.BIN_LAB + ["infeasible", "minimax design"], loc="lower center", ncol=7,
               bbox_to_anchor=(0.5, -0.03), handlelength=1.4, columnspacing=1.2,
               title="Loss ℓ(d, t) of design d under reading t", title_fontsize=6.5)
    save(fig, "fig_lit_tables", srcs)


# =========================================================================== galleries
def _chip_title(ax, line1, worst):
    ok = worst <= TAU
    ax.set_title(line1, fontsize=6.5, color=INK, loc="center", pad=21, fontweight="normal")
    ax.text(0.5, 1.12, f"worst loss {_fmt(worst)}", transform=ax.transAxes, ha="center", va="bottom", fontsize=6.5,
            color=GREEN if ok else ORANGE, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.25", fc=OK_FILL if ok else BAD_FILL, ec="none"))


def _cant_glyphs(ax, spec, cvals, c, H, tick=MUTED):
    nx, ny = spec["nelx"], spec["nely"]
    for yy in np.linspace(2, ny - 2, 9):
        ax.plot([-4, 0], [yy - 3, yy], color=INK2, lw=0.45, clip_on=False)
    ax.plot([0, 0], [0, ny], color=INK, lw=1.0, clip_on=False)
    for cv in cvals:
        ax.plot([nx + 1.5, nx + 4], [cv * H, cv * H], color=tick, lw=0.6, clip_on=False)
    if c is None:
        return
    for dy in (-3, 0, 3):
        ax.annotate("", xy=(nx + 2.5, c * H + dy - 0.5), xytext=(nx + 2.5, c * H + dy + 5.5), annotation_clip=False,
                    arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=0.6, mutation_scale=4, shrinkA=0, shrinkB=0))


def fig_gallery_2d():
    tid = "L04"
    D = base._best_designs(tid)
    keys, L, _ = base._loss_table(tid)
    rb = base.load(os.path.join(R, "e03", f"robust_{tid}.json"))
    with np.load(os.path.join(R, "e03", f"robust_{tid}.npz")) as z:
        xr, ar = z["xphys"], z["act"]
    cvals = [float(k.split("=")[1]) for k in keys]
    show = [k for k in keys if k.split("=")[1] in ("0.4", "0.5", "0.6")]
    fig, axs = plt.subplots(1, len(show) + 1, figsize=(W2, 34 * MM), gridspec_kw=dict(wspace=0.16))
    spec0 = D[show[0]][2]
    H = spec0["nely"]
    for ax, k in zip(axs, show):
        xp, act, spec, _ = D[k]
        ax.imshow(1 - base._dens2(xp, act, spec), cmap="gray", vmin=0, vmax=1, origin="lower",
                  interpolation="nearest", extent=(0, spec["nelx"], 0, spec["nely"]))
        c = float(k.split("=")[1])
        _cant_glyphs(ax, spec, cvals, c, H)
        _chip_title(ax, f"design for load center c = {c:g}", float(np.max(L[keys.index(k)])))
        ax.axis("off")
    axs[-1].imshow(1 - base._dens2(xr, ar, spec0), cmap="gray", vmin=0, vmax=1, origin="lower",
                   interpolation="nearest", extent=(0, spec0["nelx"], 0, spec0["nely"]))
    _cant_glyphs(axs[-1], spec0, cvals, None, H, tick=ORANGE)
    _chip_title(axs[-1], "robust design, no question", float(max(rb["ratio"]) - 1))
    axs[-1].axis("off")
    fig.text(0.5, 0.12, "ticks at the loaded edge: the five admissible load centers c = " +
             ", ".join(f"{v:g}" for v in cvals) + "; worst loss over all five readings", ha="center", va="top",
             fontsize=6.2, color=INK2)
    save(fig, "fig_gallery_2d", [os.path.join(R, "e03", f"{tid}.json"), os.path.join(R, "e03", f"robust_{tid}.json"),
                                 os.path.join(R, "e03", f"robust_{tid}.npz"), os.path.join(R, "runs")])


def fig_gallery_3d():
    import tempfile
    picks = [("L24", ["load=line|sup=1", "load=strip|sup=4"]), ("L06", ["h=0.4|width=line", "h=0.6|width=line"])]
    fig, axs = plt.subplots(1, 4, figsize=(W2, 44 * MM), gridspec_kw=dict(wspace=0.06))
    srcs = []
    with tempfile.TemporaryDirectory() as td:
        i = 0
        for tid, ks in picks:
            D = base._best_designs(tid)
            keys, L, _ = base._loss_table(tid)
            srcs.append(os.path.join(R, "e03", f"{tid}.json"))
            for k in ks:
                xp, act, spec, _ = D[k]
                png = os.path.join(td, f"{tid}_{i}.png")
                base._render3(xp, act, spec, png)
                img = plt.imread(png)
                rows = np.where((img[..., :3] < 0.97).any(axis=(1, 2)))[0]
                colsx = np.where((img[..., :3] < 0.97).any(axis=(0, 2)))[0]
                img = img[max(rows[0] - 6, 0):rows[-1] + 6, max(colsx[0] - 6, 0):colsx[-1] + 6, :3]
                hh, ww = img.shape[:2]                    # pad to a common 0.8 aspect so the panels align
                H_ = max(hh, int(0.8 * ww))
                W_ = max(ww, int(H_ / 0.8))
                canvas = np.ones((H_, W_, 3))
                canvas[(H_ - hh) // 2:(H_ - hh) // 2 + hh, (W_ - ww) // 2:(W_ - ww) // 2 + ww] = img
                axs[i].imshow(canvas)
                _chip_title(axs[i], f"{tid}: " + k.replace("|", ", ").replace("sup=", "support=").replace("=", " = "),
                            float(np.max(L[keys.index(k)])))
                axs[i].axis("off")
                i += 1
    save(fig, "fig_gallery_3d", srcs + [os.path.join(R, "runs")])


# =========================================================================== policies
POL = [("no_ask_a0", "Silent default (no question)", MUTED), ("ask_all_a0", "Ask-all (every open slot)", MUTED),
       ("robust", "Robust design, no question", VIOLET), ("robust_then_H", "Robust-first CGC", VIOLET),
       ("CGC_a0", "CGC, full table", BLUE), ("CGC_S_a0", "CGC-S, screening + lazy references", BLUE)]


def fig_policies():
    s = base.load(os.path.join(R, "e03", "summary.json"))["policies"]
    a15 = base.load(os.path.join(R, "a15", "consensus.json"))
    ra, rf = a15["robust_alone"], a15["tau_sweep"][f"{TAU:g}"]["robust_first"]
    s = dict(s, robust=dict(tasks=ra["tasks"], cases=ra["cases"], mean_extra_questions=0.0,
                            false_releases=ra["unsafe"], mean_optimizations=ra["bundles"] / ra["cases"]),
             robust_then_H=dict(tasks=len(lt.TASKS), cases=rf["cases"],
                                mean_extra_questions=rf["questions"] / rf["cases"],
                                false_releases=rf["unsafe"], mean_optimizations=rf["bundles"] / rf["cases"]))
    fig, axs = plt.subplots(1, 3, figsize=(W2, 50 * MM), sharey=True, gridspec_kw=dict(wspace=0.12))
    y = np.array([6.6, 5.6, 4.1, 3.1, 1.6, 0.6])
    labels = [lab + (f"  [{s[k]['tasks']} tasks]" if s[k]["tasks"] != len(lt.TASKS) else "") for k, lab, _ in POL]
    metrics = [("mean_extra_questions", "(a)", "Non-mandatory questions", "Mean per case", "{:.2f}"),
               ("false_releases", "(b)", "Pool-unsafe releases",
                f"Cases (of {s['CGC_a0']['cases']}; robust: {s['robust']['cases']})", "{:d}"),
               ("mean_optimizations", "(c)", "Reference bundles", "Mean per case", "{:.1f}")]
    for ax, (m, let, title, xl, fmt) in zip(axs, metrics):
        v = [s[k][m] for k, _, _ in POL]
        cols = [ORANGE if (m == "false_releases" and x > 0) else (GREEN if m == "false_releases" else c)
                for x, (_, _, c) in zip(v, POL)]
        ax.barh(y, v, color=cols, height=0.62, lw=0)
        for yi, x, c in zip(y, v, cols):
            ax.text(x + max(v) * 0.025, yi, fmt.format(x), va="center", fontsize=6.5,
                    color=ORANGE if c == ORANGE else INK, fontweight="bold" if c == ORANGE else "normal")
            if m == "false_releases" and x == 0:
                ax.plot([0], [yi], marker="|", color=GREEN, ms=6, mew=1.2)
        ax.set_xlim(0, max(v) * 1.22 if max(v) > 0 else 1)
        ax.set_xlabel(xl)
        hbar_axes(ax)
        head(ax, let, title, dx=-4 if ax is not axs[0] else -128)
        for yb in (2.35, 4.85):
            ax.axhline(yb, color=GRID, lw=0.6)
    axs[0].set_yticks(y, labels)
    for t, yy, c in (("Baselines", 6.1, MUTED), ("Robust design", 3.6, VIOLET), ("Consequence-guided", 1.1, BLUE)):
        axs[0].text(-0.02, yy + 1.0, t, transform=axs[0].get_yaxis_transform(), ha="right", va="center",
                    fontsize=6.5, color=c, fontweight="bold")
    axs[0].set_ylim(-0.1, 7.6)
    save(fig, "fig_policies", [os.path.join(R, "e03", "summary.json"), os.path.join(R, "e03", "replay.json"),
                               os.path.join(R, "a15", "consensus.json")])


# =========================================================================== cost
def fig_cost():
    rp = base.load(os.path.join(R, "e03", "replay.json"))
    pts = {}
    M = np.zeros((3, 3), int)
    for tid in rp:
        if tid.startswith("_") or tid not in lt.TASKS:
            continue
        dim = lt.TASKS[tid]["dim"]
        mand = set(lt.TASKS[tid]["task"].mandatory)
        rows = rp[tid]["_rows"]
        for rc, rs, ra in zip(rows["CGC_a0"], rows["CGC_S_a0"], rows["ask_all_a0"]):
            assert rc["truth"] == rs["truth"] == ra["truth"]
            key = (rc["optimizations"], rs["optimizations"], dim)
            pts[key] = pts.get(key, 0) + 1
            M[len([q for q in rc["asked"] if q not in mand]), len([q for q in ra["asked"] if q not in mand])] += 1
    fig, (a, b) = plt.subplots(1, 2, figsize=(W15, 60 * MM), gridspec_kw=dict(wspace=0.38, width_ratios=[1.25, 1]))
    lim = max(k[0] for k in pts) + 1
    a.fill_between([0, lim], [0, 0], [0, lim], color="#eef4fc", lw=0, zorder=0)
    a.plot([0, lim], [0, lim], color=MUTED, lw=0.6, zorder=1)
    a.text(lim * 0.62, lim * 0.28, "CGC-S cheaper", fontsize=6.2, color=BLUE, ha="center")
    a.text(lim * 0.47, lim * 0.56, "equal cost", fontsize=6.0, color=MUTED, rotation=38, ha="center")
    for (x, yv, dim), n in sorted(pts.items()):
        a.scatter(x, yv, s=6 + 5 * n, marker="^" if dim == 3 else "o", color=VIOLET if dim == 3 else BLUE,
                  alpha=0.8, lw=0.4, ec="white", zorder=3)
    for n in (1, 5, 10):
        a.scatter([], [], s=6 + 5 * n, color=MUTED, lw=0, label=f"{n} case" + ("s" if n > 1 else ""))
    a.scatter([], [], marker="o", color=BLUE, label="2-D task")
    a.scatter([], [], marker="^", color=VIOLET, label="3-D task")
    a.legend(loc="upper left", labelspacing=0.5, handletextpad=0.3)
    a.set_xlim(0, lim)
    a.set_ylim(0, lim)
    a.set_xlabel("Bundles, CGC (= number of readings)")
    a.set_ylabel("Bundles, CGC-S")
    head(a, "(a)", "Reference bundles per case", dx=-24)
    cats = [("same as ask-all", "#c9c6bd", INK), ("1 fewer", BLUES[3], "white"), ("2 fewer", BLUES[5], "white")]
    yrow = np.arange(3)[::-1]
    for r, j in zip(yrow, range(3)):                      # j = questions asked by ask-all
        left = 0
        for k, (lab, col, tc) in enumerate(cats):         # k = questions CGC saves
            n = int(M[j - k, j]) if j - k >= 0 else 0
            if n:
                b.barh(r, n, left=left, color=col, height=0.62, lw=0, label=lab if j == 2 else None)
                if left:
                    b.plot([left, left], [r - 0.31, r + 0.31], color="white", lw=0.8, solid_capstyle="butt")
                if n >= 6:
                    b.text(left + n / 2, r, str(n), ha="center", va="center", fontsize=6.5, color=tc)
                left += n
        b.text(left + 1.5, r, f"{int(M[:, j].sum())} cases", va="center", fontsize=6.5, color=INK2)
    saved = int(sum(k * M[j - k, j] for j in range(3) for k in range(1, j + 1)))
    b.set_yticks(yrow, [f"ask-all asks {j}" for j in range(3)])
    b.set_xlim(0, M.sum(0).max() * 1.32)
    b.set_xlabel("Cases")
    hbar_axes(b)
    b.legend(title="CGC asks", loc="upper right", frameon=False, handlelength=1.0, title_fontsize=6.5)
    head(b, "(b)", f"CGC questions vs ask-all ({saved} saved)", dx=-46)
    save(fig, "fig_cost", [os.path.join(R, "e03", "replay.json")])


# =========================================================================== verification (SI)
def fig_verification():
    v = base.load(os.path.join(R, "e04", "verification.json"))
    fig, axs = plt.subplots(1, 2, figsize=(W15, 50 * MM), gridspec_kw=dict(wspace=0.42))
    ax = axs[0]
    c3 = v["C3_two_springs"]
    th = np.linspace(0.2, 0.8, 61)
    reg = (th ** 4 / 0.5 ** 3 + (1 - th) ** 4 / 0.5 ** 3) - 1
    ax.fill_between(th, 1, 1 + reg, color=OVER, lw=0)
    ax.plot(th, 1 + reg, color=ORANGE, lw=1.1)
    ax.plot(c3["theta"], c3["V_numeric"], color=BLUE, marker="o", ms=3, mec="white", mew=0.3, lw=1.1)
    ax.text(0.5, 0.95, "optimal value V(θ) = 1", fontsize=6.2, color=BLUE, ha="center", va="top")
    ax.set_ylim(0.78, 3.45)
    ax.text(0.5, 2.2, "committed design x(0.5)\nevaluated at θ", fontsize=6.2, color=ORANGE, ha="center")
    ax.annotate(f"regret {100 * c3['regret_commit_0p5_at_0p2_numeric']:.2f}% at θ = 0.2", xy=(0.2, 3.29),
                xytext=(0.26, 2.85), fontsize=6.2, color=INK2, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.5))
    ax.set_xlabel("θ (load split)")
    ax.set_ylabel("Compliance")
    ax.grid(True, axis="y")
    ax.set_axisbelow(True)
    head(ax, "(a)", "Two springs: flat V(θ), large regret", dx=-24)
    ax = axs[1]
    d = v["V1_derivatives"]
    labs = list(d)
    ax.bar(range(len(labs)), [d[k]["max_err_dc_over_max_dc"] for k in labs], color=BLUE, width=0.55, lw=0)
    ax.set_yscale("log")
    ax.set_ylim(1e-10, 1e-5)
    ax.yaxis.set_minor_locator(mpl.ticker.NullLocator())
    ax.grid(True, axis="y")
    ax.set_axisbelow(True)
    ax.set_xticks(range(len(labs)), [k.replace("_cantilever_", " ").replace("_beta", "\nβ = ") for k in labs])
    ax.set_ylabel("max |FD − adjoint| / max |dc/dx|")
    head(ax, "(b)", "Sensitivity check", dx=-30)
    save(fig, "fig_verification", [os.path.join(R, "e04", "verification.json")])


# =========================================================================== screening (SI)
def fig_screening():
    d = base.load(os.path.join(R, "a07", "screening_a0.json"))
    fig, ax = plt.subplots(figsize=(W1, 66 * MM))
    floor = 1e-4

    def tr(x):
        return min(max(x, floor), 1e5) if np.isfinite(x) else 1e5
    lo, hi = floor * 0.7, 2e5
    ax.fill_between([TAU, hi], TAU, hi, color=OVER, lw=0, zorder=0)
    ax.fill_between([lo, TAU], lo, TAU, color="#eef4fc", lw=0, zorder=0)
    for r in d["rows"]:
        ax.scatter(tr(r["B"]), tr(r["B_lo"]), s=13, lw=0.3, ec="white", marker="^" if r["dim"] == 3 else "o",
                   color=VIOLET if r["dim"] == 3 else BLUE, alpha=0.9, zorder=3)
    ax.axhline(TAU, color=ORANGE, lw=0.7, ls=(0, (3, 2)))
    ax.axvline(TAU, color=ORANGE, lw=0.7, ls=(0, (3, 2)))
    ax.plot([floor, 1e5], [floor, 1e5], color=MUTED, lw=0.6)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.xaxis.set_minor_locator(mpl.ticker.NullLocator())
    ax.yaxis.set_minor_locator(mpl.ticker.NullLocator())
    ax.set_xlabel("Minimax loss, full table")
    ax.set_ylabel("Screening statistic, library only")
    ax.text(0.97, 0.06, f"consequential, flagged: {d['tp']}", transform=ax.transAxes, ha="right", fontsize=6.2,
            color=ORANGE)
    ax.text(0.02, 0.95, f"harmless,\nnot flagged: {d['tn']}", transform=ax.transAxes, ha="left", va="top",
            fontsize=6.2, color=BLUE)
    ax.text(0.02, 0.80, f"false flags {d['fp']},\nmisses {d['fn']}", transform=ax.transAxes, ha="left",
            va="top", fontsize=6.2, color=INK2)
    ax.text(0.02, 0.65, f"bundles: {d['library_optimizations']}\n(full table {d['full_table_optimizations']})",
            transform=ax.transAxes, ha="left", va="top", fontsize=6.2, color=INK2)
    ax.scatter([], [], marker="o", color=BLUE, label="2-D task")
    ax.scatter([], [], marker="^", color=VIOLET, label="3-D task")
    ax.legend(loc="lower right", bbox_to_anchor=(1.0, 0.1))
    head(ax, "", "Library screening vs full table", dx=-22)
    save(fig, "fig_screening", [os.path.join(R, "a07", "screening_a0.json")])


# =========================================================================== LLM front end
def fig_llm():
    sc = base.load(os.path.join(R, "e05", "scores.json"))
    models = [m for m in ("claude", "codex") if m in sc]
    label = {"codex": "GPT-6.1-Sol (Codex CLI)", "claude": "Claude Opus 5.5 (Claude CLI)"}
    col = {"claude": BLUE, "codex": ORANGE}
    fig, axs = plt.subplots(1, 2, figsize=(W15, 52 * MM), gridspec_kw=dict(wspace=0.5, width_ratios=[1.5, 1]))
    ax = axs[0]
    mets = [("recall_layout", "Layout-slot recall"), ("recall_mandatory", "Mandatory-slot recall"),
            ("layout_precision", "Layout items in\nencoded categories")]
    y = np.arange(len(mets))[::-1]
    h = 0.34
    for i, m in enumerate(models):
        v = [sc[m][k] for k, _ in mets]
        ax.barh(y + (0.5 - i) * h, v, height=h * 0.92, color=col[m], label=label[m], lw=0)
        for yi, x in zip(y + (0.5 - i) * h, v):
            ax.text(x + 0.02, yi, f"{x:.2f}", va="center", fontsize=6.2, color=INK)
    ax.set_yticks(y, [lab for _, lab in mets])
    ax.set_xlim(0, 1.12)
    ax.set_xlabel("Fraction")
    hbar_axes(ax)
    head(ax, "(a)", "Category detection (text only)", dx=-70)
    ax = axs[1]
    v = [sc[m]["mean_layout_items"] for m in models]
    ax.bar(range(len(models)), v, color=[col[m] for m in models], width=0.55, lw=0)
    for i, x in enumerate(v):
        ax.text(i, x + 0.3, f"{x:.1f}", ha="center", fontsize=6.5, color=INK)
    ann = np.mean([len([s for s in lt.TASKS[t]["task"].slots if s not in lt.TASKS[t]["task"].mandatory])
                   for t in lt.TASKS])
    ax.axhline(ann, color=INK2, lw=0.7, ls=(0, (3, 2)))
    ax.text(2.85, ann + 0.4, f"encoded slots\nper task: {ann:.1f}", fontsize=6.2, color=INK2, ha="right",
            va="bottom")
    ax.set_xlim(-0.6, 2.9)
    ax.set_xticks(range(len(models)), [{"claude": "Claude", "codex": "GPT"}[m] for m in models])
    ax.set_ylabel("Layout items listed per run")
    ax.grid(True, axis="y")
    ax.set_axisbelow(True)
    head(ax, "(b)", "Layout items listed per run", dx=-26)
    hd, lb = axs[0].get_legend_handles_labels()
    fig.legend(hd, lb, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.1))
    save(fig, "fig_llm", [os.path.join(R, "e05", "scores.json")])


FIGS = dict(method=fig_method, census=fig_census, controlled_2d=fig_controlled_2d,
            controlled_3d=fig_controlled_3d, lit_tables=fig_lit_tables, gallery_2d=fig_gallery_2d,
            gallery_3d=fig_gallery_3d, policies=fig_policies, cost=fig_cost, llm=fig_llm,
            verification=fig_verification, screening=fig_screening)


def main():
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        FIGS[n]()
        print("ok", n)
    mp = os.path.join(HERE, "manifest.json")
    old = base.load(mp) if os.path.exists(mp) else {}
    old.update(MANIFEST)
    with open(mp, "w") as fh:
        json.dump(old, fh, indent=1)


if __name__ == "__main__":
    main()
