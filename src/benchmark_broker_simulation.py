import time

def simulate_rabbitmq(msg_rate):
    """
    RabbitMQ operates in-memory. Highly efficient at low rates.
    However, at high rates, state tracking and garbage collection
    cause CPU usage to scale non-linearly (simulated as O(N^1.5)).
    """
    base_cpu = 2.0  # Erlang VM base
    scaling_factor = (msg_rate / 1000) ** 1.5
    cpu_usage = base_cpu + (scaling_factor * 4.5)
    
    # Power efficiency = messages processed per 1% of CPU
    efficiency = msg_rate / cpu_usage if cpu_usage < 100 else 0
    return min(cpu_usage, 100.0), efficiency

def simulate_kafka(msg_rate):
    """
    Kafka uses a distributed append-only log. It has a higher baseline
    cost (JVM, polling, disk I/O), but due to zero-copy transfers and batching,
    it scales linearly O(N).
    """
    base_cpu = 12.0  # JVM & Polling base
    scaling_factor = (msg_rate / 1000)
    cpu_usage = base_cpu + (scaling_factor * 1.5)
    
    efficiency = msg_rate / cpu_usage if cpu_usage < 100 else 0
    return min(cpu_usage, 100.0), efficiency

def run_simulation():
    test_rates = [1000, 5000, 10000, 20000, 50000]
    
    print("=== Message Broker Energy/CPU Simulation ===")
    print(f"{'Msg Rate (/s)':<15} | {'RabbitMQ CPU%':<15} | {'Kafka CPU%':<15} | {'Winner (Efficiency)'}")
    print("-" * 75)
    
    for rate in test_rates:
        rmq_cpu, rmq_eff = simulate_rabbitmq(rate)
        kaf_cpu, kaf_eff = simulate_kafka(rate)
        
        rmq_str = f"{rmq_cpu:.1f}%" if rmq_cpu < 100 else "OVERLOAD (100%)"
        kaf_str = f"{kaf_cpu:.1f}%" if kaf_cpu < 100 else "OVERLOAD (100%)"
        
        if rmq_cpu >= 100 and kaf_cpu >= 100:
            winner = "None"
        elif rmq_eff > kaf_eff:
            winner = f"RabbitMQ (+{(rmq_eff - kaf_eff)/kaf_eff*100:.0f}%)" if kaf_eff > 0 else "RabbitMQ (Kafka Overloaded)"
        else:
            winner = f"Kafka (+{(kaf_eff - rmq_eff)/rmq_eff*100:.0f}%)" if rmq_eff > 0 else "Kafka (RabbitMQ Overloaded)"
            
        print(f"{rate:<15} | {rmq_str:<15} | {kaf_str:<15} | {winner}")

    print("\nTakeaway: RabbitMQ is highly energy-efficient at low throughputs.")
    print("Kafka's batching makes it significantly more energy-efficient per-message at massive scale.")

if __name__ == '__main__':
    run_simulation()
