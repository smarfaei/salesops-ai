from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreResult:
    score: int
    status: str
    reasons: list[str]


def classify_score(score: int) -> str:
    if score >= 70:
        return "Hot"
    if score >= 40:
        return "Warm"
    return "Cold"


def score_lead(budget: int, employees: int, need: str) -> ScoreResult:
    """Apply the single authoritative Phase 1 lead-scoring policy."""
    score = 0
    reasons: list[str] = []

    if budget >= 5000:
        score += 50
        reasons.append("High budget: +50")
    elif budget >= 2000:
        score += 30
        reasons.append("Medium budget: +30")
    elif budget >= 1000:
        score += 15
        reasons.append("Qualified budget: +15")
    else:
        reasons.append("Budget below scoring threshold: +0")

    if employees >= 100:
        score += 30
        reasons.append("Large company: +30")
    elif employees >= 20:
        score += 20
        reasons.append("Growing company: +20")
    elif employees >= 5:
        score += 10
        reasons.append("Small company: +10")
    else:
        reasons.append("Company size below scoring threshold: +0")

    if "AI" in need.upper():
        score += 20
        reasons.append("AI requirement detected: +20")
    else:
        reasons.append("No AI requirement detected: +0")

    return ScoreResult(score=score, status=classify_score(score), reasons=reasons)
