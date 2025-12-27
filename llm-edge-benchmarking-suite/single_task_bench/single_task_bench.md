### 1. Unsupported Paradigm Type

**Error**
```

ValueError: not support paradigm(singletasklearningwithcompression)

````

**Cause**  
The algorithm configuration used an unsupported paradigm:
```yaml
paradigm_type: singletasklearningwithcompression
````

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
There is **no `requirements.txt` and no README** for the `single_task_bench` directory.

**Implication**

* Dependencies are **not automatically managed**
* Setup steps and configuration flow are **undocumented**
* Users must infer required steps from trial and error

**Resolution**

* Manually installed required packages (e.g., `llama-cpp-python`, `huggingface_hub`) inside the active Conda environment
* Documented setup, configuration changes, and troubleshooting in a custom `README.md`
