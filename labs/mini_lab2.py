""" 
What did we learn from this lab?
1. Why synchronous compute shoud never make the event loop wait
2. Why just putting async does not deload the compute and free the thread
3. Different ways to prevent this blocking 
> a. Move the blocking synchronous compute to another thread, freeing the original thread for the event loop
> b. Offload the compute over the network to an external daemon via non blocking async network call (mimics the I/O operation)
"""

import asyncio
import time
from fastapi import FastAPI

app = FastAPI(
    title="Mini-lab 2",
    version="0.1.0"
)

@app.get("/health", status_code=200, tags=['Health'])
def health_check() -> dict:
    return {
        'status': 'ok',
        'version': app.version
    }

# Lesson: The event loop must never be forced to wait for synchronous compute
@app.get("/heavy-compute")
async def heavy_compute() -> dict:
    # Non-blocking way
    # await asyncio.sleep(10.0) 
    # Synchronous call
    time.sleep(20.0)
    return {
        'status': 'completed'
    }

"""
Further Learning:
** Understand how to implement the creation of new thread
** Understand the non blocking I/O operation implementation 
"""