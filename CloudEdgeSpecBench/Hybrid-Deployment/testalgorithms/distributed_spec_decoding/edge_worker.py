import time
import torch
import requests
import numpy as np
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from sedna.common.class_factory import ClassFactory, ClassType


@ClassFactory.register(ClassType.GENERAL, alias="edge_worker")
class EdgeWorker:
    def __init__(self, **kwargs):
        self.draft_k = int(kwargs.get("draft_k", 3))
        self.draft_name = kwargs.get("draft_model", "gpt2")
        self.cloud_url = kwargs.get("cloud_url", "http://127.0.0.1:5000").rstrip('/')
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"\n[INIT] Edge Worker on {self.device}")
        print(f"  Draft Model: {self.draft_name}")
        print(f"  Cloud Endpoint: {self.cloud_url}")
        print(f"  Draft K: {self.draft_k}")
        
        # Load draft model
        self.draft_model = AutoModelForCausalLM.from_pretrained(self.draft_name).to(self.device)
        self.draft_tokenizer = AutoTokenizer.from_pretrained(self.draft_name)
        if self.draft_tokenizer.pad_token is None:
            self.draft_tokenizer.pad_token = self.draft_tokenizer.eos_token
        
        # Test cloud connection
        self._test_cloud_connection()

    def _test_cloud_connection(self):
        """Verify cloud server is reachable"""
        try:
            response = requests.get(f"{self.cloud_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"[INIT] Cloud server connected successfully!")
            else:
                print(f"[WARNING] Cloud server returned status {response.status_code}")
        except Exception as e:
            print(f"[WARNING] Could not connect to cloud: {e}")

    def _verify_tokens(self, draft_ids, cloud_logits, original_len):
        """
        Calculate acceptance rate by comparing draft vs cloud predictions.
        
        Args:
            draft_ids: Draft token IDs [batch, seq_len]
            cloud_logits: Cloud model logits for new tokens
            original_len: Length of original prompt
        
        Returns:
            (num_accepted, acceptance_rate)
        """
        accepted = 0
        draft_tokens = draft_ids[0, original_len:]  # Only new tokens
        
        for i, draft_token in enumerate(draft_tokens):
            if i >= len(cloud_logits):
                break
            
            # Get cloud's top prediction
            cloud_token = np.argmax(cloud_logits[i])
            
            # Accept if they match
            if draft_token.item() == cloud_token:
                accepted += 1
            else:
                break  # Stop at first mismatch
        
        acceptance_rate = accepted / len(draft_tokens) if len(draft_tokens) > 0 else 0.0
        return accepted, acceptance_rate

    def train(self, train_data, valid_data=None, **kwargs): 
        return self
    
    def save(self, model_path): 
        return model_path
    
    def load(self, model_path): 
        return self

    def predict(self, data, **kwargs):
        results = []
        clean_file_paths = []
        
        # Process input data
        if not isinstance(data, list) and not isinstance(data, np.ndarray):
            data = [data]
        
        for item in data:
            if isinstance(item, np.ndarray):
                item = item.tolist()
            path = item[0] if isinstance(item, list) else item
            clean_file_paths.append(str(path))

        # Limit to 5 samples for speed (can be adjusted)
        clean_file_paths = clean_file_paths[:5]
        total_jobs = len(clean_file_paths)
        
        print(f"\n[BENCHMARK] Processing {total_jobs} samples...", flush=True)

        for i, file_path in enumerate(clean_file_paths):
            print(f"\n[{i+1}/{total_jobs}] Starting sample...", flush=True)
            
            # Load prompt
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        prompt_text = f.read().strip()[:300]
                else:
                    prompt_text = "The quick brown fox jumps over the lazy dog."
            except:
                prompt_text = "AI benchmark test."

            # Tokenize
            inputs = self.draft_tokenizer(prompt_text, return_tensors="pt").to(self.device)
            input_ids = inputs["input_ids"]
            original_len = input_ids.shape[1]

            # Metrics tracking
            start_time = time.time()
            ttft = 0.0
            total_tokens = 0
            total_accepted = 0
            max_new = 20
            request_count = 0
            
            with torch.no_grad():
                while total_tokens < max_new:
                    # === EDGE: Draft Generation ===
                    draft_start = time.time()
                    draft_out = self.draft_model.generate(
                        input_ids,
                        max_new_tokens=self.draft_k,
                        pad_token_id=self.draft_tokenizer.eos_token_id,
                        do_sample=False  # Greedy for reproducibility
                    )
                    draft_time = time.time() - draft_start
                    
                    # Record TTFT (first token only)
                    if total_tokens == 0:
                        ttft = draft_time * 1000  # Convert to ms

                    # === NETWORK: Send to Cloud ===
                    draft_tokens_list = draft_out[0].tolist()
                    
                    try:
                        payload = {
                            "tokens": draft_tokens_list,
                            "original_len": original_len
                        }
                        
                        network_start = time.time()
                        response = requests.post(
                            f"{self.cloud_url}/verify",
                            json=payload,
                            timeout=120
                        )
                        network_time = time.time() - network_start
                        
                        if response.status_code != 200:
                            print(f"  [ERROR] Server returned {response.status_code}")
                            break
                        
                        cloud_data = response.json()
                        cloud_logits = cloud_data.get("logits", [])
                        
                        # === VERIFICATION: Calculate Acceptance ===
                        accepted, accept_rate = self._verify_tokens(
                            draft_out, cloud_logits, original_len
                        )
                        total_accepted += accepted
                        
                        print(f"  Request {request_count+1}: "
                              f"Drafted {self.draft_k} → Accepted {accepted} "
                              f"({accept_rate:.1%}) | "
                              f"Network: {network_time:.2f}s", flush=True)
                        
                        # Update input (only accepted tokens)
                        if accepted > 0:
                            input_ids = draft_out[:, :original_len + accepted]
                        else:
                            # Fallback: Accept cloud's first token
                            cloud_token = np.argmax(cloud_logits[0])
                            cloud_token_tensor = torch.tensor([[cloud_token]]).to(self.device)
                            input_ids = torch.cat([input_ids, cloud_token_tensor], dim=1)
                            accepted = 1
                        
                        total_tokens += accepted
                        original_len = input_ids.shape[1]
                        request_count += 1
                        
                    except requests.Timeout:
                        print(f"  [ERROR] Request timeout after 120s")
                        break
                    except Exception as e:
                        print(f"  [ERROR] Connection failed: {e}")
                        break

            end_time = time.time()
            
            # Final metrics
            total_latency = end_time - start_time
            throughput = total_tokens / total_latency if total_latency > 0 else 0
            final_accept_rate = total_accepted / total_tokens if total_tokens > 0 else 0
            
            # Energy estimation
            power_watts = 250.0 if self.device == "cuda" else 100.0
            energy_joules = total_latency * power_watts
            
            print(f"\n  COMPLETE: {total_tokens} tokens in {total_latency:.2f}s "
                  f"({throughput:.2f} tok/s) | "
                  f"Overall Acceptance: {final_accept_rate:.1%}", flush=True)
            
            results.append({
                "latency": total_latency,
                "throughput": throughput,
                "energy": energy_joules,
                "final_acceptance_rate": final_accept_rate,
                "ttft_ms": ttft,
                "draft_k": self.draft_k,
                "cloud_url": self.cloud_url,
                "total_requests": request_count
            })
        
        return results