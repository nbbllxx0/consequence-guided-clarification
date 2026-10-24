"""Geometry and loading builders for 2-D tasks on a structured grid of unit elements.

Physical coordinates: x in [0, nelx], y in [0, nely] (element width = 1).
"""
from __future__ import annotations

import numpy as np

from simp2d import LoadCase, node_id


def element_centers(nelx, nely):
    ex = np.repeat(np.arange(nelx), nely)
    ey = np.tile(np.arange(nely), nelx)
    return ex + 0.5, ey + 0.5


def mask_rectangle(nelx, nely):
    return np.ones(nelx * nely, bool)


def mask_l_domain(nelx, nely, cut_x, cut_y):
    """Remove the upper-right block x > cut_x, y > cut_y (genuine L-shaped domain)."""
    cx, cy = element_centers(nelx, nely)
    return ~((cx > cut_x) & (cy > cut_y))


def mask_holes(nelx, nely, holes):
    """Remove circular holes [(xc, yc, r), ...] (genuine excluded regions)."""
    cx, cy = element_centers(nelx, nely)
    keep = np.ones(nelx * nely, bool)
    for xc, yc, r in holes:
        keep &= (cx - xc) ** 2 + (cy - yc) ** 2 > r ** 2
    return keep


def edge_nodes(nelx, nely, edge):
    """Node ids along a straight outer edge and their arc coordinate s (in element units)."""
    if edge == "left":
        iy = np.arange(nely + 1)
        return node_id(nely, 0, iy), iy.astype(float)
    if edge == "right":
        iy = np.arange(nely + 1)
        return node_id(nely, nelx, iy), iy.astype(float)
    if edge == "bottom":
        ix = np.arange(nelx + 1)
        return node_id(nely, ix, 0), ix.astype(float)
    if edge == "top":
        ix = np.arange(nelx + 1)
        return node_id(nely, ix, nely), ix.astype(float)
    raise ValueError(edge)


def segment_nodes(nelx, nely, x0, y0, x1, y1):
    """Grid nodes on an axis-aligned segment (e.g. an inner edge of an L-domain)."""
    if x0 == x1:
        iy = np.arange(int(round(min(y0, y1))), int(round(max(y0, y1))) + 1)
        return node_id(nely, int(round(x0)), iy), iy.astype(float) - min(y0, y1)
    if y0 == y1:
        ix = np.arange(int(round(min(x0, x1))), int(round(max(x0, x1))) + 1)
        return node_id(nely, ix, int(round(y0))), ix.astype(float) - min(x0, x1)
    raise ValueError("segment must be axis-aligned")


def fixed_dofs(nodes, components=(0, 1)):
    nodes = np.asarray(nodes)
    return np.unique(np.concatenate([2 * nodes + c for c in components]))


def patch_traction(nelx, nely, nodes, s, center, width, direction, resultant=1.0, nquad=2000):
    """Consistent nodal loads of a smooth raised-cosine traction patch on an edge.

    t(s) = A * 0.5 * (1 + cos(pi (s - center) / (width/2))) for |s - center| < width/2,
    with A chosen so that the integral of t over the edge equals `resultant`.
    `width` is the full support (twice the half-width). The patch must lie on the edge.
    Linear shape functions along the edge; integration by midpoint rule on `nquad`
    points. Returns a global force vector.
    """
    s = np.asarray(s, float)
    order = np.argsort(s)
    nodes, s = np.asarray(nodes)[order], s[order]
    lo, hi = center - width / 2, center + width / 2
    if lo < s[0] - 1e-9 or hi > s[-1] + 1e-9:
        raise ValueError("patch extends beyond the edge")
    q = lo + (np.arange(nquad) + 0.5) * (hi - lo) / nquad
    t = 0.5 * (1 + np.cos(np.pi * (q - center) / (width / 2)))
    dq = (hi - lo) / nquad
    nodal = np.zeros(len(s))
    k = np.clip(np.searchsorted(s, q) - 1, 0, len(s) - 2)
    xi = (q - s[k]) / (s[k + 1] - s[k])
    np.add.at(nodal, k, t * (1 - xi) * dq)
    np.add.at(nodal, k + 1, t * xi * dq)
    nodal *= resultant / nodal.sum()
    f = np.zeros(2 * (nelx + 1) * (nely + 1))
    d = np.asarray(direction, float)
    d = d / np.linalg.norm(d)
    f[2 * nodes] += nodal * d[0]
    f[2 * nodes + 1] += nodal * d[1]
    return f


def load_cases(*vectors, weights=None):
    w = weights or [1.0] * len(vectors)
    return [LoadCase(v, wi) for v, wi in zip(vectors, w)]
