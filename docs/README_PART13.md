# Bunny - Part 13 (Agent Delegation)

Bunny is now capable of delegating complex or specialized work to *external* agents (such as an external coding agent or long-running CLI process) and natively tracking their completion status inside the workflow engine.

## Mechanism & Sandbox Safety

To maintain the strict security guarantees of Part 10 and Part 11, agent delegation is currently implemented via **File Exchange** rather than process manipulation. Bunny does *not* directly launch or control external agents. 

Instead, communication happens through designated folders within the `BunnyWorkspace` sandbox:

1. **Inbox (`BunnyWorkspace/agent_inbox/`)**: When Bunny delegates a task, it writes the prompt/instructions to a `.txt` file here, named with a unique UUID handle.
2. **Outbox (`BunnyWorkspace/agent_outbox/`)**: Bunny then polls this directory. When the external agent completes the task, it must write its response to a `.txt` file with the *exact same handle*. 

This file-based approach ensures no new vectors for command injection or out-of-bounds file access are introduced.

## Supported Agents

Currently, only one agent wrapper is supported:
- **`cli_agent`**: The generic file-exchange agent described above.

*Attempting to delegate to an unknown agent name will be immediately blocked by the `safety.py` validator.*

## New LLM Tools

The model has been equipped with two new tools to manage this:
1. `delegate_to_agent`: Dispatches the task and returns a `handle`.
2. `check_agent_status`: Synchronously queries if the agent has placed a response in the outbox.

## Workflow Integration

Delegation integrates seamlessly into Part 12's workflows via the `wait_for_agent` action. This allows Bunny to create chained workflows like:
1. Delegate coding task to `cli_agent`
2. `wait_for_agent` (pauses the workflow until the external agent responds)
3. `run_command` (run tests on the newly written code)
