import asyncio
import os
from typing import List, Dict, Any
from pathlib import Path

async def run_command(command: str, args: List[str], cwd: str, timeout: int = 120) -> Dict[str, Any]:
    try:
        p_cwd = str(Path(cwd).resolve())
        
        # NEVER use shell=True. Pass command and args to exec directly.
        # This prevents shell injection vulnerabilities.
        process = await asyncio.create_subprocess_exec(
            command,
            *args,
            cwd=p_cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            return {
                "success": False,
                "error": f"Command exceeded timeout of {timeout} seconds and was killed."
            }
            
        stdout = stdout_bytes.decode('utf-8', errors='replace')
        stderr = stderr_bytes.decode('utf-8', errors='replace')
        
        # Cap output lengths
        max_len = 50000
        if len(stdout) > max_len:
            stdout = stdout[:max_len] + "... [TRUNCATED]"
        if len(stderr) > max_len:
            stderr = stderr[:max_len] + "... [TRUNCATED]"
            
        success = (process.returncode == 0)
        
        return {
            "success": success,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": process.returncode
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
