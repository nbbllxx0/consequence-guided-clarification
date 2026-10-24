"""E06: blind second annotation of the 41 literature tasks by Codex (gpt-6.1-sol, max reasoning).

The annotator receives the screening rules, the neutral example locator, the paper text (references
removed) and the paper's figure images (tasks/sources/<id>/figs, up to MAX_FIGS). It never sees the
first annotation (src/littasks.py, screens v1-v3). It returns the ambiguity slots of the example with
admissible readings, in the E05 schema plus an evidence location. Runs are in an empty working
directory with a read-only sandbox; runs that executed any command are flagged.
Agreement with the first annotation is computed by experiments/a06_agreement.py.

Usage: python experiments/e06_codex_reannotation.py [--workers 2] [task ids]
Output: results/e06/raw/<tid>.json
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
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import e05_llm_readings as e05  # noqa: E402
import littasks as lt  # noqa: E402

OUT = os.path.join(ROOT, "results", "e06")
MAX_FIGS = 12

SCHEMA = json.loads(json.dumps(e05.SCHEMA))
SCHEMA["properties"]["items"]["items"]["properties"]["evidence"] = {"type": "string"}
SCHEMA["properties"]["items"]["items"]["required"].append("evidence")

RULES = """Annotation rules (identical to the first annotator's screening protocol):
- The example is rebuilt on a structured-grid, single-material, isotropic linear-elastic minimum-compliance
  solver with a volume constraint: rectangle/box domain (optionally with element-removed holes, notches or
  L-cuts and fixed solid/void element sets), supports on nodes, edges or faces, design-independent point, line
  or patch loads. The design parametrisation of the paper (SIMP, level set, neural, ...) does not matter.
- An ambiguity slot is one quantity of the boundary-value problem or volume constraint that text plus figures
  leave underdetermined: missing, vague, conflicting between places, or readable only approximately from a
  figure. For each slot give a finite set of admissible readings an engineer could reasonably adopt.
- Quantities that only scale the compliance value (a single load's magnitude, Young's modulus) are tagged
  effect = 'scale_only'.
- Do not list quantities that text or figures determine unambiguously.
- Give the evidence location (section, figure, table, equation) for each slot."""

PROMPT = """You are an independent annotator of a literature benchmark for structural topology optimization.
{rules}

Example to annotate: {loc}.
The paper's figure images are attached (file names follow the paper's figure order where known); the figure
captions are in the text. Use only the attached figures and the text below; do not run commands, browse, or
read any files. Answer with JSON that matches the provided schema.

=== PAPER TEXT ===
{text}
"""


def figures(arxiv):
    d = os.path.join(ROOT, "tasks", "sources", arxiv, "figs")
    if not os.path.isdir(d):
        return []
    fs = sorted(f for f in os.listdir(d) if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")))
    return [os.path.join(d, f) for f in fs[:MAX_FIGS]]


def run(tid):
    path = os.path.join(OUT, "raw", f"{tid}.json")
    if os.path.exists(path):
        with open(path) as fh:
            if json.load(fh).get("parsed"):
                return f"{tid}: cached"
    a = lt.TASKS[tid]["source"]["arxiv"]
    prompt = PROMPT.format(rules=RULES, loc=e05.LOCATOR[tid], text=e05.paper_text(a))
    figs = figures(a)
    with tempfile.TemporaryDirectory() as wd:
        schema, last = os.path.join(wd, "schema.json"), os.path.join(wd, "last.txt")
        with open(schema, "w") as fh:
            json.dump(SCHEMA, fh)
        cmd = [e05.CODEX, "exec", "-m", e05.MODELS["codex"], "-c", "model_reasoning_effort=max", "-C", wd,
               "-s", "read-only", "--skip-git-repo-check", "--ephemeral", "--json", "--output-schema", schema,
               "-o", last]
        for f in figs:
            cmd += ["-i", f]
        cmd.append("-")
        t0 = time.time()
        p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8", timeout=5400)
        wall = time.time() - t0
        events = [json.loads(l) for l in p.stdout.splitlines() if l.strip().startswith("{")]
        cmds = [e for e in events if "command" in json.dumps(e).lower() and "exec" in json.dumps(e).lower()]
        out = open(last, encoding="utf-8").read() if os.path.exists(last) else ""
    m = re.search(r"\{.*\}", out, re.S)
    rec = dict(task=tid, arxiv=a, locator=e05.LOCATOR[tid], figures=[os.path.basename(f) for f in figs],
               raw=out, parsed=json.loads(m.group(0)) if m else None, wall_s=wall, returncode=p.returncode,
               executed_command_events=len(cmds), stderr_tail=p.stderr[-2000:], model_id=e05.MODELS["codex"],
               finished=time.strftime("%Y-%m-%dT%H:%M:%S"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(rec, fh, indent=1)
    n = len(rec["parsed"]["items"]) if rec["parsed"] else None
    return f"{tid}: items={n} figs={len(figs)} rc={p.returncode} cmds={len(cmds)} {wall:.0f}s"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("tids", nargs="*")
    a = ap.parse_args()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for msg in ex.map(run, a.tids or list(lt.TASKS)):
            print(msg, flush=True)


if __name__ == "__main__":
    main()
