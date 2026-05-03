"""
Memory benchmark: JSON vs MessagePack vs Protobuf deserialization peak RAM.
Uses actual event_pb2 compiled Protobuf (consistent with benchmark_serialization.py).
"""
import json
import tracemalloc
import gc
import statistics

import event_pb2

try:
    import msgpack
    HAS_MSGPACK = True
except ImportError:
    HAS_MSGPACK = False

NUM_EVENTS = 1_000_000
NUM_RUNS = 3  # tracemalloc is slow; 3 runs sufficient for variance check


def generate_events():
    return [
        {"order_id": 1000000 + i, "user_id": 9000000 + i, "status": 1, "amount": 150.50 + (i % 10)}
        for i in range(NUM_EVENTS)
    ]


def measure_peak(fn):
    gc.collect()
    tracemalloc.start()
    fn()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak


def json_deser_peak(serialized_json):
    def _run():
        _ = [json.loads(s.decode('utf-8')) for s in serialized_json]
    return measure_peak(_run)


def protobuf_deser_peak(serialized_pb):
    def _run():
        for s in serialized_pb:
            msg = event_pb2.Event()
            msg.ParseFromString(s)
    return measure_peak(_run)


def msgpack_deser_peak(serialized_mp):
    def _run():
        _ = [msgpack.unpackb(s, raw=False) for s in serialized_mp]
    return measure_peak(_run)


if __name__ == "__main__":
    print(f"Generating {NUM_EVENTS} events and pre-serializing...")
    events = generate_events()

    # Pre-serialize once (we measure deserialization memory only)
    json_bytes = [json.dumps(e).encode('utf-8') for e in events]
    pb_bytes = []
    for e in events:
        msg = event_pb2.Event(
            order_id=e["order_id"], user_id=e["user_id"],
            status=e["status"], amount=e["amount"]
        )
        pb_bytes.append(msg.SerializeToString())

    if HAS_MSGPACK:
        mp_bytes = [msgpack.packb(e, use_bin_type=True) for e in events]

    print(f"\nPayload sizes (total for {NUM_EVENTS} events):")
    print(f"  JSON:        {sum(len(b) for b in json_bytes) / (1024*1024):.2f} MB")
    print(f"  Protobuf:    {sum(len(b) for b in pb_bytes) / (1024*1024):.2f} MB")
    if HAS_MSGPACK:
        print(f"  MessagePack: {sum(len(b) for b in mp_bytes) / (1024*1024):.2f} MB")

    print(f"\nMeasuring peak deserialization RAM ({NUM_RUNS} runs each)...\n")

    json_peaks = [json_deser_peak(json_bytes) for _ in range(NUM_RUNS)]
    pb_peaks = [protobuf_deser_peak(pb_bytes) for _ in range(NUM_RUNS)]

    json_mean = statistics.mean(json_peaks) / (1024 * 1024)
    json_std = statistics.stdev(json_peaks) / (1024 * 1024) if NUM_RUNS > 1 else 0
    pb_mean = statistics.mean(pb_peaks) / (1024 * 1024)
    pb_std = statistics.stdev(pb_peaks) / (1024 * 1024) if NUM_RUNS > 1 else 0

    print(f"JSON peak RAM:     {json_mean:.2f} ± {json_std:.2f} MB")
    print(f"Protobuf peak RAM: {pb_mean:.2f} ± {pb_std:.2f} MB")
    print(f"RAM reduction:     {((json_mean - pb_mean) / json_mean) * 100:.1f}%")

    if HAS_MSGPACK:
        mp_peaks = [msgpack_deser_peak(mp_bytes) for _ in range(NUM_RUNS)]
        mp_mean = statistics.mean(mp_peaks) / (1024 * 1024)
        mp_std = statistics.stdev(mp_peaks) / (1024 * 1024) if NUM_RUNS > 1 else 0
        print(f"MessagePack peak RAM: {mp_mean:.2f} ± {mp_std:.2f} MB")
        print(f"MessagePack vs JSON RAM reduction: {((json_mean - mp_mean) / json_mean) * 100:.1f}%")
