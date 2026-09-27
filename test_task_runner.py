import pytest
import asyncio
from app.database import create_task, get_task, get_or_create_conversation
from app.task_runner import TaskRunner
from app.tools.test_tools import simulate_slow_task

@pytest.mark.asyncio
async def test_task_runner_success():
    runner = TaskRunner(concurrency_limit=1)
    await runner.start()
    
    try:
        conv_id = get_or_create_conversation("test_runner", "runner_01")
        task_id = create_task(conv_id, "Slow task success", level=1)
        
        # Submit task that takes 1 second
        runner.submit(task_id, lambda: simulate_slow_task(1), timeout=5)
        
        # Give it a moment to start
        await asyncio.sleep(0.1)
        task = get_task(task_id)
        assert task["status"] == "RUNNING"
        
        # Wait for completion
        await asyncio.sleep(1.2)
        task = get_task(task_id)
        assert task["status"] == "DONE"
        assert "Slept for 1 seconds" in task["result"]
    finally:
        await runner.stop()

@pytest.mark.asyncio
async def test_task_runner_timeout_and_recovery():
    runner = TaskRunner(concurrency_limit=1)
    await runner.start()
    
    try:
        conv_id = get_or_create_conversation("test_runner", "runner_02")
        
        # Task 1: will timeout
        task_id_timeout = create_task(conv_id, "Slow task timeout", level=1)
        # We tell it to sleep for 3 seconds, but set timeout to 1 second
        runner.submit(task_id_timeout, lambda: simulate_slow_task(3), timeout=1)
        
        # Task 2: will succeed (proves runner recovered)
        task_id_success = create_task(conv_id, "Recovery task", level=1)
        runner.submit(task_id_success, lambda: simulate_slow_task(0), timeout=5)
        
        # Wait for both to finish (task 1 times out at 1s, task 2 runs instantly after)
        await asyncio.sleep(1.5)
        
        t1 = get_task(task_id_timeout)
        assert t1["status"] == "FAILED"
        assert "timed out after 1 seconds" in t1["result"].lower()
        
        t2 = get_task(task_id_success)
        assert t2["status"] == "DONE"
        assert "Slept for 0" in t2["result"]
    finally:
        await runner.stop()
