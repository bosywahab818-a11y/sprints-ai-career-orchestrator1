from src.tools.assignments import assignment
from src.tools.grading import (
    GradeResult,
    validate_submission,
    grade_sandbox_response,
)
from src.tools.sandbox_models import (
    SecureExecutionRequest,
    SandboxRequest,
    SandboxResponse,
)
from src.tools.e2b_execution import run_real_sandbox



from typing import TypedDict, Optional
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END

from langgraph.graph import StateGraph, START, END

"""Staged source definitions; not yet standalone."""

# From notebook cell 103
class AssessorState(TypedDict, total=False):
    learner_id: str
    assignment_id: str
    code: str

    validation: dict
    sandbox_response: dict
    grade: dict

    feedback: str
    feedback_approved: bool
    feedback_attempts: int
    evaluation_reason: str

    error: Optional[str]

# From notebook cell 95
def assessor_validate_node(state: AssessorState) -> dict:

    print("\n[1] VALIDATING SUBMISSION")

    if state["assignment_id"] != assignment.assignment_id:
        return {
            "validation": {
                "valid": False,
                "reason": "Unknown assignment ID."
            },
            "error": "Unknown assignment ID."
        }

    result = validate_submission(
        state["code"],
        assignment.function_name
    )

    print("Validation:", result)

    return {
        "validation": result,
        "error": None if result["valid"] else result["reason"]
    }

# From notebook cell 96
def assessor_execute_node(state: AssessorState) -> dict:

    print("\n[2] EXECUTING IN E2B")

    execution_request = SecureExecutionRequest(
        learner_id=state["learner_id"],
        assignment_id=state["assignment_id"],
        code=state["code"]
    )

    try:
        response = run_real_sandbox(
            execution_request,
            assignment
        )

        print("Execution status:", response.status)

        return {
            "sandbox_response": response.model_dump(),
            "error": None
        }

    except Exception as exc:
        # Do not expose raw sandbox internals to learners.
        print("Execution failure type:", type(exc).__name__)

        return {
            "error": "Sandbox execution failed.",
            "sandbox_response": {
                "status": "runtime_error",
                "tests": [],
                "error": "Sandbox execution failed."
            }
        }

# From notebook cell 97
def assessor_grade_node(state: AssessorState) -> dict:

    print("\n[3] CALCULATING GRADE")

    request = SandboxRequest(
        learner_id=state["learner_id"],
        assignment_id=state["assignment_id"],
        function_name=assignment.function_name,
        code=state["code"],
        test_cases=[case.model_dump() for case in assignment.test_cases]
    )

    response = SandboxResponse.model_validate(
        state["sandbox_response"]
    )

    grade = grade_sandbox_response(
        request,
        response
    )

    print("Score:", grade.score)
    print("Status:", grade.status)

    return {
        "grade": grade.model_dump()
    }

# From notebook cell 98
def assessor_reject_node(state: AssessorState) -> dict:

    print("\nSUBMISSION REJECTED")

    reason = state["validation"]["reason"]

    grade = GradeResult(
        learner_id=state["learner_id"],
        assignment_id=state["assignment_id"],
        score=0,
        status="needs_review",
        feedback=reason,
        tests_passed=0,
        tests_total=len(assignment.test_cases)
    )

    return {
        "grade": grade.model_dump(),
        "error": reason
    }

# From notebook cell 98
def assessor_execution_failure_node(
    state: AssessorState
) -> dict:

    grade = GradeResult(
        learner_id=state["learner_id"],
        assignment_id=state["assignment_id"],
        score=0,
        status="needs_review",
        feedback="Execution could not be completed.",
        tests_passed=0,
        tests_total=len(assignment.test_cases)
    )

    return {"grade": grade.model_dump()}

# From notebook cell 104
def generate_feedback_node(state: AssessorState) -> dict:
    """
    Generate feedback using only verified grading results.
    """

    grade = GradeResult.model_validate(state["grade"])

    if grade.status == "passed":
        feedback = (
            f"Great work! You passed {grade.tests_passed} "
            f"out of {grade.tests_total} tests and scored "
            f"{grade.score}/100. "
            "Your solution meets the tested requirements."
        )

    elif grade.status == "failed":
        feedback = (
            f"You passed {grade.tests_passed} out of "
            f"{grade.tests_total} tests and scored "
            f"{grade.score}/100. "
            "Review your implementation and test it "
            "against different inputs."
        )

    else:
        feedback = (
            f"Your submission requires review. "
            f"{grade.feedback}"
        )

    return {
        "feedback": feedback,
        "feedback_attempts": 1,
        "feedback_approved": False
    }

# From notebook cell 105
def evaluate_feedback_node(state: AssessorState) -> dict:
    """
    Evaluate whether feedback includes verified grading facts.
    """

    grade = GradeResult.model_validate(state["grade"])
    feedback = state["feedback"]

    required_facts = [
        f"{grade.score}/100",
        f"{grade.tests_passed}",
        f"{grade.tests_total}"
    ]

    missing = [
        fact for fact in required_facts
        if fact not in feedback
    ]

    approved = len(missing) == 0

    reason = (
        "Feedback includes the required grading facts."
        if approved
        else f"Missing grading facts: {missing}"
    )

    print("Feedback approved:", approved)
    print("Evaluation reason:", reason)

    return {
        "feedback_approved": approved,
        "evaluation_reason": reason
    }

# From notebook cell 106
def optimize_feedback_node(state: AssessorState) -> dict:
    """
    Repair incomplete feedback without changing the grade.
    """

    grade = GradeResult.model_validate(state["grade"])

    attempts = state.get("feedback_attempts", 1) + 1

    feedback = (
        f"Assignment {grade.assignment_id}: "
        f"Score {grade.score}/100. "
        f"Passed {grade.tests_passed} out of "
        f"{grade.tests_total} tests. "
        f"Status: {grade.status}. "
        f"{grade.feedback}"
    )

    print("Feedback refinement attempt:", attempts)

    return {
        "feedback": feedback,
        "feedback_attempts": attempts
    }

# From notebook cell 107
def route_feedback(state: AssessorState) -> str:

    if state["feedback_approved"]:
        return "finish"

    if state["feedback_attempts"] >= 3:
        return "finish"

    return "optimize"


# Recovered from notebook cell 98
def route_execution(state: AssessorState) -> str:
    if state.get("error"):
        return "reject_execution"

    return "grade"

# Recovered from notebook cell 98
def route_validation(state: AssessorState) -> str:
    if state["validation"]["valid"]:
        return "execute"

    return "reject"

# STEP 21 — RESTORED ASSESSOR GRAPH
assessor_builder = StateGraph(AssessorState)

assessor_builder.add_node("validate", assessor_validate_node)

assessor_builder.add_node("execute", assessor_execute_node)

assessor_builder.add_node("grade", assessor_grade_node)

assessor_builder.add_node("reject", assessor_reject_node)

assessor_builder.add_node(
    "reject_execution",
    assessor_execution_failure_node
)

assessor_builder.add_node(
    "generate_feedback",
    generate_feedback_node
)

assessor_builder.add_node(
    "evaluate_feedback",
    evaluate_feedback_node
)

assessor_builder.add_node(
    "optimize_feedback",
    optimize_feedback_node
)

assessor_builder.add_edge(START, "validate")

assessor_builder.add_conditional_edges(
    "validate",
    route_validation,
    {
        "execute": "execute",
        "reject": "reject"
    }
)

assessor_builder.add_conditional_edges(
    "execute",
    route_execution,
    {
        "grade": "grade",
        "reject_execution": "reject_execution"
    }
)

assessor_builder.add_edge("grade", "generate_feedback")

assessor_builder.add_edge("reject", "generate_feedback")

assessor_builder.add_edge(
    "reject_execution",
    "generate_feedback"
)

assessor_builder.add_edge(
    "generate_feedback",
    "evaluate_feedback"
)

assessor_builder.add_conditional_edges(
    "evaluate_feedback",
    route_feedback,
    {
        "finish": END,
        "optimize": "optimize_feedback"
    }
)

assessor_builder.add_edge(
    "optimize_feedback",
    "evaluate_feedback"
)

assessor_graph = assessor_builder.compile()
