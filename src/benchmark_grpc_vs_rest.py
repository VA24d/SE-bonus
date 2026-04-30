import time
import requests
import threading
import json
import grpc
from concurrent import futures
from flask import Flask, request, jsonify
from codecarbon import EmissionsTracker

import event_pb2
import event_pb2_grpc

NUM_EVENTS = 10000
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
    # Simulate processing
    return jsonify({"success": True, "message": f"Processed {data['order_id']}"})

def run_rest_server():
    app.run(port=REST_PORT, debug=False, use_reloader=False)

# --- gRPC/PROTOBUF SERVER ---
class EventServiceServicer(event_pb2_grpc.EventServiceServicer):
    def ProcessEvent(self, request, context):
        return event_pb2.EventResponse(success=True, message=f"Processed {request.order_id}")

def run_grpc_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    event_pb2_grpc.add_EventServiceServicer_to_server(EventServiceServicer(), server)
    server.add_insecure_port(f'[::]:{GRPC_PORT}')
    server.start()
    server.wait_for_termination()

# --- CLIENT BENCHMARKS ---
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

def benchmark_rest_client(events):
    start = time.perf_counter()
    session = requests.Session() # Reuse connection to be fair to HTTP/1.1
    for e in events:
        response = session.post(f"http://127.0.0.1:{REST_PORT}/process", json=e)
    total_time = time.perf_counter() - start
    return total_time

def benchmark_grpc_client(events):
    start = time.perf_counter()
    with grpc.insecure_channel(f'127.0.0.1:{GRPC_PORT}') as channel:
        stub = event_pb2_grpc.EventServiceStub(channel)
        for e in events:
            msg = event_pb2.Event(
                order_id=e["order_id"],
                user_id=e["user_id"],
                status=e["status"],
                amount=e["amount"]
            )
            response = stub.ProcessEvent(msg)
    total_time = time.perf_counter() - start
    return total_time

if __name__ == "__main__":
    print("Starting REST/JSON server...")
    rest_thread = threading.Thread(target=run_rest_server, daemon=True)
    rest_thread.start()
    
    print("Starting gRPC/Protobuf server...")
    grpc_thread = threading.Thread(target=run_grpc_server, daemon=True)
    grpc_thread.start()
    
    # Wait for servers to start
    time.sleep(2)
    
    print(f"Generating {NUM_EVENTS} test events...")
    events = generate_events()
    
    print("\n--- Running REST/JSON Network Benchmark ---")
    tracker_rest = EmissionsTracker(project_name="REST_JSON_Network", log_level="error")
    tracker_rest.start()
    rest_time = benchmark_rest_client(events)
    rest_emissions = tracker_rest.stop()
    rest_energy = tracker_rest._total_energy.kWh
    print(f"Total Latency: {rest_time:.2f} seconds")
    print(f"Actual Energy Consumed: {rest_energy:.8f} kWh")
    
    print("\n--- Running gRPC/Protobuf Network Benchmark ---")
    tracker_grpc = EmissionsTracker(project_name="gRPC_Protobuf_Network", log_level="error")
    tracker_grpc.start()
    grpc_time = benchmark_grpc_client(events)
    grpc_emissions = tracker_grpc.stop()
    grpc_energy = tracker_grpc._total_energy.kWh
    print(f"Total Latency: {grpc_time:.2f} seconds")
    print(f"Actual Energy Consumed: {grpc_energy:.8f} kWh")
    
    print("\n--- EMPIRICAL NETWORK & SERIALIZATION SUMMARY ---")
    print(f"gRPC vs REST Latency Reduction: {((rest_time - grpc_time) / rest_time) * 100:.1f}%")
    print(f"gRPC vs REST Physical Energy Reduction: {((rest_energy - grpc_energy) / rest_energy) * 100:.1f}%")
