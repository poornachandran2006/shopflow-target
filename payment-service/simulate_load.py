import asyncio
import httpx
import argparse
import random
import time

# The payment service runs on port 8001
API_URL = "http://localhost:8001"

async def send_request(client, endpoint, user_id):
    """Sends a single request to the payment service."""
    try:
        if endpoint == "/process":
            payload = {
                "user_id": f"user_{user_id}",
                "amount": round(random.uniform(10.0, 500.0), 2),
                "cart_items": [{"id": "p_001", "name": "Hackathon Pro Plan", "price": 49.99}]
            }
        else: # /refund
            payload = {
                "payment_id": f"pay_{uuid_hex()[:8]}",
                "user_id": f"user_{user_id}",
                "amount": round(random.uniform(10.0, 50.0), 2),
                "reason": "customer_request"
            }
        
        start = time.time()
        resp = await client.post(f"{API_URL}{endpoint}", json=payload, timeout=15.0)
        elapsed = (time.time() - start) * 1000
        
        if resp.status_code == 200:
            print(f"✅ [SUCCESS] {endpoint} | User {user_id:02d} | {elapsed:.0f}ms")
        else:
            error_detail = resp.json().get('detail', {})
            if isinstance(error_detail, str):
                error_name = error_detail
            else:
                error_name = error_detail.get('error', 'unknown')
            print(f"❌ [ERROR] {endpoint} | User {user_id:02d} | Status {resp.status_code} | {error_name}")
            
    except Exception as e:
        print(f"⚠️ [FAIL] {endpoint} | User {user_id:02d} | {e}")

def uuid_hex():
    import uuid
    return uuid.uuid4().hex

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--users", type=int, default=1)
    parser.add_argument("--refund", action="store_true")
    parser.add_argument("--mixed", action="store_true")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    async with httpx.AsyncClient() as client:
        if args.reset:
            try:
                await client.post(f"{API_URL}/reset")
                print("🔄 [RESET] Service state cleared")
            except Exception as e:
                print(f"⚠️ [RESET FAIL] Could not reach payment service: {e}")
            return

        print(f"🚀 Starting load simulation with {args.users} users...")
        tasks = []
        for i in range(args.users):
            endpoint = "/process"
            if args.refund:
                endpoint = "/refund"
            elif args.mixed:
                endpoint = "/process" if i % 2 == 0 else "/refund"
            
            tasks.append(send_request(client, endpoint, i))
            # Small jitter to simulate real user arrivals
            await asyncio.sleep(random.uniform(0.05, 0.15))
        
        await asyncio.gather(*tasks)
        print("🏁 Simulation complete.")

if __name__ == "__main__":
    asyncio.run(main())
