import threading
import time
import statistics
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Configuration
NETWORK_DELAY = 0.010   # 10ms simulated network RTT per hop
PROCESSING_TIME = 0.050  # 50ms simulated I/O-bound work per service
NUM_EVENTS = 50
NUM_RUNS = 5  # repeated runs for mean ± stddev


class ServiceA(BaseHTTPRequestHandler):
    def do_POST(self):
        time.sleep(NETWORK_DELAY / 2)
        time.sleep(PROCESSING_TIME)
        if self.path == "/chain":
            req = urllib.request.Request("http://127.0.0.1:8002/chain", method="POST")
            try:
                urllib.request.urlopen(req)
            except Exception:
                pass
        time.sleep(NETWORK_DELAY / 2)
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress per-request logs


class ServiceB(BaseHTTPRequestHandler):
    def do_POST(self):
        time.sleep(NETWORK_DELAY / 2)
        time.sleep(PROCESSING_TIME)
        if self.path == "/chain":
            req = urllib.request.Request("http://127.0.0.1:8003/chain", method="POST")
            try:
                urllib.request.urlopen(req)
            except Exception:
                pass
        time.sleep(NETWORK_DELAY / 2)
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass


class ServiceC(BaseHTTPRequestHandler):
    def do_POST(self):
        time.sleep(NETWORK_DELAY / 2)
        time.sleep(PROCESSING_TIME)
        time.sleep(NETWORK_DELAY / 2)
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass


def start_servers():
    for port, handler in [(8001, ServiceA), (8002, ServiceB), (8003, ServiceC)]:
        srv = ThreadingHTTPServer(('127.0.0.1', port), handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    time.sleep(0.5)


def run_chain_once(num_events):
    """Sequential chain: caller → A → B → C (blocking at each hop)."""
    latencies = []
    for _ in range(num_events):
        t0 = time.perf_counter()
        req = urllib.request.Request("http://127.0.0.1:8001/chain", method="POST")
        try:
            urllib.request.urlopen(req)
        except Exception:
            pass
        latencies.append(time.perf_counter() - t0)
    return sum(latencies), latencies  # (total_s, per_event_list)


def run_fanout_once(num_events):
    """Parallel fan-out: caller dispatches A, B, C concurrently per event."""
    latencies = []

    def send(port):
        req = urllib.request.Request(f"http://127.0.0.1:{port}/fanout", method="POST")
        try:
            urllib.request.urlopen(req)
        except Exception:
            pass

    for _ in range(num_events):
        t0 = time.perf_counter()
        threads = [threading.Thread(target=send, args=(p,)) for p in (8001, 8002, 8003)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        latencies.append(time.perf_counter() - t0)
    return sum(latencies), latencies


if __name__ == "__main__":
    print("Spinning up physical Python HTTP microservices (ports 8001, 8002, 8003)...")
    start_servers()

    print(f"\nRunning {NUM_RUNS} repeated runs of {NUM_EVENTS} events each...\n")

    # --- Chain ---
    chain_totals = []
    chain_per_event_means = []
    for run in range(NUM_RUNS):
        total, per_event = run_chain_once(NUM_EVENTS)
        chain_totals.append(total)
        chain_per_event_means.append(statistics.mean(per_event) * 1000)  # ms
        print(f"  Chain run {run+1}: total={total:.3f}s  per-event mean={chain_per_event_means[-1]:.1f}ms")

    chain_mean = statistics.mean(chain_totals)
    chain_std = statistics.stdev(chain_totals)
    chain_pe_mean = statistics.mean(chain_per_event_means)

    # --- Fan-Out ---
    fanout_totals = []
    fanout_per_event_means = []
    for run in range(NUM_RUNS):
        total, per_event = run_fanout_once(NUM_EVENTS)
        fanout_totals.append(total)
        fanout_per_event_means.append(statistics.mean(per_event) * 1000)
        print(f"  Fan-Out run {run+1}: total={total:.3f}s  per-event mean={fanout_per_event_means[-1]:.1f}ms")

    fanout_mean = statistics.mean(fanout_totals)
    fanout_std = statistics.stdev(fanout_totals)
    fanout_pe_mean = statistics.mean(fanout_per_event_means)

    print("\n--- TOPOLOGY RESULTS ---")
    print(f"Chain   total latency: {chain_mean:.3f} ± {chain_std:.3f} s  (mean ± stddev, n={NUM_RUNS})")
    print(f"Fan-Out total latency: {fanout_mean:.3f} ± {fanout_std:.3f} s  (mean ± stddev, n={NUM_RUNS})")
    print(f"Chain   per-event:     {chain_pe_mean:.1f} ms mean")
    print(f"Fan-Out per-event:     {fanout_pe_mean:.1f} ms mean")
    print(f"Latency reduction:     {((chain_mean - fanout_mean) / chain_mean) * 100:.1f}%")
    print(f"\nTheoretical minimum:")
    print(f"  Chain   = {NUM_EVENTS} × 3 × {int((PROCESSING_TIME + NETWORK_DELAY)*1000)}ms = {NUM_EVENTS * 3 * (PROCESSING_TIME + NETWORK_DELAY):.1f}s")
    print(f"  Fan-Out = {NUM_EVENTS} × {int((PROCESSING_TIME + NETWORK_DELAY)*1000)}ms = {NUM_EVENTS * (PROCESSING_TIME + NETWORK_DELAY):.1f}s")
