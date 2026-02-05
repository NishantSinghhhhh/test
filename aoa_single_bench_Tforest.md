# Fix Critical Execution Failures and Missing Configuration in AoA TForest Example

## Background

I have analyzed the example located at `examples/aoa/single_task_bench/TForest` and identified multiple critical issues that prevent it from running out-of-the-box. This example, which benchmarks the TForest algorithm for Vehicle Angle of Arrival (AoA) prediction, deviates significantly from the standard Ianvs benchmarking structure.

**Problem Description:**

1. **Missing Ianvs Configuration:** The directory lacks the standard `benchmarkingjob.yaml` or `algorithm.yaml` configuration files required to run the benchmark via the `ianvs` CLI.
2. **Broken Execution Logic:** The `task_main.py` script is hardcoded to run in "Test Mode" (`test_main()`) by default. However, it fails immediately because the required pre-trained model files (`single_tree.joblib`, `models/*.joblib`) are missing from the repository. The user must manually edit the code to enable training, which is not documented.
3. **Dependency Failures:** There is no `requirements.txt`. Execution fails repeatedly with `ModuleNotFoundError` for libraries such as `statsmodels`, `scienceplots`, and `latex` dependencies.
4. **Path Errors:** The `tools.py` script attempts to load data from `data/processed/`, but this path does not exist, and the script does not handle the missing data gracefully.

**Debug Log Evidence:**
Running the example results in immediate crashes:

```text
(ianvs-experiment) $ ianvs -f testenv.yaml
Error: not found benchmarking config(testenv.yaml) file in local

(ianvs-experiment) $ python task_main.py
Traceback (most recent call last):
  File "task_main.py", line 7, in <module>
    import statsmodels.api as sm
ModuleNotFoundError: No module named 'statsmodels'
...
FileNotFoundError: [Errno 2] No such file or directory: 'single_tree.joblib'

```

## Goals

The goal of this contribution is to refactor the `AoA/TForest` example to make it runnable and compliant with Ianvs standards.

* **Create Missing Documentation:** Update `README.md` with step-by-step execution instructions.
* **Standardize Dependencies:** Add a `requirements.txt` file.
* **Fix Code Logic:** Modify `task_main.py` to check for existing models and train automatically if they are missing, preventing the `FileNotFoundError`.
* **Ianvs Integration:** (Optional/Stretch) Draft a `testenv.yaml` to allow this example to be run via the standard `ianvs` command.

## Scope

This proposal focuses strictly on the **User Experience and Stability** of the `examples/aoa` directory.

* **Target User:** Developers and researchers trying to replicate the TForest benchmark.
* **Uniqueness:** Unlike other issues that might focus on core Ianvs bugs, this issue addresses a specific "orphan" example that currently serves as a dead end for new users. Fixing this ensures the repository's examples are actually usable educational resources.

## Detailed Design

### 1. Architecture

This fix locates entirely within the **Examples Module** (`examples/aoa/single_task_bench/TForest`). It does not require modifying the core logic of the KubeEdge Ianvs engine, ensuring zero risk of regression for other benchmarks.

### 2. Module Details

I propose the following specific changes:

**A. Add `requirements.txt**`
Create a dependency file to ensure environment reproducibility:

```text
numpy
pandas
scikit-learn
statsmodels
scienceplots
joblib
matplotlib

```

**B. Refactor `task_main.py**`
Implement a check logic in the `if __name__ == '__main__':` block:

```python
if __name__ == '__main__':
    # Check if model exists, if not, run training first
    if not os.path.exists('single_tree.joblib'):
        print("Pre-trained model not found. Starting training...")
        tforest_main()
        save_model()
        gen_error_list()
        task_selector()
    
    # Run testing
    test_main()

```

**C. Update `README.md**`
Rewrite the README to include the missing "How to Run" section:

```markdown
## Quick Start

1. Install dependencies:
   `pip install -r requirements.txt`

2. Generate Dummy Data (if using without private dataset):
   `python gen_dummy_data.py`

3. Run the Benchmark:
   `python task_main.py`

```

**D. Handle Missing Data**
Since the dataset is private, I will add a simple script `gen_dummy_data.py` (or instructions) that generates random data in the expected shape. This allows users to verify the code logic works even without the proprietary dataset.

## 🎥 Screencast: AoA TForest Example

<video controls width="100%">
  <source src="https://drive.google.com/uc?export=download&id=12-mJwvGzN5BDfu_2xFsE3czi4I5z7ClR" type="video/webm">
  Your browser does not support the video tag.
</video>

▶️ [Download screencast](https://drive.google.com/uc?export=download&id=12-mJwvGzN5BDfu_2xFsE3czi4I5z7ClR)


