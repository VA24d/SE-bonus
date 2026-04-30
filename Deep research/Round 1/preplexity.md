This body of work broadly supports your intuition: asynchronous, event‑driven designs, storage‑backed brokers optimised for throughput, and compact binary serialization all reduce the energy term \(E\) in the Software Carbon Intensity (SCI) formula, with measurable effects on CPU, memory, disk and network usage per request. [sci.greensoftware](https://sci.greensoftware.foundation)

Below, each subsection focuses on one of your three pillars and ends by making the link to SCI explicit.

***

## Microservice topologies: choreography vs. orchestration

### Empirical performance comparisons

Kristianto and Zahra implement both choreography and orchestration for a Saga spanning up to eight microservices, deployed on Kubernetes with Kafka as the message bus, and benchmark them under 1–1000 concurrent users and 1–2 instances per service. They report that, across all scenarios: [fyno](https://www.fyno.io/blog/microservice-communication-orchestration-vs-choreography-cm4s2hdkj001z9jfftra3n7zb)

- Choreography consistently yields lower average response time, higher throughput, and lower CPU utilisation than orchestration, both with and without a load balancer. [fyno](https://www.fyno.io/blog/microservice-communication-orchestration-vs-choreography-cm4s2hdkj001z9jfftra3n7zb)
- As the number of services and concurrent users grows, response times increase for both patterns, but the degradation is significantly worse for orchestration due to repeated “back‑and‑forth” interactions with a central coordinator. [fyno](https://www.fyno.io/blog/microservice-communication-orchestration-vs-choreography-cm4s2hdkj001z9jfftra3n7zb)
- CPU utilisation is consistently lower for choreography; orchestration’s coordinator introduces additional scheduling and message‑routing overhead. [fyno](https://www.fyno.io/blog/microservice-communication-orchestration-vs-choreography-cm4s2hdkj001z9jfftra3n7zb)

Singhal et al. study the same patterns for a health‑care case study and explicitly measure execution time, memory consumption and power consumption for the two approaches. Their experiments (up to four services) show: [fr.slideshare](https://fr.slideshare.net/slideshow/selection-mechanism-of-microservices-orchestration-vs-choreography/130958757)

- Choreography has lower execution time and memory usage than orchestration for their composition workflows. [fr.slideshare](https://fr.slideshare.net/slideshow/selection-mechanism-of-microservices-orchestration-vs-choreography/130958757)
- Power consumption estimated at the server level is also lower for choreography, attributed to fewer indirections and less coordinator logic. [fr.slideshare](https://fr.slideshare.net/slideshow/selection-mechanism-of-microservices-orchestration-vs-choreography/130958757)

These results are broadly confirmed by an IJCA study (Nyagaki, 2025) that evaluates orchestration and choreography under increasing event frequency. It finds that choreography is faster and less resource‑intensive for “few events” but responds slowly when many events are triggered at high frequency, whereas an orchestrator handles increased load more gracefully despite higher baseline overhead. [ijcaonline](https://www.ijcaonline.org/archives/volume187/number59/nyagaki-2025-ijca-925994.pdf)

Complementary work on event‑driven architectures (EDA) versus synchronous request/response provides additional evidence. An exploratory study on EDA’s impact on performance compares event‑driven and traditional architectures in terms of CPU usage, RAM usage, response time, packets sent/received and throughput, finding that event‑driven designs significantly improve throughput and resource utilisation under high load. Event‑driven microservice orchestration for data‑centre operations (EDMA) reports that replacing scheduled polling by event‑driven triggers reduces CPU utilisation by an average of 47.2% and improves operation response times by 89.5% across several enterprise deployments. [ijsat](https://www.ijsat.org/papers/2025/2/3113.pdf)

### Thread blocking, non‑blocking I/O, and energy

From a systems perspective, thread‑per‑request models and synchronous REST chains fundamentally create idle waiting: threads block while waiting for downstream services or I/O, tying up stacks and scheduler entries without making forward progress. Comparative work on thread‑based servers versus event‑driven servers shows that: [webhosting](https://webhosting.de/en/threading-server-model-event-driven-hosting-comparison-serverperf/)

- Per‑connection threading consumes more RAM per connection and incurs significant context‑switch overhead at high concurrency, increasing CPU load for the same useful throughput. [webhosting](https://webhosting.de/en/threading-server-model-event-driven-hosting-comparison-serverperf/)
- Event‑driven, non‑blocking servers using a small worker pool can handle thousands of concurrent connections with significantly lower CPU load and memory footprint. [webhosting](https://webhosting.de/en/threading-server-model-event-driven-hosting-comparison-serverperf/)

Solace’s REST‑vs‑messaging analysis makes the same point in microservice terms: synchronous REST calls block an application thread for the entire round‑trip, whereas asynchronous messaging allows a service to send a request and use that thread to process other work until an event arrives. They emphasise that chaining microservices synchronously effectively recreates a distributed monolith with idle threads and poor scalability, while asynchronous messaging and fan‑out patterns improve utilisation and make hotspots easier to isolate. [solace](https://solace.com/blog/experience-awesomeness-event-driven-microservices/)

Event‑driven microservices for “ultra‑low‑latency cloud workflows” show that message‑driven separation combined with lock‑free data structures maintains stable sub‑50 ms response times and >85 % resource utilisation across 2–64 cores, in part because the architecture avoids disk‑based intermediates and blocking operations. This reinforces the idea that EDA reduces idle cycles per request. [globaljournals](https://globaljournals.org/GJCST_Volume25/1-Event-Driven-Micro.pdf)

### Over‑decoupling, network chattiness, and scalability

The same studies that favour choreography for small and medium‑scale workflows also highlight its downsides at larger scales. Kristianto and Zahra note that, while choreography clearly outperforms orchestration in their experiments, it becomes “very difficult to code and handle if there are multiple events triggered from each microservice,” and recommend it only when the number of participating microservices and event triggers per Saga is small. Nyagaki’s experiments show that as the rate and number of events per transaction increase, choreography’s response times degrade and it responds slowly under high load, whereas orchestration handles large event volumes better, despite its higher baseline overhead. [ijcaonline](https://www.ijcaonline.org/archives/volume187/number59/nyagaki-2025-ijca-925994.pdf)

At the code level, Kristianto and Zahra quantify the maintenance cost of changing a workflow’s order (e.g., S1→S2→S3→S4 to S1→S3→S2→S4): choreography requires modifying six APIs across four services, while orchestration requires changing one routing API in the coordinator. This complexity encourages over‑decoupling and proliferation of fine‑grained services, which in turn increases the number of network hops and messages per business transaction. [fyno](https://www.fyno.io/blog/microservice-communication-orchestration-vs-choreography-cm4s2hdkj001z9jfftra3n7zb)

The RabbitMQ energy‑benchmarking work by Voreakou et al. illustrates how “network chattiness” inside a broker can translate directly into energy cost. For a data‑distribution use case with a 1:M fan‑out ratio, they compare a single topic‑based exchange (Direct) with per‑key fan‑out exchanges (Fanout) under 100 vs. 300 messages/s and 100–1000 queues. At 300 messages/s and high fan‑out, the Direct strategy exhibits significantly higher disk I/O and memory usage, and up to 31.18 % higher average power consumption than Fanout, because RabbitMQ must duplicate messages to multiple queues and spill backlogs to disk. While this experiment is within a broker, not between microservices, it empirically demonstrates how increased fan‑out and message duplication raise memory, disk and power footprints for the same logical workload. [jatit](http://www.jatit.org/volumes/Vol99No18/4Vol99No18.pdf)

### Relation to energy and SCI

The Green Software Foundation’s SCI specification defines SCI as a rate over a functional unit \(R\): \(\text{SCI} = (E \times I + M)/R\), where \(E\) is total energy consumed, \(I\) is grid carbon intensity, and \(M\) is amortised embodied emissions of hardware. Lowering SCI at constant \(I\) and \(M\) means reducing energy per unit of useful work. [greensoftware](https://greensoftware.foundation/standards/sci/)

The literature above supports the following macro‑level claims:

- Moving from synchronous, thread‑blocking request chains to asynchronous, event‑driven choreography reduces CPU time per request and improves throughput by eliminating idle blocked threads and improving utilisation. [sciencedirect](https://www.sciencedirect.com/science/article/abs/pii/S0167739X23003977)
- These improvements translate into lower \(E\) per transaction and therefore lower SCI, provided you keep throughput and hardware constant.  
- However, aggressive decomposition into many tiny event‑driven services increases messages, routing and possibly duplication, which raises broker CPU, memory and disk activity and hence energy per transaction. [jatit](http://www.jatit.org/volumes/Vol99No18/4Vol99No18.pdf)

For an energy‑aware design, your evaluation section can therefore frame microservice topology as an optimisation of \(E/R\): use choreography and non‑blocking I/O to cut idle CPU and latency, but constrain service granularity and event fan‑out so that the number of network and broker operations per business transaction remains bounded.

***

## Broker efficiency: Apache Kafka vs. RabbitMQ

### Architectural differences and resource utilisation

Kafka and RabbitMQ embody two distinct design points. Kafka is a distributed append‑only log that writes messages to partitioned, replicated commit logs on disk, optimised for high throughput and long retention. RabbitMQ is a general‑purpose message broker implementing AMQP, storing messages primarily in memory and moving them to disk only under back‑pressure or when configured for durability. [quix](https://quix.io/blog/apache-kafka-vs-rabbitmq-comparison)

Comparative performance work by Kamiński et al. implements the same application in .NET and Spring Boot, with both brokers fronting a MySQL database, and measures average response time, throughput, and memory usage under different workloads. Their main findings are: [quix](https://quix.io/blog/apache-kafka-vs-rabbitmq-comparison)

- In the .NET implementation, Kafka achieves up to 38 % higher throughput and 40 % lower response time than RabbitMQ, but uses substantially more memory (~400 MB vs. ~146 MB on average). [quix](https://quix.io/blog/apache-kafka-vs-rabbitmq-comparison)
- In the Spring Boot (Kotlin) implementation, RabbitMQ provides about 25 % lower average response time and ~29 % lower memory usage than Kafka, at essentially comparable throughput. [quix](https://quix.io/blog/apache-kafka-vs-rabbitmq-comparison)
- Error rates differ: Kafka yields fewer errors under high load in .NET, while RabbitMQ is more stable in Spring Boot; these differences interact with how each broker integrates with the client stack. [quix](https://quix.io/blog/apache-kafka-vs-rabbitmq-comparison)

Industry benchmarks (Confluent, OpenLogic, Datacamp) consistently show Kafka sustaining order‑of‑magnitude higher throughput (up to ~1 M messages/s) than RabbitMQ (~4–10 K messages/s) on similar hardware by exploiting sequential disk I/O and batching, while RabbitMQ achieves lower latency at very low loads but degrades earlier as throughput increases. Although these studies rarely measure power directly, they demonstrate that Kafka can service a given high‑throughput workload with fewer clusters and fewer message‑processing CPU cycles per message than RabbitMQ, at the cost of a higher baseline resource footprint. [projectpro](https://www.projectpro.io/article/kafka-vs-rabbitmq/451)

### Energy‑focused studies

Direct, apples‑to‑apples power measurements of Kafka and RabbitMQ on identical hardware are rare. Instead, two complementary strands of work examine each broker family separately from an energy standpoint.

Voreakou et al. develop a dedicated energy‑benchmarking testbed for RabbitMQ, measuring per‑process power via Scaphandre (Intel RAPL) and correlating it with broker metrics (CPU, memory, disk I/O, network traffic) under different workloads and exchange configurations. They explore two realistic use cases: [jatit](http://www.jatit.org/volumes/Vol99No18/4Vol99No18.pdf)

- **Account‑driven (1:1)**: number of routing keys equals number of queues. Across 100–300 messages/s and 100–1000 queues, the Fanout strategy yields 4.58–20.28 % lower average power consumption than Direct, and consistently lower memory usage, with no observable disk I/O. [jatit](http://www.jatit.org/volumes/Vol99No18/4Vol99No18.pdf)
- **Data‑distribution (1:M)**: three routing keys fan‑out to 100–1000 queues. At 100 messages/s, Fanout consumes slightly more power (2–11.15 %) than Direct; at 300 messages/s, Fanout consumes 5–31.18 % less power and substantially less disk I/O and memory. [jatit](http://www.jatit.org/volumes/Vol99No18/4Vol99No18.pdf)

They attribute these differences to how each strategy stresses RabbitMQ’s memory and disk subsystems: Direct incurs more message duplication and backlog under high fan‑out, increasing disk writes and memory pressure, which are strongly correlated with higher power. The authors emphasise that even seemingly small power differences, when integrated over 24/7, multi‑node deployments at scale, translate into substantial energy savings or waste. [jatit](http://www.jatit.org/volumes/Vol99No18/4Vol99No18.pdf)

Govind et al. study Kafka‑compatible brokers (Kafka and Redpanda) from both performance and energy perspectives across three hardware generations: HDD‑based, SATA‑SSD and NVMe‑SSD clusters. Key quantitative insights include: [github](https://github.com/AutoMQ/automq/wiki/Apache-Kafka-vs.-RabbitMQ:-Differences-&-Comparison)

- Storage is the primary determinant of throughput: on NVMe, Kafka‑like brokers achieve up to 5× higher throughput than on legacy HDDs for the same cluster size. [github](https://github.com/AutoMQ/automq/wiki/Apache-Kafka-vs.-RabbitMQ:-Differences-&-Comparison)
- Horizontal scaling is nearly linear: adding brokers increases throughput proportionally on SSD/NVMe, assuming partitions are balanced. [github](https://github.com/AutoMQ/automq/wiki/Apache-Kafka-vs.-RabbitMQ:-Differences-&-Comparison)
- Vertical CPU scaling shows diminishing returns beyond 2–8 cores per broker, indicating that these systems are largely I/O‑bound. [github](https://github.com/AutoMQ/automq/wiki/Apache-Kafka-vs.-RabbitMQ:-Differences-&-Comparison)
- Power behaviour differs by implementation: Kafka’s power consumption increases linearly up to ~20 % of maximum sustainable throughput, then plateaus, while Redpanda’s power scales more proportionally up to ~50 % load before stabilising. [github](https://github.com/AutoMQ/automq/wiki/Apache-Kafka-vs.-RabbitMQ:-Differences-&-Comparison)

They fit a linear model \(T(n) = a n + b\) for throughput and \(E(n) = n \cdot P_{\text{max}}\) for power at high load based on just 3‑ and 4‑node calibration experiments, and show that on unseen hardware (Ecotype cluster) this model predicts throughput with <10 % median error and power with ~7 % error. This provides a concrete methodology for “right‑sizing” Kafka‑like clusters to minimise energy consumption for a required ingest rate. [github](https://github.com/AutoMQ/automq/wiki/Apache-Kafka-vs.-RabbitMQ:-Differences-&-Comparison)

A broader systematic review of energy efficiency in microservice‑based cloud applications notes that messaging systems such as Kafka and RabbitMQ are central infrastructure whose configuration and placement significantly impact overall energy consumption, and emphasises the need for energy‑aware placement and capacity planning as part of microservice orchestration. [hal](https://hal.science/hal-05253474v1/file/SMSE_SLR_cloud_energy_microservices_camera_ready.pdf)

### Implications for design and SCI

Taken together, the evidence suggests:

- For **low‑throughput, latency‑sensitive** workflows and resource‑constrained runtimes (e.g. Spring Boot microservices), RabbitMQ can provide lower response times and lower memory footprints, and its energy cost is highly sensitive to exchange design and message fan‑out. [quix](https://quix.io/blog/apache-kafka-vs-rabbitmq-comparison)
- For **high‑throughput streaming** workloads (e.g. telemetry, logs), Kafka‑like brokers leverage sequential disk I/O and partitioned logs to deliver higher throughput per node and higher total throughput, enabling fewer clusters or fewer nodes for a given traffic pattern. [openlogic](https://www.openlogic.com/blog/kafka-vs-rabbitmq)
- Energy per message depends more on hardware choice (HDD vs. SSD/NVMe), horizontal scaling, and architectural configuration (exchange type, replication, partitioning) than on the Kafka/RabbitMQ label alone. [jatit](http://www.jatit.org/volumes/Vol99No18/4Vol99No18.pdf)

In SCI terms, brokers directly affect the energy term \(E\) both through:

- **Baseline power and cluster size**: choosing right‑sized Kafka clusters on efficient storage can reduce total nodes for a target ingest rate, lowering \(E\) for a given \(R\). [github](https://github.com/AutoMQ/automq/wiki/Apache-Kafka-vs.-RabbitMQ:-Differences-&-Comparison)
- **Per‑message work**: RabbitMQ exchange design and Kafka partitioning determine how many disk and memory operations are performed per message, which the RabbitMQ study shows can change power by up to ~31 % at equal logical throughput. [jatit](http://www.jatit.org/volumes/Vol99No18/4Vol99No18.pdf)

Your paper can therefore position broker selection and configuration as an SCI‑relevant design axis: for a fixed functional unit (e.g. per business transaction), the goal is to minimise \(E\) by using the smallest cluster that can handle peak throughput with bounded queues, on the most energy‑efficient storage tier, and with broker topology (exchanges, partitions) tuned to avoid unnecessary duplication and disk churn.

***

## Data serialization: JSON vs. Protobuf

### Controlled migration study: JSON → Protobuf

Shatnawi et al. present one of the few controlled, quantitative studies that explicitly measures the impact of migrating REST services from JSON to Protocol Buffers (Protobuf) on both performance and energy consumption. They propose a semi‑automated refactoring process that: [gravitee](https://www.gravitee.io/blog/protobuf-vs-json)

1. Identifies Data Transfer Objects (DTOs) used in REST controllers and reverse‑engineers their schema into Protobuf `.proto` definitions. [gravitee](https://www.gravitee.io/blog/protobuf-vs-json)
2. Uses the Protobuf compiler to generate Java Protobuf entities and augments DTOs with `toProto` / `fromProto` methods. [gravitee](https://www.gravitee.io/blog/protobuf-vs-json)
3. Generates Protobuf‑based REST controllers alongside the existing JSON controllers to support gradual migration. [gravitee](https://www.gravitee.io/blog/protobuf-vs-json)

They then evaluate two real web applications (an open‑source PetStore and an industrial application) under equivalent workloads and report:

- **Payload size**: 60–80 % reduction in data exchanged; for example, in one application, larger payloads shrink from 1.69 MB (JSON) to 0.36 MB (Protobuf). [gravitee](https://www.gravitee.io/blog/protobuf-vs-json)
- **Response time**: ≈80 % improvement in response time for the PetStore (2969 ms → 631 ms) and ≈60 % for the industrial application (3657 ms → 2141 ms). [gravitee](https://www.gravitee.io/blog/protobuf-vs-json)
- **CPU usage**: ≈17–18 % reduction in CPU utilisation across the two applications, consistent with the lower parsing/serialisation cost of Protobuf. [gravitee](https://www.gravitee.io/blog/protobuf-vs-json)
- **Energy consumption**: ≈18–19 % reduction in energy consumption, measured at the system level, attributed directly to Protobuf’s more efficient serialisation and smaller payloads. [gravitee](https://www.gravitee.io/blog/protobuf-vs-json)
- **Memory usage**: negligible change (≈1.3–1.4 % reduction at most), indicating that the migration does not introduce additional memory overhead. [gravitee](https://www.gravitee.io/blog/protobuf-vs-json)

These results are particularly valuable because they trace a concrete refactoring step (serialization format only) to improvements in network bytes, CPU time, and measured energy, isolating serialization as a lever for lowering SCI.

### Additional performance and footprint evidence

Earlier performance work on gRPC (which uses Protobuf) versus REST/JSON, as cited by Shatnawi et al., finds that gRPC can outperform REST by up to 7–10× in data reception and transmission due to Protobuf’s efficient binary encoding. Industry benchmarks provide consistent orders of magnitude: [gravitee](https://www.gravitee.io/blog/protobuf-vs-json)

- A Go‑based comparison reports Protobuf serialisation/deserialisation is 5–10× faster than JSON, with Protobuf messages 50–80 % smaller. [dev](https://dev.to/jones_charles_ad50858dbc0/json-vs-protocol-buffers-in-go-which-should-you-use-for-network-communication-4gio)
- A production benchmark of JSON, MessagePack and Protobuf in Go finds that a single JSON endpoint consumed 30–40 % of CPU time for (de)serialisation, and that switching to binary formats reduced CPU time by up to 40 %, payload size by 50–80 %, and improved marshalling speed by 2–3×. [dev](https://dev.to/devflex-pro/json-vs-messagepack-vs-protobuf-in-go-my-real-benchmarks-and-what-they-mean-in-production-48fh)

Blogs comparing Protobuf and JSON for microservices (e.g. Gravitee, Insight Consultants) report similar qualitative trends—smaller payloads, faster internal calls, and lower CPU overhead for Protobuf in high‑traffic, structured data workloads—but generally lack direct energy measurements. [insightconsultants](https://insightconsultants.co/protocol-buffers-vs-json-microservices/)

Taken together with Shatnawi et al.’s controlled energy measurement, this body of evidence supports the claim that replacing JSON with Protobuf in a microservice ecosystem substantially reduces:

- **Network bytes per request** (60–80 % reduction in controlled experiments). [gravitee](https://www.gravitee.io/blog/protobuf-vs-json)
- **CPU time per request** (≈17–40 % in controlled and industry studies). [dev](https://dev.to/jones_charles_ad50858dbc0/json-vs-protocol-buffers-in-go-which-should-you-use-for-network-communication-4gio)

Both reductions directly influence servers’ and network equipment’s energy consumption per request.

### Relation to network energy and SCI

Shatnawi et al. attribute their ≈18–19 % energy savings to two mechanisms: lower CPU work for serialization/deserialization and smaller payloads reducing transmission time and overhead. While their measurements focus on server‑side energy, smaller packets also reduce time spent transmitting and processing data in NICs, switches and routers along the path, which is part of the wider energy budget captured under the SCI boundary (compute, storage, networking). [sci.greensoftware](https://sci.greensoftware.foundation)

Because SCI aggregates all operational energy \(E\) across compute, storage and networking per functional unit \(R\), a 60–80 % reduction in bytes and ~17–18 % reduction in CPU utilisation per request translate almost directly into a lower SCI, especially for I/O‑bound or latency‑sensitive workloads where network and serialisation are on the critical path. [github](https://github.com/Green-Software-Foundation/sci)

For your evaluation section, you can therefore:

- Treat serialization format as a first‑class architectural choice affecting SCI—on par with microservice topology and broker selection.  
- Quantify potential SCI reduction by combining measured per‑request energy savings (≈18 % in Shatnawi et al.) with your system’s traffic profile to estimate absolute energy and emissions reductions.

***

## Combined impact on Software Carbon Intensity

The SCI specification emphasises that architectural and design choices—code, infrastructure, topology—alter the numerator \(E \times I + M\) for a given functional unit \(R\). The literature summarised above gives you an evidence‑based narrative for how your three pillars interact to influence SCI in an event‑driven microservice system: [greensoftware](https://greensoftware.foundation/standards/sci/)

- **Microservice topology (choreography vs. orchestration)** primarily affects how much idle CPU and blocking occurs per transaction, how many messages and hops a transaction entails, and how much coordination logic is executed centrally. In SCI terms, this shapes CPU‑dominated components of \(E\) and, indirectly, the amount of supporting infrastructure needed (affecting \(M\)). [solace](https://solace.com/blog/experience-awesomeness-event-driven-microservices/)
- **Broker architecture and sizing (Kafka vs. RabbitMQ)** determine the efficiency of message transport and buffering across the system: exchange/partition design and hardware choice control disk and memory operations per message and cluster size; energy‑aware right‑sizing and storage selection can reduce the number of brokers and their per‑node power. This strongly influences both \(E\) (operational energy) and \(M\) (embedded emissions of additional brokers and disks). [datacamp](https://www.datacamp.com/blog/kafka-vs-rabbitmq)
- **Serialization format (JSON vs. Protobuf)** directly reduces CPU cycles and network bytes per call, with controlled experiments demonstrating ≈60–80 % smaller payloads, ≈80 % faster responses, ≈17–18 % less CPU and ≈18–19 % lower energy per request, all without memory penalties. This attacks the “CPU + network” components of \(E\) at the per‑request level. [dev](https://dev.to/devflex-pro/json-vs-messagepack-vs-protobuf-in-go-my-real-benchmarks-and-what-they-mean-in-production-48fh)

An energy‑aware, event‑driven microservice design can therefore be framed as an optimisation problem over these three axes: for a fixed functional unit (e.g., per completed business workflow), choose communication topology, broker architecture, and serialization such that the integrated CPU, memory, disk and network work per workflow is minimised, subject to latency and reliability constraints. Mapping those choices back into the SCI formula provides a principled way to quantify and compare alternative designs in your paper.