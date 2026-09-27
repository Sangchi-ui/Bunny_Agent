# Bunny - Part 12 (Workflows & Waiting)

Bunny now supports **Chained Workflows** and **Wait Conditions**. This solves the issue of the LLM orchestrating long sequences of actions over multiple conversation turns.

## Concepts

### 1. Standalone Tasks vs. Workflows
- **Standalone Task (Part 8/9):** A single action (like `run_command` or `create_file`) submitted to the async task runner. Once it finishes, it's DONE. 
- **Workflow:** An ordered sequence of steps. The workflow *itself* is a background task (meaning you can query its status with `check_task_status`). If any step in the workflow fails or times out, the entire workflow is marked FAILED.

### 2. Wait Conditions
The new `app/waiting.py` module introduces a generic `WaitCondition` interface. Currently supported conditions:
- **TaskDoneCondition**: Wait for a specific background task ID to reach a terminal state (`DONE`, `FAILED`, `BLOCKED`).
- **FileExistsCondition**: Wait for a file to appear (validates against the sandbox boundary exactly like `read_file`!).
- **ProcessRunningCondition**: Poll for a system process via `psutil`.

### 3. Execution & Safety
When Bunny calls the `run_workflow` tool, it provides an array of steps. These steps are executed sequentially by `run_chained_workflow`. 
**Crucially, every single step is re-validated through `safety.validate_action` at execution time.** Being part of a workflow does not grant an action immunity from sandbox constraints or shell metacharacter checks.

### 4. Timeouts at Every Layer
To ensure maximum safety and to prevent hanging background workers, timeouts are enforced aggressively at three levels:
1. **Step Timeout:** Individual actions have timeouts (e.g. `run_command` defaults to 120s, file tools to 10s).
2. **Wait Timeout:** Wait conditions default to 600s.
3. **Workflow Timeout:** The entire `run_workflow` task has an absolute upper bound of 3600 seconds (1 hour). If the sum of all steps exceeds this, the workflow aborts.
