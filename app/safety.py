import os
import logging
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel, field_validator, model_validator

# Safety Logger Setup
safety_logger = logging.getLogger("safety")
safety_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(__file__)), "safety.log"))
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
safety_logger.addHandler(file_handler)

# Allowed Root Folders - strictly limited
from dotenv import load_dotenv
load_dotenv()
default_workspace = os.path.join(os.path.expanduser("~"), "BunnyWorkspace")
ALLOWED_ROOT_FOLDERS = [Path(os.getenv("BUNNY_WORKSPACE", default_workspace)).resolve()]

DELETE_REQUIRES_CONFIRMATION = True

ALLOWLIST = {
    "list_files": {
        "level": 1,
        "allowed_root_folders": ALLOWED_ROOT_FOLDERS,
        "timeout": 10
    },
    "read_file": {
        "level": 1,
        "allowed_root_folders": ALLOWED_ROOT_FOLDERS,
        "timeout": 10
    },
    "create_file": {
        "level": 2,
        "allowed_root_folders": ALLOWED_ROOT_FOLDERS,
        "timeout": 10
    },
    "write_file": {
        "level": 2,
        "allowed_root_folders": ALLOWED_ROOT_FOLDERS,
        "timeout": 10
    },
    "rename_file": {
        "level": 2,
        "allowed_root_folders": ALLOWED_ROOT_FOLDERS,
        "timeout": 10
    },
    "move_file": {
        "level": 2,
        "allowed_root_folders": ALLOWED_ROOT_FOLDERS,
        "timeout": 10
    },
    "delete_file": {
        "level": 2,
        "allowed_root_folders": ALLOWED_ROOT_FOLDERS,
        "timeout": 10
    },
    "run_command": {
        "level": 2,
        "allowed_commands": ["pytest", "npm", "git", "python", "uvicorn", "node"],
        "allowed_root_folders": ALLOWED_ROOT_FOLDERS,
        "timeout": 120
    },
    "get_cpu_usage": {"level": 1, "timeout": 10},
    "get_ram_usage": {"level": 1, "timeout": 10},
    "get_disk_usage": {"level": 1, "timeout": 10},
    "get_gpu_usage": {"level": 1, "timeout": 10},
    "get_top_processes": {"level": 1, "timeout": 10},
    "get_network_status": {"level": 1, "timeout": 10},
    "check_task_status": {"level": 1, "timeout": 10},
    "simulate_slow_task": {"level": 1, "timeout": 300}
}

class ActionRequest(BaseModel):
    action_type: str
    level: int
    payload: Dict[str, Any]

    @field_validator('level')
    @classmethod
    def check_level(cls, v: int) -> int:
        if v not in (1, 2):
            raise ValueError("Level must be exactly 1 or 2. Level 3 or arbitrary levels are strictly forbidden.")
        return v

class ValidationResult(BaseModel):
    allowed: bool
    reason: str

def validate_action(request: ActionRequest) -> ValidationResult:
    # 1. Level Check (redundant fallback to pydantic validation, ensures no bypass)
    if request.level not in (1, 2):
        return _log_and_return(False, request, f"Level {request.level} is strictly forbidden.")

    # 2. Action Type Check
    if request.action_type not in ALLOWLIST:
        return _log_and_return(False, request, f"Action type '{request.action_type}' is not in ALLOWLIST.")
    
    rules = ALLOWLIST[request.action_type]
    
    # 3. Mismatch between request level and allowed level
    if request.level != rules["level"]:
        return _log_and_return(False, request, f"Requested level {request.level} does not match allowed level {rules['level']} for action '{request.action_type}'.")

    # 4. File Path Checks
    if "allowed_root_folders" in rules:
        found_path = False
        for key in ["path", "old_path", "new_path", "src", "dest", "folder", "cwd"]:
            if key in request.payload:
                found_path = True
                target_path_str = request.payload[key]
                try:
                    # Resolve to absolute real path (resolves symlinks and ../)
                    target_path = Path(target_path_str).resolve()
                    
                    # Check if target_path starts with any of the allowed roots
                    is_inside_root = False
                    for root in rules["allowed_root_folders"]:
                        root_path = Path(root).resolve()
                        if target_path.is_relative_to(root_path):
                            is_inside_root = True
                            break
                    
                    if not is_inside_root:
                        return _log_and_return(False, request, f"Path '{target_path_str}' is outside allowed root folders.")
                        
                except Exception as e:
                    return _log_and_return(False, request, f"Path resolution failed: {e}")
        
        if not found_path:
            return _log_and_return(False, request, "Payload missing a valid path parameter for file action.")

    # 5. Command Checks
    if "allowed_commands" in rules:
        command = request.payload.get("command")
        if not command:
            return _log_and_return(False, request, "Payload missing 'command' for command action.")
            
        if command not in rules["allowed_commands"]:
            return _log_and_return(False, request, f"Command '{command}' is not in ALLOWED_COMMANDS.")

        # Check args for shell metacharacters
        args = request.payload.get("args", [])
        if not isinstance(args, list):
            return _log_and_return(False, request, "Command args must be a list of strings.")
            
        metachars = [";", "&", "|", ">", "<", "`", "$("]
        for arg in args:
            for mc in metachars:
                if mc in str(arg):
                    return _log_and_return(False, request, f"Shell metacharacter '{mc}' is forbidden in args.")

    # Passed all checks
    return _log_and_return(True, request, "Action validated and allowed.")

def _log_and_return(allowed: bool, request: ActionRequest, reason: str) -> ValidationResult:
    result = "ALLOWED" if allowed else "DENIED"
    safety_logger.info(f"[{result}] action={request.action_type} level={request.level} | Reason: {reason}")
    return ValidationResult(allowed=allowed, reason=reason)
