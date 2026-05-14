# backend/legacy_stats.py (refactored)
# Refactoring applied:
# 1. Replaced raw dict + try/except with Pydantic model (framework-correct validation)
# 2. Consistent error handling — all errors use HTTPException
# 3. Removed SQL injection vulnerability — parameterised logging only
# 4. Named constants replace magic numbers
# 5. Guard clauses flatten nested logic

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Named constants — business rules should be self-documenting
MISSION_RULES = {
    1: ("recon", 10),
    2: ("transport", 5),
}
MAX_SCORE = 100
HEAVY_PAYLOAD_THRESHOLD = 50
PAYLOAD_PENALTY_RATE = 0.1


# Pydantic model — FastAPI validates this automatically, returns 422 on bad input
class MissionRequest(BaseModel):
    type: int
    dist: float
    batt: float
    payload_weight: float = 0.0


def _compute_base_score(distance: float, battery: float, multiplier: float) -> float:
    """Calculate base mission score. Returns 0 if distance or battery is zero."""
    if distance <= 0 or battery <= 0:
        return 0
    return (distance * multiplier) / battery


def _cap_score(score: float) -> float:
    """Cap score at MAX_SCORE (100)."""
    return min(score, MAX_SCORE)


@router.post("/api/mission_stats")
def calc_stats(request: MissionRequest):
    """
    Calculate mission statistics and return a score.

    Mission types:
    - 1: Recon (multiplier 10)
    - 2: Transport (multiplier 5, heavy payload penalty applies if payload > 50)
    """
    # Guard clause — reject unknown mission types immediately
    mission = MISSION_RULES.get(request.type)
    if mission is None:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mission type: {request.type}. Valid types are 1 (recon) and 2 (transport).",
        )

    status, multiplier = mission
    score = _compute_base_score(request.dist, request.batt, multiplier)

    # Guard clause — only apply transport penalty if score is positive
    if (
        status == "transport"
        and request.payload_weight > HEAVY_PAYLOAD_THRESHOLD
        and score > 0
    ):
        score -= request.payload_weight * PAYLOAD_PENALTY_RATE

    score = _cap_score(score)

    # Structured logging — no raw SQL, no print statements
    logger.info(
        "Mission stats calculated: mission=%s score=%.2f dist=%.2f batt=%.2f",
        status,
        score,
        request.dist,
        request.batt,
    )

    return {
        "status": "success",
        "mission": status,
        "final_score": round(score, 2),
    }
