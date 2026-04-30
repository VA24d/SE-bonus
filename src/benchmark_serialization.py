import json
import time
import struct
import pickle
import sys
from codecarbon import EmissionsTracker

try:
    import msgpack
    HAS_MSGPACK = True
except ImportError:
    HAS_MSGPACK = False

# Scaled up to 1,000,000 to ensure measurable physical energy draw
NUM_EVENTS = 1000000

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
    # Serialization
    start = time.perf_counter()
    serialized = [json.dumps(e).encode('utf-8') for e in events]
    serialize_time = time.perf_counter() - start
    
    # Deserialization
    start = time.perf_counter()
    deserialized = [json.loads(s.decode('utf-8')) for s in serialized]
    deserialize_time = time.perf_counter() - start
    
    total_size = sum(len(s) for s in serialized)
    return total_size, serialize_time, deserialize_time

def benchmark_struct(events):
    # Simulates a tightly packed binary format like Protobuf
    # Format: q (long long), q (long long), i (int), f (float)
    fmt = 'qqif'
    
    # Serialization
    start = time.perf_counter()
    serialized = [struct.pack(fmt, e["order_id"], e["user_id"], e["status"], e["amount"]) for e in events]
    serialize_time = time.perf_counter() - start
    
    # Deserialization
    start = time.perf_counter()
    deserialized = []
    for s in serialized:
        unpacked = struct.unpack(fmt, s)
        deserialized.append({
            "order_id": unpacked[0],
            "user_id": unpacked[1],
            "status": unpacked[2],
            "amount": unpacked[3]
        })
    deserialize_time = time.perf_counter() - start
    
    total_size = sum(len(s) for s in serialized)
    return total_size, serialize_time, deserialize_time

def benchmark_msgpack(events):
    if not HAS_MSGPACK:
        return 0, 0, 0
    
    # Serialization
    start = time.perf_counter()
    serialized = [msgpack.packb(e, use_bin_type=True) for e in events]
    serialize_time = time.perf_counter() - start
    
    # Deserialization
    start = time.perf_counter()
    deserialized = [msgpack.unpackb(s, raw=False) for s in serialized]
    deserialize_time = time.perf_counter() - start
    
    total_size = sum(len(s) for s in serialized)
    return total_size, serialize_time, deserialize_time

if __name__ == "__main__":
    print(f"Generating {NUM_EVENTS} test events...")
    events = generate_events()
    
    print("\n--- Running JSON Benchmark ---")
    tracker_json = EmissionsTracker(project_name="JSON_Serialization", log_level="error")
    tracker_json.start()
    j_size, j_ser, j_deser = benchmark_json(events)
    json_emissions = tracker_json.stop()
    json_energy = tracker_json._total_energy.kWh
    print(f"Total Payload Size: {j_size / (1024*1024):.2f} MB")
    print(f"Serialization Time: {j_ser * 1000:.2f} ms")
    print(f"Deserialization Time: {j_deser * 1000:.2f} ms")
    print(f"Actual Energy Consumed: {json_energy:.6f} kWh")
    print(f"Carbon Emissions: {json_emissions:.6f} kg CO2eq")
    
    print("\n--- Running Struct/Binary Benchmark (Protobuf Simulation) ---")
    tracker_bin = EmissionsTracker(project_name="Binary_Serialization", log_level="error")
    tracker_bin.start()
    s_size, s_ser, s_deser = benchmark_struct(events)
    bin_emissions = tracker_bin.stop()
    bin_energy = tracker_bin._total_energy.kWh
    print(f"Total Payload Size: {s_size / (1024*1024):.2f} MB")
    print(f"Serialization Time: {s_ser * 1000:.2f} ms")
    print(f"Deserialization Time: {s_deser * 1000:.2f} ms")
    print(f"Actual Energy Consumed: {bin_energy:.6f} kWh")
    print(f"Carbon Emissions: {bin_emissions:.6f} kg CO2eq")
    
    if HAS_MSGPACK:
        print("\n--- Running MsgPack Benchmark ---")
        tracker_msg = EmissionsTracker(project_name="MsgPack_Serialization", log_level="error")
        tracker_msg.start()
        m_size, m_ser, m_deser = benchmark_msgpack(events)
        msg_emissions = tracker_msg.stop()
        msg_energy = tracker_msg._total_energy.kWh
        print(f"Total Payload Size: {m_size / (1024*1024):.2f} MB")
        print(f"Serialization Time: {m_ser * 1000:.2f} ms")
        print(f"Deserialization Time: {m_deser * 1000:.2f} ms")
        print(f"Actual Energy Consumed: {msg_energy:.6f} kWh")
        print(f"Carbon Emissions: {msg_emissions:.6f} kg CO2eq")
    
    print("\n--- EMPIRICAL ENERGY SUMMARY ---")
    print(f"Binary vs JSON CPU Time Reduction: {(( (j_ser+j_deser) - (s_ser+s_deser) ) / (j_ser+j_deser)) * 100:.1f}%")
    print(f"Binary vs JSON Physical Energy Reduction: {((json_energy - bin_energy) / json_energy) * 100:.1f}%")
