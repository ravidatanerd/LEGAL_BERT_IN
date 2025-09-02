"""
Parallel processing utilities
"""

import asyncio
import logging
from typing import List, Callable, Any, TypeVar, Awaitable
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import os

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')

class ParallelProcessor:
    """Handle parallel processing with configurable workers"""
    
    def __init__(self, max_workers: int = None, use_processes: bool = False):
        self.max_workers = max_workers or os.cpu_count() or 4
        self.use_processes = use_processes
        self.executor = None
    
    def __enter__(self):
        if self.use_processes:
            self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
        else:
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.executor:
            self.executor.shutdown(wait=True)
    
    async def process_batch(
        self, 
        items: List[T], 
        func: Callable[[T], R],
        batch_size: int = None
    ) -> List[R]:
        """Process items in parallel batches"""
        if not items:
            return []
        
        batch_size = batch_size or self.max_workers
        
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await self._process_batch_async(batch, func)
            results.extend(batch_results)
        
        return results
    
    async def _process_batch_async(
        self, 
        batch: List[T], 
        func: Callable[[T], R]
    ) -> List[R]:
        """Process a single batch asynchronously"""
        if not self.executor:
            raise RuntimeError("Executor not initialized. Use as context manager.")
        
        loop = asyncio.get_event_loop()
        futures = []
        
        for item in batch:
            future = loop.run_in_executor(self.executor, func, item)
            futures.append(future)
        
        return await asyncio.gather(*futures, return_exceptions=True)

async def process_parallel(
    items: List[T],
    func: Callable[[T], R],
    max_workers: int = None,
    batch_size: int = None,
    use_processes: bool = False
) -> List[R]:
    """Convenience function for parallel processing"""
    with ParallelProcessor(max_workers, use_processes) as processor:
        return await processor.process_batch(items, func, batch_size)

async def safe_parallel_process(
    items: List[T],
    func: Callable[[T], R],
    max_workers: int = None,
    batch_size: int = None,
    use_processes: bool = False
) -> List[tuple[T, R | Exception]]:
    """
    Process items in parallel, returning (item, result) pairs
    Exceptions are captured and returned instead of raised
    """
    results = []
    
    async def safe_func(item: T) -> tuple[T, R | Exception]:
        try:
            result = await func(item) if asyncio.iscoroutinefunction(func) else func(item)
            return (item, result)
        except Exception as e:
            logger.error(f"Error processing item {item}: {e}")
            return (item, e)
    
    with ParallelProcessor(max_workers, use_processes) as processor:
        batch_results = await processor.process_batch(items, safe_func, batch_size)
        results.extend(batch_results)
    
    return results