import urllib.request
import urllib.error
import json
import time

def print_result(step, status, message=""):
    color = "\033[92m" if status == "PASS" else "\033[91m"
    reset = "\033[0m"
    print(f"[{color}{status}{reset}] Step {step}: {message}")

def test_integration():
    print("Starting Bunny End-to-End Integration Tests...\n")
    all_passed = True
    
    # 1. FastAPI /health
    try:
        req = urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5)
        data = json.loads(req.read().decode('utf-8'))
        if data.get("status") == "ok":
            print_result(1, "PASS", "FastAPI server responds on /health")
        else:
            print_result(1, "FAIL", "FastAPI server responded but not with status='ok'")
            all_passed = False
    except Exception as e:
        print_result(1, "FAIL", f"FastAPI server /health failed: {e}")
        all_passed = False

    # 2. LM Studio check
    try:
        req = urllib.request.urlopen('http://localhost:1234/v1/models', timeout=5)
        req.read()
        print_result(2, "PASS", "LM Studio local server is reachable")
    except Exception as e:
        print_result(2, "FAIL", f"LM Studio local server is not reachable: {e}. Please start the local server in LM Studio.")
        all_passed = False

    if not all_passed:
        print("\nHalting tests because prerequisite servers are not reachable.")
        return

    # 3. POST /chat with a real question
    try:
        payload = json.dumps({"source": "integration_test", "external_chat_id": "test_001", "message": "Hi, are you a bunny?"}).encode('utf-8')
        req = urllib.request.Request('http://127.0.0.1:8000/chat', data=payload, headers={'Content-Type': 'application/json'}, method='POST')
        response = urllib.request.urlopen(req, timeout=70)
        chat_data = json.loads(response.read().decode('utf-8'))
        
        reply = chat_data.get("reply", "")
        if "placeholder reply" in reply.lower():
            print_result(3, "FAIL", "POST /chat returned the Part 1 placeholder text")
            all_passed = False
        elif not reply:
            print_result(3, "FAIL", "POST /chat returned empty reply")
            all_passed = False
        else:
            print_result(3, "PASS", "POST /chat returned a real reply from LM Studio")
            
        convo_id = chat_data.get("conversation_id")
    except Exception as e:
        print_result(3, "FAIL", f"POST /chat failed: {e}")
        all_passed = False
        convo_id = None

    # 4. GET /conversations/{id}/history
    if convo_id:
        try:
            req = urllib.request.urlopen(f'http://127.0.0.1:8000/conversations/{convo_id}/history', timeout=5)
            hist_data = json.loads(req.read().decode('utf-8'))
            messages = hist_data.get("messages", [])
            
            if len(messages) >= 2 and messages[-2]["role"] == "user" and messages[-1]["role"] == "assistant":
                print_result(4, "PASS", "Conversation history shows user message followed by assistant reply correctly")
            else:
                print_result(4, "FAIL", "History order or content is incorrect")
                all_passed = False
        except Exception as e:
            print_result(4, "FAIL", f"GET /history failed: {e}")
            all_passed = False

    # 5. Conversation ID stability
    try:
        payload2 = json.dumps({"source": "integration_test", "external_chat_id": "test_001", "message": "What did I just say?"}).encode('utf-8')
        req2 = urllib.request.Request('http://127.0.0.1:8000/chat', data=payload2, headers={'Content-Type': 'application/json'}, method='POST')
        response2 = urllib.request.urlopen(req2, timeout=70)
        chat_data2 = json.loads(response2.read().decode('utf-8'))
        
        convo_id2 = chat_data2.get("conversation_id")
        if convo_id2 == convo_id:
            print_result(5, "PASS", "Conversation ID is stable across multiple /chat calls")
        else:
            print_result(5, "FAIL", f"Conversation ID changed! First was {convo_id}, second was {convo_id2}")
            all_passed = False
    except Exception as e:
        print_result(5, "FAIL", f"Second POST /chat failed: {e}")
        all_passed = False

    print("\n--- Test Summary ---")
    if all_passed:
        print("All integration tests PASSED!")
    else:
        print("Some integration tests FAILED. Check the output above.")

if __name__ == "__main__":
    test_integration()
