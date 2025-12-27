### 1. Unsupported Paradigm Type

**Error**
```
ValueError: not support paradigm(singletasklearningwithcompression)
```

**Cause**  
The algorithm configuration used an unsupported paradigm:
```yaml
paradigm_type: singletasklearningwithcompression
```

IANVS only supports a fixed, predefined set of paradigms.

**Resolution**
Updated the algorithm configuration to a supported paradigm:

```yaml
paradigm_type: singletasklearning
```

---

### 2. Dataset Path Not Local or Absolute

**Error**

```
ValueError: dataset file(...) is not a local file and not an absolute path
```

**Cause**
The dataset paths in `testenv.yaml` pointed to non-existent or non-local locations.

**Resolution**
Created a local dataset directory inside `single_task_bench` and updated paths:

```yaml
train_data: "./dataset/train_data/data.jsonl"
test_data: "./dataset/test_data/data.jsonl"
```

IANVS strictly requires dataset paths to be local or absolute.

---

### 3. No `requirements.txt` or README Provided

**Observation**
There is **no `requirements.txt` and no README** provided for the `single_task_bench` directory.

**Implication**

* Dependencies are **not automatically managed**
* Setup steps and configuration flow are **undocumented**
* Users must infer required steps through trial and error

**Resolution**

* Manually installed required packages (e.g., `llama-cpp-python`, `huggingface_hub`) inside the active Conda environment
* Added custom documentation capturing setup, configuration changes, and troubleshooting

---

## 🎥 Screencast: single_task_bench 

RUnning of benchmarkingJob.yml is shown below

https://github.com/user-attachments/assets/single_task_bench.md.webm

**Alternative display options:**

### Option 1: Using relative path (if video is in the repo)
![Screencast Demo](assets/single_task_bench.md.webm)

### Option 2: Using GitHub's raw content URL
https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/assets/single_task_bench.md.webm

### Option 3: Link to download
▶️ [Download screencast](assets/single_task_bench.md.webm)

