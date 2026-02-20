import time
import torch
from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer

# --- CONFIGURATION ---
MODEL_NAME = "gpt2-medium"
PORT = 5000
WARMUP_ENABLED = True

# --- SETUP ---
app = Flask(__name__)
device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"[INIT] Loading Cloud Model: {MODEL_NAME} on {device}...")
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME).to(device)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print(f"[INIT] Model Loaded Successfully!")

# --- WARMUP (Critical for fair benchmarking) ---
if WARMUP_ENABLED:
    print("[INIT] Running warmup inference...")
    dummy_input = torch.tensor([[1, 2, 3, 4, 5]]).to(device)
    with torch.no_grad():
        _ = model(dummy_input)
    print("[INIT] Warmup complete. Ready to accept requests.")


@app.route('/verify', methods=['POST'])
def verify():
    """
    Endpoint called by Edge Device.
    Receives: {"tokens": [123, 456, ...], "original_len": 10}
    Returns:  {"logits": [...], "processing_time": 0.5}
    """
    try:
        data = request.json
        if not data or 'tokens' not in data:
            return jsonify({"error": "No tokens provided"}), 400

        # 1. Receive Draft Tokens
        draft_tokens_list = data['tokens']
        original_len = data.get('original_len', 0)  # Need this for verification
        
        input_ids = torch.tensor([draft_tokens_list]).to(device)

        # 2. Run Verification (Forward pass to get logits)
        start_time = time.time()
        
        with torch.no_grad():
            outputs = model(input_ids)
            logits = outputs.logits  # Shape: [1, seq_len, vocab_size]
        
        process_time = time.time() - start_time
        
        # 3. Extract logits for NEW tokens only (not the prompt)
        # We only need logits for positions >= original_len
        new_token_logits = logits[0, original_len:, :].cpu().tolist()
        
        print(f"[INFO] Verified {len(draft_tokens_list)} tokens in {process_time:.4f}s")

        return jsonify({
            "status": "success",
            "logits": new_token_logits,  # Send back for acceptance calculation
            "server_processing_time": process_time
        })

    except torch.cuda.OutOfMemoryError as e:
        print(f"[ERROR] GPU OOM: {e}")
        torch.cuda.empty_cache()
        return jsonify({"error": "GPU out of memory"}), 500
    
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model": MODEL_NAME,
        "device": str(device)
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, threaded=False)  # threaded=False for stability