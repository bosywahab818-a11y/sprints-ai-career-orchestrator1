from src.tools.local_llm import ask_local_llm
from src.tools.curriculum_retrieval import vector_db
from langgraph.graph import StateGraph, START, END
"""Staged source definitions; not yet standalone."""
from typing import TypedDict
from pydantic import BaseModel, StrictBool


# From notebook cell 21
class AdvisorState(TypedDict):
    question: str
    search_query: str
    context: str
    answer: str
    attempts: int
    sufficient: bool

# From notebook cell 40
class EvidenceEvaluation(BaseModel):
    sufficient: StrictBool
    evidence: str
    reason: str

# From notebook cell 23
def retrieve_node(state: AdvisorState) -> dict:
    """Retrieve Sprints curriculum context from ChromaDB."""

    query = state["search_query"]

    documents = vector_db.similarity_search(
        query,
        k=3
    )

    context = "\n\n".join(
        doc.page_content for doc in documents
    )

    attempts = state["attempts"] + 1

    print(f"Retrieval attempt: {attempts}")

    return {
        "context": context,
        "attempts": attempts
    }

# From notebook cell 56
def evaluate_context_node(state: AdvisorState) -> dict:
    """
    Evaluate whether retrieved Sprints curriculum passages
    contain evidence supporting the student's question.

    Requires a quotation that appears in the retrieved
    context after whitespace normalization.
    """

    question = state["question"]
    context = state["context"]

    prompt = f"""
    QUESTION:
    {question}

    CURRICULUM:
    {context}

    TASK:
    Copy the shortest relevant sentence or passage
    that directly answers the question.

    Rules:
    - Copy only text from the curriculum.
    - Do not add explanations.
    - Do not invent information.
    - If no relevant evidence exists, return NO_EVIDENCE.
    """

    evidence = ask_local_llm(
        "You extract exact supporting evidence from curriculum text.",
        prompt
    ).strip()

    print("Extracted evidence:", evidence)

    normalized_evidence = normalize_text(evidence)
    normalized_context = normalize_text(context)

    sufficient = (
        normalized_evidence != "NO_EVIDENCE"
        and len(normalized_evidence) > 10
        and normalized_evidence in normalized_context
    )

    print("Context sufficient:", sufficient)

    return {"sufficient": sufficient}

# From notebook cell 25
def reformulate_node(state: AdvisorState) -> dict:
    """Rewrite a student question to improve retrieval."""

    rewritten = ask_local_llm(
        "Rewrite the question as a concise curriculum search query. "
        "Return only the rewritten query.",
        state["question"]
    )

    print("Reformulated query:", rewritten)

    return {"search_query": rewritten}

# From notebook cell 26
def generate_answer_node(state: AdvisorState) -> dict:
    """Generate an evidence-grounded curriculum answer."""

    if not state["sufficient"]:
        return {
            "answer": "Unable to verify from the curriculum."
        }

    answer = ask_local_llm(
        "You are the Sprints Curriculum Advisor. "
        "Answer only from the supplied context. "
        "If unsupported, say: Unable to verify from the curriculum.",
        f"Context:\n{state['context']}\n\n"
        f"Question:\n{state['question']}"
    )

    return {"answer": answer}

# From notebook cell 27
def route_after_evaluation(state: AdvisorState) -> str:
    """Choose whether to answer, retry, or stop."""

    if state["sufficient"]:
        return "generate"

    if state["attempts"] >= 2:
        return "generate"

    return "reformulate"


# Recovered Advisor entry point
def run_advisor(question: str):
    """Run the LangGraph curriculum advisor workflow."""

    initial_state = {
        "question": question,
        "search_query": question,
        "context": "",
        "answer": "",
        "attempts": 0,
        "sufficient": False
    }

    result = advisor_graph.invoke(initial_state)

    print("\nFINAL ANSWER:")
    print(result["answer"])
    print("\nTotal retrieval attempts:", result["attempts"])

    return result


# Original Advisor LangGraph construction
builder = StateGraph(AdvisorState)

builder.add_node("retrieve", retrieve_node)
builder.add_node("evaluate", evaluate_context_node)
builder.add_node("reformulate", reformulate_node)
builder.add_node("generate", generate_answer_node)

builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "evaluate")

builder.add_conditional_edges(
    "evaluate",
    route_after_evaluation,
    {
        "generate": "generate",
        "reformulate": "reformulate"
    }
)

builder.add_edge("reformulate", "retrieve")
builder.add_edge("generate", END)

advisor_graph = builder.compile()



# Recovered original text normalization
def normalize_text(text: str) -> str:
    """
    Normalize whitespace for curriculum evidence matching.

    Preserves the words while removing differences caused
    by line breaks and repeated spaces.
    """
    return " ".join(text.split())
