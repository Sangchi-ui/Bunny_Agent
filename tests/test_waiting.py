import pytest
import asyncio
from typing import Dict, Any
from app import database
from app.waiting import wait_for_condition, TaskDoneCondition, run_chained_workflow
from app.safety import ALLOWED_ROOT_FOLDERS

TEMP_DIR = ALLOWED_ROOT_FOLDERS[0] / "temp_wait_test"

@pytest.fixture(autouse=True)
def setup_db():
    database.init_db()

@pytest.mark.asyncio
async def test_wait_for_task_success():
    task_id = database.create_task("test_wait", "dummy task", 1)
    
    # Run the wait condition as a background task
    wait_task = asyncio.create_task(
        wait_for_condition(TaskDoneCondition(task_id), poll_interval=1, timeout=5)
    )
    
    # Mark task as RUNNING, then DONE
    database.update_task_status(task_id, "RUNNING")
    await asyncio.sleep(1)
    database.update_task_status(task_id, "DONE", result="ok")
    
    res = await wait_task
    assert res["success"] is True
    assert "met_at" in res

@pytest.mark.asyncio
async def test_wait_for_task_timeout():
    task_id = database.create_task("test_wait", "dummy task", 1)
    
    # It never reaches DONE, timeout is 2 seconds
    res = await wait_for_condition(TaskDoneCondition(task_id), poll_interval=1, timeout=2)
    assert res["success"] is False
    assert "timed out waiting" in res["error"]

@pytest.mark.asyncio
async def test_run_workflow_success(tmp_path):
    # Step 1: Simulate slow task (0 seconds)
    # Step 2: run_command to echo
    
    steps = [
        {"action_type": "simulate_slow_task", "payload": {"seconds": 0}},
        {"action_type": "get_cpu_usage", "payload": {}}
    ]
    
    res = await run_chained_workflow(steps, overall_timeout=10)
    assert res["success"] is True
    assert len(res["results"]) == 2
    assert res["results"][0]["action"] == "simulate_slow_task"
    assert res["results"][1]["action"] == "get_cpu_usage"
    
@pytest.mark.asyncio
async def test_run_workflow_validation_rejection():
    # Attempting to run a forbidden command inside a workflow
    steps = [
        {"action_type": "simulate_slow_task", "payload": {"seconds": 0}},
        {"action_type": "run_command", "payload": {"command": "powershell", "args": ["-c", "echo 1"], "cwd": str(TEMP_DIR)}}
    ]
    
    res = await run_chained_workflow(steps, overall_timeout=10)
    
    assert res["success"] is False
    assert "validation failed" in res["error"]
    assert "powershell" in res["error"]
    # Only the first step should have completed successfully
    assert len(res["results"]) == 1
    assert res["results"][0]["action"] == "simulate_slow_task"
