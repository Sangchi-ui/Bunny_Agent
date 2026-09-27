from typing import Dict, Any
from app.database import get_task

def get_task_status(task_id: int) -> Dict[str, Any]:
    try:
        task = get_task(task_id)
        if not task:
            return {"success": False, "data": None, "error": f"Task {task_id} not found."}
            
        return {
            "success": True,
            "data": {
                "id": task["id"],
                "status": task["status"],
                "description": task["description"],
                "result": task["result"],
                "created_at": task["created_at"]
            },
            "error": None
        }
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}
