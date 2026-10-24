"""Declarative, JSON-serializable problem specifications -> simp.Problem.

A specification fixes everything the solver needs. Candidate interpretations of an
ambiguous request are specifications that differ in a few fields (entity, position,
width, direction, load-case grouping). Lengths are in element widths of the coarse
reference mesh unless a mesh `scale` is given (used for refinement studies: all
lengths are multiplied by `scale`, the element size stays 1).

2-D spec:
{
  "dim": 2, "nelx": 120, "nely": 60, "volfrac": 0.4, "scale": 1,
  "domain": {"type": "rect"} | {"type": "L", "cut_x": 60, "cut_y": 30}
            | {"type": "holes", "holes": [[xc, yc, r], ...]},
  "supports": [{"edge": "left", "range": [s0, s1] or null, "comp": "xy"|"x"|"y"}],
  "load_cases": [ {"weight": 1, "patches": [
        {"edge": "right"|..., "segment": [x0,y0,x1,y1] (optional), "center": s, "width": w,
         "dir": [dx, dy], "resultant": 1.0}, ... ]}, ... ],
  "solid": [[x0, y0, x1, y1], ...]   (passive solid boxes, optional),
}
3-D spec: "dim": 3, "nelz", faces "x0","x1","y0","y1","z0","z1"; a support may give
"rect": [u0,u1,v0,v1] on the face; a patch gives "center": [u, v], "size": [a, b]
(passive solid boxes "solid": [[x0, y0, z0, x1, y1, z1], ...]),
(raised-cosine in both directions, product kernel), "dir": [dx, dy, dz].
Face coordinates (u, v): x-faces -> (y, z); y-faces -> (x, z); z-faces -> (x, y).
"""
from __future__ import annotations

import hashlib
import json

import numpy as np

import simp


def spec_hash(spec: dict) -> str:
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:16]


# ------------------------------------------------------------------ 2-D helpers
def _scaled(n, k):
    """Element count n * k; non-integer scales are allowed only when the product is integral."""
    m = n * k
    if abs(m - round(m)) > 1e-9:
        raise ValueError(f"scale {k} gives a non-integral element count {m}")
    return int(round(m))


def _centers2(nelx, nely):
    return np.repeat(np.arange(nelx), nely) + 0.5, np.tile(np.arange(nely), nelx) + 0.5


def _domain2(spec, nelx, nely, k):
    d = spec.get("domain", {"type": "rect"})
    cx, cy = _centers2(nelx, nely)
    act = np.ones(nelx * nely, bool)
    if d["type"] == "L":
        act &= ~((cx > d["cut_x"] * k) & (cy > d["cut_y"] * k))
    elif d["type"] == "holes":
        for xc, yc, r in d["holes"]:
            act &= (cx - xc * k) ** 2 + (cy - yc * k) ** 2 > (r * k) ** 2
    elif d["type"] == "xmax":                       # rectangle truncated at x = xmax (and y = ymax)
        act &= cx < d["xmax"] * k
        if "ymax" in d:
            act &= cy < d["ymax"] * k
    elif d["type"] != "rect":
        raise ValueError(d["type"])
    return act


def _edge2(nelx, nely, edge, segment=None, k=1):
    """Nodes and arc coordinate (in coarse units) along an edge or an axis-aligned segment."""
    if segment is not None:
        x0, y0, x1, y1 = [v * k for v in segment]
        if x0 == x1:
            iy = np.arange(int(round(min(y0, y1))), int(round(max(y0, y1))) + 1)
            return simp.node_id(nely, int(round(x0)), iy), (iy - min(y0, y1)) / k
        ix = np.arange(int(round(min(x0, x1))), int(round(max(x0, x1))) + 1)
        return simp.node_id(nely, ix, int(round(y0))), (ix - min(x0, x1)) / k
    if edge in ("left", "right"):
        iy = np.arange(nely + 1)
        return simp.node_id(nely, 0 if edge == "left" else nelx, iy), iy / k
    ix = np.arange(nelx + 1)
    return simp.node_id(nely, ix, 0 if edge == "bottom" else nely), ix / k


def _raised_cosine_nodal(s, center, width, nquad=4000):
    """Consistent nodal weights (linear elements) of a raised-cosine patch, unit integral."""
    lo, hi = center - width / 2, center + width / 2
    if lo < s.min() - 1e-9 or hi > s.max() + 1e-9:
        raise ValueError(f"patch [{lo:.3f},{hi:.3f}] leaves the entity [{s.min():.3f},{s.max():.3f}]")
    q = lo + (np.arange(nquad) + 0.5) * (hi - lo) / nquad
    t = 0.5 * (1 + np.cos(np.pi * (q - center) / (width / 2)))
    order = np.argsort(s)
    ss = s[order]
    w = np.zeros(len(s))
    kk = np.clip(np.searchsorted(ss, q) - 1, 0, len(ss) - 2)
    xi = (q - ss[kk]) / (ss[kk + 1] - ss[kk])
    np.add.at(w, order[kk], t * (1 - xi))
    np.add.at(w, order[kk + 1], t * xi)
    return w / w.sum()


def _build2(spec):
    k = spec.get("scale", 1)
    nelx, nely = _scaled(spec["nelx"], k), _scaled(spec["nely"], k)
    act = _domain2(spec, nelx, nely, k)
    ndof = 2 * (nelx + 1) * (nely + 1)
    fixed = []
    for sup in spec["supports"]:
        nodes, s = _edge2(nelx, nely, sup.get("edge"), sup.get("segment"), k)
        if sup.get("range") is not None:
            lo, hi = sup["range"]
            sel = (s >= lo - 1e-9) & (s <= hi + 1e-9)
            nodes = nodes[sel]
        for c, ch in ((0, "x"), (1, "y")):
            if ch in sup.get("comp", "xy"):
                fixed.append(2 * nodes + c)
    fixed = np.unique(np.concatenate(fixed)) if fixed else np.array([], int)
    loads = []
    for lc in spec["load_cases"]:
        f = np.zeros(ndof)
        for pt in lc["patches"]:
            nodes, s = _edge2(nelx, nely, pt.get("edge"), pt.get("segment"), k)
            w = _raised_cosine_nodal(s, pt["center"], pt["width"])
            d = np.asarray(pt["dir"], float)
            d /= np.linalg.norm(d)
            r = pt.get("resultant", 1.0)
            f[2 * nodes] += r * w * d[0]
            f[2 * nodes + 1] += r * w * d[1]
        loads.append(simp.LoadCase(f, lc.get("weight", 1.0)))
    solid = None
    if spec.get("solid"):
        cx, cy = _centers2(nelx, nely)
        solid = np.zeros(nelx * nely, bool)
        for x0, y0, x1, y1 in spec["solid"]:
            solid |= (cx > x0 * k) & (cx < x1 * k) & (cy > y0 * k) & (cy < y1 * k)
    return simp.Problem(nelx, nely, fixed, loads, volfrac=spec["volfrac"], active=act, solid=solid)


# ------------------------------------------------------------------ 3-D helpers
def _face3(nelx, nely, nelz, face):
    """Node ids on a box face and their (u, v) coordinates."""
    ax, side = face[0], face[1]
    n = {"x": nelx, "y": nely, "z": nelz}
    if ax == "x":
        a, b = np.meshgrid(np.arange(nely + 1), np.arange(nelz + 1), indexing="ij")
        ix = 0 if side == "0" else nelx
        nodes = simp.node_id(nely, ix, a, b, nelz)
    elif ax == "y":
        a, b = np.meshgrid(np.arange(nelx + 1), np.arange(nelz + 1), indexing="ij")
        iy = 0 if side == "0" else nely
        nodes = simp.node_id(nely, a, iy, b, nelz)
    else:
        a, b = np.meshgrid(np.arange(nelx + 1), np.arange(nely + 1), indexing="ij")
        iz = 0 if side == "0" else nelz
        nodes = simp.node_id(nely, a, b, iz, nelz)
    del n
    return nodes.ravel(), a.ravel().astype(float), b.ravel().astype(float)


def _cos1(x, c, w):
    t = np.zeros_like(x)
    m = np.abs(x - c) < w / 2
    t[m] = 0.5 * (1 + np.cos(np.pi * (x[m] - c) / (w / 2)))
    return t


def _patch_weights3(u, v, center, size, nq=60):
    """Consistent nodal weights of a product raised-cosine patch on a structured face."""
    uc, vc = center
    a, b = size
    if uc - a / 2 < u.min() - 1e-9 or uc + a / 2 > u.max() + 1e-9 or vc - b / 2 < v.min() - 1e-9 or vc + b / 2 > v.max() + 1e-9:
        raise ValueError("3-D patch leaves the face")
    w = np.zeros(len(u))
    # integrate per face cell with nq x nq midpoint rule and bilinear shape functions
    U = np.unique(u)
    V = np.unique(v)
    idx = {(uu, vv): i for i, (uu, vv) in enumerate(zip(u, v))}
    g = (np.arange(nq) + 0.5) / nq
    for i in range(len(U) - 1):
        if U[i + 1] < uc - a / 2 or U[i] > uc + a / 2:
            continue
        for j in range(len(V) - 1):
            if V[j + 1] < vc - b / 2 or V[j] > vc + b / 2:
                continue
            qu = U[i] + g * (U[i + 1] - U[i])
            qv = V[j] + g * (V[j + 1] - V[j])
            tu, tv = _cos1(qu, uc, a), _cos1(qv, vc, b)
            if not tu.any() or not tv.any():
                continue
            T = np.outer(tu, tv)
            xi, et = np.meshgrid(g, g, indexing="ij")
            for (di, dj, N) in ((0, 0, (1 - xi) * (1 - et)), (1, 0, xi * (1 - et)), (1, 1, xi * et), (0, 1, (1 - xi) * et)):
                w[idx[(U[i + di], V[j + dj])]] += float(np.sum(T * N))
    return w / w.sum()


def _build3(spec):
    k = spec.get("scale", 1)
    nelx, nely, nelz = _scaled(spec["nelx"], k), _scaled(spec["nely"], k), _scaled(spec["nelz"], k)
    nel = nelx * nely * nelz
    ex, ey, ez = (a.ravel() + 0.5 for a in np.meshgrid(np.arange(nelx), np.arange(nely), np.arange(nelz), indexing="ij"))
    act = np.ones(nel, bool)
    d = spec.get("domain", {"type": "rect"})
    if d["type"] == "L":                     # remove x > cut_x and y > cut_y (prismatic in z)
        act &= ~((ex > d["cut_x"] * k) & (ey > d["cut_y"] * k))
    elif d["type"] == "holes":               # cylindrical holes along an axis: [axis, c1, c2, r]
        for ax, c1, c2, r in d["holes"]:
            p, q = {"z": (ex, ey), "y": (ex, ez), "x": (ey, ez)}[ax]
            act &= (p - c1 * k) ** 2 + (q - c2 * k) ** 2 > (r * k) ** 2
    elif d["type"] == "boxes_removed":
        for x0, y0, z0, x1, y1, z1 in d["boxes"]:
            act &= ~((ex > x0 * k) & (ex < x1 * k) & (ey > y0 * k) & (ey < y1 * k) & (ez > z0 * k) & (ez < z1 * k))
    ndof = 3 * (nelx + 1) * (nely + 1) * (nelz + 1)
    fixed = []
    for sup in spec["supports"]:
        nodes, u, v = _face3(nelx, nely, nelz, sup["face"])
        if sup.get("rect") is not None:
            u0, u1, v0, v1 = [t * k for t in sup["rect"]]
            m = (u >= u0 - 1e-9) & (u <= u1 + 1e-9) & (v >= v0 - 1e-9) & (v <= v1 + 1e-9)
            nodes = nodes[m]
        for c, ch in ((0, "x"), (1, "y"), (2, "z")):
            if ch in sup.get("comp", "xyz"):
                fixed.append(3 * nodes + c)
    fixed = np.unique(np.concatenate(fixed))
    loads = []
    for lc in spec["load_cases"]:
        f = np.zeros(ndof)
        for pt in lc["patches"]:
            nodes, u, v = _face3(nelx, nely, nelz, pt["face"])
            w = _patch_weights3(u / k, v / k, pt["center"], pt["size"])
            dvec = np.asarray(pt["dir"], float)
            dvec /= np.linalg.norm(dvec)
            r = pt.get("resultant", 1.0)
            for c in range(3):
                f[3 * nodes + c] += r * w * dvec[c]
        loads.append(simp.LoadCase(f, lc.get("weight", 1.0)))
    solid = None
    if spec.get("solid"):                    # passive solid boxes [x0, y0, z0, x1, y1, z1]
        solid = np.zeros(nel, bool)
        for x0, y0, z0, x1, y1, z1 in spec["solid"]:
            solid |= (ex > x0 * k) & (ex < x1 * k) & (ey > y0 * k) & (ey < y1 * k) & (ez > z0 * k) & (ez < z1 * k)
    return simp.Problem(nelx, nely, fixed, loads, volfrac=spec["volfrac"], nelz=nelz, active=act, solid=solid)


def build(spec: dict) -> simp.Problem:
    return _build3(spec) if spec.get("dim", 2) == 3 else _build2(spec)


def support_signature(spec: dict) -> str:
    """Specifications with equal signatures share the stiffness matrix of any design."""
    keys = ("dim", "nelx", "nely", "nelz", "scale", "domain", "supports", "solid")
    return spec_hash({kk: spec.get(kk) for kk in keys})


def free_rigid_modes(spec: dict) -> int:
    """Number of rigid-body modes left unconstrained by the supports (0 = statically admissible
    support set). Exact rank test of the rigid modes restricted to the fixed DOFs."""
    P = build(spec)
    fixed = np.asarray(P.fixed_dofs)
    if P.dim == 2:
        n = (P.nelx + 1) * (P.nely + 1)
        ix, iy = np.divmod(np.arange(n), P.nely + 1)
        modes = np.zeros((2 * n, 3))
        modes[0::2, 0] = 1.0
        modes[1::2, 1] = 1.0
        modes[0::2, 2], modes[1::2, 2] = -iy, ix
    else:
        n = (P.nelx + 1) * (P.nely + 1) * (P.nelz + 1)
        ix = np.arange(n) // ((P.nely + 1) * (P.nelz + 1))
        iy = (np.arange(n) // (P.nelz + 1)) % (P.nely + 1)
        iz = np.arange(n) % (P.nelz + 1)
        modes = np.zeros((3 * n, 6))
        for c in range(3):
            modes[c::3, c] = 1.0
        modes[0::3, 3], modes[1::3, 3] = -iy, ix          # rotation about z
        modes[1::3, 4], modes[2::3, 4] = -iz, iy          # rotation about x
        modes[2::3, 5], modes[0::3, 5] = -ix, iz          # rotation about y
    if fixed.size == 0:
        return modes.shape[1]
    return int(modes.shape[1] - np.linalg.matrix_rank(modes[fixed], tol=1e-9))
