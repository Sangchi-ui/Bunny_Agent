# Bunny - Part 14 (Execution Verification)

Bunny now supports **Execution Verification**. Every time a tool or action executes and claims it succeeded, an independent verification layer inspects the *actual* system state to verify the claim.

## The Principle: Execution Result vs. Verified Result

Previously, Bunny trusted the return value of its own internal tools. If `write_file` returned `{"success": True}`, Bunny confidently updated the task to `DONE` and told the user it succeeded.

Now, a second, fully independent check runs immediately after execution. If the verification fails, the task's final status is downgraded to `FAILED`, and the AI model is explicitly instructed to communicate this discrepancy to the user. This ensures Bunny *never* hallucinates or falsely reports success when a system error, missing permission, or edge-case failure occurred silently.

## Verification Matrix

Here is how each action type is independently verified in Bunny:

| Action Type | Verification Logic |
| :--- | :--- |
| `create_file` | Independently checks `pathlib.Path(path).exists()` to ensure the file was actually written to disk. |
| `write_file` | Checks that the file exists *and* reads its contents to ensure the written text is actually present in the file. |
| `delete_file` | Checks `pathlib.Path(path).exists()` to ensure the file is completely gone from the disk. |
| `rename_file` / `move_file` | Checks that the old source path is gone *and* the new destination path exists. |
| `run_command` | Checks `exit_code == 0`. Additionally, parses `stdout`. For example, if it's a `pytest` command, it actively scans for "passed" and ensures "failed" or "error" do not appear in the logs (since some test suites exit 0 even on failure). |
| `delegate_to_agent` | Re-checks that the specific UUID `inbox` file exists in the sandbox. |
| `open_app` *(Planned)* | Will independently check via `psutil.process_iter()` that the requested executable is actually running in memory. |
| **Observation Actions** | `get_cpu_usage`, `list_files`, `read_file`, `check_task_status`, etc. These actions do not mutate state, so they are trivially marked as `verified = True` since their execution *is* the verification. |
