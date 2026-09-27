from typing import Dict, Any
from app.safety import validate_action, ActionRequest
from app.tools import system_monitor

def execute_tool(action_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely executes a tool by validating it first. 
    This is the only place tool functions should be called directly.
    """
    # 1. Create the request and validate
    # To determine the level, we look at the ALLOWLIST. But ActionRequest needs a level.
    # We can infer it from the safety module's ALLOWLIST if available, 
    # but the AI would propose a level. Here, for dispatching, we pull it from ALLOWLIST
    # or assume a default since the AI hasn't explicitly supplied it via this raw interface yet.
    # Let's import ALLOWLIST to check what level this action is *supposed* to be, 
    # to construct the strict ActionRequest.
    from app.safety import ALLOWLIST
    
    if action_type not in ALLOWLIST:
        return {"success": False, "error": f"Action type '{action_type}' is unknown or not allowed."}
        
    expected_level = ALLOWLIST[action_type].get("level", 1)
    
    try:
        request = ActionRequest(
            action_type=action_type,
            level=expected_level,
            payload=payload
        )
    except Exception as e:
        return {"success": False, "error": f"Invalid action format: {e}"}

    validation = validate_action(request)
    if not validation.allowed:
        return {"success": False, "error": validation.reason}

    # 2. Dispatch to the specific tool
    try:
        if action_type == "get_cpu_usage":
            result = system_monitor.get_cpu_usage()
        elif action_type == "get_ram_usage":
            result = system_monitor.get_ram_usage()
        elif action_type == "get_disk_usage":
            path = payload.get("path", "C:\\")
            result = system_monitor.get_disk_usage(path)
        elif action_type == "get_gpu_usage":
            result = system_monitor.get_gpu_usage()
        elif action_type == "get_top_processes":
            n = payload.get("n", 5)
            result = system_monitor.get_top_processes(n)
        elif action_type == "get_network_status":
            result = system_monitor.get_network_status()
        elif action_type == "check_task_status":
            task_id = payload.get("task_id")
            if task_id is None:
                return {"success": False, "error": "Missing task_id"}
            from app.tools import task_tools
            result = task_tools.get_task_status(task_id)
        
        # File tools
        elif action_type == "list_files":
            from app.tools import file_tools
            result = file_tools.list_files(payload.get("folder"))
        elif action_type == "read_file":
            from app.tools import file_tools
            result = file_tools.read_file(payload.get("path"), payload.get("max_bytes", 100_000))
        elif action_type == "create_file":
            from app.tools import file_tools
            result = file_tools.create_file(payload.get("path"), payload.get("content"))
        elif action_type == "write_file":
            from app.tools import file_tools
            result = file_tools.write_file(payload.get("path"), payload.get("content"), payload.get("mode", "overwrite"))
        elif action_type == "rename_file":
            from app.tools import file_tools
            result = file_tools.rename_file(payload.get("old_path"), payload.get("new_path"))
        elif action_type == "move_file":
            from app.tools import file_tools
            result = file_tools.move_file(payload.get("src"), payload.get("dest"))
        elif action_type == "delete_file":
            from app.tools import file_tools
            result = file_tools.delete_file(payload.get("path"), payload.get("confirmation_token"))
            
        else:
            result = {"success": False, "error": f"Dispatcher has no handler mapped for '{action_type}'."}
            
        from app.verification import verify_result
        return verify_result(action_type, payload, result)
        
    except Exception as e:
        return {"success": False, "error": f"Tool execution failed unexpectedly: {e}"}
