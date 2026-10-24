"""Author adjudication sheet: one section per encoded task and one per exclusion.

Per task: source locator, the first annotation (slots, admissible values, reasons, reconstruction notes),
the blind Codex re-annotation (non-scale items with readings and evidence), the group-level disagreements
from a06, and blank decision lines for the author. Exclusions: reason and decision line.
Output: guide/2026-10-22-adjudication-sheet.md (frozen after the adjudication: rewritten only with --force;
always built from the pre-adjudication encoding)
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["LT_VARIANT"] = "pre"
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import e05_llm_readings as e05  # noqa: E402
import littasks as lt  # noqa: E402

E06 = os.path.join(ROOT, "results", "e06")


def main():
    out = os.path.join(ROOT, "guide", "2026-10-22-adjudication-sheet.md")
    if os.path.exists(out) and "--force" not in sys.argv:
        sys.exit(f"{out} is the frozen instrument of the adjudication; pass --force to rewrite it")
    ag = json.load(open(os.path.join(E06, "agreement_pre", "agreement.json")))
    dis = {}
    for d in ag["disagreement_list"]:
        dis.setdefault(d["task"], []).append(d)
    L = ["# Adjudication sheet: 41 encoded literature tasks and 16 exclusions", "",
         f"Blind Codex re-annotation agreement (task x group presence, symmetric): kappa = {ag['kappa']:.2f}, "
         f"raw agreement = {ag['raw_agreement']:.2f} over {ag['units']} units; {ag['disagreements']} disagreements. "
         "Groups: domain, support, load position/extent, load direction, volume fraction, passive region.", "",
         "For each task, mark one decision per slot: KEEP / CHANGE (write the new values) / DROP, and add any slot "
         "you find missing. Source texts and figures: `tasks/sources/<arXiv id>/` (local only).", ""]
    for tid, T in lt.TASKS.items():
        task = T["task"]
        a = T["source"]["arxiv"]
        L += [f"## {tid} — arXiv:{a} (frame position {T['source']['position']}, {T['dim']}-D)", "",
              f"Example: {e05.LOCATOR[tid]}", "", "**First annotation**", ""]
        for s, vals in task.slots.items():
            tag = " (mandatory)" if s in task.mandatory else ""
            L.append(f"- `{s}`{tag}: {', '.join(map(str, vals))} — {T['reasons'].get(s, '')}  \n  Decision: [ ] KEEP "
                     f"[ ] CHANGE ______ [ ] DROP")
        if T["recon"]:
            L.append(f"- Reconstruction: {'; '.join(T['recon'])}  \n  Decision: [ ] OK [ ] CHANGE ______")
        p = os.path.join(E06, "raw", f"{tid}.json")
        if os.path.exists(p):
            r = json.load(open(p))
            items = [it for it in (r.get("parsed") or {}).get("items", []) if it["effect"] != "scale_only"]
            L += ["", "**Codex re-annotation (non-scale items)**", ""]
            for it in items:
                L.append(f"- [{it['category']}] {it['entity']}: {'; '.join(it['readings'][:4])} "
                         f"(evidence: {it.get('evidence', '')[:160]})")
        if tid in dis:
            L += ["", "**Group disagreements**", ""]
            for d in dis[tid]:
                who = "first annotation only" if d["first"] else "Codex only"
                L.append(f"- {d['category']}: {who}")
        L += ["", "Missing slot? ____________________", ""]
    L += ["## Exclusions (in scope and ambiguous, not encoded)", ""]
    for a, why in lt.NOT_ENCODED.items():
        L.append(f"- arXiv:{a}: {why}  \n  Decision: [ ] EXCLUDE (agree) [ ] ENCODE (slots: ______)")
    os.makedirs(os.path.join(ROOT, "guide"), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print("tasks", len(lt.TASKS), "exclusions", len(lt.NOT_ENCODED), "lines", len(L))


if __name__ == "__main__":
    main()
