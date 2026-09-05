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


def _validate_lille_inputs(age: int, albumin_day0: float, bilirubin_day0: float,
                           bilirubin_day7: float, creatinine: float) -> None:
    """Validate input parameters for Lille score calculation."""
    if not isinstance(age, (int, float)) or age < 0 or age > 120:
        raise ValueError(f"Age must be between 0 and 120, got {age}")
    if not isinstance(albumin_day0, (int, float)) or albumin_day0 < 0 or albumin_day0 > 10:
        raise ValueError(f"Albumin must be between 0 and 10 g/dL, got {albumin_day0}")
    if not isinstance(bilirubin_day0, (int, float)) or bilirubin_day0 < 0 or bilirubin_day0 > 100:
        raise ValueError(f"Bilirubin day 0 must be between 0 and 100 mg/dL, got {bilirubin_day0}")
    if not isinstance(bilirubin_day7, (int, float)) or bilirubin_day7 < 0 or bilirubin_day7 > 100:
        raise ValueError(f"Bilirubin day 7 must be between 0 and 100 mg/dL, got {bilirubin_day7}")
    if not isinstance(creatinine, (int, float)) or creatinine < 0 or creatinine > 30:
        raise ValueError(f"Creatinine must be between 0 and 30 mg/dL, got {creatinine}")


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

    Raises:
        ValueError: If any input parameter is outside valid physiological range.
    """
    # Validate inputs
    _validate_lille_inputs(age, albumin_day0, bilirubin_day0, bilirubin_day7, creatinine)

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
    """
    Process a CSV file of patients and write Lille scores.

    Args:
        input_csv: Path to input CSV file with required columns:
                  age, albumin_day0, bilirubin_day0, bilirubin_day7, creatinine
        output_csv: Path to output CSV file

    Returns:
        Number of records processed

    Raises:
        FileNotFoundError: If input file does not exist
        ValueError: If required columns are missing
    """
    import os
    if not os.path.isfile(input_csv):
        raise FileNotFoundError(f"Input file not found: {input_csv}")

    with open(input_csv, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])

        # Validate required columns exist
        required_cols = {"age", "albumin_day0", "bilirubin_day0", "bilirubin_day7", "creatinine"}
        available_cols = set(fieldnames)
        missing = required_cols - available_cols
        if missing:
            # Try alternative column names
            alt_map = {
                "albumin_day0": "albumin",
                "bilirubin_day0": "bili_day0",
                "bilirubin_day7": "bili_day7",
            }
            still_missing = set()
            for col in missing:
                if col in alt_map and alt_map[col] in available_cols:
                    continue
                still_missing.add(col)
            if still_missing:
                raise ValueError(f"Missing required columns: {still_missing}. "
                                 f"Available columns: {fieldnames}")

        rows = list(reader)

    out_fields = fieldnames + [
        "lille_score", "response_category", "steroid_decision",
        "estimated_6m_survival_percent", "recommendation",
    ]
    out_rows = []
    errors = []
    for idx, r in enumerate(rows):
        try:
            result = calculate_lille_from_dict(r)
            row_dict = dict(r)
            row_dict["lille_score"] = result["lille_score"]
            row_dict["response_category"] = result["response_category"]
            row_dict["steroid_decision"] = result["steroid_decision"]
            row_dict["estimated_6m_survival_percent"] = result["estimated_6m_survival_percent"]
            row_dict["recommendation"] = result["recommendation"]
            out_rows.append(row_dict)
        except (ValueError, TypeError, KeyError) as e:
            errors.append(f"Row {idx + 1}: {e}")

    if errors:
        print(f"Warnings: {len(errors)} rows had errors:", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)

    # Ensure output directory exists
    out_dir = os.path.dirname(output_csv)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Processed {len(out_rows)} records -> {output_csv}")
    if errors:
        print(f"({len(errors)} rows skipped due to errors)")
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

    # Audit dispatch
    p_audit = subparsers.add_parser("audit", help="Dispatch audit task across workers")
    p_audit.add_argument("--task-id", required=True, help="Task identifier")
    p_audit.add_argument("--target", default="KEY-CLI-01", help="Target identifier")
    p_audit.add_argument("--primary", type=float, default=10.0, help="Primary metric")
    p_audit.add_argument("--secondary", type=float, default=2.0, help="Secondary metric")
    p_audit.add_argument("--status", default="NOMINAL", help="Status descriptor")

    # Chat query
    p_chat = subparsers.add_parser("chat", help="Query the supervisory chat assistant")
    p_chat.add_argument("query", nargs="+", help="Query text")

    # Verify audit integrity
    p_verify = subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

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

    elif args.command == "audit":
        from agents.models import SystemTaskPayload
        from agents.supervisor import SystemSupervisor
        supervisor = SystemSupervisor(model_provider="mock")
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.status,
        )
        dossier = supervisor.process_task(payload)
        print(json.dumps(dossier.to_dict(), indent=2, default=str))

    elif args.command == "chat":
        from agents.supervisor import SystemSupervisor
        supervisor = SystemSupervisor(model_provider="mock")
        query = " ".join(args.query)
        response = supervisor.query_supervisory_chat(query)
        print(json.dumps({"response": response}, indent=2))

    elif args.command == "verify-audit":
        from agents.base import AuditLogger
        valid = AuditLogger.verify_integrity()
        trail = AuditLogger.get_trail()
        print(json.dumps({"integrity_valid": valid, "blocks_count": len(trail)}, indent=2))

    return 0


if __name__ == "__main__":
    main()
