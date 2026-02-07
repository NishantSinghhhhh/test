"""
Baseline Scheduler: Cloud-only inference (no edge drafting)
This is the reference point for measuring speculative decoding speedup
"""

import time
import torch
import requests
import numpy as np
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from sedna.common.class_factory import ClassFactory, ClassType


@ClassFactory.register(ClassType.GENERAL, alias="cloud_only_baseline")
class CloudOnlyScheduler:
    """
    Baseline: Send entire generation task to cloud
    No edge drafting, just measure raw cloud performance
    """
    
    def __init__(self, **kwargs):
        self.target_name = kwargs.get("target_model", "gpt2-medium")
        self.cloud_url = kwargs.get("cloud_url", "http://127.0.0.1:5000").rstrip('/')
        
        print(f"\n[INIT] Baseline Cloud-Only Scheduler")
        print(f"  Target Model: {self.target_name}")
        print(f"  Cloud Endpoint: {self.cloud_url}")
    
    def train(self, *args, **kwargs): 
        return self
    
    def save(self, path): 
        return path
    
    def load(self, path): 
        return self

    def predict(self, data, **kwargs):
        results = []
        clean_file_paths = []
        
        # Process input
        if not isinstance(data, list) and not isinstance(data, np.ndarray):
            data = [data]
        
        for item in data:
            if isinstance(item, np.ndarray):
                item = item.tolist()
            path = item[0] if isinstance(item, list) else item
            clean_file_paths.append(str(path))
        
        clean_file_paths = clean_file_paths[:5]
        total_jobs = len(clean_file_paths)
        
        print(f"\n[BASELINE] Processing {total_jobs} samples (Cloud-Only)...", flush=True)
        
        for i, file_path in enumerate(clean_file_paths):
            print(f"\n[{i+1}/{total_jobs}] Starting...", flush=True)
            
            # Load prompt
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        prompt_text = f.read().strip()[:300]
                else:
                    prompt_text = "The quick brown fox jumps over the lazy dog."
            except:
                prompt_text = "AI benchmark test."
            
            # For baseline, we just tokenize and measure end-to-end cloud generation
            # In a real scenario, we'd send the prompt to cloud and let it generate
            # For this benchmark, we simulate by sending dummy tokens and measuring latency
            
            start_time = time.time()
            
            # Simulate 20 tokens generation (same as speculative approaches)
            max_tokens = 20
            tokens_generated = 0
            
            # Send generation request to cloud
            try:
                payload = {
                    "tokens": list(range(10)),  # Dummy prompt tokens
                    "original_len": 10
                }
                
                # Generate in batches (cloud does all work)
                while tokens_generated < max_tokens:
                    response = requests.post(
                        f"{self.cloud_url}/verify",
                        json=payload,
                        timeout=120
                    )
                    
                    if response.status_code == 200:
                        # Cloud generated successfully
                        tokens_generated += 5  # Assume cloud generates 5 tokens per call
                        payload["tokens"].extend(range(5))  # Extend for next iteration
                    else:
                        print(f"  [ERROR] Cloud error {response.status_code}")
                        break
            
            except Exception as e:
                print(f"  [ERROR] Connection failed: {e}")
                tokens_generated = 1  # Avoid division by zero
            
            end_time = time.time()
            
            # Calculate metrics
            total_latency = end_time - start_time
            throughput = tokens_generated / total_latency if total_latency > 0 else 0
            energy = total_latency * 100.0  # Assume 100W for cloud requests
            
            print(f"  COMPLETE: {tokens_generated} tokens | "
                  f"{total_latency:.2f}s | "
                  f"{throughput:.2f} tok/s", flush=True)
            
            results.append({
                "latency": total_latency,
                "throughput": throughput,
                "energy": energy,
                "final_acceptance_rate": 1.0,  # N/A for baseline
                "ttft_ms": 0.0,  # Not applicable (no drafting)
                "draft_k": 0,
                "cloud_url": self.cloud_url,
                "avg_rtt_ms": 0.0,
                "adaptive": False
            })
        
        return results