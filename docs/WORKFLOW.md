# Satark: Workflow & Rules of Engagement

> **Purpose:** how we work, what we do in what order, and the rules that stop us from drifting or inventing things. If a decision isn't covered here, `PROJECT_PLAN.md` or `TECH_STACK.md`, ask before building.
> **Document hierarchy (highest wins):** `PROJECT_PLAN.md` > `TECH_STACK.md` > `WORKFLOW.md` > anything said in chat.
> **Deadline:** submit **22 Nov 2026** (hard deadline 23 Nov). **Code freeze: 20 Nov.**

---

## 1. Non-negotiables

1. **Llama + ExecuTorch, on-device.** The detector and the LLM both run through ExecuTorch.
2. **Detector produces evidence; Llama only explains.** Llama never decides if something is a scam.
3. **No INTERNET permission, no runtime network calls.**
4. **Never auto-click, auto-delete or claim certainty.**
5. **Only ship what is verified:** a language is "supported" only if its phrase bank is marked `verified` by the owner.
6. **Every number in the report comes from a saved results file**, never from memory or estimation.
7. **Primary scenario is message/SMS scams (+ URLs inside them).** Network anomaly detection is future work.

---

## 2. Anti-hallucination rules (for both of us)

| # | Rule |
|---|---|
| 1 | **Verify before using.** Any library API, CLI flag, version or file format that is not already marked ✅ in `TECH_STACK.md` must be checked against the official docs or the installed package (`--help`, source, Javadoc) before code depends on it. |
| 2 | **"I don't know" is a valid answer.** Claude must say when something is unverified instead of guessing. The owner should push back on any confident claim that lacks a source. |
| 3 | **Run it before calling it done.** Code is "done" only after it has been executed and the output saved or pasted. Claude marks untested code as **UNTESTED**. |
| 4 | **Pin versions.** Record them in `VERSIONS.lock`. Never write "latest". |
| 5 | **One source of numbers.** Metrics → `benchmarks/results/*.json` and `ml/results/*.json`. The report is generated from or checked against these files. |
| 6 | **Label synthetic data.** Every dataset row has a `source` field. Reports show synthetic and hand-checked results separately. |
| 7 | **No invented facts about scams, laws or helplines.** Helpline numbers, URLs and procedures (1930, cybercrime.gov.in, Sanchar Saathi/Chakshu) are re-checked on the official sites before release and stored with a "checked on" date in `data/resources.yaml`. |
| 8 | **Translations are drafts until the owner verifies them.** Status field: `draft` → `verified`. The app only enables a language when all its reason codes are `verified`. |
| 9 | **Cite the source for imported snippets.** If code is adapted from the ExecuTorch examples or another repo, note the source and license in a comment. |
| 10 | **Small steps.** One task, one commit, one test. If an error appears, paste the full log rather than a summary. |

---

## 3. Session protocol (important)

Claude does **not** remember earlier chats. To keep us aligned, start every new working session with:

1. Paste or attach `PROJECT_PLAN.md`, `TECH_STACK.md`, `WORKFLOW.md`
2. Paste the current `STATUS.md` (template in §8)
3. State the **one task ID** for the session (e.g. `P2-03`)
4. Paste relevant error logs, device details, or file contents

**End of every session:** update `STATUS.md` (what is done, what is broken, next task), commit, push.

---

## 4. Git conventions

- `main` always builds. Work on branches: `feat/<task-id>-<short-name>`, `fix/...`, `docs/...`
- Commit message: `P2-03: add URL lookalike detector` (task ID first)
- Tag milestones: `v0.1-phase0`, `v0.2-detector`, `v0.3-tier0-app`, `v0.4-llama`, `v1.0`
- Never commit: models, audio, raw datasets, keystores, API keys, real personal data
- `.gitignore` set up on Day 1

---

## 5. Definition of Done (applies to every task)

- [ ] Does what the task's acceptance criteria say
- [ ] Executed successfully, with output saved (log, JSON or screenshot)
- [ ] No new dependency outside `TECH_STACK.md`
- [ ] Tests added where logic exists (detector, URL analyzer, verifier, normalizer)
- [ ] Docs/README touched if behavior or setup changed
- [ ] `STATUS.md` updated, committed

---

## 6. Phases, tasks and gates

### Phase 0: Setup and de-risk (3-4 Nov)

| ID | Task | Acceptance |
|---|---|---|
| P0-01 | Create repo with structure from `PROJECT_PLAN.md` §11, `.gitignore`, LICENSE, README stub, add the three docs under `docs/` | Repo pushed |
| P0-02 | Python env: Python 3.13, `pip install executorch`, record versions | `VERSIONS.lock` has python, executorch, torch |
| P0-03 | Resolve open items in `TECH_STACK.md` §11 that block Phase 0 (AAR version exists, export flags, `LlmModule` signature) | Items ticked with evidence in `docs/evidence/` |
| P0-04 | Request/accept Llama 3.2 1B Instruct access; download weights | Weights on disk (not committed) |
| P0-05 | **Export a toy model** to `.pte` and run it in a minimal Android app on the owner's phone | Output matches Python result |
| P0-06 | **Export Llama 3.2 1B Instruct** (XNNPACK, quantized) and run it on the owner's phone (use `LlamaDemo` as reference) | The phone generates coherent text; record tokens/s and RAM |
| P0-07 | Record device facts (model, RAM, Android, ABI) and check if offline TTS voices exist for the 7 languages | `docs/evidence/devices.md` |
| P0-08 | Freeze `taxonomy.yaml` | File committed |

**🚦 Gate G0 (end of 4 Nov):** P0-05 and P0-06 must pass.
- If Llama runs → continue as planned.
- If Llama does **not** run on any available phone → switch the Llama demo to the **Pi 5 (CPU)** or a higher-RAM phone, keep Tier 0 as the main product, and note it in the report. Do not drop Llama and do not swap in another runtime.

### Phase 1: Data (4-8 Nov)

| ID | Task | Acceptance |
|---|---|---|
| P1-01 | Write scam templates for each reason code (EN, HI, Hinglish) | ≥15 families per code for priority codes, ≥8 for others |
| P1-02 | Write **hard-negative** legitimate templates (bank alerts, OTPs, delivery, telecom, govt, personal chat) | ≥150 families |
| P1-03 | Generation script: slot-filling, noise, Hinglish transliteration | Reproducible with a seed |
| P1-04 | Phrase bank drafts for all codes × 7 languages | All entries exist as `draft` |
| P1-05 | Owner verification pass per language | Entries flipped to `verified`; tracked per language |
| P1-06 | URL dataset: malicious + benign (+ Indian brand lookalikes) | Licenses noted in `DATASET_CARD.md` |
| P1-07 | Splits by template family; leakage check script | Script proves zero family overlap |
| P1-08 | Start the **hand-checked test set** (target 300-500) | Running file, anonymized, never used for training |

**🚦 Gate G1 (8 Nov):** dataset v1 + dataset card exist, leakage check passes, at least Hindi/English/Hinglish phrase bank verified.

### Phase 2: Detector (8-12 Nov)

| ID | Task | Acceptance |
|---|---|---|
| P2-01 | Normalizer, script/language ID, extractors (URL, phone, amount, `.apk`) with unit tests | Tests pass |
| P2-02 | Baseline (TF-IDF + logistic regression) with metrics | `ml/results/baseline.json` |
| P2-03 | Hashed n-gram MLP detector | Metrics per language and scam type |
| P2-04 | URL analyzer (Kotlin-portable logic first in Python for spec/tests) | Tests pass |
| P2-05 | Fusion + threshold tuning to target false-positive rate | Operating point recorded |
| P2-06 | Export detector to `.pte`; verify Python vs ExecuTorch output parity | Max diff within tolerance noted |
| P2-07 | Evaluation harness producing the report tables | `evaluate.py` runs end to end |

**🚦 Gate G2 (12 Nov):** detector `.pte` within size target, parity verified, eval table exists (even if numbers are not yet at target).

### Phase 3: Android app, Tier 0 (10-16 Nov)

| ID | Task | Acceptance |
|---|---|---|
| P3-01 | Project skeleton, flavors `lite`/`full`, no INTERNET in manifest | Manifest check passes |
| P3-02 | Load detector `.pte`, run on text, show raw result | Works on device |
| P3-03 | Kotlin URL analyzer + normalizer, matching the Python tests | Test parity |
| P3-04 | Result screen (traffic light, reason, action, Listen button) | Reviewed on device |
| P3-05 | Localization: 7 languages' strings, fonts, language picker | Renders correctly on the low-end phone |
| P3-06 | Voice: TTS where available, recorded clips elsewhere | Each language has audio or a documented gap |
| P3-07 | Entry points: share intent, SMS receiver, paste box | All three work |
| P3-08 | Capability probe and tier assignment | Tier shown in debug screen |
| P3-09 | Local feedback loop (Report/Dismiss → threshold nudge within bounds) | Unit tested |
| P3-10 | Tier 0-lite path for 32-bit-only phones (if time allows, else documented) | Decision logged |

**🚦 Gate G3 (16 Nov):** full Tier 0 journey works **offline** on a real phone in at least Hindi and English, with the rest in progress.

### Phase 4: Llama layer, Tier 1 (13-17 Nov)

| ID | Task | Acceptance |
|---|---|---|
| P4-01 | Prompt contract: evidence JSON in, bounded explanation out | Prompt saved in `llm/prompts/` with version |
| P4-02 | Verifier rules implemented and unit-tested (no invented facts, no reassurance on high risk, no certainty words, language/script match, length) | Test suite passes, including adversarial cases |
| P4-03 | Integrate `LlmModule`, streaming to UI, timeout | Works on the phone |
| P4-04 | Fallback to phrase bank on verifier failure, timeout or low memory | Forced-failure tests pass |
| P4-05 | Model-pack import flow (file picker, integrity check) | Import works without INTERNET |
| P4-06 | Prompt-injection test set | Result recorded |

**🚦 Gate G4 (17 Nov):** Tier 1 explanation shown only when verified; every forced failure ends in a safe phrase-bank answer.

### Phase 5: Benchmarks and user study (15-19 Nov)

| ID | Task | Acceptance |
|---|---|---|
| P5-01 | Benchmark harness, JSON schema (§9) | Runs on a phone |
| P5-02 | Run on every device available (owner's phone, low-end phone, Pi 5 if available) | One JSON per device |
| P5-03 | Compare Llama quantization options | Table with size, RAM, tokens/s, verifier pass rate |
| P5-04 | **Offline test** with screen recording | Video saved |
| P5-05 | User study protocol + consent text | `user_study/PROTOCOL.md` |
| P5-06 | Run study with 10-15 people | Anonymized results CSV |
| P5-07 | Fix the top issues found | Issue list closed or documented |

**🚦 Gate G5 (19 Nov):** tier cut-offs decided from data, study complete.

### Phase 6: Freeze and package (19-22 Nov)

| ID | Task | Acceptance |
|---|---|---|
| P6-01 | **Code freeze 20 Nov**, bug fixes only | Tag `v1.0` |
| P6-02 | Signed release APKs (lite, full), model pack uploaded to Releases | Clean-install test on 2 devices |
| P6-03 | Fresh-machine test of the setup scripts | Followed README from zero |
| P6-04 | Demo video: real triggers, multiple languages, airplane mode, low-end phone | Video exported |
| P6-05 | Engineering report from results files | All numbers traceable |
| P6-06 | Re-check helplines/URLs in `data/resources.yaml` | "checked on" date updated |
| P6-07 | Submit (22 Nov), keep 23 Nov as buffer | Confirmation saved |

---

## 7. Change control (how we avoid drifting)

- **New idea?** Write it in `docs/PARKING_LOT.md`. Do not build it.
- **Adopt a parked idea only if** it replaces something of equal size, it is before the freeze, and it does not break a non-negotiable.
- **Changing a decision** (tech, scope, language list): add a one-line entry to the Decision Log (§8) and to the changelog in the affected doc, then update the doc **first**, code second.
- **After 20 Nov: no new features.**
- **Cut order if we fall behind:** (1) Llama follow-up Q&A, (2) battery measurement, (3) audio clips for Odia/Bengali (fallback to text-only), (4) second quantization comparison, (5) Tier 0-lite. **Never cut:** Tier 0 end to end, the verifier, device benchmarks, the offline test, honest evaluation.

---

## 8. Templates

### `STATUS.md`

```markdown
# Status: <date>
**Current phase / gate:**
**Last completed task:**
**In progress:**
**Broken / blocked (with error log link):**
**Next task ID:**
**Devices available:**
**Hours available this week:**
**Decisions made since last status:**
```

### Decision Log (`docs/DECISIONS.md`)

```markdown
| Date | Decision | Why | Alternatives rejected | Doc updated |
|---|---|---|---|---|
```

### Phrase bank entry (`data/phrase_bank/<code>.yaml`)

```yaml
code: KYC_BANK_BLOCK
actions:
  primary: CALL_BANK_ON_CARD_NUMBER
languages:
  hi:
    status: draft        # draft | verified
    verified_by: ""      # owner name once verified
    verified_on: ""
    reason: "..."
    advice: "..."
    audio: ""            # path to recorded clip if used
```

---

## 9. Benchmark result schema (`benchmarks/results/<device>.json`)

```json
{
  "commit": "",
  "device": {"model": "", "soc": "", "ram_gb": 0, "android": "", "abi": ""},
  "versions": {"executorch": "", "llama_model": "", "quantization": "", "model_size_mb": 0},
  "detector": {"latency_ms_p50": 0, "latency_ms_p95": 0, "runs": 200, "peak_pss_mb": 0},
  "llama": {"ttft_ms": 0, "tokens_per_s": 0, "peak_pss_mb": 0, "verifier_pass_rate": 0},
  "tier_assigned": "",
  "offline_test": {"airplane_mode": true, "video": ""},
  "notes": ""
}
```

---

## 10. Weekly rhythm

| Day | Do |
|---|---|
| Start of day | Read `STATUS.md`, pick the next task ID |
| During | One task at a time; commit after each |
| End of day | Update `STATUS.md`, push, note blockers |
| At each gate | Review gate criteria honestly; if failed, apply the stated contingency |
