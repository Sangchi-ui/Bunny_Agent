# Bunny - Part 5 (Safety & Permission Layer)

This module (`app/safety.py`) introduces the most critical security boundary for Bunny. It ensures that the AI cannot indiscriminately run commands or access files on your host system.

## Principle: AI Proposes, Code Disposes
The core architectural principle of this system is that the LLM **never executes anything directly**. 
Instead, the LLM outputs a structured *proposal* for an action. That proposal is immediately handed to a deterministic Python function (`validate_action`) which acts as the ultimate gatekeeper. 

If the proposed action doesn't meet the strict parameters defined in the `ALLOWLIST`, the request is instantaneously denied, logged, and prevented from executing. The LLM cannot bypass this logic using prompt injection or clever phrasing because the code executes completely independent of the AI.

## How to Add a New Allowed Action
This file is designed so that expanding the agent's capabilities is safe and deliberate. To add a new allowed action:
1. Open `app/safety.py`.
2. Locate the `ALLOWLIST` dictionary at the top of the file.
3. Add a new key for your action (e.g., `"new_action_name"`).
4. Define its level (`1` or `2`) and explicit rules (e.g., `"allowed_root_folders": [BUNNY_ROOT]` or specific `"allowed_commands"`).
5. **Never** bypass the `validate_action` check.

## Zero Dependencies
`app/safety.py` is entirely standalone. It has absolutely zero dependencies on FastAPI, Telegram, LM Studio, or any network connections. This independent design ensures that it can be rigorously unit tested (see `test_safety.py`) without needing to mock up fake network servers or databases. 
