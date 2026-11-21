from src.agents.assessor import assessor_graph
from src.tools.database import save_assessment_result
from src.agents.advisor import run_advisor
"""Sprints AI Career Orchestrator."""
from src.state import OrchestratorState



from typing import TypedDict, Optional, Literal

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from src.agents.career import (
    CareerApprovalDecision,
    find_eligible_jobs,
    verify_career_match,
)

"""Original unified orchestrator functions.
Staging only — dependencies not yet connected.
"""



# Original notebook cell 131
def orchestrator_router(state: OrchestratorState) -> str:
    task = state.get("task_type")

    if task in ("advisor", "assessor", "career"):
        return task

    return "invalid"



# Original notebook cell 132
def unified_advisor_node(state: OrchestratorState) -> dict:
    print("\n[ADVISOR] Answering curriculum question")

    question = state["question"]

    # Uses the evidence-aware RAG advisor built earlier.
    result = run_advisor(question)

    return {
        "answer": result["answer"],
        "error": None
    }



# Original notebook cell 133
def unified_assessor_node(state: OrchestratorState) -> dict:
    print("\n[ASSESSOR] Grading Python submission")

    result = assessor_graph.invoke({
        "learner_id": state["learner_id"],
        "assignment_id": state["assignment_id"],
        "code": state["code"]
    })

    return {
        "grade": result["grade"],
        "feedback": result.get("feedback", ""),
        "error": result.get("error")
    }



# Original notebook cell 145
def unified_save_grade_node(state: OrchestratorState) -> dict:

    print("\n[DATABASE] Saving assessment result")

    grade = state["grade"]

    if grade["learner_id"] != state["learner_id"]:
        raise ValueError(
            "Grade learner ID does not match session learner."
        )

    if grade["assignment_id"] != state["assignment_id"]:
        raise ValueError(
            "Grade assignment ID mismatch."
        )

    result_id = save_assessment_result(
        grade,
        state["feedback"]
    )

    print("Saved result ID:", result_id)

    return {
        "assessment_result_id": result_id
    }



# Original notebook cell 134
def unified_career_match_node(state: OrchestratorState) -> dict:
    print("\n[CAREER] Finding eligible jobs")

    matches = find_eligible_jobs(state["learner_id"])

    return {
        "matches": matches,
        "selected_match": matches[0] if matches else {},
        "approval_status": "pending" if matches else "no_match"
    }



# Original notebook cell 166
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



# Original notebook cell 131
def invalid_task_node(state: OrchestratorState) -> dict:
    return {
        "error": "Unsupported task type."
    }



# Original notebook cell 134
def route_unified_career(state: OrchestratorState) -> str:
    return "approval" if state["matches"] else "finish"



# Final graph construction


final_builder = StateGraph(OrchestratorState)

final_builder.add_node("advisor", unified_advisor_node)

final_builder.add_node("assessor", unified_assessor_node)

final_builder.add_node("save_grade", unified_save_grade_node)

final_builder.add_node("career_match", unified_career_match_node)

final_builder.add_node(
    "career_approval",
    secure_career_approval_node
)

final_builder.add_node("invalid", invalid_task_node)

final_builder.add_conditional_edges(
    START,
    orchestrator_router,
    {
        "advisor": "advisor",
        "assessor": "assessor",
        "career": "career_match",
        "invalid": "invalid"
    }
)

final_builder.add_edge("advisor", END)

final_builder.add_edge("assessor", "save_grade")

final_builder.add_edge("save_grade", END)

final_builder.add_edge("invalid", END)

final_builder.add_conditional_edges(
    "career_match",
    route_unified_career,
    {
        "approval": "career_approval",
        "finish": END
    }
)

final_builder.add_edge("career_approval", END)

final_memory = MemorySaver()

final_orchestrator = final_builder.compile(
    checkpointer=final_memory
)