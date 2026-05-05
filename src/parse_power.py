"""
Parse powermetrics output -> per-sample CPU / GPU / ANE / combined mW
and compute mean, stddev, peak, and total energy (mWh) over run duration.

Sample format (one per block):
    *** Sampled system activity (... ) (XX.XX ms elapsed) ***
    ...
    CPU Power: 457 mW
    GPU Power: 29 mW
    ANE Power: 0 mW
    Combined Power (CPU + GPU + ANE): 486 mW
"""
import re
import sys
import statistics
from pathlib import Path

SAMPLE_RE = re.compile(r"\(([\d.]+)\s*ms elapsed\)")
CPU_RE    = re.compile(r"^CPU Power:\s+(\d+)\s+mW", re.M)
GPU_RE    = re.compile(r"^GPU Power:\s+(\d+)\s+mW", re.M)
ANE_RE    = re.compile(r"^ANE Power:\s+(\d+)\s+mW", re.M)
TOT_RE    = re.compile(r"^Combined Power.*?:\s+(\d+)\s+mW", re.M)


def parse(path):
    txt = Path(path).read_text()
    blocks = txt.split("*** Sampled system activity")
    samples = []
    for b in blocks[1:]:
        m_el = SAMPLE_RE.search(b)
        m_cpu = CPU_RE.search(b)
        m_gpu = GPU_RE.search(b)
        m_ane = ANE_RE.search(b)
        m_tot = TOT_RE.search(b)
        if not (m_el and m_cpu and m_tot):
            continue
        samples.append({
            "elapsed_ms": float(m_el.group(1)),
            "cpu_mW":     int(m_cpu.group(1)),
            "gpu_mW":     int(m_gpu.group(1)) if m_gpu else 0,
            "ane_mW":     int(m_ane.group(1)) if m_ane else 0,
            "total_mW":   int(m_tot.group(1)),
        })
    return samples


def summarize(name, samples):
    if not samples:
        print(f"{name}: no samples")
        return None
    cpus   = [s["cpu_mW"]   for s in samples]
    totals = [s["total_mW"] for s in samples]
    durs_s = [s["elapsed_ms"] / 1000.0 for s in samples]

    # Energy = sum(power_W * duration_s) -> J ; /3600 -> Wh ; *1000 -> mWh
    energy_cpu_J   = sum((p / 1000.0) * d for p, d in zip(cpus,   durs_s))
    energy_total_J = sum((p / 1000.0) * d for p, d in zip(totals, durs_s))

    duration_s = sum(durs_s)
    print(f"\n=== {name} ===")
    print(f"  samples:             {len(samples)}")
    print(f"  duration:            {duration_s:.2f} s")
    print(f"  CPU mean power:      {statistics.mean(cpus):.1f} mW")
    print(f"  CPU stddev:          {statistics.stdev(cpus) if len(cpus) > 1 else 0:.1f} mW")
    print(f"  CPU peak:            {max(cpus)} mW")
    print(f"  Combined mean:       {statistics.mean(totals):.1f} mW")
    print(f"  Combined peak:       {max(totals)} mW")
    print(f"  CPU energy:          {energy_cpu_J:.3f} J  ({energy_cpu_J/3600*1000:.4f} mWh)")
    print(f"  Combined energy:     {energy_total_J:.3f} J  ({energy_total_J/3600*1000:.4f} mWh)")
    return {
        "name":       name,
        "duration_s": duration_s,
        "cpu_mean":   statistics.mean(cpus),
        "cpu_peak":   max(cpus),
        "tot_mean":   statistics.mean(totals),
        "tot_peak":   max(totals),
        "energy_J":   energy_total_J,
        "energy_kWh": energy_total_J / 3_600_000.0,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python src/parse_power.py <powermetrics.txt> [more ...]")
        sys.exit(1)

    results = []
    for p in sys.argv[1:]:
        s = parse(p)
        r = summarize(Path(p).stem, s)
        if r:
            results.append(r)

    if len(results) >= 2:
        print("\n=== COMPARISON (vs first run) ===")
        base = results[0]
        for r in results[1:]:
            d_energy = (base["energy_J"] - r["energy_J"]) / base["energy_J"] * 100 if base["energy_J"] else 0
            d_power  = (base["tot_mean"] - r["tot_mean"]) / base["tot_mean"] * 100 if base["tot_mean"] else 0
            print(f"  {r['name']} vs {base['name']}:")
            print(f"    energy delta:   {d_energy:+.1f}%")
            print(f"    mean power delta: {d_power:+.1f}%")
