import asyncio
import httpx

async def fire_request(client, req_id):
    try:
        response = await client.get("http://localhost:8000/rate-limited?user=abc", timeout=10.0)
        print(f"Req #{req_id} -> Status: {response.status_code} | Body: {response.text}")
    except Exception as e:
        print(f"Req #{req_id} Failed: {e}")

async def main():
    print("Firing 8 simultaneous requests...\n")

    limits = httpx.Limits(max_connections=20, max_keepalive_connections=0)
    async with httpx.AsyncClient(limits=limits) as client:
        tasks = [fire_request(client, i) for i in range(1, 9)]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())