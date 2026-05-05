import matplotlib.pyplot as plt
import numpy as np

def generate_serialization_chart():
    # Measured values from benchmark_serialization.py (1,000,000 events, 5 runs)
    # JSON:     67.71 MB payload, 2209.01 ms mean CPU time (ser+deser)
    # MsgPack:  49.59 MB payload,  838.84 ms mean CPU time (ser+deser)
    # Protobuf: 15.26 MB payload, 1597.31 ms mean CPU time (ser+deser)
    formats = ['JSON', 'MessagePack', 'Protobuf']
    sizes_mb = [67.71, 49.59, 15.26]
    times_ms = [2209.01, 838.84, 1597.31]

    fig, ax1 = plt.subplots(figsize=(8, 5))

    color = 'tab:blue'
    ax1.set_xlabel('Serialization Format', fontweight='bold')
    ax1.set_ylabel('Payload Size (MB)', color=color, fontweight='bold')
    bars1 = ax1.bar(np.arange(len(formats)) - 0.2, sizes_mb, 0.4, color=color, label='Size (MB)')
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('CPU Time (ms)', color=color, fontweight='bold')
    bars2 = ax2.bar(np.arange(len(formats)) + 0.2, times_ms, 0.4, color=color, label='Time (ms)')
    ax2.tick_params(axis='y', labelcolor=color)

    ax1.set_xticks(np.arange(len(formats)))
    ax1.set_xticklabels(formats)

    # Annotate size bars with values
    for bar, val in zip(bars1, sizes_mb):
        ax1.text(bar.get_x() + bar.get_width() / 2.0, bar.get_height() + 0.5,
                 f'{val:.1f}', ha='center', va='bottom', fontsize=8, color='tab:blue')

    fig.legend(loc="upper right", bbox_to_anchor=(1,1), bbox_transform=ax1.transAxes)
    plt.title('Serialization Performance: 1,000,000 Business Events', fontweight='bold')
    fig.tight_layout()
    plt.savefig('serialization_chart.pdf')
    plt.close()

def generate_topology_chart():
    # Measured values from microservices_topology.py (real HTTP servers, 5 runs)
    # 50 events × 3 services × (50ms processing + 10ms network/hop)
    # Chain:   10.23s mean (theoretical min 9.0s; excess = HTTP overhead)
    # Fan-Out:  3.47s mean (theoretical min 3.0s)
    topologies = ['Chain (Sequential)', 'Fan-Out (Parallel)']
    latency = [10.23, 3.47]  # seconds (measured)

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(topologies, latency, color=['tab:orange', 'tab:green'], width=0.5)

    ax.set_ylabel('Total Latency (Seconds)', fontweight='bold')
    ax.set_title('Topology Latency: 50 Business Events × 3 Services', fontweight='bold')

    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.05, f'{yval:.2f}s',
                va='bottom', ha='center', fontweight='bold')

    # Annotate reduction
    ax.annotate('66.1% latency\nreduction',
                xy=(1, latency[1]), xytext=(0.5, 6.5),
                arrowprops=dict(arrowstyle='->', color='black'),
                ha='center', fontsize=9, color='darkgreen')

    fig.tight_layout()
    plt.savefig('topology_chart.pdf')
    plt.close()

def generate_broker_chart():
    # Mathematical model values computed from explicit equations in paper:
    # U_RMQ(N) = 2.0 + 4.5 * (N/1000)^1.5
    # U_Kafka(N) = 12.0 + 1.5 * (N/1000)
    rates = [1000, 5000, 10000, 20000, 50000]
    rmq_cpu = [min(2.0 + 4.5 * (r/1000)**1.5, 100) for r in rates]   # [6.5, 52.3, 100, 100, 100]
    kaf_cpu = [min(12.0 + 1.5 * (r/1000), 100) for r in rates]        # [13.5, 19.5, 27.0, 42.0, 87.0]

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(rates, rmq_cpu, marker='o', linestyle='-', color='tab:orange', label='RabbitMQ', linewidth=2)
    ax.plot(rates, kaf_cpu, marker='s', linestyle='-', color='tab:purple', label='Apache Kafka', linewidth=2)

    ax.fill_between(rates, 100, 105, color='red', alpha=0.15, label='Overload Zone (≥100%)')

    # Annotate crossover point (2,034 msg/s — analytical solve from benchmark_broker_simulation.py)
    ax.axvline(x=2034, color='gray', linestyle='--', alpha=0.6, linewidth=1)
    ax.text(2300, 55, 'Crossover\n2,034 msg/s', fontsize=8, color='gray')

    # Annotate model equations
    ax.text(0.02, 0.97,
            r'$U_{RMQ}(N) = 2.0 + 4.5\cdot(N/1000)^{1.5}$' + '\n' +
            r'$U_{Kafka}(N) = 12.0 + 1.5\cdot(N/1000)$',
            transform=ax.transAxes, fontsize=7.5, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.4))

    ax.set_xlabel('Throughput (Messages / Second)', fontweight='bold')
    ax.set_ylabel('Simulated CPU Utilization (%)', fontweight='bold')
    ax.set_title('Message Broker CPU Overhead vs. Throughput (Mathematical Model)', fontweight='bold')

    ax.set_ylim(0, 108)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(loc='upper left')

    fig.tight_layout()
    plt.savefig('broker_chart.pdf')
    plt.close()

if __name__ == '__main__':
    generate_serialization_chart()
    generate_topology_chart()
    generate_broker_chart()
    print("Graphs generated successfully as PDFs.")
