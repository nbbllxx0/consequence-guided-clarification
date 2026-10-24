"""A23: frozen releases of the further low-margin tasks re-scored against six-start and refined references.

Every task with a zero-allowance CGC-S release whose full-table margin is below the largest two-start
spread (0.0406) and that E08 did not originally cover (L25, L11, L20, L21, L36) was run through E08
(`python experiments/e08_near_threshold.py L25 L11 L20 L21 L36`). This script re-scores the unchanged
base releases against those tables with the A15 `frozen` routine.
Usage: python experiments/a23_frozen_extra.py
Output: results/a15/frozen_extra.json
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.argv = sys.argv[:1] + ["consensus"]
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import a15_reviewer_replays as a15  # noqa: E402

TASKS = ("L25", "L11", "L20", "L21", "L36")


def main():
    res = a15.frozen(tids=TASKS)
    with open(os.path.join(ROOT, "results", "a15", "frozen_extra.json"), "w") as fh:
        json.dump(res, fh, indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
