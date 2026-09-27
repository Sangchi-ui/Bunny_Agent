# Bunny - Part 1 (Backend Skeleton)

This is the first part of the Bunny local AI agent backend.

## What this part does
- Sets up the FastAPI server with SQLite database layer.
- Provides endpoints for health check, chat messages, and fetching chat history.
- Manages local persistence for conversations, messages, and tasks.

## What this part does NOT do
- No AI integration yet (placeholder replies are used).
- No Telegram or external connections.
- No system command execution.

## Windows Setup Steps
1. Make sure you have Python 3.11+ installed.
2. Open a terminal in this project folder (`bunny/`).
3. Create a virtual environment:
   ```cmd
   python -m venv venv
   ```
4. Activate the virtual environment:
   ```cmd
   venv\Scripts\activate
   ```
5. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   ```
6. Run the FastAPI server:
   ```cmd
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   *Note: The server is intentionally bound only to `127.0.0.1` to ensure it is not exposed to the network.*

## How to Test
1. Check the health endpoint by visiting: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
2. Open the interactive API documentation at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
3. Use the docs UI to try `POST /chat` (provide `source`, `external_chat_id`, and `message` in the request body).
4. Use the docs UI to try `GET /conversations/{id}/history` to see the conversation history for the ID returned from the chat endpoint.
