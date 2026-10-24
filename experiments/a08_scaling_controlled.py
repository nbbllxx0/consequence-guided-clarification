"""A08: reference bundles of CGC vs CGC_S on the controlled tracks (one slot, n readings each).

Each E01 (2-D, 9 readings) and E02/E02b (3-D, 4-5 readings) cross table is replayed as a one-slot task
with the middle (E01, lbr_pos, cant_*/deck_lane) or first (offset/width tracks) value as nominal. Every
reading in turn is the hidden truth. Reports questions, releases, pool-unsafe releases and reference
bundles per case. Shows where the ledgered saving comes from: consequential slots (asking prunes readings
before their references are computed) vs harmless slots (certified release needs every reference).
Output: results/a08/scaling.json, results/a08/scaling.md
"""
import glob
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import policies as pl  # noqa: E402

R = os.path.join(ROOT, "results")
OUT = os.path.join(R, "a08")
TAU = 0.05


def oracle(C, ref, noise, keys):
    Cd = {(d, t): float(C[i][j]) for i, d in enumerate(keys) for j, t in enumerate(keys)}
    return pl.Oracle(ref={k: float(r) for k, r in zip(keys, ref)}, C=Cd,
                     noise={k: (0.0 if not np.isfinite(n) else float(n)) for k, n in zip(keys, noise)})


def run(name, C, ref, noise, nominal_idx):
    n = len(ref)
    vals = list(range(n))
    task = pl.Task(name, {"v": vals}, {"v": vals[nominal_idx]})
    keys = [pl.ikey({"v": v}) for v in vals]
    orc = oracle(C, ref, noise, keys)
    res = {}
    for p in ("CGC", "CGC_S", "no_ask"):
        rows = []
        for v in vals:
            truth = {"v": v}
            o = pl.POLICIES[p](task, orc, truth, TAU)
            surv = [pl.ikey({"v": w}) for w in vals] if not o.asked else [pl.ikey(truth)]
            worst = max(orc.loss(o.commit, t) - orc.noise.get(t, 0) for t in surv)
            rows.append(dict(q=len(o.asked), released=o.released, unsafe=bool(o.released and worst > TAU),
                             bundles=o.optimizations))
        res[p] = dict(questions=float(np.mean([r["q"] for r in rows])),
                      unsafe=int(sum(r["unsafe"] for r in rows)),
                      bundles=float(np.mean([r["bundles"] for r in rows])))
    L = np.array(C) / np.array(ref)[None, :] - 1
    return dict(n=n, nominal_worst=float(np.max(L[nominal_idx])), **res)


def main():
    os.makedirs(OUT, exist_ok=True)
    out = {}
    for p in sorted(glob.glob(os.path.join(R, "e01", "*_*.json"))):
        if p.endswith("summary.json"):
            continue
        d = json.load(open(p))
        name = os.path.basename(p)[:-5]
        out[f"2D/{name}"] = run(name, d["C"], d["best_known"], d["noise"], len(d["vals"]) // 2)
    for sub, f, nom in (("e02", "cant_z", None), ("e02", "cant_y", None), ("e02", "deck_lane", None),
                        ("e02b", "cant_z_off", 0), ("e02b", "deck_off", 0), ("e02b", "lbr_pos", None),
                        ("e02b", "deck_width", 0)):
        d = json.load(open(os.path.join(R, sub, f"{f}.json")))
        n = len(d["vals"])
        out[f"3D/{f}"] = run(f, d["C"], d["ref"], d["noise"], n // 2 if nom is None else nom)
    with open(os.path.join(OUT, "scaling.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    lines = ["| track | readings | default-design worst loss | CGC questions | CGC bundles | CGC_S questions | CGC_S bundles "
             "| CGC_S pool-unsafe | silent-default pool-unsafe |", "|---|---|---|---|---|---|---|---|---|"]
    for k, v in out.items():
        lines.append(f"| {k} | {v['n']} | {v['nominal_worst']:.3g} | {v['CGC']['questions']:.2f} | "
                     f"{v['CGC']['bundles']:.2f} | {v['CGC_S']['questions']:.2f} | {v['CGC_S']['bundles']:.2f} | "
                     f"{v['CGC_S']['unsafe']} | {v['no_ask']['unsafe']} |")
    tot = {p: sum(v[p]["bundles"] * v["n"] for v in out.values()) for p in ("CGC", "CGC_S")}
    lines += ["", f"Total bundles over all cases: CGC {tot['CGC']:.0f}, CGC_S {tot['CGC_S']:.0f}."]
    with open(os.path.join(OUT, "scaling.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
