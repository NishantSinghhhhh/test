# Codebase Changes for Multi-Algorithm (Multi-Model) Benchmarking

This document describes the **exact codebase changes** required to extend the Simple QA example from a **single model run** to **multiple algorithm (model) comparison** using IANVS.

The final folder structure assumed is:

```

llm_simple_qa/
├── testalgorithms/
│   └── gen/
│       ├── basemodel.py
│       ├── gen_algorithm.yaml
│       ├── gen_qwen_05b.yaml
│       ├── gen_qwen_15b.yaml
│       └── op_eval.py
├── testenv/
│   ├── acc.py
│   └── testenv.yaml
├── benchmarkingjob.yaml
└── README.md

````

---

## 1️⃣ Make the Base Model Configurable (`basemodel.py`)

### ❌ Before
The model ID was hard-coded, preventing comparison.

### ✅ After
The model ID is passed via **hyperparameters** from YAML.

### Required Change
```python
@ClassFactory.register(ClassType.GENERAL, alias="gen")
class BaseModel:

    def __init__(self, model_id="Qwen/Qwen2-0.5B-Instruct", **kwargs):
        self.model_id = model_id
````

And load the model dynamically:

```python
self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
self.model = AutoModelForCausalLM.from_pretrained(
    self.model_id,
    torch_dtype="auto",
    device_map="auto"
)
```

### Why this change is required

IANVS compares **algorithms**, and algorithms are driven by configuration.
Hard-coding the model prevents meaningful comparison.

---

## 2️⃣ Keep Metric Logic Generic (`testenv/acc.py`)

No structural change was required.

### Minor Fix Applied

A guard against division by zero was added:

```python
if len(same_elements) == 0:
    return 0.0
```

### Why

Prevents crashes when no valid predictions are returned.

---

## 3️⃣ Create Multiple Algorithm Configurations

Each algorithm is defined by a **separate YAML file** using the same model wrapper.

---

### `gen_qwen_05b.yaml`

```yaml
algorithm:
  paradigm_type: "singletasklearning"
  modules:
    - type: "basemodel"
      name: "gen"
      url: "./examples/llm_simple_qa/testalgorithms/gen/basemodel.py"
      hyperparameters:
        - model_id:
            values:
              - "Qwen/Qwen2-0.5B-Instruct"
```

---

### `gen_qwen_15b.yaml`

```yaml
algorithm:
  paradigm_type: "singletasklearning"
  modules:
    - type: "basemodel"
      name: "gen"
      url: "./examples/llm_simple_qa/testalgorithms/gen/basemodel.py"
      hyperparameters:
        - model_id:
            values:
              - "Qwen/Qwen2-1.5B-Instruct"
```

---

### Why separate files?

IANVS treats **each algorithm YAML as an independent experiment**, even if the code is shared.

---

## 4️⃣ Update the Benchmarking Job (`benchmarkingjob.yaml`)

Register **multiple algorithms** under `test_object.algorithms`.

```yaml
test_object:
  type: "algorithms"
  algorithms:
    - name: "qwen_05b"
      url: "./examples/llm_simple_qa/testalgorithms/gen/gen_qwen_05b.yaml"

    - name: "qwen_15b"
      url: "./examples/llm_simple_qa/testalgorithms/gen/gen_qwen_15b.yaml"
```

### Why this matters

Only algorithms listed here are executed and compared.

---

## 5️⃣ No Changes Required Elsewhere

The following files **did not require modification**:

* `testenv.yaml`
* dataset format
* metric registration
* CLI command

Comparison is **purely configuration-driven**.

---

## ✅ Final Outcome

After these changes, running:

```bash
ianvs -f examples/llm_simple_qa/benchmarkingjob.yaml
```

Will:

* Run **multiple models**
* Use the **same dataset and metric**
* Rank results automatically
* Preserve experiment history

---

## 🧠 Key Design Principle

> **IANVS compares algorithms, not models.**
> A model + configuration = one algorithm.
