# Satark: On-Device Scam & Phishing Shield for Every Indian Smartphone

> **Working title:** Satark (सतर्क / সতর্ক / સતર્ક / ସତର୍କ), meaning "alert, vigilant" in Hindi, Marathi, Bengali, Gujarati and Odia. It is a placeholder, so a find-and-replace renames it everywhere.
> **Challenge:** Arm Bharat AI-SoC Challenge, PS3, Cybersecurity & Digital Safety: *On-Device Threat, Phishing & Scam Detection*
> **Deadlines:** Open Qualifying submission **23 Nov 2026** · PoC Development submission **5 Feb 2027**
> **Document status:** v1.0, written 3 Nov 2026. This is the source of truth for scope. Changes go in the changelog at the bottom.

---

## 1. Vision in one paragraph

Most scam-detection tools assume an English-speaking user on a flagship phone with a data connection. India's most vulnerable users are the opposite: low-literacy, regional-language speakers on budget phones with patchy connectivity, and they are the ones losing money to KYC scams, UPI collect requests, fake challans and malicious APKs sent on WhatsApp. **Satark is an offline-first assistant that detects scams on the phone, explains in the user's own language by voice and simple visuals, and tells them the one safe action to take.** It adapts to the hardware: a tiny detector plus verified explanations on any smartphone, and a Llama-powered assistant when the phone can handle it.

**Three differentiators:**
1. **Runs on any smartphone** through a tiered runtime that picks the best experience the device can support.
2. **Seven languages, honestly handled:** English, Hindi, Hinglish, Marathi, Gujarati, Bengali and Odia, each verified by a native speaker.
3. **Explanations that cannot lie:** Llama only receives structured evidence, and a verifier checks its output against that evidence before the user sees it.

---

## 2. What the organizers asked for, and how we meet it

| Requirement (from the briefing) | How Satark satisfies it |
|---|---|
| Llama + ExecuTorch mandatory, on-device | Llama 3.2 1B Instruct (quantized) on ExecuTorch on Android. The detector is also exported to ExecuTorch, so the whole pipeline runs on one runtime. |
| Detector produces structured evidence, Llama only explains | Detector and URL analyzer output `{label, score, reason_codes[], indicators[]}`. Llama sees only that structure. |
| Never auto-click, auto-delete, or claim certainty from the LLM alone | App never acts on a message by itself. Verdicts are 3 bands, not fake-precise percentages. The verifier blocks over-confident wording. |
| Detect → explain → recommend → verify → learn | Full journey implemented (section 6.7). |
| Detection quality: precision, recall, FPR, latency | Per-language and per-scam-type evaluation harness (section 10). |
| On-device performance: inference time, memory, CPU load, offline | Benchmark harness on real devices with offline (airplane mode) test (section 10.2). |
| User effectiveness: clarity, action completion, risk understanding | Small user study with 10-15 people (section 10.3). |
| Benchmark on the actual target, not only a laptop | Android phone(s) as primary target, Raspberry Pi 5 as CPU baseline. |
| Capture: device/OS, model & quantization, ExecuTorch version, latency, memory, offline test | A `benchmarks/` script records all of these automatically into a results JSON. |
| Deliverables: source code, APK, demo video, engineering report | Section 15 checklist. |
| One primary scenario, extensible architecture | **Primary: SMS/message scam text, with URLs inside it analyzed.** Network anomaly detection is a documented future module. |

> **To confirm on the official page:** whether the *Open Qualifying* round requires all four deliverables or a subset. Check https://arm-education.github.io/Arm-Developer-Labs/Bharat_AI_SoC_2026_27.html and email support@armbharatchallenge.com if unclear. The plan assumes all four to be safe.

---

## 3. Scope

### In scope (v1, by 23 Nov)
- Android app (Kotlin) with SMS auto-scan and **Share-to-Satark** (WhatsApp, Telegram and any other app can share text into it)
- Scam text classification and URL risk analysis, fused into one risk score
- 3-band verdict (Safe-looking / Suspicious / Dangerous) with reason codes
- Explanations in 7 languages, as text **and** voice
- Tiered runtime (Tier 0 / Tier 1) with automatic device capability probe
- Llama 3.2 1B explanations via ExecuTorch with verifier and template fallback
- India-specific action guidance (1930, cybercrime.gov.in, Sanchar Saathi Chakshu, "call your bank on the number on your card")
- Local-only feedback (Report / Dismiss) that adjusts the on-device threshold
- Benchmark harness, evaluation harness, small user study, engineering report

### Out of scope for v1 (documented as roadmap)
- Network anomaly / intrusion detection (Pi 5 gateway)
- Hailo NPU path
- Call / voice-call scam detection
- Automatic reading of WhatsApp or other app notifications by default
- iOS
- Cloud sync of any kind

---

## 4. Users and languages

**Primary persona:** a smartphone user with low or moderate literacy, a budget Android phone (2-4 GB RAM), one regional language, often shared family usage, intermittent data. **Secondary persona:** urban user who wants a fast second opinion on a message.

### Language plan

| Language | Script | Detection input | Explanation engine | Voice output | Verified by |
|---|---|---|---|---|---|
| English | Latin | ✅ | Llama (Tier 1) or templates | Android TTS | Owner |
| Hindi | Devanagari | ✅ | Llama (Tier 1) or templates | Android TTS | Owner |
| Hinglish | Romanized Hindi | ✅ | Llama (Tier 1) or templates | Android TTS (Hindi/English) | Owner |
| Marathi | Devanagari | ✅ | **Templates** (Llama optional if it passes the verifier) | TTS if available, else recorded clips | Owner |
| Gujarati | Gujarati | ✅ | **Templates** | TTS if available, else recorded clips | Owner |
| Bengali | Bengali | ✅ | **Templates** | TTS if available, else recorded clips | Owner |
| Odia | Odia | ✅ | **Templates** | **Recorded clips likely needed** | Owner |

**Why templates for four languages:** Llama 3.2's officially supported languages include Hindi but not Gujarati, Odia, Bengali or Marathi, and a 1B model will be weak on them. A native-verified phrase bank is more trustworthy than a poor generation, and it works on every device. We test Llama on Marathi and keep it only if it passes both the verifier and native review.

**Voice reality check (to verify on test devices, not assumed):** Android's offline TTS coverage differs by phone and installed voice packs, and Odia in particular may be missing. Plan: use TTS where a voice exists, and ship **short pre-recorded audio clips** for the phrase bank where it doesn't. Recorded clips are also fully offline and sound more natural. The phrase bank is small (about 20 reasons × 3-4 sentences), so recording is feasible.

**Script and font handling:** bundle Noto Sans fonts for Devanagari, Bengali, Gujarati and Odia so older phones render text correctly.

---

## 5. Scam taxonomy (reason codes)

Every detection returns one or more reason codes. Each code has a verified phrase-bank entry in all 7 languages and one "recommended action" entry.

| Code | Scam type | Typical cue |
|---|---|---|
| `URGENCY` | Pressure language | "within 24 hours", "immediately", "last warning" |
| `KYC_BANK_BLOCK` | Fake bank/KYC | "account will be blocked", "update PAN/KYC" |
| `OTP_REQUEST` | OTP / PIN / CVV theft | asks to share or reply with OTP |
| `UPI_COLLECT` | UPI collect / refund trick | "approve request to receive money" |
| `LOTTERY_PRIZE` | Lottery / KBC / prize | "you have won", processing fee |
| `ELECTRICITY_DISCONNECT` | Fake electricity bill | "power will be cut tonight" |
| `COURIER_CUSTOMS` | Fake courier / customs / India Post | "parcel held", pay small fee |
| `DIGITAL_ARREST` | Impersonating police/CBI/TRAI | "you are under investigation" |
| `SIM_BLOCK` | Fake telecom/TRAI | "SIM will be disconnected" |
| `FAKE_CHALLAN` | Fake e-challan / RTO | traffic fine link |
| `JOB_TASK_SCAM` | Part-time job / task / like-and-earn | Telegram/WhatsApp group, daily income |
| `LOAN_APP` | Predatory loan / harassment | instant loan, no documents |
| `GOVT_SCHEME` | Fake PM-Kisan / subsidy / Aadhaar | "claim your benefit" |
| `INVESTMENT_CRYPTO` | Stock tips / crypto / doubling | guaranteed returns |
| `MALICIOUS_APK` | APK file or install link | ".apk", "install this app to continue" |
| `LOOKALIKE_DOMAIN` | Brand impersonation URL | `sbi-kyc-update.xyz` |
| `SHORTENED_URL` | Hidden destination | bit.ly, tinyurl, etc. |
| `SUSPICIOUS_TLD_OR_IP` | Risky URL structure | IP host, odd TLD, punycode, `@` in URL |
| `UNKNOWN_SENDER_LINK` | Link from unfamiliar sender | non-standard sender ID + link |
| `GENERIC_SUSPICIOUS` | Model flags it, no clear code | fallback band |

`MALICIOUS_APK` and `FAKE_CHALLAN` are priority codes. APK-based scams ("RTO challan.apk", "PM Kisan.apk") spread widely over WhatsApp in India and have a direct, severe impact.

---

## 6. System architecture

### 6.1 Pipeline

```
 INPUT                ANALYSE                     DETECT              FUSE            EXPLAIN                 ACT
┌──────────┐   ┌──────────────────┐   ┌─────────────────────┐   ┌───────────┐   ┌────────────────┐   ┌──────────────┐
│ SMS      │   │ Normalize text   │   │ Text classifier     │   │ Risk      │   │ Tier 0:        │   │ Traffic-light│
│ Share    │──▶│ Detect script &  │──▶│ (ExecuTorch, ~MBs)  │──▶│ fusion +  │──▶│  phrase bank   │──▶│ verdict      │
│ intent   │   │ language         │   │ URL analyzer (rules)│   │ threshold │   │ Tier 1:        │   │ Voice        │
│ Paste    │   │ Extract URLs,    │   │ Rule signals        │   │ → band    │   │  Llama + verify│   │ Safe action  │
└──────────┘   │ phones, amounts  │   └─────────────────────┘   └───────────┘   │  → fallback    │   │ Report/Dismiss│
               └──────────────────┘                                              └────────────────┘   └──────┬───────┘
                                                                                                             │
                                                              Local feedback adjusts threshold ◀─────────────┘
```

### 6.2 Collector and preprocessor
- **Entry points:** (a) `SMS_RECEIVED` broadcast for automatic scanning, (b) Android share intent (`ACTION_SEND`, text/plain) for WhatsApp and others, (c) paste box.
- **Normalization:** Unicode NFKC, lowercase Latin, collapse whitespace, strip zero-width characters, map Indic digits to ASCII, keep a copy of the original for display.
- **Script/language ID:** by Unicode block (cheap and reliable for the 6 scripts) plus a small heuristic for romanized Hindi vs English.
- **Extractors:** URLs (including obfuscated ones like `hxxp`, `sbi[.]com`), phone numbers, amounts, `.apk` mentions, UPI IDs.

### 6.3 Text detector (ExecuTorch)
- **Design:** hashed character n-gram features (n = 2-5, language-agnostic) into a fixed-size vector, then a small MLP (about 1-3M parameters), trained with PyTorch, exported to `.pte` with the XNNPACK backend, int8 quantized where accuracy holds.
- **Why this design:** character n-grams work across all 7 scripts and across romanized Hinglish with no per-language tokenizer, and the model stays a few MB, which is what makes Tier 0 possible on cheap phones.
- **Output:** scam probability plus multi-label reason-code scores.
- **Baselines for the report (ablations):** logistic regression on TF-IDF, and a distilled multilingual transformer (only if size permits) to show the cost/accuracy trade-off.

### 6.4 URL analyzer (rule-based, Kotlin)
Features: shortener list, TLD risk, IP-as-host, punycode, `@` or excessive subdomains, digit/hyphen density, URL length, **lookalike match** against a bundled list of about 100 Indian brands and government domains (edit distance plus keyword-in-subdomain), `.apk` path, and an optional bundled blocklist snapshot (PhishTank/OpenPhish/URLhaus, refreshed at build time, since the app has no network). **No network lookups at runtime.**

### 6.5 Risk fusion
A small calibrated combination (logistic fusion of the text score, URL score and rule flags) produces a final score mapped to three bands. Thresholds are tuned on validation data to hit a target false-positive rate, and users' local feedback nudges the threshold within a safe range.

### 6.6 Explainer and verifier (the trust layer)

**Tier 0: phrase bank.** Reason codes map to verified sentences in the user's language, plus one recommended action. Deterministic, never hallucinates, runs everywhere.

**Tier 1: Llama 3.2 1B on ExecuTorch.**
1. Input to Llama is **only** a compact JSON of evidence: band, reason codes, extracted indicators (domain, phone number, amount), and target language. The raw message is not needed for generation (reduces prompt-injection risk from attacker-controlled text).
2. Output is limited to about 60-80 tokens, low temperature, fixed format: *what it looks like → why it is risky → what to do now*.
3. **Verifier checks before display:**
   - every URL, phone number or amount in the output must appear in the evidence (no invented facts)
   - the recommended action must match the allowed action set for the band
   - **high-risk band:** output must not contain reassuring words ("safe", "genuine", "OK to click") in any supported language
   - **never** states certainty ("definitely", "100%"); hedged wording enforced
   - output language and script match the requested language
   - length and format limits are respected
4. **If any check fails, or Llama times out, or memory is low: fall back to the Tier 0 phrase bank.** The user always gets a safe answer.

**Prompt-injection note:** scam messages may contain text like "ignore previous instructions". Because Llama sees only structured evidence and not the raw message, this attack surface is removed by design. We will include an injection test in the evaluation.

### 6.7 User journey (matches the organizers' slide)
1. **Message** arrives or is shared.
2. **Detect:** score, band and reason codes in under a second on Tier 0.
3. **Explain:** text plus voice, in the user's language.
4. **Advise:** one clear primary action ("Do not click. Call your bank on the number printed on your card.") and secondary actions.
5. **Verify/Report:** buttons for 1930, cybercrime.gov.in, Sanchar Saathi Chakshu (report suspicious number/message), with a "copy details" helper.
6. **Learn:** Report / Dismiss feedback is stored locally and adjusts sensitivity.

> **Always-on rules:** never auto-click, never auto-delete, never block the user from reading their own message, never claim certainty.

### 6.8 Design decision: no INTERNET permission
The core app ships **without the Android INTERNET permission**. This makes "nothing leaves your phone" verifiable, since anyone can inspect the manifest and run the offline test. The consequence is that the roughly 1 GB Llama model pack cannot be downloaded in-app. It is delivered as a separate file (`satark-llama-1b.pte` plus tokenizer) that the user imports via an in-app file picker. This also suits rural distribution, where files move via pen drives, Bluetooth or file-sharing apps. Two release flavors:
- **Satark Lite:** small APK (target under about 20 MB), Tier 0 only
- **Satark Full:** same app plus the optional model pack import for Tier 1

---

## 7. Tiered runtime

On first launch (and after major updates), the app runs a **capability probe**: total and available RAM, CPU ABI and core count, and a ~1-second micro-benchmark. It then assigns a tier and stores it. The user can override in settings.

| Tier | Typical device | Runs | Experience |
|---|---|---|---|
| **Tier 0** | ≤3 GB RAM or weak CPU | ExecuTorch detector + URL analyzer + phrase bank + voice | Full detection, explanation and advice, all 7 languages |
| **Tier 1** | ≥4 GB RAM (final cut-off decided by benchmarks) with model pack imported | Tier 0 + Llama 3.2 1B via ExecuTorch | Richer, more natural explanations in English/Hindi/Hinglish; short follow-up questions as stretch |
| **Tier 0-lite (fallback)** | 32-bit-only (armeabi-v7a) or very old phones | Pure-Kotlin rules + linear model, no ExecuTorch | Basic detection and phrase-bank advice |

> **Risk to verify early:** ExecuTorch's Android builds target arm64. For 32-bit-only devices we need the Tier 0-lite path. We confirm this in the Day 1 de-risking step and adjust.

Tier cut-offs are **decided from measured data**, not guessed, and reported in the benchmark table.

---

## 8. Data plan

### 8.1 Sources
- **Hand-written Indian scam templates** per taxonomy code (about 15-30 each) in English, Hindi and Hinglish, then translated and verified for the other four languages
- **Public datasets** for supplementary English/spam signal (for example the UCI SMS Spam Collection) and public SMS/phishing corpora (check each license before use)
- **URL data:** PhishTank / OpenPhish / URLhaus (malicious), Tranco top domains (benign), plus our own Indian brand lookalikes
- **Legitimate Indian messages (hard negatives):** real-format bank debit/credit alerts, OTP messages ("do not share this OTP"), delivery updates, telecom recharge, government/IRCTC messages, family and friend chat. **These are critical.** Legit bank alerts contain urgency, numbers and sometimes links, and are the main cause of false positives.

### 8.2 Generation pipeline
1. Template slot-filling (bank names, amounts, UPI IDs, links, phone numbers, names)
2. Style variation: typos, spacing tricks, mixed scripts, emoji, ALL CAPS, SMS shorthand
3. Hinglish transliteration of Hindi templates
4. Translation to Marathi, Gujarati, Bengali, Odia (machine-assisted draft, then **native verification by the owner**)
5. Labeling: `is_scam`, `reason_codes[]`, `language`, `source` (template / public / hand-written)

### 8.3 Splits (leakage control)
- **Split by template family, not by augmented instance.** Variants of one template never appear in both train and test. This is the most common way hackathon projects accidentally inflate accuracy.
- **Three sets:** train / validation / test.
- **Hand-checked "real-style" test set** of about 300-500 messages written or collected separately by the owner and **never used for training or tuning**. All headline numbers in the report come from this set, with the synthetic-test numbers reported separately and labeled as such.

### 8.4 Honesty statement (goes in the report)
State clearly which data is synthetic, which is real, how it was split, and per-language sample counts. Judges reward honest, well-controlled numbers over suspiciously perfect ones.

### 8.5 Privacy and ethics
No real personal data (real phone numbers, names, account numbers) in the repo. Real messages used for the test set are anonymized. User-study data is anonymized and collected with consent.

---

## 9. Android app specification

### Screens
1. **Onboarding:** language picker (7 languages, shown in their own scripts), permission explanation in simple words, capability probe.
2. **Home:** large "Check a message" button, recent checks, status ("Protection on", "Works offline").
3. **Result:** full-screen traffic light (green / amber / red) with icon, a one-sentence reason, a large **🔊 Listen** button, the primary action button, and expandable "Why?" details.
4. **Report:** guided helpers for 1930, cybercrime.gov.in and Chakshu.
5. **Settings:** language, sensitivity, tier override, voice on/off, import Llama model pack, clear history.

### Permissions
- `RECEIVE_SMS` / `READ_SMS` for automatic scanning. **Note:** Google Play restricts these for most apps, which is fine for the hackathon APK sideload. In the report, document the Play-compliant alternative (user-initiated sharing).
- No INTERNET. No contacts, location or microphone.
- WhatsApp: **share-intent only**, no notification-listener by default. An opt-in notification listener can be a documented future option with explicit consent.

### UX principles (low-literacy friendly)
Big touch targets, minimal text, icons plus color plus voice (never color alone), one primary action per screen, no jargon, consistent placement of the Listen button.

### Tech stack
Kotlin, Jetpack Compose, ExecuTorch Android library (Java/Kotlin API), Room or DataStore for local history, Android TextToSpeech plus bundled audio clips, Gradle flavors for Lite/Full.

---

## 10. Evaluation plan

### 10.1 Detection quality
- Precision, recall, F1, **false-positive rate at the shipped threshold**, PR-AUC
- Broken down **per language**, **per scam type**, and **synthetic vs hand-checked** test sets
- Detection latency (p50 / p95)
- Robustness tests: typos, obfuscated links, mixed script, very short messages, long messages, prompt-injection strings
- Ablations: text-only vs URL-only vs fused; ExecuTorch fp32 vs int8; baseline models

### 10.2 On-device performance (the "benchmark on the actual target" requirement)
Automated harness records into a results JSON:

| Field | Measured how |
|---|---|
| Device model, Android version, SoC, RAM | system APIs |
| Model name, quantization scheme, file size | build metadata |
| ExecuTorch version | recorded at build |
| Detector latency (p50/p95) | in-app timer, N=200 runs |
| Llama time-to-first-token, tokens/sec, total time | in-app timers |
| Peak memory (PSS) | `Debug.MemoryInfo` / `dumpsys meminfo` |
| CPU load / thermal behavior (best-effort) | `top` / thermal status during runs |
| Battery impact (best-effort) | `dumpsys batterystats` |
| **Offline test** | airplane mode, full journey, screen-recorded |

**Target devices:** the owner's phone(s), **at least one genuinely low-end phone** (2-3 GB RAM; borrow one if needed), and a Raspberry Pi 5 as the CPU baseline if available. Quantization variants of Llama compared (for example 8da4w versus lower-bit schemes) to justify the shipped choice.

### 10.3 User effectiveness study (small but real)
- **Participants:** 10-15 people, deliberately mixed: age, language, tech comfort, at least several with limited English and rural backgrounds
- **Tasks:** 6 messages (3 scams, 3 legitimate) shown **without** help, then **with** Satark
- **Measures:** correct decision rate, time to decision, "why was this risky?" comprehension (asked verbally), whether they pick the right action, confidence rating, and a short usability questionnaire
- **Ethics:** informed consent, anonymized records, fictitious messages only, no real accounts
- **Reported honestly:** small sample, so we report descriptive results with limitations and no inflated claims

### 10.4 Targets (goals to validate, **not claimed results**)

| Metric | Target |
|---|---|
| Recall on hand-checked scam set | ≥ 90% |
| False-positive rate on legitimate set | ≤ 3% |
| Tier 0 detector size | ≤ 10 MB |
| Tier 0 detection latency on low-end phone (p95) | ≤ 150 ms |
| Tier 1 time-to-first-token | ≤ 3 s on supported phones |
| Lite APK size | ≤ ~20 MB |
| User study: correct decisions improve with Satark | clear improvement over unaided |

---

## 11. Repository structure

```
satark/
├── README.md                 # pitch, demo GIF, quickstart, results summary
├── LICENSE
├── docs/
│   ├── PROJECT_PLAN.md       # this file
│   ├── ARCHITECTURE.md
│   ├── DATASET_CARD.md
│   ├── PRIVACY.md
│   └── REPORT.md             # engineering report (final deliverable)
├── data/
│   ├── taxonomy.yaml         # reason codes
│   ├── templates/            # per-language scam & legit templates
│   ├── phrase_bank/          # verified explanations + actions, 7 languages
│   ├── brands.json           # Indian brands & govt domains for lookalike check
│   └── README.md             # what's committed vs generated
├── ml/
│   ├── generate_data.py
│   ├── features.py
│   ├── train_detector.py
│   ├── evaluate.py
│   ├── export_executorch.py  # .pte export
│   └── baselines/
├── llm/
│   ├── export_llama.md       # reproducible export steps & versions
│   ├── prompts/
│   └── verifier/             # verifier logic + tests
├── android/                  # Kotlin app (lite & full flavors)
├── benchmarks/
│   ├── run_benchmarks.py
│   └── results/              # JSON per device
├── user_study/               # protocol, consent text, anonymized results
├── scripts/                  # setup & build scripts
└── .github/workflows/        # lint/tests
```

Large artifacts (`.pte` models, audio clips, datasets) go to **GitHub Releases** or Git LFS, not normal commits.

---

## 12. Timeline: 3 Nov → 23 Nov (20 days)

> Plan to **submit on 22 Nov**, leaving one buffer day. Code freeze on **20 Nov**.

| Dates | Phase | Goals | Done when |
|---|---|---|---|
| **3-4 Nov** | **0. De-risk + setup** | Repo and CI created. **ExecuTorch runs a model on your phone. Llama 3.2 1B runs on-device.** Confirm 32-bit/arm64 situation. Finalize taxonomy. | Llama generates text on the phone and a toy `.pte` runs |
| **4-8 Nov** | **1. Data** | Templates for all codes, hard negatives, generation pipeline, translations started, **native verification in parallel**, hand-checked test set started | Dataset v1 + dataset card; splits by template family |
| **8-12 Nov** | **2. Detector** | Features, training, baselines, URL analyzer, fusion, thresholds, ExecuTorch export, eval harness | Per-language eval table; `.pte` under size target |
| **10-16 Nov** | **3. Android app** | Collector (SMS + share), result UI, 7-language strings and fonts, TTS and recorded clips, tier probe, feedback loop | Full Tier 0 journey works offline on a real phone |
| **13-17 Nov** | **4. Llama layer** | Prompt contract, ExecuTorch integration, verifier, fallback logic, model-pack import | Tier 1 explanations pass verifier; fallback proven by forced failures |
| **15-19 Nov** | **5. Benchmarks + user study** | Run harness on all devices, offline test recording, user study (start as soon as a usable build exists), fix top issues | Benchmark table and study data collected |
| **19-20 Nov** | **6. Freeze** | Bug fixes only; signed release APKs (Lite + Full), tag `v1.0` | Release builds installed clean on fresh devices |
| **20-22 Nov** | **7. Package** | Demo video, engineering report, README polish, setup-script test on a clean machine, submission form | Everything uploaded and links verified |
| **23 Nov** | Deadline | Buffer only | Submitted |

**Parallel tracks for efficiency:** native-language verification and audio recording run alongside coding. If something slips, the cut order is: (1) Llama Q&A stretch, (2) battery measurement, (3) Odia/Bengali recorded audio falling back to text-only, (4) the second quantization comparison. **Never cut:** Tier 0 end-to-end, the verifier, device benchmarks, offline test, honest evaluation.

---

## 13. Who does what

| Owner | Responsibilities |
|---|---|
| **You** | Native verification of Hindi, Hinglish, Marathi, Gujarati, Bengali, Odia text; recording audio clips; collecting the hand-checked test set; testing on physical phones; running the user study; recording the demo video; submission |
| **Claude (with you)** | Code for data pipeline, training, export, Android app, verifier, benchmark harness; drafting phrase bank and translations for your review; evaluation scripts; engineering report and README drafts |
| **Together** | Design decisions, debugging device issues, interpreting benchmark results |

---

## 14. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Llama 1B won't run well on target phones | High | Tier system; Tier 0 is a complete product; tested on Day 1 |
| ExecuTorch Android setup friction | High | De-risk first (Phase 0), pin exact versions, document in `llm/export_llama.md` |
| 32-bit-only phones unsupported by ExecuTorch | Medium | Tier 0-lite pure-Kotlin fallback; verify early |
| Synthetic data inflates metrics | High | Template-family splits, separate hand-checked test set, honest reporting |
| High false positives on legit bank alerts | High | Hard-negative set; threshold tuned to FPR target |
| No offline TTS voice for some languages (esp. Odia) | Medium | Recorded clips fallback |
| Translations are wrong or unnatural | High | Only ship what you verify; mark unverified entries; second reviewer from family where possible |
| Attackers craft messages to evade the model | Medium | Robustness tests; layered rules + ML; documented limitations |
| Prompt injection via message text | Medium | Llama sees evidence only, not raw text; injection test |
| SMS permission restrictions on Play Store | Low for hackathon | Sideload APK; document the compliant share-based mode |
| Time (20 days) | High | Cut order defined; freeze date fixed; daily progress log |

---

## 15. Deliverables checklist

- [ ] **Source code:** public GitHub repo, step-by-step setup scripts, README with quickstart
- [ ] **On-device app:** signed APKs (Satark Lite, Satark Full), model-pack file and instructions
- [ ] **Demo video:** end-to-end walkthrough, real threat triggers in multiple languages, shown in airplane mode, plus a low-end phone demo
- [ ] **Engineering report:** hardware mapping, quantization settings, ExecuTorch version, measured KPIs, evaluation tables, user-study results, limitations
- [ ] Dataset card and privacy statement
- [ ] Benchmark JSONs for every tested device
- [ ] Submission completed before 23 Nov (target 22 Nov)

---

## 16. After qualifying: roadmap to the PoC round (5 Feb 2027)

1. **Network module:** Raspberry Pi 5 home-network guardian (DNS/flow anomaly detection), reusing the same detect → explain → advise pipeline
2. **Hailo NPU path:** for compatible detector models on Pi 5 + AI HAT, documented separately from the Llama-on-CPU path
3. **More languages:** Tamil, Telugu, Kannada, Malayalam, Punjabi, with the same phrase-bank + verification process
4. **Voice-call scam detection** (on-device, privacy-preserving)
5. **Ask Satark:** short follow-up Q&A ("Should I reply to this?") on Tier 1
6. **Larger real-world evaluation** with community partners (with consent and ethics review)
7. **Play-compliant distribution** (share-based mode, privacy review)

---

## 17. Immediate next steps

1. Create the GitHub repo and commit this file as `docs/PROJECT_PLAN.md`
2. Phase 0 de-risking: build the ExecuTorch Android demo and run Llama 3.2 1B on your phone; report the phone model, RAM and Android version
3. Decide the languages' native-verification workflow (spreadsheet with columns: key, English, per-language text, verified ✔)
4. Begin the hand-checked test set (collect and anonymize real-style messages as you encounter them)

---

## Changelog
- **v1.0 (3 Nov 2026):** initial plan.
