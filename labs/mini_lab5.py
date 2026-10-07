import asyncio
import queue
import threading
import time


def producer_threads(q: queue.Queue, stop: object, abort_event: threading.Event):
    for i in range(1, 11):
        if abort_event.is_set():
            print("\n[Worker] Abort signal detected! Cleaning up and exiting.")
            break
        time.sleep(0.5)
        q.put(f"item_{i}")
    q.put(stop)

# The thread handler
async def token_consumer(q: queue.Queue, stop: object, abort_event: threading.Event):
    cnt = 0
    while True:
        if cnt == 3:
            abort_event.set()
            break
        item = await asyncio.to_thread(q.get)
        if item is stop:
            print("\n[Consumer] Done signal received")
            break
        print(f"\n[Consumer] Received: {item}", flush=True)
        cnt += 1

# Coocurrent work
async def heartbeat():
    for _ in range(15):
        await asyncio.sleep(0.1)
        print("...", flush=True)

async def main():
    q = queue.Queue()
    STOP = object()
    abort_event = threading.Event()

    worker = threading.Thread(
        target=producer_threads,
        args=(q, STOP, abort_event),
        name="worker_1"
    )

    worker.start()

    await asyncio.gather(
        token_consumer(q, STOP, abort_event),
        heartbeat()
    )
    
    # while True:
    #     item = asyncio.to_thread(q.get())
    #     if item is STOP:
    #         break
    #     print(f"\n[Recived] {item}", flush=True)

    worker.join()

if __name__ == "__main__":
    asyncio.run(main())