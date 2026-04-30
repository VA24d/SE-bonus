import json
import struct
import tracemalloc
import gc

NUM_EVENTS = 1000000

def generate_events():
    events = []
    for i in range(NUM_EVENTS):
        events.append({
            "order_id": 1000000 + i,
            "user_id": 9000000 + i,
            "status": 1, 
            "amount": 150.50 + (i % 10)
        })
    return events

def run_json_memory_benchmark(events):
    gc.collect()
    # Serialize first
    serialized = [json.dumps(e).encode('utf-8') for e in events]
    
    # Measure Deserialization Memory Pressure
    tracemalloc.start()
    _ = [json.loads(s.decode('utf-8')) for s in serialized]
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak

def run_binary_memory_benchmark(events):
    gc.collect()
    fmt = 'qqif'
    # Serialize first
    serialized = [struct.pack(fmt, e["order_id"], e["user_id"], e["status"], e["amount"]) for e in events]
    
    # Measure Deserialization Memory Pressure
    tracemalloc.start()
    deserialized = []
    for s in serialized:
        unpacked = struct.unpack(fmt, s)
        deserialized.append({
            "order_id": unpacked[0],
            "user_id": unpacked[1],
            "status": unpacked[2],
            "amount": unpacked[3]
        })
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak

if __name__ == "__main__":
    print(f"Generating {NUM_EVENTS} test events...")
    events = generate_events()
    
    print("\n--- Running JSON Memory Benchmark ---")
    json_peak = run_json_memory_benchmark(events)
    print(f"Peak RAM during JSON Deserialization: {json_peak / (1024*1024):.2f} MB")
    
    print("\n--- Running Binary Memory Benchmark ---")
    bin_peak = run_binary_memory_benchmark(events)
    print(f"Peak RAM during Binary Deserialization: {bin_peak / (1024*1024):.2f} MB")
    
    print("\n--- RESULTS ---")
    print(f"Memory Footprint Reduction: {((json_peak - bin_peak) / json_peak) * 100:.1f}%")
