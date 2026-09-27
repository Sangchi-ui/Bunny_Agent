import pytest
from pydantic import ValidationError
from app.safety import ActionRequest, validate_action, ALLOWLIST, BUNNY_ROOT
import os

def test_level_3_rejected_pydantic():
    with pytest.raises(ValidationError) as exc_info:
        ActionRequest(action_type="read_file", level=3, payload={"path": "test.txt"})
    
    assert "Level must be exactly 1 or 2" in str(exc_info.value)

def test_file_traversal_rejected():
    # Attempting to go up from BUNNY_ROOT
    bad_path = os.path.join(str(BUNNY_ROOT), "..", "..", "Windows", "System32")
    req = ActionRequest(action_type="read_file", level=1, payload={"path": bad_path})
    result = validate_action(req)
    assert result.allowed is False
    assert "outside allowed root folders" in result.reason

def test_file_outside_root_rejected():
    req = ActionRequest(action_type="read_file", level=1, payload={"path": "C:\\Windows\\System32\\cmd.exe"})
    result = validate_action(req)
    assert result.allowed is False
    assert "outside allowed root folders" in result.reason

def test_file_inside_root_allowed():
    good_path = os.path.join(str(BUNNY_ROOT), "app", "main.py")
    req = ActionRequest(action_type="read_file", level=1, payload={"path": good_path})
    result = validate_action(req)
    assert result.allowed is True
    assert "Action validated and allowed" in result.reason

def test_command_not_in_allowlist_rejected():
    req = ActionRequest(action_type="run_command", level=2, payload={"command": "rm"})
    result = validate_action(req)
    assert result.allowed is False
    assert "is not in ALLOWED_COMMANDS" in result.reason

def test_command_in_allowlist_allowed():
    req = ActionRequest(action_type="run_command", level=2, payload={"command": "pytest"})
    result = validate_action(req)
    assert result.allowed is True
    assert "Action validated and allowed" in result.reason

def test_unknown_action_type_rejected():
    req = ActionRequest(action_type="launch_nukes", level=1, payload={})
    result = validate_action(req)
    assert result.allowed is False
    assert "is not in ALLOWLIST" in result.reason

def test_level_mismatch_rejected():
    # run_command is configured as level 2. Try calling as level 1.
    req = ActionRequest(action_type="run_command", level=1, payload={"command": "pytest"})
    result = validate_action(req)
    assert result.allowed is False
    assert "does not match allowed level" in result.reason
