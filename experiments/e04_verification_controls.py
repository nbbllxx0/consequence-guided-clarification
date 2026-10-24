"""E04: verification and diagnostic controls (CMAME verification set).

V1  derivative check: adjoint dc/dx and d(sum xp)/dx vs central finite differences through the
    density filter and Heaviside projection (2-D Q4 and 3-D H8; beta = 1 and 8).
C1  load scale: F vs 3F give compliance ratio 9 and the same optimized design (scale-only reading
    is harmless; consequences see it).
C2  sign reversal: F vs -F give identical compliance and design (consequences cannot see it:
    the direction must be asked; mandatory slot).
C3  two springs (Codex R2 counterexample B): optimal value V(theta) = 1 is flat on [0.2, 0.8] while
    the design regret of committing to theta0 = 0.5 is 228.96% at theta = 0.2 (analytic and OC).
C4,C5  omitted intent: the robust design released without questions on L04 and L14 is evaluated
    under an intended load position outside the annotated pool (c = 0.7 and 0.3, i.e. 0.1 beyond
    the pool edge): a coverage failure that no policy can detect from the pool.
C6,C7  failed equilibrium: support readings that leave rigid-body modes (2-D x-only rollers on the
    L41 edge; 3-D L24 end strips fixed only vertically) are detected by the exact rank test and
    excluded from the admissible set.
Output: results/e04/verification.json
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import consequence as cq  # noqa: E402
import e03_literature_tasks as e03  # noqa: E402
import littasks as lt  # noqa: E402
import runner  # noqa: E402
import simp  # noqa: E402
import taskspec  # noqa: E402

OUT = os.path.join(ROOT, "results", "e04")


def derivative_check():
    out = {}
    cases = {"2D_cantilever_60x30": lt._cant2(60, 30, 0.4, 15.0, 4.0),
             "3D_cantilever_16x8x8": dict(dim=3, nelx=16, nely=8, nelz=8, volfrac=0.3, domain={"type": "rect"},
                                          supports=[{"face": "x0", "comp": "xyz"}],
                                          load_cases=[{"patches": [{"face": "x1", "center": [4.0, 4.0],
                                                                    "size": [4.0, 4.0], "dir": [0, -1, 0]}]}])}
    rng = np.random.default_rng(0)
    for name, spec in cases.items():
        P = taskspec.build(spec)
        S = simp.SIMP(P, simp.Settings(linear="superlu" if P.dim == 2 else "pardiso_spd"))
        x = np.clip(P.volfrac + 0.2 * rng.standard_normal(S.act.size), 0.05, 0.95)
        for beta in (1.0, 8.0):
            c, dc, dv, _, _ = S.gradient(x, beta)
            # 8 entries with the largest |dc| and 8 random entries; central differences, step sweep
            idx = np.concatenate([np.argsort(-np.abs(dc))[:8], rng.choice(S.act.size, 8, replace=False)])
            best = None
            for h in (1e-3, 1e-4, 1e-5, 1e-6):
                errs_c, errs_v, errs_n = [], [], []
                for i in idx:
                    xp_, xm_ = x.copy(), x.copy()
                    xp_[i] += h
                    xm_[i] -= h
                    fd_c = (S.gradient(xp_, beta)[0] - S.gradient(xm_, beta)[0]) / (2 * h)
                    fd_v = (S.physical(xp_, beta)[1].sum() - S.physical(xm_, beta)[1].sum()) / (2 * h)
                    errs_c.append(abs(fd_c - dc[i]) / abs(dc[i]))
                    errs_n.append(abs(fd_c - dc[i]) / np.abs(dc).max())
                    errs_v.append(abs(fd_v - dv[i]) / max(abs(dv[i]), 1e-12))
                rec = dict(h=h, max_rel_err_dc=float(max(errs_c)), median_rel_err_dc=float(np.median(errs_c)),
                           max_err_dc_over_max_dc=float(max(errs_n)), max_rel_err_dv=float(max(errs_v)))
                if best is None or rec["max_err_dc_over_max_dc"] < best["max_err_dc_over_max_dc"]:
                    best = rec
            out[f"{name}_beta{beta:g}"] = dict(best, n_checked=len(idx))
    return out


def optimize(spec, init="uniform", settings=None):
    st = settings or e03.settings_for(spec.get("dim", 2))
    return runner.run_many([(spec, init, st)], workers=1, threads=4, verbose=False)[0]


def scale_and_sign():
    base = lt._cant2(80, 40, 0.4, 20.0, 4.0)
    out = {}
    for name, fac, dirn in (("C1_scale_3F", 3.0, (0, -1)), ("C2_sign_minusF", 1.0, (0, 1))):
        alt = json.loads(json.dumps(base))
        alt["load_cases"][0]["patches"][0]["resultant"] = fac
        alt["load_cases"][0]["patches"][0]["dir"] = list(dirn)
        r0, r1 = optimize(base), optimize(alt)
        x0, _ = runner.load_design(r0["key"])
        x1, _ = runner.load_design(r1["key"])
        out[name] = dict(compliance_base=r0["compliance"], compliance_alt=r1["compliance"],
                         ratio=r1["compliance"] / r0["compliance"], expected_ratio=fac ** 2,
                         max_design_diff=float(np.abs(x0 - x1).max()),
                         accepted=[r0["accepted"], r1["accepted"]])
    return out


def two_springs():
    def c(x1, th):
        return th ** 4 / x1 ** 3 + (1 - th) ** 4 / (1 - x1) ** 3

    from scipy.optimize import minimize_scalar

    def opt(th):                      # x2 = 1 - x1 eliminates the volume constraint; bounds 0.1..0.9
        r = minimize_scalar(lambda x1: c(x1, th), bounds=(0.1, 0.9), method="bounded",
                            options=dict(xatol=1e-12))
        return np.array([r.x, 1 - r.x])
    ths = np.linspace(0.2, 0.8, 7)
    V = [c(opt(t)[0], t) for t in ths]
    return dict(theta=ths.tolist(), V_numeric=V, V_analytic=[1.0] * len(ths),
                regret_commit_0p5_at_0p2_analytic=c(0.5, 0.2) / 1.0 - 1.0,
                regret_commit_0p5_at_0p2_numeric=c(0.5, 0.2) / V[0] - 1.0,
                x_opt_numeric=[opt(t).tolist() for t in ths])


def omitted_intent():
    out = {}
    for tid, c_out in (("L04", 0.7), ("L14", 0.3)):
        T = lt.TASKS[tid]
        st = e03.settings_for(2)
        spec_out = T["build"](dict(c=c_out))
        r = optimize(spec_out)
        with np.load(os.path.join(ROOT, "results", "e03", f"robust_{tid}.npz")) as d:
            xr = d["xphys"]
        lib = cq.Library(st)
        lib.add("robust", xr, "robust")
        C = lib.evaluate(["robust"], {"out": spec_out})[0, 0]
        with open(os.path.join(ROOT, "results", "e03", f"robust_{tid}.json")) as fh:
            rb = json.load(fh)
        out[f"{tid}_c{c_out}"] = dict(pool=T["task"].slots["c"], intended=c_out, robust_worst_in_pool=max(rb["ratio"]) - 1,
                                      robust_loss_at_intended=C / r["compliance"] - 1, ref_accepted=r["accepted"])
    return out


def failed_equilibrium():
    s = lt.TASKS["L41"]["build"](dict(load=0.45))
    a = dict(s, supports=[{"edge": "left", "comp": "x"}])
    t = lt.TASKS["L24"]["build"](dict(sup=2, load="line"))
    b = dict(t, supports=[dict(sp, comp="y") for sp in t["supports"]])
    return {"C6_L41_x_rollers": dict(free_rigid_modes=taskspec.free_rigid_modes(a),
                                     annotated_reading_free_modes=taskspec.free_rigid_modes(s)),
            "C7_L24_vertical_only_strips": dict(free_rigid_modes=taskspec.free_rigid_modes(b),
                                                annotated_reading_free_modes=taskspec.free_rigid_modes(t)),
            "annotated_readings": int(sum(len(lt.interpretations(k)) for k in lt.TASKS)),
            "all_annotated_readings_free_modes": int(sum(taskspec.free_rigid_modes(T["build"](i))
                                                         for k, T in lt.TASKS.items() for i in lt.interpretations(k)))}


def main():
    os.makedirs(OUT, exist_ok=True)
    res = dict(V1_derivatives=derivative_check(), **scale_and_sign(), C3_two_springs=two_springs(),
               omitted_intent=omitted_intent(), failed_equilibrium=failed_equilibrium())
    with open(os.path.join(OUT, "verification.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(res, indent=1)[:6000])


if __name__ == "__main__":
    main()
