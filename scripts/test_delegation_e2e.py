import urllib.request, json, time, re, os
from pathlib import Path
from app.safety import ALLOWED_ROOT_FOLDERS

# 1. Clear agent inbox so we only have one file
inbox_dir = ALLOWED_ROOT_FOLDERS[0] / "agent_inbox"
inbox_dir.mkdir(parents=True, exist_ok=True)
for f in inbox_dir.glob("*.txt"):
    f.unlink()

payload = {
    'source': 'manual_test', 
    'external_chat_id': 'sandbox_tester4', 
    'message': 'Please use the delegate_to_agent tool to ask the cli_agent to "Write a quick hello world script". Give me the handle you get back.'
}
req = urllib.request.Request('http://127.0.0.1:8000/chat', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'}, method='POST')
print(f'\n--- USER: {payload["message"]} ---')
res = urllib.request.urlopen(req, timeout=120)
reply = json.loads(res.read())['reply']
print('--- BUNNY: ---')
print(reply)

# 2. Give background worker a second to write the file
time.sleep(2)

# 3. Find the handle in the inbox
files = list(inbox_dir.glob("*.txt"))
if files:
    handle = files[0].stem
    print(f"\n[System: Found handle {handle} in inbox]")
    
    # Simulate external agent completing task
    outbox_dir = ALLOWED_ROOT_FOLDERS[0] / "agent_outbox"
    outbox_dir.mkdir(parents=True, exist_ok=True)
    outbox_file = outbox_dir / f"{handle}.txt"
    
    print(f'[System: Writing fake response to {outbox_file}]')
    outbox_file.write_text("print('Hello from the fake external CLI agent!')", encoding="utf-8")
    
    # Ask if finished
    payload['message'] = f'Has my agent finished? The handle is {handle}. If so, get the result.'
    req = urllib.request.Request('http://127.0.0.1:8000/chat', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'}, method='POST')
    res = urllib.request.urlopen(req, timeout=120)
    print(f'\n--- USER: {payload["message"]} ---')
    reply = json.loads(res.read())['reply']
    print('--- BUNNY: ---')
    print(reply)
    
    match = re.search(r'Task ID\(s\): (\d+)', reply)
    if match:
        task_id = match.group(1)
        print(f'Waiting for async task {task_id} to finish...')
        time.sleep(5)
        
        payload['message'] = f'Use the check_task_status tool to get the actual result of task {task_id} and tell me what happened.'
        req = urllib.request.Request('http://127.0.0.1:8000/chat', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'}, method='POST')
        res = urllib.request.urlopen(req, timeout=120)
        print(f'\n--- USER: {payload["message"]} ---')
        print('--- BUNNY: ---')
        print(json.loads(res.read())['reply'])

else:
    print("\n[System: Failed to find file in inbox. Delegation failed.]")
