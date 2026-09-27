import asyncio
from typing import Dict, Any

async def simulate_slow_task(seconds: int) -> Dict[str, Any]:
    await asyncio.sleep(seconds)
    return {"success": True, "message": f"Slept for {seconds} seconds."}
