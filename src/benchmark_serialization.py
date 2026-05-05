import json
import time
import pickle
import sys
import statistics
from codecarbon import EmissionsTracker

import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'proto'))
import event_pb2

try:
    import msgpack
    HAS_MSGPACK = True
except ImportError:
    HAS_MSGPACK = False

# Scaled up to 1,000,000 to ensure measurable physical energy draw
NUM_EVENTS = 1_000_000
NUM_RUNS = 5  # Repeated runs for mean ± stddev reporting


def generate_events():
    events = []
    for i in range(NUM_EVENTS):
        events.append({
            "order_id": 1000000 + i,
            "user_id": 9000000 + i,
            "status": 1,  # 1: PROCESSED
            "amount": 150.50 + (i % 10)
        })
    return events


def benchmark_json(events):
    start = time.perf_counter()
    serialized = [json.dumps(e).encode('utf-8') for e in events]
    serialize_time = time.perf_counter() - start

    start = time.perf_counter()
    deserialized = [json.loads(s.decode('utf-8')) for s in serialized]
    deserialize_time = time.perf_counter() - start

    total_size = sum(len(s) for s in serialized)
    return total_size, serialize_time, deserialize_time


def benchmark_protobuf(events):
    start = time.perf_counter()
    serialized = []
    for e in events:
        msg = event_pb2.Event(
            order_id=e["order_id"],
            user_id=e["user_id"],
            status=e["status"],
            amount=e["amount"]
        )
        serialized.append(msg.SerializeToString())
    serialize_time = time.perf_counter() - start

    start = time.perf_counter()
    deserialized = []
    for s in serialized:
        msg = event_pb2.Event()
        msg.ParseFromString(s)
        deserialized.append({
            "order_id": msg.order_id,
            "user_id": msg.user_id,
            "status": msg.status,
            "amount": msg.amount
        })
    deserialize_time = time.perf_counter() - start

    total_size = sum(len(s) for s in serialized)
    return total_size, serialize_time, deserialize_time


def benchmark_msgpack(events):
    if not HAS_MSGPACK:
        return 0, 0, 0

    start = time.perf_counter()
    serialized = [msgpack.packb(e, use_bin_type=True) for e in events]
    serialize_time = time.perf_counter() - start

    start = time.perf_counter()
    deserialized = [msgpack.unpackb(s, raw=False) for s in serialized]
    deserialize_time = time.perf_counter() - start

    total_size = sum(len(s) for s in serialized)
    return total_size, serialize_time, deserialize_time


def run_repeated(fn, events, n=NUM_RUNS):
    """Run benchmark fn n times, return (size, mean_total_ms, stddev_total_ms)."""
    sizes = []
    totals = []
    for _ in range(n):
        size, ser, deser = fn(events)
        sizes.append(size)
        totals.append((ser + deser) * 1000)
    return sizes[0], statistics.mean(totals), statistics.stdev(totals) if n > 1 else 0.0


if __name__ == "__main__":
    print(f"Generating {NUM_EVENTS} test events...")
    events = generate_events()

    print(f"\nRunning each benchmark {NUM_RUNS} times for mean ± stddev...\n")

    # --- JSON ---
    print("--- JSON Benchmark ---")
    # Energy measured via single CodeCarbon run (TDP-estimated); timing repeated N times
    tracker_json = EmissionsTracker(project_name="JSON_Serialization", log_level="error",
                                    measure_power_secs=1, force_mode_cpu_load=True)
    tracker_json.start()
    j_size, j_mean, j_std = run_repeated(benchmark_json, events)
    json_emissions = tracker_json.stop()
    json_energy = tracker_json._total_energy.kWh
    print(f"  Payload Size:    {j_size / (1024*1024):.2f} MB")
    print(f"  CPU Time:        {j_mean:.2f} ± {j_std:.2f} ms  (mean ± stddev, n={NUM_RUNS})")
    print(f"  Energy (TDP est): {json_energy:.6f} kWh")

    # --- Protobuf ---
    print("\n--- Protobuf Benchmark ---")
    tracker_pb = EmissionsTracker(project_name="Protobuf_Serialization", log_level="error",
                                  measure_power_secs=1, force_mode_cpu_load=True)
    tracker_pb.start()
    p_size, p_mean, p_std = run_repeated(benchmark_protobuf, events)
    pb_emissions = tracker_pb.stop()
    pb_energy = tracker_pb._total_energy.kWh
    print(f"  Payload Size:    {p_size / (1024*1024):.2f} MB")
    print(f"  CPU Time:        {p_mean:.2f} ± {p_std:.2f} ms  (mean ± stddev, n={NUM_RUNS})")
    print(f"  Energy (TDP est): {pb_energy:.6f} kWh")

    # --- MessagePack ---
    if HAS_MSGPACK:
        print("\n--- MessagePack Benchmark ---")
        tracker_msg = EmissionsTracker(project_name="MsgPack_Serialization", log_level="error",
                                       measure_power_secs=1, force_mode_cpu_load=True)
        tracker_msg.start()
        m_size, m_mean, m_std = run_repeated(benchmark_msgpack, events)
        msg_emissions = tracker_msg.stop()
        msg_energy = tracker_msg._total_energy.kWh
        print(f"  Payload Size:    {m_size / (1024*1024):.2f} MB")
        print(f"  CPU Time:        {m_mean:.2f} ± {m_std:.2f} ms  (mean ± stddev, n={NUM_RUNS})")
        print(f"  Energy (TDP est): {msg_energy:.6f} kWh")

    print("\n--- SUMMARY ---")
    print(f"Protobuf vs JSON payload reduction:  {((j_size - p_size) / j_size) * 100:.1f}%")
    print(f"Protobuf vs JSON CPU time reduction: {((j_mean - p_mean) / j_mean) * 100:.1f}%")
    print(f"Protobuf vs JSON energy reduction:   {((json_energy - pb_energy) / json_energy) * 100:.1f}%  (TDP-estimated)")
    if HAS_MSGPACK:
        print(f"MessagePack vs JSON payload reduction:  {((j_size - m_size) / j_size) * 100:.1f}%")
        print(f"MessagePack vs JSON CPU time reduction: {((j_mean - m_mean) / j_mean) * 100:.1f}%")
