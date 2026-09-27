import urllib.request, json, time, os

payload = {
    'source': 'manual_test', 
    'external_chat_id': 'sandbox_tester3', 
    'message': 'Use run_workflow to run the tests in the workspace using pytest and pipe the output to a file using the args ["--junitxml=result.xml"], then wait for that task to complete, and finally read the file result.xml. DO NOT give me the steps separately. Create ONE run_workflow that does the command, wait_for_task, and read_file.'
}
req = urllib.request.Request('http://127.0.0.1:8000/chat', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'}, method='POST')
print(f'\n--- USER: {payload["message"]} ---')
res = urllib.request.urlopen(req, timeout=120)
reply = json.loads(res.read())['reply']
print('--- BUNNY: ---')
print(reply)

import re
match = re.search(r'Task ID\(s\): (\d+)', reply)
if match:
    task_id = match.group(1)
    print(f'Waiting for async task {task_id} to finish...')
    time.sleep(10)
    
    payload['message'] = f'Use the check_task_status tool to get the actual result of task {task_id} and tell me what happened.'
    req = urllib.request.Request('http://127.0.0.1:8000/chat', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'}, method='POST')
    res = urllib.request.urlopen(req, timeout=120)
    print(f'\n--- USER: Use the check_task_status tool to get the actual result of task {task_id} and tell me what happened. ---')
    print('--- BUNNY: ---')
    print(json.loads(res.read())['reply'])
