import asyncio
from app.main import lifespan
from app.database import create_task, update_task_status, get_task, get_or_create_conversation

async def test_recovery():
    # Insert a fake running task
    conv = get_or_create_conversation("test", "test")
    tid = create_task(conv, "test running task", 1)
    update_task_status(tid, "RUNNING")
    
    # Run lifespan
    class DummyApp: pass
    app = DummyApp()
    
    async with lifespan(app):
        pass
        
    t = get_task(tid)
    print(f"Task {tid} status is now {t['status']}")
    assert t['status'] == "FAILED"

asyncio.run(test_recovery())
