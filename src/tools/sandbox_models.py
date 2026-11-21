from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class PythonTestCase(BaseModel):
    name: str
    input_value: int
    expected_output: int

class SandboxTestResult(BaseModel):
    name: str
    passed: bool
    expected: int
    actual: int | None = None

class SandboxRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    learner_id: str
    assignment_id: str
    function_name: str
    code: str = Field(min_length=1, max_length=20000)
    test_cases: list[PythonTestCase] = Field(min_length=1)

class SandboxResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal[
        "completed",
        "timeout",
        "runtime_error",
        "security_error"
    ]

    tests: list[SandboxTestResult]
    error: str | None = None

class SecureExecutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    learner_id: str = Field(min_length=1)
    assignment_id: str = Field(min_length=1)
    code: str = Field(min_length=1, max_length=20000)
