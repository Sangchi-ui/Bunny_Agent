import pytest
import json
from app.database import create_task, update_task_status, get_task, get_or_create_conversation
from app.main import app
from fastapi.testclient import TestClient
import requests

client = TestClient(app)

def is_lm_studio_available():
    try:
        res = requests.get("http://localhost:1234/v1/models", timeout=2)
        return res.status_code == 200
    except requests.exceptions.RequestException:
        return False

pytestmark = pytest.mark.skipif(
    not is_lm_studio_available(), 
    reason="LM Studio local server is not reachable on port 1234 or no model is loaded."
)

def test_task_lifecycle():
    conv_id = get_or_create_conversation("test_tasks", "task_user_01")
    
    # Create task
    task_id = create_task(conv_id, "Test task lifecycle", level=1)
    task = get_task(task_id)
    assert task["status"] == "PENDING"
    assert task["description"] == "Test task lifecycle"
    
    # Update to running
    update_task_status(task_id, "RUNNING")
    task = get_task(task_id)
    assert task["status"] == "RUNNING"
    
    # Update to done with result
    update_task_status(task_id, "DONE", result="Success result")
    task = get_task(task_id)
    assert task["status"] == "DONE"
    assert task["result"] == "Success result"

def test_create_task_level_3_rejected():
    conv_id = get_or_create_conversation("test_tasks", "task_user_01")
    with pytest.raises(ValueError) as exc:
        create_task(conv_id, "Dangerous task", level=3)
    assert "level must be 1 or 2" in str(exc.value).lower()

def test_tool_call_creates_task_row():
    # End to end check: use POST /chat endpoint to see if it creates a task.
    # We will get the current count of tasks for a new conversation, make a request, and check if it increased.
    conv_id = get_or_create_conversation("test_tasks", "task_user_03")
    
    # We can query /chat
    payload = {
        "source": "test_tasks",
        "external_chat_id": "task_user_03",
        "message": "What is my current RAM usage?"
    }
    
    response = client.post("/chat", json=payload, timeout=120)
    assert response.status_code == 200
    
    # Now check if tasks were created
    tasks_res = client.get(f"/conversations/{conv_id}/tasks")
    tasks = tasks_res.json()["tasks"]
    
    # There should be at least one task created for the RAM usage check
    assert len(tasks) >= 1
    
    # The status should be DONE (or FAILED if the tool errored, but it should have resolved)
    task = tasks[0]
    assert task["status"] in ("DONE", "FAILED")
    assert task["result"] is not None

def test_check_task_status_endpoint():
    conv_id = get_or_create_conversation("test_tasks", "task_user_02")
    task_id = create_task(conv_id, "Endpoint test", level=1)
    
    # Test GET /tasks/{task_id}
    res = client.get(f"/tasks/{task_id}")
    assert res.status_code == 200
    assert res.json()["task"]["id"] == task_id
    
    # Test GET /conversations/{conversation_id}/tasks
    res = client.get(f"/conversations/{conv_id}/tasks")
    assert res.status_code == 200
    assert len(res.json()["tasks"]) >= 1
    assert res.json()["tasks"][0]["id"] == task_id
