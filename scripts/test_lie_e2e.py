import urllib.request, json, time, re
from app.safety import ALLOWED_ROOT_FOLDERS

target_file = ALLOWED_ROOT_FOLDERS[0] / "test_lie.txt"
if target_file.exists():
    target_file.unlink()

payload = {
    'source': 'manual_test', 
    'external_chat_id': 'tester99', 
    'message': f'Please create a file at {target_file} with content "test". Do not write_file, only use create_file tool.'
}
req = urllib.request.Request('http://127.0.0.1:8000/chat', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'}, method='POST')
print(f'\n--- USER: {payload["message"]} ---')
res = urllib.request.urlopen(req, timeout=120)
reply = json.loads(res.read())['reply']
print('--- BUNNY: ---')
print(reply)

match = re.search(r'Task ID\(s\): (\d+)', reply)
if match:
    task_id = match.group(1)
    print(f'Waiting for async task {task_id} to finish...')
    time.sleep(2)
    
    payload['message'] = f'Use the check_task_status tool to get the actual result of task {task_id} and tell me what happened.'
    req = urllib.request.Request('http://127.0.0.1:8000/chat', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'}, method='POST')
    res = urllib.request.urlopen(req, timeout=120)
    print(f'\n--- USER: {payload["message"]} ---')
    print('--- BUNNY: ---')
    print(json.loads(res.read())['reply'])
