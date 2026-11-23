# P4: Llama 3.2 1B on the phone: real outputs (23 Nov 2026)

**Device:** OnePlus 13R (CPH2691), Snapdragon 8 Gen 3, 12 GB RAM (RAM expansion enabled), Android 16.
**App:** Meta's reference `LlamaDemo` (executorch-examples), built from source with `org.pytorch:executorch-android:1.5.1`.
**Model:** `llama32_1b_8da4w_et151.pte` (802,247,040 bytes), `tokenizer.model`, copied to `/data/local/tmp/llama/`.
**App settings:** backend XNNPACK, model type LLAMA_3, no data path, temperature 0.00.
Replies were transcribed from phone screenshots.

## Prompt 1 (reasons written in words)

```
You are Satark, an Indian scam-safety assistant.

The detector has already classified the message.
Your job is ONLY to explain the supplied evidence.

Risk: DANGEROUS
Reasons:
- KYC/bank block
- Lookalike domain
- Suspicious domain extension
- Urgent language

Domain: sbi-kyc.xyz

Respond in exactly 3 short sentences:
1. Explain what looks suspicious.
2. Explain why it matters.
3. Give one safe action.

Never say safe, genuine or confirmed fraud.
Never invent information.
Never ask for personal information.
Do not refuse to provide scam-safety guidance.
```

**Llama's reply** (app footer: `24.20 t/s | 6.244s`):

```
Here are the explanations:
1. Explain what looks suspicious. The domain "sbi-kyc.xyz" looks suspicious because it is a variation of the official domain "sbi-kyc.com", which is the official domain of the State Bank of India.
2. Explain why it matters. This variation is suspicious because it is a domain that is not associated with the State Bank of India, which is a well-known and reputable financial institution in India.
3. Give one safe action. One safe action is to report this domain to the relevant authorities, such as the Federal Trade Commission (FTC) in the United States, to report this type of scam.
```

## Prompt 2 (evidence JSON, stricter rules)

```
You are SATARK, a scam-safety assistant for ordinary smartphone users in India.

The scam detector has already analysed the message. Your ONLY job is to explain the supplied evidence and provide safe guidance.

EVIDENCE:
{"risk_band":"DANGEROUS","reason_codes":["KYC_BANK_BLOCK","LOOKALIKE_DOMAIN","SUSPICIOUS_TLD_OR_IP","URGENCY"],"link_domains":["sbi-kyc.xyz"],"apk_link":false}

STRICT OUTPUT RULES:
- Write exactly 3 short sentences.
- Do not repeat these instructions.
- Do not use numbered lists, headings or introductions.
- Sentence 1: Explain why the message looks suspicious.
- Sentence 2: Explain the possible danger.
- Sentence 3: Give one practical safety action.
- Use simple Indian English.
- Never invent official domains, phone numbers, authorities or facts.
- Never say a message is safe or confirmed fraudulent.
- Never refuse to provide scam-safety guidance.
- Never ask for personal information.
- Only use information supported by the evidence.
```

**Llama's reply** (app footer: `35.76 t/s | 7.581s`):

```
Here's the explanation of the evidence and safe guidance:

The message looks suspicious because it contains several red flags, including a "DANGEROUS" risk band, "KYC BANK BLOCK" reason codes, "LOOKALIKE_DOMAIN" domain names, "SUSPICIOUS TLD OR IP" suspicious TLD or IP, and "URGENCY" reason codes. This suggests that the message may be a phishing attempt or a scam.

The possible danger is that the message may be a phishing attempt or a scam that could compromise the user's personal and financial information. This is especially true for KYC (Know Your Customer) banking, where the user's personal and financial information is being verified.

One practical safety action is to be extremely cautious when receiving unsolicited messages or calls from unknown numbers. If you receive a message that asks you to verify your account or provide personal information, it's best to err on the side of caution and not respond to the message. Instead, report the message to the relevant authorities, such as the National Consumer Helpline (NCH) in India, or the Federal Trade Commission (FTC) in the United States.
```

## What this shows

**Works:** the exported model loads and generates on the phone via ExecuTorch (XNNPACK, Arm CPU). The app displayed 24.20 and 35.76 tokens per second, and 6.2 s and 7.6 s for the two replies. (These are the app's own on-screen figures; we have not independently verified how the app defines them.)

**Does not work reliably: instruction following.** At 1B parameters Llama ignored the explicit format rules in both prompts:

| Rule in the prompt | Reply 1 | Reply 2 |
|---|---|---|
| "Exactly 3 short sentences" | Broke it (numbered list, repeats the instructions) | Broke it (three long paragraphs, about 200 words) |
| "Never invent information / authorities" | Invented that `sbi-kyc.com` is the official State Bank of India domain; named the US Federal Trade Commission | Named the US Federal Trade Commission and a "National Consumer Helpline (NCH)", neither supported by the evidence |
| "Do not use lists / introductions" | Used a list and an introduction | Used an introduction |
| Internal labels should not leak | n/a | Echoed `LOOKALIKE_DOMAIN`, "KYC BANK BLOCK", "DANGEROUS" |

**What it did right (both replies):** used hedged wording ("may be a phishing attempt or a scam"), did not say the message was safe, did not claim certainty, did not ask for personal information.

## What our safety layer did

`ml/pipeline.py --demo` runs both real replies through `verify_llama_output`. **Both were rejected**, and the user would have been shown the trusted phrase-bank text instead. Rejection reasons included: too long, too many sentences, numbered list or preamble, leaked internal codes, invented authority (FTC, US), invented domain, numbers not in the evidence. A good answer in English, Hindi and Hinglish is accepted, and reassuring or over-confident text is rejected.

The verifier checks listed above that catch invented authorities and leaked labels were added **because of this test**. They did not exist before these two replies were captured.

## Implication for the design

This is direct evidence for the rule "Llama explains, the detector decides, and every Llama output is verified before the user sees it." A 1B model cannot be trusted to follow constraints, so a verified fallback is not optional.

## Not yet measured

Model load time, peak memory (the app header shows about 8.3 to 8.4 GB, but we have not established whether that is the app or the whole phone), battery, and an offline (airplane mode) run. Only two prompts, one scenario, have been tried. A shorter prompt with one worked example, a hard token limit, trimming to three sentences, or the 3B model might improve compliance; none of these has been tested.
