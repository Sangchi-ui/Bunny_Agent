# Bunny - Part 16 (Hardening & Auditing)

This is the final milestone for Bunny! We have successfully conducted an audit and stress test of the entire system (Parts 1–15) to ensure it is robust, secure, and production-ready for local use.

## 1. Centralized Logging
We've replaced the scattered `print` statements and ad-hoc log files (`safety.log`, `tool_calls.log`) with a robust centralized logging system using Python's built-in `logging` module.
- **Log File**: `bunny_activity.log` (rotating, max 5MB, keeps 3 backups).
- **What is logged**:
  - FastAPI server startup and shutdown.
  - Crash recovery interventions.
  - Every tool execution attempt and its payload.
  - Every safety validation decision (`[ALLOWED]` or `[DENIED]`) with reasons.
  - Every task status change in the database.
  - Telegram bot authorizations and rejections.

## 2. Crash Recovery
If the server crashes, is killed, or loses power while tasks are executing in the background (`RUNNING`), those tasks' in-memory processes are permanently lost.
- Upon next startup, Bunny queries the database for any tasks stuck in `RUNNING`.
- It marks them as `FAILED` with the result: `"Interrupted by server restart"`.
- This ensures the UI (Telegram or Dashboard) never hangs indefinitely waiting for a dead task, and the user receives closure.
- **Telegram Reconnection**: The `python-telegram-bot` uses `update_id` offset tracking. If the bot crashes while offline, the Telegram server queues messages for up to 24 hours. Upon restart, the bot fetches the unhandled messages seamlessly, ensuring zero message loss.

## 3. Stress Tests Conducted

### Telegram Authorization Stress Test
I ran `test_telegram_auth_stress.py` to ensure that messages from unauthorized chat IDs cannot execute commands.
**Results:**
```text
test_telegram_auth_stress.py::test_telegram_rejects_unauthorized_chat_id PASSED
```
*Conclusion*: The bot intercepts the `chat_id` at the very first step of `handle_message`. Even if an unauthorized user constructs a perfect JSON payload, the bot logs a warning and drops the message *before* forwarding it to the LLM or execution engine. The allowlist literally cannot be bypassed via message content.

### Level-3 Safety Boundary Stress Test
I ran `test_level3_stress.py` to assault the `validate_action` boundary with Level 3 escalation attempts, shell injections, and path traversals.
**Results:**
```text
test_level3_stress.py::test_rejects_level_3 PASSED                       
test_level3_stress.py::test_smuggle_command_via_args PASSED              
test_level3_stress.py::test_path_traversal_create_file PASSED            
test_level3_stress.py::test_path_traversal_read_file PASSED              
test_level3_stress.py::test_path_traversal_rename_file PASSED            
test_level3_stress.py::test_path_traversal_move_file PASSED              
test_level3_stress.py::test_path_traversal_list_files PASSED             
test_level3_stress.py::test_malicious_workflow PASSED                    
```
*Conclusion*: 
- `ActionRequest` leverages Pydantic to strictly reject `level=3` prior to reaching business logic.
- Shell metacharacters (`;&|><`) are strictly blocked in `run_command` args.
- `Path.resolve()` correctly prevents `../` path traversal attacks in all file operations, enforcing the `BUNNY_WORKSPACE` sandbox constraint.
- Multi-step workflows (`run_chained_workflow`) independently construct `ActionRequest`s and route them through `validate_action` *during execution*. If step 1 dynamically produces a malicious payload for step 2, step 2 is successfully blocked mid-workflow.

## 4. Cold Startup Checklist
To run Bunny cleanly from a cold start, follow this order:
1. **LM Studio**: Open LM Studio, load your model, and start the local server on port `1234`.
2. **FastAPI Backend**: Run `uvicorn app.main:app --host 127.0.0.1 --port 8000`. Watch the console for "Starting Bunny backend..." and "Crash recovery: Marked X stuck RUNNING tasks as FAILED."
3. **Telegram Bot**: Run `python app/telegram_bot.py`. Watch the console for "Starting Bunny Telegram bot polling..."

## 5. Honest Limitations
While Bunny is highly hardened for its specific use-case, it is not invincible. Here is an honest assessment of its current limitations:
- **Single-Machine Only**: The dashboard binds to `127.0.0.1`. Do not expose FastAPI to `0.0.0.0` on a public network, as there is no built-in API key auth on `/chat`.
- **Single-User Architecture**: While conversations are tracked separately, there is no true multi-tenant sandboxing. The Telegram user and Dashboard user share the same `BUNNY_WORKSPACE` directory.
- **No Cross-Device Sync**: The Dashboard and Telegram bot intentionally maintain separate conversation threads (`external_chat_id`). They do not sync UI message history.
- **Concurrency**: The async task runner (Part 9) processes tasks sequentially. It cannot run two long-running background tasks concurrently.
- **No Resource Limits**: Bunny does not enforce CPU or Memory limits on `run_command` (e.g. via cgroups or Docker). A malicious script inside the sandbox could theoretically consume all host memory (though Bunny's own execution is safe).
