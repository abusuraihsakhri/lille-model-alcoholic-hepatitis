# Lille Model Alcoholic Hepatitis

> **Domain:** Gastroenterology, Hepatology & Clinical Nutrition  
> **Reference Guidelines & Standards:** `AASLD & ACG Clinical Practice Guidelines`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Lille Model for Alcoholic Hepatitis
Calculates the Lille score at day 7 of corticosteroid therapy to identify
non-responders who should discontinue treatment.

Formula:
  logit = 3.19 - 0.101*age + 0.147*albumin_day0 + 0.165*evolution
          - 0.206*renal_insufficiency - 0.006*bilirubin_day0
          + 0.007*bilirubin_day7 - 0.009*bilirubin_evolution

  Where:
    evolution = bilirubin_day7 - bilirubin_day0
    bilirubin_evolution = bilirubin_day0 - bilirubin_day7
    renal_insufficiency = 1 if creatinine > 1.3 mg/dL, else 0

  Lille = 1 / (1 + exp(-logit))

Score range: 0-1

References:
  - Louvet A, et al. Hepatology 2007;45:1348-54.
  - Mathurin P, et al. Gastroenterology 2002;123:1736-44.

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calculate_lille()`**: Calculate the Lille Model score for alcoholic hepatitis.

Parameters:
    age: Patient age in years
    albumin_day0: Serum albumin at day 0 in g/dL
    bilirubin_day0: Serum bilirubin at day 0 in mg/dL
    bilirubin_day7: Serum bilirubin at day 7 in mg/dL
    creatinine: Serum creatinine in mg/dL

Returns:
    Dict with lille_score, logit, response category, survival estimates,
    and clinical recommendation.
- **`calculate_lille_from_dict()`**: Calculate Lille score from a dictionary of parameters.
- **`process_batch()`**: Process a CSV file of patients and write Lille scores.
- **`main()`** — calculates and validates main parameters.

---

## 📐 Mathematical Formulation & Logic

```text
  Calculates the Lille score at day 7 of corticosteroid therapy to identify
  Formula:
  Calculate the Lille Model score for alcoholic hepatitis.
  Lille score = 1 / (1 + e^(-logit))
  lille_score = 1.0 / (1.0 + math.exp(-logit))
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --input data.csv
```

### Parameter Reference
- `--interactive`: Launch guided terminal interactive wizard.
- `--input <path>`: Evaluate input from JSON or CSV specification.
- `--json`: Output deterministic structured results in JSON format.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Parameter / observation metric | Required |
| `v1` | Parameter / observation metric | Required |
| `v2` | Parameter / observation metric | Required |
| `v3` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t lille-model-alcoholic-hepatitis .
docker run -p 8000:8000 lille-model-alcoholic-hepatitis
```
