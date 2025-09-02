"""
Parallel processing utilities for document ingestion
"""

import asyncio
import concurrent.futures
from typing import List, Callable, Any, Optional
from loguru import logger

class ParallelProcessor:
    """Parallel processing coordinator"""
    
    def __init__(self):
        self.executor = None
    
    async def process_batch(self, 
                          items: List[Any], 
                          process_func: Callable, 
                          max_workers: Optional[int] = None) -> List[Any]:
        """Process a batch of items in parallel"""
        if not items:
            return []
        
        # Use default max_workers if not specified
        if max_workers is None:
            max_workers = min(len(items), 4)  # Conservative default
        
        logger.debug(f"Processing batch of {len(items)} items with {max_workers} workers")
        
        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(max_workers)
        
        async def process_with_semaphore(item):
            async with semaphore:
                try:
                    return await process_func(item)
                except Exception as e:
                    logger.error(f"Error processing item: {e}")
                    return {"error": str(e), "item": item}
        
        # Process all items concurrently
        tasks = [process_with_semaphore(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid results
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task failed with exception: {result}")
                valid_results.append({"error": str(result)})
            else:
                valid_results.append(result)
        
        logger.debug(f"Completed batch processing: {len(valid_results)} results")
        return valid_results
    
    async def process_with_thread_pool(self, 
                                     items: List[Any], 
                                     process_func: Callable,
                                     max_workers: Optional[int] = None) -> List[Any]:
        """Process items using thread pool for CPU-bound tasks"""
        if not items:
            return []
        
        if max_workers is None:
            max_workers = min(len(items), 4)
        
        logger.debug(f"Processing {len(items)} items with thread pool ({max_workers} workers)")
        
        # Create thread pool executor
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create tasks
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(executor, process_func, item)
                for item in items
            ]
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Thread pool task failed: {result}")
                valid_results.append({"error": str(result)})
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def process_with_process_pool(self, 
                                      items: List[Any], 
                                      process_func: Callable,
                                      max_workers: Optional[int] = None) -> List[Any]:
        """Process items using process pool for CPU-intensive tasks"""
        if not items:
            return []
        
        if max_workers is None:
            max_workers = min(len(items), 2)  # Conservative for process pool
        
        logger.debug(f"Processing {len(items)} items with process pool ({max_workers} workers)")
        
        # Create process pool executor
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Create tasks
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(executor, process_func, item)
                for item in items
            ]
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Process pool task failed: {result}")
                valid_results.append({"error": str(result)})
            else:
                valid_results.append(result)
        
        return valid_results
    
    def close(self):
        """Clean up resources"""
        if self.executor:
            self.executor.shutdown(wait=True)