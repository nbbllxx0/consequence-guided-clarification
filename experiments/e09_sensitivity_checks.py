"""E09: prescribed sensitivity checks from the Codex round-3 audit.

(a) L22 at the source filter radius: the source uses a sensitivity filter of radius 4 px; E03 used a
    density filter of radius 2. Rebuild all 18 readings with density-filter radius 4, two starts, full
    table, CGC and CGC_S replay; compare with E03.
(b) L07 robust design: the E03 run stopped unconverged at 400 iterations; rerun with final move 0.01 and
    600 final iterations (same p-norm objective and references).
(c) Matched 2-D controls for the dimensional comparison: the 2-D cantilever (80x40, clamped left edge,
    12-element patch moving along the right edge at 0.2..0.8 of the height) at vf 0.15 without passive
    region and at vf 0.40 with and without a 2-element passive strip at the loaded edge, against the 3-D
    cantilever track E02 cant_y (40x20x20, vf 0.15, no passive region, patch moving along the height).
Output: results/e09/*.json
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("LT_VARIANT", "pre")       # the L07 check needs both pre-adjudication clamp readings
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import e03_literature_tasks as e03  # noqa: E402
import e08_near_threshold as e08  # noqa: E402
import littasks as lt  # noqa: E402
import policies as pl  # noqa: E402
import robust  # noqa: E402

OUT = os.path.join(ROOT, "results", "e09")


def l22_radius():
    specs = {k: dict(s, rmin=4.0) for k, s in e08.specs_for("L22", 1).items()}
    orc, info = e08.table("L22", specs, e03.INITS, e03.settings_for(2))
    rp = e08.replay("L22", orc)
    base = json.load(open(os.path.join(e03.OUT, "replay.json")))["L22"]["_rows"]
    out = dict(B=info["B"], B_nominal=info["B_nominal"], accepted=all(info["accepted"].values()),
               questions={p: float(np.mean([r["n_asked"] for r in rp[p]])) for p in rp},
               bundles={p: float(np.mean([r["bundles"] for r in rp[p]])) for p in rp},
               released={p: int(sum(r["released"] for r in rp[p])) for p in rp},
               base_questions={p: float(np.mean([r["n_asked"] for r in base[p]])) for p in ("CGC", "CGC_S")},
               base_bundles={p: float(np.mean([r["optimizations"] for r in base[p]])) for p in ("CGC", "CGC_S")})
    return out


def l07_robust():
    T = lt.TASKS["L07"]
    interps = lt.interpretations("L07")
    specs = [T["build"](t) for t in interps]
    ref = json.load(open(os.path.join(e03.OUT, "L07.json")))["ref"]
    st = dict(e03.settings_for(2), final_move=0.01, final_max_iter=600)
    st["schedule"] = [tuple(x) for x in st["schedule"]]
    R = robust.RobustSIMP(specs, [ref[pl.ikey(t)] for t in interps], st)
    r = R.optimize()
    return dict(converged=r["converged"], n_iter=r["n_iter"], ratio=r["ratio"].tolist(),
                worst_loss=float(max(r["ratio"]) - 1))


def matched_controls():
    vals = [0.2, 0.35, 0.5, 0.65, 0.8]
    st = e03.settings_for(2)

    def spec(v, vf, strip):
        s = lt._cant2(80, 40, vf, v * 40, 12.0)
        if strip:
            s["solid"] = [[78, 0, 80, 40]]
        return s
    out = {}
    for name, vf, strip in (("2D_vf015_nostrip", 0.15, False), ("2D_vf040_nostrip", 0.40, False),
                            ("2D_vf040_strip", 0.40, True)):
        specs = {f"v={v}": spec(v, vf, strip) for v in vals}
        orc, info = e08.table(None, specs, e03.INITS, st, nominal="v=0.5")
        L = np.array(info["C"]) / np.array([info["ref"][k] for k in info["keys"]])[None, :] - 1
        out[name] = dict(vals=vals, nominal_row=L[2].tolist(), max_loss=float(np.nanmax(L[np.isfinite(L)])),
                         noise_max=float(max(info["noise"].values())), accepted=all(info["accepted"].values()))
    d = json.load(open(os.path.join(ROOT, "results", "e02", "cant_y.json")))
    out["3D_cant_y_vf015_nostrip"] = dict(vals=d["vals"], nominal_row=np.array(d["L"])[2].tolist(),
                                          max_loss=float(np.max(d["L"])), noise_max=float(max(d["noise"])))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    which = sys.argv[1:] or ["l22", "l07", "matched"]
    for w, fn in (("l22", l22_radius), ("l07", l07_robust), ("matched", matched_controls)):
        if w in which:
            res = fn()
            with open(os.path.join(OUT, f"{w}.json"), "w") as fh:
                json.dump(res, fh, indent=1)
            print(w, json.dumps(res)[:1500], flush=True)


if __name__ == "__main__":
    main()
