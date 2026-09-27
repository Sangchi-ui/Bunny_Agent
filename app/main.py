from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

import os
import json
import logging
from app import database, llm_client, safety
from app.tools import dispatcher, test_tools
from app.task_runner import runner

@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    await runner.start()
    yield
    await runner.stop()

app = FastAPI(lifespan=lifespan)

tool_logger = logging.getLogger("tools")
tool_logger.setLevel(logging.INFO)
th = logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(__file__)), "tool_calls.log"))
th.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
tool_logger.addHandler(th)

class ChatRequest(BaseModel):
    source: str
    external_chat_id: str
    message: str

class ToolRequest(BaseModel):
    action_type: str
    payload: Dict[str, Any] = {}

@app.get("/health")
def health():
    return {"status": "ok", "message": "Bunny backend is running."}

@app.post("/chat")
def chat(request: ChatRequest):
    conversation_id = database.get_or_create_conversation(request.source, request.external_chat_id)
    database.add_message(conversation_id, "user", request.message)
    
    recent_db_messages = database.get_recent_messages(conversation_id, limit=10)
    messages = [{"role": m["role"], "content": m["content"]} for m in recent_db_messages]
    
    reply_msg = llm_client.get_completion(messages)
    reply_msg_original = reply_msg
    
    if "tool_calls" in reply_msg and reply_msg["tool_calls"]:
        messages.append(reply_msg)
        
        executed_task_ids = []
        
        for tool_call in reply_msg["tool_calls"]:
            func_name = tool_call["function"]["name"]
            try:
                payload = json.loads(tool_call["function"]["arguments"])
            except Exception:
                payload = {}
                
            tool_logger.info(f"Model attempting tool call: {func_name} with payload: {payload}")
            
            # Create task
            from app.safety import ALLOWLIST
            level = ALLOWLIST.get(func_name, {}).get("level", 1)
            timeout = ALLOWLIST.get(func_name, {}).get("timeout", 300)
            try:
                task_id = database.create_task(conversation_id, f"Execute {func_name}", level)
            except Exception as e:
                tool_logger.error(f"Task creation failed: {e}")
                task_id = None
                
            # Validating safety synchronously before we do anything
            request_obj = safety.ActionRequest(action_type=func_name, level=level, payload=payload)
            validation = safety.validate_action(request_obj)
            if not validation.allowed:
                result = {"success": False, "error": f"Safety validation failed: {validation.reason}"}
                if task_id:
                    database.update_task_status(task_id, "FAILED", result=str(result["error"]))
                    executed_task_ids.append(task_id)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id", "call_123"),
                    "name": func_name,
                    "content": json.dumps(result)
                })
                continue
            
            ASYNC_TOOLS = [
                "simulate_slow_task", "create_file", "write_file", "rename_file", 
                "move_file", "delete_file", "run_command", "wait_for_task", 
                "run_workflow", "delegate_to_agent", "wait_for_agent", "check_agent_status"
            ]
            
            if func_name in ASYNC_TOOLS:
                if task_id:
                    # Submit to background runner with verification
                    
                    def wrap_verify(a_type, coro_fn):
                        async def _wrapper():
                            from app.verification import verify_result
                            result = await coro_fn()
                            return verify_result(a_type, payload, result)
                        return _wrapper
                    
                    if func_name == "simulate_slow_task":
                        runner.submit(task_id, wrap_verify("simulate_slow_task", lambda: test_tools.simulate_slow_task(payload.get("seconds", 5))), timeout=timeout)
                    elif func_name == "run_command":
                        from app.tools import dev_tools
                        runner.submit(task_id, wrap_verify("run_command", lambda: dev_tools.run_command(
                            payload.get("command"),
                            payload.get("args", []),
                            payload.get("cwd"),
                            timeout=timeout
                        )), timeout=timeout)
                    elif func_name == "wait_for_task":
                        from app.waiting import wait_for_condition, TaskDoneCondition
                        w_timeout = payload.get("timeout", 60)
                        wait_tid = payload.get("task_id")
                        if not wait_tid:
                            async def missing_err(): return {"success": False, "error": "missing task_id"}
                            runner.submit(task_id, missing_err)
                        else:
                            runner.submit(task_id, wrap_verify("wait_for_task", lambda: wait_for_condition(TaskDoneCondition(wait_tid), timeout=w_timeout)), timeout=timeout)
                    elif func_name == "run_workflow":
                        from app.waiting import run_chained_workflow
                        steps = payload.get("steps", [])
                        runner.submit(task_id, wrap_verify("run_workflow", lambda: run_chained_workflow(steps, overall_timeout=timeout)), timeout=timeout)
                    elif func_name == "delegate_to_agent":
                        from app.agents import get_agent
                        agent_name = payload.get("agent_name")
                        agent = get_agent(agent_name)
                        if not agent:
                            async def err(): return {"success": False, "error": f"Agent {agent_name} not found"}
                            runner.submit(task_id, err)
                        else:
                            runner.submit(task_id, wrap_verify("delegate_to_agent", lambda: agent.send_prompt(payload.get("prompt"))), timeout=timeout)
                    elif func_name == "wait_for_agent":
                        from app.waiting import wait_for_condition, AgentDoneCondition
                        w_timeout = payload.get("timeout", 600)
                        agent_name = payload.get("agent_name")
                        handle = payload.get("handle")
                        if not agent_name or not handle:
                            async def err2(): return {"success": False, "error": "missing agent_name or handle"}
                            runner.submit(task_id, err2)
                        else:
                            runner.submit(task_id, wrap_verify("wait_for_agent", lambda: wait_for_condition(AgentDoneCondition(agent_name, handle), timeout=w_timeout)), timeout=timeout)
                    elif func_name == "check_agent_status":
                        from app.agents import get_agent
                        agent_name = payload.get("agent_name")
                        handle = payload.get("handle")
                        agent = get_agent(agent_name)
                        if not agent:
                            async def err3(): return {"success": False, "error": f"Agent {agent_name} not found"}
                            runner.submit(task_id, err3)
                        else:
                            async def check_status():
                                finished = await agent.is_finished(handle)
                                if finished:
                                    res = await agent.get_result(handle)
                                    return {"success": True, "status": "FINISHED", "result": res}
                                else:
                                    return {"success": True, "status": "PENDING", "description": agent.get_status_description(handle)}
                            runner.submit(task_id, wrap_verify("check_agent_status", check_status), timeout=timeout)
                    else:
                        # Wrap synchronous file tool execution in a coroutine
                        async def wrap_sync_tool(fn_name=func_name, p=payload):
                            import asyncio
                            return await asyncio.to_thread(dispatcher.execute_tool, fn_name, p)
                        runner.submit(task_id, wrap_sync_tool, timeout=timeout) # dispatcher already verifies
                        
                    result = {"success": True, "message": f"Task submitted to background runner with ID {task_id}. Tell the user the task has started and they can check on it later."}
                    executed_task_ids.append(task_id)
                else:
                    result = {"success": False, "error": "Could not create task record."}
            else:
                if task_id:
                    database.update_task_status(task_id, "RUNNING")
                
                result = dispatcher.execute_tool(func_name, payload)
                
                # Update task
                if task_id:
                    if result.get("success"):
                        database.update_task_status(task_id, "DONE", json.dumps(result))
                    else:
                        database.update_task_status(task_id, "FAILED", str(result.get("error", "Unknown error")))
                    
                    # Inject task_id so the LLM has it in context for follow-up questions
                    result["_task_id"] = task_id
                    executed_task_ids.append(task_id)
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.get("id", "call_123"),
                "name": func_name,
                "content": json.dumps(result)
            })
            
        messages.append({
            "role": "system",
            "content": "IMPORTANT: If any tool result indicates that verification failed (verified=False or success=False due to verification), you MUST explicitly tell the user about the discrepancy. Never silently pass through a claimed success that verification contradicts (e.g. say 'The action reported success, but I could not confirm it in the system')."
        })
            
        reply_msg = llm_client.get_completion(messages, use_tools=False)

    reply_content = reply_msg.get("content", "")
    if not reply_content:
        reply_content = "Bunny executed a tool but didn't have anything else to say."
        
    if "tool_calls" in reply_msg_original and reply_msg_original["tool_calls"] and executed_task_ids:
        reply_content += f"\n\n*(System Note: This action was recorded as Task ID(s): {', '.join(map(str, executed_task_ids))})*"
        
    database.add_message(conversation_id, "assistant", reply_content)
    
    return {"conversation_id": conversation_id, "reply": reply_content}

@app.get("/conversations/{conversation_id}/history")
def get_history(conversation_id: int, limit: int = 20):
    messages = database.get_recent_messages(conversation_id, limit)
    return {"messages": messages}

@app.post("/tool")
def execute_tool_endpoint(request: ToolRequest):
    result = dispatcher.execute_tool(request.action_type, request.payload)
    return result

@app.get("/tasks/{task_id}")
def get_task_endpoint(task_id: int):
    task = database.get_task(task_id)
    if not task:
        return {"error": "Task not found"}
    return {"task": task}

@app.get("/conversations/{conversation_id}/tasks")
def get_conversation_tasks(conversation_id: int):
    tasks = database.get_tasks(conversation_id)
    return {"tasks": tasks}
