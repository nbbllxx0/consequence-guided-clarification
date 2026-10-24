# Literature screen v2: arXiv minimum-compliance TO examples, positions 61-150

Frame: `arxiv_frame_20261022.json` (247 papers, query `all:"topology optimization" AND (all:compliance OR all:stiffness)`, retrieved 2026-10-22T20:08:54+00:00; frozen order sha256("20261022:" + id) ascending). This file screens positions 61-150; positions 1-60 are in `literature_screen_v1.json` / `.md` (not edited).
Full text read (61-150): 78 arXiv HTML, 12 arXiv PDF, 0 inaccessible.

## Counts, positions 61-150

- Eligible: **72 / 90**. Ineligible: 18 (other: 15, not structural: 2, no numerical example: 1).
- Borderline eligibility calls (flagged `borderline: true`): 14.
- Dimension of primary example: 2-D 66, 3-D 6.
- Benchmark family: cantilever 42, MBB 13, L-bracket 1, bridge 1, Michell 1, other 3, custom 11.
- Ambiguous primary examples (text plus figure admit more than one reading): **27 / 72**.
- In scope for a structured-grid compliance solver: **58 / 72** (2-D 53, 3-D 5).
- In scope and ambiguous: **22** (2-D 20, 3-D 2); ambiguity slots 84, of which 25 only scale the compliance value ('[scale only]').
- Field instances (8 fields x 72 examples = 576): figure-only 101, missing 116. Examples with at least one figure-only field: 48; with at least one missing field: 63.
- Restricted to geometry, supports, loads, volume fraction: examples with at least one figure-only field 48; with at least one missing field 4.
- Filter radius recorded as 'not applicable' (discrete truss/frame models, tagged missing): 5.

Source tag per field (eligible examples only):

| Field | text | figure | code_or_appendix | missing |
|---|---|---|---|---|
| geometry | 46 | 23 | 3 | 0 |
| supports | 31 | 37 | 4 | 0 |
| loads | 43 | 25 | 3 | 1 |
| passive_regions | 8 | 0 | 3 | 61 |
| volume_fraction | 56 | 9 | 3 | 4 |
| mesh | 61 | 3 | 2 | 6 |
| material | 56 | 2 | 4 | 10 |
| filter_radius | 32 | 2 | 4 | 34 |

## Combined counts, positions 1-150 (v1 records + v1 in-scope supplement below + v2 records)

- Eligible: **119 / 150**. Ineligible: 31 (other: 25, not structural: 4, no numerical example: 2).
- Borderline eligibility calls (flagged `borderline: true`): 19.
- Dimension of primary example: 2-D 101, 3-D 18.
- Benchmark family: cantilever 60, MBB 24, L-bracket 2, bridge 3, Michell 3, other 5, custom 22.
- Ambiguous primary examples (text plus figure admit more than one reading): **51 / 119**.
- In scope for a structured-grid compliance solver: **90 / 119** (2-D 80, 3-D 10).
- In scope and ambiguous: **36** (2-D 31, 3-D 5); ambiguity slots 140, of which 41 only scale the compliance value ('[scale only]').
- Field instances (8 fields x 119 examples = 952): figure-only 177, missing 192. Examples with at least one figure-only field: 82; with at least one missing field: 105.
- Restricted to geometry, supports, loads, volume fraction: examples with at least one figure-only field 80; with at least one missing field 11.
- Filter radius recorded as 'not applicable' (discrete truss/frame models, tagged missing): 10.

Source tag per field (eligible examples only):

| Field | text | figure | code_or_appendix | missing |
|---|---|---|---|---|
| geometry | 70 | 45 | 4 | 0 |
| supports | 50 | 63 | 6 | 0 |
| loads | 69 | 44 | 5 | 1 |
| passive_regions | 17 | 1 | 4 | 97 |
| volume_fraction | 94 | 11 | 3 | 11 |
| mesh | 99 | 7 | 2 | 11 |
| material | 92 | 3 | 4 | 20 |
| filter_radius | 60 | 3 | 4 | 52 |

### In-scope ambiguous 3-D examples, positions 1-150 (5)

- #5 1909.11320 (cantilever; Sec. 6.1.1 (3D cantilever beam), Fig. 3 left)
  - loaded region on end face: arrows drawn along bottom edge with traction units N/m^2; edge line vs strip width not stated (Fig. 3 left)
- #23 2410.23295 (custom; Results 'Structures optimization' and 'Mechanical stiffness' (first experiment), set-up Fig. 6 right, results Fig. 7)
  - supported set on base: text says 'points at the base' are fixed; all base-face nodes or a subset not stated (Results 'Structures optimization' para 1; Fig. 6 right)
  - top thin shell: thickness, stiffness and whether it is a non-design solid layer not stated (same para; Fig. 6 right)
  - load magnitude and distribution: 'distributed forces' through the shell, value not stated (same para; Fig. 6 right) [scale only]
- #40 1612.04082 (cantilever; Sec. 4.1 Cantilever supports, configuration 1; problem-definition Fig. 2(A) (text cites it as 'Fig. 1(A, D)'); result Fig. 2(B))
  - load line height on loaded face: dotted line drawn near mid-height, value not stated (Fig. 2(A))
  - load form: line load vs strip traction not stated (Fig. 2(A))
  - load magnitude: not stated (Fig. 2(A)) [scale only]
- #135 2402.12076 (MBB; Sec. 5.4, 3D beam three-point bending, design domain Fig. 9(a); first result Fig. 9(b) (porous unit of Table 2(a)); formulation Sec. 4.3 Eq. (27))
  - support strip width at the bottom ends: 'bottom sides are fixed', strips drawn at both ends, width not stated (Fig. 9 caption; Fig. 9(a))
  - loaded region at top mid-span: 'uniformly applied at the center of the beam top', drawn as arrows along a line across the depth, line vs strip width not stated (Fig. 9 caption; Fig. 9(a))
  - design-domain dimensions: only the manufactured size 120 x 48 x 48 mm is stated, FE domain size not given separately (Sec. 5.4 para 2; Fig. 9(a))
  - base Poisson's ratio: not stated (Sec. 4.3)
  - load magnitude: not stated (Sec. 5.4; Fig. 9(a)) [scale only]
  - base Young's modulus: not stated (Sec. 4.3) [scale only]
- #146 2604.03276 (custom; Supplementary Note A.14, nanopillar designed by FEM-TO (top3d-based continuum SIMP), design Fig. S18 (left); the main-text examples (Nano-TO nanocantilevers and nanopillar) are atomistic EAM models and were not taken as linear-elastic continuum TO)
  - load type at top-face centre: said to be 'identical' to the atomistic case, which prescribes a vertical displacement; force vs prescribed displacement in FEM-TO not stated (Supplementary Note A.14 para 1; Methods 'Atomistic modeling' para 4)
  - load extent: 'center of the top surface', single node vs patch not stated (main text 'Design of nanopillars using Nano-TO' para 1; Supplementary Note A.14)
  - load magnitude: not stated for FEM-TO (Supplementary Note A.14) [scale only]

## Screening rules applied

Identical to v1 (eligibility, primary example, source tags, family mapping, 60-word excerpts); repeated here for completeness.

- Eligible: original paper with at least one numerical example of structural TO in linear elasticity, compliance (stiffness) objective, a volume constraint, and prescribed loads and supports. A mass constraint on a single material and a volume penalty in a loss were accepted as volume constraints. Additional constraints (stress, AM, buckling) were accepted and noted.
- Primary example: first numerical example in document order that meets eligibility. Where a paper reports only aggregate results over randomly generated task sets before any individual case, the first individual instance shown with an optimized design was taken.
- Source tag: `text` if stated in prose (incl. tables in the body); `code_or_appendix` if stated only in a code listing or appendix; `figure` if only visible in a figure or its caption; `missing` if not found. `missing` also covers fields that do not apply to the method (no passive region mentioned; no filter in phase-field, level-set, neural or truss methods); the value string says which.
- Family: MBB = simply supported or symmetric-half beam with a mid-span point load (incl. 3-point bending); bridge = supported span with distributed or deck loads; other = named benchmark outside the list; custom = application geometry or random task.
- Excerpts are verbatim from the arXiv HTML/PDF text (math as LaTeX alt text); `[...]` marks an omission.
- New field `in_scope_structured_grid` (eligible records only): true if the primary example's boundary-value problem can be rebuilt on a structured-grid, single-material, isotropic linear-elastic compliance solver: rectangle/box domain, optionally minus element-removed holes, notches or L-cuts (staircase approximation of curved holes accepted) and with fixed solid/void element sets; supports on nodes, edges or faces; design-independent point, line or patch loads (several loads or load cases allowed); volume or single-material mass constraint. False for scanned or CAD/free-form geometry, non-rectangular outer domains, lattice/truss/frame/bar-and-hinge models, shells/plates, self-weight-only or other design-dependent loads, thermal or other multiphysics coupling, geometric/material nonlinearity or contact, dynamics, two or more solid materials, anisotropic base material, and loads applied through rigid multipoint ties. The design parametrisation (SIMP, level set, phase field, homogenisation, components, neural, microstructure grading) does not affect the call. The one-line reason is in `notes` ('In-scope: ...').
- New field `ambiguity_slots` (eligible records only): non-empty exactly for in-scope ambiguous examples; one string per underdetermined quantity, '<quantity>: <reason> (<evidence location>)'. Quantities that only scale the compliance value and not the optimal layout (a single load's magnitude, Young's modulus) carry the suffix '[scale only]'.

## Process notes and limitations

- Full texts were fetched with `scripts/fetch_papers.py` (sequential, 3 s between arXiv requests, plain python-urllib user agent, no e-mail). Raw downloads were kept outside the repository; rerun the script to reproduce them.
- Problem-definition figures were downloaded one at a time through the same script and inspected visually when a field was not in prose; PDF-only papers were read from rendered pages where pdftotext lost symbols.
- Positions 61-150 were screened by six copies of the same screening agent (blocks 61-75, 76-90, 91-105, 106-120, 121-135, 136-150, run one after another) under the identical rule set, then spot-checked against the source text by the coordinating screener: #62, #70, #71, #87, #90, #98, #112, #113, #115, #118, #128, #135, #139, #146 (14 records). Corrections: #70 set not ambiguous (only the mesh of that case and the load magnitude are unstated, which v1 did not count as ambiguity); #90 changed from eligible to ineligible (other, borderline) because the loads and supports of its TO problem are never stated; #135 discretization slot removed. All eligible excerpts were machine-checked as verbatim (whitespace-normalised) against the downloaded text. #118 (2403.02711): the current arXiv version v2 is withdrawn ('critical flaw in the proposed methodology'); the v1 PDF was read. For #68, #105 and #132 the arXiv PDF was downloaded once because a figure, the supplement or the appendix code was missing from the HTML.
- The in-scope call and the slots for positions 1-60 were added in this round from the v1 records and re-reads of the source text for the in-scope ambiguous 3-D cases (#5, #23, #40) and #29; they are listed in the supplement table below because `literature_screen_v1.json` was not edited.
- Ambiguity, family and in-scope assignments are judgement calls by a single screener; no second independent coder, no inter-rater agreement. `borderline: true` marks debatable eligibility.

## Per-paper table, positions 61-150

Source codes in order geometry, supports, loads, passive, volume fraction, mesh, material, filter: t = text, f = figure, c = code/appendix, m = missing. In-scope = `in_scope_structured_grid`; Slots = number of ambiguity slots (full text in the JSON).

| # | arXiv id | Eligible / reason | Dim | Family | Sources | Amb. | In-scope | Slots | Primary example / note |
|---|---|---|---|---|---|---|---|---|---|
| 61 | 2101.03286 | yes | 2 | MBB | `tttmtttm` | no | yes | 0 | Sec. 4.1 MBB beam, Fig. 5 (boundary conditions); first case one hidden layer of 8 neurons, result Fig. 8(a) |
| 62 | 2211.04249 | yes (borderline) | 2 | MBB | `tttmtmtm` | no | yes | 0 | Sec. 2.1, Example 2.1 (MBB beam), set-up Fig. 1; two local minima Fig. 2 (results attributed to [35, Sec. 4.6]) |
| 63 | 2404.12244 | yes | 2 | MBB | `tffmttmt` | yes | yes | 4 | Sec. 7.1.1 Mid-load problem, problem Fig. 6(a); target (top88) designs Table 1, Fig. 8(b) (V_f = 0.25) |
| 64 | 2208.10501 | yes | 2 | cantilever | `tttmtttm` | no | yes | 0 | Sec. 4.1 Central loaded cantilever (CLC); fixed-mesh level-set run, Fig. 1 (LEVITY run Fig. 2) |
| 65 | 2412.07099 | yes | 2 | custom | `fttmtftm` | no | no | 0 | Sec. 4.1, truss structure #1, Fig. 4(a); results Fig. 6(a) |
| 66 | 1712.03385 | yes | 2 | cantilever | `tftmtttm` | no | no | 0 | Sec. 6.2 Example (I), (N_X, N_Y) = (5,2), problem setting Fig. 3; conventional compliance minimization without cardinality constraint Fig. 4(a) (illustration of Fig. 2 in Sec. 5 skipped: no problem data given) |
| 67 | 2606.10509 | yes | 2 | cantilever | `fffmfftm` | no | yes | 0 | Sec. 4.1, Fig. 2 (representative cantilever beam, Q4, 100 x 20 elements, v_mat = 0.5, p = 3); settings Sec. 4.2 |
| 68 | 2505.04353 | yes | 2 | L-bracket | `fttttttt` | no | yes | 0 | Sec. 3 / 3.1, L-beam domain Fig. 11 (HTML; Fig. 10 in the PDF); first variant CV (compliance minimization with volume constraint), design Fig. 12(a) |
| 69 | 1801.05463 | yes | 2 | custom | `ttmmmtmm` | yes | yes | 8 | Sec. 3.4, Fig. 10 row 1, optimized structure columns (first individual test instance shown with a top88 design; dataset of 100,000 randomized cases, Sec. 3.1; Fig. 6 shows BC encoding only) |
| 70 | 2305.04406 | yes | 2 | cantilever | `tffmtmtm` | no | yes | 0 | Sec. 3.1 Validation, mid-cantilever beam (Fig. 7) with l_x = l_y = 2, v_f* = 0.5, one polygon S = 16; result Fig. 8 |
| 71 | 2607.26382 | yes (borderline) | 3 | cantilever | `tttmtttc` | no | yes | 0 | Sec. 4.1.2, 40-iteration optimization of the 64k-element cantilever (Table 1 'Cantilever', Fig. 1(a)); histories Fig. 3(a,b), Table 5 (Sec. 4.1.1 frozen-state solves skipped: no optimization) |
| 72 | 2605.19441 | yes | 2 | cantilever | `fttmftfm` | no | yes | 0 | Sec. 4, Cantilever Beam (Fig. 3), domain 32 x 20; Q1 result first panel of Fig. 4, Table 1 |
| 73 | 2607.07682 | yes | 2 | MBB | `tffmttmt` | yes | yes | 5 | Sec. V-A, MBB beam application (Fig. 2B), 192 x 64, volume fraction 0.4; designs SI Sec. 2.4, Fig. S11 (the first application, nanophotonic beam deflector, is not structural) |
| 74 | 2310.02069 | yes | 2 | cantilever | `tffmttmt` | yes | yes | 5 | Sec. 2.1 / 3.1, cantilever beam (Fig. 1(a)); first design shown is the top88 target at V_f = 0.20, Fig. 3(b); CNN results Table 1 |
| 75 | 2108.03654 | yes (borderline) | 2 | cantilever | `fftmtttt` | yes | yes | 1 | Sec. 6.1.1 mean compliance minimization (low rank loads, R = 10) of the 2D cantilever of Sec. 3.1 / Fig. 1; exact-method design Fig. 5(a), Table 5 |
| 76 | 2003.01215 | yes | 2 | cantilever | `tttmttmt` | no | yes | 0 | Sec. 4.2.1 '2D Beam with a Concentrated Load', Fig. 9 (first linear-elastic example; nonlinear neo-Hookean examples follow in Sec. 4.3) |
| 77 | 2608.22606 | yes | 2 | custom | `ttfmftmm` | yes | yes | 5 | Sec. 5.1, Fig. 5(c) 'SIMP reference' (first individual problem shown with an optimized design; dataset of 300 random SIMP problems, Sec. 4) |
| 78 | 2603.09780 | yes | 2 | cantilever | `fffmtttt` | yes | yes | 2 | Sec. 2, cantilever benchmark of Fig. 1 with Table 1 parameters; first result Fig. 2 (VTTO design, compared with SIMP) |
| 79 | 2603.25099 | yes | 2 | cantilever | `tttmtttt` | yes | yes | 5 | Sec. 3.5 'Benchmark problems' and Sec. 4.1, cantilever beam, 120 x 60 'Long' preset (Table 4); results Table 5, Fig. 6 top row |
| 80 | 2608.17963 | yes | 2 | MBB | `fffmtttt` | no | no | 0 | Sec. 5 / 5.1, three-phase 2D half-MBB beam (Fig. 4(a)), first volume-fraction combination (v_E=2 = 0.1, v_E=1 = 0.3), negative-mapping result in Table 1 (PDF p. 16) |
| 81 | 2503.00199 | no: not structural | - | - | - | - | - | - | Photonic inverse design (modal multiplexer, mode converter, polarization rotator, grating reflector) with optical transmission objectives; 'compliance' refers to foundry design-rule (DRC) compliance. |
| 82 | 2408.03804 | no: other | - | - | - | - | - | - | FFT-based homogenization methods paper; the only TO example (Sec. 4.4.2) is microstructure design maximizing the homogenized shear modulus of a periodic unit cell under macroscopic strain, with no structure under prescribed loads and supports. Other examples are hyperelastic/elastoplastic homogenization and uncertainty quantification. |
| 83 | 2103.08347 | yes | 2 | cantilever | `tttmtttm` | no | yes | 0 | Sec. 3.1 cantilever test case (Fig. 6, Table 1); first designs Sec. 3.2, Fig. 8 (v_Frac = 0.33, 12 elements per unit length) |
| 84 | 2505.09373 | yes | 2 | other | `tttmtttm` | no | no | 0 | Sec. 4.1 compressed column, truss model, linear compliance with volume constraint and no buckling constraint (ell = 0), Fig. 4(a) left; initial ground structure Fig. 3(a) |
| 85 | 2307.16473 | yes (borderline) | 2 | cantilever | `tftmtttm` | yes | no | 0 | Sec. 4, 3 x 2 grid truss ground structure (Fig. 1); first optimal design shown Fig. 4(a) (r = 0.5) |
| 86 | 2504.08233 | yes | 2 | MBB | `tttmtttt` | no | yes | 0 | Sec. 4.1 half MBB beam (problem Fig. 3(a)); first result Fig. 4(a), 60 x 20 B-spline IGA mesh |
| 87 | 2307.09518 | yes | 3 | Michell | `tttttttt` | no | yes | 0 | Sec. 5.1 Michell cantilever, N_a = 0 multiscale optimization (Table 1 row 1, Fig. 6(a)); problem Fig. 5(a) |
| 88 | 2204.07333 | yes | 2 | cantilever | `fffttttt` | no | yes | 0 | Sec. 1.1 reference (robust, no overhang constraint) cantilever, domain Fig. 2(a); result Fig. 5 (topCbeam(200,100,0.4,1.0,6.1)). The intro Fig. 2(b) overhang-constrained illustration is not used: its settings are not given |
| 89 | 2606.26643 | no: other | - | - | - | - | - | - | Robot hardware design paper; the only TO (Sec. IV) minimizes component mass subject to lower bounds on natural frequencies (Altair OptiStruct level-set), not compliance with a volume constraint; stiffness and stresses were only checked afterwards by FE verification. |
| 90 | 1907.07860 | no: other (borderline) | - | - | - | - | - | - | No prescribed loads and supports are reported for the topology optimization: Sec. II states only 'the principal direction of loading' and Fig. 1 shows result images; domain size, area-fraction value, mesh and material are also not stated (the only stated BCs, top/bottom compression, belong to the later beam-element fracture models). Objective is a weighted sum (compliance 0.99999, perimeter 1e-5 for set A). Borderline: compliance-dominated SIMP with an area constraint, eligible if the unreported BCs were accepted (screener's first call; changed in spot-check). |
| 91 | 2112.02030 | yes | 2 | cantilever | `fftmtttm` | no | no | 0 | Sec. 3.1 Case Study 1, first run without stress constraints (Eq. (1), V_f = 0.25); geometry Fig. 1; result Fig. 2(a) |
| 92 | 2609.25976 | yes | 2 | cantilever | `fttmmttt` | yes | yes | 5 | Sec. 2.1 / Sec. 4, cantilever beam of Fig. 1; first result Table 2 row M = 1, extended SIMP column (single candidate material) |
| 93 | 2504.00292 | yes | 2 | custom | `fffmtttm` | yes | no | 0 | Sec. 3, Fig. 6(b): gripper (part 1 of the gripper-and-two-cams assembly of Fig. 1(a)) optimized for compliance only, without the collision constraint (lambda_g = 0); boundary conditions given later in Sec. 4.3, Fig. 20(a) |
| 94 | 1906.05549 | no: other | - | - | - | - | - | - | Only optimization problem is minimum-weight (volume) truss ground-structure design of the internal reinforcement of a composite hollow beam, with a lower bound on the fundamental free-vibration eigenfrequency and an upper bound on compliance of the compression-molding load case (linear SDP); no compliance-objective example. |
| 95 | 2203.08110 | yes | 2 | cantilever | `tffmtttt` | no | yes | 0 | Sec. 4.1 2D cantilever beam, problem Fig. 4(a), Tables 1-2; standard reference design (formulation (1), no AM model) Fig. 5 |
| 96 | 2602.13856 | yes | 2 | cantilever | `tttmtttt` | no | yes | 0 | Sec. 4.1 short beam example, Fig. 4(a) model; result without topology control Fig. 4(b)-(c) |
| 97 | 2003.13751 | yes | 2 | cantilever | `tttmtttm` | no | yes | 0 | Sec. 3.1 cantilever beam, Fig. 4 problem; first result Fig. 5, IGFEM column, first row (21 x 11 node grid) |
| 98 | 2009.06245 | yes | 2 | cantilever | `tftmfttt` | yes | yes | 5 | Sec. 3.3, Fig. 7(a) (first individual optimized design, volume fraction 0.3; PDF p. 14); problem class defined in Sec. 4.1, Fig. 9 (PDF p. 15); Table 1 lists further SIMP benchmark designs |
| 99 | 2107.04123 | no: other | - | - | - | - | - | - | Microstructure (periodic unit cell) design in an FFT homogenization solver: the objective is the least-squares difference between the average stress and a target stress (target effective shear modulus, later auxetic targets) under imposed average strains, with a phase-field interface penalty and no volume constraint; no structure with prescribed loads and supports and no compliance objective. |
| 100 | 1608.06654 | no: other (borderline) | - | - | - | - | - | - | All examples use an elasto-plastic (von Mises, hardening) path-dependent analysis under a prescribed displacement and maximize the end-compliance (load-bearing capacity), with volume and plastic-strain constraints; no linear-elastic compliance example. Borderline: the reference design of Sec. 5.1.1 (L-bracket, 150 x 150 mesh, 35% volume, end-compliance with volume constraint only) is stated to coincide with the linear-elastic minimum-compliance layout. |
| 101 | 2504.14892 | yes | 2 | custom | `tffmtttm` | yes | yes | 3 | Sec. 4.1.1, asymmetrically loaded square plate, Fig. 6(a); first result Fig. 7 (standard wave equation, beta = 2.0) |
| 102 | 2510.07280 | yes | 2 | MBB | `tttmtttm` | no | yes | 0 | Sec. II.2, Fig. 2: classical SIMP solution of the half-MBB problem on 9 x 9 elements, V0 = 1/2 (first optimized design; the quantum experiments of Sec. IV use 2 x 2 and 3 x 3 domains of the same setup) |
| 103 | 2601.04003 | yes (borderline) | 2 | bridge | `tttmtttm` | no | yes | 0 | Sec. 6 Numerical Results (single example), domain Fig. 4; final design Fig. 5 at t = 1 |
| 104 | 2301.11531 | yes | 2 | MBB | `fftmtttt` | no | yes | 0 | Sec. IV-B minimum compliance problem, Fig. 2 setup; first run 60 x 20 resolution, Table II (GBD-Splitting-Direct column; no design image shown for this resolution). Sec. IV-A toy MILP skipped (not a TO problem) |
| 105 | 2102.10782 | yes | 2 | cantilever | `cccmcttm` | no | yes | 0 | Sec. 5.1, Fig. 3 'Short Beam' (first of four 2D comparison problems), Table 1 row ShortBeam; definition in Supplementary Material Sec. 3 (appended to the arXiv PDF) |
| 106 | 2308.06734 | yes | 2 | cantilever | `tttmftff` | yes | yes | 1 | Sec. 2.1, cantilever plate, Fig. 2(a) problem; first result Fig. 2(b) (V_f = 0.7). Same problem re-run in Sec. 4.1 / Fig. 12 |
| 107 | 2106.13652 | yes | 2 | cantilever | `tftmtttt` | no | yes | 0 | Sec. 5.1 Example 1, cantilever beam in square design domain, Fig. 9; Table 1 (800 x 800 design variables, 88-line reference and FE-CNN runs). Sec. 4.1 dataset samples (Fig. 8) are training data, not results |
| 108 | 1807.10787 | yes | 2 | cantilever | `tftmmtmm` | yes | yes | 8 | Sec. 5.2 Case 1, sample solution Fig. 1(a) (first individual instance shown with a design; Fig. 3 results are aggregate over random test loads; Fig. 4 shows test loads 0.3pi-0.55pi) |
| 109 | 2511.13905 | yes | 2 | cantilever | `tffmtttt` | no | yes | 0 | Sec. 4.1.1 volume-constrained minimum compliance on the standard cantilever (Fig. 1 bottom-left); first results Appendix 7.5.1, Fig. 7 (coarse 128 x 64 mesh) |
| 110 | 2507.15693 | no: other (borderline) | - | - | - | - | - | - | Robot-arm hardware paper. Sec. III-C applies Ansys Workbench topology optimization to the upper arm and forearm 'to reduce structural mass without compromising load-bearing performance'; the objective, the constraint, the supports and the load values are not stated (loads described only as torsional, payload and self-weight). Borderline: the reported retained-mass percentages (about 53% and 63.88%) are consistent with a mass-retention constraint, but a compliance objective is not stated. |
| 111 | 1609.03099 | yes | 2 | other | `ftfmttmm` | no | no | 0 | Sec. 3.1, three-bar truss under 9 load cases (damping-scheme illustration), Fig. 1; results Fig. 2, Table 1 (standard GSM column) |
| 112 | 2605.04735 | yes | 3 | cantilever | `tttmtttt` | no | yes | 0 | Sec. 4.2, cantilever beam with corner supports, Fig. 2 (setup); results Table 2, Fig. 3 (Fig. 1 is a 2-D pipeline illustration without a defined problem) |
| 113 | 2609.38089 | no: other (borderline) | - | - | - | - | - | - | All examples (deck panel at 100 Hz, thruster foundation frame at 18 Hz and 300 Hz) minimize a mixed objective dominated by harmonic active input power (frequency-domain dynamics, w_AIP = 0.9 or 0.8) with static compliance only as a regularizing term (weight 0.1 or 0.2), plus optional stress and grayness terms; no example has a pure static compliance objective. Borderline: the static-compliance term and the volume fraction constraint are present in every run. |
| 114 | 2508.05624 | yes | 2 | cantilever | `fffmmttt` | yes | yes | 3 | Sec. 2, Fig. 1 (first individual problem shown with an optimized design: left-clamped square with corner load). Alternative reading: first generated sample Fig. 6(a) row 1 (VF 0.5) in Sec. 6.2 |
| 115 | 2210.11477 | yes (borderline) | 2 | custom | `fttttttt` | yes | yes | 2 | Sec. 3.1 uni-axial compression, Fig. 5 (domain); singlescale SIMP run with omega = 1 (pure compliance), reported as the compliance end of the Pareto front in Fig. 8 (first design figure, Fig. 6, uses omega = 0.5) |
| 116 | 2603.13063 | no: other | - | - | - | - | - | - | Contact-mechanics modelling paper (third medium regularization by deformation-gradient averaging). All four examples (C-shape, closed box, constrained buckling with self-contact, configurational forces) are finite-strain hyperelastic forward simulations with contact; no topology optimization example and no compliance objective. |
| 117 | 2209.09330 | no: other | - | - | - | - | - | - | Coupled aero-structural wing shape and topology optimization: every example minimizes cruise drag subject to a lift >= weight + payload constraint and upper bounds on cruise and takeoff compliance (compliance is a constraint, not the objective; no volume constraint, weight enters the lift constraint). |
| 118 | 2403.02711 | yes | 2 | cantilever | `fffmtttm` | no | yes | 0 | Sec. 7.1, 2-D cantilever beam, Fig. 4 (problem); reference run without constraints Fig. 5(a) (J_v ref = 2.52). Read from arXiv v1 PDF; current v2 is withdrawn |
| 119 | 2410.14342 | yes | 2 | cantilever | `tftmfttm` | no | yes | 0 | Sec. 4.1, Fig. 4 Problem (1): cantilever beam with load at the right bottom tip (V_f = 0.6); DPNN-TO and SIMP 88-line results |
| 120 | 2610.16051 | yes | 2 | custom | `tffmftcm` | yes | yes | 4 | Sec. 4.2, Fig. 5 row 1: OAT benchmark test problem 1961 at 256^2 (target 0.44), classical SIMP-OC designs (first individual instance shown with designs; Figs. 3-4 are aggregate timings) |
| 121 | 2309.12012 | no: other (borderline) | - | - | - | - | - | - | Proposed method minimizes the standard deviations of strain-energy-like variables by updating orthotropic elastic properties, explicitly with no volume constraint ('no constraint needs to be imposed (such as maximum volume)'). The only volume-constrained runs are Altair OptiStruct SIMP baselines (vf 0.5, p = 1) used for comparison on the four 100 mm cube load cases; their objective is not stated in the paper. Borderline: the OptiStruct baselines are presumably minimum compliance. |
| 122 | 2501.15337 | no: other | - | - | - | - | - | - | Finite-strain robust TO of hyperelastic (regularized neo-Hookean) structures: all examples (compression block, clamped beam, pinned column), including the deterministic reference designs, minimize end-compliance at finite deformation; no linear-elastic compliance example. |
| 123 | 1809.05300 | yes | 2 | cantilever | `tttttttt` | no | yes | 0 | Sec. 3 'Numerical example', configuration of Fig. 2(a); first design = compliance design without buckling constraint (P_c = 0, f = 0.2), Fig. 2(b) / Table 1 row 1. Sec. 2.1 compressed column is an analysis-only accuracy check, not an optimization |
| 124 | 2608.29146 | no: other | - | - | - | - | - | - | Robot-arm lightweighting: every reported topology optimization minimizes weight subject to end-deformation (stiffness) constraints or assigned strain-energy targets (global optimization A.1, part-level B.2, method results C.1/D.1, robotic arm in Sec. 4). Compliance minimization with a mass-reduction constraint is mentioned only as 'a common practice', not run. |
| 125 | 2610.12922 | yes | 2 | cantilever | `tttmtttm` | no | yes | 0 | Sec. 4.1, Example 4.1 (Cantilever: 2D), domain Fig. 2 (left); results Fig. 3 |
| 126 | 2609.27216 | yes | 2 | cantilever | `tffmtttt` | no | yes | 0 | Sec. 3.2, 2D compliance optimization, cantilever beam at 128 x 64 (Fig. 8, OC / KATO / KATOsuper rows); domain and BCs in Fig. 6 (middle panel), parameters Table 4 |
| 127 | 2107.04017 | yes | 2 | cantilever | `tttmtttt` | no | yes | 0 | Sec. 3.1, 2D cantilever beam, Fig. 5 (PDF p. 9); reference design without machining constraints Fig. 6 (compliance 50.05) |
| 128 | 2607.22833 | yes | 2 | cantilever | `tftmtttt` | yes | yes | 1 | Sec. 4.1, structural cantilever without thermal load: baseline design minimizing initial elastic compliance J_el = f^T u0 (Fig. 3, 'Design under Static Elasticity'); the creep-aware design in the same figure is not eligible (nonlinear Norton creep) |
| 129 | 2603.22889 | yes | 2 | cantilever | `fffmffmf` | yes | yes | 4 | Introduction, 2D cantilever of Fig. 1(a); compliance design Fig. 1(b) (same setting reused in Fig. 2 and Sec. 3.1) |
| 130 | 2210.04392 | yes | 2 | custom | `tftttmtm` | no | no | 0 | Sec. 3.1, Case 1 (normal load, double-edged crack), Fig. 4 left: alpha = 0 (pure compliance), nu = 0.45, three materials; setting Figs. 2-3 (PDF p. 4) |
| 131 | 2609.39472 | no: other (borderline) | - | - | - | - | - | - | Feature-mapping alignment: the optimization objectives are least-squares tracking and reward functionals between feature-mapped densities and a given target density (no FE analysis in the loop). The targets are SIMP compliance solutions ('standard', vf 0.5, p = 3) of a single-load cantilever (60 x 60 unit square) and a five-bar problem, but their supports and loads are not specified beyond 'standard single-load cantilever'. Borderline: the SIMP target runs are compliance problems with a volume constraint. |
| 132 | 2107.07763 | yes | 2 | cantilever | `cttccccc` | no | yes | 0 | Sec. 3, default cantilever beam example, call UNVARTOP_2D_compliance(100,50,10,0,0.5,0,0.5); domain and BCs Fig. 4, results Fig. 5 |
| 133 | 2607.20784 | yes | 2 | MBB | `tftmtttt` | yes | yes | 2 | Sec. 4.1.1, 2D MBB beam, single-material case (1D shape function, m = 1, vf = 0.3), Table 2 row m = 1 (CASE III with density and projection filters; CASE I/II are filter ablations); problem Fig. 2(a) (PDF p. 15) |
| 134 | 2601.22241 | yes | 2 | cantilever | `tttmtttm` | yes | no | 0 | Sec. 3.2 horizontal cantilever (Fig. 2(A)); results aggregated over 27 configurations x 15 runs (Fig. 5); first individual designs shown are the best designs per configuration in Fig. 6(A) (10D) |
| 135 | 2402.12076 | yes | 3 | MBB | `tffmtmmm` | yes | yes | 6 | Sec. 5.4, 3D beam three-point bending, design domain Fig. 9(a); first result Fig. 9(b) (porous unit of Table 2(a)); formulation Sec. 4.3 Eq. (27) |
| 136 | 2609.03761 | yes | 3 | custom | `fttttttt` | yes | no | 0 | Sec. 3.4, Fig. 4: Attempt A4 (faceted bust) protected-domain SIMP run, first optimized design in document order; same run is row A4 of Table 1 (Sec. 4) |
| 137 | 2303.14690 | yes | 2 | other | `fcfcttct` | no | no | 0 | Sec. 3 / 3.1, internally pressurized arch, problem Fig. 8; first result Fig. 10 (volf = 0.30, lst = 1). Sec. 2.2 sample problems SP1-SP3 are pressure-field demonstrations without optimization |
| 138 | 2508.02594 | no: other | - | - | - | - | - | - | CubeSat payload engineering report (static, modal and random-vibration FEA). The abstract mentions 'a proposal for topological optimization' of the platform-payload interface, but the body reports only an iterative, unformulated fixture redesign (Sec. 4, Fig. 7) aimed at removing parasitic modes; no compliance objective, volume constraint or TO formulation is given. |
| 139 | 1907.01117 | yes | 2 | custom | `ffftfmtm` | yes | no | 0 | Sec. 1.2, car hood latch: boundary conditions Fig. 1(b); first optimized designs Fig. 4 (PareTO family from the unpruned initial design, i.e. strategy 2 of Sec. 5.5 / Fig. 16) |
| 140 | 2407.17957 | no: not structural | - | - | - | - | - | - | All optimization examples are acoustic topology optimization (Helmholtz problem, minimizing sound pressure level from a harmonic source by designing a ceiling) plus 2-D analytic benchmark functions. The only compliance item is Fig. 16(a), an image of under-discretization artifacts in a compliance problem with no stated loads, supports or volume constraint. |
| 141 | 2604.27208 | yes (borderline) | 2 | MBB | `tftmtttt` | no | yes | 0 | Sec. 4.1 Example I (simply supported rectangular beam), schematic Fig. 2; first design Fig. 3(a) (proposed LDT-based RBTO) |
| 142 | 2510.05572 | yes | 2 | cantilever | `tftmtttm` | no | yes | 0 | Sec. 3.1.1, 2D cantilever beam; problem Fig. 4(a); GET design Fig. 5(b) (MMC comparison design Fig. 5(a)) |
| 143 | 2609.15001 | yes | 2 | cantilever | `tccmtttc` | no | yes | 0 | Sec. 3.2, centrally loaded cantilever (first of three 2-D benchmarks), Fig. 3(a); Table 1 row 'Cantilever'; definition in Supplementary Appendix S2 |
| 144 | 2012.02860 | yes | 2 | cantilever | `fffmtttt` | no | yes | 0 | Sec. 5.1.1, 2D cantilever (Fig. 3(a)); reference design without element removal Fig. 4(a) (rho_t = n.a., V_max = 0.5) |
| 145 | 2004.06330 | no: no numerical example | - | - | - | - | - | - | Purely analytical paper on phase-field topology optimization for incremental elastoplasticity: existence of optimal sets and phase fields, sharp-interface limit and first-order optimality conditions. No figures and no numerical example; the state problem is elastoplastic, not linear-elastic. |
| 146 | 2604.03276 | yes (borderline) | 3 | custom | `cccccccc` | yes | yes | 3 | Supplementary Note A.14, nanopillar designed by FEM-TO (top3d-based continuum SIMP), design Fig. S18 (left); the main-text examples (Nano-TO nanocantilevers and nanopillar) are atomistic EAM models and were not taken as linear-elastic continuum TO |
| 147 | 2002.11027 | yes | 2 | MBB | `fffmtttm` | no | yes | 0 | Sec. 3, MBB beam benchmark (Fig. 3(A)); optimal greyscale SIMP solution with p = 1, Fig. 4(A); Table 1 row 'Optimized' |
| 148 | 2507.19388 | yes | 2 | cantilever | `fttmtmtm` | yes | yes | 2 | Sec. 2, cantilever beam (setup Fig. 1(a)); first design Fig. 2(a): unpenalized variable-thickness run, p = 1, V_frac = 0.3 |
| 149 | 2306.12297 | yes | 2 | MBB | `tftmtttt` | no | no | 0 | Sec. 3.1 MBB beam (three in-plane loads), Fig. 4 (PDF p. 16); first configuration case (a) (CFAO, initial fibre angle 0 deg) in Figs. 5-6; proposed DSCO cases (e)-(n) |
| 150 | 2508.10320 | yes | 2 | cantilever | `tffmtttm` | no | yes | 0 | Sec. 4.1 'Validation of Hypothesis', single-component compliance problem; BCs Fig. 8(a); band-limited design Fig. 8(b) (B-bar = 5) |

## Supplement: in-scope call and ambiguity slots for eligible positions 1-60

| # | arXiv id | Dim | Amb. (v1) | In-scope | Reason | Ambiguity slots |
|---|---|---|---|---|---|---|
| 1 | 2403.04937 | 2 | yes | yes | square grid with L-cut by element removal, edge clamp, point load | L cut-out size: only visible in result images, not stated (Fig. 4); load position on right edge: caption says 'at the right edge', height not stated (Fig. 4 caption); volume fraction: not stated for this instance, dataset range [0.12, 0.5] only (Sec. 3.1 Dataset); load magnitude: not stated (Fig. 4 caption) [scale only] |
| 3 | 2305.08771 | 2 | no | no | design-dependent pressure load and two solid materials | - |
| 4 | 2502.01830 | 2 | yes | yes | square domain, point supports and point load (random task) | support positions: only markers in result images (Fig. 8 row 1; legend Fig. 5); load position and direction: only an arrow in result image (Fig. 8 row 1); volume fraction: not stated for this task, sampled from [0.1, 0.5] (Sec. 3.4); filter radius: filtering mentioned, radius not found (Fig. 2 caption); load magnitude: not stated (Fig. 8 row 1) [scale only] |
| 5 | 1909.11320 | 3 | yes | yes | 3 x 1 x 1 box, clamped end face, distributed end load | loaded region on end face: arrows drawn along bottom edge with traction units N/m^2; edge line vs strip width not stated (Fig. 3 left) |
| 6 | 2507.16519 | 2 | no | yes | 2 x 1 rectangle, edge clamp, traction on edge segment | - |
| 7 | 2508.19169 | 2 | no | yes | rectangle, corner pin/roller, distributed edge load, solid bottom layer as fixed element set | - |
| 8 | 2309.00396 | 3 | yes | no | scanned denture anatomy, two materials | - |
| 9 | 2010.10770 | 2 | yes | no | component-wise lattice (joint/strut) model | - |
| 11 | 2407.07288 | 2 | yes | yes | rectangle, bottom-edge support segment, point load (random task) | domain width and height: sampled in [1.0, 2.0], readable only from illegible axis ticks (Fig. 10 row A); support segment extent on bottom edge: only drawn (Fig. 10 row A); load position on top edge: only drawn (Fig. 10 row A); load angle: oblique arrow, value not stated (Fig. 10 row A); volume fraction: not stated for this sample, range 20-40%, achieved 0.300 shown (Table 2; Fig. 10 row A); Young's modulus: not stated (MMC/ersatz paragraph) [scale only] |
| 12 | 2605.28857 | 2 | no | yes | rectangle, corner pins, mid-span point load | - |
| 13 | 2412.18441 | 2 | no | yes | 2 x 1 rectangle, edge clamp, corner point load | - |
| 14 | 2601.23269 | 2 | no | yes | square half-MBB, symmetry rollers, corner point load | - |
| 16 | 2406.18833 | 2 | no | no | discrete truss model | - |
| 17 | 2212.00964 | 3 | yes | no | CAD bracket with lugs outside the box design space; supports and load on hole walls | - |
| 18 | 2503.20915 | 2 | no | no | discrete frame model | - |
| 19 | 2005.05436 | 2 | no | yes | half-MBB rectangle, symmetry rollers, corner point load | - |
| 21 | 2502.05899 | 2 | no | yes | rectangle, bottom-edge support segments, traction on bottom segment | - |
| 22 | 2307.16521 | 3 | yes | no | thermo-mechanical coupling; cylindrical battery cells of a second material | - |
| 23 | 2410.23295 | 3 | yes | yes | cube voxel domain, base supports, top distributed load (design restricted to neural-SDF latent space; parametrisation ignored) | supported set on base: text says 'points at the base' are fixed; all base-face nodes or a subset not stated (Results 'Structures optimization' para 1; Fig. 6 right); top thin shell: thickness, stiffness and whether it is a non-design solid layer not stated (same para; Fig. 6 right); load magnitude and distribution: 'distributed forces' through the shell, value not stated (same para; Fig. 6 right) [scale only] |
| 24 | 2011.07732 | 2 | yes | no | discrete truss with unilateral contact obstacle | - |
| 25 | 1910.13002 | 3 | no | yes | 2 x 1 x 1 box, clamped end face, centre patch load, solid patch layer (homogenisation parametrisation ignored) | - |
| 26 | 2112.00648 | 2 | no | yes | half-MBB rectangle, symmetry rollers, corner point load (multiscale microstructure parametrisation ignored) | - |
| 27 | 2505.02438 | 2 | no | yes | rectangle, edge clamp, corner point load | - |
| 28 | 2608.19763 | 3 | yes | no | bar-and-hinge origami model | - |
| 29 | 2610.27378 | 3 | no | no | equipment loads applied through rigid multipoint ties (RBE2) on mounting pads; thin-slab frame domain | - |
| 30 | 2608.28513 | 3 | no | yes | 20 x 5 x 5 box, corner pins, top mid-span line load | - |
| 31 | 2312.06378 | 3 | yes | no | curved NURBS shell | - |
| 32 | 2609.27685 | 2 | yes | no | two or more solid materials | - |
| 34 | 2205.14780 | 2 | no | yes | 2 x 1 rectangle, edge clamp, traction on edge segment | - |
| 35 | 2004.07002 | 2 | no | no | modular truss model | - |
| 36 | 2105.04232 | 2 | yes | yes | 2L x L rectangle, edge clamp, line load on right edge (homogenisation parametrisation ignored) | load line vertical position on right edge: drawn near mid-height, value not stated (Fig. 9(a)); solid region around load: elements with rho > 0.99 in 'a small radius', radius not stated (Sec. 4 para 1); base Poisson's ratio: not stated (Sec. 2.1.1); load magnitude: not stated (Fig. 9(a)) [scale only]; base Young's modulus: not stated (Sec. 2.1.1) [scale only] |
| 38 | 1708.07364 | 2 | yes | yes | 150 x 60 rectangle, edge clamp, mid-edge point load | filter radius / minimum thickness: Sec. 4 default 2 vs Fig. 7 caption and Table 3 value 1.5 (Sec. 4 para 1; Fig. 7 caption; Table 3); load magnitude: not stated (Sec. 4.1 para 1) [scale only] |
| 39 | 2308.06756 | 2 | no | yes | 2 x 1 rectangle, edge clamp, mid-edge point load | - |
| 40 | 1612.04082 | 3 | yes | yes | unit cube, clamped face, line load on opposite face | load line height on loaded face: dotted line drawn near mid-height, value not stated (Fig. 2(A)); load form: line load vs strip traction not stated (Fig. 2(A)); load magnitude: not stated (Fig. 2(A)) [scale only] |
| 41 | 2103.02047 | 3 | yes | no | beam lattice (frame) model | - |
| 42 | 2104.01965 | 2 | no | yes | 2L x L rectangle, edge clamp, corner point load | - |
| 43 | 2511.14623 | 2 | yes | yes | 2 x 1 rectangle, edge clamp, traction on edge segment | clamp location: Gamma_D written as {0} x (-0.5,0.5) (domain mid-line) while prose and figure put it on the left edge x = -1 (Sec. 4.1.1 'Cantilever beam'; Fig. 4(a)) |
| 45 | 1910.05585 | 2 | no | yes | MBB rectangle (half model), rollers, mid-span point load (component parametrisation ignored) | - |
| 46 | 2111.13875 | 2 | yes | no | self-weight-only loading | - |
| 47 | 2002.01927 | 2 | yes | yes | square half-MBB-type domain, edge supports, edge load | load extent: 'top right edge' read as one element edge only from the drawing (Results para after Fig. 2; Fig. 2a); support extent: 'bottom left edge' read as one element edge only from the drawing (Results para after Fig. 2; Fig. 2a); Poisson's ratio: not stated (Eq. (6)); domain side length: not stated (Results para after Fig. 2) [scale only]; load magnitude: not stated (Fig. 2a) [scale only]; Young's modulus Y0 and void stiffness epsilon: not stated (Eq. (6)) [scale only] |
| 48 | 2305.04107 | 2 | yes | yes | rectangle, edge clamp, corner point load | domain aspect ratio and size: only a sketch drawn about 3:1 (Table 1 'Boundary Conditions' image); SIMP baseline grid resolution: not stated, filter given as 1.5 x element size (Sec. 4 para 2); Poisson's ratio: not stated (Sec. 3.3 para 1); load magnitude: not stated (Table 1 image) [scale only]; Young's modulus E_material: not stated (Sec. 3.3 para 1) [scale only] |
| 49 | 2605.02158 | 2 | yes | yes | square domain, edge-segment supports, point load (random sample) | support segment positions and extents: only unlabeled green marks (Fig. 3 row 1); load position on left edge: only a green arrow mark (Fig. 3 row 1); volume fraction: not stated for this sample, range [0.3, 0.5] (Sec. 4.1 para 1); filter radius: not stated (no mention found); Poisson's ratio: not stated (Sec. 2; Sec. 4.1 para 2); Young's modulus E0: not stated (Sec. 2) [scale only] |
| 52 | 2108.01616 | 2 | no | yes | 60 x 30 rectangle, edge clamp, two corner point loads (deterministic nominal case) | - |
| 54 | 2411.19421 | 2 | no | yes | 3 x 1 half-MBB rectangle, symmetry rollers, corner body-force patch | - |
| 55 | 2111.10439 | 2 | no | yes | rectangle, bottom-corner support segments, top mid-span segment load | - |
| 56 | 2008.07487 | 2 | yes | yes | MBB rectangle, pin/roller or symmetry supports, mid-span point load (lattice-grading parametrisation ignored) | modelled extent and aspect: text says right half on a square 200 x 200 mesh, figure shows a full ~2:1 beam (Sec. 4.1 para 1; Fig. 7); support conditions: symmetry half model in text vs pin and roller drawn on the full beam (Sec. 4.1 para 1; Fig. 7); load magnitude: not stated (Fig. 7) [scale only] |
| 59 | 2605.19110 | 2 | yes | yes | 80 x 40 rectangle with two frozen void element sets, edge clamp, mid-right load | void positions and sizes: '2 voids' only, not shown in Fig. 2 (Table 3 ID 3; Sec. 3.5); load extent and direction: descriptor 'mid-right load' only (Table 3 ID 3); physical domain size: only 80 x 40 elements stated (Table 3); Poisson's ratio: not stated (Sec. 3.2); initial filter radius: not stated, later tightened to 1.2 (Sec. 4.2); load magnitude: not stated (Table 3 ID 3) [scale only] |
