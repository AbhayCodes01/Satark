# SATARK
## Offline-first scam and phishing message screening prototype

SATARK is a prototype intended to help smartphone users identify potentially fraudulent SMS and messaging content. Its proposed workflow combines message classification, URL indicators, structured evidence, and a cautious user-facing explanation.

### Current demonstrated state
- The Python command-line pipeline was run locally with an English OTP example and a Hinglish everyday-conversation example.
- The English OTP example returned `SAFE_LOOKING`, score `0.037`, with no reason codes.
- The benign Hinglish conversation returned `SUSPICIOUS`, score `0.553`, reason code `GENERIC_SUSPICIOUS`. This is a known false positive requiring further validation.
- Llama 3.2 1B Instruct was exported for ExecuTorch 1.5.1. The model was loaded in the Android LlamaDemo/reference app on a OnePlus 13R and generated a response.
- The Android Llama response was not consistently aligned with the Python phrase-bank explanation. The complete detector → evidence → Llama → verifier → fallback flow has **not** been demonstrated as integrated into the Android app.

### Architecture
1. Message text is assessed by a baseline text classifier.
2. URL indicators check for suspicious link patterns (where URLs are present).
3. The pipeline emits structured evidence, including risk band, score, reason codes and URL indicators.
4. A trusted phrase-bank explanation is available as a deterministic fallback.
5. Llama is intended to explain structured evidence only; it must not be the sole detector and should not receive the raw message.
6. A verifier should reject unsafe, overconfident, or unsupported explanations and use the phrase-bank fallback.

### Machine-learning baseline
The documented baseline uses character-level TF-IDF features with n-grams and Logistic Regression. A multi-label classifier predicts reason codes. The generated dataset contains approximately 1,316 synthetic rows across 24 scenario families in English, Hindi and Hinglish, with scenario-family splitting intended to reduce near-duplicate leakage.

**Important evaluation limitation:** The dataset is synthetic and the supplied examples are only a small functional smoke test. No real-world accuracy, precision, recall, or production-readiness claim is made.

### Model and device
The project handoff identifies an ExecuTorch 1.5.1 export:
`build/llama32_1b_8da4w_et151.pte`
with tokenizer:
`models/llama-3.2-1b-instruct/original/tokenizer.model`

The handoff records an approximately 802 MB exported model and XNNPACK / 8da4w configuration. The Android reference app generated a response on a OnePlus 13R. A single screenshot displayed 50.54 tokens/s and 0.89 s; this is an app-reported observation, not a controlled benchmark. RAM usage, power consumption, thermal behaviour and repeatability have not been measured.

### Run the Python prototype
From the repository root, activate the project's `.venv151` environment, then run:

```powershell
python ml\pipeline.py --demo
python ml\pipeline.py "Your OTP for login is 482913. Do not share it with anyone. -Paytm" --lang en
python ml\pipeline.py "Bhaiya kal subah 7 baje station aa jana, main gaadi leke aaunga" --lang hinglish
```

### Known limitations / next steps
- Investigate the false positive on ordinary Hinglish conversation.
- Evaluate with a balanced, anonymised, hand-labelled dataset of legitimate, scam and ambiguous messages.
- Verify all phrase-bank translations with fluent reviewers.
- Verify the Android Gradle dependency and runtime are compatible with ExecuTorch 1.5.1.
- Integrate the detector into the Android application; the Python `.joblib` model cannot simply be loaded directly by Kotlin.
- Integrate evidence-only explanation, output verification and phrase-bank fallback.
- Test offline operation and privacy behaviour on the target device.
- Measure latency, peak memory, power and thermal performance under a repeatable protocol.

### Safety and privacy principles
- Do not guarantee that a message is safe or genuine.
- Do not automatically click links or delete messages.
- Do not send raw message text to the language model; pass structured evidence only.
- Verify requests through independently obtained official channels.
- Never expose real OTPs, credentials, private messages, tokens or API keys in demos or the repository.

### Repository hygiene
Do not commit `.venv*`, model weights, `.pte` files, Hugging Face tokens, API keys, secrets, generated caches or personal data unless the challenge explicitly requires a separately hosted model artifact.
