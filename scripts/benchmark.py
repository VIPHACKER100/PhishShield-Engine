"""
Performance Benchmarking Suite (Phase 64)
Stress tests the FastAPI instances concurrent request latency.
"""
import time
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor

url = "http://localhost:8000/predict/batch"
headers = {"Content-Type": "application/json"}
payload = {
    "emails": ["Check out my new website!"] * 100,
    "model_name": "naive_bayes"
}

def fetch():
    start = time.time()
    res = requests.post(url, json=payload, headers=headers)
    return res.status_code, time.time() - start

async def benchmark(total_requests: int = 500, max_workers: int = 50):
    print(f"--- Starting PhishShield Load Stress Test ---")
    print(f"Goal: Dispatch {total_requests} bulk batches of 100 emails concurrently.\n")
    
    loop = asyncio.get_event_loop()
    start_total = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        tasks = [loop.run_in_executor(pool, fetch) for _ in range(total_requests)]
        results = await asyncio.gather(*tasks)
        
    duration = time.time() - start_total
    success_count = sum(1 for status, t in results if status == 200)
    avg_latency = sum(t for status, t in results) / total_requests
    
    print(f"Success: {success_count}/{total_requests} ({(success_count/total_requests)*100}%)")
    print(f"Throughput: {total_requests / duration:.2f} rps")
    print(f"Average Request Latency: {avg_latency*1000:.2f} ms")
    
if __name__ == "__main__":
    asyncio.run(benchmark())
