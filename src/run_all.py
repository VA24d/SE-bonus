"""
Single-command runner for the full paper benchmark suite.

Executes, in order:
  1. Broker CPU model             (<1 s, analytical)
  2. Topology latency              (~35 s, real HTTP servers)
  3. Serialization                 (~3 min, 1M events × 5 runs)
  4. gRPC vs REST network          (~30 s, 2k events × 5 runs)
  5. Figure regeneration           (matplotlib -> PDFs)

Each step is a subprocess so failures are isolated. Pass --skip <name>
to drop any step:  python src/run_all.py --skip serialization

Add --power to wrap each step in a powermetrics capture (requires sudo
on macOS, Apple Silicon). Raw samples land in src/powermetrics_<step>.txt;
post-process with: python src/parse_power.py src/powermetrics_*.txt
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / "src"

STEPS = [
    ("broker",        [sys.executable, str(SRC / "benchmark_broker_simulation.py")]),
    ("topology",      [sys.executable, str(SRC / "microservices_topology.py")]),
    ("serialization", [sys.executable, str(SRC / "benchmark_serialization.py")]),
    ("grpc",          [sys.executable, str(SRC / "run_grpc_benchmark.py")]),
    ("figures",       [sys.executable, str(SRC / "generate_graphs.py")]),
]


def run_step(name, cmd, use_power):
    banner = f"[{name}]"
    print(f"\n{'=' * 72}\n{banner:>10}  {' '.join(cmd)}\n{'=' * 72}")

    if not use_power:
        t0 = time.perf_counter()
        rc = subprocess.call(cmd, cwd=ROOT)
        dt = time.perf_counter() - t0
        print(f"{banner}  exit={rc}  wall={dt:.1f}s")
        return rc, dt, None

    # powermetrics wrapper (macOS ARM64, requires sudo)
    pm_out = SRC / f"powermetrics_{name}.txt"
    print(f"{banner}  starting powermetrics -> {pm_out}")
    with open(pm_out, "w") as f:
        pm = subprocess.Popen(
            ["sudo", "-n", "powermetrics", "--samplers", "cpu_power", "-i", "500"],
            stdout=f, stderr=subprocess.DEVNULL,
        )
    time.sleep(1)
    try:
        t0 = time.perf_counter()
        rc = subprocess.call(cmd, cwd=ROOT)
        dt = time.perf_counter() - t0
    finally:
        time.sleep(1)
        pm.terminate()
        try:
            pm.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pm.kill()
    print(f"{banner}  exit={rc}  wall={dt:.1f}s  power_log={pm_out}")
    return rc, dt, pm_out


def main():
    ap = argparse.ArgumentParser(description="Run the full benchmark suite.")
    ap.add_argument("--skip", action="append", default=[],
                    help=f"skip a step (repeatable). one of: {', '.join(n for n, _ in STEPS)}")
    ap.add_argument("--only", action="append", default=[],
                    help="run only these steps (repeatable)")
    ap.add_argument("--power", action="store_true",
                    help="wrap each step in macOS powermetrics capture (needs sudo)")
    args = ap.parse_args()

    if args.power:
        # validate passwordless sudo up front
        rc = subprocess.call(["sudo", "-n", "true"], stderr=subprocess.DEVNULL)
        if rc != 0:
            print("!! --power needs passwordless sudo for powermetrics.")
            print("   Run once:  sudo -v   (then re-invoke this script)")
            sys.exit(2)

    picked = [(n, c) for n, c in STEPS
              if (not args.only or n in args.only) and n not in args.skip]

    print(f"Plan: {', '.join(n for n, _ in picked)}")
    if args.power:
        print("Power capture: ON (powermetrics --samplers cpu_power)")

    results = []
    for name, cmd in picked:
        rc, dt, pm = run_step(name, cmd, args.power)
        results.append((name, rc, dt, pm))

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    for name, rc, dt, pm in results:
        status = "OK" if rc == 0 else f"FAIL rc={rc}"
        line = f"  {name:<15} {status:<12} {dt:6.1f}s"
        if pm:
            line += f"  power_log={pm.name}"
        print(line)

    if args.power:
        power_logs = [str(pm) for _, _, _, pm in results if pm]
        if power_logs:
            print("\nParse power samples:")
            print(f"  python src/parse_power.py {' '.join(power_logs)}")

    failed = [n for n, rc, *_ in results if rc != 0]
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
