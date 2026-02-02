import numpy as np
from sedna.common.class_factory import ClassFactory, ClassType

def _get_values(y_pred, key):
    values = []
    if isinstance(y_pred, dict): return [y_pred.get(key, 0.0)]
    if isinstance(y_pred, list):
        for item in y_pred:
            if isinstance(item, dict): values.append(item.get(key, 0.0))
    return values if values else [0.0]

# --- Standard Metrics ---
@ClassFactory.register(ClassType.GENERAL, alias="normalized_speedup")
def normalized_speedup(y_true, y_pred, **kwargs):
    avg_latency = np.mean(_get_values(y_pred, "latency"))
    return 1.0 / avg_latency if avg_latency > 0 else 0.0

@ClassFactory.register(ClassType.GENERAL, alias="p95_latency")
def p95_latency(y_true, y_pred, **kwargs):
    return float(np.percentile(_get_values(y_pred, "latency"), 95))

@ClassFactory.register(ClassType.GENERAL, alias="acceptance_rate")
def acceptance_rate(y_true, y_pred, **kwargs):
    return float(np.mean(_get_values(y_pred, "final_acceptance_rate")))

@ClassFactory.register(ClassType.GENERAL, alias="energy_efficiency")
def energy_efficiency(y_true, y_pred, **kwargs):
    return float(np.mean(_get_values(y_pred, "energy")))

@ClassFactory.register(ClassType.GENERAL, alias="throughput_tok_s")
def throughput_tok_s(y_true, y_pred, **kwargs):
    return float(np.mean(_get_values(y_pred, "throughput")))

@ClassFactory.register(ClassType.GENERAL, alias="stream_jitter")
def stream_jitter(y_true, y_pred, **kwargs):
    return float(np.std(_get_values(y_pred, "latency")))

# --- NEW METRICS (Filling the Blank Columns) ---

@ClassFactory.register(ClassType.GENERAL, alias="p50_latency")
def p50_latency(y_true, y_pred, **kwargs):
    """Median Latency"""
    return float(np.percentile(_get_values(y_pred, "latency"), 50))

@ClassFactory.register(ClassType.GENERAL, alias="ttft_ms")
def ttft_ms(y_true, y_pred, **kwargs):
    """Time To First Token (Average)"""
    return float(np.mean(_get_values(y_pred, "ttft_ms")))

# --- Pass-Through Hyperparameters ---

@ClassFactory.register(ClassType.GENERAL, alias="draft_k")
def draft_k(y_true, y_pred, **kwargs):
    vals = _get_values(y_pred, "draft_k")
    return int(vals[0]) if vals else 0

@ClassFactory.register(ClassType.GENERAL, alias="compute_ratio")
def compute_ratio(y_true, y_pred, **kwargs):
    vals = _get_values(y_pred, "compute_ratio")
    return float(vals[0]) if vals else 0.0

@ClassFactory.register(ClassType.GENERAL, alias="concurrency")
def concurrency(y_true, y_pred, **kwargs):
    return 1  # Hardcoded as per testenv settings

@ClassFactory.register(ClassType.GENERAL, alias="dataset_task")
def dataset_task(y_true, y_pred, **kwargs):
    # Returns 1 for WikiText
    vals = _get_values(y_pred, "dataset_task")
    return int(vals[0]) if vals else 0
