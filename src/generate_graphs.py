import matplotlib.pyplot as plt
import numpy as np

def generate_serialization_chart():
    formats = ['JSON', 'MsgPack', 'Protobuf (Sim)']
    sizes = [693.36, 507.81, 234.38]  # KB
    times = [22.84, 7.32, 2.40]      # ms (Ser + Deser)

    fig, ax1 = plt.subplots(figsize=(8, 5))

    color = 'tab:blue'
    ax1.set_xlabel('Serialization Format', fontweight='bold')
    ax1.set_ylabel('Payload Size (KB)', color=color, fontweight='bold')
    bars1 = ax1.bar(np.arange(len(formats)) - 0.2, sizes, 0.4, color=color, label='Size (KB)')
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('CPU Time (ms)', color=color, fontweight='bold')
    bars2 = ax2.bar(np.arange(len(formats)) + 0.2, times, 0.4, color=color, label='Time (ms)')
    ax2.tick_params(axis='y', labelcolor=color)

    ax1.set_xticks(np.arange(len(formats)))
    ax1.set_xticklabels(formats)
    
    fig.legend(loc="upper right", bbox_to_anchor=(1,1), bbox_transform=ax1.transAxes)
    plt.title('Serialization Performance (10,000 Events)', fontweight='bold')
    fig.tight_layout()
    plt.savefig('serialization_chart.pdf')
    plt.close()

def generate_topology_chart():
    topologies = ['Chain (Sequential)', 'Fan-Out (Parallel)']
    latency = [7.66, 2.57]  # seconds
    
    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(topologies, latency, color=['tab:orange', 'tab:green'], width=0.5)
    
    ax.set_ylabel('Total Latency (Seconds)', fontweight='bold')
    ax.set_title('Topology Latency for 50 Business Events', fontweight='bold')
    
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval, f'{yval}s', va='bottom', ha='center', fontweight='bold')
        
    fig.tight_layout()
    plt.savefig('topology_chart.pdf')
    plt.close()

def generate_broker_chart():
    rates = [1000, 5000, 10000, 20000, 50000]
    rmq_cpu = [6.5, 52.3, 100, 100, 100]
    kaf_cpu = [13.5, 19.5, 27.0, 42.0, 87.0]

    fig, ax = plt.subplots(figsize=(8, 5))
    
    ax.plot(rates, rmq_cpu, marker='o', linestyle='-', color='tab:orange', label='RabbitMQ', linewidth=2)
    ax.plot(rates, kaf_cpu, marker='s', linestyle='-', color='tab:purple', label='Apache Kafka', linewidth=2)
    
    ax.fill_between(rates, 100, 110, color='red', alpha=0.1, label='Overload Zone')

    ax.set_xlabel('Throughput (Messages / Second)', fontweight='bold')
    ax.set_ylabel('CPU Utilization (%)', fontweight='bold')
    ax.set_title('Message Broker CPU Overhead vs. Throughput', fontweight='bold')
    
    ax.set_ylim(0, 105)
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
