## 1. Dependency Errors Due to Version Mismatches

| Dependency | Error Encountered |
|-----------|------------------|
| **numpy (>= 2.0.0)** | `No matching distribution found for numpy>=2.0.0` |
| **membership-inference-attacks** | `No matching distribution found for membership-inference-attacks` |
| **torchvision** | `torchvision requires torch==2.4.0` |
| **vllm** | `vllm requires torch==2.4.0`<br>`vllm requires openai>=1.40.0`<br>`vllm requires transformers>=4.45.2` |
| **xformers** | `xformers requires torch==2.4.0` |
| **bitsandbytes** | CUDA/Triton dependency conflicts causing Torch version breakage |
| **huggingface_hub** | `ImportError: cannot import name 'get_full_repo_name'` |
| **accelerate** | Reintroduced `get_full_repo_name` import error via forced hub upgrade |
| **datasets** | Forced `huggingface_hub>=0.23`, breaking Transformers compatibility |
| **transformers (>= 4.37)** | `ImportError: cannot import name 'get_full_repo_name'` |

```md

# PIPL Error Log (Non-Dataset Issues Only)

This document lists **all non-data-related errors** encountered while setting up and running the PIPL benchmark, along with their **reason** and **proof**.  
Errors related to dataset structure or fields have been intentionally removed.

---

## 1. ModuleNotFoundError: `No module named 'privacy_preserving_llm'`

**Reason**  
IANVS attempted to load the algorithm using a filesystem-style path instead of a Python importable module path.

**Proof**
```

load module(url=./privacy_preserving_llm/privacy_preserving_llm.py) failed
No module named 'privacy_preserving_llm'

````
Resolved when importing via:
```python
from test_algorithms.privacy_preserving_llm.privacy_preserving_llm import PrivacyPreservingLLM
````

---

## 2. ClassFactory Registry Error

`can't find class type general class name privacy-preserving-llm-collaboration`

**Reason**
The class name referenced in `algorithm.yaml` was never registered using `ClassFactory.register`.

**Proof**

```
ValueError: can't find class type general class name privacy-preserving-llm-collaboration
```

Confirmed by:

```python
ClassFactory.get_cls(ClassType.GENERAL, "privacy-preserving-llm-collaboration")
```

---

## 3. JointInference Module Requirement Error

`Required modules: {'edgemodel','cloudmodel','hard_example_mining'}, but got {'basemodel'}`

**Reason**
The `jointinference` paradigm strictly requires three module types.
The configuration still contained `basemodel`.

**Proof**

```
KeyError: Required modules: {'hard_example_mining', 'cloudmodel', 'edgemodel'}, but got: dict_keys(['basemodel'])
```

---

## 4. TensorFlow Backend Missing

`ModuleNotFoundError: No module named 'tensorflow'`

**Reason**
Sedna defaulted to the TensorFlow backend when no backend was explicitly resolved.

**Proof**

```
from sedna.backend.tensorflow import TFBackend
ModuleNotFoundError: No module named 'tensorflow'
```

---

## 5. typing_extensions / Pydantic Conflict

`ImportError: cannot import name 'TypeIs' from 'typing_extensions'`

**Reason**
Installing TensorFlow downgraded `typing_extensions`, breaking Pydantic v2 compatibility.

**Proof**

```
ImportError: cannot import name 'TypeIs'
```

Resolved only after upgrading `typing_extensions`.

---

## 6. HuggingFace Model Load Failure

`meta-llama/Llama-3-8B-Instruct is not a valid model identifier`

**Reason**
The model is gated/private and requires authentication.

**Proof**

```
If this is a private repository, make sure to pass a token
```

---

## 7. Sedna JointInference model_path Crash

`AttributeError: 'NoneType' object has no attribute 'lstrip'`

**Reason**
Sedna JointInference **requires** `algorithm.parameters.model_path`.
Module-level `model_path` is ignored.

**Proof**

```
sedna/core/base.py → model_path → FileOps.join_path
NoneType has no attribute 'lstrip'
```

---

## 8. model_path Ignored at Module Level

**Reason**
Even after adding `model_path` to `edgemodel`, `cloudmodel`, and `hard_example_mining`, Sedna ignored it.

**Proof**
The same `NoneType.lstrip` crash persisted, confirming Sedna only reads:

```yaml
algorithm:
  parameters:
    model_path: ...
```

---

## 9. Configuration File Mismatch / Cache Issue

**Reason**
IANVS continued to load an older or different algorithm configuration file.

**Proof**

```
got dict_keys(['basemodel'])
```

appeared even after `basemodel` was removed from the edited YAML.

---

## 10. TensorFlow / CUDA / spaCy Runtime Warnings

**Reason**
Optional dependencies missing or running in CPU fallback mode.

**Proof**
Warnings explicitly state fallback behavior and do not stop execution.

---

## 11. Chinese BERT TokenClassification Warning

**Reason**
NER model loaded without fine-tuned classification head.

**Proof**

```
Some weights were not initialized
You should probably TRAIN this model
```

Warning only, not fatal.

