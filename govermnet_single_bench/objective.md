# Complete Summary: Government Single-Task Learning Setup

## Overview

We configured and executed a Large Language Model (LLM) benchmark using the **Ianvs** framework. The goal was to evaluate a **Qwen2-0.5B** model on a Chinese government policy dataset for objective (multiple-choice) questions.

---

## Steps We Followed

### 1. **Initial Environment Setup**

* Activated the conda environment: `ianvs-experiment`
* Navigated to the root directory: `~/LOCAL_DISK_D/ianvs`
* Verified the project structure for the `government` example.

### 2. **Dataset Preparation**

* Identified that the dataset was initially in a folder named `multi-choice questions`.
* Manually moved/copied data to the expected Ianvs structure:
```bash
cp "dataset/government/multi-choice questions/data.jsonl" dataset/government/objective/train_data/
cp "dataset/government/multi-choice questions/data.jsonl" dataset/government/objective/test_data/

```



### 3. **Configuration & Code Alignment**

* Created and refined `gen_algorithm.yaml` to define the model hyperparameters.
* Updated `basemodel.py` to correctly load the Hugging Face model instead of a local path.
* Updated `testenv.yaml` to point to the correct data indices.

---

## All Errors Encountered & Solutions

### **Error 1: YAML Syntax - 'str' object has no attribute 'popitem'**

**Cause:** The `hyperparameters` in `gen_algorithm.yaml` were provided as a simple string instead of a list of dictionaries.
**Solution:** Added the required dash (`-`) before the parameter name to satisfy the Ianvs parser.

---

### **Error 2: YAML Format - 'str' object has no attribute 'get'**

**Cause:** Ianvs expects a "grid search" format even for a single value.
**Solution:** Formatted the hyperparameter as a nested dictionary:

```yaml
hyperparameters:
  - model:
      values:
        - "Qwen/Qwen2-0.5B-Instruct"

```

---

### **Error 3: Hardcoded Paths (The "icyfeather" Error)**

**Error Message:** `OSError: Incorrect path_or_model_id: '/home/icyfeather/models/...'`
**Cause:** The Python script `basemodel.py` had a hardcoded path belonging to a different user/environment.
**Solution:** Modified `basemodel.py` to use a dynamic variable `kwargs.get("model")` that reads from the YAML config.

---

### **Error 4: Outdated Transformers Library**

**Error Message:** `KeyError: 'qwen2'`
**Cause:** The version of `transformers` (4.36.2) was too old to recognize the newer Qwen2 architecture.
**Solution:** Upgraded the library: `pip install --upgrade transformers` (to 4.46.3).

---

### **Error 5: Dataset Schema Mismatch (Query vs Question)**

**Error Message:** `KeyError: 'query'` followed by `KeyError: 'question'`
**Cause:** The `sedna` library was internally inconsistent, looking for "query" in one function and "question" in another.
**Solution:** 1. Patched the `sedna` library file `datasources/__init__.py` to use "query" consistently.
2. Renamed dataset fields: `question` → `query` and `answer` → `response`.

---

### **Error 6: Missing Metadata Fields**

**Error Message:** `KeyError: 'level_3_dim'`
**Cause:** The benchmark framework expected hierarchy levels (Level 1-5) which were missing from the raw JSONL.
**Solution:** Created a Python script (`fix_data.py`) to inject `null` values for `level_1_dim` through `level_5_dim` into every line of the dataset.

---

### **Error 7: CUDA/GPU Absence**

**Error Message:** `AssertionError: Torch not compiled with CUDA enabled`
**Cause:** The code was hardcoded to `device = "cuda"`.
**Solution:** Updated `basemodel.py` with a hardware-agnostic check:

```python
device = "cuda" if torch.cuda.is_available() else "cpu"
# Explicitly moved model and inputs to 'device'

```

---

## Final Result

### **Success! Benchmark Running**

```bash
Processing:   0%|            | 1/1600 [00:27<12:17:14, 27.66s/question]

```
## 🎥 Screencast: AoA TForest Example


<video controls width="100%">
  <source src="assets/videos/govermnet_single_objective.webm" type="video/webm">
  Your browser does not support the video tag.
</video>

▶️ [Download screencast](assets/videos/govermnet_single_objective.webm)

