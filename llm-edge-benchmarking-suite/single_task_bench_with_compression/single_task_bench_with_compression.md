# single_task_bench_with_compression — Known Errors

This document records the **blocking errors** encountered while running
`single_task_bench_with_compression` in **IANVS**, along with their causes and resolutions.

---

## 1. Unsupported Paradigm Type

### Error

```text
ValueError: not support paradigm(singletasklearningwithcompression)
```

### Cause

The algorithm configuration used an **unsupported paradigm type**:

```yaml
paradigm_type: singletasklearningwithcompression
```

IANVS only supports a **fixed set of registered paradigms**, and
`singletasklearningwithcompression` is **not one of them**.

### Resolution

Updated the algorithm configuration to a supported paradigm:

```yaml
paradigm_type: singletasklearning
```

Compression is handled at the **model/runtime level**, not via the paradigm.

---

## 2. Qwen Model Not Downloadable as GGUF from Hugging Face

### Error

```text
404 Client Error: Repository Not Found
```

or

```text
RepositoryNotFoundError: No such file or directory
```

### Cause

The Qwen repositories on Hugging Face (e.g. `Qwen/Qwen1.5-0.5B`) provide
**PyTorch weights (`.safetensors`)**, not **GGUF files**.

Since `single_task_bench_with_compression` uses **llama.cpp**, it requires
models in **GGUF format**, which are **not available** in the official Qwen repositories.

### Resolution

Switched to a model that is already available in **GGUF format**, downloaded from a
community-maintained repository (e.g. TheBloke).

Example working alternative:

* `TinyLLaMA-1.1B-Chat` (GGUF, llama.cpp compatible)

---

## 3. Missing `requirements.txt` and README

### Observation

The `single_task_bench_with_compression` directory does **not contain**:

* a `requirements.txt` file
* a README describing setup, dependencies, or execution flow

### Impact

* Required Python dependencies are **not explicitly documented**
* Environment setup must be inferred through trial and error
* New users lack guidance on how to run the benchmark correctly

### Resolution

Dependencies were installed manually in the active Conda environment, and
this document was created to record known issues and fixes.

---

## Summary

| Issue                         | Status                                      |
| ----------------------------- | ------------------------------------------- |
| Unsupported paradigm type     | Fixed by switching to `singletasklearning`  |
| Qwen GGUF unavailable         | Resolved by using an alternative GGUF model |
| Missing requirements & README | Documented manually                         |



## 🎥 Screencast: single_task_bench_with_compression

RUnning of benchmarkingJob.yml is shown below

https://github.com/user-attachments/assets/single_task_bench.md.webm

**Alternative display options:**

### Option 1: Using relative path (if video is in the repo)
![Screencast Demo](assets/single_task_bench.webm)

### Option 2: Using GitHub's raw content URL
https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/assets/single_task_bench.md.webm

### Option 3: Link to download
▶️ [Download screencast](assets/single_task_bench.md.webm)
