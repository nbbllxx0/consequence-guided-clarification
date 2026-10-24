"""E05 (ablation): can a flagship LLM enumerate the admissible readings of a literature task?

Each model receives the paper's full text (references removed, figure image links removed; figures
themselves are not provided) and a neutral locator of the example. It must list every detail needed
to re-run the example on a structured-grid, single-material, linear-elastic minimum-compliance
solver that the text does not determine uniquely, with admissible readings and a layout/scale tag.
The annotation (src/littasks.py) is never shown to the models.

Models (personal CLI logins of the author; no API keys):
  codex  : gpt-6.1-sol, model_reasoning_effort=max, `codex exec` 0.162.1, empty working dir,
           read-only sandbox, ephemeral; runs that executed any command are flagged.
  claude : claude-opus-5-5, effort max, `claude -p --safe-mode --tools ""` (no CLAUDE.md, plugins, hooks,
           MCP or tools), neutral system prompt, empty working dir, JSON schema output.

Usage: python experiments/e05_llm_readings.py [--models codex,claude] [--reps 3] [--workers 4] [task ids]
Outputs: results/e05/raw/<model>/<tid>_r<k>.json (parsed items + metadata), results/e05/inputs/<tid>.txt
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import littasks as lt  # noqa: E402

OUT = os.path.join(ROOT, "results", "e05")
PAPERS = [os.path.join(ROOT, "tasks", "sources")]          # local copies of the 41 source papers
CODEX = os.environ.get("CODEX_EXE", "codex")                # the runs used Codex CLI 0.162.1
MODELS = {"codex": "gpt-6.1-sol", "claude": "claude-opus-5-5"}

# Neutral locators: section / figure / example name only (no setup details).
LOCATOR = {
    "L01": "Sec. 4 'Example designs', Fig. 4 (the first problem instance shown with a design)",
    "L02": "Sec. 6.1.1, Fig. 3 (left), the 3-D cantilever beam",
    "L04": "Sec. 4.2, the Michell cantilever beam",
    "L05": "Sec. 4.1, Fig. 7, the rectangular cantilever",
    "L06": "Sec. 4.1 'Cantilever supports', configuration 1",
    "L07": "Sec. 4.1.1, the 2-D cantilever beam",
    "L08": "Sec. 4.1, the 2-D cantilever beam of Table 1",
    "L09": "Sec. 5, Fig. 3, row 1 (the first dataset instance shown with a SIMP design)",
    "L11": "Sec. 3.5, Fig. 2, benchmark problem ID 3 of Table 3",
    "L12": "Results, 'Structures optimization' and 'Mechanical stiffness', Fig. 6 (right) and Fig. 7",
    "L13": "Sec. 2.1 / 3.1, the cantilever beam (Fig. 1(a), Fig. 3(b))",
    "L14": "Sec. 2, the cantilever benchmark of Fig. 1 and Table 1",
    "L15": "Sec. 3.5 'Benchmark problems' and Sec. 4.1, the cantilever beam, 120 x 60 'Long' preset",
    "L16": "Sec. 4.1.1, Fig. 6",
    "L17": "Sec. 4.1, the structural cantilever baseline design minimizing elastic compliance (Fig. 3)",
    "L18": "Introduction, the 2-D cantilever of Fig. 1",
    "L19": "Sec. 4.1.1, the 2-D MBB beam, single-material case (Table 2, m = 1)",
    "L20": "Sec. V-A, the MBB beam application (Fig. 2B)",
    "L21": "Sec. 5.1, Fig. 5(c), 'SIMP reference'",
    "L22": "Sec. 3.3, Fig. 7(a)",
    "L23": "Sec. 3.1, the uni-axial compression example (Fig. 5), pure-compliance case",
    "L24": "Sec. 5.4, the 3-D beam (Fig. 9)",
    "L25": "Results, 'Compliance minimization', the first problem (Fig. 2a)",
    "L27": "Sec. 7.1.1, the mid-load problem (Fig. 6(a), Fig. 8)",
    "L28": "Sec. 2.1 / Sec. 4, the cantilever beam of Fig. 1, single-material extended SIMP case",
    "L29": "Sec. 2.1, the cantilever plate (Fig. 2)",
    "L30": "Sec. 2, Fig. 1",
    "L31": "Sec. 5.2, Case 1, Fig. 1",
    "L33": "Supplementary Note A.14, the nanopillar designed by FEM-TO (Fig. S18)",
    "L34": "Sec. 7.1, example CANT-16-2-2-5 (Fig. 2(a), Table 1)",
    "L35": "Sec. 4.1 'Validation', the 3-D cantilever (Fig. 3)",
    "L36": "Sec. 2.1, Fig. 1",
    "L37": "Sec. 4.1.1, the double-clamped beam, low-fidelity stiffness designs (Fig. 8)",
    "L38": "Sec. 4, the example for performance verification (Fig. 11)",
    "L39": "Sec. 3.4, the MBB beam (Fig. 1(a), Fig. 2(a))",
    "L40": "Sec. 5, the MBB beam (Appendix C, Fig. 5)",
    "L41": "Sec. 4.6, case study 1 (Fig. 6)",
    "L42": "Sec. II.1, the 2-D cantilever of Fig. 1",
    "L43": "Sec. 4.3, Fig. 5, row 1",
    "L44": "Sec. 5.1, Table 3, row cantilever_basic",
    "L45": "Sec. 4.1, the cantilever beam (Fig. 6, Table 1)",
}

CATEGORIES = ["domain_extent", "support_location_extent", "support_type", "load_position",
              "load_extent_distribution", "load_direction", "load_magnitude", "volume_fraction",
              "passive_region", "material", "filter_or_solver_setting", "mesh", "other"]

SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["items"],
    "properties": {"items": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["category", "entity", "issue", "description", "readings", "effect"],
        "properties": {
            "category": {"type": "string", "enum": CATEGORIES},
            "entity": {"type": "string"},
            "issue": {"type": "string", "enum": ["missing", "vague", "conflicting", "figure_only"]},
            "description": {"type": "string"},
            "readings": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "effect": {"type": "string", "enum": ["layout", "scale_only", "unsure"]}}}}}}

PROMPT = """You are given the full text of a research paper (references removed; figure captions are kept,
but the figure images are NOT available to you). Focus only on this example: {loc}.

Goal: an engineer must re-run exactly this example on a structured-grid, single-material, linear-elastic,
minimum-compliance (volume-constrained) topology-optimization solver.

List every detail needed to set up that problem (design domain and its extent, supports, loads, passive
regions, volume fraction, material, filter or solver settings, mesh) that the text does NOT determine
uniquely: missing, vague, conflicting between places, or conveyed only by a figure you cannot see.
For each detail give:
- category (from the allowed list),
- entity (what it applies to, e.g. 'load on right edge'),
- issue type,
- a short description with where in the text it arises,
- the admissible readings: a finite list of concrete alternatives an engineer could reasonably adopt
  (values, positions as fractions of a length, or short descriptions),
- effect: 'layout' if the readings can change the optimal layout, 'scale_only' if they only scale the
  compliance value (e.g. load magnitude, Young's modulus), 'unsure' otherwise.
Do not list details that the text states unambiguously. Use only the text below; do not run commands,
browse, or read any files. Answer with JSON that matches the provided schema.

=== PAPER TEXT ===
{text}
"""


def paper_text(arxiv):
    for d in PAPERS:
        p = os.path.join(d, arxiv, "text.txt")
        if os.path.exists(p):
            with open(p, encoding="utf-8", errors="replace") as fh:
                t = fh.read()
            break
    else:
        raise FileNotFoundError(arxiv)
    m = re.search(r"^## *(References|REFERENCES|Bibliography|Reference)\b.*$", t, re.M)
    if m:
        t = t[:m.start()]
    return re.sub(r"\s*\{img:[^}]*\}", "", t).strip()


def build_input(tid):
    T = lt.TASKS[tid]
    txt = PROMPT.format(loc=LOCATOR[tid], text=paper_text(T["source"]["arxiv"]))
    os.makedirs(os.path.join(OUT, "inputs"), exist_ok=True)
    with open(os.path.join(OUT, "inputs", f"{tid}.txt"), "w", encoding="utf-8") as fh:
        fh.write(txt)
    return txt


def _parse(s):
    s = s.strip()
    m = re.search(r"\{.*\}", s, re.S)
    return json.loads(m.group(0)) if m else None


def run_codex(tid, prompt, rep):
    with tempfile.TemporaryDirectory() as wd:
        schema = os.path.join(wd, "schema.json")
        last = os.path.join(wd, "last.txt")
        with open(schema, "w") as fh:
            json.dump(SCHEMA, fh)
        cmd = [CODEX, "exec", "-m", MODELS["codex"], "-c", "model_reasoning_effort=max", "-C", wd,
               "-s", "read-only", "--skip-git-repo-check", "--ephemeral", "--json",
               "--output-schema", schema, "-o", last, "-"]
        t0 = time.time()
        p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8", timeout=3600)
        wall = time.time() - t0
        events = [json.loads(l) for l in p.stdout.splitlines() if l.strip().startswith("{")]
        cmds = [e for e in events if "command" in json.dumps(e).lower() and "exec" in json.dumps(e).lower()]
        out = open(last, encoding="utf-8").read() if os.path.exists(last) else ""
    return dict(raw=out, parsed=_parse(out) if out else None, wall_s=wall, returncode=p.returncode,
                executed_command_events=len(cmds), stderr_tail=p.stderr[-2000:])


CLAUDE_SYSTEM = "You are a careful engineering analyst. Answer the user's request using only the text provided."


def run_claude(tid, prompt, rep):
    # --safe-mode: no CLAUDE.md, skills, plugins, hooks or MCP; --tools "": no tools; neutral system prompt;
    # empty working directory. (--bare would skip the subscription login.)
    cmd = ["claude", "-p", "--safe-mode", "--model", MODELS["claude"], "--effort", "max", "--tools", "",
           "--system-prompt", CLAUDE_SYSTEM, "--output-format", "json", "--json-schema", json.dumps(SCHEMA),
           "--no-session-persistence", "--strict-mcp-config"]
    t0 = time.time()
    with tempfile.TemporaryDirectory() as wd:
        p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8", timeout=3600,
                           cwd=wd)
    wall = time.time() - t0
    parsed, meta = None, {}
    try:
        res = json.loads(p.stdout)
        meta = {k: res.get(k) for k in ("model", "num_turns", "is_error", "total_cost_usd", "usage")}
        so = res.get("structured_output")
        parsed = so if isinstance(so, dict) else _parse(res.get("result", ""))
        raw = json.dumps(so) if so is not None else res.get("result", "")
    except Exception:
        raw = p.stdout
    return dict(raw=raw, parsed=parsed, wall_s=wall, returncode=p.returncode, meta=meta,
                stderr_tail=p.stderr[-2000:])


RUNNERS = {"codex": run_codex, "claude": run_claude}


def job(model, tid, rep):
    path = os.path.join(OUT, "raw", model, f"{tid}_r{rep}.json")
    if os.path.exists(path):
        with open(path) as fh:
            r = json.load(fh)
        if r.get("parsed"):
            return path, "cached"
    prompt = build_input(tid)
    r = RUNNERS[model](tid, prompt, rep)
    r.update(task=tid, model=model, model_id=MODELS[model], rep=rep, locator=LOCATOR[tid],
             finished=time.strftime("%Y-%m-%dT%H:%M:%S"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(r, fh, indent=1)
    n = len(r["parsed"]["items"]) if r.get("parsed") else None
    return path, f"{model} {tid} r{rep}: items={n} rc={r['returncode']} {r['wall_s']:.0f}s"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="codex,claude")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("tids", nargs="*")
    a = ap.parse_args()
    tids = a.tids or list(lt.TASKS)
    missing = [t for t in tids if t not in LOCATOR]
    if missing:
        raise SystemExit(f"no locator for {missing}")
    jobs = [(m, t, r) for r in range(a.reps) for t in tids for m in a.models.split(",")]
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for path, msg in ex.map(lambda j: job(*j), jobs):
            print(msg, flush=True)


if __name__ == "__main__":
    main()
