# Lille Model for Alcoholic Hepatitis

> **Day 7 Steroid Response Assessment**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg)

---

## Overview

The Lille Model calculates a score at day 7 of corticosteroid therapy to identify patients with alcoholic hepatitis who are responding to treatment. Non-responders (score ≥0.56) have poor prognosis and should be considered for alternative therapies.

**Score range: 0-1**

---

## Formula

```
logit = 3.19 - 0.101×age + 0.147×albumin_day0 + 0.165×evolution
        - 0.206×renal_insufficiency - 0.006×bilirubin_day0
        + 0.007×bilirubin_day7 - 0.009×bilirubin_evolution

Where:
  evolution = bilirubin_day7 - bilirubin_day0
  bilirubin_evolution = bilirubin_day0 - bilirubin_day7
  renal_insufficiency = 1 if creatinine > 1.3 mg/dL, else 0

Lille = 1 / (1 + e^(-logit))
```

## Interpretation

| Score | Response | Steroid Decision | 6-Month Survival |
|-------|----------|-----------------|-----------------|
| <0.45 | Complete Response | Continue steroids | ~91% |
| 0.45-0.56 | Partial Response | Reassess | ~60% |
| ≥0.56 | No Response | Stop steroids | ~25% |

---

## Quick Start

```bash
# Single patient
python lille_model.py single --age 50 --albumin-day0 3.0 --bilirubin-day0 15.0 --bilirubin-day7 8.0 --creatinine 1.0

# Non-responder
python lille_model.py single --age 60 --albumin-day0 2.0 --bilirubin-day0 20.0 --bilirubin-day7 25.0 --creatinine 2.0

# Batch processing
python lille_model.py batch -i patients.csv -o results.csv
```

## Python API

```python
from lille_model import calculate_lille

result = calculate_lille(
    age=50, albumin_day0=3.0,
    bilirubin_day0=15.0, bilirubin_day7=8.0,
    creatinine=1.0,
)

print(f"Lille Score: {result['lille_score']}")
print(f"Response: {result['response_category']}")
print(f"Steroid Decision: {result['steroid_decision']}")
print(f"6-Month Survival: {result['estimated_6m_survival_percent']}%")
```

## Tests

```bash
python -m pytest test_lille_model.py -v
```

## References

- Louvet A, et al. The Lille model: a new tool for therapeutic strategy in patients with severe alcoholic hepatitis treated with steroids. *Hepatology* 2007;45:1348-54.
- Mathurin P, et al. Corticosteroids improve short-term survival in patients with severe alcoholic hepatitis: meta-analysis of individual patient data. *Gastroenterology* 2002;123:1736-44.

## License

MIT License. See [LICENSE](LICENSE).
