"""Clinical reference, validation and CLI regression tests for Lille model."""
import csv
import json
import math
import pytest

from lille_model import calculate_lille, calculate_lille_from_dict, process_batch, main


BASE = dict(age=50, albumin_day0=3.5, bilirubin_day0=200 / 17.104,
            bilirubin_day7=150 / 17.104, creatinine=1.0, pt_seconds=18)


def score(**changes):
    return calculate_lille(**(BASE | changes))


def test_published_worked_example():
    # Louvet 2007 R = 2.6372; Lille = exp(-R)/(1+exp(-R)).
    result = score()
    assert result["linear_predictor"] == pytest.approx(2.6372, abs=1e-5)
    assert result["lille_score"] == pytest.approx(0.0668, abs=1e-4)
    assert result["response_category"] == "Responder"
    assert result["estimated_6m_survival_percent"] is None


def test_independent_formula_reference():
    p = dict(age=60, albumin_day0=2.3, bilirubin_day0=24.0,
             bilirubin_day7=28.0, creatinine=1.8, pt_seconds=24.0)
    r = (3.19 - 0.101*60 + 0.147*23
         + 0.0165*((24 - 28)*17.104) - 0.206
         - 0.0065*(24*17.104) - 0.0096*24)
    expected = 1 / (1 + math.exp(r))
    assert calculate_lille(**p)["lille_score"] == pytest.approx(expected, abs=0.00005)


def test_worsening_bilirubin_increases_lille():
    assert score(bilirubin_day7=30)["lille_score"] > score()["lille_score"]


def test_inr_variant():
    p = {k: v for k, v in BASE.items() if k != "pt_seconds"}
    p["inr"] = 2.0
    result = calculate_lille(**p)
    assert 0 < result["lille_score"] < 1
    assert result["components"]["coagulation_method"] == "INR"


def test_renal_boundary():
    assert score(creatinine=1.3)["components"]["renal_insufficiency"] == 0
    assert score(creatinine=1.3001)["components"]["renal_insufficiency"] == 1


@pytest.mark.parametrize("changes,pattern", [
    ({"age": -1}, "Age"),
    ({"albumin_day0": -1}, "Albumin"),
    ({"bilirubin_day0": -1}, "Bilirubin day 0"),
    ({"bilirubin_day7": float("nan")}, "Bilirubin day 7"),
    ({"creatinine": float("inf")}, "Creatinine"),
    ({"pt_seconds": None}, "exactly one"),
    ({"pt_seconds": 18, "inr": 2}, "exactly one"),
    ({"pt_seconds": float("nan")}, "PT"),
    ({"pt_seconds": 0}, "PT"),
    ({"age": True}, "Age"),
])
def test_invalid_inputs(changes, pattern):
    with pytest.raises(ValueError, match=pattern):
        score(**changes)


def test_missing_dictionary_input_is_rejected():
    with pytest.raises(ValueError, match="Missing required value"):
        calculate_lille_from_dict({"age": "50", "creatinine": "1.0", "pt_seconds": "18"})


def test_zero_values_do_not_fall_back_to_defaults():
    p = BASE | {"bilirubin_day7": 0}
    assert calculate_lille_from_dict(p)["components"]["bilirubin_day7"] == 0


def test_dictionary_aliases():
    result = calculate_lille_from_dict({
        "age": "50", "albumin": "3.5", "bili_day0": "12",
        "bili_day7": "10", "creatinine": "1", "inr": "1.6"
    })
    assert 0 < result["lille_score"] < 1


def test_csv_skips_invalid_without_inventing_data(tmp_path, capsys):
    source = tmp_path / "source.csv"
    output = tmp_path / "results.csv"
    source.write_text(
        "id,age,albumin_day0,bilirubin_day0,bilirubin_day7,creatinine,pt_seconds\\n"
        "good,50,3.5,12,10,1,18\\n"
        "bad,50,3.5,12,,1,18\\n", encoding="utf8")
    assert process_batch(str(source), str(output)) == 1
    with output.open(encoding="utf8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 1 and rows[0]["id"] == "good"
    assert "Row 2" in capsys.readouterr().err


def test_csv_missing_coagulation_rejected(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text(
        "age,albumin_day0,bilirubin_day0,bilirubin_day7,creatinine\\n"
        "50,3.5,12,10,1\\n", encoding="utf8")
    with pytest.raises(ValueError, match="pt_seconds or inr"):
        process_batch(str(source), str(tmp_path / "results.csv"))


def test_cli_single_with_required_pt(capsys):
    assert main(["single", "--age", "50", "--albumin-day0", "3.5",
                 "--bilirubin-day0", "12", "--bilirubin-day7", "10",
                 "--creatinine", "1", "--pt-seconds", "18"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert "lille_score" in result


def test_cli_requires_coagulation():
    with pytest.raises(SystemExit):
        main(["single", "--age", "50", "--albumin-day0", "3.5",
              "--bilirubin-day0", "12", "--bilirubin-day7", "10",
              "--creatinine", "1"])


def test_classification_uses_unrounded_score():
    # A high score requires reassessment rather than a fabricated survival estimate.
    result = calculate_lille(age=60, albumin_day0=2.0, bilirubin_day0=30,
                             bilirubin_day7=35, creatinine=2.0, pt_seconds=24)
    assert result["lille_score"] >= 0.45
    assert result["response_category"] == "Non-responder"
    assert result["steroid_decision"] == "REASSESS"
