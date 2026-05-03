"""
Mathematical model of RabbitMQ vs Kafka CPU utilization scaling.

Model equations (parameterized from industry benchmarks):
  U_RMQ(N)   = 2.0 + 4.5 * (N/1000)^1.5   [super-linear: in-memory GC pressure]
  U_Kafka(N) = 12.0 + 1.5 * (N/1000)       [linear: log-batching + zero-copy]

Crossover solved analytically by binary search (no closed form for N^1.5 = linear).
"""
import math


def u_rmq(n):
    return min(2.0 + 4.5 * (n / 1000) ** 1.5, 100.0)


def u_kafka(n):
    return min(12.0 + 1.5 * (n / 1000), 100.0)


def efficiency(rate, cpu):
    """Messages per second per 1% CPU (higher = better)."""
    return rate / cpu if cpu < 100 else 0.0


def find_crossover(lo=100, hi=100_000, tol=1):
    """
    Binary search for N where U_RMQ(N) == U_Kafka(N).
    Returns the crossover message rate to within `tol` msg/s.
    """
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if u_rmq(mid) > u_kafka(mid):
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def run_simulation():
    crossover = find_crossover()
    print("=== Message Broker CPU Utilization Model ===")
    print(f"  U_RMQ(N)   = 2.0 + 4.5·(N/1000)^1.5  [capped at 100%]")
    print(f"  U_Kafka(N) = 12.0 + 1.5·(N/1000)      [capped at 100%]")
    print(f"\n  Analytical crossover point: {crossover:.0f} msg/s")
    print(f"  (RabbitMQ more efficient below this; Kafka more efficient above)\n")

    test_rates = [1000, 2000, 4000, int(crossover), 5000, 10000, 20000, 50000]
    # deduplicate and sort
    test_rates = sorted(set(test_rates))

    print(f"{'Msg Rate (/s)':<15} | {'RabbitMQ CPU%':<16} | {'Kafka CPU%':<14} | {'Eff Winner'}")
    print("-" * 72)

    for rate in test_rates:
        rmq_cpu = u_rmq(rate)
        kaf_cpu = u_kafka(rate)
        rmq_eff = efficiency(rate, rmq_cpu)
        kaf_eff = efficiency(rate, kaf_cpu)

        rmq_str = f"{rmq_cpu:.1f}%" if rmq_cpu < 100 else "SATURATED"
        kaf_str = f"{kaf_cpu:.1f}%" if kaf_cpu < 100 else "SATURATED"

        if rmq_cpu >= 100 and kaf_cpu >= 100:
            winner = "Both saturated"
        elif rmq_eff > kaf_eff:
            pct = (rmq_eff - kaf_eff) / kaf_eff * 100 if kaf_eff > 0 else float('inf')
            winner = f"RabbitMQ (+{pct:.0f}% eff)"
        else:
            pct = (kaf_eff - rmq_eff) / rmq_eff * 100 if rmq_eff > 0 else float('inf')
            winner = f"Kafka (+{pct:.0f}% eff)"

        marker = " ← crossover" if rate == int(crossover) else ""
        print(f"{rate:<15} | {rmq_str:<16} | {kaf_str:<14} | {winner}{marker}")

    print(f"\nSaturation points:")
    # RabbitMQ saturates when U_RMQ(N) = 100 → 4.5*(N/1000)^1.5 = 98 → N = 1000*(98/4.5)^(2/3)
    rmq_sat = 1000 * (98.0 / 4.5) ** (2.0 / 3.0)
    # Kafka saturates when U_Kafka(N) = 100 → 1.5*(N/1000) = 88 → N = 88000/1.5
    kaf_sat = (88.0 / 1.5) * 1000
    print(f"  RabbitMQ saturates at ~{rmq_sat:.0f} msg/s")
    print(f"  Kafka saturates at    ~{kaf_sat:.0f} msg/s")


if __name__ == '__main__':
    run_simulation()
