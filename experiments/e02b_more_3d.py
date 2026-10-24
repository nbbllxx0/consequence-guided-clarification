"""E02b: additional controlled 3-D tracks and checks (follows E02).

Tracks (best-of-2 references, cross table, as E02):
  cant_z_off  : E02 cantilever 40x20x20; 6x6 end patch at mid-height, centre offset
                d = 0..4 elements across the width (tolerance radius of a small offset).
  deck_off    : E02 deck 48x12x24; 12x6 top patch, lane offset d = 0..4 elements.
  lbr_pos     : 3-D L-bracket 40x40x10 (top-right quadrant removed, prismatic in z),
                top face of the vertical arm clamped; 4x4 patch on the arm end face
                (x = 40) at height y = 4..16 (5 values).
  deck_width  : deck with a central top patch of width 6..24 across the deck (4 values).
Checks:
  refine      : cant_y at 1.5x and 2x mesh (60x30x30 / 80x40x40, rmin scaled to 2.25 / 3.0),
                positions 0.35/0.5/0.65, one start; loss table compared with the coarse 3x3
                sub-table of E02.
  emin        : E02/E02b cross tables re-evaluated with Emin = 1e-9 (designs unchanged), and
                the fraction of the load resultant carried by nodes whose adjacent elements
                are all below density 0.5 ("unsupported load").
New optimizations use the GPU direct solver (linear="cudss"); E02 designs (Pardiso) are reused.
Outputs: results/e02b/<name>.json
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import consequence as cq  # noqa: E402
import e02_controlled_3d as e02  # noqa: E402
import runner  # noqa: E402
import simp  # noqa: E402
import taskspec  # noqa: E402

OUT = os.path.join(ROOT, "results", "e02b")
INITS = e02.INITS
SET = e02.SET
SETG = dict(SET, linear="cudss")
GPU_WORKERS = 6


def tracks():
    T = {}
    c = e02.cant(1)
    offs = [0, 1, 2, 3, 4]
    T["cant_z_off"] = (offs, [dict(c, load_cases=[{"patches": [{"face": "x1", "center": [10.0, 10.0 + d],
                                                                  "size": [6.0, 6.0], "dir": [0, -1, 0]}]}])
                              for d in offs])
    dk = e02.deck(1)
    T["deck_off"] = (offs, [dict(dk, load_cases=[{"patches": [{"face": "y1", "center": [24.0, 12.0 + d],
                                                                "size": [12.0, 6.0], "dir": [0, -1, 0]}]}])
                            for d in offs])
    lb = dict(dim=3, nelx=40, nely=40, nelz=10, volfrac=0.2, domain={"type": "L", "cut_x": 20, "cut_y": 20},
              supports=[{"face": "y1", "rect": [0, 20, 0, 10], "comp": "xyz"}])
    ys = [4.0, 7.0, 10.0, 13.0, 16.0]
    T["lbr_pos"] = (ys, [dict(lb, load_cases=[{"patches": [{"face": "x1", "center": [y, 5.0], "size": [4.0, 4.0],
                                                            "dir": [0, -1, 0]}]}]) for y in ys])
    ws = [6.0, 12.0, 18.0, 24.0]
    T["deck_width"] = (ws, [dict(dk, load_cases=[{"patches": [{"face": "y1", "center": [24.0, 12.0],
                                                               "size": [12.0, w], "dir": [0, -1, 0]}]}]) for w in ws])
    return T


def cross(specs, keys, settings=SETG):
    lib = cq.Library(settings)
    refs, noise = [], []
    for k, kk in enumerate(keys):
        cs = [runner.load(x)["compliance"] for x in kk]
        b = int(np.argmin(cs))
        xp, _ = runner.load_design(kk[b])
        lib.add(f"d{k}", xp, k)
        refs.append(cs[b])
        noise.append((max(cs) - min(cs)) / min(cs) if len(cs) > 1 else float("nan"))
    interps = {f"t{k}": s for k, s in enumerate(specs)}
    C = lib.evaluate([f"d{k}" for k in range(len(specs))], interps)
    return lib, np.array(refs), noise, C


def run_track(name, vals, specs, inits=INITS, settings=SETG, workers=GPU_WORKERS):
    jobs = [(s, i, settings) for s in specs for i in inits]
    recs = runner.run_many(jobs, workers=workers, threads=2)
    n = len(inits)
    keys = [[r["key"] for r in recs[n * k:n * k + n]] for k in range(len(specs))]
    lib, refs, noise, C = cross(specs, keys, settings)
    ref = np.minimum(refs, C.min(0))
    L = C / ref[None, :] - 1
    tab = dict(vals=list(map(float, vals)), C=C.tolist(), ref=ref.tolist(), L=L.tolist(), noise=noise,
               keys=keys, accepted=[all(runner.load(x)["accepted"] for x in kk) for kk in keys],
               wall_s=[sum(runner.load(x)["wall_s"] for x in kk) for kk in keys], counter=lib.counter.as_dict())
    with open(os.path.join(OUT, f"{name}.json"), "w") as fh:
        json.dump(tab, fh, indent=1)
    print(f"{name:12s} L row0={np.round(L[0], 3).tolist()} noise max={np.nanmax(noise):.2e} "
          f"accepted {sum(tab['accepted'])}/{len(keys)}", flush=True)
    return tab


def unsupported_fraction(spec, xphys, thr=0.5):
    """Fraction of the load resultant on nodes whose adjacent active elements all have
    density < thr (load applied to near-void)."""
    P = taskspec.build(spec)
    S = simp.SIMP(P, simp.Settings(**SET))
    dens = np.zeros(P.nel)
    dens[S.act] = xphys if xphys.size == S.act.size else xphys[S.act]
    nmax = np.zeros(P.ndof // 3)
    np.maximum.at(nmax, (S.edof[:, ::3] // 3).ravel(), np.repeat(dens[S.act], 8))
    f = np.abs(P.loads[0].f.reshape(-1, 3)).sum(1)
    return float(f[nmax < thr].sum() / f.sum())


def emin_check(name, vals, specs, keys):
    st9 = dict(SETG, Emin=1e-9)
    _, _, _, C6 = cross(specs, keys)
    _, _, _, C9 = cross(specs, keys, st9)
    L6 = C6 / np.diag(C6)[None, :] - 1
    L9 = C9 / np.diag(C9)[None, :] - 1
    best = [min(kk, key=lambda x: runner.load(x)["compliance"]) for kk in keys]     # as in cross()
    uf = [[unsupported_fraction(specs[t], runner.load_design(best[d])[0]) for t in range(len(specs))]
          for d in range(len(specs))]
    out = dict(vals=list(map(float, vals)), L_emin6=L6.tolist(), L_emin9=L9.tolist(), unsupported=uf)
    with open(os.path.join(OUT, f"emin_{name}.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    ratio = np.where(L6 > 1, L9 / np.maximum(L6, 1e-30), np.nan)
    print(f"emin {name:12s} max L6={L6.max():.3g} max L9={L9.max():.3g} "
          f"median L9/L6 (L6>1)={np.nanmedian(ratio) if np.isfinite(ratio).any() else float('nan'):.3g} "
          f"max unsupported={np.max(uf):.2f}", flush=True)


def refine():
    base = e02.cant(1)
    vals = [0.35, 0.5, 0.65]
    with open(os.path.join(ROOT, "results", "e02", "cant_y.json")) as fh:
        coarse = json.load(fh)
    idx = [int(np.argmin(np.abs(np.array(coarse["vals"]) - v))) for v in vals]
    Lc = np.array(coarse["L"])[np.ix_(idx, idx)]
    print("refine coarse 3x3:", np.round(Lc, 3).tolist(), flush=True)
    for k in (1.5, 2.0):
        specs = [dict(base, scale=k, rmin=1.5 * k,
                      load_cases=[{"patches": [{"face": "x1", "center": [v * 20, 10.0], "size": [6.0, 6.0],
                                                "dir": [0, -1, 0]}]}]) for v in vals]
        # cuDSS factors of 128k-element problems take several GB each (beyond the CuPy pool): one at a time
        tab = run_track(f"refine_cant_y_x{k}", vals, specs, inits=("uniform",), workers=3 if k < 2 else 1)
        print(f"refine x{k} 3x3:", np.round(tab["L"], 3).tolist(), flush=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    which = sys.argv[1:] or ["tracks", "refine", "emin"]
    T = tracks()
    if "tracks" in which:
        for name, (vals, specs) in T.items():
            run_track(name, vals, specs)
    if "emin" in which:
        runs = [(n, v, s, SET) for n, (v, s) in e02.tracks(1).items()] + [(n, v, s, SETG) for n, (v, s) in T.items()]
        for name, vals, specs, st in runs:          # E02 designs were made with Pardiso, E02b with cuDSS
            jobs = [(s, i, st) for s in specs for i in INITS]
            keys = [[runner.job_key(*j) for j in jobs[2 * k:2 * k + 2]] for k in range(len(specs))]
            if all(runner.load(x) is not None for kk in keys for x in kk):
                emin_check(name, vals, specs, keys)
    if "refine" in which:
        refine()


if __name__ == "__main__":
    main()
