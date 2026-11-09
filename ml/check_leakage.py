"""Leakage check for the Satark dataset (task P1-07).

    python ml/check_leakage.py [data/processed/dataset_v0.jsonl]

Fails (exit code 1) if:
  * any family_id appears in more than one split
  * the same normalized text appears in more than one split
  * any row is missing a required field or has an unknown split
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REQUIRED = {"id", "text", "lang", "label", "codes", "family_id", "source", "split"}
SPLITS = {"train", "val", "test"}


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/processed/dataset_v0.jsonl")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    problems = []

    for i, r in enumerate(rows):
        missing = REQUIRED - r.keys()
        if missing:
            problems.append(f"row {i}: missing fields {sorted(missing)}")
        if r.get("split") not in SPLITS:
            problems.append(f"row {i}: bad split {r.get('split')!r}")

    fam_splits = defaultdict(set)
    text_splits = defaultdict(set)
    for r in rows:
        fam_splits[r["family_id"]].add(r["split"])
        text_splits[(r["lang"], norm(r["text"]))].add(r["split"])

    for fam, splits in fam_splits.items():
        if len(splits) > 1:
            problems.append(f"family {fam} appears in splits {sorted(splits)}")
    dup = sum(1 for s in text_splits.values() if len(s) > 1)
    if dup:
        problems.append(f"{dup} identical texts appear in more than one split")

    print(f"file: {path}  rows: {len(rows)}  families: {len(fam_splits)}")
    print("rows per split:", dict(Counter(r["split"] for r in rows)))
    if problems:
        print("LEAKAGE CHECK: FAIL")
        for p in problems[:20]:
            print("  -", p)
        return 1
    print("LEAKAGE CHECK: PASS (no family or text shared across splits)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
