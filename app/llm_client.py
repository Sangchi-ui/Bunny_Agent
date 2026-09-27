import requests
from typing import List, Dict, Any

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_cpu_usage",
            "description": "Get the current overall and per-core CPU usage percentage of the system.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ram_usage",
            "description": "Get the current RAM (memory) usage statistics of the system.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_disk_usage",
            "description": "Get the disk usage statistics for a specific path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path or drive to check, default is C:\\"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_gpu_usage",
            "description": "Get the current GPU usage, memory, and temperature statistics.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_processes",
            "description": "Get the top running processes on the system by CPU and memory usage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "n": {
                        "type": "integer",
                        "description": "The number of top processes to return (default 5)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_network_status",
            "description": "Check if the system network is currently up and list active interfaces.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_task_status",
            "description": "Check the status, description, and result of a specific task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "The ID of the task to check"
                    }
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "simulate_slow_task",
            "description": "Simulate a slow running task for testing async capabilities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {
                        "type": "integer",
                        "description": "Number of seconds to sleep"
                    }
                },
                "required": ["seconds"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories in a given folder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder": {"type": "string"}
                },
                "required": ["folder"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "max_bytes": {"type": "integer"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Create a new file. Fails if file already exists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or append to an existing file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "mode": {"type": "string", "enum": ["overwrite", "append"]}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rename_file",
            "description": "Rename a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "old_path": {"type": "string"},
                    "new_path": {"type": "string"}
                },
                "required": ["old_path", "new_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "move_file",
            "description": "Move a file from one path to another.",
            "parameters": {
                "type": "object",
                "properties": {
                    "src": {"type": "string"},
                    "dest": {"type": "string"}
                },
                "required": ["src", "dest"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file. Requires a two-step confirmation if enabled.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "confirmation_token": {"type": "string"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a safe developer command in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The command executable name (e.g. pytest, python)"},
                    "args": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "List of arguments to pass to the command"
                    },
                    "cwd": {"type": "string", "description": "Working directory for the command"}
                },
                "required": ["command", "args", "cwd"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wait_for_task",
            "description": "Wait for a specific task to reach a terminal state (DONE, FAILED, or BLOCKED).",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "The ID of the task to wait for"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 60}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_workflow",
            "description": "Run a chained sequence of tools, which can include waiting for tasks and executing other commands in order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "steps": {
                        "type": "array",
                        "description": "List of tool steps to execute sequentially. Each step is an object with 'action_type' and 'payload'.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "action_type": {"type": "string"},
                                "payload": {"type": "object"}
                            },
                            "required": ["action_type", "payload"]
                        }
                    }
                },
                "required": ["steps"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delegate_to_agent",
            "description": "Delegate a prompt/task to a specified external agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string", "description": "The name of the agent to delegate to (e.g. 'cli_agent')"},
                    "prompt": {"type": "string", "description": "The task or prompt to send to the agent"}
                },
                "required": ["agent_name", "prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_agent_status",
            "description": "Check the status and get the result of a task delegated to an external agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string", "description": "The name of the agent"},
                    "handle": {"type": "string", "description": "The handle/ID of the delegated task"}
                },
                "required": ["agent_name", "handle"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wait_for_agent",
            "description": "Wait for an external agent to complete its task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string", "description": "The name of the agent"},
                    "handle": {"type": "string", "description": "The handle/ID of the delegated task"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 600}
                },
                "required": ["agent_name", "handle"]
            }
        }
    }
]

def get_completion(messages: List[Dict[str, Any]], timeout: int = 120, use_tools: bool = True) -> Dict[str, Any]:
    """
    Sends a chat completion request to the local LM Studio server.
    Returns the FULL message dictionary (content, tool_calls, etc.)
    """
    payload = {
        "model": "local-model",
        "messages": messages,
        "stream": False
    }
    
    if use_tools:
        payload["tools"] = TOOLS_SCHEMA
        
    try:
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]
    except requests.exceptions.RequestException:
        # Return a mock message dict representing the error gracefully
        return {"role": "assistant", "content": "Bunny's local AI engine isn't responding right now."}
