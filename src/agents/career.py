from src.tools.database import DB_PATH, get_learner_profile, get_demo_openings
from src.state import OrchestratorState
"""Staged source definitions; not yet standalone."""
from typing import TypedDict
from pydantic import BaseModel, ConfigDict, Field
from langgraph.types import interrupt
import sqlite3


# From notebook cell 122
class CareerState(TypedDict, total=False):
    learner_id: str
    matches: list[dict]
    selected_match: dict
    approval_status: str
    reviewer_note: str

# From notebook cell 164
class CareerApprovalDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    learner_id: str = Field(min_length=1)
    job_id: str = Field(min_length=1)
    approved: bool
    reviewer_id: str = Field(min_length=1)
    note: str = Field(default="", max_length=1000)

# From notebook cell 118
def find_eligible_jobs(learner_id: str) -> list[dict]:
    """
    Return eligible demonstration jobs for one learner.
    """

    learner = get_learner_profile(learner_id)

    if learner is None:
        raise ValueError(
            f"Learner {learner_id} not found."
        )

    jobs = get_demo_openings()

    matches = [
        evaluate_job_match(learner, job)
        for job in jobs
    ]

    eligible_matches = [
        match
        for match in matches
        if match["eligible"]
    ]

    return sorted(
        eligible_matches,
        key=lambda match: match["match_score"],
        reverse=True
    )

# From notebook cell 116
def evaluate_job_match(learner: dict, job: dict) -> dict:
    """
    Evaluate learner eligibility against a database job record.

    Only explicitly stored learner qualifications are used.
    """

    track_match = (
        learner["bootcamp_track"] == job["required_track"]
    )

    modules_match = (
        learner["completed_modules"] >= job["minimum_modules"]
    )

    score_match = (
        learner["python_assignment_score"]
        >= job["minimum_python_score"]
    )

    readiness_match = (
        learner["readiness_status"] == "Ready for Placement"
    )

    eligible = all([
        track_match,
        modules_match,
        score_match,
        readiness_match
    ])

    preferences = [
        name.strip().casefold()
        for name in learner["preferred_employers"].split(",")
    ]

    employer_preferred = (
        job["employer"].casefold() in preferences
    )

    salary_match = (
        job["salary_egp"] >= learner["target_salary_egp"]
    )

    # Ranking score, not a hiring probability.
    match_score = (
        40 * track_match
        + 20 * modules_match
        + 20 * score_match
        + 10 * employer_preferred
        + 10 * salary_match
    )

    return {
        "learner_id": learner["learner_id"],
        "job_id": job["job_id"],
        "employer": job["employer"],
        "job_title": job["title"],
        "eligible": eligible,
        "match_score": match_score,
        "checks": {
            "track_match": track_match,
            "modules_match": modules_match,
            "score_match": score_match,
            "readiness_match": readiness_match,
            "employer_preferred": employer_preferred,
            "salary_match": salary_match
        },
        "source_type": job["source_type"]
    }

# From notebook cell 165
def verify_career_match(
    learner_id: str,
    job_id: str
) -> dict:

    learner = get_learner_profile(learner_id)

    if learner is None:
        raise ValueError("Learner not found.")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        row = conn.execute("""
            SELECT *
            FROM job_openings
            WHERE job_id = ?
        """, (job_id,)).fetchone()

    if row is None:
        raise ValueError("Job opening not found.")

    job = dict(row)

    if (
        job["source_type"] != "synthetic"
        or job["opening_status"] != "Demo Open"
    ):
        raise ValueError(
            "Job is not an active demonstration opening."
        )

    match = evaluate_job_match(learner, job)

    if not match["eligible"]:
        raise ValueError(
            "Learner no longer meets job requirements."
        )

    return match

# From notebook cell 166
def secure_career_approval_node(state: OrchestratorState) -> dict:

    match = state["selected_match"]

    decision_data = interrupt({
        "message": "Human approval required",
        "learner_id": state["learner_id"],
        "job_id": match["job_id"],
        "employer": match["employer"],
        "job_title": match["job_title"],
        "match_score": match["match_score"],
        "source_type": match["source_type"]
    })

    try:
        decision = CareerApprovalDecision.model_validate(
            decision_data
        )

        if decision.learner_id != state["learner_id"]:
            raise ValueError("Learner ID mismatch.")

        if decision.job_id != match["job_id"]:
            raise ValueError("Job ID mismatch.")

        verified = verify_career_match(
            decision.learner_id,
            decision.job_id
        )

        if not verified["eligible"]:
            raise ValueError("Match is no longer eligible.")

        if verified != match:
            raise ValueError(
                "Career match changed since review began."
            )

        status = (
            "approved" if decision.approved else "rejected"
        )

        return {
            "approval_status": status,
            "reviewer_note": decision.note
        }

    except Exception as exc:
        return {
            "approval_status": "rejected",
            "reviewer_note": (
                f"Approval validation failed: {exc}"
            )
        }
