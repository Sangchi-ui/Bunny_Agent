import pytest
import asyncio
from pathlib import Path

from app.safety import validate_action, ActionRequest
from app.agents import get_agent
from app.agents.cli_agent import CLIAgent
from app.waiting import run_chained_workflow

@pytest.mark.asyncio
async def test_invalid_agent_rejected():
    req = ActionRequest(action_type="delegate_to_agent", level=2, payload={
        "agent_name": "malicious_agent",
        "prompt": "hack the planet"
    })
    res = validate_action(req)
    assert res.allowed is False
    assert "not in allowed agents list" in res.reason

@pytest.mark.asyncio
async def test_send_prompt_writes_file():
    agent = CLIAgent()
    res = await agent.send_prompt("Test prompt")
    
    assert res["success"] is True
    handle = res["handle"]
    
    inbox_path = agent.inbox_dir / f"{handle}.txt"
    assert inbox_path.exists()
    assert inbox_path.read_text() == "Test prompt"
    
    # Cleanup
    inbox_path.unlink()

@pytest.mark.asyncio
async def test_agent_lifecycle_and_result():
    agent = CLIAgent()
    res = await agent.send_prompt("Another test")
    handle = res["handle"]
    
    # Initial status
    assert await agent.is_finished(handle) is False
    assert "pending" in agent.get_status_description(handle).lower()
    
    # Simulate agent completion
    outbox_path = agent.outbox_dir / f"{handle}.txt"
    outbox_path.write_text("Test result from agent")
    
    # Check finished
    assert await agent.is_finished(handle) is True
    assert "complete" in agent.get_status_description(handle).lower()
    
    # Get result
    result = await agent.get_result(handle)
    assert result["success"] is True
    assert result["result"] == "Test result from agent"
    
    # Cleanup
    (agent.inbox_dir / f"{handle}.txt").unlink()
    outbox_path.unlink()

@pytest.mark.asyncio
async def test_wait_for_agent_timeout():
    agent = CLIAgent()
    res = await agent.send_prompt("Timeout test")
    handle = res["handle"]
    
    # Run workflow with wait_for_agent
    steps = [
        {"action_type": "wait_for_agent", "payload": {"agent_name": "cli_agent", "handle": handle, "timeout": 2}}
    ]
    
    res = await run_chained_workflow(steps, overall_timeout=10)
    
    assert res["success"] is False
    assert "timed out waiting" in res["error"]
    
    # Cleanup
    (agent.inbox_dir / f"{handle}.txt").unlink()
