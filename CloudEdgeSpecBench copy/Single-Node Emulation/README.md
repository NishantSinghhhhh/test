cat > "Single-Node Emulation/README.md" <<EOF
# Single-Node Emulation: Cloud-Edge Speculative Decoding
# 单节点仿真：云边协同推测解码

## 1. Overview
This benchmark runs a **Local Emulation** of a Cloud-Edge cluster. Both the "Edge" model (Draft) and "Cloud" model (Verifier) are executed on a single physical machine (your laptop/server).

**Why this mode?**
* **Zero Infrastructure:** No need for separate servers or cloud VMs.
* **Controlled Latency:** We inject artificial Network RTT (e.g., 50ms) to simulate 5G/Fiber/4G.
* **Logic Verification:** Validates the scheduling algorithm before real deployment.

## 2. Project Structure
The emulation environment is isolated in the \`Single-Node Emulation\` folder:

\`\`\`text
CloudEdgeSpecBench/
├── dataset/                            # Shared Dataset (WikiText)
│   ├── wikitext/                       # Raw downloaded files
│   └── samples/                        # Processed split files (0..49)
└── Single-Node Emulation/              # THIS PROJECT
    ├── benchmarkingjob.yaml            # Master Controller
    ├── testenv/                        # Environment Config
    └── testalgorithms/                 # Logic (GPT-2 + GPT-2-Medium)
\`\`\`

---

## 3. Step-by-Step Installation & Run Guide

### Step 1: Install Dependencies
Ensure you have Python 3.8+ and Ianvs installed.

\`\`\`bash
# 1. Create Conda Environment (Recommended)
conda create -n ianvs-experiment python=3.8
conda activate ianvs-experiment

# 2. Install Ianvs and AI Libraries
pip install ianvs numpy pyyaml torch transformers accelerate requests
\`\`\`

### Step 2: Prepare the Dataset
We use the **WikiText** dataset. We must split the large raw file into smaller "test samples" for the benchmark to process.

Run this script from the **root** folder (\`CloudEdgeSpecBench/\`):

\`\`\`bash
# 1. Download WikiText (If you haven't already)
mkdir -p dataset/wikitext
# (Manually place wiki.test.tokens here or download via script)

# 2. Generate 50 Test Samples
python3 -c "
import os

# CONFIG
source_path = os.path.abspath('dataset/wikitext/wiki.test.tokens')
output_dir = os.path.abspath('dataset/samples')
index_file = os.path.abspath('dataset/test_data.txt')

if not os.path.exists(source_path):
    print(f'❌ ERROR: Source file missing at {source_path}')
    exit(1)

os.makedirs(output_dir, exist_ok=True)

# Processing
print(f'Splitting {source_path}...')
with open(source_path, 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')

count = 0
with open(index_file, 'w') as index:
    for i in range(0, len(lines), 50):
        if count >= 50: break # Limit to 50 samples
        snippet = '\n'.join(lines[i:i+50]).strip()
        
        if len(snippet) > 100:
            sample_path = os.path.join(output_dir, f'sample_{count}.txt')
            with open(sample_path, 'w', encoding='utf-8') as out:
                out.write(snippet)
            
            # Write absolute path to index
            index.write(f'{sample_path} 0\n')
            count += 1

print(f'✅ Generated {count} samples in {output_dir}')
print(f'✅ Index updated at {index_file}')
"
\`\`\`

### Step 3: Configure Paths (Crucial)
Since we are inside the \`Single-Node Emulation\` folder, we must ensure our config files point to the dataset in the parent directory.

**A. Update `testenv.yaml`**
Ensure \`test_index\` points to \`../dataset/test_data.txt\`.

\`\`\`bash
# Run this to auto-fix the path
cd "Single-Node Emulation"
INDEX_PATH="\$(pwd)/../dataset/test_data.txt"

cat > testenv/cloud_edge_net/testenv.yaml <<YAML
testenv:
  dataset:
    train_index: "\$INDEX_PATH"
    test_index: "\$INDEX_PATH"
    format: "txt"

  type: "cloud_edge_simulator"
  scenarios:
    - name: "ideal_fiber"
      parameters: { rtt_ms: 10, concurrency: 1 }

  metrics:
    - name: "normalized_speedup"
      url: "./testenv/cloud_edge_net/metrics.py"
    # ... (Other metrics are loaded dynamically)
YAML
\`\`\`

**B. Update `benchmarkingjob.yaml`**
Ensure the workspace is saved outside to keep things clean.

\`\`\`bash
cat > benchmarkingjob.yaml <<YAML
benchmarkingjob:
  name: "cloud_edge_speculative_decoding_benchmark"
  workspace: "../workspace"  # Saves results in parent folder

  testenv: "./testenv/cloud_edge_net/testenv.yaml"

  test_object:
    type: "algorithms"
    algorithms:
      - name: "speculative_decoding"
        url: "./testalgorithms/speculative_decoding/algorithm.yaml"

  rank:
    sort_by: [ { "normalized_speedup": "descend" } ]
    visualization:
      mode: "selected_only"
      method: "print_table"
      
    selected_dataitem:
      metrics: [ "normalized_speedup", "acceptance_rate", "ttft_ms", "p50_latency", "energy_efficiency" ]
      hyperparameters: [ "draft_k", "compute_ratio" ]
YAML
\`\`\`

### Step 4: Run the Benchmark
Now that dependencies, data, and paths are set, execute the simulation.

\`\`\`bash
# Ensure you are inside the 'Single-Node Emulation' folder
rm -rf ../workspace  # Clear previous cache
ianvs -f benchmarkingjob.yaml
\`\`\`

---

## 4. Understanding Results

After the run completes (approx. 2-5 mins depending on CPU/GPU), you will see a table:

| Metric | Interpretation |
| :--- | :--- |
| **normalized_speedup** | **> 1.0**: The Edge collaboration was faster than Cloud-only.<br>**< 1.0**: The Edge device (or network) was too slow. |
| **ttft_ms** | **Time To First Token**. Lower is better. Shows how "snappy" the system feels. |
| **acceptance_rate** | How often the "Boss" (Cloud) agreed with the "Intern" (Edge). typically **0.6 - 0.8** for GPT-2. |
| **draft_k** | The number of tokens the Edge drafted. You will see rows for K=1, 3, 5. |

## 5. Troubleshooting

* **Error: `wc: dataset/test_data.txt: No such file`**
    * You forgot to run the Python script in Step 2.
* **Error: `ModuleNotFoundError: No module named 'transformers'`**
    * You forgot `pip install transformers`.
* **Error: `Speedup is 0.25` (Very slow)**
    * This is normal if running on CPU. The overhead of running two models sequentially on one CPU core outweighs the benefit. Run on GPU for better results.
EOF