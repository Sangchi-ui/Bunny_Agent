import os
import uuid
import asyncio
from pathlib import Path
from typing import Dict, Any

from app.agents.base_agent import BaseAgent
from app.safety import ALLOWED_ROOT_FOLDERS

class CLIAgent(BaseAgent):
    def __init__(self):
        # We use the primary root folder for our agent sandbox
        self.workspace_root = ALLOWED_ROOT_FOLDERS[0]
        self.inbox_dir = self.workspace_root / "agent_inbox"
        self.outbox_dir = self.workspace_root / "agent_outbox"
        
        # Ensure directories exist
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.outbox_dir.mkdir(parents=True, exist_ok=True)

    def _get_inbox_path(self, handle: str) -> Path:
        return self.inbox_dir / f"{handle}.txt"

    def _get_outbox_path(self, handle: str) -> Path:
        return self.outbox_dir / f"{handle}.txt"

    async def send_prompt(self, prompt: str) -> Dict[str, Any]:
        handle = str(uuid.uuid4())
        inbox_path = self._get_inbox_path(handle)
        
        try:
            # We use to_thread just in case disk IO is slow
            await asyncio.to_thread(inbox_path.write_text, prompt, encoding="utf-8")
            return {"success": True, "handle": handle}
        except Exception as e:
            return {"success": False, "error": f"Failed to write prompt: {str(e)}"}

    async def is_finished(self, handle: str) -> bool:
        outbox_path = self._get_outbox_path(handle)
        # Using a simple exists check. The path is inherently safe because we construct it 
        # inside the workspace using a safe UUID format.
        return await asyncio.to_thread(outbox_path.exists)

    async def get_result(self, handle: str) -> Dict[str, Any]:
        outbox_path = self._get_outbox_path(handle)
        
        if not outbox_path.exists():
            return {"success": False, "error": "Result file does not exist yet"}
            
        try:
            content = await asyncio.to_thread(outbox_path.read_text, encoding="utf-8")
            
            # Cap output length
            max_len = 50000
            if len(content) > max_len:
                content = content[:max_len] + "... [TRUNCATED]"
                
            return {"success": True, "result": content}
        except Exception as e:
            return {"success": False, "error": f"Failed to read result: {str(e)}"}

    def get_status_description(self, handle: str) -> str:
        if self._get_outbox_path(handle).exists():
            return f"Agent task {handle} is complete."
        elif self._get_inbox_path(handle).exists():
            return f"Agent task {handle} is pending. Waiting for external CLI."
        else:
            return f"Agent task {handle} is unknown."
