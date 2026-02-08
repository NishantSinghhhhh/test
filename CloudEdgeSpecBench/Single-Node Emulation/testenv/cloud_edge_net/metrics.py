"""
Performance Metrics for Cloud-Edge Speculative Decoding Benchmark

Implements all required metrics:
- Normalized Speedup (vs baseline)
- Throughput (tokens/s)
- Acceptance Rate (draft quality)
- TTFT (Time To First Token)
- Latency percentiles (p50, p95)
- Stream Jitter (latency variance)
- Energy Efficiency (Joules per token)
"""

import numpy as np
from sedna.common.class_factory import ClassFactory, ClassType


def _get_values(y_pred, key):
    """
    Extract values for a specific key from prediction results.
    
    Args:
        y_pred: Prediction results (dict or list of dicts)
        key (str): Key to extract
        
    Returns:
        list: Extracted values
    """
    values = []
    
    # Handle single dict
    if isinstance(y_pred, dict):
        return [y_pred.get(key, 0.0)]
    
    # Handle list of dicts
    if isinstance(y_pred, list):
        for item in y_pred:
            if isinstance(item, dict):
                values.append(item.get(key, 0.0))
    
    return values if values else [0.0]


# ============================================================================
# CORE PERFORMANCE METRICS
# ============================================================================

@ClassFactory.register(ClassType.GENERAL, alias="normalized_speedup")
def normalized_speedup(y_true, y_pred, **kwargs):
    """
    Normalized speedup relative to baseline latency.
    
    Formula: speedup = 1.0 / avg_latency
    Higher is better. Values > 1.0 indicate improvement over baseline.
    
    Args:
        y_true: Ground truth (not used)
        y_pred: Prediction results with 'latency' key
        
    Returns:
        float: Normalized speedup
    """
    latencies = _get_values(y_pred, "latency")
    avg_latency = np.mean(latencies)
    
    # Prevent division by zero
    if avg_latency <= 0:
        return 0.0
    
    return 1.0 / avg_latency


@ClassFactory.register(ClassType.GENERAL, alias="throughput_tok_s")
def throughput_tok_s(y_true, y_pred, **kwargs):
    """
    Average generation throughput in tokens per second.
    
    Higher is better.
    
    Args:
        y_true: Ground truth (not used)
        y_pred: Prediction results with 'throughput' key
        
    Returns:
        float: Average throughput
    """
    throughputs = _get_values(y_pred, "throughput")
    return float(np.mean(throughputs))


@ClassFactory.register(ClassType.GENERAL, alias="acceptance_rate")
def acceptance_rate(y_true, y_pred, **kwargs):
    """
    Draft model acceptance rate (Gamma γ).
    
    Percentage of draft tokens accepted by the verifier.
    Higher is better (indicates draft model quality).
    
    Range: 0.0 to 1.0
    
    Args:
        y_true: Ground truth (not used)
        y_pred: Prediction results with 'final_acceptance_rate' key
        
    Returns:
        float: Average acceptance rate
    """
    acceptance_rates = _get_values(y_pred, "final_acceptance_rate")
    return float(np.mean(acceptance_rates))


@ClassFactory.register(ClassType.GENERAL, alias="ttft_ms")
def ttft_ms(y_true, y_pred, **kwargs):
    """
    Time To First Token (TTFT) in milliseconds.
    
    Measures responsiveness - how long until user sees first output.
    Lower is better.
    
    Args:
        y_true: Ground truth (not used)
        y_pred: Prediction results with 'ttft_ms' key
        
    Returns:
        float: Average TTFT in milliseconds
    """
    ttfts = _get_values(y_pred, "ttft_ms")
    return float(np.mean(ttfts))


# ============================================================================
# LATENCY METRICS (Percentiles)
# ============================================================================

@ClassFactory.register(ClassType.GENERAL, alias="p50_latency")
def p50_latency(y_true, y_pred, **kwargs):
    """
    Median (50th percentile) latency in seconds.
    
    Represents typical user experience.
    Lower is better.
    
    Args:
        y_true: Ground truth (not used)
        y_pred: Prediction results with 'latency' key
        
    Returns:
        float: Median latency
    """
    latencies = _get_values(y_pred, "latency")
    return float(np.percentile(latencies, 50))


@ClassFactory.register(ClassType.GENERAL, alias="p95_latency")
def p95_latency(y_true, y_pred, **kwargs):
    """
    95th percentile latency in seconds.
    
    Represents worst-case experience for 5% of requests.
    Critical for measuring stability under jitter.
    Lower is better.
    
    Args:
        y_true: Ground truth (not used)
        y_pred: Prediction results with 'latency' key
        
    Returns:
        float: 95th percentile latency
    """
    latencies = _get_values(y_pred, "latency")
    return float(np.percentile(latencies, 95))


@ClassFactory.register(ClassType.GENERAL, alias="stream_jitter")
def stream_jitter(y_true, y_pred, **kwargs):
    """
    Latency variance (standard deviation).
    
    Measures how "stuttery" the generation is.
    Lower is better (more consistent).
    
    Args:
        y_true: Ground truth (not used)
        y_pred: Prediction results with 'latency' key
        
    Returns:
        float: Latency standard deviation
    """
    latencies = _get_values(y_pred, "latency")
    return float(np.std(latencies))


# ============================================================================
# RESOURCE METRICS
# ============================================================================

@ClassFactory.register(ClassType.GENERAL, alias="energy_efficiency")
def energy_efficiency(y_true, y_pred, **kwargs):
    """
    Energy consumption in Joules.
    
    Total energy consumed during generation.
    Lower is better (more battery-friendly).
    
    Args:
        y_true: Ground truth (not used)
        y_pred: Prediction results with 'energy' key
        
    Returns:
        float: Average energy in Joules
    """
    energies = _get_values(y_pred, "energy")
    return float(np.mean(energies))


# ============================================================================
# HYPERPARAMETER PASS-THROUGH METRICS
# (These extract config values for the results table)
# ============================================================================

@ClassFactory.register(ClassType.GENERAL, alias="draft_k")
def draft_k(y_true, y_pred, **kwargs):
    """
    Extract draft_k hyperparameter value.
    
    Returns:
        int: Draft lookahead length
    """
    vals = _get_values(y_pred, "draft_k")
    return int(vals[0]) if vals else 0


@ClassFactory.register(ClassType.GENERAL, alias="compute_ratio")
def compute_ratio(y_true, y_pred, **kwargs):
    """
    Extract compute_ratio hyperparameter value.
    
    Returns:
        float: Draft/Verify compute speed ratio
    """
    vals = _get_values(y_pred, "compute_ratio")
    return float(vals[0]) if vals else 0.0


@ClassFactory.register(ClassType.GENERAL, alias="dataset_task")
def dataset_task(y_true, y_pred, **kwargs):
    """
    Extract dataset_task hyperparameter value.
    
    Returns:
        int: Task type (1=WikiText, 2=Code, etc.)
    """
    vals = _get_values(y_pred, "dataset_task")
    return int(vals[0]) if vals else 0


@ClassFactory.register(ClassType.GENERAL, alias="concurrency")
def concurrency(y_true, y_pred, **kwargs):
    """
    Extract concurrency hyperparameter value.
    
    Returns:
        int: Number of concurrent requests
    """
    vals = _get_values(y_pred, "concurrency")
    return int(vals[0]) if vals and vals[0] > 0 else 1

@ClassFactory.register(ClassType.GENERAL, alias="avg_rtt_measured")
def avg_rtt_measured(y_true, y_pred, **kwargs):
    """Measured average RTT (for adaptive algorithm)"""
    vals = _get_values(y_pred, "avg_rtt_measured")
    return float(np.mean(vals)) if vals else 0.0


@ClassFactory.register(ClassType.GENERAL, alias="rtt_ms")
def rtt_ms(y_true, y_pred, **kwargs):
    """
    Extract RTT hyperparameter value.
    
    Returns:
        float: Round-trip time in milliseconds
    """
    vals = _get_values(y_pred, "rtt_ms")
    return float(vals[0]) if vals else 0.0


@ClassFactory.register(ClassType.GENERAL, alias="bandwidth_mbps")
def bandwidth_mbps(y_true, y_pred, **kwargs):
    """
    Extract bandwidth hyperparameter value.
    
    Returns:
        float: Bandwidth in Mbps
    """
    vals = _get_values(y_pred, "bandwidth_mbps")
    return float(vals[0]) if vals else 0.0


@ClassFactory.register(ClassType.GENERAL, alias="jitter_ms")
def jitter_ms(y_true, y_pred, **kwargs):
    """
    Extract jitter hyperparameter value.
    
    Returns:
        float: Network jitter in milliseconds
    """
    vals = _get_values(y_pred, "jitter_ms")
    return float(vals[0]) if vals else 0.0


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def compute_all_metrics(y_pred):
    """
    Compute all metrics at once for debugging.
    
    Args:
        y_pred: Prediction results
        
    Returns:
        dict: All computed metrics
    """
    metrics = {
        "normalized_speedup": normalized_speedup(None, y_pred),
        "throughput_tok_s": throughput_tok_s(None, y_pred),
        "acceptance_rate": acceptance_rate(None, y_pred),
        "ttft_ms": ttft_ms(None, y_pred),
        "p50_latency": p50_latency(None, y_pred),
        "p95_latency": p95_latency(None, y_pred),
        "stream_jitter": stream_jitter(None, y_pred),
        "energy_efficiency": energy_efficiency(None, y_pred),
        "draft_k": draft_k(None, y_pred),
        "compute_ratio": compute_ratio(None, y_pred),
        "dataset_task": dataset_task(None, y_pred),
        "concurrency": concurrency(None, y_pred),
    }
    return metrics


# Standalone testing
if __name__ == "__main__":
    print("Testing metrics module...")
    
    # Sample prediction results
    test_results = [
        {
            "latency": 3.5,
            "throughput": 6.0,
            "energy": 875.0,
            "final_acceptance_rate": 0.65,
            "ttft_ms": 150.0,
            "draft_k": 3,
            "compute_ratio": 1.0,
            "dataset_task": 1,
            "rtt_ms": 50.0,
            "bandwidth_mbps": 100.0,
            "jitter_ms": 5.0
        },
        {
            "latency": 3.8,
            "throughput": 5.8,
            "energy": 950.0,
            "final_acceptance_rate": 0.70,
            "ttft_ms": 160.0,
            "draft_k": 3,
            "compute_ratio": 1.0,
            "dataset_task": 1,
            "rtt_ms": 50.0,
            "bandwidth_mbps": 100.0,
            "jitter_ms": 5.0
        }
    ]
    
    metrics = compute_all_metrics(test_results)
    
    print("\nComputed Metrics:")
    for name, value in metrics.items():
        print(f"  {name}: {value:.4f}")
    
    print("\n✓ Metrics module tests passed")