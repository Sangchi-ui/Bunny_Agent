import asyncio
import time
import psutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from app import database
from app.safety import ALLOWED_ROOT_FOLDERS
from app.tools import dispatcher

class WaitCondition:
    async def check(self) -> bool:
        raise NotImplementedError

class TaskDoneCondition(WaitCondition):
    def __init__(self, task_id: int):
        self.task_id = task_id
        
    async def check(self) -> bool:
        task = database.get_task(self.task_id)
        if not task:
            # If task doesn't exist, we can't wait for it
            return True
        return task["status"] in ("DONE", "FAILED", "BLOCKED")

class FileExistsCondition(WaitCondition):
    def __init__(self, path: str):
        self.path = path
        
    async def check(self) -> bool:
        # Validate sandbox boundary first
        try:
            target_path = Path(self.path).resolve()
            is_inside_root = False
            for root in ALLOWED_ROOT_FOLDERS:
                root_path = Path(root).resolve()
                if target_path.is_relative_to(root_path):
                    is_inside_root = True
                    break
            if not is_inside_root:
                return True # Stop waiting if invalid
                
            return target_path.exists()
        except Exception:
            return True # Stop waiting on error

class ProcessRunningCondition(WaitCondition):
    def __init__(self, name: str, expected_running: bool = True):
        self.name = name
        self.expected_running = expected_running
        
    async def check(self) -> bool:
        found = False
        for proc in psutil.process_iter(['name']):
            try:
                if self.name.lower() in proc.info['name'].lower():
                    found = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        return found == self.expected_running

class AgentDoneCondition(WaitCondition):
    def __init__(self, agent_name: str, handle: str):
        self.agent_name = agent_name
        self.handle = handle
        
    async def check(self) -> bool:
        from app.agents import get_agent
        agent = get_agent(self.agent_name)
        if not agent:
            return True # stop waiting if invalid agent
        try:
            return await agent.is_finished(self.handle)
        except Exception:
            return True

async def wait_for_condition(condition: WaitCondition, poll_interval: int = 5, timeout: int = 600) -> Dict[str, Any]:
    start_time = time.time()
    while True:
        if (time.time() - start_time) > timeout:
            return {"success": False, "error": "timed out waiting"}
            
        try:
            met = await condition.check()
            if met:
                return {"success": True, "met_at": time.time()}
        except Exception as e:
            return {"success": False, "error": f"Condition check failed: {str(e)}"}
            
        await asyncio.sleep(poll_interval)

async def run_chained_workflow(steps: List[Dict[str, Any]], overall_timeout: int = 3600) -> Dict[str, Any]:
    """
    Executes a list of action steps sequentially. 
    Each step must be a dict like {"action_type": str, "payload": dict}.
    """
    results = []
    start_time = time.time()
    
    for i, step in enumerate(steps):
        if (time.time() - start_time) > overall_timeout:
            return {"success": False, "error": f"Workflow overall timeout ({overall_timeout}s) exceeded at step {i}"}
            
        action_type = step.get("action_type")
        payload = step.get("payload", {})
        
        # If the step is an async tool or wait condition that takes a long time, we handle it
        if action_type == "wait_for_task":
            task_id = payload.get("task_id")
            timeout = payload.get("timeout", 60)
            if not task_id:
                return {"success": False, "error": f"Step {i} missing task_id for wait_for_task"}
            
            res = await wait_for_condition(TaskDoneCondition(task_id), timeout=timeout)
            if not res.get("success"):
                return {"success": False, "error": f"Step {i} wait_for_task failed: {res.get('error')}"}
            results.append({"step": i, "action": action_type, "result": res})
            continue
            
        if action_type == "wait_for_agent":
            agent_name = payload.get("agent_name")
            handle = payload.get("handle")
            timeout = payload.get("timeout", 600)
            
            if not agent_name or not handle:
                return {"success": False, "error": f"Step {i} missing agent_name or handle"}
                
            res = await wait_for_condition(AgentDoneCondition(agent_name, handle), timeout=timeout)
            if not res.get("success"):
                return {"success": False, "error": f"Step {i} wait_for_agent failed: {res.get('error')}"}
            results.append({"step": i, "action": action_type, "result": res})
            continue

        # For normal actions, we route through dispatcher
        # However, dispatcher.execute_tool is synchronous for file ops!
        # If it's run_command, we need to run it via dev_tools!
        # Because we're in the async worker context already, we can await if it's async, or use to_thread
        
        # We must manually invoke validation here just in case dispatcher doesn't (like for run_command)
        from app.safety import validate_action, ActionRequest, ALLOWLIST
        level = ALLOWLIST.get(action_type, {}).get("level", 1)
        req = ActionRequest(action_type=action_type, level=level, payload=payload)
        val = validate_action(req)
        
        if not val.allowed:
            return {"success": False, "error": f"Step {i} validation failed: {val.reason}", "results": results}
            
        if action_type == "run_command":
            from app.tools.dev_tools import run_command
            step_timeout = ALLOWLIST.get("run_command", {}).get("timeout", 120)
            res = await run_command(payload.get("command"), payload.get("args", []), payload.get("cwd"), timeout=step_timeout)
        elif action_type == "simulate_slow_task":
            from app.tools.test_tools import simulate_slow_task
            res = await simulate_slow_task(payload.get("seconds", 5))
        else:
            # Sync tools via dispatcher
            res = await asyncio.to_thread(dispatcher.execute_tool, action_type, payload)
            
        # Check success
        if isinstance(res, dict) and not res.get("success", True):
            return {"success": False, "error": f"Step {i} failed: {res.get('error')}", "results": results}
            
        results.append({"step": i, "action": action_type, "result": res})

    return {"success": True, "results": results}
