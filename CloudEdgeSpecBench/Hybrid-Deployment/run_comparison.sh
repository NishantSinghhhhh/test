#!/bin/bash
# Run all three approaches using SAME testenv

echo "========================================="
echo "Cloud-Edge Benchmark Comparison"
echo "========================================="

# Step 2: Run all benchmarks
echo -e "\n[2/3] Running benchmarks..."

echo -e "\n>>> [1/3] Baseline (Cloud-Only)..."
ianvs -f benchmarkingjob_baseline.yaml

echo -e "\n>>> [2/3] Speculative (Fixed K)..."
ianvs -f benchmarkingjob_speculative.yaml

echo -e "\n>>> [3/3] Adaptive (NASD)..."
ianvs -f benchmarkingjob_adaptive.yaml


echo -e "\n✓ Complete! Check workspace_hybrid/comparison_report.csv"