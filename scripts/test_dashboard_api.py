import urllib.request, json, time

print("1. Initializing Dashboard Conversation...")
init_req = urllib.request.Request('http://127.0.0.1:8000/dashboard/init?source=dashboard&external_chat_id=local')
init_res = urllib.request.urlopen(init_req, timeout=10)
init_data = json.loads(init_res.read())
conv_id = init_data['conversation_id']
print(f"Conversation ID: {conv_id}")

print("\n2. Sending Prompt: 'what's my RAM usage'")
chat_payload = {
    'source': 'dashboard',
    'external_chat_id': 'local',
    'message': "what's my RAM usage"
}
chat_req = urllib.request.Request('http://127.0.0.1:8000/chat', data=json.dumps(chat_payload).encode(), headers={'Content-Type': 'application/json'}, method='POST')
chat_res = urllib.request.urlopen(chat_req, timeout=120)
chat_data = json.loads(chat_res.read())
print(f"Bunny Reply: {chat_data['reply']}")

print("\n3. Polling Task List...")
tasks_req = urllib.request.Request(f'http://127.0.0.1:8000/conversations/{conv_id}/tasks')
tasks_res = urllib.request.urlopen(tasks_req, timeout=10)
tasks_data = json.loads(tasks_res.read())

for t in tasks_data['tasks']:
    print(f"Task #{t['id']} | Status: {t['status']} | Description: {t['description']}")
    if t['result']:
        print(f"  Result: {t['result'][:100]}...")
