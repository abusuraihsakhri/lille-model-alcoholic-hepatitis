# Lille Model for Alcohol-Associated Hepatitis

A day-7 Lille score calculator for assessing corticosteroid response in **severe alcohol-associated hepatitis**. The browser calculator runs entirely client-side; a Python CLI and FastAPI endpoint are also available.

> **Clinical caution:** This is a research and educational implementation, not a medical device or an autonomous treatment recommendation. Verify inputs and discuss treatment decisions with the treating clinical team.

## Features

- Louvet et al. (2007) Lille score, range 0–1, with **nonresponse threshold ≥ 0.45**.
- Day-0 albumin, day-0/day-7 bilirubin, age, creatinine, and **explicit PT (seconds) or INR**.
- Correct conversion of albumin **g/dL → g/L** and bilirubin **mg/dL → µmol/L**.
- Single-patient browser calculation, Python CLI and batch CSV processing.
- JSON API via FastAPI at `POST /api/lille` plus separate experimental audit/demo endpoints.
- Published-reference and edge-case regression tests, CI and static Pages deployment workflow.

## Browser use

Open `web/index.html` directly or serve the repository with `python -m http.server 8080` and visit `http://localhost:8080/`. Enter all six required inputs, choose PT or INR, then select **Calculate Lille score**. The **Use example** button loads an illustrative case.

The browser does **not** transmit inputs or store them in cookies/local storage. Avoid patient identifiers. The API server, if used, is a separate deployment and does not provide authentication or regulated PHI handling.

## Formula

For albumin in **g/L** and bilirubin in **µmol/L**, the original linear predictor is:

```text
R = 3.19 - 0.101*age + 0.147*albumin_day0
    + 0.0165*(bilirubin_day0 - bilirubin_day7)
    - 0.206*renal_insufficiency - 0.0065*bilirubin_day0
    - 0.0096*PT_seconds

Lille = exp(-R) / (1 + exp(-R))
```

The published INR alternative substitutes INR for PT in the last term. Renal insufficiency was defined in the original model by creatinine >1.3 mg/dL **or** creatinine clearance <40 mL/min. This implementation uses **serum creatinine only** and does not accept a measured creatinine clearance. Interpret this limitation clinically.

Reference: Louvet A, et al. *The Lille model: A new tool for therapeutic strategy in patients with severe alcoholic hepatitis treated with steroids.* Hepatology. 2007;45:1348–1354. [doi:10.1002/hep.21607](https://doi.org/10.1002/hep.21607).

## Python and batch usage

Python **3.10–3.12** with dependencies from `requirements.txt`:

```bash
python -m pip install -r requirements.txt
python cli.py single --age 50 --albumin-day0 3.5 --bilirubin-day0 11.6932 --bilirubin-day7 8.7699 --creatinine 1.0 --pt-seconds 18
python cli.py batch -i sample.csv -o results.csv
python -m pytest -q
```

Use `--inr 2.0` **instead of** `--pt-seconds` when appropriate. CSV needs columns `age,albumin_day0,bilirubin_day0,bilirubin_day7,creatinine` plus `pt_seconds` (or `pt_sec` or `inr`). Aliases `albumin`, `bili_day0` and `bili_day7` are also supported. Rows with invalid/missing measurements are skipped with reported warnings; no laboratory values are imputed. Output may contain sensitive input columns if you provide them; manage CSV files accordingly.

## API / Docker

```bash
uvicorn agents.api:app --host 127.0.0.1 --port 8000
# Documentation: http://127.0.0.1:8000/docs
```

Example POST body for `/api/lille`:

```json
{
  "age": 50,
  "albumin_day0": 3.5,
  "bilirubin_day0": 11.6932,
  "bilirubin_day7": 8.7699,
  "creatinine": 1.0,
  "pt_seconds": 18
}
```

The Docker image launches the API on port 8000. For Compose, set a **unique** `AUDIT_SECRET_KEY` through your environment before `docker compose up --build`. The optional audit/demo subsystem stores audit events **in process memory**; its regex-based identifier screening is not a guarantee of PHI de-identification or HIPAA compliance. Never expose this unauthenticated API to the public with real patient data.

## Technical notes

- Browser: static HTML, CSS and JavaScript; no backend or Pyodide required. Compatible with current evergreen desktop/mobile browsers.
- Backend: Python, FastAPI and Pydantic. Auxiliary experimental agent/audit modules remain available through the CLI and API.
- CI checks Python 3.10, 3.11 and 3.12, reference calculations, browser JavaScript and signature integrity.
- No personalized six-month survival estimate is returned: the categorical survival figures used previously were not a validated individual prediction.

## License

[MIT](LICENSE).
