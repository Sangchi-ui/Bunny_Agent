# Bunny - Part 15 (Local Web Dashboard)

Bunny now comes with a local, single-page web dashboard! This allows you to interact with Bunny directly from your laptop's browser without needing Telegram.

## How to Access
1. Start the FastAPI server as usual (`uvicorn app.main:app --reload --host 127.0.0.1`)
2. Open your web browser and navigate to: `http://127.0.0.1:8000/dashboard`

## Security and Scope
This dashboard is intentionally **local-only**. It binds to `127.0.0.1` and is not exposed to the public internet. It is meant to be used when you are sitting physically at the host machine. If you want remote access to Bunny, use the Telegram integration (Part 3).

## Conversation Architecture
The dashboard and Telegram operate as **two separate conversations**.
- They use different `external_chat_id`s in the backend. 
- A message sent on Telegram will not appear in the dashboard's chat log, and vice versa.

However, **they share the exact same underlying Bunny brain and tools**:
- Same SQLite database (including the unified `tasks` table!)
- Same tool-calling capabilities (Part 7)
- Same file operation sandboxing (Part 10)
- Same execution verification checks (Part 14)

If you ask "What's my RAM usage?" on the dashboard, Bunny will use the exact same logic as if you asked it on Telegram. The task will even appear in the dashboard's live task list.
