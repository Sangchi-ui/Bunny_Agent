# Bunny - Part 8 (Persistent Task State)

This part introduces an independent state management layer for tasks, giving Bunny a memory of actions that exists outside of conversational history.

## Why Store Tasks Separately?
Up to this point, the conversation history (`messages` table) was the only record of what happened. While this is fine for chat, it's terrible for managing long-running operations. By separating tasks into their own `tasks` table, Bunny gains the ability to:
- Track an action's lifecycle (`PENDING` -> `RUNNING` -> `DONE`/`FAILED`).
- Remember what it did, even if the conversation history is truncated to save tokens.
- Allow you to query the status of a specific task at a later time (e.g., "What was the result of task 5?"), even from entirely different clients or endpoints.

## Instant Resolution (For Now)
Currently, Bunny only has Level 1 read-only system monitoring tools. These operations are incredibly fast and execute completely synchronously. As a result, when you trigger a tool, you'll see its task transition instantly from `RUNNING` directly to `DONE`.

The true power of this persistent `tasks` table will emerge in Part 9 (when we introduce an asynchronous runner) and Part 11 (when we introduce real developer commands that take time to complete). The persistent task architecture guarantees Bunny won't block or crash if an action takes 20 minutes to finish!

## New Endpoints
You can now check the tasks manually:
- `GET /tasks/{task_id}`
- `GET /conversations/{conversation_id}/tasks`

Or you can just ask Bunny! The LLM now has access to the `check_task_status` tool. 
