"""Round-off sensitivity of SIMP trajectories: perturb the initial design by 1e-12 and
compare final compliances. Same solver, same settings; only the start differs."""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import test_parity as tp  # noqa: E402

rng = np.random.default_rng(1)
res = {}
for name in ["bridge_120x30", "cantilever_60x30", "mbb_90x30", "lbracket_60x60", "cantilever_two_holes"]:
    spec, bc = tp.old_problem(name)
    finals = []
    for k in range(4):
        S = tp.new_solver(spec, bc)
        x0 = np.full(S.act.size, spec.volfrac)
        if k:
            x0 = x0 + 1e-12 * rng.standard_normal(x0.size)
        finals.append(float(S.optimize(x0=x0)["history"][-1]))
    f = np.array(finals)
    res[name] = dict(finals=finals, spread_rel=float((f.max() - f.min()) / f.min()))
    print(f"{name:24s} finals={np.round(f, 4)}  spread={res[name]['spread_rel']:.2e}")
with open(os.path.join(os.path.dirname(HERE), "results", "noise_floor_20261022.json"), "w") as fh:
    json.dump(res, fh, indent=1)
