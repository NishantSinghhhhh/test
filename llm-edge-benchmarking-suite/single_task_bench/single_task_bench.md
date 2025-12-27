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

## 🎥 Screencast: Multi-Algorithm (Multi-Model) Benchmarking

The following screencast shows the Simple QA benchmark running with
**multiple algorithms (Qwen 0.5B vs Qwen 1.5B)** using the same dataset,
test environment, and metric in IANVS.

[https://github.com/user-attachments/assets/single_task_bench.md.webm](https://github.com/NishantSinghhhhh/test/blob/master/assets/single_task_bench.md.webm)

###  Link to download
▶️ [Download screencast](assets/single_task_bench.md.webm)

