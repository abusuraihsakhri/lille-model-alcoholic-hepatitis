#!/usr/bin/env python3
"""
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
"""

import argparse
import csv
import json
import math
import sys
from typing import Dict, Any, Optional


def calculate_lille(
    age: int,
    albumin_day0: float,
    bilirubin_day0: float,
    bilirubin_day7: float,
    creatinine: float,
) -> Dict[str, Any]:
    """
    Calculate the Lille Model score for alcoholic hepatitis.

    Parameters:
        age: Patient age in years
        albumin_day0: Serum albumin at day 0 in g/dL
        bilirubin_day0: Serum bilirubin at day 0 in mg/dL
        bilirubin_day7: Serum bilirubin at day 7 in mg/dL
        creatinine: Serum creatinine in mg/dL

    Returns:
        Dict with lille_score, logit, response category, survival estimates,
        and clinical recommendation.
    """
    # Derived variables
    evolution = bilirubin_day7 - bilirubin_day0
    bilirubin_evolution = bilirubin_day0 - bilirubin_day7
    renal_insufficiency = 1 if creatinine > 1.3 else 0

    # Logit calculation (Louvet et al. 2007)
    logit = (
        3.19
        - 0.101 * age
        + 0.147 * albumin_day0
        + 0.165 * evolution
        - 0.206 * renal_insufficiency
        - 0.006 * bilirubin_day0
        + 0.007 * bilirubin_day7
        - 0.009 * bilirubin_evolution
    )

    # Lille score = 1 / (1 + e^(-logit))
    lille_score = 1.0 / (1.0 + math.exp(-logit))
    lille_score = round(lille_score, 4)

    # Response classification
    if lille_score < 0.45:
        response = "Complete Response"
        recommendation = "Continue corticosteroid therapy. Good prognosis."
        steroid_decision = "CONTINUE"
    elif lille_score <= 0.56:
        response = "Partial Response"
        recommendation = "Consider continuing steroids with close monitoring. Intermediate prognosis."
        steroid_decision = "REASSESS"
    else:
        response = "No Response"
        recommendation = "Consider stopping corticosteroids. Poor prognosis. Evaluate for alternative therapies or palliative care."
        steroid_decision = "STOP"

    # 6-month survival estimates (Louvet et al. 2007)
    if lille_score < 0.45:
        survival_6m = 91.0  # ~91% for complete responders
    elif lille_score <= 0.56:
        survival_6m = 60.0  # ~60% for partial responders
    else:
        survival_6m = 25.0  # ~25% for non-responders

    return {
        "tool": "lille-model",
        "lille_score": lille_score,
        "logit": round(logit, 4),
        "response_category": response,
        "steroid_decision": steroid_decision,
        "recommendation": recommendation,
        "estimated_6m_survival_percent": survival_6m,
        "components": {
            "age": age,
            "albumin_day0": albumin_day0,
            "bilirubin_day0": bilirubin_day0,
            "bilirubin_day7": bilirubin_day7,
            "creatinine": creatinine,
            "evolution": round(evolution, 4),
            "bilirubin_evolution": round(bilirubin_evolution, 4),
            "renal_insufficiency": renal_insufficiency,
        },
    }


def calculate_lille_from_dict(params: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate Lille score from a dictionary of parameters."""
    return calculate_lille(
        age=int(float(params.get("age", 50))),
        albumin_day0=float(params.get("albumin_day0") or params.get("albumin", 3.0)),
        bilirubin_day0=float(params.get("bilirubin_day0") or params.get("bili_day0", 10.0)),
        bilirubin_day7=float(params.get("bilirubin_day7") or params.get("bili_day7", 10.0)),
        creatinine=float(params.get("creatinine", 1.0)),
    )


def process_batch(input_csv: str, output_csv: str) -> int:
    """Process a CSV file of patients and write Lille scores."""
    with open(input_csv, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    out_fields = fieldnames + [
        "lille_score", "response_category", "steroid_decision",
        "estimated_6m_survival_percent", "recommendation",
    ]
    out_rows = []
    for r in rows:
        result = calculate_lille_from_dict(r)
        row_dict = dict(r)
        row_dict["lille_score"] = result["lille_score"]
        row_dict["response_category"] = result["response_category"]
        row_dict["steroid_decision"] = result["steroid_decision"]
        row_dict["estimated_6m_survival_percent"] = result["estimated_6m_survival_percent"]
        row_dict["recommendation"] = result["recommendation"]
        out_rows.append(row_dict)

    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Processed {len(out_rows)} records -> {output_csv}")
    return len(out_rows)


# =============================================================================
# CLI
# =============================================================================

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="lille-model",
        description="Lille Model for Alcoholic Hepatitis - Day 7 steroid response assessment",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Single calculation
    p_single = subparsers.add_parser("single", help="Calculate Lille score for a single patient")
    p_single.add_argument("--age", type=int, required=True, help="Patient age in years")
    p_single.add_argument("--albumin-day0", type=float, required=True,
                          help="Serum albumin at day 0 (g/dL)")
    p_single.add_argument("--bilirubin-day0", type=float, required=True,
                          help="Serum bilirubin at day 0 (mg/dL)")
    p_single.add_argument("--bilirubin-day7", type=float, required=True,
                          help="Serum bilirubin at day 7 (mg/dL)")
    p_single.add_argument("--creatinine", type=float, required=True,
                          help="Serum creatinine (mg/dL)")

    # Batch processing
    p_batch = subparsers.add_parser("batch", help="Batch process CSV file")
    p_batch.add_argument("-i", "--input", required=True, help="Input CSV file")
    p_batch.add_argument("-o", "--output", default="results.csv", help="Output CSV file")

    args = parser.parse_args(argv)

    if args.command == "single":
        result = calculate_lille(
            age=args.age,
            albumin_day0=args.albumin_day0,
            bilirubin_day0=args.bilirubin_day0,
            bilirubin_day7=args.bilirubin_day7,
            creatinine=args.creatinine,
        )
        print(json.dumps(result, indent=2))

    elif args.command == "batch":
        process_batch(args.input, args.output)

    return 0


if __name__ == "__main__":
    main()
