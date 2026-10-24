"""Parallel optimization runs with immutable records and content-addressed caching.

A job = (spec, init, settings). Its key is sha256 of all three. Results go to
results/runs/<key>.json (+ .npz with the physical density). An existing record is
reused; nothing is overwritten. Workers are single-threaded for SuperLU problems;
Pardiso (3-D) jobs get `threads` MKL threads each.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.path.join(ROOT, "results", "runs")


def code_hash():
    h = hashlib.sha256()
    for f in ("simp.py", "taskspec.py", "runner.py"):
        with open(os.path.join(ROOT, "src", f), "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()[:12]


def job_key(spec, init, settings):
    return hashlib.sha256(json.dumps({"spec": spec, "init": init, "settings": settings},
                                     sort_keys=True).encode()).hexdigest()[:20]


def initial_design(S, init, volfrac):
    """'uniform' or 'sin5': 5% smooth sinusoidal perturbation, volume restored."""
    n = S.act.size
    x = np.full(n, volfrac)
    if init == "uniform":
        return x
    if init.startswith("sin"):
        amp = float(init[3:]) / 100.0
        c = S.centers()
        L = c.max(0) + 0.5
        pert = np.ones(n)
        for j in range(c.shape[1]):
            pert *= np.sin(2 * np.pi * c[:, j] / L[j] + 0.3 * (j + 1))
        x = np.clip(volfrac * (1 + amp * pert), 0, 1)
        return x * volfrac / x.mean()
    if init.startswith("rnd"):                       # 'rnd<amp%>s<seed>': smooth random low-frequency field
        amp_s, seed_s = init[3:].split("s")
        amp, rng = float(amp_s) / 100.0, np.random.default_rng(int(seed_s))
        c = S.centers()
        L = c.max(0) + 0.5
        pert = np.zeros(n)
        for _ in range(6):
            k = rng.integers(1, 4, c.shape[1])
            ph = rng.uniform(0, 2 * np.pi, c.shape[1])
            pert += np.prod(np.cos(np.pi * k[None, :] * c / L[None, :] + ph[None, :]), axis=1)
        pert /= np.abs(pert).max()
        x = np.clip(volfrac * (1 + amp * pert), 0, 1)
        return x * volfrac / x.mean()
    raise ValueError(init)


def _worker(spec, init, settings, key, threads):
    os.environ.setdefault("OMP_NUM_THREADS", str(threads))
    os.environ.setdefault("MKL_NUM_THREADS", str(threads))
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    import simp
    import taskspec
    prob = taskspec.build(spec)
    # per-task solver settings carried in the spec: filter radius and final move limit
    st = simp.Settings(**dict(settings, **{k: spec[k] for k in ("rmin", "final_move") if k in spec}))
    S = simp.SIMP(prob, st)
    x0 = initial_design(S, init, prob.volfrac)
    r = S.optimize(x0=x0)
    kkt, lam_fit = S.kkt_residual(r["x"], r["beta"], lam=r["oc_multiplier"])
    rec = dict(key=key, spec=spec, init=init, settings=settings, code=code_hash(),
               host=platform.node(), finished=time.strftime("%Y-%m-%dT%H:%M:%S"),
               compliance=r["compliance"], n_iter=r["n_iter"], converged=r["converged"],
               volfrac=r["volfrac"], grayness=r["grayness"], wall_s=r["wall_s"], residual=r["residual"],
               kkt=kkt, oc_multiplier=r["oc_multiplier"], kkt_multiplier=lam_fit, linear=r["linear"],
               beta=r["beta"], n_active=int(S.act.size), history_tail=list(map(float, r["history"][-25:])))
    rec["accepted"] = bool(r["converged"] and r["residual"] <= 1e-8 and abs(r["volfrac"] - prob.volfrac) <= 1e-4 * prob.volfrac + 1e-6)
    np.savez_compressed(os.path.join(RUNS, key + ".npz"), xphys=r["xphys"], x=r["x"], act=S.act)
    with open(os.path.join(RUNS, key + ".json"), "w") as fh:
        json.dump(rec, fh, indent=1)
    return rec


def load(key):
    p = os.path.join(RUNS, key + ".json")
    if not os.path.exists(p):
        return None
    with open(p) as fh:
        return json.load(fh)


def load_design(key):
    with np.load(os.path.join(RUNS, key + ".npz")) as d:
        return d["xphys"], d["act"]


def run_many(jobs, workers=None, threads=1, verbose=True):
    """jobs: list of (spec, init, settings_dict). Returns records in the same order."""
    os.makedirs(RUNS, exist_ok=True)
    keys = [job_key(*j) for j in jobs]
    todo = {}
    for j, k in zip(jobs, keys):
        if load(k) is None and k not in todo:
            todo[k] = j
    if todo:
        workers = workers or max(1, (os.cpu_count() or 2) // max(threads, 1) - 1)
        t0 = time.perf_counter()
        saved = {v: os.environ.get(v) for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")}
        os.environ["OMP_NUM_THREADS"] = os.environ["MKL_NUM_THREADS"] = str(threads)   # inherited at spawn,
        os.environ["OPENBLAS_NUM_THREADS"] = "1"                                         # before numpy loads
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(_worker, *j, k, threads): k for k, j in todo.items()}
            for i, f in enumerate(as_completed(futs), 1):
                rec = f.result()
                if verbose and (i % max(1, len(todo) // 10) == 0 or i == len(todo)):
                    print(f"  [{i}/{len(todo)}] {time.perf_counter() - t0:7.1f}s  last C={rec['compliance']:.4f} "
                          f"acc={rec['accepted']} kkt={rec['kkt']:.1e}", flush=True)
        for v, val in saved.items():
            if val is None:
                os.environ.pop(v, None)
            else:
                os.environ[v] = val
    return [load(k) for k in keys]


def settings_dict(**kw):
    import simp
    d = asdict(simp.Settings(**kw))
    d["schedule"] = [list(t) for t in d["schedule"]]
    return d
