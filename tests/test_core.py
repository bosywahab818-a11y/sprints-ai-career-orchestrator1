
import sqlite3

from src.tools.database import (
    DB_PATH,
    get_learner_profile,
    get_demo_openings
)
from src.agents.career import (
    CareerApprovalDecision,
    find_eligible_jobs,
    verify_career_match
)
from src.orchestrator import orchestrator_router


def test_database_integrity():
    with sqlite3.connect(DB_PATH) as conn:
        result = conn.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

    assert result == "ok"


def test_learner_dataset():
    with sqlite3.connect(DB_PATH) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM learners"
        ).fetchone()[0]

    assert count >= 25


def test_demo_jobs():
    jobs = get_demo_openings()

    assert len(jobs) >= 4
    assert all(
        job["source_type"] == "synthetic"
        for job in jobs
    )


def test_learner_profile():
    learner = get_learner_profile("SPR-1001")

    assert learner is not None
    assert learner["learner_id"] == "SPR-1001"


def test_career_matching():
    matches = find_eligible_jobs("SPR-1001")

    assert matches

    for match in matches:
        assert match["eligible"] is True


def test_career_match_verification():
    match = verify_career_match(
        "SPR-1001",
        "JOB-001"
    )

    assert match["eligible"] is True
    assert match["source_type"] == "synthetic"


def test_router_advisor():
    assert orchestrator_router(
        {"task_type": "advisor"}
    ) == "advisor"


def test_router_assessor():
    assert orchestrator_router(
        {"task_type": "assessor"}
    ) == "assessor"


def test_router_career():
    assert orchestrator_router(
        {"task_type": "career"}
    ) == "career"


def test_router_invalid():
    assert orchestrator_router(
        {"task_type": "unknown"}
    ) == "invalid"


def test_approval_schema_valid():
    decision = CareerApprovalDecision(
        learner_id="SPR-1001",
        job_id="JOB-001",
        approved=True,
        reviewer_id="REVIEWER-001",
        note="Approved for test."
    )

    assert decision.approved is True


def test_approval_schema_missing_reviewer():
    from pydantic import ValidationError
    import pytest

    with pytest.raises(ValidationError):
        CareerApprovalDecision(
            learner_id="SPR-1001",
            job_id="JOB-001",
            approved=True
        )
