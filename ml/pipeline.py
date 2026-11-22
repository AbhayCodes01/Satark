"""Satark pipeline: message -> evidence -> verdict -> trusted explanation (+ Llama prompt/verifier).

    python ml/pipeline.py --demo                      # run built-in examples
    python ml/pipeline.py "your message here" --lang hi

Design rules (docs/PROJECT_PLAN.md):
  * The detector and URL rules produce structured EVIDENCE. The LLM never decides.
  * Llama receives only the evidence (not the raw message) and only explains.
  * Every Llama output must pass verify_llama_output(); otherwise we fall back to the
    trusted phrase bank. The user always gets a safe answer.
  * The app never auto-clicks, auto-deletes or claims certainty.
STATUS: UNTESTED on the owner's PC until first run. Detector numbers are on synthetic data.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import joblib
import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MODEL = Path("models/baseline_v0_full.joblib")
BANK = Path("data/phrase_bank/phrase_bank_v0.yaml")
SLOTS = Path("data/slots.yaml")
LANG_NAME = {"en": "English", "hi": "Hindi (Devanagari script)", "hinglish": "Hinglish (Hindi written in English letters)"}

URL_RE = re.compile(r"https?://[^\s]+|\b(?:bit\.ly|tinyurl\.com|cutt\.ly|t\.ly|rb\.gy|is\.gd)/[^\s]+", re.I)
IPV4 = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
PRIORITY = ["MALICIOUS_APK", "FAKE_CHALLAN", "OTP_REQUEST", "UPI_COLLECT", "DIGITAL_ARREST", "KYC_BANK_BLOCK",
            "GOVT_SCHEME", "LOAN_APP", "LOTTERY_PRIZE", "INVESTMENT_CRYPTO", "JOB_TASK_SCAM", "COURIER_CUSTOMS",
            "ELECTRICITY_DISCONNECT", "SIM_BLOCK", "LOOKALIKE_DOMAIN", "SHORTENED_URL", "SUSPICIOUS_TLD_OR_IP",
            "UNKNOWN_SENDER_LINK", "GENERIC_SUSPICIOUS", "URGENCY"]

URL_CODES = {"LOOKALIKE_DOMAIN", "SHORTENED_URL", "SUSPICIOUS_TLD_OR_IP", "MALICIOUS_APK", "UNKNOWN_SENDER_LINK"}

_cache = {}


def _load():
    if not _cache:
        slots = yaml.safe_load(SLOTS.read_text(encoding="utf-8"))
        official = {urlparse(u).hostname.replace("www.", "") for u in list(slots["shops"].values()) + slots["bill_urls"]}
        official |= {"sbi.co.in", "hdfcbank.com", "icicibank.com", "axisbank.com", "irctc.co.in",
                     "indiapost.gov.in", "uidai.gov.in", "parivahan.gov.in", "cybercrime.gov.in"}
        _cache.update(model=joblib.load(MODEL), bank=yaml.safe_load(BANK.read_text(encoding="utf-8")),
                      slots=slots, official=official)
    return _cache


# ------------------------------------------------------------------ URL rules
def analyze_urls(text):
    c = _load()
    flags, hosts = [], []
    for raw in URL_RE.findall(text):
        url = raw.rstrip(".,;)")
        p = urlparse(url if "://" in url else "http://" + url)
        host = (p.hostname or "").lower().replace("www.", "")
        if not host:
            continue
        hosts.append(host)
        is_official = any(host == d or host.endswith("." + d) for d in c["official"])
        if is_official:
            continue
        tld = host.rsplit(".", 1)[-1]
        if host in c["slots"]["shorteners"]:
            flags.append("SHORTENED_URL")
        if IPV4.match(host) or tld in c["slots"]["bad_tlds"] or host.startswith("xn--") or "@" in p.netloc:
            flags.append("SUSPICIOUS_TLD_OR_IP")
        if any(b in host for b in c["slots"]["brand_tokens"]):
            flags.append("LOOKALIKE_DOMAIN")
        if p.path.lower().endswith(".apk"):
            flags.append("MALICIOUS_APK")
    return sorted(set(flags), key=PRIORITY.index), hosts


# ---------------------------------------------------------------- the detector
def analyze(text, lang="en"):
    """Return the structured evidence for one message."""
    c = _load()
    m = c["model"]
    X = m["vectorizer"].transform([text])
    p_scam = float(m["scam_clf"].predict_proba(X)[0, 1])
    url_flags, hosts = analyze_urls(text)

    score = p_scam
    if url_flags:
        score = max(score, 0.5 + 0.1 * (len(url_flags) - 1))
    if "MALICIOUS_APK" in url_flags:
        score = max(score, 0.9)
    band = "SAFE_LOOKING" if score < 0.35 else "SUSPICIOUS" if score < 0.70 else "DANGEROUS"
    # Model threshold chosen on validation: also treat it as at least SUSPICIOUS.
    if p_scam >= m["threshold"] and band == "SAFE_LOOKING":
        band = "SUSPICIOUS"

    codes = []
    if band != "SAFE_LOOKING":
        probs = m["code_clf"].predict_proba(X)[0]
        codes = [lab for lab, pr in zip(m["code_labels"], probs) if pr >= 0.4 and lab not in URL_CODES]  # link codes come from rules only
        codes += url_flags
        codes = sorted(set(codes), key=PRIORITY.index)
        if not codes:
            codes = ["GENERIC_SUSPICIOUS"]
    return {"band": band, "score": round(score, 3), "model_score": round(p_scam, 3), "reason_codes": codes,
            "indicators": {"link_domains": hosts[:3], "has_apk_link": "MALICIOUS_APK" in url_flags},
            "lang": lang}


# ------------------------------------------------- Tier 0: trusted explanation
def tier0_explanation(evidence, lang):
    bank = _load()["bank"]
    band, codes = evidence["band"], evidence["reason_codes"]
    parts = {"verdict": bank["verdicts"][band][lang], "reasons": [], "actions": []}
    text_codes = [c for c in codes if c not in URL_CODES and c != "URGENCY"]
    link_codes = [c for c in codes if c in URL_CODES]
    shown = (text_codes[:1] + link_codes[:1]) or codes[:1]
    if len(shown) < 2:
        shown += [c for c in codes if c not in shown][:1]
    for code in shown[:2]:
        parts["reasons"].append(bank["reasons"][code][lang])
    keys = []
    for code in codes:
        for a in bank["code_actions"][code]:
            if a not in keys:
                keys.append(a)
    if band == "SAFE_LOOKING":
        keys = ["DO_NOT_SHARE"]
    if band == "DANGEROUS" and "REPORT_1930" not in keys[:3]:
        keys = keys[:2] + ["REPORT_1930"]
    parts["actions"] = [bank["actions"][k][lang] for k in keys[:3]]
    parts["text"] = " ".join([parts["verdict"]] + parts["reasons"] + parts["actions"])
    return parts


# --------------------------------------------- Tier 1: Llama prompt + verifier
def build_llama_prompt(evidence, lang):
    """Llama sees ONLY this evidence. The raw message is deliberately not included."""
    safe_hosts = [re.sub(r"[^a-z0-9.\-]", "", h) for h in evidence["indicators"]["link_domains"]]
    ev = {"risk_band": evidence["band"], "reason_codes": evidence["reason_codes"],
          "link_domains": safe_hosts, "apk_link": evidence["indicators"]["has_apk_link"]}
    return (
        "You are a scam-safety helper for ordinary phone users in India. "
        "A detector has already analysed a message. You only see its evidence below.\n"
        f"EVIDENCE: {json.dumps(ev, ensure_ascii=False)}\n"
        f"Write in {LANG_NAME[lang]}. Use at most 3 short, simple sentences: what looks risky, why it matters, "
        "and one safe action.\n"
        "Rules: never say the message is safe or genuine. Never claim certainty; say 'may be' or 'has signs of'. "
        "Do not mention any number, name or link that is not in the evidence. Do not ask for personal details."
    )


REASSURING = {
    "en": re.compile(r"\b(is safe|are safe|looks safe|genuine|legitimate|trustworthy|nothing to worry|no need to worry|ok to click)\b", re.I),
    "hi": re.compile(r"(सुरक्षित है|भरोसेमंद है|असली है|चिंता की कोई बात नहीं)"),
    "hinglish": re.compile(r"\b(surakshit hai|asli hai|bharosemand hai|koi chinta nahi|chinta ki koi baat nahi)\b", re.I),
}
CERTAINTY = {
    "en": re.compile(r"\b(definitely|certainly|100%|for sure|without doubt|guaranteed)\b", re.I),
    "hi": re.compile(r"(पक्का|बिल्कुल|निश्चित रूप से|100%)"),
    "hinglish": re.compile(r"\b(pakka|bilkul|100%|zaroor)\b", re.I),
}
ACTION_HINT = {
    "en": re.compile(r"\b(do not|don't|never|call|check|verify|report|ignore|delete|avoid)\b", re.I),
    "hi": re.compile(r"(न करें|न दें|न भेजें|कॉल करें|जांचें|बचें)"),
    "hinglish": re.compile(r"\b(na karein|na dein|na bhejein|call karein|jaanchein|bachein)\b", re.I),
}


def verify_llama_output(text, evidence, lang):
    """Return (ok, reasons_failed). Any failure means: use the trusted phrase bank instead."""
    fails = []
    t = (text or "").strip()
    if not t:
        return False, ["empty output"]
    if len(t) > 450:
        fails.append("too long")
    if len(re.findall(r"[.!?।]", t)) > 5:
        fails.append("too many sentences")
    if lang == "en" and REASSURING["en"].search(re.sub(r"\b(not|isn't|never)\s+(be\s+)?(safe|genuine)\b", "", t, flags=re.I)):
        fails.append("reassuring wording")
    elif lang in ("hi", "hinglish") and REASSURING[lang].search(t):
        fails.append("reassuring wording")
    if CERTAINTY[lang].search(t):
        fails.append("certainty wording")
    letters = [ch for ch in t if ch.isalpha()]
    deva = sum("\u0900" <= ch <= "\u097f" for ch in letters)
    if letters:
        if lang == "hi" and deva / len(letters) < 0.5:
            fails.append("not mostly Devanagari")
        if lang in ("en", "hinglish") and deva > 0:
            fails.append("unexpected Devanagari")
    # Facts: every number must come from the evidence (plus the 1930 helpline).
    allowed = set(re.findall(r"\d+", json.dumps(evidence, ensure_ascii=False))) | {"1930"}
    extra = [n for n in re.findall(r"\d+", t) if n not in allowed]
    if extra:
        fails.append(f"numbers not in evidence: {extra[:3]}")
    allowed_hosts = set(evidence["indicators"]["link_domains"])
    for h in re.findall(r"\b[a-z0-9\-]+(?:\.[a-z0-9\-]+)+\b", t.lower()):
        if h not in allowed_hosts and h != "cybercrime.gov.in":
            fails.append(f"link/name not in evidence: {h}")
            break
    if evidence["band"] != "SAFE_LOOKING" and not ACTION_HINT[lang].search(t):
        fails.append("no clear safe action")
    return (not fails), fails


def final_explanation(evidence, lang, llama_text=None):
    """Use Llama's text only if it passes the verifier, else the trusted phrase bank."""
    trusted = tier0_explanation(evidence, lang)
    if llama_text is None:
        return {"source": "phrase_bank", "text": trusted["text"], "trusted": trusted}
    ok, why = verify_llama_output(llama_text, evidence, lang)
    if ok:
        return {"source": "llama_verified", "text": llama_text, "trusted": trusted}
    return {"source": "phrase_bank_fallback", "text": trusted["text"], "llama_rejected_because": why, "trusted": trusted}


# ------------------------------------------------------------------------ demo
DEMO = [
    ("Dear customer, your SBI account will be blocked today. Update your KYC immediately: http://sbi-kyc.xyz/ab12c", "en"),
    ("RTO notice: aapki gaadi ka challan pending hai. Install karein http://echallan-verify.top/RTO_Challan.apk", "hinglish"),
    ("आपका Rs 5,000 का रिफंड बाकी है। पाने के लिए फोन पर आया OTP बताएं।", "hi"),
    ("Rs 1,250 debited from A/c XX4821 on 12-11-2026. If not done by you, call your bank on the number printed on your card. -HDFC Bank", "en"),
    ("Hi Rahul, are you coming home this weekend? Mom is making your favourite food.", "en"),
    ("Your parcel is waiting. Pay Rs 49 fee here: https://bit.ly/3xYz9a", "en"),
]


def show(text, lang):
    ev = analyze(text, lang)
    exp = final_explanation(ev, lang)
    print("MESSAGE :", text)
    print("EVIDENCE:", json.dumps(ev, ensure_ascii=False))
    print("EXPLAIN :", exp["text"])
    return ev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("message", nargs="?")
    ap.add_argument("--lang", default="en", choices=["en", "hi", "hinglish", "mr", "gu", "bn", "or"])
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--llama-prompt", action="store_true", help="also print the evidence-only prompt for Llama")
    ap.add_argument("--verify", default=None, help="paste Llama's answer (from the phone) to run the safety verifier on it")
    a = ap.parse_args()
    if a.demo:
        for text, lang in DEMO:
            ev = show(text, lang)
            print("-" * 100)
        # Verifier demonstration: a good Llama answer, then three bad ones that must fall back.
        ev = analyze(DEMO[0][0], "en")
        tests = {
            "good": "This message has signs of a scam. It pushes you to act fast and the link may be fake. Do not click the link and call your bank on the number on your card.",
            "reassuring": "This message is safe, you can click the link.",
            "invented number": "This may be a scam. Call 9876543210 now and do not click the link.",
            "certainty": "This is definitely a scam. Do not click.",
        }
        print("VERIFIER CHECK (same evidence, four candidate Llama answers):")
        for name, txt in tests.items():
            r = final_explanation(ev, "en", llama_text=txt)
            print(f"  {name:16s} -> {r['source']}" + (f"  (rejected: {r['llama_rejected_because']})" if "llama_rejected_because" in r else ""))
        print("-" * 100)
        print("LLAMA PROMPT (evidence only, raw message NOT included):")
        print(build_llama_prompt(ev, "en"))
        return
    if not a.message:
        ap.error("give a message or use --demo")
    ev = show(a.message, a.lang)
    if a.llama_prompt and a.lang in LANG_NAME:
        print("LLAMA PROMPT:\n" + build_llama_prompt(ev, a.lang))
    if a.verify is not None:
        r = final_explanation(ev, a.lang, llama_text=a.verify)
        print("LLAMA ANSWER:", a.verify)
        print("VERIFIER    :", r["source"], ("- rejected because " + str(r["llama_rejected_because"])) if "llama_rejected_because" in r else "- accepted")
        print("SHOWN TO USER:", r["text"])


if __name__ == "__main__":
    main()
