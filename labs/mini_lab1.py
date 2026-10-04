""" 
This lab gives a detailed explaination for the following
1. How to stream the result using `yield` and why sometimes it is necessary to stream?
2. Using `time.sleep(1.0)` to block the thread
3. Using `asyncio.sleep(1.0)` - which does not block the thread, instead hands back the control to
the event-loop
"""
# Classic function that resturns the complete output
import asyncio
import time
from collections.abc import AsyncIterator, Iterator

def countdown(n: int) -> list[int]:
    result = []
    for i in range(n):
        result.append(n)
    return result

# Implementation of sreating output with one second delay
def stream_countdown(n: int) -> Iterator[int]:
    for i in range(n):
        time.sleep(1.0) # blocks the thread completely for 60 seconds
        yield i

# Implementation of asyncio.sleep()
async def async_iterator(n: int) -> AsyncIterator[int]:
    for i in range(n):
        await asyncio.sleep(1.0) # releases the thread while it waits
        yield i

async def main():
    async for i in async_iterator(5):
        print(i)

asyncio.run(main()) # Use of ayncio.run() to execute an async function

