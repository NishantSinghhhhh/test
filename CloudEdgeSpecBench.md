# Cloud-Edge Speculative Decoding Benchmark
# 云边协同推测解码基准测试

## 1. Overview
This benchmark quantitatively evaluates the trade-off between **Edge-Side Drafting** and **Cloud-Side Verification** in Speculative Decoding systems. 

Unlike standard benchmarks that only measure raw throughput, this benchmark specifically targets the **"Cloud-Edge Break-Point"**—identifying the exact Network RTT and Device Latency thresholds where collaboration becomes slower than a simple direct-to-cloud request.

## 2. Key Features
* **Network Simulation:** Simulates Fiber (10ms), 5G (40ms), and 4G (100ms+) environments with Jitter.
* **Device Profiling:** Simulates diverse Edge devices via \`compute_ratio\` (e.g., Jetson Orin vs. Raspberry Pi).
* **Realistic Metrics:** * **Normalized Speedup:** Does it actually beat the cloud baseline?
    * **p95 Latency:** Is the system stable under network jitter?
    * **Energy Efficiency:** Estimated battery impact on the Edge device.

## 3. Project Structure
\`\`\`text
CloudEdgeSpecBench/
├── benchmarkingjob.yaml                # Master Controller (Run this file)
├── testenv/
│   └── cloud_edge_net/
│       ├── testenv.yaml                # Network Scenarios (RTT, Jitter, Concurrency)
│       └── metrics.py                  # KPI Calculations (Speedup, p95)
└── testalgorithms/
    └── speculative_decoding/
        ├── algorithm.yaml              # Strategy Settings (Draft K, Task Domain)
        ├── spec_scheduler.py           # The "Boss & Intern" Logic
        └── basemodel.py                # Standard Ianvs Interface
\`\`\`

## 4. How to Run

1. **Install Dependencies** (Ensure you have Ianvs installed):
\`\`\`bash
pip install ianvs numpy pyyaml
\`\`\`

2. **Execute the Benchmark**:
\`\`\`bash
ianvs -f benchmarkingjob.yaml
\`\`\`

## 5. Understanding the Results

After running, Ianvs will output a table. Here is how to read the columns:

| Metric | Goal | Interpretation |
| --- | --- | --- |
| **normalized_speedup** | \`> 1.0\` | **>1.2** is good. **<1.0** means the Edge is too slow or Network is too bad. |
| **p95_latency** | Low | High values indicate "stuttering" due to network jitter. |
| **acceptance_rate** | \`> 0.6\` | If low, the "Intern" (Edge Model) is guessing wrong too often. |
| **energy_efficiency** | Low | Joules consumed per generated token on the Edge device. |

## 6. Modifying the Test

* **To change Network conditions:** Edit \`testenv/cloud_edge_net/testenv.yaml\`.
* **To change Draft Length (K):** Edit \`testalgorithms/speculative_decoding/algorithm.yaml\`.

## 7. Example Results (Latest Run)
ianvs-experiment) nishant@Development-arc:~/LOCAL_DISK_D/ianvs/examples/CloudEdgeSpecBench$ ianvs -f benchmarkingjob.yaml

[INIT] Device: CPU | K=3 | Ratio=1.0
2026-02-02 19:11:15.248032: I tensorflow/stream_executor/platform/default/dso_loader.cc:50] Successfully opened dynamic library libcudart.so.12
WARNING:tensorflow:Deprecation warnings have been disabled. Set TF_ENABLE_DEPRECATION_WARNINGS=1 to re-enable them.
WARNING:root:Limited tf.compat.v2.summary API due to missing TensorBoard installation.
/home/nishant/miniconda3/envs/ianvs-experiment/lib/python3.8/site-packages/torchvision/datapoints/__init__.py:12: UserWarning: The torchvision.datapoints and torchvision.transforms.v2 namespaces are still Beta. While we do not expect major breaking changes, some APIs may still change according to user feedback. Please submit any feedback you may have in this issue: https://github.com/pytorch/vision/issues/6753, and you can also check out https://github.com/pytorch/vision/issues/7319 to learn more about the APIs that we suspect might involve future changes. You can silence this warning by calling torchvision.disable_beta_transforms_warning().
  warnings.warn(_BETA_TRANSFORMS_WARNING)
/home/nishant/miniconda3/envs/ianvs-experiment/lib/python3.8/site-packages/torchvision/transforms/v2/__init__.py:54: UserWarning: The torchvision.datapoints and torchvision.transforms.v2 namespaces are still Beta. While we do not expect major breaking changes, some APIs may still change according to user feedback. Please submit any feedback you may have in this issue: https://github.com/pytorch/vision/issues/6753, and you can also check out https://github.com/pytorch/vision/issues/7319 to learn more about the APIs that we suspect might involve future changes. You can silence this warning by calling torchvision.disable_beta_transforms_warning().
  warnings.warn(_BETA_TRANSFORMS_WARNING)
[BENCHMARK] Processing 50 Samples...
The attention mask is not set and cannot be inferred from input because pad token is same as eos token. As a consequence, you may observe unexpected behavior. Please pass your input's `attention_mask` to obtain reliable results.
[1] TTFT: 335ms | Latency: 3.84s | Speed: 5.47 t/s
[2] TTFT: 314ms | Latency: 3.23s | Speed: 6.50 t/s
[3] TTFT: 238ms | Latency: 3.44s | Speed: 6.11 t/s
[4] TTFT: 147ms | Latency: 2.84s | Speed: 7.40 t/s
[5] TTFT: 259ms | Latency: 3.78s | Speed: 5.55 t/s
[6] TTFT: 209ms | Latency: 4.42s | Speed: 4.76 t/s
[7] TTFT: 245ms | Latency: 3.88s | Speed: 5.41 t/s
[8] TTFT: 382ms | Latency: 4.23s | Speed: 4.96 t/s
[9] TTFT: 170ms | Latency: 3.40s | Speed: 6.17 t/s
[10] TTFT: 210ms | Latency: 3.28s | Speed: 6.41 t/s
[11] TTFT: 225ms | Latency: 3.78s | Speed: 5.56 t/s
[12] TTFT: 304ms | Latency: 3.81s | Speed: 5.51 t/s
[13] TTFT: 359ms | Latency: 3.30s | Speed: 6.37 t/s
[14] TTFT: 744ms | Latency: 4.29s | Speed: 4.90 t/s
[15] TTFT: 268ms | Latency: 3.53s | Speed: 5.95 t/s
[16] TTFT: 284ms | Latency: 4.52s | Speed: 4.65 t/s
[17] TTFT: 152ms | Latency: 3.11s | Speed: 6.75 t/s
[18] TTFT: 177ms | Latency: 3.69s | Speed: 5.69 t/s
[19] TTFT: 209ms | Latency: 4.18s | Speed: 5.02 t/s
[20] TTFT: 308ms | Latency: 3.90s | Speed: 5.38 t/s
[21] TTFT: 557ms | Latency: 4.54s | Speed: 4.63 t/s
[22] TTFT: 186ms | Latency: 3.85s | Speed: 5.46 t/s
[23] TTFT: 205ms | Latency: 3.48s | Speed: 6.04 t/s
[24] TTFT: 186ms | Latency: 3.29s | Speed: 6.39 t/s
[25] TTFT: 199ms | Latency: 3.51s | Speed: 5.98 t/s
[26] TTFT: 207ms | Latency: 4.27s | Speed: 4.92 t/s
[27] TTFT: 268ms | Latency: 4.14s | Speed: 5.07 t/s
[28] TTFT: 212ms | Latency: 4.12s | Speed: 5.10 t/s
[29] TTFT: 251ms | Latency: 3.39s | Speed: 6.20 t/s
[30] TTFT: 192ms | Latency: 3.28s | Speed: 6.40 t/s
[31] TTFT: 184ms | Latency: 3.02s | Speed: 6.94 t/s
[32] TTFT: 223ms | Latency: 3.50s | Speed: 6.00 t/s
[33] TTFT: 195ms | Latency: 4.26s | Speed: 4.93 t/s
[34] TTFT: 256ms | Latency: 3.15s | Speed: 6.67 t/s
[35] TTFT: 188ms | Latency: 3.12s | Speed: 6.73 t/s
[36] TTFT: 244ms | Latency: 4.24s | Speed: 4.95 t/s
[37] TTFT: 269ms | Latency: 3.58s | Speed: 5.86 t/s
[38] TTFT: 346ms | Latency: 3.38s | Speed: 6.22 t/s
[39] TTFT: 375ms | Latency: 4.03s | Speed: 5.21 t/s
[40] TTFT: 308ms | Latency: 5.78s | Speed: 3.63 t/s
[41] TTFT: 2609ms | Latency: 6.80s | Speed: 3.09 t/s
[42] TTFT: 217ms | Latency: 4.40s | Speed: 4.78 t/s
[43] TTFT: 333ms | Latency: 3.91s | Speed: 5.37 t/s
[44] TTFT: 172ms | Latency: 3.34s | Speed: 6.29 t/s
[45] TTFT: 322ms | Latency: 3.67s | Speed: 5.73 t/s
[46] TTFT: 286ms | Latency: 3.53s | Speed: 5.95 t/s
[47] TTFT: 184ms | Latency: 3.14s | Speed: 6.68 t/s
[48] TTFT: 1272ms | Latency: 5.07s | Speed: 4.14 t/s
[49] TTFT: 238ms | Latency: 4.00s | Speed: 5.25 t/s
[50] TTFT: 277ms | Latency: 3.82s | Speed: 5.50 t/s
+------+----------------------+--------------------+-------------------+--------------------+--------------------+--------------------+-------------------+--------------------+--------------------+--------------------+----------------------+---------+---------------+--------------+-------------+---------------------+-----------------------------------------------------------------------------------------------------------------+
| rank |      algorithm       | normalized_speedup |  throughput_tok_s |  acceptance_rate   |      ttft_ms       |    p50_latency     |    p95_latency    |   stream_jitter    | energy_efficiency  |      paradigm      |      basemodel       | draft_k | compute_ratio | dataset_task | concurrency |         time        |                                                       url                                                       |
+------+----------------------+--------------------+-------------------+--------------------+--------------------+--------------------+-------------------+--------------------+--------------------+--------------------+----------------------+---------+---------------+--------------+-------------+---------------------+-----------------------------------------------------------------------------------------------------------------+
|  1   | speculative_decoding | 0.3094025221913644 | 6.509751975264081 | 0.5999999999999999 | 146.94523811340332 | 3.175128579139709  | 3.480122411251068 | 0.1443897696444878 | 323.2035708427429  | singletasklearning | cloud_edge_scheduler |    3    |      1.0      |      1       |      1      | 2026-02-02 19:05:54 | ./workspace/cloud_edge_speculative_decoding_benchmark/speculative_decoding/036917a2-003c-11f1-adcf-7cb566cc3837 |
|  2   | speculative_decoding | 0.2603876229899036 | 5.613038843047288 | 0.6000000000000001 | 330.03888607025146 | 3.7809853553771973 | 4.829549539089202 | 0.6906462667972331 | 384.04283142089844 | singletasklearning | cloud_edge_scheduler |    3    |      1.0      |      1       |      1      | 2026-02-02 19:14:29 | ./workspace/cloud_edge_speculative_decoding_benchmark/speculative_decoding/d7849b6a-003c-11f1-ba66-7cb566cc3837 |
+------+----------------------+--------------------+-------------------+--------------------+--------------------+--------------------+-------------------+--------------------+--------------------+--------------------+----------------------+---------+---------------+--------------+-------------+---------------------+-----------------------------------------------------------------------------------------------------------------+
[2026-02-02 19:14:29,388] benchmarking.py(39) [INFO] - benchmarkingjob runs successfully.
(ianvs-experiment) nishant@Development-arc:~/LOCAL_DISK_D/ianvs/examples/CloudEdgeSpecBench$ 
> **Note:** A \`normalized_speedup\` of 0.253 indicates that in this specific configuration (CPU-only), the overhead of the "Edge" model was higher than the gain. To see speedups > 1.0, run this on a machine with a dedicated GPU (CUDA).