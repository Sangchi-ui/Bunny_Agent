import pytest
from pathlib import Path
from app.verification import verify_result

def test_verification_catches_lie(tmp_path):
    # Simulate a file tool lying
    target_path = tmp_path / "missing.txt"
    payload = {"path": str(target_path), "content": "hello"}
    execution_result = {"success": True}
    
    verified_res = verify_result("write_file", payload, execution_result)
    
    assert verified_res["verified"] is False
    assert verified_res["success"] is False
    assert "Verification failed" in verified_res["error"]
    assert "does not exist" in verified_res["verification_detail"]

def test_verification_passes_genuine(tmp_path):
    # Simulate a genuine file creation
    target_path = tmp_path / "exists.txt"
    target_path.write_text("hello world")
    
    payload = {"path": str(target_path), "content": "world"}
    execution_result = {"success": True}
    
    verified_res = verify_result("write_file", payload, execution_result)
    
    assert verified_res["verified"] is True
    assert verified_res["success"] is True

def test_verification_catches_failed_command():
    # Simulate pytest exiting 0 but output contains failed
    payload = {"command": "pytest", "args": ["test.py"], "cwd": "."}
    execution_result = {"success": True, "exit_code": 0, "output": "Test failed because reasons"}
    
    verified_res = verify_result("run_command", payload, execution_result)
    
    assert verified_res["verified"] is False
    assert verified_res["success"] is False
    assert "Verification failed" in verified_res["error"]
    assert "output contains test failures" in verified_res["verification_detail"]

def test_verification_passes_successful_command():
    # Simulate pytest exiting 0 and output contains passed
    payload = {"command": "pytest", "args": ["test.py"], "cwd": "."}
    execution_result = {"success": True, "exit_code": 0, "output": "1 passed in 0.01s"}
    
    verified_res = verify_result("run_command", payload, execution_result)
    
    assert verified_res["verified"] is True
    assert verified_res["success"] is True
