# Bunny - A Local AI Agent Framework

Bunny is a fully autonomous, self-hosted, local AI agent built with FastAPI, Python, and LM Studio. It is designed to act as your personal AI assistant, capable of reasoning, calling tools, persisting tasks, delegating to sub-agents, and managing sandboxed background operations securely on your laptop.

Bunny comes with a Telegram Bot interface for remote mobile access and a Local Web Dashboard for direct laptop use.

## Core Features

- **Autonomous Tool Calling**: Bunny can execute system tools like `read_file`, `write_file`, `run_command`, `list_files`, and `get_cpu_usage` to solve complex problems independently.
- **Asynchronous Task Runner**: Long-running commands (like `npm install` or testing scripts) are offloaded to a background task runner, allowing Bunny to continue communicating with you without hanging.
- **Agent Delegation**: Bunny acts as an orchestrator and can spin up sub-agents (e.g., `cli_agent`) using a secure file-based handoff mechanism to distribute work.
- **Workflow & Waiting Engine**: Bunny can chain commands sequentially, waiting for tasks or agents to finish before executing the next logical step.
- **Persistent Memory**: Uses SQLite to persist conversation histories, task statuses, and execution results. Tasks survive application restarts.

## Security & Hardening

Security is a primary design focus of Bunny. Since it has access to local shell execution, multiple layers of defense are built-in:

- **Strict Path Sandboxing**: All file tools (`read_file`, `write_file`, etc.) and `run_command` are strictly locked to a single `BunnyWorkspace` root folder. Attempts to path-traverse (`../`) are intercepted and rejected.
- **Command Allowlisting**: Only explicitly allowed CLI executables (e.g., `pytest`, `npm`, `python`, `git`) are permitted. Arbitrary system commands (`rm -rf`) are rejected.
- **Shell Metacharacter Blocking**: Bunny validates all arguments for shell injection characters (`;&|><`) to prevent command smuggling.
- **Execution Verification**: If a tool claims to have succeeded (e.g., "created a file"), an independent verification layer re-checks the disk or output logs to confirm the execution *actually* happened before telling you it did.
- **Centralized Auditing**: All tool actions and safety validations (`[ALLOWED]`/`[DENIED]`) are logged in a rotating `bunny_activity.log` file.
- **Telegram Authentication**: The Telegram bot strictly enforces `ALLOWED_TELEGRAM_CHAT_ID`, rejecting adversarial messages before they ever touch the LLM or execution engine.

## Getting Started

### Prerequisites
- Python 3.10+
- LM Studio (running a local model with a tool-calling capable LLM like Llama-3-Instruct or Qwen)
- A Telegram Bot Token (from BotFather)

### Setup
1. Clone the repository and set up a virtual environment:
   ```bash
   python -m venv venv
   # Windows: venv\Scripts\activate
   # Mac/Linux: source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Create a `.env` file in the root directory:
   ```env
   TELEGRAM_BOT_TOKEN="your_bot_token_here"
   ALLOWED_TELEGRAM_CHAT_ID="your_chat_id_here"
   BUNNY_WORKSPACE="C:/Users/YourUser/BunnyWorkspace" # Optional, defaults to ~/BunnyWorkspace
   ```
3. Start the LM Studio Local Inference Server on `http://127.0.0.1:1234` (ensure structured JSON/Tool Calling is supported by your model).

### Running Bunny
You need to run two components side-by-side:

**1. The Backend (FastAPI + Task Runner)**
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
*This starts the API, SQLite database connection, task runner, and the Local Web Dashboard.*

**2. The Telegram Bot (Optional, for remote access)**
```bash
python app/telegram_bot.py
```
*This starts long-polling for your Telegram messages.*

## Interfaces

### 1. Telegram Bot
Open your Telegram app and message the bot you created with BotFather. This is fully integrated and perfect for on-the-go requests.

### 2. Local Web Dashboard
If you are at your computer, open your browser and go to:
`http://127.0.0.1:8000/dashboard`
*Note: The Dashboard and Telegram maintain separate conversation histories, but share the exact same underlying brain, task runner, and sandbox environment.*

## Project History (Milestones)

This project was built incrementally. You can find detailed development documentation for each phase in the `docs/` folder:
- **Part 1:** FastAPI + SQLite Backend
- **Part 2:** LM Studio LLM Client Integration
- **Part 3:** Telegram Bot Interface
- **Part 4:** Integration Testing
- **Part 5:** Safety Validator & Allowlist
- **Part 6:** System Monitoring Tools
- **Part 7:** Tool-Calling Engine
- **Part 8:** Persistent Task Engine
- **Part 9:** Async Background Task Runner
- **Part 10:** Sandboxed File Operations
- **Part 11:** Sandboxed Dev Command Execution
- **Part 12:** Waiting & Workflow Engine
- **Part 13:** Multi-Agent Delegation
- **Part 14:** Execution Verification Layer
- **Part 15:** Local Web Dashboard UI
- **Part 16:** Hardening, Auditing & Stress Testing
