# Government Benchmark: Subjective Task (Text Generation)

## 1. Overview

This benchmark evaluates the **Qwen2-0.5B-Instruct** model on subjective (open-ended) government policy questions.

* **Paradigm:** Single Task Learning
* **Model:**  Qwen2-0.5B-Instruct (Hugging Face)
* **Metric:** LLM-based Judgement (Uses DeepSeek API, or falls back to a dummy score if no API key is present).

---

## 2. Environment Setup

Ensure your Conda environment is active and dependencies are updated.

```bash
# 1. Activate Environment
conda activate ianvs-experiment

# 2. Upgrade Critical Libraries (Required for Qwen2 and OpenAI client)
pip install --upgrade transformers openai

```

---

## 3. Dataset Preparation

### Step 3.1: Organize Files

Move the raw data into the standard `train` and `test` folder structure Ianvs expects.

```bash
# Create directories
mkdir -p dataset/government/subjective/train_data
mkdir -p dataset/government/subjective/test_data

# Copy data files (Using the same file for train/test for demonstration)
cp "dataset/government/subjective questions/data.jsonl" dataset/government/subjective/train_data/
cp "dataset/government/subjective questions/data.jsonl" dataset/government/subjective/test_data/
cp "dataset/government/subjective questions/metadata.json" dataset/government/subjective/test_data/

```

### Step 3.2: Fix Data Schema

The raw dataset is missing specific fields required by the `sedna` library (`level_X_dim`) and uses inconsistent keys (`question` vs `query`).

**Create `fix_data.py`:**

```python
import json
import os

# POINT TO SUBJECTIVE DATASETS
files_to_fix = [
    "dataset/government/subjective/train_data/data.jsonl",
    "dataset/government/subjective/test_data/data.jsonl"
]

for file_path in files_to_fix:
    if not os.path.exists(file_path):
        print(f"Skipping {file_path} (not found)")
        continue
        
    print(f"Fixing {file_path}...")
    fixed_lines = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            try:
                data = json.loads(line)
                
                # 1. Add missing dimension fields (Level 1-5)
                for i in range(1, 6):
                    key = f"level_{i}_dim"
                    if key not in data:
                        data[key] = None
                
                # 2. Standardize keys: 'question' -> 'query'
                if "question" in data and "query" not in data:
                    data["query"] = data.pop("question")
                
                # 3. Standardize keys: 'answer' -> 'response'
                if "answer" in data and "response" not in data:
                    data["response"] = data.pop("answer")
                    
                fixed_lines.append(json.dumps(data, ensure_ascii=False))
            except json.JSONDecodeError:
                print(f"Skipping bad line in {file_path}")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))
    print(f"Done! Fixed {len(fixed_lines)} lines.")

```

**Run the fix:**

```bash
python fix_data.py

```

---

## 4. Configuration & Code Updates

We must update 4 files to fix hardcoded paths, enable CPU support, and set hyperparameters.

### File 1: `basemodel.py`

**Location:** `examples/government/singletask_learning_bench/subjective/testalgorithms/gen/basemodel.py`
**Changes Made:**

* Added `import torch` and dynamic device detection (CPU vs CUDA).
* Updated `_openai_generate` to handle missing API keys gracefully.
* Removed hardcoded model path; uses `kwargs.get("model")`.

### File 2: `gen_algorithm.yaml`

**Location:** `examples/government/singletask_learning_bench/subjective/testalgorithms/gen/gen_algorithm.yaml`
**Changes Made:**

* Added `hyperparameters` section to pass the model name.

```yaml
algorithm:
  paradigm_type: "singletasklearning"
  modules:
    - type: "basemodel"
      name: "gen"
      url: "./examples/government/singletask_learning_bench/subjective/testalgorithms/gen/basemodel.py"
      hyperparameters:
        - model:
            values:
              - "Qwen/Qwen2-0.5B-Instruct"

```

### File 3: `testenv.yaml`

**Location:** `examples/government/singletask_learning_bench/subjective/testenv/testenv.yaml`
**Changes Made:**

* Pointed `train_data` and `test_data_info` to your local `./dataset` folder instead of `/home/icyfeather`.

### File 4: `benchmarkingjob.yaml`

**Location:** `examples/government/singletask_learning_bench/subjective/benchmarkingjob.yaml`
**Changes Made:**

* Updated `workspace` path to `./workspace_subjective`.
* Ensured `testenv` and `algorithms` urls point to the correct relative paths.

---

## 5. Running the Benchmark

### Option A: With API Key (Real Evaluation)

If you have a DeepSeek API key, the benchmark will accurately judge the quality of answers.

```bash
export DEEPSEEK_API_KEY="your_actual_key_here"
ianvs -f examples/government/singletask_learning_bench/subjective/benchmarkingjob.yaml

```

### Option B: Without API Key (Testing Pipeline)

If you do not have a key, the code will default to a dummy score (5.0) to verify the pipeline works.

```bash
ianvs -f examples/government/singletask_learning_bench/subjective/benchmarkingjob.yaml

```

---

## 6. Troubleshooting: Errors Encountered & Solutions

These are the specific errors we faced during setup and the solutions we applied.

### Error 1: Outdated OpenAI Library

**Error Message:** `ImportError: cannot import name 'OpenAI' from 'openai'`
**Cause:** The installed `openai` library (likely v0.28) was too old to support the new v1.0+ client syntax used in the script.
**Solution:** Upgraded the library:

```bash
pip install --upgrade openai

```

### Error 2: Hardcoded GPU (CUDA) Usage

**Error Message:** `AssertionError: Torch not compiled with CUDA enabled`
**Cause:** The script `basemodel.py` had `device = "cuda"` hardcoded, but the machine only had a CPU.
**Solution:** Patched `basemodel.py` to auto-detect hardware:

```python
device = "cuda" if torch.cuda.is_available() else "cpu"
# Explicitly move model and inputs to 'device'

```

### Error 3: Hardcoded Absolute Paths

**Error Message:** `OSError: Incorrect path_or_model_id: '/home/icyfeather/...'`
**Cause:** Configuration files pointed to the original developer's home directory.
**Solution:** Updated `testenv.yaml` and `basemodel.py` to point to the local `./dataset` folder and use the Hugging Face model ID.

### Error 4: Dataset Schema Mismatch

**Error Message:** `KeyError: 'level_3_dim'` and `KeyError: 'query'`
**Cause:** The `sedna` library expected fields (`level_1_dim`...`level_5_dim`, `query`, `response`) that were missing or named differently in the raw JSONL data.
**Solution:** Ran the `fix_data.py` script to rename keys (`question`→`query`) and inject `null` values for missing dimensions.

### Error 5: Missing Hyperparameters

**Error Message:** `RuntimeError: ... error: 'model'`
**Cause:** The `gen_algorithm.yaml` file lacked the `hyperparameters` block, so the Python script received no model name.
**Solution:** Added the `hyperparameters` block to the YAML file to explicitly pass `"Qwen/Qwen2-0.5B-Instruct"`.

### Error 6: Missing API Key

**Error Message:** `ValueError: You should set DEEPSEEK_API_KEY` (Potential)
**Cause:** The benchmark evaluation relies on an external API (DeepSeek).
**Solution:** Added fallback logic in `basemodel.py` to return a dummy score if the environment variable is missing, allowing the benchmark to complete without crashing.

## 🎥 Screencast: AoA TForest Example


<video controls width="100%">
  <source src="assets/videos/goverment_single_subjective.webm" type="video/webm">
  Your browser does not support the video tag.
</video>

▶️ [Download screencast](assets/videos/goverment_single_subjective.webm)
