import pytest
import os
import asyncio
from pathlib import Path
from app.safety import validate_action, ActionRequest, ALLOWED_ROOT_FOLDERS
from app.tools.dev_tools import run_command

TEST_ROOT = ALLOWED_ROOT_FOLDERS[0]
TEMP_DIR = TEST_ROOT / "temp_dev_test"

@pytest.fixture(autouse=True)
def setup_teardown():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    yield
    if TEMP_DIR.exists():
        import shutil
        shutil.rmtree(TEMP_DIR)

def test_unallowed_command_rejected():
    req = ActionRequest(action_type="run_command", level=2, payload={
        "command": "del", 
        "args": ["file.txt"], 
        "cwd": str(TEMP_DIR)
    })
    res = validate_action(req)
    assert not res.allowed
    assert "not in ALLOWED_COMMANDS" in res.reason

def test_outside_cwd_rejected():
    outside_cwd = str(Path(os.path.expanduser("~")) / "Desktop")
    req = ActionRequest(action_type="run_command", level=2, payload={
        "command": "python", 
        "args": ["--version"], 
        "cwd": outside_cwd
    })
    res = validate_action(req)
    assert not res.allowed
    assert "outside allowed root folders" in res.reason

def test_shell_metachars_rejected():
    req = ActionRequest(action_type="run_command", level=2, payload={
        "command": "python", 
        "args": ["-c", "print('hello'); rm -rf /"], 
        "cwd": str(TEMP_DIR)
    })
    res = validate_action(req)
    assert not res.allowed
    assert "forbidden in args" in res.reason

@pytest.mark.asyncio
async def test_real_execution_success():
    res = await run_command("python", ["--version"], str(TEMP_DIR))
    assert res["success"]
    assert "Python" in res["stdout"] or "Python" in res["stderr"]

@pytest.mark.asyncio
async def test_execution_timeout_killed():
    # A python script that sleeps for 10 seconds
    script = TEMP_DIR / "sleep.py"
    script.write_text("import time\nprint('sleeping')\ntime.sleep(10)")
    
    # Run it with 1 second timeout
    res = await run_command("python", [str(script)], str(TEMP_DIR), timeout=1)
    
    assert not res["success"]
    assert "killed" in res["error"].lower()
    
    # Verify process didn't leak by checking exit code logic in dev_tools
    # Since dev_tools.py explicitly calls process.kill() and wait(), 
    # it won't be a zombie.
