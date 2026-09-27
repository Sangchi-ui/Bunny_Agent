import asyncio
import logging
import traceback
import json
from typing import Callable, Awaitable, Any
from app import database

logger = logging.getLogger(__name__)

class TaskRunner:
    def __init__(self, concurrency_limit: int = 1, default_timeout: int = 300):
        self.queue = asyncio.Queue()
        self.concurrency_limit = concurrency_limit
        self.default_timeout = default_timeout
        self.workers = []

    def submit(self, task_id: int, coro_factory: Callable[[], Awaitable[Any]], timeout: int = None):
        """Submit a task to be run in the background."""
        task_timeout = timeout if timeout is not None else self.default_timeout
        self.queue.put_nowait((task_id, coro_factory, task_timeout))
        logger.info(f"Task {task_id} submitted to runner queue.")

    async def start(self):
        """Start the background worker loop."""
        logger.info(f"Starting TaskRunner with concurrency limit {self.concurrency_limit}")
        for i in range(self.concurrency_limit):
            worker = asyncio.create_task(self._worker_loop(i))
            self.workers.append(worker)

    async def stop(self):
        """Stop the background worker loop."""
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

    async def _worker_loop(self, worker_id: int):
        while True:
            try:
                task_id, coro_factory, timeout = await self.queue.get()
                logger.info(f"Worker {worker_id} picked up task {task_id}")
                
                # Mark as RUNNING
                database.update_task_status(task_id, "RUNNING")
                
                try:
                    # Run with timeout
                    coro = coro_factory()
                    result = await asyncio.wait_for(coro, timeout=timeout)
                    # Mark as DONE
                    # Check if result is a dict to serialize it, otherwise stringify
                    if isinstance(result, dict) and not result.get("success", True):
                        # Tool executed but returned success=False
                        database.update_task_status(task_id, "FAILED", result=str(result.get("error", json.dumps(result))))
                    else:
                        if isinstance(result, (dict, list)):
                            result_str = json.dumps(result)
                        else:
                            result_str = str(result)
                        database.update_task_status(task_id, "DONE", result=result_str)
                        
                    logger.info(f"Worker {worker_id} completed task {task_id}")
                except asyncio.TimeoutError:
                    logger.error(f"Task {task_id} timed out after {timeout} seconds.")
                    database.update_task_status(task_id, "FAILED", result=f"Task timed out after {timeout} seconds.")
                except Exception as e:
                    logger.error(f"Task {task_id} failed: {e}\n{traceback.format_exc()}")
                    database.update_task_status(task_id, "FAILED", result=f"Error: {e}")
                finally:
                    self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} encountered unexpected error: {e}")
                await asyncio.sleep(1)

runner = TaskRunner()
