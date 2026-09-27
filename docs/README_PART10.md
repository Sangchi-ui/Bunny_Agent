# Bunny - Part 10 (Sandboxed File Operations)

Bunny now has the ability to read, create, modify, move, and delete files on your system! 
However, to ensure Bunny doesn't accidentally (or maliciously) touch critical system files, everything is executed within a strict sandbox.

## The BunnyWorkspace Sandbox
Bunny operates strictly within an `ALLOWED_ROOT_FOLDERS` configuration. 
By default, this resolves to `C:\Users\<your-user>\BunnyWorkspace`. 

### Setup Instructions
1. Create a folder named `BunnyWorkspace` in your home directory (`C:\Users\<your-user>\BunnyWorkspace`).
2. Alternatively, you can configure this by setting `BUNNY_WORKSPACE=/absolute/path/to/folder` in your `.env` file.

**Important Note:** Bunny can ONLY touch files inside this one folder. Any attempt by the model to read your Desktop, Documents, system files, or traverse backwards out of the workspace (`../`) will be intercepted and strictly denied by the `app/safety.py` validation logic. 

## The Delete Confirmation Flow
Deleting a file is a highly destructive action (Level 2). To prevent the AI from hallucinating a destructive command and instantly deleting a file before you can stop it, the `delete_file` tool uses a forced two-step confirmation flow.

If the model calls `delete_file`, the Python dispatcher will reject the first call and return a temporary `confirmation_token` with a 60-second expiry. The model must then explicitly use this token in a second call to actually perform the deletion.

## Background Execution
Because we built the `TaskRunner` in Part 9, any heavy file modifications (like creating, writing, moving, or renaming) are immediately pushed to the background async loop. You will never experience a frozen conversation while Bunny touches the disk!
