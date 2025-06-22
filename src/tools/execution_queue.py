"""
Simple tool execution queue for handling concurrent MCP requests
"""

import asyncio
import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SimpleToolQueue:
    """Simple asyncio queue for bounded tool execution"""
    
    def __init__(self, max_workers: int = 20, queue_size: int = 200):
        self.max_workers = max_workers
        self.queue = asyncio.Queue(maxsize=queue_size)
        self.workers = []
        self._started = False
        
        # Activity tracking
        self.total_tasks_processed = 0
        self.active_workers = 0
        self.peak_queue_depth = 0
        self.peak_active_workers = 0
        
    async def start(self):
        """Start worker pool"""
        if self._started:
            return
            
        logger.info(f"Starting tool queue with {self.max_workers} workers, queue size {self.queue.maxsize}")
        
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)
        self._started = True
        
    async def _worker(self, worker_id: int):
        """Worker that processes tools from queue"""
        logger.debug(f"Started tool worker {worker_id}")
        
        while True:
            try:
                task = await self.queue.get()
                
                # Track active worker count
                self.active_workers += 1
                self.peak_active_workers = max(self.peak_active_workers, self.active_workers)
                
                # Unpack task
                tool, arguments, config, future = task
                
                logger.debug(f"Worker {worker_id} executing tool: {tool.name}")
                
                # Execute tool with 3 minute timeout
                result = await asyncio.wait_for(
                    tool.execute(arguments, config), 
                    timeout=180.0
                )
                
                # Set result
                future.set_result(result)
                logger.debug(f"Worker {worker_id} completed tool: {tool.name}")
                
                # Track completion
                self.total_tasks_processed += 1
                
            except asyncio.TimeoutError:
                logger.warning(f"Worker {worker_id} tool execution timed out after 3 minutes")
                future.set_exception(
                    Exception(f"Tool execution timed out after 3 minutes")
                )
            except Exception as e:
                logger.error(f"Worker {worker_id} tool execution failed: {e}")
                future.set_exception(e)
            finally:
                # Track worker becoming available
                self.active_workers -= 1
                self.queue.task_done()
    
    async def submit(self, tool, arguments: Dict[str, Any], config: Dict[str, Any]) -> Any:
        """Submit tool for execution and wait for result"""
        future = asyncio.Future()
        
        try:
            # Try to add to queue with small timeout to prevent hanging
            await asyncio.wait_for(
                self.queue.put((tool, arguments, config, future)),
                timeout=5.0
            )
            
            # Track peak queue depth
            current_depth = self.queue.qsize()
            self.peak_queue_depth = max(self.peak_queue_depth, current_depth)
            
            logger.debug(f"Queued tool: {tool.name}, queue depth: {current_depth}")
        except asyncio.TimeoutError:
            raise Exception("Server busy - too many requests in queue")
            
        # Wait for result
        return await future
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current queue statistics"""
        return {
            "queue_depth": self.queue.qsize(),
            "max_workers": self.max_workers,
            "max_queue_size": self.queue.maxsize,
            "workers_started": len(self.workers),
            "is_started": self._started,
            "active_workers": self.active_workers,
            "total_tasks_processed": self.total_tasks_processed,
            "peak_queue_depth": self.peak_queue_depth,
            "peak_active_workers": self.peak_active_workers
        }