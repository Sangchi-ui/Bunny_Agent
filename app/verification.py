import os
import psutil
from pathlib import Path
from typing import Dict, Any
from app.agents import get_agent

def verify_result(action_type: str, payload: dict, execution_result: dict) -> dict:
    """
    Independently verifies if an action actually succeeded by checking real system state.
    Returns the execution_result dict updated with "verified": bool and "verification_detail": str.
    """
    # If the execution already failed, verification is trivial
    if not execution_result.get("success", False):
        execution_result["verified"] = True
        execution_result["verification_detail"] = "Execution already failed, no state to verify."
        return execution_result

    verified = True
    detail = "Action verified successfully."

    try:
        if action_type in ["create_file", "write_file"]:
            path = Path(payload.get("path", "")).resolve()
            if not path.exists():
                verified = False
                detail = f"File {path} does not exist after creation/writing."
            elif action_type == "write_file":
                content = payload.get("content", "")
                actual_content = path.read_text(encoding="utf-8")
                if content not in actual_content:
                    verified = False
                    detail = f"File {path} exists, but content does not match what was written."

        elif action_type == "delete_file":
            path = Path(payload.get("path", "")).resolve()
            if path.exists():
                verified = False
                detail = f"File {path} still exists after deletion."

        elif action_type in ["rename_file", "move_file"]:
            source = Path(payload.get("source", "")).resolve()
            dest = Path(payload.get("destination", "")).resolve()
            if source.exists():
                verified = False
                detail = f"Source path {source} still exists."
            elif not dest.exists():
                verified = False
                detail = f"Destination path {dest} does not exist."

        elif action_type == "run_command":
            # Check exit code
            exit_code = execution_result.get("exit_code")
            stdout = execution_result.get("output", "")
            if exit_code != 0:
                verified = False
                detail = f"Command exited with non-zero code: {exit_code}."
            else:
                command = payload.get("command", "")
                # Specific verification for pytest
                if command == "pytest":
                    out_lower = stdout.lower()
                    if "failed" in out_lower or "error" in out_lower:
                        if "passed" not in out_lower or "failed" in out_lower:
                            verified = False
                            detail = "Command exited 0, but output contains test failures or errors."
                # Note: open_app is not yet implemented, will need psutil verification when it is.

        elif action_type == "delegate_to_agent":
            # Verify the inbox file was actually created by checking the handle
            handle = execution_result.get("handle")
            agent_name = payload.get("agent_name")
            agent = get_agent(agent_name)
            if agent and handle:
                inbox_path = agent._get_inbox_path(handle)
                if not inbox_path.exists():
                    verified = False
                    detail = f"Agent inbox file for handle {handle} does not exist."

        elif action_type in [
            "get_ram_usage", "get_cpu_usage", "get_top_processes", 
            "get_network_status", "read_file", "list_files", 
            "check_task_status", "simulate_slow_task", "wait_for_task",
            "check_agent_status", "wait_for_agent"
        ]:
            # Read-only or observation actions: data is trivially verified
            pass

        elif action_type == "run_workflow":
            # Workflow verification relies on individual step verification
            pass

    except Exception as e:
        verified = False
        detail = f"Verification logic threw an exception: {str(e)}"

    execution_result["verified"] = verified
    execution_result["verification_detail"] = detail
    
    # Override success if verification failed
    if not verified:
        execution_result["success"] = False
        execution_result["error"] = f"Verification failed: {detail}"

    return execution_result
