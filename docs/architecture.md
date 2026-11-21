# Sprints AI Career Orchestrator Architecture

## Core Architecture

The system uses a unified LangGraph StateGraph.

A task router selects one of three branches:

1. Advisor
2. Assessor
3. Career Matching

## Typed State

OrchestratorState stores:
- learner_id
- task_type
- question
- code
- assignment_id
- answer
- grade
- feedback
- assessment_result_id
- matches
- selected_match
- approval_status
- reviewer_note
- error

## Advisor

The Advisor retrieves curriculum evidence from ChromaDB
and generates answers grounded in retrieved content.

Unsupported questions return:
"Unable to verify from the curriculum."

## Assessor

The Assessor validates Python submissions before sending
them to a hosted E2B execution environment.

Test results determine the grade.

Feedback is evaluated and repaired when required.

Assessment results are stored in SQLite.

## Career Agent

The Career Agent retrieves learner profiles and job records
from SQLite.

It checks track, completed modules, Python score, and
readiness status before recommending an opportunity.

Employer preference and salary expectations contribute
to ranking.

A LangGraph interrupt pauses execution for human review.

The approval node revalidates learner eligibility and
the exact selected match before accepting approval.

## Security

Implemented prototype controls:
- Learner-specific checkpoint threads
- Session ownership checks in a trusted wrapper
- SQL parameterization
- Structured grading validation
- Hosted code execution
- Career approval data validation
- Eligibility revalidation

Production gaps:
- Real authentication and role-based authorization
- Durable checkpoint storage
- Persistent audit logs
- Verified job-opening integrations
- End-to-end idempotency
- Sandbox isolation verification
- Credential and hidden-test protection

## Demonstration

The prototype demonstrates three sequential task requests
through one unified LangGraph StateGraph.

It does not yet autonomously transition from Advisor to
Assessor to Career Matching in one uninterrupted graph run.
