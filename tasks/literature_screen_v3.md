# Literature screen v3: arXiv minimum-compliance TO examples, positions 151-247

Frame: `arxiv_frame_20261022.json` (247 papers, query `all:"topology optimization" AND (all:compliance OR all:stiffness)`, retrieved 2026-10-22T20:08:54+00:00; frozen order sha256("20261022:" + id) ascending). This file screens positions 151-247 (the last 97 papers); positions 1-60 are in `literature_screen_v1.json` / `.md` and positions 61-150 in `literature_screen_v2.json` / `.md` (neither edited).
Full text read (151-247): 85 arXiv HTML, 12 arXiv PDF, 0 inaccessible.

## Counts, positions 151-247

- Eligible: **66 / 97**. Ineligible: 31 (other: 27, no numerical example: 2, thermal-only: 1, not structural: 1).
- Borderline eligibility calls (flagged `borderline: true`): 17.
- Dimension of primary example: 2-D 56, 3-D 10.
- Benchmark family: cantilever 28, MBB 8, L-bracket 2, bridge 1, Michell 0, other 11, custom 16.
- Ambiguous primary examples (text plus figure admit more than one reading): **28 / 66**.
- In scope for a structured-grid compliance solver: **42 / 66** (2-D 38, 3-D 4).
- In scope and ambiguous: **21** (2-D 18, 3-D 3); ambiguity slots 101, of which 23 only scale the compliance value ('[scale only]').
- Field instances (8 fields x 66 examples = 528): figure-only 98, missing 120. Examples with at least one figure-only field: 42; with at least one missing field: 60.
- Restricted to geometry, supports, loads, volume fraction: examples with at least one figure-only field 40; with at least one missing field 10.
- Filter radius recorded as 'not applicable' (discrete truss/frame models, tagged missing): 3.

Source tag per field (eligible examples only):

| Field | text | figure | code_or_appendix | missing |
|---|---|---|---|---|
| geometry | 37 | 25 | 4 | 0 |
| supports | 28 | 33 | 4 | 1 |
| loads | 37 | 23 | 4 | 2 |
| passive_regions | 6 | 6 | 0 | 54 |
| volume_fraction | 49 | 5 | 3 | 9 |
| mesh | 48 | 5 | 4 | 9 |
| material | 48 | 0 | 5 | 13 |
| filter_radius | 32 | 1 | 1 | 32 |

## Combined counts, positions 1-247 (v1 records + v1 in-scope supplement in v2 + v2 records + v3 records)

- Eligible: **185 / 247**. Ineligible: 62 (other: 52, not structural: 5, no numerical example: 4, thermal-only: 1).
- Borderline eligibility calls (flagged `borderline: true`): 36.
- Dimension of primary example: 2-D 157, 3-D 28.
- Benchmark family: cantilever 88, MBB 32, L-bracket 4, bridge 4, Michell 3, other 16, custom 38.
- Ambiguous primary examples (text plus figure admit more than one reading): **79 / 185**.
- In scope for a structured-grid compliance solver: **132 / 185** (2-D 118, 3-D 14).
- In scope and ambiguous: **57** (2-D 49, 3-D 8); ambiguity slots 241, of which 64 only scale the compliance value ('[scale only]').
- Field instances (8 fields x 185 examples = 1480): figure-only 275, missing 312. Examples with at least one figure-only field: 124; with at least one missing field: 165.
- Restricted to geometry, supports, loads, volume fraction: examples with at least one figure-only field 120; with at least one missing field 21.
- Filter radius recorded as 'not applicable' (discrete truss/frame models, tagged missing): 13.

Source tag per field (eligible examples only):

| Field | text | figure | code_or_appendix | missing |
|---|---|---|---|---|
| geometry | 107 | 70 | 8 | 0 |
| supports | 78 | 96 | 10 | 1 |
| loads | 106 | 67 | 9 | 3 |
| passive_regions | 23 | 7 | 4 | 151 |
| volume_fraction | 143 | 16 | 6 | 20 |
| mesh | 147 | 12 | 6 | 20 |
| material | 140 | 3 | 9 | 33 |
| filter_radius | 92 | 4 | 5 | 84 |

### In-scope ambiguous 3-D examples, positions 1-247 (8)

Entries up to #150 are repeated from `literature_screen_v2.md`; entries from #151 are new in this file.

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
- #156 1904.06556 (cantilever; Sec. 7.1, Example CANT-16-2-2-5 (3D cantilever, 262,144 elements), Table 1; set-up Fig. 2(a); designs shown for the coarser CANT-16-2-2-4 in Fig. 3)
  - material volume V (volume fraction): appears only as the symbol V, value not stated (Sec. 1 Eq. (1); Sec. 7)
  - density upper bound rho_bar: symbol only, value not stated; with a linear VTS stiffness it bounds local thickness and shapes the layout (Sec. 1 Eq. (1); Sec. 7)
  - load extent at centre of right-hand face: 'applied in the middle of the right-hand face', single node vs line vs patch not stated (Sec. 7 para 5; Fig. 2(a))
  - Poisson's ratio: not stated (Sec. 1 Eq. (1); Sec. 7)
  - load magnitude: not stated (Sec. 7 para 5) [scale only]
  - Young's modulus: not stated (Sec. 7) [scale only]
- #172 2210.01315 (cantilever; Sec. 4.1 Validation, 3D cantilever 40 x 20 x 8, boundary conditions Fig. 3(a); first design Fig. 3(b) (topology network, c = 40.6; SIMP comparison Fig. 3(c), c = 37.8))
  - volume fraction V*: symbol only, value not stated for the validation case (Sec. 3.5 Eq. (20); Sec. 4.1)
  - load form on the free end: two arrows drawn at the two bottom corners of the end face; uniform line load along the bottom edge (top3d default) vs two corner point loads (Fig. 3(a))
  - SIMP penalty p: symbol only, value not stated (Sec. 3.2 Eq. (6))
  - Poisson's ratio: not stated (Sec. 3.2)
  - load magnitude: not stated (Fig. 3(a)) [scale only]
  - Young's modulus E0 and E_min: not stated (Sec. 3.2 Eq. (6)) [scale only]
- #209 2604.18020 (cantilever; Sec. 4.1 / 4.3, 3D cantilever benchmark, smallest end-to-end size 120 x 60 x 30 = 216,000 elements (Table 4 row 216 k); selected design Fig. 8 (fused FP32 rerun, compliance 2.174))
  - filter radius units: r_min = 1.5 reduced to 1.20 stated without units; element widths (1.5 h = 0.025 for h = 1/60) vs physical units (1.5 = 3/4 of the domain length) on a 2 x 1 x 0.5 domain (Sec. 3.1; Sec. 4.1 continuation schedule)
  - Poisson's ratio: not stated for the unit-modulus element stiffness (Sec. 3.1 Eq. (2))

### In-scope ambiguous 2-D examples, positions 151-247 (18)

- #164 2208.09591 (custom; Sec. 2.1, Fig. 1 (first individual problem shown with an optimized design: square domain, VF = 0.40, left-edge rollers, pinned right corners, upward bottom-edge load); dataset of 33,000 ToPy SIMP designs in Sec. 4.1; Table 1 aggregate; Fig. 3 test samples show no boundary conditions)
  - roller extent on left edge: input panel draws rollers along the whole edge, output panel only along the lower about 60% (Fig. 1 left and right panels)
  - load node on bottom edge: arrow drawn at about 0.15 of the width from the left corner, node index not stated (Fig. 1)
  - load direction: drawn vertical upward; dataset directions are sampled in [0, pi] with step pi/6, value for this sample not stated (Fig. 1; Sec. 4.1)
  - filter radius and SIMP penalty: ToPy settings not stated (Sec. 4.1)
  - Poisson's ratio: not stated (Sec. 4.1)
  - load magnitude: not stated (Fig. 1) [scale only]
  - Young's modulus: not stated (Sec. 4.1) [scale only]
- #165 2201.11513 (custom; Sec. 6.1 carrier plate (Fig. 1, PDF p. 9); first optimized design = deterministic TO (DTO) design in Fig. 7 (Sec. 6.1.3, PDF p. 25-26); robust LHNPSO/CA designs in the same figure)
  - deterministic load of the DTO design: not defined; mean field -1 on the top edge is the natural reading, interval-bound or sampled loads also admissible (Sec. 6.1 para 1; Sec. 6.1.3 para 2; Fig. 7)
  - load distribution on the top edge: uniform consistent traction vs equal nodal forces not stated (Sec. 6.1 para 1; Fig. 1)
  - load magnitude: mean -1, units and per-node vs per-length basis not stated (Sec. 6.1 para 1) [scale only]
- #171 2510.08830 (custom; Sec. 4.1.1, double-clamped beam (Fig. 8(a)): low-fidelity homogenization-based stiffness designs used as the initial population; first representative design Fig. 8(b), row L_min = 0.10, leftmost (lowest volume fraction shown); the evolutionary stage (Sec. 4.1.2) minimizes maximum displacement and volume and is not eligible)
  - objective of the low-fidelity stage: 'stiffness optimization' only, compliance vs another stiffness measure not written (Sec. 3.2 Eq. (22); Sec. 4.1.1 Eq. (33))
  - volume fraction of the displayed design: V0 swept over 160 values in [0.25, 0.50], value per shown design not stated (Sec. 4.1.1 para 2; Fig. 8(b))
  - load patch width at top centre: blue solid patch drawn, width not stated (Sec. 4.1 para 1; Fig. 8(a))
  - solid strip widths at clamped edges and under the load: drawn only (Fig. 8(a) legend)
  - macro mesh resolution: not stated (Sec. 4; Sec. 4.1.1)
  - load magnitude: not stated (Sec. 4.1 para 1) [scale only]
- #175 2001.00635 (cantilever; Sec. 4 example for performance verification (cantilever, 16 x 32 elements, 50% volume); first design Fig. 11(a)-(b) (previous SIMP method, before/after filtering, 40 iterations; PDF p. 7))
  - load position and direction: only 'cantilever' stated, no boundary-condition figure; Fig. 11 designs suggest a downward point load near the bottom-right corner, mid-height also admissible (Sec. 4 para 1; Fig. 11)
  - support set: clamped left edge implied by 'cantilever', not stated (Sec. 4 para 1)
  - domain orientation: text '16 x 32 square elements', figures 32 wide x 16 high (Sec. 4 para 1; Figs. 10-11)
  - Poisson's ratio: stated as 1.0, inadmissible for isotropic plane stress, actual value unknown (Sec. 4 FEM paragraph, PDF p. 7)
  - load magnitude: not stated (Sec. 4) [scale only]
- #179 2103.04594 (cantilever; Sec. 6.2.1 mean compliance minimization of the 2D cantilever of Sec. 5.1.1 / Fig. 1 (1000 load scenarios, SVD-based method); design Fig. 3, Table 9)
  - load scenario samples: 1000 scenarios with random coefficients and random surface-load vectors F_4..F_10; realizations or seed not given (Sec. 5.1.1 Eq. (13))
- #181 2310.01968 (MBB; Sec. 3.4 MBB beam optimized results, half-MBB of Fig. 1(a); first design Fig. 2(a) (60 x 20 hexagonal elements, ft = 0, volfrac 0.5, C = 298.92))
  - domain aspect ratio and size: only 60 x 20 hexagons stated; maximum length 60 sqrt(3) implied by 'rfill = 0.04 times the maximum length', height and jagged-edge treatment not stated (Sec. 3.4; Sec. 3.1; Fig. 1(a))
  - Poisson's ratio: not stated, plane stress only (Sec. 3.2)
  - load magnitude: not stated (Fig. 1(a)) [scale only]
- #183 2609.21758 (MBB; Sec. 5 bilevel compliance minimization, MBB beam (settings Appendix C); first designs Fig. 5(c) (typical BOTH and BO topologies, CNN parameterization, four tuned hyperparameters))
  - filter radius: tuned hyperparameter converging to its lower bound, which is 2.0 in the text and 1.5 in Table 1; final value of the shown designs only plotted (Sec. 5.1 para 7; Appendix C Table 1; Fig. 5(d))
  - SIMP penalty and projection sharpness of the shown designs: tuned per run, values only plotted (Fig. 5(c)-(d); Table 1)
- #184 2211.15358 (MBB; Section 'Numerical strategy to obtain a precise Pareto front': MBB beam of Fig. 10, 200 x 100 top88 runs at 10,000 volume fractions (Pareto fronts Figs. 9, 12-13); the intro example design Fig. 1 is an MBB topology without stated settings)
  - filter type: 'sensitivity/density filter' with radius 3, which of the two top88 filters is used not stated (Numerical strategy section para 3)
  - volume fraction: swept over 10,000 regularly spaced values, no single value tied to a displayed design (Numerical strategy section para 3; Fig. 1)
  - Poisson's ratio: not stated, top88 default implied (Introduction Eq. (2))
  - load magnitude: not stated (Fig. 10) [scale only]
  - reference Young's modulus E_r: not stated (Introduction Eq. (2)) [scale only]
- #185 1808.10367 (custom; Sec. 4.1 loading variability, square carrier plate (Fig. 4); single high-resolution 100 x 100 design, Fig. 8 top right (reference for the bi-fidelity runs; Table 1))
  - volume fraction V_bar: symbol only, value not stated (Sec. 2.3 Eq. (9); Sec. 4.1)
  - standard-deviation weight lambda of the Fig. 8 runs: not stated; 0.001, 0.1 and 1 appear only in the later lambda study (Sec. 4.1 para 5; Fig. 8; Fig. 10)
  - random horizontal load realizations: 148 designed-quadrature nodes and weights from [27] not listed (Sec. 4.1 para 2)
  - domain side length: not stated, needed relative to the correlation length l_c = 0.2 (Sec. 4.1 para 1; Fig. 4)
  - Heaviside sharpness beta and threshold tau: not stated for this example (Sec. 2.2 Eq. (6))
  - Poisson's ratio: not stated (Sec. 2.2)
  - Young's modulus: not stated (Sec. 2.2 Eq. (7)) [scale only]
- #187 2607.07233 (custom; Sec. 4.6 case study 1 (shelf bracket, square domain), Fig. 6: SIMP ground-truth design (c = 5.0506) and three HPG-Diff designs; first individual problem with stated settings (intro Fig. 2 shows generated designs without volume fraction or domain size; Tables 2-3 are aggregate))
  - load position on top edge: arrow drawn at about 0.45 L from the left corner, node not stated (Fig. 6(a))
  - support condition on left edge: generic triangle markers, fully clamped vs x-only rollers not stated (Fig. 6(a); Fig. 1 legend)
  - grid resolution: not stated for the case study; dataset images are square, size not given in this paper (Sec. 4.1; Sec. 4.6)
  - filter radius and SIMP penalty of the ground-truth run: not stated (Sec. 4.1)
  - Poisson's ratio: not stated (Sec. 4.1)
  - load magnitude: not stated (Fig. 6(a)) [scale only]
  - Young's modulus: not stated (Sec. 4.1) [scale only]
- #200 2510.23667 (custom; Sec. 1, Fig. 1 (first individual problem shown with an optimized design: square domain with three point supports and two point forces); later individual designs (Fig. 3, Appendix E) are random OpenTO samples drawn without stated volume fractions; benchmark tables are aggregate)
  - volume fraction: V_max shown only as a symbol (Fig. 1)
  - support positions: left roller at about mid-height, top pin and bottom roller at about 0.4 of the width, only drawn (Fig. 1)
  - load positions and directions: upward force on the top edge at about 0.57 width, oblique force on the right edge at about 0.6 height with angle near -35 deg, only drawn (Fig. 1)
  - relative load magnitudes: two forces, ratio not stated (Fig. 1)
  - mesh resolution and filter radius: not stated for this example (Fig. 1; Appendix A)
  - Poisson's ratio: not stated for this example (Appendix A.1)
- #202 2503.16211 (cantilever; Sec. II.1, 2D cantilever of Fig. 1(a), V_f = 0.5; first designs Fig. 1(d) (low-temperature ensemble mean, 2D); deterministic optimized solution 'as solved by [17]' Fig. 3(a))
  - support set: 'Fixed Nodes' drawn only at the two left corners; two corner pins vs fully clamped left edge (Fig. 1(a))
  - load node on right edge: drawn at about mid-height, node not stated (Fig. 1(a))
  - mesh resolution and domain aspect: not stated; a 20 x 8 grid (about 2.6:1) is drawn, possibly schematic (Fig. 1(a), (d))
  - SIMP penalty, filter and Poisson's ratio: not stated (Sec. IV.1)
  - load magnitude: not stated (Fig. 1(a)) [scale only]
  - Young's modulus: not stated (Sec. IV.1) [scale only]
- #204 2509.05800 (custom; Sec. 4.3, Fig. 5 row 1 ground-truth topology (VF 0.30) - first individual instance shown with an optimized design; dataset of 60,000 random 64 x 64 SIMP problems (Sec. 4.1); Fig. 1 shows inputs only)
  - support node sets: read from green marks as left edge top-to-mid, bottom edge left-to-mid and bottom-right corner; not stated for the sample (Fig. 5 row 1; Sec. 4.1 para 2)
  - load node on left edge: drawn at about 0.8 of the height from the top, element not stated (Fig. 5 row 1)
  - load angle: drawn down-left; one of 6 evenly spaced sampled angles, value not stated (Fig. 5 row 1; Sec. 4.1 para 2)
  - filter radius, SIMP penalty and optimizer of the ground-truth run: not stated (Sec. 2.1; Sec. 4.1 para 1)
- #215 2004.05461 (custom; Sec. 4.3.2, Fig. 12 column 1, SIMP (top88) ground-truth design for the first test instance (first individual instance shown with an optimized design; Table 2 aggregate); dataset rules Sec. 4.1)
  - load set of the instance: number (1-4), positions and integer components in {-2,...,2} not stated or drawn (Sec. 4.1; Fig. 12 column 1)
  - volume fraction of the instance: dataset range 0.2-0.8, value not stated (Sec. 4.1; Fig. 12)
  - void circle centre and radius: only the pixel mask is drawn (Fig. 12 bottom row, column 1)
  - filter radius and SIMP penalty: top88 settings not stated (Sec. 4.2)
  - Poisson's ratio: not stated (Sec. 4.2)
  - Young's modulus: not stated (Sec. 4.2) [scale only]
- #217 2012.05359 (custom; Sec. 5.1, Fig. 11 row 1 ground-truth SIMP design (total compliance 2724) - first individual problem shown with supports, loads and an optimized design; Fig. 1 is a 3-D overview illustration without settings; Figs. 8-10 aggregate)
  - grid resolution: not stated (Sec. 4.1)
  - volume fraction of the instance: input variable, value not stated (Sec. 4.1; Fig. 11 row 1)
  - support node set: several fixed-support symbols drawn near the upper-left part, exact nodes not stated (Fig. 11 row 1)
  - load points, directions and relative magnitudes: four horizontal arrows drawn, values random and not stated (Fig. 11 row 1; Sec. 4.1)
  - filter radius, SIMP penalty and Poisson's ratio: not stated (Sec. 2.1)
  - Young's modulus E_max: not stated (Sec. 2.1) [scale only]
- #219 2603.27000 (cantilever; Sec. 5.1, Table 3 row cantilever_basic (GT C = 63.69); ground-truth design Fig. 5 first pair (schedule controller, 300 iterations); benchmark suite Sec. 4.1)
  - load position on right edge: 'tip load' only; mid-height inferred from the symmetric design and the example prompt, corner also admissible (Algorithm 2 line 2; Sec. 1.3; Fig. 5)
  - volume fraction: configurator default 0.5 assumed; value of cantilever_basic not stated and the suite also lists 0.3, 0.4, 0.6 (Algorithm 2 line 5; Sec. 4.1)
  - filter radius: r_min set by the continuation schedule, value not stated (Sec. 3.3)
  - Poisson's ratio: not stated (Sec. 3.3)
  - load magnitude: not stated (Sec. 4.1) [scale only]
  - Young's modulus: not stated (Sec. 3.3) [scale only]
- #239 2608.30499 (L-bracket; Sec. 3, Fig. 1 top row: deterministic (kappa = 0) compliance design of the 2D L-beam (Phi = 0.0204), problem Fig. 4(b); the same benchmark is specified in Sec. 6.1 (V0 = 0.4, R = 24 h_e, 400 x 400) with designs in Fig. 5)
  - volume fraction and filter radius of the Fig. 1 design: not restated; Sec. 6.1 gives V0 = 0.4 and R = 24 h_e for the same L-beam (Fig. 1 caption; Sec. 6.1)
  - load distribution on the 1/20-wide solid block: two arrows drawn, uniform traction vs nodal forces not stated (Fig. 4(b))
  - load magnitude: F not stated (Fig. 4(b)) [scale only]
- #241 2609.07149 (cantilever; Sec. 4.1 cantilever beam 2 x 1 loaded at the bottom right (set-up Fig. 6, parameters Table 1); locally nondominated designs of branches 1-3, Fig. 10 (epsilon-constraint compliance and volume variants). Intro Fig. 1 reproduces results of [13] and is not original to this paper)
  - load position on right edge: text 'loaded at the bottom right', set-up figure draws the load block at mid-height (Sec. 4.1 para 1; Fig. 6)
  - load block size b: solid b x b block drawn, b not stated (Fig. 6; Sec. 3.1)
  - volume fraction: swept along each branch via epsilon-constraints, no single value for a displayed design (Sec. 3.2; Fig. 10)
  - load magnitude: not stated (Fig. 6) [scale only]

## Screening rules applied

Identical to v1 and v2 (eligibility, primary example, source tags, family mapping, 60-word excerpts, in-scope call, ambiguity slots); repeated here for completeness.

- Eligible: original paper with at least one numerical example of structural TO in linear elasticity, compliance (stiffness) objective, a volume constraint, and prescribed loads and supports. A mass constraint on a single material and a volume penalty in a loss were accepted as volume constraints. Additional constraints (stress, AM, buckling) were accepted and noted.
- Primary example: first numerical example in document order that meets eligibility. Where a paper reports only aggregate results over randomly generated task sets before any individual case, the first individual instance shown with an optimized design was taken.
- Source tag: `text` if stated in prose (incl. tables in the body); `code_or_appendix` if stated only in a code listing or appendix; `figure` if only visible in a figure or its caption; `missing` if not found. `missing` also covers fields that do not apply to the method (no passive region mentioned; no filter in phase-field, level-set, neural or truss methods); the value string says which.
- Family: MBB = simply supported or symmetric-half beam with a mid-span point load (incl. 3-point bending); bridge = supported span with distributed or deck loads; other = named benchmark outside the list; custom = application geometry or random task.
- Excerpts are verbatim from the arXiv HTML/PDF text (math as LaTeX alt text); `[...]` marks an omission.
- `in_scope_structured_grid` (eligible records only): true if the primary example's boundary-value problem can be rebuilt on a structured-grid, single-material, isotropic linear-elastic compliance solver: rectangle/box domain, optionally minus element-removed holes, notches or L-cuts (staircase approximation of curved holes accepted) and with fixed solid/void element sets; supports on nodes, edges or faces; design-independent point, line or patch loads (several loads or load cases allowed); volume or single-material mass constraint. False for scanned or CAD/free-form geometry, non-rectangular outer domains, lattice/truss/frame/bar-and-hinge models, shells/plates, self-weight-only or other design-dependent loads, thermal or other multiphysics coupling, geometric/material nonlinearity or contact, dynamics, two or more solid materials, anisotropic base material, and loads applied through rigid multipoint ties. The design parametrisation (SIMP, level set, phase field, homogenisation, components, neural, microstructure grading) does not affect the call. The one-line reason is in `notes` ('In-scope: ...').
- `ambiguity_slots` (eligible records only): non-empty exactly for in-scope ambiguous examples; one string per underdetermined quantity, '<quantity>: <reason> (<evidence location>)'. Quantities that only scale the compliance value and not the optimal layout (a single load's magnitude, Young's modulus) carry the suffix '[scale only]'.

## Process notes and limitations

- Full texts were fetched with `scripts/fetch_papers.py` unchanged (sequential, 3 s between arXiv requests, plain python-urllib user agent, no e-mail): 85 arXiv HTML, 11 arXiv PDF and 1 paper with neither HTML nor a current PDF (2301.07440, #221). Raw downloads were kept outside the repository; rerun the script to reproduce them.
- #221 (2301.07440): the abs page states that the paper has been withdrawn (v2); the v1 PDF was downloaded once through `fetch_papers.py --fig` and read with pdftotext (same treatment as v2 #118). The record therefore has `source_read: arxiv_pdf`.
- Figure links: `fetch_papers.py` ignores the HTML `<base href>` when it builds figure URLs. Figure URLs were resolved from the saved `source.html` against `<base href>` (falling back to the page URL) by a local helper outside the repository and then downloaded one at a time with `fetch_papers.py --fig`. Inline LaTeXML SVG figures (no separate file) were extracted from the saved `source.html` and rendered locally. PDF-only figures were read from pages rendered with pdftoppm. No other network requests were made.
- Positions 151-247 were screened sequentially by one screener (no sub-agents) under the identical rule set. Every eligible excerpt was machine-checked as verbatim (whitespace-normalised) against the downloaded text before the build, and this build script repeats that check.
- Spot-check by re-reading the source after all records were written (17 records): #151 (Case 1 has no filter factor in Appendix 10.1), #156 (no value of V or the density upper bound anywhere), #172 (V* never given), #175 (Poisson's ratio printed as 1.0), #183 (r_min lower bound 2.0 in text vs 1.5 in Table 1), #185 (V_bar never given), #197, #202, #209 (no Poisson's ratio; r_min without units), #219 (configurator defaults V_f = 0.5, 60 x 30 in Algorithm 2), #220 (Fig. 7(a) re-inspected), #226, #231, #239, #241 ('bottom right' in text vs mid-height block in Fig. 6), #244, #245. Corrections: #197 support ('Fixed Edge') and load magnitude |F| = 0.10 read from the rendered inline SVG of Fig. 1; #202 filter value changed to 'density filter used, radius not stated'; #226 geometry, support and load rewritten after inspecting Fig. 4(c) (mirrored L, clamp on the right arm, tip load on the left arm) and the volume bound recorded as the unstated mass bound M_bar; #231 supports and pressure boundary read from Fig. 6(a) and an unverified pressure value removed; #239 note added that Fig. 1 revisits the original SHoSP study; #244 supports (two hatched circular holes) and tip load read from Fig. 9(a); #245 Fig. 3 and Table 2 read from the rendered PDF page (pin/roller, mid-top point load, phase volume fractions, moduli, r_f = 8) and family changed from custom to MBB. The machine check also caught nine excerpts above 60 tokens (shortened) and two LaTeX backslash escapes broken in JSON (#170, #197), both fixed before the build.
- Ambiguity was assessed for all eligible records, including out-of-scope ones; slots are given only for in-scope ambiguous records (rule above). Ambiguity, family, primary-example and in-scope assignments are judgement calls by a single screener; no second independent coder, no inter-rater agreement. `borderline: true` marks debatable eligibility.
- Judgement calls worth a second look: for ML/dataset papers the first individual instance shown with an optimized design was taken as primary example, with unstated sample settings as slots (#164, #187, #200, #204, #215, #217; as v2 #114); intro illustrations without settings were skipped (#167, #187, #199, #217; as v2 #88); papers with compliance TO but unreported loads and supports were made ineligible borderline (#163, #222; as v2 #90), and so were #177 (OAT editing, no individual problem) and #210 (TO snapshots from a cited work, no objective or settings); mean/robust compliance objectives were accepted as borderline (#179, #185; as v2 #75), and worst-case truss compliance (#152) likewise.

## Per-paper table, positions 151-247

Source codes in order geometry, supports, loads, passive, volume fraction, mesh, material, filter: t = text, f = figure, c = code/appendix, m = missing. In-scope = `in_scope_structured_grid`; Slots = number of ambiguity slots (full text in the JSON).

| # | arXiv id | Eligible / reason | Dim | Family | Sources | Amb. | In-scope | Slots | Primary example / note |
|---|---|---|---|---|---|---|---|---|---|
| 151 | 2607.01812 | yes | 2 | cantilever | `ctcmcctm` | no | yes | 0 | Sec. 4.1, Case 1 (2D cantilever beam), Table 1 row 1; boundary conditions Fig. 4(a), result Fig. 6(a); clear prompt Appendix 10.1 |
| 152 | 2405.04805 | yes (borderline) | 2 | cantilever | `tffmtttm` | yes | no | 0 | Sec. 6.1 robust compliance optimization of a truss, ground structure Fig. 6; first solution Fig. 7(a) (problem (59), epsilon = 1e-9, S-APG); Sec. 5.4 eigenvalue toy examples skipped (not compliance) |
| 153 | 2107.08895 | no: other | - | - | - | - | - | - | Responsive (active/passive bimorph) structures: all examples maximize the work of actuation or the blocking load (difference or ratio of stimulated and unstimulated compliances) with a responsive-material volume constraint; two materials with transformation strain, no minimum-compliance example. Sec. 2 recalls the classical compliance problem without a numerical example. |
| 154 | 2106.06478 | no: other | - | - | - | - | - | - | Data-driven multiscale TO of cellular composites (LVGP surrogate of multiclass microstructures): every example maximizes the fundamental natural frequency under a base-material volume constraint; no static compliance objective (compliance is mentioned only as a possible extension). |
| 155 | 2111.06910 | no: no numerical example | - | - | - | - | - | - | Analytical paper: energy scaling law (lower and upper bounds by explicit constructions) for perimeter-regularized compliance-plus-volume minimization under a uniaxial load in 3-D; figures are sketches of constructions, no computed design. |
| 156 | 1904.06556 | yes | 3 | cantilever | `tttmmtmm` | yes | yes | 6 | Sec. 7.1, Example CANT-16-2-2-5 (3D cantilever, 262,144 elements), Table 1; set-up Fig. 2(a); designs shown for the coarser CANT-16-2-2-4 in Fig. 3 |
| 157 | 1909.05592 | yes | 2 | cantilever | `tttmtttm` | no | yes | 0 | Sec. 3, Example 1 Cantilever, configuration Fig. 3 left; first optimal domain Fig. 4 (descent direction i), 50 iterations) |
| 158 | 2606.16792 | yes (borderline) | 2 | cantilever | `fftmmfmm` | yes | no | 0 | Sec. 5.1 truss optimization: bar-area optimization of the two-, four- and eight-bar layouts (Fig. 6) under a vertical tip load, epsilon-constraint sweeps of compliance vs volume; designs Fig. 7(c) |
| 159 | 2208.10879 | yes | 2 | cantilever | `fttmtttt` | no | yes | 0 | Sec. 5.2.1 cantilever beam problem, problem Fig. 5; first solution Fig. 8(a) (100 x 50, vf = 0.35, ls = 2) |
| 160 | 1611.06242 | no: other | - | - | - | - | - | - | Bi-material phononic (acoustic metamaterial) unit-cell design: multiobjective optimization of the flexural-wave locally resonant bandgap together with effective in-plane stiffness (unit-cell compliance) or mass; periodic unit cell without prescribed structural loads and supports, two solid materials, and no volume-constrained compliance problem. |
| 161 | 2503.19807 | yes | 2 | cantilever | `fttmtfmm` | no | yes | 0 | Sec. 3.1.1, cantilever of Fig. 2 (top row), deterministic simultaneous case (middle column, iteration 50); the alternating case in the left column is a non-standard load-switching iteration and was not taken |
| 162 | 2610.24459 | no: other | - | - | - | - | - | - | Neural lattice-refinement operator for periodic 3-D unit cells; the TO targets minimize volume fraction subject to matching a prescribed homogenized stiffness tensor (tensor matching with bisection over volume fraction) on a periodic RVE; no structure under prescribed loads and supports and no compliance objective. |
| 163 | 2405.04821 | no: other (borderline) | - | - | - | - | - | - | Aerial manipulator hardware paper. Sec. 3.4 runs Altair Inspire TO of the elbow joint and the elbow link ('maximizes the stiffness [...] mass targets are set to 30% of total design space volume'), but the TO loads ('multiple combinations of bending and torsional deformations') and supports are not specified; the 500 N shear and 15 N m moment belong to the later stiffness check. Borderline: stiffness objective with a single-material mass target, eligible if the unreported loads and supports were accepted (same treatment as v2 #90). |
| 164 | 2208.09591 | yes | 2 | custom | `tffmftmm` | yes | yes | 7 | Sec. 2.1, Fig. 1 (first individual problem shown with an optimized design: square domain, VF = 0.40, left-edge rollers, pinned right corners, upward bottom-edge load); dataset of 33,000 ToPy SIMP designs in Sec. 4.1; Table 1 aggregate; Fig. 3 test samples show no boundary conditions |
| 165 | 2201.11513 | yes | 2 | custom | `tttmtttt` | yes | yes | 3 | Sec. 6.1 carrier plate (Fig. 1, PDF p. 9); first optimized design = deterministic TO (DTO) design in Fig. 7 (Sec. 6.1.3, PDF p. 25-26); robust LHNPSO/CA designs in the same figure |
| 166 | 2606.17390 | no: other | - | - | - | - | - | - | Differentiable GPU finite-element framework for inverse identification of finite-strain anisotropic plasticity parameters; no topology optimization is performed (Sec. 3.6 reuses a specimen geometry topology-optimized in prior work [67]) and no compliance objective. |
| 167 | 2404.18300 | yes | 2 | other | `fffmtttm` | no | yes | 0 | Sec. 3.2.1 Validation: tensile bar, boundary conditions Fig. 14(a); multiscale porous design cited as Fig. 15(c)/Fig. 14(c) (compliance 209); intro Fig. 3 heel-bone illustration skipped (no settings given) |
| 168 | 2602.17783 | yes | 2 | MBB | `tftmtttt` | no | no | 0 | Sec. 4.1 multi-material compliance minimization, MBB beam 2D (Fig. 2(a), Table 2 row 1); first design Fig. 3, ordered SIMP under the mass constraint (Table 4) |
| 169 | 2505.03064 | no: other | - | - | - | - | - | - | Metamaterial foam design by inverse homogenization: the unit-cell optimization matches the eigenstructure of the homogenized stiffness or compliance tensor to extremal-material targets; periodic cell without prescribed structural loads and supports, no compliance-minimization example. |
| 170 | 1909.13585 | yes | 2 | other | `fttttttt` | yes | no | 0 | Sec. 3, two-bar frame problem P1 (compliance with buckling constraint lambda_bar = 1.0, f_bar = 0.16), geometry Fig. 1(a); first design Fig. 1(b) (Omega_1 = 840 x 360) |
| 171 | 2510.08830 | yes (borderline) | 2 | custom | `fttftmtm` | yes | yes | 6 | Sec. 4.1.1, double-clamped beam (Fig. 8(a)): low-fidelity homogenization-based stiffness designs used as the initial population; first representative design Fig. 8(b), row L_min = 0.10, leftmost (lowest volume fraction shown); the evolutionary stage (Sec. 4.1.2) minimizes maximum displacement and volume and is not eligible |
| 172 | 2210.01315 | yes | 3 | cantilever | `tffmmtmm` | yes | yes | 6 | Sec. 4.1 Validation, 3D cantilever 40 x 20 x 8, boundary conditions Fig. 3(a); first design Fig. 3(b) (topology network, c = 40.6; SIMP comparison Fig. 3(c), c = 37.8) |
| 173 | 2210.00003 | no: other | - | - | - | - | - | - | Microstructure (periodic unit cell) design: maximizes homogenized Young's modulus or material strength with yield and buckling constraints under macroscopic strain/stress states; no structure under prescribed loads and supports. |
| 174 | 2309.11389 | yes | 2 | cantilever | `tttmtttm` | no | yes | 0 | Sec. 3.4.1 cantilever beam, level set-fitted PolyDG run with 1000 polygons; converged design Fig. 6 right, panel (D) (k = 155, compliance 1.2021) |
| 175 | 2001.00635 | yes | 2 | cantilever | `tmmmtttt` | yes | yes | 5 | Sec. 4 example for performance verification (cantilever, 16 x 32 elements, 50% volume); first design Fig. 11(a)-(b) (previous SIMP method, before/after filtering, 40 iterations; PDF p. 7) |
| 176 | 2207.03072 | yes | 2 | bridge | `tttmtttt` | no | yes | 0 | Sec. 3.1, first case: 2D bridge 12 x 2 m (Fig. 2, DEM and FEM designs at several iterations; final DEM design after 80 iterations) |
| 177 | 2602.22430 | no: other (borderline) | - | - | - | - | - | - | Latent-diffusion editing (warp, lattice infill, no-design region) of existing OAT dataset topologies; the only optimization is an optional 10-step SIMP-OC compliance refinement warm-started from the edited design. No individual problem is specified: the random OAT loads, fixtures and volume fractions of the shown examples are neither stated nor drawn. Borderline: the SIMP refinement is compliance with a volume fraction under the instance's boundary conditions (cf. v2 #120, where the OAT problem was identified and its classical SIMP design shown). |
| 178 | 2605.06011 | yes (borderline) | 3 | custom | `tttttttt` | no | no | 0 | Sec. 3.2 / Sec. 4.2, lattice-core cube: homogenization-based TO of the TPMS cell-size field, set-up Fig. 4 (left); optimized size distribution Fig. 19 (converged about 50 iterations) |
| 179 | 2103.04594 | yes (borderline) | 2 | cantilever | `fftmtttt` | yes | yes | 1 | Sec. 6.2.1 mean compliance minimization of the 2D cantilever of Sec. 5.1.1 / Fig. 1 (1000 load scenarios, SVD-based method); design Fig. 3, Table 9 |
| 180 | 2305.06750 | no: other | - | - | - | - | - | - | TO of self-contacting mechanisms (push-lift, self-engaging hooks, bending section) with third-medium contact at finite strain (hyperelastic); objectives are force/displacement-path targets of mechanisms, no linear-elastic compliance example. |
| 181 | 2310.01968 | yes | 2 | MBB | `fffmtttt` | yes | yes | 3 | Sec. 3.4 MBB beam optimized results, half-MBB of Fig. 1(a); first design Fig. 2(a) (60 x 20 hexagonal elements, ft = 0, volfrac 0.5, C = 298.92) |
| 182 | 2205.09629 | no: other | - | - | - | - | - | - | Component-wise reduced-order (port-reduced static condensation) lattice TO: both examples (L-bracket, cantilever beam) minimize mass subject to aggregated stress constraints; no compliance objective. |
| 183 | 2609.21758 | yes | 2 | MBB | `cccmccct` | yes | yes | 2 | Sec. 5 bilevel compliance minimization, MBB beam (settings Appendix C); first designs Fig. 5(c) (typical BOTH and BO topologies, CNN parameterization, four tuned hyperparameters) |
| 184 | 2211.15358 | yes | 2 | MBB | `tffmtttt` | yes | yes | 5 | Section 'Numerical strategy to obtain a precise Pareto front': MBB beam of Fig. 10, 200 x 100 top88 runs at 10,000 volume fractions (Pareto fronts Figs. 9, 12-13); the intro example design Fig. 1 is an MBB topology without stated settings |
| 185 | 1808.10367 | yes (borderline) | 2 | custom | `tfttmtmt` | yes | yes | 7 | Sec. 4.1 loading variability, square carrier plate (Fig. 4); single high-resolution 100 x 100 design, Fig. 8 top right (reference for the bi-fidelity runs; Table 1) |
| 186 | 2401.16175 | no: other | - | - | - | - | - | - | Truss topology design under harmonic (time-periodic) loads: all examples minimize peak power with inertia (dynamic stiffness, omega = 15 etc.) under a weight bound via SDP relaxations; static compliance appears only as a theoretical SDr example (Examples 4.1/4.4) without a numerical case. |
| 187 | 2607.07233 | yes | 2 | custom | `fffmfmmm` | yes | yes | 7 | Sec. 4.6 case study 1 (shelf bracket, square domain), Fig. 6: SIMP ground-truth design (c = 5.0506) and three HPG-Diff designs; first individual problem with stated settings (intro Fig. 2 shows generated designs without volume fraction or domain size; Tables 2-3 are aggregate) |
| 188 | 2609.10643 | yes | 2 | custom | `tttmttct` | no | no | 0 | Sec. 5.1, D_Rect plate-bending domain (150 x 150, 4-corner pinned, centre point load), baseline SIMP design Fig. 3 row 1 (SDS-guided designs in the same row); parameters Table 3, Appendix A |
| 189 | 2509.24667 | no: other | - | - | - | - | - | - | All optimizations are dynamic: log dynamic compliance of a damped cantilever at driving frequencies of 100 Hz and above (mass matrix in the state equation) and sound transmission loss of a sandwich panel; no static compliance example (Fig. 1 reproduces Bendsøe-Sigmund designs from the literature). |
| 190 | 2401.08995 | yes | 3 | custom | `fttttmtm` | no | no | 0 | Sec. 4.1 structural compliance minimization of a trapezoidal air rudder (dimensions Fig. 6, initial layout Fig. 7); final design Fig. 8(b) (mass 4.01 kg, compliance 2491.64 mJ) |
| 191 | 2006.04306 | yes | 2 | cantilever | `tctmtttt` | no | yes | 0 | Sec. 5.1.1 Example 1, 2D cantilever 120 x 80 with the ersatz material model; element-based design Fig. 6(a) (C = 31.41), smooth design Fig. 6(b); Matlab code in the Appendix |
| 192 | 2402.15458 | yes | 2 | custom | `fffmtttm` | yes | no | 0 | Femur example of Fig. 1 (problem Fig. 1(a)); homogenization-based optimized layout Fig. 1(b) (Table 1 row 'Femur Figure 1h', C0 = 76.86, V0 = 0.50); Sec. 4 settings |
| 193 | 2412.11112 | no: other | - | - | - | - | - | - | Metamaterial unit-cell design by neuroevolution (CPPN + NEAT): multi-objective exploration of homogenized elastic properties (Young's modulus, Poisson's ratio, shear moduli) of periodic cells; no structure under prescribed loads and supports and no compliance-minimization example. |
| 194 | 2410.22131 | yes | 2 | other | `fffmttmt` | no | no | 0 | Sec. 3.9, internally pressurized arch (domain Fig. 1(a)), call PyTOPress(200, 100, 0.30, 3, 2.4, 0.2, 8, 1, 100); result Fig. 2(a) |
| 195 | 2506.17487 | yes | 2 | cantilever | `tttmtttm` | no | yes | 0 | Sec. 5.1 tip-load cantilever beam, setup Fig. 3(a); first design Fig. 3(b) (classical latent vector, compliance 89.33) |
| 196 | 2403.16587 | yes | 2 | cantilever | `tttftttt` | no | yes | 0 | Sec. 3 / 3.1, 2D cantilever (Fig. 4 left), scale s = 1 (15 x 10 mm), delta = 0 (standard SIMP with Heaviside projection); first design Fig. 5, top-left panel |
| 197 | 2602.05466 | yes | 2 | cantilever | `tftmtttm` | no | no | 0 | Sec. 3.1 / 4, cantilever laminate plate (Fig. 1), concurrent MMC topology + lamination-parameter optimization; first individual designs Table 3 (best-performing CMA-ES structure, concurrent setting); Figs. 6-7 aggregate |
| 198 | 2405.07733 | yes | 3 | other | `tttmttct` | no | no | 0 | Sec. 4.1 loadbearing lid structure (Fig. 2), call TOPress3D(48,24,24,0.25,3,sqrt(3),0.20,10,1,100); design Fig. 3 |
| 199 | 1705.01442 | yes | 2 | cantilever | `tftmttcm` | no | yes | 0 | Sec. 7.1 symmetric cantilever, Lambda = 40, initialization (55); first design Fig. 3(a) ((Nx,Ny) = (150,75)); the Sec. 3.4 Fig. 1 example design carries no settings |
| 200 | 2510.23667 | yes (borderline) | 2 | custom | `fffmmmmm` | yes | yes | 6 | Sec. 1, Fig. 1 (first individual problem shown with an optimized design: square domain with three point supports and two point forces); later individual designs (Fig. 3, Appendix E) are random OpenTO samples drawn without stated volume fractions; benchmark tables are aggregate |
| 201 | 2009.05839 | yes | 3 | other | `tftmtttt` | no | no | 0 | Sec. 4.1, 3D pressure-loaded lid (Fig. 5(a)), full model 120 x 60 x 60; design Fig. 7 |
| 202 | 2503.16211 | yes (borderline) | 2 | cantilever | `fffmtfmm` | yes | yes | 6 | Sec. II.1, 2D cantilever of Fig. 1(a), V_f = 0.5; first designs Fig. 1(d) (low-temperature ensemble mean, 2D); deterministic optimized solution 'as solved by [17]' Fig. 3(a) |
| 203 | 2406.12215 | yes | 2 | MBB | `tttmtttt` | no | yes | 0 | Sec. 4.1.1 single-material MBB (Fig. 1(a)), first run Table 1: 240 x 80, V_T = 0.3, fixed trust region d0 = 0.05, filter r = 4 (no design image for this run; first MBB design image Fig. 3(a)) |
| 204 | 2509.05800 | yes | 2 | custom | `tffmfttm` | yes | yes | 4 | Sec. 4.3, Fig. 5 row 1 ground-truth topology (VF 0.30) - first individual instance shown with an optimized design; dataset of 60,000 random 64 x 64 SIMP problems (Sec. 4.1); Fig. 1 shows inputs only |
| 205 | 2603.00279 | no: other | - | - | - | - | - | - | Inverse homogenization of pentamode metamaterial unit cells for underwater acoustic lenses and cloaks: cells are optimized to match target effective bulk modulus, density and pentamode properties with a connectivity constraint; no structure under prescribed loads and supports and no compliance objective. |
| 206 | 2504.11096 | yes | 2 | MBB | `tttmtftt` | no | yes | 0 | Sec. 4.1 MBB beam (Fig. 2), VTORCH solution snapshots Fig. 3 (first design shown); SIMP/ACPF/VTORCH comparison Fig. 6, parameters Table 1 |
| 207 | 2101.01122 | yes | 2 | other | `ffffmmtm` | yes | no | 0 | Sec. 3.2, PolyTop Hook domain (Fig. 5(a)); first designs Fig. 5(b) (default PolyFilter) and 5(c) (Approximate Volume padding); the MBB results of Table 1 follow |
| 208 | 2401.13868 | no: other (borderline) | - | - | - | - | - | - | Level-set shell topology optimization: mean compliance of a shell midsurface is minimized subject to a bound on the volume enclosed by the midsurface; the paper states that no material-usage volume constraint is applied. Examples (dome, plate, cantilever) are shell analyses. Borderline: compliance objective with a volume-type (enclosed-volume) constraint. |
| 209 | 2604.18020 | yes | 3 | cantilever | `tttmtttt` | yes | yes | 2 | Sec. 4.1 / 4.3, 3D cantilever benchmark, smallest end-to-end size 120 x 60 x 30 = 216,000 elements (Table 4 row 216 k); selected design Fig. 8 (fused FP32 rerun, compliance 2.174) |
| 210 | 2111.11728 | no: other (borderline) | - | - | - | - | - | - | Linear-solver paper (Total-FETI vs FETI-DP): the topology optimization appears only as density snapshots (iterations 4, 8, 30) of a modular TO of a beam fixed at both bottom corners with a mid-span top load, taken from [4]; the TO objective, volume constraint and settings are not stated and no optimized design is reported. Borderline: the underlying modular TO is a compliance problem in the cited work. |
| 211 | 2303.15070 | yes | 2 | cantilever | `tttmtttm` | no | yes | 0 | Sec. 4.3.1 cantilever (schematic Fig. 5); first design Fig. 7(a) (sphere combination); the earlier Poisson examples (Secs. 4.1-4.2) are not elasticity |
| 212 | 1705.01538 | yes | 2 | cantilever | `tffmtttt` | no | yes | 0 | Sec. 4.1 design subjected to static loading, case (1) Eq. (18): both loads applied simultaneously; design Fig. 3(a); cantilever Fig. 2(a), parameters Table 1 |
| 213 | 2009.12560 | yes | 2 | other | `fffmtttm` | no | no | 0 | Sec. 1.1 motivating problem: two-element frame (boundary conditions Fig. 1(a)); local optimum a1 = 0.652, a2 = 0.242 (c = 2.895) and global optimum a1 = 0.4 sqrt(5), a2 = 0 (c = 2.719) |
| 214 | 2103.02588 | yes | 3 | cantilever | `fffmtftm` | no | no | 0 | Sec. 8.2 functionally graded cellular cantilever (Fig. 12): optimized E, nu and rho maps from the Sec. 6.1 minimum-compliance problem with overall mass 45%; Fig. 1(a) intro density map carries no settings |
| 215 | 2004.05461 | yes | 2 | custom | `ftmfmtmm` | yes | yes | 6 | Sec. 4.3.2, Fig. 12 column 1, SIMP (top88) ground-truth design for the first test instance (first individual instance shown with an optimized design; Table 2 aggregate); dataset rules Sec. 4.1 |
| 216 | 2108.04549 | no: thermal-only | - | - | - | - | - | - | Relaxed variational approach applied to steady-state heat conduction only: thermal compliance minimization (3D conductor) and thermal cloaking objectives; no structural (elastic) example. |
| 217 | 2012.05359 | yes | 2 | custom | `fffmmmmm` | yes | yes | 6 | Sec. 5.1, Fig. 11 row 1 ground-truth SIMP design (total compliance 2724) - first individual problem shown with supports, loads and an optimized design; Fig. 1 is a 3-D overview illustration without settings; Figs. 8-10 aggregate |
| 218 | 2610.25565 | no: other | - | - | - | - | - | - | Two-scale bone-scaffold design: unit cells are generated to match target elastic moduli (rabbit femur benchmark), and the concurrent femoral-implant problems minimize mean solid fraction (maximize porosity) subject to whole-femur compliance-deviation constraints (/r/ <= 2%) on scanned femur models; no compliance-objective example. |
| 219 | 2603.27000 | yes | 2 | cantilever | `cccmccmm` | yes | yes | 6 | Sec. 5.1, Table 3 row cantilever_basic (GT C = 63.69); ground-truth design Fig. 5 first pair (schedule controller, 300 iterations); benchmark suite Sec. 4.1 |
| 220 | 2012.15744 | yes | 3 | cantilever | `tttmtttt` | no | yes | 0 | Sec. 5.2.1 Benchmark I cantilever (Fig. 7(a)); first design Fig. 7(b) SIMP baseline (solid isotropic material), spinodoid multiscale design Fig. 8 |
| 221 | 2301.07440 | yes | 2 | custom | `tttmtttt` | no | no | 0 | Sec. 4.2 / 4.2.1 single IBFG material (Al/Al2O3), square plate under a concentrated centre load with volume constraint 50% (Fig. 7), first boundary condition CCCC. Read from the arXiv v1 PDF; the current version v2 is withdrawn and has no PDF/HTML |
| 222 | 2511.06683 | no: other (borderline) | - | - | - | - | - | - | Satellite radiator cross-sections optimized with COMSOL SIMP to minimize compliance 'under compressive loading' with volume fractions 0.1-0.6 and solid top/bottom faces; the prescribed loads and supports are not specified (the cited Methods section is not in the arXiv PDF text), and the results are reported as homogenized specific-stiffness Pareto data. Borderline: compliance objective with a volume constraint, eligible if the unreported boundary conditions were accepted (same treatment as v2 #90). |
| 223 | 2101.08605 | no: other | - | - | - | - | - | - | Length-scale study of the robust three-field formulation: the numerical examples are a heat-sink thermal compliance problem and a (nonlinear) compliant force inverter; no structural compliance-minimization example. |
| 224 | 2412.18682 | no: other | - | - | - | - | - | - | Topology optimization of prestressed nanomechanical resonators to maximize the quality factor via dissipation dilution (eigenmode-based objective with geometric nonlinearity/prestress); no static compliance objective. |
| 225 | 1504.07724 | no: other | - | - | - | - | - | - | Two-material porous composite unit cell with negative thermal expansion: topology optimization of effective stiffness and coefficient of thermal expansion of a periodic cell (thermoelastic homogenization), fabricated by multi-material AM; no structure under prescribed loads and supports and no compliance-minimization example. |
| 226 | 1711.10784 | yes | 2 | L-bracket | `fffmmmtf` | yes | no | 0 | Sec. 5.1 basic problem (discrete orientation optimization), L-shape test (Fig. 4(c)); design Fig. 5 (Theta = 0, pi/4, pi/2, 3pi/4; domain 8 x 8; filter radius 0.15) |
| 227 | 2107.03618 | no: other | - | - | - | - | - | - | Pressure-actuated compliant mechanisms (inverter, gripper) with design-dependent Darcy pressure loads and a robust formulation: the objectives are mechanism output-displacement/strain-energy measures, not minimum compliance; no compliance-minimization example. |
| 228 | 2002.10533 | yes (borderline) | 3 | custom | `ffftfmtm` | yes | no | 0 | Sec. 2.1, Tosca stiffness maximization of a total ossicular replacement prosthesis (Fig. 2, Case 1 bulk umbo plate, L = 5 mm first); optimized geometries in the results figures |
| 229 | 2512.00133 | yes (borderline) | 2 | custom | `tttttttt` | no | yes | 0 | Sec. 3.1, end-compliance TO of Fig. 7 with parameters of Table 2, case (i) 'linear elasticity' (small load factor Lambda_end = 0.01), design Fig. 8(i) (c = 210.12); the earlier C-shape example (Sec. 2.2) is contact analysis only |
| 230 | 1909.03292 | yes | 2 | other | `tttmtttt` | no | no | 0 | Sec. 3.4 verification problem (pressure-loaded stiff structure, Fig. 7), 10 x 7 mesh, result Fig. 8 after 100 MMA iterations; the first benchmark (internally pressurized arch, Sec. 4.1, Fig. 10) follows |
| 231 | 2106.09245 | yes | 2 | other | `tffmtttm` | no | no | 0 | Sec. 5.1 / 5.1.1 internally pressurized arch (Fig. 6(a), Table 1), first design Fig. 8(a) CASE I (alpha_j = gamma_j = 1), V* = 0.20, 200 x 100 hexagonal FEs |
| 232 | 2511.19211 | no: other | - | - | - | - | - | - | Soft pneumatic gripper chambers designed as pressure-actuated compliant mechanisms (objective based on output displacement / mutual strain energy, Obj negative in Fig. 5) under design-dependent pneumatic loads; no compliance-minimization example. |
| 233 | 2609.07337 | yes | 2 | cantilever | `tttmtttt` | no | yes | 0 | Sec. 6.1, two-dimensional cantilever, reference design of the minimum mean compliance problem (30), Fig. 10(a) (C_ref = 3.212e-2 N); final-use set-up Fig. 8(b), parameters Table 3. The residual-stress designs (elastoplastic AM process) are not eligible |
| 234 | 2201.10248 | yes | 2 | MBB | `cccmtttt` | no | yes | 0 | Sec. 3.4 MBB beam optimized results, half-MBB of Fig. 1; first design Fig. 6(a) (60 x 20 hexagonal elements, no filtering, C = 298.70); code in Appendix A |
| 235 | 1911.10393 | yes | 2 | cantilever | `ftfmtmtm` | no | no | 0 | Sec. 3.1 2D cantilever (Fig. 3(a)); first design Fig. 4(a) anisotropic multicomponent design with K = 3 build orientations (isotropic single-piece comparison Fig. 4(b)) |
| 236 | 1609.06236 | no: not structural | - | - | - | - | - | - | Mesh-modification method for interface problems: numerical results are a scalar Poisson-type interface convergence test and the shape optimization of an electric motor (magnetostatics) from prior work; no elastic structure and no compliance example. |
| 237 | 2111.04620 | no: other | - | - | - | - | - | - | Flexure synthesis: maximizes strain energy of prescribed-displacement degrees of constraint subject to upper bounds on strain energy of degrees of freedom (no volume constraint, no compliance objective under prescribed loads). |
| 238 | 2307.15665 | yes | 2 | cantilever | `tftmtttt` | no | yes | 0 | Sec. 4.1 Example 1, cantilever beam under parabolic end shear (Fig. 6, Table 1); first test [rho_min, rho_max] = [0.12, 0.88], coarse stages Fig. 7, final two-level design Fig. 8(a) |
| 239 | 2608.30499 | yes | 2 | L-bracket | `fffftttt` | yes | yes | 3 | Sec. 3, Fig. 1 top row: deterministic (kappa = 0) compliance design of the 2D L-beam (Phi = 0.0204), problem Fig. 4(b); the same benchmark is specified in Sec. 6.1 (V0 = 0.4, R = 24 h_e, 400 x 400) with designs in Fig. 5 |
| 240 | 1911.09757 | yes | 2 | cantilever | `tttmtttm` | no | no | 0 | Sec. 4.2.1 long cantilever (Fig. 3(a)), three phases (strong, weak, void); design evolution Fig. 4 (final after 500 iterations) |
| 241 | 2609.07149 | yes (borderline) | 2 | cantilever | `tftftccc` | yes | yes | 4 | Sec. 4.1 cantilever beam 2 x 1 loaded at the bottom right (set-up Fig. 6, parameters Table 1); locally nondominated designs of branches 1-3, Fig. 10 (epsilon-constraint compliance and volume variants). Intro Fig. 1 reproduces results of [13] and is not original to this paper |
| 242 | 2606.15645 | no: other | - | - | - | - | - | - | Hydraulic soft fish tail designed as a pressure-actuated compliant mechanism: robust min-max output-displacement objective under design-dependent hydraulic (Darcy) loads with volume and strain-energy constraints; no compliance-minimization example. |
| 243 | 2305.08110 | no: other (borderline) | - | - | - | - | - | - | Dynamic (transient) topology optimization via equivalent static loads: the static compliance subproblems use design-dependent ESLs recomputed from transient analyses with mass and damping, so the examples optimize dynamic response rather than a compliance problem under prescribed loads. Borderline: each inner subproblem is a multi-load static compliance problem with a volume constraint. |
| 244 | 2609.05466 | yes | 2 | other | `tftmtttt` | no | no | 0 | Sec. 5.2 curved beam, deterministic minimum-compliance design Fig. 9(b) (V = 0.45); Sec. 5.1 cantilever skipped (minimum volume under a compliance bound) |
| 245 | 2301.07457 | yes | 2 | MBB | `fffmtttt` | no | no | 0 | Sec. 5.2 multi-material minimum compliance of a square wall structure (Fig. 3, Table 2), three solid materials plus void, first mesh 32 x 32; Sec. 5.1 is a Poisson solver timing test |
| 246 | 2005.13497 | no: no numerical example | - | - | - | - | - | - | Analytical multi-phase-field paper on eigenvalue optimization (and its combination with mean compliance) of elastic structures: existence, continuity and differentiability of eigenvalues and optimality systems; no figures and no numerical example. |
| 247 | 2104.04571 | yes | 2 | other | `fftmfttm` | no | yes | 0 | Sec. 6.1 cantilever tie-beam (Zhou-Rozvany), 100-element mesh of Fig. 6; first designs Fig. 7 (V_f* = 99%, (a) FOCI and (b) exact sensitivity), ESO-type discrete updates |
