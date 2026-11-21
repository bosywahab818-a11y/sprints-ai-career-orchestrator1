import os
import json

from e2b import Sandbox

from src.tools.grading import validate_submission
from src.tools.sandbox_models import (
    SandboxResponse,
    SandboxTestResult,
)

def run_real_sandbox(request, assignment):
    """
    Execute a Python assignment inside an E2B sandbox.

    Prototype for trusted demonstration submissions only.
    """

    if request.assignment_id != assignment.assignment_id:
        raise ValueError("Assignment ID mismatch")

    validation = validate_submission(
        request.code,
        assignment.function_name
    )

    if not validation["valid"]:
        raise ValueError(validation["reason"])

    payload = {
        "function_name": assignment.function_name,
        "test_cases": [
            case.model_dump()
            for case in assignment.test_cases
        ]
    }

    runner_code = '''
import importlib.util
import json

with open("/tmp/tests.json") as f:
    payload = json.load(f)

spec = importlib.util.spec_from_file_location(
    "submission", "/tmp/submission.py"
)

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

fn = getattr(module, payload["function_name"])

results = []

for case in payload["test_cases"]:
    try:
        actual = fn(case["input_value"])

        passed = (
            type(actual) is int
            and actual == case["expected_output"]
        )

        results.append({
            "name": case["name"],
            "passed": passed,
            "expected": case["expected_output"],
            "actual": actual if type(actual) is int else None
        })

    except Exception:
        results.append({
            "name": case["name"],
            "passed": False,
            "expected": case["expected_output"],
            "actual": None
        })

with open("/tmp/results.json", "w") as f:
    json.dump(results, f)
'''

    with Sandbox.create(
        timeout=60,
        allow_internet_access=False,
        api_key=os.environ["E2B_API_KEY"]
    ) as sandbox:

        sandbox.files.write(
            "/tmp/submission.py",
            request.code
        )

        sandbox.files.write(
            "/tmp/tests.json",
            json.dumps(payload)
        )

        sandbox.files.write(
            "/tmp/runner.py",
            runner_code
        )

        execution = sandbox.commands.run(
            "python -I /tmp/runner.py",
            timeout=5
        )

        if execution.exit_code != 0:
            raise RuntimeError(
                "Sandbox execution failed. "
                f"Exit code: {execution.exit_code}"
            )

        raw_results = sandbox.files.read(
            "/tmp/results.json"
        )

    return SandboxResponse(
        status="completed",
        tests=[
            SandboxTestResult(**item)
            for item in json.loads(raw_results)
        ]
    )
