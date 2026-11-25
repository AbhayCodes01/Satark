# Satark: Technical Report (Phase 1, Open Qualifying)

**Challenge:** Arm Bharat AI-SoC Challenge 2026-27, PS3 (On-Device Threat, Phishing & Scam Detection)
**Team / leader:** [FILL: name] · **Institution:** [FILL] · **Faculty mentor:** [FILL]
**Repository:** https://github.com/AbhayCodes01/Satark · **Submitted:** 23 Nov 2026

> **Read this first (honest status).** This is an *initial solution*. The detector, risk fusion, trusted explanations and the Llama safety verifier run today in Python on a PC. Llama 3.2 1B, exported with ExecuTorch, runs on an Arm phone (OnePlus 13R) through Meta's reference app; real outputs and what the verifier did with them are in section 7. The detector is not yet on the phone, and the custom app is Phase 2. The custom Android app and on-device detector are the Phase 2 plan, not claimed as done here.

## 1. Problem and users

Scam messages (KYC and bank-block texts, UPI "collect" tricks, fake e-challan and PM-Kisan APKs, "digital arrest" calls, courier and electricity threats) cause large losses in India. The most exposed people are low-literacy, regional-language users on budget phones with unreliable data. They need a tool that **works offline, explains in their own language, and says what to do next**, not just a label.

## 2. Approach

Pipeline: **message → detector + link rules → structured evidence → risk band (green / amber / red) → explanation → one safe action.**

Design rules, following the organisers' guidance:
1. The detector produces *evidence* (band, reason codes, indicators). The LLM never decides whether something is a scam.
2. Llama receives **only the evidence**, never the raw message. This removes the attack surface of scam text trying to instruct the model.
3. Every Llama output passes a **verifier**. On any failure the app shows a pre-written, trusted explanation instead, so the user always gets a safe answer.
4. The system never auto-clicks, auto-deletes or claims certainty. It never says a message is "safe", only "no clear danger found, but stay careful".

## 3. Architecture

```
message (SMS / shared text)
  → normalise → detector (char n-gram TF-IDF + logistic regression) ─┐
  → link rules (shortener, odd TLD/IP, brand lookalike, .apk) ───────┤
                                                                      ▼
                                              evidence {band, reason codes, link domains}
                                                                      │
                  ┌───────────────────────────────────────────────────┤
                  ▼                                                   ▼
   Tier 0: trusted phrase bank (7 languages)        Tier 1: Llama 3.2 1B via ExecuTorch (evidence-only prompt)
                  ▲                                                   │
                  └──────────── fallback if rejected ◀──── verifier ◀─┘
```

**Tiered runtime (design):** Tier 0 (detector + phrase bank) is intended to run on any smartphone; Tier 1 adds Llama on phones with enough RAM. Cut-offs will be set from measured data.

## 4. What is implemented

| Component | Status |
|---|---|
| Synthetic dataset generator, split by scenario, leakage check | Implemented, tested on PC |
| Baseline detector + per-language evaluation | Implemented, tested on PC |
| URL rules and risk fusion | Implemented, tested on PC |
| Trusted phrase bank, 7 languages (EN, HI, Hinglish, MR, GU, BN, OR) | Drafted; checker passes; **native-speaker verification in progress** |
| Llama prompt builder (evidence only) + output verifier | Implemented, tested on PC (good answer accepted; 3 bad answers rejected) |
| Llama 3.2 1B exported to ExecuTorch `.pte` | Done (section 6) |
| Llama running on an Arm phone via ExecuTorch | Done: ran on OnePlus 13R via Meta's reference app (section 7) |
| **Detector ported to Kotlin** (pure Kotlin core, no Android APIs) | **Done and verified:** identical to the Python version on 1,494 of 1,494 test cases, including identical explanation text in all 7 languages (`docs/evidence/P5-kotlin-parity.txt`) |
| Detector connected to the phone app screen | [FILL: "Done, shown in the demo" OR "In progress, not shown in the demo"] |
| User study, detector via ExecuTorch, full custom app | **Not done: Phase 2** |

## 5. Data and evaluation

**Data.** 24 scenario families (13 scam, 11 legitimate "hard negatives" such as real bank alerts and OTP messages) written in English, Hindi and Hinglish, expanded by slot-filling and realistic noise into 1,316 messages. Train/validation/test are split **by scenario**, so a message and its translation never appear on both sides; a script verifies zero overlap (`ml/check_leakage.py`). Generation is deterministic (same seed, same file on two different machines).

**Detector results (development run).** Held-out scenarios, threshold chosen on validation:

| Split | Precision | Recall | False-positive rate |
|---|---|---|---|
| Validation | 0.986 | 1.000 | 0.018 |
| Test | 1.000 | 0.965 | 0.000 |

Per-language and per-scenario errors are in `docs/evidence/P2-baseline-training.txt`. The one validation error type was legitimate OTP messages flagged as scams, the hardest case.

**These numbers are not a measure of real-world accuracy.** The data is synthetic, written by us, and only two scenarios per class sit in each held-out split. A small probe of 8 differently-worded messages gave 7/8 correct; the miss was a casual Hinglish chat message wrongly flagged as suspicious, which shows everyday-chat coverage is too thin. Reportable accuracy requires a hand-checked set of real-style messages (target 300-500), which is Phase 2 work.

## 6. Llama on ExecuTorch

| Item | Value |
|---|---|
| Model | Llama 3.2 1B Instruct (Meta, gated; access granted) |
| Export tool | ExecuTorch `export_llm` (config-driven) |
| Quantization | 8da4w (int8 dynamic activations, int4 weights), embeddings 4-bit |
| Backend | XNNPACK (Arm CPU) |
| Context | max sequence 256, max context 512 (short evidence prompts) |
| Output size | 802,247,040 bytes (about 765 MB) |
| ExecuTorch version | **1.5.1**, matched to the Android library `org.pytorch:executorch-android:1.5.1` |

**Version decision.** A first export was made with ExecuTorch 1.6.0, but the Maven Central listing for the Android library tops out at 1.5.1 (no 1.5.0, no 1.6.0). Because the model file and the runtime must come from the same version, the model was re-exported with 1.5.1. The tool's version check used `maven-metadata.xml` from Maven Central. Export logs: `docs/evidence/`.

**Safety verifier.** Rejects Llama output that: says the message is safe or genuine; claims certainty; contains a number or link not in the evidence; is in the wrong script; is too long; or gives no clear safe action. Tested: 1 good answer accepted, 3 bad answers (reassuring, invented phone number, false certainty) rejected and replaced by the trusted text.

## 7. On-device results (Arm phone)

**Device:** OnePlus 13R (CPH2691), Snapdragon 8 Gen 3 (Arm), 12 GB RAM (RAM expansion enabled in settings, not relied on), Android 16 / OxygenOS 16.
**Software:** Meta's reference LlamaDemo app, built from source against `org.pytorch:executorch-android:1.5.1`. Our exported model (`llama32_1b_8da4w_et151.pte` plus `tokenizer.model`) was copied to `/data/local/tmp/llama/` and loaded with backend XNNPACK, model type LLAMA_3, temperature 0.

**Result: Llama 3.2 1B runs on the phone through ExecuTorch.** Verbatim prompts and replies are in `docs/evidence/P4-llama-phone-outputs.md`.

| Prompt | Speed shown by the app | Reply time shown by the app |
|---|---|---|
| 1: reasons in words + domain | 24.20 tokens/s | 6.244 s |
| 2: evidence JSON, strict rules | 35.76 tokens/s | 7.581 s |

These are the on-screen figures the demo app prints under each reply; we have not independently verified how the app defines them. **Not yet measured:** model load time, peak memory, battery, and the offline (airplane mode) run. [FILL if you measure them before submitting; otherwise leave as "not measured".]

**What the real replies showed.** At 1B parameters, Llama did not follow our format rules in either prompt. Reply 1 was a numbered list that repeated the instructions, claimed `sbi-kyc.com` was the official State Bank of India domain (invented), and suggested reporting to the US Federal Trade Commission. Reply 2 ran to three long paragraphs instead of three sentences, echoed internal labels (`LOOKALIKE_DOMAIN`, "DANGEROUS"), and named the US Federal Trade Commission and a "National Consumer Helpline" that the evidence did not support. On the positive side, both replies used hedged wording, did not call the message safe, claimed no certainty and asked for no personal information.

**What our safety layer did.** Both real replies were run through the verifier and **both were rejected**, so the user would have seen the trusted phrase-bank text. Checks for invented authorities, leaked internal labels and list-style output were added to the verifier because of this test. A good answer in English, Hindi and Hinglish passes, and reassuring or over-confident text is rejected (`python ml\pipeline.py --demo`).

**Why this matters.** This is direct evidence for the design rule that Llama only explains, the detector decides, and every Llama output is verified before display. A 1B model cannot be trusted to obey constraints, so a verified fallback is essential. Untested mitigations for Phase 2: a shorter prompt with one worked example, a hard token limit, trimming to three sentences, and trying the 3B model.

## 8. Privacy and safety by design

- Planned app ships **without the INTERNET permission**, so "nothing leaves your phone" can be checked in the manifest. Note: the reference app we built on (Meta's LlamaDemo) declares INTERNET for its optional preset-model download; the Satark detector itself makes no network calls.
- Llama sees structured evidence, not the message text; no personal data is placed in prompts.
- Reporting guidance points to the national cybercrime helpline 1930 and cybercrime.gov.in. **These details must be re-checked on the official sites before release.**
- No real personal data is in the repository; phone numbers and links in the dataset are generated.

## 9. Limitations (stated plainly)

1. Metrics are on synthetic data; real-world precision and recall are unknown.
2. Detector currently trained on English, Hindi and Hinglish only; the other four languages (Marathi, Gujarati, Bengali, Odia) have explanation text but **no detector validation**.
3. Phrase-bank wording was drafted by us with AI assistance and is being verified by native speakers; a language is not claimed as supported until verified.
4. The detector is verified identical in Kotlin, but [FILL: it is connected to the app screen / it is not yet connected to the app screen; the demo shows the PC pipeline and the Kotlin parity proof].
5. Everyday-chat false positives remain (see section 5).
6. No user study yet; no battery, load-time or memory benchmark beyond section 7.
7. Llama 3.2 1B ignored output-format rules and invented authorities in both real tests; its raw text is therefore never shown unverified. Only two prompts on one scenario have been tried.

## 10. Phase 2 plan

1. Custom Android app (Kotlin): SMS scan + share-from-WhatsApp, traffic-light result, voice read-aloud, local feedback.
2. Finish connecting the Kotlin detector to the app screen (the Kotlin core is already verified); optionally move the detector to ExecuTorch as well.
3. Tiered runtime with a device capability probe; benchmark on a low-end (2-3 GB) phone and a Raspberry Pi 5 as CPU baseline.
4. Hand-checked real-style test set and honest evaluation per language and scam type; many more hard negatives.
5. User study with 10-15 people (rural and low-literacy participants included).
6. Native verification of all seven languages; add recorded audio where offline TTS is missing.

## 11. Reproduce

```powershell
python -m venv .venv151 ; .\.venv151\Scripts\Activate.ps1
pip install executorch==1.5.1
pip install torch==2.14.0 --extra-index-url https://download.pytorch.org/whl/cpu
pip install scikit-learn joblib
python ml\generate_data.py ; python ml\check_leakage.py ; python ml\check_phrase_bank.py
python ml\train_baseline.py ; python ml\pipeline.py --demo
```
Llama export (needs Hugging Face access to Llama 3.2 1B Instruct; set `$env:PYTHONUTF8="1"`):
`python -m executorch.extension.llm.export.export_llm --config llm\llama32_1b_8da4w_et151.yaml`

## 12. Evidence files (in `docs/evidence/`)

`P0-05-toy-expected.json` (ExecuTorch toy export check) · `P0-07-export-log-et151.txt` (Llama export log) · `P2-baseline-training.txt` · `P2-pipeline-demo.txt` · `P4-llama-phone-outputs.md` (real Llama replies from the phone) · `P5-kotlin-parity.txt` (Kotlin vs Python parity)

**Demo video:** [FILL: link]
