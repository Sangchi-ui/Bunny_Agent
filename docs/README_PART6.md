# Bunny - Part 6 (System Monitoring Capabilities)

This part adds the first suite of actual operational tools to Bunny. All of these tools are strictly **read-only**, Level 1 operations that allow Bunny to understand its environment without mutating any state.

## Available Monitoring Functions
All metrics are retrieved using `psutil` (and `GPUtil` for NVIDIA GPUs) and wrapped safely to ensure a single unavailable metric never crashes the agent. 

1. **`get_cpu_usage`**: Returns overall CPU utilization percentage and per-core utilization.
2. **`get_ram_usage`**: Returns total, used, and available RAM, plus the utilization percentage.
3. **`get_disk_usage`**: Returns total, used, and free disk space for a given path (defaults to `C:\`).
4. **`get_gpu_usage`**: Returns individual GPU loads, memory usage, and temperatures. Will gracefully report `available: False` if no GPU is found or GPUtil is missing.
5. **`get_top_processes`**: Returns the top N processes running on the machine, categorized by memory usage and CPU usage.
6. **`get_network_status`**: Returns whether the network is up and lists the active network interfaces.

## Strict Safety Isolation
This module explicitly honors the "AI proposes, Code disposes" architecture from Part 5. 
The tool logic resides in `app/tools/system_monitor.py`. However, nothing in the codebase is allowed to import this file directly except `app/tools/dispatcher.py`, which **hard-gates** every execution attempt through `safety.validate_action()`.

**Explicit Confirmation:** This entire suite only reads system state. It never writes to files, executes shell strings, or alters the OS state in any capacity. Furthermore, it operates perfectly fine under a standard, non-administrator Windows user account.

## How to Test Manually
Because we haven't yet built the LLM tool-calling loop (that's for a future part), a new `POST /tool` endpoint was added to the FastAPI server for manual verification. This ensures the tools work perfectly in isolation.

You can test them using the Swagger docs UI:
1. Ensure the FastAPI server is running (`uvicorn app.main:app --reload`).
2. Go to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
3. Expand `POST /tool` and click **Try it out**.
4. Use this payload (for example, to test CPU usage):
   ```json
   {
     "action_type": "get_cpu_usage",
     "payload": {}
   }
   ```
5. Click **Execute** and observe the live read-only system state returned from your machine!
