# Satark (सतर्क)

**An offline-first scam and phishing shield for every Indian smartphone.**
Checks a message, tells you how risky it looks, explains why in your own language, and says one safe thing to do. Built for the **Arm Bharat AI-SoC Challenge 2026-27, PS3** with **Llama 3.2 1B on ExecuTorch**.

**Languages:** English · हिन्दी · Hinglish · मराठी · ગુજરાતી · বাংলা · ଓଡ଼ିଆ
(Explanation text drafted for all seven; a language counts as supported only after native-speaker verification, which is in progress.)

## Status (Phase 1, Open Qualifying)

| Part | State |
|---|---|
| Detector + link rules + risk fusion | Working (Python, PC) |
| Trusted explanations, 7 languages | Drafted, being verified |
| Llama 3.2 1B exported to ExecuTorch (`.pte`, XNNPACK, 8da4w) | Done |
| Llama safety verifier (rejects "safe", invented facts, false certainty) | Working |
| Llama running on an Arm phone | Working: OnePlus 13R via Meta's reference app, about 24-36 tokens/s as shown by the app. Raw output is unreliable, so every reply is verified (report section 7) |
| Detector ported to Kotlin (`android/SatarkCore.kt`), proven identical to Python on 1,494/1,494 cases | Done |
| Detector connected to the phone app screen | [FILL: done / in progress] |
| Full custom app, user study | Phase 2 |

Numbers in this repo come from **synthetic data** and are not real-world accuracy. See the report's limitations.

## How it works

```
message → detector + link rules → evidence → risk band → explanation → safe action
                                      │
                                      └→ Llama (sees ONLY the evidence) → verifier → else trusted phrase bank
```
Rules: Llama never decides; every Llama answer is verified; nothing is auto-clicked or auto-deleted; the app never claims certainty or says a message is "safe".

## Quick start (Windows, Python 3.13)

```powershell
python -m venv .venv151
.\.venv151\Scripts\Activate.ps1
pip install executorch==1.5.1
pip install torch==2.14.0 --extra-index-url https://download.pytorch.org/whl/cpu
pip install scikit-learn joblib

python ml\generate_data.py        # builds the synthetic dataset (1,316 rows)
python ml\check_leakage.py        # proves no scenario is shared across splits
python ml\check_phrase_bank.py    # checks the 7-language explanation text
python ml\train_baseline.py       # trains the detector, prints per-language results
python ml\pipeline.py --demo      # end-to-end examples + verifier check
```
Try your own message:
```powershell
python ml\pipeline.py "Dear customer, your SBI account will be blocked. Update KYC: http://sbi-kyc.xyz/a1" --lang en --llama-prompt
```
Check what Llama said on the phone: add `--verify "<Llama's answer>"`.

## Llama on ExecuTorch

Needs access to `meta-llama/Llama-3.2-1B-Instruct` on Hugging Face. Config: `llm/llama32_1b_8da4w_et151.yaml`.
```powershell
$env:PYTHONUTF8 = "1"
python -m executorch.extension.llm.export.export_llm --config llm\llama32_1b_8da4w_et151.yaml
```
Use **the same ExecuTorch version for export and for the Android library**. The newest Android library on Maven Central is 1.5.1, so the model is exported with 1.5.1.

Run on a phone with Meta's reference app (`meta-pytorch/executorch-examples`, `llm/android/LlamaDemo`, ExecuTorch dependency set to 1.5.1):
```powershell
adb shell mkdir -p /data/local/tmp/llama
adb push build\llama32_1b_8da4w_et151.pte /data/local/tmp/llama/
adb push models\llama-3.2-1b-instruct\original\tokenizer.model /data/local/tmp/llama/
```

**Demo video:** [FILL: link]

## Repository map

```
docs/    plan, tech stack, workflow, ENGINEERING_REPORT.md, evidence/ (logs)
data/    taxonomy, templates, slot values, phrase bank (7 languages)
ml/      generate_data, check_leakage, check_phrase_bank, train_baseline, pipeline
llm/     ExecuTorch export configs for Llama 3.2 1B
android/ Kotlin detector core + parity test; assets in android/assets (model, rules, phrase bank)
scripts/ ExecuTorch toy export check
```
Large files (models, `.pte`) are not in git. Llama weights are under Meta's license; request access on Hugging Face.

## License and notices

Application code: Apache-2.0 (add a LICENSE file). **Built with Llama.** Llama 3.2 is licensed under the Llama 3.2 Community License; model files keep their own license.
