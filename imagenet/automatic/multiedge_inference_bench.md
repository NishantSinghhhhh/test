Here is a complete `README.md` summarizing everything we did. You can save this file in your project folder (e.g., as `AUTOMATIC_BENCHMARK_GUIDE.md`) so you or anyone else can reproduce this setup without facing the same "dependency hell."

---

# Ianvs Automatic Benchmarking Guide

This guide covers how to set up and run the Ianvs "Automatic" Benchmarking job for the Vision Transformer (ViT) on a single-GPU machine (e.g., RTX 3050). It documents the necessary patches, environment setup, and troubleshooting steps for common errors.

## Part 1: How to Run (Step-by-Step)

### 1. Environment Setup (The "Clean" Install)

To avoid CUDA version mismatches, install the specific "vintage" libraries required by `onnxruntime-gpu` (v1.16).

```bash
# 1. Activate your environment
conda activate ianvs-experiment

# 2. Install generic dependencies
pip install psutil

# 3. Install the GPU "Fuel" (Force compatible versions)
conda install -y -c conda-forge cudatoolkit=11.8 cudnn=8.9.2

# 4. Link the libraries so Linux can find them
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_PREFIX/lib

```

### 2. Prepare the Model

Download the correct **ImageNet-1k** pre-trained weights. (Do NOT use the ImageNet-21k version).

```bash
cd initial_model
# Delete old files if present
rm ViT-B_16-224.npz
# Download the correct 1k-class version
wget https://storage.googleapis.com/vit_models/imagenet21k%2Bimagenet2012/ViT-B_16-224.npz
cd ..

```

### 3. Prepare the Dataset

You need the validation set. If you already have extracted images, patch the code (Step 4b). If you want to follow the strict standard, download the tarball:

```bash
cd dataset
wget https://huggingface.co/datasets/nqbinh/imagenet_test/resolve/main/ILSVRC2012_img_val.tar
cd ..

```

### 4. Apply Code Patches

You must modify three files to make the benchmark work on a single GPU.

**A. Fix Device Mapping (`devices.yaml`)**

* **File:** `examples/imagenet/multiedge_inference_bench/testalgorithms/automatic/devices.yaml`
* **Change:** Ensure all listed devices point to `gpu-0`.
```yaml
devices:
  - name: "gpu-0" # Changed from gpu-0
    type: "gpu"
    memory: "1024"
    freq: "2.6"
    bandwith: "100"
  - name: "gpu-0" # Changed from gpu-1
    type: "gpu"
    memory: "1024"
    freq: "2.6"
    bandwith: "80"
  - name: "gpu-0" # Changed from gpu-2
    type: "gpu"
    memory: "1024"
    freq: "2.6"
    bandwith: "90"

```



**B. Patch Dataset Loader (`dataset.py`)**

* **File:** `examples/imagenet/multiedge_inference_bench/testalgorithms/automatic/dataset.py`
* **Action:** Replace `torchvision.datasets.ImageNet` with `torchvision.datasets.ImageFolder` to allow using extracted folders instead of requiring the `.tar` file. (Refer to conversation history for the full code block).

**C. Create Profiler Results (`profiler_results.yml`)**

* **File:** `examples/imagenet/multiedge_inference_bench/testalgorithms/automatic/profiler_results.yml`
* **Action:** Create this file manually with the layer-wise memory usage data (12 blocks + embeddings) to skip the profiling step.

### 5. Run the Benchmark

Once everything is set up, run the job:

```bash
ianvs -f ./examples/imagenet/multiedge_inference_bench/classification_job_automatic.yaml

```

---

## Part 2: Troubleshooting (Errors & Fixes)

These are the errors encountered during setup and how they were resolved.

### Error 1: Tensor Size Mismatch

**Error:**
`RuntimeError: The size of tensor a (1000) must match the size of tensor b (21843)`
**Cause:**
Downloaded the `ImageNet-21k` model weights (21,843 classes) instead of the `ImageNet-1k` fine-tuned weights.
**Fix:**
Deleted the old `.npz` file and downloaded the correct version from the `imagenet21k+imagenet2012` folder.

### Error 2: Missing CUDA Library

**Error:**
`Failed to load library libonnxruntime_providers_cuda.so with error: libcublasLt.so.11: cannot open shared object file`
**Cause:**
The system had newer CUDA 12/13 drivers, but `onnxruntime` required CUDA 11 libraries.
**Fix:**
Forced installation of the older toolkit:

```bash
conda install -c conda-forge cudatoolkit=11.8
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_PREFIX/lib

```

### Error 3: Missing cuDNN Library

**Error:**
`Failed to load library ... libcudnn.so.8: cannot open shared object file`
**Cause:**
The environment had cuDNN v9 installed, but `onnxruntime` strictly required v8.
**Fix:**
Downgraded cuDNN:

```bash
conda install -c conda-forge cudnn=8.9.2

```

### Error 4: Invalid Argument (GPU Crash)

**Error:**
`pynvml.NVMLError_InvalidArgument: Invalid Argument`
**Cause:**
The benchmark tried to query "GPU 1" and "GPU 2" based on `devices.yaml`, but the machine only has one GPU (Index 0).
**Fix:**
Edited `devices.yaml` to point all virtual devices to `gpu-0`.

### Error 5: Missing Tar File

**Error:**
`RuntimeError: The archive ILSVRC2012_img_val.tar is not present`
**Cause:**
The standard `torchvision` ImageNet loader requires the original compressed file to verify integrity.
**Fix:**
**Option A:** Download the `.tar` file again.
**Option B (Preferred):** Patch `dataset.py` to use `ImageFolder`, allowing it to read the already extracted images.

### Error 6: Dependency Conflict (Dependency Hell)

**Error:**
`Found conflicts! Looking for incompatible packages...`
**Cause:**
Trying to mix packages from the `nvidia` channel (CUDA 13) with packages from `conda-forge` (CUDA 11).
**Fix:**
Performed a clean sweep and reinstall:

```bash
conda remove --force cuda-toolkit libcublas cudnn
conda install -c conda-forge cudatoolkit=11.8 cudnn=8.9.2

```


## 🎥 Screencast: Image_net_Multi Automatic 

<video controls width="100%">
  <source src="assets/imagenet_multi_automatic.webm" type="video/webm">
  Your browser does not support the video tag.
</video>

▶️ [Download screencast](assets/imagenet_multi_automatic.webm)
