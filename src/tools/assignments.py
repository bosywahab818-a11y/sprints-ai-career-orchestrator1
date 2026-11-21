from src.tools.grading import PythonAssignment, PythonTestCase

assignment = PythonAssignment(
    assignment_id="PY-001",
    title="Square a Number",
    function_name="square_number",
    description=(
        "Create a function square_number(n) "
        "that returns n multiplied by itself."
    ),
    test_cases=[
        PythonTestCase(
            name="Positive number",
            input_value=5,
            expected_output=25
        ),
        PythonTestCase(
            name="Negative number",
            input_value=-3,
            expected_output=9
        ),
        PythonTestCase(
            name="Zero",
            input_value=0,
            expected_output=0
        ),
        PythonTestCase(
            name="Large number",
            input_value=100,
            expected_output=10000
        )
    ]
)
