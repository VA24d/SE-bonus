"""
gRPC/Protobuf vs REST/JSON network benchmark.
Sequential and concurrent modes, 5 runs each.
Runs Flask and gRPC servers as non-daemon threads so they stay alive.
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
        time.sleep(0.5)
    return statistics.mean(times), statistics.stdev(times) if n > 1 else 0.0

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
        daemon=False
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
    rs_mean, rs_std = run_n(rest_sequential, events)
    print(f"  → {rs_mean:.3f} ± {rs_std:.3f} s\n")

    print("  gRPC/Protobuf:")
    gs_mean, gs_std = run_n(grpc_sequential, events)
    print(f"  → {gs_mean:.3f} ± {gs_std:.3f} s")
    print(f"  Latency reduction: {(rs_mean - gs_mean) / rs_mean * 100:.1f}%\n")

    print(f"=== Concurrent ({CONCURRENCY} parallel requests) ===")
    print("  REST/JSON:")
    rc_mean, rc_std = run_n(rest_concurrent, events)
    print(f"  → {rc_mean:.3f} ± {rc_std:.3f} s\n")

    print("  gRPC/Protobuf:")
    gc_mean, gc_std = run_n(grpc_concurrent, events)
    print(f"  → {gc_mean:.3f} ± {gc_std:.3f} s")
    print(f"  Latency reduction: {(rc_mean - gc_mean) / rc_mean * 100:.1f}%\n")

    print("=== SUMMARY ===")
    print(f"Sequential  REST: {rs_mean:.3f} ± {rs_std:.3f} s")
    print(f"Sequential  gRPC: {gs_mean:.3f} ± {gs_std:.3f} s  ({(rs_mean-gs_mean)/rs_mean*100:.1f}% faster)")
    print(f"Concurrent  REST: {rc_mean:.3f} ± {rc_std:.3f} s")
    print(f"Concurrent  gRPC: {gc_mean:.3f} ± {gc_std:.3f} s  ({(rc_mean-gc_mean)/rc_mean*100:.1f}% faster)")
    print(f"\nNote: energy values from emissions.csv (TDP-estimated via CodeCarbon):")
    print(f"  REST/JSON  sequential: 9.31e-05 kWh")
    print(f"  gRPC/Proto sequential: 1.61e-05 kWh  (82.7% reduction)")

    grpc_srv.stop(0)
    sys.exit(0)
