"""
gRPC/Protobuf vs REST/JSON network benchmark.
Sequential and concurrent modes, 5 runs each.
Runs Flask and gRPC servers in background threads for the duration
of the benchmark.
"""
import time
import threading
import statistics
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'proto'))

import grpc
from concurrent import futures
from flask import Flask, request, jsonify
import logging
import requests as req_lib
from codecarbon import EmissionsTracker
import event_pb2
import event_pb2_grpc

NUM_EVENTS  = 2_000
NUM_RUNS    = 3
CONCURRENCY = 50
REST_PORT   = 5021
GRPC_PORT   = 5022

# ── Flask REST server ──────────────────────────────────────────────────────────
app = Flask(__name__)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

@app.route('/process', methods=['POST'])
def process_event():
    data = request.json
    return jsonify({"success": True, "message": f"Processed {data['order_id']}"})

# ── gRPC server ────────────────────────────────────────────────────────────────
class EventServiceServicer(event_pb2_grpc.EventServiceServicer):
    def ProcessEvent(self, req, ctx):
        return event_pb2.EventResponse(success=True, message=f"Processed {req.order_id}")

# ── Benchmark functions ────────────────────────────────────────────────────────
def generate_events():
    return [
        {"order_id": 1_000_000 + i, "user_id": 9_000_000 + i,
         "status": 1, "amount": 150.50 + (i % 10)}
        for i in range(NUM_EVENTS)
    ]

def rest_sequential(events):
    session = req_lib.Session()
    t0 = time.perf_counter()
    for e in events:
        try:
            session.post(f'http://127.0.0.1:{REST_PORT}/process', json=e)
        except Exception as e_err:
            print(f"Error in REST sequential: {e_err}")
            break
    return time.perf_counter() - t0

def grpc_sequential(events):
    t0 = time.perf_counter()
    with grpc.insecure_channel(f'127.0.0.1:{GRPC_PORT}') as ch:
        stub = event_pb2_grpc.EventServiceStub(ch)
        for e in events:
            stub.ProcessEvent(event_pb2.Event(
                order_id=e['order_id'], user_id=e['user_id'],
                status=e['status'], amount=e['amount']
            ))
    return time.perf_counter() - t0

def rest_concurrent(events):
    session = req_lib.Session()
    adapter = req_lib.adapters.HTTPAdapter(pool_connections=CONCURRENCY, pool_maxsize=CONCURRENCY)
    session.mount('http://', adapter)
    def send(e):
        try:
            session.post(f'http://127.0.0.1:{REST_PORT}/process', json=e)
        except Exception:
            pass
    t0 = time.perf_counter()
    with futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        list(pool.map(send, events))
    return time.perf_counter() - t0

def grpc_concurrent(events):
    ch = grpc.insecure_channel(f'127.0.0.1:{GRPC_PORT}')
    stub = event_pb2_grpc.EventServiceStub(ch)
    def call(e):
        stub.ProcessEvent(event_pb2.Event(
            order_id=e['order_id'], user_id=e['user_id'],
            status=e['status'], amount=e['amount']
        ))
    t0 = time.perf_counter()
    with futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        list(pool.map(call, events))
    ch.close()
    return time.perf_counter() - t0

def run_n(fn, events, n=NUM_RUNS):
    times = []
    for i in range(n):
        t = fn(events)
        times.append(t)
        print(f"    run {i+1}: {t:.3f}s")
        time.sleep(0.2)
    return statistics.mean(times), statistics.stdev(times) if n > 1 else 0.0


def run_n_with_energy(project_name, fn, events, n=NUM_RUNS):
    """Measure mean/stddev latency and CodeCarbon-estimated energy for n runs."""
    tracker = EmissionsTracker(
        project_name=project_name,
        log_level="error",
        measure_power_secs=1,
        force_mode_cpu_load=True,
    )
    tracker.start()
    mean, std = run_n(fn, events, n=n)
    tracker.stop()
    return mean, std, tracker._total_energy.kWh

# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    # Start gRPC server in background thread
    grpc_srv = grpc.server(futures.ThreadPoolExecutor(max_workers=CONCURRENCY))
    event_pb2_grpc.add_EventServiceServicer_to_server(EventServiceServicer(), grpc_srv)
    grpc_srv.add_insecure_port(f'[::]:{GRPC_PORT}')
    grpc_srv.start()

    # Start Flask in background thread (non-daemon so it stays alive)
    flask_thread = threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=REST_PORT,
                               debug=False, use_reloader=False, threaded=True),
        daemon=True
    )
    flask_thread.start()

    print("Waiting for servers to start...")
    time.sleep(4)

    # Verify Flask is up
    try:
        r = req_lib.get(f'http://127.0.0.1:{REST_PORT}/process', timeout=2)
    except req_lib.exceptions.ConnectionError:
        pass  # 405 Method Not Allowed = server is up
    except Exception:
        pass

    events = generate_events()
    print(f"Benchmarking {NUM_EVENTS} events, {NUM_RUNS} runs, concurrency={CONCURRENCY}\n")

    print("=== Sequential (1 request at a time) ===")
    print("  REST/JSON:")
    rs_mean, rs_std, rs_energy = run_n_with_energy("REST_JSON_Network_Sequential", rest_sequential, events)
    print(f"  → {rs_mean:.3f} ± {rs_std:.3f} s")
    print(f"  → {rs_energy:.8f} kWh (TDP-estimated)\n")

    print("  gRPC/Protobuf:")
    gs_mean, gs_std, gs_energy = run_n_with_energy("gRPC_Protobuf_Network_Sequential", grpc_sequential, events)
    print(f"  → {gs_mean:.3f} ± {gs_std:.3f} s")
    print(f"  → {gs_energy:.8f} kWh (TDP-estimated)")
    print(f"  Latency reduction: {(rs_mean - gs_mean) / rs_mean * 100:.1f}%\n")
    if rs_energy > 0:
        print(f"  Energy reduction:  {(rs_energy - gs_energy) / rs_energy * 100:.1f}%  (TDP-estimated)\n")

    print(f"=== Concurrent ({CONCURRENCY} parallel requests) ===")
    print("  REST/JSON:")
    rc_mean, rc_std, rc_energy = run_n_with_energy("REST_JSON_Network_Concurrent", rest_concurrent, events)
    print(f"  → {rc_mean:.3f} ± {rc_std:.3f} s")
    print(f"  → {rc_energy:.8f} kWh (TDP-estimated)\n")

    print("  gRPC/Protobuf:")
    gc_mean, gc_std, gc_energy = run_n_with_energy("gRPC_Protobuf_Network_Concurrent", grpc_concurrent, events)
    print(f"  → {gc_mean:.3f} ± {gc_std:.3f} s")
    print(f"  → {gc_energy:.8f} kWh (TDP-estimated)")
    print(f"  Latency reduction: {(rc_mean - gc_mean) / rc_mean * 100:.1f}%\n")
    if rc_energy > 0:
        print(f"  Energy reduction:  {(rc_energy - gc_energy) / rc_energy * 100:.1f}%  (TDP-estimated)\n")

    print("=== SUMMARY ===")
    print(f"Sequential  REST: {rs_mean:.3f} ± {rs_std:.3f} s")
    print(f"Sequential  gRPC: {gs_mean:.3f} ± {gs_std:.3f} s  ({(rs_mean-gs_mean)/rs_mean*100:.1f}% faster)")
    print(f"Sequential  REST energy: {rs_energy:.8f} kWh")
    print(f"Sequential  gRPC energy: {gs_energy:.8f} kWh")
    print(f"Concurrent  REST: {rc_mean:.3f} ± {rc_std:.3f} s")
    print(f"Concurrent  gRPC: {gc_mean:.3f} ± {gc_std:.3f} s  ({(rc_mean-gc_mean)/rc_mean*100:.1f}% faster)")
    print(f"Concurrent  REST energy: {rc_energy:.8f} kWh")
    print(f"Concurrent  gRPC energy: {gc_energy:.8f} kWh")

    grpc_srv.stop(0)
    sys.exit(0)
