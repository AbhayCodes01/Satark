# Satark: Tech Stack (Locked Reference)

> **Purpose:** the single list of technologies we are allowed to use, with what has been *verified* versus what is still an assumption. If a tool, library or version is not in this file, we do not use it until it is added here through a change request (see `WORKFLOW.md`, section 7).
> **Last verified:** 3 Nov 2026 · **Owner:** project owner · **Related:** `PROJECT_PLAN.md`, `WORKFLOW.md`

## Status legend

| Mark | Meaning |
|---|---|
| ✅ **Verified** | Checked against an official or primary source on the date shown |
| 🔶 **Verify in Phase 0** | Believed correct but must be confirmed on our machine/phone before relying on it |
| 🔒 **Decision** | Our own design choice, not a fact about the outside world |
| ⛔ **Forbidden** | Must not be used |

**Rule:** a 🔶 item may not appear in the report or demo as a fact until it is promoted to ✅ with evidence (a command output, a log or a doc link) saved in `docs/evidence/`.

---

## 1. Runtime: ExecuTorch (mandatory)

| Item | Value | Status |
|---|---|---|
| Python package | `executorch` on PyPI, **1.5.0** exists (release files signed Sep 2026). Patch releases (e.g. 1.5.x) may exist. | ✅ 3 Nov 2026 |
| Android library | `org.pytorch:executorch-android` on Maven Central | ✅ 3 Nov 2026 |
| Android AAR ABIs | **`arm64-v8a` and `x86_64` only** | ✅ 3 Nov 2026 |
| Consequence of the above | 32-bit-only phones (`armeabi-v7a`) cannot run ExecuTorch, so they use the **Tier 0-lite** pure-Kotlin path | ✅ derived |
| Version rule | **The `.pte` exporter version and the Android AAR version must be identical.** ExecuTorch recommends the runtime match the version that generated the `.pte`. | 🔒 |
| Version to pin | Prefer **1.5.0** if `org.pytorch:executorch-android:1.5.0` exists on Maven Central. If not, pin **1.4.x** for *both* exporter and AAR. The Maven page we saw listed 1.4.0, so the 1.5.0 AAR must be checked. | 🔶 Phase 0 |
| AAR runtime dependencies | The 1.4.0 pom lists `kotlin-stdlib 1.9.23`, `fbjni 0.7.0`, `nativeloader 0.10.5`. Re-check the pom for the version we pin. | 🔶 Phase 0 |
| Backend for all our models | **XNNPACK (CPU)** | 🔒 |
| Hailo / Qualcomm / other NPUs | Not in v1 | 🔒 |
| Java API classes | `Module`, `EValue`, `Tensor` (generic models); `LlmModule`, `LlmCallback` (LLMs) | ✅ names seen in official docs/README |
| Exact constructor/method signatures | **Do not guess.** Read the Javadoc / source for the pinned version before writing code. Signatures changed across releases. | 🔶 Phase 0 |

## 2. Language model: Llama (mandatory)

| Item | Value | Status |
|---|---|---|
| Model | **Llama 3.2 1B Instruct** | 🔒 |
| Access | Gated by Meta's license (accept terms on Meta/Hugging Face to download) | 🔶 do on Day 1 |
| License obligations | Llama community license has attribution/naming conditions for distribution. **Read the exact terms before the public release** and add the required notice to the app and README. | 🔶 Phase 0 |
| Export route A (primary) | ExecuTorch's `export_llm` API, invoked as `python -m executorch.extension.llm.export.export_llm` with `--model llama3_2` style arguments. **Read `--help` and the docs for the pinned version for the exact flags.** | ✅ command form seen; flags 🔶 |
| Export route B (fallback) | Optimum-ExecuTorch: `optimum-cli export executorch --model meta-llama/Llama-3.2-1B ... --recipe xnnpack --qlinear 8da4w --qembedding 4w` (example seen in ExecuTorch docs). We need the **Instruct** variant, so check the model id. | ✅ form seen; model id 🔶 |
| Quantization candidates | 8da4w (4-bit weights, 8-bit dynamic activations), SpinQuant, QAT+LoRA. Final choice by **our measured** accuracy, memory and speed. | 🔒 candidates ✅ supported per ExecuTorch docs |
| Reference app | `meta-pytorch/executorch-examples` → `llm/android/LlamaDemo` (use as the integration reference) | ✅ link seen |
| Tokenizer | Required alongside the `.pte` (file type depends on export route). Record which. | 🔶 Phase 0 |
| Languages Llama is used for | English, Hindi, Hinglish only. The other 4 languages use the phrase bank. | 🔒 |
| Llama's official language list (includes Hindi) | Re-check on the Llama 3.2 model card | 🔶 |

### Reference numbers (Meta's, NOT ours)

Meta's ExecuTorch Llama documentation reported these for Llama 3.2 1B on a **OnePlus 12** (a flagship): SpinQuant ≈ **50 tokens/s decode** and ≈ **1.9 GiB RSS**; bf16 ≈ **19 tokens/s** and ≈ **3.2 GiB RSS**.

**What it means for us:** a 1B model needs roughly 2 GiB of RAM for itself. On a 4 GB phone, Android and other apps already use much of the memory, so **Tier 1 likely needs ≥6 GB RAM**. This is a hypothesis. Our own benchmark table decides the cut-off. Never quote Meta's numbers as ours.

## 3. Detector (ML side)

| Item | Value | Status |
|---|---|---|
| Framework | PyTorch (installed as a dependency of `executorch`; **do not install a separate torch version**) | 🔒 |
| Python | **3.13** (a cp313 Linux x86_64 wheel exists for executorch 1.5.0). If a problem appears, fall back to the newest version that has wheels. | ✅ wheel seen / 🔶 on our machine |
| Features | Hashed character n-grams (n = 2-5) into a fixed-size vector | 🔒 |
| Model | Small MLP (about 1-3M params), int8 where accuracy holds | 🔒 |
| Export | `torch.export` → ExecuTorch `.pte` with XNNPACK | ✅ standard flow |
| Baselines (report only) | scikit-learn logistic regression on TF-IDF | 🔒 |
| Supporting libs (pin exact versions via `pip freeze` in Phase 0) | `numpy`, `pandas`, `scikit-learn`, `pyyaml`, `rapidfuzz`, `pytest`, `ruff` | 🔒 names / 🔶 versions |
| URL parsing | Python stdlib `urllib.parse` (+ `tldextract` only if needed offline-safe) | 🔒 |

## 4. Android app

| Item | Value | Status |
|---|---|---|
| Language / UI | **Kotlin + Jetpack Compose** | 🔒 |
| Build | Gradle (Kotlin DSL); versions of AGP, Kotlin, Compose BOM, Gradle = **whatever the current stable Android Studio project template generates, then frozen and recorded** | 🔶 Phase 0 |
| `minSdk` | Choose the **lowest** level that the pinned ExecuTorch AAR supports (read its manifest) and that Compose supports. Goal: reach old budget phones. | 🔶 Phase 0 |
| ABI | Release: `arm64-v8a`. Debug/emulator: `x86_64` allowed. | ✅ AAR limit / 🔒 |
| ExecuTorch dependency | `implementation("org.pytorch:executorch-android:<pinned>")` | ✅ coordinate |
| Local storage | DataStore (settings, thresholds), Room (history) | 🔒 |
| TTS | Android platform `TextToSpeech` (offline voices where present) | 🔒 |
| Recorded audio clips | Short mono clips for the phrase bank, used where TTS voice is missing (expected for Odia) | 🔒 / voice availability 🔶 per device |
| Fonts | Noto Sans (Devanagari, Bengali, Gujarati, Oriya) bundled in the app | 🔒 license check 🔶 |
| SMS access | `RECEIVE_SMS`/`READ_SMS` (sideloaded APK only) | 🔒 |
| Share-in | `ACTION_SEND` intent, `text/plain` | ✅ standard Android |
| **Permissions NOT requested** | **INTERNET**, contacts, location, microphone, camera | 🔒 |
| Release flavors | `lite` (Tier 0 only), `full` (+ model-pack import) | 🔒 |
| Signing | A release keystore generated once, **backed up outside the repo** | 🔒 |
| Min test devices | Owner's phone, one low-end phone (2-3 GB RAM), emulator for UI only | 🔶 devices to be confirmed |

## 5. Raspberry Pi 5 (baseline only)

| Item | Value | Status |
|---|---|---|
| OS | 64-bit Raspberry Pi OS | 🔒 |
| Runtime | `pip install executorch` (aarch64 manylinux wheels exist for 1.5.0) | ✅ wheel seen / 🔶 on our Pi |
| Role | CPU baseline numbers for the report, not a product target in v1 | 🔒 |

## 6. Data and evaluation

| Item | Value | Status |
|---|---|---|
| Taxonomy | `data/taxonomy.yaml` (20 reason codes in `PROJECT_PLAN.md` §5) | 🔒 |
| Phrase bank format | YAML/JSON, one entry per `(reason_code, language)` with `status: draft | verified` and `verified_by` | 🔒 |
| Splits | By **template family**, never by augmented instance | 🔒 |
| Hand-checked test set | 300-500 messages, never used for training or tuning | 🔒 |
| Public data sources | UCI SMS Spam Collection (English), PhishTank/OpenPhish/URLhaus (malicious URLs), Tranco (benign domains). **Check each license/terms before use and record it in `DATASET_CARD.md`.** | 🔶 licenses |
| Machine translation | Allowed **only at dev time** to draft translations. Nothing ships as `verified` until the owner has checked it. | 🔒 |

## 7. Benchmarking tools

| Item | Tool |
|---|---|
| Device info | `adb shell getprop`, `Build.*` APIs |
| Memory | `Debug.MemoryInfo` (PSS) in app, `adb shell dumpsys meminfo <pkg>` |
| Latency | In-app `System.nanoTime()` timers, N ≥ 200 runs, report p50/p95 |
| LLM speed | Time-to-first-token and tokens/sec from the `LlmCallback` stream |
| Battery | `adb shell dumpsys batterystats` (best effort) |
| Offline test | Airplane mode + screen recording |
| Output | One JSON per device in `benchmarks/results/` using the schema in `WORKFLOW.md` §9 |

## 8. Repo and CI

| Item | Value |
|---|---|
| Host | GitHub, public |
| Default branch | `main` |
| CI | GitHub Actions: `ruff` + `pytest` for Python, Gradle `assembleLiteDebug` for Android |
| Large files | Models (`.pte`), tokenizers, audio and datasets go in **GitHub Releases** (check per-file size limits first 🔶) or Git LFS. Never in normal commits. |
| License | App code: Apache-2.0 (🔒, compatible with ExecuTorch). Model files keep their own licenses. |

---

## 9. ⛔ Forbidden list (drift guard)

- Any **network call at runtime** in the app, and the **INTERNET permission**
- Cloud LLM or cloud ML APIs at runtime (OpenAI, Anthropic, Gemini, etc.). Dev-time drafting of translations is allowed, runtime use is not.
- Firebase, analytics, crash reporters, ad SDKs, Google Play Services dependencies
- Other on-device runtimes for the **shipped** models (TFLite, ONNX Runtime, llama.cpp, MLC, MediaPipe LLM). Using them would break the "Llama + ExecuTorch" requirement.
- Any LLM other than Llama in the shipped pipeline
- Auto-click, auto-delete or auto-block of user messages
- Unverified translations marked as verified
- Real personal data in the repo

## 10. Version lock file (fill during Phase 0, then freeze)

Create `VERSIONS.lock` in the repo root and keep it current. Every benchmark JSON references the commit that matches it.

```
executorch_python:        # e.g. result of: pip show executorch
executorch_android_aar:   # must equal executorch_python
python:
torch:                    # result of pip freeze
llama_model_id:           # exact HF/Meta id and revision
llama_quantization:       # exact flags used
tokenizer_file:
android_studio:
gradle:
agp:
kotlin:
compose_bom:
minSdk:
compileSdk:
targetSdk:
test_devices:             # model, RAM, Android version, ABI
```

## 11. Open verification items (close these in Phase 0)

- [ ] Does `org.pytorch:executorch-android:1.5.0` exist on Maven Central? If not, pin 1.4.x for both sides.
- [ ] Exact `export_llm` flags for Llama 3.2 1B **Instruct** on the pinned version, and which quantization recipe works on our machine
- [ ] `LlmModule` constructor and `generate` signatures in the pinned AAR
- [ ] Tokenizer file type required by the chosen export route
- [ ] `minSdk` of the AAR
- [ ] Llama license terms for redistributing a quantized model pack and the required attribution text
- [ ] Which of our 7 languages have an **offline** Android TTS voice on the test phones
- [ ] Peak RAM of Llama 3.2 1B on the owner's phone, which sets the Tier 1 cut-off
- [ ] Per-file size limit for GitHub Release assets vs our model pack size
