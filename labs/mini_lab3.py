""" 
What is lab 3 about?
1. Understanding the fundamental difference between HTTP & SSE
2. SSE - Server Sent Event - the streaming response, delimeters and the payload

Important components:
1. The "\n\n" delimiter - acts as an indication to the client saying it's the end of the event
or the streaming has finished, if removed the client might end up in a loop where it keeps waiting 
for the serrver to send in more data.
2. The header `media_type="text/event-stream"` specifically tells the client that the type of 
output from the server will be a streaming type
"""

import asyncio

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI(title="SSE Handler")

# Dummy function to stream some data
async def number_streamer():
    for i in range(5):
        await asyncio.sleep(2)
        yield f"data: {i}\n\n"

@app.get("/health", status_code=200, tags=['Health'])
def health_check() -> dict:
    return { 'status': 'ok' }

@app.get("/stream", status_code=200, tags=["Stream"])
async def stream():
    return StreamingResponse(
        number_streamer(),
        media_type="text/event-stream",
        # Headers that are must for the production
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Acces-Buffering": "no",
        }
    )
