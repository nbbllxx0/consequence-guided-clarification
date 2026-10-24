"""Assemble literature screen v2 (positions 61-150) and combined counts 1-150.

Usage: python build_screen_v2.py RECORDS_DIR V1_SUPPLEMENT_JSON
Reads tasks/arxiv_frame_20261022.json, tasks/literature_screen_v1.json (read only),
RECORDS_DIR/NN_<id>.json for NN = 61..150 and the v1 supplement (in-scope and slots
for the eligible v1 records). Writes tasks/literature_screen_v2.json and .md.
Fails loudly on schema violations.
"""
import collections
import json
import sys
from pathlib import Path

TASKS = Path(__file__).resolve().parents[1]
FIELDS = ["geometry", "supports", "loads", "passive_regions", "volume_fraction", "mesh", "material", "filter_radius"]
SOURCES = ["text", "figure", "code_or_appendix", "missing"]
REASONS = ["not structural", "thermal-only", "stress-only objective", "review/survey",
           "no numerical example", "inaccessible", "other"]
FAMILIES = ["cantilever", "MBB", "L-bracket", "bridge", "Michell", "other", "custom"]
FIRST, LAST = 61, 150
ELIG_KEYS = {"arxiv_id", "source_read", "eligible", "example_ref", "statement_excerpt", "dim", *FIELDS,
             "ambiguous", "ambiguous_reason", "benchmark_family", "evidence", "notes", "borderline",
             "in_scope_structured_grid", "ambiguity_slots"}
INEL_KEYS = {"arxiv_id", "source_read", "eligible", "ineligible_reason", "ineligible_note", "borderline",
             "evidence_ineligibility"}


def fail(msg):
    sys.exit("SCHEMA ERROR: " + msg)


def check_slots(name, ins, amb, slots):
    if not isinstance(ins, bool):
        fail(f"{name}: in_scope_structured_grid must be bool")
    if not isinstance(slots, list) or not all(isinstance(s, str) and s.strip() for s in slots):
        fail(f"{name}: ambiguity_slots must be a list of non-empty strings")
    if (ins and amb) != bool(slots):
        fail(f"{name}: slots must be non-empty iff in-scope and ambiguous (in={ins}, amb={amb}, n={len(slots)})")
    for s in slots:
        if ":" not in s or "(" not in s or not (s.rstrip().endswith(")") or s.rstrip().endswith("[scale only]")):
            fail(f"{name}: slot not in '<quantity>: <reason> (<evidence>)' form: {s}")


def load_records(rec_dir: Path, frame: dict) -> list:
    entries = {e["id"]: e for e in frame["entries"]}
    out = []
    for pos in range(FIRST, LAST + 1):
        aid = frame["frozen_order"][pos - 1]
        f = rec_dir / f"{pos:02d}_{aid}.json"
        if not f.exists():
            fail(f"missing record {f.name}")
        r = json.loads(f.read_text(encoding="utf-8"))
        if r.get("arxiv_id") != aid:
            fail(f"{f.name}: id mismatch")
        keys = set(r)
        want = ELIG_KEYS if r.get("eligible") else INEL_KEYS
        if keys != want:
            fail(f"{f.name}: keys differ: missing {sorted(want - keys)}, extra {sorted(keys - want)}")
        if r["source_read"] not in ("arxiv_html", "arxiv_pdf", "inaccessible"):
            fail(f"{f.name}: bad source_read")
        if not isinstance(r["borderline"], bool):
            fail(f"{f.name}: borderline must be bool")
        e = entries[aid]
        rec = {"position": pos, "arxiv_id": aid, "title": e["title"],
               "first_submitted": e["first_submitted"], "primary_category": e["primary_category"]}
        rec.update({k: v for k, v in r.items() if k != "arxiv_id"})
        if rec["eligible"]:
            for k in FIELDS:
                if set(rec[k]) != {"value", "source"} or rec[k]["source"] not in SOURCES or not rec[k]["value"]:
                    fail(f"{f.name}: bad field {k}")
            if rec["dim"] not in (2, 3) or rec["benchmark_family"] not in FAMILIES:
                fail(f"{f.name}: bad dim/family")
            if not isinstance(rec["ambiguous"], bool):
                fail(f"{f.name}: ambiguous must be bool")
            if rec["ambiguous"] != bool(rec["ambiguous_reason"].strip()):
                fail(f"{f.name}: ambiguous_reason must be non-empty iff ambiguous")
            for k in ["example_ref", "statement_excerpt", "evidence", "notes"]:
                if not rec.get(k):
                    fail(f"{f.name}: empty {k}")
            words = len(rec["statement_excerpt"].replace("[...]", " ").split())
            if words > 60:
                fail(f"{f.name}: excerpt has {words} whitespace tokens (>60)")
            if not rec["notes"].count("In-scope: "):
                fail(f"{f.name}: notes lack the 'In-scope: ...' reason")
            check_slots(f.name, rec["in_scope_structured_grid"], rec["ambiguous"], rec["ambiguity_slots"])
        else:
            if rec["ineligible_reason"] not in REASONS:
                fail(f"{f.name}: bad ineligible_reason")
        out.append(rec)
    return out


def counts(recs):
    elig = [r for r in recs if r["eligible"]]
    inel = [r for r in recs if not r["eligible"]]
    c = {
        "n": len(recs), "elig": elig, "inel": inel,
        "dims": collections.Counter(r["dim"] for r in elig),
        "fams": collections.Counter(r["benchmark_family"] for r in elig),
        "reasons": collections.Counter(r["ineligible_reason"] for r in inel),
        "src": {k: collections.Counter(r[k]["source"] for r in elig) for k in FIELDS},
        "amb": sum(r["ambiguous"] for r in elig),
        "border": sum(bool(r.get("borderline")) for r in recs),
        "src_read": collections.Counter(r["source_read"] for r in recs),
        "na_filter": sum("not applicable (discrete truss/frame" in r["filter_radius"]["value"].lower() for r in elig),
    }
    crit = ["geometry", "supports", "loads", "volume_fraction"]
    c["fig_fields"] = sum(c["src"][k]["figure"] for k in FIELDS)
    c["miss_fields"] = sum(c["src"][k]["missing"] for k in FIELDS)
    c["ex_fig"] = sum(any(r[k]["source"] == "figure" for k in FIELDS) for r in elig)
    c["ex_miss"] = sum(any(r[k]["source"] == "missing" for k in FIELDS) for r in elig)
    c["ex_crit_fig"] = sum(any(r[k]["source"] == "figure" for k in crit) for r in elig)
    c["ex_crit_miss"] = sum(any(r[k]["source"] == "missing" for k in crit) for r in elig)
    ins = [r for r in elig if r["in_scope_structured_grid"]]
    c["ins"] = len(ins)
    c["ins_dims"] = collections.Counter(r["dim"] for r in ins)
    c["ins_amb"] = collections.Counter(r["dim"] for r in ins if r["ambiguous"])
    c["n_slots"] = sum(len(r["ambiguity_slots"]) for r in ins)
    c["n_slots_layout"] = sum(sum(not s.endswith("[scale only]") for s in r["ambiguity_slots"]) for r in ins)
    return c


def count_lines(c):
    L = []
    e = len(c["elig"])
    L.append(f"- Eligible: **{e} / {c['n']}**. Ineligible: {len(c['inel'])} "
             f"({', '.join(f'{k}: {v}' for k, v in c['reasons'].most_common())}).")
    L.append(f"- Borderline eligibility calls (flagged `borderline: true`): {c['border']}.")
    L.append(f"- Dimension of primary example: 2-D {c['dims'].get(2, 0)}, 3-D {c['dims'].get(3, 0)}.")
    fams = c["fams"]
    L.append(f"- Benchmark family: {', '.join(f'{f} {fams.get(f, 0)}' for f in FAMILIES)}.")
    L.append(f"- Ambiguous primary examples (text plus figure admit more than one reading): **{c['amb']} / {e}**.")
    L.append(f"- In scope for a structured-grid compliance solver: **{c['ins']} / {e}** "
             f"(2-D {c['ins_dims'].get(2, 0)}, 3-D {c['ins_dims'].get(3, 0)}).")
    L.append(f"- In scope and ambiguous: **{sum(c['ins_amb'].values())}** (2-D {c['ins_amb'].get(2, 0)}, "
             f"3-D {c['ins_amb'].get(3, 0)}); ambiguity slots {c['n_slots']}, of which "
             f"{c['n_slots'] - c['n_slots_layout']} only scale the compliance value ('[scale only]').")
    L.append(f"- Field instances (8 fields x {e} examples = {8 * e}): figure-only {c['fig_fields']}, "
             f"missing {c['miss_fields']}. Examples with at least one figure-only field: {c['ex_fig']}; "
             f"with at least one missing field: {c['ex_miss']}.")
    L.append(f"- Restricted to geometry, supports, loads, volume fraction: examples with at least one figure-only "
             f"field {c['ex_crit_fig']}; with at least one missing field {c['ex_crit_miss']}.")
    L.append(f"- Filter radius recorded as 'not applicable' (discrete truss/frame models, tagged missing): {c['na_filter']}.")
    L.append("")
    L.append("Source tag per field (eligible examples only):")
    L.append("")
    L.append("| Field | text | figure | code_or_appendix | missing |")
    L.append("|---|---|---|---|---|")
    for k in FIELDS:
        L.append(f"| {k} | " + " | ".join(str(c["src"][k][s]) for s in SOURCES) + " |")
    return L


def md_escape(s):
    return str(s).replace("|", "/").replace("\n", " ")


def build_md(v2, combined, frame, supp):
    c2, cc = counts(v2), counts(combined)
    L = ["# Literature screen v2: arXiv minimum-compliance TO examples, positions 61-150", ""]
    L.append(f"Frame: `arxiv_frame_20261022.json` ({frame['n_in_frame']} papers, query `{frame['search_query']}`, "
             f"retrieved {frame['retrieved_utc']}; frozen order sha256(\"20261022:\" + id) ascending). "
             f"This file screens positions {FIRST}-{LAST}; positions 1-60 are in `literature_screen_v1.json` / `.md` "
             f"(not edited).")
    L.append(f"Full text read (61-150): {c2['src_read'].get('arxiv_html', 0)} arXiv HTML, "
             f"{c2['src_read'].get('arxiv_pdf', 0)} arXiv PDF, {c2['src_read'].get('inaccessible', 0)} inaccessible.")
    L.append("")
    L.append(f"## Counts, positions {FIRST}-{LAST}")
    L.append("")
    L += count_lines(c2)
    L.append("")
    L.append("## Combined counts, positions 1-150 (v1 records + v1 in-scope supplement below + v2 records)")
    L.append("")
    L += count_lines(cc)
    L.append("")
    amb3 = [r for r in combined if r["eligible"] and r["in_scope_structured_grid"] and r["ambiguous"] and r["dim"] == 3]
    L.append(f"### In-scope ambiguous 3-D examples, positions 1-150 ({len(amb3)})")
    L.append("")
    for r in amb3:
        L.append(f"- #{r['position']} {r['arxiv_id']} ({r['benchmark_family']}; {md_escape(r['example_ref'])})")
        for s in r["ambiguity_slots"]:
            L.append(f"  - {md_escape(s)}")
    L.append("")
    L.append("## Screening rules applied")
    L.append("")
    L.append("Identical to v1 (eligibility, primary example, source tags, family mapping, 60-word excerpts); "
             "repeated here for completeness.")
    L.append("")
    L.append("- Eligible: original paper with at least one numerical example of structural TO in linear elasticity, "
             "compliance (stiffness) objective, a volume constraint, and prescribed loads and supports. "
             "A mass constraint on a single material and a volume penalty in a loss were accepted as volume constraints. "
             "Additional constraints (stress, AM, buckling) were accepted and noted.")
    L.append("- Primary example: first numerical example in document order that meets eligibility. Where a paper "
             "reports only aggregate results over randomly generated task sets before any individual case, the first "
             "individual instance shown with an optimized design was taken.")
    L.append("- Source tag: `text` if stated in prose (incl. tables in the body); `code_or_appendix` if stated only in "
             "a code listing or appendix; `figure` if only visible in a figure or its caption; `missing` if not found. "
             "`missing` also covers fields that do not apply to the method (no passive region mentioned; no filter in "
             "phase-field, level-set, neural or truss methods); the value string says which.")
    L.append("- Family: MBB = simply supported or symmetric-half beam with a mid-span point load (incl. 3-point "
             "bending); bridge = supported span with distributed or deck loads; other = named benchmark outside the list; "
             "custom = application geometry or random task.")
    L.append("- Excerpts are verbatim from the arXiv HTML/PDF text (math as LaTeX alt text); `[...]` marks an omission.")
    L.append("- New field `in_scope_structured_grid` (eligible records only): true if the primary example's "
             "boundary-value problem can be rebuilt on a structured-grid, single-material, isotropic linear-elastic "
             "compliance solver: rectangle/box domain, optionally minus element-removed holes, notches or L-cuts "
             "(staircase approximation of curved holes accepted) and with fixed solid/void element sets; supports on "
             "nodes, edges or faces; design-independent point, line or patch loads (several loads or load cases "
             "allowed); volume or single-material mass constraint. False for scanned or CAD/free-form geometry, "
             "non-rectangular outer domains, lattice/truss/frame/bar-and-hinge models, shells/plates, self-weight-only "
             "or other design-dependent loads, thermal or other multiphysics coupling, geometric/material nonlinearity "
             "or contact, dynamics, two or more solid materials, anisotropic base material, and loads applied through "
             "rigid multipoint ties. The design parametrisation (SIMP, level set, phase field, homogenisation, "
             "components, neural, microstructure grading) does not affect the call. The one-line reason is in `notes` "
             "('In-scope: ...').")
    L.append("- New field `ambiguity_slots` (eligible records only): non-empty exactly for in-scope ambiguous examples; "
             "one string per underdetermined quantity, '<quantity>: <reason> (<evidence location>)'. Quantities that "
             "only scale the compliance value and not the optimal layout (a single load's magnitude, Young's modulus) "
             "carry the suffix '[scale only]'.")
    L.append("")
    L.append("## Process notes and limitations")
    L.append("")
    L.append("- Full texts were fetched with `scripts/fetch_papers.py` (sequential, 3 s between arXiv requests, "
             "plain python-urllib user agent, no e-mail). Raw downloads were kept outside the repository; rerun the "
             "script to reproduce them.")
    L.append("- Problem-definition figures were downloaded one at a time through the same script and inspected "
             "visually when a field was not in prose; PDF-only papers were read from rendered pages where pdftotext "
             "lost symbols.")
    L.append("- PROCESS_NOTE_SCREENERS")
    L.append("- The in-scope call and the slots for positions 1-60 were added in this round from the v1 records and "
             "re-reads of the source text for the in-scope ambiguous 3-D cases (#5, #23, #40) and #29; "
             "they are listed in the supplement table below because `literature_screen_v1.json` was not edited.")
    L.append("- Ambiguity, family and in-scope assignments are judgement calls by a single screener; no second "
             "independent coder, no inter-rater agreement. `borderline: true` marks debatable eligibility.")
    L.append("")
    L.append(f"## Per-paper table, positions {FIRST}-{LAST}")
    L.append("")
    L.append("Source codes in order geometry, supports, loads, passive, volume fraction, mesh, material, filter: "
             "t = text, f = figure, c = code/appendix, m = missing. In-scope = `in_scope_structured_grid`; "
             "Slots = number of ambiguity slots (full text in the JSON).")
    L.append("")
    L.append("| # | arXiv id | Eligible / reason | Dim | Family | Sources | Amb. | In-scope | Slots | Primary example / note |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    code = {"text": "t", "figure": "f", "code_or_appendix": "c", "missing": "m"}
    for r in v2:
        flag = " (borderline)" if r.get("borderline") else ""
        if r["eligible"]:
            s = "".join(code[r[k]["source"]] for k in FIELDS)
            L.append(f"| {r['position']} | {r['arxiv_id']} | yes{flag} | {r['dim']} | {r['benchmark_family']} | "
                     f"`{s}` | {'yes' if r['ambiguous'] else 'no'} | "
                     f"{'yes' if r['in_scope_structured_grid'] else 'no'} | {len(r['ambiguity_slots'])} | "
                     f"{md_escape(r['example_ref'])} |")
        else:
            L.append(f"| {r['position']} | {r['arxiv_id']} | no: {r['ineligible_reason']}{flag} | - | - | - | - | - | - | "
                     f"{md_escape(r['ineligible_note'])} |")
    L.append("")
    L.append("## Supplement: in-scope call and ambiguity slots for eligible positions 1-60")
    L.append("")
    L.append("| # | arXiv id | Dim | Amb. (v1) | In-scope | Reason | Ambiguity slots |")
    L.append("|---|---|---|---|---|---|---|")
    for r in combined:
        if r["position"] > 60 or not r["eligible"]:
            continue
        sp = supp[str(r["position"])]
        slots = "; ".join(md_escape(s) for s in sp["slots"]) or "-"
        L.append(f"| {r['position']} | {r['arxiv_id']} | {r['dim']} | {'yes' if r['ambiguous'] else 'no'} | "
                 f"{'yes' if sp['in_scope'] else 'no'} | {md_escape(sp['reason'])} | {slots} |")
    L.append("")
    return "\n".join(L)


def main():
    rec_dir, supp_path = Path(sys.argv[1]), Path(sys.argv[2])
    note = sys.argv[3] if len(sys.argv) > 3 else ""
    frame = json.loads((TASKS / "arxiv_frame_20261022.json").read_text(encoding="utf-8"))
    v1 = json.loads((TASKS / "literature_screen_v1.json").read_text(encoding="utf-8"))
    supp = json.loads(supp_path.read_text(encoding="utf-8"))
    v1_elig = {str(r["position"]) for r in v1 if r["eligible"]}
    if set(supp) != v1_elig:
        fail(f"supplement positions differ from v1 eligible: {sorted(set(supp) ^ v1_elig, key=int)}")
    v1x = []
    for r in v1:
        r = dict(r)
        if r["eligible"]:
            sp = supp[str(r["position"])]
            r["in_scope_structured_grid"], r["ambiguity_slots"] = sp["in_scope"], sp["slots"]
            check_slots(f"v1 #{r['position']}", sp["in_scope"], r["ambiguous"], sp["slots"])
        v1x.append(r)
    v2 = load_records(rec_dir, frame)
    md = build_md(v2, v1x + v2, frame, supp).replace("PROCESS_NOTE_SCREENERS", note)
    (TASKS / "literature_screen_v2.json").write_text(json.dumps(v2, indent=1, ensure_ascii=False), encoding="utf-8")
    (TASKS / "literature_screen_v2.md").write_text(md, encoding="utf-8")
    print(f"wrote {len(v2)} records; combined {len(v1x) + len(v2)}")


if __name__ == "__main__":
    main()
