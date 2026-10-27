# Consequence-guided clarification: code and data

Code and data for the manuscript "Consequence-guided clarification: releasing minimum-compliance
topology-optimized designs from incomplete specifications" by S. Yang and J. Wang (Santa Clara
University), submitted to Computer Methods in Applied Mechanics and Engineering. Preprint:
arXiv:2610.34957 (https://arxiv.org/abs/2610.34957, https://doi.org/10.48550/arXiv.2610.34957).
Archived release: Zenodo, https://doi.org/10.5281/zenodo.23682520 (v1.0.0; all versions:
https://doi.org/10.5281/zenodo.23682519).

The repository holds the solver, the experiment and analysis scripts, the frozen literature frame,
the screening and adjudication records, the stored optimization runs, and the figure and table
generators. The stored runs in `results/runs/` let every replay, table and figure be regenerated
without new optimization.

## Contents

| Path | Content |
|---|---|
| `src/simp.py` | Three-field SIMP for 2-D (Q4) and 3-D (H8): density filter, Heaviside projection, optimality-criteria update, element removal, passive sets, independent load cases. Direct solvers: SuperLU, PARDISO (SPD), cuDSS on the GPU (`linear="cudss"`). |
| `src/taskspec.py` | Declarative JSON problem specification to `simp.Problem`; admissibility test for free rigid-body modes. |
| `src/runner.py` | Content-addressed run cache (`results/runs/<key>.json/.npz`) and process pool. |
| `src/consequence.py` | Design library and cross-evaluation (one factorization per design and support group). |
| `src/policies.py` | Clarification policies replayed against an intended reading. |
| `src/robust.py`, `src/mma.py` | Robust design (p-norm of reference-normalized compliances) and the method of moving asymptotes used for the bound-form min–max designs and the reference re-convergence. |
| `src/littasks.py` | The 41 literature-derived tasks with slots, admissible readings, reasons and reconstruction notes, and the two author adjudications. `LT_VARIANT=consensus` (default, primary benchmark: 36 tasks, 134 readings), `union` (41 tasks, 240 readings) or `pre` (before adjudication: 41 tasks, 153 readings). Outputs of the non-default variants go to `results/<name>_union/` and `results/<name>_pre/`. |
| `experiments/` | Experiment drivers (E01–E10) and analysis scripts (A03–A36). |
| `tests/` | Parity, geometry, load and solver checks; GPU benchmarks and profiles. |
| `tasks/` | Frozen arXiv frame (retrieved 22 October 2026), the three screening passes, the published-version checks, the screening scripts, and the two author adjudication records with their reconciliation (`tasks/adjudication/`). |
| `results/` | Stored optimization runs, cross-evaluation tables, policy replays, language-model outputs and scores, and all derived summaries. |
| `figures/make_figures.py`, `v4/figures/make_figures_v2.py`, `tables/` | Figure and table generators. |
| `v4/prompts/` | The language-model prompts and the answer schema reproduced in the Supplementary Information. |

## Not included

- Local copies of the third-party source papers (`tasks/sources/`). Each task's arXiv identifier is in
  `src/littasks.py` and in Supplementary Table S1. `tasks/scripts/fetch_papers.py` downloads the texts
  from arXiv.
- The paper texts supplied to the language-model experiments (`results/e05/inputs/`). They are rebuilt
  from the arXiv sources by `experiments/e05_llm_readings.py`.

## Licence

- Code, under the BSD 3-Clause License (`LICENSE`): `src/`, `experiments/`, `tests/`, `tasks/scripts/`,
  `figures/make_figures.py`, `v4/figures/make_figures_v2.py` and `tables/make_tables.py`.
- Data, under the Creative Commons Attribution 4.0 International licence (`LICENSE-data`): `results/`,
  the other files in `tasks/` (frame, screening passes, published-version checks, adjudication records),
  `tables/out/`, `tables/out_pre/` and `v4/prompts/`. The frame's paper metadata comes from the arXiv API,
  and arXiv's terms for that metadata still apply.

Please cite the manuscript when you use the code or the data:

```bibtex
@misc{yang2026consequence,
  author        = {Yang, Shaoliang and Wang, Jun},
  title         = {Consequence-guided clarification: releasing minimum-compliance topology-optimized
                   designs from incomplete specifications},
  year          = {2026},
  eprint        = {2610.34957},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CE},
  doi           = {10.48550/arXiv.2610.34957}
}
```

To cite the archived code and data:

```bibtex
@misc{yang2026consequencedata,
  author       = {Yang, Shaoliang and Wang, Jun},
  title        = {Code and data for: Consequence-guided clarification: releasing minimum-compliance
                  topology-optimized designs from incomplete specifications},
  howpublished = {Zenodo},
  version      = {v1.0.0},
  year         = {2026},
  doi          = {10.5281/zenodo.23682520}
}
```

## Abbreviations in the adjudication records

The two author adjudication records (Supplementary Files A and B, `tasks/adjudication/`) abbreviate
some quantities:

| Abbreviation | Quantity |
|---|---|
| `vf` | volume fraction |
| `rmin` | filter radius r_min |
| `Emin` | void stiffness E_min |
| `xmax`, `ymax` | right and top edges of the design domain |

## Environment

Python 3.10.18; numpy 2.2.6; scipy 1.15.3; matplotlib 3.10.7; pypardiso 0.4.7; pyvista 0.46.3. GPU
path: cupy 14.0.1 (CUDA 13), nvmath-python 1.0.0, nvidia-cudss-cu13 0.8.0.10; tested on an RTX 5090
(32 GB). The CPU paths do not need the GPU packages.

The parity tests (`tests/test_parity.py`, `tests/test_3d.py`) compare the solver with the earlier
AutoSiMP solver (https://github.com/nbbllxx0/AutoSiMP). Clone it and set `AUTOSIMP_DIR` to its folder;
the default is a sibling folder `AutoSiMP_full_implementation`.

## Run order (outputs in `results/`)

1. `python tests/test_parity.py`, `python tests/test_geometry_loads.py`, `python tests/test_3d.py`
2. `python experiments/e01_controlled_sweeps.py` (2-D controlled tracks)
3. `python experiments/e02_controlled_3d.py` (3-D tracks; run the first three; the 2x-mesh track is superseded by E02b refine)
4. `python experiments/e02b_more_3d.py tracks emin refine` (GPU)
5. `python experiments/e03_literature_tasks.py`, then `python experiments/a03_summarize_e03.py` and
   `python experiments/a07_lower_bound_screening.py`; for the sensitivity check repeat E03 and A03 with
   `LT_VARIANT=union`; `python experiments/a10_adjudication_agreement.py` (agreement between the two adjudications)
6. `python experiments/e04_verification_controls.py`
7. Language-model readings (optional): `python experiments/e05_llm_readings.py`, then `python experiments/a05_score_llm.py`
8. Blind re-annotation (optional): `python experiments/e06_codex_reannotation.py`, then
   `python experiments/a06_agreement.py` (repeat A05 and A06 with `LT_VARIANT=union` or `pre` for the other encodings)
9. Near-threshold, sensitivity and three-slot checks: `python experiments/e08_near_threshold.py`,
   `python experiments/e09_sensitivity_checks.py`, `python experiments/e10_three_slot.py`
10. Reviewer controls (below), then `python figures/make_figures.py`, `python v4/figures/make_figures_v2.py`
    and `python tables/make_tables.py`

Optimization runs are cached by a hash of (specification, start, settings); rerunning a step reuses
finished runs.

### Reviewer controls

- `a15_reviewer_replays.py` (output `results/a15/`) and its tables `a16_a15_tables.py`: tolerance sweep,
  zero-allowance robust baselines, local-reference gaps, frozen-design checks, silent-default attribution,
  question-order null, expected-answer rule, wall-clock.
- `a17`–`a23`: default-design checks, margins, midpoints, sub-sampling, robust norms, shared regions,
  near-tolerance extension.
- `a24`–`a28`: slot-type rules, common-pool rescoring and own-paper exclusion; optimized midpoint
  references; 2x refinement of every two-dimensional task; certified lower bounds; passive-region repair.
  `a25`–`a27` run new optimizations. Their Supplementary tables come from `a29_si_tables_v5.py`.
- `a30`–`a32` replay the stored tables only: the certified replay against the lower bounds of `a27`
  (`a30`), the reference-free screen and interaction rounds (`a31`), and the per-task question-order
  table (`a32`).
- `a33`–`a36` run new optimizations: bound-form min–max robust designs (`a33`), re-convergence of the
  references whose projected-gradient residual exceeds 0.1 (`a34`), the controlled-track policy replay
  and robust-design cost envelope (`a35`), and the full-MBB void-stiffness check (`a36`).

Each writes `results/a<NN>/`; `a29`, `a32` and `a35` also write their Supplementary tables to `v4/tables/`.

## Notes

- Losses are relative to the best known design for each reading. Losses above 10 can depend on the void
  stiffness `Emin`; E02b `emin` and A36 test this.
- E05 and E06 call the command-line clients `codex exec` (gpt-6.1-sol; the runs used Codex CLI 0.162.1,
  set `CODEX_EXE` to choose the binary) and `claude -p` (claude-opus-5-5) on the authors' own
  subscription sign-ins. No API keys are used or stored. Their outputs are included, so rerunning them
  is optional.
