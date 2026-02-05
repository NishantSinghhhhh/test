# Complete Summary: ImageNet Multi-Edge Inference Setup Journey

## Overview

We successfully configured and benchmarked the **Multi-Edge Inference** paradigm using a Vision Transformer (ViT) on the **ImageNet (ILSVRC2012)** validation dataset. This process involved resolving significant hurdles regarding large dataset management, configuration key mismatches in the Ianvs framework, missing runtime dependencies, and adapting hardcoded GPU logic for a CPU-only environment.

---

## Steps We Followed

### 1. **Dataset Acquisition & Restructuring**
* **Initial State:** The environment lacked the heavy validation dataset (6.3GB), causing extraction scripts to fail.
* **Action:** We downloaded the `ILSVRC2012_img_val.tar` from a HuggingFace mirror, extracted it into the `val/` directory, and ran the `valprep.sh` script to organize images into class-specific subdirectories (e.g., `n01440764/`).

### 2. **Model Preparation**
* **Action:** We created the `initial_model/` directory and downloaded the pre-partitioned ONNX Vision Transformer model (`vit-base-patch16-224.onnx`).

### 3. **Configuration Alignment**
* **Action:** The provided `testenv.yaml` used outdated keys (`train_url`). We updated the YAML configuration to use the correct keys required by the installed Ianvs version (`train_index`, `test_index`) and provided absolute paths to the `.txt` index files.

### 4. **Environment & Code Patching**
* **Action:** We installed missing dependencies (`onnxruntime`) and modified the `basemodel.py` source code. The original code contained hardcoded GPU monitoring (via `pynvml`) which caused crashes on our CPU-only server. We disabled these checks to allow smooth execution.

---

## All Errors Encountered & Solutions

### **Error 1: Missing Source Dataset**

**Error Message:**
```text
tar: ../ILSVRC2012_img_val.tar: Cannot open: No such file or directory
mv: cannot stat 'ILSVRC2012_val_00043730.JPEG': No such file or directory

```

**Cause:** The extraction script was trying to move files that didn't exist because the main 6.3GB dataset tarball was missing from the server.
**Solution:**
Downloaded the dataset from a mirror and properly extracted it before running the organization script:

```bash
wget [https://huggingface.co/datasets/nqbinh/imagenet_test/resolve/main/ILSVRC2012_img_val.tar](https://huggingface.co/datasets/nqbinh/imagenet_test/resolve/main/ILSVRC2012_img_val.tar)
tar -xf ../ILSVRC2012_img_val.tar -C .

```

### **Error 2: Dataset Index Key Mismatch**

**Error Message:**

```text
NotImplementedError: not one of train_index/train_data/train_data_info

```

**Cause:** The `testenv.yaml` configuration file used the keys `train_url` and `test_url`, but the core Ianvs code expects `train_index` and `test_index`.
**Solution:**
Edited `examples/imagenet/multiedge_inference_bench/testenv/testenv.yaml` to match the required schema:

```yaml
dataset:
  train_index: "/absolute/path/to/dataset/train.txt"
  test_index: "/absolute/path/to/dataset/val.txt"

```

### **Error 3: Missing ONNX Runtime**

**Error Message:**

```text
ModuleNotFoundError: No module named 'onnxruntime'

```

**Cause:** The Python environment was missing the specific engine required to execute `.onnx` model files.
**Solution:**
Installed the CPU version of the runtime:

```bash
pip install onnxruntime==1.14.1

```

### **Error 4: GPU Driver Crash (pynvml)**

**Error Message:**

```text
pynvml.NVMLError_InvalidArgument: Invalid Argument
...
RuntimeError: (paradigm=multiedgeinference) pipeline runs failed

```

**Cause:** The benchmarking code (`basemodel.py`) attempted to initialize NVIDIA management drivers (`pynvml`) to read power and memory stats. Since the server is CPU-only, the driver initialization failed.
**Solution:**
We patched `basemodel.py` to comment out GPU-specific lines:

```python
# pynvml.nvmlInit()  <-- Commented out
# handle = pynvml.nvmlDeviceGetHandleByIndex(...) <-- Commented out

```

### **Error 5: TensorRT Warning (Non-Blocking)**

**Error Message:**

```text
TF-TRT Warning: Could not find TensorRT

```

**Cause:** TensorFlow attempted to look for TensorRT optimizations.
**Solution:**
Ignored. This is a warning, not a fatal error, and is expected in a CPU-only environment.

---

## Final Result

### **Success! Benchmark Completed**

The benchmarking job successfully processed the validation dataset on the CPU.

```text
Evaluating: 100%|██████████| 1000/1000 [05:42<00:00,  2.92batch/s]
Accuracy: 92.00%

+------+----------------+----------+-----------+----------+-----------+
| rank |   algorithm    | accuracy |    fps    | paradigm | basemodel |
+------+----------------+----------+-----------+----------+-----------+
|  1   | classification |   92.0   | 11.609    | multiedge| Class...  |
|  2   | classification |   92.0   |  8.269    | multiedge| Class...  |
+------+----------------+----------+-----------+----------+-----------+

```

## 🎥 Screencast: Image_net_Multi 

<video controls width="100%">
  <source src="https://drive.google.com/file/d/12F7gcS_udl83CXgCD1c69YEyfunOl4rK/view?usp=drive_link" type="video/webm">
  Your browser does not support the video tag.
</video>

▶️ [Download screencast](https://drive.google.com/file/d/12F7gcS_udl83CXgCD1c69YEyfunOl4rK/view?usp=drive_link)
