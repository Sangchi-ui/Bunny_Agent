# Bunny - Part 11 (Command Execution)

Bunny is now capable of running real developer commands like running your test suite, starting up node scripts, or pulling down git repositories! Because command execution is the most dangerous capability an AI agent can possess, this has been built with an iron-clad multi-layer sandbox.

## Security Layers

### 1. The ALLOWED_COMMANDS List
Bunny is explicitly forbidden from running arbitrary executables. The configuration in `app/safety.py` defines exactly which binaries are permitted. 

**Currently allowed commands:**
- `pytest` - For running test suites
- `npm` - For package management and script running
- `node` - For executing JS scripts
- `git` - For version control operations
- `python` - For executing python scripts
- `uvicorn` - For starting python servers

**WARNING:** Never add generic shell interpreters (like `cmd`, `powershell`, `bash`, `sh`) to this list. Doing so completely bypasses all argument filtering, as the model could just pass malicious commands to the shell!

### 2. Shell Metacharacter Filtering
Even for allowed commands, Bunny's `validate_action` aggressively scans the argument list for shell metacharacters (`;`, `&`, `|`, `>`, `<`, `$()`, ``` ` ```). This ensures that a benign command like `python` cannot be manipulated into a command-injection chain (e.g. `python --version; rm -rf /`). 

### 3. Execution Boundary (No Shells)
We explicitly ban `shell=True`, `os.system()`, and `subprocess.run(str)` across this entire codebase. Commands are dispatched securely to the OS using `asyncio.create_subprocess_exec` via an arguments array. This bypasses the shell completely, ensuring arguments are parsed purely as data rather than executable statements.

### 4. Working Directory Sandbox
Any command Bunny runs is forced to execute *inside* the `BunnyWorkspace`. The `cwd` parameter is verified using `pathlib.resolve()` to intercept path traversal out of the folder.

### 5. Double Timeouts
All commands are wrapped in two timeout layers. `TaskRunner` guarantees the worker queue won't clog, but `dev_tools.py` will actively SIGKILL the subprocess itself if the command hangs or runs indefinitely without producing a prompt, ensuring no zombie processes are left behind on your machine.
