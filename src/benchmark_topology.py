import asyncio
import time
import psutil
import os

# Simulating processing time and CPU load for a single microservice task
async def process_task(task_id, service_name, duration=0.05):
    # Simulate IO-bound work (e.g., waiting for DB or network)
    # This represents common microservice bottlenecks
    await asyncio.sleep(duration)
    return f"Task {task_id} processed by {service_name}"

# --- TOPOLOGY 1: CHAIN (Sequential) ---
# Event goes: Broker -> Service A -> Broker -> Service B -> Broker -> Service C
async def run_chain_topology(num_events):
    start_time = time.perf_counter()
    
    for i in range(num_events):
        # Sequential processing (one must finish before the next begins)
        await process_task(i, "Service_A", 0.05)
        await process_task(i, "Service_B", 0.05)
        await process_task(i, "Service_C", 0.05)
        
    total_time = time.perf_counter() - start_time
    return total_time

# --- TOPOLOGY 2: PARALLEL FAN-OUT (Orchestration/Choreography) ---
# Event goes: Broker -> (Service A, Service B, Service C) all at once
async def run_fanout_topology(num_events):
    start_time = time.perf_counter()
    
    for i in range(num_events):
        # Parallel processing (they all receive the event simultaneously)
        await asyncio.gather(
            process_task(i, "Service_A", 0.05),
            process_task(i, "Service_B", 0.05),
            process_task(i, "Service_C", 0.05)
        )
        
    total_time = time.perf_counter() - start_time
    return total_time

async def main():
    num_events = 50  # Number of business events to simulate
    print(f"Simulating {num_events} events traversing 3 microservices...\n")
    
    # 1. Benchmark Chain Topology
    print("Running CHAIN Topology...")
    process = psutil.Process(os.getpid())
    cpu_start = process.cpu_times()
    
    chain_time = await run_chain_topology(num_events)
    
    cpu_end = process.cpu_times()
    chain_cpu_time = (cpu_end.user - cpu_start.user) + (cpu_end.system - cpu_start.system)
    
    print(f"Chain Total Latency: {chain_time:.4f} seconds")
    print(f"Chain CPU Time Used: {chain_cpu_time:.4f} seconds\n")
    
    # 2. Benchmark Fan-Out Topology
    print("Running PARALLEL FAN-OUT Topology...")
    cpu_start = process.cpu_times()
    
    fanout_time = await run_fanout_topology(num_events)
    
    cpu_end = process.cpu_times()
    fanout_cpu_time = (cpu_end.user - cpu_start.user) + (cpu_end.system - cpu_start.system)
    
    print(f"Fan-Out Total Latency: {fanout_time:.4f} seconds")
    print(f"Fan-Out CPU Time Used: {fanout_cpu_time:.4f} seconds\n")
    
    # Summary
    print("--- TOPOLOGY SUMMARY ---")
    latency_reduction = ((chain_time - fanout_time) / chain_time) * 100
    print(f"Latency Reduction with Fan-Out: {latency_reduction:.1f}%")
    
if __name__ == "__main__":
    asyncio.run(main())
