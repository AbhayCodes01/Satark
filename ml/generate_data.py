"""Generate the Satark synthetic dataset from template families (task P1-03).

Run from the repo root:
    python ml/generate_data.py

Design rules (see docs/WORKFLOW.md):
  * Deterministic: same --seed gives the same file.
  * The train/val/test split is done PER FAMILY, never per message, so a scenario
    and its translations cannot leak across splits.
  * The same noise rate is applied to scam and ham, so "messy text" is not a shortcut
    the model can learn for the scam class.
  * Every row carries source="synthetic_template". Report synthetic and hand-checked
    results separately (see docs/WORKFLOW.md rule 6).
"""
import argparse
import hashlib
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

if hasattr(sys.stdout, "reconfigure"):  # avoid Windows cp1252 crashes on Devanagari
    sys.stdout.reconfigure(encoding="utf-8")

URL_RE = re.compile(r"https?://\S+|\b[\w.-]+\.(?:xyz|top|click|online|site|info|cc|icu|buzz|shop)\b\S*|\bbit\.ly/\S+")
URL_SEG = re.compile(r"(https?://\S+)")
SHORTHAND = {"your": "ur", "please": "pls", "you": "u", "account": "a/c"}
EMOJI = ["⚠️", "🚨", "📢", "🙏", "👉"]


class Slots(dict):
    """Fills each slot lazily and remembers it, so a repeated {slot} gets the same value."""

    def __init__(self, rng: random.Random, cfg: dict, extras: dict = None):
        super().__init__()
        self.rng, self.cfg, self.extras = rng, cfg, extras or {}

    def __missing__(self, key):
        fn = getattr(self, f"_slot_{key}", None)
        if fn is None:
            raise KeyError(f"Unknown slot {{{key}}} in a template. Add it to generate_data.py or fix the typo.")
        self[key] = fn()
        return self[key]

    def _digits(self, n):
        return "".join(self.rng.choice("0123456789") for _ in range(n))

    def _slot_bank(self): return self.rng.choice(self.cfg["banks"])
    def _slot_shop(self): return self.rng.choice(sorted(self.cfg["shops"]))
    def _slot_shop_url(self): return self.cfg["shops"][self["shop"]]  # matches {shop}
    def _slot_bill_url(self): return self.rng.choice(self.cfg["bill_urls"])
    def _slot_name(self): return self.rng.choice(self.cfg["names"])
    def _slot_amount(self): return self.rng.choice(self.cfg["amounts"])
    def _slot_fee(self): return self.rng.choice(self.cfg["fees"])
    def _slot_otp(self): return self._digits(6)
    def _slot_last4(self): return self._digits(4)
    def _slot_pnr(self): return self._digits(10)
    def _slot_train(self): return self._digits(5)

    def _slot_phone(self):
        number = self.rng.choice("6789") + self._digits(9)  # random digits, not tied to any person
        return self.rng.choice([number, f"+91-{number}", f"+91 {number}"])

    def _slot_upi(self):
        return f"{self.rng.choice(self.cfg['upi_words'])}{self._digits(3)}@{self.rng.choice(self.cfg['upi_handles'])}"

    def _slot_date(self):
        return f"{self.rng.randint(1, 28):02d}-{self.rng.choice(['11', '12']):s}-2026"

    def _token(self):
        return "".join(self.rng.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(self.rng.randint(5, 8)))

    def _suspicious_base(self):
        kind = self.rng.choices(["lookalike", "short", "ip"], weights=[6, 3, 1])[0]
        if kind == "lookalike":
            sep = self.rng.choice(["-", "-", "."])
            host = f"{self.rng.choice(self.cfg['brand_tokens'])}{sep}{self.rng.choice(self.cfg['url_words'])}.{self.rng.choice(self.cfg['bad_tlds'])}"
            scheme = self.rng.choice(["http://", "https://"])
            return f"{scheme}{host}/{self._token()}" if self.rng.random() < 0.6 else f"{scheme}{host}"
        if kind == "short":
            return f"https://{self.rng.choice(self.cfg['shorteners'])}/{self._token()}"
        ip = ".".join(str(self.rng.randint(11, 223)) for _ in range(4))
        return f"http://{ip}/{self._token()}"

    def _slot_url(self): return self._suspicious_base()

    def _slot_apk_url(self):
        base = self._suspicious_base()
        if "bit.ly" in base or any(s in base for s in self.cfg["shorteners"]):
            return base  # shorteners hide the file name, which is realistic
        names = self.extras.get("apk_names", self.cfg["apk_names"])
        return f"{base.rstrip('/')}/{self.rng.choice(names)}.apk"


def apply_noise(text: str, lang: str, rng: random.Random):
    """Return (noisy_text, tag). Links are never edited (odd segments of the split are URLs)."""
    parts = URL_SEG.split(text)

    def on_text(fn):
        return "".join(p if i % 2 else fn(p) for i, p in enumerate(parts))

    tag = rng.choice(["upper", "lower", "spaces", "typo", "emoji", "shorthand", "nopunct"])
    if tag == "upper":
        return on_text(str.upper), tag
    if tag == "lower":
        return on_text(str.lower), tag
    if tag == "spaces":
        return on_text(lambda t: re.sub(r" ", lambda m: "  " if rng.random() < 0.3 else " ", t)), tag
    if tag == "emoji":
        return f"{rng.choice(EMOJI)} {text}", tag
    if tag == "nopunct":
        return on_text(lambda t: re.sub(r"[.,!\u0964]", "", t)), tag
    if tag == "shorthand" and lang in ("en", "hinglish"):
        def short(t):
            for k, v in SHORTHAND.items():
                t = re.sub(rf"\b{k}\b", v, t, flags=re.IGNORECASE)
            return t
        return on_text(short), tag
    if tag == "typo":
        seg_ids = [i for i in range(0, len(parts), 2)
                   if any(w.isascii() and w.isalpha() and len(w) > 3 for w in parts[i].split(" "))]
        if seg_ids:
            i = rng.choice(seg_ids)
            words = parts[i].split(" ")
            cand = [k for k, w in enumerate(words) if w.isascii() and w.isalpha() and len(w) > 3]
            k = rng.choice(cand)
            w = list(words[k])
            j = rng.randrange(len(w) - 1)
            w[j], w[j + 1] = w[j + 1], w[j]
            words[k] = "".join(w)
            parts[i] = " ".join(words)
        return "".join(parts), tag
    return text, "none"


def assign_splits(families, seed, val_frac, test_frac, min_per_split):
    """Per-label family split. Returns {family_id: split}."""
    rng = random.Random(seed)
    out = {}
    for label in ("scam", "ham"):
        ids = sorted(f["family_id"] for f in families if f["label"] == label)
        rng.shuffle(ids)
        n = len(ids)
        n_val = max(min_per_split, round(n * val_frac))
        n_test = max(min_per_split, round(n * test_frac))
        if n - n_val - n_test < 1:
            raise SystemExit(f"Too few '{label}' families ({n}) to make 3 splits. Add more templates.")
        for i, fid in enumerate(ids):
            out[fid] = "val" if i < n_val else "test" if i < n_val + n_test else "train"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--templates", default="data/templates/families_v0.yaml")
    ap.add_argument("--slots", default="data/slots.yaml")
    ap.add_argument("--taxonomy", default="data/taxonomy.yaml")
    ap.add_argument("--out", default="data/processed/dataset_v0.jsonl")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-per-variant", type=int, default=12)
    ap.add_argument("--noise-rate", type=float, default=0.35)
    ap.add_argument("--val-frac", type=float, default=0.15)
    ap.add_argument("--test-frac", type=float, default=0.15)
    ap.add_argument("--min-per-split", type=int, default=2)
    args = ap.parse_args()

    families = yaml.safe_load(Path(args.templates).read_text(encoding="utf-8"))["families"]
    cfg = yaml.safe_load(Path(args.slots).read_text(encoding="utf-8"))
    taxonomy = {c["code"] for c in yaml.safe_load(Path(args.taxonomy).read_text(encoding="utf-8"))["codes"]}

    # Guard against hallucinated or misspelled reason codes and duplicate ids.
    seen_ids = set()
    for f in families:
        if f["family_id"] in seen_ids:
            raise SystemExit(f"Duplicate family_id: {f['family_id']}")
        seen_ids.add(f["family_id"])
        if f["label"] not in ("scam", "ham"):
            raise SystemExit(f"{f['family_id']}: label must be scam or ham")
        unknown = set(f["codes"]) - taxonomy
        if unknown:
            raise SystemExit(f"{f['family_id']}: codes not in taxonomy: {sorted(unknown)}")
        if (f["label"] == "scam") != bool(f["codes"]):
            raise SystemExit(f"{f['family_id']}: scam needs codes, ham must have none")

    split_of = assign_splits(families, args.seed, args.val_frac, args.test_frac, args.min_per_split)
    rng = random.Random(args.seed + 1)
    rows, seen_text = [], set()

    for f in families:
        for lang, templates in f["variants"].items():
            for v_idx, tpl in enumerate(templates):
                for _ in range(args.n_per_variant):
                    text = tpl.format_map(Slots(rng, cfg, f.get("slot_overrides")))
                    tag = "none"
                    if rng.random() < args.noise_rate:
                        text, tag = apply_noise(text, lang, rng)
                    key = (lang, text)
                    if key in seen_text:
                        continue
                    seen_text.add(key)
                    rows.append({
                        "id": hashlib.sha1(f"{lang}|{text}".encode("utf-8")).hexdigest()[:12],
                        "text": text,
                        "lang": lang,
                        "label": f["label"],
                        "codes": f["codes"],
                        "family_id": f["family_id"],
                        "variant": v_idx,
                        "noise": tag,
                        "has_url": bool(URL_RE.search(text)),
                        "source": "synthetic_template",
                        "split": split_of[f["family_id"]],
                    })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"wrote {len(rows)} rows -> {out}")
    print("families per split/label:")
    fam_counts = Counter((split_of[f["family_id"]], f["label"]) for f in families)
    for split in ("train", "val", "test"):
        print(f"  {split:5s} scam={fam_counts[(split, 'scam')]:2d} ham={fam_counts[(split, 'ham')]:2d}")
    print("rows per split/label:")
    row_counts = Counter((r["split"], r["label"]) for r in rows)
    for split in ("train", "val", "test"):
        print(f"  {split:5s} scam={row_counts[(split, 'scam')]:4d} ham={row_counts[(split, 'ham')]:4d}")
    print("rows per language:", dict(Counter(r["lang"] for r in rows)))
    thin = [s for s in ("val", "test") for l in ("scam", "ham") if fam_counts[(s, l)] < 5]
    if thin:
        print("NOTE: val/test have very few families. Fine for testing the pipeline, "
              "NOT enough for reportable metrics. Target is 15+ scam and 150+ ham families.")


if __name__ == "__main__":
    main()
