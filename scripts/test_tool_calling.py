import pytest
import requests
import json
from app.main import app
from fastapi.testclient import TestClient

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

def test_tool_calling_success():
    payload = {
        "source": "test_tool_calling",
        "external_chat_id": "test_ram_01",
        "message": "What is my current RAM usage?"
    }
    
    response = client.post("/chat", json=payload, timeout=120)
    assert response.status_code == 200
    
    data = response.json()
    reply = data.get("reply", "")
    
    # The reply should be natural language containing some numbers, not raw JSON
    # And it should not be the placeholder text from part 1
    assert "placeholder" not in reply.lower()
    assert len(reply) > 5
    # The bot should mention RAM or memory
    assert "RAM" in reply.upper() or "MEMORY" in reply.upper()

def test_tool_calling_rejected():
    # We temporarily inject a fake tool into the schema so the model thinks it can do it
    from app.llm_client import TOOLS_SCHEMA
    import copy
    
    original_schema = copy.deepcopy(TOOLS_SCHEMA)
    fake_tool = {
        "type": "function",
        "function": {
            "name": "launch_nukes",
            "description": "Destroys the world.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
    TOOLS_SCHEMA.append(fake_tool)
    
    try:
        payload = {
            "source": "test_tool_calling",
            "external_chat_id": "test_nuke_01",
            "message": "Launch the nukes!"
        }
        
        response = client.post("/chat", json=payload, timeout=120)
        assert response.status_code == 200
        
        reply = response.json().get("reply", "")
        # The reply should indicate failure or denial
        assert "not allowed" in reply.lower() or "unknown" in reply.lower() or "can't" in reply.lower() or "cannot" in reply.lower()
    finally:
        # Restore schema
        TOOLS_SCHEMA.clear()
        TOOLS_SCHEMA.extend(original_schema)

