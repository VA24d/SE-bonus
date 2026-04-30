import threading
import time
import json
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Configuration
NETWORK_DELAY = 0.010  # 10ms simulated network RTT
PROCESSING_TIME = 0.050 # 50ms simulated CPU/DB work per service

class ServiceA(BaseHTTPRequestHandler):
    def do_POST(self):
        # Simulate network latency on incoming
        time.sleep(NETWORK_DELAY / 2)
        
        # Determine if this is chain or fan-out
        path = self.path
        
        # Do work
        time.sleep(PROCESSING_TIME)
        
        if path == "/chain":
            # In Chain, A calls B synchronously
            req = urllib.request.Request("http://127.0.0.1:8002/chain", method="POST")
            try:
                urllib.request.urlopen(req)
            except Exception:
                pass
                
        # Respond
        time.sleep(NETWORK_DELAY / 2)
        self.send_response(200)
        self.end_headers()

class ServiceB(BaseHTTPRequestHandler):
    def do_POST(self):
        time.sleep(NETWORK_DELAY / 2)
        time.sleep(PROCESSING_TIME)
        
        if self.path == "/chain":
            # In Chain, B calls C synchronously
            req = urllib.request.Request("http://127.0.0.1:8003/chain", method="POST")
            try:
                urllib.request.urlopen(req)
            except Exception:
                pass
                
        time.sleep(NETWORK_DELAY / 2)
        self.send_response(200)
        self.end_headers()

class ServiceC(BaseHTTPRequestHandler):
    def do_POST(self):
        time.sleep(NETWORK_DELAY / 2)
        time.sleep(PROCESSING_TIME)
        # End of chain or independent fan-out
        time.sleep(NETWORK_DELAY / 2)
        self.send_response(200)
        self.end_headers()

def start_servers():
    server_a = ThreadingHTTPServer(('127.0.0.1', 8001), ServiceA)
    server_b = ThreadingHTTPServer(('127.0.0.1', 8002), ServiceB)
    server_c = ThreadingHTTPServer(('127.0.0.1', 8003), ServiceC)
    
    threading.Thread(target=server_a.serve_forever, daemon=True).start()
    threading.Thread(target=server_b.serve_forever, daemon=True).start()
    threading.Thread(target=server_c.serve_forever, daemon=True).start()
    time.sleep(0.5) # Wait for servers to spin up

def run_chain_benchmark(num_events):
    start = time.perf_counter()
    for _ in range(num_events):
        req = urllib.request.Request("http://127.0.0.1:8001/chain", method="POST")
        try:
            urllib.request.urlopen(req)
        except Exception:
            pass
    return time.perf_counter() - start

def run_fanout_benchmark(num_events):
    start = time.perf_counter()
    
    def send_to_service(port):
        req = urllib.request.Request(f"http://127.0.0.1:{port}/fanout", method="POST")
        try:
            urllib.request.urlopen(req)
        except Exception:
            pass

    for _ in range(num_events):
        threads = [
            threading.Thread(target=send_to_service, args=(8001,)),
            threading.Thread(target=send_to_service, args=(8002,)),
            threading.Thread(target=send_to_service, args=(8003,))
        ]
        for t in threads: t.start()
        for t in threads: t.join()
        
    return time.perf_counter() - start

if __name__ == "__main__":
    print("Spinning up physical Python HTTP microservices (Ports 8001, 8002, 8003)...")
    start_servers()
    
    EVENTS = 50
    print(f"Running Sequential Chain HTTP topology ({EVENTS} events)...")
    chain_time = run_chain_benchmark(EVENTS)
    print(f"-> Chain Latency: {chain_time:.2f} seconds")
    
    print(f"Running Parallel Fan-Out HTTP topology ({EVENTS} events)...")
    fanout_time = run_fanout_benchmark(EVENTS)
    print(f"-> Fan-Out Latency: {fanout_time:.2f} seconds")
    
    print("\n--- RESULTS ---")
    print(f"Latency Reduction: {((chain_time - fanout_time) / chain_time) * 100:.1f}%")
