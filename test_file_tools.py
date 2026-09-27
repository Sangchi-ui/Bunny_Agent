import pytest
import os
import shutil
from pathlib import Path
from app.safety import validate_action, ActionRequest, ALLOWED_ROOT_FOLDERS
from app.tools.file_tools import create_file, delete_file, write_file

# Create a temporary folder inside ALLOWED_ROOT_FOLDERS for testing
TEST_ROOT = ALLOWED_ROOT_FOLDERS[0]
TEMP_DIR = TEST_ROOT / "temp_test_dir"

@pytest.fixture(autouse=True)
def setup_teardown():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    yield
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)

def test_path_outside_allowed_rejected():
    outside_path = str(Path(os.path.expanduser("~")) / "Desktop" / "secret.txt")
    
    actions = [
        ("list_files", {"folder": outside_path}, 1),
        ("read_file", {"path": outside_path}, 1),
        ("create_file", {"path": outside_path, "content": "x"}, 2),
        ("write_file", {"path": outside_path, "content": "x"}, 2),
        ("rename_file", {"old_path": outside_path, "new_path": str(TEMP_DIR / "new.txt")}, 2),
        ("move_file", {"src": outside_path, "dest": str(TEMP_DIR / "new.txt")}, 2),
        ("delete_file", {"path": outside_path}, 2),
    ]
    
    for action_type, payload, level in actions:
        req = ActionRequest(action_type=action_type, level=level, payload=payload)
        res = validate_action(req)
        assert not res.allowed, f"{action_type} should be rejected outside allowed roots"
        assert "outside allowed root folders" in res.reason

def test_path_traversal_rejected():
    # Attempt to traverse out of the allowed root using ../
    traversal_path = str(TEST_ROOT / ".." / "some_file.txt")
    req = ActionRequest(action_type="read_file", level=1, payload={"path": traversal_path})
    res = validate_action(req)
    assert not res.allowed
    assert "outside allowed root folders" in res.reason

def test_create_file_fails_if_exists():
    test_file = TEMP_DIR / "test_create.txt"
    test_file_str = str(test_file)
    
    # Create should succeed
    res1 = create_file(test_file_str, "content")
    assert res1["success"]
    assert test_file.exists()
    
    # Create again should fail
    res2 = create_file(test_file_str, "new content")
    assert not res2["success"]
    assert "already exists" in res2["error"]
    
    # Write should succeed
    res3 = write_file(test_file_str, "overwrite content")
    assert res3["success"]
    assert test_file.read_text(encoding='utf-8') == "overwrite content"

def test_delete_confirmation_flow():
    test_file = TEMP_DIR / "test_delete.txt"
    test_file.write_text("to be deleted")
    test_file_str = str(test_file)
    
    # First call - should fail and return token
    res1 = delete_file(test_file_str)
    assert not res1["success"]
    assert "requires confirmation" in res1["error"]
    assert "confirmation_token='" in res1["error"]
    
    # Extract token
    import re
    match = re.search(r"confirmation_token='([^']+)'", res1["error"])
    token = match.group(1)
    
    # Second call with wrong token - should fail
    res2 = delete_file(test_file_str, confirmation_token="wrong")
    assert not res2["success"]
    assert "Invalid or expired" in res2["error"]
    
    # Second call with right token - should succeed
    res3 = delete_file(test_file_str, confirmation_token=token)
    assert res3["success"]
    assert not test_file.exists()
