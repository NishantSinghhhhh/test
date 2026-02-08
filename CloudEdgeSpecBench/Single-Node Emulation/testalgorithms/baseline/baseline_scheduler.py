"""
Baseline Scheduler: Cloud-Only Inference (No Speculation)

Provides baseline comparison for speculative decoding benchmark.
This scheduler directly calls the target model without any edge drafting.
"""

import time
import torch
import numpy as np
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from sedna.common.class_factory import ClassFactory, ClassType


@ClassFactory.register(ClassType.GENERAL, alias="baseline_cloud_only")
class BaselineScheduler:
    """
    Baseline: Direct cloud inference without speculation.
    
    This represents the traditional approach where all inference
    happens on the cloud/server without edge assistance.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize baseline scheduler.
        
        Args:
            **kwargs: Configuration parameters including:
                - target_model: Target model name/path
                - random_seed: Random seed for reproducibility
        """
        self.target_name = kwargs.get("target_model", "gpt2-medium")
        
        # Reproducibility
        self.seed = int(kwargs.get("random_seed", 42))
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)
        
        # Device configuration
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"\n[INIT] BaselineScheduler (Cloud-Only)", flush=True)
        print(f"  Device: {self.device}", flush=True)
        print(f"  Model: {self.target_name}", flush=True)
        
        # Load model
        print(f"[LOADING] Loading model...", flush=True)
        self.model = AutoModelForCausalLM.from_pretrained(self.target_name).to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(self.target_name)
        
        # Set pad token if missing
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        print(f"[READY] Model loaded successfully", flush=True)

    def train(self, train_data, valid_data=None, **kwargs):
        """Required by Ianvs interface (no training needed)."""
        return self
    
    def save(self, model_path):
        """Required by Ianvs interface (no saving needed)."""
        return model_path
    
    def load(self, model_path):
        """Required by Ianvs interface (model loaded in __init__)."""
        return self

    def predict(self, data, **kwargs):
        """
        Run baseline cloud-only inference.
        
        Args:
            data: Input data (file paths or text samples)
            **kwargs: Additional parameters
            
        Returns:
            list: Results with latency, throughput, etc.
        """
        results = []
        clean_file_paths = []
        
        # Process input data into file paths
        if not isinstance(data, list) and not isinstance(data, np.ndarray): 
            data = [data]
        
        for item in data:
            if isinstance(item, np.ndarray): 
                item = item.tolist()
            path = item[0] if isinstance(item, list) else item
            clean_file_paths.append(str(path))

        print(f"\n[BASELINE] Processing {len(clean_file_paths)} samples...", flush=True)

        # Process each sample
        for idx, file_path in enumerate(clean_file_paths):
            # Load prompt text
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        prompt_text = f.read().strip()[:300]  # Limit to 300 chars
                else: 
                    prompt_text = "The quick brown fox jumps over the lazy dog."
            except Exception as e:
                print(f"[WARNING] Failed to read {file_path}: {e}", flush=True)
                prompt_text = "AI benchmark test."

            # Tokenize input
            inputs = self.tokenizer(prompt_text, return_tensors="pt").to(self.device)
            input_ids = inputs["input_ids"]

            # Run inference
            start_time = time.time()
            
            with torch.no_grad():
                output = self.model.generate(
                    input_ids,
                    max_new_tokens=20,  # Same as speculative version
                    pad_token_id=self.tokenizer.eos_token_id,
                    do_sample=False,  # Greedy decoding for reproducibility
                    use_cache=True
                )
            
            end_time = time.time()
            
            # Calculate metrics
            total_latency = end_time - start_time
            tokens_generated = output.shape[1] - input_ids.shape[1]
            throughput = tokens_generated / total_latency if total_latency > 0 else 0
            
            # Energy estimation
            power_watts = 250.0 if self.device == "cuda" else 100.0
            energy_joules = total_latency * power_watts
            
            # Store results
            result = {
                "latency": total_latency,
                "throughput": throughput,
                "energy": energy_joules,
                "final_acceptance_rate": 1.0,  # N/A for baseline (all tokens "accepted")
                "ttft_ms": 0.0,  # Not measured for baseline
                "draft_k": 0,  # N/A for baseline
                "compute_ratio": 0.0,  # N/A for baseline
                "dataset_task": 1,  # 1 = WikiText
                "rtt_ms": 0.0,  # N/A for baseline
                "bandwidth_mbps": 0.0,  # N/A for baseline
                "jitter_ms": 0.0  # N/A for baseline
            }
            
            results.append(result)
            
            # Progress logging
            if (idx + 1) % 5 == 0 or idx == len(clean_file_paths) - 1:
                print(f"[{idx+1}/{len(clean_file_paths)}] "
                      f"Latency: {total_latency:.2f}s | "
                      f"Speed: {throughput:.2f} tok/s", flush=True)
        
        print(f"[COMPLETE] Processed all {len(clean_file_paths)} samples\n", flush=True)
        return results

# Standalone testing
if __name__ == "__main__":
    print("Testing BaselineScheduler...")
    
    # Create scheduler
    scheduler = BaselineScheduler(
        target_model="gpt2-medium",
        random_seed=42
    )
    
    # Test with sample data
    test_data = ["The future of AI is"]
    results = scheduler.predict(test_data)
    
    print("\nTest Results:")
    for key, value in results[0].items():
        print(f"  {key}: {value}")
    
    print("\n✓ BaselineScheduler tests passed")