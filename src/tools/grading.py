from src.tools.sandbox_models import SandboxRequest, SandboxResponse
"""Staged source definitions; not yet standalone."""
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
import ast


# From notebook cell 64
class GradeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    learner_id: str
    assignment_id: str

    score: int = Field(ge=0, le=100)

    status: Literal[
        "passed",
        "failed",
        "needs_review"
    ]

    feedback: str

    tests_passed: int = Field(ge=0)
    tests_total: int = Field(ge=0)

# From notebook cell 70
class PythonTestCase(BaseModel):
    name: str
    input_value: int
    expected_output: int


class PythonAssignment(BaseModel):
    assignment_id: str
    title: str
    function_name: str
    description: str
    test_cases: list[PythonTestCase] = Field(min_length=1)

# From notebook cell 70

# From notebook cell 72
def validate_submission(
    code: str,
    required_function: str
) -> dict:
    """
    Check Python syntax and required function definition.

    Does not execute submitted code.
    """

    try:
        tree = ast.parse(code)

    except SyntaxError as error:
        return {
            "valid": False,
            "reason": f"Syntax error: {error.msg}"
        }

    function_names = [
        node.name
        for node in tree.body
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        )
    ]

    if required_function not in function_names:
        return {
            "valid": False,
            "reason": (
                f"Required function "
                f"'{required_function}' not found."
            )
        }

    return {
        "valid": True,
        "reason": "Submission structure is valid."
    }

# From notebook cell 67
def calculate_grade(
    learner_id: str,
    assignment_id: str,
    test_results: list[bool]
) -> GradeResult:
    """
    Calculate a grade from automated test results.

    Each test has equal weight.
    A score of 70 or higher is a pass.
    """

    if not test_results:
        raise ValueError("At least one test is required.")

    if not all(type(x) is bool for x in test_results):
        raise ValueError("Test results must be booleans.")

    total = len(test_results)
    passed = sum(test_results)

    score = round((passed / total) * 100)

    status = "passed" if score >= 70 else "failed"

    feedback = (
        f"Passed {passed} out of {total} tests. "
        f"Final score: {score}/100."
    )

    return GradeResult(
        learner_id=learner_id,
        assignment_id=assignment_id,
        score=score,
        status=status,
        feedback=feedback,
        tests_passed=passed,
        tests_total=total
    )

# From notebook cell 77
def grade_sandbox_response(
    request: SandboxRequest,
    response: SandboxResponse
) -> GradeResult:
    """
    Convert validated sandbox test results into a grade.

    Only completed executions can receive a passing grade.
    Other execution statuses require review.
    """

    if response.status != "completed":
        return GradeResult(
            learner_id=request.learner_id,
            assignment_id=request.assignment_id,
            score=0,
            status="needs_review",
            feedback=f"Execution status: {response.status}",
            tests_passed=0,
            tests_total=len(request.test_cases)
        )

    expected_names = [t.name for t in request.test_cases]
    actual_names = [t.name for t in response.tests]

    if (
        len(set(expected_names)) != len(expected_names)
        or len(actual_names) != len(expected_names)
        or set(actual_names) != set(expected_names)
    ):
        raise ValueError("Sandbox test results do not match assignment")

    # Recalculate pass/fail from reported outputs rather
    # than blindly trusting the 'passed' field.
    results_by_name = {t.name: t for t in response.tests}
    outcomes = []

    for case in request.test_cases:
        result = results_by_name[case.name]

        outcomes.append(
            result.passed
            and result.expected == case.expected_output
            and result.actual == case.expected_output
        )

    return calculate_grade(
        learner_id=request.learner_id,
        assignment_id=request.assignment_id,
        test_results=outcomes
    )
