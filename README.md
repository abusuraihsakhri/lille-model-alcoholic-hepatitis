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
    age: Patient age in years (0-120)
    albumin_day0: Serum albumin at day 0 in g/dL (0-10)
    bilirubin_day0: Serum bilirubin at day 0 in mg/dL (0-100)
    bilirubin_day7: Serum bilirubin at day 7 in mg/dL (0-100)
    creatinine: Serum creatinine in mg/dL (0-30)

Returns:
    Dict with lille_score, logit, response category, survival estimates,
    and clinical recommendation.

Raises:
    ValueError: If any input is outside valid physiological range.

- **`calculate_lille_from_dict()`**: Calculate Lille score from a dictionary of parameters.
- **`process_batch()`**: Process a CSV file of patients and write Lille scores.
- **`main()`** — CLI entry point for all commands.

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

### Installation
```bash
pip install -r requirements.txt
```

### 1. Single Patient Calculation
```bash
python cli.py single --age 50 --albumin-day0 3.0 --bilirubin-day0 15.0 --bilirubin-day7 10.0 --creatinine 1.0
```

### 2. Batch Processing
```bash
python cli.py batch -i patients.csv -o results.csv
```

### 3. Audit Task Dispatch
```bash
python cli.py audit --task-id TASK-001 --target KEY-001 --primary 12.0 --secondary 4.0
```

### 4. Supervisory Chat Query
```bash
python cli.py chat "Explain the Lille model indications"
```

### 5. Verify Audit Integrity
```bash
python cli.py verify-audit
```

### Parameter Reference
- `single`: Calculate Lille score for a single patient
- `batch`: Batch process CSV file
- `audit`: Dispatch audit task across workers
- `chat`: Query the supervisory chat assistant
- `verify-audit`: Verify HMAC audit trail integrity

### Input Data Schema (Batch CSV)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `age` | Patient age in years | Required |
| `albumin_day0` | Serum albumin at day 0 (g/dL) | Required |
| `bilirubin_day0` | Serum bilirubin at day 0 (mg/dL) | Required |
| `bilirubin_day7` | Serum bilirubin at day 7 (mg/dL) | Required |
| `creatinine` | Serum creatinine (mg/dL) | Required |

Alternative column names supported: `albumin` (for `albumin_day0`), `bili_day0` (for `bilirubin_day0`), `bili_day7` (for `bilirubin_day7`).

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).
* **Input Validation:** All physiological parameters validated against safe ranges.

### Security Configuration

Set a custom audit secret key via environment variable:
```bash
export AUDIT_SECRET_KEY="your-secure-key-here"
```

If not set, a secure random key is generated for development/testing.

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

### Test Coverage

- **Core Formula Tests:** Verify Lille score calculation accuracy
- **Component Tests:** Validate derived variables (evolution, renal insufficiency)
- **Response Category Tests:** Confirm classification and survival estimates
- **Input Validation Tests:** Verify parameter range enforcement
- **Error Handling Tests:** Confirm graceful handling of invalid inputs
- **Batch Processing Tests:** Validate CSV processing with error recovery
- **Security Tests:** Verify PHI guard enforcement and audit integrity

---

## 🐳 Container Deployment

```bash
docker build -t lille-model-alcoholic-hepatitis .
docker run lille-model-alcoholic-hepatitis
```

Using Docker Compose:

```bash
docker-compose up
```

To run the API server:
```bash
docker run -p 8000:8000 lille-model-alcoholic-hepatitis python -m agents.api
```

---

## 📁 Project Structure

```
lille-model-alcoholic-hepatitis/
├── .github/workflows/ci.yml    # CI/CD pipeline
├── agents/                      # Multi-agent enterprise framework
│   ├── __init__.py
│   ├── api.py                  # FastAPI REST server
│   ├── base.py                 # Security, PHI guard, audit trail
│   ├── learning.py             # Bayesian calibration engine
│   ├── llm_factory.py          # LLM provider factory
│   ├── metrics.py              # Prometheus metrics
│   ├── models.py               # Pydantic schemas
│   ├── streamer.py             # WebSocket telemetry
│   ├── supervisor.py           # Orchestrator
│   └── workers.py              # Specialized domain workers
├── tests/                      # Test suite
│   ├── test_enrichment.py
│   └── test_lille_model_alcoholic_hepatitis.py
├── web/
│   └── index.html              # Operations console UI
├── cli.py                      # CLI entry point
├── lille_model.py              # Core Lille model implementation
├── enrichment.py               # Enrichment feature suite
├── simulator.py                # Stress testing simulator
├── benchmark_dataset.json      # Golden benchmark test suite
├── openapi_spec.json           # OpenAPI specification
├── sample.csv                  # Sample input data
├── Dockerfile                  # Container build
├── docker-compose.yml          # Container orchestration
├── requirements.txt            # Python dependencies
└── LICENSE                     # MIT License
```
