"""A36: the full MBB beam load-center track re-evaluated at a smaller void stiffness (reviewer request, loop v5
round 3; designs unchanged, no new optimization).

The nine E01 reference designs of the mbb_full center track (each with the two-element passive strip at the
loaded edge) are cross-evaluated with E_min/E_0 = 1e-6, as optimized, and 1e-9, as in the frozen-design
check of the three-dimensional tracks (Fig. 4d). Loss uses the diagonal of each table (each value's own
design) as reference, as in the 3-D check. Reported: the largest loss at each void stiffness and the median
ratio of losses at 1e-9 and 1e-6 over entries with loss above 1.
Usage: python experiments/a36_mbb_void_stiffness.py
Output: results/a36/mbb_full_center.json
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import e01_controlled_sweeps as e01  # noqa: E402
import runner  # noqa: E402
import simp  # noqa: E402
import taskspec  # noqa: E402

OUT = os.path.join(ROOT, "results", "a36")


def table(specs, keys, emin):
    probs = [taskspec.build(s) for s in specs]
    S = simp.SIMP(probs[0], simp.Settings(**dict(e01.SET, Emin=emin)))
    C = np.zeros((len(specs), len(specs)))
    for i, k in enumerate(keys):
        xp, act = runner.load_design(k)
        assert np.array_equal(act, S.act)
        lu = S.factor(xp)
        for j, p in enumerate(probs):
            C[i, j] = S.evaluate(xp, p.loads, lu)[0]
    return C


def main():
    vals, specs = e01.track_specs("mbb_full")["center"]
    with open(os.path.join(ROOT, "results", "e01", "mbb_full_center.json")) as fh:
        keys = json.load(fh)["ref_keys"]
    C6, C9 = table(specs, keys, 1e-6), table(specs, keys, 1e-9)
    L6 = C6 / np.diag(C6)[None, :] - 1
    L9 = C9 / np.diag(C9)[None, :] - 1
    big = L6 > 1
    ratio = L9[big] / L6[big]
    out = dict(vals=list(map(float, vals)), L_emin6=L6.tolist(), L_emin9=L9.tolist(), max_L6=float(L6.max()),
               max_L9=float(L9.max()), n_above_1=int(big.sum()),
               median_ratio=float(np.median(ratio)) if ratio.size else None,
               min_ratio=float(ratio.min()) if ratio.size else None, max_ratio=float(ratio.max()) if ratio.size else None)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "mbb_full_center.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({k: v for k, v in out.items() if not k.startswith("L_")}, indent=1))


if __name__ == "__main__":
    main()
