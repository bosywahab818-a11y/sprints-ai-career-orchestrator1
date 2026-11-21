from typing import TypedDict, Optional, Literal

class OrchestratorState(TypedDict, total=False):
    learner_id: str
    task_type: Literal["advisor", "assessor", "career"]

    question: str
    code: str
    assignment_id: str

    answer: str
    grade: dict
    feedback: str
    assessment_result_id: int

    matches: list[dict]
    selected_match: dict
    approval_status: str
    reviewer_note: str

    error: Optional[str]
