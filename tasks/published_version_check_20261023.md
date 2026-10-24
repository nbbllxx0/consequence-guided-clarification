# Published-version check of the adjudicated tasks (2026-10-23)

Question: does the peer-reviewed version of a source paper state a value that the encoding (made from the arXiv version) treats as open?
Scope: the 22 tasks with a confirmed published version (`tasks/published_versions_20261023.json`). Full texts were read in the publisher's HTML or PDF: open-access versions first, then the remaining ones through the authors' institutional access (Santa Clara University) in their Chrome browser. Text was compared for every checked task. Figures were also compared for L16 and L36; for the others a published figure could add a dimension that the text does not state.

## Result

- Checked: 14 of 22. Unchanged: 13. Resolved by the published version: 1 (L15).
- Not checked: 8. No access through the institution: L13 and L39 (Springer proceedings book not licensed), L24, L29, L31 and L41 (Elsevier: 'does not subscribe'), L33 (RSC, including the supplementary PDF) and L34 (SIAM).
- Recommendation: keep the benchmark defined on the arXiv versions (the frozen frame; a preprint specification is a real specification that readers use), and report this check: 'In 1 of 14 checked published versions, the published text states a value the preprint leaves open (L15: load at mid-height, downward).'

| Task | DOI | Result | Evidence |
|---|---|---|---|
| L01 | 10.1007/s00466-024-02565-2 | unchanged | Fig. 4 caption identical: L-bracket, clamped along the top edge, downward point load 'at the right edge'; Fig. 4 shows designs only. No cut-out size, load position or instance volume fraction; dataset range [0.12, 0.5] (institutional access) |
| L04 | 10.1016/j.cma.2021.114197 | unchanged | Sec. 4 text identical: line of 1/10 L, 'small radius around the load'; Fig. 9 caption identical |
| L08 | 10.1007/s00366-023-01904-w | unchanged | Sec. 4.5 identical: longest side normalized to 1 mm; no height or aspect ratio in the text; Tables 1-2 show set-ups as images |
| L09 | 10.1007/s00158-026-04429-0 | unchanged for the instance | dataset description identical (random loads, f in 0.3-0.5); adds a domain diagram (Fig. 2) of admissible support locations: fixed points at corners or edge midpoints, fixed segments connecting them. The arXiv text states the same rule |
| L12 | 10.1002/aidi.202400015 | unchanged | Sec. 2.4 identical: 'points at the base of the design domain are fixed', top loaded by distributed forces through 'a thin shell at the top'; Fig. 6 inset ('Ground', 'Boundary & loading conditions') gives no extent; Sec. 4.3 adds nothing |
| L13 | 10.1007/978-981-96-1158-4_43 | not checked | no institutional access (proceedings book not licensed) |
| L14 | 10.1007/s00158-026-04343-5 | unchanged | common cantilever setup only in Fig. 1 in both versions; no load coordinate in the text |
| L15 | 10.1016/j.advengsoft.2026.104304 | RESOLVED by the published version | the published version adds: a downward unit point load at the mid-height node of the right edge (arXiv: 'tip load' only). Settles pos (mid, the encoded nominal) and the mandatory direction (down) |
| L16 | 10.1002/nme.70120 | unchanged | the plate is published Fig. 4(a) (arXiv Fig. 6(a)): fixed segments at mid-span of the top and bottom edges, tractions at the top-right and bottom-left corners, segment lengths not dimensioned; text gives only V_f = 0.45, abs(t) and L = 1 m (figure compared) |
| L20 | 10.1109/tevc.2026.3708401 | unchanged | early-access PDF: Fig. 2B caption and Sec. V-A identical ('both lower corners are supported'; 192 x 64, 12,288 design variables; half domain by symmetry); support size not stated (institutional access) |
| L22 | 10.1007/s00158-020-02770-6 | unchanged | Fig. 7 caption identical ('the same loading condition', vf 0.3 and 0.5); figure shows designs only, no load position index (institutional access) |
| L23 | 10.1016/j.cma.2023.115969 | unchanged | identical: load widths 0.04, passive solid regions of width 0.025, height not stated |
| L24 | 10.1016/j.cad.2024.103703 | not checked | no institutional access (Elsevier: 'does not subscribe') |
| L25 | 10.1038/s41467-021-27713-7 | unchanged | identical: load at the 'top-right edge', roller on the 'bottom left edge', 4 x 4 mesh |
| L29 | 10.1016/j.compstruc.2024.107474 | not checked | no institutional access (Elsevier: 'does not subscribe') |
| L31 | 10.1016/j.cad.2018.12.008 | not checked | no institutional access (Elsevier: 'does not subscribe') |
| L33 | 10.1039/d6mh00986g | not checked | no institutional access (RSC article and supplementary PDF) |
| L34 | 10.1137/19m1254490 | not checked | no institutional access (SIAM) |
| L35 | 10.1115/1.4062663 | unchanged | ASME full text: 40 x 20 x 8 elements, 'cantilever beam boundary condition', V* a symbol (equality constraint); Fig. 3(a) captioned only 'Boundary condition'; no load distribution in the text (figure not compared) |
| L36 | 10.1609/aaai.v37i8.26093 | unchanged | Fig. 1 shows the encoded set-up (roller arrows along the left edge in the input panel, on the lower part in the output panel; load arrow on the bottom edge); Sec. 2.1 gives no node set or load coordinate |
| L39 | 10.1007/978-981-96-1158-4_35 | not checked | no institutional access (proceedings book not licensed) |
| L41 | 10.1016/j.asoc.2026.115899 | not checked | no institutional access (Elsevier: 'does not subscribe') |

## Encoding issue found during the check (resolved)

L09 (arXiv:2605.02158): both versions state that supports are fixed points at corners or edge midpoints, or fixed segments connecting these locations. The encoded reading sup = 0.75 violated that rule. **Resolved 2026-10-23:** removed in both encodings at the authors' instruction (L09: 6 → 3 readings; E03 rerun).

## Remaining checklist (no access found)

For each task, open the published version and note whether its text, figures or tables state the value of each listed slot. Record 'states X' or 'open'.

**L13** — https://doi.org/10.1007/978-981-96-1158-4_43
- load: Fig. 1(a) arrow on the lower part of the right edge near the corner vs Fig. 3(b) design converging to mid-height (Fig. 1(a); Fig. 3(b))
- volfrac (mandatory): 0.20 only from the image file name; caption gives no value: mandatory

**L24** — https://doi.org/10.1016/j.cad.2024.103703
- sup: 'bottom sides are fixed', strips drawn at both ends, width not stated (Fig. 9 caption; Fig. 9(a)); convention 1-4 elements of 40
- load: 'uniformly applied at the center of the beam top', drawn as a line across the depth; line vs strip not stated (Fig. 9 caption; Fig. 9(a))

**L29** — https://doi.org/10.1016/j.compstruc.2024.107474
- strip: vertical line about 1 cm inside the right edge drawn, meaning not stated (Fig. 2(a))

**L31** — https://doi.org/10.1016/j.cad.2018.12.008
- dir (mandatory): sampled angle continuous in [0, pi]: no finite admissible set, one representative value: mandatory
- volfrac (mandatory): threshold alpha not stated: mandatory

**L33** — https://doi.org/10.1039/d6mh00986g
- load: 'center of the top surface'; single node vs patch not stated (Suppl. Note A.14)

**L34** — https://doi.org/10.1137/19m1254490
- load: 'applied in the middle of the right-hand face'; node vs patch not stated (Sec. 7; Fig. 2(a))
- volfrac (mandatory): material volume V a symbol only: mandatory

**L39** — https://doi.org/10.1007/978-981-96-1158-4_35
- ar: only 60x20 hexagons stated; maximum length 60 sqrt(3) implied, height not stated (Sec. 3.4; Fig. 1(a))

**L41** — https://doi.org/10.1016/j.asoc.2026.115899
- load: arrow at about 0.45 L on the top edge; node not stated (Fig. 6(a)); convention +-0.05 L


## Follow-up without institutional access (2026-10-23, later)

Routes tried for the 8: OpenAlex locations for each DOI, arXiv version histories, web search for author-hosted copies.

| Task | New result | Evidence |
|---|---|---|
| L34 | **unchanged** (published version read) | SIAM version of record on the UTIA repository (library.utia.cas.cz/separaty/2020/MTR/kocvara-0532969.pdf, Kocvara's institute). Sec. 7, p. A46: "a load in direction z is applied in the middle of the right-hand face (Figure 7.1(a))"; Fig. 7.1(a) one arrow, node or patch not stated; V a symbol only. |
| L31 | accepted manuscript encoded | Encoded text is arXiv v3 (27 Dec 2018), comment "accepted to Computer-Aided Design"; print April 2019 (Crossref). |
| L13 | post-publication author version encoded | Encoded text is arXiv v2 (9 Sep 2025), with a journal reference; chapter online 23 May 2025 (Crossref). |
| L39 | post-publication author version encoded | Encoded text is arXiv v4 (9 Sep 2025), with a journal reference; chapter online 23 May 2025 (Crossref). |
| L29 | not checked | OpenAlex lists an SSRN copy (10.2139/ssrn.4727205, labeled acceptedVersion). SSRN shows a bot-verification page to automated access; not bypassed. The authors can open it in a browser. |
| L24, L33, L41 | not checked | OpenAlex: closed (L33: PubMed record only, no PMC full text). No author-hosted copy found. |

Encoded versions confirmed from the stored source HTML (`tasks/sources/<id>/source.html`: 2310.02069v2, 2310.01968v4, 1807.10787v3).

Totals now: 15 of 22 published versions checked (14 unchanged, L15 resolved); 3 encoded from an accepted or post-publication author version; 4 not checked (L24, L29, L33, L41).

Remaining routes, all author actions: open the SSRN copy of L29 in a browser; interlibrary loan for L24, L33, L41; or ask the corresponding authors for the published PDF.
