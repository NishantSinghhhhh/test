## Issue Report: Cityscapes Single Task Learning Example - Complete Structural Failure

### 1. Background (40 points)

#### 1.1 Selected Example
**Example:** Cityscapes Single Task Learning Benchmark - Semantic Segmentation  
**Location:** `/examples/cityscapes/singletask_learning_bench/semantic-segmentation/`  
**Algorithm:** RFNet (ResNet Feature Fusion Network)

#### 1.2 Problem Description
The example is **completely non-functional** due to missing 80%+ of implementation files. Running `ianvs -f ./benchmarkingjob.yaml` immediately fails with:

```
RuntimeError: load module failed, error: No module named 'basemodel'
```

**Critical Discovery:** Unlike the working `cityscapes-synthia/lifelong_learning_bench` example, this directory is an **empty skeleton**:
-  Missing entire RFNet module (train.py, eval.py, models/, dataloaders/, utils/)
-  Missing task_definition_by_origin.py and task_allocation_by_origin.py
-  No dataset download instructions
-  Empty train_data.txt and test_data.txt
-  Missing __init__.py package files

**Structure Comparison:**
```bash
# Working (cityscapes-synthia):
rfnet/
├── basemodel.py 
├── task_definition_by_origin.py 
├── task_allocation_by_origin.py 
└── RFNet/ 
    ├── train.py, eval.py, mypath.py
    ├── dataloaders/, models/, utils/

# Broken (singletask_learning_bench):
rfnet/
├── basemodel.py 
├── __init__.py (empty)
└── models/ (empty)
#  Everything else missing
```

#### 1.3 Error Cascade
1. Module Import Error → wrong paths in config
2. Missing RFNet.train → entire module absent
3. Missing __init__.py → package structure incomplete
4. Empty dataset files → no data to train on
5. CUDA errors → no CPU fallback
6. Sedna permission errors → hardcoded paths

#### 1.4 Impact
**Severity: Critical** - Example is completely unusable

- Blocks new users from learning semantic segmentation
- Prevents researchers from benchmarking algorithms
- Breaks ~30% of semantic segmentation examples
- Damages project credibility

---

### 2. Goals (15 points)

#### 2.1 Primary Goal
Restore the incomplete example to full working state by copying missing modules, fixing configurations, and adding documentation.

#### 2.2 Contributions
1. **Complete Missing Structure:** Copy entire RFNet module + task files from working example
2. **Dataset Setup:** Create download scripts with working URLs and index file generators
3. **Configuration Fixes:** Update all paths to correct directory structure
4. **CPU Compatibility:** Patch train.py and eval.py for CPU-only systems
5. **Validation Tools:** Pre-flight check script to catch setup issues
6. **Documentation:** Complete README, troubleshooting guide, dataset instructions

---

### 3. Scope (15 points)

#### 3.1 Expected Users
- AI/ML researchers benchmarking semantic segmentation
- Contributors developing edge AI algorithms
- Students learning distributed edge AI

#### 3.2 In-Scope
 Copy complete RFNet module (50+ files)  
 Create dataset download/preparation scripts  
 Fix configuration paths  
 Add CPU compatibility patches  
 Create validation script  
 Write comprehensive documentation  

#### 3.3 Out-of-Scope
 Core Ianvs framework changes  
 GPU/CUDA installation  
 Modifying RFNet algorithm  

#### 3.4 Uniqueness
**This is a RESTORATION project, not bug fixing:**

| Aspect | This Issue | Others |
|--------|-----------|--------|
| Root Cause | 80%+ files missing | Individual bugs |
| Solution | Copy complete modules | Fix existing code |
| Nature | Incomplete skeleton | Working but broken |

This uniquely addresses structural incompleteness requiring wholesale module restoration.

---

### 4. Detailed Design

#### 4.1 Architecture (10 points)

**No Core Modifications Required** - All fixes are example-level:

```
examples/cityscapes/singletask_learning_bench/semantic-segmentation/
├── benchmarkingjob.yaml              # FIX: paths
├── dataset/
│   ├── prepare_dataset.sh            # ADD: download script
│   ├── train_data.txt                # ADD: index file
│   └── test_data.txt                 # ADD: index file
├── testenv/
│   ├── testenv.yaml                  # FIX: paths
│   └── map.py                        # FIX: imports
└── testalgorithms/rfnet/
    ├── rfnet_algorithm.yaml          # FIX: paths (critical)
    ├── basemodel.py                  # FIX: sys.path
    ├── task_definition_by_origin.py  # COPY
    ├── task_allocation_by_origin.py  # COPY
    └── RFNet/                        # COPY ENTIRE MODULE
        ├── train.py, eval.py         # COPY + CPU patch
        ├── dataloaders/, models/, utils/
        └── __init__.py files         # ADD
```

**Justification:** Core framework works correctly; issue is missing implementation files.

---

#### 4.2 Module Details (10 points)

### Solution 1: Copy Complete RFNet Module

**Problem:** Entire implementation missing

**Action:**
```bash
cp -r examples/cityscapes-synthia/.../rfnet/RFNet \
      examples/cityscapes/singletask_learning_bench/.../rfnet/

cp examples/cityscapes-synthia/.../task_*.py \
   examples/cityscapes/singletask_learning_bench/.../
```

**Creates:** 50+ files including train.py, eval.py, models/, dataloaders/, utils/

---

### Solution 2: Dataset Preparation Script

**Problem:** No instructions for obtaining Cityscapes dataset

**Create:** `dataset/prepare_dataset.sh`

```bash
#!/bin/bash
set -e
DOWNLOAD_URL="https://kubeedge.obs.cn-north-1.myhuaweicloud.com/sedna-robo/semantic_segmentation_dataset.zip"

wget $DOWNLOAD_URL -O dataset.zip
unzip dataset.zip -d cityscapes_data/

# Auto-generate index files
python3 << 'EOF'
import glob, os
train_imgs = glob.glob("cityscapes_data/train/leftImg8bit/**/*.png", recursive=True)
with open("train_data.txt", "w") as f:
    for img in train_imgs:
        depth = img.replace("leftImg8bit", "depth").replace("_leftImg8bit", "_disparity")
        label = img.replace("leftImg8bit", "gtFine").replace("_leftImg8bit", "_gtFine_labelTrainIds")
        f.write(f"./{img} ./{depth} ./{label}\n")
# Repeat for test set
EOF
```

**Index format:** `<image> <depth> <label>` (space-separated paths per line)

---

### Solution 3: Fix Configuration Paths

**File:** `rfnet_algorithm.yaml`

**Change:**
```yaml
# Before (broken):
url: "./examples/semantic_segmentation/lifelong_learning_bench/..."

# After (fixed):
url: "./examples/cityscapes/singletask_learning_bench/semantic-segmentation/..."
```

---

### Solution 4: Add Package Structure

**Create __init__.py files:**
```bash
touch testalgorithms/rfnet/__init__.py
touch testalgorithms/rfnet/RFNet/__init__.py
touch testalgorithms/rfnet/RFNet/models/__init__.py
touch testalgorithms/rfnet/RFNet/models/resnet/__init__.py
touch testalgorithms/rfnet/RFNet/dataloaders/__init__.py
touch testalgorithms/rfnet/RFNet/utils/__init__.py
```

---

### Solution 5: CPU Compatibility Patches

**Files:** `RFNet/eval.py` and `RFNet/train.py`

**Change:**
```python
# Before:
self.model = self.model.cuda()  # Fails without GPU

# After:
self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
self.model = self.model.to(self.device)
```

Apply to all `.cuda()` calls in both files.

---

### Solution 6: Validation Script

**Create:** `validate_setup.py`

```python
#!/usr/bin/env python3
import os, sys

checks = {
    "RFNet module": os.path.exists("testalgorithms/rfnet/RFNet/train.py"),
    "Task files": os.path.exists("testalgorithms/rfnet/task_definition_by_origin.py"),
    "Package structure": os.path.exists("testalgorithms/rfnet/RFNet/__init__.py"),
    "Dataset": os.path.exists("dataset/train_data.txt") and os.path.getsize("dataset/train_data.txt") > 0,
}

for name, passed in checks.items():
    print(f"{'' if passed else '❌'} {name}")

sys.exit(0 if all(checks.values()) else 1)
```

---

### Solution 7: One-Command Setup

**Create:** `setup_example.sh`

```bash
#!/bin/bash
set -e
echo "Setting up Cityscapes Single Task Learning..."

# 1. Copy RFNet module
cp -r ../cityscapes-synthia/.../RFNet testalgorithms/rfnet/

# 2. Copy task files
cp ../cityscapes-synthia/.../task_*.py testalgorithms/rfnet/

# 3. Create package structure
find testalgorithms/rfnet -type d -exec touch {}/__init__.py \;

# 4. Fix config paths
sed -i 's|lifelong_learning_bench|singletask_learning_bench/semantic-segmentation|g' \
    testalgorithms/rfnet/rfnet_algorithm.yaml

# 5. Download dataset
cd dataset && ./prepare_dataset.sh && cd ..

# 6. Validate
python validate_setup.py

echo " Setup complete! Run: ianvs -f benchmarkingjob.yaml"
```

---

### Testing Strategy

1. **Module Import:** `python -c "from testalgorithms.rfnet.basemodel import BaseModel"`
2. **Dataset Check:** `wc -l dataset/train_data.txt` (should show >0)
3. **CPU Test:** `CUDA_VISIBLE_DEVICES="" ianvs -f benchmarkingjob.yaml`
4. **Quick Test:** Use 5 train + 5 test samples for 1-epoch validation

---

### Documentation

**README.md** - Quick start guide:
```markdown
# Quick Start
./setup_example.sh  # One-command setup
ianvs -f benchmarkingjob.yaml

# Manual Setup
1. Copy RFNet: cp -r ../cityscapes-synthia/.../RFNet testalgorithms/rfnet/
2. Download data: cd dataset && ./prepare_dataset.sh
3. Validate: python validate_setup.py
```

**TROUBLESHOOTING.md** - Common errors and fixes

**DATASET.md** - Dataset structure and download options

---


## 🎥 Screencast: LLM_Agent_Benchmark_single_task_learning 

<video controls width="100%">
  <source src="https://drive.google.com/file/d/1CCQVMb0nT3K8OlMqdinCIUIl16h9i2Jw/view?usp=drive_link" type="video/webm">
  Your browser does not support the video tag.
</video>

▶️ [Download screencast](https://drive.google.com/file/d/1CCQVMb0nT3K8OlMqdinCIUIl16h9i2Jw/view?usp=drive_link)
