# Literature screen v1: arXiv minimum-compliance TO examples

Frame: `arxiv_frame_20261022.json` (247 papers, query `all:"topology optimization" AND (all:compliance OR all:stiffness)`, retrieved 2026-10-22T20:08:54+00:00, API totalResults 255; kept first-submitted 2015-01-01 to 2026-10-22). Screened: first 60 papers in frozen order (sha256("20261022:" + id) ascending).
Full text read: 55 arXiv HTML, 5 arXiv PDF, 0 inaccessible.

## Counts

- Eligible: **47 / 60**. Ineligible: 13 (other: 10, not structural: 2, no numerical example: 1).
- Borderline eligibility calls (flagged `borderline: true`): 5.
- Dimension of primary example: 2-D 35, 3-D 12.
- Benchmark family: cantilever 18, MBB 11, L-bracket 1, bridge 2, Michell 2, other 2, custom 11.
- Ambiguous primary examples (text plus figure admit more than one reading): **24 / 47**.
- Field instances (8 fields x 47 examples = 376): figure-only 76, missing 76. Examples with at least one figure-only field: 34; with at least one missing field: 42.
- Restricted to geometry, supports, loads, volume fraction: examples with at least one figure-only field 32; with at least one missing field 7.
- Filter radius recorded as 'not applicable' (discrete truss/frame models, tagged missing): 5.

Source tag per field (eligible examples only):

| Field | text | figure | code_or_appendix | missing |
|---|---|---|---|---|
| geometry | 24 | 22 | 1 | 0 |
| supports | 19 | 26 | 2 | 0 |
| loads | 26 | 19 | 2 | 0 |
| passive_regions | 9 | 1 | 1 | 36 |
| volume_fraction | 38 | 2 | 0 | 7 |
| mesh | 38 | 4 | 0 | 5 |
| material | 36 | 1 | 0 | 10 |
| filter_radius | 28 | 1 | 0 | 18 |

## Screening rules applied

- Eligible: original paper with at least one numerical example of structural TO in linear elasticity, compliance (stiffness) objective, a volume constraint, and prescribed loads and supports. A mass constraint on a single material and a volume penalty in a loss were accepted as volume constraints. Additional constraints (stress, AM, buckling) were accepted and noted.
- Primary example: first numerical example in document order that meets eligibility. Where a paper reports only aggregate results over randomly generated task sets before any individual case, the first individual instance shown with an optimized design was taken.
- Source tag: `text` if stated in prose (incl. tables in the body); `code_or_appendix` if stated only in a code listing or appendix; `figure` if only visible in a figure or its caption; `missing` if not found. `missing` also covers fields that do not apply to the method (no passive region mentioned; no filter in phase-field, level-set, neural or truss methods); the value string says which.
- Family: MBB = simply supported or symmetric-half beam with a mid-span point load (incl. 3-point bending); bridge = supported span with distributed or deck loads; other = named benchmark outside the list; custom = application geometry or random task.
- Excerpts are verbatim from the arXiv HTML/PDF text (math as LaTeX alt text); `[...]` marks an omission.

## Process notes and limitations

- Full texts were fetched with `scripts/fetch_papers.py` (sequential, 3 s between arXiv requests, plain python-urllib user agent). Raw downloads were kept outside the repository and are not part of this deliverable; rerun the script to reproduce them.
- Problem-definition figures were downloaded one at a time and inspected visually when a field was not in prose; PDF-only papers were read from rendered pages where pdftotext lost symbols.
- The HTML-to-text converter first dropped display equations and code listings; it was fixed and all texts reconverted. Records with figure-tagged fields were rechecked against the recovered listings (one change: #19 supports moved to code_or_appendix; #12 supports/loads are in a body code listing).
- Positions 10-60 were screened by parallel copies of the same screening agent under the identical rule set above, then spot-checked (#12, #13, #19, #22, #24, #29, #47, #54, #57, #59); positions 1-9 were screened directly. Single-screener judgement: no second independent coder, no inter-rater agreement.
- Ambiguity and family assignments are judgement calls; `borderline: true` marks debatable eligibility.

## Per-paper table

Source codes in order geometry, supports, loads, passive, volume fraction, mesh, material, filter: t = text, f = figure, c = code/appendix, m = missing.

| # | arXiv id | Eligible / reason | Dim | Family | Sources | Amb. | Primary example / note |
|---|---|---|---|---|---|---|---|
| 1 | 2403.04937 | yes | 2 | L-bracket | `fffmmttt` | yes | Sec. 4 'Example designs', Fig. 4 (first individual problem instance with reported design; Figs. 2-3 are aggregate statistics over randomly generated problem sets) |
| 2 | 2503.21456 | no: other (borderline) | - | - | - | - | No fixed volume constraint: the abstract states 'volume fraction is left unconstrained' and Sec. 2 replaces it by a logarithmic volume-compliance growth rule (Carter-Hayes/mechanostat). Borderline: Sec. 6.1 grows volume toward a target fraction. |
| 3 | 2305.08771 | yes | 2 | other | `tffmtttt` | no | Sec. 5 / 5.1 (two-material case), externally pressurized arch, problem-definition Fig. 1(a); results Fig. 2 |
| 4 | 2502.01830 | yes | 2 | custom | `tffmmttm` | yes | Sec. 4.3, Fig. 8 row 1 (first individual task shown with designs; earlier results are aggregate over random task sets; Fig. 5 shows example BCs without results) |
| 5 | 1909.11320 | yes | 3 | cantilever | `fffmtttt` | yes | Sec. 6.1.1 (3D cantilever beam), Fig. 3 left |
| 6 | 2507.16519 | yes | 2 | cantilever | `tttmtttt` | no | Sec. 4.2, Example 1 Case 1; problem-definition Fig. 1(a); first results Sec. 4.2.1, Fig. 2 |
| 7 | 2508.19169 | yes | 2 | bridge | `fftttttm` | no | Sec. 8.1, Fig. 4 (problem), Fig. 5(a) configuration without AM filter or stress constraint |
| 8 | 2309.00396 | yes | 3 | custom | `tttttttm` | yes | Sec. 3.1 and 3.3, Fig. 2 (BCs); first mass limit 20%, Fig. 3 |
| 9 | 2010.10770 | yes | 2 | cantilever | `fttmtttm` | yes | Sec. 6.1 (cantilever beam with lattice structure), Fig. 5 problem setup; results Sec. 6.1.2, Fig. 7 |
| 10 | 2101.02973 | no: other | - | - | - | - | No compliance-objective example: Sec. 5.1 solves volume minimization with a compliance constraint, then buckling-load-factor maximization with compliance and volume constraints; Sec. 5.2 is volume minimization with compliance and BLF constraints. The code can solve volume-constrained minimum compliance (Sec. 2.1) but no such example is reported. |
| 11 | 2407.07288 | yes | 2 | custom | `fffmmtmt` | yes | Results, Fig. 10 row A, 'Baseline' column (first individual instance shown with an optimized design; earlier results are aggregate over 1000 random test samples; Fig. 3a is a random RL episode, not an optimized design) |
| 12 | 2605.28857 | yes | 2 | MBB | `fccmfmfm` | no | Sec. 4, bridge structure: Fig. 2 (left) initial setup, Fig. 3 (quadratic compliance column) |
| 13 | 2412.18441 | yes | 2 | cantilever | `fffmfftf` | no | Sec. 4 / 4.1, cantilever beam: problem Fig. 4(a); first solution Fig. 6(a) (mesh 100 x 50, vf 0.35, ls 2) |
| 14 | 2601.23269 | yes | 2 | MBB | `tffmtttt` | no | Sec. 5, half MBB beam, Fig. 3 (domain and BCs); dataset of 100 TO runs (DoE over volume fraction) |
| 15 | 2012.01359 | no: other | - | - | - | - | Material/microstructure design: periodic RVE with homogenized Young's modulus and Block-Floquet buckling strength objectives; no structure with prescribed loads and supports. |
| 16 | 2406.18833 | yes | 2 | cantilever | `fffmtftm` | no | Sec. 4.1 (truss optimization), Fig. 5(a) 6-member truss; results Fig. 6 |
| 17 | 2212.00964 | yes | 3 | custom | `fffttmmm` | yes | Sec. 3.2, three-hole bracket, Fig. 9 (the preceding thin-plate example, Fig. 7, uses a hyperelastic material and is not linear-elastic) |
| 18 | 2503.20915 | yes | 2 | cantilever | `fttmtttm` | no | Sec. 5.1 '21-elements frame structure', compliance minimization setting; Fig. 8(a) (Sec. 2.2 illustration problem skipped: weight minimization) |
| 19 | 2005.05436 | yes | 2 | MBB | `tctttttt` | no | Sec. 3, half MBB beam, Fig. 2 (default test case used in Secs. 3.1-3.4) |
| 20 | 2205.14832 | no: other | - | - | - | - | Explicit dynamic, elasto-plastic (crashworthiness/blast) problems with energy-absorption or damage objectives; no linear-elastic compliance example. |
| 21 | 2502.05899 | yes | 2 | bridge | `fffmtttt` | no | Sec. 5.1, Fig. 8(a) problem setting; Fig. 8(b) optimized without shielding condition (pure mean compliance + volume) |
| 22 | 2307.16521 | yes (borderline) | 3 | custom | `fftfmttm` | yes | Sec. 4.1-4.2, battery pack, Fig. 3 (geometry, BCs); first weight listed k = 1.0 (structural compliance only), results Fig. 5(c,f,i) |
| 23 | 2410.23295 | yes | 3 | custom | `tttttttm` | yes | Results 'Structures optimization' and 'Mechanical stiffness' (first experiment), set-up Fig. 6 right, results Fig. 7 |
| 24 | 2011.07732 | yes (borderline) | 2 | cantilever | `tftmmttm` | yes | Sec. 4.1 Example (I), problem setting Fig. 1; bilateral-contact comparison case Fig. 3 (first linear instance; the unilateral-contact runs of Fig. 2 precede it) |
| 25 | 1910.13002 | yes | 3 | Michell | `fftttttt` | no | Sec. 2.5, Michell cantilever (first of the four examples listed; Fig. 4); results Sec. 4.1 Table 2 row 1 |
| 26 | 2112.00648 | yes | 2 | MBB | `tffmttmt` | no | Sec. 3.2, MBB beam, problem-definition Fig. 4(a); first result Fig. 5 (truss basis, 2 classes) |
| 27 | 2505.02438 | yes | 2 | cantilever | `cttmtttt` | no | Sec. 4.2 (2D cantilever beam), Fig. 3; results Figs. 4-5 |
| 28 | 2608.19763 | yes (borderline) | 3 | custom | `fftmtmmt` | yes | Results 'Topology optimization of origami metamaterials', Fig. 4c; formulation in Methods |
| 29 | 2610.27378 | yes | 3 | custom | `tttttttt` | no | Sec. 5.5 companion study (compliance minimization, Eq. 64) on the frame of Sec. 5.3 / Fig. 4; results Fig. 17, Table 7. Earlier examples (Sec. 5.1-5.4) are volume minimization with DDAM constraints and are not eligible. |
| 30 | 2608.28513 | yes | 3 | MBB | `tttmtttt` | no | Sec. 4.1 (macroscale stage, 3-D MBB beam), Fig. 11; Table 2 |
| 31 | 2312.06378 | yes | 3 | custom | `fffmtttt` | yes | Sec. 5.1, case 1 (Fig. 6(a) top row); Table 1 case 1 |
| 32 | 2609.27685 | yes | 2 | custom | `fttmtttt` | yes | Sec. 4, pylon mid-plane design domain Fig. 1(b); first case M = 2 materials, Table 1(c) |
| 33 | 2008.08902 | no: other | - | - | - | - | Compliant-mechanism synthesis with geometric nonlinearity and hyperelastic material; objective is a least-squares error to target tissue strains, not compliance. |
| 34 | 2205.14780 | yes | 2 | cantilever | `ffcctttt` | no | Sec. 4.1 Cantilever model, Case (i); problem-definition Fig. 1(a) (PDF p. 15); code in Appendix A |
| 35 | 2004.07002 | yes | 2 | MBB | `tttmmftm` | no | Sec. 4.1.1 (hinge-supported beam, coarse discretization), Fig. 5 |
| 36 | 2105.04232 | yes | 2 | Michell | `ffftttmt` | yes | Sec. 4.2 Michell cantilever beam; problem-definition Fig. 9(a); first configuration Table 2 row 1 / Fig. 10(a) (V = 0.25, mu_min = 0.05) |
| 37 | 2107.04468 | no: no numerical example | - | - | - | - | Analytical treatment of non-convexity sources (penalization, filtering, continuation) in compliance minimization; the three figures illustrate convexity concepts only, no structural TO example with loads and supports. Paper type stated as 'Research paper', so not classed as review. |
| 38 | 1708.07364 | yes | 2 | cantilever | `tttmtttt` | yes | Sec. 4.1, Fig. 7(a) rectangular cantilever; reference design without self-supporting constraint Fig. 8(a) (Table 3 'Beam', C_ref) |
| 39 | 2308.06756 | yes | 2 | cantilever | `tttmtftt` | no | Sec. 4, Example (a) cantilever; problem-definition Fig. 1 (first panel); results Fig. 3 |
| 40 | 1612.04082 | yes | 3 | cantilever | `ttfmtttm` | yes | Sec. 4.1 Cantilever supports, configuration 1; problem-definition Fig. 2(A) (text cites it as 'Fig. 1(A, D)'); result Fig. 2(B) |
| 41 | 2103.02047 | yes | 3 | cantilever | `fttmtmmm` | yes | Sec. 4.1 Case 1: Cantilever beam; boundary conditions Fig. 3(a); result Fig. 3(b) |
| 42 | 2104.01965 | yes | 2 | cantilever | `fffmtttm` | no | Sec. 2.3, example (a) tip-loaded cantilever, Fig. 1(a) |
| 43 | 2511.14623 | yes | 2 | cantilever | `tttmtttt` | yes | Sec. 4.1.1, case (a) 2D cantilever beam; problem-definition Fig. 4(a); results Fig. 5 |
| 44 | 2406.00067 | no: other | - | - | - | - | Compliant-mechanism synthesis (path-generating, selective compliance) with geometric and material nonlinearities; objective is not structural compliance with a volume constraint. |
| 45 | 1910.05585 | yes | 2 | MBB | `fffmtttt` | no | Sec. 5.1, 2D MBB beam; problem definition Fig. 10 (full beam) and Fig. 11 (half model); results Figs. 12-13 |
| 46 | 2111.13875 | yes | 2 | other | `tttmtttt` | yes | Sec. 4.1.1, self-weight loadbearing arch, Fig. 4(a); first case CASE I (100 x 50 FEs, without constraint g2), Fig. 5(a) |
| 47 | 2002.01927 | yes | 2 | MBB | `tttmttmm` | yes | Results, 'Compliance minimization', first problem (5 x 5 design variables), Fig. 2a |
| 48 | 2305.04107 | yes | 2 | cantilever | `fffmtmmt` | yes | Sec. 4.1, 2D cantilever beam, Table 1 (target volume fraction 0.5), boundary-condition sketch in Table 1 'Boundary Conditions' column |
| 49 | 2605.02158 | yes | 2 | custom | `tffmmtmm` | yes | Sec. 5, Fig. 3 row 1 (first individual dataset instance shown with SIMP ground-truth design; Fig. 1 in Sec. 2 is a schematic illustration of a generic problem) |
| 50 | 2608.18308 | no: not structural | - | - | - | - | Photonic inverse design of silicon multimode interferometers (FDTD, optical figure of merit); 'compliance' refers to foundry design-rule compliance. |
| 51 | 2112.02506 | no: other | - | - | - | - | All three case studies (pinned, clamped, cantilever beams) minimize the frequency response under harmonic excitation over a frequency range (damped dynamic analysis), not static compliance. |
| 52 | 2108.01616 | yes | 2 | cantilever | `tftmtttt` | no | Sec. 4.1 (cantilever beam), Fig. 4(a) configuration; deterministic (non-robust) TO result Fig. 4(b) |
| 53 | 2502.02052 | no: other | - | - | - | - | All examples use finite strain elastoplasticity (dampers, hyperelastic-elastoplastic beams, crash bumpers, profiled sheets) with energy/load-capacity objectives; no linear-elastic compliance example. |
| 54 | 2411.19421 | yes | 2 | MBB | `tttmttmt` | no | Sec. 3.1, Problem 1: 2D MBB beam (no separate problem-definition figure; results Figs. 2-4, Tables 1-2) |
| 55 | 2111.10439 | yes | 2 | MBB | `tftmtttt` | no | Sec. 3.1 (MBB beam), Fig. 6(a) boundary conditions; non-modular TO design Fig. 6(c) |
| 56 | 2008.07487 | yes | 2 | MBB | `tffmtttm` | yes | Sec. 4.1 (compliance optimization for MBB design), Fig. 7 (PDF p. 9) |
| 57 | 2509.10277 | no: other (borderline) | - | - | - | - | Main examples are mechanical-cloak metamaterial design (displacement-matching target). The only stiffness-oriented examples (Fig. 9: 'Bridge' three-point bending and cantilever, Vf = 80%) use a one-shot heuristic mapping of a single stress field to reaction-diffusion parameters, without an optimization loop or an optimization formulation. Borderline: the paper calls this structural optimization that reduces deformation energy at fixed fill fraction, and the BCs are stated in Methods ('Stress-driven parameter mapping'). |
| 58 | 2607.02352 | no: not structural | - | - | - | - | Electromagnetic (plasmonic metasurface) topology optimization maximizing optical trapping force computed with the Maxwell stress tensor. |
| 59 | 2605.19110 | yes | 2 | cantilever | `tttttttt` | yes | Sec. 3.5, Fig. 2 (cantilever-with-two-voids benchmark, first problem shown with designs); definition in Table 3, ID 3 (Sec. 4.1) |
| 60 | 2306.06585 | no: other | - | - | - | - | Inverse design of geometrically nonlinear springs/unit cells for a target polynomial force-displacement curve; no linear-elastic compliance-minimization example. |
