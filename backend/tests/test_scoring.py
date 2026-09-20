import pytest

from app.services.scoring import classify_score, score_lead


@pytest.mark.parametrize(
    ("budget", "employees", "need", "expected_score", "expected_status"),
    [
        (5000, 100, "AI automation", 100, "Hot"),
        (2000, 20, "CRM integration", 50, "Warm"),
        (999, 4, "Website", 0, "Cold"),
        (1000, 5, "AI assistant", 45, "Warm"),
    ],
)
def test_scoring_rules(budget, employees, need, expected_score, expected_status):
    result = score_lead(budget, employees, need)
    assert result.score == expected_score
    assert result.status == expected_status
    assert len(result.reasons) == 3


@pytest.mark.parametrize(
    ("score", "expected_status"),
    [(0, "Cold"), (39, "Cold"), (40, "Warm"), (69, "Warm"), (70, "Hot"), (100, "Hot")],
)
def test_status_boundaries(score, expected_status):
    assert classify_score(score) == expected_status
