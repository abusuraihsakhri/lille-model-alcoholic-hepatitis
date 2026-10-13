"""API and signed audit regression tests."""
import pytest
from fastapi import HTTPException

from agents.api import LilleRequest, api_lille
from agents.base import AuditTrail


def test_lille_api_matches_published_example():
    payload = LilleRequest(
        age=50, albumin_day0=3.5, bilirubin_day0=200 / 17.104,
        bilirubin_day7=150 / 17.104, creatinine=1.0, pt_seconds=18
    )
    assert api_lille(payload)["lille_score"] == pytest.approx(0.0668, abs=0.0001)


def test_lille_api_rejects_missing_pt_and_inr():
    payload = LilleRequest(
        age=50, albumin_day0=3.5, bilirubin_day0=12,
        bilirubin_day7=10, creatinine=1.0
    )
    with pytest.raises(HTTPException) as err:
        api_lille(payload)
    assert err.value.status_code == 422


def test_audit_detects_modified_signature_and_payload_hash():
    audit = AuditTrail(secret_key="test-secret")
    audit.log("tester", "unit", "CALCULATE", {"status": "ok"})
    assert audit.verify_integrity()
    exported = audit.get_trail()
    exported[0]["event_type"] = "MODIFIED"
    assert audit.verify_integrity()  # Export cannot alter the original trail.
    audit.logs[0]["payload_hash"] = "00" * 32
    assert not audit.verify_integrity()
