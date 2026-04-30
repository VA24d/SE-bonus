Act as an expert researcher in Green Software Engineering and Cloud-Native Distributed Systems. I am writing a 4-page IEEE conference paper titled "Towards Energy-Aware Design Choices in Event-Driven Microservices" and I need you to conduct a deep, academic literature review. 

The primary focus of my paper is evaluating how macro-level architectural choices influence physical hardware energy consumption, which maps to the Software Carbon Intensity (SCI) specification.

Please conduct an exhaustive literature search and synthesize empirical evidence, academic papers, and reputable industry benchmarks for the following three specific topics:

### 1. Microservice Topologies: Choreography vs. Orchestration
*   **The Focus:** How the communication pattern between services impacts energy footprints.
*   **Context:** Orchestration (using a central controller with synchronous request/response chains) often leads to blocking and idle waiting times, wasting CPU cycles. Choreography (asynchronous, event-driven, Parallel Fan-Out) is cited as more energy-efficient because services react independently without blocking. However, over-decoupling can lead to excessive network chattiness.
*   **What I need:** Find studies that quantify the CPU and latency trade-offs between chained sequential requests and parallel fan-out architectures. Look for research that explicitly links thread-blocking or network chattiness to energy consumption.

### 2. Broker Efficiency: Apache Kafka vs. RabbitMQ
*   **The Focus:** Architectural overhead and energy consumption patterns of message brokers.
*   **Context:** RabbitMQ operates primarily in-memory as a traditional queue, making it highly efficient for low-latency, low-throughput scenarios. Kafka is a distributed append-only log relying on disk I/O. While Kafka has a higher baseline infrastructure energy cost, it becomes significantly more energy-efficient per-message at a massive scale due to batching and sequential disk writes.
*   **What I need:** Find empirical benchmarks or academic analyses that compare the power consumption or resource utilization (CPU/Memory/Disk I/O) of RabbitMQ versus Apache Kafka under varying throughput loads. 

### 3. Data Serialization: JSON vs. Protobuf
*   **The Focus:** The computational and network energy costs of text-based vs. binary payloads.
*   **Context:** JSON is human-readable but verbose, requiring heavy string manipulation and validation for parsing. Protobuf transmits raw binary data based on a schema, dramatically reducing CPU parsing cycles and network bandwidth, directly lowering the energy consumed by network switches and servers.
*   **What I need:** Locate research that quantifies the exact resource reduction (CPU time, memory footprint, network bytes) when migrating from JSON to binary formats like Protobuf in a microservice ecosystem, and how that maps to energy efficiency.

### Formatting Requirements:
1.  **Structure:** Dedicate a specific subsection to each of the three topics above.
2.  **Academic Tone:** Write in a formal, objective, academic tone suitable for an IEEE conference paper.
3.  **Citations:** Provide real, traceable references to academic papers, IEEE/ACM journals, or verified industry whitepapers (e.g., Green Software Foundation). Do not hallucinate citations. 
4.  **Synthesis:** Do not just list papers; synthesize their findings to support the contexts provided above. Conclude with a brief summary of how these three architectural pillars collectively impact the Software Carbon Intensity (SCI) of a system.
