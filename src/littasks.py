"""Literature-derived tasks (frozen arXiv sample, tasks/literature_screen_v1.json and _v2.json).

Each task reconstructs the primary example of a screened paper on the structured-grid
solver. Ambiguity slots and admissible values are an annotation of what the paper's text
and figures leave open; each slot carries the reason and the evidence location from the
screen record. Admissible ranges for vague phrases ("about mid-height") are an operational
annotation convention, stated per slot. Mandatory slots (direction sign, unstated volume
fraction) are always asked; their computational value is fixed to a representative value
because the answer is known to the policy after asking.

Reconstruction choices that the paper does not determine (mesh resolution, patch width for
point loads) are listed in `recon`. Convention: an unstated filter radius, penalty or projection
setting is a solver setting fixed in `recon`, not an ambiguity slot; conflicting stated values
are a slot.
"""
from __future__ import annotations

import itertools
import os

import numpy as np

from policies import Task


def _cant2(nelx, nely, vf, load_center, load_width, direction=(0, -1), clamp="left", extra=None):
    s = dict(dim=2, nelx=nelx, nely=nely, volfrac=vf, domain={"type": "rect"},
             supports=[{"edge": clamp, "comp": "xy"}],
             load_cases=[{"patches": [{"edge": "right", "center": load_center, "width": load_width,
                                       "dir": list(direction)}]}])
    if extra:
        s.update(extra)
    return s


TASKS = {}


def register(task_id, source, dim, slots, nominal, build, mandatory=(), reasons=None, recon=None, admissible=None):
    TASKS[task_id] = dict(task=Task(task_id, slots, nominal, tuple(mandatory), admissible),
                          source=source, dim=dim, build=build, reasons=reasons or {}, recon=recon or [])


# --------------------------------------------------------------------------- 2-D
# L01  arXiv:2403.04937 (screen #1): L-bracket; cut-out size and load position not stated.
def _l01(t):
    n = 60
    arm = t["arm"] * n
    return dict(dim=2, nelx=n, nely=n, volfrac=0.4, domain={"type": "L", "cut_x": arm, "cut_y": arm},
                supports=[{"edge": "top", "range": [0, arm], "comp": "xy"}],
                load_cases=[{"patches": [{"segment": [n, 0, n, arm], "center": t["load"] * arm,
                                          "width": 4.0, "dir": [0, -1]}]}])


register("L01", dict(arxiv="2403.04937", position=1), 2,
         slots=dict(arm=[0.4, 0.5], load=[0.1, 0.5, 0.9], volfrac=[0.4]), nominal=dict(arm=0.4, load=0.5, volfrac=0.4),
         build=_l01, mandatory=("volfrac",),
         reasons=dict(arm="cut-out size not stated; only a schematic (screen #1, figure)",
                      load="'point load at the right edge'; position not stated (figure)",
                      volfrac="not stated for this instance (dataset range 0.12-0.5): mandatory"),
         recon=["64x64 stated; 60x60 used", "point load as 4-element patch", "vf fixed to 0.4 after asking"])


# L04  arXiv:2105.04232 (#36): 2L x L Michell-type cantilever, line load L/10 drawn around mid-height.
def _l04(t):
    s = _cant2(120, 60, 0.25, t["c"] * 60, 6.0)
    if t.get("sup", "edge") == "pins":                # union variant: two pins at the left corners
        s["supports"] = [{"segment": [0, 0, 0, 0], "comp": "xy"}, {"segment": [0, 60, 0, 60], "comp": "xy"}]
    r = t.get("pad", 0)                               # union variant: solid pad of radius r around the load line
    if r:
        s["solid"] = [[120 - r, t["c"] * 60 - 3 - r, 120, t["c"] * 60 + 3 + r]]
    return s


register("L04", dict(arxiv="2105.04232", position=36), 2,
         slots=dict(c=[0.40, 0.45, 0.50, 0.55, 0.60]), nominal=dict(c=0.5), build=_l04,
         reasons=dict(c="line load of length L/10 drawn 'around mid-height'; exact height not stated (figure); "
                        "annotation convention: +-0.1 L"),
         recon=["60x30 homogenization mesh in source; 120x60 used"])


# L05  arXiv:1708.07364 (#38): 150x60 cantilever; direction only in figure; filter radius 1.5 vs 2.
def _l05(t):
    s = _cant2(150, 60, 0.6, 30.0, 4.0, direction=(0, -1 if t["dir"] == "down" else 1))
    s["rmin"] = t["rmin"]
    return s


register("L05", dict(arxiv="1708.07364", position=38), 2,
         slots=dict(dir=["down", "up"], rmin=[1.5, 2.0]), nominal=dict(dir="down", rmin=1.5), build=_l05,
         mandatory=("dir",),
         reasons=dict(dir="downward only in figure: mandatory (compliance is sign-invariant)",
                      rmin="Sec. 4 default 2 vs Fig. 7 caption 1.5 (conflict)"),
         recon=["point force as 4-element patch"])


# L07  arXiv:2511.14623 (#43): 2x1; clamp at x=0 (text, mid-line) vs left edge x=-1 (figure).
def _l07(t):
    s = _cant2(120, 60, 0.5, 30.0, 6.0)
    if t["clamp"] == "midline":
        s["supports"] = [{"segment": [60, 0, 60, 60], "comp": "xy"}]
    return s


register("L07", dict(arxiv="2511.14623", position=43), 2,
         slots=dict(clamp=["left_edge", "midline"], volfrac=[0.5]), nominal=dict(clamp="left_edge", volfrac=0.5), build=_l07,
         mandatory=("volfrac",),
         reasons=dict(clamp="text Gamma_D = {0} x (-0.5,0.5) (mid-line) vs prose and Fig. 4(a) left edge x=-1",
                      volfrac="volume penalty beta=0.5, no constraint value: mandatory"),
         recon=["mesh-free in source; 120x60 grid", "traction segment (-0.05,0.05) as 6-element patch",
                "vf fixed to 0.5 after asking"])


# L08  arXiv:2305.04107 (#48): rectangle drawn ~3:1, dims not stated; load at bottom-right corner.
def _l08(t):
    nely = 40
    full_x = 140
    nelx = int(round(t["ar"] * nely))
    s = dict(dim=2, nelx=full_x, nely=nely, volfrac=0.5,
             domain={"type": "xmax", "xmax": nelx},
             supports=[{"edge": "left", "comp": "xy"}],
             load_cases=[{"patches": [{"segment": [nelx, 0, nelx, nely], "center": 2.0, "width": 4.0,
                                       "dir": [0, -1]}]}])
    return s


register("L08", dict(arxiv="2305.04107", position=48), 2,
         slots=dict(ar=[2.5, 3.0, 3.5]), nominal=dict(ar=3.0), build=_l08,
         reasons=dict(ar="rectangle drawn about 3:1; dimensions not stated (figure); convention +-0.5"),
         recon=["common 140x40 grid, domain truncated at x = ar*40 (removed elements)",
                "corner point load as 4-element patch at the bottom of the right end"])


# L09  arXiv:2605.02158 (#49): square; supports on upper part of left edge and on the right edge;
#      load on lower part of left edge pointing left.
def _l09(t):
    n = 64
    return dict(dim=2, nelx=n, nely=n, volfrac=0.4, domain={"type": "rect"},
                supports=[{"edge": "left", "range": [t["sup"] * n, n], "comp": "xy"},
                          {"edge": "right", "comp": "xy"}],
                load_cases=[{"patches": [{"edge": "left", "center": t["load"] * n, "width": 4.0, "dir": [-1, 0]}]}])


register("L09", dict(arxiv="2605.02158", position=49), 2,
         slots=dict(sup=[0.5, 0.75], load=[0.1, 0.25, 0.4], volfrac=[0.4]), nominal=dict(sup=0.5, load=0.25, volfrac=0.4), build=_l09,
         mandatory=("volfrac",),
         reasons=dict(sup="green segment 'upper part of left edge'; extent not given (figure)",
                      load="load 'on lower part of left edge'; position not given (figure)",
                      volfrac="not stated for this sample (0.3-0.5): mandatory"),
         recon=["64x64 stated", "vf fixed to 0.4 after asking", "right-edge support taken as full edge"])


# L11  arXiv:2605.19110 (#59; the authors' own paper): 80x40 cantilever with 2 voids, positions unknown.
def _l11(t):
    r = t.get("r", 6)                                 # union variant: void radius 2 / 4 / 6 elements
    holes = {"horizontal": [[25, 20, r], [55, 20, r]], "vertical": [[40, 11, r], [40, 29, r]],
             "diagonal": [[25, 12, r], [55, 28, r]]}[t["voids"]]
    return dict(dim=2, nelx=80, nely=40, volfrac=0.25, domain={"type": "holes", "holes": holes},
                supports=[{"edge": "left", "comp": "xy"}],
                load_cases=[{"patches": [{"edge": "right", "center": 20.0, "width": 4.0, "dir": [0, -1]}]}])


register("L11", dict(arxiv="2605.19110", position=59, note="authors' own paper; kept by frozen order"), 2,
         slots=dict(voids=["horizontal", "vertical", "diagonal"], dir=["down"]), nominal=dict(voids="horizontal", dir="down"), build=_l11,
         mandatory=("dir",),
         reasons=dict(voids="'2 voids' table descriptor only; positions and sizes not stated",
                      dir="'mid-right load', direction not stated: mandatory"),
         recon=["void radius 6 elements assumed for all layouts"])


# --------------------------------------------------------------------------- 3-D
# L02  arXiv:1909.11320 (#5): 3x1x1 box; distributed downward load along the bottom edge of the
#      end face; loaded height (edge line vs strip) not stated.
def _l02(t):
    h = {"line": 2.0, "quarter": 0.25 * 12, "half": 0.5 * 12, "full": 12.0}[t["strip"]]
    vf = {"0.5": 0.5, "1/6": 1 / 6}[t.get("vf", "0.5")]   # bound 0.5 as a fraction, or 0.5 m^3 of the 3 m^3 box
    return dict(dim=3, nelx=36, nely=12, nelz=12, volfrac=vf, domain={"type": "rect"},
                supports=[{"face": "x0", "comp": "xyz"}],
                load_cases=[{"patches": [{"face": "x1", "center": [h / 2, 6.0], "size": [h, 12.0],
                                          "dir": [0, -1, 0]}]}])


register("L02", dict(arxiv="1909.11320", position=5), 3,
         slots=dict(strip=["line", "quarter", "half"]), nominal=dict(strip="line"), build=_l02,
         reasons=dict(strip="load drawn along the bottom edge of the end face with traction units; loaded height "
                            "(edge line vs strip) not stated (figure)"),
         recon=["36x12x12 mesh (source 3,000-192,000 variables)", "full-width strip, raised-cosine in height"])


# L06  arXiv:1612.04082 (#40): unit cube, one face fixed, line load across the opposite face at
#      about mid-height; line vs strip and exact height not stated.
def _l06(t):
    n = 24
    w = {"line": 2.0, "strip": 0.2 * n}[t["width"]]
    return dict(dim=3, nelx=n, nely=n, nelz=n, volfrac=0.6, domain={"type": "rect"},
                supports=[{"face": "x0", "comp": "xyz"}],
                load_cases=[{"patches": [{"face": "x1", "center": [t["h"] * n, n / 2], "size": [w, float(n)],
                                          "dir": [0, -1, 0]}]}])


register("L06", dict(arxiv="1612.04082", position=40), 3,
         slots=dict(h=[0.4, 0.5, 0.6], width=["line", "strip"]), nominal=dict(h=0.5, width="line"), build=_l06,
         reasons=dict(h="line drawn 'at about mid-height' (figure); convention +-0.1",
                      width="line vs strip traction not stated"),
         recon=["64^3 voxels in source; 24^3 used"])


# L12  arXiv:2410.23295 (#23): cube scaffold cell, 'points at the base fixed', compressive top load
#      through a thin shell.
def _l12(t):
    n = 24
    sup = ([{"face": "y0", "rect": [0, 4, 0, 4], "comp": "xyz"}, {"face": "y0", "rect": [20, 24, 0, 4], "comp": "xyz"},
            {"face": "y0", "rect": [0, 4, 20, 24], "comp": "xyz"}, {"face": "y0", "rect": [20, 24, 20, 24], "comp": "xyz"}]
           if t["sup"] == "corners" else [{"face": "y0", "comp": "xyz"}])
    size = [float(n), float(n)] if t["load"] == "full" else [n / 2, n / 2]
    s = dict(dim=3, nelx=n, nely=n, nelz=n, volfrac=0.3, domain={"type": "rect"}, supports=sup,
             load_cases=[{"patches": [{"face": "y1", "center": [n / 2, n / 2], "size": size, "dir": [0, -1, 0]}]}])
    if t.get("shell", 0):                             # union variant: one passive solid voxel layer at the top
        s["solid"] = [[0, n - t["shell"], 0, n, n, n]]
    return s


register("L12", dict(arxiv="2410.23295", position=23), 3,
         slots=dict(sup=["corners", "full"], load=["full", "central"]), nominal=dict(sup="corners", load="full"),
         build=_l12,
         reasons=dict(sup="'points at the base fixed' (Fig. 6 'Ground'); which points not stated",
                      load="compressive load through a thin top shell; distribution not stated"),
         recon=["40^3 voxels in source; 24^3 used", "vf 0.3 = first of five stated targets"])


# --------------------------------------------------------------------------- 2-D, screen v2
# L13  arXiv:2310.02069 (#74): 100x100 cantilever; Fig. 1(a) arrow near the bottom corner of the
#      right edge vs design converging to mid-height (Fig. 3(b)).
def _l13(t):
    c = {"corner": 2.0, "lower": 25.0, "mid": 50.0}[t["load"]]
    s = _cant2(100, 100, 0.2, c, 4.0)
    s["rmin"] = 2.4
    return s


register("L13", dict(arxiv="2310.02069", position=74), 2,
         slots=dict(load=["corner", "lower", "mid"], volfrac=[0.2]), nominal=dict(load="mid", volfrac=0.2),
         build=_l13, mandatory=("volfrac",),
         reasons=dict(load="Fig. 1(a) arrow on the lower part of the right edge near the corner vs Fig. 3(b) design "
                           "converging to mid-height (Fig. 1(a); Fig. 3(b))",
                      volfrac="0.20 only from the image file name; caption gives no value: mandatory"),
         recon=["point force as 4-element patch", "vf fixed to 0.2 after asking"])


# L14  arXiv:2603.09780 (#78): 20x10 cantilever (80x40, h=0.25); unit-length load segment drawn
#      centred near mid-height of the right edge.
def _l14(t):
    return _cant2(80, 40, 0.3, t["c"] * 40, 4.0)


register("L14", dict(arxiv="2603.09780", position=78), 2,
         slots=dict(c=[0.4, 0.5, 0.6]), nominal=dict(c=0.5), build=_l14,
         reasons=dict(c="unit-length segment drawn centred near mid-height; position not stated (Fig. 1); "
                        "annotation convention: +-0.1 height"),
         recon=["adaptive mesh in source; fixed 80x40 grid (level 2)", "PDE filter radius 0.375 = 1.5 elements"])


# L15  arXiv:2603.25099 (#79): 120x60 cantilever, 'tip load'; corner vs mid-height not stated;
#      top and bottom corners are equivalent by mirror symmetry and the sign invariance of compliance.
def _l15(t):
    return _cant2(120, 60, 0.4, {"corner": 2.0, "mid": 30.0}[t["pos"]], 4.0)


register("L15", dict(arxiv="2603.25099", position=79, note="authors' own paper; kept by frozen order"), 2,
         slots=dict(pos=["corner", "mid"], dir=["down"]), nominal=dict(pos="mid", dir="down"), build=_l15,
         mandatory=("dir",),
         reasons=dict(pos="'tip load' only; corner vs mid-height not stated (Sec. 3.5; Fig. 6 symmetric designs)",
                      dir="load direction not stated: mandatory"),
         recon=["square elements assumed (only 120x60 stated)", "point force as 4-element patch"])


# L16  arXiv:2504.14892 (#101): square plate; two short fixed segments at mid-span of the top and
#      bottom edges; tractions on short segments at the top-right (down) and bottom-left (up) corners.
def _l16(t):
    n = 80
    a, b = t["sup"] * n, t["load"] * n
    return dict(dim=2, nelx=n, nely=n, volfrac=0.45, domain={"type": "rect"},
                supports=[{"edge": "top", "range": [n / 2 - a / 2, n / 2 + a / 2], "comp": "xy"},
                          {"edge": "bottom", "range": [n / 2 - a / 2, n / 2 + a / 2], "comp": "xy"}],
                load_cases=[{"patches": [{"edge": "top", "center": n - b / 2, "width": b, "dir": [0, -1]},
                                         {"edge": "bottom", "center": b / 2, "width": b, "dir": [0, 1]}]}])


register("L16", dict(arxiv="2504.14892", position=101), 2,
         slots=dict(sup=[0.05, 0.1, 0.2], load=[0.05, 0.1, 0.2]), nominal=dict(sup=0.1, load=0.1), build=_l16,
         reasons=dict(sup="support segment length and position only drawn (Fig. 6(a)); convention 0.05-0.2 L",
                      load="traction segment length only drawn, ending at the corners (Fig. 6(a)); convention 0.05-0.2 L"),
         recon=["level-set evolution in source; density SIMP on 80x80", "rmin 1.5 (no filter in source)"])


# L17  arXiv:2607.22833 (#128): 200x100 cantilever; traction 'to the right edge' (text) vs a short
#      segment at the bottom of the right edge (Fig. 3).
def _l17(t):
    L = {"short": 10.0, "quarter": 25.0, "full": 100.0}[t["len"]]
    return _cant2(200, 100, 0.5, 50.0 if t.get("pos", "lower") == "mid" else L / 2, L)


register("L17", dict(arxiv="2607.22833", position=128), 2,
         slots=dict(len=["short", "quarter", "full"]), nominal=dict(len="full"), build=_l17,
         reasons=dict(len="text 'to the right edge' vs Fig. 3 short segment at the bottom; length not stated "
                          "(Sec. 4.1; Fig. 3)"),
         recon=["RAMP+MMA in source; SIMP+OC", "traction as raised-cosine patch of the stated length"])


# L18  arXiv:2603.22889 (#129): 60x30 cantilever; 'distributed load' drawn as one arrow at the
#      lower-right corner; loaded extent not stated.
def _l18(t):
    p = {"corner": {"edge": "right", "center": 1.0, "width": 2.0},
         "right6": {"edge": "right", "center": 3.0, "width": 6.0},
         "bottom6": {"edge": "bottom", "center": 57.0, "width": 6.0}}[t["patch"]]
    s = dict(dim=2, nelx=60, nely=30, volfrac=0.5, domain={"type": "rect"},
             supports=[{"edge": "left", "comp": "xy"}],
             load_cases=[{"patches": [dict(p, dir=[0, -1])]}])
    s["rmin"] = 2.5
    return s


register("L18", dict(arxiv="2603.22889", position=129), 2,
         slots=dict(patch=["corner", "right6", "bottom6"]), nominal=dict(patch="corner"), build=_l18,
         reasons=dict(patch="'distributed load' at the lower-right corner drawn as a single arrow; extent and edge "
                            "not stated (Fig. 1 caption; Fig. 1(a)); convention: up to 6 elements on either edge"),
         recon=["MMA in source; OC"])


# L19  arXiv:2607.20784 (#133): MBB, right symmetric half optimized; 180x30 elements stated for
#      'the domain': full beam (half model 90x30) or half model (full beam 12:1).
def _mbb_half(nelx, nely, xmax, vf, sup_len=0.0, corner_comp="y"):
    return dict(dim=2, nelx=nelx, nely=nely, volfrac=vf, domain={"type": "xmax", "xmax": xmax},
                supports=[{"edge": "left", "comp": "x"},
                          {"segment": [xmax - sup_len, 0, xmax, 0], "comp": corner_comp}],
                load_cases=[{"patches": [{"edge": "top", "center": 1.0, "width": 2.0, "dir": [0, -1]}]}])


def _l19(t):
    s = _mbb_half(180, 30, {"full": 90, "half": 180}[t["extent"]], 0.3)
    s["rmin"] = 3.6
    return s


register("L19", dict(arxiv="2607.20784", position=133), 2,
         slots=dict(extent=["full", "half"]), nominal=dict(extent="full"), build=_l19,
         reasons=dict(extent="180x30 elements stated for 'the domain' while the right half is optimized; "
                             "full vs half not stated (Sec. 4.1.1)"),
         recon=["common 180x30 half-model grid truncated at xmax", "mid-span point load as 2-element patch at the "
                "symmetry edge"])


# L20  arXiv:2607.07682 (#73): MBB 192x64 with half-symmetry; half or full beam not stated; corner
#      supports drawn as small blocks of unstated size.
def _l20(t):
    s = _mbb_half(192, 64, {"full": 96, "half": 192}[t["extent"]], 0.4, {"node": 0.0, "block": 4.0}[t["sup"]],
                  t.get("supcomp", "y"))
    s["rmin"] = 2.0
    return s


register("L20", dict(arxiv="2607.07682", position=73), 2,
         slots=dict(extent=["full", "half"], sup=["node", "block"]), nominal=dict(extent="half", sup="node"),
         build=_l20,
         reasons=dict(extent="192x64 with half-symmetry; half or full beam not stated (Sec. V-A; Fig. 2B; Fig. S11)",
                      sup="'both lower corners supported', drawn as small blocks; size not stated (Fig. 2B)"),
         recon=["L-BFGS in source; OC", "block support = 4-element segment ending at the corner"])


# L21  arXiv:2608.22606 (#77): 60x20 cantilever; load node 'at the upper end of the right edge';
#      convolution filter radius not stated.
def _l21(t):
    s = _cant2(60, 20, 0.469, {"corner": 19.0, "upper": 16.0, "u75": 15.0}[t["load"]], 2.0)
    s["rmin"] = 1.5
    return s


register("L21", dict(arxiv="2608.22606", position=77), 2,
         slots=dict(load=["corner", "upper"], volfrac=[0.469]),
         nominal=dict(load="corner", volfrac=0.469), build=_l21, mandatory=("volfrac",),
         reasons=dict(load="drawn at the upper end of the right edge; node not stated (Fig. 5(c))",
                      volfrac="only the initialization label V = 0.469: mandatory"),
         recon=["sensitivity filter in source, radius not stated: density filter rmin 1.5 (solver setting)",
                "unit nodal load as 2-element patch"])


# L22  arXiv:2009.06245 (#98): 36x36 cantilever; 2x2-element load area at position index 1-18 along
#      the right edge (top to bottom); index of the Fig. 7 design not stated.
def _l22(t):
    s = _cant2(36, 36, 0.3, 36.0 - (2 * t["pos"] - 1), 2.0)
    s["rmin"] = 2.0
    return s


register("L22", dict(arxiv="2009.06245", position=98), 2,
         slots=dict(pos=list(range(1, 19))), nominal=dict(pos=9), build=_l22,
         reasons=dict(pos="load position index 1-18 not stated for Fig. 7, only 'same loading condition' "
                          "(Fig. 7 caption; Sec. 4.1); nominal 9 from the resemblance to Table 1"),
         recon=["sensitivity filter r=4 px in source; density filter r=2 (r=4 on 36x36 blurs the 2-element load)",
                "2x2 area load as a 2-element edge patch"])


# L23  arXiv:2210.11477 (#115): unit square under two inward edge loads; passive solid regions of
#      width 0.025 at the loads, height only drawn.
def _l23(t):
    n = 100
    h = {"load": 4.0, "double": 8.0, "wide": 10.0}[t["solid"]]
    return dict(dim=2, nelx=n, nely=n, volfrac=0.15, domain={"type": "rect"},
                supports=[{"segment": [0, 50, 0, 50], "comp": "y"}, {"segment": [n, 50, n, 50], "comp": "y"},
                          {"segment": [50, 50, 50, 50], "comp": "x"}],
                load_cases=[{"patches": [{"edge": "left", "center": 50.0, "width": 4.0, "dir": [1, 0]},
                                         {"edge": "right", "center": 50.0, "width": 4.0, "dir": [-1, 0]}]}],
                solid=[[0, 50 - h / 2, 2.5, 50 + h / 2], [n - 2.5, 50 - h / 2, n, 50 + h / 2]])


register("L23", dict(arxiv="2210.11477", position=115), 2,
         slots=dict(solid=["load", "double"]), nominal=dict(solid="load"), build=_l23,
         reasons=dict(solid="passive region width 0.025 stated, height only drawn (about the 0.04 load width) "
                            "(Sec. 3.1; Fig. 5); convention: 1x or 2x the load width"),
         recon=["200x200 in source; 100x100", "robust eroded/dilated formulation replaced by nominal SIMP"])


# L25  arXiv:2002.01927 (#47): square quarter-type domain (4x4 elements in source): roller on the
#      'bottom left edge', symmetry on the right boundary, load on the 'top right edge'.
def _l25(t):
    n = 40
    a = {"elem": 10.0, "node": 0.0}[t["sup"]]
    b = {"elem": 10.0, "corner": 2.0}[t["load"]]
    return dict(dim=2, nelx=n, nely=n, volfrac=0.5, domain={"type": "rect"},
                supports=[{"edge": "bottom", "range": [0, a], "comp": "y"}, {"edge": "right", "comp": "x"}],
                load_cases=[{"patches": [{"edge": "top", "center": n - b / 2, "width": b, "dir": [0, -1]}]}])


register("L25", dict(arxiv="2002.01927", position=47), 2,
         slots=dict(sup=["elem", "node"], load=["elem", "corner"]), nominal=dict(sup="elem", load="elem"),
         build=_l25,
         reasons=dict(sup="'bottom left edge' read as one source element edge only from Fig. 2a",
                      load="'top right edge' read as one source element edge only from Fig. 2a"),
         recon=["4x4 COMSOL elements in source; 40x40 grid (one source edge = 10 elements)", "rmin 1.5"])


# L27  arXiv:2404.12244 (#63): mid-load problem, 100x100 FE grid (square) vs Fig. 8 target image
#      about 1.75:1; pin and roller at the bottom corners, load at bottom mid-span.
def _l27(t):
    xmax = {"square": 100, "wide": 175}[t["ar"]]
    s = dict(dim=2, nelx=175, nely=100, volfrac=0.25, domain={"type": "xmax", "xmax": xmax},
             supports=[{"segment": [0, 0, 0, 0], "comp": "xy"}, {"segment": [xmax, 0, xmax, 0], "comp": "y"}],
             load_cases=[{"patches": [{"edge": "bottom", "center": xmax / 2, "width": 4.0, "dir": [0, -1]}]}])
    s["rmin"] = 2.4
    return s


register("L27", dict(arxiv="2404.12244", position=63), 2,
         slots=dict(ar=["square", "wide"]), nominal=dict(ar="square"), build=_l27,
         reasons=dict(ar="Fig. 6(a) and 100x100 FEs give a square; Fig. 8 target image about 1.75:1 "
                         "(Sec. 7.1.1; Fig. 6(a); Fig. 8)"),
         recon=["common 175x100 grid truncated at xmax", "vf 0.25 as in Fig. 8", "point load as 4-element patch"])


# L28  arXiv:2609.25976 (#92): cantilever on 120x60 hexagonal elements, drawn about 2.2:1; corner
#      load at the lower right; volume fraction a symbol only.
def _l28(t):
    xmax = {"2.0": 120, "2.2": 132, "2.31": 139}[t["ar"]]
    s = dict(dim=2, nelx=139, nely=60, volfrac=0.5, domain={"type": "xmax", "xmax": xmax},
             supports=[{"edge": "left", "comp": "xy"}],
             load_cases=[{"patches": [{"segment": [xmax, 0, xmax, 60], "center": 2.0, "width": 4.0,
                                       "dir": [0, -1]}]}])
    s["rmin"] = 2.0
    return s


register("L28", dict(arxiv="2609.25976", position=92), 2,
         slots=dict(ar=["2.0", "2.2", "2.31"], volfrac=[0.5]), nominal=dict(ar="2.2", volfrac=0.5), build=_l28,
         mandatory=("volfrac",),
         reasons=dict(ar="only 120x60 hexagonal elements stated, drawn about 2.2:1; regular hexagons give 2.31, "
                         "square cells 2.0 (Sec. 4; Fig. 1)",
                      volfrac="V_fm appears only as a symbol: mandatory"),
         recon=["hexagonal mesh replaced by square grid 139x60 truncated at xmax",
                "r_fill = 4 without units; rmin 2.0 elements", "vf fixed to 0.5 after asking"])


# L29  arXiv:2308.06734 (#106): 150x52 cantilever plate, load 18 cm below the top edge; a vertical
#      line about 1 cm inside the right edge is drawn without explanation (non-design strip?).
def _l29(t):
    s = _cant2(150, 52, 0.7, 34.0, 4.0)
    if t["strip"] == "solid":
        s["solid"] = [[149, 0, 150, 52]]
    s["rmin"] = 1.5
    return s


register("L29", dict(arxiv="2308.06734", position=106), 2,
         slots=dict(strip=["none", "solid"]), nominal=dict(strip="none"), build=_l29,
         reasons=dict(strip="vertical line about 1 cm inside the right edge drawn, meaning not stated (Fig. 2(a))"),
         recon=["filter R = 1.2 without units; rmin 1.5 elements", "point force as 4-element patch"])


# L30  arXiv:2508.05624 (#114): 64x64 left-clamped square, bottom-right corner load; volume fraction
#      of the instance not stated (mandatory only).
def _l30(t):
    s = _cant2(64, 64, 0.4, 2.0, 4.0)
    s["rmin"] = 2.0
    return s


register("L30", dict(arxiv="2508.05624", position=114), 2,
         slots=dict(volfrac=[0.4]), nominal=dict(volfrac=0.4), build=_l30, mandatory=("volfrac",),
         reasons=dict(volfrac="symbol f only; dataset range 30-50%: mandatory"),
         recon=["dataset mesh 64x64 and filter 2.0 assumed for this instance", "vf fixed to 0.4 after asking"])


# L31  arXiv:1807.10787 (#108): 120x40 cantilever, mid-tip load at a sampled angle; volume threshold
#      and filter radius not stated.
def _l31(t):
    s = _cant2(120, 40, 0.4, 20.0, 4.0)
    if t.get("sup", "edge") == "pins":                # union variant: two pins at the left corners
        s["supports"] = [{"segment": [0, 0, 0, 0], "comp": "xy"}, {"segment": [0, 40, 0, 40], "comp": "xy"}]
    s["rmin"] = 1.5
    return s


register("L31", dict(arxiv="1807.10787", position=108), 2,
         slots=dict(dir=["down"], volfrac=[0.4]), nominal=dict(dir="down", volfrac=0.4),
         build=_l31, mandatory=("dir", "volfrac"),
         reasons=dict(dir="angle of the shown sample not stated (sampled in [0, pi]): mandatory",
                      volfrac="threshold alpha not stated: mandatory"),
         recon=["local p-norm density constraint omitted", "filter radius r_e not stated: rmin 1.5 (solver setting)",
                "angle fixed to vertical after asking", "vf fixed to 0.4 after asking"])


# --------------------------------------------------------------------------- 3-D, screen v2
# L24  arXiv:2402.12076 (#135): 3-D three-point bending, 120x48x48 mm; bottom end strips fixed
#      (width not stated); load at top mid-span along a line across the depth (line vs strip).
def _l24(t):
    nx, ny, nz = 40, 16, 16
    w = t["sup"]
    a = {"line": 2.0, "strip": 6.0}[t["load"]]
    return dict(dim=3, nelx=nx, nely=ny, nelz=nz, volfrac=0.4, domain={"type": "rect"},
                supports=[{"face": "y0", "rect": [0, w, 0, nz], "comp": "xyz"},
                          {"face": "y0", "rect": [nx - w, nx, 0, nz], "comp": "xyz"}],
                load_cases=[{"patches": [{"face": "y1", "center": [nx / 2, nz / 2], "size": [a, float(nz)],
                                          "dir": [0, -1, 0]}]}])


register("L24", dict(arxiv="2402.12076", position=135), 3,
         slots=dict(sup=[1, 2, 4], load=["line", "strip"]), nominal=dict(sup=2, load="line"), build=_l24,
         reasons=dict(sup="'bottom sides are fixed', strips drawn at both ends, width not stated (Fig. 9 caption; "
                          "Fig. 9(a)); convention 1-4 elements of 40",
                      load="'uniformly applied at the center of the beam top', drawn as a line across the depth; "
                           "line vs strip not stated (Fig. 9 caption; Fig. 9(a))"),
         recon=["IGA porous-unit model in source; solid SIMP on 40x16x16 (3 mm voxels)",
                "FE domain taken as the manufactured size"])


# L33  arXiv:2604.03276 (#146; borderline): FEM-TO nanopillar baseline, 40x40x100 box, four clamped
#      base-corner patches (20% side); top-centre load, single node vs patch not stated.
def _l33(t):
    nx, ny, nz = 16, 40, 16
    a = {"node": 2.0, "patch": 6.0}[t["load"]]
    c = 0.2 * nx if t.get("sup", "patches") == "patches" else 0.0   # union variant: four corner nodes
    sup = [{"face": "y0", "rect": [u0, u1, v0, v1], "comp": "xyz"}
           for u0, u1 in ((0, c), (nx - c, nx)) for v0, v1 in ((0, c), (nz - c, nz))]
    return dict(dim=3, nelx=nx, nely=ny, nelz=nz, volfrac=0.2025, domain={"type": "rect"}, supports=sup,
                load_cases=[{"patches": [{"face": "y1", "center": [nx / 2, nz / 2], "size": [a, a],
                                          "dir": [0, -1, 0]}]}])


register("L33", dict(arxiv="2604.03276", position=146, note="borderline eligible: supplementary FEM baseline"), 3,
         slots=dict(load=["node", "patch"]), nominal=dict(load="node"), build=_l33,
         reasons=dict(load="'center of the top surface'; single node vs patch not stated (Suppl. Note A.14)"),
         recon=["40x40x100 in source; 16x40x16", "force reading only: the prescribed-displacement reading is not "
                "representable in the force-loaded compliance solver", "rmin 1.5 (2.549 at source resolution)"])


# --------------------------------------------------------------------------- screen v3 (151-247)
# L34  arXiv:1904.06556 (#156): 3-D cantilever 16x2x2 cubes, left face fixed, z-load 'in the middle
#      of the right-hand face'; node vs patch not stated; material volume V a symbol only.
def _l34(t):
    a = {"node": 2.0, "patch": 6.0}[t["load"]]
    return dict(dim=3, nelx=96, nely=12, nelz=12, volfrac=0.2, domain={"type": "rect"},
                supports=[{"face": "x0", "comp": "xyz"}],
                load_cases=[{"patches": [{"face": "x1", "center": [6.0, 6.0], "size": [a, a], "dir": [0, 0, -1]}]}])


register("L34", dict(arxiv="1904.06556", position=156), 3,
         slots=dict(load=["node", "patch"], volfrac=[0.2]), nominal=dict(load="node", volfrac=0.2), build=_l34,
         mandatory=("volfrac",),
         reasons=dict(load="'applied in the middle of the right-hand face'; node vs patch not stated (Sec. 7; Fig. 2(a))",
                      volfrac="material volume V a symbol only: mandatory"),
         recon=["variable-thickness-sheet (linear) model in source; SIMP p=3", "density upper bound rho_bar not "
                "representable (bound 1)", "262k elements in source; 96x12x12", "vf fixed to 0.2 after asking"])


# L35  arXiv:2210.01315 (#172): 3-D cantilever 40x20x8; two arrows at the bottom corners of the end face:
#      bottom-edge line load (top3d default) vs two corner point loads; V* a symbol only.
def _l35(t):
    if t["load"] == "line":
        p = [{"face": "x1", "center": [1.0, 4.0], "size": [2.0, 8.0], "dir": [0, -1, 0]}]
    else:
        p = [{"face": "x1", "center": [1.0, z], "size": [2.0, 2.0], "dir": [0, -1, 0], "resultant": 0.5}
             for z in (1.0, 7.0)]
    return dict(dim=3, nelx=40, nely=20, nelz=8, volfrac=0.3, domain={"type": "rect"},
                supports=[{"face": "x0", "comp": "xyz"}], load_cases=[{"patches": p}])


register("L35", dict(arxiv="2210.01315", position=172), 3,
         slots=dict(load=["line", "corners"], volfrac=[0.3]), nominal=dict(load="line", volfrac=0.3), build=_l35,
         mandatory=("volfrac",),
         reasons=dict(load="two arrows at the bottom corners of the end face; line load vs two corner point loads "
                           "(Fig. 3(a))",
                      volfrac="V* a symbol only: mandatory"),
         recon=["neural density field in source; SIMP", "line load as raised-cosine strip across the depth",
                "penalty p not stated: p=3 (solver setting)", "vf fixed to 0.3 after asking"])


# L36  arXiv:2208.09591 (#164): 64x64; x-rollers on the left edge (whole edge in the input panel, lower
#      ~60% in the output panel); pins at the right corners; upward load on the bottom edge near 0.15 W.
def _l36(t):
    n = 64
    roll = ([{"segment": [0, y, 0, y], "comp": "x"} for y in (0, 16, 32, 48, 64)] if t["roller"] == "nodes5"
            else [{"edge": "left", "range": [0, {"full": 64.0, "lower60": 38.4}[t["roller"]]], "comp": "x"}])
    return dict(dim=2, nelx=n, nely=n, volfrac=0.4, domain={"type": "rect"},
                supports=roll + [{"segment": [n, 0, n, 0], "comp": "xy"}, {"segment": [n, n, n, n], "comp": "xy"}],
                load_cases=[{"patches": [{"edge": "bottom", "center": t["load"] * n, "width": 2.0, "dir": [0, 1]}]}])


register("L36", dict(arxiv="2208.09591", position=164), 2,
         slots=dict(roller=["full", "lower60"], load=[0.12, 0.15, 0.18]), nominal=dict(roller="full", load=0.15),
         build=_l36,
         reasons=dict(roller="rollers along the whole left edge in the input panel, lower ~60% in the output panel "
                             "(Fig. 1)",
                      load="arrow at about 0.15 of the width; node not stated (Fig. 1); convention +-0.03 W"),
         recon=["ToPy filter/penalty not stated: rmin 1.5, p=3 (solver settings)", "direction taken as drawn (up)"])


# L37  arXiv:2510.08830 (#171): double-clamped 150x40 beam; thin solid strips at the clamped edges and a
#      solid patch under the top-centre load, widths only drawn; V0 of the shown design not stated.
def _l37(t):
    w, a = t["strip"], t["patch"]
    pad = t.get("pad", 2)                             # union variant: loading-pad depth 0 / 1 / 2 elements
    solid = [[0, 0, w, 40], [150 - w, 0, 150, 40]] + ([[75 - a / 2, 40 - pad, 75 + a / 2, 40]] if pad else [])
    return dict(dim=2, nelx=150, nely=40, volfrac=0.35, domain={"type": "rect"},
                supports=[{"edge": "left", "comp": "xy"}, {"edge": "right", "comp": "xy"}],
                load_cases=[{"patches": [{"edge": "top", "center": 75.0, "width": a, "dir": [0, -1]}]}],
                solid=solid)


register("L37", dict(arxiv="2510.08830", position=171), 2,
         slots=dict(strip=[1.0, 3.0], patch=[2.0, 6.0], volfrac=[0.35]), nominal=dict(strip=1.0, patch=2.0, volfrac=0.35),
         build=_l37, mandatory=("volfrac",),
         reasons=dict(strip="solid strips at the clamped edges drawn only (Fig. 8(a) legend); convention 1-3 elements",
                      patch="load patch width at top centre drawn only (Fig. 8(a)); convention 2-6 elements",
                      volfrac="V0 swept over 160 values; value of the shown design not stated: mandatory"),
         recon=["homogenization multiscale model in source; single-scale SIMP", "mesh not stated: 150x40 (1 mm)",
                "rmin 1.5 (L_min bar-width bound not modelled)", "vf fixed to 0.35 after asking"])


# L38  arXiv:2001.00635 (#175): 'cantilever', 16 x 32 elements in the text but drawn 32 wide x 16 high;
#      load position not stated (designs suggest the bottom-right corner).
def _l38(t):
    xm, ym = {"wide": (32, 16), "tall": (16, 32)}[t["orient"]]
    c = {"corner": 1.0, "mid": ym / 2}[t["load"]]
    sup = ([{"segment": [0, 0, 0, 0], "comp": "xy"}, {"segment": [0, ym, 0, ym], "comp": "xy"}]
           if t.get("sup", "edge") == "pins" else [{"edge": "left", "range": [0, ym], "comp": "xy"}])
    d = [0, -1] if t.get("dir", "down") == "down" else [float(np.sqrt(0.5)), -float(np.sqrt(0.5))]
    return dict(dim=2, nelx=32, nely=32, volfrac=0.5, domain={"type": "xmax", "xmax": xm, "ymax": ym},
                supports=sup,
                load_cases=[{"patches": [{"segment": [xm, 0, xm, ym], "center": c, "width": 2.0, "dir": d}]}])


register("L38", dict(arxiv="2001.00635", position=175), 2,
         slots=dict(orient=["wide", "tall"], load=["corner", "mid"]), nominal=dict(orient="wide", load="corner"),
         build=_l38,
         reasons=dict(orient="text '16 x 32 square elements', figures 32 wide x 16 high (Sec. 4; Figs. 10-11)",
                      load="only 'cantilever'; designs suggest a bottom-right corner load, mid-height admissible "
                           "(Sec. 4; Fig. 11)"),
         recon=["common 32x32 grid truncated at (xmax, ymax)", "clamped left edge (implied by 'cantilever')",
                "no filter in source (threshold post-filter): rmin 1.5", "Poisson's ratio printed as 1.0: 0.3 used"])


# L39  arXiv:2310.01968 (#181): half-MBB on 60x20 hexagons; Lx, Ly not stated: square-cell reading 3:1,
#      regular-hexagon reading 60 sqrt(3) / 30 = 3.46:1.
def _l39(t):
    s = _mbb_half(69, 20, {"3.0": 60, "3.46": 69}[t["ar"]], 0.5)
    s["rmin"] = 1.5
    return s


register("L39", dict(arxiv="2310.01968", position=181), 2,
         slots=dict(ar=["3.0", "3.46"]), nominal=dict(ar="3.46"), build=_l39,
         reasons=dict(ar="only 60x20 hexagons stated; maximum length 60 sqrt(3) implied, height not stated "
                         "(Sec. 3.4; Fig. 1(a))"),
         recon=["hexagonal mesh replaced by a square grid 69x20 truncated at xmax",
                "ft = 0 (no filter) in source; square grids need a filter: rmin 1.5"])


# L40  arXiv:2609.21758 (#183): half-MBB 144x48, vf 0.3; filter radius converges to its lower bound,
#      stated as 2.0 in the text and 1.5 in Table 1.
def _l40(t):
    # union variant: 144x48 cells read as squares (3:1) or as 2:1 rectangles (6:1), common 288x48 grid
    s = _mbb_half(288, 48, {"3": 144, "6": 288}[t["ar"]], 0.3) if "ar" in t else _mbb_half(144, 48, 144, 0.3)
    s["rmin"] = t["rmin"]
    return s


register("L40", dict(arxiv="2609.21758", position=183), 2,
         slots=dict(rmin=[1.5, 2.0]), nominal=dict(rmin=2.0), build=_l40,
         reasons=dict(rmin="lower bound of the tuned filter radius: 2.0 in Sec. 5.1, 1.5 in Table 1 (conflict)"),
         recon=["CNN parameterization and tuned penalty/projection replaced by the standard schedule"])


# L41  arXiv:2607.07233 (#187): square shelf bracket, left edge supported, downward load on the top edge
#      at about 0.45 L; grid not stated. The x-only roller reading of the left-edge markers is a
#      mechanism (no vertical restraint) and is not admissible.
def _l41(t):
    n = 64
    return dict(dim=2, nelx=n, nely=n, volfrac=0.4, domain={"type": "rect"},
                supports=[{"edge": "left", "comp": "xy"}],
                load_cases=[{"patches": [{"edge": "top", "center": t["load"] * n, "width": 2.0, "dir": [0, -1]}]}])


register("L41", dict(arxiv="2607.07233", position=187), 2,
         slots=dict(load=[0.4, 0.45, 0.5]), nominal=dict(load=0.45), build=_l41,
         reasons=dict(load="arrow at about 0.45 L on the top edge; node not stated (Fig. 6(a)); convention +-0.05 L"),
         recon=["grid not stated: 64x64", "filter/penalty not stated: rmin 1.5, p=3",
                "x-only roller reading excluded (mechanism)"])


# L42  arXiv:2503.16211 (#202): cantilever drawn on a 20x8 grid; 'Fixed Nodes' only at the two left
#      corners (pins vs clamped edge); load at about mid-height of the right edge.
def _l42(t):
    sup = ([{"segment": [0, 0, 0, 0], "comp": "xy"}, {"segment": [0, 24, 0, 24], "comp": "xy"}]
           if t["sup"] == "pins" else [{"edge": "left", "comp": "xy"}])
    if "ar" in t:                                     # union variant: 2.5:1 (drawn 20x8 grid) or 3:1, common 72x24 grid
        xm = {"2.5": 60, "3.0": 72}[t["ar"]]
        return dict(dim=2, nelx=72, nely=24, volfrac=0.5, domain={"type": "xmax", "xmax": xm}, supports=sup,
                    load_cases=[{"patches": [{"segment": [xm, 0, xm, 24], "center": 12.0, "width": 2.0,
                                              "dir": [0, -1]}]}])
    return dict(dim=2, nelx=60, nely=24, volfrac=0.5, domain={"type": "rect"}, supports=sup,
                load_cases=[{"patches": [{"edge": "right", "center": 12.0, "width": 2.0, "dir": [0, -1]}]}])


register("L42", dict(arxiv="2503.16211", position=202), 2,
         slots=dict(sup=["pins", "clamp"]), nominal=dict(sup="clamp"), build=_l42,
         reasons=dict(sup="'Fixed Nodes' drawn only at the two left corners; two pins vs clamped edge (Fig. 1(a))"),
         recon=["20x8 drawn grid refined 3x to 60x24", "filter radius not stated: rmin 1.5"])


# L43  arXiv:2509.05800 (#204): 64x64 dataset instance; supports read from green marks; load on the
#      left edge at about 0.8 of the height from the top, drawn down-left (one of 6 sampled angles).
def _l43(t):
    n = 64
    a = np.deg2rad(t["angle"])
    return dict(dim=2, nelx=n, nely=n, volfrac=0.3, domain={"type": "rect"},
                supports=[{"edge": "left", "range": [32, 64], "comp": "xy"},
                          {"edge": "bottom", "range": [0, 32], "comp": "xy"}, {"segment": [n, 0, n, 0], "comp": "xy"}],
                load_cases=[{"patches": [{"edge": "left", "center": (1 - t["pos"]) * n, "width": 2.0,
                                          "dir": [float(np.cos(a)), float(np.sin(a))]}]}])


register("L43", dict(arxiv="2509.05800", position=204), 2,
         slots=dict(pos=[0.75, 0.8, 0.85], angle=[210, 240]), nominal=dict(pos=0.8, angle=240), build=_l43,
         reasons=dict(pos="drawn at about 0.8 of the height from the top; element not stated (Fig. 5 row 1); "
                          "convention +-0.05",
                      angle="drawn down-left; one of 6 sampled angles, value not stated (Fig. 5; Sec. 4.1): "
                            "210 or 240 deg"),
         recon=["support node sets as read from the green marks", "filter not stated: rmin 1.5"])


# L44  arXiv:2603.27000 (#219; the authors' own earlier paper): 60x30 cantilever 'tip load'; volume
#      fraction of cantilever_basic not stated (default 0.5 assumed).
def _l44(t):
    return _cant2(60, 30, 0.5, {"mid": 15.0, "corner": 2.0}[t["pos"]], 4.0)


register("L44", dict(arxiv="2603.27000", position=219, note="authors' own paper; kept by frozen order"), 2,
         slots=dict(pos=["mid", "corner"], volfrac=[0.5]), nominal=dict(pos="mid", volfrac=0.5), build=_l44,
         mandatory=("volfrac",),
         reasons=dict(pos="'tip load' only; mid-height inferred from the symmetric design, corner admissible "
                          "(Alg. 2; Sec. 1.3; Fig. 5)",
                      volfrac="configurator default 0.5 assumed; suite also lists 0.3/0.4/0.6: mandatory"),
         recon=["r_min schedule not stated: rmin 1.5", "vf fixed to 0.5 after asking"])


# L45  arXiv:2609.07149 (#241): 2x1 cantilever loaded through a solid b x b block; text 'bottom right',
#      set-up figure draws the block at mid-height; b not stated; volume swept.
def _l45(t):
    b = t["b"] * 50
    y0 = 0.0 if t["pos"] == "corner" else 25 - b / 2
    d = (0, -1) if t.get("dir", "down") == "down" else (1, 0)   # union variant: axial reading
    s = _cant2(100, 50, 0.4, y0 + b / 2, b, direction=d)
    s["solid"] = [[100 - b, y0, 100, y0 + b]]
    s["rmin"] = t.get("rmin", 12.5)                   # union variant: R = 25 (Table 1) or beta = R/(3h) = 10 readings
    s["final_move"] = 0.01          # period-2 OC oscillation (0.1%) with move 0.02 under this large filter
    return s


register("L45", dict(arxiv="2609.07149", position=241), 2,
         slots=dict(pos=["corner", "mid"], b=[0.05, 0.1], volfrac=[0.4]), nominal=dict(pos="corner", b=0.1, volfrac=0.4),
         build=_l45, mandatory=("volfrac",),
         reasons=dict(pos="text 'loaded at the bottom right' vs Fig. 6 block at mid-height (Sec. 4.1; Fig. 6)",
                      b="solid b x b load block drawn, b not stated (Fig. 6; Sec. 3.1); convention 0.05-0.1 H",
                      volfrac="swept along the nondominated curves; no single value: mandatory"),
         recon=["200x100 in source; 100x50 with the filter radius halved (R = 25 -> 12.5 elements)",
                "robust eroded/dilated projection replaced by nominal SIMP", "vf fixed to 0.4 after asking",
                "final move limit 0.01 (0.02 gives a 0.1% period-2 oscillation that fails the convergence window)"])


# In-scope ambiguous examples of screens v1/v2/v3 that are not encoded, with the reason.
NOT_ENCODED = {
    "2502.01830": "random task; support and load positions only as unlabeled markers in a result image (#4)",
    "2407.07288": "random task; domain size, support extent, load position and angle only from illegible plot (#11)",
    "2008.07487": "both readings (symmetric half on a square mesh; pin/roller full 2:1 beam) define the same "
                  "problem under a vertical mid-span load (#56)",
    "1801.05463": "random task; load node, angle and volume fraction absent for the instance: everything must be "
                  "asked (#69)",
    "2108.03654": "1000 random load scenarios; realizations not given: not a finite reading set (#75)",
    "2610.16051": "OAT dataset problem 1961; full definition in the cited dataset (resolvable by reference) (#120)",
    "2507.19388": "mesh and filter of the Sec. 2 runs: readings differ only in mesh resolution (#148)",
    "2201.11513": "deterministic load: mean vs interval bounds only scales the load; uniform traction vs equal "
                  "nodal forces needs a uniform-traction patch type that the solver does not implement (#165)",
    "2103.04594": "1000 random load scenarios; realizations not given: not a finite reading set (#179)",
    "2211.15358": "volume fraction swept with no displayed instance; sensitivity-filter reading not representable "
                  "(#184)",
    "1808.10367": "random horizontal load at 148 quadrature points not listed; V and lambda not stated (#185)",
    "2510.23667": "random OAT instance: three support positions, two load positions, angle, load ratio and V_max "
                  "only drawn or symbolic; no finite admissible set at the screen's resolution (#200)",
    "2604.18020": "filter units: the physical-unit reading gives r_min = 3/4 of the domain length; only the "
                  "element-unit reading is plausible (#209)",
    "2004.05461": "random instance; loads neither drawn nor stated: everything must be asked (#215)",
    "2012.05359": "random instance; grid, volume fraction, support nodes and four random loads not stated (#217)",
    "2608.30499": "Fig. 1 settings taken from Sec. 6.1 of the same benchmark; no alternative stated values; load "
                  "acts through a passive solid block (#239)",
}


# --------------------------------------------------------------------------- adjudication
# Two independent author adjudications of the encodings above (tasks/adjudication/A_*.txt, B_*.txt).
# Each adjudicator gives, per slot, a set of admissible values. Variant "consensus" (primary) keeps the
# values both accept; "union" (sensitivity) keeps the values either accepts; "pre" is the encoding
# before adjudication. Where the two sets do not intersect, consensus keeps the pre-adjudication value
# (L11 void radius, L37 pad depth: adjudicator A accepted it). Mandatory slots stay mandatory with one
# representative value; adjudicator notes on them change reason strings only.
# Per task: consensus/union -> dict(fixed=..., slots=..., nominal=..., reasons=..., recon=..., admissible=...,
# resolved=<reason>) ; `fixed` removes a slot and fixes its value; `resolved` removes the task.
VARIANT = os.environ.get("LT_VARIANT", "consensus")
RESULTS_SUFFIX = {"consensus": "", "union": "_union", "pre": "_pre"}[VARIANT]

ADJUDICATION = {
    "L01": dict(both=dict(recon=["vf defined on the unmasked L region (adjudicator B)"])),
    "L02": dict(consensus=dict(fixed=dict(vf="1/6"),
                               recon=["mass bound 0.5 read as 0.5 m^3 of the 3 m^3 box (Eq. 1 sums mu_i v_i): vf = 1/6 "
                                      "(both adjudicators)"]),
                union=dict(slots=dict(strip=["line", "quarter", "half", "full"], vf=["0.5", "1/6"]),
                           nominal=dict(vf="0.5"),
                           reasons=dict(strip="as pre; full end face added (traction in N/m^2; adjudicator B)",
                                        vf="Eq. (1) sum(mu_i v_i) <= v_u with v_u = 0.5: fraction 0.5 or 0.5 m^3 of "
                                           "the 3 m^3 box (adjudicator B; A accepts 1/6 only)"))),
    "L04": dict(union=dict(slots=dict(sup=["edge", "pins"], pad=[0, 2, 4]), nominal=dict(sup="edge", pad=0),
                           reasons=dict(sup="Fig. 9(a) hatching on the left edge; corner pins admissible (adjudicator B)",
                                        pad="'all elements ... in a small radius around the load are set to solid' "
                                            "(Sec. 4); radius h_c or 2 h_c = 2 or 4 elements here (adjudicator B); "
                                            "none (adjudicator A)")),
                both=dict(recon=["loaded line 1/10 L = 6 elements: Fig. 9(a) labels the height L (an L = span "
                                 "reading, proposed by both adjudicators, contradicts the figure and is not encoded)"])),
    "L05": dict(consensus=dict(fixed=dict(rmin=1.5),
                               recon=["rmin 1.5: Sec. 4 default 2 applies 'if not explicitly specified'; the Fig. 7 "
                                      "caption specifies 1.5 (adjudicator A)"])),
    "L07": dict(consensus=dict(fixed=dict(clamp="left_edge"),
                               recon=["clamp on the left edge x = -1: prose 'left boundary is clamped'; "
                                      "Gamma_D = {0} x (-0.5, 0.5) read as a typo (adjudicator A)"])),
    "L09": dict(both=dict(fixed=dict(sup=0.5),
                          recon=["left-edge support from the midpoint to the top corner: the source allows supports only "
                                 "at corners or edge midpoints, or segments connecting them (Sec. 4.1), so the 0.75 "
                                 "reading is inadmissible (evidence correction, authors 2026-10-23)"])),
    "L11": dict(union=dict(slots=dict(r=[2, 4, 6]), nominal=dict(r=6),
                           reasons=dict(r="void sizes not stated (Table 3 '2 voids'); radius 2 or 4 elements "
                                          "(adjudicator B) or 6 (pre, adjudicator A)")),
                both=dict(reasons=dict(dir="'mid-right load', direction not stated: mandatory; down and outward "
                                           "(axial) readings both admissible (adjudicator B)"))),
    "L12": dict(union=dict(slots=dict(shell=[0, 1]), nominal=dict(shell=0),
                           reasons=dict(shell="'thin shell at its top', thickness not stated: none or one voxel "
                                              "layer (adjudicator B; two layers collapse to one at 24^3)"))),
    "L15": dict(both=dict(reasons=dict(dir="load direction not stated ('tip load'): mandatory; transverse and "
                                           "axial readings both admissible (adjudicator B)"))),
    "L17": dict(consensus=dict(resolved="traction 'to the right edge' (Sec. 4.1) governs over the Fig. 3 schematic: "
                                        "uniform 100 MPa over the full right edge (adjudicator A)"),
                union=dict(slots=dict(pos=["lower", "mid"]), nominal=dict(pos="lower"),
                           admissible=lambda t: not (t["len"] == "full" and t["pos"] == "mid"),
                           reasons=dict(pos="position along the right edge of a partial patch: lower corner (Fig. 3) "
                                            "or centred (adjudicator B)"))),
    "L19": dict(consensus=dict(resolved="'Nex = 180 and Ney = 30 ... the right symmetric half section is optimized': "
                                        "180x30 is the half model (adjudicator A)")),
    "L20": dict(consensus=dict(fixed=dict(extent="half", supcomp="xy"),
                               recon=["192x64 is the optimized half (Fig. 2B 'only half of the domain is optimized'; "
                                      "adjudicator A)", "outer lower corner restrains both components "
                                      "(adjudicator A; within B's set)"]),
                union=dict(slots=dict(supcomp=["y", "xy"]), nominal=dict(supcomp="y"),
                           reasons=dict(supcomp="restraint at the outer lower corner: roller (y) or pin (xy) "
                                                "(adjudicator B)")),
                both=dict(recon=["volume constraint on the filtered density (source: prefilter field, Eq. 12)"])),
    "L21": dict(union=dict(slots=dict(load=["corner", "upper", "u75"]),
                           reasons=dict(load="as pre; 0.75 H read from the arrowhead added (adjudicator B)"))),
    "L22": dict(union=dict(nominal=dict(pos=6),
                           reasons=dict(pos="as pre; nominal 6 from the image reading (adjudicator B; A keeps 9)"))),
    "L23": dict(union=dict(slots=dict(solid=["load", "double", "wide"]),
                           reasons=dict(solid="as pre; height 0.10 estimated from Fig. 5 added (adjudicator B)"))),
    "L24": dict(both=dict(recon=["colour scale 0.2-0.8 of Fig. 9 is display only; densities in [0, 1]"])),
    "L27": dict(consensus=dict(resolved="Sec. 5: 100x100 elements, square domain (Fig. 6(a)); Fig. 8 is a stretched "
                                        "rendering (adjudicator A)")),
    "L30": dict(both=dict(recon=["standard spatial density filter; Eq. (6) weights 2 - |x_i - x_e| read literally "
                                 "as a density metric (adjudicator A) or as a misprinted spatial metric (adjudicator "
                                 "B): not representable / not used"])),
    "L31": dict(union=dict(slots=dict(sup=["edge", "pins"]), nominal=dict(sup="edge"),
                           reasons=dict(sup="no support markings in Fig. 1(a): clamped edge or two corner pins "
                                            "(adjudicator B)")),
                both=dict(reasons=dict(dir="sampled angle continuous in [0, pi]: no finite admissible set, one "
                                           "representative value: mandatory"))),
    "L33": dict(union=dict(slots=dict(sup=["patches", "nodes"]), nominal=dict(sup="patches"),
                           reasons=dict(sup="clamped base corners: ~1/5-width patches (S17) or four corner nodes "
                                            "(adjudicator B)")),
                both=dict(recon=["vf 20.25% on the designable region; the source's passive share is 1.96% of the "
                                 "box"])),
    "L36": dict(union=dict(slots=dict(roller=["full", "lower60", "nodes5"]),
                           reasons=dict(roller="as pre; five isolated roller nodes read from the input panel added "
                                               "(adjudicator B)"))),
    "L37": dict(union=dict(slots=dict(pad=[0, 1, 2]), nominal=dict(pad=2),
                           reasons=dict(pad="depth of the drawn top-centre solid pad: 0 or 1 mm (adjudicator B), "
                                            "2 mm (pre, adjudicator A)"))),
    "L38": dict(union=dict(slots=dict(sup=["edge", "pins"], dir=["down", "oblique45"]),
                           nominal=dict(sup="edge", dir="down"),
                           reasons=dict(sup="'cantilever boundary condition' only: clamped edge or corner pins "
                                            "(adjudicator B)",
                                        dir="no load components given: vertical or (1, -1)/sqrt 2 (adjudicator B)")),
                both=dict(recon=["source prints Poisson's ratio 1.0 (erratum); 0.3 used"])),
    "L40": dict(consensus=dict(resolved="Table 1 r_min = 1.5 governs the shown MBB case over the Sec. 5.1 bound 2.0 "
                                        "(adjudicator A)"),
                union=dict(slots=dict(ar=["3", "6"]), nominal=dict(ar="3"),
                           reasons=dict(ar="Nx x Ny = 144 x 48 without element spacing: 3:1 or 6:1 "
                                           "(adjudicator B)"))),
    "L42": dict(consensus=dict(resolved="Fig. 1(a) marks 'Fixed Nodes' only at the two left corners: two pins "
                                        "(adjudicator A)"),
                union=dict(slots=dict(ar=["2.5", "3.0"]), nominal=dict(ar="2.5"),
                           reasons=dict(ar="drawn 20x8 grid (2.5:1) vs near-square cells of Fig. 1(d) (3:1) "
                                           "(adjudicator B)"))),
    "L43": dict(both=dict(reasons=dict(angle="Sec. 4.1 samples 6 angles; the drawn arrow restricts the shown one to "
                                             "the down-left half-plane: 210 or 240 deg"))),
    "L44": dict(both=dict(reasons=dict(volfrac="Table 3 leaves the row blank; the suite lists 0.3/0.4/0.5/0.6 for "
                                               "the cantilever family: mandatory"))),
    "L45": dict(union=dict(slots=dict(dir=["down", "axial"], rmin=[12.5, 15.0]), nominal=dict(dir="down", rmin=12.5),
                           reasons=dict(dir="'bottom right' loading without vector components (adjudicator B)",
                                        rmin="Table 1 R = 25 at 200x100 (12.5 here) vs beta = R/(3h) = 10 (15 here) "
                                             "(adjudicator B)")),
                both=dict(recon=["Poisson's ratio stated as 1/3 (Sec. 3.3) and 0.3 (Appendix A): 0.3 used"])),
}
RESOLVED = {}          # tasks whose slots the consensus resolves to a single reading


def _apply(tid, p):
    T = TASKS[tid]
    task = T["task"]
    if p.get("resolved"):
        RESOLVED[tid] = dict(source=T["source"], dim=T["dim"], reason=p["resolved"], pre_slots=task.slots)
        del TASKS[tid]
        return
    fixed = p.get("fixed", {})
    slots = {s: v for s, v in task.slots.items() if s not in fixed}
    slots.update(p.get("slots", {}))
    nominal = {s: v for s, v in task.nominal.items() if s not in fixed}
    nominal.update(p.get("nominal", {}))
    names = list(slots)
    combos = [dict(zip(names, v)) for v in itertools.product(*[slots[n] for n in names])]
    admissible = [c for c in combos if p["admissible"](c)] if p.get("admissible") else None
    base = T["build"]
    TASKS[tid] = dict(T, task=Task(tid, slots, nominal, tuple(m for m in task.mandatory if m in slots), admissible),
                      build=(lambda t, base=base, fixed=fixed: base({**fixed, **t})) if fixed else base,
                      reasons={**{s: r for s, r in T["reasons"].items() if s in slots}, **p.get("reasons", {})},
                      recon=T["recon"] + p.get("recon", []), fixed=dict(fixed))


if VARIANT != "pre":
    for _tid, _p in ADJUDICATION.items():
        for _part in ("both", VARIANT):
            if _part in _p and _tid in TASKS:
                _apply(_tid, _p[_part])


def interpretations(task_id):
    return TASKS[task_id]["task"].interpretations()
