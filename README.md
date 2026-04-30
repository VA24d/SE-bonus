# Towards Energy-Aware Design Choices in Event-Driven Microservices

This repository contains the empirical benchmarking suite and raw LaTeX paper source for the study on energy-aware microservice architectural design.

## Project Overview
As enterprise systems transition toward cloud-native microservices, structural decisions regarding communication topology, message broker selection, and data serialization heavily influence hardware resource consumption. This repository provides Python-based simulations and physical proxy-metric benchmarks that prove how to lower the operational energy component of the Software Carbon Intensity (SCI) specification.

## Benchmark Scripts
The `src/` directory contains four standalone Python scripts to measure various energy-related proxy metrics:

1. **Serialization Benchmark (`benchmark_serialization.py`)**
   - Simulates 1,000,000 business events and compares JSON, MsgPack, and a packed binary surrogate (simulating Protocol Buffers).
   - Utilizes `CodeCarbon` to measure true physical CPU power draw (kWh) and carbon emissions during parsing.
   - *Result:* Proves an 85.5% reduction in physical energy using binary formats.

2. **Network Topology Benchmark (`microservices_topology.py`)**
   - Spawns three local Python `ThreadingHTTPServer` instances simulating independent microservices.
   - Injects 10ms of network latency per hop and compares Sequential Chain requests vs. Parallel Fan-out patterns.
   - *Result:* Proves a 64.5% latency reduction via parallel fan-out choreography.

3. **Memory Footprint Benchmark (`benchmark_memory.py`)**
   - Uses Python's `tracemalloc` to measure the peak RAM consumption during massive deserialization workloads.
   - *Result:* Proves a nearly 40% reduction in peak RAM footprint, saving baseline memory power.

4. **Broker Simulation (`benchmark_broker_simulation.py`)**
   - Implements an $O(N)$ vs $O(N^{1.5})$ mathematical CPU scaling model based on industry benchmarks comparing Apache Kafka vs RabbitMQ throughput efficiency.

## Installation & Usage

### Dependencies
Ensure you have an Anaconda or standard Python 3.10+ environment active. Install the required telemetry libraries:
```bash
pip install codecarbon msgpack matplotlib
```

### Running the Benchmarks
Simply execute any of the scripts from the root directory:
```bash
python src/benchmark_serialization.py
python src/microservices_topology.py
python src/benchmark_memory.py
python src/benchmark_broker_simulation.py
```

### Compiling the Paper
The final academic paper is included as `paper.tex`. You can compile it into a PDF using the Tectonic LaTeX engine:
```bash
./tectonic paper.tex
```

## Contributing
These scripts serve as an open-source framework for validating green software engineering practices. Pull requests extending these benchmarks to deploy actual containerized brokers or complex Mininet network topologies are welcome!
