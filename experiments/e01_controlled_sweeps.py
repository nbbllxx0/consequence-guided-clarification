"""E01: controlled mechanics track (pilot plan, Codex R2 Sec. 5.2), 2-D.

Four geometries x three continuous ambiguity tracks x 9 parameter values x 2 inits.
For each (geometry, track): best-of-2 reference per value, then the full 9x9 table
L[i, j] = C_j(d_i) / C_j(ref_j) - 1  (design optimized for value i, evaluated under j),
plus the per-value noise floor |C(uniform) - C(sin5)| / min.
Outputs: results/e01/<geom>_<track>.json and results/e01/summary.json.
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import runner  # noqa: E402
import simp  # noqa: E402
import taskspec  # noqa: E402

OUT = os.path.join(ROOT, "results", "e01")
SET = runner.settings_dict(rmin=2.4)          # 0.04 x height 60
INITS = ("uniform", "sin5")
NV = 9

# frozen geometry definitions (coarse units = element widths); loaded entity length Le
GEOMS = {
    "cantilever": dict(base=dict(dim=2, nelx=120, nely=60, volfrac=0.4, domain={"type": "rect"},
                                 supports=[{"edge": "left", "comp": "xy"}],
                                 solid=[[118, 0, 120, 60]]),
                       entity=dict(edge="right"), Le=60.0, dir=[0, -1]),
    "mbb_full": dict(base=dict(dim=2, nelx=180, nely=60, volfrac=0.4, domain={"type": "rect"},
                               supports=[{"edge": "bottom", "range": [0, 6], "comp": "xy"},
                                         {"edge": "bottom", "range": [174, 180], "comp": "y"}],
                               solid=[[0, 58, 180, 60]]),
                     entity=dict(edge="top"), Le=180.0, dir=[0, -1]),
    "l_domain": dict(base=dict(dim=2, nelx=60, nely=60, volfrac=0.4, domain={"type": "L", "cut_x": 30, "cut_y": 30},
                               supports=[{"edge": "top", "range": [0, 30], "comp": "xy"}],
                               solid=[[58, 0, 60, 30]]),
                     entity=dict(segment=[60, 0, 60, 30]), Le=30.0, dir=[0, -1]),
    "plate_hole": dict(base=dict(dim=2, nelx=120, nely=60, volfrac=0.4, domain={"type": "holes", "holes": [[60, 30, 9]]},
                                 supports=[{"edge": "left", "comp": "xy"}],
                                 solid=[[118, 0, 120, 60]]),
                       entity=dict(edge="right"), Le=60.0, dir=[0, -1]),
}


def track_specs(g):
    G = GEOMS[g]
    Le, ent = G["Le"], G["entity"]
    wmin = max(0.10 * Le, 4.0)
    wnom = (wmin + 0.30 * Le) / 2
    vals = np.linspace(0, 1, NV)
    out = {}

    def spec_with(patches):
        s = json.loads(json.dumps(G["base"]))
        s["load_cases"] = [{"weight": 1.0, "patches": patches}]
        return s
    centers = (0.2 + 0.6 * vals) * Le
    out["center"] = (centers / Le, [spec_with([dict(ent, center=float(c), width=wnom, dir=G["dir"])]) for c in centers])
    widths = wmin + (0.30 * Le - wmin) * vals
    out["width"] = (widths / Le, [spec_with([dict(ent, center=0.5 * Le, width=float(w), dir=G["dir"])]) for w in widths])
    alphas = 0.2 + 0.6 * vals
    out["split"] = (alphas, [spec_with([dict(ent, center=0.25 * Le, width=wmin, dir=G["dir"], resultant=float(a)),
                                        dict(ent, center=0.75 * Le, width=wmin, dir=G["dir"], resultant=float(1 - a))])
                             for a in alphas])
    return out


def cross_table(specs, recs_by_spec):
    """Best-of-inits references; 9x9 cross-evaluation (shared supports -> one factorization per design)."""
    n = len(specs)
    probs = [taskspec.build(s) for s in specs]
    S0 = simp.SIMP(probs[0], simp.Settings(**SET))
    loads_all = [p.loads for p in probs]
    ref_c, ref_key, noise = [], [], []
    for recs in recs_by_spec:
        cs = [r["compliance"] for r in recs]
        b = int(np.argmin(cs))
        ref_c.append(cs[b])
        ref_key.append(recs[b]["key"])
        noise.append((max(cs) - min(cs)) / min(cs))
    C = np.zeros((n, n))
    for i, k in enumerate(ref_key):
        xp, act = runner.load_design(k)
        assert np.array_equal(act, S0.act)
        lu = S0.factor(xp)
        for j in range(n):
            C[i, j] = S0.evaluate(xp, loads_all[j], lu)[0]
    ref = np.array(ref_c)
    # a cross design may beat the computed reference: keep signed gaps, report them
    best_known = np.minimum(ref, C.min(0))
    L_ref = C / ref[None, :] - 1.0
    L_best = C / best_known[None, :] - 1.0
    return dict(C=C.tolist(), ref=ref.tolist(), best_known=best_known.tolist(), L_ref=L_ref.tolist(),
                L_best=L_best.tolist(), noise=noise, ref_keys=ref_key,
                n_ref_beaten=int(np.sum(C.min(0) < ref * (1 - 1e-9))))


def main():
    os.makedirs(OUT, exist_ok=True)
    plan = {}
    jobs = []
    for g in GEOMS:
        for tr, (vals, specs) in track_specs(g).items():
            plan[(g, tr)] = (vals, specs)
            for s in specs:
                for init in INITS:
                    jobs.append((s, init, SET))
    print(f"E01: {len(jobs)} optimization jobs")
    recs = runner.run_many(jobs)
    it = iter(recs)
    summary = {}
    for (g, tr), (vals, specs) in plan.items():
        per = [[next(it) for _ in INITS] for _ in specs]
        tab = cross_table(specs, per)
        acc = [all(r["accepted"] for r in rr) for rr in per]
        kkt = [max(r["kkt"] for r in rr) for rr in per]
        tab.update(vals=list(map(float, vals)), accepted=acc, kkt_max=kkt,
                   wall_s=[sum(r["wall_s"] for r in rr) for rr in per])
        with open(os.path.join(OUT, f"{g}_{tr}.json"), "w") as fh:
            json.dump(tab, fh, indent=1)
        L = np.array(tab["L_ref"])
        summary[f"{g}/{tr}"] = dict(max_loss=float(L.max()), mid_row_max_loss=float(L[NV // 2].max()),
                                    noise_max=float(max(tab["noise"])), accepted=f"{sum(acc)}/{len(acc)}",
                                    kkt_max=float(max(kkt)), ref_beaten=tab["n_ref_beaten"])
        print(f"{g:11s} {tr:7s} max L={L.max():7.3f}  nominal-row max L={L[NV // 2].max():6.3f}  "
              f"noise max={max(tab['noise']):.2e}  accepted {sum(acc)}/{len(acc)}  kkt<= {max(kkt):.1e}  ref beaten {tab['n_ref_beaten']}")
    with open(os.path.join(OUT, "summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1)


if __name__ == "__main__":
    main()
