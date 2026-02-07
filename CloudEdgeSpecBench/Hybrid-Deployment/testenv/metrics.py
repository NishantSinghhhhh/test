import numpy as np
from sedna.common.class_factory import ClassFactory, ClassType

def _get_values(y_pred, key):
    values = []
    if isinstance(y_pred, dict): 
        return [y_pred.get(key, 0.0)]
    if isinstance(y_pred, list):
        for item in y_pred:
            if isinstance(item, dict): 
                values.append(item.get(key, 0.0))
    return values if values else [0.0]


# === EXISTING METRICS ===

@ClassFactory.register(ClassType.GENERAL, alias="latency")
def latency(y_true, y_pred, **kwargs):
    return float(np.mean(_get_values(y_pred, "latency")))


@ClassFactory.register(ClassType.GENERAL, alias="throughput_tok_s")
def throughput_tok_s(y_true, y_pred, **kwargs):
    return float(np.mean(_get_values(y_pred, "throughput")))


@ClassFactory.register(ClassType.GENERAL, alias="normalized_speedup")
def normalized_speedup(y_true, y_pred, **kwargs):
    avg_latency = np.mean(_get_values(y_pred, "latency"))
    return 1.0 / avg_latency if avg_latency > 0 else 0.0


@ClassFactory.register(ClassType.GENERAL, alias="acceptance_rate")
def acceptance_rate(y_true, y_pred, **kwargs):
    return float(np.mean(_get_values(y_pred, "final_acceptance_rate")))


@ClassFactory.register(ClassType.GENERAL, alias="energy_efficiency")
def energy_efficiency(y_true, y_pred, **kwargs):
    return float(np.mean(_get_values(y_pred, "energy")))


@ClassFactory.register(ClassType.GENERAL, alias="draft_k")
def draft_k(y_true, y_pred, **kwargs):
    vals = _get_values(y_pred, "draft_k")
    return int(vals[0]) if vals else 0


@ClassFactory.register(ClassType.GENERAL, alias="cloud_url")
def cloud_url(y_true, y_pred, **kwargs):
    vals = _get_values(y_pred, "cloud_url")
    return str(vals[0]) if vals else "N/A"


# === NEW METRICS ===

@ClassFactory.register(ClassType.GENERAL, alias="ttft_ms")
def ttft_ms(y_true, y_pred, **kwargs):
    """Time To First Token"""
    vals = _get_values(y_pred, "ttft_ms")
    return float(np.mean(vals))


@ClassFactory.register(ClassType.GENERAL, alias="p95_latency")
def p95_latency(y_true, y_pred, **kwargs):
    """95th percentile latency"""
    latencies = _get_values(y_pred, "latency")
    return float(np.percentile(latencies, 95))


@ClassFactory.register(ClassType.GENERAL, alias="total_requests")
def total_requests(y_true, y_pred, **kwargs):
    """Number of cloud requests made"""
    vals = _get_values(y_pred, "total_requests")
    return int(np.sum(vals))

# Add to your existing metrics.py

@ClassFactory.register(ClassType.GENERAL, alias="avg_rtt_ms")
def avg_rtt_ms(y_true, y_pred, **kwargs):
    """Average RTT (only for adaptive algorithm)"""
    vals = _get_values(y_pred, "avg_rtt_ms")
    return float(np.mean(vals)) if vals else 0.0