"""
Adaptive K Scheduler for Single-Node Emulation
Network-Adaptive Speculative Decoding (NASD)

Dynamically adjusts draft_k based on measured network RTT.
Key Innovation: K adapts to network conditions in real-time.
"""

import time
import torch
import numpy as np
import os
import sys
from transformers import AutoModelForCausalLM, AutoTokenizer
from sedna.common.class_factory import ClassFactory, ClassType

# Import network simulator
sys.path.append(os.path.join(os.path.dirname(__file__), "../../testenv/cloud_edge_net"))
from latency_injector import NetworkSimulator


@ClassFactory.register(ClassType.GENERAL, alias="adaptive_k_scheduler")
class AdaptiveKScheduler:
    """
    Network-Adaptive Speculative Decoding (NASD) for Single-Node.
    
    Key Innovation: Adjusts K based on measured network RTT
    - High RTT → Larger K (amortize network cost)
    - Low RTT → Smaller K (avoid wasted compute)
    """
    
    def __init__(self, **kwargs):
        """
        Initialize adaptive scheduler.
        
        Args:
            **kwargs: Configuration parameters
        """
        # Model config
        self.draft_name = kwargs.get("draft_model", "gpt2")
        self.target_name = kwargs.get("target_model", "gpt2-medium")
        
        # Adaptive K range
        self.k_min = int(kwargs.get("k_min", 1))
        self.k_max = int(kwargs.get("k_max", 10))
        self.current_k = 3  # Start with default
        
        # Network simulation parameters
        self.rtt_ms = float(kwargs.get("rtt_ms", 50))
        self.bandwidth_mbps = float(kwargs.get("bandwidth_mbps", 100))
        self.jitter_ms = float(kwargs.get("jitter_ms", 0))
        self.concurrency = int(kwargs.get("concurrency", 1))
        
        # Adaptive parameters
        self.rtt_history = []
        self.alpha = 0.3  # EMA smoothing factor
        
        # Reproducibility
        self.seed = int(kwargs.get("random_seed", 42))
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)
        
        # Initialize network simulator
        self.network = NetworkSimulator(
            rtt_ms=self.rtt_ms,
            bandwidth_mbps=self.bandwidth_mbps,
            jitter_ms=self.jitter_ms,
            max_concurrent=self.concurrency,
            seed=self.seed
        )
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"\n[INIT] AdaptiveKScheduler (NASD)", flush=True)
        print(f"  Device: {self.device}", flush=True)
        print(f"  K Range: [{self.k_min}, {self.k_max}]", flush=True)
        print(f"  Base Network: RTT={self.rtt_ms}ms, BW={self.bandwidth_mbps}Mbps", flush=True)
        
        # Load models
        print(f"[LOADING] Loading models...", flush=True)
        self.draft_model = AutoModelForCausalLM.from_pretrained(self.draft_name).to(self.device)
        self.draft_tokenizer = AutoTokenizer.from_pretrained(self.draft_name)
        
        self.target_model = AutoModelForCausalLM.from_pretrained(self.target_name).to(self.device)
        self.target_tokenizer = AutoTokenizer.from_pretrained(self.target_name)
        
        if self.draft_tokenizer.pad_token is None:
            self.draft_tokenizer.pad_token = self.draft_tokenizer.eos_token
        if self.target_tokenizer.pad_token is None:
            self.target_tokenizer.pad_token = self.target_tokenizer.eos_token
        
        print(f"[READY] Models loaded successfully", flush=True)

    def _calculate_optimal_k(self, rtt_ms):
        """
        Calculate optimal K based on RTT.
        
        Formula: K = RTT / threshold
        Threshold = 20ms per token (tunable)
        
        Args:
            rtt_ms (float): Measured RTT in milliseconds
            
        Returns:
            int: Optimal K (clipped to [k_min, k_max])
        """
        threshold = 20  # ms per token (tunable parameter)
        k_optimal = int(rtt_ms / threshold)
        k_optimal = max(self.k_min, min(self.k_max, k_optimal))
        return k_optimal
    
    def _update_rtt_estimate(self, new_rtt):
        """
        Update RTT estimate using Exponential Moving Average.
        
        Args:
            new_rtt (float): Newly measured RTT in milliseconds
        """
        if not self.rtt_history:
            self.rtt_history.append(new_rtt)
        else:
            # EMA: smoothed = α * new + (1-α) * prev
            smoothed = self.alpha * new_rtt + (1 - self.alpha) * self.rtt_history[-1]
            self.rtt_history.append(smoothed)
        
        # Update current K based on smoothed RTT
        avg_rtt = self.rtt_history[-1]
        self.current_k = self._calculate_optimal_k(avg_rtt)

    def _calculate_payload_size(self, token_ids):
        """Estimate payload size for bandwidth simulation."""
        num_tokens = token_ids.shape[1]
        return num_tokens * 4 + num_tokens * 8192

    def _verify_tokens(self, draft_ids, original_input_len):
        """
        Verify draft tokens using target model.
        
        Args:
            draft_ids: Draft sequence
            original_input_len: Original input length
            
        Returns:
            tuple: (accepted_count, acceptance_rate, verified_ids)
        """
        with torch.no_grad():
            target_out = self.target_model(draft_ids)
            target_logits = target_out.logits
            
            draft_tokens = draft_ids[0, original_input_len:]
            
            accepted = 0
            for i, draft_token in enumerate(draft_tokens):
                if i >= target_logits.shape[1] - original_input_len:
                    break
                
                target_probs = torch.softmax(target_logits[0, original_input_len + i, :], dim=-1)
                target_token = torch.argmax(target_probs).item()
                
                if draft_token.item() == target_token:
                    accepted += 1
                else:
                    break
            
            acceptance_rate = accepted / len(draft_tokens) if len(draft_tokens) > 0 else 0.0
            
            if accepted > 0:
                verified_ids = draft_ids[:, :original_input_len + accepted]
            else:
                first_target_token = torch.argmax(target_logits[0, original_input_len - 1, :]).unsqueeze(0).unsqueeze(0)
                verified_ids = torch.cat([draft_ids[:, :original_input_len], first_target_token], dim=1)
                accepted = 1
            
            return accepted, acceptance_rate, verified_ids

    def train(self, *args, **kwargs): 
        return self
    
    def save(self, path): 
        return path
    
    def load(self, path): 
        return self

    def predict(self, data, **kwargs):
        """
        Run adaptive speculative decoding benchmark.
        
        Args:
            data: Input data
            
        Returns:
            list: Results with adaptive metrics
        """
        results = []
        clean_file_paths = []
        
        if not isinstance(data, list) and not isinstance(data, np.ndarray):
            data = [data]
        
        for item in data:
            if isinstance(item, np.ndarray):
                item = item.tolist()
            path = item[0] if isinstance(item, list) else item
            clean_file_paths.append(str(path))

        print(f"\n[BENCHMARK] Processing {len(clean_file_paths)} samples (Adaptive K)...", flush=True)

        for idx, file_path in enumerate(clean_file_paths):
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

            start_time = time.time()
            ttft = 0.0
            total_tokens_generated = 0
            total_tokens_accepted = 0
            acceptance_rates = []
            k_history = []
            max_new_tokens = 20
            
            with torch.no_grad():
                while total_tokens_generated < max_new_tokens:
                    # Use current adaptive K
                    draft_k = self.current_k
                    k_history.append(draft_k)
                    
                    # Edge: Draft
                    draft_start = time.time()
                    draft_out = self.draft_model.generate(
                        input_ids,
                        max_new_tokens=draft_k,
                        pad_token_id=self.draft_tokenizer.eos_token_id,
                        do_sample=False,
                        use_cache=True
                    )
                    draft_time = time.time() - draft_start
                    
                    if total_tokens_generated == 0:
                        ttft = draft_time * 1000

                    # Network: Simulate delay and measure RTT
                    network_start = time.time()
                    payload_size = self._calculate_payload_size(draft_out)
                    network_delay = self.network.inject_delay(payload_size)
                    measured_rtt = (time.time() - network_start) * 1000

                    # Update adaptive K based on measured RTT
                    self._update_rtt_estimate(measured_rtt)

                    # Cloud: Verify
                    accepted, accept_rate, verified_ids = self._verify_tokens(
                        draft_out, 
                        original_len + total_tokens_generated
                    )
                    
                    total_tokens_accepted += accepted
                    acceptance_rates.append(accept_rate)
                    
                    input_ids = verified_ids
                    total_tokens_generated += accepted
                    
                    if self.draft_tokenizer.eos_token_id in verified_ids[0]:
                        break

            end_time = time.time()
            
            total_latency = end_time - start_time
            throughput = total_tokens_generated / total_latency if total_latency > 0 else 0
            final_accept_rate = total_tokens_accepted / (len(acceptance_rates) * np.mean(k_history)) if acceptance_rates else 0
            avg_rtt = np.mean(self.rtt_history) if self.rtt_history else self.rtt_ms
            avg_k = np.mean(k_history) if k_history else self.current_k
            
            power_watts = 250.0 if self.device == "cuda" else 100.0
            energy_joules = total_latency * power_watts
            
            result = {
                "latency": total_latency,
                "throughput": throughput,
                "energy": energy_joules,
                "final_acceptance_rate": final_accept_rate,
                "ttft_ms": ttft,
                "draft_k": avg_k,  # Report average K used
                "compute_ratio": 1.0,
                "dataset_task": 1,
                "rtt_ms": self.rtt_ms,
                "bandwidth_mbps": self.bandwidth_mbps,
                "jitter_ms": self.jitter_ms,
                "avg_rtt_measured": avg_rtt  # NEW: Measured RTT
            }
            
            results.append(result)
            
            if (idx + 1) % 5 == 0 or idx == len(clean_file_paths) - 1:
                print(f"[{idx+1}/{len(clean_file_paths)}] "
                      f"TTFT: {ttft:.0f}ms | "
                      f"Latency: {total_latency:.2f}s | "
                      f"Speed: {throughput:.2f} tok/s | "
                      f"Accept: {final_accept_rate:.2%} | "
                      f"Avg K: {avg_k:.1f}", flush=True)
        
        print(f"[COMPLETE] Processed all {len(clean_file_paths)} samples\n", flush=True)
        return results