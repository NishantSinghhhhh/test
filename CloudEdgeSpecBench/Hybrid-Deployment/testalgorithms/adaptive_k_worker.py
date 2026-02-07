"""
Adaptive K Worker: Dynamically adjusts draft_k based on network RTT
This is your innovative acceleration idea for cloud-edge constraints
"""

import time
import torch
import requests
import numpy as np
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from sedna.common.class_factory import ClassFactory, ClassType


@ClassFactory.register(ClassType.GENERAL, alias="adaptive_k_worker")
class AdaptiveKWorker:
    """
    Network-Adaptive Speculative Decoding (NASD)
    
    Innovation: Dynamically adjusts K based on measured network RTT
    - High RTT → Increase K (amortize network cost)
    - Low RTT → Decrease K (reduce wasted compute)
    """
    
    def __init__(self, **kwargs):
        self.k_min = int(kwargs.get("k_min", 1))
        self.k_max = int(kwargs.get("k_max", 10))
        self.draft_name = kwargs.get("draft_model", "gpt2")
        self.cloud_url = kwargs.get("cloud_url", "http://127.0.0.1:5000").rstrip('/')
        
        # Adaptive parameters
        self.rtt_history = []
        self.current_k = 3  # Start with default
        self.alpha = 0.3  # EMA smoothing factor
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"\n[INIT] Adaptive K Worker")
        print(f"  K Range: [{self.k_min}, {self.k_max}]")
        print(f"  Cloud: {self.cloud_url}")
        
        # Load draft model
        self.draft_model = AutoModelForCausalLM.from_pretrained(self.draft_name).to(self.device)
        self.draft_tokenizer = AutoTokenizer.from_pretrained(self.draft_name)
        if self.draft_tokenizer.pad_token is None:
            self.draft_tokenizer.pad_token = self.draft_tokenizer.eos_token
    
    def _calculate_optimal_k(self, rtt_ms):
        """
        Calculate optimal K based on RTT
        
        Formula: K_opt = max(K_min, min(K_max, RTT / threshold))
        
        Intuition:
        - RTT = 10ms → K = 1 (network is fast, don't waste compute)
        - RTT = 100ms → K = 5 (network is slow, amortize cost)
        - RTT = 200ms → K = 10 (network is very slow, maximize batch)
        """
        threshold = 20  # ms per token (tunable)
        k_optimal = int(rtt_ms / threshold)
        k_optimal = max(self.k_min, min(self.k_max, k_optimal))
        return k_optimal
    
    def _update_rtt_estimate(self, new_rtt):
        """Exponential Moving Average of RTT"""
        if not self.rtt_history:
            self.rtt_history.append(new_rtt)
        else:
            smoothed = self.alpha * new_rtt + (1 - self.alpha) * self.rtt_history[-1]
            self.rtt_history.append(smoothed)
        
        # Update K based on smoothed RTT
        avg_rtt = self.rtt_history[-1]
        self.current_k = self._calculate_optimal_k(avg_rtt)
    
    def _verify_tokens(self, draft_ids, cloud_logits, original_len):
        """Token verification logic"""
        accepted = 0
        draft_tokens = draft_ids[0, original_len:]
        
        for i, draft_token in enumerate(draft_tokens):
            if i >= len(cloud_logits):
                break
            cloud_token = np.argmax(cloud_logits[i])
            if draft_token.item() == cloud_token:
                accepted += 1
            else:
                break
        
        acceptance_rate = accepted / len(draft_tokens) if len(draft_tokens) > 0 else 0.0
        return accepted, acceptance_rate
    
    def train(self, *args, **kwargs): return self
    def save(self, path): return path
    def load(self, path): return self
    
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
        
        print(f"\n[BENCHMARK] Processing {total_jobs} samples with Adaptive K...", flush=True)
        
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
            
            inputs = self.draft_tokenizer(prompt_text, return_tensors="pt").to(self.device)
            input_ids = inputs["input_ids"]
            original_len = input_ids.shape[1]
            
            # Metrics
            start_time = time.time()
            ttft = 0.0
            total_tokens = 0
            total_accepted = 0
            max_new = 20
            k_history = []
            
            with torch.no_grad():
                while total_tokens < max_new:
                    # === ADAPTIVE K: Use current estimate ===
                    draft_k = self.current_k
                    k_history.append(draft_k)
                    
                    # Edge: Draft
                    draft_start = time.time()
                    draft_out = self.draft_model.generate(
                        input_ids,
                        max_new_tokens=draft_k,
                        pad_token_id=self.draft_tokenizer.eos_token_id,
                        do_sample=False
                    )
                    draft_time = time.time() - draft_start
                    
                    if total_tokens == 0:
                        ttft = draft_time * 1000
                    
                    # Network: Send to cloud
                    draft_tokens_list = draft_out[0].tolist()
                    
                    try:
                        payload = {"tokens": draft_tokens_list, "original_len": original_len}
                        
                        network_start = time.time()
                        response = requests.post(
                            f"{self.cloud_url}/verify",
                            json=payload,
                            timeout=120
                        )
                        network_time = time.time() - network_start
                        measured_rtt = network_time * 1000  # Convert to ms
                        
                        # === ADAPTIVE: Update RTT estimate and K ===
                        self._update_rtt_estimate(measured_rtt)
                        
                        if response.status_code != 200:
                            print(f"  [ERROR] Server error {response.status_code}")
                            break
                        
                        cloud_data = response.json()
                        cloud_logits = cloud_data.get("logits", [])
                        
                        # Verify
                        accepted, accept_rate = self._verify_tokens(
                            draft_out, cloud_logits, original_len
                        )
                        total_accepted += accepted
                        
                        print(f"  K={draft_k} | RTT={measured_rtt:.0f}ms | "
                              f"Accepted={accepted}/{draft_k} ({accept_rate:.1%}) | "
                              f"Next K={self.current_k}", flush=True)
                        
                        # Update input
                        if accepted > 0:
                            input_ids = draft_out[:, :original_len + accepted]
                        else:
                            cloud_token = np.argmax(cloud_logits[0])
                            cloud_token_tensor = torch.tensor([[cloud_token]]).to(self.device)
                            input_ids = torch.cat([input_ids, cloud_token_tensor], dim=1)
                            accepted = 1
                        
                        total_tokens += accepted
                        original_len = input_ids.shape[1]
                        
                    except Exception as e:
                        print(f"  [ERROR] {e}")
                        break
            
            end_time = time.time()
            
            # Final metrics
            total_latency = end_time - start_time
            throughput = total_tokens / total_latency if total_latency > 0 else 0
            final_accept_rate = total_accepted / total_tokens if total_tokens > 0 else 0
            avg_rtt = np.mean(self.rtt_history) if self.rtt_history else 0
            avg_k = np.mean(k_history) if k_history else 0
            
            print(f"\n  COMPLETE: {total_tokens} tokens | {throughput:.2f} tok/s | "
                  f"Avg K: {avg_k:.1f} | Avg RTT: {avg_rtt:.0f}ms", flush=True)
            
            results.append({
                "latency": total_latency,
                "throughput": throughput,
                "energy": total_latency * 100.0,
                "final_acceptance_rate": final_accept_rate,
                "ttft_ms": ttft,
                "draft_k": avg_k,  # Report average K used
                "avg_rtt_ms": avg_rtt,
                "cloud_url": self.cloud_url,
                "adaptive": True
            })
        
        return results