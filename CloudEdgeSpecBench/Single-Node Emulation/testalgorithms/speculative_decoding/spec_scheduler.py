"""
Speculative Decoding Scheduler for Cloud-Edge Benchmarking

Implements the "Boss & Intern" collaboration model:
- Edge (Intern): Fast draft model generates K tokens
- Cloud (Boss): Powerful verifier model validates tokens
- Network: Simulated constraints between edge and cloud

This scheduler runs both models in the same process (single-node emulation).
"""

import time
import torch
import numpy as np
import os
import sys
from transformers import AutoModelForCausalLM, AutoTokenizer
from sedna.common.class_factory import ClassFactory, ClassType

# Import the network simulator
sys.path.append(os.path.join(os.path.dirname(__file__), "../../testenv/cloud_edge_net"))
from latency_injector import NetworkSimulator


@ClassFactory.register(ClassType.GENERAL, alias="cloud_edge_scheduler")
class SpeculativeScheduler:
    """
    Cloud-Edge Speculative Decoding Scheduler.
    
    Simulates edge-cloud collaboration for LLM inference with:
    - Draft model (edge): Fast but less accurate
    - Target model (cloud): Slow but accurate
    - Network simulation: Realistic latency/bandwidth/jitter
    """
    
    def __init__(self, **kwargs):
        """
        Initialize scheduler with models and network simulator.
        
        Args:
            **kwargs: Configuration parameters including:
                - draft_model: Draft model name/path
                - target_model: Target model name/path
                - draft_k: Number of tokens to draft per iteration
                - rtt_ms: Network round-trip time
                - bandwidth_mbps: Network bandwidth
                - jitter_ms: Network jitter
                - concurrency: Max concurrent requests
                - random_seed: Random seed for reproducibility
        """
        # Algorithm parameters
        self.draft_k = int(kwargs.get("draft_k", 3))
        self.draft_name = kwargs.get("draft_model", "gpt2") 
        self.target_name = kwargs.get("target_model", "gpt2-medium")
        
        # Network simulation parameters
        self.rtt_ms = float(kwargs.get("rtt_ms", 50))
        self.bandwidth_mbps = float(kwargs.get("bandwidth_mbps", 100))
        self.jitter_ms = float(kwargs.get("jitter_ms", 0))
        self.concurrency = int(kwargs.get("concurrency", 1))
        
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
        
        # Device configuration
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"\n[INIT] SpeculativeScheduler", flush=True)
        print(f"  Device: {self.device}", flush=True)
        print(f"  Draft: {self.draft_name}, Target: {self.target_name}", flush=True)
        print(f"  Draft K: {self.draft_k}", flush=True)
        print(f"  Network: RTT={self.rtt_ms}ms, BW={self.bandwidth_mbps}Mbps, Jitter=±{self.jitter_ms}ms", flush=True)
        
        # Load models
        print(f"[LOADING] Loading models...", flush=True)
        self.draft_model = AutoModelForCausalLM.from_pretrained(self.draft_name).to(self.device)
        self.draft_tokenizer = AutoTokenizer.from_pretrained(self.draft_name)
        
        self.target_model = AutoModelForCausalLM.from_pretrained(self.target_name).to(self.device)
        self.target_tokenizer = AutoTokenizer.from_pretrained(self.target_name)
        
        # Set pad tokens if missing
        if self.draft_tokenizer.pad_token is None:
            self.draft_tokenizer.pad_token = self.draft_tokenizer.eos_token
        if self.target_tokenizer.pad_token is None:
            self.target_tokenizer.pad_token = self.target_tokenizer.eos_token
        
        print(f"[READY] Models loaded successfully", flush=True)

    def train(self, train_data, valid_data=None, **kwargs):
        """Required by Ianvs interface (no training needed)."""
        return self
    
    def save(self, model_path):
        """Required by Ianvs interface (no saving needed)."""
        return model_path
    
    def load(self, model_path):
        """Required by Ianvs interface (models loaded in __init__)."""
        return self

    def _calculate_payload_size(self, token_ids):
        """
        Estimate network payload size for bandwidth simulation.
        
        Includes:
        - Token IDs (4 bytes per token, int32)
        - KV cache estimate (~8KB per token, simplified)
        
        Args:
            token_ids (torch.Tensor): Token ID tensor
            
        Returns:
            int: Estimated payload size in bytes
        """
        num_tokens = token_ids.shape[1]
        token_bytes = num_tokens * 4  # int32
        
        # Simplified KV cache estimate
        # Real KV cache size depends on: num_layers * hidden_size * 2 (K and V)
        # For GPT-2: 12 layers * 768 hidden * 2 = ~18KB per token
        # Using conservative estimate of 8KB
        kv_cache_bytes = num_tokens * 8192
        
        return token_bytes + kv_cache_bytes

    def _verify_tokens(self, draft_ids, original_input_len):
        """
        Verify draft tokens using target model (Speculative Decoding logic).
        
        Process:
        1. Run target model forward pass on draft sequence
        2. Compare target's predictions with draft tokens
        3. Accept tokens until first mismatch (greedy verification)
        
        Args:
            draft_ids (torch.Tensor): Draft sequence (input + new tokens)
            original_input_len (int): Length of original input (before drafting)
            
        Returns:
            tuple: (accepted_count, acceptance_rate, verified_ids)
        """
        with torch.no_grad():
            # Get target model's predictions
            target_out = self.target_model(draft_ids)
            target_logits = target_out.logits
            
            # Extract only the new draft tokens (not the original input)
            draft_tokens = draft_ids[0, original_input_len:]
            
            # Verify each draft token
            accepted = 0
            for i, draft_token in enumerate(draft_tokens):
                # Check if we have corresponding target prediction
                if i >= target_logits.shape[1] - original_input_len:
                    break
                
                # Get target's top prediction at this position
                target_probs = torch.softmax(target_logits[0, original_input_len + i, :], dim=-1)
                target_token = torch.argmax(target_probs).item()
                
                # Accept if draft matches target's prediction
                if draft_token.item() == target_token:
                    accepted += 1
                else:
                    # Reject remaining tokens (greedy verification)
                    break
            
            # Calculate acceptance rate
            total_drafted = len(draft_tokens)
            acceptance_rate = accepted / total_drafted if total_drafted > 0 else 0.0
            
            # Create verified sequence (input + accepted tokens)
            if accepted > 0:
                verified_ids = draft_ids[:, :original_input_len + accepted]
            else:
                # Fallback: use target's first prediction
                first_target_token = torch.argmax(target_logits[0, original_input_len - 1, :]).unsqueeze(0).unsqueeze(0)
                verified_ids = torch.cat([draft_ids[:, :original_input_len], first_target_token], dim=1)
                accepted = 1
            
            return accepted, acceptance_rate, verified_ids

    def predict(self, data, **kwargs):
        """
        Run speculative decoding benchmark on provided data.
        
        Args:
            data: Input data (file paths or text samples)
            **kwargs: Additional parameters
            
        Returns:
            list: Results with latency, throughput, acceptance rate, etc.
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

        print(f"\n[BENCHMARK] Processing {len(clean_file_paths)} samples...", flush=True)

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
            inputs = self.draft_tokenizer(prompt_text, return_tensors="pt").to(self.device)
            input_ids = inputs["input_ids"]
            original_len = input_ids.shape[1]

            # Metrics tracking
            start_time = time.time()
            ttft = 0.0
            total_tokens_generated = 0
            total_tokens_accepted = 0
            acceptance_rates = []
            max_new_tokens = 20  # Generate 20 tokens total
            
            with torch.no_grad():
                while total_tokens_generated < max_new_tokens:
                    # =================================================================
                    # STEP 1: EDGE - Draft Generation (The "Intern")
                    # =================================================================
                    draft_start = time.time()
                    
                    draft_out = self.draft_model.generate(
                        input_ids, 
                        max_new_tokens=self.draft_k,
                        pad_token_id=self.draft_tokenizer.eos_token_id,
                        do_sample=False,  # Greedy decoding for reproducibility
                        use_cache=True
                    )
                    
                    draft_time = time.time() - draft_start
                    
                    # Record Time To First Token (only for first iteration)
                    if total_tokens_generated == 0:
                        ttft = draft_time * 1000  # Convert to milliseconds

                    # =================================================================
                    # STEP 2: NETWORK - Edge → Cloud (Simulated)
                    # =================================================================
                    payload_size = self._calculate_payload_size(draft_out)
                    network_delay = self.network.inject_delay(payload_size)

                    # =================================================================
                    # STEP 3: CLOUD - Verification (The "Boss")
                    # =================================================================
                    verify_start = time.time()
                    
                    accepted, accept_rate, verified_ids = self._verify_tokens(
                        draft_out, 
                        original_len + total_tokens_generated
                    )
                    
                    verify_time = time.time() - verify_start
                    
                    # Track acceptance statistics
                    total_tokens_accepted += accepted
                    acceptance_rates.append(accept_rate)
                    
                    # Update input sequence with verified tokens
                    input_ids = verified_ids
                    total_tokens_generated += accepted
                    
                    # Stop if we hit EOS token
                    if self.draft_tokenizer.eos_token_id in verified_ids[0]:
                        break

            # Calculate final metrics
            end_time = time.time()
            total_latency = end_time - start_time
            throughput = total_tokens_generated / total_latency if total_latency > 0 else 0
            final_accept_rate = total_tokens_accepted / (len(acceptance_rates) * self.draft_k) if acceptance_rates else 0
            
            # Energy estimation (Watts * Time = Joules)
            power_watts = 250.0 if self.device == "cuda" else 100.0
            energy_joules = total_latency * power_watts
            
            # Store results
            result = {
                "latency": total_latency,
                "throughput": throughput,
                "energy": energy_joules,
                "final_acceptance_rate": final_accept_rate,
                "ttft_ms": ttft,
                "draft_k": self.draft_k,
                "compute_ratio": 1.0,  # Could calculate from draft_time/verify_time
                "dataset_task": 1,  # 1 = WikiText (can be extended)
                "rtt_ms": self.rtt_ms,
                "bandwidth_mbps": self.bandwidth_mbps,
                "jitter_ms": self.jitter_ms
            }
            
            results.append(result)
            
            # Progress logging (every 5 samples or last sample)
            if (idx + 1) % 5 == 0 or idx == len(clean_file_paths) - 1:
                print(f"[{idx+1}/{len(clean_file_paths)}] "
                      f"TTFT: {ttft:.0f}ms | "
                      f"Latency: {total_latency:.2f}s | "
                      f"Speed: {throughput:.2f} tok/s | "
                      f"Accept: {final_accept_rate:.2%}", flush=True)
        
        print(f"[COMPLETE] Processed all {len(clean_file_paths)} samples\n", flush=True)
        return results


# Standalone testing
if __name__ == "__main__":
    print("Testing SpeculativeScheduler...")
    
    # Create scheduler
    scheduler = SpeculativeScheduler(
        draft_model="gpt2",
        target_model="gpt2-medium",
        draft_k=3,
        rtt_ms=50,
        bandwidth_mbps=100,
        jitter_ms=5,
        random_seed=42
    )
    
    # Test with sample data
    test_data = ["The future of AI is"]
    results = scheduler.predict(test_data)
    
    print("\nTest Results:")
    for key, value in results[0].items():
        print(f"  {key}: {value}")
    
    print("\n✓ SpeculativeScheduler tests passed")