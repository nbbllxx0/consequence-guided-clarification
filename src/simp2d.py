"""Backward-compatible 2-D names for the shared solver in ``simp.py``.

The 2-D implementation that passed the AutoSiMP parity tests on 2026-10-22 was
merged into ``simp.py`` (2-D and 3-D). ``tests/test_parity.py`` and
``tests/test_geometry_loads.py`` re-verify the merged code through these aliases.
"""
from simp import (LoadCase, Settings, heaviside, heaviside_deriv, ke_q4 as element_stiffness_unit,  # noqa: F401
                  edof_2d as edof_table, node_id)
from simp import Problem as Problem2D  # noqa: F401
from simp import SIMP as SIMP2D  # noqa: F401
