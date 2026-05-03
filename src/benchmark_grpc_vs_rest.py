import time
import requests
import threading
import statistics
import json
import grpc
from concurrent import futures
from flask import Flask, request, jsonify
from codecarbon import EmissionsTracker

import event_pb2
import event_pb2_grpc

NUM_EVENTS = 10000
NUM_RUNS = 5       # repeated runs for mean ± stddev
CONCURRENCY = 50   # concurrent requests per batch
REST_PORT = 5001
GRPC_PORT = 5002

# --- REST/JSON SERVER (Flask) ---
app = Flask(__name__)
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/process', methods=['POST'])
def process_event():
    data = request.json
    return jsonify({"success": True, "message": f"Processed {data['order_id']}"})

def run_rest_server():
    app.run(port=REST_PORT, debug=False, use_reloader=False, threaded=True)

# --- gRPC/PROTOBUF SERVER ---
class EventServiceServicer(event_pb2_grpc.EventServiceServicer):
    def ProcessEvent(self, request, context):
        return event_pb2.EventResponse(success=True, message=f"Processed {request.order_id}")

def run_grpc_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=CONCURRENCY))
    event_pb2_grpc.add_EventServiceServicer_to_server(EventServiceServicer(), server)
    server.add_insecure_port(f'[::]:{GRPC_PORT}')
    server.start()
    server.wait_for_termination()

# --- CLIENT BENCHMARKS ---
def generate_events():
    return [
        {"order_id": 1000000 + i, "user_id": 9000000 + i, "status": 1, "amount": 150.50 + (i % 10)}
        for i in range(NUM_EVENTS)
    ]

def benchmark_rest_sequential(events):
    """Sequential HTTP/1.1 requests (keep-alive session)."""
    session = requests.Session()
    start = time.perf_counter()
    for e in events:
        session.post(f"http://127.0.0.1:{REST_PORT}/process", json=e)
    return time.perf_counter() - start

def benchmark_rest_concurrent(events, concurrency=CONCURRENCY):
    """Concurrent HTTP/1.1 requests using thread pool."""
    results = []
    lock = threading.Lock()

    def send(e):
        s = requests.Session()
        s.post(f"http://127.0.0.1:{REST_PORT}/process", json=e)

    start = time.perf_counter()
    with futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(send, events))
    return time.perf_counter() - start

def benchmark_grpc_sequential(events):
    """Sequential gRPC unary calls."""
    start = time.perf_counter()
    with grpc.insecure_channel(f'127.0.0.1:{GRPC_PORT}') as channel:
        stub = event_pb2_grpc.EventServiceStub(channel)
        for e in events:
            msg = event_pb2.Event(
                order_id=e["order_id"], user_id=e["user_id"],
                status=e["status"], amount=e["amount"]
            )
            stub.ProcessEvent(msg)
    return time.perf_counter() - start

def benchmark_grpc_concurrent(events, concurrency=CONCURRENCY):
    """Concurrent gRPC calls using thread pool (exercises HTTP/2 multiplexing)."""
    channel = grpc.insecure_channel(f'127.0.0.1:{GRPC_PORT}')
    stub = event_pb2_grpc.EventServiceStub(channel)

    def call(e):
        msg = event_pb2.Event(
            order_id=e["order_id"], user_id=e["user_id"],
            status=e["status"], amount=e["amount"]
        )
        stub.ProcessEvent(msg)

    start = time.perf_counter()
    with futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(call, events))
    channel.close()
    return time.perf_counter() - start

def run_repeated(fn, events, n=NUM_RUNS):
    times = [fn(events) for _ in range(n)]
    return statistics.mean(times), statistics.stdev(times) if n > 1 else 0.0

if __name__ == "__main__":
    print("Starting REST/JSON server...")
    threading.Thread(target=run_rest_server, daemon=True).start()
    print("Starting gRPC/Protobuf server...")
    threading.Thread(target=run_grpc_server, daemon=True).start()
    time.sleep(2)

    events = generate_events()
    print(f"\nBenchmarking {NUM_EVENTS} events, {NUM_RUNS} runs each, concurrency={CONCURRENCY}\n")

    # --- Sequential ---
    print("=== Sequential (1 request at a time) ===")
    tracker = EmissionsTracker(project_name="REST_JSON_Sequential", log_level="error")
    tracker.start()
    rest_seq_mean, rest_seq_std = run_repeated(benchmark_rest_sequential, events)
    rest_seq_energy = tracker._total_energy.kWh; tracker.stop()

    tracker = EmissionsTracker(project_name="gRPC_Protobuf_Sequential", log_level="error")
    tracker.start()
    grpc_seq_mean, grpc_seq_std = run_repeated(benchmark_grpc_sequential, events)
    grpc_seq_energy = tracker._total_energy.kWh; tracker.stop()

    print(f"REST/JSON  sequential: {rest_seq_mean:.2f} ± {rest_seq_std:.2f} s  |  {rest_seq_energy:.8f} kWh")
    print(f"gRPC/Proto sequential: {grpc_seq_mean:.2f} ± {grpc_seq_std:.2f} s  |  {grpc_seq_energy:.8f} kWh")
    print(f"  Latency reduction:  {((rest_seq_mean - grpc_seq_mean) / rest_seq_mean) * 100:.1f}%")
    print(f"  Energy reduction:   {((rest_seq_energy - grpc_seq_energy) / rest_seq_energy) * 100:.1f}%  (TDP-estimated)")

    # --- Concurrent ---
    print(f"\n=== Concurrent ({CONCURRENCY} parallel requests) ===")
    tracker = EmissionsTracker(project_name="REST_JSON_Concurrent", log_level="error")
    tracker.start()
    rest_con_mean, rest_con_std = run_repeated(benchmark_rest_concurrent, events)
    rest_con_energy = tracker._total_energy.kWh; tracker.stop()

    tracker = EmissionsTracker(project_name="gRPC_Protobuf_Concurrent", log_level="error")
    tracker.start()
    grpc_con_mean, grpc_con_std = run_repeated(benchmark_grpc_concurrent, events)
    grpc_con_energy = tracker._total_energy.kWh; tracker.stop()

    print(f"REST/JSON  concurrent: {rest_con_mean:.2f} ± {rest_con_std:.2f} s  |  {rest_con_energy:.8f} kWh")
    print(f"gRPC/Proto concurrent: {grpc_con_mean:.2f} ± {grpc_con_std:.2f} s  |  {grpc_con_energy:.8f} kWh")
    print(f"  Latency reduction:  {((rest_con_mean - grpc_con_mean) / rest_con_mean) * 100:.1f}%")
    print(f"  Energy reduction:   {((rest_con_energy - grpc_con_energy) / rest_con_energy) * 100:.1f}%  (TDP-estimated)")
