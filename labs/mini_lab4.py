""" 
What will we learn in lab 4?
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