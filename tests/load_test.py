import asyncio
import aiohttp
import time
from typing import List, Dict
import statistics
import argparse

async def send_query(session: aiohttp.ClientSession, url: str, query: str) -> Dict:
    start_time = time.time()
    async with session.post(url, json={"text": query}) as response:
        response_time = time.time() - start_time
        return {
            "status": response.status,
            "response_time": response_time,
            "success": response.status == 200
        }

async def load_test(
    base_url: str,
    num_requests: int,
    concurrent_requests: int,
    query: str = "What is RAG?"
) -> None:
    url = f"{base_url}/api/query"
    results: List[Dict] = []
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(num_requests):
            task = send_query(session, url, query)
            tasks.append(task)
            
            if len(tasks) >= concurrent_requests:
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)
                tasks = []
        
        if tasks:
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
    
    # Calculate metrics
    response_times = [r["response_time"] for r in results if r["success"]]
    success_rate = sum(1 for r in results if r["success"]) / len(results) * 100
    
    print(f"\nLoad Test Results:")
    print(f"Total Requests: {len(results)}")
    print(f"Success Rate: {success_rate:.2f}%")
    print(f"Average Response Time: {statistics.mean(response_times):.2f}s")
    print(f"95th Percentile Response Time: {statistics.quantiles(response_times, n=20)[-1]:.2f}s")
    print(f"Max Response Time: {max(response_times):.2f}s")
    print(f"Min Response Time: {min(response_times):.2f}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load test the RAG API")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--requests", type=int, default=100, help="Total number of requests")
    parser.add_argument("--concurrent", type=int, default=10, help="Number of concurrent requests")
    parser.add_argument("--query", default="What is RAG?", help="Query to test with")
    
    args = parser.parse_args()
    
    asyncio.run(load_test(
        base_url=args.url,
        num_requests=args.requests,
        concurrent_requests=args.concurrent,
        query=args.query
    ))
