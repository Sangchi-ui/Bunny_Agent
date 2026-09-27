import pytest
import os
from pathlib import Path
from pydantic import ValidationError

from app.safety import validate_action, ActionRequest, ALLOWED_ROOT_FOLDERS
from app.waiting import run_chained_workflow

def test_rejects_level_3():
    # 1. Attempting to directly construct ActionRequest with level=3
    # This should fail Pydantic validation before even reaching validate_action
    with pytest.raises(ValidationError) as exc_info:
        ActionRequest(action_type="run_command", level=3, payload={"command": "npm", "args": []})
    
    assert "Level must be exactly 1 or 2" in str(exc_info.value)

def test_smuggle_command_via_args():
    # 2. Attempting to smuggle a disallowed command via args
    req = ActionRequest(
        action_type="run_command", 
        level=2, 
        payload={"command": "npm", "args": ["install", ";", "rm", "-rf", "/"], "cwd": str(ALLOWED_ROOT_FOLDERS[0])}
    )
    res = validate_action(req)
    assert not res.allowed
    assert "Shell metacharacter" in res.reason

def test_path_traversal_create_file():
    # 3. Path traversal on all file operations
    workspace = ALLOWED_ROOT_FOLDERS[0]
    malicious_path = str(workspace / ".." / ".." / "Windows" / "System32" / "secret.txt")
    
    req = ActionRequest(action_type="create_file", level=2, payload={"path": malicious_path, "content": "hack"})
    res = validate_action(req)
    assert not res.allowed
    assert "outside allowed root folders" in res.reason

def test_path_traversal_read_file():
    workspace = ALLOWED_ROOT_FOLDERS[0]
    malicious_path = str(workspace / ".." / ".." / "etc" / "passwd")
    
    req = ActionRequest(action_type="read_file", level=1, payload={"path": malicious_path})
    res = validate_action(req)
    assert not res.allowed
    assert "outside allowed root folders" in res.reason

def test_path_traversal_rename_file():
    workspace = ALLOWED_ROOT_FOLDERS[0]
    valid_path = str(workspace / "valid.txt")
    malicious_path = str(workspace / ".." / ".." / "etc" / "shadow")
    
    req = ActionRequest(action_type="rename_file", level=2, payload={"old_path": valid_path, "new_path": malicious_path})
    res = validate_action(req)
    assert not res.allowed
    assert "outside allowed root folders" in res.reason

def test_path_traversal_move_file():
    workspace = ALLOWED_ROOT_FOLDERS[0]
    valid_path = str(workspace / "valid.txt")
    malicious_path = str(workspace / ".." / ".." / "etc" / "shadow")
    
    req = ActionRequest(action_type="move_file", level=2, payload={"src": valid_path, "dest": malicious_path})
    res = validate_action(req)
    assert not res.allowed
    assert "outside allowed root folders" in res.reason

def test_path_traversal_list_files():
    workspace = ALLOWED_ROOT_FOLDERS[0]
    malicious_path = str(workspace / "..")
    
    req = ActionRequest(action_type="list_files", level=1, payload={"folder": malicious_path})
    res = validate_action(req)
    assert not res.allowed
    assert "outside allowed root folders" in res.reason

@pytest.mark.asyncio
async def test_malicious_workflow():
    # 4. Attempt to run a workflow with a malicious step
    # Workflow should execute step 1 and then FAIL on step 2 during validation
    workspace = ALLOWED_ROOT_FOLDERS[0]
    malicious_path = str(workspace / ".." / "etc" / "passwd")
    
    steps = [
        {"action_type": "get_cpu_usage", "payload": {}},
        {"action_type": "read_file", "payload": {"path": malicious_path}}
    ]
    
    res = await run_chained_workflow(steps, overall_timeout=10)
    assert res["success"] is False
    assert "validation failed" in res["error"]
    assert "outside allowed root folders" in res["error"]
