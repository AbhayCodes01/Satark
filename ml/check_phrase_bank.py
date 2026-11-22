"""Check the Satark phrase bank and export a review sheet (tasks P1-04 / P1-05).

    python ml/check_phrase_bank.py                 # validate + per-language status
    python ml/check_phrase_bank.py --csv data/phrase_bank/review.csv   # also write a review sheet

Validation (exit code 1 on failure):
  * every taxonomy code has a reason in every language
  * every code has actions, and every action key exists in every language
  * no empty or placeholder strings (TODO, XXX, ???)
  * helpline text appears only in the REPORT_1930 action
  * no certainty wording in the English strings ("definitely", "100%", "certainly")
The release gate is separate: a language counts as READY only when its status is "verified".
The CSV is written with a BOM so Excel and Google Sheets show Indian scripts correctly.
"""
import argparse
import csv
import re
import sys
from pathlib import Path

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CERTAINTY_EN = re.compile(r"\b(definitely|certainly|100%|for sure|guaranteed to be a scam)\b", re.IGNORECASE)
PLACEHOLDER = re.compile(r"TODO|XXX|\?\?\?")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", default="data/phrase_bank/phrase_bank_v0.yaml")
    ap.add_argument("--taxonomy", default="data/taxonomy.yaml")
    ap.add_argument("--csv", default=None)
    args = ap.parse_args()

    bank = yaml.safe_load(Path(args.bank).read_text(encoding="utf-8"))
    taxonomy = [c["code"] for c in yaml.safe_load(Path(args.taxonomy).read_text(encoding="utf-8"))["codes"]]
    langs = bank["languages"]
    problems = []

    def need(section, key, entry):
        for lang in langs:
            text = (entry or {}).get(lang)
            if not isinstance(text, str) or not text.strip():
                problems.append(f"{section}.{key}: missing or empty text for '{lang}'")
            elif PLACEHOLDER.search(text):
                problems.append(f"{section}.{key}.{lang}: contains a placeholder")
        extra = set(entry or {}) - set(langs)
        if extra:
            problems.append(f"{section}.{key}: unknown language keys {sorted(extra)}")

    for code in taxonomy:
        if code not in bank["reasons"]:
            problems.append(f"reasons: taxonomy code {code} has no entry")
        else:
            need("reasons", code, bank["reasons"][code])
        if code not in bank["code_actions"]:
            problems.append(f"code_actions: taxonomy code {code} has no entry")
    for code in bank["reasons"]:
        if code not in taxonomy:
            problems.append(f"reasons: {code} is not in taxonomy.yaml")
    for code, acts in bank["code_actions"].items():
        for a in acts:
            if a not in bank["actions"]:
                problems.append(f"code_actions.{code}: unknown action {a}")
    for key, entry in bank["actions"].items():
        need("actions", key, entry)
    for key, entry in bank["verdicts"].items():
        need("verdicts", key, entry)

    # Helpline text must live only in REPORT_1930 so there is one place to update.
    for section in ("reasons", "verdicts", "actions"):
        for key, entry in bank[section].items():
            if section == "actions" and key == "REPORT_1930":
                continue
            for lang, text in (entry or {}).items():
                if isinstance(text, str) and ("1930" in text or "cybercrime.gov.in" in text):
                    problems.append(f"{section}.{key}.{lang}: helpline text outside REPORT_1930")

    # Never claim certainty (English check only; other languages need the owner's eyes).
    for section in ("reasons", "verdicts", "actions"):
        for key, entry in bank[section].items():
            text = (entry or {}).get("en", "")
            if CERTAINTY_EN.search(text):
                problems.append(f"{section}.{key}.en: certainty wording")

    n_strings = sum(len(bank[s]) for s in ("reasons", "verdicts", "actions")) * len(langs)
    print(f"phrase bank: {args.bank}")
    print(f"codes: {len(taxonomy)}  actions: {len(bank['actions'])}  verdicts: {len(bank['verdicts'])}  languages: {len(langs)}  strings: {n_strings}")
    print("language status (release gate):")
    for lang in langs:
        r = bank["review"].get(lang, {})
        ready = "READY" if r.get("status") == "verified" else "NOT READY"
        print(f"  {lang:9s} {r.get('status', 'missing'):9s} {ready}  verified_by={r.get('verified_by') or '-'}")

    if args.csv:
        out = Path(args.csv)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["key", "english", "language", "text", "ok_yes_no", "correction_if_any"])
            for section in ("verdicts", "reasons", "actions"):
                for key, entry in bank[section].items():
                    for lang in langs:
                        if lang == "en":
                            continue
                        w.writerow([f"{section}.{key}", entry["en"], lang, entry[lang], "", ""])
        print(f"review sheet written: {out}  (open in Excel or Google Sheets)")

    if problems:
        print("PHRASE BANK CHECK: FAIL")
        for p in problems[:30]:
            print("  -", p)
        return 1
    print("PHRASE BANK CHECK: PASS (structure is complete; wording still needs native review)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
