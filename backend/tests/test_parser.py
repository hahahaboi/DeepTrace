import pytest
from app.parser import clean_ansi_codes, parse_error_log

def test_clean_ansi_codes():
    ansi_text = "\x1b[31mError:\x1b[0m Test failed with \x1b[1mcode 1\x1b[0m"
    expected = "Error: Test failed with code 1"
    assert clean_ansi_codes(ansi_text) == expected
    assert clean_ansi_codes("") == ""

def test_parse_error_log_python_traceback():
    raw_log = """
[INFO] Starting tests...
[DEBUG] Initializing DB
Traceback (most recent call last):
  File "app/main.py", line 42, in run
    result = execute_task()
  File "app/tasks.py", line 12, in execute_task
    raise ValueError("DB connection timeout")
ValueError: DB connection timeout
[INFO] Finished tests.
    """
    parsed = parse_error_log(raw_log)
    assert "Traceback (most recent call last):" in parsed
    assert 'raise ValueError("DB connection timeout")' in parsed
    assert "ValueError: DB connection timeout" in parsed
    assert "[INFO]" not in parsed
    assert "[DEBUG]" not in parsed

def test_parse_error_log_node_stack_trace():
    raw_log = """
> deeptrace@0.1.0 test
> jest

  console.error
    Failed to load config

Error: Jest test failed
    at Object.<anonymous> (tests/index.test.js:8:21)
    at Promise.then.completed (node_modules/jest-circus/build/utils.js:298:28)
    at runTest (node_modules/jest-circus/build/run.js:124:4)
    at runTests (node_modules/jest-circus/build/run.js:189:12)
    at run (node_modules/jest-circus/build/index.js:58:32)
[INFO] process exited with 1
    """
    parsed = parse_error_log(raw_log)
    assert "Error: Jest test failed" in parsed
    assert "at Object.<anonymous> (tests/index.test.js:8:21)" in parsed
    assert "[INFO]" not in parsed

def test_parse_error_log_fallback_keywords():
    raw_log = """
[INFO] Loading dependencies
[INFO] Running compiler
[FATAL] Compilation failed: Syntax error in file.go:12
[INFO] Completed
    """
    parsed = parse_error_log(raw_log)
    assert "[FATAL] Compilation failed: Syntax error in file.go:12" in parsed

def test_parse_error_log_fallback_tail():
    raw_log = "\n".join([f"Log message line {i}" for i in range(1, 30)])
    parsed = parse_error_log(raw_log)
    lines = parsed.splitlines()
    assert len(lines) == 20
    assert lines[-1] == "Log message line 29"
    assert lines[0] == "Log message line 10"
