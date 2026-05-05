# Towards Energy-Aware Design Choices in Event-Driven Microservices

Empirical benchmarking suite and LaTeX source for a study on sustainable
architectural decisions in event-driven microservices. Quantifies how **topology
choreography**, **message broker selection**, and **data serialization format**
affect resource-use proxy metrics that map to the operational energy term ($E$)
of the [Software Carbon Intensity (SCI) specification](https://greensoftware.foundation/sci)
(ISO/IEC 21031:2024).

- 📄 **Paper:** [`paper.pdf`](./paper.pdf) · [`paper.tex`](./paper.tex)
- 🧪 **Benchmarks:** [`src/`](./src)
- 🔗 **Repo:** [github.com/VA24d/SE-bonus](https://github.com/VA24d/SE-bonus)

---

## Results Summary

| Dimension | Finding | Script | Figure |
|---|---|---|---|
| Topology (Chain vs Parallel Fan-Out) | **66.1%** end-to-end latency reduction | [`src/microservices_topology.py`](src/microservices_topology.py) | `topology_chart.pdf` |
| Serialization (JSON vs Protobuf, 1M events) | **77.5%** payload + **27.7%** CPU + **15.8%** TDP-est. energy reduction | [`src/benchmark_serialization.py`](src/benchmark_serialization.py) | `serialization_chart.pdf` |
| Broker (RabbitMQ vs Kafka, CPU model) | Crossover at **2,034 msg/s** | [`src/benchmark_broker_simulation.py`](src/benchmark_broker_simulation.py) | `broker_chart.pdf` |
| gRPC/Protobuf vs REST/JSON (network) | **84.3%** latency + **82.7%** TDP-est. energy reduction | [`src/run_grpc_benchmark.py`](src/run_grpc_benchmark.py) | — |

Energy figures come from [CodeCarbon](https://github.com/mlco2/codecarbon),
wired into [`benchmark_serialization.py`](src/benchmark_serialization.py) and
[`run_grpc_benchmark.py`](src/run_grpc_benchmark.py). Both were executed and
their readings feed paper §IV-A (logged to [`emissions.csv`](./emissions.csv)).
Intel RAPL is not available on Apple Silicon (ARM64), so CodeCarbon falls back
to TDP × CPU-utilization estimation — absolute kWh values are **upper-bound
proxies**, valid for comparison, not physical wattage. The other three scripts
report proxy metrics only (latency, CPU time, peak RAM, modeled CPU%).

---

## Repository Layout

```
.
├── paper.tex                       # IEEE conference paper source
├── paper.pdf                       # Compiled paper (with all cited references in references/)
├── abstract.txt                    # Final abstract
├── preliminary abstract.pdf        # Research proposal (original scope)
├── requirements.txt                # Pinned Python deps
├── serialization_chart.pdf         # Generated figure
├── topology_chart.pdf              # Generated figure
├── broker_chart.pdf                # Generated figure
├── emissions.csv                   # CodeCarbon energy log
├── references/                     # Cited PDFs + notes
└── src/
    ├── benchmark_serialization.py      # JSON vs MsgPack vs Protobuf (paper §4.1)
    ├── microservices_topology.py       # Chain vs Fan-Out, real HTTP (paper §4.2)
    ├── benchmark_broker_simulation.py  # RMQ vs Kafka CPU model (paper §4.3)
    ├── run_grpc_benchmark.py           # gRPC/Protobuf vs REST/JSON (paper §4.1)
    ├── run_all.py                       # Orchestrator: runs every benchmark + figures
    ├── generate_graphs.py              # Chart PDF generator
    ├── measure_power.sh                 # macOS powermetrics capture wrapper (sudo)
    ├── parse_power.py                   # Parse powermetrics samples -> Joules / mWh
    ├── benchmark_topology.py           # Auxiliary: asyncio-sim topology (not cited)
    ├── benchmark_memory.py             # Auxiliary: peak RAM comparison (not cited)
    └── proto/
        ├── event.proto                 # Protobuf schema
        ├── event_pb2.py                # Generated bindings
        └── event_pb2_grpc.py           # Generated gRPC stubs
```

---

## Reproducing the Paper

### 1. Environment

Requires **Python 3.12+** (tested on 3.12.12, Apple M2 ARM64).

```bash
pip install -r requirements.txt
```

### 2. Regenerate Protobuf bindings (optional)

Generated stubs are committed. To rebuild from `event.proto`:

```bash
cd src
python -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. proto/event.proto
```

### 3. Run benchmarks

From repo root, one command runs the whole suite:

```bash
python src/run_all.py
```

Individual steps (matching the paper sections):

```bash
python src/benchmark_broker_simulation.py   # §IV-C, <1s
python src/microservices_topology.py        # §IV-B, ~35s
python src/benchmark_serialization.py       # §IV-A, ~3min
python src/run_grpc_benchmark.py            # §IV-A, ~30s
```

Runner flags:
- `--only <name>` / `--skip <name>` — pick or drop steps
- `--power` — wrap each step in a macOS `powermetrics` capture for real
  CPU wattage (requires passwordless sudo; run `sudo -v` first, then
  post-process with `python src/parse_power.py src/powermetrics_*.txt`)

### 4. Regenerate figures

```bash
python src/generate_graphs.py
```

Emits `serialization_chart.pdf`, `topology_chart.pdf`, `broker_chart.pdf` in
the repo root.

The compiled paper and all referenced source PDFs are already committed —
see [`paper.pdf`](./paper.pdf) and [`references/`](./references).

---

## Verification

Every paper claim was re-measured against a fresh benchmark run; see
[`VERIFICATION_SUMMARY.md`](./VERIFICATION_SUMMARY.md) for the audit trail.
References were cross-checked against the source PDFs under [`references/`](./references).

---

## Notes on Methodology

- **Protobuf** is the real, compiled [`event_pb2`](src/proto/event_pb2.py)
  generated from [`event.proto`](src/proto/event.proto). Not a surrogate.
- **Topology** benchmark spawns three `ThreadingHTTPServer` instances on
  distinct ports; Chain blocks A→B→C while Fan-Out dispatches A, B, C in
  parallel threads. Both execute identical per-service work.
- **Broker** results come from an analytical CPU-scaling model parameterised
  from published benchmarks ([Kamiński et al. 2025](https://doi.org/10.35784/jcsi.7977)).
  Equations are printed verbatim by the script. No live brokers are deployed.
- **Energy** uses CodeCarbon's TDP-based estimator on ARM64. Absolute values
  should be read as comparative proxies only.

---

## Future Work

The preliminary proposal targeted a containerised 4–6 service testbed with
direct hardware energy telemetry. That remains future work (see paper §V).
This repo delivers the simulation phase.

---

## Citation

If you use this work, please cite:

```bibtex
@misc{vijay2026energyaware,
  author       = {Vijay},
  title        = {Towards Energy-Aware Design Choices in Event-Driven Microservices},
  year         = {2026},
  institution  = {IIIT Hyderabad},
  howpublished = {\url{https://github.com/VA24d/SE-bonus}}
}
```

---

## License & Contact

Open source for academic use. Issues and pull requests welcome — especially
contributions extending these benchmarks to containerised broker deployments,
Mininet topologies, or direct RAPL-based hardware energy capture.
