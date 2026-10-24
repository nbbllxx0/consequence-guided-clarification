"""Assemble the literature screen from per-paper screening records.

Usage: python build_screen.py RECORDS_DIR
Reads tasks/arxiv_frame_20261022.json and RECORDS_DIR/NN_<id>.json (one per
screened paper, NN = 1-based frozen-order position) and writes
tasks/literature_screen_v1.json (list of records in frozen order) and
tasks/literature_screen_v1.md (counts and one table line per paper).
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
N_SCREEN = 60


def load_records(rec_dir: Path, frame: dict) -> list:
    entries = {e["id"]: e for e in frame["entries"]}
    out = []
    for pos, aid in enumerate(frame["frozen_order"][:N_SCREEN], start=1):
        f = rec_dir / f"{pos:02d}_{aid}.json"
        if not f.exists():
            sys.exit(f"missing record {f.name}")
        r = json.loads(f.read_text(encoding="utf-8"))
        if r["arxiv_id"] != aid:
            sys.exit(f"{f.name}: id mismatch")
        e = entries[aid]
        rec = {"position": pos, "arxiv_id": aid, "title": e["title"],
               "first_submitted": e["first_submitted"], "primary_category": e["primary_category"]}
        rec.update({k: v for k, v in r.items() if k != "arxiv_id"})
        if rec["eligible"]:
            for k in FIELDS:
                if rec[k].get("source") not in SOURCES:
                    sys.exit(f"{f.name}: bad source for {k}")
            if rec["dim"] not in (2, 3) or rec["benchmark_family"] not in FAMILIES:
                sys.exit(f"{f.name}: bad dim/family")
            if not isinstance(rec["ambiguous"], bool):
                sys.exit(f"{f.name}: ambiguous must be bool")
            for k in ["example_ref", "statement_excerpt", "evidence"]:
                if not rec.get(k):
                    sys.exit(f"{f.name}: empty {k}")
            words = len(rec["statement_excerpt"].replace("[...]", " ").split())
            if words > 60:
                sys.exit(f"{f.name}: excerpt has {words} whitespace tokens (>60)")
        else:
            if rec.get("ineligible_reason") not in REASONS:
                sys.exit(f"{f.name}: bad ineligible_reason")
        rec.setdefault("borderline", False)
        out.append(rec)
    return out


def md_escape(s: str) -> str:
    return str(s).replace("|", "/").replace("\n", " ")


def build_md(recs: list, frame: dict) -> str:
    elig = [r for r in recs if r["eligible"]]
    inel = [r for r in recs if not r["eligible"]]
    dims = collections.Counter(r["dim"] for r in elig)
    fams = collections.Counter(r["benchmark_family"] for r in elig)
    reasons = collections.Counter(r["ineligible_reason"] for r in inel)
    src = {k: collections.Counter(r[k]["source"] for r in elig) for k in FIELDS}
    n_fig_fields = sum(src[k]["figure"] for k in FIELDS)
    n_miss_fields = sum(src[k]["missing"] for k in FIELDS)
    ex_with_fig = sum(any(r[k]["source"] == "figure" for k in FIELDS) for r in elig)
    ex_with_miss = sum(any(r[k]["source"] == "missing" for k in FIELDS) for r in elig)
    crit = ["geometry", "supports", "loads", "volume_fraction"]
    ex_crit_fig = sum(any(r[k]["source"] == "figure" for k in crit) for r in elig)
    ex_crit_miss = sum(any(r[k]["source"] == "missing" for k in crit) for r in elig)
    n_amb = sum(r["ambiguous"] for r in elig)
    n_border = sum(bool(r.get("borderline")) for r in recs)
    na_filter = sum("not applicable" in r["filter_radius"]["value"].lower() for r in elig)
    src_read = collections.Counter(r["source_read"] for r in recs)

    L = []
    L.append("# Literature screen v1: arXiv minimum-compliance TO examples")
    L.append("")
    L.append(f"Frame: `arxiv_frame_20261022.json` ({frame['n_in_frame']} papers, query `{frame['search_query']}`, "
             f"retrieved {frame['retrieved_utc']}, API totalResults {frame['api_totalResults']}; "
             f"kept first-submitted {frame['date_filter']['min']} to {frame['date_filter']['max']}). "
             f"Screened: first {len(recs)} papers in frozen order (sha256(\"20261022:\" + id) ascending).")
    L.append(f"Full text read: {src_read.get('arxiv_html', 0)} arXiv HTML, {src_read.get('arxiv_pdf', 0)} arXiv PDF, "
             f"{src_read.get('inaccessible', 0)} inaccessible.")
    L.append("")
    L.append("## Counts")
    L.append("")
    L.append(f"- Eligible: **{len(elig)} / {len(recs)}**. Ineligible: {len(inel)} "
             f"({', '.join(f'{k}: {v}' for k, v in reasons.most_common())}).")
    L.append(f"- Borderline eligibility calls (flagged `borderline: true`): {n_border}.")
    L.append(f"- Dimension of primary example: 2-D {dims.get(2, 0)}, 3-D {dims.get(3, 0)}.")
    L.append(f"- Benchmark family: {', '.join(f'{f} {fams.get(f, 0)}' for f in FAMILIES)}.")
    L.append(f"- Ambiguous primary examples (text plus figure admit more than one reading): **{n_amb} / {len(elig)}**.")
    L.append(f"- Field instances (8 fields x {len(elig)} examples = {8 * len(elig)}): figure-only {n_fig_fields}, "
             f"missing {n_miss_fields}. Examples with at least one figure-only field: {ex_with_fig}; "
             f"with at least one missing field: {ex_with_miss}.")
    L.append(f"- Restricted to geometry, supports, loads, volume fraction: examples with at least one figure-only "
             f"field {ex_crit_fig}; with at least one missing field {ex_crit_miss}.")
    L.append(f"- Filter radius recorded as 'not applicable' (discrete truss/frame models, tagged missing): {na_filter}.")
    L.append("")
    L.append("Source tag per field (eligible examples only):")
    L.append("")
    L.append("| Field | text | figure | code_or_appendix | missing |")
    L.append("|---|---|---|---|---|")
    for k in FIELDS:
        L.append(f"| {k} | " + " | ".join(str(src[k][s]) for s in SOURCES) + " |")
    L.append("")
    L.append("## Screening rules applied")
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
    L.append("")
    L.append("## Process notes and limitations")
    L.append("")
    L.append("- Full texts were fetched with `scripts/fetch_papers.py` (sequential, 3 s between arXiv requests, "
             "plain python-urllib user agent). Raw downloads were kept outside the repository and are not part of "
             "this deliverable; rerun the script to reproduce them.")
    L.append("- Problem-definition figures were downloaded one at a time and inspected visually when a field was not "
             "in prose; PDF-only papers were read from rendered pages where pdftotext lost symbols.")
    L.append("- The HTML-to-text converter first dropped display equations and code listings; it was fixed and all "
             "texts reconverted. Records with figure-tagged fields were rechecked against the recovered listings "
             "(one change: #19 supports moved to code_or_appendix; #12 supports/loads are in a body code listing).")
    L.append("- Positions 10-60 were screened by parallel copies of the same screening agent under the identical rule "
             "set above, then spot-checked (#12, #13, #19, #22, #24, #29, #47, #54, #57, #59); positions 1-9 were "
             "screened directly. Single-screener judgement: no second independent coder, no inter-rater agreement.")
    L.append("- Ambiguity and family assignments are judgement calls; `borderline: true` marks debatable eligibility.")
    L.append("")
    L.append("## Per-paper table")
    L.append("")
    L.append("Source codes in order geometry, supports, loads, passive, volume fraction, mesh, material, filter: "
             "t = text, f = figure, c = code/appendix, m = missing.")
    L.append("")
    L.append("| # | arXiv id | Eligible / reason | Dim | Family | Sources | Amb. | Primary example / note |")
    L.append("|---|---|---|---|---|---|---|---|")
    code = {"text": "t", "figure": "f", "code_or_appendix": "c", "missing": "m"}
    for r in recs:
        flag = " (borderline)" if r.get("borderline") else ""
        if r["eligible"]:
            s = "".join(code[r[k]["source"]] for k in FIELDS)
            L.append(f"| {r['position']} | {r['arxiv_id']} | yes{flag} | {r['dim']} | {r['benchmark_family']} | "
                     f"`{s}` | {'yes' if r['ambiguous'] else 'no'} | {md_escape(r['example_ref'])} |")
        else:
            L.append(f"| {r['position']} | {r['arxiv_id']} | no: {r['ineligible_reason']}{flag} | - | - | - | - | "
                     f"{md_escape(r['ineligible_note'])} |")
    L.append("")
    return "\n".join(L)


def main():
    rec_dir = Path(sys.argv[1])
    frame = json.loads((TASKS / "arxiv_frame_20261022.json").read_text(encoding="utf-8"))
    recs = load_records(rec_dir, frame)
    (TASKS / "literature_screen_v1.json").write_text(json.dumps(recs, indent=1, ensure_ascii=False), encoding="utf-8")
    (TASKS / "literature_screen_v1.md").write_text(build_md(recs, frame), encoding="utf-8")
    print(f"wrote {len(recs)} records")


if __name__ == "__main__":
    main()
