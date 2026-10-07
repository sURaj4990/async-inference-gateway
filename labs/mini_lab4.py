""" 
What will we learn in lab 4?
1. How firing up multiple workers behave as different processe
2. Each process has it's own In-memory store that it can write to which is independent
from other processe stores.
3. Why in memory store is broken and we need external database like Redis
4. How `--reload` argument prevents multiple processes executing at once
"""

import os
import time

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Rate Limiter")

# In-memory store: tracks requests per IP/user
REQUEST_COUNT = {}
MAX_REQUESTS = 3

@app.get("/rate-limited")
def rate_limited(user: str = 'alice') -> dict:
    pid = os.getpid() # OS process ID

    time.sleep(0.5)
    current_count = REQUEST_COUNT.get(user, 0)
    if current_count >= MAX_REQUESTS:
        raise HTTPException(
            status_code=429, 
            detail=f"Limit Exceeded on process ID - {pid}"
        )

    REQUEST_COUNT[user] = current_count + 1
    return {
        'status': 'success',
        'count': REQUEST_COUNT.get(user),
        'worker_id': pid,
    }

""" 
Further Learning:
1. Learn how to write test scripts
2. Understand how workers handle in-memory store 
"""