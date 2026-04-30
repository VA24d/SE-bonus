\documentclass[11pt]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[margin=1in]{geometry}
\usepackage{lmodern}
\usepackage{amsmath,amssymb}
\usepackage{hyperref}
\usepackage{parskip}

\title{Review of ``Towards Energy-Aware Design Choices in Event-Driven Microservices''}
\author{}
\date{2026-04-30}

\begin{document}

\maketitle

\section*{Overall assessment}

The topic is timely and the paper is easy to follow, but the current draft overstates what the reported evidence establishes. I read the full manuscript, checked the central quantitative claims against the reported numbers, and explicitly looked for symbol-definition drift, branch/sign ambiguity, dimensional grounding, and implementation ambiguity. The paper contains no equations or appendices, so branch/sign issues are not the main risk here; the technical risk sits in claim-to-evidence alignment, metric definition, and model specification. In its present form, the manuscript supports a study about \emph{latency, payload size, CPU-time proxies, and simplified broker simulations}; it does \emph{not} yet support measured claims about energy use, carbon emissions, or Software Carbon Intensity (SCI) improvement.

\section*{Most important technical findings}

\subsection*{1. Energy and SCI claims are not actually measured}
\textbf{Location:} Abstract; Introduction; \emph{Green Software Engineering and SCI}; all three Results subsections; Conclusion.

\textbf{Assessment:} Unsupported claim.

\textbf{Problem:} The draft repeatedly claims energy-footprint reduction, lower carbon emissions, and practical SCI guidance, including statements such as ``through the lens of the Software Carbon Intensity (SCI) specification,'' ``provide a holistic view of the SCI specification in practice,'' and ``reduce a system's energy footprint by orders of magnitude.'' However, the reported measurements are payload size, CPU serialization time, elapsed latency, and a simulated CPU-utilization model. The paper does not report measured power, measured energy, carbon intensity of electricity, embodied hardware allocation, or an SCI calculation per functional unit.

\textbf{Why it matters:} This is the manuscript's central claim. Without an explicit power or carbon model, the current evidence only supports \emph{resource-use proxies}, not direct conclusions about energy or SCI. The conclusion therefore overreaches the reported evidence.

\textbf{Suggested fix:} Either (a) add real energy instrumentation and compute SCI-style quantities with a clearly defined functional unit, or (b) reframe the manuscript as a proxy-metric study and soften all causal energy/carbon language to ``may reduce energy under stated assumptions.'' Also remove or sharply qualify ``orders of magnitude,'' because the reported numbers do not establish that scale of energy reduction.

\subsection*{2. The manuscript drifts between ``empirical benchmarks'' and ``controlled simulations,'' and between Protobuf and a surrogate binary format}
\textbf{Location:} Abstract; Methodology; Figure~1 caption; Serialization Results.

\textbf{Assessment:} Definite inconsistency.

\textbf{Problem:} The abstract claims ``empirical benchmarks and simulation,'' while the Methodology section says the study used ``three controlled simulations.'' The serialization experiment is described as comparing JSON, MessagePack, and a tightly packed Python \texttt{Struct} ``simulating the binary compactness of Protocol Buffers,'' while the literature review and figure caption speak as though Protobuf itself was evaluated. The Results paragraph then discusses JSON versus the ``binary Struct'' and generalizes to ``binary serialization'' overall.

\textbf{Why it matters:} Readers cannot tell which claims are based on direct measurement, which are simulation, and which serializer was actually benchmarked. This ambiguity weakens both the scientific contribution and the practical guidance.

\textbf{Suggested fix:} Use one accurate description consistently. If Protobuf is not directly benchmarked, rename the condition everywhere as a packed binary surrogate and stop attributing its results to Protobuf. If the goal is to claim Protobuf-specific benefit, benchmark an actual Protobuf implementation.

\subsection*{3. The topology comparison largely encodes its own latency result and does not establish workload equivalence}
\textbf{Location:} \emph{Topology Latency Simulation}; \emph{Topology Latency Impact}.

\textbf{Assessment:} Likely issue, with an unsupported generalization.

\textbf{Problem:} The sequential case is defined as A $\rightarrow$ B $\rightarrow$ C with blocking, while the fan-out case is defined as three services processing in parallel with a fixed 0.05-second I/O-bound task each. Under those assumptions, a roughly threefold latency reduction is built into the design: the reported 7.66~s versus 2.57~s is very close to the theoretical 7.5~s versus 2.5~s implied by the setup. The paper then presents this as evidence that the architectural refactor itself reduces energy use.

\textbf{Why it matters:} If the three services are truly independent, the comparison is mostly a restatement of perfect parallelism. If they are not independent, then the fan-out variant may not perform the same business function as the sequential chain. In either case, the current setup does not justify broad energy-efficiency claims about orchestration versus choreography.

\textbf{Suggested fix:} State the data dependencies explicitly, justify why the two topologies represent the same business semantics, and add at least one scenario with realistic broker overhead, queueing, retries, or shared-resource contention. Report repeated runs and dispersion, not only a single total latency number.

\subsection*{4. The broker-efficiency model is under-specified and the cross-over claim is not validated}
\textbf{Location:} \emph{Broker Overhead Mathematical Modeling}; \emph{Message Broker Efficiency Scaling}.

\textbf{Assessment:} Unsupported claim.

\textbf{Problem:} The draft assigns RabbitMQ an $O(N^{1.5})$ overhead and Kafka an $O(N)$ overhead, plus baseline CPU percentages, but it does not provide the actual equations, fitted coefficients, calibration procedure, or sensitivity analysis. The saturation and cross-over claims therefore depend on undocumented modeling choices. The reported metric is CPU utilization percentage, yet the discussion interprets it as energy efficiency and sometimes as energy per message.

\textbf{Why it matters:} The broker section is used to recommend RabbitMQ for low-volume systems and Kafka for enterprise-scale systems. Without explicit model equations and validation, the recommendation could be an artifact of arbitrary assumptions rather than a robust result.

\textbf{Suggested fix:} Write the full model equations, explain how each parameter was derived from [b5] or other sources, and show a sensitivity analysis for the cross-over point. If the goal is energy guidance, report a normalized metric such as joules/message, watt-hours per fixed workload, or a clearly stated proxy instead of CPU\% alone.

\subsection*{5. Figure/text alignment is incomplete in the serialization study}
\textbf{Location:} \emph{Serialization Benchmarking}; Figure~1 caption; \emph{Serialization Impact}.

\textbf{Assessment:} Definite inconsistency.

\textbf{Problem:} The experiment claims to benchmark three formats (JSON, MessagePack, and the packed-binary surrogate), and Figure~1 explicitly mentions JSON, MsgPack, and Protobuf (Simulated). However, the results paragraph only interprets JSON versus the binary surrogate and never discusses MessagePack's position, despite it being one of the study's stated comparison points.

\textbf{Why it matters:} Omitting one of the tested conditions makes the figure-caption narrative incomplete and encourages overgeneralization from a two-way comparison that the paper itself describes as three-way.

\textbf{Suggested fix:} Add a short interpretation of the MessagePack result and explain whether it is closer to JSON or to the packed-binary surrogate. If the manuscript wants to keep only a JSON-vs-Protobuf story, then remove MessagePack from the methodology and figure.

\subsection*{6. Reproducibility and implementation details are too thin for a methods paper}
\textbf{Location:} Entire Methodology section.

\textbf{Assessment:} Likely issue.

\textbf{Problem:} The draft does not specify the Python version, exact libraries used for MessagePack and serialization timing, machine or operating-system details, timing methodology, event schema beyond a brief prose example, or how CPU time was measured. The broker model also lacks executable definitions.

\textbf{Why it matters:} These omissions make it hard to reproduce the reported numbers or to judge whether the reported improvements are library-specific, environment-specific, or robust.

\textbf{Suggested fix:} Add a compact reproducibility table covering software versions, hardware, event schema size, number of repetitions, aggregation method, and timing/instrumentation method. For the broker model, include the actual formulas or pseudocode.

\section*{Meaningful editorial findings}

\subsection*{1. Claim wording should be calibrated to the evidence}
\textbf{Location:} Abstract and Conclusion.

\textbf{Problem:} Verbs such as ``demonstrate,'' ``proves,'' and ``is required'' are stronger than the current evidence warrants, especially where the result is simulation-based.

\textbf{Why it matters:} Even if the underlying direction is plausible, overconfident wording makes the manuscript easier to challenge on methodological grounds.

\textbf{Suggested fix:} Prefer wording such as ``suggests,'' ``indicates,'' or ``under the stated model assumptions.''

\textbf{Candidate rewrite:} ``These experiments suggest that lower-latency topologies and more compact binary encodings can reduce resource-use proxies that may translate into lower energy consumption under an explicitly stated power model.''

\subsection*{2. Reference-list integrity needs attention}
\textbf{Location:} Bibliography entries [b2], [b4], [b5], and [b6].

\textbf{Problem:} The references mix a foundation web page, journal-style entries, and an industry benchmark report, but the metadata style is inconsistent. Entry [b2] is a raw online reference with no access date; [b5] is an industry benchmark report and should be framed as such rather than implicitly as peer-reviewed evidence; and the metadata for [b4] and [b6] should be checked carefully for exact title, venue, and author formatting.

\textbf{Why it matters:} Because the paper's main recommendations lean heavily on prior work, citation integrity directly affects credibility.

\textbf{Suggested fix:} Normalize the bibliography to one style, add missing metadata, and explicitly distinguish peer-reviewed evidence from industry benchmarking.

\section*{Proofing sweep}

I ran the mandatory high-yield proofing scan on the compiled PDF and it returned no high-confidence hits for duplicated punctuation, semicolon-capitalization anomalies, product-name capitalization, or arctangent-style branch ambiguity. The remaining low-cost cleanup I would still make is:

\begin{itemize}
  \item \textbf{Broker-model subsection:} the two model descriptions are written as raw hyphen-prefixed lines instead of a proper list environment; convert them to \texttt{itemize} or prose so the typesetting looks intentional and IEEE-style.
  \item \textbf{Format naming:} standardize ``MessagePack'' versus ``MsgPack,'' and standardize whether the third format is called ``Protobuf,'' ``Protocol Buffers,'' or ``binary Struct (simulating Protobuf).''
\end{itemize}

\section*{Highest-priority fixes}

\begin{enumerate}
  \item Reframe the paper around measured proxy metrics, or add actual energy/SCI instrumentation and calculations.
  \item Resolve the benchmark-versus-simulation and Protobuf-versus-\texttt{Struct} terminology drift everywhere.
  \item Fully specify and validate the broker model before making broker-selection recommendations.
  \item Clarify workload equivalence and add more realistic topology experiments.
  \item Repair bibliography metadata and source framing for [b2], [b4], [b5], and [b6].
\end{enumerate}

\section*{Items needing external verification}

\begin{itemize}
  \item Verify that the bibliographic metadata for [b4] and [b6] exactly matches the cited sources.
  \item Verify whether [b5] is the right primary source for the throughput and CPU-efficiency numbers, or whether those claims should be paired with peer-reviewed benchmarking.
\end{itemize}

\end{document}