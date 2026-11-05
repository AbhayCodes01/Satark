# Satark repo skeleton (task P0-01)
# Run from the repo root (the folder that contains PROJECT_PLAN.md):
#   powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1
# Safe to re-run: existing files are never overwritten.

$ErrorActionPreference = "Stop"
$utf8 = New-Object System.Text.UTF8Encoding $false

function Write-FileSafe([string]$Path, [string]$Content) {
    if (Test-Path $Path) { Write-Host "skip (exists): $Path"; return }
    $dir = Split-Path $Path -Parent
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [System.IO.File]::WriteAllText((Join-Path (Get-Location) $Path), $Content, $utf8)
    Write-Host "created: $Path"
}

# ---------- folders ----------
$folders = @(
  "docs/evidence", "data/templates", "data/phrase_bank", "data/raw", "data/processed",
  "ml/baselines", "ml/results", "llm/prompts", "llm/verifier", "android",
  "benchmarks/results", "user_study", "scripts", ".github/workflows"
)
foreach ($f in $folders) {
    New-Item -ItemType Directory -Path $f -Force | Out-Null
    $keep = Join-Path $f ".gitkeep"
    if (-not (Test-Path $keep)) { New-Item -ItemType File -Path $keep | Out-Null }
}

# ---------- move planning docs into docs/ ----------
foreach ($d in @("PROJECT_PLAN.md", "TECH_STACK.md", "WORKFLOW.md")) {
    if (Test-Path $d) {
        Move-Item $d (Join-Path "docs" $d) -Force
        Write-Host "moved: $d -> docs/$d"
    }
}
if (-not (Test-Path "docs/WORKFLOW.md")) { Write-Warning "docs/WORKFLOW.md is missing. Download it and place it in docs/." }

# ---------- .gitignore ----------
Write-FileSafe ".gitignore" @'
# Python
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.ipynb_checkpoints/

# Models and large artifacts (use GitHub Releases or Git LFS)
*.pte
*.pth
*.safetensors
*.gguf
tokenizer.model
tokenizer.bin
data/raw/*
data/processed/*
!data/raw/.gitkeep
!data/processed/.gitkeep
data/audio/

# Android
android/.gradle/
android/build/
android/app/build/
android/local.properties
*.apk
*.aab
*.aar
*.jks
*.keystore

# Secrets and OS files
.env
*.pem
.DS_Store
Thumbs.db
.idea/
'@

# ---------- README stub ----------
Write-FileSafe "README.md" @'
# Satark

On-device scam and phishing shield for every Indian smartphone.
Works offline, explains in 7 languages (English, Hindi, Hinglish, Marathi, Gujarati, Bengali, Odia), built on Llama + ExecuTorch.

**Status:** Phase 0 (setup). See `docs/PROJECT_PLAN.md`, `docs/TECH_STACK.md`, `docs/WORKFLOW.md` and `STATUS.md`.

Setup instructions, demo and results will be added as the project progresses.
'@

# ---------- STATUS.md ----------
Write-FileSafe "STATUS.md" @'
# Status: 4 Nov 2026
**Current phase / gate:** Phase 0 -> Gate G0 (target 4 Nov)
**Last completed task:** P0-01 (repo skeleton) once bootstrap.ps1 has run
**In progress:** P0-02 Python env, P0-03 verification items, P0-04 Llama access
**Broken / blocked:** none yet
**Next task ID:** P0-02
**Devices available:** (fill in: phone model, RAM, Android version)
**Hours available this week:** (fill in)
**Decisions made since last status:** none
'@

# ---------- VERSIONS.lock ----------
Write-FileSafe "VERSIONS.lock" @'
executorch_python:
executorch_android_aar:   # must equal executorch_python
python:
torch:
llama_model_id:
llama_quantization:
tokenizer_file:
android_studio:
gradle:
agp:
kotlin:
compose_bom:
minSdk:
compileSdk:
targetSdk:
test_devices:
'@

# ---------- docs stubs ----------
Write-FileSafe "docs/PARKING_LOT.md" @'
# Parking lot
Ideas that are NOT being built. Adopt one only if it replaces something of equal size, before the 20 Nov freeze, and breaks no non-negotiable (see WORKFLOW.md section 7).

| Date | Idea | Why it might matter |
|---|---|---|
'@

Write-FileSafe "docs/DECISIONS.md" @'
# Decision log

| Date | Decision | Why | Alternatives rejected | Doc updated |
|---|---|---|---|---|
| 2026-11-03 | Primary scenario: message/SMS scams + URLs. Tiered runtime. 7 languages. | See PROJECT_PLAN.md | Network anomaly (future), full multi-channel | PROJECT_PLAN.md v1.0 |
'@

Write-FileSafe "docs/evidence/README.md" @'
# Evidence
Saved command outputs, logs and screenshots that promote items in TECH_STACK.md from "verify" to "verified".
Name files like: `P0-02-pip-freeze.txt`, `P0-06-llama-on-phone.md`.
'@

# ---------- data/taxonomy.yaml ----------
Write-FileSafe "data/taxonomy.yaml" @'
# Reason codes. Each needs a phrase-bank entry in all 7 languages.
version: 1
codes:
  - {code: URGENCY,                name: Pressure language,                 group: text, priority: false}
  - {code: KYC_BANK_BLOCK,         name: Fake bank / KYC,                   group: text, priority: false}
  - {code: OTP_REQUEST,            name: OTP / PIN / CVV theft,             group: text, priority: false}
  - {code: UPI_COLLECT,            name: UPI collect / refund trick,        group: text, priority: false}
  - {code: LOTTERY_PRIZE,          name: Lottery / prize,                   group: text, priority: false}
  - {code: ELECTRICITY_DISCONNECT, name: Fake electricity bill,             group: text, priority: false}
  - {code: COURIER_CUSTOMS,        name: Fake courier / customs,            group: text, priority: false}
  - {code: DIGITAL_ARREST,         name: Impersonating police / agencies,   group: text, priority: false}
  - {code: SIM_BLOCK,              name: Fake telecom / SIM block,          group: text, priority: false}
  - {code: FAKE_CHALLAN,           name: Fake e-challan / RTO,              group: text, priority: true}
  - {code: JOB_TASK_SCAM,          name: Part-time job / task scam,         group: text, priority: false}
  - {code: LOAN_APP,               name: Predatory loan app,                group: text, priority: false}
  - {code: GOVT_SCHEME,            name: Fake government scheme,            group: text, priority: false}
  - {code: INVESTMENT_CRYPTO,      name: Investment / crypto,               group: text, priority: false}
  - {code: MALICIOUS_APK,          name: APK file or install link,          group: text, priority: true}
  - {code: LOOKALIKE_DOMAIN,       name: Brand impersonation URL,           group: url,  priority: false}
  - {code: SHORTENED_URL,          name: Shortened URL,                     group: url,  priority: false}
  - {code: SUSPICIOUS_TLD_OR_IP,   name: Risky URL structure,               group: url,  priority: false}
  - {code: UNKNOWN_SENDER_LINK,    name: Link from unfamiliar sender,       group: rule, priority: false}
  - {code: GENERIC_SUSPICIOUS,     name: Flagged without a clear code,      group: text, priority: false}
languages: [en, hi, hinglish, mr, gu, bn, or]
'@

# ---------- data/resources.yaml ----------
Write-FileSafe "data/resources.yaml" @'
# Reporting resources shown in the app.
# RULE: nothing here is trusted until checked_on is filled after visiting the official site.
resources:
  - id: national_cybercrime_helpline
    label: National cybercrime helpline
    value: "1930"
    checked_on: ""
  - id: cybercrime_portal
    label: National Cyber Crime Reporting Portal
    value: "cybercrime.gov.in"
    checked_on: ""
  - id: sanchar_saathi
    label: Sanchar Saathi (report suspected fraud communication)
    value: "sancharsaathi.gov.in"
    checked_on: ""
'@

Write-Host ""
Write-Host "Done. Next: git init / commit / push (see the chat instructions)."
