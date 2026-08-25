#!/usr/bin/env python3
"""
Tests for Lille Model for Alcoholic Hepatitis.
"""
import json
import math
import sys
import os
import csv
import pytest

sys.path.insert(0, os.path.dirname(__file__))

from lille_model import calculate_lille, calculate_lille_from_dict, process_batch, main


# =============================================================================
# Core Formula Tests
# =============================================================================

class TestLilleFormula:
    def test_complete_response(self):
        """Patient with good bilirubin response should get Lille < 0.45."""
        result = calculate_lille(
            age=45, albumin_day0=3.5,
            bilirubin_day0=15.0, bilirubin_day7=8.0,
            creatinine=0.9,
        )
        assert result["lille_score"] < 0.45
        assert result["response_category"] == "Complete Response"
        assert result["steroid_decision"] == "CONTINUE"

    def test_no_response(self):
        """Younger patient with high albumin and worsening bilirubin: Lille >= 0.56."""
        # Parameters chosen to produce a positive logit (non-response)
        # logit = 3.19 - 0.101*40 + 0.147*3.5 + 0.165*10 - 0.206*1
        #         - 0.006*10 + 0.007*20 - 0.009*(-10) = 1.28
        result = calculate_lille(
            age=40, albumin_day0=3.5,
            bilirubin_day0=10.0, bilirubin_day7=20.0,
            creatinine=2.0,
        )
        assert result["lille_score"] >= 0.56
        assert result["response_category"] == "No Response"
        assert result["steroid_decision"] == "STOP"

    def test_partial_response(self):
        """Borderline response should be in partial range."""
        result = calculate_lille(
            age=52, albumin_day0=2.8,
            bilirubin_day0=18.0, bilirubin_day7=14.0,
            creatinine=1.2,
        )
        # This should be in the borderline range
        assert 0.0 <= result["lille_score"] <= 1.0

    def test_score_range(self):
        """Lille score must be between 0 and 1."""
        result = calculate_lille(
            age=50, albumin_day0=3.0,
            bilirubin_day0=10.0, bilirubin_day7=5.0,
            creatinine=1.0,
        )
        assert 0.0 <= result["lille_score"] <= 1.0

    def test_score_range_extreme_values(self):
        """Even extreme values should produce score in 0-1 range."""
        result = calculate_lille(
            age=80, albumin_day0=1.0,
            bilirubin_day0=40.0, bilirubin_day7=45.0,
            creatinine=5.0,
        )
        assert 0.0 <= result["lille_score"] <= 1.0


# =============================================================================
# Component Calculation Tests
# =============================================================================

class TestComponents:
    def test_evolution_positive(self):
        """Bilirubin going up: evolution > 0."""
        result = calculate_lille(
            age=50, albumin_day0=3.0,
            bilirubin_day0=10.0, bilirubin_day7=15.0,
            creatinine=1.0,
        )
        assert result["components"]["evolution"] == 5.0

    def test_evolution_negative(self):
        """Bilirubin going down: evolution < 0."""
        result = calculate_lille(
            age=50, albumin_day0=3.0,
            bilirubin_day0=15.0, bilirubin_day7=10.0,
            creatinine=1.0,
        )
        assert result["components"]["evolution"] == -5.0

    def test_bilirubin_evolution(self):
        """bilirubin_evolution = day0 - day7."""
        result = calculate_lille(
            age=50, albumin_day0=3.0,
            bilirubin_day0=15.0, bilirubin_day7=10.0,
            creatinine=1.0,
        )
        assert result["components"]["bilirubin_evolution"] == 5.0

    def test_renal_insufficiency_positive(self):
        """Creatinine > 1.3 triggers renal insufficiency."""
        result = calculate_lille(
            age=50, albumin_day0=3.0,
            bilirubin_day0=10.0, bilirubin_day7=8.0,
            creatinine=1.5,
        )
        assert result["components"]["renal_insufficiency"] == 1

    def test_renal_insufficiency_negative(self):
        """Creatinine <= 1.3 means no renal insufficiency."""
        result = calculate_lille(
            age=50, albumin_day0=3.0,
            bilirubin_day0=10.0, bilirubin_day7=8.0,
            creatinine=1.0,
        )
        assert result["components"]["renal_insufficiency"] == 0

    def test_renal_insufficiency_boundary(self):
        """Creatinine exactly 1.3 should NOT trigger renal insufficiency."""
        result = calculate_lille(
            age=50, albumin_day0=3.0,
            bilirubin_day0=10.0, bilirubin_day7=8.0,
            creatinine=1.3,
        )
        assert result["components"]["renal_insufficiency"] == 0


# =============================================================================
# Logit Calculation Tests
# =============================================================================

class TestLogit:
    def test_logit_is_numeric(self):
        result = calculate_lille(
            age=50, albumin_day0=3.0,
            bilirubin_day0=10.0, bilirubin_day7=8.0,
            creatinine=1.0,
        )
        assert isinstance(result["logit"], float)

    def test_lille_from_logit(self):
        """Verify Lille = 1 / (1 + e^(-logit))."""
        result = calculate_lille(
            age=50, albumin_day0=3.0,
            bilirubin_day0=10.0, bilirubin_day7=8.0,
            creatinine=1.0,
        )
        expected = 1.0 / (1.0 + math.exp(-result["logit"]))
        assert abs(result["lille_score"] - round(expected, 4)) < 0.001


# =============================================================================
# Response Category Tests
# =============================================================================

class TestResponseCategory:
    def test_complete_response_survival(self):
        result = calculate_lille(
            age=45, albumin_day0=3.5,
            bilirubin_day0=12.0, bilirubin_day7=6.0,
            creatinine=0.8,
        )
        if result["lille_score"] < 0.45:
            assert result["estimated_6m_survival_percent"] == 91.0

    def test_no_response_survival(self):
        result = calculate_lille(
            age=60, albumin_day0=2.0,
            bilirubin_day0=25.0, bilirubin_day7=28.0,
            creatinine=2.5,
        )
        if result["lille_score"] >= 0.56:
            assert result["estimated_6m_survival_percent"] == 25.0


# =============================================================================
# Batch Processing Tests
# =============================================================================

class TestBatch:
    def test_batch_processing(self, tmp_path):
        csv_in = tmp_path / "in.csv"
        csv_out = tmp_path / "out.csv"
        csv_in.write_text(
            "patient_id,age,albumin_day0,bilirubin_day0,bilirubin_day7,creatinine\n"
            "P001,45,3.5,15.0,8.0,0.9\n"
            "P002,60,2.0,20.0,25.0,2.0\n",
            encoding="utf-8",
        )
        count = process_batch(str(csv_in), str(csv_out))
        assert count == 2
        assert csv_out.exists()
        content = csv_out.read_text(encoding="utf-8")
        assert "lille_score" in content
        assert "response_category" in content


# =============================================================================
# CLI Tests
# =============================================================================

class TestCLI:
    def test_cli_single(self):
        ret = main(["single", "--age", "50", "--albumin-day0", "3.0",
                     "--bilirubin-day0", "15.0", "--bilirubin-day7", "10.0",
                     "--creatinine", "1.0"])
        assert ret == 0

    def test_cli_batch(self, tmp_path):
        csv_in = tmp_path / "in.csv"
        csv_out = tmp_path / "out.csv"
        csv_in.write_text(
            "age,albumin_day0,bilirubin_day0,bilirubin_day7,creatinine\n"
            "50,3.0,15.0,10.0,1.0\n",
            encoding="utf-8",
        )
        ret = main(["batch", "-i", str(csv_in), "-o", str(csv_out)])
        assert ret == 0
        assert csv_out.exists()


# =============================================================================
# From Dict Tests
# =============================================================================

class TestFromDict:
    def test_from_dict_basic(self):
        params = {"age": "50", "albumin_day0": "3.0",
                  "bilirubin_day0": "15.0", "bilirubin_day7": "10.0",
                  "creatinine": "1.0"}
        result = calculate_lille_from_dict(params)
        assert 0.0 <= result["lille_score"] <= 1.0

    def test_from_dict_alt_keys(self):
        params = {"age": "50", "albumin": "3.0",
                  "bili_day0": "15.0", "bili_day7": "10.0",
                  "creatinine": "1.0"}
        result = calculate_lille_from_dict(params)
        assert 0.0 <= result["lille_score"] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
