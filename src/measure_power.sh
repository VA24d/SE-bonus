#!/bin/bash
# Capture actual CPU wattage via macOS powermetrics while running a benchmark.
# Apple Silicon has no Intel RAPL, so this is the ground-truth hardware path.
#
# USAGE:
#   sudo ./src/measure_power.sh <benchmark>
#     benchmark ∈ { serialization | grpc | topology | broker | idle }
#
# Output: src/powermetrics_<benchmark>.txt  (raw samples; parse with parse_power.py)

set -euo pipefail

BENCH="${1:-serialization}"
OUT="src/powermetrics_${BENCH}.txt"
SAMPLE_MS=500

echo "==> Warming up (3 s idle baseline capture)…"
powermetrics --samplers cpu_power -i "$SAMPLE_MS" -n 6 > "src/powermetrics_idle.txt" 2>/dev/null &
PM_IDLE=$!
wait "$PM_IDLE"

echo "==> Launching powermetrics sampler (sample every ${SAMPLE_MS} ms)…"
powermetrics --samplers cpu_power -i "$SAMPLE_MS" > "$OUT" 2>/dev/null &
PM_PID=$!

# Give sampler 1s to settle
sleep 1

echo "==> Running benchmark: $BENCH"
case "$BENCH" in
  serialization) python src/benchmark_serialization.py ;;
  grpc)          python src/run_grpc_benchmark.py      ;;
  topology)      python src/microservices_topology.py  ;;
  broker)        python src/benchmark_broker_simulation.py ;;
  idle)          sleep 15 ;;
  *) echo "unknown bench: $BENCH"; kill "$PM_PID"; exit 1 ;;
esac

echo "==> Stopping sampler"
kill "$PM_PID" 2>/dev/null || true
wait "$PM_PID" 2>/dev/null || true

echo "==> Wrote $OUT"
echo "==> Parse with: python src/parse_power.py $OUT"
