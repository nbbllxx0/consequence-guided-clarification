# Reconciliation of the two adjudication records (2026-10-23)

Records: `A_shaoliang.txt` (adjudicator A) and `B_jun_wang.txt` (adjudicator B), both on `guide/2026-10-22-adjudication-sheet.md`. Implementation: `src/littasks.py` (`ADJUDICATION`, `LT_VARIANT`). Agreement statistics: `experiments/a10_adjudication_agreement.py` → `results/a10/adjudication.md`.

## Rule

Each record gives, per slot, a set of admissible values (KEEP = the encoded set; CHANGE = a new set; a resolution to one stated value closes the slot; an added slot opens a new one).
- **Consensus encoding (primary results):** the values both adjudicators accept.
- **Union encoding (sensitivity check):** the values either adjudicator accepts.
- Disjoint sets (L11 void radius, L37 pad depth): consensus keeps the pre-adjudication value, which A accepted; union keeps all values.
- Mandatory slots stay mandatory with one representative value.

Why intersection for the primary results: every ambiguity left in the benchmark is then endorsed by both readers, which is the conservative basis for the paper's claims. The union shows how the results move if every proposed reading is admitted.

## Agreement (results/a10/adjudication.md)

- 69 candidate slots: 52 encoded non-mandatory slots plus 17 proposed additions. 17 mandatory slots are kept by both.
- Kept open by A: 44. By B: 69. By both: 44. Raw agreement 0.64.
- κ = 0.00 because B keeps every unit open. Report the counts, not κ.
- Both keep 44 slots open; 40 of these have identical value sets.
- Exclusions: 15 of 16 agreed. arXiv:2201.11513 is kept excluded (B's own fallback; see below).

## Outcome per task

| Task | A | B | Consensus | Union |
|---|---|---|---|---|
| L02 | vf = 1/6 (0.5 m³ of 3 m³) | strip + full face; vf ∈ {0.5, 1/6} | vf fixed 1/6; strip as encoded | strip ×4, vf ×2 (8 readings) |
| L04 | keep; loaded length 0.2 H | + len, sup, pad | unchanged | + sup {edge, pins}, pad {0, 2, 4} (30 readings) |
| L05 | rmin → 1.5 | keep (conflict) | rmin fixed 1.5 (mandatory only) | as encoded |
| L07 | clamp → left edge | keep | clamp fixed left edge (mandatory only) | as encoded |
| L11 | keep radius 6 | + void size {2, 4} | unchanged | radius {2, 4, 6} |
| L12 | keep | + shell {0, 1} | unchanged | + shell (8 readings) |
| L17 | len → full edge | keep; + pos | **resolved** (full edge) | + pos {lower, mid} (5 readings) |
| L19 | extent → half model | keep | **resolved** (half) | as encoded |
| L20 | extent → half; corner xy | keep; + corner comp {y, xy} | extent half, corner xy; sup as encoded | + supcomp (8 readings) |
| L21 | keep | + 0.75 H | unchanged | load ×3 |
| L22 | nominal 9 | nominal 6 | nominal 9 | nominal 6 |
| L23 | keep | + 0.10 | unchanged | solid ×3 |
| L27 | ar → square | keep | **resolved** (square) | as encoded |
| L31 | keep | + sup {edge, pins} | unchanged | + sup |
| L33 | patches (as encoded) | + sup {nodes, patches} | unchanged | + sup |
| L36 | keep | + nodes5 | unchanged | roller ×3 |
| L37 | keep pad 2 mm | + pad {0, 1} mm | unchanged | pad {0, 1, 2} (12 readings) |
| L38 | keep | + sup, dir | unchanged | + sup, dir (16 readings) |
| L40 | rmin → 1.5 | keep; + ar {3, 6} | **resolved** (rmin 1.5) | + ar (4 readings) |
| L42 | sup → pins | keep; + ar {2.5, 3.0} | **resolved** (pins) | + ar (4 readings) |
| L45 | keep | + dir, rmin | unchanged | + dir, rmin (16 readings) |

Other tasks: both KEEP. Some reason or reconstruction notes were added: L01, L11, L15, L24, L30, L31, L33, L38, L43, L44 and L45.

Totals:

| Encoding | Tasks | Readings | Non-mandatory slots |
|---|---|---|---|
| Consensus | 36 | 134 | 43 |
| Union | 41 | 240 | 67 |
| Pre-adjudication (reproduced exactly) | 41 | 153 | 52 |

## Departures from the records (confirmed by the authors 2026-10-23)

1. **L04 loaded length.**
   - Both records read "a line of 1/10 L" with L as the span, which gives 0.2 H. A changes the length; B adds a length slot.
   - Fig. 9(a) of arXiv:2105.04232 labels the height L and the span 2L (`tasks/sources/2105.04232/figs/cantilever_BC.png`).
   - I kept 0.1 H = 6 elements and did not encode the length slot.
2. **B's cap of 18 readings per task is not applied to L04 in the union.**
   - The union of B's three additions with the five-value position fan gives 30 readings.
   - Applying the cap would mean choosing which additions to drop. The computation was affordable, so I ran all 30.
3. **Mandatory slots.** B's direction changes (L11 down/outward, L15 down/axial) and B's L44 volume-fraction list change reason strings only.
   - These slots are always asked, so their values do not change the computation.
   - B's own rule keeps mandatory slots with one representative value.
4. **L38 and L45 direction.** I encoded these as ordinary (computational) slots in the union, as B proposes. They were not made mandatory.
5. **arXiv:2201.11513.** Kept excluded. B makes encoding conditional on a uniform-traction patch type; the solver does not have one. The paper states the limit in Sec. 5.
6. **Nominal values.**
   - L39: A reads 3.0. The encoded value 3.46 is kept because B keeps it.
   - L22: union uses B's nominal 6; consensus keeps 9.
7. **L09 support (added 2026-10-23, decided by the authors).** Both records keep sup ∈ {0.5, 0.75}. The source (Sec. 4.1, both versions) allows supports only at corners or edge midpoints, or as segments connecting them, so 0.75 is inadmissible. It is removed in both encodings (L09: 6 → 3 readings).

## Author confirmation (2026-10-23)

- Departures 1–6 confirmed; departure 7 chosen by the authors' instruction to pick the optimal option. Both records are accepted as signed; the text files serve as supplementary information.
- Both adjudicators are authors. In B's scope note, "AI-assisted evidence check" referred to the local copies of the source papers. At the authors' request the phrase was removed from `B_jun_wang.txt`; the original is `guide/jun wang.txt`. A's "[SE]" tag means the Codex re-annotation items recorded on the sheet.
