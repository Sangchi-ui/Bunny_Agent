# Bunny - Part 9 (Async Task Runner)

This part transforms Bunny from a simple synchronous chatbot into a system capable of handling long-running, asynchronous operations without blocking your conversations!

## The `TaskRunner`
The new `TaskRunner` uses Python's built-in `asyncio.Queue` to manage background tasks.
- **Concurrency Limit**: It runs with a configurable concurrency limit (defaulting to 1). This ensures that heavy actions (like future dev commands or builds) do not overwhelm the host machine's resources by running concurrently.
- **Hard Timeouts**: Every task is submitted with a timeout (default 300 seconds). If a task hangs, it is automatically cancelled and marked as `FAILED`. No task will ever run indefinitely in the background and silently consume resources.
- **Resilience**: The runner intercepts exceptions and timeouts cleanly, ensuring that one bad task doesn't crash the entire worker loop.

## The Async Tool Flow
When you ask Bunny to perform an action that takes time, the flow changes:
1. The model proposes the tool call.
2. The backend intercepts it and, instead of running it synchronously and waiting, it inserts it into the `TaskRunner` queue.
3. The API *immediately* responds to the model with a temporary success state (e.g. "Task submitted and is RUNNING with ID X").
4. The model responds to *you*, telling you that the work has started in the background.
5. You can freely continue chatting with Bunny or ask for the task's status while the runner executes the operation asynchronously.

## Looking Forward
Currently, the runner is proven using a dummy `simulate_slow_task(seconds)` tool. In Part 10 and 11, this exact same runner architecture will be leveraged to safely run real shell commands, tests, and builds without blocking the Telegram bot!
