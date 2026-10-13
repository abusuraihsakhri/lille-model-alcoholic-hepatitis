#!/usr/bin/env python3
"""Lille model for response after corticosteroid treatment in severe alcohol-associated hepatitis.

Based on Louvet et al., Hepatology (2007), DOI: 10.1002/hep.21607.
Calculation is performed locally. This score is not a standalone treatment decision.
Inputs: albumin in g/dL, bilirubin in mg/dL, creatinine in mg/dL and
either prothrombin time in seconds or INR (explicitly selected).
"""

import argparse
import csv
import json
import math
import sys
from typing import Dict, Any, Optional



def _validate_lille_inputs(age, albumin_day0, bilirubin_day0,
                           bilirubin_day7, creatinine, pt_seconds, inr):
    """Reject missing, non-finite, ambiguous and implausible measurements."""
    fields = (
        ("Age", age, 18, 120, "years"),
        ("Albumin", albumin_day0, 0.1, 10, "g/dL"),
        ("Bilirubin day 0", bilirubin_day0, 0, 100, "mg/dL"),
        ("Bilirubin day 7", bilirubin_day7, 0, 100, "mg/dL"),
        ("Creatinine", creatinine, 0.1, 30, "mg/dL"),
    )
    for label, value, low, high, units in fields:
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or not low <= value <= high):
            raise ValueError(f"{label} must be between {low} and {high} {units}; got {value!r}")
    if (pt_seconds is None) == (inr is None):
        raise ValueError("Provide exactly one of pt_seconds or inr")
    if pt_seconds is not None:
        if (isinstance(pt_seconds, bool) or not isinstance(pt_seconds, (int, float))
                or not math.isfinite(pt_seconds) or not 5 <= pt_seconds <= 120):
            raise ValueError("PT must be between 5 and 120 seconds")
    if inr is not None:
        if (isinstance(inr, bool) or not isinstance(inr, (int, float))
                or not math.isfinite(inr) or not 0.5 <= inr <= 15):
            raise ValueError("INR must be between 0.5 and 15")


def calculate_lille(
    age: int,
    albumin_day0: float,
    bilirubin_day0: float,
    bilirubin_day7: float,
    creatinine: float,
    pt_seconds: Optional[float] = None,
    inr: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate the validated Louvet Lille score (0 to 1).

    Bilirubin is converted from mg/dL to micromol/L (factor 17.104);
    albumin is converted from g/dL to g/L (factor 10).
    R = 3.19 - 0.101*age + 0.147*albumin_g_L
        + 0.0165*(bilirubin_day0 - bilirubin_day7)_micromol_L
        - 0.206*renal_insufficiency - 0.0065*bilirubin_day0_micromol_L
        - 0.0096*(PT_seconds OR INR)
    Lille = exp(-R) / (1 + exp(-R)).
    """
    _validate_lille_inputs(
        age, albumin_day0, bilirubin_day0, bilirubin_day7,
        creatinine, pt_seconds, inr
    )
    b0 = bilirubin_day0 * 17.104
    b7 = bilirubin_day7 * 17.104
    renal_insufficiency = int(creatinine > 1.3)
    coagulation = pt_seconds if pt_seconds is not None else inr
    r = (
        3.19 - 0.101 * age + 0.147 * (albumin_day0 * 10)
        + 0.0165 * (b0 - b7) - 0.206 * renal_insufficiency
        - 0.0065 * b0 - 0.0096 * coagulation
    )
    # Stable logistic evaluation; classify the unrounded score.
    if r >= 0:
        z = math.exp(-r)
        score = z / (1 + z)
    else:
        z = math.exp(r)
        score = 1 / (1 + z)

    nonresponder = score >= 0.45
    return {
        "tool": "lille-model",
        "lille_score": round(score, 4),
        "linear_predictor": round(r, 6),
        "logit": round(-r, 6),
        "response_category": "Non-responder" if nonresponder else "Responder",
        "steroid_decision": "REASSESS" if nonresponder else "CONSIDER_CONTINUATION",
        "recommendation": (
            "Lille >= 0.45: treatment nonresponse; promptly review corticosteroid "
            "discontinuation with the treating clinical team."
            if nonresponder else
            "Lille < 0.45: response is more likely; review continued treatment "
            "with the treating clinical team."
        ),
        "estimated_6m_survival_percent": None,
        "components": {
            "age": age,
            "albumin_day0": albumin_day0,
            "bilirubin_day0": bilirubin_day0,
            "bilirubin_day7": bilirubin_day7,
            "creatinine": creatinine,
            "pt_seconds": pt_seconds,
            "inr": inr,
            "coagulation_method": "PT" if pt_seconds is not None else "INR",
            "evolution": round(bilirubin_day7 - bilirubin_day0, 4),
            "bilirubin_evolution": round(bilirubin_day0 - bilirubin_day7, 4),
            "renal_insufficiency": renal_insufficiency,
        },
    }


def calculate_lille_from_dict(params: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate using named fields, with no fabricated default lab values."""
    def required(*names):
        for name in names:
            value = params.get(name)
            if value is not None and str(value).strip() != "":
                try:
                    return float(value)
                except (ValueError, TypeError) as exc:
                    raise ValueError(f"Invalid value for {name}: {value!r}") from exc
        raise ValueError(f"Missing required value: {names[0]}")

    pt_value = params.get("pt_seconds", params.get("pt_sec"))
    inr_value = params.get("inr")
    pt_seconds = None if pt_value is None or str(pt_value).strip() == "" else required("pt_seconds", "pt_sec")
    inr = None if inr_value is None or str(inr_value).strip() == "" else required("inr")
    return calculate_lille(
        age=required("age"),
        albumin_day0=required("albumin_day0", "albumin"),
        bilirubin_day0=required("bilirubin_day0", "bili_day0"),
        bilirubin_day7=required("bilirubin_day7", "bili_day7"),
        creatinine=required("creatinine"),
        pt_seconds=pt_seconds,
        inr=inr,
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

        if not ({"pt_seconds", "pt_sec", "inr"} & available_cols):
            raise ValueError("Missing required column: pt_seconds or inr")
        rows = list(reader)

    out_fields = list(dict.fromkeys(fieldnames + [
        "lille_score", "response_category", "steroid_decision",
        "estimated_6m_survival_percent", "recommendation",
    ]))
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

    coag = p_single.add_mutually_exclusive_group(required=True)
    coag.add_argument("--pt-seconds", type=float, help="Prothrombin time (seconds)")
    coag.add_argument("--inr", type=float, help="INR alternative from Louvet 2007")

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
            pt_seconds=args.pt_seconds,
            inr=args.inr,
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
