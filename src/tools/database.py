import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from src.tools.grading import GradeResult
DB_PATH = Path(__file__).resolve().parents[2] / "data" / "sprints_learners.db"

"""Staged source definitions; not yet standalone."""

# From notebook cell 114
def get_learner_profile(learner_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        tables = {
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

        if "learners" not in tables:
            raise ValueError(
                "Expected table 'learners' not found. "
                f"Available tables: {sorted(tables)}"
            )

        row = conn.execute(
            "SELECT * FROM learners WHERE learner_id = ?",
            (learner_id,)
        ).fetchone()

        return dict(row) if row else None

# From notebook cell 140
def initialize_assessment_database():

    with sqlite3.connect(DB_PATH) as conn:

        conn.execute("""
        CREATE TABLE IF NOT EXISTS assessment_results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            learner_id TEXT NOT NULL,
            assignment_id TEXT NOT NULL,
            score INTEGER NOT NULL
                CHECK(score BETWEEN 0 AND 100),
            status TEXT NOT NULL,
            tests_passed INTEGER NOT NULL,
            tests_total INTEGER NOT NULL,
            feedback TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (learner_id)
                REFERENCES learners(learner_id)
        )
        """)

        conn.commit()

    print("PASS: Assessment results table created!")

# From notebook cell 141
def save_assessment_result(grade: dict, feedback: str):

    validated = GradeResult.model_validate(grade)

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    with sqlite3.connect(DB_PATH) as conn:

        conn.execute("PRAGMA foreign_keys = ON")

        cursor = conn.execute("""
        INSERT INTO assessment_results (
            learner_id,
            assignment_id,
            score,
            status,
            tests_passed,
            tests_total,
            feedback,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            validated.learner_id,
            validated.assignment_id,
            validated.score,
            validated.status,
            validated.tests_passed,
            validated.tests_total,
            feedback,
            timestamp
        ))

        result_id = cursor.lastrowid

        conn.commit()

    return result_id

# From notebook cell 160
def save_assessment_idempotent(
    submission_id: str,
    grade: dict,
    feedback: str
):
    if not submission_id:
        raise ValueError("Submission ID is required.")

    validated = GradeResult.model_validate(grade)

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    with sqlite3.connect(DB_PATH) as conn:

        conn.execute("PRAGMA foreign_keys = ON")

        conn.execute("""
        INSERT INTO assessment_results (
            submission_id,
            learner_id,
            assignment_id,
            score,
            status,
            tests_passed,
            tests_total,
            feedback,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(submission_id) DO NOTHING
        """, (
            submission_id,
            validated.learner_id,
            validated.assignment_id,
            validated.score,
            validated.status,
            validated.tests_passed,
            validated.tests_total,
            feedback,
            timestamp
        ))

        row = conn.execute("""
            SELECT
                result_id,
                learner_id,
                assignment_id,
                score
            FROM assessment_results
            WHERE submission_id = ?
        """, (submission_id,)).fetchone()

        if row is None:
            raise RuntimeError("Assessment was not saved.")

        if (
            row[1] != validated.learner_id
            or row[2] != validated.assignment_id
            or row[3] != validated.score
        ):
            raise ValueError(
                "Submission ID reused with conflicting grade."
            )

        conn.commit()

        return row[0]

# From notebook cell 143
def get_assessment_history(learner_id: str):

    with sqlite3.connect(DB_PATH) as conn:

        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
        SELECT
            result_id,
            learner_id,
            assignment_id,
            score,
            status,
            tests_passed,
            tests_total,
            feedback,
            created_at
        FROM assessment_results
        WHERE learner_id = ?
        ORDER BY result_id DESC
        """, (learner_id,)).fetchall()

        return [dict(row) for row in rows]


def get_demo_openings():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT *
            FROM job_openings
            WHERE opening_status = 'Demo Open'
              AND source_type = 'synthetic'
            ORDER BY job_id
        """).fetchall()

        return [dict(row) for row in rows]
